"""
API router configuration
"""
from fastapi import APIRouter
from .routes import stocks, sentiment, prices, correlation, admin, auth

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(stocks.router, prefix="/stocks", tags=["Stocks"])
api_router.include_router(sentiment.router, prefix="/sentiment", tags=["Sentiment"])
api_router.include_router(prices.router, prefix="/prices", tags=["Prices"])
api_router.include_router(correlation.router, prefix="/correlation", tags=["Correlation"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin"])
