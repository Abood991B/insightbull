"""
Analysis Response Schemas

Pydantic models for analysis API responses implementing U-FR4 and U-FR5 requirements.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.utils.timezone import utc_now


class SentimentTrendPoint(BaseModel):
    """Sentiment trend data point for time series analysis"""
    timestamp: datetime = Field(..., description="Data timestamp")
    sentiment_score: float = Field(..., description="Sentiment score (-1.0 to 1.0)")
    price: Optional[float] = Field(None, description="Stock price at timestamp")
    volume: Optional[int] = Field(None, description="Trading volume")
    source_count: int = Field(..., description="Number of sentiment sources")


class SentimentHistory(BaseModel):
    """Historical sentiment data with price correlation - Implements U-FR4"""
    symbol: str = Field(..., description="Stock symbol")
    timeframe: str = Field(..., description="Data timeframe")
    data_points: List[SentimentTrendPoint] = Field(..., description="Time series data points")
    
    # Summary statistics
    avg_sentiment: float = Field(..., description="Average sentiment score")
    sentiment_volatility: float = Field(..., description="Sentiment standard deviation")
    price_correlation: Optional[float] = Field(None, description="Sentiment-price correlation")
    
    # Data quality metrics
    total_records: int = Field(..., description="Total number of data points")
    data_coverage: float = Field(..., description="Data coverage percentage")
    
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict()


class CorrelationMetrics(BaseModel):
    """Statistical correlation metrics"""
    pearson_correlation: float = Field(..., description="Pearson correlation coefficient (-1.0 to 1.0)")
    p_value: float = Field(..., description="Statistical significance p-value")
    confidence_interval: List[float] = Field(..., description="95% confidence interval [lower, upper]")
    sample_size: int = Field(..., description="Number of data points used")
    r_squared: float = Field(..., description="Coefficient of determination")


class CorrelationAnalysis(BaseModel):
    """Real-time correlation analysis - Implements U-FR5"""
    symbol: str = Field(..., description="Stock symbol")
    timeframe: str = Field(..., description="Analysis timeframe")
    
    # Correlation metrics
    correlation_metrics: CorrelationMetrics = Field(..., description="Statistical correlation metrics")
    
    # Trend analysis
    sentiment_trend: str = Field(..., description="Sentiment trend (increasing/decreasing/stable)")
    price_trend: str = Field(..., description="Price trend (increasing/decreasing/stable)")
    
    # Visual data for charts
    scatter_data: List[Dict[str, float]] = Field(..., description="Scatter plot data points")
    trend_line: Dict[str, Any] = Field(..., description="Regression trend line parameters")
    
    # Analysis metadata
    analysis_period: Dict[str, datetime] = Field(..., description="Analysis start and end dates")
    data_quality: float = Field(..., description="Data quality score (0.0 to 1.0)")
    last_updated: datetime = Field(..., description="Last data update")
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict()


class TrendAnalysis(BaseModel):
    """Trend analysis for sentiment and price movements"""
    direction: str = Field(..., description="Trend direction (up/down/stable)")
    strength: float = Field(..., description="Trend strength (0.0 to 1.0)")
    duration_days: int = Field(..., description="Trend duration in days")
    confidence: float = Field(..., description="Trend confidence score (0.0 to 1.0)")


class ComparisonAnalysis(BaseModel):
    """Multi-stock comparison analysis"""
    stocks: List[str] = Field(..., description="Stock symbols being compared")
    timeframe: str = Field(..., description="Comparison timeframe")
    
    # Comparative metrics
    sentiment_rankings: List[Dict[str, Any]] = Field(..., description="Stocks ranked by sentiment")
    correlation_matrix: Dict[str, Dict[str, float]] = Field(..., description="Correlation matrix between stocks")
    performance_metrics: Dict[str, Dict[str, float]] = Field(..., description="Performance metrics per stock")
    
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict()