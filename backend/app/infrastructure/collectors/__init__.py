"""
Data Collection Infrastructure
=============================

External data collectors implementing the Strategy pattern.
Supports multiple data sources: Hacker News, FinHub, NewsAPI, MarketAux, GDELT.
"""

from .base_collector import BaseCollector
from .hackernews_collector import HackerNewsCollector
from .finnhub_collector import FinHubCollector
from .newsapi_collector import NewsAPICollector
from .marketaux_collector import MarketauxCollector
from .gdelt_collector import GDELTCollector

__all__ = [
    "BaseCollector",
    "HackerNewsCollector", 
    "FinHubCollector",
    "NewsAPICollector",
    "MarketauxCollector",
    "GDELTCollector"
]