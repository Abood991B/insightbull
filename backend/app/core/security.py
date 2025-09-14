"""
Security utilities for authentication and authorization
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
import httpx
import logging

from config import settings

logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Dict[str, Any]:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        raise ValueError("Invalid token")


async def verify_google_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify Google OAuth2 token"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            
            # Verify the token is for our app
            if data.get("aud") != settings.GOOGLE_CLIENT_ID:
                logger.warning("Invalid Google token audience")
                return None
            
            return {
                "email": data.get("email"),
                "name": data.get("name"),
                "sub": data.get("sub"),
                "picture": data.get("picture")
            }
            
    except Exception as e:
        logger.error(f"Error verifying Google token: {e}")
        return None


def encrypt_api_key(api_key: str) -> str:
    """Encrypt an API key for storage"""
    # In production, use proper encryption like Fernet
    from cryptography.fernet import Fernet
    import base64
    
    # Generate or load encryption key
    # This should be stored securely, not in code
    key = settings.SECRET_KEY[:32].encode().ljust(32, b'0')
    key = base64.urlsafe_b64encode(key)
    fernet = Fernet(key)
    
    return fernet.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str) -> str:
    """Decrypt an API key"""
    from cryptography.fernet import Fernet
    import base64
    
    key = settings.SECRET_KEY[:32].encode().ljust(32, b'0')
    key = base64.urlsafe_b64encode(key)
    fernet = Fernet(key)
    
    return fernet.decrypt(encrypted_key.encode()).decode()
