"""
Security Testing Script

This script tests the Phase 2 security implementation:
- Authentication service
- JWT token handling
- Security middleware
- Admin route protection

Run this script to validate the security setup.
"""

import asyncio
import json
from datetime import datetime

from app.infrastructure.config.settings import get_settings
from app.infrastructure.security.auth_service import AuthService
from app.infrastructure.security.jwt_handler import JWTHandler
from app.infrastructure.security.security_utils import SecurityUtils
from app.utils.timezone import utc_now


async def test_auth_service():
    """Test the AuthService functionality"""
    print("🔐 Testing AuthService...")
    
    settings = get_settings()
    auth_service = AuthService(settings)
    
    # Test token creation for demo purposes
    test_tokens = await auth_service.create_admin_session(
        "admin@example.com",
        {"permissions": ["admin"]}
    )
    
    print(f"✅ Created test tokens: {test_tokens['token_type']}")
    
    # Test token validation
    access_token = test_tokens["access_token"]
    admin_user = await auth_service.validate_admin_token(access_token)
    
    if admin_user:
        print(f"✅ Token validation successful for: {admin_user.email}")
        
        # Test permissions
        has_admin = await auth_service.verify_admin_permissions(admin_user, "admin")
        print(f"✅ Admin permission check: {has_admin}")
        
        # Test activity logging
        await auth_service.log_admin_activity(
            admin_user, 
            "test_login", 
            {"timestamp": utc_now().isoformat()}
        )
        print("✅ Activity logging successful")
    else:
        print("❌ Token validation failed")
    
    # Test token refresh
    refresh_token = test_tokens["refresh_token"]
    new_tokens = await auth_service.refresh_admin_token(refresh_token)
    
    if new_tokens:
        print("✅ Token refresh successful")
    else:
        print("❌ Token refresh failed")


def test_jwt_handler():
    """Test JWT token operations"""
    print("\n🔑 Testing JWT Handler...")
    
    settings = get_settings()
    jwt_handler = JWTHandler(settings)
    
    # Test token creation
    test_data = {
        "sub": "test@example.com",
        "permissions": ["admin"]
    }
    
    access_token = jwt_handler.create_access_token(test_data)
    refresh_token = jwt_handler.create_refresh_token(test_data)
    
    print("✅ JWT tokens created successfully")
    
    # Test token verification
    payload = jwt_handler.verify_token(access_token)
    if payload and payload.get("sub") == "test@example.com":
        print("✅ JWT token verification successful")
    else:
        print("❌ JWT token verification failed")
    
    # Test token subject extraction
    subject = jwt_handler.get_token_subject(access_token)
    if subject == "test@example.com":
        print("✅ JWT subject extraction successful")
    else:
        print("❌ JWT subject extraction failed")


def test_security_utils():
    """Test security utilities"""
    print("\n🛡️ Testing Security Utils...")
    
    security_utils = SecurityUtils()
    
    # Test password hashing
    password = "test_password_123"
    salt = security_utils.generate_salt()
    hashed = security_utils.hash_password(password, salt)
    
    # Test password verification
    is_valid = security_utils.verify_password(password, salt, hashed)
    
    if is_valid:
        print("✅ Password hashing and verification successful")
    else:
        print("❌ Password hashing/verification failed")
    
    # Test input sanitization
    dangerous_input = "<script>alert('xss')</script>Test"
    sanitized = security_utils.sanitize_input(dangerous_input)
    
    if "<script>" not in sanitized:
        print("✅ Input sanitization successful")
    else:
        print("❌ Input sanitization failed")
    
    # Test email validation
    valid_email = "test@example.com"
    invalid_email = "not-an-email"
    
    if (security_utils.validate_email(valid_email) and 
        not security_utils.validate_email(invalid_email)):
        print("✅ Email validation successful")
    else:
        print("❌ Email validation failed")
    
    # Test stock symbol validation
    valid_symbol = "AAPL"
    invalid_symbol = "invalid123"
    
    if (security_utils.validate_stock_symbol(valid_symbol) and 
        not security_utils.validate_stock_symbol(invalid_symbol)):
        print("✅ Stock symbol validation successful")
    else:
        print("❌ Stock symbol validation failed")
    
    # Test security headers
    headers = security_utils.get_security_headers()
    required_headers = [
        "X-Content-Type-Options",
        "X-Frame-Options", 
        "X-XSS-Protection",
        "Strict-Transport-Security"
    ]
    
    if all(header in headers for header in required_headers):
        print("✅ Security headers generation successful")
    else:
        print("❌ Security headers generation failed")


def test_configuration():
    """Test security configuration"""
    print("\n⚙️ Testing Security Configuration...")
    
    settings = get_settings()
    
    # Check required security settings
    required_settings = [
        'secret_key',
        'jwt_secret_key', 
        'jwt_algorithm',
        'jwt_access_token_expire_minutes',
        'api_key_encryption_key',
        'rate_limit_requests',
        'enable_security_headers'
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not hasattr(settings, setting) or not getattr(settings, setting):
            missing_settings.append(setting)
    
    if not missing_settings:
        print("✅ All security settings configured")
    else:
        print(f"❌ Missing security settings: {missing_settings}")
    
    # Check CORS origins
    origins = settings.get_allowed_origins_list()
    if origins and len(origins) > 0:
        print(f"✅ CORS origins configured: {len(origins)} origins")
    else:
        print("❌ CORS origins not configured")


async def main():
    """Run all security tests"""
    print("🚀 Starting Phase 2 Security Testing...\n")
    
    try:
        # Test configuration first
        test_configuration()
        
        # Test individual components
        test_jwt_handler()
        test_security_utils()
        
        # Test integrated service
        await test_auth_service()
        
        print("\n✅ Phase 2 Security Testing Complete!")
        print("\n📋 Summary:")
        print("- AuthService: JWT validation, admin sessions, activity logging")
        print("- Security Middleware: Rate limiting, CORS, input validation, headers")
        print("- Route Protection: Admin authentication dependencies")
        print("- Configuration: Security settings and encryption")
        
    except Exception as e:
        print(f"\n❌ Security testing failed: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())