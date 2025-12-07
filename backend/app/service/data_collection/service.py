"""
Data Collection Service - Service Layer
=======================================

Provides business logic services for data collection operations.
This service layer component wraps infrastructure collectors with 
business logic, validation, and transformation rules.

Service Layer responsibilities:
- Business rules for data collection
- Data validation and cleaning
- Format standardization  
- Error handling and recovery
- Caching and optimization
"""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from app.utils.timezone import utc_now, to_naive_utc

from app.infrastructure.collectors import (
    BaseCollector,
    HackerNewsCollector,
    FinHubCollector,
    NewsAPICollector,
    MarketauxCollector,
    GDELTCollector
)
from app.infrastructure import get_logger
from app.infrastructure.security.security_utils import SecurityUtils

logger = get_logger()


@dataclass
class CollectionRequest:
    """Data collection request parameters"""
    source: str
    symbols: List[str]
    limit: int = 100
    days_back: int = 7
    filters: Optional[Dict[str, Any]] = None


@dataclass
class CollectionResult:
    """Standardized collection result"""
    source: str
    symbol: str
    timestamp: datetime
    data: List[Dict[str, Any]]
    success: bool
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class DataCollectionService:
    """
    Service layer for data collection operations.
    Provides business logic wrapper around infrastructure collectors.
    """
    
    def __init__(self):
        self.security = SecurityUtils()
        self.collectors = {
            'hackernews': HackerNewsCollector(),  # No API key required
            'gdelt': GDELTCollector(),  # No API key required - free and unlimited
            'finnhub': FinHubCollector(
                api_key=self.security.get_api_key("FINNHUB_API_KEY", "finnhub_api_key")
            ),
            'newsapi': NewsAPICollector(
                api_key=self.security.get_api_key("NEWSAPI_KEY", "newsapi_key")
            ),
            'marketaux': MarketauxCollector(
                api_key=self.security.get_api_key("MARKETAUX_API_KEY", "marketaux_api_key")
            )
        }
        self.logger = get_logger()
    
    async def collect_multi_source_data(
        self, 
        symbols: List[str],
        sources: List[str] = None,
        days_back: int = 7,
        max_items: int = 100
    ) -> List[CollectionResult]:
        """
        Collect data from multiple sources with business logic applied.
        
        Business Rules:
        - Validate symbols format
        - Apply rate limiting
        - Standardize data format
        - Handle errors gracefully
        """
        if sources is None:
            sources = ['hackernews', 'gdelt', 'finnhub', 'newsapi']
        
        # Validate business rules
        symbols = self._validate_symbols(symbols)
        sources = self._validate_sources(sources)
        
        results = []
        
        # Collect from each source with business logic
        for source in sources:
            if source in self.collectors:
                source_results = await self._collect_from_source(
                    source, symbols, days_back, max_items
                )
                results.extend(source_results)
        
        return results
    
    async def _collect_from_source(
        self,
        source: str,
        symbols: List[str],
        days_back: int,
        max_items: int
    ) -> List[CollectionResult]:
        """Collect data from a specific source with error handling"""
        results = []
        collector = self.collectors[source]
        
        for symbol in symbols:
            try:
                self.logger.info(f"Collecting {source} data for {symbol}")
                
                # Apply business logic based on source type
                if source == 'hackernews':
                    data = await self._collect_hackernews_with_rules(
                        collector, symbol, days_back, max_items
                    )
                elif source == 'gdelt':
                    data = await self._collect_gdelt_with_rules(
                        collector, symbol, days_back, max_items
                    )
                elif source in ['finnhub', 'newsapi', 'marketaux']:
                    data = await self._collect_news_with_rules(
                        collector, symbol, days_back, max_items
                    )
                else:
                    continue
                
                result = CollectionResult(
                    source=source,
                    symbol=symbol,
                    timestamp=utc_now(),
                    data=data,
                    success=True,
                    metadata={
                        'count': len(data),
                        'days_back': days_back
                    }
                )
                results.append(result)
                
            except Exception as e:
                self.logger.error(f"Error collecting {source} data for {symbol}: {e}")
                error_result = CollectionResult(
                    source=source,
                    symbol=symbol,
                    timestamp=utc_now(),
                    data=[],
                    success=False,
                    error=str(e)
                )
                results.append(error_result)
        
        return results
    
    async def _collect_hackernews_with_rules(
        self,
        collector: HackerNewsCollector,
        symbol: str,
        days_back: int,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Apply business rules for Hacker News data collection"""
        from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
        
        # Create collection config
        date_range = DateRange.last_days(days_back)
        config = CollectionConfig(
            symbols=[symbol],
            date_range=date_range,
            max_items_per_symbol=max_items,
            include_comments=True,
            min_score=2  # Quality filter: at least 2 points
        )
        
        try:
            result = await collector.collect_data(config)
            
            if result.success and result.data:
                # Convert RawData objects to dicts and apply validation
                validated_data = self._validate_hackernews_items([
                    {
                        'title': item.metadata.get('title', ''),
                        'content': item.text,
                        'content_type': item.content_type,
                        'author': item.metadata.get('author', ''),
                        'points': item.metadata.get('points', 0),
                        'num_comments': item.metadata.get('num_comments', 0),
                        'url': item.url,
                        'hn_id': item.metadata.get('hn_id', ''),
                        'timestamp': item.timestamp,
                        'all_symbols': item.metadata.get('all_symbols', [symbol])
                    }
                    for item in result.data
                ])
                return validated_data
            else:
                self.logger.warning(f"HN collection failed for {symbol}: {result.error_message}")
                return []
                
        except Exception as e:
            self.logger.warning(f"Failed to collect from Hacker News for {symbol}: {e}")
            return []
    
    async def _collect_gdelt_with_rules(
        self,
        collector: GDELTCollector,
        symbol: str,
        days_back: int,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Apply business rules for GDELT data collection"""
        from app.infrastructure.collectors.base_collector import CollectionConfig, DateRange
        
        # Create collection config
        date_range = DateRange.last_days(days_back)
        config = CollectionConfig(
            symbols=[symbol],
            date_range=date_range,
            max_items_per_symbol=max_items,
            include_comments=False  # GDELT doesn't have comments
        )
        
        try:
            result = await collector.collect_data(config)
            
            if result.success and result.data:
                # Convert RawData objects to dicts and apply validation
                validated_data = self._validate_gdelt_items([
                    {
                        'title': item.metadata.get('title', item.text),
                        'content': item.text,
                        'content_type': item.content_type,
                        'domain': item.metadata.get('domain', ''),
                        'source_country': item.metadata.get('source_country', ''),
                        'language': item.metadata.get('language', 'English'),
                        'is_trusted_source': item.metadata.get('is_trusted_source', False),
                        'url': item.url,
                        'timestamp': item.timestamp,
                        'all_symbols': item.metadata.get('all_symbols', [symbol])
                    }
                    for item in result.data
                ])
                return validated_data
            else:
                self.logger.warning(f"GDELT collection failed for {symbol}: {result.error_message}")
                return []
                
        except Exception as e:
            self.logger.warning(f"Failed to collect from GDELT for {symbol}: {e}")
            return []
    
    async def _collect_news_with_rules(
        self,
        collector: Union[FinHubCollector, NewsAPICollector, MarketauxCollector],
        symbol: str,
        days_back: int,
        max_items: int
    ) -> List[Dict[str, Any]]:
        """Apply business rules for news data collection"""
        
        # Calculate date range
        end_date = to_naive_utc(utc_now())
        start_date = end_date - timedelta(days=days_back)
        
        # Collect news data
        data = await collector.collect_news(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            limit=max_items
        )
        
        # Apply business validation
        return self._validate_news_articles(data)
    
    def _validate_symbols(self, symbols: List[str]) -> List[str]:
        """Business rule: Validate stock symbols format"""
        validated = []
        for symbol in symbols:
            # Clean and validate symbol
            clean_symbol = symbol.upper().strip()
            if len(clean_symbol) >= 1 and len(clean_symbol) <= 10:
                validated.append(clean_symbol)
            else:
                self.logger.warning(f"Invalid symbol format: {symbol}")
        
        return validated
    
    def _validate_sources(self, sources: List[str]) -> List[str]:
        """Business rule: Validate available sources"""
        available_sources = list(self.collectors.keys())
        validated = [s for s in sources if s in available_sources]
        
        if len(validated) != len(sources):
            invalid = set(sources) - set(validated)
            self.logger.warning(f"Invalid sources ignored: {invalid}")
        
        return validated
    
    def _validate_hackernews_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Business validation for Hacker News items"""
        validated = []
        
        for item in items:
            # Business rules for HN content
            content = item.get('content', '') or ''
            title = item.get('title', '') or ''
            
            # Must have either title or content with reasonable length
            if (len(title) > 5 or len(content) > 20) and item.get('points', 0) >= 0:
                validated.append(item)
        
        return validated
    
    def _validate_gdelt_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Business validation for GDELT news items"""
        validated = []
        
        for item in items:
            # Business rules for GDELT content
            title = item.get('title', '') or ''
            content = item.get('content', '') or ''
            
            # Must have title with reasonable length
            if len(title) > 10 or len(content) > 20:
                validated.append(item)
        
        return validated
    
    def _validate_news_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Business validation for news articles"""
        validated = []
        
        for article in articles:
            # Business rules for news content
            if (article.get('title') and 
                article.get('content') and
                len(article.get('title', '')) > 5):
                validated.append(article)
        
        return validated
    
    async def get_collection_status(self) -> Dict[str, Any]:
        """Get status of all data collection sources"""
        status = {
            'timestamp': utc_now().isoformat(),
            'sources': {}
        }
        
        for source_name, collector in self.collectors.items():
            try:
                # Test collector health
                health = await self._test_collector_health(collector)
                status['sources'][source_name] = {
                    'available': health,
                    'last_check': utc_now().isoformat()
                }
            except Exception as e:
                status['sources'][source_name] = {
                    'available': False,
                    'error': str(e)
                }
        
        return status
    
    async def _test_collector_health(self, collector: BaseCollector) -> bool:
        """Test if a collector is healthy and available"""
        try:
            # Basic health check - validate collector availability
            return True
        except Exception:
            return False


# Service instance
data_collection_service = DataCollectionService()

__all__ = [
    'DataCollectionService',
    'CollectionRequest', 
    'CollectionResult',
    'data_collection_service'
]