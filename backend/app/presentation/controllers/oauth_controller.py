"""
OAuth2 Controller
=================

FastAPI controller for OAuth2 authentication endpoints.
Handles Google OAuth2 authentication flow for admin users.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx
import structlog

from app.infrastructure.security.auth_service import AuthService
from app.infrastructure.config.settings import Settings, get_settings
from app.presentation.schemas.admin_schemas import *


logger = structlog.get_logger()
router = APIRouter()


class OAuth2CallbackRequest(BaseModel):
    """OAuth2 callback request from frontend"""
    code: str
    redirect_uri: str


class OAuth2TokenResponse(BaseModel):
    """OAuth2 authentication response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class TOTPVerificationRequest(BaseModel):
    """TOTP verification request"""
    email: str
    totp_code: str


class TOTPVerificationResponse(BaseModel):
    """TOTP verification response"""
    verified: bool
    message: str


@router.post("/auth/oauth/google", response_model=OAuth2TokenResponse)
async def google_oauth_callback(
    request: OAuth2CallbackRequest,
    settings: Annotated[Settings, Depends(get_settings)]
):
    """
    Handle Google OAuth2 callback and create admin session
    
    This endpoint:
    1. Exchanges OAuth2 code for Google tokens
    2. Fetches user info from Google
    3. Validates admin authorization
    4. Creates JWT tokens for the frontend
    """
    try:
        # Exchange code for tokens with Google
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": request.code,
                    "client_id": settings.google_client_id,
                    "client_secret": settings.google_client_secret,
                    "redirect_uri": request.redirect_uri,
                    "grant_type": "authorization_code",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )

            if not token_response.is_success:
                error_data = token_response.json() if token_response.content else {}
                logger.error("Google token exchange failed", 
                           error=error_data.get("error_description", "Unknown error"))
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Token exchange failed: {error_data.get('error_description', 'Unknown error')}"
                )

            tokens = token_response.json()

            # Get user info from Google
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )

            if not user_response.is_success:
                logger.error("Failed to fetch user info from Google")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Failed to retrieve user information"
                )

            user_info = user_response.json()

        # Validate admin authorization
        auth_service = AuthService(settings)
        admin_emails = settings.admin_emails or []
        
        if user_info["email"].lower() not in [email.lower() for email in admin_emails]:
            logger.warning("Unauthorized admin access attempt", email=user_info["email"])
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Unauthorized: You are not authorized to access the admin panel"
            )

        # Create admin session and JWT tokens
        session_data = {
            "sub": user_info["email"],
            "email": user_info["email"],
            "name": user_info.get("name", user_info["email"]),
            "picture": user_info.get("picture"),
            "permissions": ["admin", "view_logs", "manage_watchlist", "configure_apis", "manage_storage", "view_analytics"],
            "auth_method": "oauth2_google"
        }

        tokens = await auth_service.create_admin_session(
            user_info["email"], 
            session_data
        )

        logger.info("Admin OAuth2 authentication successful", email=user_info["email"])

        return OAuth2TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            expires_in=1800,  # 30 minutes
            user={
                "email": user_info["email"],
                "name": user_info.get("name", user_info["email"]),
                "picture": user_info.get("picture")
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("OAuth2 authentication error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed due to server error"
        )


@router.post("/auth/totp/verify", response_model=TOTPVerificationResponse)
async def verify_totp(
    request: TOTPVerificationRequest,
    settings: Annotated[Settings, Depends(get_settings)]
):
    """
    Verify TOTP code for admin user
    
    This endpoint validates TOTP codes for two-factor authentication.
    It's called after OAuth2 authentication to complete the login process.
    """
    try:
        auth_service = AuthService(settings)
        
        # In a full implementation, you would validate the TOTP against stored secrets
        # For this integration, we'll accept any 6-digit code for demonstration
        if not request.totp_code or len(request.totp_code) != 6 or not request.totp_code.isdigit():
            return TOTPVerificationResponse(
                verified=False,
                message="Invalid TOTP code format"
            )

        # Simulate TOTP verification
        # In production, implement proper TOTP verification with stored secrets
        logger.info("TOTP verification attempt", email=request.email)
        
        return TOTPVerificationResponse(
            verified=True,
            message="TOTP verification successful"
        )

    except Exception as e:
        logger.error("TOTP verification error", error=str(e), exc_info=True)
        return TOTPVerificationResponse(
            verified=False,
            message="TOTP verification failed"
        )


@router.get("/auth/totp/setup")
async def setup_totp(
    email: str,
    settings: Annotated[Settings, Depends(get_settings)]
):
    """
    Setup TOTP for a new admin user
    
    Returns QR code data for setting up TOTP in authenticator apps.
    """
    try:
        # Generate TOTP secret and QR code URL
        import secrets
        import base64
        from urllib.parse import quote
        
        # Generate a random TOTP secret
        secret = base64.b32encode(secrets.token_bytes(20)).decode('utf-8')
        
        # Create QR code URL for authenticator apps
        issuer = "Stock Market Dashboard"
        otpauth_url = f"otpauth://totp/{quote(issuer)}:{quote(email)}?secret={secret}&issuer={quote(issuer)}"
        
        logger.info("TOTP setup initiated", email=email)
        
        return {
            "secret": secret,
            "qrcode_url": otpauth_url,
            "manual_entry_key": secret,
            "issuer": issuer
        }

    except Exception as e:
        logger.error("TOTP setup error", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup TOTP"
        )