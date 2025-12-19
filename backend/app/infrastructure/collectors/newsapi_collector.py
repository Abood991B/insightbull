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
from app.utils.timezone import utc_now

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

# Use centralized logging system
from app.infrastructure.log_system import get_logger
logger = get_logger()


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
        """Get HTTP client with connection pooling for better performance"""
        return httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "InsightStockDash/1.0 (Financial News Collector)"
            },
            limits=httpx.Limits(
                max_keepalive_connections=20,  # Keep 20 connections alive
                max_connections=100,            # Max 100 total connections
                keepalive_expiry=30.0           # Keep connections alive for 30s
            )
        )
    
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
                
                if response.status_code == 200:
                    self.logger.debug("NewsAPI connection validated successfully")
                    return True
                elif response.status_code == 401:
                    error_msg = "Invalid API key - Please check your NewsAPI key in settings"
                    self.logger.error(f"NewsAPI validation failed: {error_msg} (401 Unauthorized)")
                    raise ValueError(error_msg)
                elif response.status_code == 426:
                    error_msg = "Upgrade required - Your NewsAPI plan doesn't support this endpoint"
                    self.logger.error(f"NewsAPI validation failed: {error_msg} (426 Upgrade Required)")
                    raise ValueError(error_msg)
                elif response.status_code == 429:
                    error_msg = "Rate limit exceeded - You've reached your daily request limit. Try again tomorrow or upgrade your NewsAPI plan"
                    self.logger.error(f"NewsAPI validation failed: {error_msg} (429 Too Many Requests)")
                    raise ValueError(error_msg)
                elif response.status_code == 500:
                    error_msg = "NewsAPI server error - Service temporarily unavailable"
                    self.logger.error(f"NewsAPI validation failed: {error_msg} (500 Internal Server Error)")
                    raise ValueError(error_msg)
                else:
                    error_msg = f"Unexpected error (HTTP {response.status_code})"
                    try:
                        error_data = response.json()
                        api_message = error_data.get('message', 'Unknown error')
                        error_msg = f"{error_msg}: {api_message}"
                    except:
                        pass
                    self.logger.error(f"NewsAPI validation failed: {error_msg}")
                    raise ValueError(error_msg)
                
        except Exception as e:
            self.logger.error(
                f"NewsAPI connection validation exception: {str(e)}",
                extra={"error_type": type(e).__name__, "operation": "validate_connection"}
            )
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect financial news from NewsAPI with parallel symbol processing.
        
        NOTE: NewsAPI free tier has strict rate limits (~58s between requests).
        To keep collection time reasonable, we limit to max 5 symbols per run.
        
        Args:
            config: Collection configuration
            
        Returns:
            CollectionResult with collected news data
        """
        start_time = utc_now()
        collected_data = []
        
        try:
            self._validate_config(config)
            
            # CRITICAL: Limit NewsAPI to max 5 symbols to avoid excessive wait times
            # NewsAPI free tier: ~58s rate limit = 5 symbols ≈ 5 minutes (reasonable)
            # For 15 symbols it would take 15 minutes which is unacceptable
            max_symbols_for_newsapi = 5
            symbols_to_collect = config.symbols[:max_symbols_for_newsapi]
            
            if len(config.symbols) > max_symbols_for_newsapi:
                self.logger.warning(
                    f"NewsAPI rate limit protection: Processing only {max_symbols_for_newsapi} of {len(config.symbols)} symbols",
                    extra={
                        "total_symbols": len(config.symbols),
                        "processing_symbols": max_symbols_for_newsapi,
                        "skipped_symbols": len(config.symbols) - max_symbols_for_newsapi,
                        "reason": "NewsAPI free tier rate limit (~58s between requests)"
                    }
                )
            
            # Parallelize collection across symbols (rate limiter handles concurrency)
            tasks = [
                self._collect_symbol_with_limit(symbol, config)
                for symbol in symbols_to_collect
            ]
            
            # Execute all symbol collections in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, Exception):
                    self.logger.error(f"NewsAPI symbol collection failed: {str(result)}")
                    continue
                if isinstance(result, list):
                    collected_data.extend(result)
            
            execution_time = (utc_now() - start_time).total_seconds()
            
            return CollectionResult(
                source=self.source,
                success=True,
                data=collected_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (utc_now() - start_time).total_seconds()
            error_msg = f"NewsAPI collection failed: {str(e)}"
            self.logger.error(error_msg)
            
            return CollectionResult(
                source=self.source,
                success=False,
                data=[],
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def _collect_symbol_with_limit(self, symbol: str, config: CollectionConfig) -> List[RawData]:
        """Collect news for a symbol with rate limiting"""
        await self._apply_rate_limit()
        return await self._collect_symbol_news(symbol, config)
    
    async def _collect_symbol_news(self, symbol: str, config: CollectionConfig) -> List[RawData]:
        """Collect news for specific stock symbol with improved relevance filtering"""
        collected_data = []
        
        try:
            # Build a more specific financial query
            # Include company name and financial context terms
            company_name = self._get_company_name(symbol)
            
            if company_name:
                # Use company name + financial context for better relevance
                query = f'"{company_name}" AND (stock OR shares OR market OR earnings OR investor)'
            else:
                # Fallback: symbol + financial context
                query = f'{symbol} AND (stock OR shares OR market OR earnings OR trading)'
            
            url = f"{self.base_url}/everything"
            params = {
                "q": query,
                # No source filtering - let NewsAPI find from any available source
                "from": config.date_range.start_date.strftime("%Y-%m-%d"),
                "to": config.date_range.end_date.strftime("%Y-%m-%d"),
                "sortBy": "relevancy",
                "language": config.language,
                "pageSize": min(config.max_items_per_symbol * 2, 100),  # Get extra for filtering
                "apiKey": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                articles = news_data.get("articles", [])
                
                for article in articles:
                    try:
                        # Pre-filter before creating RawData
                        title = article.get("title") or ""
                        description = article.get("description") or ""
                        content = article.get("content") or ""
                        full_text = f"{title} {description} {content}"
                        
                        # Skip obviously non-financial content
                        if self._is_non_financial_content(full_text):
                            self.logger.debug(f"Skipping non-financial article: {title[:50]}")
                            continue
                        
                        article_data = self._parse_article(article, symbol, "symbol_news")
                        if article_data:
                            collected_data.append(article_data)
                            
                        # Stop once we have enough
                        if len(collected_data) >= config.max_items_per_symbol:
                            break
                            
                    except Exception as e:
                        self.logger.warning(f"Error parsing article for {symbol}: {str(e)}")
                        continue
            
            self.logger.info(f"Collected {len(collected_data)} news articles for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error collecting news for {symbol}: {str(e)}")
        
        return collected_data
    
    def _get_company_name(self, symbol: str) -> Optional[str]:
        """Get company name for a stock symbol."""
        company_names = {
            "AAPL": "Apple",
            "MSFT": "Microsoft",
            "GOOGL": "Google",
            "GOOG": "Google",
            "AMZN": "Amazon",
            "META": "Meta",
            "NVDA": "Nvidia",
            "TSLA": "Tesla",
            "AMD": "AMD",
            "INTC": "Intel",
            "NFLX": "Netflix",
            "CRM": "Salesforce",
            "ORCL": "Oracle",
            "IBM": "IBM",
            "CSCO": "Cisco",
            "ADBE": "Adobe",
            "PYPL": "PayPal",
            "SQ": "Block",
            "SHOP": "Shopify",
            "UBER": "Uber",
            "LYFT": "Lyft",
            "AVGO": "Broadcom",
            "TXN": "Texas Instruments",
            "QCOM": "Qualcomm",
            "NOW": "ServiceNow",
        }
        return company_names.get(symbol.upper())
    
    def _is_non_financial_content(self, text: str) -> bool:
        """Check if content is clearly non-financial (sports, entertainment, etc.)"""
        text_lower = text.lower()
        
        # Exclusion patterns - if these appear without financial context, skip
        non_financial_patterns = [
            "volleyball", "basketball", "football", "soccer", "hockey",
            "baseball", "tennis", "golf", "olympics", "championship",
            "tournament", "playoff", "league", "nba", "nfl", "mlb",
            "movie", "film", "cinema", "actor", "actress", "director",
            "box office", "premiere", "trailer", "sequel", "streaming",
            "tv show", "series", "episode", "album", "concert", "tour",
            "music video", "grammy", "song", "recipe", "cooking",
            "weather forecast", "obituary", "wedding"
        ]
        
        # Financial terms that indicate relevance
        financial_terms = [
            "stock", "share", "market", "trading", "earnings", "revenue",
            "profit", "investor", "analyst", "price target", "upgrade",
            "downgrade", "quarterly", "fiscal", "ipo", "merger"
        ]
        
        has_non_financial = any(pattern in text_lower for pattern in non_financial_patterns)
        has_financial = any(term in text_lower for term in financial_terms)
        
        # Skip if has non-financial content AND no financial context
        return has_non_financial and not has_financial

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
                        full_text = f"{title} {description} {content}"
                        
                        # Skip non-financial content
                        if self._is_non_financial_content(full_text):
                            continue
                        
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
                timestamp = utc_now()
            
            return self._create_raw_data(
                content_type=content_type,
                text=full_text,
                timestamp=timestamp,
                stock_symbol=symbol.upper(),
                url=article.get("url", ""),
                metadata={
                    "title": title,  # Store title for database insertion
                    "source_name": article.get("source", {}).get("name", ""),
                    "author": article.get("author", ""),
                    "url_to_image": article.get("urlToImage", ""),
                    "newsapi_source_id": article.get("source", {}).get("id", ""),
                    "all_symbols": [symbol.upper()]  # Store symbols for stock_mentions column
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