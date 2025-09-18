"""
Sentiment Controller
====================

FastAPI controller for sentiment analysis endpoints.
Handles sentiment data retrieval and analysis operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import structlog

from app.data_access.database import get_db
from app.service.sentiment_service import SentimentService


logger = structlog.get_logger()
router = APIRouter()


@router.get("/trends")
async def get_sentiment_trends(
    stock_symbol: str = Query(..., description="Stock symbol to analyze"),
    time_period: str = Query("7d", description="Time period for analysis"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get sentiment trends for a specific stock.
    
    Implements U-FR3: Analyze Stock Sentiment
    """
    try:
        logger.info("Getting sentiment trends", stock_symbol=stock_symbol, time_period=time_period)
        
        # Use real sentiment service
        sentiment_service = SentimentService(db)
        trends = await sentiment_service.get_sentiment_trends(stock_symbol, time_period)
        
        return trends
        
    except Exception as e:
        logger.error("Error getting sentiment trends", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sentiment trends"
        )


@router.get("/analysis/{stock_symbol}")
async def get_stock_sentiment_analysis(
    stock_symbol: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed sentiment analysis for a stock.
    
    Implements U-FR4: View Detailed Analysis
    """
    try:
        logger.info("Getting stock sentiment analysis", stock_symbol=stock_symbol)
        
        # Use real sentiment service
        sentiment_service = SentimentService(db)
        analysis = await sentiment_service.get_stock_sentiment_analysis(stock_symbol)
        
        return analysis
        
    except Exception as e:
        logger.error("Error getting sentiment analysis", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve sentiment analysis"
        )


@router.get("/health")
async def sentiment_health():
    """Health check for sentiment controller."""
    return {"status": "healthy", "controller": "sentiment"}