"""
Sentiment analysis service using FinBERT and VADER
"""
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update

from app.core.database import AsyncSessionLocal
from app.models import SentimentData, SystemLog
from config import settings

logger = logging.getLogger(__name__)


class SentimentAnalyzer:
    """Service for analyzing sentiment of collected text data"""
    
    def __init__(self):
        self.finbert_tokenizer = None
        self.finbert_model = None
        self.vader_analyzer = None
        self.session = None
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize sentiment analysis models"""
        try:
            # Initialize FinBERT for financial news
            logger.info("Loading FinBERT model...")
            self.finbert_tokenizer = AutoTokenizer.from_pretrained(settings.FINBERT_MODEL)
            self.finbert_model = AutoModelForSequenceClassification.from_pretrained(settings.FINBERT_MODEL)
            
            # Initialize VADER for social media
            logger.info("Loading VADER analyzer...")
            self.vader_analyzer = SentimentIntensityAnalyzer()
            
            logger.info("Sentiment models initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize sentiment models: {e}")
            raise
    
    async def __aenter__(self):
        self.session = AsyncSessionLocal()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def process_pending(self):
        """Process all pending sentiment analysis"""
        try:
            # Get unprocessed sentiment data
            result = await self.session.execute(
                select(SentimentData).where(
                    SentimentData.sentiment_score == 0
                ).limit(100)  # Process in batches
            )
            pending = result.scalars().all()
            
            if not pending:
                logger.info("No pending sentiment data to process")
                return
            
            logger.info(f"Processing {len(pending)} pending sentiment analyses")
            
            # Process each item
            for item in pending:
                try:
                    if item.source == "reddit":
                        # Use VADER for Reddit posts
                        sentiment = self._analyze_with_vader(item.content)
                    else:
                        # Use FinBERT for news sources
                        sentiment = await self._analyze_with_finbert(item.content)
                    
                    # Update the record
                    item.sentiment = sentiment['label']
                    item.sentiment_score = sentiment['score']
                    item.confidence = sentiment.get('confidence', 0)
                    item.model_used = sentiment['model']
                    
                except Exception as e:
                    logger.error(f"Error processing sentiment for item {item.id}: {e}")
                    item.sentiment = "neutral"
                    item.sentiment_score = 0
                    item.confidence = 0
            
            await self.session.commit()
            logger.info("Sentiment processing completed")
            
        except Exception as e:
            logger.error(f"Sentiment processing failed: {e}")
            await self.session.rollback()
            raise
    
    def _analyze_with_vader(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using VADER (for social media)"""
        try:
            if not text:
                return {
                    'label': 'neutral',
                    'score': 0,
                    'confidence': 0,
                    'model': 'vader'
                }
            
            # Clean text
            text = self._preprocess_text(text)
            
            # Get VADER scores
            scores = self.vader_analyzer.polarity_scores(text)
            
            # Determine sentiment label
            compound = scores['compound']
            if compound >= 0.05:
                label = 'positive'
            elif compound <= -0.05:
                label = 'negative'
            else:
                label = 'neutral'
            
            # Calculate confidence based on intensity
            confidence = abs(compound)
            
            return {
                'label': label,
                'score': compound,  # Range: -1 to 1
                'confidence': min(confidence * 1.5, 1.0),  # Scale up confidence
                'model': 'vader',
                'raw_scores': scores
            }
            
        except Exception as e:
            logger.error(f"VADER analysis failed: {e}")
            return {
                'label': 'neutral',
                'score': 0,
                'confidence': 0,
                'model': 'vader'
            }
    
    async def _analyze_with_finbert(self, text: str) -> Dict[str, Any]:
        """Analyze sentiment using FinBERT (for financial news)"""
        try:
            if not text:
                return {
                    'label': 'neutral',
                    'score': 0,
                    'confidence': 0,
                    'model': 'finbert'
                }
            
            # Clean and truncate text
            text = self._preprocess_text(text)[:512]  # FinBERT max length
            
            # Tokenize
            inputs = self.finbert_tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                padding=True,
                max_length=512
            )
            
            # Get predictions
            with torch.no_grad():
                outputs = self.finbert_model(**inputs)
                predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            
            # Get sentiment scores (FinBERT outputs: positive, negative, neutral)
            positive = predictions[0][0].item()
            negative = predictions[0][1].item()
            neutral = predictions[0][2].item()
            
            # Determine label and score
            max_score = max(positive, negative, neutral)
            if positive == max_score:
                label = 'positive'
                score = positive - negative  # Range: -1 to 1
            elif negative == max_score:
                label = 'negative'
                score = -negative + positive  # Range: -1 to 1
            else:
                label = 'neutral'
                score = 0
            
            return {
                'label': label,
                'score': score,
                'confidence': max_score,
                'model': 'finbert',
                'raw_scores': {
                    'positive': positive,
                    'negative': negative,
                    'neutral': neutral
                }
            }
            
        except Exception as e:
            logger.error(f"FinBERT analysis failed: {e}")
            return {
                'label': 'neutral',
                'score': 0,
                'confidence': 0,
                'model': 'finbert'
            }
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for sentiment analysis"""
        if not text:
            return ""
        
        # Remove URLs
        import re
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove special characters but keep sentiment indicators
        text = re.sub(r'[^\w\s!?.,;:\'\"-]', ' ', text)
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    async def analyze_single(self, text: str, source: str = "news") -> Dict[str, Any]:
        """Analyze a single text"""
        if source == "reddit":
            return self._analyze_with_vader(text)
        else:
            return await self._analyze_with_finbert(text)
    
    async def batch_analyze(self, texts: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Analyze multiple texts in batch"""
        results = []
        
        for item in texts:
            text = item.get('text', '')
            source = item.get('source', 'news')
            
            if source == "reddit":
                result = self._analyze_with_vader(text)
            else:
                result = await self._analyze_with_finbert(text)
            
            results.append(result)
        
        return results
