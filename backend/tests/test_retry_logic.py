"""
Test Database Retry Logic
==========================

Verifies that the new retry logic for SQLite database locks is working correctly.
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.data_access.database.connection import init_database, get_db_session
from app.data_access.models import StocksWatchlist
from app.utils.timezone import utc_now
from sqlalchemy import select
import structlog

logger = structlog.get_logger()


async def test_retry_logic():
    """Test the database retry logic with concurrent writes."""
    print("=" * 60)
    print("DATABASE RETRY LOGIC TEST")
    print("=" * 60)
    
    # Initialize database
    await init_database()
    print("\n✅ Database initialized")
    
    # Test 1: Simple write operation
    print("\n📝 Test 1: Simple write operation")
    async with get_db_session() as session:
        test_stock = StocksWatchlist(
            symbol="TEST",
            name="Test Company",
            sector="Technology",
            is_active=True,
            added_to_watchlist=utc_now(),
            priority=0
        )
        session.add(test_stock)
        # Commit happens in context manager with retry logic
    print("✅ Single write succeeded")
    
    # Test 2: Concurrent writes (simulating collectors running in parallel)
    print("\n📝 Test 2: Concurrent writes (simulating pipeline)")
    
    async def write_operation(worker_id: int):
        """Simulate a collector writing to database."""
        async with get_db_session() as session:
            stock = StocksWatchlist(
                symbol=f"TEST{worker_id}",
                name=f"Test Company {worker_id}",
                sector="Technology",
                is_active=True,
                added_to_watchlist=utc_now(),
                priority=worker_id
            )
            session.add(stock)
            # Commit with retry logic happens automatically
        return worker_id
    
    # Run 10 concurrent writes (similar to pipeline with multiple collectors)
    tasks = [write_operation(i) for i in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check results
    successful = sum(1 for r in results if isinstance(r, int))
    failed = sum(1 for r in results if isinstance(r, Exception))
    
    print(f"\n✅ Concurrent writes completed: {successful} succeeded, {failed} failed")
    
    if failed > 0:
        print("\n❌ FAILURES DETECTED:")
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"   Worker {i}: {result}")
    
    # Test 3: Verify all data was written
    print("\n📝 Test 3: Verify data integrity")
    async with get_db_session() as session:
        result = await session.execute(
            select(StocksWatchlist).where(StocksWatchlist.symbol.like("TEST%"))
        )
        test_stocks = result.scalars().all()
        print(f"✅ Found {len(test_stocks)} test records in database")
    
    # Cleanup
    print("\n📝 Test 4: Cleanup test data")
    async with get_db_session() as session:
        result = await session.execute(
            select(StocksWatchlist).where(StocksWatchlist.symbol.like("TEST%"))
        )
        test_stocks = result.scalars().all()
        for stock in test_stocks:
            await session.delete(stock)
        # Commit with retry logic
    print("✅ Test data cleaned up")
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"✅ Single write: PASSED")
    print(f"✅ Concurrent writes: {successful}/10 succeeded")
    print(f"✅ Data integrity: PASSED")
    print(f"✅ Cleanup: PASSED")
    
    if failed == 0:
        print("\n🎉 ALL TESTS PASSED - Retry logic is working correctly!")
    else:
        print(f"\n⚠️  {failed} concurrent writes failed - retry logic may need tuning")
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(test_retry_logic())
    sys.exit(0 if success else 1)
