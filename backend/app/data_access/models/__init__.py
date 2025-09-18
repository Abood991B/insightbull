"""
Database Models
===============

SQLAlchemy models for data persistence.
Maps business entities to database tables.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import hashlib

from app.data_access.database.base import Base


class Stock(Base):
    """Stock entity model."""
    __tablename__ = "stocks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sentiment_data = relationship("SentimentData", back_populates="stock")
    price_data = relationship("StockPrice", back_populates="stock")


class SentimentData(Base):
    """Sentiment analysis results model."""
    __tablename__ = "sentiment_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    source = Column(String(50), nullable=False)  # reddit, news, financial_reports
    sentiment_score = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_used = Column(String(50), nullable=True)  # VADER, FinBERT (nullable for migration compatibility)
    raw_text = Column(Text)
    extra_data = Column(JSON)  # Additional source-specific data
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="sentiment_data")
    
    # Composite index for duplicate detection (stock + source + content_hash)
    __table_args__ = (
        Index('idx_sentiment_duplicate_check', 'stock_id', 'source', 'content_hash'),
    )
    
    @staticmethod
    def generate_content_hash(text: str, source: str, stock_symbol: str) -> str:
        """Generate a hash for duplicate detection based on content, source, and stock."""
        content = f"{stock_symbol}:{source}:{text.strip().lower()}"
        return hashlib.sha256(content.encode('utf-8')).hexdigest()


class StockPrice(Base):
    """Stock price data model."""
    __tablename__ = "stock_prices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id"), nullable=False)
    price = Column(Float, nullable=False)
    volume = Column(Integer)
    change = Column(Float)
    change_percent = Column(Float)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("Stock", back_populates="price_data")


class NewsArticle(Base):
    """News articles model."""
    __tablename__ = "news_articles"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(1000), unique=True)
    source = Column(String(100), nullable=False)
    author = Column(String(255))
    published_at = Column(DateTime(timezone=True), nullable=False)
    sentiment_score = Column(Float)
    confidence = Column(Float)
    stock_mentions = Column(JSON)  # Array of stock symbols mentioned
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RedditPost(Base):
    """Reddit posts model."""
    __tablename__ = "reddit_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    reddit_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    subreddit = Column(String(100), nullable=False)
    author = Column(String(100))
    score = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    url = Column(String(1000))
    created_utc = Column(DateTime(timezone=True), nullable=False)
    sentiment_score = Column(Float)
    confidence = Column(Float)
    stock_mentions = Column(JSON)  # Array of stock symbols mentioned
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class SystemLog(Base):
    """System logs model."""
    __tablename__ = "system_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    level = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    logger = Column(String(100), nullable=False)  # Logger name/component
    component = Column(String(100))  # Component/module
    function = Column(String(100))  # Function name
    line_number = Column(Integer)  # Line number
    extra_data = Column(JSON)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())


# Export all models for easy import
__all__ = [
    "Stock", 
    "SentimentData", 
    "StockPrice", 
    "NewsArticle", 
    "RedditPost", 
    "SystemLog"
]