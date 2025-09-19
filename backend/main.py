"""
Main FastAPI Application
========================

Entry point for the Insight Stock Dashboard backend.
Implements the 5-layer architecture with proper dependency injection.
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
import time
from contextlib import asynccontextmanager

from app.infrastructure.config import get_settings
from app.presentation.routes import (
    dashboard_router,
    stocks_router,
    analysis_router,
    pipeline_router,
    admin_router
)
from app.presentation.middleware.logging_middleware import LoggingMiddleware
from app.presentation.middleware.security_middleware import setup_security_middleware
from app.data_access.database.connection import init_database
from app.business.scheduler import Scheduler


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

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Startup
    logger.info("Starting Insight Stock Dashboard Backend")
    
    # Initialize database
    await init_database()
    settings = get_settings()
    logger.info(f"Database URL: {settings.database_url.split('@')[0] + '@***' if '@' in settings.database_url else settings.database_url}")
    logger.info("Database initialized and configured")
    
    # Phase 7: Start Scheduler for automated pipeline orchestration
    scheduler = Scheduler()
    await scheduler.start()
    logger.info("Scheduler started for automated pipeline orchestration")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Insight Stock Dashboard Backend")
    
    # Phase 7: Stop Scheduler
    await scheduler.stop()
    logger.info("Phase 7: Scheduler stopped")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Backend API for sentiment analysis and stock market insights",
        docs_url="/api/docs" if settings.debug else None,
        redoc_url="/api/redoc" if settings.debug else None,
        openapi_url="/api/openapi.json" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Setup all security middleware (includes CORS, rate limiting, headers, etc.)
    setup_security_middleware(app, settings)
    
    # Add custom logging middleware (after security middleware)
    app.add_middleware(LoggingMiddleware)
    
    # Include routers - Phase 4, 5, 8 Implementation
    app.include_router(dashboard_router)  # Already has /api/dashboard prefix
    app.include_router(stocks_router)     # Already has /api/stocks prefix  
    app.include_router(analysis_router)   # Already has /api/analysis prefix
    app.include_router(pipeline_router)   # Phase 5: Pipeline management (admin only)
    app.include_router(admin_router, prefix="/api")  # Phase 8: Admin panel functionality
    
    # Global exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.error(
            "Validation error",
            path=request.url.path,
            method=request.method,
            errors=exc.errors()
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "details": exc.errors(),
                "timestamp": int(time.time())
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            exception=str(exc),
            exc_info=True
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal Server Error",
                "message": "An unexpected error occurred",
                "timestamp": int(time.time())
            }
        )
    
    # Health check endpoint
    @app.get("/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.app_name,
            "version": settings.app_version,
            "timestamp": int(time.time())
        }
    
    return app


# Create the application instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level=settings.log_level.lower(),
        access_log=True
    )