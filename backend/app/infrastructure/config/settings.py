"""
Application Configuration
========================

Centralized configuration management using Pydantic Settings.
Handles environment variables, validation, and configuration loading.
"""

from typing import List, Optional, Union
from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache
import secrets


class Settings(BaseSettings):
    """All application settings in one class."""
    
    # Database Configuration
    database_url: str = "sqlite+aiosqlite:///./insight_stock_db.sqlite"
    database_host: str = "localhost"
    database_port: int = 5432
    database_name: str = "insight_stock_db"
    database_user: str = ""
    database_password: str = ""
    
    # API Keys
    finnhub_api_key: str = ""
    marketaux_api_key: str = ""
    news_api_key: str = ""
    
    # Reddit API Configuration
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    reddit_user_agent: str = "InsightStockDash/1.0"
    
    # Application Settings
    app_name: str = "Insight Stock Dashboard"
    app_version: str = "1.0.0"
    debug: bool = True
    environment: str = "development"
    
    # Security
    secret_key: str = secrets.token_urlsafe(32)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # CORS Settings
    allowed_origins: str = "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000"
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
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