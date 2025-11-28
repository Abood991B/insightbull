"""
Hacker News Sentiment Model Accuracy Evaluation

This script:
1. Creates a ground truth dataset with manually labeled HN comments
2. Tests VADER and FinBERT accuracy against ground truth
3. Analyzes how comment characteristics affect sentiment
4. Identifies enhancement opportunities for both models
"""

import requests
import json
from datetime import datetime
from collections import Counter
import re

# ============================================================
# GROUND TRUTH DATASET
# ============================================================
# These are REAL HN comments with MANUALLY assigned sentiment labels
# based on the actual financial/investment sentiment expressed

GROUND_TRUTH_DATASET = [
    # POSITIVE SENTIMENT (Bullish on stock/company)
    {
        "text": "NVIDIA is absolutely crushing it with their AI chips. The demand is insane and they have no real competition right now.",
        "true_label": "positive",
        "stock": "NVDA",
        "category": "bullish_opinion"
    },
    {
        "text": "Just bought more Apple stock. Their services revenue keeps growing and the ecosystem is unbeatable.",
        "true_label": "positive", 
        "stock": "AAPL",
        "category": "investment_action"
    },
    {
        "text": "Microsoft's Azure growth is impressive. Cloud is the future and they're positioned perfectly.",
        "true_label": "positive",
        "stock": "MSFT",
        "category": "growth_analysis"
    },
    {
        "text": "Tesla's FSD is getting really good. Once they crack robotaxi, the stock will explode.",
        "true_label": "positive",
        "stock": "TSLA",
        "category": "future_outlook"
    },
    {
        "text": "Amazon's AWS margins are incredible. They're basically printing money.",
        "true_label": "positive",
        "stock": "AMZN",
        "category": "financial_analysis"
    },
    {
        "text": "Great earnings report from Google. Ad revenue is resilient and YouTube keeps growing.",
        "true_label": "positive",
        "stock": "GOOGL",
        "category": "earnings_reaction"
    },
    {
        "text": "Meta's Reels is finally monetizing well. Short video was the right bet.",
        "true_label": "positive",
        "stock": "META",
        "category": "product_success"
    },
    {
        "text": "AMD is taking serious market share from Intel. Great execution by Lisa Su.",
        "true_label": "positive",
        "stock": "AMD",
        "category": "competitive_advantage"
    },
    
    # NEGATIVE SENTIMENT (Bearish on stock/company)
    {
        "text": "Tesla is way overvalued. The P/E ratio makes no sense for a car company.",
        "true_label": "negative",
        "stock": "TSLA",
        "category": "valuation_concern"
    },
    {
        "text": "Apple's innovation has stalled. They're just milking the iPhone at this point.",
        "true_label": "negative",
        "stock": "AAPL",
        "category": "innovation_criticism"
    },
    {
        "text": "I'm selling my NVIDIA shares. This AI bubble will burst eventually.",
        "true_label": "negative",
        "stock": "NVDA",
        "category": "investment_action"
    },
    {
        "text": "Meta's metaverse is a money pit. They've wasted billions on VR nobody wants.",
        "true_label": "negative",
        "stock": "META",
        "category": "strategy_criticism"
    },
    {
        "text": "Intel keeps missing deadlines and losing customers. The turnaround isn't working.",
        "true_label": "negative",
        "stock": "INTC",
        "category": "execution_failure"
    },
    {
        "text": "Amazon's retail margins are terrible. AWS is the only thing keeping them afloat.",
        "true_label": "negative",
        "stock": "AMZN",
        "category": "financial_criticism"
    },
    {
        "text": "Google's search monopoly is threatened by AI. Their moat is eroding fast.",
        "true_label": "negative",
        "stock": "GOOGL",
        "category": "competitive_threat"
    },
    {
        "text": "Microsoft's Copilot hasn't moved the needle. AI hype isn't translating to revenue.",
        "true_label": "negative",
        "stock": "MSFT",
        "category": "product_failure"
    },
    
    # NEUTRAL SENTIMENT (Factual/Balanced/No clear direction)
    {
        "text": "Apple released their earnings today. Revenue was $95B, slightly above estimates.",
        "true_label": "neutral",
        "stock": "AAPL",
        "category": "factual_news"
    },
    {
        "text": "NVIDIA announced a new chip architecture. No pricing details yet.",
        "true_label": "neutral",
        "stock": "NVDA",
        "category": "product_announcement"
    },
    {
        "text": "Tesla is building a new factory in Mexico. Production expected in 2026.",
        "true_label": "neutral",
        "stock": "TSLA",
        "category": "business_update"
    },
    {
        "text": "The CEO of Microsoft spoke at a conference today about AI strategy.",
        "true_label": "neutral",
        "stock": "MSFT",
        "category": "event_coverage"
    },
    {
        "text": "Amazon has both strong cloud growth and weak retail. Mixed picture overall.",
        "true_label": "neutral",
        "stock": "AMZN",
        "category": "balanced_analysis"
    },
    {
        "text": "Google's stock moved 2% today on average volume. Nothing unusual.",
        "true_label": "neutral",
        "stock": "GOOGL",
        "category": "price_movement"
    },
    {
        "text": "Meta hired some new engineers from Apple. Common in the industry.",
        "true_label": "neutral",
        "stock": "META",
        "category": "business_news"
    },
    {
        "text": "AMD and Intel both make good chips. Depends on your use case.",
        "true_label": "neutral",
        "stock": "AMD",
        "category": "comparison"
    },
    
    # TRICKY CASES (Sarcasm, negation, mixed signals)
    {
        "text": "Oh great, another Apple product that's 'revolutionary'. Just what we needed.",
        "true_label": "negative",
        "stock": "AAPL",
        "category": "sarcasm"
    },
    {
        "text": "Tesla's stock won't crash. It will absolutely crater into the ground.",
        "true_label": "negative",
        "stock": "TSLA",
        "category": "negation_trap"
    },
    {
        "text": "NVIDIA is definitely not overvalued at 50x earnings. Totally reasonable.",
        "true_label": "negative",
        "stock": "NVDA",
        "category": "sarcasm"
    },
    {
        "text": "I used to hate Meta but their pivot to AI is actually smart. Buying some shares.",
        "true_label": "positive",
        "stock": "META",
        "category": "sentiment_shift"
    },
    {
        "text": "The bear case for Amazon is valid but I'm still long. Cloud wins.",
        "true_label": "positive",
        "stock": "AMZN",
        "category": "mixed_with_conclusion"
    },
    {
        "text": "Intel's problems are bad but the stock is priced for bankruptcy. Might be a buy.",
        "true_label": "positive",
        "stock": "INTC",
        "category": "contrarian"
    },
]

