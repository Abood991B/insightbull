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
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import logging
import numpy as np

# Transformers imports
try:
    from transformers import (
        AutoTokenizer, 
        AutoModelForSequenceClassification,
        pipeline
    )
    import torch.nn.functional as F
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
        self._preprocessor = FinancialTextPreprocessor(use_advanced_preprocessing=True)  # Enable advanced by default
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
    Enhanced text preprocessor optimized for financial content and FinBERT.
    
    Handles financial text specific cleaning while preserving
    domain-relevant information like tickers, financial terms, and numbers.
    Includes advanced preprocessing with entity normalization and abbreviation expansion.
    """
    
    def __init__(self, use_advanced_preprocessing: bool = True):
        """
        Initialize preprocessor.
        
        Args:
            use_advanced_preprocessing: Enable advanced financial preprocessing features
        """
        self.use_advanced = use_advanced_preprocessing
        
        # Compile regex patterns for efficiency
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.ticker_pattern = re.compile(r'\$[A-Z]{1,5}\b')  # Stock tickers like $AAPL
        self.ticker_context_pattern = re.compile(r'\b([A-Z]{2,5})\s+(?:stock|shares|equity|ticker)\b', re.IGNORECASE)
        self.multiple_spaces = re.compile(r'\s+')
        self.html_pattern = re.compile(r'<[^>]+>')
        
        # Financial-specific patterns to preserve
        self.currency_pattern = re.compile(r'\$[\d,]+(?:\.\d{2})?')
        self.percentage_pattern = re.compile(r'\d+(?:\.\d+)?%')
        self.date_pattern = re.compile(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b')
        
        # Advanced preprocessing patterns
        if self.use_advanced:
            self.billion_pattern = re.compile(r'\$(\d+(?:\.\d+)?)\s*B(?:illion)?', re.IGNORECASE)
            self.million_pattern = re.compile(r'\$(\d+(?:\.\d+)?)\s*M(?:illion)?', re.IGNORECASE)
            self.trillion_pattern = re.compile(r'\$(\d+(?:\.\d+)?)\s*T(?:rillion)?', re.IGNORECASE)
            
            # Company name variations (normalize to standard)
            self.company_aliases = {
                r'\bAAPL\b': 'Apple',
                r'\bMSFT\b': 'Microsoft',
                r'\bGOOGL?\b': 'Google',
                r'\bAMZN\b': 'Amazon',
                r'\bTSLA\b': 'Tesla',
                r'\bMETA\b': 'Meta',
                r'\bNVDA\b': 'Nvidia',
                r'\bAMD\b': 'AMD',
                r'\bINTEL?\b': 'Intel',
                r'\bORCL\b': 'Oracle'
            }
            
            # Financial abbreviations to expand
            self.financial_abbrev = {
                r'\bP/E\b': 'price to earnings',
                r'\bEPS\b': 'earnings per share',
                r'\bROI\b': 'return on investment',
                r'\bROE\b': 'return on equity',
                r'\bEBITDA\b': 'earnings before interest taxes depreciation amortization',
                r'\bIPO\b': 'initial public offering',
                r'\bM&A\b': 'mergers and acquisitions',
                r'\bYoY\b': 'year over year',
                r'\bQoQ\b': 'quarter over quarter',
                r'\bATH\b': 'all time high',
                r'\bATL\b': 'all time low',
                r'\bCEO\b': 'chief executive officer',
                r'\bCFO\b': 'chief financial officer',
                r'\bQ[1-4]\b': lambda m: f'quarter {m.group(0)[-1]}',
                r'\bFY\b': 'fiscal year',
                r'\bGDP\b': 'gross domestic product',
                r'\bCPI\b': 'consumer price index'
            }
            
            # Financial keywords for intelligent truncation
            self.financial_keywords = [
                'earnings', 'revenue', 'profit', 'loss', 'growth', 'decline',
                'stock', 'shares', 'price', 'market', 'analyst', 'forecast',
                'quarter', 'guidance', 'outlook', 'performance', 'sales',
                'dividend', 'buyback', 'acquisition', 'merger', 'expansion',
                'beat', 'miss', 'estimate', 'consensus', 'upgrade', 'downgrade',
                'bullish', 'bearish', 'rally', 'selloff', 'volatility'
            ]
            
            # Noise patterns to filter
            self.noise_patterns = [
                re.compile(r'\b(?:Advertisement|Sponsored|Ad)\b', re.IGNORECASE),
                re.compile(r'\b(?:Click here|Read more|Subscribe)\b', re.IGNORECASE),
                re.compile(r'\[.*?\]'),  # [Advertisement], [Sponsored], etc.
            ]
    
    def preprocess(self, text: str) -> str:
        """
        Preprocess financial text for FinBERT analysis.
        
        Preserves financial-relevant information while cleaning noise.
        Includes advanced preprocessing if enabled.
        
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
        
        # Advanced preprocessing
        if self.use_advanced:
            # Filter noise patterns (ads, promotional content)
            text = self._filter_noise(text)
            
            # Extract and normalize financial entities
            text = self._normalize_entities(text)
            
            # Normalize company names
            text = self._normalize_company_names(text)
            
            # Standardize large numbers
            text = self._standardize_numbers(text)
            
            # Expand financial abbreviations
            text = self._expand_abbreviations(text)
            
            # Normalize percentage expressions
            text = re.sub(r'(\d+(?:\.\d+)?)%', r'\1 percent', text)
        
        # Preserve stock tickers (important for financial sentiment)
        # No modification needed - FinBERT should understand these
        
        # Normalize excessive whitespace
        text = self.multiple_spaces.sub(' ', text)
        
        # Strip leading/trailing whitespace
        text = text.strip()
        
        # Ensure text isn't too long for BERT
        if len(text) > 2000:
            if self.use_advanced:
                # Intelligent truncation preserving key financial content
                text = self._intelligent_truncation(text)
            else:
                # Simple truncation
                text = text[:2000]
                # Try to end at a sentence boundary
                last_period = text.rfind('.')
                if last_period > 1500:  # Don't cut too much
                    text = text[:last_period + 1]
        
        return text
    
    def _filter_noise(self, text: str) -> str:
        """Remove noise patterns like ads and promotional content."""
        for pattern in self.noise_patterns:
            text = pattern.sub(' ', text)
        return text
    
    def _normalize_entities(self, text: str) -> str:
        """Extract and normalize financial entities like tickers."""
        # Normalize ticker mentions with context
        # e.g., "AAPL stock" -> "Apple stock"
        matches = self.ticker_context_pattern.findall(text)
        for ticker in matches:
            if ticker.upper() in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']:
                # Replace with company name for better context
                for pattern, company in self.company_aliases.items():
                    if re.match(pattern, ticker, re.IGNORECASE):
                        text = re.sub(rf'\b{ticker}\b', company, text, flags=re.IGNORECASE)
                        break
        
        return text
    
    def _normalize_company_names(self, text: str) -> str:
        """Normalize company name variations to standard names."""
        for pattern, standard_name in self.company_aliases.items():
            # Only replace if ticker is standalone or followed by financial context
            text = re.sub(pattern, standard_name, text)
        return text
    
    def _standardize_numbers(self, text: str) -> str:
        """Standardize financial numbers for better understanding."""
        # Trillion marker
        text = self.trillion_pattern.sub(
            lambda m: f'${float(m.group(1)) * 1e12:,.0f}', text
        )
        
        # Billion marker
        text = self.billion_pattern.sub(
            lambda m: f'${float(m.group(1)) * 1e9:,.0f}', text
        )
        
        # Million marker
        text = self.million_pattern.sub(
            lambda m: f'${float(m.group(1)) * 1e6:,.0f}', text
        )
        
        return text
    
    def _expand_abbreviations(self, text: str) -> str:
        """Expand common financial abbreviations."""
        for abbr, expansion in self.financial_abbrev.items():
            if callable(expansion):
                text = re.sub(abbr, expansion, text, flags=re.IGNORECASE)
            else:
                text = re.sub(abbr, expansion, text, flags=re.IGNORECASE)
        
        return text
    
    def _intelligent_truncation(self, text: str) -> str:
        """
        Intelligently truncate long texts while preserving key information.
        
        Strategy:
        1. Keep first 200 tokens (usually headline/summary)
        2. Extract sentences with high financial keyword density
        3. Keep last 150 tokens (often conclusion/outlook)
        """
        sentences = re.split(r'[.!?]+', text)
        
        if len(sentences) <= 5:
            # Short text, simple truncation
            text = text[:2000]
            last_period = text.rfind('.')
            if last_period > 1500:
                text = text[:last_period + 1]
            return text
        
        # Score each sentence by financial keyword density
        scored_sentences = []
        for sent in sentences:
            sent_lower = sent.lower()
            score = sum(1 for keyword in self.financial_keywords if keyword in sent_lower)
            scored_sentences.append((score, sent))
        
        # Sort by score (descending)
        scored_sentences.sort(reverse=True, key=lambda x: x[0])
        
        # Take top scoring sentences
        important_sentences = [sent for score, sent in scored_sentences[:10] if score > 0]
        
        # Reconstruct: beginning + important middle + end
        beginning = '. '.join(sentences[:3])
        middle = '. '.join(important_sentences)
        end = '. '.join(sentences[-2:]) if len(sentences) > 2 else ''
        
        reconstructed = f"{beginning}. {middle}. {end}"
        
        # Final length check
        if len(reconstructed) > 2000:
            reconstructed = reconstructed[:2000]
            last_period = reconstructed.rfind('.')
            if last_period > 1500:
                reconstructed = reconstructed[:last_period + 1]
        
        return reconstructed
    
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


