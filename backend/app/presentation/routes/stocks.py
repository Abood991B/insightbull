"""
Stock API Routes

Implements U-FR2: Select Time Range and U-FR3: Filter by Stock
Provides stock information with time-based filtering and individual stock details.
"""

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from app.presentation.schemas import (
    StockDetail,
    StockList,
    StockListItem,
    StockMetrics,
    PriceDataPoint,
    SentimentDataPoint
)
from app.presentation.deps import (
    get_stock_repository,
    get_sentiment_repository,
    get_price_repository,
    validate_timeframe,
    validate_stock_symbol
)
from app.data_access.repositories import (
    StockRepository,
    SentimentDataRepository,
    StockPriceRepository
)

router = APIRouter(prefix="/api/stocks", tags=["stocks"])


@router.get("/", response_model=StockList)
async def get_all_stocks(
    limit: int = Query(20, le=100, description="Maximum number of stocks to return"),
    active_only: bool = Query(True, description="Only return actively tracked stocks"),
    stock_repo: StockRepository = Depends(get_stock_repository),
    sentiment_repo: SentimentDataRepository = Depends(get_sentiment_repository),
    price_repo: StockPriceRepository = Depends(get_price_repository)
) -> StockList:
    """
    Get all tracked stocks with latest data - Implements U-FR3
    
    Args:
        limit: Maximum number of stocks to return
        active_only: Filter for only actively tracked stocks
        
    Returns:
        StockList: List of all tracked stocks with basic information
    """
    try:
        # Get all stocks
        all_stocks = await stock_repo.get_all()
        
        if active_only:
            all_stocks = [s for s in all_stocks if s.is_active]
        
        # Build stock list items with latest data
        stock_items = []
        for stock in all_stocks[:limit]:
            # Get latest sentiment and price
            latest_sentiment = await sentiment_repo.get_latest_sentiment_for_stock(stock.symbol)
            latest_price = await price_repo.get_latest_price_for_stock(stock.symbol)
            
            stock_items.append(StockListItem(
                symbol=stock.symbol,
                company_name=stock.company_name,
                sector=stock.sector,
                is_active=stock.is_active,
                latest_sentiment=round(latest_sentiment.score, 3) if latest_sentiment else None,
                latest_price=latest_price.close_price if latest_price else None,
                last_updated=latest_sentiment.timestamp if latest_sentiment else stock.updated_at
            ))
        
        return StockList(
            stocks=stock_items,
            total_count=len(all_stocks),
            active_count=len([s for s in all_stocks if s.is_active])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stocks: {str(e)}"
        )


@router.get("/{symbol}", response_model=StockDetail)
async def get_stock_detail(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    timeframe: str = Query("7d", pattern="^(1d|7d|14d)$", description="Data timeframe: 1d, 7d, or 14d"),
    stock_repo: StockRepository = Depends(get_stock_repository),
    sentiment_repo: SentimentDataRepository = Depends(get_sentiment_repository),
    price_repo: StockPriceRepository = Depends(get_price_repository)
) -> StockDetail:
    """
    Get detailed stock information - Implements U-FR2 & U-FR3
    
    Args:
        symbol: Stock symbol to retrieve details for
        timeframe: Time range for historical data (1d, 7d, 14d)
        
    Returns:
        StockDetail: Comprehensive stock information including:
        - Price history
        - Sentiment history  
        - Statistical metrics
        - Time-based filtering
    """
    try:
        # Validate inputs
        symbol = validate_stock_symbol(symbol)
        timeframe = validate_timeframe(timeframe)
        
        # Get stock information
        stock = await stock_repo.get_by_symbol(symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with symbol '{symbol}' not found"
            )
        
        # Calculate date range based on timeframe
        days_map = {"1d": 1, "7d": 7, "14d": 14}
        days = days_map[timeframe]
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get price history
        price_history = await _get_price_history(price_repo, symbol, days)
        
        # Get sentiment history
        sentiment_history = await _get_sentiment_history(sentiment_repo, symbol, start_date)
        
        # Calculate metrics
        metrics = await _calculate_stock_metrics(
            sentiment_repo, price_repo, symbol, start_date, price_history, sentiment_history
        )
        
        return StockDetail(
            symbol=stock.symbol,
            company_name=stock.company_name,
            sector=stock.sector,
            price_history=price_history,
            sentiment_history=sentiment_history,
            metrics=metrics,
            timeframe=timeframe,
            last_updated=stock.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stock details: {str(e)}"
        )


async def _get_price_history(
    price_repo: StockPriceRepository,
    symbol: str,
    days: int
) -> List[PriceDataPoint]:
    """Get formatted price history for the stock"""
    
    price_records = await price_repo.get_price_history(symbol, days=days)
    
    return [
        PriceDataPoint(
            timestamp=record.timestamp,
            open_price=record.open_price,
            close_price=record.close_price,
            high_price=record.high_price,
            low_price=record.low_price,
            volume=record.volume
        )
        for record in price_records
    ]


async def _get_sentiment_history(
    sentiment_repo: SentimentDataRepository,
    symbol: str,
    start_date: datetime
) -> List[SentimentDataPoint]:
    """Get formatted sentiment history for the stock"""
    
    sentiment_records = await sentiment_repo.get_sentiment_by_date_range(
        symbol, start_date, datetime.utcnow()
    )
    
    return [
        SentimentDataPoint(
            timestamp=record.created_at,
            score=record.sentiment_score,
            label=record.sentiment_label,
            confidence=record.confidence_score,
            source=record.source
        )
        for record in sentiment_records
    ]


async def _calculate_stock_metrics(
    sentiment_repo: SentimentDataRepository,
    price_repo: StockPriceRepository,
    symbol: str,
    start_date: datetime,
    price_history: List[PriceDataPoint],
    sentiment_history: List[SentimentDataPoint]
) -> StockMetrics:
    """Calculate statistical metrics for the stock"""
    
    # Calculate sentiment metrics
    if sentiment_history:
        sentiment_scores = [s.score for s in sentiment_history]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        sentiment_volatility = _calculate_standard_deviation(sentiment_scores)
    else:
        avg_sentiment = 0.0
        sentiment_volatility = 0.0
    
    # Calculate price change
    price_change_percent = None
    if len(price_history) >= 2:
        oldest_price = price_history[-1].close_price  # List is ordered latest first
        latest_price = price_history[0].close_price
        price_change_percent = ((latest_price - oldest_price) / oldest_price) * 100
    
    # Calculate data quality score (simplified)
    expected_records = max(1, (datetime.utcnow() - start_date).days * 24)  # Hourly expected
    actual_records = len(sentiment_history)
    data_quality_score = min(1.0, actual_records / expected_records)
    
    return StockMetrics(
        avg_sentiment=round(avg_sentiment, 3),
        sentiment_volatility=round(sentiment_volatility, 3),
        price_change_percent=round(price_change_percent, 2) if price_change_percent else None,
        total_sentiment_records=len(sentiment_history),
        data_quality_score=round(data_quality_score, 3)
    )


def _calculate_standard_deviation(values: List[float]) -> float:
    """Calculate standard deviation of a list of values"""
    if len(values) < 2:
        return 0.0
    
    mean = sum(values) / len(values)
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5