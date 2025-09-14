"""
Admin schemas for API validation
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime


class AdminDashboardResponse(BaseModel):
    total_stocks: int
    total_sentiment_records: int
    sentiment_last_24h: int
    active_apis: int
    total_apis: int
    system_health: Literal["healthy", "warning", "critical"]
    recent_errors: int
    last_pipeline_run: Optional[datetime] = None


class ApiConfigBase(BaseModel):
    name: str = Field(..., max_length=100)
    endpoint: Optional[str] = Field(None, max_length=500)
    api_key: Optional[str] = None
    enabled: bool = True
    rate_limit: Optional[int] = None


class ApiConfigCreate(ApiConfigBase):
    pass


class ApiConfigUpdate(BaseModel):
    endpoint: Optional[str] = None
    api_key: Optional[str] = None
    enabled: Optional[bool] = None
    rate_limit: Optional[int] = None


class ApiConfigResponse(ApiConfigBase):
    id: str
    last_checked: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    has_api_key: bool = False
    
    class Config:
        from_attributes = True


class StockWatchlistUpdate(BaseModel):
    symbol: str = Field(..., max_length=10)
    name: str = Field(..., max_length=255)
    sector: Optional[str] = Field(None, max_length=100)
    market_cap: Optional[float] = None
    is_active: bool = True


class StorageSettings(BaseModel):
    storage_type: Literal["local", "cloud", "database"]
    retention_days: int = Field(30, ge=1, le=365)
    cleanup_enabled: bool = True
    max_storage_gb: Optional[int] = None


class SystemLogResponse(BaseModel):
    id: str
    level: str
    source: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class ModelMetricResponse(BaseModel):
    id: str
    model_name: str
    accuracy: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    evaluation_date: datetime
    test_size: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True
