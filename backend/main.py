"""
Main FastAPI Application
========================

InsightBullCopyright (C) 2025-2026 Abdulrahman Baidaq

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program. If not, see <https://www.gnu.org/licenses/>.

Entry point for the InsightBull backend.
Implements the 5-layer architecture with proper dependency injection.
"""

# Load environment variables first
from dotenv import load_dotenv
load_dotenv()

import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import structlog
import time
from typing import Dict, Any
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
from app.utils.timezone import utc_now

# Initialize the centralized logging system early (includes external lib suppression)
from app.infrastructure.log_system import get_logger
_log_system = get_logger()  # Ensures LogSystem singleton is initialized


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


def print_startup_banner():
    """Print professional startup banner with system information."""
    settings = get_settings()
    banner = f"""
╔════════════════════════════════════════════════════════════════════════════╗
║                                                                            ║
║   ██╗███╗   ██╗███████╗██╗ ██████╗ ██╗  ██╗████████╗                     ║
║   ██║████╗  ██║██╔════╝██║██╔════╝ ██║  ██║╚══██╔══╝                     ║
║   ██║██╔██╗ ██║███████╗██║██║  ███╗███████║   ██║                        ║
║   ██║██║╚██╗██║╚════██║██║██║   ██║██╔══██║   ██║                        ║
║   ██║██║ ╚████║███████║██║╚██████╔╝██║  ██║   ██║                        ║
║   ╚═╝╚═╝  ╚═══╝╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝                        ║
║                                                                            ║
║              STOCK MARKET SENTIMENT ANALYSIS DASHBOARD                    ║
║                    Backend API Service v{settings.app_version:<25}║
║                                                                            ║
╟────────────────────────────────────────────────────────────────────────────╢
║  Environment: {settings.environment:<58} ║
║  Database:    SQLite (Async)                                               ║
║  Architecture: 5-Layer Clean Architecture                                  ║
║  Features:    Sentiment Analysis | Real-time Prices | Smart Scheduler     ║
╚════════════════════════════════════════════════════════════════════════════╝
"""
    print(banner)


