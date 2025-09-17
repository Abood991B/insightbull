"""
Reddit Data Collector
====================

Collects posts and comments from finance-related subreddits using PRAW.
Filters conte        try:
            # Use async context manager for Reddit client
            async with self._get_reddit_client() as reddit:
                # Convert symbols to uppercase for consistent matching
                target_symbols = {symbol.upper() for symbol in config.symbols}
                
                # Collect from each subreddit
                for subreddit_name in self.FINANCE_SUBREDDITS:
                    subreddit_data = await self._collect_from_subreddit(
                        reddit, subreddit_name, target_symbols, config
                    )
                    collected_data.extend(subreddit_data)
                    
                    # Apply rate limiting between subreddits
                    if self.rate_limiter:
                        await asyncio.sleep(0.5)  # Small delay between subredditsols and applies quality filters.

Following FYP Report specification:
- Multi-source data collection from social media
- Content filtering by stock symbols
- Quality control and data validation
"""

import re
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set, TYPE_CHECKING
import asyncio
import logging

try:
    import asyncpraw
    from asyncpraw.exceptions import AsyncPRAWException
    ASYNCPRAW_AVAILABLE = True
except ImportError:
    ASYNCPRAW_AVAILABLE = False
    asyncpraw = None
    AsyncPRAWException = Exception

if TYPE_CHECKING and ASYNCPRAW_AVAILABLE:
    from asyncpraw import Reddit

from .base_collector import (
    BaseCollector, 
    DataSource, 
    RawData, 
    CollectionConfig, 
    CollectionResult,
    CollectionError
)

logger = logging.getLogger(__name__)