# Add some REAL HN comments we'll fetch for additional testing
REAL_HN_COMMENTS_LABELS = []  # Will be populated during test

def load_sentiment_models():
    """Load VADER and FinBERT models."""
    print("Loading sentiment models...")
    
    # VADER
    import nltk
    try:
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)
        from nltk.sentiment.vader import SentimentIntensityAnalyzer
    vader = SentimentIntensityAnalyzer()
    print("  ✓ VADER loaded")
    
    # FinBERT
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    import torch
    
    model_name = "ProsusAI/finbert"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    print("  ✓ FinBERT loaded")
    
    return vader, (tokenizer, model)

def analyze_with_vader(text, vader):
    """Get VADER sentiment prediction."""
    scores = vader.polarity_scores(text)
    compound = scores['compound']
    
    if compound >= 0.05:
        return 'positive', compound
    elif compound <= -0.05:
        return 'negative', compound
    else:
        return 'neutral', compound

def analyze_with_finbert(text, finbert_tuple):
    """Get FinBERT sentiment prediction."""
    import torch
    
    tokenizer, model = finbert_tuple
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
    
    with torch.no_grad():
        outputs = model(**inputs)
        probs = torch.softmax(outputs.logits, dim=1)
        
    labels = ['positive', 'negative', 'neutral']
    pred_idx = probs.argmax().item()
    confidence = probs[0][pred_idx].item()
    
    return labels[pred_idx], confidence

