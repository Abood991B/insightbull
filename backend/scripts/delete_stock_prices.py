"""
Script to delete all data from the stock_prices table.
"""
import asyncio
import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.data_access.database.connection import init_database, get_db_session
from sqlalchemy import text


async def delete_stock_prices():
    """Delete all rows from stock_prices table."""
    try:
        # Initialize database connection
        await init_database()
        
        async with get_db_session() as session:
            result = await session.execute(text('SELECT COUNT(*) FROM stock_prices'))
            count_before = result.scalar()
            print(f"Found {count_before} rows in stock_prices table")
            
            result = await session.execute(text('DELETE FROM stock_prices'))
            await session.commit()
            print(f"✓ Successfully deleted {result.rowcount} rows from stock_prices table")
            return result.rowcount
    except Exception as e:
        print(f"✗ Error deleting data: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(delete_stock_prices())
