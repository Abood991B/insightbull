"""
Content Validation Service
==========================

Provides content relevance validation for the sentiment analysis pipeline.
Filters out non-financial content (sports, entertainment, etc.) before processing.
"""

from .relevance_validator import (
    FinancialContentValidator,
    RelevanceResult,
    get_content_validator
)

__all__ = [
    "FinancialContentValidator",
    "RelevanceResult",
    "get_content_validator"
]
