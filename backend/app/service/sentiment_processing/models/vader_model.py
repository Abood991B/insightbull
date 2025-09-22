"""
Enhanced VADER Sentiment Analysis Model
========================================

VADER (Valence Aware Dictionary and sEntiment Reasoner) implementation
for social media sentiment analysis with financial domain expertise.

Enhanced Features:
- Financial lexicon expansion with bullish/bearish terms
- Reddit slang and abbreviation handling
- Advanced preprocessing with emoji sentiment
- Dynamic threshold tuning for better accuracy
- Context-aware sentiment analysis
- Confidence score boosting

Optimized for informal text with emojis, slang, and social media language.
Following FYP Report specification for social media sentiment analysis.
"""

import time
import re
from typing import List, Dict, Any, Tuple, Optional
import asyncio
import logging
from dataclasses import dataclass
from collections import defaultdict

# NLTK imports
try:
    import nltk
    from nltk.sentiment import SentimentIntensityAnalyzer
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as VaderSIA
except ImportError:
    raise ImportError("NLTK and vaderSentiment are required. Install with: pip install nltk vaderSentiment")

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


@dataclass
class EnhancementConfig:
    """Configuration for VADER enhancements."""
    use_financial_lexicon: bool = True
    use_reddit_slang: bool = True
    use_emoji_boost: bool = True
    use_dynamic_thresholds: bool = True
    use_context_awareness: bool = True
    positive_threshold: float = 0.05
    negative_threshold: float = -0.05
    confidence_boost_factor: float = 1.2


class FinancialLexicon:
    """Financial domain-specific sentiment lexicon."""
    
    BULLISH_TERMS = {
        # Strong bullish terms
        'moon': 3.0, 'mooning': 3.0, 'squeeze': 2.5, 'gamma': 2.0,
        'bullish': 2.5, 'bull': 2.0, 'rally': 2.0, 'breakout': 2.0,
        'pump': 2.0, 'soar': 2.5, 'surge': 2.5, 'rocket': 3.0,
        'tendies': 2.5, 'gains': 2.0, 'profit': 2.0, 'green': 1.5,
        'calls': 1.5, 'long': 1.5, 'buy': 1.5, 'accumulate': 2.0,
        'undervalued': 2.0, 'oversold': 1.5, 'support': 1.0,
        'uptrend': 2.0, 'momentum': 1.5, 'growth': 1.5,
        
        # Reddit-specific bullish
        'yolo': 2.0, 'diamond hands': 3.0, 'hodl': 2.5, 'apes': 2.0,
        'to the moon': 3.5, 'printing': 2.5, 'brrr': 2.0,
        'lambo': 2.5, 'tendie': 2.5, 'stonks': 2.0,
    }
    
    BEARISH_TERMS = {
        # Strong bearish terms
        'crash': -3.0, 'dump': -2.5, 'tank': -2.5, 'plunge': -2.5,
        'bearish': -2.5, 'bear': -2.0, 'selloff': -2.0, 'collapse': -3.0,
        'bloodbath': -3.0, 'red': -1.5, 'puts': -1.5, 'short': -1.5,
        'sell': -1.5, 'overvalued': -2.0, 'overbought': -1.5,
        'resistance': -1.0, 'downtrend': -2.0, 'correction': -1.5,
        'bubble': -2.0, 'bag': -2.0, 'bagholder': -2.5, 'bagholding': -2.5,
        
        # Reddit-specific bearish
        'guh': -3.0, 'loss porn': -2.5, 'paper hands': -2.0,
        'rug pull': -3.0, 'bleeding': -2.5, 'rekt': -3.0,
        'heavy bags': -2.5, 'catching knives': -2.5,
    }
    
    NEUTRAL_MODIFIERS = {
        'maybe': 0.5, 'possibly': 0.5, 'might': 0.5,
        'could': 0.3, 'should': 0.3, 'would': 0.3,
        'if': 0.2, 'but': -0.3, 'however': -0.3,
    }


