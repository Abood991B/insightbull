"""
Presentation Schemas

Centralized imports for all API response schemas.
"""

from .dashboard import (
    DashboardSummary,
    MarketSentimentOverview,
    StockSummary,
    SystemStatus
)

from .stock import (
    StockDetail,
    StockList,
    StockListItem,
    StockMetrics,
    PriceDataPoint,
    SentimentDataPoint
)

from .analysis import (
    SentimentHistory,
    CorrelationAnalysis,
    CorrelationMetrics,
    SentimentTrendPoint,
    TrendAnalysis,
    ComparisonAnalysis
)

__all__ = [
    # Dashboard schemas
    "DashboardSummary",
    "MarketSentimentOverview", 
    "StockSummary",
    "SystemStatus",
    
    # Stock schemas
    "StockDetail",
    "StockList",
    "StockListItem",
    "StockMetrics",
    "PriceDataPoint",
    "SentimentDataPoint",
    
    # Analysis schemas
    "SentimentHistory",
    "CorrelationAnalysis",
    "CorrelationMetrics",
    "SentimentTrendPoint",
    "TrendAnalysis",
    "ComparisonAnalysis"
]