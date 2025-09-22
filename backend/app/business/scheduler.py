"""
Scheduler - Business Layer Job Scheduling
=========================================

Automated job scheduling and triggers for the sentiment analysis pipeline.
Implements the Scheduler component from FYP Implementation Plan Layer 2: Business Layer.

Features:
- Automated data collection scheduling
- Pipeline job orchestration  
- Cron-like scheduling capabilities
- Error handling and retry logic
- Job status monitoring and logging

This component coordinates with DataCollector and Pipeline to automate
the sentiment analysis workflow according to configured schedules.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.infrastructure.log_system import get_logger
from app.business.pipeline import DataPipeline
from app.service.watchlist_service import get_current_stock_symbols
from app.service.price_service import price_service
from app.data_access.database.connection import get_db_session


class JobStatus(Enum):
    """Job execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ScheduledJob:
    """Represents a scheduled job"""
    job_id: str
    name: str
    job_type: str
    trigger_config: Dict[str, Any]
    parameters: Dict[str, Any]
    status: JobStatus = JobStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    run_count: int = 0
    error_count: int = 0
    last_error: Optional[str] = None
    enabled: bool = True


class Scheduler:
    """
    Background job scheduler for data collection, sentiment analysis, and pipeline execution.
    
    Features:
    - Automated data collection scheduling
    - Sentiment analysis orchestration  
    - Full pipeline execution
    - Dynamic watchlist integration
    - Error handling and retry logic
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the scheduler"""
        # Prevent re-initialization of singleton
        if hasattr(self, 'logger'):
            return
            
        self.logger = get_logger()
        self.scheduler = AsyncIOScheduler()
        # Remove duplicate DataCollector - pipeline handles its own collectors
        self.pipeline = DataPipeline()
        
        self.jobs: Dict[str, ScheduledJob] = {}
        self._is_running = False
        
        # Fallback stock symbols (used only if dynamic watchlist fails)
        self.fallback_symbols = [
            "NVDA", "MSFT", "AAPL", "AVGO", "ORCL", "PLTR", "CSCO", "AMD", "IBM", "CRM",
            "NOW", "INTU", "QCOM", "MU", "TXN", "ADBE", "GOOGL", "AMZN", "META", "TSLA"
        ]
    
    async def start(self):
        """Start the scheduler"""
        if not self._is_running:
            self.scheduler.start()
            self._is_running = True
            self.logger.info("Scheduler started successfully - automated job scheduling is now active")
            
            # Start real-time price service
            await price_service.start()
            self.logger.info("Real-time stock price service started")
            
            # Setup default scheduled jobs
            await self._setup_default_jobs()
            self.logger.info(f"Default scheduled jobs created: {len(self.jobs)} jobs configured")
    
    async def stop(self):
        """Stop the scheduler"""
        if self._is_running:
            # Stop real-time price service
            await price_service.stop()
            self.logger.info("Real-time stock price service stopped")
            
            self.scheduler.shutdown()
            self._is_running = False
            self.logger.info("Scheduler stopped")
    
    async def get_current_symbols(self) -> List[str]:
        """
        Get current stock symbols from dynamic watchlist.
        Falls back to hardcoded symbols if watchlist is unavailable.
        """
        try:
            # Get database session
            async with get_db_session() as db:
                symbols = await get_current_stock_symbols(db)
                if symbols:
                    self.logger.info(f"Using dynamic watchlist with {len(symbols)} symbols")
                    return symbols
                else:
                    self.logger.warning("Dynamic watchlist is empty, using fallback symbols")
                    return self.fallback_symbols
        except Exception as e:
            self.logger.warning(f"Failed to get dynamic watchlist: {e}, using fallback symbols")
            return self.fallback_symbols
    
    async def refresh_scheduled_jobs(self):
        """
        Refresh all scheduled jobs with updated watchlist.
        This should be called when the admin updates the watchlist.
        """
        try:
            self.logger.info("Refreshing scheduled jobs with updated watchlist")
            
            # Get updated symbols
            current_symbols = await self.get_current_symbols()
            
            # Cancel existing recurring jobs (but keep running jobs)
            jobs_to_refresh = ["Daily Data Collection", "Hourly Sentiment Analysis", "Weekly Full Pipeline"]
            for job_name in jobs_to_refresh:
                # Find and remove the job
                for job_id, job in list(self.jobs.items()):
                    if job.name == job_name and job.status in [JobStatus.PENDING]:
                        self.scheduler.remove_job(job_id)
                        del self.jobs[job_id]
                        self.logger.info(f"Removed old scheduled job: {job_name}")
            
            # Recreate default jobs with new symbols
            await self._setup_default_jobs()
            
            self.logger.info(f"Successfully refreshed scheduled jobs with {len(current_symbols)} symbols")
            
        except Exception as e:
            self.logger.error(f"Error refreshing scheduled jobs: {e}")
    
    async def _setup_default_jobs(self):
        """Setup default scheduled jobs for the pipeline"""
        
        # Get current symbols from dynamic watchlist
        current_symbols = await self.get_current_symbols()
        
        # Daily data collection job at 6 AM UTC
        await self.schedule_data_collection(
            name="Daily Data Collection",
            cron_expression="0 6 * * *",  # Daily at 6 AM
            symbols=current_symbols,
            lookback_days=1
        )
        
        # Hourly sentiment analysis during market hours
        await self.schedule_sentiment_analysis(
            name="Hourly Sentiment Analysis", 
            cron_expression="0 9-16 * * 1-5",  # Hourly 9AM-4PM weekdays
            symbols=current_symbols
        )
        
        # Weekly full pipeline run on Sundays
        await self.schedule_full_pipeline(
            name="Weekly Full Pipeline",
            cron_expression="0 2 * * 0",  # Sundays at 2 AM
            symbols=current_symbols,
            lookback_days=7
        )
    
    async def schedule_data_collection(self, name: str, cron_expression: str,
                                     symbols: List[str], lookback_days: int = 1) -> str:
        """
        Schedule a data collection job.
        
        Args:
            name: Human-readable job name
            cron_expression: Cron expression for scheduling
            symbols: List of stock symbols
            lookback_days: Days to look back for data collection
            
        Returns:
            Job ID of the scheduled job
        """
        job_id = f"datacoll_{uuid.uuid4().hex[:8]}"
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            job_type="data_collection",
            trigger_config={"cron": cron_expression},
            parameters={
                "symbols": symbols,
                "lookback_days": lookback_days
            }
        )
        
        # Schedule with APScheduler (replace existing to prevent duplicates)
        self.scheduler.add_job(
            func=self._execute_data_collection,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            args=[job_id],
            replace_existing=True,
            max_instances=1  # Prevent multiple instances of same job
        )
        
        self.jobs[job_id] = job
        
        self.logger.info(
            f"Scheduled data collection job: {name}",
            job_id=job_id,
            cron=cron_expression,
            symbols=symbols
        )
        
        return job_id
    
    async def schedule_sentiment_analysis(self, name: str, cron_expression: str,
                                        symbols: List[str]) -> str:
        """
        Schedule a sentiment analysis job.
        
        Args:
            name: Human-readable job name
            cron_expression: Cron expression for scheduling
            symbols: List of stock symbols
            
        Returns:
            Job ID of the scheduled job
        """
        job_id = f"sentiment_{uuid.uuid4().hex[:8]}"
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            job_type="sentiment_analysis",
            trigger_config={"cron": cron_expression},
            parameters={"symbols": symbols}
        )
        
        # Schedule with APScheduler (replace existing to prevent duplicates)
        self.scheduler.add_job(
            func=self._execute_sentiment_analysis,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            args=[job_id],
            replace_existing=True,
            max_instances=1  # Prevent multiple instances of same job
        )
        
        self.jobs[job_id] = job
        
        self.logger.info(
            f"Scheduled sentiment analysis job: {name}",
            job_id=job_id,
            cron=cron_expression,
            symbols=symbols
        )
        
        return job_id
    
    async def schedule_full_pipeline(self, name: str, cron_expression: str,
                                   symbols: List[str], lookback_days: int = 7) -> str:
        """
        Schedule a full pipeline execution job.
        
        Args:
            name: Human-readable job name  
            cron_expression: Cron expression for scheduling
            symbols: List of stock symbols
            lookback_days: Days to look back for processing
            
        Returns:
            Job ID of the scheduled job
        """
        job_id = f"pipeline_{uuid.uuid4().hex[:8]}"
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            job_type="full_pipeline",
            trigger_config={"cron": cron_expression},
            parameters={
                "symbols": symbols,
                "lookback_days": lookback_days
            }
        )
        
        # Schedule with APScheduler (replace existing to prevent duplicates)
        self.scheduler.add_job(
            func=self._execute_full_pipeline,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            args=[job_id],
            replace_existing=True,
            max_instances=1  # Prevent multiple instances of same job
        )
        
        self.jobs[job_id] = job
        
        self.logger.info(
            f"Scheduled full pipeline job: {name}",
            job_id=job_id,
            cron=cron_expression,
            symbols=symbols
        )
        
        return job_id
    
    async def _execute_data_collection(self, job_id: str):
        """Execute a data collection job"""
        job = self.jobs.get(job_id)
        if not job or not job.enabled:
            return
        
        job.status = JobStatus.RUNNING
        job.last_run = datetime.utcnow()
        
        try:
            self.logger.info(f"🚀 EXECUTING SCHEDULED JOB: Data Collection", 
                           job_id=job_id, 
                           job_name=job.name,
                           symbols=job.parameters["symbols"][:5],  # Show first 5 symbols
                           lookback_days=job.parameters["lookback_days"])
            
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=job.parameters["lookback_days"])
            
            # Execute data collection using pipeline
            from .pipeline import PipelineConfig, DateRange
            config = PipelineConfig(
                symbols=job.parameters["symbols"],
                date_range=DateRange(start_date=start_date, end_date=end_date),
                max_items_per_symbol=job.parameters.get("max_items", 100)
            )
            collection_result = await self.pipeline.run_pipeline(config)
            
            if collection_result.status.value == "completed":
                job.status = JobStatus.COMPLETED
                job.run_count += 1
                self.logger.info(f"Data collection job {job_id} completed successfully")
            else:
                job.status = JobStatus.FAILED
                job.error_count += 1
                job.last_error = f"Pipeline failed: {collection_result.errors}"
                self.logger.error(f"Data collection job {job_id} failed", errors=collection_result.errors)
        
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_count += 1
            job.last_error = str(e)
            self.logger.error(f"Data collection job {job_id} failed with exception", error=str(e))
    
    async def _execute_sentiment_analysis(self, job_id: str):
        """Execute a sentiment analysis job"""
        job = self.jobs.get(job_id)
        if not job or not job.enabled:
            return
        
        job.status = JobStatus.RUNNING
        job.last_run = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting scheduled sentiment analysis job {job_id}")
            
            # Execute sentiment analysis on recent data
            result = await self.pipeline.process_recent_data(
                symbols=job.parameters["symbols"],
                hours_back=24  # Process last 24 hours of data
            )
            
            if result.get("status") == "success":
                job.status = JobStatus.COMPLETED
                job.run_count += 1
                self.logger.info(f"Sentiment analysis job {job_id} completed successfully")
            else:
                job.status = JobStatus.FAILED
                job.error_count += 1
                job.last_error = result.get("error", "Unknown error")
                self.logger.error(f"Sentiment analysis job {job_id} failed")
        
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_count += 1
            job.last_error = str(e)
            self.logger.error(f"Sentiment analysis job {job_id} failed with exception", error=str(e))
    
    async def _execute_full_pipeline(self, job_id: str):
        """Execute a full pipeline job"""
        job = self.jobs.get(job_id)
        if not job or not job.enabled:
            return
        
        job.status = JobStatus.RUNNING
        job.last_run = datetime.utcnow()
        
        try:
            self.logger.info(f"Starting scheduled full pipeline job {job_id}")
            
            # Execute full pipeline
            result = await self.pipeline.run_full_pipeline(
                symbols=job.parameters["symbols"],
                lookback_days=job.parameters["lookback_days"]
            )
            
            if result.get("status") == "success":
                job.status = JobStatus.COMPLETED
                job.run_count += 1
                self.logger.info(f"Full pipeline job {job_id} completed successfully")
            else:
                job.status = JobStatus.FAILED
                job.error_count += 1
                job.last_error = result.get("error", "Unknown error")
                self.logger.error(f"Full pipeline job {job_id} failed")
        
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_count += 1
            job.last_error = str(e)
            self.logger.error(f"Full pipeline job {job_id} failed with exception", error=str(e))
    
    def cancel_job(self, job_id: str) -> bool:
        """Cancel a scheduled job"""
        job = self.jobs.get(job_id)
        if not job:
            return False
        
        try:
            self.scheduler.remove_job(job_id)
            job.status = JobStatus.CANCELLED
            job.enabled = False
            
            self.logger.info(f"Cancelled scheduled job {job_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}", error=str(e))
            return False
    
    def get_job_status(self, job_id: str) -> Optional[ScheduledJob]:
        """Get status of a scheduled job"""
        return self.jobs.get(job_id)
    
    def list_jobs(self) -> List[ScheduledJob]:
        """List all scheduled jobs"""
        return list(self.jobs.values())
    
    def enable_job(self, job_id: str) -> bool:
        """Enable a job"""
        job = self.jobs.get(job_id)
        if job:
            job.enabled = True
            return True
        return False
    
    def disable_job(self, job_id: str) -> bool:
        """Disable a job"""
        job = self.jobs.get(job_id)
        if job:
            job.enabled = False
            return True
        return False