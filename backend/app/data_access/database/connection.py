"""
Database Connection Management
==============================

SQLAlchemy database connection and session management.
Implements connection pooling and async support.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import OperationalError
import structlog
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import asyncio

from app.infrastructure.config import get_settings
from app.data_access.database.base import Base

logger = structlog.get_logger()

# Import models to register them with Base metadata (must be after Base import)
def _import_models():
    """Import all models to register them with SQLAlchemy Base."""
    from app.data_access.models import Stock, SentimentData, StockPrice, NewsArticle, HackerNewsPost, SystemLog

# Global engine and session factory
engine = None
async_session_factory = None


async def init_database():
    """Initialize database connection and create tables."""
    global engine, async_session_factory
    
    settings = get_settings()
    
    # Convert PostgreSQL URL to async version if needed
    database_url = settings.database_url
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
    
    logger.info("Initializing database connection", database_url=database_url.split('@')[0] + '@***' if '@' in database_url else database_url)
    
    # Create async engine
    engine = create_async_engine(
        database_url,
        echo=settings.debug,
        poolclass=NullPool,  # Use NullPool for development, change for production
        pool_pre_ping=True,
        pool_recycle=300,
    )
    
    # Create session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Import models to register them with Base
    _import_models()
    
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created/verified")


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session context manager with retry logic for SQLite locks.
    
    Implements exponential backoff for database lock errors to handle
    concurrent write operations in SQLite.
    """
    if async_session_factory is None:
        raise RuntimeError("Database not initialized. Call init_database() first.")
    
    max_retries = 3
    retry_delay_base = 0.5  # seconds
    
    async with async_session_factory() as session:
        try:
            yield session
            
            # Commit with retry logic for SQLite locks
            for attempt in range(max_retries):
                try:
                    await session.commit()
                    break  # Success, exit retry loop
                except OperationalError as e:
                    if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                        retry_delay = retry_delay_base * (2 ** attempt)
                        logger.warning(
                            "Database locked, retrying commit",
                            attempt=attempt + 1,
                            max_retries=max_retries,
                            retry_delay=retry_delay
                        )
                        await asyncio.sleep(retry_delay)
                    else:
                        # Max retries reached or different error
                        logger.error(
                            "Database commit failed after retries",
                            error=str(e),
                            attempts=attempt + 1
                        )
                        raise
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session in FastAPI."""
    async with get_db_session() as session:
        yield session


async def close_database():
    """Close database connections."""
    global engine
    
    if engine:
        await engine.dispose()
        logger.info("Database connections closed")