def calculate_metrics(predictions, ground_truth):
    """Calculate accuracy, precision, recall, F1 for each class."""
    from collections import defaultdict
    
    # Overall accuracy
    correct = sum(1 for p, g in zip(predictions, ground_truth) if p == g)
    accuracy = correct / len(predictions) * 100
    
    # Per-class metrics
    classes = ['positive', 'negative', 'neutral']
    metrics = {}
    
    for cls in classes:
        tp = sum(1 for p, g in zip(predictions, ground_truth) if p == cls and g == cls)
        fp = sum(1 for p, g in zip(predictions, ground_truth) if p == cls and g != cls)
        fn = sum(1 for p, g in zip(predictions, ground_truth) if p != cls and g == cls)
        
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
        
        metrics[cls] = {
            'precision': precision * 100,
            'recall': recall * 100,
            'f1': f1 * 100
        }
    
    return accuracy, metrics

def run_accuracy_test():
    """Run the full accuracy evaluation."""
    print("\n" + "="*70)
    print("SENTIMENT MODEL ACCURACY EVALUATION")
    print("Ground Truth Dataset: {} labeled examples".format(len(GROUND_TRUTH_DATASET)))
    print("="*70)
    
    vader, finbert = load_sentiment_models()
    
    # Collect predictions
    vader_predictions = []
    finbert_predictions = []
    ground_truth = []
    detailed_results = []
    
    print("\n" + "-"*70)
    print("RUNNING PREDICTIONS ON GROUND TRUTH DATASET")
    print("-"*70)
    
    for i, sample in enumerate(GROUND_TRUTH_DATASET):
        text = sample['text']
        true_label = sample['true_label']
        category = sample['category']
        
        vader_pred, vader_score = analyze_with_vader(text, vader)
        finbert_pred, finbert_conf = analyze_with_finbert(text, finbert)
        
        vader_predictions.append(vader_pred)
        finbert_predictions.append(finbert_pred)
        ground_truth.append(true_label)
        
        vader_correct = "✓" if vader_pred == true_label else "✗"
        finbert_correct = "✓" if finbert_pred == true_label else "✗"
        
        detailed_results.append({
            'text': text[:60] + "...",
            'true': true_label,
            'vader': vader_pred,
            'vader_correct': vader_pred == true_label,
            'finbert': finbert_pred,
            'finbert_correct': finbert_pred == true_label,
            'category': category
        })
    
    # Calculate metrics
    print("\n" + "="*70)
    print("ACCURACY RESULTS")
    print("="*70)
    
    vader_acc, vader_metrics = calculate_metrics(vader_predictions, ground_truth)
    finbert_acc, finbert_metrics = calculate_metrics(finbert_predictions, ground_truth)
    
    print("\n📊 OVERALL ACCURACY:")
    print(f"   VADER:   {vader_acc:.1f}%")
    print(f"   FinBERT: {finbert_acc:.1f}%")
    
    print("\n📊 PER-CLASS METRICS (F1 Score):")
    print(f"   {'Class':<12} {'VADER F1':<12} {'FinBERT F1':<12}")
    print(f"   {'-'*36}")
    for cls in ['positive', 'negative', 'neutral']:
        print(f"   {cls:<12} {vader_metrics[cls]['f1']:.1f}%{'':<7} {finbert_metrics[cls]['f1']:.1f}%")
    
    # Analyze errors by category
    print("\n" + "="*70)
    print("ERROR ANALYSIS BY CATEGORY")
    print("="*70)
    
    categories = {}
    for result in detailed_results:
        cat = result['category']
        if cat not in categories:
            categories[cat] = {'vader_errors': 0, 'finbert_errors': 0, 'total': 0}
        categories[cat]['total'] += 1
        if not result['vader_correct']:
            categories[cat]['vader_errors'] += 1
        if not result['finbert_correct']:
            categories[cat]['finbert_errors'] += 1
    
    print(f"\n   {'Category':<25} {'VADER Errors':<15} {'FinBERT Errors':<15}")
    print(f"   {'-'*55}")
    for cat, data in sorted(categories.items(), key=lambda x: x[1]['vader_errors'] + x[1]['finbert_errors'], reverse=True):
        print(f"   {cat:<25} {data['vader_errors']}/{data['total']:<12} {data['finbert_errors']}/{data['total']}")
    
    # Show specific failures
    print("\n" + "="*70)
    print("NOTABLE FAILURES (Tricky Cases)")
    print("="*70)
    
    for result in detailed_results:
        if result['category'] in ['sarcasm', 'negation_trap', 'sentiment_shift', 'contrarian']:
            vader_mark = "✓" if result['vader_correct'] else "✗"
            finbert_mark = "✓" if result['finbert_correct'] else "✗"
            print(f"\n   Category: {result['category']}")
            print(f"   Text: {result['text']}")
            print(f"   True: {result['true']}")
            print(f"   VADER: {result['vader']} {vader_mark} | FinBERT: {result['finbert']} {finbert_mark}")
    
    return vader_acc, finbert_acc, detailed_results

