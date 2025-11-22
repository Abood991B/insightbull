"""
Debug script to test Reddit collector configuration and initialization
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

async def main():
    print("="*60)
    print("REDDIT COLLECTOR DEBUG TEST")
    print("="*60)
    
    # Step 1: Check API key loading
    print("\n1. Loading API keys...")
    from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader
    loader = SecureAPIKeyLoader()
    keys = loader.load_api_keys()
    
    reddit_client_id = keys.get('reddit_client_id', '')
    reddit_client_secret = keys.get('reddit_client_secret', '')
    reddit_user_agent = keys.get('reddit_user_agent', '')
    
    print(f"   Reddit client_id: {'✓ PRESENT' if reddit_client_id else '✗ MISSING'} ({len(reddit_client_id) if reddit_client_id else 0} chars)")
    print(f"   Reddit client_secret: {'✓ PRESENT' if reddit_client_secret else '✗ MISSING'} ({len(reddit_client_secret) if reddit_client_secret else 0} chars)")
    print(f"   Reddit user_agent: {'✓ PRESENT' if reddit_user_agent else '✗ MISSING'}")
    print(f"   User agent value: {reddit_user_agent[:50]}..." if len(reddit_user_agent) > 50 else f"   User agent value: {reddit_user_agent}")
    
    # Check if user_agent looks encrypted (base64)
    if reddit_user_agent:
        import base64
        try:
            # If it can be base64 decoded, it might still be encrypted
            decoded = base64.b64decode(reddit_user_agent)
            print(f"   ⚠️  WARNING: User agent appears to be base64 encoded (still encrypted?)")
        except:
            print(f"   ✓ User agent appears to be plaintext")
    
    # Step 2: Try to initialize Reddit collector
    print("\n2. Initializing Reddit collector...")
    try:
        from app.infrastructure.collectors.reddit_collector import RedditCollector
        
        # Use default user agent if encrypted one doesn't work
        if not reddit_user_agent or len(reddit_user_agent) > 100:  # Encrypted strings are long
            reddit_user_agent = "InsightStockDash/1.0"
            print(f"   Using default user agent: {reddit_user_agent}")
        
        collector = RedditCollector(
            client_id=reddit_client_id,
            client_secret=reddit_client_secret,
            user_agent=reddit_user_agent,
            rate_limiter=None
        )
        print("   ✓ Reddit collector created successfully")
        print(f"   Collector source: {collector.source}")
        print(f"   Requires API key: {collector.requires_api_key}")
    except Exception as e:
        print(f"   ✗ Failed to create Reddit collector: {e}")
        return
    
    # Step 3: Test connection
    print("\n3. Testing Reddit API connection...")
    try:
        is_valid = await collector.validate_connection()
        if is_valid:
            print("   ✓ Reddit API connection successful!")
        else:
            print("   ✗ Reddit API connection failed (invalid credentials)")
    except Exception as e:
        print(f"   ✗ Connection test error: {e}")
    
    # Step 4: Test data collection
    print("\n4. Testing Reddit data collection...")
    try:
        from app.infrastructure.collectors.base_collector import CollectionConfig
        from datetime import datetime, timedelta
        
        config = CollectionConfig(
            symbols=['AAPL'],  # Test with single symbol
            date_range=(datetime.now() - timedelta(days=1), datetime.now()),
            max_items_per_symbol=5,
            include_comments=False
        )
        
        print("   Collecting data for AAPL (max 5 items)...")
        result = await collector.collect_data(config)
        
        print(f"   Collection success: {result.success}")
        print(f"   Items collected: {len(result.data)}")
        print(f"   Execution time: {result.execution_time:.2f}s")
        
        if result.error_message:
            print(f"   Error message: {result.error_message}")
        
        if result.data:
            print(f"\n   Sample data:")
            for i, item in enumerate(result.data[:2], 1):
                print(f"      Item {i}:")
                print(f"         Stock: {item.stock_symbol}")
                print(f"         Text preview: {item.text[:100]}...")
                print(f"         Metadata: {list(item.metadata.keys()) if item.metadata else 'None'}")
        else:
            print("   ⚠️  No data collected")
            
    except Exception as e:
        print(f"   ✗ Collection test error: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 5: Check pipeline integration
    print("\n5. Testing Pipeline integration...")
    try:
        from app.business.pipeline import Pipeline
        
        pipeline = Pipeline()
        await pipeline.initialize()
        
        collectors = list(pipeline._collectors.keys())
        print(f"   Pipeline collectors: {collectors}")
        
        if 'reddit' in pipeline._collectors:
            print("   ✓ Reddit collector registered in pipeline")
            reddit_collector = pipeline._collectors['reddit']
            print(f"   Reddit collector type: {type(reddit_collector).__name__}")
            print(f"   Reddit client_id in pipeline: {reddit_collector.client_id[:20]}..." if reddit_collector.client_id else "NONE")
        else:
            print("   ✗ Reddit collector NOT registered in pipeline")
            
    except Exception as e:
        print(f"   ✗ Pipeline test error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("DEBUG TEST COMPLETE")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())
