"""
Security Utilities for Backend System

This module provides security utilities including:
- Password hashing and verification
- API key encryption/decryption  
- Input sanitization
- Security headers

Following FYP security requirements and best practices.
"""

import hashlib
import secrets
import base64
import re
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import html


class SecurityUtils:
    """Security utility functions for the application"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize security utils with optional encryption key
        
        Args:
            encryption_key: Key for API key encryption
        """
        if encryption_key:
            self.cipher_suite = Fernet(encryption_key)
        else:
            self.cipher_suite = None
    
    @staticmethod
    def generate_salt() -> str:
        """Generate random salt for password hashing"""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """
        Hash password with salt using PBKDF2
        
        Args:
            password: Plain text password
            salt: Random salt string
            
        Returns:
            Hashed password string
        """
        password_bytes = password.encode('utf-8')
        salt_bytes = salt.encode('utf-8')
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt_bytes,
            iterations=100000,
        )
        key = kdf.derive(password_bytes)
        return base64.urlsafe_b64encode(key).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, salt: str, hashed_password: str) -> bool:
        """
        Verify password against hashed version
        
        Args:
            password: Plain text password to verify
            salt: Salt used in original hash
            hashed_password: Original hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return SecurityUtils.hash_password(password, salt) == hashed_password
    
    def encrypt_api_key(self, api_key: str) -> Optional[str]:
        """
        Encrypt API key for secure storage
        
        Args:
            api_key: Plain text API key
            
        Returns:
            Encrypted API key or None if cipher not initialized
        """
        if not self.cipher_suite:
            return None
        
        encrypted_key = self.cipher_suite.encrypt(api_key.encode('utf-8'))
        return base64.urlsafe_b64encode(encrypted_key).decode('utf-8')
    
    def decrypt_api_key(self, encrypted_key: str) -> Optional[str]:
        """
        Decrypt API key from storage
        
        Args:
            encrypted_key: Encrypted API key string
            
        Returns:
            Decrypted API key or None if decryption fails
        """
        if not self.cipher_suite:
            return None
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode('utf-8'))
            decrypted_key = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_key.decode('utf-8')
        except Exception:
            return None
    
    @staticmethod
    def sanitize_input(input_string: str) -> str:
        """
        Sanitize user input to prevent XSS attacks
        
        Args:
            input_string: Raw user input
            
        Returns:
            Sanitized input string
        """
        if not input_string:
            return ""
        
        # HTML escape
        sanitized = html.escape(input_string)
        
        # Remove potentially dangerous patterns
        dangerous_patterns = [
            r'<script.*?</script>',
            r'javascript:',
            r'onload=',
            r'onerror=',
            r'onclick=',
        ]
        
        for pattern in dangerous_patterns:
            sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """
        Validate email format
        
        Args:
            email: Email string to validate
            
        Returns:
            True if valid email format, False otherwise
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_stock_symbol(symbol: str) -> bool:
        """
        Validate stock symbol format
        
        Args:
            symbol: Stock symbol to validate
            
        Returns:
            True if valid symbol format, False otherwise
        """
        if not symbol:
            return False
        
        # Stock symbols: 1-5 uppercase letters
        pattern = r'^[A-Z]{1,5}$'
        return bool(re.match(pattern, symbol.upper()))
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token for form protection"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """
        Get security headers for HTTP responses
        
        Returns:
            Dictionary of security headers
        """
        return {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'",
            "Referrer-Policy": "strict-origin-when-cross-origin"
        }
    
    @staticmethod
    def is_safe_redirect_url(url: str, allowed_hosts: list) -> bool:
        """
        Check if redirect URL is safe (prevents open redirect)
        
        Args:
            url: URL to validate
            allowed_hosts: List of allowed host domains
            
        Returns:
            True if URL is safe to redirect to, False otherwise
        """
        if not url:
            return False
        
        # Check for absolute URLs
        if url.startswith('http://') or url.startswith('https://'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            return parsed.hostname in allowed_hosts
        
        # Relative URLs are generally safe
        return url.startswith('/')
    
    @staticmethod
    def generate_api_key() -> str:
        """Generate secure API key"""
        return secrets.token_urlsafe(32)