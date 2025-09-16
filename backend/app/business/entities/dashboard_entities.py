"""
Dashboard Entities
==================

Business domain entities for dashboard-related data.
Represents the core business objects and their relationships.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class SentimentMetrics:
    """Sentiment metrics entity."""
    overall_sentiment: str
    sentiment_score: float
    confidence: float


@dataclass
class StockInfo:
    """Stock information entity."""
    symbol: str
    price: Optional[float] = None
    change: Optional[float] = None
    change_percent: Optional[float] = None
    sentiment_score: Optional[float] = None


@dataclass
class SentimentDataPoint:
    """Individual sentiment data point."""
    timestamp: datetime
    sentiment_score: float
    volume: int


@dataclass 
class DashboardData:
    """Complete dashboard data entity."""
    sentiment_overview: SentimentMetrics
    time_period: str
    stock_data: List[StockInfo]
    sentiment_trends: List[SentimentDataPoint]
    news_summary: Dict[str, Any]