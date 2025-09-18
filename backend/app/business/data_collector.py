"""
Data Collector - Business Layer Orchestration
==============================================

Coordinates data collection from multiple external sources as specified
in the FYP Implementation Plan Layer 2: Business Layer.

Implements the DataCollector component that orchestrates:
- Reddit data collection via PRAW
- Financial news from FinHub, Marketaux, NewsAPI
- Stock price data from Yahoo Finance
- Rate limiting and error handling
- Data preprocessing coordination

This component acts as the central coordinator for all data ingestion
operations in the sentiment analysis pipeline.
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import time

from app.infrastructure.collectors import (
    RedditCollector,
    FinHubCollector, 
    MarketauxCollector,
    NewsAPICollector
)
from app.infrastructure.rate_limiter import RateLimitHandler
from app.infrastructure.log_system import get_logger
from app.infrastructure.security.security_utils import SecurityUtils
from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader
from app.business.entities.dashboard_entities import StockInfo


@dataclass
class CollectionJob:
    """Represents a data collection job"""
    job_id: str
    symbols: List[str]
    sources: List[str]
    date_range: Dict[str, datetime]
    status: str = "pending"
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    results: Dict[str, Any] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.results is None:
            self.results = {}
        if self.errors is None:
            self.errors = []


class DataCollector:
    """
    Central coordinator for data collection operations.
    
    Implements the DataCollector component from FYP Implementation Plan
    Layer 2: Business Layer - coordinates data collection from multiple sources.
    """
    
    def __init__(self):
        """Initialize the data collector with configured collectors"""
        self.logger = get_logger()
        self.rate_limiter = RateLimitHandler()
        self.security = SecurityUtils()
        
        # Initialize secure API key loader with encryption/decryption
        self.secure_loader = SecureAPIKeyLoader()
        
        # Log API key loading process
        self.logger.info("🔐 Loading and decrypting API keys...")
        
        # Initialize collectors with encrypted/decrypted credentials
        reddit_client_id = self.secure_loader.get_decrypted_key("REDDIT_CLIENT_ID")
        reddit_client_secret = self.secure_loader.get_decrypted_key("REDDIT_CLIENT_SECRET")
        
        if reddit_client_id and reddit_client_secret:
            self.reddit_collector = RedditCollector(
                client_id=reddit_client_id,
                client_secret=reddit_client_secret,
                user_agent="StockInsight/1.0",
                rate_limiter=self.rate_limiter
            )
            self.logger.info("✅ Reddit collector configured")
        else:
            self.reddit_collector = None
            self.logger.info("⚠️ Reddit collector skipped - missing REDDIT_CLIENT_ID or REDDIT_CLIENT_SECRET")
        
        finnhub_key = self.secure_loader.get_decrypted_key("FINNHUB_API_KEY")
        if finnhub_key:
            self.finnhub_collector = FinHubCollector(
                api_key=finnhub_key,
                rate_limiter=self.rate_limiter
            )
            self.logger.info("✅ FinHub collector configured")
        else:
            self.finnhub_collector = None
            self.logger.info("⚠️ FinHub collector skipped - missing FINNHUB_API_KEY")
        
        marketaux_key = self.secure_loader.get_decrypted_key("MARKETAUX_API_KEY")
        if marketaux_key:
            self.marketaux_collector = MarketauxCollector(
                api_key=marketaux_key,
                rate_limiter=self.rate_limiter
            )
            self.logger.info("✅ MarketAux collector configured")
        else:
            self.marketaux_collector = None
            self.logger.info("⚠️ MarketAux collector skipped - missing MARKETAUX_API_KEY")
        
        newsapi_key = self.secure_loader.get_decrypted_key("NEWSAPI_KEY")
        if newsapi_key:
            self.newsapi_collector = NewsAPICollector(
                api_key=newsapi_key,
                rate_limiter=self.rate_limiter
            )
            self.logger.info("✅ NewsAPI collector configured")
        else:
            self.newsapi_collector = None
            self.logger.info("⚠️ NewsAPI collector skipped - missing NEWSAPI_KEY")
        
        # Count active collectors
        active_collectors = sum(1 for collector in [
            self.reddit_collector, self.finnhub_collector, 
            self.marketaux_collector, self.newsapi_collector
        ] if collector is not None)
        
        self.logger.info(f"🔧 Auto-configured {active_collectors} collectors with encrypted API keys")
        
        self.active_jobs: Dict[str, CollectionJob] = {}
        
    async def collect_all_data(self, symbols: List[str], 
                              date_range: Dict[str, datetime]) -> CollectionJob:
        """
        Collect data from all sources for given symbols and date range.
        
        Args:
            symbols: List of stock symbols to collect data for
            date_range: Dictionary with 'start' and 'end' datetime keys
            
        Returns:
            CollectionJob with results and status
        """
        job_id = f"collection_{int(time.time())}"
        job = CollectionJob(
            job_id=job_id,
            symbols=symbols,
            sources=["reddit", "finnhub", "marketaux", "newsapi"],
            date_range=date_range,
            started_at=datetime.utcnow()
        )
        
        self.active_jobs[job_id] = job
        
        try:
            self.logger.info(
                f"Starting data collection job {job_id}",
                symbols=symbols,
                date_range=date_range,
                sources=job.sources
            )
            
            # Collect data from all sources concurrently
            collection_tasks = [
                self._collect_reddit_data(symbols, date_range),
                self._collect_finnhub_data(symbols, date_range),
                self._collect_marketaux_data(symbols, date_range),
                self._collect_newsapi_data(symbols, date_range)
            ]
            
            results = await asyncio.gather(*collection_tasks, return_exceptions=True)
            
            # Process results
            source_names = ["reddit", "finnhub", "marketaux", "newsapi"]
            for i, result in enumerate(results):
                source = source_names[i]
                if isinstance(result, Exception):
                    error_msg = f"Error collecting from {source}: {str(result)}"
                    job.errors.append(error_msg)
                    self.logger.error(error_msg, source=source, job_id=job_id)
                else:
                    job.results[source] = result
                    self.logger.info(
                        f"Successfully collected data from {source}",
                        source=source,
                        records_count=len(result) if result else 0,
                        job_id=job_id
                    )
            
            job.status = "completed" if job.results else "failed"
            job.completed_at = datetime.utcnow()
            
            duration = (job.completed_at - job.started_at).total_seconds()
            total_records = sum(len(data) if data else 0 for data in job.results.values())
            
            self.logger.log_pipeline_step(
                step="data_collection",
                status="success" if job.status == "completed" else "error",
                duration=duration,
                records_processed=total_records,
                job_id=job_id,
                sources_successful=len(job.results),
                errors_count=len(job.errors)
            )
            
        except Exception as e:
            job.status = "error"
            job.errors.append(f"Collection job failed: {str(e)}")
            job.completed_at = datetime.utcnow()
            
            self.logger.error(
                f"Data collection job {job_id} failed",
                error=str(e),
                job_id=job_id
            )
        
        return job
    
    async def _collect_reddit_data(self, symbols: List[str], 
                                  date_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """Collect Reddit data for symbols"""
        if not self.reddit_collector:
            return []
        
        try:
            await self.rate_limiter.acquire("reddit")
            
            # Import required classes
            from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
            
            # Create proper configuration
            date_range_obj = DateRange(
                start_date=date_range['start'],
                end_date=date_range['end']
            )
            config = CollectionConfig(
                symbols=symbols,
                date_range=date_range_obj,
                max_items_per_symbol=50,
                include_comments=True
            )
            
            # Use the standardized collect_data method
            result = await self.reddit_collector.collect_data(config)
            
            # Convert RawData objects to dictionaries
            return [
                {
                    'source': data.source.value,
                    'content_type': data.content_type,
                    'text': data.text,
                    'timestamp': data.timestamp,
                    'stock_symbol': data.stock_symbol,
                    'url': data.url,
                    'metadata': data.metadata or {}
                }
                for data in result.data
            ] if result.success else []
            
        except Exception as e:
            self.logger.error(f"Reddit collection failed: {str(e)}")
            raise
    
    async def _collect_finnhub_data(self, symbols: List[str], 
                                   date_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """Collect Finnhub news data"""
        if not self.finnhub_collector:
            return []
        
        try:
            await self.rate_limiter.acquire("finnhub")
            
            # Import required classes
            from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
            
            # Create proper configuration
            date_range_obj = DateRange(
                start_date=date_range['start'],
                end_date=date_range['end']
            )
            config = CollectionConfig(
                symbols=symbols,
                date_range=date_range_obj,
                max_items_per_symbol=25
            )
            
            # Use the standardized collect_data method
            result = await self.finnhub_collector.collect_data(config)
            
            # Convert RawData objects to dictionaries
            return [
                {
                    'source': data.source.value,
                    'content_type': data.content_type,
                    'text': data.text,
                    'timestamp': data.timestamp,
                    'stock_symbol': data.stock_symbol,
                    'url': data.url,
                    'metadata': data.metadata or {}
                }
                for data in result.data
            ] if result.success else []
            
        except Exception as e:
            self.logger.error(f"Finnhub collection failed: {str(e)}")
            raise
    
    async def _collect_marketaux_data(self, symbols: List[str], 
                                     date_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """Collect Marketaux news data"""
        if not self.marketaux_collector:
            return []
        
        try:
            await self.rate_limiter.acquire("marketaux")
            
            # Import required classes
            from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
            
            # Create proper configuration
            date_range_obj = DateRange(
                start_date=date_range['start'],
                end_date=date_range['end']
            )
            config = CollectionConfig(
                symbols=symbols,
                date_range=date_range_obj,
                max_items_per_symbol=25
            )
            
            # Use the standardized collect_data method
            result = await self.marketaux_collector.collect_data(config)
            
            # Convert RawData objects to dictionaries
            return [
                {
                    'source': data.source.value,
                    'content_type': data.content_type,
                    'text': data.text,
                    'timestamp': data.timestamp,
                    'stock_symbol': data.stock_symbol,
                    'url': data.url,
                    'metadata': data.metadata or {}
                }
                for data in result.data
            ] if result.success else []
            
        except Exception as e:
            self.logger.error(f"Marketaux collection failed: {str(e)}")
            raise
    
    async def _collect_newsapi_data(self, symbols: List[str], 
                                   date_range: Dict[str, datetime]) -> List[Dict[str, Any]]:
        """Collect NewsAPI data"""
        if not self.newsapi_collector:
            return []
        
        try:
            await self.rate_limiter.acquire("newsapi")
            
            # Import required classes
            from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
            
            # Create proper configuration
            date_range_obj = DateRange(
                start_date=date_range['start'],
                end_date=date_range['end']
            )
            config = CollectionConfig(
                symbols=symbols,
                date_range=date_range_obj,
                max_items_per_symbol=25
            )
            
            # Use the standardized collect_data method
            result = await self.newsapi_collector.collect_data(config)
            
            # Convert RawData objects to dictionaries
            return [
                {
                    'source': data.source.value,
                    'content_type': data.content_type,
                    'text': data.text,
                    'timestamp': data.timestamp,
                    'stock_symbol': data.stock_symbol,
                    'url': data.url,
                    'metadata': data.metadata or {}
                }
                for data in result.data
            ] if result.success else []
            
        except Exception as e:
            self.logger.error(f"NewsAPI collection failed: {str(e)}")
            raise
    
    def get_job_status(self, job_id: str) -> Optional[CollectionJob]:
        """Get status of a collection job"""
        return self.active_jobs.get(job_id)
    
    def list_active_jobs(self) -> List[CollectionJob]:
        """List all active collection jobs"""
        return list(self.active_jobs.values())
    
    def cleanup_completed_jobs(self, max_age_hours: int = 24):
        """Remove completed jobs older than specified hours"""
        cutoff_time = datetime.utcnow() - timedelta(hours=max_age_hours)
        
        jobs_to_remove = []
        for job_id, job in self.active_jobs.items():
            if (job.status in ["completed", "failed", "error"] and 
                job.completed_at and job.completed_at < cutoff_time):
                jobs_to_remove.append(job_id)
        
        for job_id in jobs_to_remove:
            del self.active_jobs[job_id]
        
        if jobs_to_remove:
            self.logger.info(
                f"Cleaned up {len(jobs_to_remove)} completed collection jobs",
                cleaned_jobs=jobs_to_remove
            )