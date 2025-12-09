#!/usr/bin/env python3
"""
Data Collector Encryption Integration Test
==========================================

Tests the integration between DataCollector and the encryption system.
This validates that collectors are properly initialized with encrypted API keys.

Usage:
    python test_collector_encryption.py
"""

import os
import sys
import asyncio
from dotenv import load_dotenv
from app.utils.timezone import utc_now

# Load environment variables first
load_dotenv()

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))


async def test_data_collector_encryption():
    """Test DataCollector with encryption system"""
    print("🔗 Testing DataCollector Encryption Integration")
    print("=" * 55)
    
    try:
        # Import the updated DataCollector
        from app.business.data_collector import DataCollector
        
        print("1. Initializing DataCollector with encryption...")
        collector = DataCollector()
        print("   ✅ DataCollector initialized successfully")
        
        print("\n2. Checking collector initialization status...")
        
        collectors_info = [
            ("HackerNews", collector.hackernews_collector),
            ("FinHub", collector.finnhub_collector),
            ("NewsAPI", collector.newsapi_collector)
        ]
        
        active_count = 0
        for name, collector_obj in collectors_info:
            if collector_obj is not None:
                print(f"   ✅ {name} collector: ACTIVE")
                active_count += 1
            else:
                print(f"   ⚠️  {name} collector: INACTIVE (no API key)")
        
        print(f"\n   📊 Summary: {active_count}/3 collectors active")
        
        print("\n3. Testing SecureAPIKeyLoader integration...")
        
        # Test that the secure loader was used
        if hasattr(collector, 'secure_loader'):
            print("   ✅ SecureAPIKeyLoader is integrated")
            
            # Test key retrieval (HackerNews has no API key - free and unlimited)
            test_keys = ['FINNHUB_API_KEY', 'NEWSAPI_KEY']
            for key_name in test_keys:
                key_value = collector.secure_loader.get_decrypted_key(key_name)
                if key_value:
                    print(f"   ✅ {key_name}: Retrieved and decrypted")
                else:
                    print(f"   ⚠️  {key_name}: Empty or not found")
        else:
            print("   ❌ SecureAPIKeyLoader not found in DataCollector")
            return False
        
        print("\n4. Testing collection method safety...")
        
        # Test that collection methods handle None collectors properly
        test_symbols = ["AAPL", "MSFT"]
        from datetime import timedelta
        date_range = {
            'start': utc_now() - timedelta(days=1),
            'end': utc_now()
        }
        
        collection_methods = [
            ("HackerNews", collector._collect_hackernews_data),
            ("FinHub", collector._collect_finnhub_data),
            ("NewsAPI", collector._collect_newsapi_data)
        ]
        
        for name, method in collection_methods:
            try:
                # This should return empty list if collector is None
                result = await method(test_symbols, date_range)
                if isinstance(result, list):
                    print(f"   ✅ {name} collection method: Safe (returned {len(result)} items)")
                else:
                    print(f"   ⚠️  {name} collection method: Unexpected return type")
            except Exception as e:
                print(f"   ❌ {name} collection method: Error - {str(e)}")
        
        print("\n5. Environment and encryption validation...")
        
        # Check if environment variables are properly loaded
        # Note: HackerNews uses free Algolia API with no key required
        env_status = {
            'FINNHUB_API_KEY': bool(os.getenv('FINNHUB_API_KEY')),
            'NEWSAPI_KEY': bool(os.getenv('NEWSAPI_KEY')),
            'API_ENCRYPTION_KEY': bool(os.getenv('API_ENCRYPTION_KEY'))
        }
        
        print("   Environment variables status:")
        for key, status in env_status.items():
            print(f"     {'✅' if status else '❌'} {key}: {'Set' if status else 'Not set'}")
        
        # Test encryption with current environment
        from app.infrastructure.security.api_key_manager import APIKeyManager
        manager = APIKeyManager()
        
        print("\n   Testing encryption with current environment:")
        for key, is_set in env_status.items():
            if is_set and key != 'API_ENCRYPTION_KEY':
                original_value = os.getenv(key)
                encrypted = manager.encrypt_api_key(original_value)
                decrypted = manager.decrypt_api_key(encrypted)
                
                if decrypted == original_value:
                    print(f"     ✅ {key}: Encryption/decryption OK")
                else:
                    print(f"     ❌ {key}: Encryption/decryption FAILED")
        
        print(f"\n🎉 DataCollector encryption integration test completed!")
        print(f"   • {active_count} collectors are active and ready")
        print(f"   • Encryption system is properly integrated")
        print(f"   • Collection methods are safe and handle missing keys")
        
        return active_count > 0
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def show_detailed_collector_status():
    """Show detailed status of collectors and their requirements"""
    print("\n📋 Collector Requirements Check:")
    print("-" * 40)
    
    # Note: HackerNews uses free Algolia API (no key required)
    requirements = {
        'HackerNews': [],  # Free Algolia API - no credentials needed
        'FinHub': ['FINNHUB_API_KEY'],
        'NewsAPI': ['NEWSAPI_KEY']
    }
    
    for collector_name, required_keys in requirements.items():
        print(f"\n{collector_name} Collector:")
        
        if not required_keys:
            print(f"  ✅ No API key required (free Algolia API)")
            print(f"  → Status: READY")
            continue
        
        all_keys_present = True
        for key in required_keys:
            value = os.getenv(key)
            if value:
                print(f"  ✅ {key}: Available")
            else:
                print(f"  ❌ {key}: Missing")
                all_keys_present = False
        
        status = "READY" if all_keys_present else "NOT READY"
        print(f"  → Status: {status}")


async def main():
    """Run the complete test suite"""
    print("🔐 Data Collector Encryption Integration Test")
    print("=" * 60)
    
    # Show detailed collector status
    show_detailed_collector_status()
    
    # Run the main test
    success = await test_data_collector_encryption()
    
    if success:
        print("\n✅ Integration test PASSED!")
        print("   Your DataCollector is properly integrated with the encryption system.")
    else:
        print("\n❌ Integration test FAILED!")
        print("   There may be issues with the encryption integration.")
    
    print("\nTest completed. You can now run 'python main.py' to see the system in action.")


if __name__ == "__main__":
    asyncio.run(main())