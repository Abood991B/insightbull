"""
Routes package initialization

Centralizes all API route imports for the presentation layer.
"""

from .dashboard import router as dashboard_router
from .stocks import router as stocks_router  
from .analysis import router as analysis_router

__all__ = ["dashboard_router", "stocks_router", "analysis_router"]