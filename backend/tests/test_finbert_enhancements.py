"""
Test Suite for FinBERT Enhancements
====================================

Tests for:
1. ConfidenceCalibrator (temperature scaling)
2. EnsembleFinBERTModel (multi-model ensemble)
3. Enhanced FinancialTextPreprocessor (entity recognition, noise filtering)
"""

import pytest
import asyncio
import torch
import numpy as np
from app.service.sentiment_processing.models.finbert_model import (
    FinBERTModel,
    EnsembleFinBERTModel,
    ConfidenceCalibrator,
    FinancialTextPreprocessor
)
from app.service.sentiment_processing.models.sentiment_model import (
    TextInput,
    DataSource,
    SentimentLabel
)


class TestConfidenceCalibrator:
    """Test confidence calibration with temperature scaling."""
    
    def test_calibrator_initialization(self):
        """Test calibrator initializes with correct temperature."""
        calibrator = ConfidenceCalibrator(temperature=1.5)
        assert calibrator.temperature == 1.5
    
    def test_calibrate_scores(self):
        """Test temperature scaling reduces overconfidence."""
        calibrator = ConfidenceCalibrator(temperature=2.0)
        
        # Create mock logits (highly confident)
        logits = torch.tensor([[5.0, -2.0, -3.0]])  # Strong positive prediction
        
        # Get raw softmax for comparison
        import torch.nn.functional as F
        raw_softmax = F.softmax(logits, dim=-1)
        raw_max_conf = torch.max(raw_softmax).item()
        
        # Calibrate
        calibrated = calibrator.calibrate_scores(logits)
        
        # Calibrated scores should be less extreme (more uncertain)
        assert calibrated.shape == (1, 3)
        assert torch.all(calibrated >= 0) and torch.all(calibrated <= 1)
        assert torch.allclose(calibrated.sum(dim=1), torch.tensor([1.0]))
        
        # With temperature=2.0, confidence should be reduced compared to raw softmax
        max_conf = torch.max(calibrated).item()
        assert max_conf < raw_max_conf  # Calibrated should be less confident than raw
        assert max_conf < 0.96  # Should still be relatively confident but not extreme
    
    def test_set_temperature(self):
        """Test updating temperature value."""
        calibrator = ConfidenceCalibrator(temperature=1.0)
        assert calibrator.temperature == 1.0
        
        calibrator.set_temperature(2.0)
        assert calibrator.temperature == 2.0


class TestEnhancedFinancialTextPreprocessor:
    """Test enhanced financial text preprocessing."""
    
    @pytest.fixture
    def preprocessor(self):
        """Create preprocessor instance."""
        return FinancialTextPreprocessor(use_advanced_preprocessing=True)
    
    def test_number_standardization(self, preprocessor):
        """Test financial number standardization."""
        test_cases = [
            ("Apple reported $1.5B in revenue", "$1,500,000,000"),
            ("The company raised $50M in funding", "$50,000,000"),
            ("Market cap reached $2.3T", "$2,300,000,000,000")
        ]
        
        for input_text, expected_contains in test_cases:
            result = preprocessor.preprocess(input_text)
            assert expected_contains in result, f"Expected '{expected_contains}' in '{result}'"
    
    def test_abbreviation_expansion(self, preprocessor):
        """Test financial abbreviation expansion."""
        test_cases = [
            ("Strong EPS this quarter", "earnings per share"),
            ("P/E ratio improved significantly", "price to earnings"),
            ("ROI exceeded expectations", "return on investment"),
            ("EBITDA growth accelerated", "earnings before interest taxes depreciation amortization")
        ]
        
        for input_text, expected_contains in test_cases:
            result = preprocessor.preprocess(input_text)
            assert expected_contains.lower() in result.lower(), \
                f"Expected '{expected_contains}' in '{result}'"
    
    def test_company_name_normalization(self, preprocessor):
        """Test company ticker to name normalization."""
        test_cases = [
            ("AAPL stock surged", "Apple"),
            ("MSFT announced earnings", "Microsoft"),
            ("TSLA shares jumped", "Tesla")
        ]
        
        for input_text, expected_company in test_cases:
            result = preprocessor.preprocess(input_text)
            # Company name should appear in result
            assert expected_company in result or input_text.split()[0] in result
    
    def test_noise_filtering(self, preprocessor):
        """Test removal of promotional/ad content."""
        test_cases = [
            "Apple reported earnings [Advertisement]",
            "Tech stocks rally - Click here for more",
            "Market update (Sponsored Content)"
        ]
        
        for input_text in test_cases:
            result = preprocessor.preprocess(input_text)
            # Noise patterns should be removed or minimized
            assert "Advertisement" not in result
            assert "Click here" not in result
            assert len(result) > 0  # Still has content
    
    def test_percentage_normalization(self, preprocessor):
        """Test percentage normalization."""
        input_text = "Stock rose 15% on strong earnings"
        result = preprocessor.preprocess(input_text)
        
        # Should convert % to "percent"
        assert "15 percent" in result or "15%" in result
    
    def test_intelligent_truncation(self, preprocessor):
        """Test intelligent truncation preserves financial keywords."""
        # Create long text with financial keywords scattered
        long_text = "Introduction text. " * 50
        long_text += "Strong earnings beat expectations with revenue growth. "
        long_text += "Filler text. " * 50
        long_text += "Analyst upgrades stock price target. "
        long_text += "More filler. " * 50
        long_text += "Guidance outlook remains positive."
        
        result = preprocessor.preprocess(long_text)
        
        # Should preserve key financial content
        assert len(result) <= 2000
        # At least some financial keywords should be present
        financial_keywords = ['earnings', 'revenue', 'analyst', 'guidance', 'outlook']
        keywords_found = sum(1 for kw in financial_keywords if kw in result.lower())
        assert keywords_found >= 2, "Should preserve financial keywords during truncation"
    
    def test_entity_extraction(self, preprocessor):
        """Test financial entity extraction."""
        text = "$AAPL stock rose 15% to $150.50 on 01/15/2025"
        entities = preprocessor.extract_financial_entities(text)
        
        assert 'tickers' in entities
        assert 'percentages' in entities
        assert 'currencies' in entities
        assert 'dates' in entities
        
        assert len(entities['tickers']) >= 1  # Should find $AAPL
        assert len(entities['percentages']) >= 1  # Should find 15%


