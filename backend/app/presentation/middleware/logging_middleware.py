"""
Logging Middleware
==================

Custom middleware for request/response logging using structured logging.
"""

import time
import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable


logger = structlog.get_logger()


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details."""
        start_time = time.time()
        
        # Extract request information
        request_info = {
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params),
            "client_ip": request.client.host if request.client else "unknown",
            "user_agent": request.headers.get("user-agent", "unknown"),
            "request_id": id(request)  # Simple request ID
        }
        
        # Log incoming request
        logger.info("Request started", **request_info)
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                "Request completed",
                **request_info,
                status_code=response.status_code,
                process_time_ms=round(process_time * 1000, 2)
            )
            
            # Add processing time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as exc:
            # Calculate processing time for failed requests
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                **request_info,
                exception=str(exc),
                process_time_ms=round(process_time * 1000, 2),
                exc_info=True
            )
            
            # Re-raise the exception
            raise exc