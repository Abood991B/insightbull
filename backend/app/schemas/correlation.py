"""
Correlation data schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class CorrelationBase(BaseModel):
    stock_symbol: str = Field(..., max_length=10)
    time_window: Literal["1d", "7d", "14d"]
    correlation_coefficient: float = Field(..., ge=-1.0, le=1.0)
    p_value: Optional[float] = Field(None, ge=0.0, le=1.0)
    sample_size: Optional[int] = Field(None, gt=0)
    calculated_at: datetime


class CorrelationCreate(CorrelationBase):
    pass


class CorrelationResponse(CorrelationBase):
    id: UUID
    created_at: datetime
    
    class Config:
        from_attributes = True
