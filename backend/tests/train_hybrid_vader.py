"""
Train Hybrid VADER ML Component
================================

Trains the Logistic Regression component of Hybrid VADER on labeled data.

Data Sources (in priority order):
1. Real-world Reddit posts from database with sentiment labels
2. CSV file with labeled data (if --data-path provided)
3. Synthetic sample data (fallback for testing)

Usage:
    python train_hybrid_vader.py [--data-path PATH] [--min-samples N] [--use-db-only]

Arguments:
    --data-path PATH     : Optional CSV file with columns: text, label
    --min-samples N      : Minimum samples required for training (default: 100)
    --use-db-only        : Only use database data, don't supplement with sample data
"""

import asyncio
import argparse
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.service.sentiment_processing.models.hybrid_vader_model import HybridVADERModel, HybridConfig
from app.data_access.database.connection import get_db_session, init_database
from app.data_access.repositories.sentiment_repository import SentimentDataRepository
from app.data_access.models import SentimentData
from sqlalchemy import select


# Sample training data (synthetic examples for demonstration)
# In production, replace with your 1000 labeled Reddit comments from FYP evaluation
SAMPLE_TRAINING_DATA = [
    # Positive examples (label=2)
    ("GME to the moon! Diamond hands forever 🚀💎🙌", 2),
    ("BTFD! This is the way. Strong buy signal", 2),
    ("Bullish breakout confirmed. Squeeze incoming", 2),
    ("Amazing gains today! Portfolio is printing", 2),
    ("Rocket fuel loaded. Next stop: tendies town 🚀", 2),
    ("Diamond hands paying off. Moon mission confirmed", 2),
    ("YOLO calls printing money. Best trade ever", 2),
    ("Apes together strong! Holding to the moon", 2),
    ("Green days ahead. Bullish setup looking great", 2),
    ("Squeeze is squozing! This is it! 🚀📈", 2),
    ("Massive gains incoming. Chart looks perfect", 2),
    ("Bull run confirmed. Loading more calls", 2),
    ("Best setup I've seen in months. Going all in", 2),
    ("Tendies secured! Diamond hands win again", 2),
    ("Lambo money incoming. This stock is amazing", 2),
    ("Strong support at this level. Buying more", 2),
    ("Breakout above resistance. Moon mission activated", 2),
    ("Gamma squeeze potential is huge here", 2),
    ("Bullish news just dropped. Price going up", 2),
    ("Momentum building. This is going to explode", 2),
    
    # Negative examples (label=0)
    ("Market crash incoming. Bloodbath ahead 📉", 0),
    ("Paper hands selling. This is a rug pull", 0),
    ("GUH. Portfolio down 50%. Absolutely rekt", 0),
    ("Dump incoming. Get out while you can", 0),
    ("Bear trap activated. This is going to tank", 0),
    ("Crash imminent. Red days ahead for sure", 0),
    ("Lost everything. This stock is garbage", 0),
    ("Massive selloff coming. Chart looks terrible", 0),
    ("This is a disaster. Should have sold earlier", 0),
    ("Bleeding money every day. Time to cut losses", 0),
    ("Rug pull confirmed. Everyone getting scammed", 0),
    ("Down 80% on this position. Never buying again", 0),
    ("Bear market incoming. Everything is tanking", 0),
    ("Loss porn material. Portfolio completely dead", 0),
    ("Paper hands were right. This is crashing hard", 0),
    ("Bearish breakdown below support. More downside", 0),
    ("Terrible earnings. Stock going to zero", 0),
    ("FUD is real. This company is doomed", 0),
    ("Selling at a huge loss. Cut my losses", 0),
    ("Bagholding this forever. Never recovering", 0),
    
    # Neutral examples (label=1)
    ("Market conditions unclear. Waiting for direction", 1),
    ("Could go either way at this point. Uncertain", 1),
    ("Sideways trading. No clear trend yet", 1),
    ("Need more data before making a decision", 1),
    ("Watching from the sidelines for now", 1),
    ("Mixed signals. Chart is inconclusive", 1),
    ("Not sure about this one. Need to research more", 1),
    ("Flat day. No major movements", 1),
    ("Consolidation phase. Waiting for breakout", 1),
    ("Volume is low. Not much happening today", 1),
    ("Range bound. Support and resistance holding", 1),
    ("Neutral outlook for now. Waiting for catalyst", 1),
    ("No clear direction. Market is indecisive", 1),
    ("Holding steady. No major news", 1),
    ("Wait and see approach. Too early to tell", 1),
    ("Choppy market. Hard to predict movement", 1),
    ("Mixed feelings about this position", 1),
    ("Sideways movement continues. Boring day", 1),
    ("Not seeing any clear signals yet", 1),
    ("Neutral stance. Waiting for confirmation", 1),
]


