"""
Dashboard Response Schemas

Pydantic models for dashboard API responses implementing U-FR1 requirements.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, ConfigDict


class StockSummary(BaseModel):
    """Summary information for a stock displayed on dashboard"""
    symbol: str = Field(..., description="Stock symbol (e.g., AAPL)")
    company_name: str = Field(..., description="Company name")
    current_price: Optional[float] = Field(None, description="Latest stock price")
    price_change_24h: Optional[float] = Field(None, description="24h price change percentage")
    sentiment_score: Optional[float] = Field(None, description="Latest sentiment score (-1.0 to 1.0)")
    sentiment_label: Optional[str] = Field(None, description="Sentiment label (Positive/Neutral/Negative)")
    last_updated: Optional[datetime] = Field(None, description="Last data update timestamp")


class MarketSentimentOverview(BaseModel):
    """Overall market sentiment metrics"""
    average_sentiment: float = Field(..., description="Market-wide average sentiment score")
    positive_stocks: int = Field(..., description="Number of stocks with positive sentiment")
    neutral_stocks: int = Field(..., description="Number of stocks with neutral sentiment")
    negative_stocks: int = Field(..., description="Number of stocks with negative sentiment")
    total_stocks: int = Field(..., description="Total number of tracked stocks")
    last_updated: datetime = Field(..., description="Last calculation timestamp")


class SystemStatus(BaseModel):
    """System operational status"""
    pipeline_status: str = Field(..., description="Data collection pipeline status")
    last_collection: Optional[datetime] = Field(None, description="Last successful data collection")
    active_data_sources: List[str] = Field(..., description="Currently active data sources")
    total_sentiment_records: int = Field(..., description="Total sentiment records in database")


class DashboardSummary(BaseModel):
    """Complete dashboard summary response - Implements U-FR1"""
    market_overview: MarketSentimentOverview
    top_stocks: List[StockSummary] = Field(..., description="Top performing stocks by sentiment")
    recent_movers: List[StockSummary] = Field(..., description="Stocks with significant recent changes")
    system_status: SystemStatus
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Response generation timestamp")

    model_config = ConfigDict()