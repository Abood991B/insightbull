"""
Collector Settings and Optimization Configuration
==================================================

Centralized configuration for all data source collectors.
Defines optimal fetching strategies, rate limits, and quality settings.

Based on actual API documentation:
- HackerNews: Unlimited (Algolia), be courteous
- GDELT: Unlimited (free), 250 articles/request max
- Finnhub: 60 calls/minute (free tier)
- NewsAPI: 100 requests/day (free tier)
- Marketaux: 100 requests/day (free tier)
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from enum import Enum


class CollectionMode(Enum):
    """Collection execution mode"""
    SEQUENTIAL = "sequential"   # One at a time
    PARALLEL = "parallel"       # Multiple concurrent
    BATCH = "batch"             # Single request for multiple symbols


@dataclass
class SourceSettings:
    """Configuration settings for a data source"""
    # Basic info
    name: str
    display_name: str
    requires_api_key: bool
    
    # Rate limiting
    requests_per_minute: int
    requests_per_hour: int
    daily_quota: Optional[int]  # None = unlimited
    
    # Collection strategy
    collection_mode: CollectionMode
    max_concurrent_requests: int
    batch_size: int                    # Symbols per batch
    delay_between_requests: float      # Seconds
    delay_between_symbols: float       # Seconds (for sequential)
    
    # Fetching limits
    max_items_per_symbol: int          # Optimal items per symbol
    max_items_per_request: int         # API limit per request
    
    # Quality settings
    min_relevance_score: float         # 0.0-1.0
    prefer_recent: bool                # Prioritize recent content
    include_comments: bool             # For social sources
    
    # Cache settings
    cache_ttl_seconds: int
    
    # Retry settings
    max_retries: int
    initial_retry_delay: float
    max_retry_delay: float
    
    # Sentiment routing
    sentiment_model: str               # "finbert" (FinBERT-Tone for all sources)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "name": self.name,
            "display_name": self.display_name,
            "requires_api_key": self.requires_api_key,
            "requests_per_minute": self.requests_per_minute,
            "requests_per_hour": self.requests_per_hour,
            "daily_quota": self.daily_quota,
            "collection_mode": self.collection_mode.value,
            "max_concurrent_requests": self.max_concurrent_requests,
            "batch_size": self.batch_size,
            "delay_between_requests": self.delay_between_requests,
            "delay_between_symbols": self.delay_between_symbols,
            "max_items_per_symbol": self.max_items_per_symbol,
            "max_items_per_request": self.max_items_per_request,
            "min_relevance_score": self.min_relevance_score,
            "prefer_recent": self.prefer_recent,
            "include_comments": self.include_comments,
            "cache_ttl_seconds": self.cache_ttl_seconds,
            "max_retries": self.max_retries,
            "initial_retry_delay": self.initial_retry_delay,
            "max_retry_delay": self.max_retry_delay,
            "sentiment_model": self.sentiment_model
        }


# =============================================================================
# DATA SOURCE CONFIGURATIONS
# =============================================================================

COLLECTOR_SETTINGS: Dict[str, SourceSettings] = {
    
    # -------------------------------------------------------------------------
    # HACKER NEWS (Algolia API)
    # -------------------------------------------------------------------------
    # API: https://hn.algolia.com/api
    # Limits: No official limits, extremely generous
    # Best for: Tech community sentiment, developer-focused stocks
    # -------------------------------------------------------------------------
    "hackernews": SourceSettings(
        name="hackernews",
        display_name="Hacker News",
        requires_api_key=False,
        
        # Rate limiting - very generous
        requests_per_minute=120,
        requests_per_hour=7200,
        daily_quota=None,  # Unlimited
        
        # Collection strategy - parallel is fine
        collection_mode=CollectionMode.PARALLEL,
        max_concurrent_requests=5,
        batch_size=10,
        delay_between_requests=0.1,
        delay_between_symbols=0.1,
        
        # Fetching - stories + comments
        max_items_per_symbol=25,
        max_items_per_request=100,
        
        # Quality
        min_relevance_score=0.3,
        prefer_recent=True,
        include_comments=True,
        
        # Cache - shorter TTL for near-realtime
        cache_ttl_seconds=180,
        
        # Retries
        max_retries=3,
        initial_retry_delay=0.5,
        max_retry_delay=30.0,
        
        # Sentiment - FinBERT-Tone for all content (95.7% avg confidence)
        sentiment_model="finbert"
    ),
    
    # -------------------------------------------------------------------------
    # GDELT (DOC 2.0 API)
    # -------------------------------------------------------------------------
    # API: https://api.gdeltproject.org/api/v2/doc/doc
    # Limits: No official limits, free and open
    # Best for: Global news coverage, high volume
    # Note: Returns up to 250 articles per request
    # -------------------------------------------------------------------------
    "gdelt": SourceSettings(
        name="gdelt",
        display_name="GDELT",
        requires_api_key=False,
        
        # Rate limiting - be courteous
        requests_per_minute=60,
        requests_per_hour=3600,
        daily_quota=None,  # Unlimited
        
        # Collection strategy - sequential to be courteous
        collection_mode=CollectionMode.SEQUENTIAL,
        max_concurrent_requests=3,
        batch_size=1,
        delay_between_requests=0.5,
        delay_between_symbols=0.5,
        
        # Fetching - high volume available
        max_items_per_symbol=30,
        max_items_per_request=250,  # GDELT limit
        
        # Quality - filter for financial relevance
        min_relevance_score=0.4,
        prefer_recent=True,
        include_comments=False,  # No comments
        
        # Cache - updates every 15 min
        cache_ttl_seconds=300,
        
        # Retries
        max_retries=3,
        initial_retry_delay=1.0,
        max_retry_delay=60.0,
        
        # Sentiment - FinBERT for news
        sentiment_model="finbert"
    ),
    
    # -------------------------------------------------------------------------
    # FINNHUB
    # -------------------------------------------------------------------------
    # API: https://finnhub.io/docs/api
    # Limits: 60 API calls/minute (free tier)
    # Best for: High-quality financial news, company-specific
    # -------------------------------------------------------------------------
    "finnhub": SourceSettings(
        name="finnhub",
        display_name="Finnhub",
        requires_api_key=True,
        
        # Rate limiting - 60/min limit, use 50%
        requests_per_minute=30,
        requests_per_hour=1500,
        daily_quota=None,  # Per-minute limited
        
        # Collection strategy - parallel with caution
        collection_mode=CollectionMode.PARALLEL,
        max_concurrent_requests=3,
        batch_size=5,
        delay_between_requests=1.0,
        delay_between_symbols=0.2,
        
        # Fetching - quality over quantity
        max_items_per_symbol=20,
        max_items_per_request=50,
        
        # Quality - high quality financial sources
        min_relevance_score=0.5,
        prefer_recent=True,
        include_comments=False,
        
        # Cache - conserve quota
        cache_ttl_seconds=600,
        
        # Retries
        max_retries=3,
        initial_retry_delay=1.0,
        max_retry_delay=120.0,
        
        # Sentiment - FinBERT for financial news
        sentiment_model="finbert"
    ),
    
    # -------------------------------------------------------------------------
    # NEWSAPI
    # -------------------------------------------------------------------------
    # API: https://newsapi.org/docs
    # Limits: 100 requests/day (free tier)
    # Best for: General business news
    # CRITICAL: Very limited quota - must be conservative
    # -------------------------------------------------------------------------
    "newsapi": SourceSettings(
        name="newsapi",
        display_name="NewsAPI",
        requires_api_key=True,
        
        # Rate limiting - 100/day = ~4/hour
        requests_per_minute=2,
        requests_per_hour=50,
        daily_quota=100,  # Hard daily limit
        
        # Collection strategy - strictly sequential
        collection_mode=CollectionMode.SEQUENTIAL,
        max_concurrent_requests=1,
        batch_size=1,
        delay_between_requests=5.0,  # 12/min max
        delay_between_symbols=5.0,
        
        # Fetching - minimal to conserve quota
        max_items_per_symbol=10,
        max_items_per_request=100,
        
        # Quality - maximize value per request
        min_relevance_score=0.6,
        prefer_recent=True,
        include_comments=False,
        
        # Cache - long TTL to avoid re-fetching
        cache_ttl_seconds=1800,  # 30 minutes
        
        # Retries - fewer to conserve quota
        max_retries=2,
        initial_retry_delay=2.0,
        max_retry_delay=300.0,
        
        # Sentiment - FinBERT for news
        sentiment_model="finbert"
    ),
    
    # -------------------------------------------------------------------------
    # MARKETAUX
    # -------------------------------------------------------------------------
    # API: https://www.marketaux.com/documentation
    # Limits: 100 requests/day (free tier)
    # Best for: Financial news with entity recognition
    # Supports batch requests (up to 10 symbols per request)
    # -------------------------------------------------------------------------
    "marketaux": SourceSettings(
        name="marketaux",
        display_name="Marketaux",
        requires_api_key=True,
        
        # Rate limiting - 100/day
        requests_per_minute=5,
        requests_per_hour=50,
        daily_quota=100,
        
        # Collection strategy - BATCH mode (10 symbols per request)
        collection_mode=CollectionMode.BATCH,
        max_concurrent_requests=2,
        batch_size=10,  # Marketaux supports 10 symbols per request
        delay_between_requests=3.0,
        delay_between_symbols=0,  # Batched together
        
        # Fetching
        max_items_per_symbol=15,
        max_items_per_request=100,
        
        # Quality
        min_relevance_score=0.5,
        prefer_recent=True,
        include_comments=False,
        
        # Cache - long TTL
        cache_ttl_seconds=1800,  # 30 minutes
        
        # Retries - fewer to conserve quota
        max_retries=2,
        initial_retry_delay=2.0,
        max_retry_delay=300.0,
        
        # Sentiment - FinBERT for financial news
        sentiment_model="finbert"
    )
}


def get_collector_settings(source: str) -> Optional[SourceSettings]:
    """Get settings for a specific collector"""
    return COLLECTOR_SETTINGS.get(source.lower())


def get_all_collector_settings() -> Dict[str, SourceSettings]:
    """Get all collector settings"""
    return COLLECTOR_SETTINGS.copy()


def get_optimal_pipeline_config(num_symbols: int) -> Dict[str, Any]:
    """
    Get optimal pipeline configuration based on number of symbols.
    
    Adjusts settings to balance data quality with API quota conservation.
    
    Args:
        num_symbols: Number of symbols in the watchlist
        
    Returns:
        Optimized configuration dict
    """
    config = {
        "max_items_per_symbol": {},
        "collection_priority": [],
        "estimated_requests": {},
        "estimated_time_minutes": 0
    }
    
    # Calculate optimal items per symbol based on watchlist size
    # Larger watchlists = fewer items per symbol to conserve quota
    if num_symbols <= 5:
        scale_factor = 1.0
    elif num_symbols <= 10:
        scale_factor = 0.8
    elif num_symbols <= 15:
        scale_factor = 0.6
    else:
        scale_factor = 0.4
    
    total_requests = 0
    total_time = 0
    
    for name, settings in COLLECTOR_SETTINGS.items():
        # Scale items per symbol
        scaled_items = max(5, int(settings.max_items_per_symbol * scale_factor))
        config["max_items_per_symbol"][name] = scaled_items
        
        # Calculate estimated requests
        if settings.collection_mode == CollectionMode.BATCH:
            requests = (num_symbols + settings.batch_size - 1) // settings.batch_size
        else:
            requests = num_symbols
        
        config["estimated_requests"][name] = requests
        total_requests += requests
        
        # Calculate estimated time
        source_time = requests * settings.delay_between_requests
        if settings.collection_mode == CollectionMode.SEQUENTIAL:
            source_time += num_symbols * settings.delay_between_symbols
        total_time += source_time
    
    # Priority order based on API limits and value
    # Free APIs first, then by quality
    config["collection_priority"] = [
        "hackernews",   # Free, fast, tech-focused
        "gdelt",        # Free, global coverage
        "finnhub",      # Paid but generous
        "marketaux",    # Limited but batched
        "newsapi"       # Most limited, last
    ]
    
    config["estimated_time_minutes"] = round(total_time / 60, 1)
    config["total_estimated_requests"] = total_requests
    
    return config


def calculate_daily_quota_usage(
    num_symbols: int, 
    runs_per_day: int = 4
) -> Dict[str, Any]:
    """
    Calculate expected daily API quota usage.
    
    Args:
        num_symbols: Number of symbols in watchlist
        runs_per_day: Expected pipeline runs per day
        
    Returns:
        Quota usage analysis
    """
    usage = {}
    
    for name, settings in COLLECTOR_SETTINGS.items():
        if settings.daily_quota is None:
            usage[name] = {
                "daily_limit": "Unlimited",
                "requests_per_run": num_symbols if settings.collection_mode != CollectionMode.BATCH else (num_symbols + settings.batch_size - 1) // settings.batch_size,
                "daily_usage": "N/A",
                "status": "OK"
            }
        else:
            requests_per_run = (
                (num_symbols + settings.batch_size - 1) // settings.batch_size
                if settings.collection_mode == CollectionMode.BATCH
                else num_symbols
            )
            daily_usage = requests_per_run * runs_per_day
            remaining = settings.daily_quota - daily_usage
            
            status = "OK" if remaining > 20 else ("WARNING" if remaining > 0 else "EXCEEDED")
            
            usage[name] = {
                "daily_limit": settings.daily_quota,
                "requests_per_run": requests_per_run,
                "daily_usage": daily_usage,
                "remaining": remaining,
                "status": status
            }
    
    return usage
