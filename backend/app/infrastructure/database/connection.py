"""
Database Connection Management

Provides utilities for managing database connections, sessions,
and engine configuration with proper async support.
"""

import os
import logging
from typing import Optional, AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


def get_database_url() -> str:
    """
    Get database URL from environment or use default SQLite
    
    Returns:
        Database URL string
    """
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        # Convert sync URLs to async for SQLAlchemy 2.0
        if database_url.startswith('postgresql://'):
            database_url = database_url.replace('postgresql://', 'postgresql+asyncpg://')
        elif database_url.startswith('sqlite:///'):
            database_url = database_url.replace('sqlite:///', 'sqlite+aiosqlite:///')
        elif database_url.startswith('mysql://'):
            database_url = database_url.replace('mysql://', 'mysql+aiomysql://')
    else:
        # Default SQLite database for development
        database_url = 'sqlite+aiosqlite:///./data/insight_stock.db'
    
    logger.info(f"Using database URL: {database_url.split('@')[0]}...")  # Hide credentials
    return database_url


def get_engine(database_url: Optional[str] = None):
    """
    Create and configure async database engine
    
    Args:
        database_url: Database URL (uses default if None)
        
    Returns:
        Configured async engine
    """
    if database_url is None:
        database_url = get_database_url()
    
    # Engine configuration based on database type
    engine_kwargs = {
        'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true',
        'echo_pool': os.getenv('SQL_ECHO_POOL', 'false').lower() == 'true',
    }
    
    # SQLite-specific configuration
    if 'sqlite' in database_url:
        engine_kwargs.update({
            'poolclass': StaticPool,
            'connect_args': {
                'check_same_thread': False,
                'timeout': 30
            }
        })
    
    # PostgreSQL-specific configuration
    elif 'postgresql' in database_url:
        engine_kwargs.update({
            'pool_size': int(os.getenv('DB_POOL_SIZE', 5)),
            'max_overflow': int(os.getenv('DB_MAX_OVERFLOW', 10)),
            'pool_pre_ping': True,
            'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', 3600)),
        })
    
    engine = create_async_engine(database_url, **engine_kwargs)
    
    logger.info(f"Created async database engine with pool_size: {engine_kwargs.get('pool_size', 'default')}")
    return engine


# Global engine instance
_engine = None
_session_factory = None


def get_session_factory():
    """Get or create session factory"""
    global _engine, _session_factory
    
    if _engine is None:
        _engine = get_engine()
    
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=True,
            autocommit=False
        )
    
    return _session_factory


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Get async database session
    
    Yields:
        AsyncSession: Database session
    """
    session_factory = get_session_factory()
    
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {str(e)}")
            raise
        finally:
            await session.close()


async def create_database_tables():
    """
    Create all database tables
    
    This should be called during application startup
    """
    try:
        from app.data_access.models import Base
        
        engine = get_engine()
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("Database tables created successfully")
        
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")
        raise


async def drop_database_tables():
    """
    Drop all database tables
    
    WARNING: This will destroy all data!
    """
    try:
        from app.data_access.models import Base
        
        engine = get_engine()
        
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("All database tables dropped!")
        
    except Exception as e:
        logger.error(f"Error dropping database tables: {str(e)}")
        raise


async def check_database_connection() -> bool:
    """
    Check if database connection is working
    
    Returns:
        True if connection is successful, False otherwise
    """
    try:
        async with get_async_session() as session:
            result = await session.execute("SELECT 1")
            result.scalar()
            return True
    except Exception as e:
        logger.error(f"Database connection check failed: {str(e)}")
        return False


def get_sync_engine(database_url: Optional[str] = None):
    """
    Create synchronous engine for migrations and CLI tools
    
    Args:
        database_url: Database URL (uses default if None)
        
    Returns:
        Synchronous SQLAlchemy engine
    """
    if database_url is None:
        database_url = get_database_url()
        # Convert async URL back to sync for migrations
        if 'sqlite+aiosqlite' in database_url:
            database_url = database_url.replace('sqlite+aiosqlite', 'sqlite')
        elif 'postgresql+asyncpg' in database_url:
            database_url = database_url.replace('postgresql+asyncpg', 'postgresql')
        elif 'mysql+aiomysql' in database_url:
            database_url = database_url.replace('mysql+aiomysql', 'mysql')
    
    # Engine configuration
    engine_kwargs = {
        'echo': os.getenv('SQL_ECHO', 'false').lower() == 'true',
    }
    
    # SQLite-specific configuration
    if 'sqlite' in database_url:
        engine_kwargs.update({
            'poolclass': StaticPool,
            'connect_args': {'check_same_thread': False}
        })
    
    return create_engine(database_url, **engine_kwargs)


# Cleanup function
async def close_database_connections():
    """
    Close all database connections
    
    Should be called during application shutdown
    """
    global _engine
    
    if _engine:
        await _engine.dispose()
        _engine = None
        logger.info("Database connections closed")


# Development utilities
async def reset_database():
    """
    Reset database by dropping and recreating all tables
    
    WARNING: This will destroy all data!
    """
    logger.warning("Resetting database - all data will be lost!")
    
    await drop_database_tables()
    await create_database_tables()
    
    logger.info("Database reset completed")


def ensure_database_directory():
    """
    Ensure the database directory exists for SQLite
    """
    database_url = get_database_url()
    
    if 'sqlite' in database_url:
        # Extract path from SQLite URL
        import re
        match = re.search(r'sqlite.*:///(.*)', database_url)
        if match:
            db_path = match.group(1)
            db_dir = os.path.dirname(db_path)
            
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Created database directory: {db_dir}")