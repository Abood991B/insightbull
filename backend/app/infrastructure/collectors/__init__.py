"""
Data Collection Infrastructure
=============================

External data collectors implementing the Strategy pattern.
Supports multiple data sources: Reddit, FinHub, NewsAPI, MarketAux.
"""

from .base_collector import BaseCollector
from .reddit_collector import RedditCollector
from .finnhub_collector import FinHubCollector
from .newsapi_collector import NewsAPICollector
from .marketaux_collector import MarketauxCollector

__all__ = [
    "BaseCollector",
    "RedditCollector", 
    "FinHubCollector",
    "NewsAPICollector",
    "MarketauxCollector"
]