class RedditSlangProcessor:
    """Processor for Reddit-specific slang and abbreviations."""
    
    SLANG_MAPPINGS = {
        # Common abbreviations
        'btfd': 'buy the fucking dip',
        'btd': 'buy the dip',
        'dd': 'due diligence',
        'fomo': 'fear of missing out',
        'fud': 'fear uncertainty doubt',
        'imo': 'in my opinion',
        'imho': 'in my humble opinion',
        'tbh': 'to be honest',
        'nfa': 'not financial advice',
        'dyor': 'do your own research',
        'ath': 'all time high',
        'atl': 'all time low',
        'idk': 'i dont know',
        'iirc': 'if i recall correctly',
        
        # Stock-specific
        'gme': 'gamestop',
        'amc': 'amc entertainment',
        'bb': 'blackberry',
        'pltr': 'palantir',
        'tsla': 'tesla',
        'spy': 'sp500',
        'qqq': 'nasdaq',
        
        # Trading terms
        'fd': 'weekly options',
        'iv': 'implied volatility',
        'otm': 'out of the money',
        'itm': 'in the money',
        'dte': 'days to expiration',
        'cc': 'covered call',
        'csp': 'cash secured put',
        
        # Wsb specific
        'wsb': 'wallstreetbets',
        'guh': 'major loss',
        'brr': 'money printer',
        'jpow': 'jerome powell',
        'papa': 'elon musk',
    }
    
    EMOJI_SENTIMENTS = {
        # Positive emojis
        '🚀': 3.0, '📈': 2.5, '💎': 2.5, '🙌': 2.0,
        '🔥': 2.0, '💰': 2.0, '🤑': 2.5, '😍': 2.0,
        '🎯': 1.5, '✅': 1.5, '👍': 1.5, '💪': 2.0,
        '🌙': 2.5, '⬆️': 1.5, '📊': 1.0, '🏆': 2.0,
        
        # Negative emojis
        '📉': -2.5, '💩': -2.0, '🤮': -2.5, '😭': -2.0,
        '🔴': -1.5, '⬇️': -1.5, '🐻': -2.0, '💔': -2.0,
        '😱': -1.5, '😰': -1.5, '🤯': -1.0, '❌': -2.0,
        '🩸': -2.5, '☠️': -3.0, '⚠️': -1.0,
    }
    
    def process_slang(self, text: str) -> str:
        """Replace slang with full terms."""
        text_lower = text.lower()
        for slang, expansion in self.SLANG_MAPPINGS.items():
            # Use word boundaries to avoid partial matches
            pattern = r'\b' + re.escape(slang) + r'\b'
            text_lower = re.sub(pattern, expansion, text_lower, flags=re.IGNORECASE)
        return text_lower
    
    def extract_emoji_sentiment(self, text: str) -> float:
        """Calculate sentiment boost from emojis."""
        emoji_score = 0.0
        emoji_count = 0
        
        for emoji, score in self.EMOJI_SENTIMENTS.items():
            count = text.count(emoji)
            if count > 0:
                emoji_score += score * count
                emoji_count += count
        
        # Normalize by emoji count to avoid over-weighting
        if emoji_count > 0:
            return emoji_score / emoji_count * 0.3  # Scale down to avoid dominating
        return 0.0