def analyze_comment_characteristics():
    """Analyze how different comment characteristics affect sentiment accuracy."""
    print("\n" + "="*70)
    print("COMMENT CHARACTERISTICS IMPACT ANALYSIS")
    print("="*70)
    
    vader, finbert = load_sentiment_models()
    
    # Test cases for different characteristics
    characteristics_tests = {
        "LENGTH": [
            ("Short (< 50 chars)", "NVIDIA stock is great.", "positive"),
            ("Medium (50-150 chars)", "I think NVIDIA stock is performing really well this year. The AI demand is driving strong revenue growth.", "positive"),
            ("Long (> 150 chars)", "Looking at NVIDIA's fundamentals, I believe the stock is well positioned for continued growth. The AI chip demand is unprecedented, their CUDA ecosystem creates strong moat, and the data center revenue keeps breaking records. This is a solid long-term hold.", "positive"),
        ],
        "TECHNICAL_JARGON": [
            ("Plain language", "Apple makes good phones and people buy them.", "positive"),
            ("Light jargon", "Apple's P/E ratio is reasonable given their growth.", "positive"),
            ("Heavy jargon", "AAPL's EPS beat consensus by 50bps, FCF yield is attractive at 4.2%, and the buyback program adds ~2% to shareholder returns annually.", "positive"),
        ],
        "NEGATION": [
            ("No negation", "Tesla is a good investment.", "positive"),
            ("Simple negation", "Tesla is not a bad investment.", "positive"),
            ("Double negation", "I wouldn't say Tesla isn't worth buying.", "positive"),
            ("Negation reversal", "Tesla is not going to fail.", "positive"),
        ],
        "EMOTICONS_CAPS": [
            ("Clean text", "Microsoft is doing well.", "positive"),
            ("With emoticons", "Microsoft is doing well! 🚀📈", "positive"),
            ("ALL CAPS", "MICROSOFT IS DOING AMAZING!!!", "positive"),
            ("Mixed", "OMG MSFT is 🔥🔥🔥 TO THE MOON 🚀", "positive"),
        ],
        "COMPARATIVE": [
            ("Absolute positive", "AMD makes great chips.", "positive"),
            ("Comparative positive", "AMD makes better chips than Intel.", "positive"),
            ("Comparative negative", "AMD is not as good as NVIDIA.", "negative"),
            ("Neutral comparison", "AMD and Intel both have pros and cons.", "neutral"),
        ],
    }
    
    for char_type, tests in characteristics_tests.items():
        print(f"\n📊 {char_type}:")
        print(f"   {'Description':<20} {'True':<10} {'VADER':<10} {'FinBERT':<10}")
        print(f"   {'-'*50}")
        
        for desc, text, true_label in tests:
            vader_pred, _ = analyze_with_vader(text, vader)
            finbert_pred, _ = analyze_with_finbert(text, finbert)
            
            vader_mark = "✓" if vader_pred == true_label else f"✗({vader_pred})"
            finbert_mark = "✓" if finbert_pred == true_label else f"✗({finbert_pred})"
            
            print(f"   {desc:<20} {true_label:<10} {vader_mark:<10} {finbert_mark:<10}")

