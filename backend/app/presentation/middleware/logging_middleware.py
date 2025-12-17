"""
Logging Middleware
==================

Custom middleware for request/response logging using structured logging.
Implements smart filtering to reduce noise from high-frequency polling endpoints.
"""

import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Set


logger = structlog.get_logger()


# High-frequency endpoints that should not be logged on every request
# These are polled frequently by the frontend and create excessive log noise
QUIET_ENDPOINTS: Set[str] = {
    "/api/admin/scheduler/events",      # Polled every 5 seconds
    "/api/admin/scheduler/jobs",        # Polled every 30 seconds  
    "/api/admin/market/status",         # Polled every 10 seconds
    "/api/stocks/market/status",        # Polled every 10 seconds
    "/api/dashboard/overview",          # Auto-refresh
    "/health",                          # Health checks
    "/api/admin/scheduler/history",     # History polling
    "/api/admin/collectors/health",     # Health polling
}

# Only log these endpoints if they return an error status code
QUIET_SUCCESS_ONLY_ENDPOINTS: Set[str] = {
    "/api/stocks/prices/latest",        # Price updates
}

# Skip OPTIONS requests entirely (CORS preflight)
SKIP_METHODS: Set[str] = {"OPTIONS"}


class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging HTTP requests and responses.
    
    Implements smart filtering to reduce log noise:
    - High-frequency polling endpoints are not logged unless they fail
    - Successful responses on quiet endpoints are skipped
    - Errors are always logged regardless of endpoint
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()
        path = request.url.path
        method = request.method
        
        # Skip OPTIONS requests entirely (CORS preflight - very noisy)
        if method in SKIP_METHODS:
            return await call_next(request)
        
        # Determine logging behavior for this endpoint
        should_skip_logging = path in QUIET_ENDPOINTS
        should_log_errors_only = path in QUIET_SUCCESS_ONLY_ENDPOINTS
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add processing time header (always)
            response.headers["X-Process-Time"] = str(process_time)
            
            # Determine if we should log this response
            is_error = response.status_code >= 400
            should_log = (
                is_error or  # Always log errors
                (not should_skip_logging and not should_log_errors_only) or  # Normal endpoints
                (should_log_errors_only and is_error)  # Error-only endpoints with error
            )
            
            if should_log:
                log_level = logger.warning if response.status_code >= 400 else logger.info
                log_level(
                    "HTTP",
                    method=request.method,
                    path=path,
                    status=response.status_code,
                    duration_ms=round(process_time * 1000, 2),
                    client=request.client.host if request.client else "unknown"
                )
            
            return response
            
        except Exception as exc:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Always log errors
            logger.error(
                "HTTP error",
                method=request.method,
                path=path,
                exception=str(exc),
                duration_ms=round(process_time * 1000, 2),
                client=request.client.host if request.client else "unknown",
                exc_info=True
            )
            
            # Re-raise the exception
            raise exc