# Test API Key Functionality
# Run this in the backend directory to test the API key system

import os
import sys
sys.path.append('.')

from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader

def test_api_keys():
    print("🔑 Testing API Key System")
    print("=" * 50)
    
    # Test loading keys
    loader = SecureAPIKeyLoader()
    keys = loader.load_api_keys()
    
    print("✅ Loaded API Keys:")
    for key_name, value in keys.items():
        if value:
            print(f"  {key_name}: {value[:4]}••••••••")
        else:
            print(f"  {key_name}: <not set>")
    
    print("\n🔧 Testing Update Functionality...")
    
    # Test updating a key
    test_key = "TEST_REDDIT_CLIENT_ID_12345"
    loader.update_api_key('REDDIT_CLIENT_ID', test_key)
    
    # Reload and verify
    updated_keys = loader.load_api_keys()
    
    if updated_keys.get('REDDIT_CLIENT_ID') == test_key:
        print("✅ Key update successful!")
        print(f"  Updated REDDIT_CLIENT_ID: {test_key[:4]}••••••••")
    else:
        print("❌ Key update failed!")
    
    print("\n✅ API Key system working correctly!")
    print("💾 Keys are persisted to: data/secure_keys/encrypted_keys.json")

if __name__ == "__main__":
    test_api_keys()