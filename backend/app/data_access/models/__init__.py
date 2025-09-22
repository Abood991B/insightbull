"""
Database Models
===============

SQLAlchemy models for data persistence.
Maps business entities to database tables.
"""

from sqlalchemy import Column, Integer, String, DateTime, Float, Text, Boolean, ForeignKey, JSON, Index, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import hashlib

from app.data_access.database.base import Base


class StocksWatchlist(Base):
    """Unified Stocks and Watchlist entity model."""
    __tablename__ = "stocks_watchlist"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    symbol = Column(String(10), nullable=False, unique=True, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(100))
    
    # Watchlist management fields
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    added_to_watchlist = Column(DateTime(timezone=True), server_default=func.now())
    priority = Column(Integer, default=0, nullable=False)  # For ordering/prioritization
    
    # Stock metadata
    market_cap = Column(String(50))  # Large Cap, Mid Cap, Small Cap
    exchange = Column(String(20), default="NASDAQ")  # NASDAQ, NYSE, etc.
    current_price = Column(Numeric(precision=10, scale=2), nullable=True)  # Latest stock price for quick access
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    sentiment_data = relationship("SentimentData", back_populates="stock")
    price_data = relationship("StockPrice", back_populates="stock")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_stocks_watchlist_active', 'is_active'),
        Index('idx_stocks_watchlist_symbol_active', 'symbol', 'is_active'),
        Index('idx_stocks_watchlist_priority', 'priority'),
    )


class SentimentData(Base):
    """Sentiment analysis results model."""
    __tablename__ = "sentiment_data"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks_watchlist.id"), nullable=False)
    source = Column(String(50), nullable=False)  # reddit, news, financial_reports
    sentiment_score = Column(Numeric(precision=5, scale=4), nullable=False)  # Range -1.0000 to 1.0000
    confidence = Column(Numeric(precision=5, scale=4), nullable=False)  # Range 0.0000 to 1.0000
    sentiment_label = Column(String(20), nullable=False, index=True, default="Neutral")  # Positive, Negative, Neutral
    model_used = Column(String(50), nullable=True)  # VADER, FinBERT (nullable for migration compatibility)
    raw_text = Column(Text)
    extra_data = Column(JSON)  # Additional source-specific data
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    stock = relationship("StocksWatchlist", back_populates="sentiment_data")
    
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
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks_watchlist.id"), nullable=False)
    symbol = Column(String(20), nullable=True, index=True)  # Stock symbol for easier querying (nullable due to SQLite limitations)
    name = Column(String(200))  # Company name for better readability
    price = Column(Numeric(precision=10, scale=2), nullable=False)  # Max 99999999.99
    volume = Column(Integer)
    change = Column(Numeric(precision=8, scale=2))  # Max 999999.99 (positive or negative)
    change_percent = Column(Numeric(precision=6, scale=2))  # Max 9999.99% 
    timestamp = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Additional price fields for better tracking (2 decimal places)
    open_price = Column(Numeric(precision=10, scale=2))
    close_price = Column(Numeric(precision=10, scale=2)) 
    high_price = Column(Numeric(precision=10, scale=2))
    low_price = Column(Numeric(precision=10, scale=2))
    
    # Relationships
    stock = relationship("StocksWatchlist", back_populates="price_data")


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
    sentiment_score = Column(Numeric(precision=5, scale=4))  # Range -1.0000 to 1.0000
    confidence = Column(Numeric(precision=5, scale=4))  # Range 0.0000 to 1.0000
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
    sentiment_score = Column(Numeric(precision=5, scale=4))  # Range -1.0000 to 1.0000
    confidence = Column(Numeric(precision=5, scale=4))  # Range 0.0000 to 1.0000
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
    "StocksWatchlist", 
    "SentimentData", 
    "StockPrice", 
    "NewsArticle", 
    "RedditPost", 
    "SystemLog"
]

# Keep Stock as alias for backward compatibility during transition
Stock = StocksWatchlist