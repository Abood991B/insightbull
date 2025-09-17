"""
Sentiment Processing Module
==========================

Contains all sentiment analysis processing components including:
- Main sentiment engine orchestrator
- Individual model implementations (FinBERT, VADER)
- Core sentiment model abstractions

This module handles the SY-FR3 requirement: Perform Sentiment Analysis
"""

from .sentiment_engine import SentimentEngine, EngineConfig
from .models.finbert_model import FinBERTModel
from .models.vader_model import VADERModel
from .models.sentiment_model import (
    SentimentModel,
    SentimentResult,
    SentimentLabel,
    TextInput,
    DataSource,
    ModelInfo,
    SentimentModelError
)

__all__ = [
    "SentimentEngine",
    "EngineConfig",
    "FinBERTModel", 
    "VADERModel",
    "SentimentModel",
    "SentimentResult",
    "SentimentLabel", 
    "TextInput",
    "DataSource",
    "ModelInfo",
    "SentimentModelError"
]