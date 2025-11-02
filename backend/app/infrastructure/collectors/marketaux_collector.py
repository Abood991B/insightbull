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
from app.utils.timezone import utc_now

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
        """Get HTTP client with connection pooling for better performance"""
        return httpx.AsyncClient(
            timeout=30.0,
            limits=httpx.Limits(
                max_keepalive_connections=20,  # Keep 20 connections alive
                max_connections=100,            # Max 100 total connections
                keepalive_expiry=30.0           # Keep connections alive for 30s
            )
        )
    
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
        Collect financial news from MarketAux with batch support.
        
        Args:
            config: Collection configuration
            
        Returns:
            CollectionResult with collected news data
        """
        start_time = utc_now()
        collected_data = []
        
        try:
            self._validate_config(config)
            
            # Use batch collection for better efficiency (MarketAux supports up to 10 symbols per request)
            if len(config.symbols) > 3:
                collected_data = await self._collect_batch(config.symbols, config)
            else:
                # Small number of symbols - collect individually with rate limiting
                for symbol in config.symbols:
                    await self._apply_rate_limit()
                    symbol_data = await self._collect_symbol_news(symbol, config)
                    limited_data = symbol_data[:config.max_items_per_symbol]
                    collected_data.extend(limited_data)
            
            execution_time = (utc_now() - start_time).total_seconds()
            
            return CollectionResult(
                source=self.source,
                success=True,
                data=collected_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (utc_now() - start_time).total_seconds()
            error_msg = f"MarketAux collection failed: {str(e)}"
            self.logger.error(error_msg)
            
            return CollectionResult(
                source=self.source,
                success=False,
                data=[],
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def _collect_batch(self, symbols: List[str], config: CollectionConfig) -> List[RawData]:
        """
        Collect news for multiple symbols using MarketAux batch API.
        MarketAux supports up to 10 symbols per request (comma-separated).
        
        Args:
            symbols: List of stock symbols
            config: Collection configuration
            
        Returns:
            List of collected news data
        """
        collected_data = []
        batch_size = 10  # MarketAux max symbols per request
        
        # Split symbols into batches
        for i in range(0, len(symbols), batch_size):
            batch_symbols = symbols[i:i + batch_size]
            
            # Apply rate limiting before each batch
            await self._apply_rate_limit()
            
            try:
                # Create comma-separated symbol list
                symbols_param = ",".join([s.upper() for s in batch_symbols])
                
                url = f"{self.base_url}/news/all"
                params = {
                    "symbols": symbols_param,  # Batch request
                    "filter_entities": "true",
                    "language": "en",
                    "limit": config.max_items_per_symbol * len(batch_symbols),  # Total items for batch
                    "published_after": config.date_range.start_date.strftime("%Y-%m-%dT%H:%M:%S"),
                    "api_token": self.api_key
                }
                
                async with self._get_http_client() as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    
                    data = response.json()
                    
                    if "data" in data:
                        articles = data["data"]
                        
                        # Group articles by symbol to ensure fair distribution
                        articles_by_symbol = {symbol: [] for symbol in batch_symbols}
                        
                        for article in articles:
                            # Determine which symbol(s) this article belongs to
                            article_symbols = self._extract_symbols_from_article(article, batch_symbols)
                            
                            for symbol in article_symbols:
                                if len(articles_by_symbol[symbol]) < config.max_items_per_symbol:
                                    parsed_article = self._parse_news_item(article, symbol)
                                    if parsed_article:
                                        articles_by_symbol[symbol].append(parsed_article)
                        
                        # Flatten the grouped articles
                        for symbol_articles in articles_by_symbol.values():
                            collected_data.extend(symbol_articles)
                        
                        self.logger.info(f"Batch collected {len(collected_data)} articles for {len(batch_symbols)} symbols")
                
            except Exception as e:
                self.logger.error(f"Error collecting batch: {str(e)}")
                # Fall back to individual collection with retry logic
                for symbol in batch_symbols:
                    symbol_data = await self._collect_symbol_with_retry(symbol, config, max_retries=3)
                    collected_data.extend(symbol_data)
        
        return collected_data
    
    def _extract_symbols_from_article(self, article: dict, candidate_symbols: List[str]) -> List[str]:
        """
        Extract which symbols an article is relevant to.
        
        Args:
            article: Article data from API
            candidate_symbols: List of symbols to check against
            
        Returns:
            List of relevant symbols
        """
        relevant_symbols = []
        
        # Check if article has entities field
        if "entities" in article:
            article_symbols = [e.get("symbol", "").upper() for e in article.get("entities", [])]
            for symbol in candidate_symbols:
                if symbol.upper() in article_symbols:
                    relevant_symbols.append(symbol)
        
        # If no entities, check title and description
        if not relevant_symbols:
            text = f"{article.get('title', '')} {article.get('description', '')}".upper()
            for symbol in candidate_symbols:
                if symbol.upper() in text:
                    relevant_symbols.append(symbol)
        
        # Default to first symbol if none found
        if not relevant_symbols and candidate_symbols:
            relevant_symbols = [candidate_symbols[0]]
        
        return relevant_symbols
    
    async def _collect_symbol_with_retry(
        self, 
        symbol: str, 
        config: CollectionConfig, 
        max_retries: int = 3
    ) -> List[RawData]:
        """Collect news for a symbol with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                await self._apply_rate_limit()
                symbol_data = await self._collect_symbol_news(symbol, config)
                return symbol_data[:config.max_items_per_symbol]
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds (1s, 2s, 4s)
                    delay = 2 ** attempt
                    self.logger.warning(
                        f"Marketaux collection failed for {symbol} (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"Marketaux collection failed for {symbol} after {max_retries} attempts: {str(e)}")
                    return []  # Return empty list on final failure
        return []
    
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
                timestamp = utc_now()
            
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
    
