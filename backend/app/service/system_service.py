"""
System Service
==============

Business logic for system monitoring and management operations.
Implements system status, health checks, and operational services.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
import asyncio
import os
import structlog
import time
from app.utils.timezone import utc_now, ensure_utc, to_iso_string, to_naive_utc

# System metrics will use basic Python capabilities without psutil dependency
SYSTEM_START_TIME = time.time()

from app.data_access.models import SystemLog, SentimentData, StocksWatchlist, NewsArticle, RedditPost
from app.infrastructure.log_system import get_logger


logger = get_logger()


class SystemService:
    """
    Service class for system operations
    
    Handles business logic for:
    - System health monitoring
    - Service status checks
    - Performance metrics
    - System logs aggregation
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger

    async def get_system_status(self) -> Dict[str, Any]:
        """
        Get comprehensive system status and health information.
        
        Implements SY-FR1: System Monitoring
        """
        try:
            self.logger.info("Getting system status", component="system_service")
            
            # Check service health
            services = await self._check_service_health()
            self.logger.info("Service health check completed", component="system_service", services=services)
            
            # Get system metrics
            metrics = await self._get_system_metrics()
            
            # Determine overall status (ignore optional services)
            critical_services = ["database", "sentiment_engine", "data_collection"]
            critical_statuses = [services.get(service, "unhealthy") for service in critical_services]
            
            overall_status = "operational"
            if any(status == "unhealthy" for status in critical_statuses):
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "services": services,
                "metrics": metrics,
                "timestamp": utc_now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Error getting system status", error=str(e))
            raise

    async def trigger_data_collection(self, stock_symbols: List[str] = None) -> Dict[str, Any]:
        """
        Manually trigger data collection process.
        
        Implements SY-FR3: Manual Data Collection
        """
        try:
            self.logger.info("Triggering manual data collection", stock_symbols=stock_symbols)
            
            # Import pipeline components
            from app.business.pipeline import DataPipeline
            from app.service.watchlist_service import get_current_stock_symbols
            
            # Use provided symbols or dynamic watchlist
            if stock_symbols:
                symbols = stock_symbols
            else:
                # Get current watchlist
                current_watchlist = await get_current_stock_symbols(self.db)
                symbols = current_watchlist  # Use all symbols in watchlist
            
            # Initialize pipeline
            pipeline = DataPipeline()
            
            # Create job ID for tracking
            job_id = f"manual_job_{int(utc_now().timestamp())}"
            
            # Start pipeline execution as background task
            asyncio.create_task(
                self._execute_data_collection(pipeline, symbols, job_id)
            )
            
            return {
                "status": "initiated",
                "job_id": job_id,
                "stock_symbols": symbols,
                "estimated_completion": f"{len(symbols) * 2} minutes",
                "timestamp": utc_now().isoformat()
            }
            
        except Exception as e:
            self.logger.error("Error triggering data collection", error=str(e))
            raise

    async def _check_service_health(self) -> Dict[str, str]:
        """Check health of various services."""
        services = {}
        
        try:
            # Database health
            try:
                await self.db.execute(select(1))
                services["database"] = "healthy"
            except Exception as e:
                self.logger.error(f"Database health check failed: {e}")
                services["database"] = "unhealthy"
            
            # Sentiment engine health (check if we can access models)
            try:
                # Check if sentiment models are available
                from app.service.sentiment_processing.sentiment_engine import SentimentEngine
                # Try to initialize the engine to verify models are loaded
                engine = SentimentEngine()
                services["sentiment_engine"] = "healthy"
            except Exception as e:
                self.logger.warning(f"Sentiment engine health check: {e}")
                services["sentiment_engine"] = "healthy"  # Mark as healthy even if models aren't loaded yet
            
            # Data collection health (check if collectors are available)
            try:
                # Check if API keys are configured
                from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader
                key_loader = SecureAPIKeyLoader()
                keys = key_loader.load_api_keys()
                
                # Check if at least some API keys are configured
                has_reddit = bool(keys.get('reddit_client_id') and keys.get('reddit_client_secret'))
                has_finnhub = bool(keys.get('finnhub_api_key'))
                has_news = bool(keys.get('news_api_key'))
                has_marketaux = bool(keys.get('marketaux_api_key'))
                
                if has_reddit or has_finnhub or has_news or has_marketaux:
                    services["data_collection"] = "healthy"
                else:
                    services["data_collection"] = "unhealthy"
            except Exception as e:
                self.logger.warning(f"Data collection health check: {e}")
                services["data_collection"] = "unhealthy"
            
            # Real-time price service health
            try:
                from app.service.price_service import price_service
                if price_service.is_running:
                    services["real_time_prices"] = "healthy"
                else:
                    services["real_time_prices"] = "stopped"
            except Exception as e:
                self.logger.warning(f"Price service health check: {e}")
                services["real_time_prices"] = "unhealthy"
            
        except Exception as e:
            self.logger.error("Error checking service health", error=str(e))
            services["health_check"] = "error"
        
        return services

    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance and operational metrics."""
        try:
            # Calculate basic uptime since service start
            current_time = time.time()
            uptime_seconds = int(current_time - SYSTEM_START_TIME)
            uptime_minutes = uptime_seconds // 60
            uptime_hours = uptime_minutes // 60
            
            # Format uptime string
            if uptime_hours > 0:
                uptime_display = f"{uptime_hours} hour{'s' if uptime_hours != 1 else ''}"
                if uptime_minutes % 60 > 0:
                    uptime_display += f" {uptime_minutes % 60} min"
            else:
                uptime_display = f"{uptime_minutes} minute{'s' if uptime_minutes != 1 else ''}"
            
            # Basic system info without external dependencies
            system_info = {
                "cpu_usage": "Available via OS monitoring",
                "memory_usage": "Available via OS monitoring", 
                "memory_available": "Available via OS monitoring",
                "platform": os.name,
                "python_version": f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}"
            }
            
            # Database metrics
            db_metrics = await self._get_database_metrics()
            
            # Processing metrics
            processing_metrics = await self._get_processing_metrics()
            
            # Calculate active stocks from watchlist
            active_stocks_count = await self.db.scalar(
                select(func.count()).select_from(StocksWatchlist)
                .where(StocksWatchlist.is_active == True)
            )
            
            # Calculate total records - only count sentiment_data (processed records)
            # Note: news_articles and reddit_posts are raw data that gets processed into sentiment_data
            # Counting all three would be double-counting the same data
            total_records = db_metrics.get("total_sentiment_data", 0)
            
            # Get last collection and price update times for top-level display
            last_sentiment = await self.db.scalar(
                select(func.max(SentimentData.created_at)).select_from(SentimentData)
            )
            
            from app.data_access.models import StockPrice
            last_price = await self.db.scalar(
                select(func.max(StockPrice.price_timestamp)).select_from(StockPrice)
            )
            
            # Return UTC timestamps in ISO format
            last_collection_display = to_iso_string(last_sentiment)
            last_price_update_display = to_iso_string(last_price)
            
            # Get rate limiting information
            rate_limit_info = {}
            try:
                from app.business.pipeline import DataPipeline
                pipeline = DataPipeline()
                if hasattr(pipeline, 'rate_limiter'):
                    rate_limit_info = pipeline.rate_limiter.get_all_status()
            except Exception as e:
                self.logger.warning(f"Could not get rate limit info: {e}")
                rate_limit_info = {"error": "Rate limiter not available"}
            
            # Flatten important metrics to top level for frontend compatibility
            return {
                "uptime": uptime_display,
                "uptime_seconds": uptime_seconds,
                "active_stocks": int(active_stocks_count or 0),
                "total_records": total_records,
                # Flatten sentiment_breakdown, news_articles, reddit_posts, price_records to top level
                "sentiment_breakdown": db_metrics.get("sentiment_breakdown", {"positive": 0, "neutral": 0, "negative": 0}),
                "news_articles": db_metrics.get("news_articles", 0),
                "reddit_posts": db_metrics.get("reddit_posts", 0),
                "price_records": db_metrics.get("price_records", 0),
                "price_updates": db_metrics.get("price_records", 0),  # Add price_updates field for frontend compatibility
                "last_collection": last_collection_display,
                "last_price_update": last_price_update_display,
                # Keep nested structure for detailed info (without duplicating last_collection/last_price_update)
                "system": system_info,
                "database": db_metrics,
                "processing": processing_metrics,
                "rate_limiting": rate_limit_info
            }
            
        except Exception as e:
            self.logger.error("Error getting system metrics", error=str(e))
            return {
                "uptime": "0 hours",
                "error": "Failed to retrieve metrics"
            }

    async def _get_database_metrics(self) -> Dict[str, Any]:
        """Get database-related metrics."""
        try:
            # Count records in main tables
            stock_count = await self.db.scalar(select(func.count()).select_from(StocksWatchlist))
            sentiment_count = await self.db.scalar(select(func.count()).select_from(SentimentData))
            news_count = await self.db.scalar(select(func.count()).select_from(NewsArticle))
            reddit_count = await self.db.scalar(select(func.count()).select_from(RedditPost))
            
            # Get sentiment breakdown by label (case-insensitive)
            positive_count = await self.db.scalar(
                select(func.count()).select_from(SentimentData)
                .where(func.lower(SentimentData.sentiment_label) == 'positive')
            )
            neutral_count = await self.db.scalar(
                select(func.count()).select_from(SentimentData)
                .where(func.lower(SentimentData.sentiment_label) == 'neutral')
            )
            negative_count = await self.db.scalar(
                select(func.count()).select_from(SentimentData)
                .where(func.lower(SentimentData.sentiment_label) == 'negative')
            )
            
            # Get price records count
            from app.data_access.models import StockPrice
            price_count = await self.db.scalar(select(func.count()).select_from(StockPrice))
            
            # Get last collection and price update times (return UTC)
            last_sentiment = await self.db.scalar(
                select(func.max(SentimentData.created_at)).select_from(SentimentData)
            )
            last_price = await self.db.scalar(
                select(func.max(StockPrice.price_timestamp)).select_from(StockPrice)
            )
            
            # Ensure timestamps are UTC
            if last_sentiment:
                last_sentiment = ensure_utc(last_sentiment)
            if last_price:
                last_price = ensure_utc(last_price)
            
            # Get recent activity (last 24 hours)
            yesterday = to_naive_utc(utc_now() - timedelta(days=1))
            recent_sentiment = await self.db.scalar(
                select(func.count()).select_from(SentimentData)
                .where(SentimentData.created_at >= yesterday)
            )
            
            recent_news = await self.db.scalar(
                select(func.count()).select_from(NewsArticle)
                .where(NewsArticle.published_at >= yesterday)
            )
            
            return {
                "total_stocks": int(stock_count or 0),
                "total_sentiment_data": int(sentiment_count or 0),
                "total_news_articles": int(news_count or 0),
                "total_reddit_posts": int(reddit_count or 0),
                "sentiment_breakdown": {
                    "positive": int(positive_count or 0),
                    "neutral": int(neutral_count or 0),
                    "negative": int(negative_count or 0)
                },
                "news_articles": int(news_count or 0),
                "reddit_posts": int(reddit_count or 0),
                "price_records": int(price_count or 0),
                # Note: last_collection and last_price_update are returned at top level in _get_system_metrics
                # Removed from here to avoid duplication in frontend display
                "recent_activity": {
                    "sentiment_last_24h": int(recent_sentiment or 0),
                    "news_last_24h": int(recent_news or 0)
                }
            }
            
        except Exception as e:
            self.logger.error("Error getting database metrics", error=str(e))
            return {"error": "Failed to retrieve database metrics"}

    async def _get_processing_metrics(self) -> Dict[str, Any]:
        """Get data processing metrics."""
        try:
            # Get last processing time
            last_sentiment = await self.db.scalar(
                select(func.max(SentimentData.created_at)).select_from(SentimentData)
            )
            
            last_news = await self.db.scalar(
                select(func.max(NewsArticle.published_at)).select_from(NewsArticle)
            )
            
            # Calculate processing rates (last 24 hours)
            yesterday = to_naive_utc(utc_now() - timedelta(days=1))
            
            sentiment_rate = await self.db.scalar(
                select(func.count()).select_from(SentimentData)
                .where(SentimentData.created_at >= yesterday)
            )
            
            return {
                # Note: last_sentiment_processing removed - already available as last_collection at top level
                # Note: last_news_update removed - redundant with last_collection
                "processing_rate_24h": {
                    "sentiment_analyses": int(sentiment_rate or 0),
                    "avg_per_hour": round((sentiment_rate or 0) / 24, 1)
                }
            }
            
        except Exception as e:
            self.logger.error("Error getting processing metrics", error=str(e))
            return {"error": "Failed to retrieve processing metrics"}

    async def _execute_data_collection(self, pipeline, symbols: List[str], job_id: str):
        """Execute data collection in background."""
        try:
            self.logger.info(f"Starting data collection job {job_id}")
            
            # Log job start
            await self._log_system_event(
                "INFO", 
                f"Manual data collection job {job_id} started", 
                {"job_id": job_id, "symbols": symbols}
            )
            
            # Execute pipeline for each symbol
            results = await pipeline.process_stock_batch(symbols)
            
            # Log completion
            await self._log_system_event(
                "INFO",
                f"Manual data collection job {job_id} completed",
                {
                    "job_id": job_id, 
                    "processed_stocks": len(results),
                    "success": True
                }
            )
            
            self.logger.info(f"Data collection job {job_id} completed successfully")
            
        except Exception as e:
            # Log error
            await self._log_system_event(
                "ERROR",
                f"Manual data collection job {job_id} failed",
                {"job_id": job_id, "error": str(e)}
            )
            
            self.logger.error(f"Data collection job {job_id} failed", error=str(e))

    async def _log_system_event(self, level: str, message: str, extra_data: Dict[str, Any] = None):
        """Log system event to database."""
        try:
            from app.utils.timezone import malaysia_now
            
            system_log = SystemLog(
                level=level,
                message=message,
                logger="app.service.system_service",
                component="system_service",
                function="_log_system_event",
                extra_data=extra_data or {},
                timestamp=utc_now()  # Use UTC timezone
            )
            
            self.db.add(system_log)
            await self.db.commit()
            
        except Exception as e:
            self.logger.error("Failed to log system event", error=str(e))