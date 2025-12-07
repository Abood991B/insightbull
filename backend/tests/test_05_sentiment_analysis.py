"""
Phase 5: Sentiment Analysis Engine Tests
========================================

Essential tests for the FinBERT sentiment analysis implementation.
Uses ProsusAI/finbert model with optional Gemini AI verification.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock
from datetime import datetime

# Import sentiment analysis components
from app.service.sentiment_processing import (
    SentimentResult, SentimentLabel, TextInput, DataSource, FinBERTModel, SentimentEngine, EngineConfig
)
from app.utils.timezone import utc_now


class TestSentimentAnalysis:
    """Core sentiment analysis functionality tests."""
    
    def test_sentiment_result_structure(self):
        """Test SentimentResult data structure."""
        result = SentimentResult(
            label=SentimentLabel.POSITIVE,
            score=0.75,
            confidence=0.85,
            raw_scores={'positive': 0.75, 'negative': 0.1, 'neutral': 0.15},
            processing_time=25.0,
            model_name="FinBERT"
        )
        
        assert result.label == SentimentLabel.POSITIVE
        assert result.score == 0.75
        assert result.confidence == 0.85
        assert result.model_name == "FinBERT"
    
    def test_text_input_structure(self):
        """Test TextInput data structure."""
        text_input = TextInput(
            text="Apple reports strong quarterly earnings",
            source=DataSource.NEWSAPI,
            stock_symbol="AAPL",
            timestamp=utc_now()
        )
        
        assert text_input.text == "Apple reports strong quarterly earnings"
        assert text_input.source == DataSource.NEWSAPI
        assert text_input.stock_symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_sentiment_engine_with_finbert(self):
        """Test sentiment engine with FinBERT model."""
        config = EngineConfig(
            enable_finbert=True,
            default_batch_size=4
        )
        
        with patch('app.service.sentiment_processing.models.finbert_model.pipeline') as mock_pipeline:
            # Mock FinBERT pipeline
            mock_finbert_pipeline = Mock()
            mock_finbert_pipeline.return_value = [{
                'label': 'positive',
                'score': 0.85
            }]
            mock_pipeline.return_value = mock_finbert_pipeline
            
            engine = SentimentEngine(config)
            await engine.initialize()
            
            # Test analysis
            inputs = [
                TextInput("Great investment opportunity", DataSource.NEWSAPI, "AAPL"),
                TextInput("Strong earnings report", DataSource.FINNHUB, "MSFT")
            ]
            
            results = await engine.analyze(inputs)
            
            assert len(results) == 2
            for result in results:
                assert result.model_name == "FinBERT"
                assert result.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL]
    
    @pytest.mark.asyncio
    async def test_engine_health_check(self):
        """Test engine health monitoring."""
        config = EngineConfig(enable_finbert=True)
        
        with patch('app.service.sentiment_processing.models.finbert_model.pipeline') as mock_pipeline:
            mock_finbert_pipeline = Mock()
            mock_finbert_pipeline.return_value = [{'label': 'neutral', 'score': 0.7}]
            mock_pipeline.return_value = mock_finbert_pipeline
            
            engine = SentimentEngine(config)
            await engine.initialize()
            
            health = await engine.health_check()
            
            assert health['engine_initialized'] is True
            assert isinstance(health['available_models'], list)
    
    @pytest.mark.asyncio  
    async def test_engine_statistics(self):
        """Test engine performance statistics."""
        config = EngineConfig(enable_finbert=True)
        
        with patch('app.service.sentiment_processing.models.finbert_model.pipeline') as mock_pipeline:
            mock_finbert_pipeline = Mock()
            mock_finbert_pipeline.return_value = [{
                'label': 'positive',
                'score': 0.75
            }]
            mock_pipeline.return_value = mock_finbert_pipeline
            
            engine = SentimentEngine(config)
            await engine.initialize()
            
            # Process some texts
            inputs = [
                TextInput("Good stock performance", DataSource.NEWSAPI, "AAPL"),
                TextInput("Weak earnings forecast", DataSource.FINNHUB, "TSLA")
            ]
            
            await engine.analyze(inputs)
            
            stats = engine.get_stats()
            assert stats.total_texts_processed >= 2
            assert stats.success_rate == 100.0
            assert 'FinBERT' in stats.model_usage
    
    def test_sentiment_labels_enum(self):
        """Test sentiment label enumeration."""
        assert SentimentLabel.POSITIVE.value == "positive"
        assert SentimentLabel.NEGATIVE.value == "negative"
        assert SentimentLabel.NEUTRAL.value == "neutral"
    
    def test_data_source_enum(self):
        """Test data source enumeration."""
        assert DataSource.HACKERNEWS.value == "hackernews"
        assert DataSource.FINNHUB.value == "finnhub"
        assert DataSource.NEWSAPI.value == "newsapi"
        assert DataSource.MARKETAUX.value == "marketaux"
    
    def test_engine_config(self):
        """Test engine configuration."""
        config = EngineConfig(
            enable_finbert=True,
            finbert_use_gpu=False,
            max_concurrent_batches=3,
            default_batch_size=16
        )
        
        assert config.enable_finbert is True
        assert config.finbert_use_gpu is False
        assert config.max_concurrent_batches == 3
        assert config.default_batch_size == 16


# Helper functions for test utilities
def create_sample_texts():
    """Create sample text inputs for testing."""
    return [
        TextInput("Apple reports record quarterly revenue", DataSource.NEWSAPI, "AAPL"),
        TextInput("Tesla faces production challenges", DataSource.FINNHUB, "TSLA"),
        TextInput("Microsoft cloud growth accelerates", DataSource.MARKETAUX, "MSFT"),
        TextInput("NVIDIA demand exceeds expectations", DataSource.NEWSAPI, "NVDA")
    ]


def assert_valid_sentiment_result(result: SentimentResult):
    """Assert that a sentiment result is valid."""
    assert isinstance(result, SentimentResult)
    assert result.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL]
    assert -1.0 <= result.score <= 1.0
    assert 0.0 <= result.confidence <= 1.0
    assert result.processing_time >= 0.0
    assert result.model_name is not None


if __name__ == "__main__":
    # Run a quick validation test
    async def quick_test():
        """Quick validation of core functionality."""
        print("Testing Phase 5 sentiment analysis validation...")
        
        # Test data structures
        sample_result = SentimentResult(
            label=SentimentLabel.POSITIVE,
            score=0.8,
            confidence=0.9,
            raw_scores={'positive': 0.8, 'negative': 0.1, 'neutral': 0.1},
            processing_time=10.0,
            model_name="FinBERT"
        )
        assert_valid_sentiment_result(sample_result)
        
        # Test FinBERT with mocked pipeline
        with patch('app.service.sentiment_processing.models.finbert_model.pipeline') as mock_pipeline:
            mock_finbert_pipeline = Mock()
            mock_finbert_pipeline.return_value = [{'label': 'positive', 'score': 0.85}]
            mock_pipeline.return_value = mock_finbert_pipeline
            
            config = EngineConfig(enable_finbert=True)
            engine = SentimentEngine(config)
            await engine.initialize()
            
            inputs = [TextInput("Test text", DataSource.NEWSAPI, "AAPL")]
            results = await engine.analyze(inputs)
            
            assert len(results) == 1
            assert results[0].model_name == "FinBERT"
        
        print("Phase 5 sentiment analysis validation complete!")
        return True
    
    # Run the quick test
    success = asyncio.run(quick_test())
    if success:
        print("All essential tests passed - Phase 5 implementation validated!")
    else:
        print("Validation failed")
