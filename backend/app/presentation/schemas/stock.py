"""
Stock Response Schemas

Pydantic models for stock API responses implementing U-FR2 and U-FR3 requirements.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict
from app.utils.timezone import utc_now


class PriceDataPoint(BaseModel):
    """Individual price data point"""
    timestamp: datetime = Field(..., description="Price timestamp")
    open_price: Optional[float] = Field(None, description="Opening price")
    close_price: float = Field(..., description="Closing price")
    high_price: Optional[float] = Field(None, description="Highest price")
    low_price: Optional[float] = Field(None, description="Lowest price")
    volume: Optional[int] = Field(None, description="Trading volume")


class SentimentDataPoint(BaseModel):
    """Individual sentiment data point"""
    timestamp: datetime = Field(..., description="Sentiment timestamp")
    score: float = Field(..., description="Sentiment score (-1.0 to 1.0)")
    label: str = Field(..., description="Sentiment label (Positive/Neutral/Negative)")
    confidence: Optional[float] = Field(None, description="Model confidence score")
    source: str = Field(..., description="Data source (hackernews, news, etc.)")


class StockMetrics(BaseModel):
    """Statistical metrics for a stock"""
    avg_sentiment: float = Field(..., description="Average sentiment score")
    sentiment_volatility: float = Field(..., description="Sentiment standard deviation")
    price_change_percent: Optional[float] = Field(None, description="Price change percentage")
    total_sentiment_records: int = Field(..., description="Number of sentiment records")
    data_quality_score: float = Field(..., description="Data quality score (0.0 to 1.0)")


class StockDetail(BaseModel):
    """Detailed stock information - Implements U-FR2 & U-FR3"""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Business sector")
    
    # Time series data
    price_history: List[PriceDataPoint] = Field(..., description="Historical price data")
    sentiment_history: List[SentimentDataPoint] = Field(..., description="Historical sentiment data")
    
    # Aggregated metrics
    metrics: StockMetrics = Field(..., description="Statistical metrics")
    
    # Metadata
    timeframe: str = Field(..., description="Data timeframe (1d, 7d, 14d)")
    last_updated: datetime = Field(..., description="Last data update")
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict()


class StockListItem(BaseModel):
    """Stock list item for /api/stocks endpoint"""
    symbol: str = Field(..., description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Business sector")
    is_active: bool = Field(..., description="Whether stock is actively tracked")
    latest_sentiment: Optional[float] = Field(None, description="Latest sentiment score")
    latest_price: Optional[float] = Field(None, description="Latest stock price")
    last_updated: Optional[datetime] = Field(None, description="Last update timestamp")


class StockList(BaseModel):
    """List of all tracked stocks - Implements U-FR3"""
    stocks: List[StockListItem]
    total_count: int = Field(..., description="Total number of stocks")
    active_count: int = Field(..., description="Number of actively tracked stocks")
    generated_at: datetime = Field(default_factory=utc_now)

    model_config = ConfigDict()