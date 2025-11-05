"""
Script to fetch and update market cap information for all watchlist stocks.
Run this once to populate market_cap field in stocks_watchlist table.
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from app.service.price_service import RealTimeStockPriceService
from app.data_access.database import init_database


async def update_market_caps():
    """Fetch and update market caps for all watchlist stocks."""
    print("=" * 80)
    print("UPDATING MARKET CAP INFORMATION FOR WATCHLIST STOCKS")
    print("=" * 80)
    print()
    
    # Initialize database connection
    print("Initializing database connection...")
    await init_database()
    print("✅ Database connected\n")
    
    # Create price service instance
    price_service = RealTimeStockPriceService()
    
    print("Fetching market cap data from Yahoo Finance...")
    print("This may take a minute as we need to query each stock individually.")
    print()
    
    # Fetch and update
    result = await price_service.fetch_and_update_market_caps()
    
    print()
    print("=" * 80)
    if result.get('success'):
        print("✅ MARKET CAP UPDATE COMPLETED SUCCESSFULLY")
        print("=" * 80)
        print()
        print(f"Updated: {result['updated_count']} / {result['total_stocks']} stocks")
        
        if result.get('failed_symbols'):
            print(f"\n⚠️ Failed to fetch data for: {', '.join(result['failed_symbols'])}")
        
        print()
        print("Market cap categories:")
        print("  - Mega Cap: $200B+")
        print("  - Large Cap: $10B - $200B")
        print("  - Mid Cap: $2B - $10B")
        print("  - Small Cap: < $2B")
    else:
        print("❌ MARKET CAP UPDATE FAILED")
        print("=" * 80)
        print()
        print(f"Error: {result.get('message', 'Unknown error')}")
    
    print()
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(update_market_caps())
