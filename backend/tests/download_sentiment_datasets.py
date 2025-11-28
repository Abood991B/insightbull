"""
Download Large-Scale Sentiment Datasets for Hybrid VADER Training

Downloads publicly available financial and general sentiment datasets from HuggingFace.
Combines them into a unified training CSV format compatible with train_hybrid_vader.py.

Datasets:
1. twitter-financial-news-sentiment (~12K samples) - Financial tweets with sentiment labels
2. tweet_sentiment_extraction (~30K samples) - General tweets with sentiment labels

Total: ~42K labeled samples for training
"""

import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from datasets import load_dataset


def download_twitter_financial_news():
    """
    Download Twitter Financial News Sentiment dataset.
    
    Dataset: zeroshot/twitter-financial-news-sentiment
    Labels: 0=Bearish, 1=Bullish, 2=Neutral
    
    Returns:
        pd.DataFrame with columns [text, label, source]
    """
    print("\n[1/2] Downloading Twitter Financial News Sentiment...")
    print("      Source: HuggingFace - zeroshot/twitter-financial-news-sentiment")
    
    dataset = load_dataset("zeroshot/twitter-financial-news-sentiment")
    
    # Combine train and validation splits
    records = []
    
    label_map = {
        0: "negative",  # Bearish
        1: "positive",  # Bullish  
        2: "neutral"    # Neutral
    }
    
    for split_name, split in dataset.items():
        print(f"      Processing {split_name}: {len(split)} samples")
        for item in split:
            records.append({
                "text": item["text"],
                "label": label_map[item["label"]],
                "source": "twitter_financial"
            })
    
    df = pd.DataFrame(records)
    print(f"      Total: {len(df)} samples")
    print(f"      Distribution: {df['label'].value_counts().to_dict()}")
    
    return df


def download_tweet_sentiment_extraction():
    """
    Download Tweet Sentiment Extraction dataset.
    
    Dataset: mteb/tweet_sentiment_extraction
    Schema: id, text, label (int), label_text (positive/negative/neutral)
    
    Returns:
        pd.DataFrame with columns [text, label, source]
    """
    print("\n[2/2] Downloading Tweet Sentiment Extraction...")
    print("      Source: HuggingFace - mteb/tweet_sentiment_extraction")
    
    dataset = load_dataset("mteb/tweet_sentiment_extraction")
    
    records = []
    
    for split_name, split in dataset.items():
        print(f"      Processing {split_name}: {len(split)} samples")
        for item in split:
            # Skip samples with empty text
            text = str(item.get("text", "")).strip()
            if not text or len(text) < 5:
                continue
            
            # Use label_text field which contains "positive", "negative", "neutral"
            label = str(item.get("label_text", "neutral")).lower()
            
            # Normalize labels
            if label in ["positive", "pos"]:
                label = "positive"
            elif label in ["negative", "neg"]:
                label = "negative"
            else:
                label = "neutral"
                
            records.append({
                "text": text,
                "label": label,
                "source": "tweet_extraction"
            })
    
    df = pd.DataFrame(records)
    print(f"      Total: {len(df)} samples")
    print(f"      Distribution: {df['label'].value_counts().to_dict()}")
    
    return df


def combine_datasets(dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """
    Combine multiple datasets and clean up.
    
    Args:
        dfs: List of DataFrames with [text, label, source] columns
        
    Returns:
        Combined DataFrame with duplicates removed
    """
    print("\n[Combining Datasets]")
    
    combined = pd.concat(dfs, ignore_index=True)
    print(f"  Raw total: {len(combined)} samples")
    
    # Remove duplicates based on text
    combined = combined.drop_duplicates(subset=["text"], keep="first")
    print(f"  After dedup: {len(combined)} samples")
    
    # Remove very short texts (< 10 chars)
    combined = combined[combined["text"].str.len() >= 10]
    print(f"  After length filter: {len(combined)} samples")
    
    # Shuffle
    combined = combined.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"\n  Final Distribution:")
    print(f"    {combined['label'].value_counts().to_dict()}")
    print(f"  By Source:")
    print(f"    {combined['source'].value_counts().to_dict()}")
    
    return combined


def main():
    """Download all datasets and save combined training data."""
    print("=" * 60)
    print("Sentiment Dataset Downloader for Hybrid VADER Training")
    print("=" * 60)
    
    # Create output directory
    output_dir = Path(__file__).parent / "data" / "training"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Download datasets
    datasets = []
    
    try:
        df_financial = download_twitter_financial_news()
        datasets.append(df_financial)
        
        # Save individual dataset
        financial_path = output_dir / "twitter_financial_sentiment.csv"
        df_financial.to_csv(financial_path, index=False)
        print(f"      Saved to: {financial_path}")
    except Exception as e:
        print(f"      ERROR: Failed to download twitter-financial-news: {e}")
    
    try:
        df_tweets = download_tweet_sentiment_extraction()
        datasets.append(df_tweets)
        
        # Save individual dataset
        tweets_path = output_dir / "tweet_sentiment_extraction.csv"
        df_tweets.to_csv(tweets_path, index=False)
        print(f"      Saved to: {tweets_path}")
    except Exception as e:
        print(f"      ERROR: Failed to download tweet_sentiment_extraction: {e}")
    
    if not datasets:
        print("\nERROR: No datasets were downloaded!")
        return 1
    
    # Combine and save
    combined = combine_datasets(datasets)
    
    combined_path = output_dir / "combined_training.csv"
    combined.to_csv(combined_path, index=False)
    
    print("\n" + "=" * 60)
    print("DOWNLOAD COMPLETE")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - {output_dir / 'twitter_financial_sentiment.csv'}")
    print(f"  - {output_dir / 'tweet_sentiment_extraction.csv'}")
    print(f"  - {combined_path}")
    print(f"\nTotal training samples: {len(combined)}")
    print(f"\nNext step: Train Hybrid VADER with:")
    print(f"  python train_hybrid_vader.py --data-path {combined_path}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
