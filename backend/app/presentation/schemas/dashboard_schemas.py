"""
Dashboard Schemas
=================

Pydantic schemas for dashboard-related API requests and responses.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class SentimentOverview(BaseModel):
    """Overall sentiment summary."""
    overall_sentiment: str = Field(..., description="Overall sentiment (positive/neutral/negative)")
    sentiment_score: float = Field(..., description="Numerical sentiment score (-1 to 1)")
    confidence: float = Field(..., description="Confidence level (0 to 1)")


class StockData(BaseModel):
    """Stock data model."""
    symbol: str = Field(..., description="Stock symbol")
    price: Optional[float] = Field(None, description="Current stock price")
    change: Optional[float] = Field(None, description="Price change")
    change_percent: Optional[float] = Field(None, description="Price change percentage")
    sentiment_score: Optional[float] = Field(None, description="Sentiment score for this stock")


class SentimentTrend(BaseModel):
    """Sentiment trend data point."""
    timestamp: datetime = Field(..., description="Data point timestamp")
    sentiment_score: float = Field(..., description="Sentiment score at this time")
    volume: int = Field(..., description="Number of data points")


class NewsSummary(BaseModel):
    """News summary statistics."""
    total_articles: int = Field(..., description="Total number of articles analyzed")
    sentiment_distribution: Dict[str, int] = Field(..., description="Distribution of sentiment classifications")


class DashboardResponse(BaseModel):
    """Dashboard overview response model."""
    sentiment_overview: SentimentOverview
    time_period: str = Field(..., description="Time period for the data")
    stock_data: List[StockData] = Field(default_factory=list)
    sentiment_trends: List[SentimentTrend] = Field(default_factory=list)
    news_summary: NewsSummary
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }