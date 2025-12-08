"""
Sentiment Data Re-processing Script
====================================

MAINTENANCE UTILITY - Not required for normal operation.

When to use this script:
- After upgrading/changing the sentiment analysis model
- After enabling AI verification and wanting to apply it to historical data
- After changing confidence thresholds for consistency across all data
- For data quality audits or corrections

This script is NOT needed for:
- Normal pipeline operation (new data is processed automatically)
- Daily/regular usage

What it does:
1. Loads all existing SentimentData records with raw_text
2. Re-analyzes each text using the current SentimentEngine (ProsusAI/finbert + optional Gemini AI)
3. Updates sentiment_score, confidence, sentiment_label, and model_used fields
4. Preserves original metadata and relationships

Usage:
    cd backend
    python scripts/reprocess_sentiment_data.py [--batch-size 50] [--dry-run] [--with-ai]

Options:
    --batch-size: Number of records to process per batch (default: 50)
    --dry-run: Preview changes without committing to database
    --with-ai: Enable Gemini AI verification for uncertain predictions
    --limit: Maximum number of records to process (default: all)

Examples:
    # Preview what would change (safe, no database modifications)
    python scripts/reprocess_sentiment_data.py --dry-run

    # Re-process all data with AI verification
    python scripts/reprocess_sentiment_data.py --with-ai

    # Re-process first 100 records as a test
    python scripts/reprocess_sentiment_data.py --limit 100 --dry-run
"""

import asyncio
import argparse
import sys
import os
from datetime import datetime
from typing import List, Dict, Any, Optional

# Ensure we're running from the backend directory for relative paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.dirname(SCRIPT_DIR)
os.chdir(BACKEND_DIR)

# Load environment variables from .env file BEFORE importing app modules
from dotenv import load_dotenv
load_dotenv(os.path.join(BACKEND_DIR, '.env'))

# Add backend to path
sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.data_access.database import init_database, get_db_session
from app.data_access.models import SentimentData
from app.service.sentiment_processing import (
    SentimentEngine, EngineConfig, TextInput, DataSource, get_sentiment_engine, reset_sentiment_engine
)
from app.utils.timezone import utc_now


