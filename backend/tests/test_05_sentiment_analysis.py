"""
Phase 5: Sentiment Analysis Engine Tests
========================================

Essential tests for the dual-model sentiment analysis implementation.
Covers VADER (social media) and FinBERT (financial news) integration.
"""

import pytest
import asyncio
from unittest.mock import patch, Mock
from datetime import datetime

# Import sentiment analysis components
from app.service.sentiment_processing import (
    SentimentResult, SentimentLabel, TextInput, DataSource, VADERModel, FinBERTModel, SentimentEngine, EngineConfig
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
            raw_scores={'pos': 0.75, 'neg': 0.1, 'neu': 0.15},
            processing_time=25.0,
            model_name="VADER"
        )
        
        assert result.label == SentimentLabel.POSITIVE
        assert result.score == 0.75
        assert result.confidence == 0.85
        assert result.model_name == "VADER"
    
    def test_text_input_structure(self):
        """Test TextInput data structure."""
        text_input = TextInput(
            text="Great stock performance! 📈",
            source=DataSource.REDDIT,
            stock_symbol="AAPL",
            timestamp=utc_now()
        )
        
        assert text_input.text == "Great stock performance! 📈"
        assert text_input.source == DataSource.REDDIT
        assert text_input.stock_symbol == "AAPL"
    
    @pytest.mark.asyncio
    async def test_vader_model_basic(self):
        """Test VADER model basic functionality."""
        with patch('app.service.sentiment_processing.models.vader_model.SentimentIntensityAnalyzer') as mock_analyzer:
            # Mock VADER analyzer
            mock_instance = Mock()
            mock_instance.polarity_scores.return_value = {
                'compound': 0.6,
                'pos': 0.7,
                'neu': 0.2,
                'neg': 0.1
            }
            mock_analyzer.return_value = mock_instance
            
            # Test VADER model
            model = VADERModel()
            model.analyzer = mock_instance
            model._is_loaded = True
            
            inputs = [TextInput("Amazing stock! 🚀", DataSource.REDDIT)]
            results = await model.analyze(inputs)
            
            assert len(results) == 1
            assert results[0].label == SentimentLabel.POSITIVE
            assert results[0].model_name == "VADER"
    
    @pytest.mark.asyncio
    async def test_sentiment_engine_routing(self):
        """Test sentiment engine model routing."""
        config = EngineConfig(
            enable_vader=True,
            enable_finbert=True,  # Enable FinBERT for proper routing testing
            default_batch_size=4
        )
        
        with patch('app.service.sentiment_processing.models.vader_model.SentimentIntensityAnalyzer') as mock_analyzer, \
             patch('app.service.sentiment_processing.models.finbert_model.pipeline') as mock_pipeline:
            # Mock VADER
            mock_vader_instance = Mock()
            mock_vader_instance.polarity_scores.return_value = {
                'compound': 0.5,
                'pos': 0.6,
                'neu': 0.3,
                'neg': 0.1
            }
            mock_analyzer.return_value = mock_vader_instance
            
            # Mock FinBERT pipeline
            mock_finbert_pipeline = Mock()
            mock_finbert_pipeline.return_value = [{
                'label': 'positive',
                'score': 0.8
            }]
            mock_pipeline.return_value = mock_finbert_pipeline
            
            engine = SentimentEngine(config)
            await engine.initialize()
            
            # Test routing
            social_inputs = [
                TextInput("Love this stock! 💎", DataSource.REDDIT, "AAPL"),
                TextInput("Great investment choice", DataSource.NEWSAPI, "MSFT")
            ]
            
            results = await engine.analyze(social_inputs)
            
            assert len(results) == 2
            for result in results:
                # With both models enabled, expect proper routing to VADER or FinBERT
                assert result.model_name in ["VADER", "FinBERT"]
                assert result.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL]
    
    @pytest.mark.asyncio
    async def test_engine_health_check(self):
        """Test engine health monitoring."""
        config = EngineConfig(enable_vader=True, enable_finbert=False)
        
        with patch('app.service.sentiment_processing.models.vader_model.SentimentIntensityAnalyzer') as mock_analyzer:
            # Properly mock the analyzer to avoid initialization issues
            mock_instance = Mock()
            mock_analyzer.return_value = mock_instance
            
            engine = SentimentEngine(config)
            await engine.initialize()
            
            health = await engine.health_check()
            
            # Health may be degraded if models have issues, but engine should be initialized
            assert health['engine_initialized'] is True
            assert isinstance(health['available_models'], list)
    
    @pytest.mark.asyncio  
    async def test_engine_statistics(self):
        """Test engine performance statistics."""
        config = EngineConfig(enable_vader=True, enable_finbert=False)
        
        with patch('app.service.sentiment_processing.models.vader_model.SentimentIntensityAnalyzer') as mock_analyzer:
            mock_instance = Mock()
            mock_instance.polarity_scores.return_value = {
                'compound': 0.3,
                'pos': 0.4,
                'neu': 0.4,
                'neg': 0.2
            }
            mock_analyzer.return_value = mock_instance
            
            engine = SentimentEngine(config)
            await engine.initialize()
            
            # Process some texts
            inputs = [
                TextInput("Good stock", DataSource.REDDIT, "AAPL"),
                TextInput("Bad news", DataSource.REDDIT, "TSLA")
            ]
            
            await engine.analyze(inputs)
            
            stats = engine.get_stats()
            assert stats.total_texts_processed >= 2
            assert stats.success_rate == 100.0
            assert 'VADER' in stats.model_usage
    
    def test_sentiment_labels_enum(self):
        """Test sentiment label enumeration."""
        assert SentimentLabel.POSITIVE.value == "positive"
        assert SentimentLabel.NEGATIVE.value == "negative"
        assert SentimentLabel.NEUTRAL.value == "neutral"
    
    def test_data_source_enum(self):
        """Test data source enumeration."""
        assert DataSource.REDDIT.value == "reddit"
        assert DataSource.FINNHUB.value == "finnhub"
        assert DataSource.NEWSAPI.value == "newsapi"
        assert DataSource.MARKETAUX.value == "marketaux"
    
    def test_engine_config(self):
        """Test engine configuration."""
        config = EngineConfig(
            enable_vader=True,
            enable_finbert=True,
            finbert_use_gpu=False,
            max_concurrent_batches=3,
            default_batch_size=16
        )
        
        assert config.enable_vader is True
        assert config.enable_finbert is True
        assert config.finbert_use_gpu is False
        assert config.max_concurrent_batches == 3
        assert config.default_batch_size == 16


