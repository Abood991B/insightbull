"""
Dashboard Use Cases
===================

Business logic for dashboard-related operations.
Implements the business rules for dashboard data aggregation and processing.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import structlog

from app.business.entities.dashboard_entities import DashboardData, SentimentMetrics


logger = structlog.get_logger()


class DashboardUseCases:
    """Use cases for dashboard operations."""
    
    def __init__(self):
        """Initialize dashboard use cases."""
        self.logger = logger.bind(component="DashboardUseCases")
    
    async def get_dashboard_overview(self, time_period: str = "7d") -> DashboardData:
        """
        Get dashboard overview data.
        
        Args:
            time_period: Time period for data aggregation
            
        Returns:
            DashboardData: Aggregated dashboard information
        """
        self.logger.info("Getting dashboard overview", time_period=time_period)
        
        # Use DashboardService for real data
        from app.service.dashboard_service import DashboardService
        dashboard_service = DashboardService(self.db)
        
        # Get real dashboard data
        overview_data = await dashboard_service.get_dashboard_overview(time_period)
        
        # Convert to DashboardData schema
        from app.presentation.schemas.dashboard import SentimentMetrics
        
        return DashboardData(
            sentiment_overview=SentimentMetrics(
                overall_sentiment=overview_data["sentiment_overview"]["overall_sentiment"],
                sentiment_score=overview_data["sentiment_overview"]["sentiment_score"],
                confidence=overview_data["sentiment_overview"]["confidence"]
            ),
            time_period=time_period,
            stock_data=overview_data["stock_data"],
            sentiment_trends=overview_data["sentiment_trends"],
            news_summary=overview_data["news_summary"]
        )
    
    async def get_time_range_data(self, start_date: datetime, end_date: datetime) -> DashboardData:
        """
        Get dashboard data for a specific time range.
        
        Implements U-FR2: Select Time Range
        
        Args:
            start_date: Start date for data range
            end_date: End date for data range
            
        Returns:
            DashboardData: Data for the specified time range
        """
        self.logger.info("Getting time range data", start_date=start_date, end_date=end_date)
        
        # Implementation will be added in later phases
        time_period = f"{start_date.strftime('%Y-%m-%d')}_to_{end_date.strftime('%Y-%m-%d')}"
        
        return await self.get_dashboard_overview(time_period)