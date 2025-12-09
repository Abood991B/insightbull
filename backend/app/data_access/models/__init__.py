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
    source = Column(String(50), nullable=False)  # hackernews, news, financial_reports
    sentiment_score = Column(Numeric(precision=5, scale=4), nullable=False)  # Range -1.0000 to 1.0000
    confidence = Column(Numeric(precision=5, scale=4), nullable=False)  # Range 0.0000 to 1.0000
    sentiment_label = Column(String(20), nullable=False, index=True, default="Neutral")  # Positive, Negative, Neutral
    model_used = Column(String(50), nullable=True)  # FinBERT (ProsusAI/finbert) - nullable for migration compatibility
    raw_text = Column(Text)
    stock_mentions = Column(JSON)  # Array of stock symbols mentioned in the content (e.g., ["AAPL", "MSFT"])
    additional_metadata = Column(JSON)  # Additional metadata: source_url, content_type, original_timestamp, label
    content_hash = Column(String(64), nullable=True, index=True)  # SHA-256 hash for duplicate detection
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # When sentiment analysis was performed
    
    # Relationships
    stock = relationship("StocksWatchlist", back_populates="sentiment_data")
    
    # Composite index for duplicate detection (stock + source + content_hash)
    __table_args__ = (
        Index('idx_sentiment_duplicate_check', 'stock_id', 'source', 'content_hash'),
        Index('idx_sentiment_created_at', 'created_at'),
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
    price_timestamp = Column(DateTime(timezone=True), nullable=False)  # When the price data is from (market time)
    
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
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks_watchlist.id"), nullable=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    url = Column(String(1000), unique=True)
    source = Column(String(100), nullable=False)
    author = Column(String(255))
    published_at = Column(DateTime(timezone=True), nullable=False)  # When article was published by source
    sentiment_score = Column(Numeric(precision=5, scale=4))  # Range -1.0000 to 1.0000
    confidence = Column(Numeric(precision=5, scale=4))  # Range 0.0000 to 1.0000
    stock_mentions = Column(JSON)  # Array of stock symbols mentioned
    # Relationship back to stock for joins
    stock = relationship("StocksWatchlist")


class HackerNewsPost(Base):
    """Hacker News posts and comments model."""
    __tablename__ = "hackernews_posts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks_watchlist.id"), nullable=True)
    hn_id = Column(String(50), unique=True, nullable=False)
    title = Column(String(500), nullable=True)  # Nullable for comments
    content = Column(Text)
    content_type = Column(String(20), nullable=False, default="story")  # story or comment
    author = Column(String(100))
    points = Column(Integer, default=0)
    num_comments = Column(Integer, default=0)
    url = Column(String(1000))
    created_utc = Column(DateTime(timezone=True), nullable=False)  # When item was created on HN
    sentiment_score = Column(Numeric(precision=5, scale=4))  # Range -1.0000 to 1.0000
    confidence = Column(Numeric(precision=5, scale=4))  # Range 0.0000 to 1.0000
    stock_mentions = Column(JSON)  # Array of stock symbols mentioned
    # Relationship back to stock for joins
    stock = relationship("StocksWatchlist")


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
    "HackerNewsPost", 
    "SystemLog"
]

# Keep Stock as alias for backward compatibility during transition
Stock = StocksWatchlist