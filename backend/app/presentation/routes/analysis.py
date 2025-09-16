"""
Analysis API Routes

Implements U-FR4: Compare Sentiment vs Price and U-FR5: Dynamic Correlation Analysis
Provides advanced analytics for sentiment-price relationships and correlation analysis.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path

from app.presentation.schemas import (
    SentimentHistory,
    CorrelationAnalysis,
    CorrelationMetrics,
    SentimentTrendPoint,
    TrendAnalysis
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

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.get("/stocks/{symbol}/sentiment", response_model=SentimentHistory)
async def get_sentiment_history(
    symbol: str = Path(..., description="Stock symbol"),
    timeframe: str = Query("7d", regex="^(1d|7d|14d)$", description="Analysis timeframe"),
    limit: int = Query(100, le=1000, description="Maximum data points to return"),
    stock_repo: StockRepository = Depends(get_stock_repository),
    sentiment_repo: SentimentDataRepository = Depends(get_sentiment_repository),
    price_repo: StockPriceRepository = Depends(get_price_repository)
) -> SentimentHistory:
    """
    Get sentiment history for dual-axis visualization - Implements U-FR4
    
    This endpoint provides time-series data for comparing sentiment vs price trends,
    enabling users to visualize correlations between market sentiment and stock performance.
    
    Args:
        symbol: Stock symbol to analyze
        timeframe: Time range for analysis (1d, 7d, 14d)
        limit: Maximum number of data points
        
    Returns:
        SentimentHistory: Time series data with sentiment scores and prices
    """
    try:
        # Validate inputs
        symbol = validate_stock_symbol(symbol)
        timeframe = validate_timeframe(timeframe)
        
        # Verify stock exists
        stock = await stock_repo.get_by_symbol(symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock '{symbol}' not found"
            )
        
        # Calculate date range
        days_map = {"1d": 1, "7d": 7, "14d": 14}
        days = days_map[timeframe]
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get sentiment and price data
        sentiment_data = await sentiment_repo.get_sentiment_by_date_range(
            symbol, start_date, datetime.utcnow()
        )
        
        # Build time series data points
        data_points = await _build_sentiment_trend_points(
            sentiment_data, symbol, price_repo, limit
        )
        
        # Calculate summary statistics
        sentiment_scores = [dp.sentiment_score for dp in data_points]
        prices = [dp.price for dp in data_points if dp.price is not None]
        
        avg_sentiment = statistics.mean(sentiment_scores) if sentiment_scores else 0.0
        sentiment_volatility = statistics.stdev(sentiment_scores) if len(sentiment_scores) > 1 else 0.0
        
        # Calculate price correlation
        price_correlation = None
        if len(prices) > 1 and len(sentiment_scores) > 1:
            price_correlation = _calculate_correlation(sentiment_scores, prices)
        
        # Calculate data quality metrics
        expected_hours = days * 24
        data_coverage = min(1.0, len(data_points) / expected_hours) if expected_hours > 0 else 0.0
        
        return SentimentHistory(
            symbol=symbol,
            timeframe=timeframe,
            data_points=data_points,
            avg_sentiment=round(avg_sentiment, 3),
            sentiment_volatility=round(sentiment_volatility, 3),
            price_correlation=round(price_correlation, 3) if price_correlation else None,
            total_records=len(data_points),
            data_coverage=round(data_coverage, 3)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sentiment history: {str(e)}"
        )


@router.get("/stocks/{symbol}/correlation", response_model=CorrelationAnalysis)
async def get_correlation_analysis(
    symbol: str = Path(..., description="Stock symbol"),
    timeframe: str = Query("7d", regex="^(1d|7d|14d)$", description="Analysis timeframe"),
    stock_repo: StockRepository = Depends(get_stock_repository),
    sentiment_repo: SentimentDataRepository = Depends(get_sentiment_repository),
    price_repo: StockPriceRepository = Depends(get_price_repository)
) -> CorrelationAnalysis:
    """
    Get real-time Pearson correlation calculation - Implements U-FR5
    
    Provides comprehensive correlation analysis between sentiment and price movements,
    including statistical significance, confidence intervals, and trend analysis.
    
    Args:
        symbol: Stock symbol to analyze
        timeframe: Time range for correlation analysis
        
    Returns:
        CorrelationAnalysis: Detailed correlation metrics and trend analysis
    """
    try:
        # Validate inputs
        symbol = validate_stock_symbol(symbol)
        timeframe = validate_timeframe(timeframe)
        
        # Verify stock exists
        stock = await stock_repo.get_by_symbol(symbol)
        if not stock:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stock '{symbol}' not found"
            )
        
        # Calculate date range
        days_map = {"1d": 1, "7d": 7, "14d": 14}
        days = days_map[timeframe]
        start_date = datetime.utcnow() - timedelta(days=days)
        end_date = datetime.utcnow()
        
        # Get data for correlation analysis
        correlation_data = await _get_correlation_data(
            sentiment_repo, price_repo, symbol, start_date, end_date
        )
        
        if len(correlation_data) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient data for correlation analysis (minimum 3 data points required)"
            )
        
        # Calculate correlation metrics
        correlation_metrics = _calculate_correlation_metrics(correlation_data)
        
        # Analyze trends
        sentiment_trend = _analyze_trend([d['sentiment'] for d in correlation_data])
        price_trend = _analyze_trend([d['price'] for d in correlation_data])
        
        # Prepare scatter plot data
        scatter_data = [
            {"sentiment": d['sentiment'], "price": d['price']}
            for d in correlation_data
        ]
        
        # Calculate trend line parameters
        trend_line = _calculate_trend_line(correlation_data)
        
        # Calculate data quality
        expected_points = days * 24  # Hourly data expected
        data_quality = min(1.0, len(correlation_data) / expected_points)
        
        return CorrelationAnalysis(
            symbol=symbol,
            timeframe=timeframe,
            correlation_metrics=correlation_metrics,
            sentiment_trend=sentiment_trend,
            price_trend=price_trend,
            scatter_data=scatter_data,
            trend_line=trend_line,
            analysis_period={
                "start": start_date,
                "end": end_date
            },
            data_quality=round(data_quality, 3),
            last_updated=datetime.utcnow()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform correlation analysis: {str(e)}"
        )


async def _build_sentiment_trend_points(
    sentiment_data: List,
    symbol: str,
    price_repo: StockPriceRepository,
    limit: int
) -> List[SentimentTrendPoint]:
    """Build sentiment trend points with corresponding price data"""
    
    trend_points = []
    
    for sentiment_record in sentiment_data[:limit]:
        # Get price data closest to sentiment timestamp
        price_record = await price_repo.get_price_at_time(symbol, sentiment_record.created_at)
        
        trend_points.append(SentimentTrendPoint(
            timestamp=sentiment_record.created_at,
            sentiment_score=sentiment_record.sentiment_score,
            price=price_record.close_price if price_record else None,
            volume=price_record.volume if price_record else None,
            source_count=1  # Simplified - each record represents one source
        ))
    
    return trend_points


async def _get_correlation_data(
    sentiment_repo: SentimentDataRepository,
    price_repo: StockPriceRepository,
    symbol: str,
    start_date: datetime,
    end_date: datetime
) -> List[Dict[str, float]]:
    """Get paired sentiment and price data for correlation analysis"""
    
    # Get sentiment data
    sentiment_records = await sentiment_repo.get_sentiment_by_date_range(
        symbol, start_date, end_date
    )
    
    correlation_data = []
    
    for sentiment_record in sentiment_records:
        # Find closest price record
        price_record = await price_repo.get_price_at_time(symbol, sentiment_record.created_at)
        
        if price_record:
            correlation_data.append({
                'timestamp': sentiment_record.created_at,
                'sentiment': float(sentiment_record.sentiment_score),
                'price': float(price_record.close_price)
            })
    
    return correlation_data


def _calculate_correlation_metrics(data: List[Dict[str, float]]) -> CorrelationMetrics:
    """Calculate comprehensive correlation statistics"""
    
    sentiments = [d['sentiment'] for d in data]
    prices = [d['price'] for d in data]
    
    # Calculate Pearson correlation
    correlation = _calculate_correlation(sentiments, prices)
    
    # Calculate p-value (simplified approximation)
    n = len(data)
    t_stat = correlation * ((n - 2) / (1 - correlation**2))**0.5 if correlation != 1 else float('inf')
    p_value = 0.05 if abs(t_stat) > 2 else 0.1  # Simplified p-value approximation
    
    # Calculate confidence interval (simplified)
    margin_error = 1.96 / (n**0.5) if n > 0 else 0
    confidence_interval = [
        max(-1.0, correlation - margin_error),
        min(1.0, correlation + margin_error)
    ]
    
    # Calculate R-squared
    r_squared = correlation**2
    
    return CorrelationMetrics(
        pearson_correlation=round(correlation, 4),
        p_value=round(p_value, 4),
        confidence_interval=[round(ci, 4) for ci in confidence_interval],
        sample_size=n,
        r_squared=round(r_squared, 4)
    )


def _calculate_correlation(x: List[float], y: List[float]) -> float:
    """Calculate Pearson correlation coefficient"""
    
    if len(x) != len(y) or len(x) < 2:
        return 0.0
    
    n = len(x)
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)
    
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    
    sum_sq_x = sum((x[i] - mean_x)**2 for i in range(n))
    sum_sq_y = sum((y[i] - mean_y)**2 for i in range(n))
    
    denominator = (sum_sq_x * sum_sq_y)**0.5
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator


def _analyze_trend(values: List[float]) -> str:
    """Analyze trend direction in a series of values"""
    
    if len(values) < 3:
        return "stable"
    
    # Simple trend analysis using first and last values
    first_third = statistics.mean(values[:len(values)//3])
    last_third = statistics.mean(values[-len(values)//3:])
    
    change_percent = ((last_third - first_third) / abs(first_third)) * 100 if first_third != 0 else 0
    
    if change_percent > 5:
        return "increasing"
    elif change_percent < -5:
        return "decreasing"
    else:
        return "stable"


def _calculate_trend_line(data: List[Dict[str, float]]) -> Dict[str, Any]:
    """Calculate linear regression trend line parameters"""
    
    sentiments = [d['sentiment'] for d in data]
    prices = [d['price'] for d in data]
    
    n = len(data)
    if n < 2:
        return {"slope": 0, "intercept": 0, "r_squared": 0}
    
    # Calculate linear regression
    mean_x = statistics.mean(sentiments)
    mean_y = statistics.mean(prices)
    
    numerator = sum((sentiments[i] - mean_x) * (prices[i] - mean_y) for i in range(n))
    denominator = sum((sentiments[i] - mean_x)**2 for i in range(n))
    
    if denominator == 0:
        slope = 0
    else:
        slope = numerator / denominator
    
    intercept = mean_y - slope * mean_x
    
    # Calculate R-squared
    correlation = _calculate_correlation(sentiments, prices)
    r_squared = correlation**2
    
    return {
        "slope": round(slope, 4),
        "intercept": round(intercept, 4),
        "r_squared": round(r_squared, 4)
    }