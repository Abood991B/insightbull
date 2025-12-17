"""
FinHub Data Collector
====================

Collects financial news and company data using FinHub API.
Provides real-time and historical financial news.

Following FYP Report specification:
- Financial news collection from professional sources
- Company-specific news filtering
- Market data integration
"""

from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import asyncio
from app.utils.timezone import utc_now

try:
    import finnhub
    FINNHUB_AVAILABLE = True
except ImportError:
    FINNHUB_AVAILABLE = False
    finnhub = None

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


class FinHubCollector(BaseCollector):
    """
    FinHub API collector for financial news and market data.
    
    Features:
    - Company news collection
    - Market news aggregation  
    - Real-time and historical data
    - Professional financial sources
    """
    
    def __init__(self, api_key: str, rate_limiter=None):
        """
        Initialize FinHub collector.
        
        Args:
            api_key: FinHub API key
            rate_limiter: Rate limiting handler
        """
        super().__init__(api_key=api_key, rate_limiter=rate_limiter)
        
        if not FINNHUB_AVAILABLE:
            self.logger.warning("finnhub library not available. Using HTTP client fallback.")
            self._client = None
        else:
            self._client = finnhub.Client(api_key=api_key)
        
        self.base_url = "https://finnhub.io/api/v1"
        
    @property
    def source(self) -> DataSource:
        return DataSource.FINNHUB
    
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
        """Validate FinHub API connection"""
        try:
            # Test API with a simple quote request
            url = f"{self.base_url}/quote"
            params = {
                "symbol": "AAPL",
                "token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                return response.status_code == 200 and response.json().get("c") is not None
                
        except Exception as e:
            self.logger.error(f"FinHub connection validation failed: {str(e)}")
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect financial news from FinHub.
        
        Args:
            config: Collection configuration
            
        Returns:
            CollectionResult with collected news data
        """
        start_time = utc_now()
        collected_data = []
        
        try:
            self._validate_config(config)
            
            # Use batch collection if multiple symbols (more efficient)
            if len(config.symbols) > 1:
                collected_data = await self._collect_batch(config.symbols, config)
            else:
                # Single symbol collection
                await self._apply_rate_limit()
                symbol_data = await self._collect_company_news(config.symbols[0], config)
                collected_data = symbol_data[:config.max_items_per_symbol]
            
            execution_time = (utc_now() - start_time).total_seconds()
            
            return CollectionResult(
                source=self.source,
                success=True,
                data=collected_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (utc_now() - start_time).total_seconds()
            error_msg = f"FinHub collection failed: {str(e)}"
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
        Collect news for multiple symbols in parallel with smart batching.
        
        Args:
            symbols: List of stock symbols
            config: Collection configuration
            
        Returns:
            List of collected news data
        """
        collected_data = []
        
        # Process symbols in parallel batches of 5 (FinHub handles this well)
        batch_size = 5
        tasks = []
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]
            
            # Create parallel tasks for this batch
            for symbol in batch:
                tasks.append(self._collect_symbol_with_limit(symbol, config))
            
            # Wait for batch to complete before starting next batch (respects rate limits)
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Batch collection error: {str(result)}")
                    continue
                if isinstance(result, list):
                    collected_data.extend(result)
            
            # Clear tasks for next batch
            tasks = []
        
        return collected_data
    
    async def _collect_symbol_with_limit(
        self, 
        symbol: str, 
        config: CollectionConfig, 
        max_retries: int = 3
    ) -> List[RawData]:
        """Collect news for a single symbol with rate limiting and retry logic"""
        for attempt in range(max_retries):
            try:
                await self._apply_rate_limit()
                symbol_data = await self._collect_company_news(symbol, config)
                return symbol_data[:config.max_items_per_symbol]
            except Exception as e:
                if attempt < max_retries - 1:
                    # Exponential backoff: 2^attempt seconds (1s, 2s, 4s)
                    delay = 2 ** attempt
                    self.logger.warning(
                        f"FinHub collection failed for {symbol} (attempt {attempt + 1}/{max_retries}): {str(e)}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"FinHub collection failed for {symbol} after {max_retries} attempts: {str(e)}")
                    return []  # Return empty list on final failure
        return []
    
    async def _collect_company_news(self, symbol: str, config: CollectionConfig) -> List[RawData]:
        """Collect company-specific news"""
        collected_data = []
        
        try:
            # Format dates for API
            from_date = config.date_range.start_date.strftime("%Y-%m-%d")
            to_date = config.date_range.end_date.strftime("%Y-%m-%d")
            
            url = f"{self.base_url}/company-news"
            params = {
                "symbol": symbol.upper(),
                "from": from_date,
                "to": to_date,
                "token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                
                if not isinstance(news_data, list):
                    self.logger.warning(f"Unexpected response format for {symbol}")
                    return collected_data
                
                for item in news_data[:config.max_items_per_symbol]:
                    try:
                        article_data = self._parse_news_item(item, symbol, "company_news")
                        if article_data:
                            collected_data.append(article_data)
                    except Exception as e:
                        self.logger.warning(f"Error parsing news item for {symbol}: {str(e)}")
                        continue
            
            # Log at debug level to reduce noise (summary logged at end of collection)
            self.logger.debug(f"Collected {len(collected_data)} news items for {symbol}")
            
        except Exception as e:
            self.logger.error(f"Error collecting company news for {symbol}: {str(e)}")
        
        return collected_data
    
    async def _collect_market_news(self, config: CollectionConfig) -> List[RawData]:
        """Collect general market news"""
        collected_data = []
        
        try:
            url = f"{self.base_url}/news"
            params = {
                "category": "general",
                "token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                news_data = response.json()
                
                if not isinstance(news_data, list):
                    self.logger.warning("Unexpected response format for market news")
                    return collected_data
                
                # Filter market news by date and relevance
                relevant_news = []
                for item in news_data:
                    try:
                        news_time = datetime.fromtimestamp(item.get("datetime", 0), tz=timezone.utc)
                        if config.date_range.start_date <= news_time <= config.date_range.end_date:
                            # Check if news mentions any target symbols
                            headline = item.get("headline", "").upper()
                            summary = item.get("summary", "").upper()
                            
                            for symbol in config.symbols:
                                if symbol.upper() in headline or symbol.upper() in summary:
                                    article_data = self._parse_news_item(item, symbol, "market_news")
                                    if article_data:
                                        relevant_news.append(article_data)
                                    break
                    except Exception as e:
                        self.logger.warning(f"Error filtering market news: {str(e)}")
                        continue
                
                # Limit results
                collected_data = relevant_news[:config.max_items_per_symbol]
            
            self.logger.info(f"Collected {len(collected_data)} relevant market news items")
            
        except Exception as e:
            self.logger.error(f"Error collecting market news: {str(e)}")
        
        return collected_data
    
    def _parse_news_item(self, item: Dict[str, Any], symbol: str, content_type: str) -> Optional[RawData]:
        """Parse a news item into RawData format"""
        try:
            headline = item.get("headline", "")
            summary = item.get("summary", "")
            
            if not headline:
                return None
            
            # Combine headline and summary
            text = headline
            if summary and summary != headline:
                text += f"\n\n{summary}"
            
            # Parse timestamp
            timestamp = datetime.fromtimestamp(
                item.get("datetime", 0), 
                tz=timezone.utc
            )
            
            return self._create_raw_data(
                content_type=content_type,
                text=text,
                timestamp=timestamp,
                stock_symbol=symbol.upper(),
                url=item.get("url", ""),
                metadata={
                    "title": headline,  # Store headline as title for database insertion
                    "author": item.get("source", ""),  # Use source as author (e.g., "Reuters")
                    "source": item.get("source", ""),
                    "category": item.get("category", ""),
                    "related": item.get("related", ""),
                    "image": item.get("image", ""),
                    "finnhub_id": item.get("id", ""),
                    "all_symbols": [symbol.upper()]  # Store symbols for stock_mentions column
                }
            )
            
        except Exception as e:
            self.logger.warning(f"Error parsing news item: {str(e)}")
            return None
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get current stock quote (bonus feature for integration).
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock quote data or None if failed
        """
        try:
            await self._apply_rate_limit()
            
            url = f"{self.base_url}/quote"
            params = {
                "symbol": symbol.upper(),
                "token": self.api_key
            }
            
            async with self._get_http_client() as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                quote_data = response.json()
                
                return {
                    "symbol": symbol.upper(),
                    "current_price": quote_data.get("c"),
                    "high": quote_data.get("h"),
                    "low": quote_data.get("l"),
                    "open": quote_data.get("o"),
                    "previous_close": quote_data.get("pc"),
                    "timestamp": utc_now().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Error getting quote for {symbol}: {str(e)}")
            return None
    
