"""
Admin Panel Schemas
==================

Pydantic schemas for admin panel API requests and responses.
Implements FYP Report Phase 8 requirements U-FR6 through U-FR10.
"""

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


# U-FR6: Model Accuracy Evaluation Schemas
class ModelMetrics(BaseModel):
    """Individual model performance metrics"""
    name: str = Field(..., description="Name of the sentiment model")
    accuracy: float = Field(..., ge=0, le=1, description="Model accuracy (0-1)")
    precision: float = Field(..., ge=0, le=1, description="Model precision (0-1)")
    recall: float = Field(..., ge=0, le=1, description="Model recall (0-1)")
    f1_score: float = Field(..., ge=0, le=1, description="F1 score (0-1)")
    total_predictions: int = Field(..., ge=0, description="Total predictions made")
    last_evaluated: datetime = Field(..., description="Last evaluation timestamp")


class ModelAccuracyResponse(BaseModel):
    """Model accuracy evaluation response - Implements U-FR6"""
    models: List[ModelMetrics] = Field(..., description="Performance metrics for each model")
    overall_accuracy: float = Field(..., ge=0, le=1, description="Overall system accuracy")
    evaluation_period: str = Field(..., description="Evaluation time period")
    total_data_points: int = Field(..., ge=0, description="Total data points evaluated")
    last_updated: datetime = Field(..., description="Last update timestamp")


# U-FR7: API Configuration Schemas
class APIKeyStatus(str, Enum):
    """API key status enumeration"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    INVALID = "invalid"


class APIServiceConfig(BaseModel):
    """Individual API service configuration"""
    service_name: str = Field(..., description="Name of the API service")
    is_configured: bool = Field(..., description="Whether API key is configured")
    status: APIKeyStatus = Field(..., description="Current status of the API key")
    rate_limit: Optional[int] = Field(None, description="Rate limit per hour")
    last_tested: Optional[datetime] = Field(None, description="Last connectivity test")
    error_message: Optional[str] = Field(None, description="Last error message if any")


class APIConfigResponse(BaseModel):
    """API configuration overview response - Implements U-FR7"""
    services: List[APIServiceConfig] = Field(..., description="Configuration for each API service")
    total_configured: int = Field(..., description="Total number of configured APIs")
    total_active: int = Field(..., description="Total number of active APIs")
    last_updated: datetime = Field(..., description="Last configuration update")


class APIKeyUpdateRequest(BaseModel):
    """API key update request"""
    service: str = Field(..., description="Name of the API service")
    keys: Dict[str, str] = Field(..., description="API keys for the service")
    additional_config: Optional[Dict[str, Any]] = Field(None, description="Additional configuration")


class APIKeyUpdateResponse(BaseModel):
    """API key update response"""
    success: bool
    service: str
    status: APIKeyStatus
    message: str


# U-FR8: Stock Watchlist Management Schemas
class StockInfo(BaseModel):
    """Stock information for watchlist"""
    symbol: str = Field(..., max_length=10, description="Stock symbol")
    company_name: str = Field(..., description="Company name")
    sector: Optional[str] = Field(None, description="Company sector")
    is_active: bool = Field(True, description="Whether stock is actively tracked")
    added_date: datetime = Field(..., description="Date added to watchlist")


class WatchlistResponse(BaseModel):
    """Current watchlist response - Implements U-FR8"""
    stocks: List[StockInfo] = Field(..., description="List of tracked stocks")
    total_stocks: int = Field(..., description="Total number of stocks in watchlist")
    active_stocks: int = Field(..., description="Number of actively tracked stocks")
    last_updated: datetime = Field(..., description="Last watchlist update")


class WatchlistUpdateRequest(BaseModel):
    """Watchlist update request"""
    action: str = Field(..., pattern="^(add|remove|activate|deactivate|toggle)$")
    symbol: str = Field(..., max_length=10, description="Stock symbol")
    company_name: Optional[str] = Field(None, description="Company name (required for add)")

    @field_validator('company_name')
    @classmethod
    def validate_company_name(cls, v, info):
        if info.data.get('action') == 'add' and not v:
            raise ValueError('Company name is required when adding a stock')
        return v


class WatchlistUpdateResponse(BaseModel):
    """Watchlist update response"""
    success: bool
    action: str
    symbol: str
    message: str
    updated_watchlist: WatchlistResponse


# U-FR9: Data Storage Settings Schemas
class StorageMetrics(BaseModel):
    """Storage usage metrics"""
    total_records: int = Field(..., ge=0, description="Total number of records")
    storage_size_mb: float = Field(..., ge=0, description="Storage size in MB")
    sentiment_records: int = Field(..., ge=0, description="Number of sentiment records")
    stock_price_records: int = Field(..., ge=0, description="Number of stock price records")
    oldest_record: Optional[datetime] = Field(None, description="Oldest record timestamp")
    newest_record: Optional[datetime] = Field(None, description="Newest record timestamp")


class RetentionPolicy(BaseModel):
    """Data retention policy configuration"""
    sentiment_data_days: int = Field(..., ge=1, description="Days to retain sentiment data")
    price_data_days: int = Field(..., ge=1, description="Days to retain price data")
    log_data_days: int = Field(..., ge=1, description="Days to retain log data")
    auto_cleanup_enabled: bool = Field(..., description="Whether auto cleanup is enabled")


class StorageSettingsResponse(BaseModel):
    """Storage settings response - Implements U-FR9"""
    metrics: StorageMetrics = Field(..., description="Current storage metrics")
    retention_policy: RetentionPolicy = Field(..., description="Current retention policy")
    backup_enabled: bool = Field(..., description="Whether automatic backups are enabled")
    last_cleanup: Optional[datetime] = Field(None, description="Last cleanup timestamp")
    next_cleanup: Optional[datetime] = Field(None, description="Next scheduled cleanup")


class StorageSettingsUpdateRequest(BaseModel):
    """Storage settings update request"""
    sentiment_data_days: Optional[int] = Field(None, ge=1, le=365)
    price_data_days: Optional[int] = Field(None, ge=1, le=365)
    log_data_days: Optional[int] = Field(None, ge=1, le=90)
    auto_cleanup_enabled: Optional[bool] = None
    backup_enabled: Optional[bool] = None


class StorageSettingsUpdateResponse(BaseModel):
    """Storage settings update response"""
    success: bool
    message: str
    updated_settings: StorageSettingsResponse


# U-FR10: System Logs Schemas
class LogLevel(str, Enum):
    """Log level enumeration"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogEntry(BaseModel):
    """Individual log entry"""
    timestamp: datetime = Field(..., description="Log entry timestamp")
    level: LogLevel = Field(..., description="Log level")
    logger: str = Field(..., description="Logger name")
    message: str = Field(..., description="Log message")
    component: Optional[str] = Field(None, description="Component that generated the log")
    function: Optional[str] = Field(None, description="Function that generated the log")
    line_number: Optional[int] = Field(None, description="Line number")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Additional log data")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class LogFilters(BaseModel):
    """Log filtering parameters"""
    level: Optional[LogLevel] = Field(None, description="Minimum log level")
    start_time: Optional[datetime] = Field(None, description="Start time filter")
    end_time: Optional[datetime] = Field(None, description="End time filter")
    logger: Optional[str] = Field(None, description="Logger name filter")
    module: Optional[str] = Field(None, description="Module name filter")
    search_term: Optional[str] = Field(None, description="Search term in message")
    limit: int = Field(100, ge=1, le=1000, description="Maximum number of logs to return")
    offset: int = Field(0, ge=0, description="Offset for pagination")


