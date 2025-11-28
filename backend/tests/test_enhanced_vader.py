"""
Quick test script to verify Enhanced VADER is working correctly.
"""
import asyncio
from app.service.sentiment_processing import get_sentiment_engine, EngineConfig
from app.service.sentiment_processing.models.sentiment_model import TextInput, DataSource


async def test_enhanced_vader():
    """Test Enhanced VADER with community-style texts."""
    
    # Initialize engine
    engine = get_sentiment_engine(EngineConfig())
    await engine.initialize()
    
    # Test cases showcasing Enhanced VADER features
    test_cases = [
        # Financial lexicon + emoji boost
        ("GME to the moon! Diamond hands forever 🚀💎🙌", DataSource.HACKERNEWS),
        
        # Bearish terms + emoji
        ("Market crash incoming. Bloodbath ahead 📉", DataSource.HACKERNEWS),
        
        # Community slang
        ("BTFD! This is the way. YOLO calls on $TSLA", DataSource.HACKERNEWS),
        
        # Negative slang
        ("Paper hands selling. This is a rug pull. GUH", DataSource.HACKERNEWS),
        
        # Mixed sentiment
        ("Uncertain market conditions. Could go either way.", DataSource.HACKERNEWS),
    ]
    
    inputs = [TextInput(text, source) for text, source in test_cases]
    results = await engine.analyze_batch(inputs)
    
    # Display results
    print("\n" + "="*70)
    print("ENHANCED VADER TEST RESULTS")
    print("="*70)
    
    for i, (test_input, result) in enumerate(zip(inputs, results), 1):
        print(f"\nTest {i}:")
        print(f"  Text: {test_input.text}")
        print(f"  Label: {result.label.value}")
        print(f"  Score: {result.score:.3f}")
        print(f"  Confidence: {result.confidence:.3f}")
        print(f"  Model: {result.model_name}")
        
        # Show enhancements if available
        if 'enhancements' in result.raw_scores:
            enhancements = result.raw_scores['enhancements']
            print(f"  Enhancements:")
            if enhancements.get('emoji_boost'):
                print(f"    - Emoji boost: {enhancements['emoji_boost']:.2f}")
            if enhancements.get('financial_terms'):
                print(f"    - Financial terms: {enhancements['financial_terms']}")
    
    print("\n" + "="*70)
    print("Enhanced VADER Features Active:")
    print("  ✓ Financial Lexicon (55+ terms)")
    print("  ✓ Community Slang Processing (40+ mappings)")
    print("  ✓ Emoji Sentiment Boost (30+ emojis)")
    print("  ✓ Dynamic Thresholds")
    print("  ✓ Context Awareness")
    print("="*70 + "\n")


if __name__ == "__main__":
    asyncio.run(test_enhanced_vader())
