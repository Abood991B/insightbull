"""
Base Data Collector Interface
============================

Abstract base class implementing the Strategy pattern for data collection.
Provides standardized interface for all external data sources.

Following FYP Report specification:
- SY-FR1: Data Collection Pipeline
- SY-FR6: Handle API Rate Limits
"""

from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from app.utils.timezone import utc_now

logger = logging.getLogger(__name__)


class DataSource(Enum):
    """Supported data sources"""
    HACKERNEWS = "hackernews"
    FINNHUB = "finnhub"
    NEWSAPI = "newsapi"
    GDELT = "gdelt"
    YFINANCE = "yfinance"


@dataclass
class DateRange:
    """Date range for data collection"""
    start_date: datetime
    end_date: datetime
    
    def __post_init__(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
    
    @classmethod
    def last_days(cls, days: int) -> 'DateRange':
        """Create date range for last N days"""
        from datetime import timezone
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        return cls(start_date=start_date, end_date=end_date)
    
    @classmethod
    def near_realtime(cls) -> 'DateRange':
        """
        Create date range optimized for near real-time data collection.
        Uses 5 days to balance recency with API limitations (especially NewsAPI free tier).
        """
        return cls.last_days(5)


@dataclass
class RawData:
    """Raw data structure from external sources"""
    source: DataSource
    content_type: str  # post, comment, article, headline
    text: str
    timestamp: datetime
    stock_symbol: Optional[str] = None
    url: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if not self.text or not self.text.strip():
            raise ValueError("Text content cannot be empty")
        if not isinstance(self.timestamp, datetime):
            raise ValueError("Timestamp must be a datetime object")


@dataclass
class CollectionConfig:
    """Configuration for data collection"""
    symbols: List[str]
    date_range: DateRange
    max_items_per_symbol: int = 100
    include_comments: bool = True
    language: str = "en"
    min_score: Optional[int] = None  # HackerNews points, news engagement
    
    def __post_init__(self):
        if not self.symbols:
            raise ValueError("At least one stock symbol must be provided")
        if self.max_items_per_symbol <= 0:
            raise ValueError("max_items_per_symbol must be positive")


@dataclass
class CollectionResult:
    """Result of data collection operation"""
    source: DataSource
    success: bool
    data: List[RawData]
    error_message: Optional[str] = None
    items_collected: int = 0
    execution_time: float = 0.0
    
    def __post_init__(self):
        self.items_collected = len(self.data)


class BaseCollector(ABC):
    """
    Abstract base class for all data collectors.
    
    Implements the Strategy pattern allowing interchangeable
    data collection implementations for different sources.
    """
    
    def __init__(self, api_key: Optional[str] = None, rate_limiter=None):
        """
        Initialize collector with API credentials and rate limiter.
        
        Args:
            api_key: API key for external service (if required)
            rate_limiter: Rate limiting handler for API throttling
        """
        self.api_key = api_key
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
    @property
    @abstractmethod
    def source(self) -> DataSource:
        """Return the data source this collector handles"""
        pass
        
    @property
    @abstractmethod
    def requires_api_key(self) -> bool:
        """Return whether this collector requires an API key"""
        pass
    
    @abstractmethod
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect data from external source.
        
        Args:
            config: Collection configuration with symbols and date range
            
        Returns:
            CollectionResult with success status and collected data
            
        Raises:
            CollectionError: When data collection fails
        """
        pass
    
    @abstractmethod
    async def validate_connection(self) -> bool:
        """
        Validate connection to external service.
        
        Returns:
            True if connection is valid, False otherwise
        """
        pass
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the collector.
        
        Returns:
            Dictionary with health status and diagnostics
        """
        try:
            start_time = utc_now()
            is_healthy = await self.validate_connection()
            response_time = (utc_now() - start_time).total_seconds()
            
            return {
                "source": self.source.value,
                "healthy": is_healthy,
                "response_time": response_time,
                "api_key_configured": self.api_key is not None,
                "rate_limiter_configured": self.rate_limiter is not None,
                "timestamp": start_time.isoformat()
            }
        except Exception as e:
            self.logger.error(f"Health check failed for {self.source.value}: {str(e)}")
            return {
                "source": self.source.value,
                "healthy": False,
                "error": str(e),
                "timestamp": utc_now().isoformat()
            }
    
    def _validate_config(self, config: CollectionConfig) -> None:
        """Validate collection configuration"""
        if not isinstance(config, CollectionConfig):
            raise TypeError("Config must be a CollectionConfig instance")
        
        if self.requires_api_key and not self.api_key:
            raise ValueError(f"{self.source.value} collector requires an API key")
    
    async def _apply_rate_limit(self) -> None:
        """Apply rate limiting if configured"""
        if self.rate_limiter:
            await self.rate_limiter.acquire(self.source.value)
    
    def _create_raw_data(
        self,
        content_type: str,
        text: str,
        timestamp: datetime,
        stock_symbol: Optional[str] = None,
        url: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> RawData:
        """Helper method to create RawData objects"""
        return RawData(
            source=self.source,
            content_type=content_type,
            text=text,
            timestamp=timestamp,
            stock_symbol=stock_symbol,
            url=url,
            metadata=metadata or {}
        )


class CollectionError(Exception):
    """Exception raised during data collection"""
    
    def __init__(self, message: str, source: DataSource, original_error: Optional[Exception] = None):
        self.message = message
        self.source = source
        self.original_error = original_error
        super().__init__(f"{source.value}: {message}")