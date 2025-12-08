"""
Test Configuration
Pytest configuration and fixtures for backend testing.
"""

import pytest
import asyncio
import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, Mock

from app.data_access.database.base import Base
from app.data_access.database.connection import get_db
from main import create_app

# Test database URL (use in-memory SQLite for testing)
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

# Configure pytest-asyncio mode
pytest_plugins = ("pytest_asyncio",)

@pytest.fixture(scope="function")
def client():
    """Create test client with mocked database."""
    app = create_app()
    
    # Mock the database dependency completely
    def mock_get_db():
        # Return a mock session that doesn't require database connection
        mock_session = Mock()
        mock_session.commit = AsyncMock()
        mock_session.rollback = AsyncMock()
        mock_session.close = AsyncMock()
        mock_session.add = Mock()
        mock_session.execute = AsyncMock()
        mock_session.scalar = AsyncMock()
        return mock_session
    
    app.dependency_overrides[get_db] = mock_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_admin_auth():
    """Mock admin authentication for testing."""
    mock_admin = {
        "id": "test-admin-id", 
        "email": "admin@test.com",
        "permissions": ["admin"]
    }
    
    mock_func = AsyncMock(return_value=mock_admin)
    return mock_func

@pytest.fixture
def mock_db_session():
    """Mock database session for testing."""
    mock_session = Mock()
    mock_session.commit = AsyncMock()
    mock_session.rollback = AsyncMock()
    mock_session.close = AsyncMock()
    mock_session.add = Mock()
    mock_session.execute = AsyncMock()
    mock_session.scalar = AsyncMock()
    return mock_session

@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Create a real async database session for integration tests.
    Uses in-memory SQLite database that is recreated for each test.
    """
    # Create async engine for in-memory SQLite
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Create session factory
    async_session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Yield session for test
    async with async_session_factory() as session:
        yield session
    
    # Cleanup - drop all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()