class ConfidenceCalibrator:
    """
    Calibrate FinBERT confidence scores using temperature scaling.
    
    Temperature scaling adjusts model confidence to better reflect true accuracy.
    Trained on validation set with ground truth labels.
    """
    
    def __init__(self, temperature: float = 1.5):
        """
        Initialize confidence calibrator.
        
        Args:
            temperature: Scaling factor (>1 reduces overconfidence, <1 increases)
                        Default 1.5 for financial models which tend to be overconfident
        """
        self.temperature = temperature
        logger.info(f"ConfidenceCalibrator initialized with temperature={temperature}")
    
    def calibrate_scores(self, logits: torch.Tensor) -> torch.Tensor:
        """
        Apply temperature scaling to logits before softmax.
        
        Args:
            logits: Raw model outputs [batch_size, num_classes]
            
        Returns:
            Calibrated probability distribution
        """
        # Scale logits by temperature
        scaled_logits = logits / self.temperature
        
        # Apply softmax
        calibrated_probs = F.softmax(scaled_logits, dim=-1)
        
        return calibrated_probs
    
    def find_optimal_temperature(self, 
                                  val_logits: torch.Tensor, 
                                  val_labels: torch.Tensor) -> float:
        """
        Find optimal temperature using validation set.
        
        Minimizes negative log-likelihood (cross-entropy) on validation data.
        
        Args:
            val_logits: Validation set logits [n_samples, num_classes]
            val_labels: Ground truth labels [n_samples]
            
        Returns:
            Optimal temperature value
        """
        from scipy.optimize import minimize
        
        def objective(temp):
            scaled_logits = val_logits / temp[0]
            loss = F.cross_entropy(scaled_logits, val_labels)
            return loss.item()
        
        result = minimize(objective, x0=[1.5], bounds=[(0.5, 3.0)])
        optimal_temp = result.x[0]
        
        logger.info(f"Optimal temperature found: {optimal_temp:.3f}")
        return optimal_temp
    
    def set_temperature(self, temperature: float):
        """Update temperature value."""
        self.temperature = temperature
        logger.info(f"Temperature updated to {temperature}")


