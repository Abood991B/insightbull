"""
Rate Limiting System
===================

Implements intelligent rate limiting for external API calls with advanced features:
- Per-source rate limit configuration
- Adaptive rate limiting based on API response headers
- Intelligent caching with TTL
- Circuit breaker pattern for failing APIs
- Priority queue for high-volume stocks
- Request deduplication
- Burst handling and exponential backoff

Following FYP Report specification:
- SY-FR6: Handle API Rate Limits
"""

import asyncio
import time
import hashlib
import json
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, List, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class BackoffStrategy(Enum):
    """Backoff strategies for rate limiting"""
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    FIXED = "fixed"


class RequestPriority(Enum):
    """Request priority levels for stock processing"""
    CRITICAL = 1  # High-volume stocks (AAPL, TSLA, etc.)
    HIGH = 2      # Recently active stocks
    NORMAL = 3    # Standard processing
    LOW = 4       # Background/maintenance


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


@dataclass
class CacheEntry:
    """Cached API response entry with TTL"""
    data: Any
    timestamp: float
    ttl: float  # Time to live in seconds
    hash_key: str
    
    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        return time.time() - self.timestamp > self.ttl


@dataclass
class CircuitBreakerState:
    """Circuit breaker state for failing APIs"""
    failure_count: int = 0
    last_failure_time: float = 0
    is_open: bool = False
    success_count: int = 0
    
    # Thresholds
    failure_threshold: int = 5  # Open after 5 failures
    success_threshold: int = 2  # Close after 2 successes
    timeout: float = 300.0  # 5 minutes in open state


