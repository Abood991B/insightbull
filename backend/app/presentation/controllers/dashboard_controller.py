"""
Dashboard Controller
====================

FastAPI controller for dashboard-related endpoints.
Handles dashboard data, metrics, and overview information.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.data_access.database import get_db
from app.presentation.schemas.dashboard_schemas import DashboardResponse
from app.business.use_cases.dashboard_use_cases import DashboardUseCases


logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview", response_model=DashboardResponse)
async def get_dashboard_overview(
    time_period: str = "7d",
    db: AsyncSession = Depends(get_db)
):
    """
    Get dashboard overview data.
    
    Implements U-FR1: View Sentiment Dashboard
    """
    try:
        logger.info("Getting dashboard overview", time_period=time_period)
        
        # For now, return mock data structure
        # This will be implemented in later phases
        return {
            "sentiment_overview": {
                "overall_sentiment": "neutral",
                "sentiment_score": 0.1,
                "confidence": 0.75
            },
            "time_period": time_period,
            "stock_data": [],
            "sentiment_trends": [],
            "news_summary": {
                "total_articles": 0,
                "sentiment_distribution": {"positive": 0, "neutral": 0, "negative": 0}
            }
        }
        
    except Exception as e:
        logger.error("Error getting dashboard overview", error=str(e), exc_info=True) 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/health")
async def dashboard_health():
    """Health check for dashboard controller."""
    return {"status": "healthy", "controller": "dashboard"}