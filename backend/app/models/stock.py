"""
Stock model for watchlist management
"""
from sqlalchemy import Column, String, Boolean, Numeric, DateTime, func
from sqlalchemy.orm import relationship
from .base import BaseModel


class Stock(BaseModel):
    """Stock entity for tracking watchlist"""
    __tablename__ = "stocks"
    
    symbol = Column(String(10), primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    market_cap = Column(Numeric(precision=15, scale=2))
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    sentiment_data = relationship("SentimentData", back_populates="stock", cascade="all, delete-orphan")
    price_data = relationship("PriceData", back_populates="stock", cascade="all, delete-orphan")
    correlation_data = relationship("CorrelationData", back_populates="stock", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Stock {self.symbol}: {self.name}>""
