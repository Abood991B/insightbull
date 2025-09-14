#!/usr/bin/env python
"""
Startup script for initializing the backend application
"""
import asyncio
import sys
import os
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent))

import logging
from sqlalchemy import text
from app.core.database import engine, init_db
from app.core.logging import setup_logging
from config import settings

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)


async def check_database_connection():
    """Check if database is accessible"""
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            logger.info("✓ Database connection successful")
            return True
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        return False


async def check_redis_connection():
    """Check if Redis is accessible"""
    try:
        import redis.asyncio as redis
        
        client = redis.from_url(settings.REDIS_URL)
        await client.ping()
        await client.close()
        logger.info("✓ Redis connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ Redis connection failed: {e}")
        return False


async def verify_api_keys():
    """Verify that required API keys are configured"""
    api_keys = {
        "Reddit": (settings.REDDIT_CLIENT_ID, settings.REDDIT_CLIENT_SECRET),
        "FinnHub": (settings.FINNHUB_API_KEY,),
        "Marketaux": (settings.MARKETAUX_API_KEY,),
        "NewsAPI": (settings.NEWSAPI_KEY,),
    }
    
    all_configured = True
    for name, keys in api_keys.items():
        if all(keys):
            logger.info(f"✓ {name} API configured")
        else:
            logger.warning(f"✗ {name} API not configured")
            all_configured = False
    
    return all_configured


async def initialize_application():
    """Initialize the application"""
    logger.info("=" * 60)
    logger.info("Stock Market Sentiment Dashboard - Backend Initialization")
    logger.info("=" * 60)
    
    # Check database connection
    if not await check_database_connection():
        logger.error("Cannot proceed without database connection")
        logger.info("Please ensure PostgreSQL is running and configured correctly")
        return False
    
    # Check Redis connection
    if not await check_redis_connection():
        logger.warning("Redis not available - caching will be disabled")
    
    # Initialize database tables
    logger.info("Initializing database tables...")
    try:
        await init_db()
        logger.info("✓ Database tables initialized")
    except Exception as e:
        logger.error(f"✗ Failed to initialize database: {e}")
        return False
    
    # Verify API keys
    if not await verify_api_keys():
        logger.warning("Some APIs are not configured - data collection may be limited")
    
    # Load ML models
    logger.info("Loading ML models...")
    try:
        from app.services.sentiment_analyzer import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        logger.info("✓ ML models loaded successfully")
    except Exception as e:
        logger.error(f"✗ Failed to load ML models: {e}")
        logger.warning("Sentiment analysis will not be available")
    
    logger.info("=" * 60)
    logger.info("✓ Backend initialization completed successfully!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("To start the server, run:")
    logger.info("  uvicorn main:app --reload --port 3000")
    logger.info("")
    logger.info("API documentation will be available at:")
    logger.info("  http://localhost:3000/api/docs")
    logger.info("")
    
    return True


async def main():
    """Main entry point"""
    success = await initialize_application()
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
