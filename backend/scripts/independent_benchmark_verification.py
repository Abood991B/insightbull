"""
Independent Benchmark Verification Script
=========================================
This script independently verifies all benchmark values claimed in the FYP Report.
It runs FinBERT model on the Financial PhraseBank dataset and calculates all metrics from scratch.

Date: Fresh verification run
Purpose: Validate FYP Report Chapter 8 and 9 numerical claims
"""

import os
import sys
import time
import json
from datetime import datetime, timezone
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from sklearn.metrics import (
    accuracy_score, 
    precision_score, 
    recall_score, 
    f1_score, 
    confusion_matrix,
    classification_report
)

# ============================================================================
# CONFIGURATION - Matching FYP Report specifications
# ============================================================================
MODEL_NAME = "ProsusAI/finbert"
DATASET_PATH = Path(__file__).parent.parent / "data" / "training" / "financial_phrasebank.csv"
CONFIDENCE_THRESHOLD = 0.85  # As specified in FYP Report

# Label mapping for FinBERT model
FINBERT_LABEL_MAP = {0: "positive", 1: "negative", 2: "neutral"}
GROUND_TRUTH_LABELS = ["positive", "negative", "neutral"]

# ============================================================================
# EXPECTED VALUES FROM FYP REPORT (for comparison)
# ============================================================================
EXPECTED_VALUES = {
    "dataset_size": 5057,
    "positive_count": 1425,
    "negative_count": 688,
    "neutral_count": 2944,
    "accuracy": 88.33,
    "macro_precision": 85.46,
    "macro_recall": 90.47,
    "macro_f1": 87.56,
    "positive_precision": 79.91,
    "positive_recall": 90.74,
    "positive_f1": 84.98,
    "negative_precision": 80.83,
    "negative_recall": 95.06,
    "negative_f1": 87.37,
    "neutral_precision": 95.64,
    "neutral_recall": 85.60,
    "neutral_f1": 90.34,
    "confidence_threshold": 0.85,
}


def load_dataset():
    """Load and validate the Financial PhraseBank dataset."""
    print("\n" + "="*80)
    print("STEP 1: Loading Dataset")
    print("="*80)
    
    df = pd.read_csv(DATASET_PATH)
    print(f"Dataset path: {DATASET_PATH}")
    print(f"Total samples loaded: {len(df)}")
    
    # Validate columns
    assert "text" in df.columns, "Missing 'text' column"
    assert "label" in df.columns, "Missing 'label' column"
    
    # Count distribution
    label_counts = df["label"].value_counts()
    print(f"\nLabel Distribution:")
    for label in GROUND_TRUTH_LABELS:
        count = label_counts.get(label, 0)
        print(f"  {label}: {count}")
    
    return df


def load_model():
    """Load FinBERT model and tokenizer."""
    print("\n" + "="*80)
    print("STEP 2: Loading FinBERT Model")
    print("="*80)
    
    print(f"Model: {MODEL_NAME}")
    
    # Check for GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.to(device)
    model.eval()
    
    print("Model loaded successfully")
    return tokenizer, model, device


def predict_batch(texts, tokenizer, model, device, batch_size=32):
    """Run predictions on a batch of texts."""
    predictions = []
    confidences = []
    
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i:i+batch_size]
        
        # Tokenize
        inputs = tokenizer(
            batch_texts.tolist() if hasattr(batch_texts, 'tolist') else list(batch_texts),
            padding=True,
            truncation=True,
            max_length=512,
            return_tensors="pt"
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Predict
        with torch.no_grad():
            outputs = model(**inputs)
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
        # Get predictions and confidence
        max_probs, pred_indices = torch.max(probs, dim=1)
        
        for j in range(len(batch_texts)):
            pred_idx = pred_indices[j].item()
            pred_label = FINBERT_LABEL_MAP[pred_idx]
            confidence = max_probs[j].item()
            
            predictions.append(pred_label)
            confidences.append(confidence)
        
        # Progress indicator
        if (i + batch_size) % 500 == 0 or i + batch_size >= len(texts):
            print(f"  Processed {min(i + batch_size, len(texts))}/{len(texts)} samples...")
    
    return predictions, confidences


def calculate_metrics(y_true, y_pred):
    """Calculate all metrics independently."""
    print("\n" + "="*80)
    print("STEP 4: Calculating Metrics")
    print("="*80)
    
    # Accuracy
    accuracy = accuracy_score(y_true, y_pred) * 100
    
    # Macro averages
    macro_precision = precision_score(y_true, y_pred, average='macro', zero_division=0) * 100
    macro_recall = recall_score(y_true, y_pred, average='macro', zero_division=0) * 100
    macro_f1 = f1_score(y_true, y_pred, average='macro', zero_division=0) * 100
    
    # Per-class metrics
    class_precision = precision_score(y_true, y_pred, labels=GROUND_TRUTH_LABELS, average=None, zero_division=0) * 100
    class_recall = recall_score(y_true, y_pred, labels=GROUND_TRUTH_LABELS, average=None, zero_division=0) * 100
    class_f1 = f1_score(y_true, y_pred, labels=GROUND_TRUTH_LABELS, average=None, zero_division=0) * 100
    
    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=GROUND_TRUTH_LABELS)
    
    results = {
        "accuracy": round(accuracy, 2),
        "macro_precision": round(macro_precision, 2),
        "macro_recall": round(macro_recall, 2),
        "macro_f1": round(macro_f1, 2),
        "per_class": {},
        "confusion_matrix": cm.tolist()
    }
    
    for i, label in enumerate(GROUND_TRUTH_LABELS):
        results["per_class"][label] = {
            "precision": round(class_precision[i], 2),
            "recall": round(class_recall[i], 2),
            "f1": round(class_f1[i], 2)
        }
    
    return results