class SystemLogsResponse(BaseModel):
    """System logs response - Implements U-FR10"""
    logs: List[LogEntry] = Field(..., description="List of log entries")
    total_count: int = Field(..., ge=0, description="Total number of matching logs")
    filtered_count: int = Field(..., ge=0, description="Number of logs after filtering")
    filters_applied: LogFilters = Field(..., description="Applied filters")
    has_more: bool = Field(..., description="Whether there are more logs available")


# System Management Schemas
class ManualDataCollectionRequest(BaseModel):
    """Manual data collection trigger request"""
    stock_symbols: Optional[List[str]] = Field(None, description="Specific stocks to collect (all if empty)")
    include_sentiment: bool = Field(True, description="Whether to include sentiment analysis")
    force_refresh: bool = Field(False, description="Whether to force refresh even if recent data exists")
    days_back: Optional[int] = Field(1, ge=1, le=30, description="Number of days to look back for data collection")
    data_sources: Optional[List[str]] = Field(
        None, 
        description="Specific data sources to use. Options: hackernews, finnhub, newsapi, gdelt, yfinance. If empty, all sources are used."
    )


class ManualDataCollectionResponse(BaseModel):
    """Manual data collection response"""
    success: bool
    job_id: Optional[str] = Field(None, description="Background job ID if applicable")
    estimated_completion: Optional[str] = Field(None, description="Estimated completion time")
    symbols_targeted: List[str] = Field(..., description="Symbols that will be processed")
    message: str