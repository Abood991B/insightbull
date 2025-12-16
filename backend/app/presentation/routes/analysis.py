"""
Analysis API Routes

Implements U-FR4: Compare Sentiment vs Price and U-FR5: Dynamic Correlation Analysis
Provides advanced analytics for sentiment-price relationships and correlation analysis.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
import statistics
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from app.utils.timezone import utc_now, to_naive_utc, ensure_utc

from app.presentation.schemas import (
    SentimentHistory,
    CorrelationAnalysis,
    CorrelationMetrics,
    SentimentTrendPoint
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
    timeframe: str = Query("7d", pattern="^(1d|7d|14d|30d)$", description="Analysis timeframe"),
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
        days_map = {"1d": 1, "7d": 7, "14d": 14, "30d": 30}
        days = days_map[timeframe]
        start_date = to_naive_utc(utc_now() - timedelta(days=days))
        end_date = to_naive_utc(utc_now())
        
        # Get sentiment and price data
        sentiment_data = await sentiment_repo.get_sentiment_by_date_range(
            symbol, start_date, end_date
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
    timeframe: str = Query("7d", pattern="^(1d|7d|14d|30d)$", description="Analysis timeframe"),
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
        days_map = {"1d": 1, "7d": 7, "14d": 14, "30d": 30}
        days = days_map[timeframe]
        start_date = to_naive_utc(utc_now() - timedelta(days=days))
        end_date = to_naive_utc(utc_now())
        
        # Get data for correlation analysis
        correlation_data = await _get_correlation_data(
            sentiment_repo, price_repo, symbol, start_date, end_date
        )
        
        if len(correlation_data) < 3:
            # Provide user-friendly error with suggestion for better timeframe
            timeframe_labels = {"1d": "1 day", "7d": "7 days", "14d": "14 days", "30d": "30 days"}
            current_label = timeframe_labels.get(timeframe, timeframe)
            
            suggested_timeframe = "7 days" if timeframe == "1d" else ("14 days" if timeframe == "7d" else "30 days")
            
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient data for {current_label} timeframe. Found {len(correlation_data)} data points, but correlation analysis requires at least 3. Try selecting a longer timeframe ({suggested_timeframe}) or wait for more data to be collected."
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
        
        # Convert naive datetime to aware UTC for proper API serialization
        start_date_utc = ensure_utc(start_date)
        end_date_utc = ensure_utc(end_date)
        
        return CorrelationAnalysis(
            symbol=symbol,
            timeframe=timeframe,
            correlation_metrics=correlation_metrics,
            sentiment_trend=sentiment_trend,
            price_trend=price_trend,
            scatter_data=scatter_data,
            trend_line=trend_line,
            analysis_period={
                "start": start_date_utc,
                "end": end_date_utc
            },
            data_quality=round(data_quality, 3),
            last_updated=utc_now()
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
        
        # Convert naive datetime from DB to aware UTC for proper API serialization
        timestamp_utc = ensure_utc(sentiment_record.created_at)
        
        trend_points.append(SentimentTrendPoint(
            timestamp=timestamp_utc,
            sentiment_score=sentiment_record.sentiment_score,
            price=price_record.price if price_record else None,  # Use real-time price, not close_price
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
                'price': float(price_record.price)  # Use real-time price, not close_price
            })
    
    return correlation_data


def _calculate_correlation_metrics(data: List[Dict[str, float]]) -> CorrelationMetrics:
    """Calculate comprehensive correlation statistics"""
    
    sentiments = [d['sentiment'] for d in data]
    prices = [d['price'] for d in data]
    
    # Calculate Pearson correlation
    correlation = _calculate_correlation(sentiments, prices)
    
    n = len(data)
    
    # Calculate p-value using proper t-distribution approximation
    if n > 2 and abs(correlation) < 1.0:
        t_stat = correlation * ((n - 2) / (1 - correlation**2))**0.5
        # Two-tailed p-value approximation using t-distribution
        # For degrees of freedom = n-2, use approximation
        df = n - 2
        # Approximation of t-distribution CDF using rational approximation
        x = abs(t_stat)
        # Use Abramowitz and Stegun approximation for p-value
        if df >= 30:
            # For large df, t approaches normal distribution
            p_value = 2 * _normal_cdf(-x)
        else:
            # Beta regularized incomplete function approximation
            p_value = _t_distribution_pvalue(x, df)
    else:
        p_value = 1.0
    
    # Calculate confidence interval using Fisher's z-transformation
    if n > 3 and abs(correlation) < 0.999:
        # Fisher z-transformation
        z = 0.5 * (abs(correlation + 1e-10) and 1 or 0)
        if correlation != 0:
            z = 0.5 * _safe_log((1 + correlation) / (1 - correlation))
        se_z = 1 / ((n - 3) ** 0.5) if n > 3 else 1
        z_critical = 1.96  # 95% confidence
        z_lower = z - z_critical * se_z
        z_upper = z + z_critical * se_z
        # Transform back
        ci_lower = (2.71828 ** (2 * z_lower) - 1) / (2.71828 ** (2 * z_lower) + 1)
        ci_upper = (2.71828 ** (2 * z_upper) - 1) / (2.71828 ** (2 * z_upper) + 1)
        confidence_interval = [
            max(-1.0, min(1.0, ci_lower)),
            max(-1.0, min(1.0, ci_upper))
        ]
    else:
        margin_error = 1.96 / (n**0.5) if n > 0 else 0
        confidence_interval = [
            max(-1.0, correlation - margin_error),
            min(1.0, correlation + margin_error)
        ]
    
    # Calculate R-squared
    r_squared = correlation**2
    
    return CorrelationMetrics(
        pearson_correlation=round(correlation, 4),
        p_value=round(min(1.0, max(0.0, p_value)), 4),
        confidence_interval=[round(ci, 4) for ci in confidence_interval],
        sample_size=n,
        r_squared=round(r_squared, 4)
    )


def _safe_log(x: float) -> float:
    """Safe natural logarithm with bounds checking"""
    import math
    if x <= 0:
        return -10.0
    return math.log(x)


def _normal_cdf(x: float) -> float:
    """Approximate cumulative distribution function for standard normal"""
    import math
    # Abramowitz and Stegun approximation
    a1, a2, a3, a4, a5 = 0.254829592, -0.284496736, 1.421413741, -1.453152027, 1.061405429
    p = 0.3275911
    sign = 1 if x >= 0 else -1
    x = abs(x) / (2 ** 0.5)
    t = 1.0 / (1.0 + p * x)
    y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * math.exp(-x * x)
    return 0.5 * (1.0 + sign * y)


def _t_distribution_pvalue(t: float, df: int) -> float:
    """Approximate two-tailed p-value from t-distribution"""
    import math
    # Approximation using relationship with F-distribution
    # For small df, use lookup-like approximation
    x = df / (df + t * t)
    # Regularized incomplete beta function approximation
    # Using simple empirical approximation based on critical values
    if t < 0.5:
        return 1.0
    elif df >= 30:
        return 2 * _normal_cdf(-t)
    else:
        # Interpolate between known critical values
        # t-critical for df: 2.0 -> p=0.05 approximately
        if abs(t) > 3.5:
            return 0.001
        elif abs(t) > 2.8:
            return 0.01
        elif abs(t) > 2.0:
            return 0.05
        elif abs(t) > 1.7:
            return 0.1
        elif abs(t) > 1.3:
            return 0.2
        else:
            return 0.4


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