def analyze_confidence_distribution(confidences, y_true, y_pred):
    """Analyze predictions by confidence threshold."""
    print("\n" + "="*80)
    print("STEP 5: Confidence Distribution Analysis")
    print("="*80)
    
    confidences = np.array(confidences)
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    
    # Count above/below threshold
    high_conf_mask = confidences >= CONFIDENCE_THRESHOLD
    low_conf_mask = confidences < CONFIDENCE_THRESHOLD
    
    high_conf_count = high_conf_mask.sum()
    low_conf_count = low_conf_mask.sum()
    
    print(f"Confidence Threshold: {CONFIDENCE_THRESHOLD}")
    print(f"High Confidence (>= {CONFIDENCE_THRESHOLD}): {high_conf_count} ({high_conf_count/len(confidences)*100:.2f}%)")
    print(f"Low Confidence (< {CONFIDENCE_THRESHOLD}): {low_conf_count} ({low_conf_count/len(confidences)*100:.2f}%)")
    
    # Accuracy for each group
    if high_conf_count > 0:
        high_conf_acc = accuracy_score(y_true[high_conf_mask], y_pred[high_conf_mask]) * 100
        print(f"\nHigh Confidence Accuracy: {high_conf_acc:.2f}%")
    
    if low_conf_count > 0:
        low_conf_acc = accuracy_score(y_true[low_conf_mask], y_pred[low_conf_mask]) * 100
        print(f"Low Confidence Accuracy: {low_conf_acc:.2f}%")
    
    return {
        "threshold": CONFIDENCE_THRESHOLD,
        "high_confidence_count": int(high_conf_count),
        "low_confidence_count": int(low_conf_count),
        "high_confidence_percentage": round(high_conf_count/len(confidences)*100, 2),
        "low_confidence_percentage": round(low_conf_count/len(confidences)*100, 2)
    }


