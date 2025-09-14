"""
Sentiment analysis API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional, Literal
from datetime import datetime, timedelta
import logging

from app.core.database import get_db
from app.models import SentimentData, Stock
from app.schemas.sentiment import SentimentResponse, SentimentAggregateResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{symbol}", response_model=List[SentimentResponse])
async def get_sentiment_data(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    time_range: Literal["1d", "7d", "14d"] = Query("7d"),
    source: Optional[str] = Query(None),
    limit: int = Query(100, le=500)
):
    """Get sentiment data for a specific stock"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if time_range == "1d":
            start_date = end_date - timedelta(days=1)
        elif time_range == "7d":
            start_date = end_date - timedelta(days=7)
        else:  # 14d
            start_date = end_date - timedelta(days=14)
        
        # Build query
        query = select(SentimentData).where(
            and_(
                SentimentData.stock_symbol == symbol.upper(),
                SentimentData.published_at >= start_date,
                SentimentData.published_at <= end_date
            )
        )
        
        if source:
            query = query.where(SentimentData.source == source.lower())
        
        query = query.order_by(desc(SentimentData.published_at)).limit(limit)
        
        result = await db.execute(query)
        sentiment_data = result.scalars().all()
        
        return sentiment_data
        
    except Exception as e:
        logger.error(f"Error fetching sentiment data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch sentiment data")


@router.get("/aggregate/{symbol}", response_model=SentimentAggregateResponse)
async def get_aggregate_sentiment(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    time_range: Literal["1d", "7d", "14d"] = Query("7d"),
    group_by: Literal["hour", "day"] = Query("day")
):
    """Get aggregated sentiment scores for a stock"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if time_range == "1d":
            start_date = end_date - timedelta(days=1)
        elif time_range == "7d":
            start_date = end_date - timedelta(days=7)
        else:  # 14d
            start_date = end_date - timedelta(days=14)
        
        # Query for sentiment counts and average
        query = select(
            SentimentData.stock_symbol,
            func.count(SentimentData.id).label("total_count"),
            func.sum(func.cast(SentimentData.sentiment == "positive", type_=int)).label("positive_count"),
            func.sum(func.cast(SentimentData.sentiment == "negative", type_=int)).label("negative_count"),
            func.sum(func.cast(SentimentData.sentiment == "neutral", type_=int)).label("neutral_count"),
            func.avg(SentimentData.sentiment_score).label("avg_sentiment")
        ).where(
            and_(
                SentimentData.stock_symbol == symbol.upper(),
                SentimentData.published_at >= start_date,
                SentimentData.published_at <= end_date
            )
        ).group_by(SentimentData.stock_symbol)
        
        result = await db.execute(query)
        data = result.first()
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No sentiment data found for {symbol}")
        
        # Determine sentiment trend
        avg_sentiment = float(data.avg_sentiment or 0)
        if avg_sentiment > 0.1:
            trend = "bullish"
        elif avg_sentiment < -0.1:
            trend = "bearish"
        else:
            trend = "neutral"
        
        return SentimentAggregateResponse(
            stock_symbol=data.stock_symbol,
            time_window=time_range,
            positive_count=data.positive_count or 0,
            negative_count=data.negative_count or 0,
            neutral_count=data.neutral_count or 0,
            average_sentiment=avg_sentiment,
            sentiment_trend=trend,
            period_start=start_date,
            period_end=end_date
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating aggregate sentiment: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate aggregate sentiment")


@router.get("/trends/top", response_model=List[dict])
async def get_trending_stocks(
    db: AsyncSession = Depends(get_db),
    time_range: Literal["1d", "7d"] = Query("1d"),
    limit: int = Query(10, le=20)
):
    """Get trending stocks by sentiment volume and score"""
    try:
        # Calculate date range
        end_date = datetime.utcnow()
        if time_range == "1d":
            start_date = end_date - timedelta(days=1)
        else:  # 7d
            start_date = end_date - timedelta(days=7)
        
        # Query for trending stocks
        query = select(
            SentimentData.stock_symbol,
            func.count(SentimentData.id).label("mention_count"),
            func.avg(SentimentData.sentiment_score).label("avg_sentiment"),
            func.sum(func.cast(SentimentData.sentiment == "positive", type_=int)).label("positive_count")
        ).where(
            and_(
                SentimentData.published_at >= start_date,
                SentimentData.published_at <= end_date
            )
        ).group_by(
            SentimentData.stock_symbol
        ).order_by(
            desc("mention_count")
        ).limit(limit)
        
        result = await db.execute(query)
        trending = result.all()
        
        trending_stocks = []
        for row in trending:
            sentiment_score = float(row.avg_sentiment or 0)
            trending_stocks.append({
                "symbol": row.stock_symbol,
                "mention_count": row.mention_count,
                "average_sentiment": sentiment_score,
                "positive_ratio": (row.positive_count or 0) / row.mention_count if row.mention_count > 0 else 0,
                "trend": "bullish" if sentiment_score > 0.1 else "bearish" if sentiment_score < -0.1 else "neutral"
            })
        
        return trending_stocks
        
    except Exception as e:
        logger.error(f"Error fetching trending stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trending stocks")