class RedditCollector(BaseCollector):
    """
    Reddit data collector using PRAW (Python Reddit API Wrapper).
    
    Collects posts and comments from finance subreddits:
    - r/stocks, r/investing, r/SecurityAnalysis
    - r/ValueInvesting, r/financialindependence
    - r/StockMarket, r/pennystocks
    """
    
    # Finance-related subreddits to monitor
    FINANCE_SUBREDDITS = [
        "stocks",
        "investing", 
        "SecurityAnalysis",
        "ValueInvesting",
        "StockMarket",
        "financialindependence",
        "pennystocks",
        "SecurityAnalysis",
        "ValueInvesting"
    ]
    
    def __init__(self, client_id: str, client_secret: str, user_agent: str, rate_limiter=None):
        """
        Initialize Reddit collector with API credentials.
        
        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret  
            user_agent: User agent string for API requests
            rate_limiter: Rate limiting handler
        """
        super().__init__(api_key=f"{client_id}:{client_secret}", rate_limiter=rate_limiter)
        
        if not ASYNCPRAW_AVAILABLE:
            raise ImportError("asyncpraw library is required for Reddit collection. Install with: pip install asyncpraw")
        
        self.client_id = client_id
        self.client_secret = client_secret
        self.user_agent = user_agent
        
        # Compile regex patterns for stock symbol detection
        self._stock_patterns = [
            re.compile(r'\$([A-Z]{1,5})\b'),  # $AAPL format
            re.compile(r'\b([A-Z]{2,5})\b'),  # AAPL format (2-5 chars to avoid false positives)
        ]
        
    @property
    def source(self) -> DataSource:
        return DataSource.REDDIT
    
    @property 
    def requires_api_key(self) -> bool:
        return True
    
    def _get_reddit_client(self):
        """Create async Reddit client instance"""
        return asyncpraw.Reddit(
            client_id=self.client_id,
            client_secret=self.client_secret,
            user_agent=self.user_agent,
            read_only=True  # We only need read access
        )
    
    async def validate_connection(self) -> bool:
        """Validate Reddit API connection"""
        try:
            async with self._get_reddit_client() as reddit:
                # Test connection by accessing user info
                user = await reddit.user.me()
                return True
        except Exception as e:
            self.logger.error(f"Reddit connection validation failed: {str(e)}")
            return False
    
    async def collect_data(self, config: CollectionConfig) -> CollectionResult:
        """
        Collect posts and comments from Reddit.
        
        Args:
            config: Collection configuration
            
        Returns:
            CollectionResult with collected data
        """
        start_time = datetime.utcnow()
        collected_data = []
        
        try:
            self._validate_config(config)
            await self._apply_rate_limit()
            
            reddit = self._get_reddit_client()
            
            # Collect data for each symbol individually to ensure equal distribution
            for symbol in config.symbols:
                symbol_data = await self._collect_for_symbol(reddit, symbol.upper(), config)
                collected_data.extend(symbol_data)
                
                # Apply rate limiting between symbols
                if self.rate_limiter:
                    await asyncio.sleep(0.3)
            
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            return CollectionResult(
                source=self.source,
                success=True,
                data=collected_data,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            error_msg = f"Reddit collection failed: {str(e)}"
            self.logger.error(error_msg)
            
            return CollectionResult(
                source=self.source,
                success=False,
                data=[],
                error_message=error_msg,
                execution_time=execution_time
            )
    
    async def _collect_for_symbol(
        self,
        reddit: Any,
        symbol: str,
        config: CollectionConfig
    ) -> List[RawData]:
        """Collect data for a specific symbol to ensure equal distribution"""
        collected_data = []
        items_collected = 0
        max_items = config.max_items_per_symbol
        
        try:
            # Search across all finance subreddits for this specific symbol
            for subreddit_name in self.FINANCE_SUBREDDITS:
                if items_collected >= max_items:
                    break
                    
                subreddit_data = await self._collect_from_subreddit_for_symbol(
                    reddit, subreddit_name, symbol, config, max_items - items_collected
                )
                collected_data.extend(subreddit_data)
                items_collected += len(subreddit_data)
                
                # Small delay between subreddits
                await asyncio.sleep(0.2)
                
        except Exception as e:
            self.logger.warning(f"Error collecting Reddit data for {symbol}: {str(e)}")
        
        return collected_data[:max_items]  # Ensure we don't exceed the limit
    
    async def _collect_from_subreddit_for_symbol(
        self,
        reddit: Any,
        subreddit_name: str,
        target_symbol: str,
        config: CollectionConfig,
        max_items: int
    ) -> List[RawData]:
        """Collect data from a subreddit for a specific symbol"""
        collected_data = []
        
        try:
            subreddit = await reddit.subreddit(subreddit_name)
            
            # Search for posts mentioning the specific symbol
            search_query = f"{target_symbol} OR ${target_symbol}"
            
            # Get recent posts
            posts = subreddit.search(search_query, sort='new', time_filter='week', limit=max_items * 2)
            
            async for post in posts:
                if len(collected_data) >= max_items:
                    break
                    
                try:
                    # Since we already searched for this symbol, just verify it's mentioned
                    post_text = f"{post.title} {post.selftext or ''}".upper()
                    
                    # Simple check - if we found it in search, it should be valid
                    if target_symbol.upper() in post_text or f"${target_symbol.upper()}" in post_text:
                        post_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                        
                        # Check date range
                        start_date = config.date_range.start_date
                        end_date = config.date_range.end_date
                        
                        if start_date.tzinfo is None:
                            start_date = start_date.replace(tzinfo=timezone.utc)
                        if end_date.tzinfo is None:
                            end_date = end_date.replace(tzinfo=timezone.utc)
                        
                        if start_date <= post_time <= end_date:
                            post_raw_data = self._create_raw_data(
                                content_type="post",
                                text=f"{post.title}\\n\\n{post.selftext or ''}",
                                timestamp=post_time,
                                stock_symbol=target_symbol,
                                url=f"https://reddit.com{post.permalink}",
                                metadata={
                                    "subreddit": subreddit_name,
                                    "author": str(post.author) if post.author else "[deleted]",
                                    "score": post.score,
                                    "num_comments": post.num_comments
                                }
                            )
                            collected_data.append(post_raw_data)
                            
                except Exception as e:
                    self.logger.debug(f"Error processing post: {str(e)}")
                    continue
                    
        except Exception as e:
            self.logger.warning(f"Error collecting from r/{subreddit_name} for {target_symbol}: {str(e)}")
        
        return collected_data
    
    async def _collect_from_subreddit(
        self, 
        reddit: Any, 
        subreddit_name: str,
        target_symbols: Set[str],
        config: CollectionConfig
    ) -> List[RawData]:
        """Collect data from a specific subreddit"""
        collected_data = []
        
        try:
            subreddit = await reddit.subreddit(subreddit_name)
            
            # Get recent posts (hot, new, top) - asyncpraw requires async iteration
            hot_posts = []
            new_posts = []
            
            # Collect hot posts
            async for post in subreddit.hot(limit=50):
                hot_posts.append(post)
            
            # Collect new posts
            async for post in subreddit.new(limit=50):
                new_posts.append(post)
            
            posts = hot_posts + new_posts
            
            for post in posts:
                try:
                    # Check if post is within date range
                    post_time = datetime.fromtimestamp(post.created_utc, tz=timezone.utc)
                    
                    # Ensure both datetimes are timezone-aware for comparison
                    start_date = config.date_range.start_date
                    end_date = config.date_range.end_date
                    
                    # Convert to timezone-aware if needed
                    if start_date.tzinfo is None:
                        start_date = start_date.replace(tzinfo=timezone.utc)
                    if end_date.tzinfo is None:
                        end_date = end_date.replace(tzinfo=timezone.utc)
                    
                    if not (start_date <= post_time <= end_date):
                        continue
                    
                    # Check minimum score if specified
                    if config.min_score and post.score < config.min_score:
                        continue
                    
                    # Extract stock symbols from post
                    post_symbols = self._extract_stock_symbols(post.title + " " + (post.selftext or ""))
                    matching_symbols = post_symbols.intersection(target_symbols)
                    
                    if matching_symbols:
                        # Create raw data for post
                        post_data = self._create_raw_data(
                            content_type="post",
                            text=f"{post.title}\n\n{post.selftext or ''}",
                            timestamp=post_time,
                            stock_symbol=list(matching_symbols)[0],  # Use first matching symbol
                            url=f"https://reddit.com{post.permalink}",
                            metadata={
                                "subreddit": subreddit_name,
                                "author": str(post.author) if post.author else "[deleted]",
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "upvote_ratio": post.upvote_ratio,
                                "all_symbols": list(matching_symbols)
                            }
                        )
                        collected_data.append(post_data)
                        
                        # Collect comments if enabled
                        if config.include_comments:
                            comment_data = await self._collect_comments(
                                post, matching_symbols, config
                            )
                            collected_data.extend(comment_data)
                
                except Exception as e:
                    self.logger.warning(f"Error processing post {post.id}: {str(e)}")
                    continue
            
            self.logger.info(f"Collected {len(collected_data)} items from r/{subreddit_name}")
            
        except Exception as e:
            self.logger.error(f"Error accessing subreddit r/{subreddit_name}: {str(e)}")
        
        return collected_data
    
    async def _collect_comments(
        self, 
        post, 
        target_symbols: Set[str], 
        config: CollectionConfig
    ) -> List[RawData]:
        """Collect comments from a post - temporarily disabled to avoid API issues"""
        # Temporarily disable comment collection due to Reddit API comment issues
        # Focus on post content which is working perfectly
        self.logger.debug(f"Comment collection disabled for post {post.id} - focusing on post content")
        return []
    
    def _extract_stock_symbols(self, text: str) -> Set[str]:
        """
        Extract stock symbols from text using regex patterns.
        
        Args:
            text: Text to search for stock symbols
            
        Returns:
            Set of detected stock symbols (uppercase)
        """
        if not text:
            return set()
        
        symbols = set()
        
        # Apply each regex pattern
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
            'API', 'AI', 'ML', 'VR', 'AR', 'EV', 'ESG', 'DD', 'TA', 'FA'
        }
        
        # Remove false positives and ensure reasonable length
        filtered_symbols = {
            symbol for symbol in symbols 
            if symbol not in false_positives and 2 <= len(symbol) <= 5
        }
        
        return filtered_symbols