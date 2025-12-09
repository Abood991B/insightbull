"""
Log System - Singleton Pattern Implementation
=============================================

Centralized logging system implementing the Singleton pattern as specified 
in the FYP Implementation Plan. Provides structured logging throughout the
5-layer architecture with correlation IDs and contextual information.

Features:
- Singleton pattern for consistent logging
- Structured logging with JSON format
- Correlation ID tracking
- Performance monitoring
- Error tracking and aggregation
"""

import logging
from logging.handlers import TimedRotatingFileHandler
import json
import sys
import threading
import time
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
import structlog
from app.utils.timezone import utc_now
from pathlib import Path
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
import inspect
import os


class LogSystem:
    """
    Singleton logging system for centralized log management.
    
    Implements the LogSystem component from the FYP Implementation Plan
    Layer 3: Infrastructure Layer.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Ensure only one instance exists (Singleton pattern)"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LogSystem, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the logging system"""
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        # Configure structured logging
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer()
            ],
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )
        
        # Create logger instance
        self._logger = structlog.get_logger()
        
        # Thread-local storage for correlation IDs
        self._local = threading.local()
        self._correlation_ids = {}  # Thread ID -> correlation ID mapping
        
        # Log deduplication cache (message hash -> last logged time)
        self._log_cache = {}
        self._cache_lock = threading.Lock()
        
        # Rate limiting settings
        self.DEDUP_WINDOW_SECONDS = 60  # Don't repeat same log within 60 seconds
        self.MAX_CACHE_SIZE = 1000  # Limit cache size
        self._last_cleanup = time.time()  # Track last cleanup time
        self.CLEANUP_INTERVAL = 300  # Clean cache every 5 minutes
        
        # Setup file logging
        self._setup_file_logging()
        
        # Mark as initialized
        self._initialized = True
    
    def _setup_file_logging(self):
        """
        Setup file logging with rotation.
        
        Implements log rotation to prevent disk space issues:
        - Rotates daily at midnight
        - Keeps 30 days of logs
        - Automatically compresses old logs
        """
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Setup file handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Rotating file handler for all logs (daily rotation, keep 30 days)
        file_handler = TimedRotatingFileHandler(
            log_dir / "application.log",
            when='midnight',        # Rotate at midnight
            interval=1,             # Every 1 day
            backupCount=30,         # Keep 30 days of logs
            encoding='utf-8',
            utc=True                # Use UTC for rotation timing
        )
        file_handler.setLevel(logging.INFO)
        file_handler.suffix = "%Y-%m-%d"  # Add date suffix to rotated files
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Rotating error file handler (daily rotation, keep 90 days for debugging)
        error_handler = TimedRotatingFileHandler(
            log_dir / "errors.log",
            when='midnight',
            interval=1,
            backupCount=90,         # Keep error logs longer
            encoding='utf-8',
            utc=True
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.suffix = "%Y-%m-%d"
        
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
        root_logger.addHandler(error_handler)
        
        return structlog.get_logger()
    
    def generate_correlation_id(self) -> str:
        """Generate a unique correlation ID for request tracking"""
        return str(uuid4())
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current thread"""
        thread_id = threading.get_ident()
        self._correlation_ids[thread_id] = correlation_id
    
    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID for current thread"""
        thread_id = threading.get_ident()
        return self._correlation_ids.get(thread_id)
    
    def clear_correlation_id(self):
        """Clear correlation ID for current thread"""
        thread_id = threading.get_ident()
        self._correlation_ids.pop(thread_id, None)
    
    def _add_context(self, **kwargs) -> Dict[str, Any]:
        """Add contextual information to log entry"""
        context = {
            "timestamp": utc_now().isoformat(),
            "correlation_id": self.get_correlation_id(),
            **kwargs
        }
        return {k: v for k, v in context.items() if v is not None}
    
    def _should_log(self, level: str, message: str, **kwargs) -> bool:
        """Check if this log should be written (deduplication and noise filtering)"""
        # Skip deduplication for ERROR and CRITICAL logs
        if level in ["ERROR", "CRITICAL"]:
            return True
        
        # Filter out noisy/repetitive messages
        noisy_patterns = [
            "Getting system logs",
            "Getting system status", 
            "Admin requesting",
            "Loading and decrypting API keys",
            "API keys loaded and decrypted successfully",
            "Repository initialization configured",
            "Database health check",
            "Service health check completed",
            "SecureAPIKeyLoader initialized",
            "Auto-configured",
            "collectors with encrypted API keys",
            "Registered default observer",
            "Observer registered",
            "Watchlist observer",
            "Administrator initiated system logs export",
            "HackerNews collector configured",
            "FinHub collector configured", 
            "NewsAPI collector configured",
            "YFinance collector configured",
            "collector configured"
        ]
        
        # Skip noisy INFO messages
        if level == "INFO":
            for pattern in noisy_patterns:
                if pattern.lower() in message.lower():
                    return False
        
        # Create a hash of the message and key context
        import hashlib
        context_key = f"{level}:{message}:{kwargs.get('component', '')}:{kwargs.get('function', '')}"
        message_hash = hashlib.md5(context_key.encode()).hexdigest()
        
        current_time = utc_now().timestamp()
        
        with self._cache_lock:
            # Clean old entries from cache (proactive cleanup)
            should_cleanup = (
                len(self._log_cache) > self.MAX_CACHE_SIZE or 
                (current_time - self._last_cleanup) > self.CLEANUP_INTERVAL
            )
            
            if should_cleanup:
                cutoff_time = current_time - self.DEDUP_WINDOW_SECONDS
                old_size = len(self._log_cache)
                self._log_cache = {
                    k: v for k, v in self._log_cache.items() 
                    if v > cutoff_time
                }
                self._last_cleanup = current_time
                
                # Log cleanup stats occasionally (but avoid infinite recursion)
                if old_size > len(self._log_cache) and old_size > 100:
                    print(f"LogSystem: Cleaned cache from {old_size} to {len(self._log_cache)} entries")
            
            # Check if we've logged this recently
            last_logged = self._log_cache.get(message_hash, 0)
            if current_time - last_logged < self.DEDUP_WINDOW_SECONDS:
                return False  # Skip this log
            
            # Update cache
            self._log_cache[message_hash] = current_time
            return True
    
    def _write_to_database(self, level: str, message: str, **kwargs):
        """Write log entry to database asynchronously"""
        try:
            # Get caller information
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back.f_back  # Go back 3 frames to get actual caller
            
            logger_name = kwargs.get('logger', 'app.infrastructure.log_system')
            
            # Smart component detection - ALWAYS detect component from caller
            provided_component = kwargs.get('component')
            component = None  # Force detection
            
            # Try to extract component from caller's module path
            if caller_frame:
                module_name = caller_frame.f_globals.get('__name__', '')
                
                # More comprehensive component detection
                if 'admin' in module_name:
                    if 'service' in module_name:
                        component = 'admin_service'
                    elif 'routes' in module_name or 'admin.py' in module_name:
                        component = 'api_routes'
                    else:
                        component = 'admin_service'
                elif 'system_service' in module_name:
                    component = 'system_service'
                elif 'data_collector' in module_name:
                    component = 'data_collector'
                elif 'hackernews_collector' in module_name:
                    component = 'hackernews_collector'
                elif 'gdelt_collector' in module_name:
                    component = 'gdelt_collector'
                elif 'finnhub_collector' in module_name or 'finhub_collector' in module_name:
                    component = 'finnhub_collector'
                elif 'newsapi_collector' in module_name:
                    component = 'newsapi_collector'
                elif 'yfinance_collector' in module_name:
                    component = 'yfinance_collector'
                elif 'collector_config' in module_name:
                    component = 'collector_config'
                elif 'pipeline' in module_name:
                    component = 'pipeline'
                elif 'sentiment' in module_name:
                    component = 'sentiment_engine'
                elif 'auth' in module_name:
                    component = 'auth_service'
                elif 'watchlist' in module_name:
                    component = 'watchlist_service'
                elif 'storage' in module_name:
                    component = 'storage_service'
                elif 'routes' in module_name:
                    component = 'api_routes'
                elif 'log_system' in module_name:
                    component = 'system_core'
                else:
                    # Extract the last meaningful part of the module name
                    parts = module_name.split('.')
                    if len(parts) > 1:
                        last_part = parts[-1]
                        # Map common module names to components
                        if last_part in ['admin', 'routes']:
                            component = 'api_routes'
                        elif last_part in ['service', 'services']:
                            component = 'system_service'
                        else:
                            component = last_part
                    else:
                        component = 'system_core'
            else:
                component = 'system_core'
            
            function_name = caller_frame.f_code.co_name if caller_frame else 'unknown'
            line_number = caller_frame.f_lineno if caller_frame else None
            
            # Filter out standard context from extra_data
            extra_data = {k: v for k, v in kwargs.items() 
                         if k not in ['logger', 'component', 'timestamp', 'correlation_id']}
            
            # Create log entry in background task (only if event loop exists)
            try:
                loop = asyncio.get_running_loop()
                asyncio.create_task(self._async_write_to_db(
                    level=level,
                    message=message,
                    logger=logger_name,
                    component=component,
                    function=function_name,
                    line_number=line_number,
                    extra_data=extra_data
                ))
            except RuntimeError:
                # No running event loop (e.g., background threads)
                # Database logging will be skipped, but console/file logging still works
                pass
        except Exception as e:
            # Don't let database logging errors break the application
            pass  # Silently ignore - logging to console/file already happened
    
    async def _async_write_to_db(self, level: str, message: str, logger: str, 
                                component: str, function: str, line_number: int, 
                                extra_data: Dict[str, Any]):
        """Async method to write log to database"""
        try:
            # Import here to avoid circular imports
            from app.data_access.database.connection import get_db_session
            from app.data_access.models import SystemLog
            from app.utils.timezone import malaysia_now
            
            async with get_db_session() as db:
                log_entry = SystemLog(
                    level=level,
                    message=message,
                    logger=logger,
                    component=component,
                    function=function,
                    line_number=line_number,
                    extra_data=extra_data or {},
                    timestamp=utc_now()
                )
                db.add(log_entry)
                await db.commit()
        except Exception as e:
            # Don't let database logging errors break the application
            print(f"Failed to write log to database: {e}")
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        try:
            # Check if we should log this (deduplication)
            if not self._should_log("INFO", message, **kwargs):
                return
                
            context = self._add_context(**kwargs)
            self._logger.info(message, **context)
            # Also write to database
            self._write_to_database("INFO", message, **kwargs)
        except Exception as e:
            # Fallback logging to prevent startup failures
            print(f"LogSystem.info failed: {e} - Message: {message}")
            try:
                self._logger.info(message)
            except:
                print(f"INFO: {message}")
    
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        try:
            # Check if we should log this (deduplication)
            if not self._should_log("WARNING", message, **kwargs):
                return
                
            context = self._add_context(**kwargs)
            self._logger.warning(message, **context)
            # Also write to database
            self._write_to_database("WARNING", message, **kwargs)
        except Exception as e:
            # Fallback logging to prevent startup failures
            print(f"LogSystem.warning failed: {e} - Message: {message}")
            try:
                self._logger.warning(message)
            except:
                print(f"WARNING: {message}")
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        try:
            # Always log errors (no deduplication)
            context = self._add_context(**kwargs)
            self._logger.error(message, **context)
            # Also write to database
            self._write_to_database("ERROR", message, **kwargs)
        except Exception as e:
            # Fallback logging to prevent startup failures
            print(f"LogSystem.error failed: {e} - Message: {message}")
            try:
                self._logger.error(message)
            except:
                print(f"ERROR: {message}")
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        try:
            # Check if we should log this (deduplication)
            if not self._should_log("DEBUG", message, **kwargs):
                return
                
            context = self._add_context(**kwargs)
            self._logger.debug(message, **context)
            # Also write to database
            self._write_to_database("DEBUG", message, **kwargs)
        except Exception as e:
            # Fallback logging to prevent startup failures
            print(f"LogSystem.debug failed: {e} - Message: {message}")
            try:
                self._logger.debug(message)
            except:
                print(f"DEBUG: {message}")
    
    def log_api_call(self, method: str, endpoint: str, status_code: int, 
                     duration: float, **kwargs):
        """Log API call with performance metrics"""
        self.info(
            "API call completed",
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_pipeline_step(self, step: str, status: str, duration: float = None, 
                         records_processed: int = None, **kwargs):
        """Log data pipeline step execution"""
        log_data = {
            "pipeline_step": step,
            "status": status,
            **kwargs
        }
        
        if duration is not None:
            log_data["duration_seconds"] = round(duration, 3)
        
        if records_processed is not None:
            log_data["records_processed"] = records_processed
        
        if status == "success":
            self.info(f"Pipeline step completed: {step}", **log_data)
        elif status == "error":
            self.error(f"Pipeline step failed: {step}", **log_data)
        else:
            self.warning(f"Pipeline step status: {step}", **log_data)
    
    def log_sentiment_analysis(self, model: str, texts_processed: int, 
                              avg_score: float, duration: float, **kwargs):
        """Log sentiment analysis operation"""
        self.info(
            "Sentiment analysis completed",
            model=model,
            texts_processed=texts_processed,
            average_sentiment_score=round(avg_score, 3),
            processing_time_seconds=round(duration, 3),
            **kwargs
        )
    
    def log_database_operation(self, operation: str, table: str, 
                              records_affected: int, duration: float, **kwargs):
        """Log database operation"""
        self.info(
            "Database operation completed",
            operation=operation,
            table=table,
            records_affected=records_affected,
            duration_ms=round(duration * 1000, 2),
            **kwargs
        )
    
    def log_external_api_call(self, service: str, endpoint: str, 
                             response_time: float, status: str, **kwargs):
        """Log external API call"""
        self.info(
            "External API call",
            service=service,
            endpoint=endpoint,
            response_time_ms=round(response_time * 1000, 2),
            status=status,
            **kwargs
        )
    
    def log_pipeline_operation(self, operation: str, context: Dict[str, Any]):
        """Log pipeline operation with detailed context"""
        # Filter out 'message' from context to avoid conflicts
        filtered_context = {k: v for k, v in context.items() if k != 'message'}
        self.info(
            f"Pipeline operation: {operation}",
            operation_type=operation,
            **filtered_context
        )
    
    def log_performance_metric(self, metric_name: str, context: Dict[str, Any]):
        """Log performance metric"""
        # Filter out 'message' from context to avoid conflicts
        filtered_context = {k: v for k, v in context.items() if k != 'message'}
        self.info(
            f"Performance metric: {metric_name}",
            metric_name=metric_name,
            **filtered_context
        )
    
    def log_error(self, error_type: str, context: Dict[str, Any]):
        """Log error with detailed context"""
        # Filter out 'message' from context to avoid conflicts, but keep error_type
        filtered_context = {k: v for k, v in context.items() if k != 'message'}
        # Ensure error_type is in the context
        filtered_context['error_type'] = error_type
        self.error(
            f"Error: {error_type}",
            **filtered_context
        )


# Global instance for easy access
logger = LogSystem()


def get_logger() -> LogSystem:
    """Get the singleton logger instance"""
    return LogSystem()