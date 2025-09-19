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

# System metrics will use basic Python capabilities without psutil dependency
SYSTEM_START_TIME = time.time()

from app.data_access.models import SystemLog, SentimentData, Stock, NewsArticle, RedditPost
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
            self.logger.info("Getting system status")
            
            # Check service health
            services = await self._check_service_health()
            
            # Get system metrics
            metrics = await self._get_system_metrics()
            
            # Determine overall status
            overall_status = "operational"
            if any(status != "healthy" for status in services.values()):
                overall_status = "degraded"
            
            return {
                "status": overall_status,
                "services": services,
                "metrics": metrics,
                "timestamp": datetime.utcnow().isoformat()
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
                symbols = current_watchlist[:10]  # Limit to prevent overload
            
            # Initialize pipeline
            pipeline = DataPipeline()
            
            # Create job ID for tracking
            job_id = f"manual_job_{int(datetime.utcnow().timestamp())}"
            
            # Start pipeline execution as background task
            asyncio.create_task(
                self._execute_data_collection(pipeline, symbols, job_id)
            )
            
            return {
                "status": "initiated",
                "job_id": job_id,
                "stock_symbols": symbols,
                "estimated_completion": f"{len(symbols) * 2} minutes",
                "timestamp": datetime.utcnow().isoformat()
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
            except Exception:
                services["database"] = "unhealthy"
            
            # Sentiment engine health (check if we can access models)
            try:
                from app.service.sentiment_processing.sentiment_engine import SentimentEngine
                services["sentiment_engine"] = "healthy"
            except Exception:
                services["sentiment_engine"] = "unhealthy"
            
            # Data collection health (check if collectors are available)
            try:
                from app.service.data_collection.service import DataCollectionService
                services["data_collection"] = "healthy"
            except Exception:
                services["data_collection"] = "unhealthy"
            
            # Redis/Cache health (if available)
            try:
                # Check if Redis is configured and available
                redis_url = os.getenv("REDIS_URL")
                if redis_url:
                    services["redis"] = "healthy"  # Could add actual Redis ping here
                else:
                    services["redis"] = "not_configured"
            except Exception:
                services["redis"] = "unhealthy"
            
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
            uptime_hours = uptime_seconds // 3600
            
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
            
            return {
                "uptime": f"{uptime_hours} hours",
                "uptime_seconds": uptime_seconds,
                "system": system_info,
                "database": db_metrics,
                "processing": processing_metrics
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
            stock_count = await self.db.scalar(select(func.count()).select_from(Stock))
            sentiment_count = await self.db.scalar(select(func.count()).select_from(SentimentData))
            news_count = await self.db.scalar(select(func.count()).select_from(NewsArticle))
            reddit_count = await self.db.scalar(select(func.count()).select_from(RedditPost))
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            recent_sentiment = await self.db.scalar(
                select(func.count()).select_from(SentimentData)
                .where(SentimentData.created_at >= yesterday)
            )
            
            recent_news = await self.db.scalar(
                select(func.count()).select_from(NewsArticle)
                .where(NewsArticle.created_at >= yesterday)
            )
            
            return {
                "total_stocks": int(stock_count or 0),
                "total_sentiment_data": int(sentiment_count or 0),
                "total_news_articles": int(news_count or 0),
                "total_reddit_posts": int(reddit_count or 0),
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
                select(func.max(NewsArticle.created_at)).select_from(NewsArticle)
            )
            
            # Calculate processing rates (last 24 hours)
            yesterday = datetime.utcnow() - timedelta(days=1)
            
            sentiment_rate = await self.db.scalar(
                select(func.count()).select_from(SentimentData)
                .where(SentimentData.created_at >= yesterday)
            )
            
            return {
                "last_sentiment_processing": last_sentiment.isoformat() if last_sentiment else None,
                "last_news_update": last_news.isoformat() if last_news else None,
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
            system_log = SystemLog(
                level=level,
                message=message,
                logger="app.service.system_service",
                component="system_service",
                function="_log_system_event",
                extra_data=extra_data or {}
            )
            
            self.db.add(system_log)
            await self.db.commit()
            
        except Exception as e:
            self.logger.error("Failed to log system event", error=str(e))