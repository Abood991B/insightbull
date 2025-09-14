"""
API configuration model for managing external API settings
"""
from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import BaseModel


class ApiConfig(BaseModel):
    """Configuration for external API integrations"""
    __tablename__ = "api_configs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False, unique=True)
    endpoint = Column(String(500))
    api_key_encrypted = Column(Text)  # Encrypted API key
    enabled = Column(Boolean, default=True)
    rate_limit = Column(Integer)  # Requests per time period
    last_checked = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    def __repr__(self):
        return f"<ApiConfig {self.name} - {'Enabled' if self.enabled else 'Disabled'}>"
