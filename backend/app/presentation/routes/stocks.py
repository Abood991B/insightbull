"""
Stock API Routes

Implements U-FR2: Select Time Range and U-FR3: Filter by Stock
Provides stock information with time-based filtering and individual stock details.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
import pytz

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


@router.get("/{symbol}/analysis", response_model=Dict)
async def get_stock_analysis_dashboard(
    symbol: str = Path(..., description="Stock symbol (e.g., AAPL)"),
    timeframe: str = Query("7d", pattern="^(1d|7d|14d|30d)$", description="Analysis timeframe"),
    stock_repo: StockRepository = Depends(get_stock_repository),
    sentiment_repo: SentimentDataRepository = Depends(get_sentiment_repository),
    price_repo: StockPriceRepository = Depends(get_price_repository)
) -> Dict:
    """
    Get comprehensive stock analysis dashboard data
    
    Returns all data needed for the Stock Analysis page including:
    - Stock overview metrics
    - Sentiment distribution
    - Top sentiment performers comparison
    - Watchlist overview
    """
    try:
        # Validate inputs
        symbol = validate_stock_symbol(symbol)
        
        # Get stock information
        stock = await stock_repo.get_by_symbol(symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock with symbol '{symbol}' not found"
            )
        
        # Calculate date range
        days_map = {"1d": 1, "7d": 7, "14d": 14, "30d": 30}
        days = days_map.get(timeframe, 7)
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get stock overview data
        stock_overview = await _get_stock_overview(stock, sentiment_repo, price_repo, start_date)
        
        # Get sentiment distribution for this stock
        sentiment_distribution = await _get_sentiment_distribution(sentiment_repo, symbol, start_date)
        
        # Get top sentiment performers (comparison with other stocks)
        top_performers = await _get_top_sentiment_performers(stock_repo, sentiment_repo, start_date)
        
        # Get watchlist overview
        watchlist_overview = await _get_watchlist_overview(stock_repo, sentiment_repo, price_repo, start_date)
        
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "stock_overview": stock_overview,
            "sentiment_distribution": sentiment_distribution,
            "top_performers": top_performers,
            "watchlist_overview": watchlist_overview,
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stock analysis: {str(e)}"
        )


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
                company_name=stock.name,  # Fixed: model uses 'name' not 'company_name'
                sector=stock.sector,
                is_active=stock.is_active,
                latest_sentiment=round(float(latest_sentiment.sentiment_score), 3) if latest_sentiment else None,
                latest_price=latest_price.close_price if latest_price else None,
                last_updated=latest_sentiment.created_at if latest_sentiment else stock.updated_at
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
            company_name=stock.name,  # Fixed: model uses 'name' not 'company_name'
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
            confidence=record.confidence,
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
        sentiment_scores = [float(s.sentiment_score) for s in sentiment_history]
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


async def _get_stock_overview(stock, sentiment_repo, price_repo, start_date):
    """Get stock overview metrics for the analysis dashboard"""
    
    # Get latest price
    latest_price = await price_repo.get_latest_price_for_stock(stock.symbol)
    current_price = float(latest_price.close_price) if latest_price else 0.0
    
    # Get 24h price change
    yesterday = datetime.utcnow() - timedelta(days=1)
    yesterday_price = await price_repo.get_price_at_time(stock.symbol, yesterday)
    
    price_change_24h = 0.0
    if yesterday_price and latest_price:
        price_change_24h = ((current_price - float(yesterday_price.close_price)) / float(yesterday_price.close_price)) * 100
    
    # Get average sentiment score
    sentiment_records = await sentiment_repo.get_sentiment_by_date_range(
        stock.symbol, start_date, datetime.utcnow()
    )
    
    avg_sentiment = 0.0
    if sentiment_records:
        sentiment_scores = [float(s.sentiment_score) for s in sentiment_records]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
    
    # Determine market status (simplified)
    eastern = pytz.timezone('US/Eastern')
    now_et = datetime.now(eastern)
    is_market_open = (
        now_et.weekday() < 5 and  # Monday = 0, Friday = 4
        9 <= now_et.hour < 16  # 9 AM to 4 PM ET
    )
    
    return {
        "current_price": round(current_price, 2),
        "sentiment_score": round(avg_sentiment, 3),
        "price_change_24h": round(price_change_24h, 2),
        "market_status": "Open" if is_market_open else "Closed",
        "company_name": stock.name,
        "sector": stock.sector
    }


async def _get_sentiment_distribution(sentiment_repo, symbol, start_date):
    """Get sentiment distribution for pie chart"""
    
    sentiment_records = await sentiment_repo.get_sentiment_by_date_range(
        symbol, start_date, datetime.utcnow()
    )
    
    positive_count = 0
    negative_count = 0
    neutral_count = 0
    
    for record in sentiment_records:
        score = float(record.sentiment_score)
        if score > 0.1:
            positive_count += 1
        elif score < -0.1:
            negative_count += 1
        else:
            neutral_count += 1
    
    total = len(sentiment_records)
    
    if total == 0:
        return {
            "positive": 0,
            "negative": 0,
            "neutral": 0,
            "total": 0
        }
    
    return {
        "positive": positive_count,
        "negative": negative_count,
        "neutral": neutral_count,
        "total": total,
        "positive_percent": round((positive_count / total) * 100, 1),
        "negative_percent": round((negative_count / total) * 100, 1),
        "neutral_percent": round((neutral_count / total) * 100, 1)
    }


async def _get_top_sentiment_performers(stock_repo, sentiment_repo, start_date):
    """Get top sentiment performers for bar chart"""
    
    # Get all active stocks
    active_stocks = await stock_repo.get_active_stocks()
    
    performers = []
    
    for stock in active_stocks[:10]:  # Limit to top 10 for performance
        sentiment_records = await sentiment_repo.get_sentiment_by_date_range(
            stock.symbol, start_date, datetime.utcnow()
        )
        
        if sentiment_records:
            sentiment_scores = [float(s.sentiment_score) for s in sentiment_records]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
            
            performers.append({
                "symbol": stock.symbol,
                "company_name": stock.name,
                "sentiment_score": round(avg_sentiment, 3),
                "data_points": len(sentiment_records)
            })
    
    # Sort by sentiment score descending
    performers.sort(key=lambda x: x["sentiment_score"], reverse=True)
    
    return performers[:5]  # Return top 5


async def _get_watchlist_overview(stock_repo, sentiment_repo, price_repo, start_date):
    """Get watchlist overview for table"""
    
    # Get all active stocks
    active_stocks = await stock_repo.get_active_stocks()
    
    watchlist_data = []
    
    for stock in active_stocks:
        # Get latest price
        latest_price = await price_repo.get_latest_price_for_stock(stock.symbol)
        current_price = float(latest_price.close_price) if latest_price else 0.0
        
        # Get 24h price change
        yesterday = datetime.utcnow() - timedelta(days=1)
        yesterday_price = await price_repo.get_price_at_time(stock.symbol, yesterday)
        
        price_change = 0.0
        if yesterday_price and latest_price:
            price_change = ((current_price - float(yesterday_price.close_price)) / float(yesterday_price.close_price)) * 100
        
        # Get sentiment
        sentiment_records = await sentiment_repo.get_sentiment_by_date_range(
            stock.symbol, start_date, datetime.utcnow()
        )
        
        avg_sentiment = 0.0
        if sentiment_records:
            sentiment_scores = [float(s.sentiment_score) for s in sentiment_records]
            avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)
        
        watchlist_data.append({
            "symbol": stock.symbol,
            "company_name": stock.name,
            "price": round(current_price, 2),
            "change": round(price_change, 2),
            "sentiment": round(avg_sentiment, 2),
            "status": "Active"
        })
    
    # Sort by sentiment score descending
    watchlist_data.sort(key=lambda x: x["sentiment"], reverse=True)
    
    return watchlist_data