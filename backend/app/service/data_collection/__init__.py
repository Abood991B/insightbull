"""
Data Collection Service Layer
============================

Service layer for data collection operations.
Provides business logic wrapper around infrastructure collectors.

Components:
- DataCollectionService: Main service with business logic
- CollectionRequest/Result: Data transfer objects
- Business validation and transformation rules
"""

from .service import (
    DataCollectionService,
    CollectionRequest,
    CollectionResult,
    data_collection_service
)

__all__ = [
    'DataCollectionService',
    'CollectionRequest',
    'CollectionResult', 
    'data_collection_service'
]