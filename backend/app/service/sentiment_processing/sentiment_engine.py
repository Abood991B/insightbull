"""
Sentiment Analysis Engine
========================

Central orchestrator for sentiment analysis using multiple models.
Implements intelligent routing of data to appropriate models based on source type.

Following FYP Report specification for SY-FR3 (Perform Sentiment Analysis)
with dual-model approach: FinBERT for financial news, VADER for social media.
"""

import asyncio
import time
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
from datetime import datetime
import logging
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import threading

from .models.sentiment_model import (
    SentimentModel,
    SentimentResult, 
    SentimentLabel, 
    TextInput,
    ModelInfo,
    SentimentModelError
)
from ...infrastructure.collectors.base_collector import DataSource
from .models.hybrid_vader_model import HybridVADERModel, HybridConfig
from .models.finbert_model import FinBERTModel, EnsembleFinBERTModel

logger = logging.getLogger(__name__)

# Global singleton instance
_sentiment_engine_instance = None
_sentiment_engine_lock = threading.Lock()


@dataclass
class EngineConfig:
    """Configuration for the sentiment analysis engine."""
    enable_vader: bool = True
    enable_finbert: bool = True
    use_ensemble_finbert: bool = False  # New: Enable ensemble FinBERT
    finbert_use_gpu: bool = True
    finbert_use_calibration: bool = True  # New: Enable confidence calibration
    max_concurrent_batches: int = 3
    default_batch_size: int = 32
    timeout_seconds: int = 300
    fallback_to_neutral: bool = True
    cache_results: bool = False


@dataclass
class AnalysisJob:
    """Represents a sentiment analysis job."""
    job_id: str
    inputs: List[TextInput]
    created_at: datetime
    status: str = "pending"  # pending, processing, completed, failed
    results: Optional[List[SentimentResult]] = None
    error: Optional[str] = None
    processing_time: Optional[float] = None


@dataclass
class EngineStats:
    """Statistics for the sentiment analysis engine."""
    total_texts_processed: int = 0
    total_processing_time: float = 0.0
    avg_processing_time: float = 0.0
    model_usage: Dict[str, int] = None
    error_count: int = 0
    success_rate: float = 100.0
    
    def __post_init__(self):
        if self.model_usage is None:
            self.model_usage = defaultdict(int)


