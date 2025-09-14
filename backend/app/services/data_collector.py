"""
Data collection service for fetching data from external APIs
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import aiohttp
import praw
import yfinance as yf
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models import Stock, SentimentData, PriceData, ApiConfig, SystemLog
from config import settings

logger = logging.getLogger(__name__)


class DataCollector:
    """Service for collecting data from various sources"""
    
    def __init__(self):
        self.session = None
        self.api_configs = {}
        
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        await self.load_api_configs()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def load_api_configs(self):
        """Load API configurations from database"""
        from sqlalchemy import select
        
        result = await self.session.execute(select(ApiConfig).where(ApiConfig.enabled == True))
        configs = result.scalars().all()
        
        for config in configs:
            self.api_configs[config.name.lower()] = config
        
        logger.info(f"Loaded {len(self.api_configs)} API configurations")
    
    async def collect_all(self):
        """Collect data from all sources"""
        try:
            # Get active stocks
            from sqlalchemy import select
            result = await self.session.execute(
                select(Stock).where(Stock.is_active == True)
            )
            stocks = result.scalars().all()
            
            logger.info(f"Collecting data for {len(stocks)} stocks")
            
            # Collect from each source in parallel
            tasks = []
            
            if "reddit" in self.api_configs:
                tasks.append(self.collect_reddit_data(stocks))
            
            if "finnhub" in self.api_configs:
                tasks.append(self.collect_finnhub_data(stocks))
            
            if "marketaux" in self.api_configs:
                tasks.append(self.collect_marketaux_data(stocks))
            
            if "newsapi" in self.api_configs:
                tasks.append(self.collect_newsapi_data(stocks))
            
            # Always collect price data
            tasks.append(self.collect_price_data(stocks))
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any errors
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Task {i} failed: {result}")
            
            await self.session.commit()
            logger.info("Data collection completed")
            
        except Exception as e:
            logger.error(f"Data collection failed: {e}")
            await self.session.rollback()
            raise
    
    async def collect_reddit_data(self, stocks: List[Stock]):
        """Collect data from Reddit using PRAW"""
        try:
            config = self.api_configs.get("reddit")
            if not config:
                logger.warning("Reddit API not configured")
                return
            
            # Initialize Reddit client
            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT
            )
            
            subreddits = ["wallstreetbets", "stocks", "investing"]
            
            for stock in stocks[:10]:  # Limit to avoid rate limits
                for subreddit_name in subreddits:
                    try:
                        subreddit = reddit.subreddit(subreddit_name)
                        
                        # Search for stock mentions
                        for submission in subreddit.search(
                            stock.symbol, 
                            time_filter="day", 
                            limit=10
                        ):
                            # Create sentiment data entry (will be analyzed later)
                            sentiment = SentimentData(
                                stock_symbol=stock.symbol,
                                source="reddit",
                                content=f"{submission.title} {submission.selftext[:500]}",
                                sentiment="neutral",  # Placeholder
                                sentiment_score=0,  # Will be calculated
                                source_url=f"https://reddit.com{submission.permalink}",
                                published_at=datetime.fromtimestamp(submission.created_utc)
                            )
                            self.session.add(sentiment)
                        
                        await asyncio.sleep(0.5)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Error collecting Reddit data for {stock.symbol}: {e}")
            
            logger.info("Reddit data collection completed")
            
        except Exception as e:
            logger.error(f"Reddit collection failed: {e}")
            raise
    
    async def collect_finnhub_data(self, stocks: List[Stock]):
        """Collect data from FinnHub API"""
        try:
            config = self.api_configs.get("finnhub")
            if not config or not settings.FINNHUB_API_KEY:
                logger.warning("FinnHub API not configured")
                return
            
            base_url = "https://finnhub.io/api/v1"
            headers = {"X-Finnhub-Token": settings.FINNHUB_API_KEY}
            
            async with aiohttp.ClientSession() as session:
                for stock in stocks[:10]:  # Limit for rate limiting
                    try:
                        # Get company news
                        today = datetime.now().strftime("%Y-%m-%d")
                        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                        
                        url = f"{base_url}/company-news"
                        params = {
                            "symbol": stock.symbol,
                            "from": week_ago,
                            "to": today
                        }
                        
                        async with session.get(url, headers=headers, params=params) as response:
                            if response.status == 200:
                                news = await response.json()
                                
                                for article in news[:5]:  # Limit articles per stock
                                    sentiment = SentimentData(
                                        stock_symbol=stock.symbol,
                                        source="finnhub",
                                        content=f"{article.get('headline', '')} {article.get('summary', '')[:500]}",
                                        sentiment="neutral",  # Placeholder
                                        sentiment_score=0,  # Will be calculated
                                        source_url=article.get('url'),
                                        published_at=datetime.fromtimestamp(article.get('datetime', 0))
                                    )
                                    self.session.add(sentiment)
                        
                        await asyncio.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Error collecting FinnHub data for {stock.symbol}: {e}")
            
            logger.info("FinnHub data collection completed")
            
        except Exception as e:
            logger.error(f"FinnHub collection failed: {e}")
            raise
    
    async def collect_marketaux_data(self, stocks: List[Stock]):
        """Collect data from Marketaux API"""
        try:
            config = self.api_configs.get("marketaux")
            if not config or not settings.MARKETAUX_API_KEY:
                logger.warning("Marketaux API not configured")
                return
            
            base_url = "https://api.marketaux.com/v1/news/all"
            
            async with aiohttp.ClientSession() as session:
                for stock in stocks[:5]:  # Very limited due to free tier
                    try:
                        params = {
                            "api_token": settings.MARKETAUX_API_KEY,
                            "symbols": stock.symbol,
                            "limit": 3
                        }
                        
                        async with session.get(base_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                articles = data.get("data", [])
                                
                                for article in articles:
                                    sentiment = SentimentData(
                                        stock_symbol=stock.symbol,
                                        source="marketaux",
                                        content=f"{article.get('title', '')} {article.get('description', '')[:500]}",
                                        sentiment="neutral",  # Placeholder
                                        sentiment_score=0,  # Will be calculated
                                        source_url=article.get('url'),
                                        published_at=datetime.fromisoformat(
                                            article.get('published_at', '').replace('Z', '+00:00')
                                        )
                                    )
                                    self.session.add(sentiment)
                        
                        await asyncio.sleep(2)  # Rate limiting for free tier
                        
                    except Exception as e:
                        logger.error(f"Error collecting Marketaux data for {stock.symbol}: {e}")
            
            logger.info("Marketaux data collection completed")
            
        except Exception as e:
            logger.error(f"Marketaux collection failed: {e}")
            raise
    
    async def collect_newsapi_data(self, stocks: List[Stock]):
        """Collect data from NewsAPI"""
        try:
            config = self.api_configs.get("newsapi")
            if not config or not settings.NEWSAPI_KEY:
                logger.warning("NewsAPI not configured")
                return
            
            base_url = "https://newsapi.org/v2/everything"
            
            async with aiohttp.ClientSession() as session:
                for stock in stocks[:5]:  # Limited for free tier
                    try:
                        params = {
                            "apiKey": settings.NEWSAPI_KEY,
                            "q": f'"{stock.symbol}" OR "{stock.name}"',
                            "sortBy": "publishedAt",
                            "pageSize": 5,
                            "language": "en"
                        }
                        
                        async with session.get(base_url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                articles = data.get("articles", [])
                                
                                for article in articles:
                                    if article.get("title") and article.get("publishedAt"):
                                        sentiment = SentimentData(
                                            stock_symbol=stock.symbol,
                                            source="newsapi",
                                            content=f"{article.get('title', '')} {article.get('description', '')[:500]}",
                                            sentiment="neutral",  # Placeholder
                                            sentiment_score=0,  # Will be calculated
                                            source_url=article.get('url'),
                                            published_at=datetime.fromisoformat(
                                                article.get('publishedAt', '').replace('Z', '+00:00')
                                            )
                                        )
                                        self.session.add(sentiment)
                        
                        await asyncio.sleep(1)  # Rate limiting
                        
                    except Exception as e:
                        logger.error(f"Error collecting NewsAPI data for {stock.symbol}: {e}")
            
            logger.info("NewsAPI data collection completed")
            
        except Exception as e:
            logger.error(f"NewsAPI collection failed: {e}")
            raise
    
    async def collect_price_data(self, stocks: List[Stock]):
        """Collect price data from Yahoo Finance"""
        try:
            for stock in stocks:
                try:
                    ticker = yf.Ticker(stock.symbol)
                    
                    # Get historical data for the last 7 days
                    hist = ticker.history(period="7d")
                    
                    if not hist.empty:
                        for date, row in hist.iterrows():
                            # Check if price data already exists
                            from sqlalchemy import select, and_
                            existing = await self.session.execute(
                                select(PriceData).where(
                                    and_(
                                        PriceData.stock_symbol == stock.symbol,
                                        PriceData.date == date.date()
                                    )
                                )
                            )
                            
                            if not existing.scalar_one_or_none():
                                price = PriceData(
                                    stock_symbol=stock.symbol,
                                    date=date.date(),
                                    open=float(row['Open']),
                                    high=float(row['High']),
                                    low=float(row['Low']),
                                    close=float(row['Close']),
                                    volume=int(row['Volume'])
                                )
                                self.session.add(price)
                    
                    await asyncio.sleep(0.5)  # Be nice to Yahoo Finance
                    
                except Exception as e:
                    logger.error(f"Error collecting price data for {stock.symbol}: {e}")
            
            logger.info("Price data collection completed")
            
        except Exception as e:
            logger.error(f"Price collection failed: {e}")
            raise
