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

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.infrastructure.config.settings import Settings, get_settings
from app.infrastructure.security.auth_service import AuthService, AdminUser

# Use centralized logging system
from app.infrastructure.log_system import get_logger
logger = get_logger()

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


# Convenience dependencies for common permission levels
require_admin = require_admin_permission("admin")


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