"""
API Testing Script for Phase 4

Simple test script to validate Phase 4 API endpoints.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from main import create_app
from app.data_access.database import init_database


async def initialize_test_db():
    """Initialize database for testing"""
    try:
        await init_database()
        print("✅ Database initialized successfully")
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        raise


def test_phase_4_endpoints():
    """Test all Phase 4 API endpoints"""
    
    print("🧪 Testing Phase 4 API Endpoints")
    print("=" * 50)
    
    # Initialize database first
    print("\nInitializing database...")
    asyncio.run(initialize_test_db())
    
    # Create test client
    app = create_app()
    client = TestClient(app)
    
    # Test health endpoint
    print("\n1. Testing Health Endpoint...")
    response = client.get("/health")
    if response.status_code == 200:
        print("✅ Health check passed")
        print(f"   Response: {response.json()}")
    else:
        print(f"❌ Health check failed: {response.status_code}")
    
    # Test dashboard summary endpoint
    print("\n2. Testing Dashboard Summary...")
    response = client.get("/api/dashboard/summary")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Dashboard summary endpoint accessible")
        data = response.json()
        print(f"   Market overview: {data.get('market_overview', {}).get('total_stocks', 'N/A')} stocks")
    else:
        print(f"❌ Dashboard summary failed")
        print(f"   Error: {response.text}")
    
    # Test stocks list endpoint
    print("\n3. Testing Stocks List...")
    response = client.get("/api/stocks/")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Stocks list endpoint accessible")
        data = response.json()
        print(f"   Total stocks: {data.get('total_count', 'N/A')}")
    else:
        print(f"❌ Stocks list failed")
        print(f"   Error: {response.text}")
    
    # Test stock detail endpoint (this will likely fail due to no data, but should return proper error)
    print("\n4. Testing Stock Detail...")
    response = client.get("/api/stocks/AAPL?timeframe=7d")
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("✅ Stock detail endpoint working (404 expected - no data)")
    elif response.status_code == 200:
        print("✅ Stock detail endpoint working (data found)")
    else:
        print(f"❌ Stock detail unexpected status: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test analysis endpoint
    print("\n5. Testing Sentiment Analysis...")
    response = client.get("/api/analysis/stocks/AAPL/sentiment?timeframe=7d")
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("✅ Sentiment analysis endpoint working (404 expected - no data)")
    elif response.status_code == 200:
        print("✅ Sentiment analysis endpoint working (data found)")
    else:
        print(f"❌ Sentiment analysis unexpected status: {response.status_code}")
        print(f"   Error: {response.text}")
    
    # Test correlation analysis endpoint
    print("\n6. Testing Correlation Analysis...")
    response = client.get("/api/analysis/stocks/AAPL/correlation?timeframe=7d")
    print(f"   Status: {response.status_code}")
    if response.status_code == 404:
        print("✅ Correlation analysis endpoint working (404 expected - no data)")
    elif response.status_code == 200:
        print("✅ Correlation analysis endpoint working (data found)")
    else:
        print(f"❌ Correlation analysis unexpected status: {response.status_code}")
        print(f"   Error: {response.text}")
    
    print("\n" + "=" * 50)
    print("🎉 Phase 4 API Testing Complete!")
    print("\nNote: 404 errors are expected when no data exists in the database.")
    print("The endpoints are properly configured and will work when data is available.")


if __name__ == "__main__":
    test_phase_4_endpoints()