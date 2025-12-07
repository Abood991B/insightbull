"""
Financial PhraseBank Benchmark - Compare ProsusAI/finbert vs yiyanghkust/finbert-tone
Uses local CSV file from data/training/financial_phrasebank.csv
"""

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import Dict, List, Tuple
import time
import pandas as pd
import os
import sys

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def load_financial_phrasebank() -> List[Tuple[str, str]]:
    """Load Financial PhraseBank from local CSV file."""
    
    csv_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "data", "training", "financial_phrasebank.csv"
    )
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Financial PhraseBank not found at: {csv_path}")
    
    df = pd.read_csv(csv_path)
    print(f"Loaded {len(df)} samples from Financial PhraseBank")
    print(f"Distribution: {df['label'].value_counts().to_dict()}")
    
    samples = [(row['text'], row['label'].lower()) for _, row in df.iterrows()]
    return samples


def test_model_on_phrasebank(model_name: str, label_map: Dict[int, str], samples: List[Tuple[str, str]]) -> Dict:
    """Test a model on Financial PhraseBank dataset."""
    
    print(f"\n{'='*60}")
    print(f"Testing: {model_name}")
    print(f"{'='*60}")
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    # Load model
    print("Loading model...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.to(device)
    model.eval()
    
    print(f"Total samples: {len(samples)}")
    
    correct = 0
    total = 0
    results_by_class = {
        'positive': {'correct': 0, 'total': 0},
        'negative': {'correct': 0, 'total': 0},
        'neutral': {'correct': 0, 'total': 0}
    }
    
    errors = []
    
    start_time = time.time()
    
    for i, (text, true_label) in enumerate(samples):
        # Get prediction
        encodings = tokenizer(
            text,
            truncation=True,
            padding=True,
            max_length=128,
            return_tensors='pt'
        )
        
        with torch.no_grad():
            outputs = model(
                input_ids=encodings['input_ids'].to(device),
                attention_mask=encodings['attention_mask'].to(device)
            )
            probs = torch.softmax(outputs.logits, dim=-1)[0]
        
        pred_id = torch.argmax(probs).item()
        pred_label = label_map[pred_id]
        confidence = probs[pred_id].item()
        
        results_by_class[true_label]['total'] += 1
        total += 1
        
        if pred_label == true_label:
            correct += 1
            results_by_class[true_label]['correct'] += 1
        else:
            if len(errors) < 10:  # Keep first 10 errors
                errors.append({
                    'text': text[:60] + '...' if len(text) > 60 else text,
                    'true': true_label,
                    'pred': pred_label,
                    'conf': confidence
                })
        
        if (i + 1) % 500 == 0:
            print(f"  Processed {i+1}/{len(samples)}...")
    
    elapsed = time.time() - start_time
    accuracy = correct / total if total > 0 else 0
    
    print(f"\n{'='*40}")
    print(f"RESULTS: {model_name}")
    print(f"{'='*40}")
    print(f"Overall Accuracy: {accuracy:.1%} ({correct}/{total})")
    print(f"Time: {elapsed:.1f}s")
    print(f"\nPer-class accuracy:")
    
    for cls, data in results_by_class.items():
        if data['total'] > 0:
            cls_acc = data['correct'] / data['total']
            print(f"  {cls}: {cls_acc:.1%} ({data['correct']}/{data['total']})")
    
    if errors:
        print(f"\nSample errors:")
        for e in errors[:5]:
            print(f"  [{e['true']} -> {e['pred']}] ({e['conf']:.0%}) {e['text']}")
    
    return {
        'model': model_name,
        'accuracy': accuracy,
        'correct': correct,
        'total': total,
        'class_accuracy': {
            cls: data['correct'] / data['total'] if data['total'] > 0 else 0
            for cls, data in results_by_class.items()
        },
        'time': elapsed
    }


def main():
    print("="*70)
    print("FINANCIAL PHRASEBANK BENCHMARK")
    print("Comparing ProsusAI/finbert vs yiyanghkust/finbert-tone")
    print("="*70)
    
    # Load data from local CSV
    samples = load_financial_phrasebank()
    
    if not samples:
        print("ERROR: No data available for testing!")
        return
    
    # Test ProsusAI/finbert
    # Label mapping: 0=positive, 1=negative, 2=neutral
    prosus_results = test_model_on_phrasebank(
        "ProsusAI/finbert",
        {0: "positive", 1: "negative", 2: "neutral"},
        samples
    )
    
    # Test yiyanghkust/finbert-tone
    # Label mapping: 0=neutral, 1=positive, 2=negative
    tone_results = test_model_on_phrasebank(
        "yiyanghkust/finbert-tone",
        {0: "neutral", 1: "positive", 2: "negative"},
        samples
    )
    
    # Summary
    print("\n" + "="*70)
    print("FINAL COMPARISON")
    print("="*70)
    print(f"\n{'Model':<30} {'Accuracy':<12} {'Positive':<10} {'Negative':<10} {'Neutral':<10}")
    print("-"*70)
    
    for r in [prosus_results, tone_results]:
        name = r['model'].split('/')[-1]
        print(f"{name:<30} {r['accuracy']:.1%}        "
              f"{r['class_accuracy']['positive']:.1%}      "
              f"{r['class_accuracy']['negative']:.1%}      "
              f"{r['class_accuracy']['neutral']:.1%}")
    
    print("\n" + "="*70)
    winner = prosus_results if prosus_results['accuracy'] > tone_results['accuracy'] else tone_results
    print(f"WINNER: {winner['model']} with {winner['accuracy']:.1%} accuracy")
    print("="*70)


if __name__ == "__main__":
    main()