class VADERModel(SentimentModel):
    """
    Enhanced VADER sentiment analysis model for social media content.
    
    Optimized for:
    - Reddit posts and comments with financial context
    - Twitter-like short texts with trading slang
    - Informal language with emojis and financial slang
    - Real-time processing requirements
    
    Enhanced Features:
    - Financial lexicon integration (bullish/bearish terms)
    - Reddit slang and abbreviation processing
    - Emoji sentiment boosting
    - Dynamic threshold adjustment
    - Context-aware analysis
    - No GPU required (dictionary-based)
    - Fast inference (perfect for real-time)
    """
    
    def __init__(self, config: Optional[EnhancementConfig] = None):
        self.config = config or EnhancementConfig()
        self.analyzer = None
        self.financial_lexicon = FinancialLexicon()
        self.slang_processor = RedditSlangProcessor()
        self._preprocessor = EnhancedVADERPreprocessor(self.slang_processor)
        
        # Custom lexicon updates
        self.custom_lexicon = {}
        self._build_custom_lexicon()
        
        super().__init__()
    
    def _build_custom_lexicon(self):
        """Build custom lexicon from financial terms."""
        if self.config.use_financial_lexicon:
            self.custom_lexicon.update(self.financial_lexicon.BULLISH_TERMS)
            self.custom_lexicon.update(self.financial_lexicon.BEARISH_TERMS)
            self.custom_lexicon.update(self.financial_lexicon.NEUTRAL_MODIFIERS)
    
    def _initialize_model_info(self) -> ModelInfo:
        """Initialize enhanced VADER model metadata."""
        return ModelInfo(
            name="VADER",  # Keep same name for database compatibility
            version="1.0.0-enhanced",
            description="VADER with financial domain expertise and Reddit optimizations",
            supported_sources=[
                DataSource.REDDIT  # Still focused on social media
            ],
            max_batch_size=100,
            avg_processing_time=7.0  # Slightly slower due to enhancements
        )
    
    async def _load_model(self) -> None:
        """Load enhanced VADER analyzer with custom lexicon."""
        try:
            # Download VADER lexicon if not present
            try:
                nltk.data.find('vader_lexicon')
            except LookupError:
                logger.info("Downloading VADER lexicon...")
                nltk.download('vader_lexicon', quiet=True)
            
            # Initialize analyzer with vaderSentiment for better customization
            self.analyzer = VaderSIA()
            
            # Update lexicon with custom terms
            if self.custom_lexicon:
                self.analyzer.lexicon.update(self.custom_lexicon)
                logger.info(f"Added {len(self.custom_lexicon)} custom terms to VADER lexicon")
            
            # Test the analyzer
            test_result = self.analyzer.polarity_scores("test")
            if not isinstance(test_result, dict):
                raise ModelLoadError("Enhanced VADER analyzer initialization failed")
            
            logger.info("Enhanced VADER model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load Enhanced VADER model: {str(e)}")
            raise ModelLoadError(f"Enhanced VADER model loading failed: {str(e)}")
    
    async def _analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze sentiment with enhancements.
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            List of enhanced SentimentResult objects
        """
        if not self.analyzer:
            raise AnalysisError("Enhanced VADER analyzer not loaded")
        
        results = []
        
        for text in texts:
            start_time = time.time()
            
            try:
                # Apply enhanced preprocessing
                processed_text, metadata = self._preprocessor.preprocess_with_metadata(text)
                
                # Get emoji sentiment if enabled
                emoji_boost = 0.0
                if self.config.use_emoji_boost:
                    emoji_boost = self.slang_processor.extract_emoji_sentiment(text)
                
                # Get VADER scores
                vader_scores = self.analyzer.polarity_scores(processed_text)
                
                # Apply emoji boost to compound score
                if emoji_boost != 0:
                    vader_scores['compound'] = self._apply_boost(
                        vader_scores['compound'], 
                        emoji_boost
                    )
                
                # Apply context-aware adjustments
                if self.config.use_context_awareness:
                    vader_scores = self._apply_context_adjustments(
                        vader_scores, 
                        metadata
                    )
                
                # Convert to result with dynamic thresholds
                result = self._convert_enhanced_result(
                    vader_scores, 
                    metadata,
                    time.time() - start_time
                )
                results.append(result)
                
            except Exception as e:
                logger.error(f"Enhanced VADER analysis failed: {str(e)}")
                results.append(self._create_error_result(time.time() - start_time, str(e)))
        
        return results
    
    def _apply_boost(self, base_score: float, boost: float) -> float:
        """Apply sentiment boost while keeping score in [-1, 1] range."""
        boosted = base_score + boost
        # Clamp to valid range
        return max(-1.0, min(1.0, boosted))
    
    def _apply_context_adjustments(
        self, 
        scores: Dict[str, float], 
        metadata: Dict[str, Any]
    ) -> Dict[str, float]:
        """Apply context-based score adjustments."""
        adjusted_scores = scores.copy()
        
        # Boost confidence for texts with strong signals
        if metadata.get('has_strong_signal', False):
            factor = self.config.confidence_boost_factor
            if adjusted_scores['compound'] > 0:
                adjusted_scores['pos'] *= factor
            elif adjusted_scores['compound'] < 0:
                adjusted_scores['neg'] *= factor
        
        # Reduce neutral tendency for texts with clear sentiment indicators
        if metadata.get('sentiment_indicators', 0) > 2:
            adjusted_scores['neu'] *= 0.8
            
        # Re-normalize scores
        total = adjusted_scores['pos'] + adjusted_scores['neu'] + adjusted_scores['neg']
        if total > 0:
            adjusted_scores['pos'] /= total
            adjusted_scores['neu'] /= total
            adjusted_scores['neg'] /= total
        
        return adjusted_scores
    
    def _convert_enhanced_result(
        self, 
        vader_scores: Dict[str, float], 
        metadata: Dict[str, Any],
        processing_time: float
    ) -> SentimentResult:
        """
        Convert VADER scores to enhanced SentimentResult with dynamic thresholds.
        """
        compound = vader_scores['compound']
        pos_score = vader_scores['pos']
        neu_score = vader_scores['neu']
        neg_score = vader_scores['neg']
        
        # Dynamic threshold adjustment based on metadata
        pos_threshold = self.config.positive_threshold
        neg_threshold = self.config.negative_threshold
        
        if self.config.use_dynamic_thresholds:
            # Adjust thresholds based on text characteristics
            if metadata.get('word_count', 0) < 10:
                # Short texts need stronger signals
                pos_threshold *= 1.5
                neg_threshold *= 1.5
            elif metadata.get('word_count', 0) > 50:
                # Longer texts can have more nuanced sentiment
                pos_threshold *= 0.8
                neg_threshold *= 0.8
        
        # Determine label with enhanced logic
        if compound >= pos_threshold:
            label = SentimentLabel.POSITIVE
            # Boost confidence if we have supporting indicators
            confidence = pos_score
            if metadata.get('positive_indicators', 0) > 0:
                confidence = min(1.0, confidence * 1.2)
        elif compound <= neg_threshold:
            label = SentimentLabel.NEGATIVE
            confidence = neg_score
            if metadata.get('negative_indicators', 0) > 0:
                confidence = min(1.0, confidence * 1.2)
        else:
            label = SentimentLabel.NEUTRAL
            confidence = neu_score
        
        return SentimentResult(
            label=label,
            score=compound,
            confidence=confidence,
            raw_scores={
                'compound': compound,
                'positive': pos_score,
                'neutral': neu_score,
                'negative': neg_score,
                'enhancements': {
                    'emoji_sentiment': metadata.get('emoji_sentiment', 0),
                    'financial_terms': metadata.get('financial_terms', 0),
                    'reddit_slang': metadata.get('reddit_slang', 0),
                }
            },
            processing_time=processing_time * 1000,
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


class EnhancedVADERPreprocessor:
    """
    Advanced text preprocessor for enhanced VADER analysis.
    """
    
    def __init__(self, slang_processor: RedditSlangProcessor):
        self.slang_processor = slang_processor
        
        # Compile regex patterns
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.mention_pattern = re.compile(r'@\w+')
        self.hashtag_pattern = re.compile(r'#(\w+)')
        self.ticker_pattern = re.compile(r'\$([A-Z]{1,5})\b')
        self.multiple_spaces = re.compile(r'\s+')
        self.repeated_chars = re.compile(r'(.)\1{3,}')
        
        # Financial indicators
        self.bullish_indicators = set(FinancialLexicon.BULLISH_TERMS.keys())
        self.bearish_indicators = set(FinancialLexicon.BEARISH_TERMS.keys())
    
    def preprocess_with_metadata(self, text: str) -> Tuple[str, Dict[str, Any]]:
        """
        Enhanced preprocessing with metadata extraction.
        
        Returns:
            Tuple of (processed_text, metadata_dict)
        """
        if not text:
            return "", {}
        
        metadata = {
            'original_length': len(text),
            'word_count': len(text.split()),
        }
        
        # Extract tickers before processing
        tickers = self.ticker_pattern.findall(text)
        metadata['tickers'] = tickers
        metadata['ticker_count'] = len(tickers)
        
        # Process Reddit slang
        text = self.slang_processor.process_slang(text)
        metadata['reddit_slang'] = len([
            word for word in text.lower().split() 
            if word in self.slang_processor.SLANG_MAPPINGS
        ])
        
        # Extract emoji sentiment
        metadata['emoji_sentiment'] = self.slang_processor.extract_emoji_sentiment(text)
        
        # Remove URLs
        text = self.url_pattern.sub(' LINK ', text)
        
        # Process mentions
        text = self.mention_pattern.sub(' USER ', text)
        
        # Process hashtags (keep the word)
        text = self.hashtag_pattern.sub(r'\1', text)
        
        # Normalize repeated characters (keep max 2)
        text = self.repeated_chars.sub(r'\1\1', text)
        
        # Count sentiment indicators
        text_lower = text.lower()
        metadata['positive_indicators'] = sum(
            1 for word in self.bullish_indicators 
            if word in text_lower
        )
        metadata['negative_indicators'] = sum(
            1 for word in self.bearish_indicators 
            if word in text_lower
        )
        metadata['sentiment_indicators'] = (
            metadata['positive_indicators'] + 
            metadata['negative_indicators']
        )
        
        # Strong signal detection
        metadata['has_strong_signal'] = (
            metadata['sentiment_indicators'] > 3 or
            abs(metadata['emoji_sentiment']) > 1.5 or
            any(word in text_lower for word in ['moon', 'crash', 'squeeze', 'dump'])
        )
        
        # Financial term count
        all_financial = self.bullish_indicators | self.bearish_indicators
        metadata['financial_terms'] = sum(
            1 for word in all_financial 
            if word in text_lower
        )
        
        # Normalize whitespace
        text = self.multiple_spaces.sub(' ', text)
        text = text.strip()
        
        return text, metadata
    
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
    async def test_enhanced_vader():
        """Test enhanced VADER with sample texts."""
        config = EnhancementConfig(
            use_financial_lexicon=True,
            use_reddit_slang=True,
            use_emoji_boost=True,
            use_dynamic_thresholds=True,
            use_context_awareness=True
        )
        model = VADERModel(config)
        await model.ensure_loaded()
        
        from .sentiment_model import TextInput
        
        test_texts = [
            TextInput("$GME to the moon! 🚀🚀🚀 Diamond hands forever! 💎🙌", DataSource.REDDIT),
            TextInput("Market crash incoming... This is going to be a bloodbath 😭📉", DataSource.REDDIT),
            TextInput("BTFD! This dip is a gift. Bullish AF on $TSLA", DataSource.REDDIT),
            TextInput("Bag holding $PLTR, down 40% but still hodling", DataSource.REDDIT),
            TextInput("DD: Strong support at 150, oversold RSI, squeeze incoming", DataSource.REDDIT),
            TextInput("Neutral market conditions, waiting for direction", DataSource.REDDIT),
        ]
        
        results = await model.analyze(test_texts)
        
        print("Enhanced VADER Analysis Results:")
        print("-" * 50)
        for i, result in enumerate(results):
            print(f"\nText {i+1}: {test_texts[i].text}")
            print(f"  Label: {result.label.value}")
            print(f"  Score: {result.score:.3f}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Enhancements: {result.raw_scores.get('enhancements', {})}")
            print(f"  Time: {result.processing_time:.1f}ms")
    
    # Run test
    asyncio.run(test_enhanced_vader())