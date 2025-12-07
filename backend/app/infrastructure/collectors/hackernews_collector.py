"""
Hacker News Data Collector
==========================

Collects stories and comments from Hacker News using the Algolia Search API.
Filters content by stock symbols and provides near real-time data collection.

API Documentation: https://hn.algolia.com/api

Key Features:
- No API key required (unlimited requests)
- Near real-time indexing (< 1 minute delay)
- Full-text search across stories and comments
- Date-based filtering with Unix timestamps

Following FYP Report specification:
- Multi-source data collection from social media
- Content filtering by stock symbols  
- Quality control and data validation
"""

import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set
import asyncio
import logging
import aiohttp
from app.utils.timezone import utc_now
from app.infrastructure.log_system import get_logger

from .base_collector import (
    BaseCollector, 
    DataSource, 
    RawData, 
    CollectionConfig, 
    CollectionResult,
    CollectionError
)

# Use structured logging system for consistent log management
logger = logging.getLogger(__name__)
structured_logger = get_logger()


class HackerNewsCollector(BaseCollector):
    """
    Hacker News data collector using Algolia Search API.
    
    Collects stories and comments mentioning stock symbols.
    No authentication required - free and unlimited access.
    
    API Endpoints:
    - Search: https://hn.algolia.com/api/v1/search
    - Search by date: https://hn.algolia.com/api/v1/search_by_date
    
    Rate Limiting:
    - No official rate limits
    - Recommended: 1 request per second for courtesy
    """
    
    # Base URL for Algolia HN API
    BASE_URL = "https://hn.algolia.com/api/v1"
    
    # Request timeout in seconds
    REQUEST_TIMEOUT = 30
    
    # Minimum points for quality filtering
    DEFAULT_MIN_POINTS = 2
    
    def __init__(self, rate_limiter=None):
        """
        Initialize Hacker News collector.
        
        Args:
            rate_limiter: Optional rate limiting handler (recommended for batch operations)
        """
        super().__init__(api_key=None, rate_limiter=rate_limiter)
        
        # Compile regex patterns for stock symbol detection
        self._stock_patterns = [
            re.compile(r'\$([A-Z]{1,5})\b'),  # $AAPL format
            re.compile(r'\b([A-Z]{2,5})\b'),  # AAPL format (2-5 chars)
        ]
        
        # HTTP session for connection pooling
        self._session: Optional[aiohttp.ClientSession] = None
        
    @property
    def source(self) -> DataSource:
        return DataSource.HACKERNEWS
    
    @property 
    def requires_api_key(self) -> bool:
        return False
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def validate_connection(self) -> bool:
        """Validate connection to Hacker News API"""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.BASE_URL}/search",
                params={"query": "test", "hitsPerPage": 1}
            ) as response:
                is_valid = response.status == 200
                if is_valid:
                    structured_logger.info(
                        "HackerNews API connection validated successfully",
                        component="hackernews_collector",
                        api_endpoint=self.BASE_URL
                    )
                else:
                    structured_logger.warning(
                        f"HackerNews API returned non-200 status: {response.status}",
                        component="hackernews_collector",
                        status_code=response.status
                    )
                return is_valid
        except Exception as e:
            structured_logger.error(
                f"HackerNews connection validation failed: {str(e)}",
                component="hackernews_collector",
                error_type=type(e).__name__
            )
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect stories and comments from Hacker News.
        
        Uses parallel collection across symbols for efficiency.
        
        Args:
            config: Collection configuration with symbols and date range
            
        Returns:
            CollectionResult with collected data
        """
        start_time = utc_now()
        collected_data = []
        
        # Log collection start with structured logging
        structured_logger.info(
            f"Starting HackerNews data collection for {len(config.symbols)} symbols",
            component="hackernews_collector",
            symbols=config.symbols,
            date_range_start=config.date_range.start_date.isoformat(),
            date_range_end=config.date_range.end_date.isoformat(),
            include_comments=config.include_comments
        )
        
        try:
            self._validate_config(config)
            await self._apply_rate_limit()
            
            # Parallelize collection across symbols
            tasks = [
                self._collect_for_symbol(symbol.upper(), config)
                for symbol in config.symbols
            ]
            
            # Execute all symbol collections in parallel
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results and track errors
            error_count = 0
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    error_count += 1
                    structured_logger.error(
                        f"HackerNews collection failed for symbol: {config.symbols[i]}",
                        component="hackernews_collector",
                        symbol=config.symbols[i],
                        error=str(result)
                    )
                    continue
                if isinstance(result, list):
                    collected_data.extend(result)
            
            execution_time = (utc_now() - start_time).total_seconds()
            
            # Log collection completion with stats
            structured_logger.info(
                f"HackerNews collection complete: {len(collected_data)} items collected",
                component="hackernews_collector",
                items_collected=len(collected_data),
                symbols_processed=len(config.symbols),
                symbols_with_errors=error_count,
                execution_time_seconds=round(execution_time, 2)
            )
            
            return CollectionResult(
                source=self.source,
                success=True,
                data=collected_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (utc_now() - start_time).total_seconds()
            error_msg = f"HackerNews collection failed: {str(e)}"
            
            structured_logger.error(
                error_msg,
                component="hackernews_collector",
                symbols=config.symbols,
                execution_time_seconds=round(execution_time, 2),
                error_type=type(e).__name__
            )
            
            return CollectionResult(
                source=self.source,
                success=False,
                data=[],
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def _collect_for_symbol(
        self,
        symbol: str,
        config: CollectionConfig
    ) -> List[RawData]:
        """
        Collect stories and comments for a specific stock symbol.
        
        Args:
            symbol: Stock symbol to search for
            config: Collection configuration
            
        Returns:
            List of RawData items for this symbol
        """
        collected_data = []
        max_items = config.max_items_per_symbol
        
        try:
            # Collect stories first
            stories = await self._search_stories(symbol, config, max_items // 2)
            collected_data.extend(stories)
            
            # Collect comments if enabled
            if config.include_comments:
                comments = await self._search_comments(
                    symbol, config, max_items - len(stories)
                )
                collected_data.extend(comments)
            
            # Log per-symbol collection stats
            if collected_data:
                structured_logger.debug(
                    f"HackerNews collected {len(collected_data)} items for {symbol}",
                    component="hackernews_collector",
                    symbol=symbol,
                    stories_count=len(stories),
                    comments_count=len(collected_data) - len(stories)
                )
            
            # Small delay between symbols for courtesy
            await asyncio.sleep(0.1)
            
        except Exception as e:
            structured_logger.warning(
                f"Error collecting HackerNews data for symbol: {symbol}",
                component="hackernews_collector",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__
            )
        
        return collected_data[:max_items]
    
    async def _search_stories(
        self,
        symbol: str,
        config: CollectionConfig,
        max_items: int
    ) -> List[RawData]:
        """Search for stories mentioning a stock symbol"""
        collected_data = []
        
        try:
            session = await self._get_session()
            
            # Build search query - use simple terms (Algolia HN API works best with simple queries)
            # The API does implicit OR between space-separated terms
            company_name = self._get_company_name(symbol)
            if company_name:
                # Use company name as primary query (more natural language match)
                # Symbol check is done in _contains_symbol filter
                query = company_name
            else:
                query = symbol
            
            # Build date filters
            start_ts = int(config.date_range.start_date.timestamp())
            end_ts = int(config.date_range.end_date.timestamp())
            
            # Use search_by_date for recent items (more relevant for real-time)
            params = {
                "query": query,
                "tags": "story",
                "hitsPerPage": min(max_items * 2, 200),  # Get extra for filtering
                "numericFilters": f"created_at_i>{start_ts},created_at_i<{end_ts}"
            }
            
            async with session.get(
                f"{self.BASE_URL}/search_by_date",
                params=params
            ) as response:
                if response.status != 200:
                    structured_logger.warning(
                        f"HackerNews API returned non-200 status for stories search",
                        component="hackernews_collector",
                        symbol=symbol,
                        status_code=response.status,
                        query=query
                    )
                    return []
                
                data = await response.json()
                hits = data.get("hits", [])
                
                for hit in hits:
                    if len(collected_data) >= max_items:
                        break
                    
                    # Apply quality filters
                    points = hit.get("points", 0) or 0
                    min_score = config.min_score or self.DEFAULT_MIN_POINTS
                    
                    if points < min_score:
                        continue
                    
                    # Verify symbol is actually mentioned
                    title = hit.get("title", "")
                    story_text = hit.get("story_text") or ""
                    full_text = f"{title} {story_text}"
                    
                    if not self._contains_symbol(full_text, symbol):
                        continue
                    
                    # Skip non-financial content
                    if self._is_non_financial_content(full_text):
                        structured_logger.debug(
                            f"Skipping non-financial HN story: {title[:50]}",
                            component="hackernews_collector"
                        )
                        continue
                    
                    # Parse timestamp
                    created_at = hit.get("created_at_i", 0)
                    timestamp = datetime.fromtimestamp(created_at, tz=timezone.utc)
                    
                    # Extract all mentioned symbols
                    extracted_symbols = self._extract_stock_symbols(full_text)
                    watchlist_symbols = {s.upper() for s in config.symbols}
                    valid_symbols = extracted_symbols.intersection(watchlist_symbols)
                    if symbol not in valid_symbols:
                        valid_symbols.add(symbol)
                    
                    # Create RawData
                    raw_data = self._create_raw_data(
                        content_type="story",
                        text=title if not story_text else f"{title}\n\n{story_text}",
                        timestamp=timestamp,
                        stock_symbol=symbol,
                        url=hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        metadata={
                            "title": title,
                            "hn_id": hit.get("objectID"),
                            "author": hit.get("author"),
                            "points": points,
                            "num_comments": hit.get("num_comments", 0) or 0,
                            "all_symbols": list(valid_symbols)
                        }
                    )
                    collected_data.append(raw_data)
                
        except Exception as e:
            structured_logger.warning(
                f"Error searching HackerNews stories for symbol: {symbol}",
                component="hackernews_collector",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__
            )
        
        return collected_data
    
    async def _search_comments(
        self,
        symbol: str,
        config: CollectionConfig,
        max_items: int
    ) -> List[RawData]:
        """Search for comments mentioning a stock symbol"""
        collected_data = []
        
        if max_items <= 0:
            return collected_data
        
        try:
            session = await self._get_session()
            
            # Build search query - use simple terms
            company_name = self._get_company_name(symbol)
            if company_name:
                query = company_name
            else:
                query = symbol
            
            # Build date filters
            start_ts = int(config.date_range.start_date.timestamp())
            end_ts = int(config.date_range.end_date.timestamp())
            
            params = {
                "query": query,
                "tags": "comment",
                "hitsPerPage": min(max_items * 2, 200),
                "numericFilters": f"created_at_i>{start_ts},created_at_i<{end_ts}"
            }
            
            async with session.get(
                f"{self.BASE_URL}/search_by_date",
                params=params
            ) as response:
                if response.status != 200:
                    structured_logger.warning(
                        f"HackerNews API returned non-200 status for comments search",
                        component="hackernews_collector",
                        symbol=symbol,
                        status_code=response.status,
                        query=query
                    )
                    return []
                
                data = await response.json()
                hits = data.get("hits", [])
                
                for hit in hits:
                    if len(collected_data) >= max_items:
                        break
                    
                    comment_text = hit.get("comment_text", "")
                    if not comment_text:
                        continue
                    
                    # Clean HTML tags from comment
                    comment_text = self._clean_html(comment_text)
                    
                    # Verify symbol is mentioned
                    if not self._contains_symbol(comment_text, symbol):
                        continue
                    
                    # Parse timestamp
                    created_at = hit.get("created_at_i", 0)
                    timestamp = datetime.fromtimestamp(created_at, tz=timezone.utc)
                    
                    # Extract all mentioned symbols
                    extracted_symbols = self._extract_stock_symbols(comment_text)
                    watchlist_symbols = {s.upper() for s in config.symbols}
                    valid_symbols = extracted_symbols.intersection(watchlist_symbols)
                    if symbol not in valid_symbols:
                        valid_symbols.add(symbol)
                    
                    # Create RawData
                    raw_data = self._create_raw_data(
                        content_type="comment",
                        text=comment_text,
                        timestamp=timestamp,
                        stock_symbol=symbol,
                        url=f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        metadata={
                            "hn_id": hit.get("objectID"),

                            "author": hit.get("author"),
                            "all_symbols": list(valid_symbols)
                        }
                    )
                    collected_data.append(raw_data)
                
        except Exception as e:
            structured_logger.warning(
                f"Error searching HackerNews comments for symbol: {symbol}",
                component="hackernews_collector",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__
            )
        
        return collected_data
    
    def _contains_symbol(self, text: str, symbol: str) -> bool:
        """Check if text contains the stock symbol OR company name"""
        if not text:
            return False
        text_upper = text.upper()
        
        # Check for symbol
        symbol_found = (
            f"${symbol}" in text_upper or
            f" {symbol} " in f" {text_upper} " or
            text_upper.startswith(f"{symbol} ") or
            text_upper.endswith(f" {symbol}")
        )
        
        if symbol_found:
            return True
        
        # Also check for company name
        company_name = self._get_company_name(symbol)
        if company_name:
            return company_name.upper() in text_upper
        
        return False
    
    def _extract_stock_symbols(self, text: str) -> Set[str]:
        """Extract stock symbols from text using regex patterns"""
        if not text:
            return set()
        
        symbols = set()
        
        for pattern in self._stock_patterns:
            matches = pattern.findall(text.upper())
            symbols.update(matches)
        
        # Filter out common false positives
        false_positives = {
            'THE', 'AND', 'OR', 'BUT', 'FOR', 'ON', 'AT', 'TO', 'FROM',
            'WITH', 'BY', 'OF', 'IN', 'OUT', 'UP', 'DOWN', 'ALL', 'ANY',
            'GET', 'GOT', 'PUT', 'SET', 'NEW', 'OLD', 'BIG', 'LOT', 'TOP',
            'END', 'YOU', 'HE', 'SHE', 'WE', 'THEY', 'IT', 'THIS', 'THAT',
            'WHAT', 'WHO', 'WHY', 'HOW', 'WHEN', 'WHERE', 'USD', 'EUR',
            'GBP', 'CAD', 'AUD', 'JPY', 'CNY', 'INR', 'CEO', 'CFO', 'CTO',
            'IPO', 'ETF', 'NYSE', 'NASDAQ', 'SEC', 'FDA', 'FED', 'GDP',
            'API', 'AI', 'ML', 'VR', 'AR', 'EV', 'ESG', 'DD', 'TA', 'FA',
            'HTML', 'CSS', 'JS', 'SQL', 'AWS', 'GCP', 'SRE', 'DNS', 'CDN',
            'URL', 'URI', 'SDK', 'IDE', 'UI', 'UX', 'OS', 'VM', 'DB'
        }
        
        return {s for s in symbols if s not in false_positives and 2 <= len(s) <= 5}
    
    def _clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ""
        # Simple HTML tag removal
        import re
        clean = re.sub(r'<[^>]+>', ' ', text)
        clean = re.sub(r'\s+', ' ', clean)
        return clean.strip()
    
    def _get_company_name(self, symbol: str) -> Optional[str]:
        """Get company name for symbol to improve search quality"""
        company_names = {
            'AAPL': 'Apple',
            'MSFT': 'Microsoft',
            'NVDA': 'NVIDIA',
            'GOOGL': 'Google',
            'AMZN': 'Amazon',
            'META': 'Meta',
            'TSLA': 'Tesla',
            'AVGO': 'Broadcom',
            'ORCL': 'Oracle',
            'CRM': 'Salesforce',
            'AMD': 'AMD',
            'ADBE': 'Adobe',
            'CSCO': 'Cisco',
            'ACN': 'Accenture',
            'INTC': 'Intel',
            'IBM': 'IBM',
            'TXN': 'Texas Instruments',
            'QCOM': 'Qualcomm',
            'NOW': 'ServiceNow',
            'INTU': 'Intuit'
        }
        return company_names.get(symbol.upper())
    
    def _is_non_financial_content(self, text: str) -> bool:
        """
        Check if content is clearly non-financial (sports, entertainment, etc.).
        Returns True if content should be skipped.
        """
        text_lower = text.lower()
        
        # Exclusion patterns - content with these is likely NOT financial
        non_financial_patterns = [
            "volleyball", "basketball", "football", "soccer", "hockey",
            "baseball", "tennis", "golf", "olympics", "championship",
            "tournament", "playoff", "nba finals", "nfl", "mlb", "nhl",
            "world cup", "super bowl", "slam dunk", "touchdown", "home run",
            "movie", "film", "cinema", "actor", "actress", "director",
            "box office", "premiere", "trailer", "sequel", "franchise",
            "hollywood", "streaming service", "tv show", "series premiere",
            "album release", "concert", "tour", "music video", "grammy",
            "recipe", "cooking", "ingredients", "calories",
            "weather forecast", "temperature", "humidity",
            "obituary", "wedding", "birth announcement"
        ]
        
        # Financial terms that indicate relevance (override exclusions)
        financial_terms = [
            "stock", "share", "market", "trading", "earnings", "revenue",
            "profit", "investor", "analyst", "valuation", "ipo", "merger",
            "acquisition", "quarterly", "fiscal", "dividend", "price target",
            "wall street", "hedge fund", "venture capital", "startup funding"
        ]
        
        has_non_financial = any(pattern in text_lower for pattern in non_financial_patterns)
        has_financial = any(term in text_lower for term in financial_terms)
        
        # Skip if has non-financial content AND no financial context
        return has_non_financial and not has_financial

    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup session"""
        await self.close()
