"""
JWT Token Handler for Admin Authentication

This module handles JWT token creation, validation, and management
for admin authentication. Integrates with the existing frontend
TOTP authentication system.

Following FYP security requirements:
- Secure token validation
- Session management
- Token refresh handling
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import os
import base64
from app.utils.timezone import utc_now

from app.infrastructure.config.settings import Settings


class JWTHandler:
    """Handles JWT token operations for admin authentication"""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        self.refresh_token_expire_days = 7
        
    def create_access_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT access token for admin sessions
        
        Args:
            data: Token payload data
            
        Returns:
            Encoded JWT token string
        """
        to_encode = data.copy()
        expire = utc_now() + timedelta(minutes=self.access_token_expire_minutes)
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode, 
            self.settings.jwt_secret_key, 
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """
        Create JWT refresh token for session renewal
        
        Args:
            data: Token payload data
            
        Returns:
            Encoded JWT refresh token string
        """
        to_encode = data.copy()
        expire = utc_now() + timedelta(days=self.refresh_token_expire_days)
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.jwt_secret_key,
            algorithm=self.algorithm
        )
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Verify and decode JWT token
        
        Args:
            token: JWT token string
            
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.algorithm]
            )
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None
    
    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired
        
        Args:
            token: JWT token string
            
        Returns:
            True if expired, False otherwise
        """
        try:
            payload = jwt.decode(
                token,
                self.settings.jwt_secret_key,
                algorithms=[self.algorithm],
                options={"verify_exp": False}
            )
            exp = payload.get("exp")
            if exp:
                return utc_now() > datetime.fromtimestamp(exp)
            return True
        except jwt.JWTError:
            return True
    
    def get_token_subject(self, token: str) -> Optional[str]:
        """
        Extract subject (user ID) from token
        
        Args:
            token: JWT token string
            
        Returns:
            Token subject or None if invalid
        """
        payload = self.verify_token(token)
        if payload:
            return payload.get("sub")
        return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """
        Create new access token from valid refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            New access token or None if refresh token is invalid
        """
        payload = self.verify_token(refresh_token)
        if payload and payload.get("type") == "refresh":
            # Create new access token with same subject
            new_data = {"sub": payload.get("sub")}
            return self.create_access_token(new_data)
        return None