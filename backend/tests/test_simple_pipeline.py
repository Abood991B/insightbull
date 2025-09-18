#!/usr/bin/env python3
"""
Simple pipeline test to debug sentiment analysis
"""

import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.business.pipeline import DataPipeline, PipelineConfig, DateRange
from datetime import datetime, timedelta

async def test_sentiment_debug():
    print("PIPELINE SENTIMENT DEBUG TEST")
    print("=" * 50)
    
    # Create pipeline
    pipeline = DataPipeline()
    
    # Simple config
    config = PipelineConfig(
        symbols=["AAPL"],
        date_range=DateRange(
            start_date=datetime.now() - timedelta(days=7),  # Extended to 7 days for Reddit data
            end_date=datetime.now()
        ),
        max_items_per_symbol=5,
        include_reddit=True,
        include_finnhub=True,
        include_newsapi=True,
        include_marketaux=True
    )
    
    print("Running pipeline...")
    result = await pipeline.run_pipeline(config)
    
    print(f"Pipeline result: {result.status}")
    print(f"Items analyzed: {result.total_items_analyzed}")
    print(f"Items stored: {result.total_items_stored}")

if __name__ == "__main__":
    asyncio.run(test_sentiment_debug())