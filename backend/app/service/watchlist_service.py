"""
Watchlist Service
================

Service for managing and retrieving dynamic stock watchlist.
Replaces static DEFAULT_TARGET_STOCKS with database-driven watchlist.

This module provides:
- Dynamic stock watchlist retrieval
- Fallback to default stocks if no watchlist exists
- Integration with Observer pattern for real-time updates
- Centralized watchlist management across the application
- Stock company name mapping and validation
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_
import structlog
import aiohttp
import asyncio

from app.data_access.models import Stock, WatchlistEntry
from app.infrastructure.log_system import get_logger

logger = get_logger()

# Comprehensive static mapping for common stocks
COMPANY_NAMES = {
    # Technology - Large Cap
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc. (Class A)",
    "GOOG": "Alphabet Inc. (Class C)",
    "AMZN": "Amazon.com, Inc.",
    "META": "Meta Platforms, Inc.",
    "TSLA": "Tesla, Inc.",
    "NVDA": "NVIDIA Corporation",
    "ADBE": "Adobe Inc.",
    "CRM": "Salesforce, Inc.",
    "ORCL": "Oracle Corporation",
    "NOW": "ServiceNow, Inc.",
    "INTU": "Intuit Inc.",
    
    # Technology - Semiconductors
    "AMD": "Advanced Micro Devices, Inc.",
    "QCOM": "QUALCOMM Incorporated",
    "MU": "Micron Technology, Inc.",
    "TXN": "Texas Instruments Incorporated",
    "AVGO": "Broadcom Inc.",
    "INTC": "Intel Corporation",
    "AMAT": "Applied Materials, Inc.",
    
    # Technology - Software & IT
    "IBM": "International Business Machines Corporation",
    "CSCO": "Cisco Systems, Inc.",
    "PLTR": "Palantir Technologies Inc.",
    "SNOW": "Snowflake Inc.",
    "ZM": "Zoom Video Communications, Inc.",
    "DDOG": "Datadog, Inc.",
    "CRWD": "CrowdStrike Holdings, Inc.",
    
    # Financial Services
    "JPM": "JPMorgan Chase & Co.",
    "BAC": "Bank of America Corporation",
    "WFC": "Wells Fargo & Company",
    "GS": "The Goldman Sachs Group, Inc.",
    "MS": "Morgan Stanley",
    "C": "Citigroup Inc.",
    "V": "Visa Inc.",
    "MA": "Mastercard Incorporated",
    "PYPL": "PayPal Holdings, Inc.",
    "SQ": "Block, Inc.",
    "AXP": "American Express Company",
    "COF": "Capital One Financial Corporation",
    "BLK": "BlackRock, Inc.",
    
    # Healthcare & Biotech
    "JNJ": "Johnson & Johnson",
    "PFE": "Pfizer Inc.",
    "UNH": "UnitedHealth Group Incorporated",
    "MRK": "Merck & Co., Inc.",
    "ABBV": "AbbVie Inc.",
    "TMO": "Thermo Fisher Scientific Inc.",
    "DHR": "Danaher Corporation",
    "BMY": "Bristol-Myers Squibb Company",
    "AMGN": "Amgen Inc.",
    "GILD": "Gilead Sciences, Inc.",
    
    # Consumer & Retail
    "WMT": "Walmart Inc.",
    "PG": "The Procter & Gamble Company",
    "KO": "The Coca-Cola Company",
    "PEP": "PepsiCo, Inc.",
    "NFLX": "Netflix, Inc.",
    "DIS": "The Walt Disney Company",
    "NKE": "Nike, Inc.",
    "SBUX": "Starbucks Corporation",
    "MCD": "McDonald's Corporation",
    "HD": "The Home Depot, Inc.",
    
    # Energy & Utilities
    "XOM": "Exxon Mobil Corporation",
    "CVX": "Chevron Corporation",
    "COP": "ConocoPhillips",
    "SLB": "Schlumberger Limited",
    "KMI": "Kinder Morgan, Inc.",
    "NEE": "NextEra Energy, Inc.",
    
    # Industrial & Manufacturing
    "BA": "The Boeing Company",
    "CAT": "Caterpillar Inc.",
    "GE": "General Electric Company",
    "MMM": "3M Company",
    "LMT": "Lockheed Martin Corporation",
    "RTX": "Raytheon Technologies Corporation",
    
    # Real Estate & REITs
    "AMT": "American Tower Corporation",
    "PLD": "Prologis, Inc.",
    "CCI": "Crown Castle Inc.",
    "EQIX": "Equinix, Inc.",
    "SPG": "Simon Property Group, Inc.",
    
    # Communication Services
    "T": "AT&T Inc.",
    "VZ": "Verizon Communications Inc.",
    "TMUS": "T-Mobile US, Inc.",
    "CHTR": "Charter Communications, Inc.",
    "CMCSA": "Comcast Corporation"
}

# Cache for API lookups to avoid repeated calls
_company_cache: Dict[str, Tuple[str, datetime]] = {}
_cache_duration = timedelta(hours=24)  # Cache for 24 hours


# Default fallback stocks (same as original DEFAULT_TARGET_STOCKS)
DEFAULT_FALLBACK_STOCKS = [
    "NVDA",   # 1. NVIDIA Corporation
    "MSFT",   # 2. Microsoft Corporation  
    "AAPL",   # 3. Apple Inc.
    "AVGO",   # 4. Broadcom Inc.
    "ORCL",   # 5. Oracle Corporation
    "PLTR",   # 6. Palantir Technologies Inc.
    "CSCO",   # 7. Cisco Systems, Inc.
    "AMD",    # 8. Advanced Micro Devices, Inc.
    "IBM",    # 9. International Business Machines Corporation
    "CRM",    # 10. Salesforce, Inc.
    "NOW",    # 11. ServiceNow, Inc.
    "INTU",   # 12. Intuit Inc.
    "QCOM",   # 13. QUALCOMM Incorporated
    "MU",     # 14. Micron Technology, Inc.
    "TXN",    # 15. Texas Instruments Incorporated
    "ADBE",   # 16. Adobe Inc.
    "GOOGL",  # 17. Alphabet Inc. (Class A)
    "AMZN",   # 18. Amazon.com, Inc.
    "META",   # 19. Meta Platforms, Inc.
    "TSLA"    # 20. Tesla, Inc.
]


class WatchlistService:
    """
    Service for managing dynamic stock watchlist
    
    Provides centralized access to the current stock watchlist,
    with fallback to default stocks if no watchlist is configured.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger
    
    async def get_current_watchlist(self) -> List[str]:
        """
        Get the current stock watchlist from database
        
        Returns:
            List of stock symbols in the current watchlist.
            Falls back to DEFAULT_FALLBACK_STOCKS if no watchlist exists.
        """
        try:
            # Check if watchlist table exists and has entries
            watchlist_count = await self.db.scalar(
                select(func.count()).select_from(WatchlistEntry)
            )
            
            if watchlist_count and watchlist_count > 0:
                # Get active watchlist from database
                result = await self.db.execute(
                    select(Stock.symbol)
                    .join(WatchlistEntry, Stock.id == WatchlistEntry.stock_id)
                    .where(WatchlistEntry.is_active == True)
                    .order_by(WatchlistEntry.added_date)
                )
                
                watchlist_symbols = list(result.scalars())
                
                if watchlist_symbols:
                    self.logger.info("Retrieved dynamic watchlist", 
                                   symbol_count=len(watchlist_symbols),
                                   symbols=watchlist_symbols[:5])  # Log first 5 only
                    return watchlist_symbols
            
            # Fallback to default stocks if no watchlist configured
            self.logger.info("Using fallback watchlist", 
                           symbol_count=len(DEFAULT_FALLBACK_STOCKS))
            return DEFAULT_FALLBACK_STOCKS.copy()
            
        except Exception as e:
            self.logger.warning("Error retrieving watchlist, using fallback", 
                              error=str(e))
            return DEFAULT_FALLBACK_STOCKS.copy()
    
    async def get_watchlist_with_metadata(self) -> List[Dict[str, Any]]:
        """
        Get watchlist with full metadata including company names and dates
        
        Returns:
            List of dictionaries containing stock symbol, name, and metadata
        """
        try:
            result = await self.db.execute(
                select(
                    Stock.symbol,
                    Stock.name,
                    WatchlistEntry.added_date,
                    WatchlistEntry.is_active
                )
                .join(WatchlistEntry, Stock.id == WatchlistEntry.stock_id)
                .where(WatchlistEntry.is_active == True)
                .order_by(WatchlistEntry.added_date)
            )
            
            watchlist_data = []
            for row in result:
                watchlist_data.append({
                    "symbol": row.symbol,
                    "name": row.name or f"{row.symbol} Corporation",
                    "added_date": row.added_date,
                    "is_active": row.is_active
                })
            
            return watchlist_data
            
        except Exception as e:
            self.logger.error("Error retrieving watchlist metadata", error=str(e))
            # Return fallback data
            return [
                {
                    "symbol": symbol,
                    "name": f"{symbol} Corporation",
                    "added_date": datetime.utcnow(),
                    "is_active": True
                }
                for symbol in DEFAULT_FALLBACK_STOCKS
            ]
    
    async def add_to_watchlist(self, stock_symbols: List[str]) -> Dict[str, Any]:
        """
        Add stocks to the watchlist
        
        Args:
            stock_symbols: List of stock symbols to add
            
        Returns:
            Dictionary with operation results
        """
        try:
            added_stocks = []
            skipped_stocks = []
            
            for symbol in stock_symbols:
                # Ensure stock exists in stocks table
                stock = await self._ensure_stock_exists(symbol.upper())
                
                # Check if already in watchlist
                existing_entry = await self.db.scalar(
                    select(WatchlistEntry)
                    .where(and_(
                        WatchlistEntry.stock_id == stock.id,
                        WatchlistEntry.is_active == True
                    ))
                )
                
                if existing_entry:
                    skipped_stocks.append(symbol)
                    continue
                
                # Add to watchlist
                watchlist_entry = WatchlistEntry(
                    stock_id=stock.id,
                    added_date=datetime.utcnow(),
                    is_active=True
                )
                self.db.add(watchlist_entry)
                added_stocks.append(symbol)
            
            await self.db.commit()
            
            self.logger.info("Added stocks to watchlist", 
                           added=added_stocks, 
                           skipped=skipped_stocks)
            
            return {
                "added_stocks": added_stocks,
                "skipped_stocks": skipped_stocks,
                "success": True
            }
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error adding stocks to watchlist", error=str(e))
            raise
    
    async def remove_from_watchlist(self, stock_symbols: List[str]) -> Dict[str, Any]:
        """
        Remove stocks from the watchlist
        
        Args:
            stock_symbols: List of stock symbols to remove
            
        Returns:
            Dictionary with operation results
        """
        try:
            removed_stocks = []
            not_found_stocks = []
            
            for symbol in stock_symbols:
                # Find stock
                stock = await self.db.scalar(
                    select(Stock).where(Stock.symbol == symbol.upper())
                )
                
                if not stock:
                    not_found_stocks.append(symbol)
                    continue
                
                # Remove from watchlist (soft delete by setting is_active = False)
                result = await self.db.execute(
                    delete(WatchlistEntry).where(and_(
                        WatchlistEntry.stock_id == stock.id,
                        WatchlistEntry.is_active == True
                    ))
                )
                
                if result.rowcount > 0:
                    removed_stocks.append(symbol)
                else:
                    not_found_stocks.append(symbol)
            
            await self.db.commit()
            
            self.logger.info("Removed stocks from watchlist", 
                           removed=removed_stocks, 
                           not_found=not_found_stocks)
            
            return {
                "removed_stocks": removed_stocks,
                "not_found_stocks": not_found_stocks,
                "success": True
            }
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error removing stocks from watchlist", error=str(e))
            raise
    
    async def clear_watchlist(self) -> Dict[str, Any]:
        """
        Clear all stocks from the watchlist
        
        Returns:
            Dictionary with operation results
        """
        try:
            # Count current entries
            current_count = await self.db.scalar(
                select(func.count()).select_from(WatchlistEntry)
                .where(WatchlistEntry.is_active == True)
            )
            
            # Remove all entries
            await self.db.execute(
                delete(WatchlistEntry).where(WatchlistEntry.is_active == True)
            )
            
            await self.db.commit()
            
            self.logger.info("Cleared watchlist", removed_count=current_count)
            
            return {
                "removed_count": current_count,
                "success": True
            }
            
        except Exception as e:
            await self.db.rollback()
            self.logger.error("Error clearing watchlist", error=str(e))
            raise
    
    async def initialize_default_watchlist(self) -> Dict[str, Any]:
        """
        Initialize watchlist with default stocks if empty
        
        Returns:
            Dictionary with initialization results
        """
        try:
            # Check if watchlist is empty
            current_count = await self.db.scalar(
                select(func.count()).select_from(WatchlistEntry)
                .where(WatchlistEntry.is_active == True)
            )
            
            if current_count and current_count > 0:
                self.logger.info("Watchlist already initialized", current_count=current_count)
                return {"message": "Watchlist already exists", "initialized": False}
            
            # Add default stocks to watchlist
            result = await self.add_to_watchlist(DEFAULT_FALLBACK_STOCKS)
            
            self.logger.info("Initialized default watchlist", 
                           stock_count=len(DEFAULT_FALLBACK_STOCKS))
            
            return {
                "message": "Default watchlist initialized",
                "initialized": True,
                "stock_count": len(result["added_stocks"])
            }
            
        except Exception as e:
            self.logger.error("Error initializing default watchlist", error=str(e))
            raise
    
    async def _ensure_stock_exists(self, symbol: str) -> Stock:
        """
        Ensure stock exists in database, create if necessary
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Stock model instance
        """
        stock = await self.db.scalar(
            select(Stock).where(Stock.symbol == symbol.upper())
        )
        
        if not stock:
            # Create new stock entry
            stock = Stock(
                symbol=symbol.upper(),
                name=f"{symbol.upper()} Corporation",  # Basic name, can be updated later
                created_at=datetime.utcnow()
            )
            self.db.add(stock)
            await self.db.flush()  # Get ID without committing
            
            self.logger.info("Created new stock entry", symbol=symbol)
        
        return stock
    
    # Company Name Service Methods
    @staticmethod
    def is_valid_symbol(symbol: str) -> bool:
        """Check if a stock symbol is valid (exists in our mapping)."""
        symbol = symbol.upper().strip()
        return symbol in COMPANY_NAMES
    
    @staticmethod
    def get_all_symbols() -> dict:
        """Get all available stock symbols with their company names."""
        return COMPANY_NAMES.copy()
    
    @staticmethod
    def search_symbols(query: str) -> dict:
        """Search for stock symbols that match the query."""
        query = query.upper().strip()
        if not query:
            return {}
        
        matches = {}
        for symbol, name in COMPANY_NAMES.items():
            if query in symbol or query in name.upper():
                matches[symbol] = name
        
        return matches
    
    @staticmethod
    def get_sector(symbol: str) -> str:
        """Get sector for a stock symbol."""
        symbol = symbol.upper().strip()
        
        # Technology stocks
        tech_stocks = ["AAPL", "MSFT", "GOOGL", "GOOG", "AMZN", "META", "ADBE", "CRM", "ORCL", "NOW", "INTU", "IBM", "CSCO", "PLTR", "SNOW", "ZM", "DDOG", "CRWD"]
        semiconductor_stocks = ["NVDA", "AMD", "QCOM", "MU", "TXN", "AVGO", "INTC", "AMAT"]
        financial_stocks = ["JPM", "BAC", "WFC", "GS", "MS", "C", "V", "MA", "PYPL", "SQ", "AXP", "COF", "BLK"]
        healthcare_stocks = ["JNJ", "PFE", "ABT", "TMO", "DHR", "BMY", "AMGN", "MDT", "GILD", "VRTX"]
        energy_stocks = ["XOM", "CVX", "COP", "EOG", "SLB", "PXD", "KMI", "OXY", "MPC", "VLO"]
        industrial_stocks = ["BA", "CAT", "DE", "HON", "MMM", "GE", "UNP", "RTX", "LMT", "FDX"]
        
        if symbol in tech_stocks:
            return "Technology"
        elif symbol in semiconductor_stocks:
            return "Technology - Semiconductors"
        elif symbol in financial_stocks:
            return "Financial Services"
        elif symbol in healthcare_stocks:
            return "Healthcare"
        elif symbol in energy_stocks:
            return "Energy"
        elif symbol in industrial_stocks:
            return "Industrials"
        else:
            return "Technology"  # Default
    
    @staticmethod
    def get_company_name(symbol: str) -> str:
        """
        Get company name for a stock symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            
        Returns:
            Company name string
        """
        symbol = symbol.upper().strip()
        
        # First try static mapping
        if symbol in COMPANY_NAMES:
            return COMPANY_NAMES[symbol]
        
        # If not found, return formatted default
        return f"{symbol} Inc."
    
    @staticmethod
    async def validate_and_get_company_name(symbol: str) -> Tuple[bool, str]:
        """
        Validate stock symbol and get company name using external API.
        
        Args:
            symbol: Stock ticker symbol to validate
            
        Returns:
            Tuple of (is_valid, company_name)
        """
        symbol = symbol.upper().strip()
        
        # Check cache first
        if symbol in _company_cache:
            cached_name, cached_time = _company_cache[symbol]
            if datetime.utcnow() - cached_time < _cache_duration:
                return True, cached_name
        
        # Try static mapping first
        if symbol in COMPANY_NAMES:
            company_name = COMPANY_NAMES[symbol]
            _company_cache[symbol] = (company_name, datetime.utcnow())
            return True, company_name
        
        # Try to validate using a free API (Alpha Vantage, Yahoo Finance, etc.)
        try:
            company_name = await WatchlistService._fetch_from_api(symbol)
            if company_name:
                _company_cache[symbol] = (company_name, datetime.utcnow())
                return True, company_name
        except Exception as e:
            logger.warning(f"Failed to validate symbol {symbol} via API: {e}")
        
        # If validation fails, return false but provide a default name
        default_name = f"{symbol} Inc."
        return False, default_name
    
    @staticmethod
    async def _fetch_from_api(symbol: str) -> Optional[str]:
        """
        Fetch company name from external API.
        Using a simple approach that doesn't require API keys.
        """
        try:
            # Using Yahoo Finance API (no key required)
            url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}"
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        if data.get('quotes'):
                            for quote in data['quotes']:
                                if quote.get('symbol', '').upper() == symbol.upper():
                                    return quote.get('longname') or quote.get('shortname')
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching company name for {symbol}: {e}")
            return None
    
    @staticmethod
    def add_company_mapping(symbol: str, company_name: str) -> None:
        """
        Add a new company mapping to the static dictionary.
        
        Args:
            symbol: Stock ticker symbol
            company_name: Full company name
        """
        symbol = symbol.upper().strip()
        COMPANY_NAMES[symbol] = company_name
        logger.info(f"Added company mapping: {symbol} -> {company_name}")
    
    @staticmethod
    def get_all_known_symbols() -> Dict[str, str]:
        """Get all known symbol to company name mappings"""
        return COMPANY_NAMES.copy()


# Global watchlist service factory
async def get_watchlist_service(db: AsyncSession) -> WatchlistService:
    """
    Factory function to create WatchlistService instance
    
    Args:
        db: Database session
        
    Returns:
        WatchlistService instance
    """
    return WatchlistService(db)


# Convenience functions for common operations
async def get_current_stock_symbols(db: AsyncSession) -> List[str]:
    """
    Convenience function to get current watchlist symbols
    
    Args:
        db: Database session
        
    Returns:
        List of stock symbols from current watchlist
    """
    service = await get_watchlist_service(db)
    return await service.get_current_watchlist()


async def get_watchlist_with_details(db: AsyncSession) -> List[Dict[str, Any]]:
    """
    Convenience function to get watchlist with full details
    
    Args:
        db: Database session
        
    Returns:
        List of watchlist entries with metadata
    """
    service = await get_watchlist_service(db)
    return await service.get_watchlist_with_metadata()