class SentimentReprocessor:
    """Re-processes existing sentiment data with the new model pipeline."""
    
    def __init__(
        self, 
        batch_size: int = 50, 
        dry_run: bool = False,
        with_ai: bool = False,
        limit: Optional[int] = None
    ):
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.with_ai = with_ai
        self.limit = limit
        self.stats = {
            "total_records": 0,
            "processed": 0,
            "updated": 0,
            "skipped_no_text": 0,
            "errors": 0,
            "sentiment_changes": {
                "positive_to_negative": 0,
                "positive_to_neutral": 0,
                "negative_to_positive": 0,
                "negative_to_neutral": 0,
                "neutral_to_positive": 0,
                "neutral_to_negative": 0,
                "unchanged": 0
            }
        }
    
    def _map_source_to_datasource(self, source: str) -> DataSource:
        """Map database source string to DataSource enum."""
        source_map = {
            "hackernews": DataSource.HACKERNEWS,
            "finnhub": DataSource.FINNHUB,
            "newsapi": DataSource.NEWSAPI,
            "marketaux": DataSource.MARKETAUX,
            "gdelt": DataSource.GDELT,
            "reddit": DataSource.HACKERNEWS,  # Fallback
        }
        return source_map.get(source.lower(), DataSource.NEWSAPI)
    
    def _track_sentiment_change(self, old_label: str, new_label: str):
        """Track sentiment label changes for statistics."""
        old = old_label.lower() if old_label else "neutral"
        new = new_label.lower()
        
        if old == new:
            self.stats["sentiment_changes"]["unchanged"] += 1
        else:
            key = f"{old}_to_{new}"
            if key in self.stats["sentiment_changes"]:
                self.stats["sentiment_changes"][key] += 1
    
    async def get_total_records(self, db: AsyncSession) -> int:
        """Get total count of records with raw_text."""
        result = await db.execute(
            select(func.count(SentimentData.id))
            .where(SentimentData.raw_text.isnot(None))
            .where(SentimentData.raw_text != "")
        )
        return result.scalar() or 0
    
    async def get_batch(self, db: AsyncSession, offset: int) -> List[SentimentData]:
        """Get a batch of sentiment records to process."""
        query = (
            select(SentimentData)
            .options(selectinload(SentimentData.stock))  # Eagerly load stock relationship
            .where(SentimentData.raw_text.isnot(None))
            .where(SentimentData.raw_text != "")
            .order_by(SentimentData.created_at.desc())
            .offset(offset)
            .limit(self.batch_size)
        )
        result = await db.execute(query)
        return list(result.scalars().all())
    
    async def process_batch(
        self, 
        db: AsyncSession, 
        records: List[SentimentData],
        engine: SentimentEngine
    ) -> int:
        """Process a batch of records and update them."""
        if not records:
            return 0
        
        # Prepare TextInput objects
        text_inputs = []
        valid_records = []
        
        for record in records:
            if not record.raw_text or len(record.raw_text.strip()) < 5:
                self.stats["skipped_no_text"] += 1
                continue
            
            # Get stock symbol from relationship or metadata
            stock_symbol = "UNKNOWN"
            if record.stock and hasattr(record.stock, 'symbol'):
                stock_symbol = record.stock.symbol
            elif record.additional_metadata and isinstance(record.additional_metadata, dict):
                stock_symbol = record.additional_metadata.get('stock_symbol', 'UNKNOWN')
            
            text_input = TextInput(
                text=record.raw_text.strip(),
                source=self._map_source_to_datasource(record.source or "newsapi"),
                stock_symbol=stock_symbol
            )
            text_inputs.append(text_input)
            valid_records.append(record)
        
        if not text_inputs:
            return 0
        
        # Analyze batch with sentiment engine
        try:
            results = await engine.analyze(text_inputs)
        except Exception as e:
            print(f"    Error analyzing batch: {e}")
            self.stats["errors"] += len(valid_records)
            return 0
        
        # Update records
        updated_count = 0
        for record, result in zip(valid_records, results):
            try:
                # Track sentiment change
                old_label = record.sentiment_label or "Neutral"
                new_label = result.label.value.capitalize()
                self._track_sentiment_change(old_label, new_label)
                
                if not self.dry_run:
                    # Update the record
                    record.sentiment_score = result.score
                    record.confidence = result.confidence
                    record.sentiment_label = new_label
                    record.model_used = result.model_name
                    
                    # Update metadata with reprocessing info
                    if record.additional_metadata is None:
                        record.additional_metadata = {}
                    record.additional_metadata["reprocessed_at"] = utc_now().isoformat()
                    record.additional_metadata["reprocessed_model"] = result.model_name
                    if hasattr(result, 'ai_verified') and result.ai_verified:
                        record.additional_metadata["ai_verified"] = True
                
                updated_count += 1
                self.stats["updated"] += 1
                
            except Exception as e:
                print(f"    Error updating record {record.id}: {e}")
                self.stats["errors"] += 1
        
        if not self.dry_run:
            await db.commit()
        
        return updated_count
    
    async def run(self):
        """Main execution method."""
        print("=" * 70)
        print("SENTIMENT DATA RE-PROCESSING SCRIPT")
        print("=" * 70)
        print(f"Mode: {'DRY RUN (no changes)' if self.dry_run else 'LIVE (will update database)'}")
        print(f"AI Verification: {'ENABLED' if self.with_ai else 'DISABLED'}")
        print(f"Batch Size: {self.batch_size}")
        if self.limit:
            print(f"Limit: {self.limit} records")
        print()
        
        # Initialize database
        print("Initializing database connection...")
        await init_database()
        
        # Check if Gemini API key is available
        if self.with_ai:
            print("Checking Gemini API key...")
            try:
                from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader
                key_loader = SecureAPIKeyLoader()
                keys = key_loader.load_api_keys()
                gemini_key = keys.get('gemini_api_key', '')
                if gemini_key:
                    print(f"  Gemini API key found: {gemini_key[:8]}...{gemini_key[-4:]}")
                    # Test Gemini connection
                    import google.generativeai as genai
                    genai.configure(api_key=gemini_key)
                    model = genai.GenerativeModel('gemma-3-27b-it')  # Use Gemma 3 27B for better reasoning
                    print("  Gemma 3 27B API configured successfully (using gemma-3-27b-it)!")
                else:
                    print("  WARNING: No Gemini API key found in secure storage!")
                    print("  AI verification will be disabled. Add key via admin dashboard.")
                    self.with_ai = False
            except Exception as e:
                print(f"  ERROR loading Gemini API key: {e}")
                print("  AI verification will be disabled.")
                self.with_ai = False
        
        # Initialize sentiment engine
        print("Initializing sentiment engine (ProsusAI/finbert)...")
        reset_sentiment_engine()  # Clear any cached instance
        
        config = EngineConfig(
            enable_finbert=True,
            finbert_use_gpu=False,
            default_batch_size=self.batch_size,
            enable_ai_verification=self.with_ai
        )
        engine = SentimentEngine(config)
        await engine.initialize()
        
        # Check engine health
        health = await engine.health_check()
        if not health.get("engine_initialized"):
            print("ERROR: Sentiment engine failed to initialize!")
            return
        
        print(f"Engine initialized. Available models: {health.get('available_models', [])}")
        print()
        
        async with get_db_session() as db:
            # Get total count
            total = await self.get_total_records(db)
            self.stats["total_records"] = total
            
            if self.limit:
                total = min(total, self.limit)
            
            print(f"Found {self.stats['total_records']} records with raw text")
            print(f"Will process: {total} records")
            print()
            
            if total == 0:
                print("No records to process. Exiting.")
                return
            
            # Process in batches
            offset = 0
            batch_num = 0
            
            while offset < total:
                batch_num += 1
                records = await self.get_batch(db, offset)
                
                if not records:
                    break
                
                # Respect limit
                if self.limit and self.stats["processed"] + len(records) > self.limit:
                    records = records[:self.limit - self.stats["processed"]]
                
                print(f"Batch {batch_num}: Processing {len(records)} records (offset {offset})...")
                
                updated = await self.process_batch(db, records, engine)
                self.stats["processed"] += len(records)
                
                print(f"  Updated: {updated} | Progress: {self.stats['processed']}/{total} ({100*self.stats['processed']/total:.1f}%)")
                
                offset += self.batch_size
                
                # Small delay between batches to avoid overwhelming the system
                await asyncio.sleep(0.1)
        
        # Print final statistics
        self._print_stats()
    
    def _print_stats(self):
        """Print final statistics."""
        print()
        print("=" * 70)
        print("RE-PROCESSING COMPLETE")
        print("=" * 70)
        print(f"Total Records in DB:    {self.stats['total_records']}")
        print(f"Records Processed:      {self.stats['processed']}")
        print(f"Records Updated:        {self.stats['updated']}")
        print(f"Skipped (no text):      {self.stats['skipped_no_text']}")
        print(f"Errors:                 {self.stats['errors']}")
        print()
        print("SENTIMENT CHANGES:")
        print("-" * 40)
        changes = self.stats["sentiment_changes"]
        print(f"  Unchanged:            {changes['unchanged']}")
        print(f"  Positive -> Negative: {changes['positive_to_negative']}")
        print(f"  Positive -> Neutral:  {changes['positive_to_neutral']}")
        print(f"  Negative -> Positive: {changes['negative_to_positive']}")
        print(f"  Negative -> Neutral:  {changes['negative_to_neutral']}")
        print(f"  Neutral -> Positive:  {changes['neutral_to_positive']}")
        print(f"  Neutral -> Negative:  {changes['neutral_to_negative']}")
        
        if self.dry_run:
            print()
            print("NOTE: This was a DRY RUN. No changes were made to the database.")
            print("Run without --dry-run to apply changes.")


async def main():
    parser = argparse.ArgumentParser(
        description="Re-process sentiment data with FinBERT + AI verification"
    )
    parser.add_argument(
        "--batch-size", 
        type=int, 
        default=50,
        help="Number of records per batch (default: 50)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating database"
    )
    parser.add_argument(
        "--with-ai",
        action="store_true",
        help="Enable Gemini AI verification for uncertain predictions"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum records to process (default: all)"
    )
    
    args = parser.parse_args()
    
    reprocessor = SentimentReprocessor(
        batch_size=args.batch_size,
        dry_run=args.dry_run,
        with_ai=args.with_ai,
        limit=args.limit
    )
    
    await reprocessor.run()


if __name__ == "__main__":
    asyncio.run(main())
