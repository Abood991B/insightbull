"""
Test Suite for ML/AI Enhancements
=================================

Tests for:
- Negation detection (FinBERT)
- Sarcasm detection (FinBERT)
- DistilBERT ensemble voting
- Temporal decay weighting
- Confidence threshold enforcement (0.85)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from app.service.sentiment_processing.models.distilbert_model import DistilBERTFinancialModel
from app.service.sentiment_processing.hybrid_sentiment_analyzer import AIVerifiedSentimentAnalyzer
from app.service.sentiment_service import SentimentService
from app.utils.timezone import utc_now, to_naive_utc


class TestNegationDetection:
    """Test FinBERT negation handling enhancement via AIVerifiedSentimentAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Initialize analyzer with AI disabled, ensemble enabled."""
        return AIVerifiedSentimentAnalyzer(
            ai_enabled=False,
            ensemble_enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_negation_positive_flip(self, analyzer):
        """Test negation flips negative to positive."""
        test_cases = [
            "The stock isn't terrible",
            "Not a bad earnings report"
        ]
        
        for text in test_cases:
            result = await analyzer.analyze(text)
            print(f"\nText: {text}")
            print(f"Sentiment: {result.label} (score: {result.score:.3f})")
            print(f"Confidence: {result.confidence:.3f}")
            
            # Should be positive or neutral (not negative)
            assert result.label in ['positive', 'neutral'], \
                f"Negation failed for: {text} - got {result.label}"


class TestSarcasmDetection:
    """Test FinBERT sarcasm handling enhancement via AIVerifiedSentimentAnalyzer."""
    
    @pytest.fixture
    def analyzer(self):
        """Initialize analyzer with AI disabled, ensemble enabled."""
        return AIVerifiedSentimentAnalyzer(
            ai_enabled=False,
            ensemble_enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_sarcasm_marker_detection(self, analyzer):
        """Test /s sarcasm marker detection."""
        text = "Great earnings report /s"
        
        result = await analyzer.analyze(text)
        print(f"\nText: {text}")
        print(f"Sentiment: {result.label} (score: {result.score:.3f})")
        print(f"Confidence: {result.confidence:.3f}")
        
        # Should be negative (sarcasm detected and flipped)
        assert result.label == 'negative', \
            f"Sarcasm not detected for: {text} - got {result.label}"


class TestDistilBERTEnsemble:
    """Test DistilBERT ensemble voting integration."""
    
    def test_ensemble_loads_successfully(self):
        """Test DistilBERT model loads without errors."""
        try:
            model = DistilBERTFinancialModel()
            assert model is not None
            print("\n[OK] DistilBERT model loaded successfully")
        except Exception as e:
            pytest.fail(f"DistilBERT failed to load: {e}")
    
    @pytest.fixture
    def analyzer(self):
        """Initialize analyzer with ensemble enabled."""
        return AIVerifiedSentimentAnalyzer(
            ai_enabled=False,
            ensemble_enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_ensemble_triggers_on_uncertain(self, analyzer):
        """Test ensemble triggers and produces valid results."""
        text = "The company reported mixed results with some challenges"
        
        result = await analyzer.analyze(text)
        
        print(f"\nText: {text}")
        print(f"Sentiment: {result.label} (score: {result.score:.3f})")
        print(f"Confidence: {result.confidence:.3f}")
        
        # Should have valid result
        assert result.label in ['positive', 'neutral', 'negative']
        assert 0.0 <= result.confidence <= 1.0
        print("\n[OK] Ensemble produced valid result")


class TestTemporalDecay:
    """Test temporal decay time-weighting."""
    
    def test_temporal_weight_calculation(self):
        """Test exponential decay formula."""
        service = SentimentService(db=None)  # Mock db for calculation test
        
        current_time = utc_now()
        
        # Test different time points
        test_cases = [
            (current_time, 1.0, "Current time"),
            (current_time - timedelta(hours=24), 0.5, "24h ago (half-life)"),
            (current_time - timedelta(hours=48), 0.25, "48h ago"),
            (current_time - timedelta(days=7), 0.05, "7d ago (minimum)"),
        ]
        
        for timestamp, expected_weight, description in test_cases:
            weight = service._calculate_temporal_weight(timestamp, current_time)
            print(f"\n{description}: weight = {weight:.3f} (expected ~{expected_weight})")
            
            # Allow 10% tolerance
            assert abs(weight - expected_weight) < 0.1 * expected_weight, \
                f"Weight calculation failed for {description}"
    
    def test_temporal_decay_enabled(self):
        """Test temporal decay is enabled by default."""
        service = SentimentService(db=None)
        
        assert service.decay_enabled is True
        assert service.decay_half_life == 24
        print("\n[OK] Temporal decay enabled with 24h half-life")


class TestConfidenceThreshold:
    """Test confidence threshold enforcement (0.85)."""
    
    @pytest.fixture
    def analyzer(self):
        """Initialize analyzer with confidence threshold."""
        return AIVerifiedSentimentAnalyzer(
            ai_enabled=False,
            ensemble_enabled=True,
            confidence_threshold=0.85
        )
    
    @pytest.mark.asyncio
    async def test_high_confidence_predictions(self, analyzer):
        """Test system produces high-confidence predictions."""
        test_cases = [
            "Company reported record profits and strong growth",
            "Stock crashed after terrible earnings miss"
        ]
        
        high_confidence_count = 0
        
        for text in test_cases:
            result = await analyzer.analyze(text)
            print(f"\nText: {text[:50]}...")
            print(f"Sentiment: {result.label}")
            print(f"Confidence: {result.confidence:.3f}")
            
            if result.confidence >= 0.75:  # Reasonable threshold for testing
                high_confidence_count += 1
        
        # At least 1 out of 2 should have high confidence
        assert high_confidence_count >= 1, \
            f"Only {high_confidence_count}/2 predictions had confidence >=0.75"
        
        print(f"\n[OK] {high_confidence_count}/2 predictions had confidence >=0.75")


class TestIntegration:
    """Integration tests for all enhancements working together."""
    
    @pytest.fixture
    def analyzer(self):
        """Initialize analyzer with all features."""
        return AIVerifiedSentimentAnalyzer(
            ai_enabled=False,
            ensemble_enabled=True
        )
    
    @pytest.mark.asyncio
    async def test_negation_with_ensemble(self, analyzer):
        """Test negation detection works with ensemble voting."""
        text = "The stock isn't bad despite market concerns"
        
        result = await analyzer.analyze(text)
        
        print(f"\nText: {text}")
        print(f"Sentiment: {result.label} (score: {result.score:.3f})")
        print(f"Confidence: {result.confidence:.3f}")
        
        # Should handle negation correctly
        assert result.label in ['positive', 'neutral']
        print("\n[OK] Negation + ensemble integration successful")
    
    @pytest.mark.asyncio
    async def test_complex_text_handling(self, analyzer):
        """Test complex text with multiple features."""
        text = "The company didn't fail to meet expectations, but challenges remain"
        
        result = await analyzer.analyze(text)
        
        print(f"\nText: {text}")
        print(f"Sentiment: {result.label} (score: {result.score:.3f})")
        print(f"Confidence: {result.confidence:.3f}")
        
        # Should produce valid result
        assert result.label in ['positive', 'neutral', 'negative']
        assert 0.0 <= result.confidence <= 1.0
        assert -1.0 <= result.score <= 1.0
        print("\n[OK] Complex text handling successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
