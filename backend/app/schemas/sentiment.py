"""
Sentiment data schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class SentimentBase(BaseModel):
    stock_symbol: str = Field(..., max_length=10)
    source: Literal['reddit', 'finnhub', 'marketaux', 'newsapi']
    content: Optional[str] = None
    sentiment: Literal['positive', 'negative', 'neutral']
    sentiment_score: float = Field(..., ge=-1.0, le=1.0)
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    model_used: Optional[Literal['finbert', 'vader']] = None
    source_url: Optional[str] = None
    published_at: datetime


class SentimentCreate(SentimentBase):
    pass


class SentimentResponse(SentimentBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class SentimentAggregateResponse(BaseModel):
    stock_symbol: str
    time_window: str
    positive_count: int
    negative_count: int
    neutral_count: int
    average_sentiment: float
    sentiment_trend: Literal['bullish', 'bearish', 'neutral']
    period_start: datetime
    period_end: datetime
