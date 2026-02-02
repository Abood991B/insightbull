"""
Alternative Model Benchmark Verification
=========================================
Verifies the finbert-tone model metrics for comparison claims in FYP Report Chapter 9.
"""

import sys
import time
from pathlib import Path
import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

# Dataset path
DATASET_PATH = Path(__file__).parent.parent / "data" / "training" / "financial_phrasebank.csv"

# Alternative model to verify
MODEL_NAME = "yiyanghkust/finbert-tone"

# FinBERT-tone has different label mapping
# Actual mapping from model config: {0: 'Neutral', 1: 'Positive', 2: 'Negative'}
TONE_LABEL_MAP = {0: "neutral", 1: "positive", 2: "negative"}
GROUND_TRUTH_LABELS = ["positive", "negative", "neutral"]


def main():
    print("="*70)
    print("FINBERT-TONE MODEL VERIFICATION")
    print("="*70)
    
    # Load dataset
    df = pd.read_csv(DATASET_PATH)
    print(f"\nDataset: {len(df)} samples")
    
    # Load model
    print(f"\nLoading model: {MODEL_NAME}")
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()
    
    # Run predictions
    print("\nRunning predictions...")
    predictions = []
    batch_size = 32
    
    start_time = time.time()
    texts = df["text"].values
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size].tolist()
        
        inputs = tokenizer(
            batch_texts,
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            pred_indices = torch.argmax(probs, dim=1)
        
        for idx in pred_indices:
            predictions.append(TONE_LABEL_MAP[idx.item()])
        
        if (i + batch_size) % 1000 == 0:
            print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)}")
    
    pred_time = time.time() - start_time
    print(f"\nPrediction time: {pred_time:.2f}s")
    
    # Calculate metrics
    y_true = df["label"].values
    y_pred = np.array(predictions)
    
    accuracy = accuracy_score(y_true, y_pred) * 100
    
    # Per-class metrics
    prec_per_class = precision_score(y_true, y_pred, labels=GROUND_TRUTH_LABELS, average=None, zero_division=0) * 100
    rec_per_class = recall_score(y_true, y_pred, labels=GROUND_TRUTH_LABELS, average=None, zero_division=0) * 100
    
    print("\n" + "="*70)
    print("FINBERT-TONE RESULTS")
    print("="*70)
    print(f"\nAccuracy: {accuracy:.2f}%")
    
    print("\nPer-class metrics:")
    for i, label in enumerate(GROUND_TRUTH_LABELS):
        print(f"  {label.capitalize()}: Precision={prec_per_class[i]:.2f}%, Recall={rec_per_class[i]:.2f}%")
    
    # Compare with report claims
    print("\n" + "="*70)
    print("COMPARISON WITH FYP REPORT CLAIMS")
    print("="*70)
    
    report_claims = {
        "accuracy": 78.80,
        "positive_recall": 57.30,
        "negative_recall": 67.40,
        "neutral_precision": 91.80
    }
    
    calculated = {
        "accuracy": accuracy,
        "positive_recall": rec_per_class[0],  # positive is index 0
        "negative_recall": rec_per_class[1],  # negative is index 1
        "neutral_precision": prec_per_class[2]  # neutral is index 2
    }
    
    print(f"\n{'Metric':<20} {'Report':<12} {'Calculated':<12} {'Match':<8}")
    print("-"*60)
    
    all_match = True
    for metric in report_claims:
        expected = report_claims[metric]
        actual = calculated[metric]
        diff = abs(expected - actual)
        match = diff < 1.0  # Allow 1% tolerance
        if not match:
            all_match = False
        print(f"{metric:<20} {expected:<12.2f} {actual:<12.2f} {'YES' if match else 'NO':<8}")
    
    print("-"*60)
    print(f"\nAll values match: {'YES' if all_match else 'NO'}")


if __name__ == "__main__":
    main()
