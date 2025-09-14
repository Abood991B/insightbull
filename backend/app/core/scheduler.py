"""
Background task scheduler for data collection and processing
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from config import settings

logger = logging.getLogger(__name__)

scheduler = None


def start_scheduler():
    """Initialize and start the background scheduler"""
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    scheduler = AsyncIOScheduler()
    
    # Schedule data collection pipeline
    if settings.PIPELINE_SCHEDULE:
        scheduler.add_job(
            run_data_pipeline,
            CronTrigger.from_crontab(settings.PIPELINE_SCHEDULE),
            id="data_pipeline",
            name="Data Collection Pipeline",
            replace_existing=True
        )
        logger.info(f"Scheduled data pipeline with cron: {settings.PIPELINE_SCHEDULE}")
    
    # Schedule correlation calculation (every hour)
    scheduler.add_job(
        calculate_correlations,
        CronTrigger(minute=0),  # Run at the start of every hour
        id="correlation_calc",
        name="Correlation Calculation",
        replace_existing=True
    )
    
    # Schedule cleanup old data (daily at 2 AM)
    scheduler.add_job(
        cleanup_old_data,
        CronTrigger(hour=2, minute=0),
        id="cleanup",
        name="Data Cleanup",
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Background scheduler started")
    
    return scheduler


async def run_data_pipeline():
    """Execute the main data collection pipeline"""
    try:
        logger.info("Starting data collection pipeline")
        
        from app.services.data_collector import DataCollector
        collector = DataCollector()
        
        # Collect data from all sources
        await collector.collect_all()
        
        # Process sentiment analysis
        from app.services.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        await analyzer.process_pending()
        
        logger.info("Data collection pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Data pipeline failed: {e}", exc_info=True)


async def calculate_correlations():
    """Calculate sentiment-price correlations"""
    try:
        logger.info("Starting correlation calculation")
        
        from app.services.correlation_service import CorrelationService
        service = CorrelationService()
        await service.calculate_all_correlations()
        
        logger.info("Correlation calculation completed")
        
    except Exception as e:
        logger.error(f"Correlation calculation failed: {e}", exc_info=True)


async def cleanup_old_data():
    """Clean up old data from database"""
    try:
        logger.info("Starting data cleanup")
        
        from app.services.cleanup_service import CleanupService
        service = CleanupService()
        await service.cleanup_old_records()
        
        logger.info("Data cleanup completed")
        
    except Exception as e:
        logger.error(f"Data cleanup failed: {e}", exc_info=True)


def get_scheduler():
    """Get the scheduler instance"""
    return scheduler
