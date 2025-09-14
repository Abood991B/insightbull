"""
Configuration settings for the backend application
"""
import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, validator
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with validation"""
    
    # Application
    APP_NAME: str = "Stock Market Sentiment Dashboard API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # API Configuration
    API_PREFIX: str = "/api"
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]
    
    # Database
    DATABASE_URL: str = Field(
        default="postgresql://postgres:password@localhost:5432/sentiment_dashboard",
        env="DATABASE_URL"
    )
    
    # Redis
    REDIS_URL: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL"
    )
    
    # Security
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        env="SECRET_KEY"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth2 (Google)
    GOOGLE_CLIENT_ID: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET: Optional[str] = Field(default=None, env="GOOGLE_CLIENT_SECRET")
    GOOGLE_REDIRECT_URI: str = Field(
        default="http://localhost:5173/admin/auth/callback",
        env="GOOGLE_REDIRECT_URI"
    )
    
    # External APIs
    REDDIT_CLIENT_ID: Optional[str] = Field(default=None, env="REDDIT_CLIENT_ID")
    REDDIT_CLIENT_SECRET: Optional[str] = Field(default=None, env="REDDIT_CLIENT_SECRET")
    REDDIT_USER_AGENT: str = Field(
        default="StockSentimentDashboard/1.0",
        env="REDDIT_USER_AGENT"
    )
    
    FINNHUB_API_KEY: Optional[str] = Field(default=None, env="FINNHUB_API_KEY")
    MARKETAUX_API_KEY: Optional[str] = Field(default=None, env="MARKETAUX_API_KEY")
    NEWSAPI_KEY: Optional[str] = Field(default=None, env="NEWSAPI_KEY")
    
    # Rate Limiting
    RATE_LIMIT_REDDIT: int = 60  # requests per minute
    RATE_LIMIT_FINNHUB: int = 60  # requests per minute
    RATE_LIMIT_MARKETAUX: int = 100  # requests per day
    RATE_LIMIT_NEWSAPI: int = 100  # requests per day
    
    # Data Pipeline
    PIPELINE_SCHEDULE: str = "*/15 * * * *"  # Every 15 minutes
    BATCH_SIZE: int = 100
    MAX_WORKERS: int = 4
    
    # Sentiment Analysis
    FINBERT_MODEL: str = "ProsusAI/finbert"
    SENTIMENT_CACHE_TTL: int = 900  # 15 minutes
    PRICE_CACHE_TTL: int = 300  # 5 minutes
    
    # WebSocket
    WEBSOCKET_ENABLED: bool = True
    WEBSOCKET_PING_INTERVAL: int = 30
    
    # Monitoring
    ENABLE_METRICS: bool = True
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @validator("CORS_ORIGINS", pre=True)
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @property
    def database_settings(self) -> Dict[str, Any]:
        """Parse database URL for SQLAlchemy settings"""
        return {
            "pool_size": 20,
            "max_overflow": 0,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance"""
    return Settings()


# Create a global settings instance
settings = get_settings()