def compare_with_expected(results, df):
    """Compare calculated results with expected values from FYP Report."""
    print("\n" + "="*80)
    print("STEP 6: Comparison with FYP Report Values")
    print("="*80)
    
    comparisons = []
    
    # Dataset size comparison
    comparisons.append({
        "metric": "Dataset Size",
        "expected": EXPECTED_VALUES["dataset_size"],
        "calculated": len(df),
        "match": len(df) == EXPECTED_VALUES["dataset_size"]
    })
    
    # Label counts
    label_counts = df["label"].value_counts()
    for label in ["positive", "negative", "neutral"]:
        expected_key = f"{label}_count"
        comparisons.append({
            "metric": f"{label.capitalize()} Count",
            "expected": EXPECTED_VALUES[expected_key],
            "calculated": int(label_counts.get(label, 0)),
            "match": int(label_counts.get(label, 0)) == EXPECTED_VALUES[expected_key]
        })
    
    # Main metrics
    for metric in ["accuracy", "macro_precision", "macro_recall", "macro_f1"]:
        expected = EXPECTED_VALUES[metric]
        calculated = results[metric]
        diff = abs(expected - calculated)
        comparisons.append({
            "metric": metric.replace("_", " ").title(),
            "expected": expected,
            "calculated": calculated,
            "difference": round(diff, 2),
            "match": diff < 0.5  # Allow 0.5% tolerance
        })
    
    # Per-class metrics
    for label in GROUND_TRUTH_LABELS:
        for metric_type in ["precision", "recall", "f1"]:
            expected_key = f"{label}_{metric_type}"
            expected = EXPECTED_VALUES[expected_key]
            calculated = results["per_class"][label][metric_type]
            diff = abs(expected - calculated)
            comparisons.append({
                "metric": f"{label.capitalize()} {metric_type.capitalize()}",
                "expected": expected,
                "calculated": calculated,
                "difference": round(diff, 2),
                "match": diff < 0.5
            })
    
    # Print comparison table
    print("\n{:<25} {:>12} {:>12} {:>10} {:>8}".format(
        "Metric", "Expected", "Calculated", "Diff", "Match"
    ))
    print("-" * 70)
    
    all_match = True
    for comp in comparisons:
        diff_str = f"{comp.get('difference', 0):.2f}" if 'difference' in comp else "N/A"
        match_str = "YES" if comp["match"] else "NO"
        if not comp["match"]:
            all_match = False
        print("{:<25} {:>12} {:>12} {:>10} {:>8}".format(
            comp["metric"],
            str(comp["expected"]),
            str(comp["calculated"]),
            diff_str,
            match_str
        ))
    
    return comparisons, all_match


def main():
    """Main verification function."""
    print("\n")
    print("="*80)
    print("INDEPENDENT BENCHMARK VERIFICATION")
    print("FYP Report Numerical Claims Verification")
    print(f"Run Time: {datetime.now(timezone.utc).isoformat()}")
    print("="*80)
    
    start_time = time.time()
    
    # Step 1: Load dataset
    df = load_dataset()
    
    # Step 2: Load model
    tokenizer, model, device = load_model()
    
    # Step 3: Run predictions
    print("\n" + "="*80)
    print("STEP 3: Running FinBERT Predictions")
    print("="*80)
    
    predict_start = time.time()
    predictions, confidences = predict_batch(df["text"].values, tokenizer, model, device)
    predict_time = time.time() - predict_start
    print(f"\nPrediction time: {predict_time:.2f} seconds")
    
    # Step 4: Calculate metrics
    results = calculate_metrics(df["label"].values, predictions)
    
    # Print results
    print(f"\n--- CALCULATED METRICS ---")
    print(f"Accuracy: {results['accuracy']:.2f}%")
    print(f"Macro Precision: {results['macro_precision']:.2f}%")
    print(f"Macro Recall: {results['macro_recall']:.2f}%")
    print(f"Macro F1: {results['macro_f1']:.2f}%")
    
    print(f"\n--- PER-CLASS METRICS ---")
    for label in GROUND_TRUTH_LABELS:
        metrics = results["per_class"][label]
        print(f"{label.capitalize()}: P={metrics['precision']:.2f}%, R={metrics['recall']:.2f}%, F1={metrics['f1']:.2f}%")
    
    print(f"\n--- CONFUSION MATRIX ---")
    print("Rows: Actual, Columns: Predicted")
    print("Labels: positive, negative, neutral")
    cm = np.array(results["confusion_matrix"])
    print(cm)
    
    # Step 5: Confidence analysis
    conf_analysis = analyze_confidence_distribution(confidences, df["label"].values, predictions)
    
    # Step 6: Compare with expected
    comparisons, all_match = compare_with_expected(results, df)
    
    # Final summary
    total_time = time.time() - start_time
    
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"Total Execution Time: {total_time:.2f} seconds")
    print(f"Model Used: {MODEL_NAME}")
    print(f"Dataset Size: {len(df)} samples")
    print(f"All Values Match FYP Report: {'YES' if all_match else 'NO'}")
    
    # Save results
    output = {
        "verification_timestamp": datetime.now(timezone.utc).isoformat(),
        "model": MODEL_NAME,
        "dataset_path": str(DATASET_PATH),
        "dataset_size": len(df),
        "execution_time_seconds": round(total_time, 2),
        "prediction_time_seconds": round(predict_time, 2),
        "metrics": results,
        "confidence_analysis": conf_analysis,
        "comparison_with_expected": comparisons,
        "all_values_match": all_match
    }
    
    output_path = Path(__file__).parent.parent / "data" / "independent_verification_results.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to: {output_path}")
    
    return output


if __name__ == "__main__":
    results = main()
