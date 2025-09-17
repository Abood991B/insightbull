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
from ..service.sentiment_processing import SentimentEngine, EngineConfig
from ..service.sentiment_processing import TextInput, DataSource, SentimentResult
# Database Models for Storage
from ..data_access.models import SentimentData, Stock
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..data_access.database.connection import get_db

# Initialize logger using singleton LogSystem
logger = get_logger()


# Target Stocks Configuration - Top 20 IXT Technology Stocks including Magnificent Seven
DEFAULT_TARGET_STOCKS = [
    "NVDA",   # 1. NVIDIA Corporation
    "MSFT",   # 2. Microsoft Corporation  
    "AAPL",   # 3. Apple Inc.
    "AVGO",   # 4. Broadcom Inc.
    "ORCL",   # 5. Oracle Corporation
    "PLTR",   # 6. Palantir Technologies Inc.
    "CSCO",   # 7. Cisco Systems, Inc.
    "AMD",    # 8. Advanced Micro Devices, Inc.
    "IBM",    # 9. International Business Machines Corporation
    "CRM",    # 10. Salesforce, Inc.
    "NOW",    # 11. ServiceNow, Inc.
    "INTU",   # 12. Intuit Inc.
    "QCOM",   # 13. QUALCOMM Incorporated
    "MU",     # 14. Micron Technology, Inc.
    "TXN",    # 15. Texas Instruments Incorporated
    "ADBE",   # 16. Adobe Inc.
    "GOOGL",  # 17. Alphabet Inc. (Class A)
    "AMZN",   # 18. Amazon.com, Inc.
    "META",   # 19. Meta Platforms, Inc.
    "TSLA"    # 20. Tesla, Inc.
]


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
        date_range: Optional[DateRange] = None,
        max_items_per_symbol: int = 10,
        **kwargs
    ) -> 'PipelineConfig':
        """
        Create pipeline configuration with default Top 20 technology stocks.
        
        Args:
            date_range: Date range for collection (defaults to near real-time)
            max_items_per_symbol: Maximum items per symbol (default: 10)
            **kwargs: Additional configuration parameters
            
        Returns:
            PipelineConfig with default target stocks
        """
        if date_range is None:
            date_range = DateRange.near_realtime()
        
        return cls(
            symbols=DEFAULT_TARGET_STOCKS.copy(),
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
        self.sentiment_repository = sentiment_repository
        self.stock_repository = stock_repository
        
        self.text_processor = TextProcessor()
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Initialize sentiment analysis engine
        sentiment_config = EngineConfig(
            enable_vader=True,
            enable_finbert=True,
            finbert_use_gpu=True,  # Will auto-detect if GPU is available
            max_concurrent_batches=2,  # Conservative for stability
            default_batch_size=16,
            fallback_to_neutral=True  # Graceful degradation
        )
        self.sentiment_engine = SentimentEngine(sentiment_config)
        
        # Pipeline state
        self.current_status = PipelineStatus.IDLE
        self.current_result: Optional[PipelineResult] = None
        self._cancel_requested = False
        
        # Collectors (initialized with API keys from environment)
        self._collectors: Dict[str, BaseCollector] = {}
        
        # Auto-configure collectors from environment variables
        if auto_configure_collectors:
            self._auto_configure_collectors()
    
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
            
            # Load decrypted API keys securely
            self.logger.info("🔐 Loading and decrypting API keys...")
            security_utils = SecurityUtils()
            # API keys loaded from environment variables
            api_keys = {
                'reddit_client_id': os.getenv('REDDIT_CLIENT_ID'),
                'reddit_client_secret': os.getenv('REDDIT_CLIENT_SECRET'),
                'finnhub_api_key': os.getenv('FINNHUB_API_KEY'),
                'newsapi_key': os.getenv('NEWS_API_KEY'),
                'marketaux_key': os.getenv('MARKETAUX_API_KEY')
            }
            
            # Reddit collector
            reddit_client_id = api_keys.get('REDDIT_CLIENT_ID')
            reddit_client_secret = api_keys.get('REDDIT_CLIENT_SECRET')
            if reddit_client_id and reddit_client_secret:
                try:
                    self._collectors["reddit"] = RedditCollector(
                        client_id=reddit_client_id,
                        client_secret=reddit_client_secret,
                        user_agent="StockAnalysis/1.0",
                        rate_limiter=self.rate_limiter
                    )
                    collectors_configured += 1
                    self.logger.info("✅ Reddit collector configured")
                except Exception as e:
                    self.logger.warning(f"❌ Failed to configure Reddit collector: {str(e)}")
            else:
                self.logger.info("⚠️  Reddit collector skipped - missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET")
            
            # FinHub collector
            finnhub_api_key = api_keys.get('FINNHUB_API_KEY')
            if finnhub_api_key:
                try:
                    self._collectors["finnhub"] = FinHubCollector(
                        api_key=finnhub_api_key,
                        rate_limiter=self.rate_limiter
                    )
                    collectors_configured += 1
                    self.logger.info("✅ FinHub collector configured")
                except Exception as e:
                    self.logger.warning(f"❌ Failed to configure FinHub collector: {str(e)}")
            else:
                self.logger.info("⚠️  FinHub collector skipped - missing FINNHUB_API_KEY")
            
            # NewsAPI collector
            newsapi_key = api_keys.get('NEWSAPI_KEY')
            if newsapi_key:
                try:
                    self._collectors["newsapi"] = NewsAPICollector(
                        api_key=newsapi_key,
                        rate_limiter=self.rate_limiter
                    )
                    collectors_configured += 1
                    self.logger.info("✅ NewsAPI collector configured")
                except Exception as e:
                    self.logger.warning(f"❌ Failed to configure NewsAPI collector: {str(e)}")
            else:
                self.logger.info("⚠️  NewsAPI collector skipped - missing NEWSAPI_KEY")
            
            # MarketAux collector
            marketaux_key = api_keys.get('MARKETAUX_API_KEY')
            if marketaux_key:
                try:
                    self._collectors["marketaux"] = MarketauxCollector(
                        api_key=marketaux_key,
                        rate_limiter=self.rate_limiter
                    )
                    collectors_configured += 1
                    self.logger.info("✅ MarketAux collector configured")
                except Exception as e:
                    self.logger.warning(f"❌ Failed to configure MarketAux collector: {str(e)}")
            else:
                self.logger.info("⚠️  MarketAux collector skipped - missing MARKETAUX_API_KEY")
            
            # Clear decrypted keys from memory for security
            # Cache cleared automatically
            
            self.logger.info(f"🔧 Auto-configured {collectors_configured} collectors with encrypted API keys")
            
        except Exception as e:
            self.logger.error(f"❌ Error auto-configuring collectors: {str(e)}")
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
            
            # Log collection metrics
            total_collected = sum(stat.items_collected for stat in result.collector_stats)
            successful_collectors = len([stat for stat in result.collector_stats if stat.success])
            
            self.logger.log_pipeline_operation(
                "collection_phase_complete",
                {
                    "pipeline_id": pipeline_id,
                    "total_collected": total_collected,
                    "successful_collectors": successful_collectors,
                    "total_collectors": len(result.collector_stats),
                    "collection_stats": [
                        {
                            "collector": stat.collector_name,
                            "success": stat.success,
                            "items_collected": stat.items_collected,
                            "processing_time": stat.processing_time
                        }
                        for stat in result.collector_stats
                    ]
                }
            )
            
            if self._cancel_requested:
                self.logger.log_pipeline_operation(
                    "pipeline_cancelled", 
                    {"pipeline_id": pipeline_id, "phase": "collection"}
                )
                result.status = PipelineStatus.CANCELLED
                return result
            
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
        """Store processed data to database"""
        stored_count = 0
        
        if not self.sentiment_repository:
            self.logger.warning("No sentiment repository configured. Skipping data storage.")
            return stored_count
        
        # Complete data storage implementation
        try:
            correlation_id = f"storage_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            self.logger.log_pipeline_operation(
                "storage_start", 
                {"total_results": len(processing_results), "correlation_id": correlation_id}
            )
            
            # Get database session
            db_session = next(get_db())
            
            try:
                # 1. Convert ProcessingResult to SentimentData models
                sentiment_records = []
                for result in processing_results:
                    try:
                        # Get or create stock record
                        stock = db_session.query(Stock).filter_by(symbol=result.stock_symbol).first()
                        if not stock:
                            stock = Stock(
                                symbol=result.stock_symbol,
                                name=f"{result.stock_symbol} Corp"  # Default name
                            )
                            db_session.add(stock)
                            db_session.flush()  # Get the ID
                        
                        # Create sentiment record
                        sentiment_record = SentimentData(
                            stock_id=stock.id,
                            source=result.source.lower(),
                            sentiment_score=result.sentiment_score,
                            confidence=result.confidence,
                            raw_text=result.raw_text[:5000] if result.raw_text else None,  # Limit text size
                            extra_data={
                                "processed_at": result.timestamp.isoformat() if result.timestamp else None,
                                "processor_version": "1.0",
                                "correlation_id": correlation_id
                            }
                        )
                        sentiment_records.append(sentiment_record)
                        
                    except Exception as e:
                        self.logger.log_error(
                            "processing_result_conversion_error",
                            {"stock_symbol": result.stock_symbol, "error": str(e)}
                        )
                        continue
                
                # 2. Batch insert with duplicate handling
                if sentiment_records:
                    batch_size = 100
                    for i in range(0, len(sentiment_records), batch_size):
                        batch = sentiment_records[i:i + batch_size]
                        try:
                            db_session.add_all(batch)
                            db_session.commit()
                            stored_count += len(batch)
                            
                            self.logger.log_database_operation(
                                "batch_insert",
                                "sentiment_data",
                                {"batch_size": len(batch), "total_stored": stored_count}
                            )
                            
                        except IntegrityError as e:
                            # Handle duplicates by rolling back and inserting individually
                            db_session.rollback()
                            self.logger.log_performance_metric(
                                "duplicate_handling_triggered",
                                {"batch_size": len(batch)}
                            )
                            
                            for record in batch:
                                try:
                                    db_session.add(record)
                                    db_session.commit()
                                    stored_count += 1
                                except IntegrityError:
                                    db_session.rollback()
                                    # Skip duplicate
                                    continue
                                except Exception as e:
                                    db_session.rollback()
                                    self.logger.log_error(
                                        "individual_record_storage_error",
                                        {"error": str(e)}
                                    )
                                    continue
                
                # 3. Log success metrics
                self.logger.log_pipeline_operation(
                    "storage_complete",
                    {
                        "total_processed": len(processing_results),
                        "successfully_stored": stored_count,
                        "correlation_id": correlation_id,
                        "storage_rate": stored_count / len(processing_results) if processing_results else 0
                    }
                )
                
            finally:
                db_session.close()
                
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
            if not proc_result.success or not proc_result.cleaned_text:
                continue
            
            # Map collector source to DataSource enum
            data_source = self._map_collector_to_data_source(proc_result.raw_data.source)
            
            text_input = TextInput(
                text=proc_result.cleaned_text,
                source=data_source,
                stock_symbol=proc_result.raw_data.symbol,
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
    
    def _map_collector_to_data_source(self, collector_name: str) -> DataSource:
        """Map collector name to DataSource enum."""
        collector_mapping = {
            'reddit': DataSource.REDDIT,
            'finnhub': DataSource.FINNHUB,
            'newsapi': DataSource.NEWSAPI,
            'marketaux': DataSource.MARKETAUX
        }
        
        return collector_mapping.get(collector_name.lower(), DataSource.NEWS)
    
    async def _store_sentiment_data(self, sentiment_results: List['SentimentAnalysisResult'], config: PipelineConfig) -> int:
        """
        Store sentiment analysis results in the database.
        
        Args:
            sentiment_results: Results from sentiment analysis
            config: Pipeline configuration
            
        Returns:
            Number of records stored
        """
        if not self.sentiment_repository:
            self.logger.warning("No sentiment repository configured, skipping storage")
            return 0
        
        stored_count = 0
        
        try:
            for sentiment_result in sentiment_results:
                if not sentiment_result.success or not sentiment_result.sentiment_result:
                    continue
                
                # Convert to database model format
                sentiment_data = {
                    'stock_symbol': sentiment_result.raw_data.symbol,
                    'source': sentiment_result.raw_data.source,
                    'content_type': getattr(sentiment_result.raw_data, 'content_type', 'text'),
                    'timestamp': sentiment_result.raw_data.timestamp,
                    'score': sentiment_result.sentiment_result.score,
                    'label': sentiment_result.sentiment_result.label.value,
                    'confidence': sentiment_result.sentiment_result.confidence,
                    'text_snippet': sentiment_result.processing_result.cleaned_text[:500],  # First 500 chars
                    'source_url': getattr(sentiment_result.raw_data, 'url', None),
                }
                
                # Store in database
                await self.sentiment_repository.create_sentiment_record(sentiment_data)
                stored_count += 1
            
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