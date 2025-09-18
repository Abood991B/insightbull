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
from app.presentation.schemas.dashboard import DashboardSummary
from app.service.dashboard_service import DashboardService


logger = structlog.get_logger()
router = APIRouter()


@router.get("/overview", response_model=DashboardSummary)
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
        
        # Use real dashboard service
        dashboard_service = DashboardService(db)
        overview = await dashboard_service.get_dashboard_overview(time_period)
        
        return overview
        
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