"""
DistilBERT Financial Sentiment Model
===================================

Lightweight ensemble model for confidence voting and disagreement detection.
Uses DistilBERT fine-tuned on financial data (50% smaller than BERT, 60% faster).

Purpose:
- Second opinion for FinBERT predictions
- Disagreement detection (when models disagree → lower confidence)
- Fast ensemble voting without expensive AI calls

Model: mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis
- 82M parameters (vs FinBERT 110M)
- 60% faster inference
- 78-82% accuracy on financial texts
"""

import time
import torch
from typing import List, Dict, Any, Optional
import logging

try:
    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
    import torch.nn.functional as F
except ImportError:
    raise ImportError("Transformers required: pip install transformers torch")

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


class DistilBERTFinancialModel(SentimentModel):
    """
    DistilBERT financial sentiment model for ensemble voting.
    
    Lighter and faster than FinBERT, used as second opinion for:
    - Confidence validation
    - Disagreement detection
    - Ensemble voting
    
    Not meant to replace FinBERT, but complement it.
    """
    
    MODEL_NAME = "mrm8488/distilroberta-finetuned-financial-news-sentiment-analysis"
    
    def __init__(self, use_gpu: bool = None, max_length: int = 512):
        """
        Initialize DistilBERT financial model.
        
        Args:
            use_gpu: Use GPU if available (auto-detect if None)
            max_length: Max sequence length for tokenization
        """
        self.use_gpu = use_gpu if use_gpu is not None else torch.cuda.is_available()
        self.max_length = max_length
        self.device = None
        self.tokenizer = None
        self.model = None
        self.pipeline = None
        super().__init__()
    
    def _initialize_model_info(self) -> ModelInfo:
        """Initialize model metadata."""
        return ModelInfo(
            name="DistilBERT",
            version="1.0.0",
            description="Lightweight ensemble model for confidence voting (82M params, 60% faster)",
            supported_sources=[
                DataSource.FINNHUB,
                DataSource.NEWSAPI,
                DataSource.GDELT,
                DataSource.HACKERNEWS,
                DataSource.YFINANCE
            ],
            max_batch_size=32 if self.use_gpu else 16,  # Faster than FinBERT
            avg_processing_time=80.0 if not self.use_gpu else 30.0
        )
    
    async def _load_model(self) -> None:
        """Load DistilBERT financial model."""
        try:
            logger.info(f"Loading DistilBERT-financial from {self.MODEL_NAME}...")
            
            # Set device
            if self.use_gpu and torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info("Using GPU for DistilBERT-financial")
            else:
                self.device = torch.device("cpu")
                logger.info("Using CPU for DistilBERT-financial")
            
            # Load tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                self.MODEL_NAME,
                use_fast=True
            )
            
            # Load model
            self.model = AutoModelForSequenceClassification.from_pretrained(
                self.MODEL_NAME,
                num_labels=3,
                output_attentions=False,
                output_hidden_states=False
            )
            
            # Move to device
            self.model.to(self.device)
            self.model.eval()
            
            # Create pipeline
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.use_gpu and torch.cuda.is_available() else -1,
                top_k=None,
                truncation=True,
                max_length=self.max_length
            )
            
            # Test model
            test_result = self.pipeline("Stock market shows positive growth.")
            if not test_result:
                raise ModelLoadError("DistilBERT-financial test failed")
            
            logger.info("DistilBERT-financial loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load DistilBERT-financial: {str(e)}")
            raise ModelLoadError(f"DistilBERT-financial loading failed: {str(e)}")
    
    async def _analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze batch of texts using DistilBERT-financial.
        
        Args:
            texts: List of text strings
            
        Returns:
            List of SentimentResult objects
        """
        if not self.pipeline:
            raise AnalysisError("DistilBERT-financial pipeline not loaded")
        
        results = []
        batch_size = self.model_info.max_batch_size
        
        for i in range(0, len(texts), batch_size):
            sub_batch = texts[i:i + batch_size]
            sub_results = await self._process_sub_batch(sub_batch)
            results.extend(sub_results)
        
        return results
    
    async def _process_sub_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Process sub-batch of texts."""
        sub_results = []
        
        for text in texts:
            start_time = time.time()
            
            try:
                # Truncate if too long
                if len(text) > 500:
                    text = text[:500]
                
                # Run inference
                raw_results = self.pipeline(text)
                
                # Convert to standard format
                result = self._convert_distilbert_result(
                    raw_results[0],
                    time.time() - start_time
                )
                sub_results.append(result)
                
            except Exception as e:
                logger.error(f"DistilBERT-financial analysis failed: {str(e)}")
                sub_results.append(self._create_error_result(time.time() - start_time, str(e)))
        
        return sub_results
    
    def _convert_distilbert_result(self, distilbert_scores: List[Dict], processing_time: float) -> SentimentResult:
        """
        Convert DistilBERT scores to standardized format.
        
        Model outputs: [{'label': 'positive', 'score': 0.85}, ...]
        """
        # Create score dictionary
        scores_dict = {item['label'].lower(): item['score'] for item in distilbert_scores}
        
        # Best prediction
        best_prediction = max(distilbert_scores, key=lambda x: x['score'])
        predicted_label = best_prediction['label'].lower()
        confidence = best_prediction['score']
        
        # Map to standard labels
        label_mapping = {
            'positive': SentimentLabel.POSITIVE,
            'negative': SentimentLabel.NEGATIVE,
            'neutral': SentimentLabel.NEUTRAL
        }
        
        label = label_mapping.get(predicted_label, SentimentLabel.NEUTRAL)
        
        # Calculate score [-1 to 1]
        pos_score = scores_dict.get('positive', 0.0)
        neg_score = scores_dict.get('negative', 0.0)
        normalized_score = pos_score - neg_score
        
        return SentimentResult(
            label=label,
            score=normalized_score,
            confidence=confidence,
            raw_scores={
                'positive': pos_score,
                'negative': neg_score,
                'neutral': scores_dict.get('neutral', 0.0),
                'predicted_label': predicted_label
            },
            processing_time=processing_time * 1000,
            model_name=self.model_info.name
        )
    
    def _create_error_result(self, processing_time: float, error_msg: str) -> SentimentResult:
        """Create neutral result on error."""
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
            self.model.to('cpu')
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("DistilBERT-financial resources cleaned up")
