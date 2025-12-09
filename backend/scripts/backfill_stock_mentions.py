"""
Backfill Stock Mentions for Existing Sentiment Data
====================================================

This script populates the stock_mentions column for existing sentiment_data records
by looking up the stock symbol from the stocks_watchlist table.

Run with: python scripts/backfill_stock_mentions.py
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select, update
from app.data_access.database.connection import get_db_session, init_database
from app.data_access.models import SentimentData, StocksWatchlist


async def backfill_stock_mentions():
    """Backfill stock_mentions from stocks_watchlist to sentiment_data."""
    
    print("=" * 60)
    print("Backfilling stock_mentions for existing sentiment data")
    print("=" * 60)
    
    # Initialize database first
    await init_database()
    
    async with get_db_session() as db:
        # 1. Build a mapping of stock_id -> stock_symbol
        result = await db.execute(
            select(StocksWatchlist.id, StocksWatchlist.symbol)
        )
        stock_map = {row.id: row.symbol for row in result.all()}
        print(f"Found {len(stock_map)} stocks in watchlist")
        
        # 2. Get all sentiment records without stock_mentions
        result = await db.execute(
            select(SentimentData)
            .where(SentimentData.stock_mentions.is_(None))
        )
        sentiment_records = result.scalars().all()
        
        print(f"Found {len(sentiment_records)} sentiment records without stock_mentions")
        
        if not sentiment_records:
            print("Nothing to backfill!")
            return
        
        updated_count = 0
        
        for sentiment in sentiment_records:
            # Get the stock symbol from the mapping
            stock_symbol = stock_map.get(sentiment.stock_id)
            
            if stock_symbol:
                # Create stock_mentions array with the stock symbol
                stock_mentions = [stock_symbol]
                
                await db.execute(
                    update(SentimentData)
                    .where(SentimentData.id == sentiment.id)
                    .values(stock_mentions=stock_mentions)
                )
                updated_count += 1
        
        await db.commit()
        
        print("-" * 60)
        print(f"Updated {updated_count} sentiment records with stock symbols")
        print(f"Unmatched (missing stock_id): {len(sentiment_records) - updated_count}")
        print("=" * 60)
        print("Backfill complete!")


if __name__ == "__main__":
    asyncio.run(backfill_stock_mentions())
