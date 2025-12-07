"""
Sentiment Model Implementations
===============================

Collection of sentiment analysis models:
- FinBERTModel: FinBERT-Tone for ALL content sources (95.7% avg confidence)
- Base SentimentModel: Abstract interface for all models
"""

from .sentiment_model import (
    SentimentModel,
    SentimentResult,
    SentimentLabel,
    TextInput,
    DataSource,
    ModelInfo,
    SentimentModelError
)
from .finbert_model import FinBERTModel

__all__ = [
    "SentimentModel",
    "SentimentResult",
    "SentimentLabel",
    "TextInput",
    "DataSource",
    "ModelInfo",
    "SentimentModelError",
    "FinBERTModel"
]