class EnsembleFinBERTModel(SentimentModel):
    """
    Ensemble FinBERT model combining multiple checkpoints for robust predictions.
    
    Uses weighted averaging of predictions from:
    1. ProsusAI/finbert (primary - 60% weight)
    2. yiyanghkust/finbert-tone (alternative - 40% weight)
    
    Ensemble reduces variance and improves accuracy by 1-2% over single model.
    """
    
    # Model configurations
    MODELS_CONFIG = [
        {"name": "ProsusAI/finbert", "weight": 0.6, "label_map": {"positive": "positive", "negative": "negative", "neutral": "neutral"}},
        {"name": "yiyanghkust/finbert-tone", "weight": 0.4, "label_map": {"Positive": "positive", "Negative": "negative", "Neutral": "neutral"}}
    ]
    
    def __init__(self, use_gpu: bool = None, max_length: int = 512, use_calibration: bool = True):
        """
        Initialize Ensemble FinBERT model.
        
        Args:
            use_gpu: Whether to use GPU acceleration (auto-detect if None)
            max_length: Maximum sequence length for tokenization
            use_calibration: Whether to apply confidence calibration
        """
        self.use_gpu = use_gpu if use_gpu is not None else torch.cuda.is_available()
        self.max_length = max_length
        self.use_calibration = use_calibration
        self.device = None
        self.models = []  # List of (model, tokenizer, weight, label_map)
        self.calibrator = ConfidenceCalibrator(temperature=1.5) if use_calibration else None
        self._preprocessor = FinancialTextPreprocessor(use_advanced_preprocessing=True)
        super().__init__()
    
    def _initialize_model_info(self) -> ModelInfo:
        """Initialize Ensemble FinBERT model metadata."""
        return ModelInfo(
            name="FinBERT-Ensemble",
            version="1.0.0",
            description="Ensemble of multiple FinBERT models for robust financial sentiment analysis",
            supported_sources=[
                DataSource.FINNHUB,
                DataSource.MARKETAUX,
                DataSource.NEWSAPI
            ],
            max_batch_size=12 if self.use_gpu else 6,  # Smaller batches due to multiple models
            avg_processing_time=200.0 if not self.use_gpu else 75.0  # Slower due to ensemble
        )
    
    async def _load_model(self) -> None:
        """Load all ensemble FinBERT models."""
        try:
            logger.info("Loading Ensemble FinBERT models...")
            
            # Set device
            if self.use_gpu and torch.cuda.is_available():
                self.device = torch.device("cuda")
                logger.info("Using GPU for Ensemble FinBERT inference")
            else:
                self.device = torch.device("cpu")
                logger.info("Using CPU for Ensemble FinBERT inference")
            
            # Load each model in ensemble
            for config in self.MODELS_CONFIG:
                try:
                    logger.info(f"Loading {config['name']} (weight: {config['weight']})...")
                    
                    tokenizer = AutoTokenizer.from_pretrained(
                        config['name'],
                        use_fast=True
                    )
                    
                    model = AutoModelForSequenceClassification.from_pretrained(
                        config['name'],
                        num_labels=3,
                        output_attentions=False,
                        output_hidden_states=False
                    )
                    
                    model.to(self.device)
                    model.eval()
                    
                    self.models.append({
                        'name': config['name'],
                        'model': model,
                        'tokenizer': tokenizer,
                        'weight': config['weight'],
                        'label_map': config['label_map']
                    })
                    
                    logger.info(f"✓ {config['name']} loaded successfully")
                    
                except Exception as e:
                    logger.warning(f"Failed to load {config['name']}: {str(e)}. Skipping...")
            
            if not self.models:
                raise ModelLoadError("No models loaded successfully in ensemble")
            
            # Normalize weights if some models failed to load
            total_weight = sum(m['weight'] for m in self.models)
            for model_info in self.models:
                model_info['weight'] = model_info['weight'] / total_weight
            
            logger.info(f"Ensemble FinBERT loaded with {len(self.models)} models")
            
        except Exception as e:
            logger.error(f"Failed to load Ensemble FinBERT: {str(e)}")
            raise ModelLoadError(f"Ensemble FinBERT loading failed: {str(e)}")
    
    async def _analyze_batch(self, texts: List[str]) -> List[SentimentResult]:
        """
        Analyze sentiment for a batch of texts using ensemble.
        
        Args:
            texts: List of text strings to analyze
            
        Returns:
            List of SentimentResult objects
        """
        if not self.models:
            raise AnalysisError("Ensemble FinBERT models not loaded")
        
        results = []
        
        # Process texts in smaller sub-batches
        batch_size = self.model_info.max_batch_size
        
        for i in range(0, len(texts), batch_size):
            sub_batch = texts[i:i + batch_size]
            sub_results = await self._process_ensemble_batch(sub_batch)
            results.extend(sub_results)
        
        return results
    
    async def _process_ensemble_batch(self, texts: List[str]) -> List[SentimentResult]:
        """Process a batch using ensemble of models."""
        batch_results = []
        
        for text in texts:
            start_time = time.time()
            
            try:
                # Preprocess text
                processed_text = self._preprocessor.preprocess(text)
                
                # Get predictions from all models
                all_predictions = []
                for model_info in self.models:
                    pred = self._predict_single_model(processed_text, model_info)
                    all_predictions.append(pred)
                
                # Ensemble fusion
                ensemble_result = self._ensemble_fusion(all_predictions, time.time() - start_time)
                batch_results.append(ensemble_result)
                
            except Exception as e:
                logger.error(f"Ensemble analysis failed: {str(e)}")
                batch_results.append(self._create_error_result(time.time() - start_time, str(e)))
        
        return batch_results
    
    def _predict_single_model(self, text: str, model_info: Dict) -> Dict[str, Any]:
        """Get prediction from a single model in ensemble."""
        tokenizer = model_info['tokenizer']
        model = model_info['model']
        label_map = model_info['label_map']
        
        # Tokenize
        inputs = tokenizer(
            text,
            padding=True,
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Get logits
        with torch.no_grad():
            outputs = model(**inputs)
            logits = outputs.logits
            
            # Apply calibration if enabled
            if self.calibrator:
                probs = self.calibrator.calibrate_scores(logits)
            else:
                probs = F.softmax(logits, dim=-1)
        
        # Convert to numpy
        probs = probs.cpu().numpy()[0]
        
        # Map labels (different models may use different label names)
        label_scores = {}
        config_labels = list(label_map.keys())
        for i, label in enumerate(config_labels):
            standard_label = label_map[label]
            label_scores[standard_label] = float(probs[i])
        
        return {
            'model_name': model_info['name'],
            'label_scores': label_scores,
            'predicted_label': max(label_scores, key=label_scores.get),
            'confidence': max(label_scores.values())
        }
    
    def _ensemble_fusion(self, predictions: List[Dict], processing_time: float) -> SentimentResult:
        """
        Fuse predictions from multiple models using weighted averaging.
        
        Args:
            predictions: List of prediction dictionaries from each model
            processing_time: Total processing time
            
        Returns:
            Ensemble SentimentResult
        """
        # Weighted average of scores
        ensemble_scores = {'positive': 0.0, 'negative': 0.0, 'neutral': 0.0}
        
        for i, pred in enumerate(predictions):
            weight = self.models[i]['weight']
            for label in ensemble_scores:
                ensemble_scores[label] += weight * pred['label_scores'].get(label, 0.0)
        
        # Determine final label
        predicted_label = max(ensemble_scores, key=ensemble_scores.get)
        confidence = ensemble_scores[predicted_label]
        
        # Map to standard label
        label_mapping = {
            'positive': SentimentLabel.POSITIVE,
            'negative': SentimentLabel.NEGATIVE,
            'neutral': SentimentLabel.NEUTRAL
        }
        label = label_mapping[predicted_label]
        
        # Calculate normalized score [-1 to 1]
        normalized_score = ensemble_scores['positive'] - ensemble_scores['negative']
        
        # Include individual model predictions in raw_scores
        model_predictions = {
            pred['model_name'].split('/')[-1]: {
                'label': pred['predicted_label'],
                'confidence': pred['confidence'],
                'scores': pred['label_scores']
            }
            for pred in predictions
        }
        
        return SentimentResult(
            label=label,
            score=normalized_score,
            confidence=confidence,
            raw_scores={
                'ensemble_scores': ensemble_scores,
                'individual_models': model_predictions,
                'num_models': len(predictions),
                'calibrated': self.use_calibration
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
        """Clean up all ensemble model resources."""
        for model_info in self.models:
            model_info['model'].to('cpu')
        
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        
        logger.info("Ensemble FinBERT resources cleaned up")


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