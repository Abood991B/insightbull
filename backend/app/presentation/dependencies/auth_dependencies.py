"""
Authentication Dependencies for Route Protection

This module provides FastAPI dependencies for protecting admin routes
and validating user sessions. Integrates with the existing frontend
authentication system.

Features:
- JWT token validation dependency
- Admin permission checking
- Activity logging for admin actions
- Optional authentication for public endpoints

Following FYP security requirements.
"""

from typing import Optional, Annotated
import logging

from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.security.auth_service import AuthService, AdminUser


logger = logging.getLogger(__name__)

# Security scheme for OpenAPI documentation
security = HTTPBearer(auto_error=False)


async def get_auth_service(
    settings: Annotated[Settings, Depends(get_settings)]
) -> AuthService:
    """
    Dependency to get AuthService instance
    
    Returns:
        AuthService instance
    """
    return AuthService(settings)


async def get_current_admin_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> AdminUser:
    """
    Dependency to get current authenticated admin user
    
    This dependency validates JWT tokens from the frontend authentication system
    and ensures the user has admin permissions.
    
    Args:
        credentials: HTTP Bearer token credentials
        auth_service: Authentication service instance
        
    Returns:
        AdminUser object if authentication successful
        
    Raises:
        HTTPException: If authentication fails
    """
    if not credentials:
        logger.warning("No authorization credentials provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Validate token and get admin user
    admin_user = await auth_service.validate_admin_token(credentials.credentials)
    
    if not admin_user:
        logger.warning("Invalid or expired authentication token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not admin_user.is_active:
        logger.warning(f"Inactive admin user attempted access: {admin_user.email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin account is deactivated"
        )
    
    return admin_user


async def get_optional_admin_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> Optional[AdminUser]:
    """
    Dependency to optionally get current admin user
    
    This dependency is for endpoints that can be accessed by both
    authenticated and unauthenticated users, but may provide different
    functionality based on authentication status.
    
    Args:
        credentials: Optional HTTP Bearer token credentials
        auth_service: Authentication service instance
        
    Returns:
        AdminUser object if authenticated, None otherwise
    """
    if not credentials:
        return None
    
    try:
        admin_user = await auth_service.validate_admin_token(credentials.credentials)
        if admin_user and admin_user.is_active:
            return admin_user
    except Exception as e:
        logger.debug(f"Optional authentication failed: {str(e)}")
    
    return None


def require_admin_permission(permission: str = "admin"):
    """
    Dependency factory to require specific admin permissions
    
    Args:
        permission: Required permission level
        
    Returns:
        Dependency function that validates the permission
    """
    async def permission_dependency(
        admin_user: Annotated[AdminUser, Depends(get_current_admin_user)],
        auth_service: Annotated[AuthService, Depends(get_auth_service)]
    ) -> AdminUser:
        """
        Validate admin has required permission
        
        Args:
            admin_user: Current admin user
            auth_service: Authentication service
            
        Returns:
            AdminUser if permission check passes
            
        Raises:
            HTTPException: If permission check fails
        """
        has_permission = await auth_service.verify_admin_permissions(
            admin_user, permission
        )
        
        if not has_permission:
            logger.warning(
                f"Admin user {admin_user.email} attempted access without "
                f"required permission: {permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {permission}"
            )
        
        return admin_user
    
    return permission_dependency


async def log_admin_activity(
    admin_user: Annotated[AdminUser, Depends(get_current_admin_user)],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    Dependency to log admin activity
    
    This can be used with endpoints that need activity logging
    
    Args:
        admin_user: Current admin user
        auth_service: Authentication service
    """
    # The actual logging will be done in the endpoint using auth_service.log_admin_activity
    return {"admin_user": admin_user, "auth_service": auth_service}


# Convenience dependencies for common permission levels
require_admin = require_admin_permission("admin")
require_view_logs = require_admin_permission("view_logs")
require_manage_watchlist = require_admin_permission("manage_watchlist")
require_configure_apis = require_admin_permission("configure_apis")
require_manage_storage = require_admin_permission("manage_storage")


async def validate_api_key(
    x_api_key: Annotated[Optional[str], Header(alias="X-API-Key")] = None,
    settings: Annotated[Settings, Depends(get_settings)] = None
) -> bool:
    """
    Dependency to validate API key for external integrations
    
    This is for potential future API key based authentication
    for external systems or public API access.
    
    Args:
        x_api_key: API key from header
        settings: Application settings
        
    Returns:
        True if API key is valid, False otherwise
    """
    if not x_api_key:
        return False
    
    # Basic API key validation - should be alphanumeric and sufficient length
    return len(x_api_key) >= 32 and x_api_key.isalnum()


async def rate_limit_check(
    request_count: int = 1,
    window_minutes: int = 60
):
    """
    Dependency for additional rate limiting on specific endpoints
    
    This can be used for endpoints that need stricter rate limiting
    than the global middleware.
    
    Args:
        request_count: Number of requests allowed
        window_minutes: Time window in minutes
    """
    # Rate limiting functionality - can be implemented with Redis or in-memory store
    # Integration point for rate limiting middleware
    pass


# Error responses for OpenAPI documentation
auth_responses = {
    401: {
        "description": "Authentication required",
        "content": {
            "application/json": {
                "example": {"detail": "Authentication required"}
            }
        }
    },
    403: {
        "description": "Insufficient permissions",
        "content": {
            "application/json": {
                "example": {"detail": "Insufficient permissions"}
            }
        }
    }
}