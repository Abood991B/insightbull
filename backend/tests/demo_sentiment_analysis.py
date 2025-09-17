#!/usr/bin/env python3
"""
Phase 6: Sentiment Analysis Engine Demo
=======================================

Demonstration of the complete sentiment analysis implementation.
Shows the dual-model approach with FinBERT and VADER working together.
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import List

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.service.sentiment_processing import SentimentEngine, EngineConfig
from app.service.sentiment_processing import TextInput, DataSource, SentimentLabel


async def demo_sentiment_analysis():
    """Demonstrate the complete sentiment analysis engine."""
    
    print("🚀 Phase 6: Sentiment Analysis Engine Demonstration")
    print("=" * 60)
    
    # Configure sentiment engine
    config = EngineConfig(
        enable_vader=True,
        enable_finbert=True,
        finbert_use_gpu=False,  # Use CPU for demo compatibility
        max_concurrent_batches=2,
        default_batch_size=8,
        fallback_to_neutral=True
    )
    
    print(f"Engine Configuration:")
    print(f"  VADER enabled: {config.enable_vader}")
    print(f"  FinBERT enabled: {config.enable_finbert}")
    print(f"  GPU usage: {config.finbert_use_gpu}")
    print(f"  Batch size: {config.default_batch_size}")
    print()
    
    # Initialize engine
    engine = SentimentEngine(config)
    
    try:
        print("Initializing sentiment analysis models...")
        await engine.initialize()
        
        # Show available models
        available_models = engine.get_available_models()
        print(f"✅ Available models: {available_models}")
        
        # Show model routing
        routing = engine.get_routing_config()
        print("Model Routing Configuration:")
        for source, model in routing.items():
            print(f"  {source.value} → {model}")
        print()
        
        # Create test inputs covering different data sources
        test_inputs = [
            # Social Media (VADER)
            TextInput(
                text="I absolutely love this stock! Best investment ever! 🚀📈 #ToTheMoon",
                source=DataSource.REDDIT,
                stock_symbol="AAPL",
                metadata={'subreddit': 'wallstreetbets'}
            ),
            TextInput(
                text="This stock is crashing hard... not looking good 😞 $TSLA",
                source=DataSource.REDDIT,
                stock_symbol="TSLA",
                metadata={'subreddit': 'stocks'}
            ),
            TextInput(
                text="Market seems neutral today, nothing exciting happening",
                source=DataSource.TWITTER,
                stock_symbol="SPY"
            ),
            
            # Financial News (FinBERT)
            TextInput(
                text="Apple Inc. reported record quarterly earnings, beating analyst expectations by 15%. Revenue increased 12% year-over-year driven by strong iPhone sales.",
                source=DataSource.NEWS,
                stock_symbol="AAPL",
                metadata={'publisher': 'Reuters'}
            ),
            TextInput(
                text="Tesla faces significant production challenges due to supply chain disruptions and regulatory hurdles in key markets.",
                source=DataSource.FINNHUB,
                stock_symbol="TSLA",
                metadata={'category': 'company_news'}
            ),
            TextInput(
                text="Microsoft maintains stable outlook with moderate growth expected in cloud services division over the next quarter.",
                source=DataSource.MARKETAUX,
                stock_symbol="MSFT",
                metadata={'category': 'earnings'}
            ),
            
            # Mixed content
            TextInput(
                text="NVIDIA's AI chip demand continues to surge as companies invest heavily in machine learning infrastructure.",
                source=DataSource.NEWSAPI,
                stock_symbol="NVDA"
            ),
            TextInput(
                text="Amazon stock looking bullish! Great fundamentals and strong market position 💪",
                source=DataSource.REDDIT,
                stock_symbol="AMZN"
            )
        ]
        
        print(f"Processing {len(test_inputs)} sample texts...")
        print("-" * 60)
        
        # Analyze sentiment
        start_time = datetime.now()
        results = await engine.analyze(test_inputs)
        end_time = datetime.now()
        
        processing_time = (end_time - start_time).total_seconds() * 1000
        
        # Display results
        for i, (input_text, result) in enumerate(zip(test_inputs, results)):
            print(f"\n📝 Sample {i+1}:")
            print(f"   Text: {input_text.text[:80]}{'...' if len(input_text.text) > 80 else ''}")
            print(f"   Source: {input_text.source.value}")
            print(f"   Symbol: {input_text.stock_symbol}")
            print(f"   Model: {result.model_name}")
            print(f"   Label: {result.label.value.upper()}")
            print(f"   Score: {result.score:.3f} (range: -1.0 to 1.0)")
            print(f"   Confidence: {result.confidence:.3f}")
            print(f"   Processing Time: {result.processing_time:.1f}ms")
            
            # Show sentiment interpretation
            if result.label == SentimentLabel.POSITIVE:
                emoji = "📈 🟢"
                interpretation = "Bullish sentiment"
            elif result.label == SentimentLabel.NEGATIVE:
                emoji = "📉 🔴"
                interpretation = "Bearish sentiment"
            else:
                emoji = "➡️ ⚪"
                interpretation = "Neutral sentiment"
            
            print(f"   Interpretation: {emoji} {interpretation}")
        
        print("\n" + "=" * 60)
        
        # Show engine statistics
        stats = engine.get_stats()
        print("📊 Engine Statistics:")
        print(f"   Total processed: {stats.total_texts_processed}")
        print(f"   Success rate: {stats.success_rate:.1f}%")
        print(f"   Average processing time: {stats.avg_processing_time:.1f}ms")
        print(f"   Total batch processing time: {processing_time:.1f}ms")
        print(f"   Model usage: {dict(stats.model_usage)}")
        
        # Performance metrics
        throughput = len(test_inputs) / (processing_time / 1000) if processing_time > 0 else 0
        print(f"   Throughput: {throughput:.1f} texts/second")
        
        print()
        
        # Health check
        print("🏥 System Health Check:")
        health = await engine.health_check()
        print(f"   Overall status: {health['overall_status'].upper()}")
        print(f"   Engine initialized: {health['engine_initialized']}")
        print(f"   Available models: {health['available_models']}")
        
        for model_name, model_health in health['models'].items():
            status = model_health.get('status', 'unknown').upper()
            print(f"   {model_name} status: {status}")
        
        print()
        
        # Show sentiment distribution
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        model_counts = {}
        
        for result in results:
            sentiment_counts[result.label.value] += 1
            model_counts[result.model_name] = model_counts.get(result.model_name, 0) + 1
        
        print("📈 Analysis Summary:")
        print(f"   Positive sentiment: {sentiment_counts['positive']}/{len(results)} ({sentiment_counts['positive']/len(results)*100:.1f}%)")
        print(f"   Negative sentiment: {sentiment_counts['negative']}/{len(results)} ({sentiment_counts['negative']/len(results)*100:.1f}%)")
        print(f"   Neutral sentiment: {sentiment_counts['neutral']}/{len(results)} ({sentiment_counts['neutral']/len(results)*100:.1f}%)")
        print()
        print("🤖 Model Usage:")
        for model, count in model_counts.items():
            print(f"   {model}: {count}/{len(results)} texts ({count/len(results)*100:.1f}%)")
        
        print("\n" + "=" * 60)
        print("✅ Phase 6 Sentiment Analysis Engine demonstration completed successfully!")
        print("🎯 Key Features Demonstrated:")
        print("   • Dual-model approach (FinBERT + VADER)")
        print("   • Intelligent source-based routing")
        print("   • Batch processing and optimization")
        print("   • Comprehensive error handling")
        print("   • Real-time performance monitoring")
        print("   • Health checks and statistics")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error during demonstration: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        try:
            await engine.shutdown()
            print("🔄 Engine shutdown completed")
        except Exception as e:
            print(f"⚠️  Error during shutdown: {str(e)}")
    
    return True


async def test_individual_models():
    """Test individual models separately."""
    print("\n🧪 Individual Model Testing")
    print("-" * 40)
    
    # Test VADER
    try:
        from app.service.sentiment_processing import VADERModel
        print("Testing VADER model...")
        
        vader = VADERModel()
        await vader.ensure_loaded()
        
        vader_inputs = [
            TextInput("This is amazing! 🚀", DataSource.REDDIT),
            TextInput("Terrible news today 😞", DataSource.REDDIT)
        ]
        
        vader_results = await vader.analyze(vader_inputs)
        print(f"✅ VADER: Analyzed {len(vader_results)} texts")
        
        for input_text, result in zip(vader_inputs, vader_results):
            print(f"   '{input_text.text}' → {result.label.value} ({result.score:.2f})")
    
    except Exception as e:
        print(f"❌ VADER test failed: {e}")
    
    # Test FinBERT (if available)
    try:
        from app.service.sentiment_processing import FinBERTModel
        from app.service.sentiment_processing.models.finbert_model import is_finbert_available
        
        if is_finbert_available():
            print("\nTesting FinBERT model...")
            
            finbert = FinBERTModel(use_gpu=False)
            await finbert.ensure_loaded()
            
            finbert_inputs = [
                TextInput("Company reports strong quarterly earnings", DataSource.NEWS),
                TextInput("Significant losses reported in Q3", DataSource.NEWS)
            ]
            
            finbert_results = await finbert.analyze(finbert_inputs)
            print(f"✅ FinBERT: Analyzed {len(finbert_results)} texts")
            
            for input_text, result in zip(finbert_inputs, finbert_results):
                print(f"   '{input_text.text}' → {result.label.value} ({result.score:.2f})")
            
            await finbert.cleanup()
        else:
            print("⚠️  FinBERT dependencies not available (requires transformers + torch)")
    
    except Exception as e:
        print(f"❌ FinBERT test failed: {e}")


if __name__ == "__main__":
    print("Starting Phase 6 Sentiment Analysis Engine Demo...")
    
    try:
        # Run main demonstration
        success = asyncio.run(demo_sentiment_analysis())
        
        if success:
            # Run individual model tests
            asyncio.run(test_individual_models())
            
            print("\n🎉 All demonstrations completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Demonstration failed")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)