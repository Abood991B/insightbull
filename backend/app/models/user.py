"""
User model for authentication and authorization
"""
from sqlalchemy import Column, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel


class User(BaseModel):
    """User entity for admin access"""
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255))
    role = Column(String(50), default="user")  # 'admin', 'user'
    oauth_provider = Column(String(50))  # 'google', etc.
    oauth_id = Column(String(255))
    last_login = Column(DateTime(timezone=True))
    
    def __repr__(self):
        return f"<User {self.email} - {self.role}>"
    
    @property
    def is_admin(self):
        return self.role == "admin"
