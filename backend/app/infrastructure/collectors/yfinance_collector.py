"""
YFinance Data Collector
=======================

Collects financial news using yfinance library (Yahoo Finance).
Provides unlimited free access to stock news data.

Key Features:
- No API key required (completely free and unlimited)
- Direct access to Yahoo Finance news feed
- Returns 10-15 articles per ticker typically
- Includes title, summary, published date, and source

Following FYP Report specification:
- Multi-source data collection from financial sources
- Content filtering by stock symbols
- Quality control and data validation
"""

import re
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import asyncio
from app.utils.timezone import utc_now
from app.infrastructure.log_system import get_logger

try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False
    yf = None

from .base_collector import (
    BaseCollector,
    DataSource,
    RawData,
    CollectionConfig,
    CollectionResult,
    CollectionError
)

# Use centralized logging system
logger = get_logger()


class YFinanceCollector(BaseCollector):
    """
    Yahoo Finance news collector using yfinance library.
    
    Collects news articles for stock symbols from Yahoo Finance.
    No authentication required - completely free and unlimited.
    
    Features:
    - No API key required
    - Unlimited requests
    - Returns ~10-15 articles per symbol
    - Includes title, summary, publish date, publisher
    
    Rate Limiting:
    - No official rate limits
    - Recommended: 1-2 requests per second for courtesy
    """
    
    # Request timeout in seconds
    REQUEST_TIMEOUT = 30
    
    def __init__(self, rate_limiter=None):
        """
        Initialize YFinance collector.
        
        Args:
            rate_limiter: Optional rate limiting handler (recommended for batch operations)
        """
        if not YFINANCE_AVAILABLE:
            raise ImportError(
                "yfinance library is required for YFinanceCollector. "
                "Install with: pip install yfinance"
            )
        
        super().__init__(api_key=None, rate_limiter=rate_limiter)
        
    @property
    def source(self) -> DataSource:
        return DataSource.YFINANCE
    
    @property 
    def requires_api_key(self) -> bool:
        return False
    
    async def close(self):
        """Close any resources (no persistent connections needed for yfinance)"""
        pass
    
    async def validate_connection(self) -> bool:
        """Validate connection to Yahoo Finance by testing a simple query"""
        try:
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _test_connection():
                ticker = yf.Ticker("AAPL")
                news = ticker.news
                return news is not None
            
            is_valid = await loop.run_in_executor(None, _test_connection)
            
            if is_valid:
                logger.info(
                    "YFinance connection validated successfully",
                    component="yfinance_collector",
                    api_endpoint="Yahoo Finance"
                )
            else:
                logger.warning(
                    "YFinance connection test returned no data",
                    component="yfinance_collector"
                )
            return is_valid
            
        except Exception as e:
            logger.error(
                f"YFinance connection validation failed: {str(e)}",
                component="yfinance_collector",
                error_type=type(e).__name__
            )
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect news from Yahoo Finance for configured symbols.
        
        Args:
            config: Collection configuration with symbols and date range
            
        Returns:
            CollectionResult with collected data
        """
        start_time = utc_now()
        collected_data = []
        
        # Log collection start with structured logging
        logger.info(
            f"Starting YFinance data collection for {len(config.symbols)} symbols",
            component="yfinance_collector",
            symbols=config.symbols,
            date_range_start=config.date_range.start_date.isoformat(),
            date_range_end=config.date_range.end_date.isoformat()
        )
        
        try:
            self._validate_config(config)
            await self._apply_rate_limit()
            
            # Collect for each symbol
            error_count = 0
            for symbol in config.symbols:
                try:
                    symbol_data = await self._collect_for_symbol(
                        symbol.upper(),
                        config
                    )
                    collected_data.extend(symbol_data)
                    
                    # Small delay between symbols for courtesy
                    await asyncio.sleep(0.3)
                    
                except Exception as e:
                    error_count += 1
                    logger.warning(
                        f"Error collecting YFinance data for symbol: {symbol}",
                        component="yfinance_collector",
                        symbol=symbol,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    continue
            
            execution_time = (utc_now() - start_time).total_seconds()
            
            # Log collection completion with stats
            logger.info(
                f"YFinance collection complete: {len(collected_data)} items collected",
                component="yfinance_collector",
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
            error_msg = f"YFinance collection failed: {str(e)}"
            
            logger.error(
                error_msg,
                component="yfinance_collector",
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
            # Run yfinance call in executor to avoid blocking
            loop = asyncio.get_event_loop()
            
            def _get_news():
                ticker = yf.Ticker(symbol)
                return ticker.news
            
            news_items = await loop.run_in_executor(None, _get_news)
            
            if not news_items:
                logger.debug(
                    f"No news found for symbol: {symbol}",
                    component="yfinance_collector",
                    symbol=symbol
                )
                return collected_data
            
            # Process each news item
            for item in news_items[:max_items]:
                try:
                    raw_data = self._parse_news_item(item, symbol, config)
                    if raw_data:
                        collected_data.append(raw_data)
                except Exception as e:
                    logger.debug(
                        f"Error parsing news item for {symbol}: {str(e)}",
                        component="yfinance_collector",
                        symbol=symbol
                    )
                    continue
            
            logger.debug(
                f"Collected {len(collected_data)} news items for {symbol}",
                component="yfinance_collector",
                symbol=symbol,
                items_count=len(collected_data)
            )
            
        except Exception as e:
            logger.error(
                f"Error collecting news for {symbol}: {str(e)}",
                component="yfinance_collector",
                symbol=symbol,
                error_type=type(e).__name__
            )
        
        return collected_data
    
    def _parse_news_item(
        self,
        item: Dict[str, Any],
        symbol: str,
        config: CollectionConfig
    ) -> Optional[RawData]:
        """
        Parse a yfinance news item into RawData format.
        
        Args:
            item: News item from yfinance
            symbol: Stock symbol
            config: Collection configuration
            
        Returns:
            RawData object or None if parsing fails
        """
        try:
            # yfinance 0.2.50+ uses nested 'content' structure
            # Earlier versions had flat structure
            content = item.get('content', item)
            
            # Extract title
            title = content.get('title', item.get('title', ''))
            
            # yfinance news items can have different structures
            # Try multiple field names for summary/description
            summary = ''
            for field in ['summary', 'description', 'text']:
                if field in content and content[field]:
                    summary = content[field]
                    break
                elif field in item and item[field]:
                    summary = item[field]
                    break
            
            # Clean HTML from summary if present
            if summary and '<' in summary:
                summary = re.sub(r'<[^>]+>', '', summary)
            
            # Combine title and summary for analysis text
            if summary and summary != title:
                text = f"{title}. {summary}"
            else:
                text = title
            
            if not text or not text.strip():
                return None
            
            # Parse timestamp - check multiple locations
            pub_date = content.get('pubDate', item.get('providerPublishTime'))
            if pub_date:
                # yfinance can return ISO string or Unix timestamp
                if isinstance(pub_date, str):
                    # Parse ISO format string (e.g., '2025-12-09T12:00:52Z')
                    try:
                        timestamp = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                    except ValueError:
                        timestamp = utc_now()
                elif isinstance(pub_date, (int, float)):
                    timestamp = datetime.fromtimestamp(pub_date, tz=timezone.utc)
                elif isinstance(pub_date, datetime):
                    timestamp = pub_date if pub_date.tzinfo else pub_date.replace(tzinfo=timezone.utc)
                else:
                    timestamp = utc_now()
            else:
                timestamp = utc_now()
            
            # Check if within date range
            if config.date_range:
                start_date = config.date_range.start_date
                end_date = config.date_range.end_date
                
                # Make dates timezone-aware if needed
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                
                if not (start_date <= timestamp <= end_date):
                    return None
            
            # Extract URL from nested structure
            canonical_url = content.get('canonicalUrl', {})
            click_url = content.get('clickThroughUrl', {})
            url = canonical_url.get('url', '') or click_url.get('url', '') or item.get('link', item.get('url', ''))
            
            # Extract publisher from nested structure
            provider = content.get('provider', {})
            publisher = provider.get('displayName', item.get('publisher', 'Yahoo Finance'))
            
            # Build metadata
            metadata = {
                'publisher': publisher,
                'type': content.get('contentType', item.get('type', 'news')),
                'uuid': content.get('id', item.get('uuid', '')),
                'related_tickers': item.get('relatedTickers', [symbol]),
                'thumbnail': content.get('thumbnail', item.get('thumbnail', {}))
            }
            
            return RawData(
                source=DataSource.YFINANCE,
                content_type='article',
                text=text.strip(),
                timestamp=timestamp,
                stock_symbol=symbol,
                url=url,
                metadata=metadata
            )
            
        except Exception as e:
            logger.debug(
                f"Failed to parse news item: {str(e)}",
                component="yfinance_collector",
                error_type=type(e).__name__
            )
            return None
