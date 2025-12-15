"""
Dependencies for API Routes

FastAPI dependency injection for database sessions and common route dependencies.
"""

from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.data_access.database.connection import get_db_session
from app.data_access.repositories import (
    StockRepository,
    SentimentDataRepository, 
    StockPriceRepository
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Database session dependency
    
    Yields:
        AsyncSession: Database session
    """
    async with get_db_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()


def get_stock_repository(db: AsyncSession = Depends(get_db)) -> StockRepository:
    """
    Stock repository dependency
    
    Args:
        db: Database session
        
    Returns:
        StockRepository: Stock repository instance
    """
    return StockRepository(db)


def get_sentiment_repository(db: AsyncSession = Depends(get_db)) -> SentimentDataRepository:
    """
    Sentiment repository dependency
    
    Args:
        db: Database session
        
    Returns:
        SentimentDataRepository: Sentiment repository instance
    """
    return SentimentDataRepository(db)


def get_price_repository(db: AsyncSession = Depends(get_db)) -> StockPriceRepository:
    """
    Stock price repository dependency
    
    Args:
        db: Database session
        
    Returns:
        StockPriceRepository: Price repository instance
    """
    return StockPriceRepository(db)


def validate_timeframe(timeframe: str) -> str:
    """
    Validate timeframe parameter
    
    Args:
        timeframe: Timeframe string (1d, 7d, 14d, 30d)
        
    Returns:
        str: Validated timeframe
        
    Raises:
        HTTPException: If timeframe is invalid
    """
    valid_timeframes = ["1d", "7d", "14d", "30d"]
    if timeframe not in valid_timeframes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid timeframe. Must be one of: {', '.join(valid_timeframes)}"
        )
    return timeframe


def validate_stock_symbol(symbol: str) -> str:
    """
    Validate and normalize stock symbol
    
    Args:
        symbol: Stock symbol
        
    Returns:
        str: Normalized stock symbol (uppercase)
        
    Raises:
        HTTPException: If symbol format is invalid
    """
    if not symbol or len(symbol) > 10 or not symbol.replace(".", "").isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid stock symbol format"
        )
    return symbol.upper()