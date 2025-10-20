"""
NewsAPI Data Collector
=====================

Collects financial news using NewsAPI service.
Focuses on business and financial news sources.

Following FYP Report specification:
- Multi-source news aggregation
- Business and financial focus
- High-quality news sources
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import asyncio
import logging

try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False
    NewsApiClient = None

import httpx

from .base_collector import (
    BaseCollector, 
    DataSource, 
    RawData, 
    CollectionConfig, 
    CollectionResult,
    CollectionError
)

logger = logging.getLogger(__name__)


class NewsAPICollector(BaseCollector):
    """
    NewsAPI collector for financial and business news.
    
    Features:
    - Business news aggregation
    - Financial keyword filtering
    - Multiple source coverage
    - Quality news sources
    """
    
    # Financial keywords for news filtering
    FINANCIAL_KEYWORDS = [
        "stock", "stocks", "shares", "market", "trading", "investment",
        "earnings", "revenue", "profit", "finance", "financial", "economy",
        "economic", "NYSE", "NASDAQ", "SEC", "IPO", "merger", "acquisition"
    ]
    
    # Available financial news sources (verified to work with free NewsAPI)
    FINANCIAL_SOURCES = [
        "bloomberg",
        "business-insider", 
        "fortune",
        "the-wall-street-journal"
    ]
    
    def __init__(self, api_key: str, rate_limiter=None):
        """
        Initialize NewsAPI collector.
        
        Args:
            api_key: NewsAPI key
            rate_limiter: Rate limiting handler
        """
        super().__init__(api_key=api_key, rate_limiter=rate_limiter)
        
        if not NEWSAPI_AVAILABLE:
            self.logger.warning("newsapi library not available. Using HTTP client fallback.")
            self._client = None
        else:
            self._client = NewsApiClient(api_key=api_key)
        

        self.base_url = "https://newsapi.org/v2"
    
    @property
    def source(self) -> DataSource:
        return DataSource.NEWSAPI
    
    @property 
    def requires_api_key(self) -> bool:
        return True
    
    def _get_http_client(self) -> httpx.AsyncClient:
        """Get a fresh HTTP client for each request"""
        return httpx.AsyncClient(timeout=30.0)
    
    async def validate_connection(self) -> bool:
        """Validate NewsAPI connection"""
        try:
            # Test API with a simple sources request
            url = f"{self.base_url}/sources"
            params = {
                "category": "business",
                "apiKey": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                return response.status_code == 200
                
        except Exception as e:
            self.logger.error(f"NewsAPI connection validation failed: {str(e)}")
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect financial news from NewsAPI.
        
        Args:
            config: Collection configuration
            
        Returns:
            CollectionResult with collected news data
        """
        start_time = datetime.utcnow()
        collected_data = []
        
        try:
            self._validate_config(config)
            await self._apply_rate_limit()
            
            # Collect news for each symbol only - ensures equal distribution
            for symbol in config.symbols:
                symbol_data = await self._collect_symbol_news(symbol, config)
                collected_data.extend(symbol_data)
                
                # Apply rate limiting between symbols
                if self.rate_limiter:
                    await asyncio.sleep(0.3)  # NewsAPI has stricter limits
            
            # Skip general news collection to focus on target stocks only
            # This ensures equal distribution across all target symbols
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CollectionResult(
                source=self.source,
                success=True,
                data=collected_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"NewsAPI collection failed: {str(e)}"
            self.logger.error(error_msg)
            
            return CollectionResult(
                source=self.source,
                success=False,
                data=[],
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def _collect_symbol_news(self, symbol: str, config: CollectionConfig) -> List[RawData]:
        """Collect news for specific stock symbol"""
        collected_data = []
        
        try:
            # Simple direct search for the target symbol only
            query = f'{symbol}'
            
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                # No source filtering - let NewsAPI find from any available source
                "from": config.date_range.start_date.strftime("%Y-%m-%d"),
                "to": config.date_range.end_date.strftime("%Y-%m-%d"),
                "sortBy": "relevancy",
                "language": config.language,
                "pageSize": min(config.max_items_per_symbol, 100),
                "apiKey": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                articles = news_data.get("articles", [])
                
                for article in articles:
                    try:
                        article_data = self._parse_article(article, symbol, "symbol_news")
                        if article_data:
                            collected_data.append(article_data)
                    except Exception as e:
                        self.logger.warning(f"Error parsing article for {symbol}: {str(e)}")
                        continue
            
            self.logger.info(f"Collected {len(collected_data)} news articles for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error collecting news for {symbol}: {str(e)}")
        
        return collected_data
    
    async def _collect_general_financial_news(self, config: CollectionConfig) -> List[RawData]:
        """Collect general financial news"""
        collected_data = []
        
        try:
            # Build query for general financial news - no source filtering
            query = "stock market OR trading OR earnings OR financial OR investment"
            
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                # No source filtering - accept any financial source
                "from": config.date_range.start_date.strftime("%Y-%m-%d"),
                "to": config.date_range.end_date.strftime("%Y-%m-%d"),
                "sortBy": "popularity",
                "language": config.language,
                "pageSize": 50,
                "apiKey": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                articles = news_data.get("articles", [])
                
                # Filter articles that mention target symbols - handle None values safely
                for article in articles:
                    try:
                        # Safely handle None values
                        title = article.get("title") or ""
                        description = article.get("description") or ""
                        content = article.get("content") or ""
                        
                        title_upper = title.upper()
                        description_upper = description.upper()
                        content_upper = content.upper()
                        
                        # Check if article mentions any target symbols
                        mentioned_symbols = []
                        for symbol in config.symbols:
                            symbol_upper = symbol.upper()
                            if (symbol_upper in title_upper or 
                                symbol_upper in description_upper or 
                                symbol_upper in content_upper):
                                mentioned_symbols.append(symbol)
                        
                        if mentioned_symbols:
                            # Use first mentioned symbol
                            article_data = self._parse_article(
                                article, mentioned_symbols[0], "general_news"
                            )
                            if article_data:
                                collected_data.append(article_data)
                                
                    except Exception as e:
                        self.logger.debug(f"Skipping article due to error: {str(e)}")
                        continue
            
            self.logger.info(f"Collected {len(collected_data)} general financial news articles")
            
        except Exception as e:
            self.logger.error(f"Error collecting general financial news: {str(e)}")
        
        return collected_data
    
    def _parse_article(self, article: Dict[str, Any], symbol: str, content_type: str) -> Optional[RawData]:
        """Parse a news article into RawData format"""
        try:
            title = article.get("title", "")
            description = article.get("description", "")
            content = article.get("content", "")
            
            if not title:
                return None
            
            # Combine title, description, and content
            text_parts = [title]
            if description and description != title:
                text_parts.append(description)
            if content and content not in [title, description]:
                # Remove common NewsAPI content truncation markers
                content = content.replace("[+", "").replace("chars]", "")
                text_parts.append(content)
            
            full_text = "\n\n".join(text_parts)
            
            # Parse timestamp
            published_at = article.get("publishedAt", "")
            if published_at:
                timestamp = datetime.fromisoformat(
                    published_at.replace("Z", "+00:00")
                )
            else:
                from app.utils.timezone import malaysia_now
                timestamp = malaysia_now()
            
            return self._create_raw_data(
                content_type=content_type,
                text=full_text,
                timestamp=timestamp,
                stock_symbol=symbol.upper(),
                url=article.get("url", ""),
                metadata={
                    "source_name": article.get("source", {}).get("name", ""),
                    "author": article.get("author", ""),
                    "url_to_image": article.get("urlToImage", ""),
                    "newsapi_source_id": article.get("source", {}).get("id", "")
                }
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing article: {str(e)}")
            return None
    
    async def get_sources(self, category: str = "business") -> List[Dict[str, Any]]:
        """
        Get available news sources (bonus feature).
        
        Args:
            category: News category (business, general, etc.)
            
        Returns:
            List of available sources
        """
        try:
            await self._apply_rate_limit()
            
            url = f"{self.base_url}/sources"
            params = {
                "category": category,
                "language": "en",
                "apiKey": self.api_key
            }
            
            async with self._http_client as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                sources_data = response.json()
                return sources_data.get("sources", [])
                
        except Exception as e:
            self.logger.error(f"Error getting sources: {str(e)}")
            return []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._http_client:
            await self._http_client.aclose()