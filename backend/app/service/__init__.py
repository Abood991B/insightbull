"""
Service Layer
=============

Application services for data collection and sentiment processing.
Orchestrates business logic and coordinates between layers.
"""

from .sentiment_processing import SentimentEngine
from .data_collection import DataCollectionService, data_collection_service

__all__ = [
    "SentimentEngine",
    "DataCollectionService",
    "data_collection_service"
]