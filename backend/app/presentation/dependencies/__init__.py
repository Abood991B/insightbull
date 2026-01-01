"""
Presentation Layer Dependencies

This module contains FastAPI dependencies for:
- Authentication and authorization
- Request validation
- Database connections
- Security enforcement

Following the 5-layer architecture pattern.
"""

from .auth_dependencies import (
    get_current_admin_user,
    require_admin_permission,
    require_admin,
    auth_responses
)

__all__ = [
    "get_current_admin_user",
    "require_admin_permission",
    "require_admin",
    "auth_responses"
]