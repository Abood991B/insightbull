"""
Test Configuration and Fixtures
================================

Shared fixtures and configuration for all test modules.
Provides test database sessions, mock data, and reusable test utilities.
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator, Generator
from unittest.mock import MagicMock, AsyncMock, patch
from datetime import datetime, timedelta
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Test database URL (in-memory SQLite for isolation)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db_engine():
    """Create a test database engine."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    yield engine
    await engine.dispose()


@pytest.fixture
async def test_db_session(test_db_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async_session = sessionmaker(
        test_db_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


# ============================================================================
# Mock Data Fixtures
# ============================================================================

@pytest.fixture
def mock_stock_data():
    """Mock stock data for testing."""
    return [
        {"symbol": "AAPL", "name": "Apple Inc.", "is_active": True},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "is_active": True},
        {"symbol": "GOOGL", "name": "Alphabet Inc.", "is_active": True},
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "is_active": True},
        {"symbol": "TSLA", "name": "Tesla Inc.", "is_active": True},
    ]


@pytest.fixture
def mock_sentiment_data():
    """Mock sentiment data for testing."""
    return [
        {
            "symbol": "AAPL",
            "sentiment_label": "positive",
            "sentiment_score": 0.85,
            "confidence": 0.92,
            "source": "news",
            "content": "Apple reports record quarterly earnings",
            "analyzed_at": datetime.utcnow()
        },
        {
            "symbol": "MSFT",
            "sentiment_label": "positive",
            "sentiment_score": 0.78,
            "confidence": 0.88,
            "source": "news",
            "content": "Microsoft cloud revenue exceeds expectations",
            "analyzed_at": datetime.utcnow()
        },
        {
            "symbol": "TSLA",
            "sentiment_label": "negative",
            "sentiment_score": -0.45,
            "confidence": 0.75,
            "source": "hackernews",
            "content": "Tesla faces production challenges in Q4",
            "analyzed_at": datetime.utcnow()
        },
        {
            "symbol": "GOOGL",
            "sentiment_label": "neutral",
            "sentiment_score": 0.02,
            "confidence": 0.65,
            "source": "news",
            "content": "Google announces new AI research partnership",
            "analyzed_at": datetime.utcnow()
        },
    ]


@pytest.fixture
def mock_news_articles():
    """Mock news articles for testing."""
    return [
        {
            "title": "Apple Unveils New iPhone Features",
            "content": "Apple announced new features for the upcoming iPhone release, including advanced AI capabilities.",
            "source": "TechNews",
            "url": "https://example.com/apple-iphone",
            "published_at": datetime.utcnow() - timedelta(hours=2),
            "symbol": "AAPL"
        },
        {
            "title": "Microsoft Azure Growth Continues",
            "content": "Microsoft reported strong growth in its Azure cloud platform with enterprise adoption increasing.",
            "source": "BusinessDaily",
            "url": "https://example.com/msft-azure",
            "published_at": datetime.utcnow() - timedelta(hours=4),
            "symbol": "MSFT"
        },
    ]


@pytest.fixture
def mock_price_data():
    """Mock stock price data for testing."""
    base_time = datetime.utcnow()
    return [
        {
            "symbol": "AAPL",
            "price": 195.50,
            "change_percent": 1.25,
            "volume": 45000000,
            "timestamp": base_time
        },
        {
            "symbol": "MSFT",
            "price": 420.75,
            "change_percent": 0.85,
            "volume": 22000000,
            "timestamp": base_time
        },
        {
            "symbol": "GOOGL",
            "price": 175.25,
            "change_percent": -0.45,
            "volume": 18000000,
            "timestamp": base_time
        },
    ]


