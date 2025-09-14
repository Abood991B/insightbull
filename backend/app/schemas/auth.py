"""
Authentication schemas for API validation
"""
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from datetime import datetime


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Optional[dict] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    role: Optional[str] = None


class GoogleAuthRequest(BaseModel):
    token: str


class UserBase(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    role: Literal["admin", "user"] = "user"


class UserCreate(UserBase):
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None


class UserResponse(UserBase):
    id: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True
