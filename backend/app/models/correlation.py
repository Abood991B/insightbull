"""
Correlation data model for sentiment-price correlation analysis
"""
from sqlalchemy import Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import BaseModel


class CorrelationData(BaseModel):
    """Correlation analysis results between sentiment and price"""
    __tablename__ = "correlation_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_symbol = Column(String(10), ForeignKey("stocks.symbol"), nullable=False, index=True)
    time_window = Column(String(10), nullable=False)  # '1d', '7d', '14d'
    correlation_coefficient = Column(Float, nullable=False)
    p_value = Column(Float)
    sample_size = Column(Integer)
    calculated_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    stock = relationship("Stock", back_populates="correlation_data")
    
    def __repr__(self):
        return f"<CorrelationData {self.stock_symbol} - {self.time_window}: {self.correlation_coefficient:.3f}>"