async def load_database_data():
    """
    Load real-world sentiment data from database.
    
    Extracts Reddit posts with their sentiment labels for training.
    
    Returns:
        List of (text, label) tuples
    """
    print("Loading data from database...")
    
    data = []
    
    # Initialize database connection first
    await init_database()
    
    async with get_db_session() as session:
        # Query all sentiment data from Reddit source with labels
        result = await session.execute(
            select(SentimentData)
            .where(SentimentData.source == 'reddit')
            .where(SentimentData.raw_text.isnot(None))
            .where(SentimentData.sentiment_label.isnot(None))
            .order_by(SentimentData.created_at.desc())
        )
        
        sentiment_records = result.scalars().all()
        
        # Convert to training format
        label_map = {
            'negative': 0,
            'neutral': 1,
            'positive': 2
        }
        
        for record in sentiment_records:
            if record.raw_text and record.sentiment_label:
                label_str = record.sentiment_label.lower()
                if label_str in label_map:
                    text = record.raw_text
                    label = label_map[label_str]
                    data.append((text, label))
        
    print(f"Loaded {len(data)} labeled samples from database")
    
    # Show distribution
    if data:
        from collections import Counter
        labels = [label for _, label in data]
        dist = Counter(labels)
        print(f"  Distribution: Negative={dist[0]}, Neutral={dist[1]}, Positive={dist[2]}")
    
    return data


def load_csv_data(csv_path: str):
    """
    Load training data from CSV file.
    
    Expected format:
    - Column 'text': Text content
    - Column 'label': Integer label (0=negative, 1=neutral, 2=positive)
    
    Args:
        csv_path: Path to CSV file
        
    Returns:
        List of (text, label) tuples
    """
    print(f"Loading data from CSV: {csv_path}")
    
    import pandas as pd
    df = pd.read_csv(csv_path)
    
    if 'text' not in df.columns or 'label' not in df.columns:
        raise ValueError("CSV must have 'text' and 'label' columns")
    
    data = [(row['text'], row['label']) for _, row in df.iterrows()]
    
    print(f"Loaded {len(data)} samples from CSV")
    
    # Show distribution
    from collections import Counter
    labels = [label for _, label in data]
    dist = Counter(labels)
    print(f"  Distribution: Negative={dist[0]}, Neutral={dist[1]}, Positive={dist[2]}")
    
    return data


def get_sample_data():
    """Get synthetic sample data for demonstration/testing."""
    return SAMPLE_TRAINING_DATA


async def load_training_data(data_path: str = None, use_db_only: bool = False, 
                             min_samples: int = 100):
    """
    Load training data from multiple sources.
    
    Priority:
    1. Database data (real-world Reddit posts)
    2. CSV file (if provided)
    3. Sample data (if needed to reach min_samples)
    
    Args:
        data_path: Path to CSV file (optional)
        use_db_only: Only use database data
        min_samples: Minimum samples required
        
    Returns:
        X_train, y_train, X_val, y_val
    """
    all_data = []
    
    # 1. Load from database (highest priority - real data)
    try:
        db_data = await load_database_data()
        if db_data:
            all_data.extend(db_data)
            print(f"[OK] Added {len(db_data)} samples from database")
    except Exception as e:
        print(f"[WARNING] Failed to load database data: {e}")
    
    # 2. Load from CSV if provided
    if data_path and os.path.exists(data_path):
        try:
            csv_data = load_csv_data(data_path)
            if csv_data:
                all_data.extend(csv_data)
                print(f"[OK] Added {len(csv_data)} samples from CSV")
        except Exception as e:
            print(f"[WARNING] Failed to load CSV data: {e}")
    
    # 3. Supplement with sample data if needed (unless use_db_only)
    if not use_db_only and len(all_data) < min_samples:
        sample_data = get_sample_data()
        samples_needed = min_samples - len(all_data)
        all_data.extend(sample_data[:samples_needed])
        print(f"[OK] Added {min(len(sample_data), samples_needed)} sample data points")
    
    # Check if we have enough data
    if len(all_data) < min_samples:
        raise ValueError(
            f"Insufficient training data: {len(all_data)} samples "
            f"(minimum required: {min_samples})\n"
            f"Options:\n"
            f"  1. Run the data collection pipeline to gather more Reddit data\n"
            f"  2. Provide a CSV file with --data-path\n"
            f"  3. Lower --min-samples threshold"
        )
    
    print(f"\nTotal training data: {len(all_data)} samples")
    
    # Split into X, y
    X = [text for text, _ in all_data]
    y = [label for _, label in all_data]
    
    # Show final distribution
    from collections import Counter
    dist = Counter(y)
    print(f"\nFinal Distribution:")
    print(f"  Negative (0): {dist[0]} samples ({dist[0]/len(y)*100:.1f}%)")
    print(f"  Neutral  (1): {dist[1]} samples ({dist[1]/len(y)*100:.1f}%)")
    print(f"  Positive (2): {dist[2]} samples ({dist[2]/len(y)*100:.1f}%)")
    
    # Split 80/20 train/val
    from sklearn.model_selection import train_test_split
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    print(f"\nSplit: {len(X_train)} training, {len(X_val)} validation")
    
    return X_train, y_train, X_val, y_val


