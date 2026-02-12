"""
Stock Repository

Repository for Stock model with specialized stock market queries.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid
from app.utils.timezone import utc_now, to_naive_utc

from app.data_access.models import Stock, SentimentData, StockPrice
from .base_repository import BaseRepository


class StockRepository(BaseRepository[Stock]):
    """Repository for Stock model with specialized stock market queries."""
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(Stock, db_session)
    
    async def get_by_symbol(self, symbol: str) -> Optional[Stock]:
        """
        Get stock by symbol
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            Stock instance or None if not found
        """
        result = await self.db_session.execute(
            select(Stock).where(Stock.symbol == symbol.upper())
        )
        return result.scalar_one_or_none()
    
    async def get_active_stocks(self, limit: int = 100) -> List[Stock]:
        """
        Get all active stocks
        
        Args:
            limit: Maximum number of stocks to return
            
        Returns:
            List of active stocks
        """
        result = await self.db_session.execute(
            select(Stock)
            .where(Stock.symbol.isnot(None))  # Ensure symbol exists
            .order_by(Stock.symbol)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_stocks_by_sector(self, sector: str, limit: int = 50) -> List[Stock]:
        """
        Get stocks filtered by sector
        
        Args:
            sector: Sector name (e.g., 'Technology')
            limit: Maximum number of stocks to return
            
        Returns:
            List of stocks in the specified sector
        """
        result = await self.db_session.execute(
            select(Stock)
            .where(Stock.sector == sector)
            .order_by(Stock.symbol)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_stock_with_latest_sentiment(self, symbol: str) -> Optional[Stock]:
        """
        Get stock with its latest sentiment data
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock with loaded sentiment data or None
        """
        result = await self.db_session.execute(
            select(Stock)
            .options(selectinload(Stock.sentiment_data))
            .where(Stock.symbol == symbol.upper())
        )
        stock = result.scalar_one_or_none()
        
        if stock and stock.sentiment_data:
            # Sort sentiment data by creation date (latest first)
            stock.sentiment_data.sort(key=lambda x: x.created_at, reverse=True)
        
        return stock
    
    async def get_stock_with_price_history(
        self, 
        symbol: str, 
        days: int = 30
    ) -> Optional[Stock]:
        """
        Get stock with price history for specified days
        
        Args:
            symbol: Stock symbol
            days: Number of days of price history
            
        Returns:
            Stock with loaded price data or None
        """
        cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
        
        result = await self.db_session.execute(
            select(Stock)
            .options(selectinload(Stock.price_data))
            .where(Stock.symbol == symbol.upper())
        )
        stock = result.scalar_one_or_none()
        
        if stock and stock.price_data:
            # Filter price data to only include recent data
            stock.price_data = [
                price for price in stock.price_data 
                if price.price_timestamp >= cutoff_date
            ]
            # Sort by price_timestamp (latest first)
            stock.price_data.sort(key=lambda x: x.price_timestamp, reverse=True)
        
        return stock
    
    async def search_stocks(self, query: str, limit: int = 20) -> List[Stock]:
        """
        Search stocks by symbol or name
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching stocks
        """
        from app.utils.sql import escape_like
        search_term = f"%{escape_like(query.upper())}%"
        
        result = await self.db_session.execute(
            select(Stock)
            .where(
                and_(
                    (Stock.symbol.ilike(search_term)) | 
                    (Stock.name.ilike(search_term))
                )
            )
            .order_by(Stock.symbol)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_stocks_with_recent_activity(
        self, 
        hours: int = 24, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get stocks that have recent sentiment or price data
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of stocks
            
        Returns:
            List of stocks with activity counts
        """
        cutoff_time = to_naive_utc(utc_now() - timedelta(hours=hours))
        
        # Query for stocks with recent sentiment data
        sentiment_query = select(
            Stock.id,
            Stock.symbol,
            Stock.name,
            func.count(SentimentData.id).label('sentiment_count')
        ).select_from(
            Stock.__table__.join(SentimentData.__table__)
        ).where(
            SentimentData.created_at >= cutoff_time
        ).group_by(
            Stock.id, Stock.symbol, Stock.name
        )
        
        result = await self.db_session.execute(sentiment_query)
        stocks_with_activity = []
        
        for row in result:
            stocks_with_activity.append({
                'id': row.id,
                'symbol': row.symbol,
                'name': row.name,
                'sentiment_count': row.sentiment_count,
                'last_activity': cutoff_time
            })
        
        return stocks_with_activity[:limit]
    
    async def get_stock_statistics(self) -> Dict[str, Any]:
        """
        Get overall stock statistics
        
        Returns:
            Dictionary with stock statistics
        """
        # Total stocks count
        total_stocks = await self.count()
        
        # Stocks by sector
        sector_query = select(
            Stock.sector,
            func.count(Stock.id).label('count')
        ).where(
            Stock.sector.isnot(None)
        ).group_by(Stock.sector)
        
        sector_result = await self.db_session.execute(sector_query)
        sectors = {row.sector: row.count for row in sector_result}
        
        # Recent additions (last 7 days)
        week_ago = to_naive_utc(utc_now() - timedelta(days=7))
        recent_query = select(func.count(Stock.id)).where(
            Stock.created_at >= week_ago
        )
        recent_result = await self.db_session.execute(recent_query)
        recent_additions = recent_result.scalar()
        
        return {
            'total_stocks': total_stocks,
            'sectors': sectors,
            'recent_additions': recent_additions,
            'generated_at': utc_now()
        }