"""
Cleanup service for managing old data
"""
import logging
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, func

from app.core.database import AsyncSessionLocal
from app.models import SentimentData, PriceData, CorrelationData, SystemLog

logger = logging.getLogger(__name__)


class CleanupService:
    """Service for cleaning up old data"""
    
    def __init__(self, retention_days: int = 30):
        self.retention_days = retention_days
        self.session = None
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def cleanup_old_records(self):
        """Clean up old records from database"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
            
            # Count records to be deleted
            sentiment_count = await self.session.scalar(
                select(func.count(SentimentData.id)).where(
                    SentimentData.created_at < cutoff_date
                )
            )
            
            price_count = await self.session.scalar(
                select(func.count(PriceData.id)).where(
                    PriceData.created_at < cutoff_date
                )
            )
            
            correlation_count = await self.session.scalar(
                select(func.count(CorrelationData.id)).where(
                    CorrelationData.created_at < cutoff_date
                )
            )
            
            log_count = await self.session.scalar(
                select(func.count(SystemLog.id)).where(
                    SystemLog.created_at < cutoff_date - timedelta(days=30)  # Keep logs longer
                )
            )
            
            logger.info(f"Cleaning up: {sentiment_count} sentiment, {price_count} price, "
                       f"{correlation_count} correlation, {log_count} log records")
            
            # Delete old sentiment data
            if sentiment_count > 0:
                await self.session.execute(
                    delete(SentimentData).where(
                        SentimentData.created_at < cutoff_date
                    )
                )
            
            # Delete old price data (keep longer history)
            if price_count > 0:
                await self.session.execute(
                    delete(PriceData).where(
                        PriceData.created_at < cutoff_date - timedelta(days=60)
                    )
                )
            
            # Delete old correlation data
            if correlation_count > 0:
                await self.session.execute(
                    delete(CorrelationData).where(
                        CorrelationData.created_at < cutoff_date
                    )
                )
            
            # Delete old logs (keep error logs longer)
            if log_count > 0:
                await self.session.execute(
                    delete(SystemLog).where(
                        SystemLog.created_at < cutoff_date - timedelta(days=30),
                        SystemLog.level != "error"
                    )
                )
                
                # Delete error logs older than 90 days
                await self.session.execute(
                    delete(SystemLog).where(
                        SystemLog.created_at < cutoff_date - timedelta(days=90),
                        SystemLog.level == "error"
                    )
                )
            
            await self.session.commit()
            
            # Log cleanup completion
            log = SystemLog(
                level="info",
                source="cleanup_service",
                message=f"Cleanup completed: {sentiment_count + price_count + correlation_count + log_count} records deleted",
                metadata={
                    "sentiment": sentiment_count,
                    "price": price_count,
                    "correlation": correlation_count,
                    "logs": log_count
                }
            )
            self.session.add(log)
            await self.session.commit()
            
            logger.info("Data cleanup completed successfully")
            
        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            await self.session.rollback()
            
            # Log error
            log = SystemLog(
                level="error",
                source="cleanup_service",
                message=f"Cleanup failed: {str(e)}"
            )
            self.session.add(log)
            await self.session.commit()
            
            raise
