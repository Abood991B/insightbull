"""
Sentiment data model for storing sentiment analysis results
"""
from sqlalchemy import Column, String, Float, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from .base import BaseModel


class SentimentData(BaseModel):
    """Sentiment analysis results for stock-related content"""
    __tablename__ = "sentiment_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_symbol = Column(String(10), ForeignKey("stocks.symbol"), nullable=False, index=True)
    source = Column(String(50), nullable=False)  # 'reddit', 'finnhub', 'marketaux', 'newsapi'
    content = Column(Text)
    sentiment = Column(String(20), nullable=False)  # 'positive', 'negative', 'neutral'
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float)
    model_used = Column(String(50))  # 'finbert', 'vader'
    source_url = Column(Text)
    published_at = Column(DateTime(timezone=True), index=True)
    
    # Relationships
    stock = relationship("Stock", back_populates="sentiment_data")
    
    def __repr__(self):
        return f"<SentimentData {self.stock_symbol} - {self.sentiment} ({self.sentiment_score:.2f})>"
