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
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete, and_
import structlog

from app.data_access.models import Stock, WatchlistEntry
from app.infrastructure.log_system import get_logger

logger = get_logger()


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
                
                watchlist_symbols = [row.symbol for row in result.scalars()]
                
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