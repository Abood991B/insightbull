"""
Text Preprocessing Pipeline
==========================

Cleans and normalizes raw text data for sentiment analysis.
Handles HTML/Markdown cleanup, URL removal, and noise filtering.

Following FYP Report specification:
- SY-FR2: Preprocess Raw Data
- Data quality improvement
- Standardized text formatting
"""

import re
import html
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from ..infrastructure.log_system import get_logger
from ..utils.timezone import utc_now

from ..infrastructure.collectors.base_collector import RawData

logger = get_logger()


@dataclass
class ProcessingConfig:
    """Configuration for text processing"""
    remove_html: bool = True
    remove_urls: bool = True
    remove_mentions: bool = True
    remove_hashtags: bool = False
    normalize_whitespace: bool = True
    convert_to_lowercase: bool = False
    min_length: int = 10
    max_length: int = 5000
    language: str = "en"
    
    expand_contractions: bool = True


@dataclass
class ProcessingResult:
    """Result of text processing operation"""
    original_text: str
    processed_text: str
    removed_elements: Dict[str, int]
    processing_time: float
    success: bool
    error_message: Optional[str] = None


class TextProcessor:
    """
    Text preprocessing pipeline for raw social media and news content.
    
    Features:
    - HTML/Markdown cleaning
    - URL and mention removal
    - Whitespace normalization
    - Content validation
    - Noise filtering
    """
    
    # Common contractions for expansion
    CONTRACTIONS = {
        "ain't": "is not", "aren't": "are not", "can't": "cannot",
        "couldn't": "could not", "didn't": "did not", "doesn't": "does not",
        "don't": "do not", "hadn't": "had not", "hasn't": "has not",
        "haven't": "have not", "he'd": "he would", "he'll": "he will",
        "he's": "he is", "i'd": "i would", "i'll": "i will", "i'm": "i am",
        "i've": "i have", "isn't": "is not", "it'd": "it would",
        "it'll": "it will", "it's": "it is", "let's": "let us",
        "mightn't": "might not", "mustn't": "must not", "shan't": "shall not",
        "she'd": "she would", "she'll": "she will", "she's": "she is",
        "shouldn't": "should not", "that's": "that is", "there's": "there is",
        "they'd": "they would", "they'll": "they will", "they're": "they are",
        "they've": "they have", "we'd": "we would", "we're": "we are",
        "we've": "we have", "weren't": "were not", "what's": "what is",
        "where's": "where is", "who's": "who is", "won't": "will not",
        "wouldn't": "would not", "you'd": "you would", "you'll": "you will",
        "you're": "you are", "you've": "you have"
    }
    
    def __init__(self, config: Optional[ProcessingConfig] = None):
        """
        Initialize text processor.
        
        Args:
            config: Processing configuration
        """
        self.config = config or ProcessingConfig()
        self.logger = logger
        
        self._compile_patterns()
    
    def _compile_patterns(self):
        """Compile frequently used regex patterns"""
        # URL patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        self.url_short_pattern = re.compile(r'\b(?:bit\.ly|tinyurl|t\.co|goo\.gl|ow\.ly)/\S+')
        
        # Social media patterns
        self.mention_pattern = re.compile(r'@\w+|u/\w+|r/\w+')
        self.hashtag_pattern = re.compile(r'#\w+')
        
        # Whitespace patterns
        self.whitespace_pattern = re.compile(r'\s+')
        self.newline_pattern = re.compile(r'\n+')
        
        self.repeated_chars_pattern = re.compile(r'(.)\1{3,}')
        
        self.forum_quote_pattern = re.compile(r'^&gt;.*$', re.MULTILINE)
        self.edit_pattern = re.compile(r'\[?\s*edit\s*:.*?\]?', re.IGNORECASE)
    
    def process_raw_data(self, raw_data: RawData) -> ProcessingResult:
        """
        Process a single RawData object.
        
        Args:
            raw_data: Raw data to process
            
        Returns:
            ProcessingResult with processed text
        """
        start_time = utc_now()
        
        try:
            processed_text, removed_elements = self.process_text_with_tracking(raw_data.text)
            execution_time = (utc_now() - start_time).total_seconds()
            
            return ProcessingResult(
                original_text=raw_data.text,
                processed_text=processed_text,
                removed_elements=removed_elements,
                processing_time=execution_time,
                success=True
            )
            
        except Exception as e:
            execution_time = (utc_now() - start_time).total_seconds()
            return ProcessingResult(
                original_text=raw_data.text,
                processed_text="",
                removed_elements={},
                processing_time=execution_time,
                success=False,
                error_message=str(e)
            )
    
    def process_text_with_tracking(self, text: str) -> tuple[str, dict]:
        """
        Process text and track removed elements.
        
        Args:
            text: Text to process
            
        Returns:
            Tuple of (processed_text, removed_elements_dict)
        """
        if not text or not text.strip():
            return "", {}
        
        removed_elements = {
            "urls": [],
            "mentions": [],
            "hashtags": [],
            "html_tags": [],
            "special_chars": 0
        }
        
        processed = text
        
        # Track URLs before removal
        if self.config.remove_urls:
            urls = self.url_pattern.findall(processed) + self.url_short_pattern.findall(processed)
            removed_elements["urls"] = urls
            processed = self._remove_urls(processed)
        
        # Track mentions before removal  
        if self.config.remove_mentions:
            mentions = self.mention_pattern.findall(processed)
            removed_elements["mentions"] = mentions
            processed = self._remove_mentions(processed)
        
        # Track hashtags before removal
        if self.config.remove_hashtags:
            hashtags = self.hashtag_pattern.findall(processed)
            removed_elements["hashtags"] = hashtags
            processed = self._remove_hashtags(processed)
        
        # Continue with normal processing
        processed = self.process_text(processed)
        
        return processed, removed_elements

    def process_text(self, text: str) -> str:
        """
        Process a single text string.
        
        Args:
            text: Text to process
            
        Returns:
            Processed text
        """
        if not text or not text.strip():
            return ""
        
        processed = text
        
        # 1. HTML decoding and cleanup
        if self.config.remove_html:
            processed = self._remove_html(processed)
        
        # 2. URL removal
        if self.config.remove_urls:
            processed = self._remove_urls(processed)
        
        # 3. Social media specific cleanup
        if self.config.remove_mentions:
            processed = self._remove_mentions(processed)
        
        if self.config.remove_hashtags:
            processed = self._remove_hashtags(processed)
        
        # 4. Community forum specific cleanup (HackerNews, etc.)
        processed = self._clean_community_content(processed)
        
        # 5. Contraction expansion
        if self.config.expand_contractions:
            processed = self._expand_contractions(processed)
        
        # 6. Whitespace normalization
        if self.config.normalize_whitespace:
            processed = self._normalize_whitespace(processed)
        
        # 7. Special character cleanup
        processed = self._clean_special_characters(processed)
        
        # 8. Case conversion
        if self.config.convert_to_lowercase:
            processed = processed.lower()
        
        # 9. Final validation and trimming
        processed = processed.strip()
        
        # Validate length constraints
        if len(processed) < self.config.min_length:
            return ""
        
        # Intelligent truncation: preserve the most important parts
        # For financial news, the beginning (lead) and end (conclusion) are most critical
        if len(processed) > self.config.max_length:
            # Keep first 60% and last 40% of the allowed length
            keep_start = int(self.config.max_length * 0.6)
            keep_end = int(self.config.max_length * 0.4)
            
            start_text = processed[:keep_start].rsplit(' ', 1)[0]
            end_text = processed[-keep_end:].split(' ', 1)[-1]
            
            processed = f"{start_text} ... {end_text}"
        
        return processed
    
    def _remove_html(self, text: str) -> str:
        """Remove HTML tags and decode HTML entities"""
        # HTML entity decoding
        text = html.unescape(text)
        
        # Simple HTML tag removal using regex
        text = re.sub(r'<[^>]+>', ' ', text)
        
        return text
    
    def _remove_urls(self, text: str) -> str:
        """Remove URLs from text"""
        # Remove standard URLs
        text = self.url_pattern.sub(' ', text)
        # Remove short URLs
        text = self.url_short_pattern.sub(' ', text)
        return text
    
    def _remove_mentions(self, text: str) -> str:
        """Remove @mentions and u/username references"""
        return self.mention_pattern.sub(' ', text)
    
    def _remove_hashtags(self, text: str) -> str:
        """Remove hashtags"""
        return self.hashtag_pattern.sub(' ', text)
    
    def _clean_community_content(self, text: str) -> str:
        """Clean community forum content (HackerNews, etc.)"""
        # Remove quote blocks
        text = self.forum_quote_pattern.sub('', text)
        # Remove edit markers
        text = self.edit_pattern.sub('', text)
        return text
    
    def _expand_contractions(self, text: str) -> str:
        """Expand contractions"""
        words = text.split()
        expanded_words = []
        
        for word in words:
            word_lower = word.lower()
            # Handle punctuation attached to contractions
            if word_lower in self.CONTRACTIONS:
                expanded_words.append(self.CONTRACTIONS[word_lower])
            elif word_lower.rstrip('.,!?;:') in self.CONTRACTIONS:
                punctuation = word[len(word.rstrip('.,!?;:')):]
                expanded = self.CONTRACTIONS[word_lower.rstrip('.,!?;:')]
                expanded_words.append(expanded + punctuation)
            else:
                expanded_words.append(word)
        
        return ' '.join(expanded_words)
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace"""
        # Replace multiple newlines with single newline
        text = self.newline_pattern.sub(' ', text)
        # Replace multiple spaces with single space
        text = self.whitespace_pattern.sub(' ', text)
        return text.strip()
    
    def _clean_special_characters(self, text: str) -> str:
        """Clean excessive special characters while preserving meaning"""
        # Remove excessive character repetition (e.g., "sooooo" -> "so")
        text = self.repeated_chars_pattern.sub(r'\1\1', text)
        
        # Preserve important punctuation and financial symbols
        # Remove only truly problematic special characters
        text = re.sub(r'[^\w\s.,!?;:()\-\'\"$%#@/]', ' ', text)
        
        return text
    
    def process_batch(self, raw_data_list: List[RawData]) -> List[ProcessingResult]:
        """
        Process a batch of RawData objects.
        
        Args:
            raw_data_list: List of RawData to process
            
        Returns:
            List of ProcessingResult objects
        """
        results = []
        
        for raw_data in raw_data_list:
            result = self.process_raw_data(raw_data)
            results.append(result)
        
        return results