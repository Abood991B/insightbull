"""
System log model for tracking application events
"""
from sqlalchemy import Column, String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from .base import BaseModel


class SystemLog(BaseModel):
    """System activity and error logging"""
    __tablename__ = "system_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False)  # 'info', 'warning', 'error'
    source = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    metadata = Column(JSONB)  # Additional context data
    
    def __repr__(self):
        return f"<SystemLog [{self.level.upper()}] {self.source}: {self.message[:50]}>"
