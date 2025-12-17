"""
Database Cleanup Script - Remove Empty and Foreign Language Sentiment Data
===========================================================================

Removes sentiment_data records that are:
1. Empty or near-empty (< 10 chars after cleaning)
2. Foreign language (non-English content)
3. Invalid confidence/score ranges

Run with: python scripts/cleanup_bad_sentiment_data.py
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.data_access.database.connection import get_db_session
from app.data_access.models import SentimentData
from app.infrastructure.log_system import get_logger
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload

logger = get_logger()


async def cleanup_bad_sentiment_data():
    """Remove empty and foreign language sentiment data records."""
    
    from app.data_access.database.connection import init_database
    
    # Initialize database connection
    await init_database()
    
    logger.info("Starting sentiment data cleanup...")
    
    async with get_db_session() as db:
        # 1. Fetch all sentiment data for analysis
        query = select(SentimentData).options(selectinload(SentimentData.stock))
        result = await db.execute(query)
        all_records = result.scalars().all()
        
        logger.info(f"Total sentiment records: {len(all_records)}")
        
        # Track records to delete
        ids_to_delete = []
        reasons = {
            "empty": 0,
            "foreign": 0,
            "invalid_score": 0,
            "invalid_confidence": 0
        }
        
        # 2. Analyze each record
        for record in all_records:
            raw_text = record.raw_text or ""
            
            # Check 1: Empty or near-empty text
            cleaned_text = raw_text.strip()
            if len(cleaned_text) < 10:
                ids_to_delete.append(record.id)
                reasons["empty"] += 1
                logger.debug(f"Empty text: {record.id} - '{cleaned_text[:50]}'")
                continue
            
            # Check 2: Foreign language detection (basic)
            ascii_chars = sum(1 for c in cleaned_text if ord(c) < 128)
            ascii_ratio = ascii_chars / len(cleaned_text) if len(cleaned_text) > 0 else 0
            
            # Foreign characters commonly found in Finnish, German, etc.
            foreign_chars = set('äöüßàâçéèêëîïôûùÿæœåøÅÄÖ')
            has_foreign = any(char in cleaned_text for char in foreign_chars)
            
            if ascii_ratio < 0.85 or has_foreign:
                ids_to_delete.append(record.id)
                reasons["foreign"] += 1
                logger.debug(f"Foreign language: {record.id} - ASCII ratio: {ascii_ratio:.2%}, Has foreign chars: {has_foreign}")
                logger.debug(f"Text preview: '{cleaned_text[:100]}'")
                continue
            
            # Check 3: Invalid score range
            score = float(record.sentiment_score)
            if score < -1.0 or score > 1.0:
                ids_to_delete.append(record.id)
                reasons["invalid_score"] += 1
                logger.debug(f"Invalid score: {record.id} - Score: {score}")
                continue
            
            # Check 4: Invalid confidence range
            confidence = float(record.confidence)
            if confidence < 0.0 or confidence > 1.0:
                ids_to_delete.append(record.id)
                reasons["invalid_confidence"] += 1
                logger.debug(f"Invalid confidence: {record.id} - Confidence: {confidence}")
                continue
        
        # 3. Delete bad records
        if ids_to_delete:
            logger.info(f"Found {len(ids_to_delete)} records to delete:")
            logger.info(f"  - Empty/near-empty: {reasons['empty']}")
            logger.info(f"  - Foreign language: {reasons['foreign']}")
            logger.info(f"  - Invalid score: {reasons['invalid_score']}")
            logger.info(f"  - Invalid confidence: {reasons['invalid_confidence']}")
            
            # Batch delete
            delete_query = delete(SentimentData).where(SentimentData.id.in_(ids_to_delete))
            await db.execute(delete_query)
            await db.commit()
            
            logger.info(f"✓ Deleted {len(ids_to_delete)} bad sentiment records")
        else:
            logger.info("✓ No bad records found - database is clean!")
        
        # 4. Final statistics
        final_query = select(SentimentData)
        final_result = await db.execute(final_query)
        final_count = len(final_result.scalars().all())
        
        logger.info(f"Cleanup complete:")
        logger.info(f"  - Before: {len(all_records)} records")
        logger.info(f"  - After: {final_count} records")
        logger.info(f"  - Deleted: {len(ids_to_delete)} records")


if __name__ == "__main__":
    print("=" * 80)
    print("SENTIMENT DATA CLEANUP SCRIPT")
    print("=" * 80)
    print("This script will remove:")
    print("  1. Empty or near-empty sentiment records (< 10 chars)")
    print("  2. Foreign language content (non-English)")
    print("  3. Invalid confidence/score ranges")
    print("=" * 80)
    print()
    
    confirm = input("Proceed with cleanup? (yes/no): ").strip().lower()
    
    if confirm == "yes":
        asyncio.run(cleanup_bad_sentiment_data())
        print("\n✓ Cleanup completed successfully!")
    else:
        print("\nCleanup cancelled.")
