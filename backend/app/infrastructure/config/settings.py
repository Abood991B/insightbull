"""
Application Configuration
========================

Centralized configuration management using Pydantic Settings.
Handles environment variables, validation, and configuration loading.
"""

from typing import List, Optional, Union
from pydantic import Field
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    """All application settings in one class."""
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./data/insight_stock.db"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "insight_stock.db"
    database_user: str = ""
    database_password: str = ""
    
    # API Keys
    finnhub_api_key: str = ""
    news_api_key: str = ""
    
    # HackerNews API - No API key required (free and unlimited)
    # YFinance - No API key required (free and unlimited)
    
    # Application Settings
    app_name: str = "Insight Stock Dashboard"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    environment: str = Field(default="production", description="Environment: development, staging, production")
    
    # Security
    secret_key: str = secrets.token_urlsafe(32)
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # Google OAuth2 Configuration
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # Admin Configuration
    admin_emails: Optional[List[str]] = Field(default_factory=list)
    
    @field_validator('admin_emails', mode='before')
    @classmethod
    def parse_admin_emails(cls, v):
        """Parse comma-separated admin emails from environment variable."""
        if isinstance(v, str):
            return [email.strip() for email in v.split(',') if email.strip()]
        return v or []
    
    # API Key Encryption (REQUIRED — no auto-generation)
    api_encryption_key: str = ""
    api_encryption_salt: str = ""

    @field_validator('api_encryption_key', mode='after')
    @classmethod
    def validate_encryption_key(cls, v):
        """Warn if encryption key is not set."""
        if not v:
            import warnings
            warnings.warn(
                "API_ENCRYPTION_KEY is not set. "
                "API key encryption will fail at runtime. "
                "Generate one: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
        return v

    # Rate Limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600  # 1 hour in seconds
    
    # Security Headers
    enable_security_headers: bool = True
    csrf_protection: bool = True
    
    # Proxy Trust — set True only if behind a trusted reverse proxy
    trust_proxy_headers: bool = False
    
    # CORS Settings
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8080,http://127.0.0.1:3000,http://127.0.0.1:8080"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    # AI Verification Configuration
    ai_verification_mode: str = "low_confidence_and_neutral"  # none, low_confidence, neutral_only, low_confidence_and_neutral, all
    ai_confidence_threshold: float = 0.85
    
    def get_allowed_origins_list(self) -> List[str]:
        """Convert allowed_origins string to list."""
        if isinstance(self.allowed_origins, str):
            return [origin.strip() for origin in self.allowed_origins.split(',')]
        return self.allowed_origins

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()