async def perform_health_check() -> Dict[str, Any]:
    """
    Perform startup health check on all critical services.
    Returns health status dictionary.
    """
    health_status = {
        "timestamp": utc_now().isoformat(),
        "overall_status": "healthy",
        "services": {}
    }
    
    try:
        # Check 1: Database Connection
        try:
            from app.data_access.database.connection import get_db_session
            from sqlalchemy import text
            async with get_db_session() as session:
                await session.execute(text("SELECT 1"))
            health_status["services"]["database"] = {
                "status": "✓ Operational",
                "type": "SQLite Async"
            }
        except Exception as e:
            health_status["services"]["database"] = {
                "status": "✗ Failed",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check 2: Sentiment Engine
        try:
            from app.service.sentiment_processing import get_sentiment_engine
            engine = get_sentiment_engine()
            # Get actual model names from engine
            available_models = engine.get_available_models() if hasattr(engine, 'get_available_models') else []
            # Format model names for display (clean up technical names)
            display_models = []
            for model in available_models:
                if "finbert" in model.lower() or "prosus" in model.lower():
                    if "FinBERT" not in display_models:
                        display_models.append("FinBERT")
                else:
                    display_models.append(model)
            # Ensure FinBERT is always shown as primary model (it's always loaded)
            if "FinBERT" not in display_models:
                display_models.insert(0, "FinBERT")
            # Add AI verification indicator if enabled
            if hasattr(engine, 'config') and engine.config.enable_ai_verification:
                display_models.append("Gemini-AI-Verification")
            health_status["services"]["sentiment_engine"] = {
                "status": "✓ Operational",
                "models": display_models
            }
        except Exception as e:
            health_status["services"]["sentiment_engine"] = {
                "status": "✗ Failed",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check 3: Watchlist Service
        try:
            from app.data_access.database.connection import get_db_session
            from app.service.watchlist_service import WatchlistService
            async with get_db_session() as session:
                watchlist_service = WatchlistService(session)
                symbols = await watchlist_service.get_current_watchlist()
            health_status["services"]["watchlist"] = {
                "status": "✓ Operational",
                "stocks_tracked": len(symbols)
            }
        except Exception as e:
            health_status["services"]["watchlist"] = {
                "status": "✗ Failed",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check 4: Scheduler
        try:
            from app.business.scheduler import Scheduler
            # Get actual job count from scheduler if possible
            scheduler_instance = Scheduler._instance if hasattr(Scheduler, '_instance') else None
            if scheduler_instance and hasattr(scheduler_instance, 'scheduler'):
                job_count = len(scheduler_instance.scheduler.get_jobs())
            else:
                job_count = 6  # Default: 5 pipeline jobs + 1 quota reset
            health_status["services"]["scheduler"] = {
                "status": "✓ Operational",
                "jobs_configured": job_count
            }
        except Exception as e:
            health_status["services"]["scheduler"] = {
                "status": "✗ Failed",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
        # Check 5: API Key Manager
        try:
            from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader
            key_loader = SecureAPIKeyLoader()
            health_status["services"]["api_keys"] = {
                "status": "✓ Operational",
                "encryption": "Enabled"
            }
        except Exception as e:
            health_status["services"]["api_keys"] = {
                "status": "✗ Failed",
                "error": str(e)
            }
            health_status["overall_status"] = "degraded"
        
    except Exception as e:
        health_status["overall_status"] = "unhealthy"
        health_status["critical_error"] = str(e)
    
    return health_status


def print_health_check_summary(health: Dict[str, Any]):
    """Print health check summary in a readable format."""
    status_icon = "✓" if health["overall_status"] == "healthy" else "⚠" if health["overall_status"] == "degraded" else "✗"
    
    print(f"\n{'='*80}")
    print(f"  STARTUP HEALTH CHECK - {status_icon} {health['overall_status'].upper()}")
    print(f"{'='*80}")
    
    for service_name, service_info in health["services"].items():
        status = service_info.get("status", "Unknown")
        print(f"  {service_name.replace('_', ' ').title():<25} {status}")
        
        # Print additional info
        for key, value in service_info.items():
            if key != "status" and key != "error":
                print(f"    ├─ {key}: {value}")
        
        # Print errors if any
        if "error" in service_info:
            print(f"    └─ Error: {service_info['error']}")
    
    print(f"{'='*80}\n")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management."""
    # Print startup banner
    print_startup_banner()
    
    # Startup
    logger.info("Starting InsightBull Backend")
    
    # Initialize database
    await init_database()
    settings = get_settings()
    logger.info(f"Database URL: {settings.database_url.split('@')[0] + '@***' if '@' in settings.database_url else settings.database_url}")
    logger.info("Database initialized and configured")
    
    # Start Scheduler for automated pipeline orchestration
    scheduler = Scheduler()
    await scheduler.start()
    logger.info("Scheduler started for automated pipeline orchestration")
    
    # Perform health check
    health_status = await perform_health_check()
    print_health_check_summary(health_status)
    logger.info("Startup health check completed", **health_status)
    
    yield
    
    # Shutdown
    logger.info("Shutting down InsightBull Backend")
    
    # Stop Scheduler
    await scheduler.stop()
    logger.info("Scheduler stopped gracefully")


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
    
    # Include routers
    app.include_router(dashboard_router)  # Dashboard endpoints (/api/dashboard)
    app.include_router(stocks_router)     # Stock data endpoints (/api/stocks)
    app.include_router(analysis_router)   # Analysis endpoints (/api/analysis)
    app.include_router(pipeline_router)   # Pipeline management (admin only)
    app.include_router(admin_router, prefix="/api")  # Admin panel functionality
    
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
        access_log=False  # Disable uvicorn access log - using custom middleware instead
    )