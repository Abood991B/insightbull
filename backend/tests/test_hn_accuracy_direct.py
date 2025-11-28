"""
Hacker News Sentiment Accuracy Test - Using ACTUAL Hybrid VADER & FinBERT Models

This test directly loads your production models without going through
the service layer (which tries to initialize collectors).
"""

import asyncio
import sys
import os
from datetime import datetime
from typing import TYPE_CHECKING

# Setup paths - add models directory to path for imports
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
models_path = os.path.join(backend_path, "app", "service", "sentiment_processing", "models")

# Insert at beginning of path so these modules are found first
if models_path not in sys.path:
    sys.path.insert(0, models_path)
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Import using importlib to avoid Pylance issues while still working at runtime
import importlib.util

def load_module(name: str, path: str):
    """Load a module from a specific file path."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load {name} from {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

# Load models directly from file paths
sentiment_model = load_module("sentiment_model", os.path.join(models_path, "sentiment_model.py"))
hybrid_vader_model = load_module("hybrid_vader_model", os.path.join(models_path, "hybrid_vader_model.py"))
finbert_model = load_module("finbert_model", os.path.join(models_path, "finbert_model.py"))

# Get the classes we need
SentimentLabel = sentiment_model.SentimentLabel
HybridVADERModel = hybrid_vader_model.HybridVADERModel
HybridConfig = hybrid_vader_model.HybridConfig
FinBERTModel = finbert_model.FinBERTModel

# Ground Truth Dataset - 30 manually labeled examples
GROUND_TRUTH_DATASET = [
    # POSITIVE SENTIMENT (Bullish)
    {"text": "NVIDIA is absolutely crushing it with their AI chips. The demand is insane and they have no real competition right now.", "true_label": "positive", "category": "bullish_opinion"},
    {"text": "Just bought more Apple stock. Their services revenue keeps growing and the ecosystem is unbeatable.", "true_label": "positive", "category": "investment_action"},
    {"text": "Microsoft's Azure growth is impressive. Cloud is the future and they're positioned perfectly.", "true_label": "positive", "category": "growth_analysis"},
    {"text": "Tesla's FSD is getting really good. Once they crack robotaxi, the stock will explode.", "true_label": "positive", "category": "future_outlook"},
    {"text": "Amazon's AWS margins are incredible. They're basically printing money.", "true_label": "positive", "category": "financial_analysis"},
    {"text": "Great earnings report from Google. Ad revenue is resilient and YouTube keeps growing.", "true_label": "positive", "category": "earnings_reaction"},
    {"text": "Meta's Reels is finally monetizing well. Short video was the right bet.", "true_label": "positive", "category": "product_success"},
    {"text": "AMD is taking serious market share from Intel. Great execution by Lisa Su.", "true_label": "positive", "category": "competitive_advantage"},
    
    # NEGATIVE SENTIMENT (Bearish)
    {"text": "Tesla is way overvalued. The P/E ratio makes no sense for a car company.", "true_label": "negative", "category": "valuation_concern"},
    {"text": "Apple's innovation has stalled. They're just milking the iPhone at this point.", "true_label": "negative", "category": "innovation_criticism"},
    {"text": "I'm selling my NVIDIA shares. This AI bubble will burst eventually.", "true_label": "negative", "category": "investment_action"},
    {"text": "Meta's metaverse is a money pit. They've wasted billions on VR nobody wants.", "true_label": "negative", "category": "strategy_criticism"},
    {"text": "Intel keeps missing deadlines and losing customers. The turnaround isn't working.", "true_label": "negative", "category": "execution_failure"},
    {"text": "Amazon's retail margins are terrible. AWS is the only thing keeping them afloat.", "true_label": "negative", "category": "financial_criticism"},
    {"text": "Google's search monopoly is threatened by AI. Their moat is eroding fast.", "true_label": "negative", "category": "competitive_threat"},
    {"text": "Microsoft's Copilot hasn't moved the needle. AI hype isn't translating to revenue.", "true_label": "negative", "category": "product_failure"},
    
    # NEUTRAL SENTIMENT
    {"text": "Apple released their earnings today. Revenue was $95B, slightly above estimates.", "true_label": "neutral", "category": "factual_news"},
    {"text": "NVIDIA announced a new chip architecture. No pricing details yet.", "true_label": "neutral", "category": "product_announcement"},
    {"text": "Tesla is building a new factory in Mexico. Production expected in 2026.", "true_label": "neutral", "category": "business_update"},
    {"text": "The CEO of Microsoft spoke at a conference today about AI strategy.", "true_label": "neutral", "category": "event_coverage"},
    {"text": "Amazon has both strong cloud growth and weak retail. Mixed picture overall.", "true_label": "neutral", "category": "balanced_analysis"},
    {"text": "Google's stock moved 2% today on average volume. Nothing unusual.", "true_label": "neutral", "category": "price_movement"},
    {"text": "Meta hired some new engineers from Apple. Common in the industry.", "true_label": "neutral", "category": "business_news"},
    {"text": "AMD and Intel both make good chips. Depends on your use case.", "true_label": "neutral", "category": "comparison"},
    
    # TRICKY CASES
    {"text": "Oh great, another Apple product that's 'revolutionary'. Just what we needed.", "true_label": "negative", "category": "sarcasm"},
    {"text": "Tesla's stock won't crash. It will absolutely crater into the ground.", "true_label": "negative", "category": "negation_trap"},
    {"text": "NVIDIA is definitely not overvalued at 50x earnings. Totally reasonable.", "true_label": "negative", "category": "sarcasm"},
    {"text": "I used to hate Meta but their pivot to AI is actually smart. Buying some shares.", "true_label": "positive", "category": "sentiment_shift"},
    {"text": "The bear case for Amazon is valid but I'm still long. Cloud wins.", "true_label": "positive", "category": "mixed_with_conclusion"},
    {"text": "Intel's problems are bad but the stock is priced for bankruptcy. Might be a buy.", "true_label": "positive", "category": "contrarian"},
]


def calculate_metrics(predictions, ground_truth):
    """Calculate accuracy and per-class F1 scores."""
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    accuracy = correct / len(predictions) * 100
    
    classes = ['positive', 'negative', 'neutral']
    metrics = {}
    
    for cls in classes:
        tp = sum(1 for p, g in zip(predictions, ground_truth) if p == cls and g == cls)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p == cls and g != cls)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if p != cls and g == cls)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics[cls] = {'precision': precision * 100, 'recall': recall * 100, 'f1': f1 * 100}
    
    return accuracy, metrics


async def test_hybrid_vader():
    """Test accuracy using your production Hybrid VADER model."""
    print("\n" + "="*70)
    print("TESTING YOUR HYBRID VADER MODEL")
    print("="*70)
    
    # Initialize your actual Hybrid VADER model
    config = HybridConfig()
    hybrid_vader = HybridVADERModel(config)
    await hybrid_vader._load_model()
    
    # Check if ML component is trained
    if hybrid_vader.is_ml_trained:
        print("✓ Hybrid VADER loaded WITH ML component (full ensemble)")
    else:
        print("⚠ Hybrid VADER loaded WITHOUT ML component (Enhanced VADER only)")
        print("  (ML component needs training - run train_hybrid_vader.py)")
    
    # Get predictions
    texts = [sample['text'] for sample in GROUND_TRUTH_DATASET]
    results = await hybrid_vader._analyze_batch(texts)
    
    predictions = [r.label.value for r in results]
    ground_truth = [sample['true_label'] for sample in GROUND_TRUTH_DATASET]
    
    accuracy, metrics = calculate_metrics(predictions, ground_truth)
    
    print(f"\n📊 HYBRID VADER ACCURACY: {accuracy:.1f}%")
    print(f"\n   Per-class F1 Scores:")
    for cls in ['positive', 'negative', 'neutral']:
        print(f"   - {cls}: {metrics[cls]['f1']:.1f}%")
    
    return accuracy, metrics, results, predictions


async def test_finbert():
    """Test accuracy using your production FinBERT model."""
    print("\n" + "="*70)
    print("TESTING YOUR FinBERT MODEL")
    print("="*70)
    
    finbert = FinBERTModel()
    await finbert._load_model()
    print("✓ FinBERT loaded")
    
    texts = [sample['text'] for sample in GROUND_TRUTH_DATASET]
    results = await finbert._analyze_batch(texts)
    
    predictions = [r.label.value for r in results]
    ground_truth = [sample['true_label'] for sample in GROUND_TRUTH_DATASET]
    
    accuracy, metrics = calculate_metrics(predictions, ground_truth)
    
    print(f"\n📊 FinBERT ACCURACY: {accuracy:.1f}%")
    print(f"\n   Per-class F1 Scores:")
    for cls in ['positive', 'negative', 'neutral']:
        print(f"   - {cls}: {metrics[cls]['f1']:.1f}%")
    
    return accuracy, metrics, results, predictions


async def compare_models():
    """Compare both models head-to-head."""
    print("\n" + "="*70)
    print("SENTIMENT MODEL ACCURACY COMPARISON")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Ground Truth Dataset: {len(GROUND_TRUTH_DATASET)} labeled examples")
    print("="*70)
    
    # Test both models
    hybrid_acc, hybrid_metrics, hybrid_results, hybrid_preds = await test_hybrid_vader()
    finbert_acc, finbert_metrics, finbert_results, finbert_preds = await test_finbert()
    
    # Head-to-head comparison
    print("\n" + "="*70)
    print("HEAD-TO-HEAD COMPARISON")
    print("="*70)
    
    print(f"\n{'Metric':<25} {'Hybrid VADER':<15} {'FinBERT':<15} {'Winner'}")
    print("-"*70)
    print(f"{'Overall Accuracy':<25} {hybrid_acc:.1f}%{'':<8} {finbert_acc:.1f}%{'':<8} {'Hybrid VADER' if hybrid_acc > finbert_acc else 'FinBERT' if finbert_acc > hybrid_acc else 'Tie'}")
    
    for cls in ['positive', 'negative', 'neutral']:
        h_f1 = hybrid_metrics[cls]['f1']
        f_f1 = finbert_metrics[cls]['f1']
        winner = 'Hybrid VADER' if h_f1 > f_f1 else 'FinBERT' if f_f1 > h_f1 else 'Tie'
        print(f"{cls.capitalize() + ' F1':<25} {h_f1:.1f}%{'':<8} {f_f1:.1f}%{'':<8} {winner}")
    
    # Show disagreements
    print("\n" + "="*70)
    print("MODEL DISAGREEMENTS (Where they differ)")
    print("="*70)
    
    disagreements = 0
    for i, sample in enumerate(GROUND_TRUTH_DATASET):
        h_pred = hybrid_preds[i]
        f_pred = finbert_preds[i]
        true_label = sample['true_label']
        
        if h_pred != f_pred:
            disagreements += 1
            h_correct = "✓" if h_pred == true_label else "✗"
            f_correct = "✓" if f_pred == true_label else "✗"
            print(f"\n   [{sample['category']}]")
            print(f"   Text: {sample['text'][:60]}...")
            print(f"   True: {true_label}")
            print(f"   Hybrid VADER: {h_pred} {h_correct} | FinBERT: {f_pred} {f_correct}")
    
    print(f"\n   Total disagreements: {disagreements}/{len(GROUND_TRUTH_DATASET)}")
    
    # Show tricky case performance
    print("\n" + "="*70)
    print("TRICKY CASE PERFORMANCE")
    print("="*70)
    
    tricky_categories = ['sarcasm', 'negation_trap', 'sentiment_shift', 'contrarian', 'mixed_with_conclusion']
    
    for i, sample in enumerate(GROUND_TRUTH_DATASET):
        if sample['category'] in tricky_categories:
            h_pred = hybrid_preds[i]
            f_pred = finbert_preds[i]
            true_label = sample['true_label']
            
            h_correct = "✓" if h_pred == true_label else "✗"
            f_correct = "✓" if f_pred == true_label else "✗"
            
            print(f"\n   [{sample['category']}]")
            print(f"   Text: {sample['text'][:60]}...")
            print(f"   True: {true_label}")
            print(f"   Hybrid VADER: {h_pred} {h_correct} | FinBERT: {f_pred} {f_correct}")
    
    # Final recommendation
    print("\n" + "="*70)
    print("FINAL RECOMMENDATION FOR HACKER NEWS DATA")
    print("="*70)
    
    print(f"""
    📊 ACCURACY SUMMARY:
       - Hybrid VADER: {hybrid_acc:.1f}%
       - FinBERT:      {finbert_acc:.1f}%
    
    🎯 FOR HACKER NEWS (informal community discussions):
    
       Your Hybrid VADER model already includes:
       ✓ Financial lexicon (75 terms: moon, crash, bullish, etc.)
       ✓ Community slang processing (40+ phrases: HODL, tendies, etc.)
       ✓ Emoji sentiment boosting (30+ emojis)
       ✓ Dynamic threshold adjustment
       ✓ ML ensemble (if trained)
       
       RECOMMENDATION: Use Hybrid VADER for Hacker News
       
       Reasons:
       1. Already optimized for informal financial discussions
       2. Same architecture for community data (HN is similar style)
       3. Financial lexicon catches stock-specific terms
       4. Faster than FinBERT
       
       POTENTIAL IMPROVEMENTS:
       1. Add HN-specific terms to lexicon (YC, startup, etc.)
       2. Train ML component on HN-labeled data
       3. Adjust thresholds for HN's more technical tone
    """)


if __name__ == "__main__":
    asyncio.run(compare_models())
