"""
Infrastructure Layer
====================

External integrations, third-party APIs, sentiment analysis models, and configuration.
Provides concrete implementations of interfaces defined in other layers.

Components:
- Collectors: Data collection from external APIs (HackerNews, FinHub, etc.)
- Security: API key management and security utilities  
- Rate Limiter: API throttling and backoff strategies
- Log System: Centralized logging (Singleton pattern)
- Configuration: Settings and environment management
"""

from .log_system import LogSystem, get_logger
from .rate_limiter import RateLimitHandler
from .security.security_utils import SecurityUtils

__all__ = [
    "LogSystem",
    "get_logger", 
    "RateLimitHandler",
    "SecurityUtils"
]