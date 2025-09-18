"""
Data Collection Base Classes
===========================

Base classes and interfaces for data collection services.
Provides common structure for different data source collectors.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass


@dataclass
class CollectionResult:
    """Result of a data collection operation."""
    success: bool
    data_count: int
    source: str
    timestamp: datetime
    errors: List[str]


class DataCollector(ABC):
    """Abstract base class for all data collectors."""
    
    def __init__(self, source_name: str):
        self.source_name = source_name
    
    @abstractmethod
    async def collect(self, **kwargs) -> CollectionResult:
        """Collect data from the source."""
        pass
    
    @abstractmethod
    async def validate_data(self, data: Any) -> bool:
        """Validate collected data."""
        pass


# Implementations extending these base classes:
# - StockPriceCollector(DataCollector)
# - NewsCollector(DataCollector)  
# - RedditCollector(DataCollector)