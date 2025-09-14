"""
Stock schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from decimal import Decimal


class StockBase(BaseModel):
    symbol: str = Field(..., max_length=10)
    name: str = Field(..., max_length=255)
    sector: Optional[str] = Field(None, max_length=100)
    market_cap: Optional[Decimal] = None
    is_active: bool = True


class StockCreate(StockBase):
    pass


class StockUpdate(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    market_cap: Optional[Decimal] = None
    is_active: Optional[bool] = None


class StockResponse(StockBase):
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True
