"""
Admin Controller
================

FastAPI controller for admin-related endpoints.
Handles admin authentication, system management, and configuration.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.data_access.database import get_db


logger = structlog.get_logger()
router = APIRouter()


@router.get("/system-status")
async def get_system_status(
    db: AsyncSession = Depends(get_db)
):
    """
    Get system status and health information.
    
    Implements SY-FR1: System Monitoring
    """
    try:
        logger.info("Getting system status")
        
        # Mock response for now
        return {
            "status": "operational",
            "services": {
                "database": "healthy",
                "redis": "healthy", 
                "sentiment_engine": "healthy",
                "data_collection": "healthy"
            },
            "metrics": {
                "uptime": "0 hours",
                "processed_articles": 0,
                "active_stocks": 0,
                "last_update": None
            }
        }
        
    except Exception as e:
        logger.error("Error getting system status", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


@router.get("/logs")
async def get_system_logs(
    limit: int = 100,
    level: str = "INFO",
    db: AsyncSession = Depends(get_db)
):
    """
    Get system logs.
    
    Implements SY-FR2: Logging System
    """
    try:
        logger.info("Getting system logs", limit=limit, level=level)
        
        # Mock response for now
        return {
            "logs": [],
            "total": 0,
            "level": level,
            "limit": limit
        }
        
    except Exception as e:
        logger.error("Error getting system logs", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system logs"
        )


@router.post("/data-collection/trigger")
async def trigger_data_collection(
    stock_symbols: list[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Manually trigger data collection.
    
    Implements SY-FR3: Manual Data Collection
    """
    try:
        logger.info("Triggering data collection", stock_symbols=stock_symbols)
        
        # Mock response for now
        return {
            "status": "initiated",
            "stock_symbols": stock_symbols or [],
            "estimated_completion": "5 minutes"
        }
        
    except Exception as e:
        logger.error("Error triggering data collection", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger data collection"
        )


@router.get("/health")
async def admin_health():
    """Health check for admin controller."""
    return {"status": "healthy", "controller": "admin"}