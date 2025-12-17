"""
Security Middleware for API Protection

This module implements comprehensive security middleware including:
- Rate limiting per IP address
- CORS configuration  
- Input validation and sanitization
- Security headers
- Request logging

Following FYP security requirements and best practices.
"""

import time
from typing import Dict, Any, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import json

from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.infrastructure.config.settings import Settings
from app.infrastructure.security.security_utils import SecurityUtils

# Use centralized logging system
from app.infrastructure.log_system import get_logger
logger = get_logger()


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent API abuse
    
    Implements sliding window rate limiter with per-IP tracking
    """
    
    def __init__(self, app, requests_per_window: int = 100, window_seconds: int = 3600):
        super().__init__(app)
        self.requests_per_window = requests_per_window
        self.window_seconds = window_seconds
        self.client_requests: Dict[str, deque] = defaultdict(deque)
    
    async def dispatch(self, request: Request, call_next):
        """Process request with rate limiting"""
        client_ip = self.get_client_ip(request)
        
        # Exempt localhost/development IPs from rate limiting
        # This prevents blocking during development when frontend auto-refreshes
        localhost_ips = ["127.0.0.1", "localhost", "::1", "0.0.0.0"]
        if client_ip in localhost_ips or client_ip == "unknown":
            # Skip rate limiting for local development
            response = await call_next(request)
            return response
        
        current_time = time.time()
        
        # Clean old requests outside the window
        self.cleanup_old_requests(client_ip, current_time)
        
        # Check if client has exceeded rate limit
        if len(self.client_requests[client_ip]) >= self.requests_per_window:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=429,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(self.window_seconds)}
            )
        
        # Add current request timestamp
        self.client_requests[client_ip].append(current_time)
        
        # Process request
        response = await call_next(request)
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        forwarded_host = request.headers.get("X-Forwarded-Host")
        if forwarded_host:
            return forwarded_host
        
        # Direct connection
        return request.client.host if request.client else "unknown"
    
    def cleanup_old_requests(self, client_ip: str, current_time: float):
        """Remove requests older than the time window"""
        window_start = current_time - self.window_seconds
        client_deque = self.client_requests[client_ip]
        
        while client_deque and client_deque[0] < window_start:
            client_deque.popleft()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Security headers middleware
    
    Adds security headers to all responses
    """
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.security_utils = SecurityUtils()
    
    async def dispatch(self, request: Request, call_next):
        """Add security headers to response"""
        response = await call_next(request)
        
        if self.settings.enable_security_headers:
            headers = self.security_utils.get_security_headers()
            
            for header_name, header_value in headers.items():
                response.headers[header_name] = header_value
        
        return response


class InputValidationMiddleware(BaseHTTPMiddleware):
    """
    Input validation and sanitization middleware
    
    Validates and sanitizes request data to prevent attacks
    """
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
        self.security_utils = SecurityUtils()
        self.max_request_size = 10 * 1024 * 1024  # 10MB
    
    async def dispatch(self, request: Request, call_next):
        """Validate and sanitize request data"""
        
        # Check request size
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(f"Request too large from IP: {self.get_client_ip(request)}")
            raise HTTPException(
                status_code=413,
                detail="Request entity too large"
            )
        
        # Validate request method
        if request.method not in ["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"]:
            logger.warning(f"Invalid HTTP method: {request.method}")
            raise HTTPException(
                status_code=405,
                detail="Method not allowed"
            )
        
        # Sanitize query parameters
        if request.query_params:
            self.sanitize_query_params(request)
        
        # Log suspicious requests
        self.log_suspicious_activity(request)
        
        response = await call_next(request)
        return response
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
    
    def sanitize_query_params(self, request: Request):
        """Sanitize query parameters"""
        suspicious_patterns = [
            '<script', 'javascript:', 'onload=', 'onerror=',
            'DROP TABLE', 'DELETE FROM', 'INSERT INTO',
            '../', '..\\', '/etc/passwd', 'cmd.exe'
        ]
        
        for key, value in request.query_params.items():
            value_lower = value.lower()
            for pattern in suspicious_patterns:
                if pattern.lower() in value_lower:
                    logger.warning(f"Suspicious query parameter detected: {key}={value}")
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid request parameters"
                    )
    
    def log_suspicious_activity(self, request: Request):
        """Log potentially suspicious requests"""
        user_agent = request.headers.get("user-agent", "").lower()
        client_ip = self.get_client_ip(request)
        
        # Check for suspicious user agents
        suspicious_agents = [
            'sqlmap', 'nikto', 'nmap', 'masscan', 'nessus',
            'openvas', 'burp', 'w3af', 'havij', 'pangolin'
        ]
        
        for agent in suspicious_agents:
            if agent in user_agent:
                logger.warning(f"Suspicious user agent from IP {client_ip}: {user_agent}")
                break


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request logging middleware for audit trail
    
    Logs all requests with details for monitoring and debugging
    """
    
    def __init__(self, app, settings: Settings):
        super().__init__(app)
        self.settings = settings
    
    async def dispatch(self, request: Request, call_next):
        """Log request details"""
        start_time = time.time()
        client_ip = self.get_client_ip(request)
        
        # Log request
        logger.info(f"Request: {request.method} {request.url.path} from {client_ip}")
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            # Log response
            logger.info(
                f"Response: {response.status_code} for {request.method} "
                f"{request.url.path} in {process_time:.3f}s"
            )
            
            # Add process time header
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"Error: {str(e)} for {request.method} {request.url.path} "
                f"in {process_time:.3f}s"
            )
            raise
    
    def get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


def setup_cors_middleware(app, settings: Settings):
    """
    Setup CORS middleware with proper configuration
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    allowed_origins = settings.get_allowed_origins_list()
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        allow_headers=[
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-CSRF-Token",
            "X-Requested-With"
        ],
        expose_headers=["X-Process-Time"],
        max_age=3600,  # Cache preflight response for 1 hour
    )


def setup_security_middleware(app, settings: Settings):
    """
    Setup all security middleware
    
    Args:
        app: FastAPI application instance
        settings: Application settings
    """
    # Add middleware in reverse order (they execute in LIFO order)
    
    # NOTE: Request logging handled by LoggingMiddleware in main.py
    # Removed RequestLoggingMiddleware to avoid duplicate HTTP logs
    
    # Security headers
    app.add_middleware(SecurityHeadersMiddleware, settings=settings)
    
    # Input validation
    app.add_middleware(InputValidationMiddleware, settings=settings)
    
    # Rate limiting (innermost)
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_window=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window
    )
    
    # CORS
    setup_cors_middleware(app, settings)