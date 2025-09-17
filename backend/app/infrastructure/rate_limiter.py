"""
Rate Limiting System
===================

Implements intelligent rate limiting for external API calls.
Handles different rate limits per API source with exponential backoff.

Following FYP Report specification:
- SY-FR6: Handle API Rate Limits
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Backoff strategies for rate limiting"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    requests_per_minute: int
    requests_per_hour: int = field(default=0)
    burst_limit: int = field(default=0)  # Max requests in burst
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    initial_delay: float = 1.0  # Initial delay in seconds
    max_delay: float = 300.0  # Maximum delay in seconds
    max_retries: int = 3
    
    def __post_init__(self):
        if self.requests_per_minute <= 0:
            raise ValueError("requests_per_minute must be positive")
        if self.requests_per_hour == 0:
            self.requests_per_hour = self.requests_per_minute * 60
        if self.burst_limit == 0:
            self.burst_limit = max(1, self.requests_per_minute // 2)


@dataclass 
class RequestRecord:
    """Record of API request timing"""
    timestamp: float
    success: bool
    delay_applied: float = 0.0


class RateLimitHandler:
    """
    Handles rate limiting for multiple API sources.
    
    Features:
    - Per-source rate limit configuration
    - Exponential backoff with jitter
    - Request queue management
    - Burst handling
    - Thread-safe operation
    """
    
    # Default rate limit configurations for known APIs
    DEFAULT_CONFIGS = {
        "reddit": RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=3600,
            burst_limit=10
        ),
        "finnhub": RateLimitConfig(
            requests_per_minute=60,
            requests_per_hour=3000,
            burst_limit=5
        ),
        "newsapi": RateLimitConfig(
            requests_per_minute=5,  # Free tier limit
            requests_per_hour=100,
            burst_limit=2
        ),
        "marketaux": RateLimitConfig(
            requests_per_minute=10,
            requests_per_hour=100,
            burst_limit=3
        )
    }
    
    def __init__(self, custom_configs: Optional[Dict[str, RateLimitConfig]] = None):
        """
        Initialize rate limiter with configurations.
        
        Args:
            custom_configs: Custom rate limit configurations per source
        """
        self.configs = self.DEFAULT_CONFIGS.copy()
        if custom_configs:
            self.configs.update(custom_configs)
        
        # Request tracking per source
        self._request_history: Dict[str, list[RequestRecord]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        self._queues: Dict[str, asyncio.Queue] = {}
        
        # Initialize locks and queues for each configured source
        for source in self.configs:
            self._request_history[source] = []
            self._locks[source] = asyncio.Lock()
            self._queues[source] = asyncio.Queue()
            
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    async def acquire(self, source: str) -> None:
        """
        Acquire permission to make an API request.
        
        Blocks until it's safe to make a request according to rate limits.
        
        Args:
            source: API source identifier (reddit, finnhub, etc.)
        """
        if source not in self.configs:
            self.logger.warning(f"No rate limit config for source: {source}")
            return
        
        async with self._locks[source]:
            await self._wait_for_rate_limit(source)
            
        # Record the request
        self._record_request(source, success=True)
    
    async def _wait_for_rate_limit(self, source: str) -> None:
        """Wait until it's safe to make a request"""
        config = self.configs[source]
        current_time = time.time()
        
        # Clean old requests from history
        self._cleanup_old_requests(source, current_time)
        
        # Check if we need to wait
        delay = self._calculate_delay(source, current_time)
        
        if delay > 0:
            self.logger.info(f"Rate limit delay for {source}: {delay:.2f}s")
            await asyncio.sleep(delay)
    
    def _cleanup_old_requests(self, source: str, current_time: float) -> None:
        """Remove requests older than the rate limit window"""
        config = self.configs[source]
        cutoff_time = current_time - 3600  # 1 hour window
        
        self._request_history[source] = [
            record for record in self._request_history[source]
            if record.timestamp > cutoff_time
        ]
    
    def _calculate_delay(self, source: str, current_time: float) -> float:
        """Calculate required delay before next request"""
        config = self.configs[source]
        history = self._request_history[source]
        
        if not history:
            return 0.0
        
        # Check minute-based rate limit
        minute_ago = current_time - 60
        recent_requests = [r for r in history if r.timestamp > minute_ago]
        
        if len(recent_requests) >= config.requests_per_minute:
            # Need to wait until oldest request in minute window expires
            oldest_in_minute = min(recent_requests, key=lambda r: r.timestamp)
            delay = 60 - (current_time - oldest_in_minute.timestamp)
            return max(0, delay)
        
        # Check hourly rate limit
        hour_ago = current_time - 3600
        hourly_requests = [r for r in history if r.timestamp > hour_ago]
        
        if len(hourly_requests) >= config.requests_per_hour:
            # Need to wait until oldest request in hour window expires
            oldest_in_hour = min(hourly_requests, key=lambda r: r.timestamp)
            delay = 3600 - (current_time - oldest_in_hour.timestamp)
            return max(0, delay)
        
        # Check burst limit (rapid consecutive requests)
        if len(recent_requests) > 0:
            last_request = max(recent_requests, key=lambda r: r.timestamp)
            time_since_last = current_time - last_request.timestamp
            
            # If too many recent requests, apply minimum delay
            if len(recent_requests) >= config.burst_limit and time_since_last < 1.0:
                return 1.0 - time_since_last
        
        return 0.0
    
    def _record_request(self, source: str, success: bool, delay: float = 0.0) -> None:
        """Record a request in the history"""
        if source not in self._request_history:
            self._request_history[source] = []
        
        record = RequestRecord(
            timestamp=time.time(),
            success=success,
            delay_applied=delay
        )
        
        self._request_history[source].append(record)
    
    async def handle_error(self, source: str, error: Exception, attempt: int = 1) -> float:
        """
        Handle API error with appropriate backoff strategy.
        
        Args:
            source: API source that failed
            error: Exception that occurred
            attempt: Current attempt number (1-indexed)
            
        Returns:
            Delay in seconds before retry (0 means don't retry)
        """
        config = self.configs.get(source)
        if not config or attempt > config.max_retries:
            return 0.0
        
        # Record failed request
        self._record_request(source, success=False)
        
        # Calculate backoff delay
        delay = self._calculate_backoff_delay(config, attempt)
        
        self.logger.warning(
            f"API error for {source} (attempt {attempt}): {str(error)}. "
            f"Retrying in {delay:.2f}s"
        )
        
        return delay
    
    def _calculate_backoff_delay(self, config: RateLimitConfig, attempt: int) -> float:
        """Calculate backoff delay based on strategy"""
        base_delay = config.initial_delay
        
        if config.backoff_strategy == BackoffStrategy.FIXED:
            delay = base_delay
        elif config.backoff_strategy == BackoffStrategy.LINEAR:
            delay = base_delay * attempt
        else:  # EXPONENTIAL
            delay = base_delay * (2 ** (attempt - 1))
        
        # Add jitter to prevent thundering herd
        import random
        jitter = random.uniform(0.1, 0.3) * delay
        delay += jitter
        
        return min(delay, config.max_delay)
    
    def get_status(self, source: str) -> Dict[str, Any]:
        """
        Get current rate limit status for a source.
        
        Args:
            source: API source identifier
            
        Returns:
            Dictionary with current status information
        """
        if source not in self.configs:
            return {"error": f"Unknown source: {source}"}
        
        config = self.configs[source]
        history = self._request_history.get(source, [])
        current_time = time.time()
        
        # Count recent requests
        minute_ago = current_time - 60
        hour_ago = current_time - 3600
        
        recent_minute = len([r for r in history if r.timestamp > minute_ago])
        recent_hour = len([r for r in history if r.timestamp > hour_ago])
        
        return {
            "source": source,
            "requests_last_minute": recent_minute,
            "requests_last_hour": recent_hour,
            "minute_limit": config.requests_per_minute,
            "hour_limit": config.requests_per_hour,
            "minute_remaining": max(0, config.requests_per_minute - recent_minute),
            "hour_remaining": max(0, config.requests_per_hour - recent_hour),
            "estimated_delay": self._calculate_delay(source, current_time),
            "total_requests": len(history)
        }
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status for all configured sources"""
        return {source: self.get_status(source) for source in self.configs}
    
    def update_config(self, source: str, config: RateLimitConfig) -> None:
        """Update rate limit configuration for a source"""
        self.configs[source] = config
        
        if source not in self._request_history:
            self._request_history[source] = []
        if source not in self._locks:
            self._locks[source] = asyncio.Lock()
        if source not in self._queues:
            self._queues[source] = asyncio.Queue()
        
        self.logger.info(f"Updated rate limit config for {source}")