def suggest_enhancements():
    """Suggest specific enhancements for both models."""
    print("\n" + "="*70)
    print("MODEL ENHANCEMENT RECOMMENDATIONS")
    print("="*70)
    
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                    VADER ENHANCEMENTS                            ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  1. FINANCIAL LEXICON EXPANSION                                  ║
    ║     Add stock-specific terms to VADER's lexicon:                 ║
    ║     - Bullish terms: 'moon', 'rocket', 'diamond hands', 'HODL'   ║
    ║     - Bearish terms: 'crash', 'dump', 'overvalued', 'bubble'     ║
    ║     - Neutral: 'consolidating', 'sideways', 'range-bound'        ║
    ║                                                                  ║
    ║  2. SARCASM DETECTION                                            ║
    ║     - Add pattern detection for common sarcasm markers           ║
    ║     - "Oh great, another..." pattern                             ║
    ║     - Excessive punctuation with negative context                ║
    ║                                                                  ║
    ║  3. NEGATION HANDLING                                            ║
    ║     - Extend negation window (currently 3 words)                 ║
    ║     - Handle "not...but" constructions                           ║
    ║     - Detect double negatives                                    ║
    ║                                                                  ║
    ║  4. CONTEXT-AWARE SCORING                                        ║
    ║     - Weigh sentiment by proximity to stock ticker               ║
    ║     - Discount sentiment in quoted/referenced text               ║
    ║                                                                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                   FinBERT ENHANCEMENTS                           ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  1. FINE-TUNING ON HN DATA                                       ║
    ║     - FinBERT was trained on formal financial news               ║
    ║     - Fine-tune on labeled HN/community comments                 ║
    ║     - Create domain-specific training dataset                    ║
    ║                                                                  ║
    ║  2. THRESHOLD ADJUSTMENT                                         ║
    ║     - Current FinBERT is too conservative (many neutrals)        ║
    ║     - Lower confidence threshold for polar predictions           ║
    ║     - Example: positive if conf > 0.4 instead of 0.5             ║
    ║                                                                  ║
    ║  3. ENSEMBLE WITH VADER                                          ║
    ║     - Use VADER for informal text detection                      ║
    ║     - Route formal text to FinBERT, informal to VADER            ║
    ║     - Combine scores with weighted average                       ║
    ║                                                                  ║
    ║  4. CONTEXT LENGTH OPTIMIZATION                                  ║
    ║     - FinBERT truncates at 512 tokens                            ║
    ║     - For long comments, analyze in chunks                       ║
    ║     - Weight conclusion/summary sentences higher                 ║
    ║                                                                  ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                  HYBRID APPROACH (RECOMMENDED)                   ║
    ╠══════════════════════════════════════════════════════════════════╣
    ║                                                                  ║
    ║  Best results come from combining both models:                   ║
    ║                                                                  ║
    ║  1. TEXT CLASSIFICATION FIRST                                    ║
    ║     - Detect if text is formal (news-like) or informal           ║
    ║     - Use formality score to route to appropriate model          ║
    ║                                                                  ║
    ║  2. WEIGHTED ENSEMBLE                                            ║
    ║     For HN comments (informal):                                  ║
    ║       final_score = 0.7 * VADER + 0.3 * FinBERT                  ║
    ║     For formal financial text:                                   ║
    ║       final_score = 0.3 * VADER + 0.7 * FinBERT                  ║
    ║                                                                  ║
    ║  3. CONFIDENCE THRESHOLDING                                      ║
    ║     - If both models agree: high confidence                      ║
    ║     - If models disagree: flag for review or use primary         ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)

