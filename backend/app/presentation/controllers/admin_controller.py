"""
Admin Controller
================

FastAPI controller for admin-related endpoints.
Handles admin authentication, system management, and configuration.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.data_access.database import get_db
from app.presentation.dependencies import (
    get_current_admin_user,
    get_optional_admin_user,
    require_admin,
    auth_responses
)
from app.infrastructure.security.auth_service import AuthService, AdminUser
from app.infrastructure.config.settings import Settings, get_settings
from app.presentation.schemas.dashboard_schemas import *


logger = structlog.get_logger()
router = APIRouter()


# Authentication endpoints for admin integration
@router.post("/auth/validate", responses={**auth_responses})
async def validate_admin_token(
    admin_user: Annotated[AdminUser, Depends(get_current_admin_user)]
):
    """
    Validate admin JWT token from frontend authentication
    
    This endpoint validates tokens created by the existing frontend
    OAuth2 + TOTP authentication system.
    """
    logger.info(f"Admin token validated for user: {admin_user.email}")
    return {
        "valid": True,
        "user_id": admin_user.user_id,
        "email": admin_user.email,
        "permissions": admin_user.permissions,
        "last_login": admin_user.last_login.isoformat() if admin_user.last_login else None
    }


@router.get("/auth/verify", responses={**auth_responses})
async def verify_admin_session(
    admin_user: Annotated[AdminUser, Depends(get_current_admin_user)]
):
    """
    Verify admin session is still active
    """
    return {
        "authenticated": True,
        "user": {
            "id": admin_user.user_id,
            "email": admin_user.email,
            "permissions": admin_user.permissions
        }
    }


@router.post("/auth/refresh")
async def refresh_admin_token(
    refresh_data: dict,
    settings: Annotated[Settings, Depends(get_settings)]
):
    """
    Refresh admin access token
    """
    auth_service = AuthService(settings)
    refresh_token = refresh_data.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Refresh token required"
        )
    
    tokens = await auth_service.refresh_admin_token(refresh_token)
    
    if not tokens:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired refresh token"
        )
    
    return tokens


@router.get("/system-status", responses={**auth_responses})
async def get_system_status(
    admin_user: Annotated[AdminUser, Depends(get_current_admin_user)],
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