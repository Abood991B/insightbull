"""
Stock Price Repository

Repository for StockPrice model with specialized price analysis queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, between
from datetime import datetime, timedelta
import uuid
from app.utils.timezone import utc_now, to_naive_utc, ensure_utc

from app.data_access.models import StockPrice, Stock
from .base_repository import BaseRepository


class StockPriceRepository(BaseRepository[StockPrice]):
    """Repository for StockPrice model with specialized price analysis queries."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(StockPrice, db_session)
    
    async def get_price_history(
        self, 
        symbol: str, 
        days: int = 30,
        limit: int = 1000
    ) -> List[StockPrice]:
        """
        Get price history for a stock
        
        Args:
            symbol: Stock symbol
            days: Number of days of history
            limit: Maximum number of records
            
        Returns:
            List of stock prices ordered by timestamp (latest first)
        """
        cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
        
        result = await self.db_session.execute(
            select(StockPrice)
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    StockPrice.price_timestamp >= cutoff_date
                )
            )
            .order_by(desc(StockPrice.price_timestamp))
            .limit(limit)
        )
        
        prices = result.scalars().all()
        
        # Ensure all timestamps are timezone-aware
        for price in prices:
            if price.price_timestamp:
                price.price_timestamp = ensure_utc(price.price_timestamp)
        
        return prices
    
    async def get_latest_price(self, symbol: str) -> Optional[StockPrice]:
        """
        Get the most recent price for a stock
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest stock price or None if not found
        """
        result = await self.db_session.execute(
            select(StockPrice)
            .join(Stock)
            .where(Stock.symbol == symbol.upper())
            .order_by(desc(StockPrice.price_timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_latest_price_for_stock(self, symbol: str) -> Optional[StockPrice]:
        """
        Get the latest price record for a specific stock
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest price record or None
        """
        result = await self.db_session.execute(
            select(StockPrice)
            .join(Stock)
            .where(Stock.symbol == symbol.upper())
            .order_by(desc(StockPrice.price_timestamp))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_price_range(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[StockPrice]:
        """
        Get price data within a specific date range
        
        Args:
            symbol: Stock symbol
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of stock prices within the date range
        """
        result = await self.db_session.execute(
            select(StockPrice)
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    between(StockPrice.price_timestamp, start_date, end_date)
                )
            )
            .order_by(StockPrice.price_timestamp)
        )
        return result.scalars().all()
    
    async def get_price_statistics(
        self, 
        symbol: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get price statistics for a stock
        
        Args:
            symbol: Stock symbol
            days: Number of days to analyze
            
        Returns:
            Dictionary with price statistics
        """
        cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
        
        result = await self.db_session.execute(
            select(
                func.count(StockPrice.id).label('record_count'),
                func.avg(StockPrice.close_price).label('avg_close'),
                func.min(StockPrice.low_price).label('period_low'),
                func.max(StockPrice.high_price).label('period_high'),
                func.sum(StockPrice.volume).label('total_volume'),
                func.avg(StockPrice.volume).label('avg_volume')
            )
            .select_from(StockPrice.__table__.join(Stock.__table__))
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    StockPrice.price_timestamp >= cutoff_date
                )
            )
        )
        
        row = result.first()
        
        # Get first and last prices for period return calculation
        first_price_result = await self.db_session.execute(
            select(StockPrice.close_price)
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    StockPrice.price_timestamp >= cutoff_date
                )
            )
            .order_by(StockPrice.price_timestamp)
            .limit(1)
        )
        first_price = first_price_result.scalar()
        
        last_price_result = await self.db_session.execute(
            select(StockPrice.close_price)
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    StockPrice.price_timestamp >= cutoff_date
                )
            )
            .order_by(desc(StockPrice.price_timestamp))
            .limit(1)
        )
        last_price = last_price_result.scalar()
        
        # Calculate period return
        period_return = 0.0
        if first_price and last_price and first_price > 0:
            period_return = ((last_price - first_price) / first_price) * 100
        
        return {
            'symbol': symbol,
            'period_days': days,
            'record_count': row.record_count or 0,
            'average_close': float(row.avg_close) if row.avg_close else 0.0,
            'period_low': float(row.period_low) if row.period_low else 0.0,
            'period_high': float(row.period_high) if row.period_high else 0.0,
            'total_volume': int(row.total_volume) if row.total_volume else 0,
            'average_volume': float(row.avg_volume) if row.avg_volume else 0.0,
            'first_price': float(first_price) if first_price else 0.0,
            'last_price': float(last_price) if last_price else 0.0,
            'period_return_percent': period_return,
            'generated_at': utc_now()
        }

    async def get_price_at_time(self, symbol: str, target_time: datetime) -> Optional[StockPrice]:
        """
        Get price record closest to a specific time
        
        Args:
            symbol: Stock symbol
            target_time: Target timestamp
            
        Returns:
            Price record closest to target time or None
        """
        # Convert to naive UTC for SQLite compatibility
        target_time_naive = to_naive_utc(target_time)
        
        result = await self.db_session.execute(
            select(StockPrice)
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    StockPrice.price_timestamp <= target_time_naive
                )
            )
            .order_by(desc(StockPrice.price_timestamp))
            .limit(1)
        )
        
        price = result.scalar_one_or_none()
        
        # Ensure timestamp is timezone-aware
        if price and price.price_timestamp:
            price.price_timestamp = ensure_utc(price.price_timestamp)
        
        return price