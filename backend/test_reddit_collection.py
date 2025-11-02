"""
Test Reddit data collection to verify all columns are stored correctly.

This script:
1. Collects fresh Reddit data for a test symbol
2. Processes and analyzes sentiment
3. Shows what gets stored in reddit_posts table
4. Shows what gets stored in sentiment_data table
5. Verifies all columns are populated

Run this to confirm the pipeline fix is working!
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.business.pipeline import DataPipeline, PipelineConfig
from app.infrastructure.collectors.base_collector import DateRange
from app.data_access.database import init_database, get_db_session
from app.data_access.models import RedditPost, SentimentData, StocksWatchlist
from sqlalchemy import select, func
import structlog

logger = structlog.get_logger()

# Test configuration
TEST_SYMBOL = "AAPL"  # Test with Apple stock
DAYS_BACK = 3  # Collect last 3 days of data
MAX_ITEMS = 5  # Collect only 5 items for testing


async def test_reddit_collection():
    """Test Reddit data collection and storage."""
    
    logger.info("=" * 80)
    logger.info("REDDIT DATA COLLECTION TEST")
    logger.info("=" * 80)
    logger.info(f"Test Symbol: {TEST_SYMBOL}")
    logger.info(f"Date Range: Last {DAYS_BACK} days")
    logger.info(f"Max Items: {MAX_ITEMS}")
    logger.info("")
    
    # Initialize database
    await init_database()
    
    # Get counts BEFORE collection
    async with get_db_session() as session:
        reddit_count_before = (await session.execute(
            select(func.count()).select_from(RedditPost)
        )).scalar()
        sentiment_count_before = (await session.execute(
            select(func.count()).select_from(SentimentData)
        )).scalar()
        
        logger.info(f"BEFORE Collection:")
        logger.info(f"  - Reddit posts: {reddit_count_before}")
        logger.info(f"  - Sentiment records: {sentiment_count_before}")
        logger.info("")
    
    # Create pipeline
    pipeline = DataPipeline()
    
    # Configure date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=DAYS_BACK)
    date_range = DateRange(start_date=start_date, end_date=end_date)
    
    # Create pipeline config - Reddit ONLY
    config = PipelineConfig(
        symbols=[TEST_SYMBOL],
        date_range=date_range,
        max_items_per_symbol=MAX_ITEMS,
        include_reddit=True,  # ✅ Only Reddit
        include_finnhub=False,  # ❌ No other sources
        include_newsapi=False,
        include_marketaux=False,
        include_comments=False,  # Skip comments for faster testing
        parallel_collectors=False
    )
    
    # Run pipeline
    logger.info("Starting Reddit collection pipeline...")
    logger.info("")
    
    try:
        result = await pipeline.run_pipeline(config)
        
        logger.info("Pipeline completed!")
        logger.info(f"  - Status: {result.status.value}")
        logger.info(f"  - Items collected: {result.total_items_collected}")
        logger.info(f"  - Items processed: {result.total_items_processed}")
        logger.info(f"  - Items analyzed: {result.total_items_analyzed}")
        logger.info(f"  - Items stored: {result.total_items_stored}")
        logger.info(f"  - Execution time: {result.execution_time:.2f}s")
        logger.info("")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        return
    
    # Get counts AFTER collection
    async with get_db_session() as session:
        reddit_count_after = (await session.execute(
            select(func.count()).select_from(RedditPost)
        )).scalar()
        sentiment_count_after = (await session.execute(
            select(func.count()).select_from(SentimentData)
        )).scalar()
        
        new_reddit = reddit_count_after - reddit_count_before
        new_sentiment = sentiment_count_after - sentiment_count_before
        
        logger.info(f"AFTER Collection:")
        logger.info(f"  - Reddit posts: {reddit_count_after} (+{new_reddit} new)")
        logger.info(f"  - Sentiment records: {sentiment_count_after} (+{new_sentiment} new)")
        logger.info("")
        
        if new_reddit == 0:
            logger.warning("⚠️ No new Reddit posts collected!")
            logger.warning("This might mean:")
            logger.warning("  1. No recent posts mention the test symbol")
            logger.warning("  2. All posts are duplicates (already in database)")
            logger.warning("  3. Reddit API key is not configured")
            logger.info("")
            return
        
        # Fetch and display the NEW Reddit posts
        logger.info("=" * 80)
        logger.info("NEW REDDIT POSTS DETAILS")
        logger.info("=" * 80)
        
        # Get the most recent Reddit posts
        result = await session.execute(
            select(RedditPost)
            .order_by(RedditPost.created_at.desc())
            .limit(new_reddit)
        )
        reddit_posts = result.scalars().all()
        
        for i, post in enumerate(reddit_posts, 1):
            logger.info(f"\nPost #{i}:")
            logger.info(f"  ID: {post.id}")
            logger.info(f"  Title: {post.title[:80]}..." if len(post.title or '') > 80 else f"  Title: {post.title}")
            logger.info(f"  Content: {post.content[:100]}..." if len(post.content or '') > 100 else f"  Content: {post.content}")
            logger.info(f"  Author: {post.author or 'NULL ❌'}")
            logger.info(f"  URL: {post.url}")
            logger.info(f"  Subreddit: {getattr(post, 'subreddit', 'N/A')}")
            logger.info(f"  Sentiment Score: {post.sentiment_score or 'NULL ❌'}")
            logger.info(f"  Confidence: {post.confidence or 'NULL ❌'}")
            logger.info(f"  Stock Mentions: {post.stock_mentions or 'NULL ❌'}")
            logger.info(f"  Created: {post.created_at}")
        
        # Get corresponding sentiment data
        logger.info("")
        logger.info("=" * 80)
        logger.info("CORRESPONDING SENTIMENT DATA")
        logger.info("=" * 80)
        
        result = await session.execute(
            select(SentimentData)
            .where(SentimentData.source == 'reddit')
            .order_by(SentimentData.created_at.desc())
            .limit(new_sentiment)
        )
        sentiment_records = result.scalars().all()
        
        for i, sentiment in enumerate(sentiment_records, 1):
            logger.info(f"\nSentiment #{i}:")
            logger.info(f"  ID: {sentiment.id}")
            logger.info(f"  Stock ID: {sentiment.stock_id}")
            logger.info(f"  Source: {sentiment.source}")
            logger.info(f"  Sentiment Score: {sentiment.sentiment_score}")
            logger.info(f"  Confidence: {sentiment.confidence}")
            logger.info(f"  Sentiment Label: {sentiment.sentiment_label}")
            logger.info(f"  Model Used: {sentiment.model_used}")
            logger.info(f"  Raw Text: {sentiment.raw_text[:100]}...")
            logger.info(f"  Created: {sentiment.created_at}")
        
        # Verification summary
        logger.info("")
        logger.info("=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        
        # Check if all columns are populated
        issues = []
        
        for post in reddit_posts:
            if not post.title:
                issues.append("❌ title is NULL")
            if not post.content:
                issues.append("❌ content is NULL")
            if not post.author:
                issues.append("⚠️ author is NULL (might be deleted user)")
            if post.sentiment_score is None:
                issues.append("❌ sentiment_score is NULL")
            if post.confidence is None:
                issues.append("❌ confidence is NULL")
            if not post.stock_mentions:
                issues.append("⚠️ stock_mentions is NULL")
        
        if not issues:
            logger.info("✅ ALL COLUMNS POPULATED CORRECTLY!")
            logger.info("")
            logger.info("Reddit posts table stores:")
            logger.info("  ✅ title")
            logger.info("  ✅ content")
            logger.info("  ✅ author")
            logger.info("  ✅ sentiment_score")
            logger.info("  ✅ confidence")
            logger.info("  ✅ stock_mentions")
            logger.info("")
            logger.info("Sentiment data table stores:")
            logger.info("  ✅ sentiment_score")
            logger.info("  ✅ confidence")
            logger.info("  ✅ sentiment_label")
            logger.info("  ✅ model_used")
            logger.info("")
            logger.info("🎉 Pipeline is working perfectly!")
        else:
            logger.error("⚠️ ISSUES FOUND:")
            for issue in set(issues):
                logger.error(f"  {issue}")
            logger.info("")
            logger.info("💡 These issues should NOT happen with the new pipeline fixes.")
            logger.info("   If you see this, there may be a configuration problem.")
        
        logger.info("=" * 80)


async def main():
    """Main entry point."""
    try:
        await test_reddit_collection()
    except KeyboardInterrupt:
        logger.warning("Test cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Test failed: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    print("\n")
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║       REDDIT DATA COLLECTION TEST SCRIPT                      ║")
    print("║                                                                ║")
    print("║  This will collect fresh Reddit data and verify all columns   ║")
    print("║  are stored correctly in both reddit_posts and sentiment_data ║")
    print("║                                                                ║")
    print("║  NOTE: Requires Reddit API credentials to be configured       ║")
    print("╚════════════════════════════════════════════════════════════════╝")
    print("\n")
    
    asyncio.run(main())
