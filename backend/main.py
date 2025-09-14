"""
Main FastAPI application entry point
Enhanced with rate limiting and comprehensive logging
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from config import settings
from app.api import api_router
from app.core.database import init_db
from app.core.websocket import sio_app
from app.core.logging import setup_logging
from app.core.rate_limiter import get_rate_limiter, RateLimitMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    
    # Initialize database
    await init_db()
    
    # Initialize rate limiter
    rate_limiter = await get_rate_limiter()
    logger.info("Rate limiter initialized")
    
    # Start background tasks
    from app.core.scheduler import start_scheduler
    scheduler = start_scheduler()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")
    if scheduler:
        scheduler.shutdown()


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    docs_url=f"{settings.API_PREFIX}/docs",
    redoc_url=f"{settings.API_PREFIX}/redoc",
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request, call_next):
    """Apply rate limiting to all requests"""
    rate_limiter = await get_rate_limiter()
    middleware = RateLimitMiddleware(rate_limiter)
    return await middleware(request, call_next)

# Include API router
app.include_router(api_router, prefix=settings.API_PREFIX)

# Mount Socket.IO app if enabled
if settings.WEBSOCKET_ENABLED:
    app.mount("/ws", sio_app)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "features": {
            "rate_limiting": True,
            "websockets": settings.WEBSOCKET_ENABLED,
            "pipeline_logging": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=3000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
