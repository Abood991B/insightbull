#!/usr/bin/env python
"""
Quick API test script to verify backend endpoints
"""
import asyncio
import httpx
import json
from datetime import datetime

BASE_URL = "http://localhost:3000/api"

async def test_endpoints():
    """Test various API endpoints"""
    print("=" * 60)
    print("Testing Stock Market Sentiment Dashboard API")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        try:
            response = await client.get("http://localhost:3000/health")
            if response.status_code == 200:
                print("✓ Health check passed")
            else:
                print(f"✗ Health check failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Cannot connect to server: {e}")
            print("  Make sure the server is running: uvicorn main:app --port 3000")
            return
        
        # Test stocks endpoint
        try:
            response = await client.get(f"{BASE_URL}/stocks")
            if response.status_code == 200:
                stocks = response.json()
                print(f"✓ Stocks endpoint: {len(stocks)} stocks found")
                
                # Test individual stock
                if stocks:
                    symbol = stocks[0]['symbol']
                    response = await client.get(f"{BASE_URL}/stocks/{symbol}")
                    if response.status_code == 200:
                        print(f"✓ Individual stock endpoint: {symbol}")
            else:
                print(f"✗ Stocks endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Stocks endpoint error: {e}")
        
        # Test sentiment endpoint
        try:
            response = await client.get(f"{BASE_URL}/sentiment/MSFT?time_range=7d")
            if response.status_code == 200:
                print("✓ Sentiment endpoint working")
            elif response.status_code == 404:
                print("⚠ Sentiment endpoint: No data yet (run data collection)")
            else:
                print(f"✗ Sentiment endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Sentiment endpoint error: {e}")
        
        # Test price endpoint
        try:
            response = await client.get(f"{BASE_URL}/prices/MSFT")
            if response.status_code == 200:
                print("✓ Price endpoint working")
            elif response.status_code == 404:
                print("⚠ Price endpoint: No data yet (run data collection)")
            else:
                print(f"✗ Price endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Price endpoint error: {e}")
        
        # Test correlation endpoint
        try:
            response = await client.get(f"{BASE_URL}/correlation/MSFT?time_window=7d")
            if response.status_code == 200:
                print("✓ Correlation endpoint working")
            elif response.status_code == 404:
                print("⚠ Correlation endpoint: Insufficient data")
            else:
                print(f"✗ Correlation endpoint failed: {response.status_code}")
        except Exception as e:
            print(f"✗ Correlation endpoint error: {e}")
        
        print("=" * 60)
        print("API test completed")
        print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test_endpoints())
