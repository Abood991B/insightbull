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
import logging
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

logger = logging.getLogger(__name__)


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
        """Get a fresh HTTP client for each request"""
        return httpx.AsyncClient(timeout=30.0)
    
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
            await self._apply_rate_limit()
            
            # Collect company news for each symbol individually for equal distribution
            for symbol in config.symbols:
                symbol_data = await self._collect_company_news(symbol, config)
                # Limit to max_items_per_symbol to ensure equal distribution
                limited_data = symbol_data[:config.max_items_per_symbol]
                collected_data.extend(limited_data)
                
                # Apply rate limiting between symbols
                if self.rate_limiter:
                    await asyncio.sleep(0.2)
            
            # Skip general market news to focus on target stocks only
            
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
            
            self.logger.info(f"Collected {len(collected_data)} news items for {symbol}")
            
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
                    "source": item.get("source", ""),
                    "category": item.get("category", ""),
                    "related": item.get("related", ""),
                    "image": item.get("image", ""),
                    "finnhub_id": item.get("id", "")
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
    
