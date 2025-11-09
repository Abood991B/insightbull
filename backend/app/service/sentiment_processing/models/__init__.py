"""
Sentiment Model Implementations
===============================

Collection of different sentiment analysis models:
- FinBERT: For financial news and professional content
- Hybrid VADER: For social media with Enhanced VADER + ML ensemble
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
from .hybrid_vader_model import HybridVADERModel

__all__ = [
    "SentimentModel",
    "SentimentResult",
    "SentimentLabel",
    "TextInput",
    "DataSource",
    "ModelInfo",
    "SentimentModelError",
    "FinBERTModel",
    "HybridVADERModel"
]