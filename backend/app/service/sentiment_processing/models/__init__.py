"""
Sentiment Model Implementations
===============================

Collection of different sentiment analysis models:
- FinBERT: For financial news and professional content
- VADER: For social media and informal text
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
from .vader_model import VADERModel

__all__ = [
    "SentimentModel",
    "SentimentResult",
    "SentimentLabel",
    "TextInput",
    "DataSource",
    "ModelInfo",
    "SentimentModelError",
    "FinBERTModel",
    "VADERModel"
]