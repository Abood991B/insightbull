"""
Sentiment Processing Module
==========================

Contains all sentiment analysis processing components including:
- Main sentiment engine orchestrator
- FinBERT-Tone model implementation (95.7% avg confidence)
- Core sentiment model abstractions

This module handles the SY-FR3 requirement: Perform Sentiment Analysis
"""

from .sentiment_engine import SentimentEngine, EngineConfig, get_sentiment_engine, reset_sentiment_engine
from .models.finbert_model import FinBERTModel
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
    "SentimentModel",
    "SentimentResult",
    "SentimentLabel", 
    "TextInput",
    "DataSource",
    "ModelInfo",
    "SentimentModelError"
]