async def train_hybrid_model(data_path: str = None, use_db_only: bool = False,
                             min_samples: int = 100):
    """
    Train Hybrid VADER ML component.
    
    Args:
        data_path: Optional path to labeled data CSV
        use_db_only: Only use database data
        min_samples: Minimum samples required for training
    """
    print("\n" + "="*70)
    print("HYBRID VADER TRAINING")
    print("="*70 + "\n")
    
    # Load data
    X_train, y_train, X_val, y_val = await load_training_data(
        data_path, use_db_only, min_samples
    )
    
    # Show class distribution
    from collections import Counter
    train_dist = Counter(y_train)
    val_dist = Counter(y_val)
    
    print("\nTraining Set Distribution:")
    print(f"  Negative (0): {train_dist[0]} samples")
    print(f"  Neutral  (1): {train_dist[1]} samples")
    print(f"  Positive (2): {train_dist[2]} samples")
    
    print("\nValidation Set Distribution:")
    print(f"  Negative (0): {val_dist[0]} samples")
    print(f"  Neutral  (1): {val_dist[1]} samples")
    print(f"  Positive (2): {val_dist[2]} samples")
    
    # Initialize Hybrid VADER
    print("\n" + "-"*70)
    print("Initializing Hybrid VADER model...")
    print("-"*70 + "\n")
    
    config = HybridConfig(
        vader_weight=0.4,
        ml_weight=0.6,
        high_confidence_threshold=0.7,
        vader_high_confidence_weight=0.8,
        max_features=5000
    )
    
    model = HybridVADERModel(config)
    await model.ensure_loaded()
    
    print("\n" + "-"*70)
    print("Training ML component...")
    print("-"*70 + "\n")
    
    # Train (async method)
    results = await model.train_ml_component(X_train, y_train, X_val, y_val)
    
    print("\n" + "="*70)
    print("TRAINING COMPLETE")
    print("="*70)
    
    print(f"\nResults:")
    print(f"  Training accuracy:   {results['train_accuracy']:.4f} ({results['train_accuracy']*100:.2f}%)")
    if results['val_accuracy']:
        print(f"  Validation accuracy: {results['val_accuracy']:.4f} ({results['val_accuracy']*100:.2f}%)")
    print(f"  Number of features:  {results['n_features']}")
    print(f"  Training samples:    {results['n_samples']}")
    
    print("\n" + "-"*70)
    print("Testing on sample texts...")
    print("-"*70 + "\n")
    
    # Test on a few examples (no emojis to avoid Windows terminal encoding issues)
    test_texts = [
        "GME to the moon! Diamond hands forever! Rocket ship engaged",
        "Market crash incoming. Bloodbath ahead. Bearish sentiment everywhere",
        "Uncertain market conditions. Waiting for direction",
    ]
    
    from app.service.sentiment_processing.models.sentiment_model import TextInput, DataSource
    inputs = [TextInput(text, DataSource.REDDIT) for text in test_texts]
    predictions = await model.analyze(inputs)
    
    for text, result in zip(test_texts, predictions):
        # Safely encode text for Windows terminal
        safe_text = text.encode('ascii', errors='replace').decode('ascii')
        print(f"Text: {safe_text}")
        print(f"  Prediction: {result.label.value}")
        print(f"  Score: {result.score:.3f}")
        print(f"  Confidence: {result.confidence:.3f}")
        
        if 'ensemble' in result.raw_scores:
            ensemble = result.raw_scores['ensemble']
            print(f"  Strategy: {ensemble['strategy']}")
            print(f"  VADER: {ensemble['vader_score']:.3f} (weight: {ensemble['weights']['vader']:.2f})")
            print(f"  ML: {ensemble['ml_score']:.3f} (weight: {ensemble['weights']['ml']:.2f})")
        print()
    
    print("="*70)
    print("[SUCCESS] Hybrid VADER trained successfully!")
    print("="*70)
    print("\nModel files saved to:")
    print(f"  - {config.model_path}")
    print(f"  - {config.vectorizer_path}")
    print("\nYou can now use Hybrid VADER in the sentiment engine.")
    print("="*70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Train Hybrid VADER ML component",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Use database + sample data (default)
  python train_hybrid_vader.py
  
  # Use only database data
  python train_hybrid_vader.py --use-db-only
  
  # Use database + CSV data
  python train_hybrid_vader.py --data-path labeled_reddit.csv
  
  # Require at least 500 samples
  python train_hybrid_vader.py --min-samples 500
        """
    )
    parser.add_argument(
        '--data-path',
        type=str,
        default=None,
        help='Path to CSV file with columns: text, label (0=neg, 1=neu, 2=pos)'
    )
    parser.add_argument(
        '--use-db-only',
        action='store_true',
        help='Only use database data, do not supplement with sample data'
    )
    parser.add_argument(
        '--min-samples',
        type=int,
        default=100,
        help='Minimum number of training samples required (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Run training
    asyncio.run(train_hybrid_model(
        data_path=args.data_path,
        use_db_only=args.use_db_only,
        min_samples=args.min_samples
    ))


if __name__ == "__main__":
    main()
