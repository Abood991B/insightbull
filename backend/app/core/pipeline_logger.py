"""
Pipeline Operations Logger
Implements SY-FR9: Log Pipeline Operations from FYP Report
"""
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager

from app.core.database import AsyncSessionLocal
from app.models import SystemLog


class LogLevel(Enum):
    """Log levels for pipeline operations"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class PipelineStage(Enum):
    """Pipeline stages for categorizing operations"""
    INITIALIZATION = "initialization"
    DATA_COLLECTION = "data_collection"
    PREPROCESSING = "preprocessing"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    CORRELATION_ANALYSIS = "correlation_analysis"
    STORAGE = "storage"
    CLEANUP = "cleanup"
    COMPLETION = "completion"


class PipelineLogger:
    """
    Comprehensive logging service for pipeline operations
    Addresses SY-FR9 functional requirement from FYP Report
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session: Optional[AsyncSession] = None
        self.pipeline_id: Optional[str] = None
        self.start_time: Optional[datetime] = None
        self.stage_times: Dict[str, datetime] = {}
        
    async def initialize_pipeline_run(self, pipeline_id: str) -> None:
        """Initialize a new pipeline run with logging"""
        self.pipeline_id = pipeline_id
        self.start_time = datetime.utcnow()
        self.session = AsyncSessionLocal()
        
        await self.log_operation(
            stage=PipelineStage.INITIALIZATION,
            level=LogLevel.INFO,
            message=f"Pipeline {pipeline_id} started",
            details={"start_time": self.start_time.isoformat()}
        )
    
    async def log_stage_start(self, stage: PipelineStage, details: Optional[Dict[str, Any]] = None) -> None:
        """Log the start of a pipeline stage"""
        stage_start_time = datetime.utcnow()
        self.stage_times[f"{stage.value}_start"] = stage_start_time
        
        await self.log_operation(
            stage=stage,
            level=LogLevel.INFO,
            message=f"Stage {stage.value} started",
            details=details or {}
        )
    
    async def log_stage_completion(
        self, 
        stage: PipelineStage, 
        success: bool = True,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log the completion of a pipeline stage"""
        completion_time = datetime.utcnow()
        start_key = f"{stage.value}_start"
        
        stage_duration = None
        if start_key in self.stage_times:
            stage_duration = (completion_time - self.stage_times[start_key]).total_seconds()
        
        status = "completed" if success else "failed"
        level = LogLevel.INFO if success else LogLevel.ERROR
        
        log_details = details or {}
        if stage_duration:
            log_details["duration_seconds"] = stage_duration
        
        await self.log_operation(
            stage=stage,
            level=level,
            message=f"Stage {stage.value} {status}",
            details=log_details
        )
    
    async def log_data_collection_stats(
        self, 
        source: str, 
        records_collected: int,
        errors: int = 0,
        rate_limited: bool = False
    ) -> None:
        """Log data collection statistics"""
        details = {
            "source": source,
            "records_collected": records_collected,
            "errors": errors,
            "rate_limited": rate_limited
        }
        
        level = LogLevel.WARNING if errors > 0 or rate_limited else LogLevel.INFO
        message = f"Data collection from {source}: {records_collected} records"
        
        if errors > 0:
            message += f", {errors} errors"
        if rate_limited:
            message += ", rate limited"
        
        await self.log_operation(
            stage=PipelineStage.DATA_COLLECTION,
            level=level,
            message=message,
            details=details
        )
    
    async def log_sentiment_analysis_stats(
        self,
        model_name: str,
        records_processed: int,
        processing_time: float,
        errors: int = 0
    ) -> None:
        """Log sentiment analysis statistics"""
        details = {
            "model": model_name,
            "records_processed": records_processed,
            "processing_time_seconds": processing_time,
            "errors": errors,
            "avg_time_per_record": processing_time / max(records_processed, 1)
        }
        
        level = LogLevel.WARNING if errors > 0 else LogLevel.INFO
        message = f"Sentiment analysis with {model_name}: {records_processed} records in {processing_time:.2f}s"
        
        await self.log_operation(
            stage=PipelineStage.SENTIMENT_ANALYSIS,
            level=level,
            message=message,
            details=details
        )
    
    async def log_correlation_analysis(
        self,
        stock_symbol: str,
        correlation_value: float,
        time_window: str,
        data_points: int
    ) -> None:
        """Log correlation analysis results"""
        details = {
            "stock_symbol": stock_symbol,
            "correlation_value": correlation_value,
            "time_window": time_window,
            "data_points": data_points
        }
        
        await self.log_operation(
            stage=PipelineStage.CORRELATION_ANALYSIS,
            level=LogLevel.INFO,
            message=f"Correlation analysis for {stock_symbol}: {correlation_value:.4f}",
            details=details
        )
    
    async def log_error(
        self,
        stage: PipelineStage,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log pipeline errors with context"""
        details = {
            "error_type": type(error).__name__,
            "error_message": str(error),
            "context": context or {}
        }
        
        await self.log_operation(
            stage=stage,
            level=LogLevel.ERROR,
            message=f"Error in {stage.value}: {str(error)}",
            details=details
        )
    
    async def log_performance_metrics(
        self,
        stage: PipelineStage,
        metrics: Dict[str, Any]
    ) -> None:
        """Log performance metrics for pipeline stages"""
        await self.log_operation(
            stage=stage,
            level=LogLevel.INFO,
            message=f"Performance metrics for {stage.value}",
            details=metrics
        )
    
    async def log_operation(
        self,
        stage: PipelineStage,
        level: LogLevel,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a pipeline operation to both file and database"""
        # Log to file
        log_func = getattr(self.logger, level.value)
        log_func(f"[{self.pipeline_id}] [{stage.value}] {message}")
        
        # Log to database if session is available
        if self.session:
            try:
                system_log = SystemLog(
                    level=level.value,
                    source=f"pipeline_{stage.value}",
                    message=message,
                    details=details,
                    pipeline_id=self.pipeline_id
                )
                
                self.session.add(system_log)
                await self.session.commit()
                
            except Exception as e:
                self.logger.error(f"Failed to log to database: {e}")
                # Don't let logging failures break the pipeline
    
    async def complete_pipeline_run(self, success: bool = True, summary: Optional[Dict[str, Any]] = None) -> None:
        """Complete the pipeline run and log final statistics"""
        if not self.start_time:
            return
        
        end_time = datetime.utcnow()
        total_duration = (end_time - self.start_time).total_seconds()
        
        final_details = {
            "total_duration_seconds": total_duration,
            "success": success,
            "summary": summary or {}
        }
        
        level = LogLevel.INFO if success else LogLevel.ERROR
        status = "completed successfully" if success else "failed"
        
        await self.log_operation(
            stage=PipelineStage.COMPLETION,
            level=level,
            message=f"Pipeline {self.pipeline_id} {status} in {total_duration:.2f} seconds",
            details=final_details
        )
        
        # Close database session
        if self.session:
            await self.session.close()
            self.session = None
    
    @asynccontextmanager
    async def stage_context(self, stage: PipelineStage, details: Optional[Dict[str, Any]] = None):
        """Context manager for automatic stage logging"""
        await self.log_stage_start(stage, details)
        success = True
        stage_details = details or {}
        
        try:
            yield
        except Exception as e:
            success = False
            stage_details["error"] = str(e)
            await self.log_error(stage, e)
            raise
        finally:
            await self.log_stage_completion(stage, success, stage_details)


class PipelineLoggerFactory:
    """Factory for creating pipeline loggers"""
    
    @staticmethod
    async def create_pipeline_logger(pipeline_type: str = "data_pipeline") -> PipelineLogger:
        """Create a new pipeline logger with unique ID"""
        pipeline_id = f"{pipeline_type}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        logger = PipelineLogger()
        await logger.initialize_pipeline_run(pipeline_id)
        return logger


# Global logger for pipeline operations
_global_pipeline_logger: Optional[PipelineLogger] = None

async def get_pipeline_logger() -> PipelineLogger:
    """Get or create global pipeline logger"""
    global _global_pipeline_logger
    
    if _global_pipeline_logger is None:
        _global_pipeline_logger = await PipelineLoggerFactory.create_pipeline_logger()
    
    return _global_pipeline_logger

async def create_new_pipeline_logger(pipeline_type: str = "data_pipeline") -> PipelineLogger:
    """Create a new pipeline logger for a specific run"""
    return await PipelineLoggerFactory.create_pipeline_logger(pipeline_type)


# Decorator for automatic pipeline operation logging
def log_pipeline_operation(stage: PipelineStage):
    """Decorator to automatically log pipeline operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = await get_pipeline_logger()
            
            async with logger.stage_context(stage):
                result = await func(*args, **kwargs)
                return result
        
        return wrapper
    return decorator


# Example usage functions for testing
async def example_pipeline_run():
    """Example of how to use the pipeline logger"""
    logger = await create_new_pipeline_logger("example_pipeline")
    
    try:
        # Data collection stage
        async with logger.stage_context(PipelineStage.DATA_COLLECTION):
            await asyncio.sleep(1)  # Simulate work
            await logger.log_data_collection_stats("reddit", 150, errors=2)
            await logger.log_data_collection_stats("finnhub", 200, rate_limited=True)
        
        # Sentiment analysis stage
        async with logger.stage_context(PipelineStage.SENTIMENT_ANALYSIS):
            await asyncio.sleep(2)  # Simulate work
            await logger.log_sentiment_analysis_stats("FinBERT", 200, 45.5, errors=1)
            await logger.log_sentiment_analysis_stats("VADER", 150, 12.3)
        
        # Correlation analysis stage
        async with logger.stage_context(PipelineStage.CORRELATION_ANALYSIS):
            await logger.log_correlation_analysis("MSFT", 0.65, "7d", 100)
            await logger.log_correlation_analysis("AAPL", 0.72, "7d", 95)
        
        # Complete successfully
        summary = {
            "total_records_processed": 350,
            "total_errors": 3,
            "stocks_analyzed": 2
        }
        await logger.complete_pipeline_run(success=True, summary=summary)
        
    except Exception as e:
        await logger.complete_pipeline_run(success=False)
        raise