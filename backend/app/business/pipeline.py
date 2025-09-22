"""
Data Collection Pipeline
========================

Main orchestrator for the data collection process.
Implements the Facade pattern to coordinate multiple collectors.

Following FYP Report specification:
- SY-FR1: Data Collection Pipeline
- Multi-source data integration
- Pipeline orchestration and monitoring
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import logging

from .processor import TextProcessor, ProcessingConfig, ProcessingResult
from ..infrastructure.collectors.base_collector import (
    BaseCollector, CollectionConfig, CollectionResult, DateRange, RawData
)
from ..infrastructure.collectors.reddit_collector import RedditCollector
from ..infrastructure.collectors.finnhub_collector import FinHubCollector  
from ..infrastructure.collectors.newsapi_collector import NewsAPICollector
from ..infrastructure.collectors.marketaux_collector import MarketauxCollector
from ..infrastructure.rate_limiter import RateLimitHandler
from ..data_access.repositories.sentiment_repository import SentimentDataRepository
from ..data_access.repositories.stock_repository import StockRepository
from ..infrastructure.security.security_utils import SecurityUtils
from ..infrastructure.log_system import get_logger
# Sentiment Analysis Integration
from ..service.sentiment_processing import get_sentiment_engine, EngineConfig
from ..service.sentiment_processing import TextInput, DataSource, SentimentResult
# Database Models for Storage
from ..data_access.models import SentimentData, Stock, NewsArticle, RedditPost
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..data_access.database.connection import get_db
# WebSocket imports removed - using direct database storage

# Initialize logger using singleton LogSystem
logger = get_logger()


# Note: TARGET_STOCKS are now managed dynamically via WatchlistService
# The static list has been replaced with database-driven watchlist management


class PipelineStatus(Enum):
    """Pipeline execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution"""
    symbols: List[str]
    date_range: DateRange
    max_items_per_symbol: int = 100
    include_reddit: bool = True
    include_finnhub: bool = True
    include_newsapi: bool = True
    include_marketaux: bool = True
    include_comments: bool = True
    parallel_collectors: bool = True
    processing_config: Optional[ProcessingConfig] = None
    
    def __post_init__(self):
        if not self.symbols:
            raise ValueError("At least one stock symbol must be provided")
        if self.processing_config is None:
            self.processing_config = ProcessingConfig()
    
    @classmethod
    def create_default_config(
        cls,
        symbols: Optional[List[str]] = None,
        date_range: Optional[DateRange] = None,
        max_items_per_symbol: int = 10,
        **kwargs
    ) -> 'PipelineConfig':
        """
        Create pipeline configuration with provided symbols (dynamic watchlist required).
        
        Args:
            symbols: List of stock symbols (required - use dynamic watchlist)
            date_range: Date range for collection (defaults to near real-time)
            max_items_per_symbol: Maximum items per symbol (default: 10)
            **kwargs: Additional configuration parameters
            
        Returns:
            PipelineConfig with provided symbols
        """
        if date_range is None:
            date_range = DateRange.near_realtime()
        if symbols is None:
            raise ValueError("PipelineConfig.create_default_config now requires a symbols argument (dynamic watchlist)")
        
        return cls(
            symbols=symbols,
            date_range=date_range,
            max_items_per_symbol=max_items_per_symbol,
            **kwargs
        )


@dataclass
class CollectorStats:
    """Statistics for a single collector"""
    name: str
    enabled: bool
    success: bool
    items_collected: int
    execution_time: float
    error_message: Optional[str] = None


@dataclass
class SentimentAnalysisResult:
    """Result of sentiment analysis for a single text"""
    raw_data: RawData
    processing_result: ProcessingResult
    sentiment_result: Optional[SentimentResult]
    success: bool
    timestamp: datetime
    error: Optional[str] = None


@dataclass
class PipelineResult:
    """Result of pipeline execution"""
    pipeline_id: str
    status: PipelineStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    total_items_collected: int = 0
    total_items_processed: int = 0
    total_items_stored: int = 0
    total_items_analyzed: int = 0  # New: sentiment analysis count
    collector_stats: List[CollectorStats] = field(default_factory=list)
    processing_stats: Dict[str, Any] = field(default_factory=dict)
    sentiment_stats: Dict[str, Any] = field(default_factory=dict)  # New: sentiment analysis stats
    error_message: Optional[str] = None
    
    @property
    def execution_time(self) -> float:
        """Total execution time in seconds"""
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    @property
    def success_rate(self) -> float:
        """Success rate across all collectors"""
        if not self.collector_stats:
            return 0.0
        successful = sum(1 for stat in self.collector_stats if stat.success)
        return successful / len(self.collector_stats)


class DataPipeline:
    """
    Main data collection pipeline implementing the Facade pattern.
    
    Orchestrates multiple data collectors, text processing, and storage.
    Provides a unified interface for data collection operations.
    """
    
    def __init__(
        self,
        rate_limiter: Optional[RateLimitHandler] = None,
        sentiment_repository: Optional[SentimentDataRepository] = None,
        stock_repository: Optional[StockRepository] = None,
        auto_configure_collectors: bool = True
    ):
        """
        Initialize the data pipeline.
        
        Args:
            rate_limiter: Rate limiting handler for API calls
            sentiment_repository: Repository for storing sentiment data
            stock_repository: Repository for stock data
            auto_configure_collectors: If True, automatically configure collectors from environment variables
        """
        self.rate_limiter = rate_limiter or RateLimitHandler()
        self.text_processor = TextProcessor()
        self.logger = get_logger()  # Use LogSystem singleton logger
        
        # Note: Repositories will be initialized later during async execution
        # since they require async sessions
        self.sentiment_repository = sentiment_repository
        self.stock_repository = stock_repository
        self._repository_initialized = False
        
        # Initialize sentiment analysis engine (singleton)
        sentiment_config = EngineConfig(
            enable_vader=True,
            enable_finbert=True,
            finbert_use_gpu=True,  # Will auto-detect if GPU is available
            max_concurrent_batches=2,  # Conservative for stability
            default_batch_size=16,
            fallback_to_neutral=True  # Graceful degradation
        )
        self.sentiment_engine = get_sentiment_engine(sentiment_config)
        
        # Pipeline state
        self.current_status = PipelineStatus.IDLE
        self.current_result: Optional[PipelineResult] = None
        self._cancel_requested = False
        
        # Collectors (initialized with API keys from environment)
        self._collectors: Dict[str, BaseCollector] = {}
        
        # Auto-configure collectors from environment variables
        if auto_configure_collectors:
            self._auto_configure_collectors()
    
    async def _initialize_repositories(self) -> None:
        """Initialize repositories with async database sessions."""
        if self._repository_initialized:
            return
            
        try:
            # Initialize database connection
            from ..data_access.database.connection import init_database, get_db_session
            await init_database()
            
            # Note: Repository initialization will be done per operation to ensure proper session management
            # This prevents the SQLAlchemy connection pool warnings about unclosed connections
            self.sentiment_repository = "INITIALIZED"  # Marker to show it will be created per operation
            self.stock_repository = "INITIALIZED"  # Marker to show it will be created per operation
            self.logger.info("Repository initialization configured for per-operation session management")
                    
            self._repository_initialized = True
            
        except Exception as e:
            self.logger.warning(f"Could not initialize repositories: {e}")

    def configure_collectors(self, api_keys: Dict[str, Any]) -> None:
        """
        Configure data collectors with API keys.
        
        Args:
            api_keys: Dictionary of API keys for each service
        """
        try:
            # Reddit collector
            if "reddit" in api_keys:
                reddit_config = api_keys["reddit"]
                self._collectors["reddit"] = RedditCollector(
                    client_id=reddit_config.get("client_id"),
                    client_secret=reddit_config.get("client_secret"),
                    user_agent=reddit_config.get("user_agent", "StockSentimentBot/1.0"),
                    rate_limiter=self.rate_limiter
                )
            
            # FinHub collector
            if "finnhub" in api_keys:
                self._collectors["finnhub"] = FinHubCollector(
                    api_key=api_keys["finnhub"],
                    rate_limiter=self.rate_limiter
                )
            
            # NewsAPI collector
            if "newsapi" in api_keys:
                self._collectors["newsapi"] = NewsAPICollector(
                    api_key=api_keys["newsapi"],
                    rate_limiter=self.rate_limiter
                )
            
            # MarketAux collector
            if "marketaux" in api_keys:
                self._collectors["marketaux"] = MarketauxCollector(
                    api_key=api_keys["marketaux"],
                    rate_limiter=self.rate_limiter
                )
            
            self.logger.info(f"Configured {len(self._collectors)} collectors")
            
        except Exception as e:
            self.logger.error(f"Error configuring collectors: {str(e)}")
            raise
    
    def _auto_configure_collectors(self) -> None:
        """
        Automatically configure collectors using encrypted environment variables.
        
        Uses SecureAPIKeyLoader to decrypt API keys for enhanced security.
        Environment variables expected:
        - REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET
        - NEWSAPI_KEY
        - FINNHUB_API_KEY
        - MARKETAUX_API_KEY
        """
        try:
            collectors_configured = 0
            
            # Ensure .env file is loaded (critical for tests and direct usage)
            try:
                from dotenv import load_dotenv
                load_dotenv()
            except ImportError:
                pass  # dotenv is optional
            
            # Load decrypted API keys securely using the same method as DataCollector
            self.logger.info("🔐 Loading and decrypting API keys...")
            from ..infrastructure.security.api_key_manager import SecureAPIKeyLoader
            secure_loader = SecureAPIKeyLoader()
            
            # Load decrypted API keys using SecureAPIKeyLoader (same as DataCollector)
            api_keys = secure_loader.load_api_keys()
            
            # Reddit collector
            reddit_client_id = api_keys.get('reddit_client_id')
            reddit_client_secret = api_keys.get('reddit_client_secret')
            reddit_user_agent = api_keys.get('reddit_user_agent')
            
            if reddit_client_id and reddit_client_secret:
                try:
                    self._collectors["reddit"] = RedditCollector(
                        client_id=reddit_client_id,
                        client_secret=reddit_client_secret,
                        user_agent=reddit_user_agent,
                        rate_limiter=self.rate_limiter
                    )
                    self.logger.info("Reddit collector configured", component="pipeline")
                except Exception as e:
                    self.logger.warning(f"Failed to configure Reddit collector: {str(e)}", component="pipeline")
            else:
                self.logger.warning("Reddit collector skipped - API keys not configured", component="pipeline")
            
            # FinHub collector
            finnhub_api_key = api_keys.get('finnhub_api_key')
            if finnhub_api_key:
                try:
                    self._collectors["finnhub"] = FinHubCollector(
                        api_key=finnhub_api_key,
                        rate_limiter=self.rate_limiter
                    )
                    collectors_configured += 1
                    self.logger.info("FinHub collector configured", component="pipeline")
                except Exception as e:
                    self.logger.warning(f"Failed to configure FinHub collector: {str(e)}", component="pipeline")
            else:
                self.logger.warning("FinHub collector skipped - API key not configured", component="pipeline")
            
            # NewsAPI collector
            newsapi_key = api_keys.get('news_api_key')
            if newsapi_key:
                try:
                    self._collectors["newsapi"] = NewsAPICollector(
                        api_key=newsapi_key,
                        rate_limiter=self.rate_limiter
                    )
                    collectors_configured += 1
                    self.logger.info("NewsAPI collector configured", component="pipeline")
                except Exception as e:
                    self.logger.warning(f"Failed to configure NewsAPI collector: {str(e)}", component="pipeline")
            else:
                self.logger.warning("NewsAPI collector skipped - API key not configured", component="pipeline")
            
            # MarketAux collector
            marketaux_key = api_keys.get('marketaux_api_key')
            if marketaux_key:
                try:
                    self._collectors["marketaux"] = MarketauxCollector(
                        api_key=marketaux_key,
                        rate_limiter=self.rate_limiter
                    )
                    collectors_configured += 1
                    self.logger.info("MarketAux collector configured", component="pipeline")
                except Exception as e:
                    self.logger.warning(f"Failed to configure MarketAux collector: {str(e)}", component="pipeline")
            else:
                self.logger.warning("MarketAux collector skipped - API key not configured", component="pipeline")
            
            # Clear decrypted keys from memory for security
            # Cache cleared automatically
            
            self.logger.info(f"Auto-configured {collectors_configured} collectors with encrypted API keys")
            
        except Exception as e:
            self.logger.error(f"Error auto-configuring collectors: {str(e)}")
            # Don't raise - pipeline can still work with manually configured collectors
    
    async def run_pipeline(self, config: PipelineConfig) -> PipelineResult:
        """
        Execute the complete data collection pipeline.
        
        Args:
            config: Pipeline configuration
            
        Returns:
            PipelineResult with execution details
        """
        pipeline_id = f"pipeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        start_time = datetime.utcnow()
        
        # Initialize repositories for database operations
        await self._initialize_repositories()
        
        # Initialize result
        result = PipelineResult(
            pipeline_id=pipeline_id,
            status=PipelineStatus.RUNNING,
            start_time=start_time
        )
        
        self.current_result = result
        self.current_status = PipelineStatus.RUNNING
        self._cancel_requested = False
            
        try:
            # Log pipeline start with comprehensive context
            self.logger.log_pipeline_operation(
                "pipeline_execution_start",
                {
                    "pipeline_id": pipeline_id,
                    "symbols": config.symbols,
                    "date_range": {
                        "start": config.date_range.start_date.isoformat() if config.date_range else None,
                        "end": config.date_range.end_date.isoformat() if config.date_range else None
                    },
                    "config": {
                        "include_reddit": config.include_reddit,
                        "include_finnhub": config.include_finnhub,
                        "max_items_per_symbol": config.max_items_per_symbol,
                        "include_comments": config.include_comments
                    }
                }
            )
            
            # Step 1: Data Collection with tracking
            self.logger.log_pipeline_operation(
                "collection_phase_start",
                {"pipeline_id": pipeline_id, "symbols": config.symbols}
            )
            
            collection_results = await self._collect_data(config)
            result.collector_stats = self._build_collector_stats(collection_results)
            
            # Log collection metrics with detailed breakdown
            total_collected = sum(stat.items_collected for stat in result.collector_stats)
            successful_collectors = len([stat for stat in result.collector_stats if stat.success])
            
            # Create detailed collection summary
            collection_summary = {}
            for stat in result.collector_stats:
                source_name = stat.name.upper()
                collection_summary[source_name] = {
                    "items_collected": stat.items_collected,
                    "success": stat.success,
                    "processing_time_ms": round(stat.execution_time * 1000, 2),
                    "error": stat.error_message if not stat.success else None
                }
            
            self.logger.log_pipeline_operation(
                "collection_phase_complete",
                {
                    "pipeline_id": pipeline_id,
                    "total_collected": total_collected,
                    "successful_collectors": successful_collectors,
                    "total_collectors": len(result.collector_stats),
                    "collection_breakdown": collection_summary,
                    "collection_stats": [
                        {
                            "collector": stat.name,
                            "success": stat.success,
                            "items_collected": stat.items_collected,
                            "processing_time": stat.execution_time
                        }
                        for stat in result.collector_stats
                    ]
                }
            )
            
            # Log human-readable summary
            self.logger.info(
                f"📊 Data Collection Summary for Pipeline {pipeline_id}:",
                extra={
                    "pipeline_id": pipeline_id,
                    "total_items": total_collected,
                    "reddit_items": collection_summary.get("REDDIT", {}).get("items_collected", 0),
                    "finnhub_items": collection_summary.get("FINNHUB", {}).get("items_collected", 0),
                    "newsapi_items": collection_summary.get("NEWSAPI", {}).get("items_collected", 0),
                    "marketaux_items": collection_summary.get("MARKETAUX", {}).get("items_collected", 0),
                    "successful_sources": successful_collectors,
                    "total_sources": len(result.collector_stats)
                }
            )
            
            if self._cancel_requested:
                self.logger.log_pipeline_operation(
                    "pipeline_cancelled", 
                    {"pipeline_id": pipeline_id, "phase": "collection"}
                )
                result.status = PipelineStatus.CANCELLED
                return result

            # Step 1.5: Store Raw Data (News Articles and Reddit Posts)
            self.logger.log_pipeline_operation(
                "raw_data_storage_phase_start",
                {"pipeline_id": pipeline_id}
            )
            
            raw_data_stored_count = await self._store_raw_data(collection_results, pipeline_id)
            
            self.logger.log_pipeline_operation(
                "raw_data_storage_phase_complete",
                {
                    "pipeline_id": pipeline_id,
                    "raw_items_stored": raw_data_stored_count
                }
            )

            # Step 2: Data Processing with tracking
            self.logger.log_pipeline_operation(
                "processing_phase_start",
                {"pipeline_id": pipeline_id, "items_to_process": total_collected}
            )
            
            processing_results = await self._process_data(collection_results, config)
            result.processing_stats = self._build_processing_stats(processing_results)
            
            successful_processing = len([r for r in processing_results if r.success])
            self.logger.log_pipeline_operation(
                "processing_phase_complete",
                {
                    "pipeline_id": pipeline_id,
                    "total_processed": successful_processing,
                    "processing_success_rate": successful_processing / total_collected if total_collected > 0 else 0
                }
            )
            
            if self._cancel_requested:
                self.logger.log_pipeline_operation(
                    "pipeline_cancelled", 
                    {"pipeline_id": pipeline_id, "phase": "processing"}
                )
                result.status = PipelineStatus.CANCELLED
                return result
            
            # Step 3: Sentiment Analysis with tracking
            self.logger.log_pipeline_operation(
                "sentiment_analysis_start",
                {"pipeline_id": pipeline_id, "items_for_analysis": successful_processing}
            )
            
            sentiment_results = await self._analyze_sentiment(processing_results, config)
            result.sentiment_stats = self._build_sentiment_stats(sentiment_results)
            result.total_items_analyzed = len([r for r in sentiment_results if r.success])
            
            self.logger.log_pipeline_operation(
                "sentiment_analysis_complete",
                {
                    "pipeline_id": pipeline_id,
                    "items_analyzed": result.total_items_analyzed,
                    "analysis_success_rate": result.total_items_analyzed / successful_processing if successful_processing > 0 else 0
                }
            )
            
            if self._cancel_requested:
                self.logger.log_pipeline_operation(
                    "pipeline_cancelled", 
                    {"pipeline_id": pipeline_id, "phase": "sentiment_analysis"}
                )
                result.status = PipelineStatus.CANCELLED
                return result
            
            # Step 4: Data Storage with tracking
            if self.sentiment_repository:
                self.logger.log_pipeline_operation(
                    "storage_phase_start",
                    {"pipeline_id": pipeline_id, "items_to_store": result.total_items_analyzed}
                )
                
                stored_count = await self._store_sentiment_data(sentiment_results, config)
                result.total_items_stored = stored_count
                
                self.logger.log_pipeline_operation(
                    "storage_phase_complete",
                    {
                        "pipeline_id": pipeline_id,
                        "items_stored": stored_count,
                        "storage_success_rate": stored_count / result.total_items_analyzed if result.total_items_analyzed > 0 else 0
                    }
                )
            else:
                self.logger.log_pipeline_operation(
                    "storage_phase_skipped",
                    {"pipeline_id": pipeline_id, "reason": "no_sentiment_repository"}
                )
            
            # Update final statistics
            result.total_items_collected = sum(stat.items_collected for stat in result.collector_stats)
            result.total_items_processed = len([r for r in processing_results if r.success])
            result.status = PipelineStatus.COMPLETED
            result.end_time = datetime.utcnow()
            
            # Log comprehensive completion metrics
            execution_time = (result.end_time - result.start_time).total_seconds()
            self.logger.log_pipeline_operation(
                "pipeline_execution_complete",
                {
                    "pipeline_id": pipeline_id,
                    "execution_time_seconds": execution_time,
                    "total_collected": result.total_items_collected,
                    "total_processed": result.total_items_processed,
                    "total_analyzed": result.total_items_analyzed,
                    "total_stored": result.total_items_stored or 0,
                    "overall_success_rate": (result.total_items_stored or 0) / result.total_items_collected if result.total_items_collected > 0 else 0,
                    "items_per_second": result.total_items_collected / execution_time if execution_time > 0 else 0
                }
            )
            
        except Exception as e:
            result.status = PipelineStatus.FAILED
            result.error_message = str(e)
            result.end_time = datetime.utcnow()
            
            # Log comprehensive error information
            execution_time = (result.end_time - result.start_time).total_seconds()
            self.logger.log_error(
                "pipeline_execution_failed",
                {
                    "pipeline_id": pipeline_id,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "execution_time_seconds": execution_time,
                    "partial_results": {
                        "items_collected": result.total_items_collected or 0,
                        "items_processed": result.total_items_processed or 0,
                        "items_analyzed": result.total_items_analyzed or 0,
                        "items_stored": result.total_items_stored or 0
                    },
                    "symbols": config.symbols
                }
            )
        
        finally:
            self.current_status = result.status
        
        return result
    
    async def _collect_data(self, config: PipelineConfig) -> Dict[str, CollectionResult]:
        """Collect data from all configured sources"""
        collection_config = CollectionConfig(
            symbols=config.symbols,
            date_range=config.date_range,
            max_items_per_symbol=config.max_items_per_symbol,
            include_comments=config.include_comments
        )
        
        # Determine which collectors to use
        collectors_to_run = []
        
        if config.include_reddit and "reddit" in self._collectors:
            collectors_to_run.append(("reddit", self._collectors["reddit"]))
        
        if config.include_finnhub and "finnhub" in self._collectors:
            collectors_to_run.append(("finnhub", self._collectors["finnhub"]))
        
        if config.include_newsapi and "newsapi" in self._collectors:
            collectors_to_run.append(("newsapi", self._collectors["newsapi"]))
        
        if config.include_marketaux and "marketaux" in self._collectors:
            collectors_to_run.append(("marketaux", self._collectors["marketaux"]))
        
        # Run collectors
        if config.parallel_collectors:
            # Run collectors in parallel
            tasks = []
            for name, collector in collectors_to_run:
                task = asyncio.create_task(
                    self._run_collector_with_timeout(name, collector, collection_config)
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            collection_results = {}
            for i, (name, _) in enumerate(collectors_to_run):
                if isinstance(results[i], Exception):
                    self.logger.error(f"Collector {name} failed: {str(results[i])}")
                    collection_results[name] = CollectionResult(
                        source=name,
                        success=False,
                        data=[],
                        error_message=str(results[i])
                    )
                else:
                    collection_results[name] = results[i]
        else:
            # Run collectors sequentially
            collection_results = {}
            for name, collector in collectors_to_run:
                if self._cancel_requested:
                    break
                
                try:
                    result = await self._run_collector_with_timeout(name, collector, collection_config)
                    collection_results[name] = result
                except Exception as e:
                    self.logger.error(f"Collector {name} failed: {str(e)}")
                    collection_results[name] = CollectionResult(
                        source=name,
                        success=False,
                        data=[],
                        error_message=str(e)
                    )
        
        return collection_results
    
    async def _run_collector_with_timeout(
        self, 
        name: str, 
        collector: BaseCollector, 
        config: CollectionConfig,
        timeout: int = 300  # 5 minutes
    ) -> CollectionResult:
        """Run a collector with timeout protection"""
        try:
            return await asyncio.wait_for(
                collector.collect_data(config), 
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise Exception(f"Collector {name} timed out after {timeout} seconds")
    
    async def _process_data(
        self, 
        collection_results: Dict[str, CollectionResult], 
        config: PipelineConfig
    ) -> List[ProcessingResult]:
        """Process collected raw data"""
        processing_results = []
        
        # Configure text processor
        if config.processing_config:
            self.text_processor.config = config.processing_config
        
        # Process data from each collector with comprehensive tracking
        processing_metrics = {
            "total_collectors": len(collection_results),
            "processed_collectors": 0,
            "total_items": 0,
            "processed_items": 0,
            "error_count": 0,
            "processing_start": datetime.utcnow(),
            "correlation_id": f"process_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Calculate total items across all collectors
        for collection_result in collection_results.values():
            if collection_result.success and collection_result.data:
                processing_metrics["total_items"] += len(collection_result.data)
        
        self.logger.log_pipeline_operation(
            "processing_start",
            {
                "total_collectors": processing_metrics["total_collectors"],
                "total_items": processing_metrics["total_items"],
                "processor": self.text_processor.__class__.__name__,
                "correlation_id": processing_metrics["correlation_id"]
            }
        )
        
        for collector_name, collection_result in collection_results.items():
            if not collection_result.success or not collection_result.data:
                self.logger.log_pipeline_operation(
                    "collector_skipped",
                    {
                        "collector": collector_name,
                        "reason": "no_data" if not collection_result.data else "collection_failed",
                        "correlation_id": processing_metrics["correlation_id"]
                    }
                )
                continue
            
            collector_start = datetime.utcnow()
            collector_items = len(collection_result.data)
            collector_processed = 0
            collector_errors = 0
            
            self.logger.log_pipeline_operation(
                "collector_processing_start",
                {
                    "collector": collector_name,
                    "items_count": collector_items,
                    "correlation_id": processing_metrics["correlation_id"]
                }
            )
            
            # Process in batches to avoid memory issues
            batch_size = 50
            for i in range(0, len(collection_result.data), batch_size):
                if self._cancel_requested:
                    self.logger.log_pipeline_operation(
                        "processing_cancelled",
                        {
                            "collector": collector_name,
                            "processed_items": collector_processed,
                            "correlation_id": processing_metrics["correlation_id"]
                        }
                    )
                    break
                
                batch = collection_result.data[i:i + batch_size]
                batch_start = datetime.utcnow()
                
                try:
                    batch_results = self.text_processor.process_batch(batch)
                    # Attach original raw_data to each processing result
                    for result, raw_data in zip(batch_results, batch):
                        result.raw_data = raw_data  # Add raw_data reference
                    processing_results.extend(batch_results)
                    collector_processed += len(batch)
                    processing_metrics["processed_items"] += len(batch)
                    
                    # Log batch processing metrics
                    batch_time = (datetime.utcnow() - batch_start).total_seconds()
                    self.logger.log_performance_metric(
                        "batch_processed",
                        {
                            "collector": collector_name,
                            "batch_size": len(batch),
                            "batch_processing_time": batch_time,
                            "items_per_second": len(batch) / batch_time if batch_time > 0 else 0,
                            "correlation_id": processing_metrics["correlation_id"]
                        }
                    )
                    
                except Exception as e:
                    collector_errors += len(batch)
                    processing_metrics["error_count"] += len(batch)
                    
                    self.logger.log_error(
                        "batch_processing_failed",
                        {
                            "collector": collector_name,
                            "batch_size": len(batch),
                            "error": str(e),
                            "error_type": type(e).__name__,
                            "correlation_id": processing_metrics["correlation_id"]
                        }
                    )
            
            # Log collector completion metrics
            collector_time = (datetime.utcnow() - collector_start).total_seconds()
            collector_success_rate = collector_processed / collector_items if collector_items > 0 else 0
            
            self.logger.log_pipeline_operation(
                "collector_processing_complete",
                {
                    "collector": collector_name,
                    "total_items": collector_items,
                    "processed_items": collector_processed,
                    "error_count": collector_errors,
                    "success_rate": collector_success_rate,
                    "processing_time_seconds": collector_time,
                    "correlation_id": processing_metrics["correlation_id"]
                }
            )
            
            processing_metrics["processed_collectors"] += 1
        
        # Calculate and log final processing metrics
        processing_metrics["processing_end"] = datetime.utcnow()
        processing_metrics["total_processing_time"] = (
            processing_metrics["processing_end"] - processing_metrics["processing_start"]
        ).total_seconds()
        processing_metrics["success_rate"] = (
            processing_metrics["processed_items"] / processing_metrics["total_items"] 
            if processing_metrics["total_items"] > 0 else 0
        )
        processing_metrics["items_per_second"] = (
            processing_metrics["processed_items"] / processing_metrics["total_processing_time"]
            if processing_metrics["total_processing_time"] > 0 else 0
        )
        
        self.logger.log_pipeline_operation(
            "processing_complete",
            {
                "total_collectors": processing_metrics["total_collectors"],
                "processed_collectors": processing_metrics["processed_collectors"],
                "total_items": processing_metrics["total_items"],
                "processed_items": processing_metrics["processed_items"],
                "error_count": processing_metrics["error_count"],
                "success_rate": processing_metrics["success_rate"],
                "total_processing_time_seconds": processing_metrics["total_processing_time"],
                "items_per_second": processing_metrics["items_per_second"],
                "correlation_id": processing_metrics["correlation_id"]
            }
        )
        
        return processing_results
    
    async def _store_data(
        self, 
        processing_results: List[ProcessingResult], 
        config: PipelineConfig
    ) -> int:
        """Store processed data to database using proper session management"""
        stored_count = 0
        
        # Complete data storage implementation using async repositories with proper session management
        try:
            correlation_id = f"storage_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            self.logger.log_pipeline_operation(
                "storage_start", 
                {"total_results": len(processing_results), "correlation_id": correlation_id}
            )
            
            # Process each result using async repositories with proper session lifecycle
            from ..data_access.database.connection import get_db_session
            
            for result in processing_results:
                try:
                    # Use proper async session context manager for each record
                    async with get_db_session() as session:
                        # Create repositories with the managed session
                        sentiment_repository = SentimentDataRepository(session)
                        stock_repository = StockRepository(session)
                        
                        # Get or create stock record using repository
                        stock = await stock_repository.get_by_symbol(result.stock_symbol)
                        if not stock:
                            stock_data = {
                                "symbol": result.stock_symbol,
                                "name": f"{result.stock_symbol} Corp"  # Default name
                            }
                            stock = await stock_repository.create(stock_data)
                        
                        # Determine sentiment label based on score
                        def get_sentiment_label(score: float) -> str:
                            if score >= 0.1:
                                return "Positive"
                            elif score <= -0.1:
                                return "Negative"
                            else:
                                return "Neutral"
                        
                        # Create sentiment record using repository
                        sentiment_data = {
                            "stock_id": stock.id,
                            "source": result.source.lower(),
                            "sentiment_score": result.sentiment_score,
                            "confidence": result.confidence,
                            "sentiment_label": get_sentiment_label(result.sentiment_score),
                            "model_used": getattr(result, 'model_used', 'unknown'),
                            "raw_text": result.raw_text[:5000] if result.raw_text else None,  # Limit text size
                            "extra_data": {
                                "processed_at": result.timestamp.isoformat() if result.timestamp else None,
                                "processor_version": "1.0",
                                "correlation_id": correlation_id,
                                "label": getattr(result, 'label', None),
                                "source_url": getattr(result, 'source_url', None),
                                "content_type": getattr(result, 'content_type', None),
                                "original_timestamp": getattr(result, 'original_timestamp', None)
                            }
                        }
                        
                        await sentiment_repository.create(sentiment_data)
                        stored_count += 1
                        # Session automatically commits and closes due to context manager
                        
                except Exception as e:
                    self.logger.log_error(
                        "sentiment_record_storage_error",
                        {"stock_symbol": result.stock_symbol, "error": str(e)}
                    )
                    continue
            
            # Log success metrics
            self.logger.log_pipeline_operation(
                "storage_complete",
                {
                    "total_processed": len(processing_results),
                    "successfully_stored": stored_count,
                    "correlation_id": correlation_id,
                    "storage_rate": stored_count / len(processing_results) if processing_results else 0
                }
            )
                
        except Exception as e:
            self.logger.log_error(
                "storage_operation_failed",
                {
                    "error": str(e),
                    "total_results": len(processing_results),
                    "stored_count": stored_count
                }
            )
        
        return stored_count

    async def _store_raw_data(self, collection_results: Dict[str, CollectionResult], correlation_id: str) -> int:
        """
        Store raw news articles and Reddit posts in their respective tables.
        
        Args:
            collection_results: Results from data collection
            correlation_id: Pipeline execution ID for tracking
            
        Returns:
            Number of raw data items stored
        """
        stored_count = 0
        
        try:
            # Process each collection result
            for source_name, collection_result in collection_results.items():
                if not collection_result.success or not collection_result.data:
                    continue
                
                for raw_data in collection_result.data:
                    try:
                        async with get_db() as session:
                            # Determine stock from raw data
                            stock_symbol = getattr(raw_data, 'stock_symbol', None)
                            if not stock_symbol:
                                continue
                            
                            # Get or create stock record
                            from ..data_access.repositories.stock_repository import StockRepository
                            stock_repository = StockRepository(session)
                            stock = await stock_repository.get_by_symbol(stock_symbol)
                            
                            if not stock:
                                stock_data = {
                                    "symbol": stock_symbol,
                                    "name": f"{stock_symbol} Corp"  # Default name
                                }
                                stock = await stock_repository.create(stock_data)
                            
                            # Store based on source type
                            if source_name.lower() in ['newsapi', 'marketaux', 'finnhub']:
                                # Store as news article
                                news_article = NewsArticle(
                                    stock_id=stock.id,
                                    title=getattr(raw_data, 'title', '')[:500],  # Limit title length
                                    content=getattr(raw_data, 'content', '')[:10000],  # Limit content length
                                    url=getattr(raw_data, 'url', ''),
                                    source=source_name.lower(),
                                    published_at=getattr(raw_data, 'published_at', None),
                                    author=getattr(raw_data, 'author', ''),
                                    content_hash=getattr(raw_data, 'content_hash', ''),
                                    extra_data={
                                        "pipeline_id": correlation_id,
                                        "collected_at": datetime.utcnow().isoformat(),
                                        "original_data": {
                                            "description": getattr(raw_data, 'description', ''),
                                            "category": getattr(raw_data, 'category', ''),
                                            "language": getattr(raw_data, 'language', '')
                                        }
                                    }
                                )
                                session.add(news_article)
                                
                            elif source_name.lower() == 'reddit':
                                # Store as Reddit post
                                reddit_post = RedditPost(
                                    stock_id=stock.id,
                                    post_id=getattr(raw_data, 'post_id', ''),
                                    title=getattr(raw_data, 'title', '')[:500],  # Limit title length
                                    content=getattr(raw_data, 'content', '')[:10000],  # Limit content length
                                    url=getattr(raw_data, 'url', ''),
                                    subreddit=getattr(raw_data, 'subreddit', ''),
                                    author=getattr(raw_data, 'author', ''),
                                    score=getattr(raw_data, 'score', 0),
                                    num_comments=getattr(raw_data, 'num_comments', 0),
                                    created_utc=getattr(raw_data, 'created_utc', None),
                                    content_hash=getattr(raw_data, 'content_hash', ''),
                                    extra_data={
                                        "pipeline_id": correlation_id,
                                        "collected_at": datetime.utcnow().isoformat(),
                                        "original_data": {
                                            "upvote_ratio": getattr(raw_data, 'upvote_ratio', 0.0),
                                            "distinguished": getattr(raw_data, 'distinguished', None),
                                            "stickied": getattr(raw_data, 'stickied', False),
                                            "is_self": getattr(raw_data, 'is_self', False)
                                        }
                                    }
                                )
                                session.add(reddit_post)
                            
                            await session.commit()
                            stored_count += 1
                            
                    except Exception as e:
                        self.logger.error(
                            f"Error storing raw data item from {source_name}: {e}",
                            extra={
                                "source": source_name,
                                "correlation_id": correlation_id,
                                "error": str(e)
                            }
                        )
                        continue
            
            # Log success metrics
            self.logger.log_pipeline_operation(
                "raw_data_storage_complete",
                {
                    "total_stored": stored_count,
                    "correlation_id": correlation_id,
                    "sources_processed": list(collection_results.keys())
                }
            )
                
        except Exception as e:
            self.logger.log_error(
                "raw_data_storage_operation_failed",
                {
                    "error": str(e),
                    "correlation_id": correlation_id,
                    "stored_count": stored_count
                }
            )
        
        return stored_count
    
    def _build_collector_stats(self, collection_results: Dict[str, CollectionResult]) -> List[CollectorStats]:
        """Build collector statistics"""
        stats = []
        
        for collector_name, result in collection_results.items():
            stat = CollectorStats(
                name=collector_name,
                enabled=True,
                success=result.success,
                items_collected=result.items_collected,
                execution_time=result.execution_time,
                error_message=result.error_message
            )
            stats.append(stat)
        
        return stats
    
    def _build_processing_stats(self, processing_results: List[ProcessingResult]) -> Dict[str, Any]:
        """Build processing statistics"""
        if not processing_results:
            return {}
        
        successful = [r for r in processing_results if r.success]
        failed = [r for r in processing_results if not r.success]
        
        avg_processing_time = sum(r.processing_time for r in processing_results) / len(processing_results)
        
        return {
            "total_processed": len(processing_results),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(processing_results) if processing_results else 0,
            "average_processing_time": avg_processing_time,
            "total_processing_time": sum(r.processing_time for r in processing_results)
        }
    
    def cancel_pipeline(self) -> None:
        """Cancel the currently running pipeline"""
        self._cancel_requested = True
        self.logger.info("Pipeline cancellation requested")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            "status": self.current_status.value,
            "current_result": self.current_result.__dict__ if self.current_result else None,
            "available_collectors": list(self._collectors.keys()),
            "rate_limiter_status": self.rate_limiter.get_all_status()
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on all components"""
        health_status = {
            "pipeline": "healthy",
            "collectors": {},
            "rate_limiter": "healthy",
            "text_processor": "healthy",
            "sentiment_engine": {}
        }
        
        # Check collectors
        for name, collector in self._collectors.items():
            try:
                collector_health = await collector.health_check()
                health_status["collectors"][name] = collector_health
            except Exception as e:
                health_status["collectors"][name] = {
                    "healthy": False,
                    "error": str(e)
                }
        
        # Check sentiment engine
        try:
            sentiment_health = await self.sentiment_engine.health_check()
            health_status["sentiment_engine"] = sentiment_health
        except Exception as e:
            health_status["sentiment_engine"] = {
                "status": "error",
                "error": str(e)
            }
        
        return health_status
    
    # Sentiment Analysis Integration Methods
    
    async def _analyze_sentiment(self, processing_results: List[ProcessingResult], config: PipelineConfig) -> List['SentimentAnalysisResult']:
        """
        Analyze sentiment for processed text data.
        
        Args:
            processing_results: Results from text processing step
            config: Pipeline configuration
            
        Returns:
            List of sentiment analysis results
        """
        self.logger.info("Starting sentiment analysis...")
        
        # Initialize sentiment engine if not already done
        if not self.sentiment_engine.is_initialized:
            await self.sentiment_engine.initialize()
        
        sentiment_results = []
        
        # Convert processing results to TextInput objects for sentiment analysis
        text_inputs = []
        result_mapping = {}  # Map TextInput to ProcessingResult
        
        for proc_result in processing_results:
            if not proc_result.success or not proc_result.processed_text:
                continue
            
            # FIXED: raw_data.source is already a DataSource enum, no mapping needed!
            data_source = proc_result.raw_data.source
            
            text_input = TextInput(
                text=proc_result.processed_text,
                source=data_source,
                stock_symbol=proc_result.raw_data.stock_symbol,
                timestamp=proc_result.raw_data.timestamp,
                metadata={
                    'collector': proc_result.raw_data.source,
                    'url': getattr(proc_result.raw_data, 'url', None),
                    'title': getattr(proc_result.raw_data, 'title', None)
                }
            )
            
            text_inputs.append(text_input)
            result_mapping[id(text_input)] = proc_result
        
        if not text_inputs:
            self.logger.warning("No valid texts found for sentiment analysis")
            return sentiment_results
        
        try:
            # Perform sentiment analysis in batches
            self.logger.info(f"Analyzing sentiment for {len(text_inputs)} texts...")
            sentiment_scores = await self.sentiment_engine.analyze(text_inputs)
            
            # Create sentiment analysis results
            for text_input, sentiment_score in zip(text_inputs, sentiment_scores):
                proc_result = result_mapping[id(text_input)]
                
                sentiment_result = SentimentAnalysisResult(
                    raw_data=proc_result.raw_data,
                    processing_result=proc_result,
                    sentiment_result=sentiment_score,
                    success=True,
                    timestamp=datetime.utcnow()
                )
                
                sentiment_results.append(sentiment_result)
            
            self.logger.info(f"Sentiment analysis completed for {len(sentiment_results)} items")
            
        except Exception as e:
            self.logger.error(f"Sentiment analysis failed: {str(e)}")
            
            # Create failed results for tracking
            for text_input in text_inputs:
                proc_result = result_mapping[id(text_input)]
                
                sentiment_result = SentimentAnalysisResult(
                    raw_data=proc_result.raw_data,
                    processing_result=proc_result,
                    sentiment_result=None,
                    success=False,
                    error=str(e),
                    timestamp=datetime.utcnow()
                )
                
                sentiment_results.append(sentiment_result)
        
        return sentiment_results
    
    def _map_collector_to_data_source(self, collector_source) -> DataSource:
        """Map collector source to DataSource enum."""
        # If it's already a DataSource enum, return it directly
        if isinstance(collector_source, DataSource):
            return collector_source
            
        # If it's a string, map it to DataSource enum
        if isinstance(collector_source, str):
            collector_mapping = {
                'reddit': DataSource.REDDIT,
                'finnhub': DataSource.FINNHUB,
                'newsapi': DataSource.NEWSAPI,
                'marketaux': DataSource.MARKETAUX
            }
            return collector_mapping.get(collector_source.lower(), DataSource.NEWS)
        
        # Default fallback
        return DataSource.NEWS
    

    
    async def _store_sentiment_data(self, sentiment_results: List['SentimentAnalysisResult'], config: PipelineConfig) -> int:
        """
        Store sentiment analysis results in the database using proper session management.
        
        Args:
            sentiment_results: Results from sentiment analysis
            config: Pipeline configuration
            
        Returns:
            Number of records stored
        """
        stored_count = 0
        
        try:
            from ..data_access.database.connection import get_db_session
            
            for sentiment_result in sentiment_results:
                if not sentiment_result.success or not sentiment_result.sentiment_result:
                    continue
                
                # First ensure stock exists and get its ID
                stock_symbol = sentiment_result.raw_data.stock_symbol
                if not stock_symbol:
                    continue
                
                try:
                    # Use proper async session context manager for each record
                    async with get_db_session() as session:
                        # Create repositories with the managed session
                        sentiment_repository = SentimentDataRepository(session)
                        stock_repository = StockRepository(session)
                        
                        # Find or create stock record
                        stock = await stock_repository.get_by_symbol(stock_symbol)
                        if not stock:
                            stock_data = {
                                'symbol': stock_symbol.upper(),
                                'name': stock_symbol.upper(),  # For now, use symbol as company name
                                'sector': 'Unknown'
                            }
                            stock = await stock_repository.create(stock_data)
                        
                        # Generate content hash for duplicate detection
                        source_str = str(sentiment_result.raw_data.source.value) if hasattr(sentiment_result.raw_data.source, 'value') else str(sentiment_result.raw_data.source)
                        content_hash = SentimentData.generate_content_hash(
                            sentiment_result.processing_result.processed_text,
                            source_str,
                            stock_symbol
                        )
                        
                        # Check for duplicates
                        if await sentiment_repository.exists_by_content_hash(stock.id, source_str, content_hash):
                            continue  # Skip duplicate content
                        
                        # Determine sentiment label based on score
                        def get_sentiment_label(score: float) -> str:
                            if score >= 0.1:
                                return "Positive"
                            elif score <= -0.1:
                                return "Negative"
                            else:
                                return "Neutral"
                        
                        # Convert to database model format (now with proper model_used column)
                        sentiment_data = {
                            'stock_id': stock.id,
                            'source': source_str,
                            'sentiment_score': sentiment_result.sentiment_result.score,
                            'confidence': sentiment_result.sentiment_result.confidence,
                            'sentiment_label': get_sentiment_label(sentiment_result.sentiment_result.score),
                            'model_used': sentiment_result.sentiment_result.model_name,  # Use actual model name from result
                            'raw_text': sentiment_result.processing_result.processed_text[:1000],  # First 1000 chars
                            'content_hash': content_hash,  # Add content hash for duplicate prevention
                            'extra_data': {
                                'label': sentiment_result.sentiment_result.label.value if hasattr(sentiment_result.sentiment_result.label, 'value') else str(sentiment_result.sentiment_result.label),
                                'source_url': getattr(sentiment_result.raw_data, 'url', None),
                                'content_type': getattr(sentiment_result.raw_data, 'content_type', 'text'),
                                'original_timestamp': sentiment_result.raw_data.timestamp.isoformat() if sentiment_result.raw_data.timestamp else None
                            }
                        }
                        
                        # Store using repository with proper session management
                        await sentiment_repository.create(sentiment_data)
                        stored_count += 1
                        # Session automatically commits and closes due to context manager
                        
                except Exception as e:
                    self.logger.error(f"Failed to store sentiment record for {stock_symbol}: {e}")
                    continue
            
            self.logger.info(f"Stored {stored_count} sentiment records")
            
        except Exception as e:
            self.logger.error(f"Failed to store sentiment data: {str(e)}")
            raise
        
        return stored_count
    
    def _build_sentiment_stats(self, sentiment_results: List['SentimentAnalysisResult']) -> Dict[str, Any]:
        """Build sentiment analysis statistics."""
        if not sentiment_results:
            return {}
        
        successful_results = [r for r in sentiment_results if r.success and r.sentiment_result]
        
        if not successful_results:
            return {
                'total_analyzed': 0,
                'success_count': 0,
                'error_count': len(sentiment_results),
                'success_rate': 0.0
            }
        
        # Calculate label distribution
        label_counts = {}
        model_usage = {}
        total_processing_time = 0.0
        
        for result in successful_results:
            sentiment = result.sentiment_result
            
            # Count labels
            label = sentiment.label.value
            label_counts[label] = label_counts.get(label, 0) + 1
            
            # Count model usage
            model = sentiment.model_name
            model_usage[model] = model_usage.get(model, 0) + 1
            
            # Sum processing time
            total_processing_time += sentiment.processing_time
        
        return {
            'total_analyzed': len(sentiment_results),
            'success_count': len(successful_results),
            'error_count': len(sentiment_results) - len(successful_results),
            'success_rate': (len(successful_results) / len(sentiment_results)) * 100,
            'label_distribution': label_counts,
            'model_usage': model_usage,
            'avg_processing_time': total_processing_time / len(successful_results) if successful_results else 0.0,
            'total_processing_time': total_processing_time
        }
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the pipeline and cleanup resources."""
        self.logger.info("Shutting down data pipeline...")
        
        # Cancel any running pipeline
        if self.current_status == PipelineStatus.RUNNING:
            self._cancel_requested = True
            self.logger.info("Cancelling running pipeline...")
        
        # Shutdown sentiment engine
        try:
            await self.sentiment_engine.shutdown()
        except Exception as e:
            self.logger.error(f"Error during sentiment engine shutdown: {e}")
        
        # Reset state
        self.current_status = PipelineStatus.IDLE
        self.current_result = None
        
        self.logger.info("Data pipeline shutdown complete")
    
    async def run_full_pipeline(self, symbols: List[str], lookback_days: int = 7) -> Dict[str, Any]:
        """
        Run the complete pipeline for scheduled jobs.
        
        This is the FULL PIPELINE that does everything:
        1. Data Collection from all sources
        2. Sentiment Analysis processing  
        3. Database storage
        4. Data validation and cleanup
        
        Args:
            symbols: List of stock symbols to process
            lookback_days: Number of days to look back for data
            
        Returns:
            Dict with execution results
        """
        try:
            # Create pipeline configuration
            date_range = DateRange.last_days(lookback_days)
            config = PipelineConfig(
                symbols=symbols,
                date_range=date_range,
                max_items_per_symbol=100,
                include_reddit=True,
                include_finnhub=True,
                include_newsapi=True,
                include_marketaux=True,
                parallel_collectors=True
            )
            
            self.logger.info(f"🚀 Starting FULL PIPELINE for {len(symbols)} symbols, {lookback_days} days lookback")
            
            # Execute the complete pipeline
            result = await self.run_pipeline(config)
            
            if result.status == PipelineStatus.COMPLETED:
                return {
                    "status": "success",
                    "pipeline_id": result.pipeline_id,
                    "items_collected": result.total_items,
                    "sentiment_records": result.sentiment_records_created,
                    "execution_time": result.execution_time,
                    "symbols_processed": len(symbols)
                }
            else:
                return {
                    "status": "error",
                    "error": result.error_message or "Pipeline execution failed"
                }
                
        except Exception as e:
            self.logger.error(f"Full pipeline execution failed: {str(e)}")
            return {
                "status": "error", 
                "error": str(e)
            }
    
    async def process_recent_data(self, symbols: List[str], hours_back: int = 24) -> Dict[str, Any]:
        """
        Process recent data for sentiment analysis (lighter than full pipeline).
        
        This is SENTIMENT PROCESSING ONLY:
        1. Processes existing data from database
        2. Runs sentiment analysis on unprocessed items
        3. Updates sentiment records
        4. Does NOT collect new data
        
        Args:
            symbols: List of stock symbols to process
            hours_back: Hours to look back for unprocessed data
            
        Returns:
            Dict with processing results
        """
        try:
            self.logger.info(f"🧠 Starting SENTIMENT PROCESSING for {len(symbols)} symbols, {hours_back} hours back")
            
            # This would process existing data from database for sentiment analysis
            # For now, return success (in production, implement actual recent data processing)
            
            processed_count = 0
            sentiment_records = 0
            
            # TODO: Implement actual recent data processing
            # 1. Query database for unprocessed items in last N hours
            # 2. Run sentiment analysis on those items
            # 3. Update sentiment records
            # 4. Return processing statistics
            
            return {
                "status": "success",
                "items_processed": processed_count,
                "sentiment_records": sentiment_records,
                "symbols_processed": len(symbols),
                "hours_back": hours_back
            }
            
        except Exception as e:
            self.logger.error(f"Recent data processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }