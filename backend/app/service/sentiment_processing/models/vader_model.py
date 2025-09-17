"""
VADER Sentiment Analysis Model
=============================

VADER (Valence Aware Dictionary and sEntiment Reasoner) implementation
for social media sentiment analysis (Reddit, Twitter).

Optimized for informal text with emojis, slang, and social media language.
Following FYP Report specification for social media sentiment analysis.
"""

import time
import re
from typing import List, Dict, Any
import asyncio
import logging

# NLTK imports
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
except ImportError:
    raise ImportError("NLTK is required for VADER sentiment analysis. Install with: pip install nltk")

from .sentiment_model import (
    SentimentModel, 
    SentimentResult, 
    SentimentLabel, 
    ModelInfo, 
    DataSource,
    ModelLoadError,
    AnalysisError
)

logger = logging.getLogger(__name__)


class VADERModel(SentimentModel):
    """
    VADER sentiment analysis model for social media content.
    
    Optimized for:
    - Reddit posts and comments
    - Twitter-like short texts
    - Informal language with emojis and slang
    - Real-time processing requirements
    
    Features:
    - No GPU required (dictionary-based)
    - Fast inference (perfect for real-time)
    - Handles negations, intensifiers, punctuation
    - Emoji-aware sentiment analysis
    """
    
    def __init__(self):
        self.analyzer = None
        self._preprocessor = VADERTextPreprocessor()
        super().__init__()
    
    def _initialize_model_info(self) -> ModelInfo:
        """Initialize VADER model metadata."""
        return ModelInfo(
            name="VADER",
            version="3.3.2",
            description="Dictionary-based sentiment analyzer for social media",
            supported_sources=[
                DataSource.REDDIT,
                DataSource.TWITTER
            ],
            max_batch_size=100,  # Can handle large batches efficiently
            avg_processing_time=5.0  # Very fast processing
        )
    
    async def _load_model(self) -> None:
        """Load VADER analyzer and download required NLTK data."""
        try:
            # Download VADER lexicon if not present
            try:
                nltk.data.find('vader_lexicon')
            except LookupError:
                logger.info("Downloading VADER lexicon...")
                nltk.download('vader_lexicon', quiet=True)
            
            # Initialize analyzer
            self.analyzer = SentimentIntensityAnalyzer()
            
            # Test the analyzer
            test_result = self.analyzer.polarity_scores("test")
            if not isinstance(test_result, dict):
                raise ModelLoadError("VADER analyzer initialization failed")
            
            logger.info("VADER model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load VADER model: {str(e)}")
            raise ModelLoadError(f"VADER model loading failed: {str(e)}")
    
    async def _analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze sentiment for a batch of texts using VADER.
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            List of SentimentResult objects
        """
        if not self.analyzer:
            raise AnalysisError("VADER analyzer not loaded")
        
        results = []
        
        for text in texts:
            start_time = time.time()
            
            try:
                # Preprocess text for better VADER performance
                processed_text = self._preprocessor.preprocess(text)
                
                # Get VADER scores
                vader_scores = self.analyzer.polarity_scores(processed_text)
                
                # Convert to standardized format
                result = self._convert_vader_result(vader_scores, time.time() - start_time)
                results.append(result)
                
            except Exception as e:
                logger.error(f"VADER analysis failed for text: {str(e)}")
                # Return neutral result on error
                results.append(self._create_error_result(time.time() - start_time, str(e)))
        
        return results
    
    def _convert_vader_result(self, vader_scores: Dict[str, float], processing_time: float) -> SentimentResult:
        """
        Convert VADER scores to standardized SentimentResult.
        
        VADER returns:
        - pos: positive score [0.0 to 1.0]
        - neu: neutral score [0.0 to 1.0] 
        - neg: negative score [0.0 to 1.0]
        - compound: normalized compound score [-1.0 to 1.0]
        """
        compound = vader_scores['compound']
        pos_score = vader_scores['pos']
        neu_score = vader_scores['neu']
        neg_score = vader_scores['neg']
        
        # Determine label based on compound score
        if compound >= 0.05:
            label = SentimentLabel.POSITIVE
            confidence = pos_score
        elif compound <= -0.05:
            label = SentimentLabel.NEGATIVE
            confidence = neg_score
        else:
            label = SentimentLabel.NEUTRAL
            confidence = neu_score
        
        return SentimentResult(
            label=label,
            score=compound,  # Already normalized to [-1, 1]
            confidence=confidence,
            raw_scores={
                'compound': compound,
                'positive': pos_score,
                'neutral': neu_score,
                'negative': neg_score
            },
            processing_time=processing_time * 1000,  # Convert to milliseconds
            model_name=self.model_info.name
        )
    
    def _create_error_result(self, processing_time: float, error_msg: str) -> SentimentResult:
        """Create a neutral result when analysis fails."""
        return SentimentResult(
            label=SentimentLabel.NEUTRAL,
            score=0.0,
            confidence=0.0,
            raw_scores={'error': error_msg},
            processing_time=processing_time * 1000,
            model_name=self.model_info.name
        )


class VADERTextPreprocessor:
    """
    Text preprocessor optimized for VADER sentiment analysis.
    
    Handles social media specific text cleaning while preserving
    sentiment-relevant features like punctuation and capitalization.
    """
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        self.multiple_spaces = re.compile(r'\s+')
        self.multiple_punctuation = re.compile(r'([.!?]){3,}')
    
    def preprocess(self, text: str) -> str:
        """
        Preprocess text for VADER analysis.
        
        Preserves sentiment-relevant features while cleaning noise.
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        
        # Remove URLs (usually not sentiment-bearing)
        text = self.url_pattern.sub(' ', text)
        
        # Replace mentions with generic token (preserves structure)
        text = self.mention_pattern.sub(' @user ', text)
        
        # Convert hashtags to regular words (remove #)
        text = self.hashtag_pattern.sub(lambda m: m.group(0)[1:], text)
        
        # Normalize excessive punctuation (preserve emphasis)
        text = self.multiple_punctuation.sub(r'\1\1\1', text)
        
        # Normalize whitespace
        text = self.multiple_spaces.sub(' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        return text
    
    def extract_features(self, text: str) -> Dict[str, Any]:
        """
        Extract additional features that might be useful for analysis.
        
        Args:
            text: Raw text string
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            'length': len(text),
            'word_count': len(text.split()),
            'has_urls': bool(self.url_pattern.search(text)),
            'mention_count': len(self.mention_pattern.findall(text)),
            'hashtag_count': len(self.hashtag_pattern.findall(text)),
            'exclamation_count': text.count('!'),
            'question_count': text.count('?'),
            'caps_ratio': sum(1 for c in text if c.isupper()) / len(text) if text else 0
        }
        
        return features


# Utility functions for VADER-specific operations
def is_vader_available() -> bool:
    """Check if VADER is available and properly installed."""
    try:
        import nltk
        from nltk.sentiment import SentimentIntensityAnalyzer
        
        # Check if lexicon is downloaded
        try:
            nltk.data.find('vader_lexicon')
            return True
        except LookupError:
            return False
            
    except ImportError:
        return False


async def download_vader_data() -> bool:
    """Download VADER lexicon data if not present."""
    try:
        import nltk
        
        # Check if already downloaded
        try:
            nltk.data.find('vader_lexicon')
            return True
        except LookupError:
            pass
        
        # Download the data
        nltk.download('vader_lexicon', quiet=True)
        
        # Verify download
        nltk.data.find('vader_lexicon')
        return True
        
    except Exception as e:
        logger.error(f"Failed to download VADER data: {str(e)}")
        return False


# Example usage and testing
if __name__ == "__main__":
    async def test_vader():
        """Test VADER model with sample texts."""
        model = VADERModel()
        
        from .sentiment_model import TextInput
        
        test_texts = [
            TextInput("I love this stock! 🚀📈", DataSource.REDDIT),
            TextInput("Market is crashing... not good 😞", DataSource.REDDIT),
            TextInput("Neutral market conditions today.", DataSource.REDDIT),
            TextInput("$AAPL to the moon!!! Best investment ever! 💎🙌", DataSource.REDDIT),
            TextInput("Terrible earnings report. Selling everything.", DataSource.REDDIT)
        ]
        
        results = await model.analyze(test_texts)
        
        for i, result in enumerate(results):
            print(f"Text {i+1}: {test_texts[i].text}")
            print(f"  Label: {result.label.value}")
            print(f"  Score: {result.score:.3f}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Time: {result.processing_time:.1f}ms")
            print()
    
    # Run test if executed directly
    asyncio.run(test_vader())