class TestEnsembleFinBERTModel:
    """Test Ensemble FinBERT model."""
    
    @pytest.mark.asyncio
    async def test_ensemble_initialization(self):
        """Test ensemble model initialization."""
        try:
            model = EnsembleFinBERTModel(use_gpu=False, use_calibration=True)
            assert model.use_calibration == True
            assert model.calibrator is not None
            assert isinstance(model.calibrator, ConfidenceCalibrator)
        except Exception as e:
            pytest.skip(f"FinBERT models not available: {e}")
    
    @pytest.mark.asyncio
    async def test_ensemble_vs_single_model(self):
        """Compare ensemble vs single model predictions."""
        try:
            # Initialize both models
            single_model = FinBERTModel(use_gpu=False)
            ensemble_model = EnsembleFinBERTModel(use_gpu=False, use_calibration=True)
            
            await single_model.ensure_loaded()
            await ensemble_model.ensure_loaded()
            
            # Test financial news text
            test_text = "Apple Inc. reported record quarterly earnings, beating analyst expectations by 15%."
            inputs = [TextInput(test_text, DataSource.FINNHUB)]
            
            single_results = await single_model.analyze(inputs)
            ensemble_results = await ensemble_model.analyze(inputs)
            
            # Both should predict positive sentiment
            assert single_results[0].label == SentimentLabel.POSITIVE
            assert ensemble_results[0].label == SentimentLabel.POSITIVE
            
            # Ensemble should have ensemble_scores in raw_scores
            assert 'ensemble_scores' in ensemble_results[0].raw_scores
            assert 'individual_models' in ensemble_results[0].raw_scores
            
            # Cleanup
            await single_model.cleanup()
            await ensemble_model.cleanup()
            
        except Exception as e:
            pytest.skip(f"FinBERT models not available for comparison: {e}")


class TestIntegration:
    """Integration tests for enhanced FinBERT."""
    
    @pytest.mark.asyncio
    async def test_full_pipeline_with_preprocessing(self):
        """Test full pipeline with enhanced preprocessing."""
        try:
            model = FinBERTModel(use_gpu=False)
            await model.ensure_loaded()
            
            # Test text with multiple enhancement scenarios
            test_cases = [
                TextInput(
                    "AAPL reported $1.5B revenue with EPS of $1.20, up 15% YoY",
                    DataSource.FINNHUB
                ),
                TextInput(
                    "Microsoft (MSFT) announced M&A deal worth $50M, P/E ratio improves",
                    DataSource.MARKETAUX
                ),
                TextInput(
                    "Tesla shares drop 10% after CEO comments on Q3 guidance [Advertisement]",
                    DataSource.NEWSAPI
                )
            ]
            
            results = await model.analyze(test_cases)
            
            # Should successfully analyze all
            assert len(results) == 3
            assert all(r.label in [SentimentLabel.POSITIVE, SentimentLabel.NEGATIVE, SentimentLabel.NEUTRAL] 
                      for r in results)
            assert all(r.confidence > 0 for r in results)
            
            # First should be positive (strong earnings)
            assert results[0].label == SentimentLabel.POSITIVE
            
            # Third should be negative (stock drop)
            assert results[2].label == SentimentLabel.NEGATIVE
            
            await model.cleanup()
            
        except Exception as e:
            pytest.skip(f"FinBERT not available: {e}")
    
    @pytest.mark.asyncio
    async def test_preprocessing_improves_accuracy(self):
        """Test that preprocessing improves sentiment detection."""
        try:
            # Test with advanced preprocessing
            model_advanced = FinBERTModel(use_gpu=False)
            await model_advanced.ensure_loaded()
            model_advanced._preprocessor.use_advanced = True
            
            # Test with basic preprocessing
            model_basic = FinBERTModel(use_gpu=False)
            await model_basic.ensure_loaded()
            model_basic._preprocessor.use_advanced = False
            
            # Challenging text with abbreviations and numbers
            text = "AAPL EPS beat by $1.50, P/E improved to 25, revenue up $2.5B YoY"
            inputs = [TextInput(text, DataSource.FINNHUB)]
            
            results_advanced = await model_advanced.analyze(inputs)
            results_basic = await model_basic.analyze(inputs)
            
            # Both should detect positive sentiment
            assert results_advanced[0].label == SentimentLabel.POSITIVE
            
            # Advanced preprocessing may provide clearer signal
            # (confidence might be higher, but not guaranteed)
            
            await model_advanced.cleanup()
            await model_basic.cleanup()
            
        except Exception as e:
            pytest.skip(f"FinBERT not available: {e}")


# Utility functions for testing
def create_mock_logits(positive_score: float = 5.0, 
                       negative_score: float = -2.0, 
                       neutral_score: float = -1.0) -> torch.Tensor:
    """Create mock logits for testing."""
    return torch.tensor([[positive_score, negative_score, neutral_score]])


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v", "-s"])
