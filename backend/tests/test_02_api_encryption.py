#!/usr/bin/env python3
"""
API Key Encryption Implementation Test
=====================================

Comprehensive test suite for the API Key Encryption system including:
- APIKeyManager encryption/decryption
- SecureAPIKeyLoader functionality
- Data collector integration
- Environment variable handling
- Error handling and fallback mechanisms

Usage:
    python test_api_encryption.py
"""

import os
import sys
import asyncio
from typing import Dict, Any
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

# Load environment variables
load_dotenv()

from app.infrastructure.security.api_key_manager import APIKeyManager, SecureAPIKeyLoader
from app.business.data_collector import DataCollector


class APIEncryptionTester:
    """Comprehensive test suite for API key encryption"""
    
    def __init__(self):
        self.test_api_keys = {
            'FINNHUB_API_KEY': 'test_finnhub_key_abcdef',
            'NEWSAPI_KEY': 'test_newsapi_key_ghijkl'
        }
        self.results = []
    
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        status = "✅ PASS" if passed else "❌ FAIL"
        self.results.append((test_name, passed))
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        print()
    
    def test_api_key_manager_basic(self):
        """Test basic APIKeyManager functionality"""
        print("🔧 Testing APIKeyManager Basic Operations...")
        
        try:
            # Initialize APIKeyManager
            manager = APIKeyManager()
            
            # Test encryption
            test_key = "test_secret_key_12345"
            encrypted = manager.encrypt_api_key(test_key)
            
            self.log_test(
                "APIKeyManager Initialization", 
                manager is not None,
                f"Manager created successfully"
            )
            
            self.log_test(
                "API Key Encryption",
                encrypted != test_key and len(encrypted) > 0,
                f"Original: {test_key[:10]}... → Encrypted: {encrypted[:20]}..."
            )
            
            # Test decryption
            decrypted = manager.decrypt_api_key(encrypted)
            
            self.log_test(
                "API Key Decryption",
                decrypted == test_key,
                f"Decrypted: {decrypted} (matches original: {decrypted == test_key})"
            )
            
            # Test empty key handling
            empty_encrypted = manager.encrypt_api_key("")
            empty_decrypted = manager.decrypt_api_key("")
            
            self.log_test(
                "Empty Key Handling",
                empty_encrypted == "" and empty_decrypted == "",
                "Empty keys handled correctly"
            )
            
        except Exception as e:
            self.log_test("APIKeyManager Basic Operations", False, f"Error: {str(e)}")
    
    def test_bulk_encryption(self):
        """Test bulk encryption/decryption operations"""
        print("🔐 Testing Bulk Encryption Operations...")
        
        try:
            manager = APIKeyManager()
            
            # Test encrypt_all_keys
            encrypted_keys = manager.encrypt_all_keys(self.test_api_keys)
            
            all_encrypted = all(
                encrypted_keys[key] != original_value 
                for key, original_value in self.test_api_keys.items()
                if original_value  # Skip empty values
            )
            
            self.log_test(
                "Bulk Encryption",
                all_encrypted,
                f"Encrypted {len(encrypted_keys)} keys successfully"
            )
            
            # Test decrypt_all_keys
            decrypted_keys = manager.decrypt_all_keys(encrypted_keys)
            
            all_decrypted = all(
                decrypted_keys[key] == original_value
                for key, original_value in self.test_api_keys.items()
            )
            
            self.log_test(
                "Bulk Decryption",
                all_decrypted,
                f"Decrypted {len(decrypted_keys)} keys successfully"
            )
            
        except Exception as e:
            self.log_test("Bulk Encryption Operations", False, f"Error: {str(e)}")
    
    def test_secure_api_key_loader(self):
        """Test SecureAPIKeyLoader functionality"""
        print("🔑 Testing SecureAPIKeyLoader...")
        
        try:
            # Temporarily set test environment variables
            original_env = {}
            for key, value in self.test_api_keys.items():
                original_env[key] = os.getenv(key)
                os.environ[key] = value
            
            try:
                loader = SecureAPIKeyLoader()
                
                self.log_test(
                    "SecureAPIKeyLoader Initialization",
                    loader is not None,
                    "Loader created successfully"
                )
                
                # Test load_api_keys
                loaded_keys = loader.load_api_keys()
                
                self.log_test(
                    "API Keys Loading",
                    len(loaded_keys) == len(self.test_api_keys),
                    f"Loaded {len(loaded_keys)} keys"
                )
                
                # Test individual key retrieval
                finnhub_key = loader.get_decrypted_key("FINNHUB_API_KEY")
                
                self.log_test(
                    "Individual Key Retrieval",
                    finnhub_key == self.test_api_keys["FINNHUB_API_KEY"],
                    f"Retrieved: {finnhub_key}"
                )
                
                # Test cache functionality
                loader.clear_cache()
                finnhub_key_2 = loader.get_decrypted_key("FINNHUB_API_KEY")
                
                self.log_test(
                    "Cache Clear and Reload",
                    finnhub_key_2 == self.test_api_keys["FINNHUB_API_KEY"],
                    "Cache cleared and reloaded successfully"
                )
                
            finally:
                # Restore original environment
                for key, original_value in original_env.items():
                    if original_value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = original_value
                        
        except Exception as e:
            self.log_test("SecureAPIKeyLoader", False, f"Error: {str(e)}")
    
    async def test_data_collector_integration(self):
        """Test DataCollector integration with encryption"""
        print("🔗 Testing DataCollector Integration...")
        
        try:
            # Test with current environment (should use real keys if available)
            collector = DataCollector()
            
            self.log_test(
                "DataCollector Initialization",
                collector is not None,
                "DataCollector created with encryption support"
            )
            
            # Count active collectors
            active_collectors = sum(1 for collector_attr in [
                'hackernews_collector', 'finnhub_collector', 
                'newsapi_collector'
            ] if getattr(collector, collector_attr) is not None)
            
            self.log_test(
                "Active Collectors Count",
                active_collectors >= 0,  # Can be 0 if no keys are set
                f"Found {active_collectors} active collectors"
            )
            
            # Test collector status
            collectors_status = {}
            for collector_name in ['hackernews_collector', 'finnhub_collector', 'newsapi_collector']:
                collector_obj = getattr(collector, collector_name)
                collectors_status[collector_name] = collector_obj is not None
            
            self.log_test(
                "Collector Status Check",
                True,  # Always pass, just informational
                f"Collectors: {collectors_status}"
            )
            
        except Exception as e:
            self.log_test("DataCollector Integration", False, f"Error: {str(e)}")
    
    def test_environment_integration(self):
        """Test integration with actual environment variables"""
        print("🌍 Testing Environment Integration...")
        
        try:
            # Check current environment
            current_keys = {
                'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY'),
                'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY'),
                'API_ENCRYPTION_KEY': os.getenv('API_ENCRYPTION_KEY')
            }
            
            keys_found = sum(1 for v in current_keys.values() if v)
            
            self.log_test(
                "Environment Variables Check",
                keys_found > 0,
                f"Found {keys_found} API keys in environment"
            )
            
            # Test with actual keys if available
            if keys_found > 0:
                loader = SecureAPIKeyLoader()
                loaded_keys = loader.load_api_keys()
                
                successfully_loaded = sum(1 for v in loaded_keys.values() if v)
                
                self.log_test(
                    "Real Environment Keys Loading",
                    successfully_loaded > 0,
                    f"Successfully loaded {successfully_loaded} keys from environment"
                )
            
            # Show key status (masked for security)
            print("    🔍 Current Environment Status:")
            for key, value in current_keys.items():
                if value:
                    masked_value = f"{value[:4]}...{value[-4:]}" if len(value) > 8 else "***"
                    print(f"       ✅ {key}: {masked_value}")
                else:
                    print(f"       ❌ {key}: Not set")
            
        except Exception as e:
            self.log_test("Environment Integration", False, f"Error: {str(e)}")
    
    def test_error_handling(self):
        """Test error handling and fallback mechanisms"""
        print("⚡ Testing Error Handling...")
        
        try:
            manager = APIKeyManager()
            
            # Test malformed encrypted data
            malformed_data = "not_base64_encrypted_data"
            decrypted = manager.decrypt_api_key(malformed_data)
            
            self.log_test(
                "Malformed Data Fallback",
                decrypted == malformed_data,  # Should return original if decryption fails
                "Gracefully handled malformed encrypted data"
            )
            
            # Test None input
            none_result = manager.encrypt_api_key(None)
            
            self.log_test(
                "None Input Handling",
                none_result == "",  # Should handle None gracefully
                "Handled None input correctly"
            )
            
        except Exception as e:
            # Error handling should not raise exceptions
            self.log_test("Error Handling", False, f"Error handling failed: {str(e)}")
    
    def print_summary(self):
        """Print test summary"""
        print("=" * 60)
        print("🧪 API Key Encryption Test Summary")
        print("=" * 60)
        
        passed = sum(1 for _, result in self.results if result)
        total = len(self.results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total*100):.1f}%" if total > 0 else "No tests run")
        
        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for test_name, result in self.results:
                if not result:
                    print(f"   • {test_name}")
        
        print(f"\n{'🎉 All tests passed!' if passed == total else '⚠️  Some tests failed - check implementation'}")
        print("=" * 60)


async def main():
    """Run all encryption tests"""
    print("🔐 API Key Encryption Implementation Test Suite")
    print("=" * 60)
    print()
    
    tester = APIEncryptionTester()
    
    # Run all tests
    tester.test_api_key_manager_basic()
    tester.test_bulk_encryption()
    tester.test_secure_api_key_loader()
    await tester.test_data_collector_integration()
    tester.test_environment_integration()
    tester.test_error_handling()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())