class SentimentEngine:
    """
    Central sentiment analysis engine with intelligent model routing.
    
    Features:
    - Automatic model selection based on data source
    - Batch processing optimization
    - Concurrent processing support
    - Error handling and fallback strategies
    - Performance monitoring and statistics
    - Graceful degradation when models are unavailable
    """
    
    def __init__(self, config: Optional[EngineConfig] = None):
        """
        Initialize the sentiment analysis engine.
        
        Args:
            config: Engine configuration options
        """
        self.config = config or EngineConfig()
        self.models: Dict[str, SentimentModel] = {}
        self.is_initialized = False
        self.stats = EngineStats()
        self._executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent_batches)
        self._active_jobs: Dict[str, AnalysisJob] = {}
        
        # Model routing configuration
        # Model routing configuration - Hybrid VADER for community discussions, FinBERT for financial sources
        # Following FYP specification: "VADER IS FOR HACKERNEWS AND FINBERT FOR THE OTHER 3 SOURCES(MARKETAUX, NEWSAPI, FINHUB)"
        self._model_routing = {
            DataSource.HACKERNEWS: "Hybrid-VADER", # Community discussions -> Hybrid VADER
            DataSource.FINNHUB: "FinBERT",   # Financial news -> FinBERT
            DataSource.MARKETAUX: "FinBERT", # Financial news -> FinBERT  
            DataSource.NEWSAPI: "FinBERT"    # Financial news -> FinBERT
        }
    
    async def initialize(self) -> None:
        """Initialize all available sentiment models."""
        if self.is_initialized:
            return
        
        logger.info("Initializing Sentiment Analysis Engine...")
        
        # Initialize Hybrid VADER model (Enhanced VADER + ML ensemble)
        if self.config.enable_vader:
            try:
                hybrid_config = HybridConfig()
                self.models["Hybrid-VADER"] = HybridVADERModel(hybrid_config)
                logger.info("Using Hybrid VADER model (Enhanced VADER + Logistic Regression)")
                
                await self.models["Hybrid-VADER"].ensure_loaded()
                logger.info("Hybrid VADER model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Hybrid VADER model: {e}")
                if not self.config.fallback_to_neutral:
                    raise
        
        # Initialize FinBERT model (standard or ensemble)
        if self.config.enable_finbert:
            try:
                if self.config.use_ensemble_finbert:
                    # Use ensemble FinBERT for improved accuracy (1-2% gain)
                    self.models["FinBERT"] = EnsembleFinBERTModel(
                        use_gpu=self.config.finbert_use_gpu,
                        use_calibration=self.config.finbert_use_calibration
                    )
                    logger.info("Using Ensemble FinBERT model (ProsusAI + yiyanghkust)")
                else:
                    # Use standard FinBERT
                    self.models["FinBERT"] = FinBERTModel(use_gpu=self.config.finbert_use_gpu)
                    logger.info("Using standard FinBERT model (ProsusAI)")
                
                await self.models["FinBERT"].ensure_loaded()
                logger.info("FinBERT model initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize FinBERT model: {e}")
                if not self.config.fallback_to_neutral:
                    raise
        
        if not self.models:
            raise SentimentModelError("No sentiment models could be initialized")
        
        self.is_initialized = True
        logger.info(f"Sentiment Engine initialized with {len(self.models)} models")
    
    async def analyze(self, inputs: List[TextInput]) -> List[SentimentResult]:
        """
        Analyze sentiment for multiple text inputs.
        
        Args:
            inputs: List of TextInput objects to analyze
            
        Returns:
            List of SentimentResult objects in the same order as inputs
        """
        if not self.is_initialized:
            await self.initialize()
        
        if not inputs:
            return []
        
        logger.debug(f"Processing {len(inputs)} sentiment analysis inputs")
        start_time = time.time()
        
        try:
            # Group inputs by required model
            model_groups = self._group_inputs_by_model(inputs)
            
            # Process each group with appropriate model
            all_results = {}
            tasks = []
            
            for model_name, group_inputs in model_groups.items():
                if model_name in self.models:
                    logger.debug(f"Using model '{model_name}' for {len(group_inputs)} inputs")
                    task = self._process_model_group(model_name, group_inputs)
                    tasks.append(task)
                else:
                    # Handle missing model case
                    logger.warning(f"Model {model_name} not available, using fallback")
                    fallback_results = self._create_fallback_results(group_inputs)
                    for i, result in enumerate(fallback_results):
                        all_results[id(group_inputs[i])] = result
            
            # Wait for all model processing to complete
            if tasks:
                task_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for task_result in task_results:
                    if isinstance(task_result, Exception):
                        logger.error(f"Model processing failed: {task_result}")
                        continue
                    
                    model_results = task_result
                    for input_obj, result in model_results:
                        all_results[id(input_obj)] = result
            
            # Reconstruct results in original order
            results = []
            for input_obj in inputs:
                result = all_results.get(id(input_obj))
                if result is None:
                    # Create neutral fallback result
                    result = self._create_neutral_result()
                results.append(result)
            
            # Update statistics
            processing_time = time.time() - start_time
            self._update_stats(inputs, results, processing_time)
            
            return results
            
        except Exception as e:
            logger.error(f"Sentiment analysis failed: {e}")
            if self.config.fallback_to_neutral:
                return self._create_fallback_results(inputs)
            raise
    
    async def analyze_batch(self, inputs: List[TextInput]) -> List[SentimentResult]:
        """
        Analyze sentiment for a batch of text inputs.
        Alias for analyze() method for backward compatibility.
        
        Args:
            inputs: List of TextInput objects to analyze
            
        Returns:
            List of SentimentResult objects in the same order as inputs
        """
        return await self.analyze(inputs)
    
    async def analyze_single(self, text: str, source: DataSource, **kwargs) -> SentimentResult:
        """
        Analyze sentiment for a single text.
        
        Args:
            text: Text to analyze
            source: Data source type
            **kwargs: Additional TextInput parameters
            
        Returns:
            Single SentimentResult
        """
        input_obj = TextInput(text=text, source=source, **kwargs)
        results = await self.analyze([input_obj])
        return results[0]
    
    async def _process_model_group(self, model_name: str, inputs: List[TextInput]) -> List[Tuple[TextInput, SentimentResult]]:
        """Process a group of inputs with a specific model."""
        model = self.models[model_name]
        logger.debug(f"Processing {len(inputs)} inputs with model '{model_name}'")
        
        try:
            results = await model.analyze(inputs)
            logger.debug(f"Model '{model_name}' returned {len(results)} results")
            
            # Update model usage stats
            self.stats.model_usage[model_name] += len(inputs)
            
            return list(zip(inputs, results))
            
        except Exception as e:
            logger.error(f"Model {model_name} processing failed: {e}")
            
            # Create error results
            error_results = []
            for input_obj in inputs:
                error_result = SentimentResult(
                    label=SentimentLabel.NEUTRAL,
                    score=0.0,
                    confidence=0.0,
                    raw_scores={'error': str(e)},
                    processing_time=0.0,
                    model_name=model_name
                )
                error_results.append((input_obj, error_result))
            
            return error_results
    
    def _group_inputs_by_model(self, inputs: List[TextInput]) -> Dict[str, List[TextInput]]:
        """Group inputs by the model that should process them."""
        groups = defaultdict(list)
        
        for input_obj in inputs:
            model_name = self._model_routing.get(input_obj.source, "VADER")
            logger.debug(f"Routing {input_obj.source.name} -> {model_name}")
            groups[model_name].append(input_obj)
        
        return dict(groups)
    
    def _create_fallback_results(self, inputs: List[TextInput]) -> List[SentimentResult]:
        """Create neutral fallback results when models fail."""
        return [self._create_neutral_result() for _ in inputs]
    
    def _create_neutral_result(self) -> SentimentResult:
        """Create a neutral sentiment result."""
        return SentimentResult(
            label=SentimentLabel.NEUTRAL,
            score=0.0,
            confidence=0.0,
            raw_scores={'fallback': True},
            processing_time=0.0,
            model_name="FALLBACK"
        )
    
    def _update_stats(self, inputs: List[TextInput], results: List[SentimentResult], processing_time: float) -> None:
        """Update engine statistics."""
        self.stats.total_texts_processed += len(inputs)
        self.stats.total_processing_time += processing_time
        
        if self.stats.total_texts_processed > 0:
            self.stats.avg_processing_time = (
                self.stats.total_processing_time / self.stats.total_texts_processed
            )
        
        # Count errors
        error_count = sum(1 for result in results if 'error' in result.raw_scores)
        self.stats.error_count += error_count
        
        # Calculate success rate
        total_processed = self.stats.total_texts_processed
        if total_processed > 0:
            self.stats.success_rate = ((total_processed - self.stats.error_count) / total_processed) * 100
    
    def get_available_models(self) -> List[str]:
        """Get list of available model names."""
        return list(self.models.keys())
    
    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        """Get information about a specific model."""
        model = self.models.get(model_name)
        return model.get_model_info() if model else None
    
    def get_all_model_info(self) -> Dict[str, ModelInfo]:
        """Get information about all available models."""
        return {name: model.get_model_info() for name, model in self.models.items()}
    
    def get_routing_config(self) -> Dict[DataSource, str]:
        """Get current model routing configuration."""
        return self._model_routing.copy()
    
    def set_model_routing(self, source: DataSource, model_name: str) -> None:
        """
        Set which model should handle a specific data source.
        
        Args:
            source: Data source type
            model_name: Name of the model to use
        """
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} is not available")
        
        self._model_routing[source] = model_name
        logger.info(f"Routing updated: {source.value} -> {model_name}")
    
    def get_stats(self) -> EngineStats:
        """Get current engine statistics."""
        return self.stats
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform comprehensive health check of all models.
        
        Returns:
            Dictionary with health status of each component
        """
        health_status = {
            "engine_initialized": self.is_initialized,
            "available_models": list(self.models.keys()),
            "model_routing": {k.value: v for k, v in self._model_routing.items()},
            "stats": {
                "total_processed": self.stats.total_texts_processed,
                "success_rate": self.stats.success_rate,
                "avg_processing_time": self.stats.avg_processing_time
            },
            "models": {}
        }
        
        # Check each model
        for model_name, model in self.models.items():
            try:
                model_health = await model.health_check()
                health_status["models"][model_name] = model_health
            except Exception as e:
                health_status["models"][model_name] = {
                    "status": "error",
                    "error": str(e)
                }
        
        # Overall status
        all_healthy = all(
            model_status.get("status") == "healthy" 
            for model_status in health_status["models"].values()
        )
        health_status["overall_status"] = "healthy" if all_healthy else "degraded"
        
        return health_status
    
    async def shutdown(self) -> None:
        """Gracefully shutdown the engine and cleanup resources."""
        logger.info("Shutting down Sentiment Analysis Engine...")
        
        # Cleanup FinBERT model if present
        if "FinBERT" in self.models:
            try:
                await self.models["FinBERT"].cleanup()
            except Exception as e:
                logger.error(f"Error during FinBERT cleanup: {e}")
        
        # Shutdown thread pool
        self._executor.shutdown(wait=True)
        
        # Clear models
        self.models.clear()
        self.is_initialized = False
        
        logger.info("Sentiment Analysis Engine shutdown complete")


# Utility functions
def create_default_engine() -> SentimentEngine:
    """Create a sentiment engine with default configuration."""
    return SentimentEngine(EngineConfig())


def create_cpu_only_engine() -> SentimentEngine:
    """Create a sentiment engine optimized for CPU-only environments."""
    config = EngineConfig(
        finbert_use_gpu=False,
        max_concurrent_batches=2,
        default_batch_size=16
    )
    return SentimentEngine(config)


def create_fast_engine() -> SentimentEngine:
    """Create a sentiment engine optimized for speed (VADER only)."""
    config = EngineConfig(
        enable_finbert=False,
        enable_vader=True,
        max_concurrent_batches=5,
        default_batch_size=100
    )
    return SentimentEngine(config)


# Example usage and testing
if __name__ == "__main__":
    async def test_sentiment_engine():
        """Test the sentiment analysis engine with various inputs."""
        
        # Create engine
        engine = SentimentEngine()
        
        # Test inputs from different sources
        test_inputs = [
            TextInput("I love this stock! Great investment!", DataSource.HACKERNEWS, stock_symbol="AAPL"),
            TextInput("Apple Inc. reported strong quarterly earnings today.", DataSource.NEWS, stock_symbol="AAPL"),
            TextInput("Market conditions are uncertain...", DataSource.TWITTER),
            TextInput("Tesla announces breakthrough in battery technology.", DataSource.FINNHUB, stock_symbol="TSLA"),
            TextInput("Banking sector faces regulatory challenges.", DataSource.MARKETAUX),
        ]
        
        try:
            print("Testing Sentiment Analysis Engine...")
            print(f"Test inputs: {len(test_inputs)}")
            print()
            
            # Analyze all inputs
            results = await engine.analyze(test_inputs)
            
            # Display results
            for i, (input_obj, result) in enumerate(zip(test_inputs, results)):
                print(f"Input {i+1}: {input_obj.text[:50]}...")
                print(f"  Source: {input_obj.source.value}")
                print(f"  Label: {result.label.value}")
                print(f"  Score: {result.score:.3f}")
                print(f"  Confidence: {result.confidence:.3f}")
                print(f"  Model: {result.model_name}")
                print(f"  Time: {result.processing_time:.1f}ms")
                print()
            
            # Show engine stats
            stats = engine.get_stats()
            print("Engine Statistics:")
            print(f"  Total processed: {stats.total_texts_processed}")
            print(f"  Success rate: {stats.success_rate:.1f}%")
            print(f"  Avg processing time: {stats.avg_processing_time:.1f}ms")
            print(f"  Model usage: {dict(stats.model_usage)}")
            print()
            
            # Health check
            health = await engine.health_check()
            print("Health Check:")
            print(f"  Overall status: {health['overall_status']}")
            print(f"  Available models: {health['available_models']}")
            print()
            
        finally:
            # Cleanup
            await engine.shutdown()
    
    # Run test if executed directly
    asyncio.run(test_sentiment_engine())


def get_sentiment_engine(config: Optional[EngineConfig] = None) -> SentimentEngine:
    """
    Get the global singleton SentimentEngine instance.
    
    This ensures that models are only loaded once across the entire application,
    preventing duplicate initialization messages and improving performance.
    
    Args:
        config: Engine configuration (only used for first initialization)
        
    Returns:
        The singleton SentimentEngine instance
    """
    global _sentiment_engine_instance
    
    if _sentiment_engine_instance is None:
        with _sentiment_engine_lock:
            # Double-check locking pattern
            if _sentiment_engine_instance is None:
                logger.info("Creating singleton SentimentEngine instance")
                _sentiment_engine_instance = SentimentEngine(config)
    
    return _sentiment_engine_instance


def reset_sentiment_engine():
    """
    Reset the singleton SentimentEngine instance.
    
    This is primarily for testing purposes to ensure clean state between tests.
    """
    import asyncio
    global _sentiment_engine_instance
    
    with _sentiment_engine_lock:
        if _sentiment_engine_instance is not None:
            # Properly handle async shutdown
            try:
                loop = asyncio.get_running_loop()
                # Create a task to run the shutdown
                asyncio.create_task(_sentiment_engine_instance.shutdown())
            except RuntimeError:
                # No running loop, run shutdown synchronously
                asyncio.run(_sentiment_engine_instance.shutdown())
            except Exception as e:
                logger.warning(f"Error during sentiment engine shutdown: {e}")
            finally:
                _sentiment_engine_instance = None
                logger.info("Singleton SentimentEngine instance reset")