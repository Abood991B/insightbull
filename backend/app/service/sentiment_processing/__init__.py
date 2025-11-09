"""
Sentiment Processing Module
==========================

Contains all sentiment analysis processing components including:
- Main sentiment engine orchestrator
- Individual model implementations (FinBERT, Hybrid VADER)
- Core sentiment model abstractions

This module handles the SY-FR3 requirement: Perform Sentiment Analysis
"""

from .sentiment_engine import SentimentEngine, EngineConfig, get_sentiment_engine, reset_sentiment_engine
from .models.finbert_model import FinBERTModel
from .models.hybrid_vader_model import HybridVADERModel, HybridConfig
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
    "get_sentiment_engine",
    "reset_sentiment_engine",
    "FinBERTModel", 
    "HybridVADERModel",
    "HybridConfig",
    "SentimentModel",
    "SentimentResult",
    "SentimentLabel", 
    "TextInput",
    "DataSource",
    "ModelInfo",
    "SentimentModelError"
]