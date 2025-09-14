"""
Stock-related API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging

from app.core.database import get_db
from app.models import Stock
from app.schemas.stock import StockResponse, StockCreate, StockUpdate

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/", response_model=List[StockResponse])
async def get_stocks(
    db: AsyncSession = Depends(get_db),
    active_only: bool = Query(True, description="Only return active stocks")
):
    """Get all tracked stocks"""
    try:
        query = select(Stock)
        if active_only:
            query = query.where(Stock.is_active == True)
        
        result = await db.execute(query.order_by(Stock.symbol))
        stocks = result.scalars().all()
        
        return stocks
    except Exception as e:
        logger.error(f"Error fetching stocks: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stocks")


@router.get("/{symbol}", response_model=StockResponse)
async def get_stock(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """Get specific stock details"""
    try:
        result = await db.execute(
            select(Stock).where(Stock.symbol == symbol.upper())
        )
        stock = result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        return stock
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock")


@router.get("/{symbol}/latest")
async def get_stock_with_latest_data(
    symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """Get stock with latest price and sentiment data"""
    try:
        # Get stock
        result = await db.execute(
            select(Stock).where(Stock.symbol == symbol.upper())
        )
        stock = result.scalar_one_or_none()
        
        if not stock:
            raise HTTPException(status_code=404, detail=f"Stock {symbol} not found")
        
        # Get latest price
        from app.models import PriceData
        from sqlalchemy import desc
        
        price_result = await db.execute(
            select(PriceData)
            .where(PriceData.stock_symbol == symbol.upper())
            .order_by(desc(PriceData.date))
            .limit(1)
        )
        latest_price = price_result.scalar_one_or_none()
        
        # Get latest sentiment
        from app.models import SentimentData
        
        sentiment_result = await db.execute(
            select(SentimentData)
            .where(SentimentData.stock_symbol == symbol.upper())
            .order_by(desc(SentimentData.published_at))
            .limit(1)
        )
        latest_sentiment = sentiment_result.scalar_one_or_none()
        
        return {
            "stock": stock.to_dict(),
            "latest_price": latest_price.to_dict() if latest_price else None,
            "latest_sentiment": latest_sentiment.to_dict() if latest_sentiment else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching stock data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch stock data")
