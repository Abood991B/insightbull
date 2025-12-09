"""
Data Collection Infrastructure
=============================

External data collectors implementing the Strategy pattern.
Supports multiple data sources: Hacker News, FinHub, NewsAPI, GDELT, YFinance.
"""

from .base_collector import BaseCollector
from .hackernews_collector import HackerNewsCollector
from .finnhub_collector import FinHubCollector
from .newsapi_collector import NewsAPICollector
from .gdelt_collector import GDELTCollector
from .yfinance_collector import YFinanceCollector

__all__ = [
    "BaseCollector",
    "HackerNewsCollector", 
    "FinHubCollector",
    "NewsAPICollector",
    "GDELTCollector",
    "YFinanceCollector"
]