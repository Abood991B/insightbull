"""
Stock price API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, desc
from typing import List, Optional
from datetime import datetime, timedelta, date
import logging

from app.core.database import get_db
from app.models import PriceData, Stock
from app.schemas.price import PriceResponse, PriceHistoryResponse

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/{symbol}", response_model=List[PriceResponse])
async def get_price_history(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    limit: int = Query(100, le=365)
):
    """Get historical price data for a stock"""
    try:
        # Default date range if not provided
        if not end_date:
            end_date = date.today()
        if not start_date:
            start_date = end_date - timedelta(days=30)
        
        # Build query
        query = select(PriceData).where(
            and_(
                PriceData.stock_symbol == symbol.upper(),
                PriceData.date >= start_date,
                PriceData.date <= end_date
            )
        ).order_by(desc(PriceData.date)).limit(limit)
        
        result = await db.execute(query)
        prices = result.scalars().all()
        
        if not prices:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        return prices
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching price data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch price data")


@router.get("/{symbol}/latest")
async def get_latest_price(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """Get the latest price for a stock"""
    try:
        query = select(PriceData).where(
            PriceData.stock_symbol == symbol.upper()
        ).order_by(desc(PriceData.date)).limit(1)
        
        result = await db.execute(query)
        latest_price = result.scalar_one_or_none()
        
        if not latest_price:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        # Calculate price change from previous day
        prev_query = select(PriceData).where(
            and_(
                PriceData.stock_symbol == symbol.upper(),
                PriceData.date < latest_price.date
            )
        ).order_by(desc(PriceData.date)).limit(1)
        
        prev_result = await db.execute(prev_query)
        prev_price = prev_result.scalar_one_or_none()
        
        price_change = 0
        price_change_percent = 0
        
        if prev_price:
            price_change = float(latest_price.close - prev_price.close)
            price_change_percent = (price_change / float(prev_price.close)) * 100
        
        return {
            "symbol": latest_price.stock_symbol,
            "date": latest_price.date,
            "open": float(latest_price.open) if latest_price.open else None,
            "high": float(latest_price.high) if latest_price.high else None,
            "low": float(latest_price.low) if latest_price.low else None,
            "close": float(latest_price.close),
            "volume": latest_price.volume,
            "change": price_change,
            "change_percent": price_change_percent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching latest price: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch latest price")


@router.get("/{symbol}/summary", response_model=PriceHistoryResponse)
async def get_price_summary(
    symbol: str,
    db: AsyncSession = Depends(get_db),
    days: int = Query(30, le=365)
):
    """Get price summary statistics for a stock"""
    try:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get price data
        query = select(PriceData).where(
            and_(
                PriceData.stock_symbol == symbol.upper(),
                PriceData.date >= start_date,
                PriceData.date <= end_date
            )
        ).order_by(PriceData.date)
        
        result = await db.execute(query)
        prices = result.scalars().all()
        
        if not prices:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        # Calculate statistics
        avg_price = sum(float(p.close) for p in prices) / len(prices)
        first_price = float(prices[0].close)
        last_price = float(prices[-1].close)
        price_change = last_price - first_price
        price_change_percent = (price_change / first_price) * 100 if first_price > 0 else 0
        
        return PriceHistoryResponse(
            stock_symbol=symbol.upper(),
            prices=prices,
            period_start=prices[0].date,
            period_end=prices[-1].date,
            average_price=avg_price,
            price_change=price_change,
            price_change_percent=price_change_percent
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating price summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to calculate price summary")
