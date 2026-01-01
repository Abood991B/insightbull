"""
Sentiment Analysis Models
========================

Implementation of the Strategy pattern for sentiment analysis.
Uses FinBERT-Tone (yiyanghkust/finbert-tone) unified model for all sources.

Following FYP Report specification for SY-FR3 (Perform Sentiment Analysis).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import asyncio
from app.infrastructure.log_system import get_logger
from app.utils.timezone import utc_now

# Import DataSource from the canonical location
from ....infrastructure.collectors.base_collector import DataSource

logger = get_logger()


class SentimentLabel(Enum):
    """Standardized sentiment labels across all models."""
    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


@dataclass
class SentimentResult:
    """
    Standardized sentiment analysis result.
    
    Attributes:
        label: Sentiment classification (positive, negative, neutral)
        score: Normalized confidence score [-1.0 to 1.0]
        confidence: Model confidence in prediction [0.0 to 1.0]
        raw_scores: Original model scores for debugging
        processing_time: Time taken for analysis in milliseconds
        model_name: Name of the model used
        text: Original text that was analyzed
        source: Data source of the text
        metadata: Additional context from input (stock_id, article_id, etc.)
    """
    label: SentimentLabel
    score: float  # -1.0 (very negative) to 1.0 (very positive)
    confidence: float  # 0.0 to 1.0
    raw_scores: Dict[str, float]
    processing_time: float
    model_name: str
    text: str = ""  # Original text analyzed
    source: Optional[DataSource] = None  # Data source
    metadata: Optional[Dict[str, Any]] = None  # Context from input


@dataclass
class ModelInfo:
    """
    Model metadata and capabilities.
    
    Attributes:
        name: Model name
        version: Model version
        description: Model description
        supported_sources: Data sources this model handles
        max_batch_size: Maximum texts per batch
        avg_processing_time: Average processing time per text (ms)
    """
    name: str
    version: str
    description: str
    supported_sources: List[DataSource]
    max_batch_size: int
    avg_processing_time: float


@dataclass
class TextInput:
    """
    Input text with metadata for sentiment analysis.
    
    Attributes:
        text: Raw text content
        source: Data source type
        stock_symbol: Associated stock symbol (if any)
        timestamp: When the text was created
        metadata: Additional context information
    """
    text: str
    source: DataSource
    stock_symbol: Optional[str] = None
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


class SentimentModel(ABC):
    """
    Abstract base class for sentiment analysis models.
    
    Implements Strategy pattern allowing interchangeable sentiment analysis models.
    Each model handles specific data sources and provides standardized output.
    """
    
    def __init__(self):
        self.model_info = self._initialize_model_info()
        self._is_loaded = False
        self._load_lock = asyncio.Lock()
    
    @abstractmethod
    def _initialize_model_info(self) -> ModelInfo:
        """Initialize model metadata. Implemented by concrete classes."""
        pass
    
    @abstractmethod
    async def _load_model(self) -> None:
        """Load the actual model. Implemented by concrete classes."""
        pass
    
    @abstractmethod
    async def _analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Perform sentiment analysis on a batch of texts.
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            List of sentiment results in the same order as input
        """
        pass
    
    async def ensure_loaded(self) -> None:
        """Ensure model is loaded (thread-safe lazy loading)."""
        if not self._is_loaded:
            async with self._load_lock:
                if not self._is_loaded:
                    logger.info(f"Loading {self.model_info.name} model...")
                    await self._load_model()
                    self._is_loaded = True
                    logger.info(f"{self.model_info.name} model loaded successfully")
    
    async def analyze(self, inputs: List[TextInput]) -> List[SentimentResult]:
        """
        Analyze sentiment for multiple text inputs.
        
        Args:
            inputs: List of TextInput objects to analyze
            
        Returns:
            List of SentimentResult objects
            
        Raises:
            ValueError: If any input is invalid
            RuntimeError: If model fails to load or analyze
        """
        if not inputs:
            return []
        
        # Validate inputs
        self._validate_inputs(inputs)
        
        # Ensure model is loaded
        await self.ensure_loaded()
        
        # Extract texts for batch processing
        texts = [input_item.text for input_item in inputs]
        
        # Process in batches to avoid memory issues
        results = []
        batch_size = self.model_info.max_batch_size
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_inputs = inputs[i:i + batch_size]
            batch_results = await self._analyze_batch(batch_texts)
            
            # Populate text, source, and metadata from inputs
            for j, result in enumerate(batch_results):
                input_obj = batch_inputs[j]
                result.text = input_obj.text
                result.source = input_obj.source
                result.metadata = input_obj.metadata or {}
            
            results.extend(batch_results)
        
        return results
    
    def _validate_inputs(self, inputs: List[TextInput]) -> None:
        """Validate input texts and metadata."""
        for i, input_item in enumerate(inputs):
            if not input_item.text or not input_item.text.strip():
                raise ValueError(f"Input {i}: Text cannot be empty")
            
            if input_item.source not in self.model_info.supported_sources:
                raise ValueError(
                    f"Input {i}: Source {input_item.source} not supported by {self.model_info.name}"
                )
            
            if len(input_item.text) > 10000:  # Reasonable limit
                logger.warning(f"Input {i}: Text length {len(input_item.text)} is very long")
    
    def get_model_info(self) -> ModelInfo:
        """Get model information and capabilities."""
        return self.model_info
    
    def supports_source(self, source: DataSource) -> bool:
        """Check if this model supports a specific data source."""
        return source in self.model_info.supported_sources
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform model health check.
        
        Returns:
            Dictionary with health status information
        """
        try:
            await self.ensure_loaded()
            
            # Test with a simple input
            test_input = TextInput(
                text="Test sentiment analysis",
                source=self.model_info.supported_sources[0]
            )
            
            start_time = utc_now()
            result = await self.analyze([test_input])
            end_time = utc_now()
            
            processing_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "status": "healthy",
                "model_name": self.model_info.name,
                "is_loaded": self._is_loaded,
                "test_processing_time_ms": processing_time,
                "test_result": {
                    "label": result[0].label.value,
                    "score": result[0].score,
                    "confidence": result[0].confidence
                }
            }
            
        except Exception as e:
            logger.error(f"Health check failed for {self.model_info.name}: {str(e)}")
            return {
                "status": "unhealthy",
                "model_name": self.model_info.name,
                "is_loaded": self._is_loaded,
                "error": str(e)
            }


class SentimentModelError(Exception):
    """Base exception for sentiment model errors."""
    pass


class ModelLoadError(SentimentModelError):
    """Exception raised when model fails to load."""
    pass


class AnalysisError(SentimentModelError):
    """Exception raised when sentiment analysis fails."""
    pass