"""
Sentiment Data Repository

Repository implementation for SentimentData model with specialized queries
for sentiment analysis data management.
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_, between
from app.utils.timezone import ensure_utc, to_naive_utc
from sqlalchemy.orm import selectinload
from datetime import datetime, timedelta
import uuid
from app.utils.timezone import utc_now

from app.data_access.models import SentimentData, Stock
from .base_repository import BaseRepository


class SentimentDataRepository(BaseRepository[SentimentData]):
    """
    Repository for SentimentData model with specialized sentiment analysis queries
    """
    
    def __init__(self, db_session: AsyncSession):
        super().__init__(SentimentData, db_session)
    
    async def get_by_stock_symbol(
        self, 
        symbol: str, 
        limit: int = 100
    ) -> List[SentimentData]:
        """
        Get sentiment data for a specific stock symbol
        
        Args:
            symbol: Stock symbol
            limit: Maximum number of records
            
        Returns:
            List of sentiment data ordered by creation date (latest first)
        """
        result = await self.db_session.execute(
            select(SentimentData)
            .join(Stock)
            .where(Stock.symbol == symbol.upper())
            .order_by(desc(SentimentData.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def exists_by_content_hash(
        self, 
        stock_id: str, 
        source: str, 
        content_hash: str
    ) -> bool:
        """
        Check if sentiment data already exists for the given content hash.
        
        Args:
            stock_id: Stock UUID
            source: Data source name
            content_hash: SHA-256 hash of content
            
        Returns:
            True if duplicate exists, False otherwise
        """
        result = await self.db_session.execute(
            select(SentimentData.id)
            .where(
                and_(
                    SentimentData.stock_id == stock_id,
                    SentimentData.source == source,
                    SentimentData.content_hash == content_hash
                )
            )
            .limit(1)
        )
        return result.scalar_one_or_none() is not None
    
    async def get_sentiment_by_date_range(
        self, 
        symbol: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[SentimentData]:
        """
        Get sentiment data for a stock within a date range
        
        Args:
            symbol: Stock symbol
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            List of sentiment data within the date range
        """
        result = await self.db_session.execute(
            select(SentimentData)
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    between(SentimentData.created_at, start_date, end_date)
                )
            )
            .order_by(desc(SentimentData.created_at))
        )
        return result.scalars().all()
    
    async def get_latest_sentiment_by_stock(self, symbol: str) -> Optional[SentimentData]:
        """
        Get the most recent sentiment data for a stock
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest sentiment data or None if not found
        """
        result = await self.db_session.execute(
            select(SentimentData)
            .join(Stock)
            .where(Stock.symbol == symbol.upper())
            .order_by(desc(SentimentData.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_sentiment_summary_by_stock(
        self, 
        symbol: str, 
        days: int = 30
    ) -> Dict[str, Any]:
        """
        Get sentiment summary statistics for a stock
        
        Args:
            symbol: Stock symbol
            days: Number of days to analyze
            
        Returns:
            Dictionary with sentiment statistics
        """
        cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
        
        # Get sentiment data for the period
        result = await self.db_session.execute(
            select(
                func.count(SentimentData.id).label('total_count'),
                func.avg(SentimentData.sentiment_score).label('avg_sentiment'),
                func.min(SentimentData.sentiment_score).label('min_sentiment'),
                func.max(SentimentData.sentiment_score).label('max_sentiment'),
                func.stddev(SentimentData.sentiment_score).label('sentiment_stddev')
            )
            .select_from(SentimentData.__table__.join(Stock.__table__))
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    SentimentData.created_at >= cutoff_date
                )
            )
        )
        
        row = result.first()
        
        # Get sentiment distribution
        distribution_result = await self.db_session.execute(
            select(
                SentimentData.sentiment_label,
                func.count(SentimentData.id).label('count')
            )
            .select_from(SentimentData.__table__.join(Stock.__table__))
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    SentimentData.created_at >= cutoff_date
                )
            )
            .group_by(SentimentData.sentiment_label)
        )
        
        distribution = {row.sentiment_label: row.count for row in distribution_result}
        
        return {
            'symbol': symbol,
            'period_days': days,
            'total_records': row.total_count or 0,
            'average_sentiment': float(row.avg_sentiment) if row.avg_sentiment else 0.0,
            'min_sentiment': float(row.min_sentiment) if row.min_sentiment else 0.0,
            'max_sentiment': float(row.max_sentiment) if row.max_sentiment else 0.0,
            'sentiment_stddev': float(row.sentiment_stddev) if row.sentiment_stddev else 0.0,
            'sentiment_distribution': distribution,
            'generated_at': utc_now()
        }
    
    async def get_sentiment_trends(
        self, 
        symbol: str, 
        days: int = 30, 
        interval_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Get sentiment trends over time for a stock
        
        Args:
            symbol: Stock symbol
            days: Number of days to analyze
            interval_hours: Grouping interval in hours
            
        Returns:
            List of sentiment trend data points
        """
        cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
        
        # PostgreSQL-style date truncation (adapt for SQLite if needed)
        result = await self.db_session.execute(
            select(
                func.date(SentimentData.created_at).label('date'),
                func.avg(SentimentData.sentiment_score).label('avg_sentiment'),
                func.count(SentimentData.id).label('record_count')
            )
            .select_from(SentimentData.__table__.join(Stock.__table__))
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    SentimentData.created_at >= cutoff_date
                )
            )
            .group_by(func.date(SentimentData.created_at))
            .order_by(func.date(SentimentData.created_at))
        )
        
        trends = []
        for row in result:
            trends.append({
                'date': row.date,
                'average_sentiment': float(row.avg_sentiment),
                'record_count': row.record_count
            })
        
        return trends
    
    async def get_top_sentiment_stocks(
        self, 
        limit: int = 10, 
        days: int = 7,
        sentiment_type: str = 'positive'  # 'positive', 'negative', or 'neutral'
    ) -> List[Dict[str, Any]]:
        """
        Get top stocks by sentiment performance
        
        Args:
            limit: Number of top stocks to return
            days: Number of days to analyze
            sentiment_type: Type of sentiment to rank by
            
        Returns:
            List of stocks ranked by sentiment
        """
        cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
        
        # Define sentiment conditions
        sentiment_condition = SentimentData.sentiment_score > 0.1
        if sentiment_type == 'negative':
            sentiment_condition = SentimentData.sentiment_score < -0.1
        elif sentiment_type == 'neutral':
            sentiment_condition = between(SentimentData.sentiment_score, -0.1, 0.1)
        
        result = await self.db_session.execute(
            select(
                Stock.symbol,
                Stock.name,
                func.avg(SentimentData.sentiment_score).label('avg_sentiment'),
                func.count(SentimentData.id).label('sentiment_count')
            )
            .select_from(Stock.__table__.join(SentimentData.__table__))
            .where(
                and_(
                    SentimentData.created_at >= cutoff_date,
                    sentiment_condition
                )
            )
            .group_by(Stock.id, Stock.symbol, Stock.name)
            .having(func.count(SentimentData.id) >= 3)  # Minimum sentiment records
            .order_by(desc(func.avg(SentimentData.sentiment_score)))
            .limit(limit)
        )
        
        top_stocks = []
        for row in result:
            top_stocks.append({
                'symbol': row.symbol,
                'name': row.name,
                'average_sentiment': float(row.avg_sentiment),
                'sentiment_count': row.sentiment_count
            })
        
        return top_stocks
    
    async def get_sentiment_by_source(
        self, 
        symbol: str, 
        source: str,
        limit: int = 50
    ) -> List[SentimentData]:
        """
        Get sentiment data by source (news, reddit, etc.)
        
        Args:
            symbol: Stock symbol
            source: Data source
            limit: Maximum number of records
            
        Returns:
            List of sentiment data from the specified source
        """
        result = await self.db_session.execute(
            select(SentimentData)
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    SentimentData.source == source
                )
            )
            .order_by(desc(SentimentData.created_at))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_sentiment_data(
        self,
        stock_id: uuid.UUID,
        sentiment_score: float,
        sentiment_label: str,
        confidence_score: float,
        source: str,
        source_data: Dict[str, Any] = None
    ) -> SentimentData:
        """
        Create new sentiment data with validation
        
        Args:
            stock_id: UUID of the stock
            sentiment_score: Numerical sentiment score (-1 to 1)
            sentiment_label: Label (positive, negative, neutral)
            confidence_score: Confidence in the prediction (0 to 1)
            source: Data source
            source_data: Additional source-specific data
            
        Returns:
            Created sentiment data instance
        """
        # Validate sentiment score range
        if not -1.0 <= sentiment_score <= 1.0:
            raise ValueError("Sentiment score must be between -1.0 and 1.0")
        
        # Validate confidence score range
        if not 0.0 <= confidence_score <= 1.0:
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        
        # Validate sentiment label
        valid_labels = ['positive', 'negative', 'neutral']
        if sentiment_label.lower() not in valid_labels:
            raise ValueError(f"Sentiment label must be one of: {valid_labels}")
        
        sentiment_data = {
            'stock_id': stock_id,
            'sentiment_score': sentiment_score,
            'sentiment_label': sentiment_label.lower(),
            'confidence_score': confidence_score,
            'source': source,
            'source_data': source_data or {}
        }
        
        return await self.create(sentiment_data)
    
    async def get_sentiment_correlation_data(
        self, 
        symbol: str, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get sentiment data formatted for correlation analysis
        
        Args:
            symbol: Stock symbol
            days: Number of days to analyze
            
        Returns:
            List of data points for correlation analysis
        """
        cutoff_date = to_naive_utc(utc_now() - timedelta(days=days))
        
        result = await self.db_session.execute(
            select(
                SentimentData.created_at,
                SentimentData.sentiment_score,
                SentimentData.confidence_score,
                SentimentData.source
            )
            .join(Stock)
            .where(
                and_(
                    Stock.symbol == symbol.upper(),
                    SentimentData.created_at >= cutoff_date
                )
            )
            .order_by(SentimentData.created_at)
        )
        
        correlation_data = []
        for row in result:
            correlation_data.append({
                'timestamp': row.created_at,
                'sentiment_score': float(row.sentiment_score),
                'confidence_score': float(row.confidence_score),
                'source': row.source
            })
        
        return correlation_data
    
    async def get_recent_sentiment_scores(self, since: datetime, limit: int = 1000) -> List[SentimentData]:
        """
        Get recent sentiment scores across all stocks since a given time
        
        Args:
            since: Start time for recent data
            limit: Maximum number of records to return
            
        Returns:
            List of recent sentiment data
        """
        # Convert to naive UTC for SQLite compatibility
        since_naive = to_naive_utc(since)
        
        result = await self.db_session.execute(
            select(SentimentData)
            .where(SentimentData.created_at >= since_naive)
            .order_by(desc(SentimentData.created_at))
            .limit(limit)
        )
        
        # Ensure all returned timestamps are timezone-aware
        sentiments = result.scalars().all()
        for sentiment in sentiments:
            if sentiment.created_at:
                sentiment.created_at = ensure_utc(sentiment.created_at)
        
        return sentiments
    
    async def get_latest_sentiment_for_stock(self, symbol: str) -> Optional[SentimentData]:
        """
        Get the latest sentiment record for a specific stock
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Latest sentiment data or None
        """
        result = await self.db_session.execute(
            select(SentimentData)
            .join(Stock)
            .where(Stock.symbol == symbol.upper())
            .order_by(desc(SentimentData.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_latest_sentiment(self) -> Optional[SentimentData]:
        """
        Get the most recent sentiment record across all stocks
        
        Returns:
            Latest sentiment data or None
        """
        result = await self.db_session.execute(
            select(SentimentData)
            .order_by(desc(SentimentData.created_at))
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_total_count(self) -> int:
        """
        Get total count of sentiment records
        
        Returns:
            Total number of sentiment records
        """
        result = await self.db_session.execute(
            select(func.count(SentimentData.id))
        )
        return result.scalar() or 0