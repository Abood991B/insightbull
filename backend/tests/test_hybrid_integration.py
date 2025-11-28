"""
Test script to verify Hybrid VADER integration in the sentiment engine
"""
import asyncio
import sys
from app.service.sentiment_processing import get_sentiment_engine
from app.service.sentiment_processing.models.sentiment_model import TextInput, DataSource


async def test_hybrid_vader_integration():
    """Test that Hybrid VADER is properly integrated."""
    print("="*70)
    print("TESTING HYBRID VADER INTEGRATION")
    print("="*70)
    
    # Get sentiment engine
    print("\n1. Initializing Sentiment Engine...")
    engine = get_sentiment_engine()
    await engine.initialize()
    
    print(f"\n2. Loaded Models: {list(engine.models.keys())}")
    print(f"   Expected: ['Hybrid-VADER', 'FinBERT']")
    
    print(f"\n3. Routing Configuration:")
    for source, model in engine._model_routing.items():
        print(f"   - {source.value}: {model}")
    
    # Test HackerNews sentiment (should use Hybrid VADER)
    print("\n4. Testing HackerNews sentiment analysis (Hybrid VADER)...")
    hn_texts = [
        "GME to the moon! Diamond hands forever!",
        "Market crash incoming. Bearish sentiment.",
        "Uncertain market conditions."
    ]
    
    inputs = [TextInput(text, DataSource.HACKERNEWS) for text in hn_texts]
    results = await engine.analyze(inputs)
    
    print("\n   Results:")
    for text, result in zip(hn_texts, results):
        print(f"\n   Text: {text[:60]}")
        print(f"   - Prediction: {result.label.value}")
        print(f"   - Score: {result.score:.3f}")
        print(f"   - Confidence: {result.confidence:.3f}")
        print(f"   - Model: {result.model_name}")
        
        # Check if ensemble info is present (indicates Hybrid VADER)
        if 'ensemble' in result.raw_scores:
            ensemble = result.raw_scores['ensemble']
            print(f"   - Strategy: {ensemble['strategy']}")
            print(f"   - VADER weight: {ensemble['weights']['vader']:.2f}")
            print(f"   - ML weight: {ensemble['weights']['ml']:.2f}")
    
    print("\n" + "="*70)
    print("INTEGRATION TEST COMPLETE")
    print("="*70)
    
    # Verify Hybrid VADER is being used
    if "Hybrid-VADER" in engine.models:
        print("\n[SUCCESS] Hybrid VADER model is loaded in the engine")
    else:
        print("\n[ERROR] Hybrid VADER model NOT found in engine")
        sys.exit(1)
    
    if engine._model_routing[DataSource.HACKERNEWS] == "Hybrid-VADER":
        print("[SUCCESS] HackerNews is routed to Hybrid VADER")
    else:
        print(f"[ERROR] HackerNews routing incorrect: {engine._model_routing[DataSource.HACKERNEWS]}")
        sys.exit(1)
    
    if results[0].model_name == "Hybrid-VADER":
        print("[SUCCESS] HackerNews analysis uses Hybrid VADER model")
    else:
        print(f"[ERROR] HackerNews analysis used wrong model: {results[0].model_name}")
        sys.exit(1)
    
    print("\n[SUCCESS] All integration checks passed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_hybrid_vader_integration())
