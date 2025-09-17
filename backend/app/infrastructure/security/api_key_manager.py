"""
API Key Encryption Utility
==========================

Provides encryption/decryption functionality for sensitive API keys
to enhance security in the Phase 5 data collection pipeline.

Features:
- AES encryption for API keys
- Environment-based master key
- Secure key storage and retrieval
- Automatic encryption/decryption in pipeline

Usage:
    from app.infrastructure.security.api_encryption import APIKeyManager
    
    manager = APIKeyManager()
    encrypted_key = manager.encrypt_api_key("your-secret-key")
    decrypted_key = manager.decrypt_api_key(encrypted_key)
"""

import os
import base64
import logging
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class APIKeyManager:
    """
    Manages encryption and decryption of API keys for secure storage.
    
    Uses AES encryption with a master key derived from environment variables
    to protect sensitive API credentials used in data collection.
    """
    
    def __init__(self, master_password: Optional[str] = None):
        """
        Initialize the API Key Manager.
        
        Args:
            master_password: Optional master password. If not provided,
                           will use environment variable or generate one.
        """
        self.master_password = master_password or self._get_master_password()
        self._cipher_suite = self._create_cipher_suite()
    
    def _get_master_password(self) -> str:
        """Get or generate master password for encryption"""
        # Try to get from environment first
        master_key = os.getenv('API_ENCRYPTION_KEY')
        
        if not master_key:
            # Generate a default key based on system info (not recommended for production)
            import platform
            import hashlib
            
            system_info = f"{platform.node()}-{platform.system()}-phase5-pipeline"
            master_key = hashlib.sha256(system_info.encode()).hexdigest()[:32]
            
            logger.warning(
                "No API_ENCRYPTION_KEY environment variable found. "
                "Using system-generated key. For production, set API_ENCRYPTION_KEY."
            )
        
        return master_key
    
    def _create_cipher_suite(self) -> Fernet:
        """Create Fernet cipher suite from master password"""
        # Convert master password to bytes and create key
        password_bytes = self.master_password.encode()
        
        # Use a fixed salt for consistency (in production, use random salt stored securely)
        salt = b'phase5_salt_2025'
        
        # Derive key using PBKDF2
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        
        key = base64.urlsafe_b64encode(kdf.derive(password_bytes))
        return Fernet(key)
    
    def encrypt_api_key(self, api_key: str) -> str:
        """
        Encrypt an API key.
        
        Args:
            api_key: The plain text API key to encrypt
            
        Returns:
            Base64 encoded encrypted API key
        """
        try:
            if not api_key:
                return ""
            
            encrypted_bytes = self._cipher_suite.encrypt(api_key.encode())
            return base64.urlsafe_b64encode(encrypted_bytes).decode()
            
        except Exception as e:
            logger.error(f"Failed to encrypt API key: {e}")
            # Return original key if encryption fails (fallback)
            return api_key
    
    def decrypt_api_key(self, encrypted_key: str) -> str:
        """
        Decrypt an API key.
        
        Args:
            encrypted_key: The encrypted API key to decrypt
            
        Returns:
            Plain text API key
        """
        try:
            if not encrypted_key:
                return ""
            
            # Try to decrypt (if it's actually encrypted)
            try:
                encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
                decrypted_bytes = self._cipher_suite.decrypt(encrypted_bytes)
                return decrypted_bytes.decode()
                
            except Exception:
                # If decryption fails, assume it's already plain text
                logger.debug("Key appears to be plain text, returning as-is")
                return encrypted_key
                
        except Exception as e:
            logger.error(f"Failed to decrypt API key: {e}")
            # Return original key if decryption fails (fallback)
            return encrypted_key
    
    def encrypt_all_keys(self, keys_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Encrypt multiple API keys.
        
        Args:
            keys_dict: Dictionary of key names to API keys
            
        Returns:
            Dictionary with encrypted API keys
        """
        encrypted_keys = {}
        
        for key_name, api_key in keys_dict.items():
            if api_key:
                encrypted_keys[key_name] = self.encrypt_api_key(api_key)
            else:
                encrypted_keys[key_name] = ""
        
        return encrypted_keys
    
    def decrypt_all_keys(self, encrypted_keys_dict: Dict[str, str]) -> Dict[str, str]:
        """
        Decrypt multiple API keys.
        
        Args:
            encrypted_keys_dict: Dictionary of key names to encrypted API keys
            
        Returns:
            Dictionary with decrypted API keys
        """
        decrypted_keys = {}
        
        for key_name, encrypted_key in encrypted_keys_dict.items():
            if encrypted_key:
                decrypted_keys[key_name] = self.decrypt_api_key(encrypted_key)
            else:
                decrypted_keys[key_name] = ""
        
        return decrypted_keys
    
    def is_encrypted(self, key: str) -> bool:
        """
        Check if a key appears to be encrypted.
        
        Args:
            key: The key to check
            
        Returns:
            True if key appears encrypted, False otherwise
        """
        if not key:
            return False
        
        try:
            # Try to base64 decode and decrypt
            encrypted_bytes = base64.urlsafe_b64decode(key.encode())
            self._cipher_suite.decrypt(encrypted_bytes)
            return True
        except Exception:
            return False


class SecureAPIKeyLoader:
    """
    Secure loader for API keys with automatic encryption/decryption.
    
    Integrates with the data collection pipeline to provide transparent
    encryption of sensitive API credentials.
    """
    
    def __init__(self):
        self.key_manager = APIKeyManager()
        self._cache = {}
    
    def load_api_keys(self) -> Dict[str, str]:
        """
        Load and decrypt API keys from environment.
        
        Returns:
            Dictionary of decrypted API keys ready for use
        """
        if self._cache:
            return self._cache
        
        # Load keys from environment
        encrypted_keys = {
            'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID', ''),
            'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET', ''),
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY', ''),
            'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY', ''),
            'MARKETAUX_API_KEY': os.getenv('MARKETAUX_API_KEY', '')
        }
        
        # Decrypt all keys
        decrypted_keys = self.key_manager.decrypt_all_keys(encrypted_keys)
        
        # Cache decrypted keys
        self._cache = decrypted_keys
        
        logger.info("API keys loaded and decrypted successfully")
        return decrypted_keys
    
    def get_decrypted_key(self, key_name: str) -> str:
        """
        Get a specific decrypted API key.
        
        Args:
            key_name: Name of the API key (e.g., 'FINNHUB_API_KEY')
            
        Returns:
            Decrypted API key
        """
        keys = self.load_api_keys()
        return keys.get(key_name, '')
    
    def clear_cache(self):
        """Clear the decrypted keys cache for security"""
        self._cache.clear()


def create_encrypted_env_template():
    """
    Utility function to create an encrypted .env template.
    
    This can be used to encrypt existing API keys for storage.
    """
    print("🔐 API Key Encryption Utility")
    print("=" * 40)
    
    # Load current keys
    current_keys = {
        'REDDIT_CLIENT_ID': os.getenv('REDDIT_CLIENT_ID', ''),
        'REDDIT_CLIENT_SECRET': os.getenv('REDDIT_CLIENT_SECRET', ''),
        'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY', ''),
        'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY', ''),
        'MARKETAUX_API_KEY': os.getenv('MARKETAUX_API_KEY', '')
    }
    
    manager = APIKeyManager()
    
    print("Encrypting API keys...")
    encrypted_keys = manager.encrypt_all_keys(current_keys)
    
    print("\n📄 Encrypted .env template:")
    print("# Encrypted API Keys for Phase 5 Pipeline")
    print("# Generated on:", datetime.utcnow().isoformat())
    print()
    
    for key_name, encrypted_value in encrypted_keys.items():
        if encrypted_value:
            print(f"{key_name}={encrypted_value}")
        else:
            print(f"# {key_name}=<not_set>")
    
    print()
    print("🔑 To use encrypted keys, set API_ENCRYPTION_KEY environment variable")
    print("   or the system will generate a default key.")


if __name__ == "__main__":
    from datetime import datetime
    from dotenv import load_dotenv
    
    load_dotenv()
    create_encrypted_env_template()