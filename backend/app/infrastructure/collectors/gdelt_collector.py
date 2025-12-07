"""
GDELT Data Collector
====================

Collects global news data using GDELT DOC 2.0 API.
Provides high-volume global financial news coverage.

API Documentation: https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/

Key Features:
- No API key required (completely free and unlimited)
- Global news coverage from 100+ countries in 65 languages
- Updates every 15 minutes
- Massive historical data availability (3 months rolling window)
- Articles returned with title, URL, source domain, language, date

Note on Sentiment:
- GDELT DOC 2.0 artlist mode does NOT return per-article tone scores
- Tone is available for FILTERING (tone<-5, tone>5) but not in response
- Our system uses FinBERT (ProsusAI/finbert) to analyze the article titles for sentiment
- This is consistent with how we process other news sources

Following FYP Report specification:
- Multi-source data collection
- High-volume news aggregation
"""

import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional, Set
from urllib.parse import urlencode, quote
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


class GDELTCollector(BaseCollector):
    """
    GDELT DOC 2.0 API collector for global financial news.
    
    Collects news articles mentioning stock symbols from global sources.
    No authentication required - completely free and unlimited.
    
    Articles contain: title, URL, source domain, language, country, date.
    Sentiment analysis is performed by FinBERT (ProsusAI/finbert) on article titles.
    
    API Endpoint:
    - DOC API: https://api.gdeltproject.org/api/v2/doc/doc
    
    Rate Limiting:
    - No official rate limits
    - Recommended: 1-2 requests per second for courtesy
    - Returns up to 250 articles per request
    """
    
    # Base URL for GDELT DOC 2.0 API
    BASE_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
    
    # Request timeout in seconds
    REQUEST_TIMEOUT = 45
    
    # Maximum results per request (GDELT limit)
    MAX_RESULTS_PER_REQUEST = 250
    
    # Financial/business domains for quality filtering
    TRUSTED_FINANCIAL_DOMAINS = {
        "reuters.com", "bloomberg.com", "wsj.com", "ft.com",
        "cnbc.com", "marketwatch.com", "finance.yahoo.com",
        "businessinsider.com", "forbes.com", "barrons.com",
        "seekingalpha.com", "thestreet.com", "investopedia.com",
        "fool.com", "benzinga.com", "zacks.com"
    }
    
    def __init__(self, rate_limiter=None):
        """
        Initialize GDELT collector.
        
        Args:
            rate_limiter: Optional rate limiting handler (recommended for batch operations)
        """
        super().__init__(api_key=None, rate_limiter=rate_limiter)
        
        # HTTP session for connection pooling
        self._session: Optional[aiohttp.ClientSession] = None
        
    @property
    def source(self) -> DataSource:
        return DataSource.GDELT
    
    @property 
    def requires_api_key(self) -> bool:
        return False
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session with connection pooling"""
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=self.REQUEST_TIMEOUT)
            connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={
                    "User-Agent": "InsightStockDash/1.0 (Financial Sentiment Analysis)"
                }
            )
        return self._session
    
    async def close(self):
        """Close the HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    async def validate_connection(self) -> bool:
        """Validate connection to GDELT API"""
        try:
            session = await self._get_session()
            
            # Simple test query
            params = {
                "query": "stock market",
                "mode": "artlist",
                "maxrecords": "1",
                "format": "json"
            }
            
            url = f"{self.BASE_URL}?{urlencode(params)}"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    is_valid = "articles" in data or isinstance(data, dict)
                    if is_valid:
                        structured_logger.info(
                            "GDELT API connection validated successfully",
                            component="gdelt_collector",
                            api_endpoint=self.BASE_URL
                        )
                    return is_valid
                else:
                    structured_logger.warning(
                        f"GDELT API returned non-200 status: {response.status}",
                        component="gdelt_collector",
                        status_code=response.status
                    )
                    return False
                
        except Exception as e:
            structured_logger.error(
                f"GDELT connection validation failed: {str(e)}",
                component="gdelt_collector",
                error_type=type(e).__name__
            )
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect news articles from GDELT.
        
        Uses parallel collection across symbols for efficiency.
        Returns articles with pre-computed tone/sentiment scores.
        
        Args:
            config: Collection configuration with symbols and date range
            
        Returns:
            CollectionResult with collected data including tone scores
        """
        start_time = utc_now()
        collected_data = []
        
        # Log collection start with structured logging
        structured_logger.info(
            f"Starting GDELT data collection for {len(config.symbols)} symbols",
            component="gdelt_collector",
            symbols=config.symbols,
            date_range_start=config.date_range.start_date.isoformat(),
            date_range_end=config.date_range.end_date.isoformat()
        )
        
        try:
            self._validate_config(config)
            await self._apply_rate_limit()
            
            # Collect for each symbol sequentially to be courteous to GDELT
            # (parallel might overwhelm the free API)
            error_count = 0
            for symbol in config.symbols:
                try:
                    symbol_data = await self._collect_for_symbol(
                        symbol.upper(), 
                        config
                    )
                    collected_data.extend(symbol_data)
                    
                    # Small delay between symbols for courtesy
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    error_count += 1
                    structured_logger.warning(
                        f"Error collecting GDELT data for symbol: {symbol}",
                        component="gdelt_collector",
                        symbol=symbol,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    continue
            
            execution_time = (utc_now() - start_time).total_seconds()
            
            # Log collection completion with stats
            structured_logger.info(
                f"GDELT collection complete: {len(collected_data)} items collected",
                component="gdelt_collector",
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
            error_msg = f"GDELT collection failed: {str(e)}"
            
            structured_logger.error(
                error_msg,
                component="gdelt_collector",
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
        Collect news articles for a specific stock symbol.
        
        Args:
            symbol: Stock symbol to search for
            config: Collection configuration
            
        Returns:
            List of RawData items for this symbol
        """
        collected_data = []
        max_items = config.max_items_per_symbol
        
        try:
            # Get company name for better search results
            company_name = self._get_company_name(symbol)
            
            # Build search query - use company name if available
            if company_name:
                # Search for company name + stock/shares context
                query = f'"{company_name}" (stock OR shares OR earnings OR market)'
            else:
                query = f"{symbol} stock"
            
            # Build date range for GDELT format (YYYYMMDDHHMMSS)
            start_dt = config.date_range.start_date.strftime("%Y%m%d%H%M%S")
            end_dt = config.date_range.end_date.strftime("%Y%m%d%H%M%S")
            
            # Build API parameters
            params = {
                "query": query,
                "mode": "artlist",
                "maxrecords": str(min(max_items * 2, self.MAX_RESULTS_PER_REQUEST)),
                "format": "json",
                "startdatetime": start_dt,
                "enddatetime": end_dt,
                "sourcelang": "eng"  # English sources only
            }
            
            url = f"{self.BASE_URL}?{urlencode(params, quote_via=quote)}"
            
            session = await self._get_session()
            
            async with session.get(url) as response:
                if response.status != 200:
                    structured_logger.warning(
                        f"GDELT API returned non-200 status for symbol: {symbol}",
                        component="gdelt_collector",
                        symbol=symbol,
                        status_code=response.status,
                        query=query
                    )
                    return []
                
                data = await response.json()
                articles = data.get("articles", [])
                
                for article in articles:
                    if len(collected_data) >= max_items:
                        break
                    
                    title = article.get("title", "")
                    if not title or not title.strip():
                        continue
                    
                    # Verify the article is relevant to the symbol
                    if not self._is_relevant(title, symbol, company_name):
                        continue
                    
                    # Parse the seen date
                    seen_date = article.get("seendate", "")
                    timestamp = self._parse_gdelt_date(seen_date)
                    if not timestamp:
                        continue
                    
                    # Get source domain and metadata
                    # Note: GDELT artlist mode does NOT return per-article tone
                    # Sentiment will be computed by FinBERT on the title
                    domain = article.get("domain", "")
                    url = article.get("url", "")
                    source_country = article.get("sourcecountry", "")
                    language = article.get("language", "English")
                    
                    # Determine if from trusted financial source
                    is_trusted_source = any(
                        trusted in domain.lower() 
                        for trusted in self.TRUSTED_FINANCIAL_DOMAINS
                    )
                    
                    # Extract all mentioned symbols from title
                    extracted_symbols = self._extract_stock_symbols(title)
                    watchlist_symbols = {s.upper() for s in config.symbols}
                    valid_symbols = extracted_symbols.intersection(watchlist_symbols)
                    if symbol not in valid_symbols:
                        valid_symbols.add(symbol)
                    
                    # Create RawData with GDELT-specific metadata
                    raw_data = self._create_raw_data(
                        content_type="article",
                        text=title,  # GDELT provides title only, not full text
                        timestamp=timestamp,
                        stock_symbol=symbol,
                        url=url,
                        metadata={
                            "title": title,
                            "domain": domain,
                            "source_country": source_country,
                            "language": language,
                            "is_trusted_source": is_trusted_source,
                            "all_symbols": list(valid_symbols),
                            "social_image": article.get("socialimage", ""),
                            "seen_date": seen_date
                        }
                    )
                    collected_data.append(raw_data)
                
                # Log per-symbol collection stats
                if collected_data:
                    structured_logger.debug(
                        f"GDELT collected {len(collected_data)} articles for {symbol}",
                        component="gdelt_collector",
                        symbol=symbol,
                        articles_count=len(collected_data)
                    )
                
        except aiohttp.ClientError as e:
            structured_logger.warning(
                f"HTTP error collecting GDELT data for symbol: {symbol}",
                component="gdelt_collector",
                symbol=symbol,
                error=str(e),
                error_type="ClientError"
            )
        except Exception as e:
            structured_logger.warning(
                f"Error collecting GDELT data for symbol: {symbol}",
                component="gdelt_collector",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__
            )
        
        return collected_data[:max_items]
    
    def _parse_gdelt_date(self, date_str: str) -> Optional[datetime]:
        """
        Parse GDELT date format (YYYYMMDDTHHMMSSZ or YYYYMMDDHHMMSS).
        
        Args:
            date_str: GDELT date string
            
        Returns:
            datetime object or None if parsing fails
        """
        if not date_str:
            return None
        
        try:
            # Try format: 20251130T143000Z
            if "T" in date_str:
                date_str = date_str.replace("Z", "")
                return datetime.strptime(date_str, "%Y%m%dT%H%M%S").replace(tzinfo=timezone.utc)
            # Try format: 20251130143000
            elif len(date_str) >= 14:
                return datetime.strptime(date_str[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            # Try format: 20251130
            elif len(date_str) >= 8:
                return datetime.strptime(date_str[:8], "%Y%m%d").replace(tzinfo=timezone.utc)
        except ValueError as e:
            self.logger.debug(f"Failed to parse GDELT date '{date_str}': {e}")
        
        return None
    
    def _is_relevant(self, text: str, symbol: str, company_name: Optional[str]) -> bool:
        """
        Check if text is relevant to the stock symbol or company.
        
        Args:
            text: Article title/text
            symbol: Stock symbol
            company_name: Company name (optional)
            
        Returns:
            True if relevant, False otherwise
        """
        if not text:
            return False
        
        text_upper = text.upper()
        
        # Check for symbol
        symbol_patterns = [
            f"${symbol}",
            f" {symbol} ",
            f"({symbol})",
            f":{symbol}",
        ]
        
        for pattern in symbol_patterns:
            if pattern in text_upper or text_upper.startswith(f"{symbol} ") or text_upper.endswith(f" {symbol}"):
                return True
        
        # Check for company name
        if company_name and company_name.upper() in text_upper:
            return True
        
        return False
    
    def _extract_stock_symbols(self, text: str) -> Set[str]:
        """Extract stock symbols from text using regex patterns"""
        if not text:
            return set()
        
        symbols = set()
        
        # Pattern for $SYMBOL format
        dollar_pattern = re.compile(r'\$([A-Z]{1,5})\b')
        symbols.update(dollar_pattern.findall(text.upper()))
        
        # Pattern for standalone symbols (2-5 uppercase letters)
        word_pattern = re.compile(r'\b([A-Z]{2,5})\b')
        symbols.update(word_pattern.findall(text.upper()))
        
        # Filter out common false positives
        false_positives = {
            'THE', 'AND', 'OR', 'BUT', 'FOR', 'ON', 'AT', 'TO', 'FROM',
            'WITH', 'BY', 'OF', 'IN', 'OUT', 'UP', 'DOWN', 'ALL', 'ANY',
            'GET', 'GOT', 'PUT', 'SET', 'NEW', 'OLD', 'BIG', 'LOT', 'TOP',
            'END', 'YOU', 'HE', 'SHE', 'WE', 'THEY', 'IT', 'THIS', 'THAT',
            'WHAT', 'WHO', 'WHY', 'HOW', 'WHEN', 'WHERE', 'USD', 'EUR',
            'GBP', 'CAD', 'AUD', 'JPY', 'CNY', 'INR', 'CEO', 'CFO', 'CTO',
            'IPO', 'ETF', 'NYSE', 'NASDAQ', 'SEC', 'FDA', 'FED', 'GDP',
            'API', 'AI', 'ML', 'VR', 'AR', 'EV', 'ESG', 'USA', 'UK', 'EU',
            'CEO', 'CFO', 'COO', 'CIO', 'VP', 'EVP', 'SVP', 'MD', 'PM',
            'Q1', 'Q2', 'Q3', 'Q4', 'YOY', 'QOQ', 'MOM', 'YTD', 'MTD'
        }
        
        return {s for s in symbols if s not in false_positives and 2 <= len(s) <= 5}
    
    def _get_company_name(self, symbol: str) -> Optional[str]:
        """Get company name for symbol to improve search quality"""
        company_names = {
            'AAPL': 'Apple',
            'MSFT': 'Microsoft',
            'NVDA': 'NVIDIA',
            'GOOGL': 'Google',
            'GOOG': 'Google',
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
            'INTU': 'Intuit',
            'AMAT': 'Applied Materials',
            'MU': 'Micron',
            'LRCX': 'Lam Research',
            'PANW': 'Palo Alto Networks'
        }
        return company_names.get(symbol.upper())
    
    async def __aenter__(self):
        """Async context manager entry"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - cleanup session"""
        await self.close()
