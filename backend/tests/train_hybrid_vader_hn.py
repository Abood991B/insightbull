"""
Hacker News Training Script for Hybrid VADER
=============================================

Collects labeled data from Hacker News and trains the ML component
of the Hybrid VADER model for improved sentiment analysis accuracy.

Training Strategy:
1. Collect recent HN comments mentioning tech stocks
2. Use heuristic labeling based on:
   - Strong price/performance indicators
   - Financial keywords
   - Author context (when available)
3. Train Logistic Regression ensemble
4. Validate on held-out set

Usage:
    python -m tests.train_hybrid_vader_hn

Author: Stock Sentiment Dashboard
"""

import asyncio
import sys
import os
import re
import random
from datetime import datetime, timezone, timedelta
from typing import List, Tuple, Dict, Any
import logging

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Target stocks for training data
TRAINING_STOCKS = [
    'AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN',
    'META', 'TSLA', 'AMD', 'INTC', 'CRM'
]


class HNTrainingDataCollector:
    """Collect and label training data from Hacker News."""
    
    BASE_URL = "https://hn.algolia.com/api/v1"
    
    # Patterns for heuristic labeling
    STRONG_POSITIVE_PATTERNS = [
        r'\b(?:up|gained|rose|jumped|surged|soared|rallied)\s+\d+%',
        r'\b(?:beat|exceeded|crushed)\s+(?:earnings|expectations|estimates)',
        r'\b(?:all.time|record)\s+high',
        r'\b(?:bullish|strong\s+buy|outperform)',
        r'\b(?:great|excellent|amazing)\s+(?:results|quarter|growth)',
        r'\b(?:moon|rocket|tendies|gains)',
        r'\$[A-Z]+\s+(?:is|looks)\s+(?:great|strong|solid)',
    ]
    
    STRONG_NEGATIVE_PATTERNS = [
        r'\b(?:down|fell|dropped|plunged|crashed|tanked)\s+\d+%',
        r'\b(?:missed|disappointed|weak)\s+(?:earnings|expectations|estimates)',
        r'\b(?:all.time|record)\s+low',
        r'\b(?:bearish|sell|underperform|avoid)',
        r'\b(?:terrible|awful|disaster|failed)\s+(?:results|quarter)',
        r'\b(?:crash|dump|bleeding|rekt|loss)',
        r'\$[A-Z]+\s+(?:is|looks)\s+(?:terrible|weak|doomed)',
        r'\bdown\s+\d+%',
        r'\blosing\s+money',
    ]
    
    NEUTRAL_INDICATORS = [
        r'\b(?:flat|unchanged|sideways|stable)',
        r'\b(?:mixed|moderate|fair)',
        r'\b(?:wait|hold|watch)',
        r'\?$',  # Questions tend to be neutral
    ]
    
    def __init__(self):
        self._session = None
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile regex patterns for efficiency."""
        self.pos_patterns = [re.compile(p, re.IGNORECASE) for p in self.STRONG_POSITIVE_PATTERNS]
        self.neg_patterns = [re.compile(p, re.IGNORECASE) for p in self.STRONG_NEGATIVE_PATTERNS]
        self.neu_patterns = [re.compile(p, re.IGNORECASE) for p in self.NEUTRAL_INDICATORS]
    
    async def get_session(self):
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
    
    def label_text(self, text: str) -> Tuple[int, float]:
        """
        Heuristically label text based on patterns.
        
        Returns:
            Tuple of (label, confidence)
            label: 0=negative, 1=neutral, 2=positive
            confidence: 0.0-1.0 confidence in the label
        """
        if not text:
            return 1, 0.3  # Default neutral, low confidence
        
        text_lower = text.lower()
        
        # Check patterns
        pos_matches = sum(1 for p in self.pos_patterns if p.search(text_lower))
        neg_matches = sum(1 for p in self.neg_patterns if p.search(text_lower))
        neu_matches = sum(1 for p in self.neu_patterns if p.search(text_lower))
        
        # Calculate label
        if pos_matches > 0 and neg_matches == 0:
            confidence = min(0.9, 0.5 + 0.15 * pos_matches)
            return 2, confidence
        elif neg_matches > 0 and pos_matches == 0:
            confidence = min(0.9, 0.5 + 0.15 * neg_matches)
            return 0, confidence
        elif pos_matches > neg_matches:
            confidence = min(0.7, 0.4 + 0.1 * (pos_matches - neg_matches))
            return 2, confidence
        elif neg_matches > pos_matches:
            confidence = min(0.7, 0.4 + 0.1 * (neg_matches - pos_matches))
            return 0, confidence
        else:
            # Neutral
            confidence = min(0.6, 0.3 + 0.1 * neu_matches)
            return 1, confidence
    
    async def collect_for_symbol(self, symbol: str, max_items: int = 200) -> List[Dict[str, Any]]:
        """Collect training data for a symbol."""
        session = await self.get_session()
        collected = []
        
        # Search for both stories and comments
        for content_type in ['story', 'comment']:
            query = f'"{symbol}" OR "${symbol}"'
            
            # Get data from last 30 days
            end_ts = int(datetime.now(timezone.utc).timestamp())
            start_ts = end_ts - (30 * 24 * 60 * 60)
            
            params = {
                "query": query,
                "tags": content_type,
                "hitsPerPage": min(max_items, 200),
                "numericFilters": f"created_at_i>{start_ts},created_at_i<{end_ts}"
            }
            
            try:
                async with session.get(f"{self.BASE_URL}/search_by_date", params=params) as response:
                    if response.status != 200:
                        continue
                    
                    data = await response.json()
                    hits = data.get("hits", [])
                    
                    for hit in hits:
                        if content_type == 'story':
                            text = hit.get('title', '')
                            story_text = hit.get('story_text', '')
                            if story_text:
                                text = f"{text}\n{story_text}"
                        else:
                            text = hit.get('comment_text', '')
                            # Clean HTML
                            text = re.sub(r'<[^>]+>', ' ', text)
                        
                        if len(text) < 20:
                            continue
                        
                        # Label the text
                        label, confidence = self.label_text(text)
                        
                        # Only use high-confidence labels for training
                        if confidence >= 0.5:
                            collected.append({
                                'text': text,
                                'label': label,
                                'confidence': confidence,
                                'symbol': symbol,
                                'type': content_type,
                                'hn_id': hit.get('objectID'),
                                'points': hit.get('points', 0) or 0
                            })
                
            except Exception as e:
                logger.warning(f"Error collecting {content_type}s for {symbol}: {e}")
                continue
            
            # Small delay between requests
            await asyncio.sleep(0.2)
        
        return collected


async def collect_training_data() -> Tuple[List[str], List[int]]:
    """Collect training data from HN for all target stocks."""
    collector = HNTrainingDataCollector()
    all_data = []
    
    try:
        logger.info(f"Collecting training data for {len(TRAINING_STOCKS)} stocks...")
        
        for symbol in TRAINING_STOCKS:
            logger.info(f"  Collecting {symbol}...")
            data = await collector.collect_for_symbol(symbol, max_items=100)
            all_data.extend(data)
            logger.info(f"    Got {len(data)} labeled items")
        
        logger.info(f"Total raw data: {len(all_data)} items")
        
        # Balance classes
        by_label = {0: [], 1: [], 2: []}
        for item in all_data:
            by_label[item['label']].append(item)
        
        logger.info(f"  Negative: {len(by_label[0])}")
        logger.info(f"  Neutral: {len(by_label[1])}")
        logger.info(f"  Positive: {len(by_label[2])}")
        
        # Balance by undersampling majority class
        min_count = min(len(by_label[0]), len(by_label[1]), len(by_label[2]))
        min_count = max(min_count, 50)  # At least 50 per class
        
        balanced_data = []
        for label in [0, 1, 2]:
            items = by_label[label]
            # Sort by confidence and take top items
            items.sort(key=lambda x: x['confidence'], reverse=True)
            balanced_data.extend(items[:min_count])
        
        # Shuffle
        random.shuffle(balanced_data)
        
        logger.info(f"Balanced dataset: {len(balanced_data)} items ({min_count} per class)")
        
        texts = [item['text'] for item in balanced_data]
        labels = [item['label'] for item in balanced_data]
        
        return texts, labels
        
    finally:
        await collector.close()


async def train_model(texts: List[str], labels: List[int]):
    """Train the Hybrid VADER ML component."""
    from app.service.sentiment_processing.models.hybrid_vader_model import HybridVADERModel, HybridConfig
    
    # Split into train/val
    split_idx = int(len(texts) * 0.8)
    X_train, X_val = texts[:split_idx], texts[split_idx:]
    y_train, y_val = labels[:split_idx], labels[split_idx:]
    
    logger.info(f"Training set: {len(X_train)} samples")
    logger.info(f"Validation set: {len(X_val)} samples")
    
    # Initialize model
    config = HybridConfig(
        model_path="data/models/hybrid_vader_hn_lr.pkl",
        vectorizer_path="data/models/hybrid_vader_hn_vectorizer.pkl"
    )
    model = HybridVADERModel(config)
    
    # Load VADER component
    await model._load_model()
    
    # Train ML component
    logger.info("Training ML component...")
    result = await model.train_ml_component(X_train, y_train, X_val, y_val)
    
    logger.info("Training complete!")
    logger.info(f"  Train accuracy: {result['train_accuracy']:.4f}")
    if result['val_accuracy']:
        logger.info(f"  Val accuracy: {result['val_accuracy']:.4f}")
    logger.info(f"  Features: {result['n_features']}")
    logger.info(f"  Samples: {result['n_samples']}")
    
    return result


async def test_sarcasm_detection():
    """Test the new sarcasm detection on sample texts."""
    from app.service.sentiment_processing.models.hybrid_vader_model import SarcasmDetector
    
    logger.info("\n" + "="*60)
    logger.info("Testing Sarcasm Detection")
    logger.info("="*60)
    
    detector = SarcasmDetector()
    
    test_cases = [
        # Sarcastic examples (should be detected)
        ("Oh great, another day of watching my portfolio crash", True),
        ("Yeah right, like $TSLA is going to hit $1000 /s", True),
        ("What a 'brilliant' investment strategy - down 40%", True),
        ("Loving my 50% losses, best decision ever", True),
        ("Oh wonderful, another earnings miss", True),
        ("Thanks for nothing, $META management", True),
        ("Sure, $NVDA will definitely crash tomorrow... right", True),
        ("What could possibly go wrong buying at all-time highs", True),
        
        # Non-sarcastic (should NOT be detected)
        ("$AAPL beat earnings expectations by 15%", False),
        ("I think Tesla has strong growth potential", False),
        ("The stock is down 10% after the announcement", False),
        ("Holding long term, not worried about daily moves", False),
        ("Great quarter for Microsoft cloud business", False),
    ]
    
    correct = 0
    for text, expected_sarcastic in test_cases:
        result = detector.detect_sarcasm(text)
        is_correct = result['is_sarcastic'] == expected_sarcastic
        correct += 1 if is_correct else 0
        
        status = "CORRECT" if is_correct else "WRONG"
        logger.info(f"\n{status}: '{text[:50]}...'")
        logger.info(f"  Expected: {'sarcastic' if expected_sarcastic else 'not sarcastic'}")
        logger.info(f"  Detected: {'sarcastic' if result['is_sarcastic'] else 'not sarcastic'} "
                   f"(conf: {result['confidence']:.2f})")
        if result['markers_found']:
            logger.info(f"  Markers: {result['markers_found'][:2]}")
    
    accuracy = correct / len(test_cases)
    logger.info(f"\nSarcasm Detection Accuracy: {accuracy:.1%} ({correct}/{len(test_cases)})")


async def main():
    """Main training pipeline."""
    logger.info("="*60)
    logger.info("Hacker News Training Script for Hybrid VADER")
    logger.info("="*60)
    
    # First, test sarcasm detection
    await test_sarcasm_detection()
    
    # Then, collect and train
    logger.info("\n" + "="*60)
    logger.info("Collecting Training Data from Hacker News")
    logger.info("="*60)
    
    texts, labels = await collect_training_data()
    
    if len(texts) < 50:
        logger.error(f"Not enough training data: {len(texts)} samples")
        logger.info("Try again later when more HN data is available")
        return
    
    logger.info("\n" + "="*60)
    logger.info("Training Hybrid VADER Model")
    logger.info("="*60)
    
    await train_model(texts, labels)
    
    logger.info("\n" + "="*60)
    logger.info("Training Complete!")
    logger.info("="*60)


if __name__ == "__main__":
    asyncio.run(main())
