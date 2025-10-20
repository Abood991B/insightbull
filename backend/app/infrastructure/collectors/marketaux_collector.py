"""
MarketAux Data Collector
=======================

Collects financial news using MarketAux API.
Provides comprehensive market news and analysis.

Following FYP Report specification:
- Professional financial news sources
- Market analysis and insights
- Real-time news aggregation
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import asyncio
import logging

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


class MarketauxCollector(BaseCollector):
    """
    MarketAux API collector for financial news and market analysis.
    
    Features:
    - Professional financial news
    - Market analysis and insights
    - Multiple source aggregation
    - Real-time updates
    """
    
    def __init__(self, api_key: str, rate_limiter=None):
        """
        Initialize MarketAux collector.
        
        Args:
            api_key: MarketAux API key
            rate_limiter: Rate limiting handler
        """
        super().__init__(api_key=api_key, rate_limiter=rate_limiter)
        
        self.base_url = "https://api.marketaux.com/v1"
    
    @property
    def source(self) -> DataSource:
        return DataSource.MARKETAUX
    
    @property 
    def requires_api_key(self) -> bool:
        return True
    
    def _get_http_client(self) -> httpx.AsyncClient:
        """Get a fresh HTTP client for each request"""
        return httpx.AsyncClient(timeout=30.0)
    
    async def validate_connection(self) -> bool:
        """Validate MarketAux API connection"""
        try:
            # Test API with a simple news request
            url = f"{self.base_url}/news/all"
            params = {
                "limit": 1,
                "api_token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                return response.status_code == 200
                
        except Exception as e:
            self.logger.error(f"MarketAux connection validation failed: {str(e)}")
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect financial news from MarketAux.
        
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
            
            # Collect symbol-specific news only for equal distribution
            for symbol in config.symbols:
                symbol_data = await self._collect_symbol_news(symbol, config)
                # Ensure equal distribution by limiting to max_items_per_symbol
                limited_data = symbol_data[:config.max_items_per_symbol]
                collected_data.extend(limited_data)
                
                # Apply rate limiting between symbols
                if self.rate_limiter:
                    await asyncio.sleep(0.2)
            
            # Skip general market news to focus on target stocks only
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CollectionResult(
                source=self.source,
                success=True,
                data=collected_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"MarketAux collection failed: {str(e)}"
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
            url = f"{self.base_url}/news/all"
            params = {
                "symbols": symbol.upper(),
                "filter_entities": "true",
                "language": "en",
                "limit": config.max_items_per_symbol,
                "published_after": config.date_range.start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "published_before": config.date_range.end_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "sort": "published_desc",
                "api_token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                articles = news_data.get("data", [])
                
                for article in articles:
                    try:
                        article_data = self._parse_article(article, symbol, "symbol_news")
                        if article_data:
                            collected_data.append(article_data)
                    except Exception as e:
                        self.logger.warning(f"Error parsing article for {symbol}: {str(e)}")
                        continue
            
            self.logger.info(f"Collected {len(collected_data)} MarketAux articles for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error collecting MarketAux news for {symbol}: {str(e)}")
        
        return collected_data
    
    async def _collect_market_news(self, config: CollectionConfig) -> List[RawData]:
        """Collect general market news"""
        collected_data = []
        
        try:
            url = f"{self.base_url}/news/all"
            params = {
                "filter_entities": "true",
                "language": "en",
                "limit": 50,  # Get more for filtering
                "published_after": config.date_range.start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "published_before": config.date_range.end_date.strftime("%Y-%m-%dT%H:%M:%S"),
                "sort": "published_desc",
                "api_token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                articles = news_data.get("data", [])
                
                # Filter articles that mention target symbols
                relevant_articles = []
                for article in articles:
                    try:
                        # Check entities and text for symbol mentions
                        entities = article.get("entities", [])
                        title = article.get("title", "").upper()
                        description = article.get("description", "").upper()
                        
                        mentioned_symbols = set()
                        
                        # Check entities
                        for entity in entities:
                            if entity.get("type") == "stock":
                                symbol = entity.get("symbol", "").upper()
                                if symbol in [s.upper() for s in config.symbols]:
                                    mentioned_symbols.add(symbol)
                        
                        # Check text content
                        for symbol in config.symbols:
                            symbol_upper = symbol.upper()
                            if symbol_upper in title or symbol_upper in description:
                                mentioned_symbols.add(symbol_upper)
                        
                        if mentioned_symbols:
                            article_data = self._parse_article(
                                article, list(mentioned_symbols)[0], "market_news"
                            )
                            if article_data:
                                relevant_articles.append(article_data)
                                
                    except Exception as e:
                        self.logger.warning(f"Error filtering market news: {str(e)}")
                        continue
                
                # Limit results
                collected_data = relevant_articles[:config.max_items_per_symbol]
            
            self.logger.info(f"Collected {len(collected_data)} relevant MarketAux market news")
            
        except Exception as e:
            self.logger.error(f"Error collecting MarketAux market news: {str(e)}")
        
        return collected_data
    
    def _parse_article(self, article: Dict[str, Any], symbol: str, content_type: str) -> Optional[RawData]:
        """Parse a MarketAux article into RawData format"""
        try:
            title = article.get("title", "")
            description = article.get("description", "")
            snippet = article.get("snippet", "")
            
            if not title:
                return None
            
            # Combine title, description, and snippet
            text_parts = [title]
            if description and description != title:
                text_parts.append(description)
            if snippet and snippet not in [title, description]:
                text_parts.append(snippet)
            
            full_text = "\n\n".join(text_parts)
            
            # Parse timestamp
            published_at = article.get("published_at", "")
            if published_at:
                # MarketAux uses ISO format
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
                    "source": article.get("source", ""),
                    "image_url": article.get("image_url", ""),
                    "entities": article.get("entities", []),
                    "keywords": article.get("keywords", []),
                    "marketaux_uuid": article.get("uuid", ""),
                    "sentiment": article.get("sentiment", {}),
                    "similar": article.get("similar", [])
                }
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing MarketAux article: {str(e)}")
            return None
    
    async def get_market_sentiment(self, symbols: List[str]) -> Dict[str, Any]:
        """
        Get market sentiment analysis (bonus feature).
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Market sentiment data
        """
        try:
            await self._apply_rate_limit()
            
            url = f"{self.base_url}/news/sentiment"
            params = {
                "symbols": ",".join(symbols),
                "api_token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                return response.json()
                
        except Exception as e:
            self.logger.error(f"Error getting market sentiment: {str(e)}")
            return {}
    