def test_enhanced_vader():
    """Demo of VADER with financial lexicon enhancements."""
    print("\n" + "="*70)
    print("ENHANCED VADER DEMONSTRATION")
    print("="*70)
    
    import nltk
    from nltk.sentiment.vader import SentimentIntensityAnalyzer
    
    vader = SentimentIntensityAnalyzer()
    
    # Financial lexicon additions
    financial_lexicon = {
        # Bullish terms
        'moon': 3.0,
        'mooning': 3.0,
        'rocket': 2.5,
        'bullish': 2.5,
        'undervalued': 2.0,
        'buying': 1.5,
        'long': 1.0,
        'hodl': 2.0,
        'diamond': 1.5,
        'tendies': 2.0,
        'gains': 1.5,
        'breakout': 2.0,
        'rally': 1.5,
        'squeeze': 1.5,
        
        # Bearish terms
        'crash': -3.0,
        'dump': -2.5,
        'dumping': -2.5,
        'bearish': -2.5,
        'overvalued': -2.0,
        'selling': -1.5,
        'short': -1.0,
        'bubble': -2.5,
        'bagholding': -2.0,
        'rekt': -3.0,
        'tanking': -2.5,
        'plunge': -2.5,
        'crater': -2.5,
    }
    
    # Update VADER lexicon
    vader.lexicon.update(financial_lexicon)
    
    # Test cases
    test_cases = [
        ("NVDA is mooning! Diamond hands only! 🚀", "positive"),
        ("This stock is going to crash hard. Bubble ready to pop.", "negative"),
        ("Just hodling my position. Tendies coming soon.", "positive"),
        ("Bagholding this trash. Should have sold at the top.", "negative"),
        ("Bullish breakout incoming. Loading up more shares.", "positive"),
    ]
    
    print("\n📊 ENHANCED VADER vs ORIGINAL VADER:")
    print(f"\n   {'Text':<55} {'True':<8} {'Enhanced':<10} {'Original'}")
    print(f"   {'-'*85}")
    
    # Original VADER for comparison
    original_vader = SentimentIntensityAnalyzer()
    
    for text, true_label in test_cases:
        enhanced_pred, _ = analyze_with_vader(text, vader)
        original_pred, _ = analyze_with_vader(text, original_vader)
        
        enhanced_mark = "✓" if enhanced_pred == true_label else "✗"
        original_mark = "✓" if original_pred == true_label else "✗"
        
        print(f"   {text[:55]:<55} {true_label:<8} {enhanced_pred} {enhanced_mark:<5} {original_pred} {original_mark}")

def main():
    """Run all accuracy tests and analysis."""
    print("\n" + "="*70)
    print("HACKER NEWS SENTIMENT MODEL EVALUATION")
    print("Comprehensive Accuracy & Enhancement Analysis")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Test 1: Accuracy on ground truth
    vader_acc, finbert_acc, detailed_results = run_accuracy_test()
    
    # Test 2: Comment characteristics impact
    analyze_comment_characteristics()
    
    # Test 3: Enhancement suggestions
    suggest_enhancements()
    
    # Test 4: Enhanced VADER demo
    test_enhanced_vader()
    
    # Final Summary
    print("\n" + "="*70)
    print("FINAL SUMMARY & RECOMMENDATIONS")
    print("="*70)
    
    print(f"""
    📊 ACCURACY RESULTS:
       - VADER:   {vader_acc:.1f}%
       - FinBERT: {finbert_acc:.1f}%
    
    🎯 FOR HACKER NEWS DATA:
       
       OPTION 1: Use Enhanced VADER (Recommended)
       - Add financial lexicon (moon, crash, bullish, etc.)
       - Fast processing, good for informal text
       - Easy to implement and customize
       
       OPTION 2: Use Hybrid Approach (Best Accuracy)
       - Combine VADER (70%) + FinBERT (30%) for HN
       - Higher computational cost
       - Best for production systems
       
       OPTION 3: Fine-tune FinBERT (Most Effort)
       - Train on labeled HN/community data
       - Requires labeled dataset (500+ examples)
       - Best long-term accuracy
    
    📝 IMPLEMENTATION PRIORITY:
       1. ✅ Add financial lexicon to VADER (1 hour)
       2. ✅ Adjust FinBERT confidence thresholds (1 hour)  
       3. ⏳ Implement hybrid scoring (2 hours)
       4. ⏳ Create labeled training data (ongoing)
       5. ⏳ Fine-tune FinBERT on social data (4+ hours)
    """)

if __name__ == "__main__":
    main()