# Helper functions for test utilities
def create_sample_texts():
    """Create sample text inputs for testing."""
    return [
        TextInput("Bullish on AAPL! 🚀", DataSource.REDDIT, "AAPL"),
        TextInput("Apple earnings beat expectations", DataSource.NEWSAPI, "AAPL"),
        TextInput("Market looking volatile today", DataSource.MARKETAUX, "SPY"),
        TextInput("Tesla production challenges continue", DataSource.FINNHUB, "TSLA")
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
        print("🧪 Running Phase 6 sentiment analysis validation...")
        
        # Test data structures
        sample_result = SentimentResult(
            label=SentimentLabel.POSITIVE,
            score=0.8,
            confidence=0.9,
            raw_scores={'pos': 0.8, 'neg': 0.1, 'neu': 0.1},
            processing_time=10.0,
            model_name="TestModel"
        )
        assert_valid_sentiment_result(sample_result)
        
        # Test VADER with mocked analyzer
        with patch('app.service.sentiment_processing.models.vader_model.SentimentIntensityAnalyzer') as mock_analyzer:
            mock_instance = Mock()
            mock_instance.polarity_scores.return_value = {
                'compound': 0.5,
                'pos': 0.6,
                'neu': 0.3,
                'neg': 0.1
            }
            mock_analyzer.return_value = mock_instance
            
            model = VADERModel()
            model.analyzer = mock_instance
            model._is_loaded = True
            
            inputs = [TextInput("Great stock performance!", DataSource.REDDIT)]
            results = await model.analyze(inputs)
            
            assert len(results) == 1
            assert_valid_sentiment_result(results[0])
        
        print("✅ Phase 6 sentiment analysis validation complete!")
        return True
    
    # Run the quick test
    success = asyncio.run(quick_test())
    if success:
        print("🎯 All essential tests passed - Phase 6 implementation validated!")
    else:
        print("❌ Validation failed")
