"""
Sentiment Model Implementations
===============================

Collection of sentiment analysis models:
- FinBERTModel: FinBERT-Tone for ALL content sources (95.7% avg confidence)
- DistilBERTFinancialModel: Lightweight ensemble model for confidence voting (82M params)
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
from .distilbert_model import DistilBERTFinancialModel

__all__ = [
    "SentimentModel",
    "SentimentResult",
    "SentimentLabel",
    "TextInput",
    "DataSource",
    "ModelInfo",
    "SentimentModelError",
    "FinBERTModel",
    "DistilBERTFinancialModel"
]