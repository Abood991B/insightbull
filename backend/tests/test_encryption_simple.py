#!/usr/bin/env python3
"""
Quick API Key Encryption Test
============================

Simple test to verify the encryption utilities are working.
Tests the core encryption/decryption functionality.

Usage:
    python test_encryption_simple.py
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

def test_encryption_utilities():
    """Test the encryption utilities directly"""
    print("🔐 Testing API Key Encryption Utilities")
    print("=" * 50)
    
    try:
        from app.infrastructure.security.api_key_manager import APIKeyManager
        
        # Initialize manager
        print("1. Initializing APIKeyManager...")
        manager = APIKeyManager()
        print("   ✅ APIKeyManager created successfully")
        
        # Test basic encryption/decryption
        print("\n2. Testing basic encryption/decryption...")
        test_key = "my_secret_api_key_12345"
        print(f"   Original key: {test_key}")
        
        encrypted = manager.encrypt_api_key(test_key)
        print(f"   Encrypted: {encrypted[:30]}..." if len(encrypted) > 30 else f"   Encrypted: {encrypted}")
        
        decrypted = manager.decrypt_api_key(encrypted)
        print(f"   Decrypted: {decrypted}")
        
        if decrypted == test_key:
            print("   ✅ Encryption/Decryption SUCCESSFUL")
        else:
            print("   ❌ Encryption/Decryption FAILED")
            return False
        
        # Test with actual environment keys
        print("\n3. Testing with environment variables...")
        actual_keys = {
            'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID', ''),
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY', ''),
            'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY', ''),
            'MARKETAUX_API_KEY': os.getenv('MARKETAUX_API_KEY', '')
        }
        
        for key_name, key_value in actual_keys.items():
            if key_value:
                print(f"   Testing {key_name}...")
                encrypted_env = manager.encrypt_api_key(key_value)
                decrypted_env = manager.decrypt_api_key(encrypted_env)
                
                if decrypted_env == key_value:
                    print(f"   ✅ {key_name}: OK")
                else:
                    print(f"   ❌ {key_name}: FAILED")
                    return False
            else:
                print(f"   ⚠️  {key_name}: Not set in environment")
        
        print("\n4. Testing SecureAPIKeyLoader...")
        from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader
        
        loader = SecureAPIKeyLoader()
        loaded_keys = loader.load_api_keys()
        
        print(f"   Loaded {len(loaded_keys)} keys from environment")
        
        # Test individual key retrieval
        for key_name in actual_keys.keys():
            retrieved_key = loader.get_decrypted_key(key_name)
            if retrieved_key:
                print(f"   ✅ {key_name}: Retrieved successfully")
            else:
                print(f"   ⚠️  {key_name}: Empty or not found")
        
        print("\n🎉 All encryption tests completed successfully!")
        return True
        
    except ImportError as e:
        print(f"❌ Import Error: {e}")
        print("   Make sure the encryption modules are properly installed")
        return False
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False


def show_environment_status():
    """Show current environment status"""
    print("\n🌍 Current Environment Status:")
    print("-" * 30)
    
    env_keys = [
        'REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET',
        'FINNHUB_API_KEY', 'NEWSAPI_KEY', 'MARKETAUX_API_KEY',
        'API_ENCRYPTION_KEY', 'DATABASE_URL'
    ]
    
    for key in env_keys:
        value = os.getenv(key)
        if value:
            # Mask the value for security
            if len(value) > 8:
                masked = f"{value[:4]}...{value[-4:]}"
            else:
                masked = "***"
            print(f"✅ {key}: {masked}")
        else:
            print(f"❌ {key}: Not set")


if __name__ == "__main__":
    print("Starting API Key Encryption Test...\n")
    
    # Show environment status first
    show_environment_status()
    
    # Run encryption tests
    success = test_encryption_utilities()
    
    if success:
        print("\n✅ All tests passed! Your encryption system is working correctly.")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
    
    print("\nTest completed.")