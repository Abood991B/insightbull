"""
Real-time Stock Price Service
=============================

Fetches live stock prices using Yahoo Finance with configurable intervals
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional
import yfinance as yf
from sqlalchemy.orm import Session

from ..data_access.models import StocksWatchlist, StockPrice
from ..data_access.database import get_db_session
logger = logging.getLogger(__name__)


class RealTimeStockPriceService:
    """Service for fetching real-time stock prices using Yahoo Finance."""

    def __init__(self, update_interval: int = 30):
        """
        Initialize the real-time stock price service.

        Args:
            update_interval: Interval in seconds between price updates (default: 30)
        """
        self.update_interval = update_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

        # Rate limiting configuration
        self.max_retries = 3
        self.base_backoff = 1.0  # Base backoff in seconds
        self.max_backoff = 60.0  # Max backoff in seconds
        self.request_count = 0
        self.last_request_time = datetime.now(timezone.utc)

        # Yahoo Finance rate limit: ~2000 requests per hour per IP
        self.hourly_limit = 1800  # Conservative limit (1800 requests/hour)
        self.hourly_window_start = datetime.now(timezone.utc)
        self.hourly_request_count = 0

    async def start(self):
        """Start the real-time price fetching service."""
        if self.is_running:
            logger.warning("Real-time stock price service is already running")
            return

        self.is_running = True
        self._task = asyncio.create_task(self._price_update_loop())
        logger.info(f"Started real-time stock price service with {self.update_interval}s interval")

    async def stop(self):
        """Stop the real-time price fetching service."""
        if not self.is_running:
            logger.warning("Real-time stock price service is not running")
            return

        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped real-time stock price service")

    def _check_request_rate(self):
        """Check and enforce request rate limiting."""
        now = datetime.now(timezone.utc)

        # Reset counter if more than a minute has passed
        if (now - self.last_request_time).total_seconds() > 60:
            self.request_count = 0

        # If we've made too many requests in the last minute, wait
        if self.request_count >= 30:  # Max 30 requests per minute
            sleep_time = 60 - (now - self.last_request_time).total_seconds()
            if sleep_time > 0:
                logger.debug(f"Rate limiting: sleeping for {sleep_time:.1f}s")
                import time
                time.sleep(min(sleep_time, 10))  # Cap sleep at 10 seconds
        
        self.last_request_time = datetime.now(timezone.utc)
    
    async def _check_hourly_rate_limit(self):
        """Check and enforce hourly rate limiting."""
        now = datetime.now(timezone.utc)
        
        # Reset hourly counter if more than an hour has passed
        if (now - self.hourly_window_start).total_seconds() > 3600:
            self.hourly_request_count = 0
            self.hourly_window_start = now
        
        # If we're approaching the hourly limit, add delay
        if self.hourly_request_count >= self.hourly_limit * 0.9:  # 90% of limit
            remaining_time = 3600 - (now - self.hourly_window_start).total_seconds()
            if remaining_time > 0:
                logger.warning(f"Approaching hourly rate limit ({self.hourly_request_count}/{self.hourly_limit}). "
                             f"Waiting {remaining_time:.0f}s until reset.")
                await asyncio.sleep(min(remaining_time, 300))  # Wait up to 5 minutes
        
    async def _price_update_loop(self):
        """Main loop for fetching and updating stock prices."""
        try:
            while self.is_running:
                # Check if it's market hours before fetching
                if self.is_market_hours():
                    await self._fetch_and_update_prices()
                    logger.debug("Fetched prices during market hours")
                else:
                    logger.debug("Skipping price fetch - outside market hours")
                
                await asyncio.sleep(self.update_interval)
        except asyncio.CancelledError:
            logger.info("Real-time price update loop cancelled")
        except Exception as e:
            logger.error(f"Error in real-time price update loop: {e}")
            
    async def _fetch_and_update_prices(self):
        """Fetch current prices for all watchlist stocks and update database."""
        try:
            async with get_db_session() as db:
                # Get all active stocks from watchlist
                from sqlalchemy import select
                result = await db.execute(
                    select(StocksWatchlist).filter(StocksWatchlist.is_active == True)
                )
                active_stocks = result.scalars().all()
                
                if not active_stocks:
                    logger.debug("No active stocks in watchlist")
                    return
                    
                symbols = [stock.symbol for stock in active_stocks]
                logger.debug(f"Fetching prices for {len(symbols)} symbols")
                
                # Fetch prices using yfinance
                price_data = await self._get_yahoo_prices(symbols)
                
                # Update database with new prices
                await self._update_stock_prices(db, active_stocks, price_data)
                
        except Exception as e:
            logger.error(f"Error fetching and updating stock prices: {e}")
            
    async def _get_yahoo_prices(self, symbols: List[str]) -> dict:
        """
        Fetch current prices from Yahoo Finance with rate limiting and retry logic.
        
        Args:
            symbols: List of stock symbols to fetch
            
        Returns:
            Dictionary mapping symbols to price data
        """
        try:
            # Check hourly rate limit
            await self._check_hourly_rate_limit()
            
            # Run yfinance in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            
            def fetch_prices():
                price_data = {}
                for symbol in symbols:
                    try:
                        # Check if we need to wait due to rate limiting
                        self._check_request_rate()
                        
                        ticker = yf.Ticker(symbol)
                        # Try to get info with timeout
                        info = ticker.info
                        
                        # Get current price (try different fields)
                        current_price = (
                            info.get('currentPrice') or 
                            info.get('regularMarketPrice') or
                            info.get('previousClose')
                        )
                        
                        if current_price:
                            price_data[symbol] = {
                                'current_price': float(current_price),
                                'previous_close': float(info.get('previousClose', current_price)),
                                'open_price': float(info.get('regularMarketOpen', current_price)),
                                'high_price': float(info.get('dayHigh', current_price)),
                                'low_price': float(info.get('dayLow', current_price)),
                                'volume': int(info.get('volume', 0)),
                            }
                            self.request_count += 1
                            self.hourly_request_count += 1
                        else:
                            logger.warning(f"No price data available for {symbol}")
                            
                    except Exception as e:
                        logger.warning(f"Error fetching price for {symbol}: {e}")
                        continue  # Continue with other symbols
                        
                return price_data
                
            # Retry with exponential backoff
            for attempt in range(self.max_retries):
                try:
                    return await loop.run_in_executor(None, fetch_prices)
                except Exception as e:
                    if attempt == self.max_retries - 1:
                        logger.error(f"Failed to fetch prices after {self.max_retries} attempts: {e}")
                        return {}
                    
                    backoff_time = min(self.base_backoff * (2 ** attempt), self.max_backoff)
                    logger.warning(f"Price fetch attempt {attempt + 1} failed, retrying in {backoff_time}s: {e}")
                    await asyncio.sleep(backoff_time)
            
            return {}
            
        except Exception as e:
            logger.error(f"Error in Yahoo Finance price fetch: {e}")
            # Fallback to mock data for testing when Yahoo Finance is unavailable
            return self._generate_mock_prices(symbols)
            
    async def _update_stock_prices(self, db: Session, stocks: List[StocksWatchlist], price_data: dict):
        """
        Update stock prices in the database.
        
        Args:
            db: Database session
            stocks: List of stock objects
            price_data: Dictionary of price data by symbol
        """
        try:
            for stock in stocks:
                if stock.symbol not in price_data:
                    continue
                    
                data = price_data[stock.symbol]
                
                # Calculate change and change percentage with proper decimal precision
                from decimal import Decimal, ROUND_HALF_UP
                
                current_price = Decimal(str(data['current_price'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                previous_close = Decimal(str(data['previous_close'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) if data['previous_close'] else Decimal('0.00')
                
                # Calculate change from previous close
                change = (current_price - previous_close) if previous_close else Decimal('0.00')
                change_percent = (change / previous_close * 100) if previous_close and previous_close != 0 else Decimal('0.00')
                
                # Round to appropriate decimal places
                change = change.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                change_percent = change_percent.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                
                # Create new stock price record
                stock_price = StockPrice(
                    stock_id=stock.id,
                    symbol=stock.symbol,  # Add symbol for easier querying
                    name=stock.name,      # Add company name for better readability
                    price=current_price,
                    open_price=Decimal(str(data['open_price'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    close_price=previous_close,
                    high_price=Decimal(str(data['high_price'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    low_price=Decimal(str(data['low_price'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
                    volume=data['volume'],
                    change=change,  # Add calculated change
                    change_percent=change_percent,  # Add calculated change percentage
                    timestamp=datetime.now(timezone.utc)
                )
                
                db.add(stock_price)
                
                # Update the stock's current price for quick access
                stock.current_price = data['current_price']
                
            await db.commit()
            logger.info(f"Updated prices for {len(price_data)} stocks")
            
        except Exception as e:
            logger.error(f"Error updating stock prices in database: {e}")
            await db.rollback()
            
    async def fetch_single_stock_price(self, symbol: str) -> Optional[dict]:
        """
        Fetch current price for a single stock symbol.
        
        Args:
            symbol: Stock symbol to fetch
            
        Returns:
            Price data dictionary or None if failed
        """
        try:
            price_data = await self._get_yahoo_prices([symbol])
            return price_data.get(symbol)
        except Exception as e:
            logger.error(f"Error fetching single stock price for {symbol}: {e}")
            return None
    
    def get_service_status(self) -> dict:
        """
        Get current service status and configuration.
        
        Returns:
            Dictionary with service status information
        """
        try:
            # Get active stock count
            async def get_stock_count():
                try:
                    async with get_db_session() as db:
                        from sqlalchemy import select, func
                        result = await db.execute(
                            select(func.count()).select_from(StocksWatchlist).filter(StocksWatchlist.is_active == True)
                        )
                        return result.scalar()
                except Exception as e:
                    logger.error(f"Error getting stock count: {e}")
                    return 0
            
            # Run async function synchronously for status
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                active_stocks = loop.run_until_complete(get_stock_count())
            except:
                active_stocks = 0
            
            # Calculate next market open time
            next_market_open = self._get_next_market_open()
            
            return {
                "service_name": "Real-time Stock Price Service",
                "is_running": self.is_running,
                "update_interval": self.update_interval,
                "market_hours_only": True,
                "current_market_status": "open" if self.is_market_hours() else "closed",
                "next_market_open": next_market_open.isoformat() if next_market_open else None,
                "active_stocks_count": active_stocks,
                "rate_limiting": {
                    "requests_per_minute": 30,
                    "requests_per_hour": self.hourly_limit,
                    "current_hour_count": self.hourly_request_count
                },
                "last_request_time": self.last_request_time.isoformat() if self.last_request_time else None
            }
        except Exception as e:
            logger.error(f"Error getting service status: {e}")
            return {"error": f"Failed to get service status: {str(e)}"}
    
    def _get_next_market_open(self) -> Optional[datetime]:
        """Calculate the next market open time."""
        try:
            import pytz
            eastern = pytz.timezone('US/Eastern')
            now = datetime.now(pytz.UTC).astimezone(eastern)
            
            # If market is currently open, return tomorrow's open
            if self.is_market_hours():
                next_day = now + timedelta(days=1)
                while next_day.weekday() >= 5:  # Skip weekends
                    next_day += timedelta(days=1)
                return next_day.replace(hour=9, minute=30, second=0, microsecond=0)
            
            # If market is closed, find next open
            next_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            
            # If today's market has already closed, go to next day
            if now.hour >= 16:
                next_open += timedelta(days=1)
            
            # Skip weekends
            while next_open.weekday() >= 5:
                next_open += timedelta(days=1)
            
            return next_open
            
        except Exception as e:
            logger.error(f"Error calculating next market open: {e}")
            return None
    
    async def update_configuration(self, config: dict) -> bool:
        """
        Update service configuration.
        
        Args:
            config: New configuration settings
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if "update_interval" in config:
                new_interval = int(config["update_interval"])
                if 10 <= new_interval <= 300:  # Between 10 seconds and 5 minutes
                    self.update_interval = new_interval
                    logger.info(f"Updated price service interval to {new_interval}s")
                else:
                    logger.warning(f"Invalid update interval: {new_interval}. Must be between 10-300 seconds")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating service configuration: {e}")
            return False
            
    def is_market_hours(self) -> bool:
        """
        Check if it's currently market hours (9:30 AM - 4:00 PM ET, weekdays).
        
        Returns:
            True if market is open, False otherwise
        """
        try:
            import pytz
            
            # Get current time in Eastern timezone (more reliable)
            eastern = pytz.timezone('US/Eastern')
            now = datetime.now(pytz.UTC).astimezone(eastern)
            
            # Log current time for debugging
            logger.debug(f"Market hours check - Current ET time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}, Weekday: {now.weekday()}")
            
            # Check if it's a weekday (0=Monday, 6=Sunday)
            if now.weekday() >= 5:  # Saturday or Sunday
                logger.debug("Market closed - Weekend")
                return False
                
            # Check if it's within market hours (9:30 AM - 4:00 PM ET)
            market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
            
            is_open = market_open <= now <= market_close
            
            if not is_open:
                logger.debug(f"Market closed - Outside hours. Market: {market_open.strftime('%H:%M')}-{market_close.strftime('%H:%M')}, Current: {now.strftime('%H:%M')}")
            else:
                logger.debug(f"Market is OPEN - Current time {now.strftime('%H:%M')} is within market hours")
            
            return is_open
            
        except Exception as e:
            logger.error(f"Error checking market hours: {e}")
            # For safety, return False during errors to avoid unnecessary API calls
            return False
            
    def _generate_mock_prices(self, symbols: List[str]) -> dict:
        """
        Generate mock price data for testing when Yahoo Finance is unavailable.
        
        Args:
            symbols: List of stock symbols
            
        Returns:
            Dictionary of mock price data
        """
        import random
        
        mock_data = {}
        base_prices = {
            'AAPL': 150.0, 'MSFT': 300.0, 'GOOGL': 140.0, 'AMZN': 130.0, 'META': 300.0,
            'AMD': 120.0, 'TSLA': 250.0, 'NVDA': 450.0, 'MU': 80.0, 'ADBE': 500.0
        }
        
        for symbol in symbols:
            base_price = base_prices.get(symbol, 100.0)
            # Add some random variation (±5%)
            variation = random.uniform(-0.05, 0.05)
            current_price = base_price * (1 + variation)
            
            mock_data[symbol] = {
                'current_price': round(current_price, 2),
                'previous_close': round(base_price, 2),
                'open_price': round(base_price * random.uniform(0.98, 1.02), 2),
                'high_price': round(current_price * random.uniform(1.0, 1.03), 2),
                'low_price': round(current_price * random.uniform(0.97, 1.0), 2),
                'volume': random.randint(1000000, 10000000),
            }
            
        logger.info(f"Generated mock price data for {len(mock_data)} symbols")
        return mock_data


# Global instance for the service
price_service = RealTimeStockPriceService()


async def start_price_service():
    """Start the global price service."""
    await price_service.start()


async def stop_price_service():
    """Stop the global price service."""
    await price_service.stop()