@pytest.fixture
def mock_api_config():
    """Mock API configuration for testing."""
    return {
        "hackernews": {
            "enabled": True,
            "requires_api_key": False,
            "rate_limit": 100
        },
        "finnhub": {
            "enabled": True,
            "requires_api_key": True,
            "api_key": "test_finnhub_key_12345",
            "rate_limit": 60
        },
        "newsapi": {
            "enabled": True,
            "requires_api_key": True,
            "api_key": "test_newsapi_key_67890",
            "rate_limit": 100
        },
        "gdelt": {
            "enabled": True,
            "requires_api_key": False,
            "rate_limit": 50
        },
        "yfinance": {
            "enabled": True,
            "requires_api_key": False,
            "rate_limit": 200
        }
    }


@pytest.fixture
def mock_admin_user():
    """Mock admin user for testing authenticated endpoints."""
    return {
        "email": "admin@insightstock.com",
        "name": "Test Admin",
        "is_admin": True,
        "session_id": "test_session_12345",
        "totp_verified": True
    }


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture
def mock_http_response():
    """Factory for creating mock HTTP responses."""
    def _create_response(status_code: int = 200, json_data: dict = None):
        response = MagicMock()
        response.status_code = status_code
        response.json.return_value = json_data or {}
        response.raise_for_status = MagicMock()
        if status_code >= 400:
            response.raise_for_status.side_effect = Exception(f"HTTP {status_code}")
        return response
    return _create_response


@pytest.fixture
def mock_async_http_client():
    """Mock async HTTP client for API tests."""
    client = AsyncMock()
    client.get = AsyncMock()
    client.post = AsyncMock()
    client.put = AsyncMock()
    client.delete = AsyncMock()
    return client


# ============================================================================
# Sentiment Analysis Fixtures
# ============================================================================

@pytest.fixture
def sample_financial_texts():
    """Sample financial texts for sentiment analysis testing."""
    return {
        "positive": [
            "Apple reports record-breaking quarterly revenue with strong iPhone sales",
            "Microsoft cloud services show exceptional growth exceeding all expectations",
            "NVIDIA stock surges as AI demand continues to drive unprecedented growth",
            "Tesla deliveries beat analyst expectations with record Q4 numbers",
        ],
        "negative": [
            "Company faces significant regulatory challenges that could impact revenue",
            "Stock plunges after disappointing earnings report misses expectations",
            "Layoffs announced as tech sector continues cost-cutting measures",
            "Investigation launched into potential accounting irregularities",
        ],
        "neutral": [
            "Company announces upcoming investor conference scheduled for next quarter",
            "Board of directors meets to discuss annual strategic planning",
            "New office location announced in downtown metropolitan area",
            "Standard quarterly filing submitted to regulatory authorities",
        ]
    }


@pytest.fixture
def mock_finbert_output():
    """Mock FinBERT model output for testing."""
    return {
        "label": "positive",
        "score": 0.89,
        "confidence": 0.92,
        "logits": [0.15, 0.08, 0.89]
    }


# ============================================================================
# Pipeline Fixtures
# ============================================================================

@pytest.fixture
def mock_pipeline_config():
    """Mock pipeline configuration for testing."""
    return {
        "symbols": ["AAPL", "MSFT", "GOOGL"],
        "date_range": {
            "start": datetime.utcnow() - timedelta(days=1),
            "end": datetime.utcnow()
        },
        "max_items_per_symbol": 10,
        "include_hackernews": True,
        "include_finnhub": True,
        "include_newsapi": True,
        "include_gdelt": True,
        "include_yfinance": True,
        "parallel_collectors": True
    }


@pytest.fixture
def mock_collection_result():
    """Mock data collection result."""
    return {
        "status": "completed",
        "items_collected": 45,
        "sources": {
            "hackernews": 12,
            "finnhub": 10,
            "newsapi": 15,
            "gdelt": 8
        },
        "duration_seconds": 12.5,
        "errors": []
    }


# ============================================================================
# Utility Functions
# ============================================================================

def create_test_timestamp(days_ago: int = 0, hours_ago: int = 0) -> datetime:
    """Create a test timestamp relative to now."""
    return datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)


def assert_api_response_valid(response: dict, required_keys: list):
    """Assert that an API response contains required keys."""
    for key in required_keys:
        assert key in response, f"Missing required key: {key}"
