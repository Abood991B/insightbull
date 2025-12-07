"""
Financial Content Relevance Validator
=====================================

Filters non-financial content (sports, movies, etc.) from sentiment analysis.
"""

import re
from typing import Optional, List, Set
from dataclasses import dataclass


@dataclass
class RelevanceResult:
    """Result of content relevance validation."""
    is_relevant: bool
    confidence: float
    reason: str
    detected_financial_terms: List[str]
    detected_exclusion_patterns: List[str]


class FinancialContentValidator:
    """Validates whether content is relevant to financial/stock analysis."""
    
    FINANCIAL_KEYWORDS = {
        # Market terms
        "stock", "stocks", "share", "shares", "equity", "equities",
        "market", "markets", "trading", "trade", "trader", "investor",
        "investment", "invest", "portfolio", "holdings",
        
        # Financial metrics
        "earnings", "revenue", "profit", "loss", "eps", "pe ratio",
        "dividend", "yield", "margin", "ebitda", "guidance",
        "quarterly", "q1", "q2", "q3", "q4", "fiscal", "fy",
        
        # Market actions
        "buy", "sell", "hold", "upgrade", "downgrade", "outperform",
        "underperform", "price target", "rating", "analyst",
        "bullish", "bearish", "rally", "surge", "plunge", "crash",
        "soar", "tumble", "jump", "drop", "gain", "decline",
        
        # Corporate actions
        "merger", "acquisition", "ipo", "buyback", "split",
        "spinoff", "takeover", "deal", "valuation",
        
        # Financial entities
        "nasdaq", "nyse", "dow", "s&p", "sec", "fed", "fomc",
        "wall street", "hedge fund", "mutual fund", "etf",
        
        # Company-specific
        "ceo", "cfo", "executive", "board", "shareholder",
        "quarterly report", "annual report", "10-k", "10-q",
        "guidance", "outlook", "forecast"
    }
    
    # Strongly financial - these almost always indicate financial content
    STRONG_FINANCIAL_INDICATORS = {
        "stock price", "share price", "market cap", "eps", 
        "price target", "earnings report", "quarterly earnings",
        "revenue growth", "profit margin", "analyst rating",
        "buy rating", "sell rating", "hold rating",
        "$nasdaq", "$nyse", "pe ratio", "p/e ratio",
        "dividend yield", "stock split", "buyback",
        "investor relations", "sec filing"
    }
    
    # Exclusion patterns - content with these is likely NOT financial
    NON_FINANCIAL_PATTERNS = {
        # Sports
        "volleyball", "basketball", "football", "soccer", "hockey",
        "baseball", "tennis", "golf", "olympics", "championship",
        "tournament", "playoff", "league", "nba", "nfl", "mlb", "nhl",
        "coach", "player", "team wins", "team loses", "score",
        "touchdown", "goal scored", "home run", "slam dunk",
        "game highlights", "sports news", "match report",
        
        # Entertainment/Movies
        "movie", "film", "cinema", "actor", "actress", "director",
        "box office", "premiere", "trailer", "sequel", "franchise",
        "hollywood", "bollywood", "netflix original", "streaming",
        "tv show", "series", "episode", "season finale",
        "plot:", "starring:", "runtime:", "genre:",
        
        # Music/Entertainment
        "album", "concert", "tour", "music video", "grammy",
        "billboard", "spotify", "song", "lyrics",
        
        # Gaming (non-financial)
        "video game", "playstation", "xbox", "nintendo", "esports",
        "twitch", "gameplay", "dlc", "patch notes",
        
        # Food/Recipes
        "recipe", "cooking", "restaurant review", "ingredients",
        "calories", "nutrition facts",
        
        # Weather
        "weather forecast", "temperature", "precipitation",
        "humidity", "wind speed",
        
        # General news not financial
        "obituary", "wedding", "birth announcement", "local news",
        "community event", "school", "university sports"
    }
    
    # Stock symbols that are also common words (need extra validation)
    AMBIGUOUS_SYMBOLS = {
        "A", "ALL", "ARE", "AT", "BE", "BIG", "CAN", "CAR", "COST",
        "DAY", "FAST", "FUN", "GOOD", "HAS", "IT", "KEY", "LOW",
        "MAN", "NOW", "ONE", "OUT", "PLAY", "RUN", "SEE", "SO",
        "THE", "TRUE", "TWO", "VERY", "WAS", "WELL", "WORK", "YOU"
    }
    
    # Company name to symbol mapping for major tech stocks
    COMPANY_NAMES = {
        "AAPL": ["apple", "iphone", "ipad", "mac", "macbook", "tim cook"],
        "MSFT": ["microsoft", "windows", "azure", "office 365", "satya nadella"],
        "GOOGL": ["google", "alphabet", "youtube", "android", "sundar pichai"],
        "AMZN": ["amazon", "aws", "prime", "alexa", "jeff bezos", "andy jassy"],
        "META": ["meta", "facebook", "instagram", "whatsapp", "mark zuckerberg", "zuckerberg"],
        "NVDA": ["nvidia", "geforce", "cuda", "jensen huang"],
        "TSLA": ["tesla", "elon musk", "model 3", "model y", "model s", "cybertruck"],
        "AMD": ["amd", "advanced micro devices", "ryzen", "radeon", "lisa su"],
        "INTC": ["intel", "core i7", "core i9", "pat gelsinger"],
        "NFLX": ["netflix", "streaming service", "reed hastings"],
        "CRM": ["salesforce", "marc benioff"],
        "ORCL": ["oracle", "larry ellison"],
        "IBM": ["ibm", "international business machines", "watson"],
        "CSCO": ["cisco", "networking"],
        "ADBE": ["adobe", "photoshop", "creative cloud"],
        "PYPL": ["paypal", "venmo"],
        "SQ": ["square", "block inc", "cash app", "jack dorsey"],
        "SHOP": ["shopify", "e-commerce"],
        "UBER": ["uber", "ride sharing", "uber eats"],
        "LYFT": ["lyft", "rideshare"],
    }
    
    def __init__(self):
        """Initialize the validator with compiled patterns."""
        # Compile patterns for efficiency
        self._financial_pattern = self._compile_pattern(self.FINANCIAL_KEYWORDS)
        self._strong_financial_pattern = self._compile_pattern(self.STRONG_FINANCIAL_INDICATORS)
        self._non_financial_pattern = self._compile_pattern(self.NON_FINANCIAL_PATTERNS)
    
    def _compile_pattern(self, keywords: Set[str]) -> re.Pattern:
        """Compile a set of keywords into a regex pattern."""
        # Escape special regex characters and join with OR
        escaped = [re.escape(kw) for kw in keywords]
        pattern = r'\b(' + '|'.join(escaped) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def validate(
        self, 
        text: str, 
        symbol: Optional[str] = None,
        strict: bool = False
    ) -> RelevanceResult:
        """
        Validate whether content is financially relevant.
        
        Args:
            text: The content to validate
            symbol: Optional stock symbol for context
            strict: If True, require strong financial indicators
            
        Returns:
            RelevanceResult with relevance decision and confidence
        """
        if not text or len(text.strip()) < 10:
            return RelevanceResult(
                is_relevant=False,
                confidence=1.0,
                reason="Text too short or empty",
                detected_financial_terms=[],
                detected_exclusion_patterns=[]
            )
        
        text_lower = text.lower()
        
        # Check for exclusion patterns first
        exclusion_matches = self._non_financial_pattern.findall(text_lower)
        
        # Check for strong financial indicators
        strong_matches = self._strong_financial_pattern.findall(text_lower)
        
        # Check for general financial keywords
        financial_matches = self._financial_pattern.findall(text_lower)
        
        # Check if company name is mentioned (strong positive signal)
        company_mentioned = False
        if symbol and symbol.upper() in self.COMPANY_NAMES:
            company_terms = self.COMPANY_NAMES[symbol.upper()]
            for term in company_terms:
                if term.lower() in text_lower:
                    company_mentioned = True
                    financial_matches.append(f"company:{term}")
                    break
        
        # Decision logic
        has_exclusions = len(exclusion_matches) > 0
        has_strong_financial = len(strong_matches) > 0
        has_financial = len(financial_matches) > 0
        financial_count = len(financial_matches) + len(strong_matches) * 2
        exclusion_count = len(exclusion_matches)
        
        # Strong financial indicators override exclusions
        if has_strong_financial and len(strong_matches) >= 2:
            return RelevanceResult(
                is_relevant=True,
                confidence=0.95,
                reason="Strong financial indicators detected",
                detected_financial_terms=strong_matches + financial_matches,
                detected_exclusion_patterns=exclusion_matches
            )
        
        # Many exclusion patterns with few financial terms = not relevant
        if exclusion_count >= 2 and financial_count < 3:
            return RelevanceResult(
                is_relevant=False,
                confidence=0.85,
                reason=f"Non-financial content detected: {', '.join(exclusion_matches[:3])}",
                detected_financial_terms=financial_matches,
                detected_exclusion_patterns=exclusion_matches
            )
        
        # Single exclusion with no financial terms = not relevant
        if has_exclusions and not has_financial:
            return RelevanceResult(
                is_relevant=False,
                confidence=0.80,
                reason=f"Non-financial content: {exclusion_matches[0]}",
                detected_financial_terms=[],
                detected_exclusion_patterns=exclusion_matches
            )
        
        # Company name mentioned = likely relevant
        if company_mentioned:
            return RelevanceResult(
                is_relevant=True,
                confidence=0.90,
                reason="Company name mentioned in financial context",
                detected_financial_terms=financial_matches,
                detected_exclusion_patterns=exclusion_matches
            )
        
        # Multiple financial terms = relevant
        if financial_count >= 3:
            return RelevanceResult(
                is_relevant=True,
                confidence=0.85,
                reason="Multiple financial terms detected",
                detected_financial_terms=financial_matches,
                detected_exclusion_patterns=exclusion_matches
            )
        
        # Some financial terms, no exclusions = probably relevant
        if has_financial and not has_exclusions:
            return RelevanceResult(
                is_relevant=True,
                confidence=0.70,
                reason="Financial terms detected",
                detected_financial_terms=financial_matches,
                detected_exclusion_patterns=[]
            )
        
        # Strict mode requires clear financial content
        if strict:
            return RelevanceResult(
                is_relevant=False,
                confidence=0.60,
                reason="Insufficient financial indicators (strict mode)",
                detected_financial_terms=financial_matches,
                detected_exclusion_patterns=exclusion_matches
            )
        
        # Check for patterns that indicate non-financial content
        non_financial_patterns_extra = [
            r'\d{3,4}p',  # Video resolution (720p, 1080p)
            r'WEB-DL|H264|x264|BluRay|HDTV',  # Video encoding
            r'\d{1,3}[- ,]\d{1,3}$',  # Sports scores at end
            r'\d{1,3}[- ,]\d{1,3}\s',  # Sports scores  
            r'nonconvex|inclined plane|granular flow|macroscopi',  # Scientific terms
            r'Plot:',  # Movie plot description
        ]
        
        for pattern in non_financial_patterns_extra:
            if re.search(pattern, text, re.IGNORECASE):
                return RelevanceResult(
                    is_relevant=False,
                    confidence=0.75,
                    reason=f"Detected non-financial pattern: {pattern}",
                    detected_financial_terms=financial_matches,
                    detected_exclusion_patterns=exclusion_matches + [pattern]
                )
        
        # No financial terms and no clear signals either way = require at least some financial context
        if not has_financial and not company_mentioned:
            return RelevanceResult(
                is_relevant=False,
                confidence=0.65,
                reason="No financial indicators detected",
                detected_financial_terms=[],
                detected_exclusion_patterns=exclusion_matches
            )
        
        # Default: assume relevant if no exclusions found and has some financial context
        return RelevanceResult(
            is_relevant=not has_exclusions,
            confidence=0.50,
            reason="Ambiguous content - defaulting based on exclusion patterns",
            detected_financial_terms=financial_matches,
            detected_exclusion_patterns=exclusion_matches
        )
    
    def is_relevant(
        self, 
        text: str, 
        symbol: Optional[str] = None,
        min_confidence: float = 0.6
    ) -> bool:
        """
        Simple boolean check for relevance.
        
        Args:
            text: Content to check
            symbol: Optional stock symbol
            min_confidence: Minimum confidence threshold
            
        Returns:
            True if content is relevant with sufficient confidence
        """
        result = self.validate(text, symbol)
        return result.is_relevant and result.confidence >= min_confidence
    
    def get_relevance_score(self, text: str, symbol: Optional[str] = None) -> float:
        """
        Get a 0-1 relevance score for the content.
        
        Higher scores = more likely to be financial content.
        
        Args:
            text: Content to score
            symbol: Optional stock symbol
            
        Returns:
            Float between 0-1
        """
        result = self.validate(text, symbol)
        if result.is_relevant:
            return result.confidence
        else:
            return 1.0 - result.confidence


# Global singleton instance
_validator_instance: Optional[FinancialContentValidator] = None


def get_content_validator() -> FinancialContentValidator:
    """Get the global content validator instance."""
    global _validator_instance
    if _validator_instance is None:
        _validator_instance = FinancialContentValidator()
    return _validator_instance
