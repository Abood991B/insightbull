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
    
    def update_api_key(self, key_name: str, new_value: str):
        """
        Update an API key with a new encrypted value and persist to file.
        
        Args:
            key_name: Name of the API key (e.g., 'FINNHUB_API_KEY')
            new_value: New unencrypted value to store
        """
        # Encrypt the new value
        encrypted_value = self.key_manager.encrypt_api_key(new_value)
        
        # Update environment variable (in memory for this session)
        os.environ[key_name] = encrypted_value
        
        # Persist to encrypted file for next system restart
        self._save_encrypted_key_to_file(key_name, encrypted_value)
        
        # Clear cache to force reload with new values
        self.clear_cache()
        
        logger.info(f"Updated and persisted API key: {key_name}")
    
    def _save_encrypted_key_to_file(self, key_name: str, encrypted_value: str):
        """Save encrypted API key to persistent storage file."""
        import json
        from pathlib import Path
        
        # Create secure keys directory
        keys_dir = Path("data/secure_keys")
        keys_dir.mkdir(parents=True, exist_ok=True)
        
        # File to store encrypted keys
        keys_file = keys_dir / "encrypted_keys.json"
        
        # Load existing keys
        existing_keys = {}
        if keys_file.exists():
            try:
                with open(keys_file, 'r') as f:
                    existing_keys = json.load(f)
            except:
                existing_keys = {}
        
        # Update the specific key
        existing_keys[key_name] = encrypted_value
        
        # Save back to file
        with open(keys_file, 'w') as f:
            json.dump(existing_keys, f, indent=2)
        
        logger.info(f"Persisted encrypted key {key_name} to secure storage")
    
    def load_api_keys(self) -> Dict[str, str]:
        """
        Load and decrypt API keys from environment and persistent storage.
        
        Returns:
            Dictionary of decrypted API keys ready for use
        """
        if self._cache:
            return self._cache
        
        # Load keys from environment first (HackerNews needs no API key)
        encrypted_keys = {
            'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY', ''),
            'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY', ''),
            'NEWS_API_KEY': os.getenv('NEWS_API_KEY', ''),  # Alternative name
            'MARKETAUX_API_KEY': os.getenv('MARKETAUX_API_KEY', ''),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', '')  # AI verification
        }
        
        # Override with keys from persistent storage if they exist
        persistent_keys = self._load_encrypted_keys_from_file()
        encrypted_keys.update(persistent_keys)
        
        # Decrypt all keys
        decrypted_keys = self.key_manager.decrypt_all_keys(encrypted_keys)
        
        # Map keys to expected names (lowercase with underscores)
        mapped_keys = {
            'finnhub_api_key': decrypted_keys.get('FINNHUB_API_KEY', ''),
            'news_api_key': decrypted_keys.get('NEWSAPI_KEY', '') or decrypted_keys.get('NEWS_API_KEY', ''),
            'marketaux_api_key': decrypted_keys.get('MARKETAUX_API_KEY', ''),
            'gemini_api_key': decrypted_keys.get('GEMINI_API_KEY', '')
        }
        
        # Cache mapped keys
        self._cache = mapped_keys
        
        logger.info("API keys loaded and decrypted successfully from environment and persistent storage")
        return mapped_keys
    
    def _load_encrypted_keys_from_file(self) -> Dict[str, str]:
        """Load encrypted keys from persistent storage file."""
        import json
        from pathlib import Path
        
        keys_file = Path("data/secure_keys/encrypted_keys.json")
        
        if not keys_file.exists():
            return {}
        
        try:
            with open(keys_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load encrypted keys from file: {e}")
            return {}


def create_encrypted_env_template():
    """
    Utility function to create an encrypted .env template.
    
    This can be used to encrypt existing API keys for storage.
    """
    print("API Key Encryption Utility")
    print("=" * 40)
    
    # Load current keys (HackerNews needs no API key)
    current_keys = {
        'FINNHUB_API_KEY': os.getenv('FINNHUB_API_KEY', ''),
        'NEWSAPI_KEY': os.getenv('NEWSAPI_KEY', ''),
        'MARKETAUX_API_KEY': os.getenv('MARKETAUX_API_KEY', ''),
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', '')  # AI verification
    }
    
    manager = APIKeyManager()
    
    print("Encrypting API keys...")
    encrypted_keys = manager.encrypt_all_keys(current_keys)
    
    print("\nEncrypted .env template:")
    print("# Encrypted API Keys for Phase 5 Pipeline")
    from app.utils.timezone import utc_now
    print("# Generated on:", utc_now().isoformat())
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