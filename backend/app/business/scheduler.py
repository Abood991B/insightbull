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
- Smart source selection based on run type and quota availability
- Intelligent quota management integration

This component coordinates with DataCollector and Pipeline to automate
the sentiment analysis workflow according to configured schedules.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import pytz
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from ..utils.timezone import utc_now, to_naive_utc
from apscheduler.triggers.cron import CronTrigger

from app.infrastructure.log_system import get_logger
from app.business.pipeline import DataPipeline
from app.service.watchlist_service import get_current_stock_symbols
from app.service.price_service import price_service
from app.data_access.database.connection import get_db_session

# Suppress APScheduler's verbose "Added job" messages
logging.getLogger('apscheduler.scheduler').setLevel(logging.WARNING)
logging.getLogger('apscheduler.executors.default').setLevel(logging.WARNING)


class RunType(Enum):
    """
    Run type determines which data sources to use.
    
    FREQUENT: High-frequency runs (every 30 min during market hours)
              Uses only FREE sources (HackerNews, GDELT) to conserve quota
              
    STRATEGIC: Strategic runs (pre-market, after-hours)
               Uses ALL sources including quota-limited ones
               
    DEEP: Deep analysis runs (weekend)
          Uses ALL sources with extended lookback
    """
    FREQUENT = "frequent"       # Free sources only
    STRATEGIC = "strategic"     # All sources
    DEEP = "deep"              # All sources, extended lookback


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
    created_at: datetime = field(default_factory=utc_now)
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
        # Initialize pipeline with enhanced collection features enabled
        self.pipeline = DataPipeline(
            use_enhanced_collection=True  # Enable batching and all optimizations
        )
        
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
            # Count actual jobs from APScheduler (includes quota reset)
            actual_job_count = len(self.scheduler.get_jobs())
            
            # Log consolidated scheduler summary
            job_summary = []
            for job_id, job in self.jobs.items():
                job_summary.append({
                    "name": job.name,
                    "run_type": job.parameters.get("run_type"),
                    "cron": job.parameters.get("cron_expression")
                })
            
            self.logger.info(
                "Scheduler configured with smart pipeline jobs",
                extra={
                    "total_jobs": actual_job_count,
                    "pipeline_jobs": len(self.jobs),
                    "jobs": job_summary
                }
            )
    
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
    
    def _is_market_hours(self) -> tuple[bool, str]:
        """
        Check if current time is during market hours (NYSE/NASDAQ).
        Returns (is_market_hours, period_name)
        
        Market periods (Eastern Time):
        - Pre-market: 7:00 AM - 9:30 AM
        - Market hours: 9:30 AM - 4:00 PM
        - After-hours: 4:00 PM - 8:00 PM
        - Overnight: 8:00 PM - 7:00 AM
        """
        try:
            et_tz = pytz.timezone('America/New_York')
            current_time_et = datetime.now(et_tz)
            current_hour = current_time_et.hour
            current_minute = current_time_et.minute
            day_of_week = current_time_et.weekday()
            
            # Weekend check (Saturday=5, Sunday=6)
            if day_of_week >= 5:
                return False, "weekend"
            
            # Convert to minutes for easier comparison
            current_minutes = current_hour * 60 + current_minute
            
            # Market periods in minutes from midnight
            pre_market_start = 7 * 60  # 7:00 AM
            market_open = 9 * 60 + 30  # 9:30 AM
            market_close = 16 * 60  # 4:00 PM
            after_hours_end = 20 * 60  # 8:00 PM
            
            if pre_market_start <= current_minutes < market_open:
                return False, "pre_market"
            elif market_open <= current_minutes < market_close:
                return True, "market_hours"
            elif market_close <= current_minutes < after_hours_end:
                return False, "after_hours"
            else:
                return False, "overnight"
                
        except Exception as e:
            self.logger.warning(f"Error checking market hours: {e}, defaulting to non-market hours")
            return False, "unknown"
    
    def _get_smart_interval(self) -> int:
        """
        Get smart collection interval based on market hours.
        
        Returns interval in minutes:
        - Market hours: 15 minutes (high frequency)
        - Pre-market: 30 minutes (moderate frequency)
        - After-hours: 30 minutes (moderate frequency)
        - Overnight: 120 minutes (low frequency)
        - Weekend: 240 minutes (very low frequency)
        """
        is_market, period = self._is_market_hours()
        
        interval_map = {
            "market_hours": 15,
            "pre_market": 30,
            "after_hours": 30,
            "overnight": 120,
            "weekend": 240
        }
        
        interval = interval_map.get(period, 60)  # Default 60 min
        self.logger.info(f"Smart scheduling: period='{period}', interval={interval} minutes")
        return interval
    
    def _get_sources_for_run_type(self, run_type: RunType) -> Dict[str, bool]:
        """
        Get which sources to enable based on run type.
        
        FREQUENT runs (every 15 min during market): Only FREE sources
        - HackerNews, GDELT, Finnhub have NO daily quota limits
        - This conserves NewsAPI (100/day) and Marketaux (100/day) quotas
        
        STRATEGIC runs (pre-market, after-hours): ALL sources
        - These are 3-4 runs per day, well within quota limits
        
        DEEP runs (weekend): ALL sources with extended lookback
        """
        if run_type == RunType.FREQUENT:
            # Only free, unlimited sources for high-frequency runs
            # Finnhub has 60/min rate limit but NO daily quota
            return {
                "include_hackernews": True,
                "include_gdelt": True,
                "include_finnhub": True,    # 60/min limit is fine for 30min intervals
                "include_newsapi": False,   # CONSERVE: 100/day limit
                "include_marketaux": False  # CONSERVE: 100/day limit
            }
        else:
            # All sources for strategic/deep runs
            return {
                "include_hackernews": True,
                "include_gdelt": True,
                "include_finnhub": True,
                "include_newsapi": True,
                "include_marketaux": True
            }
    
    async def _check_quota_before_run(self, sources: Dict[str, bool], num_symbols: int) -> Dict[str, bool]:
        """
        Check quotas before running and disable sources that would exceed limits.
        
        Args:
            sources: Dict of source_name -> enabled boolean
            num_symbols: Number of symbols to collect
            
        Returns:
            Updated sources dict with quota-exceeded sources disabled
        """
        try:
            from app.service.quota_tracking_service import get_quota_tracking_service
            quota_service = get_quota_tracking_service()
            
            updated_sources = sources.copy()
            
            # Check each quota-limited source
            quota_sources = ["newsapi", "marketaux"]
            for source in quota_sources:
                config_key = f"include_{source}"
                if updated_sources.get(config_key, False):
                    # Check if we can make requests
                    check = quota_service.can_make_request(source, num_symbols)
                    if not check.get("allowed", True):
                        updated_sources[config_key] = False
                        self.logger.warning(
                            f"Disabled {source} for this run due to quota: {check.get('reason')}",
                            component="scheduler",
                            source=source,
                            remaining=check.get("remaining")
                        )
            
            return updated_sources
            
        except Exception as e:
            self.logger.warning(f"Quota check failed, using original sources: {e}")
            return sources
    
    async def _setup_default_jobs(self):
        """
        Setup default scheduled jobs with SMART SOURCE SELECTION.
        
        Strategy:
        - FREQUENT runs (every 15 min during market): FREE sources (HN, GDELT, Finnhub)
          These 3 sources have NO daily quota limits, only per-minute rate limits.
        - STRATEGIC runs (pre-market, after-hours): ALL sources (3-4 times/day)
        - DEEP runs (weekend): ALL sources with 7-day lookback
        
        This ensures NewsAPI and Marketaux stay within their 100/day limits:
        - 3-4 strategic runs * 20 symbols = 60-80 requests/day (within limit)
        - Frequent runs use only free sources = 0 quota usage
        
        Source Classification:
        - FREE (no daily limit): HackerNews, GDELT, Finnhub (60/min)
        - QUOTA LIMITED (100/day): NewsAPI, Marketaux
        """
        
        # Get current symbols from dynamic watchlist
        current_symbols = await self.get_current_symbols()
        
        # =========================================================================
        # STRATEGIC RUNS: Use ALL sources (conserves quota by running only 3-4x/day)
        # =========================================================================
        
        # Pre-Market Preparation: 8:00 AM ET daily (Mon-Fri)
        # Collects fresh overnight news and social sentiment before market opens
        await self.schedule_smart_pipeline(
            name="Pre-Market Preparation",
            cron_expression="0 13 * * 1-5",  # 8:00 AM ET = 13:00 UTC
            symbols=current_symbols,
            lookback_days=1,
            run_type=RunType.STRATEGIC
        )
        
        # =========================================================================
        # FREQUENT RUNS: Every 15 min using FREE sources (HN, GDELT, Finnhub)
        # These sources have NO daily quota - only per-minute rate limits
        # =========================================================================
        
        # Active Trading Updates: Every 15 minutes during market hours (9:30 AM - 4:00 PM ET)
        # Near real-time sentiment tracking using FREE sources only
        # Note: 9:30 AM ET = 14:30 UTC, 4:00 PM ET = 21:00 UTC
        await self.schedule_smart_pipeline(
            name="Active Trading Updates",
            cron_expression="*/15 14-20 * * 1-5",  # Every 15 min, 9:30 AM-4:00 PM ET
            symbols=current_symbols,
            lookback_days=1,
            run_type=RunType.FREQUENT  # FREE SOURCES ONLY (HN, GDELT, Finnhub)
        )
        
        # =========================================================================
        # STRATEGIC RUNS: After-hours use ALL sources
        # =========================================================================
        
        # After-Hours Analysis: 5:00 PM ET (Mon-Fri)
        await self.schedule_smart_pipeline(
            name="After-Hours Analysis",
            cron_expression="0 22 * * 1-5",  # 5 PM ET (22:00 UTC Mon-Fri)
            symbols=current_symbols,
            lookback_days=1,
            run_type=RunType.STRATEGIC
        )
        
        # After-Hours Late Evening: 8:00 PM ET (Mon-Fri)
        await self.schedule_smart_pipeline(
            name="After-Hours Late Evening",
            cron_expression="0 1 * * 2-6",  # 8 PM ET Mon-Fri = 1:00 UTC Tue-Sat
            symbols=current_symbols,
            lookback_days=1,
            run_type=RunType.STRATEGIC
        )
        
        # =========================================================================
        # DEEP RUNS: Weekend comprehensive analysis
        # =========================================================================
        
        # Weekend Deep Analysis: Saturday 10:00 AM ET
        await self.schedule_smart_pipeline(
            name="Weekend Deep Analysis",
            cron_expression="0 15 * * 6",  # Saturday 10 AM ET = 15:00 UTC
            symbols=current_symbols,
            lookback_days=7,
            run_type=RunType.DEEP
        )
        
        # =========================================================================
        # DAILY QUOTA RESET: Midnight UTC
        # =========================================================================
        await self._schedule_quota_reset()
    
    async def _schedule_quota_reset(self):
        """Schedule daily quota reset job at midnight UTC."""
        job_id = "quota_reset_daily"
        
        # Schedule with APScheduler
        self.scheduler.add_job(
            func=self._execute_quota_reset,
            trigger=CronTrigger.from_crontab("0 0 * * *"),  # Midnight UTC
            id=job_id,
            replace_existing=True,
            max_instances=1
        )
        
        self.logger.info("Scheduled daily quota reset at midnight UTC")
    
    async def _execute_quota_reset(self):
        """Execute daily quota reset."""
        try:
            from app.service.quota_tracking_service import get_quota_tracking_service
            quota_service = get_quota_tracking_service()
            quota_service._check_and_reset_daily()
            self.logger.info("Daily quota reset completed")
        except Exception as e:
            self.logger.error(f"Failed to reset quotas: {e}")
    
    async def schedule_smart_pipeline(
        self, 
        name: str, 
        cron_expression: str,
        symbols: List[str], 
        lookback_days: int = 1,
        run_type: RunType = RunType.STRATEGIC
    ) -> str:
        """
        Schedule a pipeline job with smart source selection.
        
        Args:
            name: Human-readable job name
            cron_expression: Cron expression for scheduling
            symbols: List of stock symbols
            lookback_days: Days to look back
            run_type: Type of run (affects source selection)
            
        Returns:
            Job ID of the scheduled job
        """
        job_id = f"smart_pipeline_{uuid.uuid4().hex[:8]}"
        
        job = ScheduledJob(
            job_id=job_id,
            name=name,
            job_type="smart_pipeline",
            trigger_config={"cron": cron_expression},
            parameters={
                "symbols": symbols,
                "lookback_days": lookback_days,
                "run_type": run_type.value
            }
        )
        
        # Schedule with APScheduler
        self.scheduler.add_job(
            func=self._execute_smart_pipeline,
            trigger=CronTrigger.from_crontab(cron_expression),
            id=job_id,
            args=[job_id],
            replace_existing=True,
            max_instances=1
        )
        
        self.jobs[job_id] = job
        
        # Collect job info for summary (don't log individually)
        # Job details will be logged in summary at end of _setup_default_jobs()
        
        return job_id
    
    async def _execute_smart_pipeline(self, job_id: str):
        """Execute a smart pipeline job with source selection and quota tracking."""
        job = self.jobs.get(job_id)
        if not job or not job.enabled:
            return
        
        job.status = JobStatus.RUNNING
        job.last_run = utc_now()
        
        try:
            symbols = job.parameters["symbols"]
            lookback_days = job.parameters["lookback_days"]
            run_type = RunType(job.parameters["run_type"])
            
            self.logger.info(
                f"EXECUTING SMART PIPELINE: {job.name}",
                job_id=job_id,
                run_type=run_type.value,
                symbol_count=len(symbols),
                lookback_days=lookback_days
            )
            
            # Get sources for this run type
            sources = self._get_sources_for_run_type(run_type)
            
            # Check quotas and potentially disable over-quota sources
            sources = await self._check_quota_before_run(sources, len(symbols))
            
            enabled_sources = [k.replace("include_", "") for k, v in sources.items() if v]
            self.logger.info(f"Using sources for {job.name}: {enabled_sources}")
            
            # Execute pipeline with specific sources
            from .pipeline import PipelineConfig, DateRange
            end_date = to_naive_utc(utc_now())
            start_date = end_date - timedelta(days=lookback_days)
            
            config = PipelineConfig(
                symbols=symbols,
                date_range=DateRange(start_date=start_date, end_date=end_date),
                max_items_per_symbol=20,
                **sources  # Pass source configuration
            )
            
            result = await self.pipeline.run_pipeline(config)
            
            # Record quota usage for quota-limited sources
            await self._record_quota_usage(sources, len(symbols))
            
            if result.status.value == "completed":
                job.status = JobStatus.COMPLETED
                job.run_count += 1
                self.logger.info(f"Smart pipeline {job_id} completed successfully")
            else:
                job.status = JobStatus.FAILED
                job.error_count += 1
                job.last_error = f"Pipeline failed: {result.errors}"
                self.logger.error(f"Smart pipeline {job_id} failed", errors=result.errors)
                
        except Exception as e:
            job.status = JobStatus.FAILED
            job.error_count += 1
            job.last_error = str(e)
            self.logger.error(f"Smart pipeline {job_id} failed with exception", error=str(e))
    
    async def _record_quota_usage(self, sources: Dict[str, bool], num_symbols: int):
        """Record quota usage after a successful run."""
        try:
            from app.service.quota_tracking_service import get_quota_tracking_service
            quota_service = get_quota_tracking_service()
            
            # Record NewsAPI usage
            if sources.get("include_newsapi", False):
                quota_service.record_usage("newsapi", num_symbols)
            
            # Record Marketaux usage (batched, so fewer requests)
            if sources.get("include_marketaux", False):
                # Marketaux batches 10 symbols per request
                requests = (num_symbols + 9) // 10
                quota_service.record_usage("marketaux", requests)
                
        except Exception as e:
            self.logger.warning(f"Failed to record quota usage: {e}")

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
        job.last_run = utc_now()
        
        try:
            self.logger.info(f"EXECUTING SCHEDULED JOB: Data Collection",
                           job_id=job_id, 
                           job_name=job.name,
                           symbols=job.parameters["symbols"][:5],  # Show first 5 symbols
                           lookback_days=job.parameters["lookback_days"])
            
            # Calculate date range
            end_date = to_naive_utc(utc_now())
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
        job.last_run = utc_now()
        
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
        job.last_run = utc_now()
        
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
        """List all scheduled jobs.

        This method populates the `next_run` field for each ScheduledJob by
        querying APScheduler's internal job metadata (next_run_time). Without
        this, frontend components will receive `next_run=None` and cannot
        display upcoming runs.
        """
        jobs_list: List[ScheduledJob] = []
        for job_id, job in self.jobs.items():
            try:
                aps_job = self.scheduler.get_job(job_id)
                if aps_job and getattr(aps_job, 'next_run_time', None):
                    # APScheduler returns timezone-aware datetimes; convert to naive UTC
                    next_run = aps_job.next_run_time
                    # Convert to naive UTC datetime for consistency with other code
                    try:
                        # If next_run has tzinfo, convert to UTC and drop tzinfo
                        next_run_utc = next_run.astimezone(pytz.utc).replace(tzinfo=None)
                    except Exception:
                        next_run_utc = next_run
                    job.next_run = next_run_utc
                else:
                    job.next_run = None
            except Exception as e:
                self.logger.warning(f"Failed to get APScheduler job metadata for {job_id}: {e}")
                job.next_run = None

            jobs_list.append(job)

        return jobs_list
    
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