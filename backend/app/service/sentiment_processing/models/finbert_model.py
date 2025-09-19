"""
FinBERT Sentiment Analysis Model
===============================

FinBERT (Financial BERT) implementation for financial news sentiment analysis.
Uses the ProsusAI/finbert pre-trained model specialized for financial domain.

Optimized for:
- Financial news articles
- Company announcements
- Market reports
- Professional financial content

Following FYP Report specification for financial news sentiment analysis.
"""

import time
import re
import torch
from typing import List, Dict, Any, Optional
import asyncio
import logging

# Transformers imports
try:
    from transformers import (
        AutoTokenizer, 
        AutoModelForSequenceClassification,
        pipeline
    )
except ImportError:
    raise ImportError("Transformers is required for FinBERT. Install with: pip install transformers torch")

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


class FinBERTModel(SentimentModel):
    """
    FinBERT sentiment analysis model for financial content.
    
    Specialized for:
    - Financial news articles
    - Company announcements  
    - Market analysis reports
    - Professional financial content
    
    Features:
    - Domain-specific pre-training on financial texts
    - High accuracy on financial sentiment
    - GPU acceleration support
    - Batch processing optimization
    """
    
    MODEL_NAME = "ProsusAI/finbert"
    
    def __init__(self, use_gpu: bool = None, max_length: int = 512):
        """
        Initialize FinBERT model.
        
        Args:
            use_gpu: Whether to use GPU acceleration (auto-detect if None)
            max_length: Maximum sequence length for tokenization
        """
        self.use_gpu = use_gpu if use_gpu is not None else torch.cuda.is_available()
        self.max_length = max_length
        self.device = None
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        self._preprocessor = FinancialTextPreprocessor()
        super().__init__()
    
    def _initialize_model_info(self) -> ModelInfo:
        """Initialize FinBERT model metadata."""
        return ModelInfo(
            name="FinBERT",
            version="1.0.0",
            description="BERT-based sentiment analyzer for financial content",
            supported_sources=[
                DataSource.FINNHUB,   # Financial news sources -> FinBERT
                DataSource.MARKETAUX,
                DataSource.NEWSAPI
            ],
            max_batch_size=16 if self.use_gpu else 8,  # Smaller batches for GPU memory
            avg_processing_time=150.0 if not self.use_gpu else 50.0  # CPU vs GPU timing
        )
    
    async def _load_model(self) -> None:
        """Load FinBERT model and tokenizer."""
        try:
            logger.info(f"Loading FinBERT model from {self.MODEL_NAME}...")
            
            # Set device
            if self.use_gpu and torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info("Using GPU for FinBERT inference")
            else:
                self.device = torch.device("cpu")
                logger.info("Using CPU for FinBERT inference")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                use_fast=True
            )
            
            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME,
                num_labels=3,  # positive, negative, neutral
                output_attentions=False,
                output_hidden_states=False
            )
            
            # Move model to device
            self.model.to(self.device)
            self.model.eval()  # Set to evaluation mode
            
            # Create pipeline for easier inference
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.use_gpu and torch.cuda.is_available() else -1,
                top_k=None,  # Return all scores (replaces deprecated return_all_scores=True)
                truncation=True,
                max_length=self.max_length
            )
            
            # Test the model
            test_result = self.pipeline("The company reported strong quarterly earnings.")
            if not test_result:
                raise ModelLoadError("FinBERT model test failed")
            
            logger.info("FinBERT model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load FinBERT model: {str(e)}")
            raise ModelLoadError(f"FinBERT model loading failed: {str(e)}")
    
    async def _analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze sentiment for a batch of texts using FinBERT.
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            List of SentimentResult objects
        """
        if not self.pipeline:
            raise AnalysisError("FinBERT pipeline not loaded")
        
        results = []
        
        # Process texts in smaller sub-batches to manage memory
        batch_size = self.model_info.max_batch_size
        
        for i in range(0, len(texts), batch_size):
            sub_batch = texts[i:i + batch_size]
            sub_results = await self._process_sub_batch(sub_batch)
            results.extend(sub_results)
        
        return results
    
    async def _process_sub_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Process a sub-batch of texts."""
        sub_results = []
        
        for text in texts:
            start_time = time.time()
            
            try:
                # Preprocess text for better FinBERT performance
                processed_text = self._preprocessor.preprocess(text)
                
                # Run inference
                raw_results = self.pipeline(processed_text)
                
                # Convert to standardized format
                result = self._convert_finbert_result(
                    raw_results[0], 
                    time.time() - start_time
                )
                sub_results.append(result)
                
            except Exception as e:
                logger.error(f"FinBERT analysis failed for text: {str(e)}")
                # Return neutral result on error
                sub_results.append(self._create_error_result(time.time() - start_time, str(e)))
        
        return sub_results
    
    def _convert_finbert_result(self, finbert_scores: List[Dict], processing_time: float) -> SentimentResult:
        """
        Convert FinBERT scores to standardized SentimentResult.
        
        FinBERT returns list of scores for each label:
        [{'label': 'positive', 'score': 0.8}, {'label': 'negative', 'score': 0.1}, {'label': 'neutral', 'score': 0.1}]
        """
        # Create score dictionary
        scores_dict = {item['label'].lower(): item['score'] for item in finbert_scores}
        
        # Find the label with highest confidence
        best_prediction = max(finbert_scores, key=lambda x: x['score'])
        predicted_label = best_prediction['label'].lower()
        confidence = best_prediction['score']
        
        # Map FinBERT labels to our standard labels
        label_mapping = {
            'positive': SentimentLabel.POSITIVE,
            'negative': SentimentLabel.NEGATIVE, 
            'neutral': SentimentLabel.NEUTRAL
        }
        
        label = label_mapping.get(predicted_label, SentimentLabel.NEUTRAL)
        
        # Calculate normalized score [-1 to 1]
        pos_score = scores_dict.get('positive', 0.0)
        neg_score = scores_dict.get('negative', 0.0)
        neu_score = scores_dict.get('neutral', 0.0)
        
        # Normalize to [-1, 1] range
        normalized_score = pos_score - neg_score
        
        return SentimentResult(
            label=label,
            score=normalized_score,
            confidence=confidence,
            raw_scores={
                'positive': pos_score,
                'negative': neg_score,
                'neutral': neu_score,
                'predicted_label': predicted_label
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
    
    async def cleanup(self) -> None:
        """Clean up model resources."""
        if self.model is not None:
            # Move model to CPU to free GPU memory
            self.model.to('cpu')
            
        # Clear CUDA cache if using GPU
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("FinBERT model resources cleaned up")


class FinancialTextPreprocessor:
    """
    Text preprocessor optimized for financial content and FinBERT.
    
    Handles financial text specific cleaning while preserving
    domain-relevant information like tickers, financial terms, and numbers.
    """
    
    def __init__(self):
        # Compile regex patterns for efficiency
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.ticker_pattern = re.compile(r'\$[A-Z]{1,5}\b')  # Stock tickers like $AAPL
        self.multiple_spaces = re.compile(r'\s+')
        self.html_pattern = re.compile(r'<[^>]+>')
        
        # Financial-specific patterns to preserve
        self.currency_pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?')
        self.percentage_pattern = re.compile(r'\d+(?:\.\d+)?%')
        self.date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
    
    def preprocess(self, text: str) -> str:
        """
        Preprocess financial text for FinBERT analysis.
        
        Preserves financial-relevant information while cleaning noise.
        
        Args:
            text: Raw text string
            
        Returns:
            Cleaned text string optimized for FinBERT
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = self.html_pattern.sub(' ', text)
        
        # Remove URLs (usually not sentiment-bearing in financial context)
        text = self.url_pattern.sub(' ', text)
        
        # Remove email addresses
        text = self.email_pattern.sub(' ', text)
        
        # Preserve stock tickers (important for financial sentiment)
        # No modification needed - FinBERT should understand these
        
        # Normalize excessive whitespace
        text = self.multiple_spaces.sub(' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Ensure text isn't too long for BERT
        if len(text) > 2000:  # Conservative limit
            text = text[:2000]
            # Try to end at a sentence boundary
            last_period = text.rfind('.')
            if last_period > 1500:  # Don't cut too much
                text = text[:last_period + 1]
        
        return text
    
    def extract_financial_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract financial entities from text.
        
        Args:
            text: Raw text string
            
        Returns:
            Dictionary of extracted financial entities
        """
        entities = {
            'tickers': self.ticker_pattern.findall(text),
            'currencies': self.currency_pattern.findall(text),
            'percentages': self.percentage_pattern.findall(text),
            'dates': self.date_pattern.findall(text)
        }
        
        return entities


# Utility functions for FinBERT-specific operations
def is_finbert_available() -> bool:
    """Check if FinBERT dependencies are available."""
    try:
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        import torch
        return True
    except ImportError:
        return False


def get_device_info() -> Dict[str, Any]:
    """Get information about available compute devices."""
    info = {
        'torch_available': False,
        'cuda_available': False,
        'cuda_device_count': 0,
        'recommended_batch_size': 4
    }
    
    try:
        import torch
        info['torch_available'] = True
        info['cuda_available'] = torch.cuda.is_available()
        
        if torch.cuda.is_available():
            info['cuda_device_count'] = torch.cuda.device_count()
            info['cuda_device_name'] = torch.cuda.get_device_name(0)
            info['recommended_batch_size'] = 16
        else:
            info['recommended_batch_size'] = 8
            
    except ImportError:
        pass
    
    return info


# Example usage and testing
if __name__ == "__main__":
    async def test_finbert():
        """Test FinBERT model with sample financial texts."""
        if not is_finbert_available():
            print("FinBERT dependencies not available. Install with: pip install transformers torch")
            return
        
        model = FinBERTModel()
        
        from .sentiment_model import TextInput
        
        test_texts = [
            TextInput("Apple Inc. reported record quarterly earnings beating all analyst expectations.", DataSource.NEWS),
            TextInput("The company faces significant headwinds due to supply chain disruptions.", DataSource.NEWS),
            TextInput("Market conditions remain stable with moderate growth expected.", DataSource.NEWS),
            TextInput("Tesla stock surged after announcing breakthrough in battery technology.", DataSource.FINNHUB),
            TextInput("Banking sector struggles amid rising interest rates and regulatory pressure.", DataSource.MARKETAUX)
        ]
        
        print("Testing FinBERT model...")
        print(f"Device info: {get_device_info()}")
        print()
        
        results = await model.analyze(test_texts)
        
        for i, result in enumerate(results):
            print(f"Text {i+1}: {test_texts[i].text}")
            print(f"  Label: {result.label.value}")
            print(f"  Score: {result.score:.3f}")
            print(f"  Confidence: {result.confidence:.3f}")
            print(f"  Time: {result.processing_time:.1f}ms")
            print()
        
        # Cleanup
        await model.cleanup()
    
    # Run test if executed directly
    asyncio.run(test_finbert())