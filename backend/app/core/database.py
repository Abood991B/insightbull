"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging

from config import settings
from app.models.base import Base

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    **settings.database_settings
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Sync engine for migrations and some operations
sync_engine = create_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    **settings.database_settings
)

# Sync session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=sync_engine
)


async def init_db():
    """Initialize database tables"""
    try:
        async with engine.begin() as conn:
            # Import all models to ensure they're registered
            from app.models import (
                Stock, SentimentData, PriceData, CorrelationData,
                User, ApiConfig, SystemLog, ModelMetric
            )
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
            
            logger.info("Database tables created successfully")
            
            # Initialize default data
            await init_default_data()
            
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


async def init_default_data():
    """Initialize default data in database"""
    async with AsyncSessionLocal() as session:
        try:
            # Check if stocks already exist
            from sqlalchemy import select
            from app.models import Stock
            
            result = await session.execute(select(Stock).limit(1))
            if result.scalar_one_or_none():
                return  # Data already initialized
            
            # Add default stocks (Top tech stocks)
            default_stocks = [
                {"symbol": "MSFT", "name": "Microsoft Corporation", "sector": "Technology"},
                {"symbol": "NVDA", "name": "NVIDIA Corporation", "sector": "Technology"},
                {"symbol": "AAPL", "name": "Apple Inc.", "sector": "Technology"},
                {"symbol": "AVGO", "name": "Broadcom Inc.", "sector": "Technology"},
                {"symbol": "ORCL", "name": "Oracle Corporation", "sector": "Technology"},
                {"symbol": "PLTR", "name": "Palantir Technologies Inc.", "sector": "Technology"},
                {"symbol": "IBM", "name": "International Business Machines", "sector": "Technology"},
                {"symbol": "CSCO", "name": "Cisco Systems Inc.", "sector": "Technology"},
                {"symbol": "CRM", "name": "Salesforce Inc.", "sector": "Technology"},
                {"symbol": "INTU", "name": "Intuit Inc.", "sector": "Technology"},
                {"symbol": "NOW", "name": "ServiceNow Inc.", "sector": "Technology"},
                {"symbol": "AMD", "name": "Advanced Micro Devices Inc.", "sector": "Technology"},
                {"symbol": "ACN", "name": "Accenture plc", "sector": "Technology"},
                {"symbol": "TXN", "name": "Texas Instruments Inc.", "sector": "Technology"},
                {"symbol": "QCOM", "name": "QUALCOMM Inc.", "sector": "Technology"},
                {"symbol": "ADBE", "name": "Adobe Inc.", "sector": "Technology"},
                {"symbol": "AMAT", "name": "Applied Materials Inc.", "sector": "Technology"},
                {"symbol": "PANW", "name": "Palo Alto Networks Inc.", "sector": "Technology"},
                {"symbol": "MU", "name": "Micron Technology Inc.", "sector": "Technology"},
                {"symbol": "CRWD", "name": "CrowdStrike Holdings Inc.", "sector": "Technology"},
            ]
            
            for stock_data in default_stocks:
                stock = Stock(**stock_data, is_active=True)
                session.add(stock)
            
            await session.commit()
            logger.info(f"Initialized {len(default_stocks)} default stocks")
            
        except Exception as e:
            logger.error(f"Failed to initialize default data: {e}")
            await session.rollback()


async def get_db():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


@contextmanager
def get_sync_db():
    """Get synchronous database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
