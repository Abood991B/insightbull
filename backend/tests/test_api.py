"""
Basic API Tests
===============

Test basic functionality of the FastAPI application.
"""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_dashboard_health(test_client: TestClient):
    """Test dashboard health endpoint."""
    response = test_client.get("/api/v1/dashboard/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["controller"] == "dashboard"


def test_sentiment_health(test_client: TestClient):
    """Test sentiment health endpoint."""
    response = test_client.get("/api/v1/sentiment/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["controller"] == "sentiment"


def test_admin_health(test_client: TestClient):
    """Test admin health endpoint."""
    response = test_client.get("/api/v1/admin/health")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "healthy"
    assert data["controller"] == "admin"


def test_dashboard_overview(test_client: TestClient):
    """Test dashboard overview endpoint."""
    response = test_client.get("/api/v1/dashboard/overview")
    assert response.status_code == 200
    
    data = response.json()
    assert "sentiment_overview" in data
    assert "time_period" in data
    assert "stock_data" in data
    assert "sentiment_trends" in data
    assert "news_summary" in data


def test_sentiment_trends(test_client: TestClient):
    """Test sentiment trends endpoint."""
    response = test_client.get("/api/v1/sentiment/trends?stock_symbol=AAPL")
    assert response.status_code == 200
    
    data = response.json()
    assert data["stock_symbol"] == "AAPL"
    assert "sentiment_data" in data
    assert "overall_sentiment" in data
    assert "confidence" in data


def test_sentiment_analysis(test_client: TestClient):
    """Test stock sentiment analysis endpoint."""
    response = test_client.get("/api/v1/sentiment/analysis/AAPL")
    assert response.status_code == 200
    
    data = response.json()
    assert data["stock_symbol"] == "AAPL"
    assert "sentiment_score" in data
    assert "confidence" in data
    assert "source_breakdown" in data


def test_system_status(test_client: TestClient):
    """Test admin system status endpoint.""" 
    response = test_client.get("/api/v1/admin/system-status")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "operational"
    assert "services" in data
    assert "metrics" in data


def test_cors_headers(test_client: TestClient):
    """Test CORS headers are properly set."""
    response = test_client.options("/health")
    assert response.status_code == 200


def test_api_documentation_available(test_client: TestClient):
    """Test that API documentation is available."""
    response = test_client.get("/api/docs")
    assert response.status_code == 200


def test_openapi_spec_available(test_client: TestClient):
    """Test that OpenAPI specification is available."""
    response = test_client.get("/api/openapi.json")
    assert response.status_code == 200
    
    data = response.json()
    assert "openapi" in data
    assert "info" in data
    assert "paths" in data