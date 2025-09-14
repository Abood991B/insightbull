"""
Price data schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID


class PriceBase(BaseModel):
    stock_symbol: str = Field(..., max_length=10)
    date: date
    open: Optional[Decimal] = None
    high: Optional[Decimal] = None
    low: Optional[Decimal] = None
    close: Decimal
    volume: Optional[int] = None


class PriceCreate(PriceBase):
    pass


class PriceResponse(PriceBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    stock_symbol: str
    prices: List[PriceResponse]
    period_start: date
    period_end: date
    average_price: float
    price_change: float
    price_change_percent: float