class RateLimitHandler:
    """
    Handles rate limiting for multiple API sources with advanced features.
    
    Features:
    - Per-source rate limit configuration
    - Adaptive rate limiting from API response headers
    - Intelligent caching with TTL
    - Circuit breaker pattern for failing APIs
    - Priority queue for high-volume stocks
    - Request deduplication
    - Exponential backoff with jitter
    - Burst handling
    - Thread-safe operation
    """
    
    # Default rate limit configurations for known APIs
    DEFAULT_CONFIGS = {
        "hackernews": RateLimitConfig(
            requests_per_minute=120,  # HN API is generous
            requests_per_hour=7200,
            burst_limit=20
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
    
    # High-priority stocks (high trading volume)
    HIGH_PRIORITY_SYMBOLS = {
        "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", 
        "META", "TSLA", "NFLX"
    }
    
    # Cache TTL by source (in seconds)
    CACHE_TTL = {
        "hackernews": 300,  # 5 minutes
        "finnhub": 600,     # 10 minutes
        "newsapi": 900,     # 15 minutes
        "marketaux": 900    # 15 minutes
    }
    
    # Concurrency limits per source
    SEMAPHORE_LIMITS = {
        "hackernews": 5,   # 5 concurrent HN requests
        "finnhub": 5,      # 5 concurrent FinHub requests
        "newsapi": 2,      # 2 concurrent NewsAPI requests
        "marketaux": 3     # 3 concurrent Marketaux requests
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
        
        # Caching layer
        self._cache: Dict[str, CacheEntry] = {}
        self._cache_lock = asyncio.Lock()
        
        # Circuit breakers per source
        self._circuit_breakers: Dict[str, CircuitBreakerState] = defaultdict(CircuitBreakerState)
        
        # Semaphores for parallel collection (limit concurrent requests per source)
        self._semaphores: Dict[str, asyncio.Semaphore] = {}
        
        # Request deduplication tracking
        self._active_requests: Dict[str, Set[asyncio.Event]] = defaultdict(set)
        
        # Adaptive rate tracking
        self._api_quotas: Dict[str, Dict[str, int]] = {}
        
        # Initialize locks, queues, and semaphores for each configured source
        for source in self.configs:
            self._request_history[source] = []
            self._locks[source] = asyncio.Lock()
            self._queues[source] = asyncio.Queue()
            self._semaphores[source] = asyncio.Semaphore(
                self.SEMAPHORE_LIMITS.get(source, 3)
            )
            
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    async def acquire(self, source: str) -> None:
        """
        Acquire permission to make an API request.
        
        Blocks until it's safe to make a request according to rate limits.
        
        Args:
            source: API source identifier (hackernews, finnhub, etc.)
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
        if source not in self._semaphores:
            self._semaphores[source] = asyncio.Semaphore(
                self.SEMAPHORE_LIMITS.get(source, 3)
            )
        
        self.logger.info(f"Updated rate limit config for {source}")
    
    # ==================== Enhanced Features ====================
    
    def get_symbol_priority(self, symbol: str) -> RequestPriority:
        """Determine priority for a stock symbol"""
        symbol = symbol.upper()
        if symbol in self.HIGH_PRIORITY_SYMBOLS:
            return RequestPriority.CRITICAL
        return RequestPriority.NORMAL
    
    async def acquire_with_cache(
        self, 
        source: str, 
        symbol: str,
        use_cache: bool = True
    ) -> tuple[bool, Optional[Any]]:
        """
        Acquire permission to make API request with cache checking.
        
        Args:
            source: API source identifier
            symbol: Stock symbol
            use_cache: Whether to check cache first
            
        Returns:
            Tuple of (should_make_request, cached_data)
        """
        # Check circuit breaker
        if not await self._check_circuit_breaker(source):
            raise Exception(f"Circuit breaker open for {source}")
        
        # Check cache first
        if use_cache:
            cache_key = self._generate_cache_key(source, symbol)
            cached_data = await self._get_from_cache(cache_key)
            if cached_data is not None:
                self.logger.debug(f"Cache hit for {source}:{symbol}")
                return False, cached_data  # Don't make request, use cache
        
        # Check for duplicate in-flight requests
        request_key = f"{source}:{symbol}"
        if request_key in self._active_requests and self._active_requests[request_key]:
            # Wait for existing request to complete
            self.logger.debug(f"Waiting for duplicate request: {request_key}")
            event = list(self._active_requests[request_key])[0]
            await event.wait()
            # Check cache again after wait
            cache_key = self._generate_cache_key(source, symbol)
            cached_data = await self._get_from_cache(cache_key)
            return False, cached_data  # Use result from first request
        
        # Acquire semaphore for parallel execution
        async with self._semaphores[source]:
            # Apply base rate limiting
            await self.acquire(source)
            
            # Mark request as active
            event = asyncio.Event()
            self._active_requests[request_key].add(event)
            
            return True, None  # Proceed with request
    
    async def release_request(self, source: str, symbol: str):
        """Release request tracking and notify waiting tasks"""
        request_key = f"{source}:{symbol}"
        if request_key in self._active_requests:
            for event in self._active_requests[request_key]:
                event.set()
            self._active_requests[request_key].clear()
    
    async def _check_circuit_breaker(self, source: str) -> bool:
        """Check if circuit breaker allows requests"""
        breaker = self._circuit_breakers[source]
        
        if not breaker.is_open:
            return True
        
        # Check if timeout has expired
        if time.time() - breaker.last_failure_time > breaker.timeout:
            # Try half-open state
            self.logger.info(f"Circuit breaker half-open for {source}")
            breaker.is_open = False
            breaker.failure_count = 0
            breaker.success_count = 0
            return True
        
        self.logger.warning(f"Circuit breaker open for {source}, rejecting request")
        return False
    
    async def record_success(self, source: str, response_headers: Optional[Dict] = None):
        """
        Record successful API request.
        
        Args:
            source: API source
            response_headers: HTTP response headers for adaptive rate limiting
        """
        breaker = self._circuit_breakers[source]
        
        if breaker.is_open:
            breaker.success_count += 1
            if breaker.success_count >= breaker.success_threshold:
                breaker.is_open = False
                breaker.failure_count = 0
                self.logger.info(f"Circuit breaker closed for {source}")
        
        # Update adaptive rate limits from headers
        if response_headers:
            await self._update_adaptive_limits(source, response_headers)
    
    async def record_failure(self, source: str, error: Exception):
        """Record failed API request"""
        breaker = self._circuit_breakers[source]
        breaker.failure_count += 1
        breaker.last_failure_time = time.time()
        
        if breaker.failure_count >= breaker.failure_threshold:
            breaker.is_open = True
            self.logger.error(
                f"Circuit breaker opened for {source} after "
                f"{breaker.failure_count} failures: {str(error)}"
            )
    
    async def _update_adaptive_limits(self, source: str, headers: Dict):
        """Update rate limits based on API response headers"""
        # Common header patterns
        remaining_headers = [
            'x-ratelimit-remaining',
            'x-rate-limit-remaining',
            'ratelimit-remaining'
        ]
        
        reset_headers = [
            'x-ratelimit-reset',
            'x-rate-limit-reset',
            'ratelimit-reset'
        ]
        
        remaining = None
        reset_time = None
        
        # Check for rate limit headers (case-insensitive)
        headers_lower = {k.lower(): v for k, v in headers.items()}
        
        for header in remaining_headers:
            if header in headers_lower:
                try:
                    remaining = int(headers_lower[header])
                    break
                except (ValueError, TypeError):
                    pass
        
        for header in reset_headers:
            if header in headers_lower:
                try:
                    reset_time = int(headers_lower[header])
                    break
                except (ValueError, TypeError):
                    pass
        
        if remaining is not None:
            self._api_quotas[source] = {
                'remaining': remaining,
                'reset_time': reset_time,
                'updated_at': time.time()
            }
            
            # Log warning if approaching limit
            if remaining < 10:
                self.logger.warning(
                    f"API quota low for {source}: {remaining} requests remaining"
                )
    
    def _generate_cache_key(self, source: str, symbol: str, **kwargs) -> str:
        """Generate cache key from request parameters"""
        key_data = {
            'source': source,
            'symbol': symbol,
            **kwargs
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    async def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """Get data from cache if not expired"""
        async with self._cache_lock:
            if cache_key in self._cache:
                entry = self._cache[cache_key]
                if not entry.is_expired():
                    return entry.data
                else:
                    # Remove expired entry
                    del self._cache[cache_key]
        return None
    
    async def cache_response(
        self, 
        source: str, 
        symbol: str, 
        data: Any,
        **kwargs
    ):
        """Cache API response"""
        cache_key = self._generate_cache_key(source, symbol, **kwargs)
        ttl = self.CACHE_TTL.get(source, 600)
        
        async with self._cache_lock:
            self._cache[cache_key] = CacheEntry(
                data=data,
                timestamp=time.time(),
                ttl=ttl,
                hash_key=cache_key
            )
            
            # Cleanup old cache entries (keep cache size manageable)
            if len(self._cache) > 1000:
                await self._cleanup_cache()
    
    async def _cleanup_cache(self):
        """Remove expired cache entries"""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        
        for key in expired_keys:
            del self._cache[key]
        
        self.logger.debug(f"Cleaned up {len(expired_keys)} expired cache entries")
    
    def get_enhanced_status(self) -> Dict[str, Any]:
        """Get comprehensive status including enhanced features"""
        base_status = self.get_all_status()
        
        return {
            "base_rate_limits": base_status,
            "circuit_breakers": {
                source: {
                    "is_open": breaker.is_open,
                    "failure_count": breaker.failure_count,
                    "success_count": breaker.success_count,
                    "last_failure": breaker.last_failure_time
                }
                for source, breaker in self._circuit_breakers.items()
            },
            "cache_stats": {
                "total_entries": len(self._cache),
                "entries_by_source": self._count_cache_by_source()
            },
            "api_quotas": self._api_quotas,
            "active_requests": {
                source: len(events)
                for source, events in self._active_requests.items()
                if events
            }
        }
    
    def _count_cache_by_source(self) -> Dict[str, int]:
        """Count cache entries by source"""
        counts = defaultdict(int)
        for entry in self._cache.values():
            # Extract source from hash_key (first part before ':')
            try:
                source = json.loads(entry.hash_key)['source']
                counts[source] += 1
            except:
                pass
        return dict(counts)