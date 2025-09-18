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
import json
import sys
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from uuid import uuid4
import structlog
from pathlib import Path


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
        if self._initialized:
            return
            
        self._correlation_ids = {}
        self._logger = self._setup_logger()
        self._initialized = True
    
    def _setup_logger(self) -> structlog.BoundLogger:
        """Configure structured logging with proper formatting"""
        
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure structlog
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
        
        # Setup file handlers
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # File handler for all logs
        file_handler = logging.FileHandler(log_dir / "application.log")
        file_handler.setLevel(logging.INFO)
        
        # Console handler for development
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Error file handler
        error_handler = logging.FileHandler(log_dir / "errors.log")
        error_handler.setLevel(logging.ERROR)
        
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
            "timestamp": datetime.utcnow().isoformat(),
            "correlation_id": self.get_correlation_id(),
            **kwargs
        }
        return {k: v for k, v in context.items() if v is not None}
    
    def info(self, message: str, **kwargs):
        """Log info level message"""
        context = self._add_context(**kwargs)
        self._logger.info(message, **context)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message"""
        context = self._add_context(**kwargs)
        self._logger.warning(message, **context)
    
    def error(self, message: str, **kwargs):
        """Log error level message"""
        context = self._add_context(**kwargs)
        self._logger.error(message, **context)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message"""
        context = self._add_context(**kwargs)
        self._logger.debug(message, **context)
    
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