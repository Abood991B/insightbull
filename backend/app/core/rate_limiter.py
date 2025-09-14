"""
API Rate Limiting Service
Implements rate limiting as required by SY-FR6 functional requirement
"""
import time
import asyncio
from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
import logging
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Rate limiter implementing token bucket algorithm
    Addresses SY-FR6: Handle API Rate Limits from FYP Report
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client
        self.local_buckets: Dict[str, Dict] = {}  # Fallback for when Redis is not available
        self.default_limits = {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_size": 10
        }
    
    async def is_allowed(
        self, 
        identifier: str, 
        endpoint: str = "default",
        custom_limits: Optional[Dict[str, int]] = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is allowed based on rate limits
        
        Args:
            identifier: Unique identifier (IP, user ID, API key)
            endpoint: API endpoint being accessed
            custom_limits: Custom rate limits for specific endpoints
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        limits = custom_limits or self.default_limits
        key = f"rate_limit:{identifier}:{endpoint}"
        
        try:
            if self.redis_client:
                return await self._redis_rate_limit(key, limits)
            else:
                return await self._local_rate_limit(key, limits)
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            # Fail open - allow request if rate limiter fails
            return True, {"remaining": limits["requests_per_minute"], "reset_time": time.time() + 60}
    
    async def _redis_rate_limit(self, key: str, limits: Dict[str, int]) -> Tuple[bool, Dict[str, any]]:
        """Redis-based rate limiting using sliding window"""
        current_time = int(time.time())
        window_size = 60  # 1 minute window
        
        # Use Redis pipeline for atomic operations
        pipe = self.redis_client.pipeline()
        
        # Remove expired entries
        pipe.zremrangebyscore(key, 0, current_time - window_size)
        
        # Count current requests in window
        pipe.zcard(key)
        
        # Add current request
        pipe.zadd(key, {str(current_time): current_time})
        
        # Set expiry
        pipe.expire(key, window_size)
        
        results = await pipe.execute()
        current_count = results[1] + 1  # +1 for current request
        
        is_allowed = current_count <= limits["requests_per_minute"]
        
        rate_info = {
            "remaining": max(0, limits["requests_per_minute"] - current_count),
            "reset_time": current_time + window_size,
            "limit": limits["requests_per_minute"]
        }
        
        if not is_allowed:
            # Remove the request we just added since it's not allowed
            await self.redis_client.zrem(key, str(current_time))
        
        return is_allowed, rate_info
    
    async def _local_rate_limit(self, key: str, limits: Dict[str, int]) -> Tuple[bool, Dict[str, any]]:
        """Local memory-based rate limiting (fallback)"""
        current_time = time.time()
        
        if key not in self.local_buckets:
            self.local_buckets[key] = {
                "requests": [],
                "created": current_time
            }
        
        bucket = self.local_buckets[key]
        
        # Clean old requests (older than 1 minute)
        bucket["requests"] = [
            req_time for req_time in bucket["requests"] 
            if current_time - req_time < 60
        ]
        
        current_count = len(bucket["requests"])
        is_allowed = current_count < limits["requests_per_minute"]
        
        if is_allowed:
            bucket["requests"].append(current_time)
        
        rate_info = {
            "remaining": max(0, limits["requests_per_minute"] - current_count - (1 if is_allowed else 0)),
            "reset_time": current_time + 60,
            "limit": limits["requests_per_minute"]
        }
        
        return is_allowed, rate_info
    
    async def get_rate_limit_status(self, identifier: str, endpoint: str = "default") -> Dict[str, any]:
        """Get current rate limit status without consuming a request"""
        key = f"rate_limit:{identifier}:{endpoint}"
        current_time = int(time.time())
        
        if self.redis_client:
            try:
                count = await self.redis_client.zcount(key, current_time - 60, current_time)
                return {
                    "remaining": max(0, self.default_limits["requests_per_minute"] - count),
                    "reset_time": current_time + 60,
                    "limit": self.default_limits["requests_per_minute"]
                }
            except Exception:
                pass
        
        # Fallback to local
        if key in self.local_buckets:
            bucket = self.local_buckets[key]
            valid_requests = [
                req_time for req_time in bucket["requests"] 
                if current_time - req_time < 60
            ]
            return {
                "remaining": max(0, self.default_limits["requests_per_minute"] - len(valid_requests)),
                "reset_time": current_time + 60,
                "limit": self.default_limits["requests_per_minute"]
            }
        
        return {
            "remaining": self.default_limits["requests_per_minute"],
            "reset_time": current_time + 60,
            "limit": self.default_limits["requests_per_minute"]
        }


class RateLimitMiddleware:
    """
    FastAPI middleware for rate limiting
    Implements automatic rate limiting on all endpoints
    """
    
    def __init__(self, rate_limiter: RateLimiter):
        self.rate_limiter = rate_limiter
        self.endpoint_limits = {
            "/api/sentiment": {"requests_per_minute": 30},
            "/api/correlation": {"requests_per_minute": 20},
            "/api/admin": {"requests_per_minute": 10},
            "/api/stocks": {"requests_per_minute": 100}
        }
    
    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""
        # Get client identifier (IP address or user ID)
        client_ip = request.client.host
        user_id = getattr(request.state, 'user_id', None)
        identifier = user_id or client_ip
        
        # Get endpoint for specific limits
        endpoint = self._get_endpoint_category(request.url.path)
        custom_limits = self.endpoint_limits.get(endpoint)
        
        # Check rate limit
        is_allowed, rate_info = await self.rate_limiter.is_allowed(
            identifier, endpoint, custom_limits
        )
        
        if not is_allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {rate_info['limit']} per minute",
                    "retry_after": int(rate_info['reset_time'] - time.time())
                },
                headers={
                    "X-RateLimit-Limit": str(rate_info['limit']),
                    "X-RateLimit-Remaining": str(rate_info['remaining']),
                    "X-RateLimit-Reset": str(int(rate_info['reset_time'])),
                    "Retry-After": str(int(rate_info['reset_time'] - time.time()))
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        response.headers["X-RateLimit-Limit"] = str(rate_info['limit'])
        response.headers["X-RateLimit-Remaining"] = str(rate_info['remaining'])
        response.headers["X-RateLimit-Reset"] = str(int(rate_info['reset_time']))
        
        return response
    
    def _get_endpoint_category(self, path: str) -> str:
        """Categorize endpoint for rate limiting"""
        for endpoint_pattern in self.endpoint_limits.keys():
            if path.startswith(endpoint_pattern):
                return endpoint_pattern
        return "default"


async def create_rate_limiter() -> RateLimiter:
    """Factory function to create rate limiter with Redis connection"""
    try:
        from app.core.database import get_redis_client
        redis_client = await get_redis_client()
        return RateLimiter(redis_client)
    except Exception as e:
        logger.warning(f"Could not connect to Redis for rate limiting: {e}")
        return RateLimiter()  # Use local fallback


# External API rate limiting (for data collection services)
class ExternalAPIRateLimiter:
    """
    Rate limiter for external API calls
    Implements retry logic with exponential backoff
    """
    
    def __init__(self):
        self.api_limits = {
            "reddit": {"requests_per_minute": 60, "burst": 10},
            "finnhub": {"requests_per_minute": 60, "burst": 5},
            "marketaux": {"requests_per_minute": 100, "burst": 10},
            "newsapi": {"requests_per_minute": 1000, "burst": 50},  # Higher limit
            "yahoo_finance": {"requests_per_minute": 2000, "burst": 100}  # No official limit
        }
        self.backoff_times = {}
    
    async def wait_if_needed(self, api_name: str) -> None:
        """Wait if API is currently rate limited"""
        if api_name in self.backoff_times:
            wait_until = self.backoff_times[api_name]
            current_time = time.time()
            
            if current_time < wait_until:
                wait_seconds = wait_until - current_time
                logger.info(f"Rate limited for {api_name}, waiting {wait_seconds:.1f} seconds")
                await asyncio.sleep(wait_seconds)
                
                # Remove backoff after waiting
                del self.backoff_times[api_name]
    
    def handle_rate_limit_response(self, api_name: str, response_headers: Dict[str, str]) -> None:
        """Handle rate limit response and set backoff time"""
        # Check for rate limit headers
        retry_after = response_headers.get('retry-after') or response_headers.get('Retry-After')
        
        if retry_after:
            try:
                backoff_seconds = int(retry_after)
            except ValueError:
                # If it's a date string, parse it
                try:
                    from datetime import datetime
                    retry_time = datetime.strptime(retry_after, '%a, %d %b %Y %H:%M:%S %Z')
                    backoff_seconds = (retry_time - datetime.utcnow()).total_seconds()
                except ValueError:
                    backoff_seconds = 60  # Default fallback
        else:
            # Use exponential backoff
            current_backoff = self.backoff_times.get(f"{api_name}_count", 1)
            backoff_seconds = min(current_backoff * 2, 300)  # Max 5 minutes
            self.backoff_times[f"{api_name}_count"] = backoff_seconds
        
        self.backoff_times[api_name] = time.time() + backoff_seconds
        logger.warning(f"API {api_name} rate limited, backing off for {backoff_seconds} seconds")
    
    def reset_backoff(self, api_name: str) -> None:
        """Reset backoff time after successful request"""
        if api_name in self.backoff_times:
            del self.backoff_times[api_name]
        if f"{api_name}_count" in self.backoff_times:
            del self.backoff_times[f"{api_name}_count"]


# Global instances
rate_limiter = None
external_rate_limiter = ExternalAPIRateLimiter()

async def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance"""
    global rate_limiter
    if rate_limiter is None:
        rate_limiter = await create_rate_limiter()
    return rate_limiter