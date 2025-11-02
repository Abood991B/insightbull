"""
Pipeline Management API Routes
==============================

Admin endpoints for managing data collection pipeline.
Includes pipeline execution, status monitoring, and configuration.

Following FYP Report specification:
- Admin pipeline management (Admin-only access)
- Pipeline monitoring and statistics  
- Manual pipeline triggers
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from app.utils.timezone import utc_now, to_naive_utc

from ...business.pipeline import DataPipeline, PipelineConfig, PipelineResult, PipelineStatus
from ...business.processor import ProcessingConfig
from ...infrastructure.collectors.base_collector import DateRange
from ...infrastructure.rate_limiter import RateLimitHandler
from ...data_access.repositories.sentiment_repository import SentimentDataRepository
from ...data_access.repositories.stock_repository import StockRepository
from ..deps import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/admin/pipeline", tags=["Admin Pipeline Management"])

# Global pipeline instance (in production, this would be dependency injected)
_pipeline_instance: Optional[DataPipeline] = None


# Pydantic Models
class PipelineConfigRequest(BaseModel):
    """Request model for pipeline configuration"""
    symbols: List[str] = Field(..., min_length=1, max_length=10, description="Stock symbols to analyze")
    days_back: int = Field(default=7, ge=1, le=30, description="Number of days to collect data for")
    max_items_per_symbol: int = Field(default=100, ge=10, le=500, description="Maximum items per symbol")
    include_reddit: bool = Field(default=True, description="Include Reddit data collection")
    include_finnhub: bool = Field(default=True, description="Include FinHub data collection") 
    include_newsapi: bool = Field(default=True, description="Include NewsAPI data collection")
    include_marketaux: bool = Field(default=True, description="Include MarketAux data collection")
    include_comments: bool = Field(default=True, description="Include Reddit comments")
    parallel_collectors: bool = Field(default=True, description="Run collectors in parallel")


class ProcessingConfigRequest(BaseModel):
    """Request model for text processing configuration"""
    remove_html: bool = Field(default=True, description="Remove HTML tags")
    remove_urls: bool = Field(default=True, description="Remove URLs")
    remove_mentions: bool = Field(default=True, description="Remove @mentions")
    remove_hashtags: bool = Field(default=False, description="Remove hashtags")
    normalize_whitespace: bool = Field(default=True, description="Normalize whitespace")
    min_length: int = Field(default=10, ge=5, le=100, description="Minimum text length")
    max_length: int = Field(default=5000, ge=100, le=10000, description="Maximum text length")
    expand_contractions: bool = Field(default=True, description="Expand contractions")


class APIKeysRequest(BaseModel):
    """Request model for API keys configuration"""
    reddit: Optional[Dict[str, str]] = Field(default=None, description="Reddit API configuration")
    finnhub: Optional[str] = Field(default=None, description="FinHub API key")
    newsapi: Optional[str] = Field(default=None, description="NewsAPI key") 
    marketaux: Optional[str] = Field(default=None, description="MarketAux API key")


class PipelineStatusResponse(BaseModel):
    """Response model for pipeline status"""
    status: str
    current_result: Optional[Dict[str, Any]]
    available_collectors: List[str]
    rate_limiter_status: Dict[str, Dict[str, Any]]


class PipelineResultResponse(BaseModel):
    """Response model for pipeline execution result"""
    pipeline_id: str
    status: str
    start_time: datetime
    end_time: Optional[datetime]
    execution_time: float
    total_items_collected: int
    total_items_processed: int
    total_items_stored: int
    success_rate: float
    collector_stats: List[Dict[str, Any]]
    processing_stats: Dict[str, Any]
    error_message: Optional[str]


def get_pipeline() -> DataPipeline:
    """Get or create the global pipeline instance"""
    global _pipeline_instance
    
    if _pipeline_instance is None:
        rate_limiter = RateLimitHandler()
        _pipeline_instance = DataPipeline(rate_limiter=rate_limiter)
    
    return _pipeline_instance


# API Endpoints

@router.post("/configure", response_model=Dict[str, str])
async def configure_pipeline(
    api_keys: APIKeysRequest,
    pipeline: DataPipeline = Depends(get_pipeline)
):
    """
    Configure pipeline with API keys.
    
    **Admin only** - Configure external API keys for data collectors.
    """
    try:
        # Convert API keys to expected format
        api_keys_dict = {}
        
        if api_keys.reddit:
            api_keys_dict["reddit"] = api_keys.reddit
        
        if api_keys.finnhub:
            api_keys_dict["finnhub"] = api_keys.finnhub
        
        if api_keys.newsapi:
            api_keys_dict["newsapi"] = api_keys.newsapi
        
        if api_keys.marketaux:
            api_keys_dict["marketaux"] = api_keys.marketaux
        
        # Configure collectors
        pipeline.configure_collectors(api_keys_dict)
        
        return {
            "status": "success",
            "message": f"Configured {len(api_keys_dict)} API keys",
            "configured_collectors": list(api_keys_dict.keys())
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Configuration failed: {str(e)}")


@router.post("/run", response_model=Dict[str, str])
async def run_pipeline(
    config: PipelineConfigRequest,
    processing_config: Optional[ProcessingConfigRequest] = None,
    background_tasks: BackgroundTasks = None,
    pipeline: DataPipeline = Depends(get_pipeline)
):
    """
    Start a data collection pipeline run.
    
    **Admin only** - Trigger manual pipeline execution with custom configuration.
    """
    try:
        # Check if pipeline is already running
        if pipeline.current_status == PipelineStatus.RUNNING:
            raise HTTPException(
                status_code=409, 
                detail="Pipeline is already running. Cancel current run first."
            )
        
        # Build date range
        end_date = to_naive_utc(utc_now())
        start_date = end_date - timedelta(days=config.days_back)
        date_range = DateRange(start_date=start_date, end_date=end_date)
        
        # Build processing config
        proc_config = None
        if processing_config:
            proc_config = ProcessingConfig(
                remove_html=processing_config.remove_html,
                remove_urls=processing_config.remove_urls,
                remove_mentions=processing_config.remove_mentions,
                remove_hashtags=processing_config.remove_hashtags,
                normalize_whitespace=processing_config.normalize_whitespace,
                min_length=processing_config.min_length,
                max_length=processing_config.max_length,
                expand_contractions=processing_config.expand_contractions
            )
        
        # Build pipeline config
        pipeline_config = PipelineConfig(
            symbols=config.symbols,
            date_range=date_range,
            max_items_per_symbol=config.max_items_per_symbol,
            include_reddit=config.include_reddit,
            include_finnhub=config.include_finnhub,
            include_newsapi=config.include_newsapi,
            include_marketaux=config.include_marketaux,
            include_comments=config.include_comments,
            parallel_collectors=config.parallel_collectors,
            processing_config=proc_config
        )
        
        # Start pipeline in background
        if background_tasks:
            background_tasks.add_task(pipeline.run_pipeline, pipeline_config)
            return {
                "status": "started",
                "message": "Pipeline execution started in background",
                "symbols": config.symbols,
                "date_range": f"{start_date.date()} to {end_date.date()}"
            }
        else:
            # Synchronous execution (not recommended for production)
            result = await pipeline.run_pipeline(pipeline_config)
            return {
                "status": "completed",
                "pipeline_id": result.pipeline_id,
                "items_collected": str(result.total_items_collected),
                "execution_time": f"{result.execution_time:.2f}s"
            }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Pipeline execution failed: {str(e)}")


@router.get("/status", response_model=PipelineStatusResponse)
async def get_pipeline_status(pipeline: DataPipeline = Depends(get_pipeline)):
    """
    Get current pipeline status.
    
    **Admin only** - View current pipeline execution status and statistics.
    """
    try:
        status = pipeline.get_status()
        return PipelineStatusResponse(**status)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.get("/result", response_model=Optional[PipelineResultResponse])
async def get_pipeline_result(pipeline: DataPipeline = Depends(get_pipeline)):
    """
    Get the result of the last pipeline execution.
    
    **Admin only** - View detailed results from the most recent pipeline run.
    """
    try:
        if not pipeline.current_result:
            return None
        
        result = pipeline.current_result
        
        return PipelineResultResponse(
            pipeline_id=result.pipeline_id,
            status=result.status.value,
            start_time=result.start_time,
            end_time=result.end_time,
            execution_time=result.execution_time,
            total_items_collected=result.total_items_collected,
            total_items_processed=result.total_items_processed,
            total_items_stored=result.total_items_stored,
            success_rate=result.success_rate,
            collector_stats=[stat.__dict__ for stat in result.collector_stats],
            processing_stats=result.processing_stats,
            error_message=result.error_message
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get result: {str(e)}")


@router.post("/cancel", response_model=Dict[str, str])
async def cancel_pipeline(pipeline: DataPipeline = Depends(get_pipeline)):
    """
    Cancel the currently running pipeline.
    
    **Admin only** - Stop pipeline execution gracefully.
    """
    try:
        if pipeline.current_status != PipelineStatus.RUNNING:
            raise HTTPException(
                status_code=409,
                detail="No pipeline is currently running"
            )
        
        pipeline.cancel_pipeline()
        
        return {
            "status": "cancelled",
            "message": "Pipeline cancellation requested"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel pipeline: {str(e)}")


@router.get("/health", response_model=Dict[str, Any])
async def pipeline_health_check(pipeline: DataPipeline = Depends(get_pipeline)):
    """
    Perform health check on pipeline components.
    
    **Admin only** - Check the health of all pipeline components and dependencies.
    """
    try:
        health_status = await pipeline.health_check()
        return health_status
        
    except Exception as e:
        return {
            "pipeline": "unhealthy",
            "error": str(e),
            "timestamp": utc_now().isoformat()
        }


@router.get("/collectors", response_model=Dict[str, Any])
async def get_collector_info(pipeline: DataPipeline = Depends(get_pipeline)):
    """
    Get information about available data collectors.
    
    **Admin only** - View collector configuration and capabilities.
    """
    try:
        collector_info = {}
        
        for name, collector in pipeline._collectors.items():
            collector_info[name] = {
                "name": name,
                "source": collector.source.value,
                "requires_api_key": collector.requires_api_key,
                "configured": collector.api_key is not None
            }
        
        return {
            "collectors": collector_info,
            "total_collectors": len(collector_info),
            "configured_collectors": len([c for c in collector_info.values() if c["configured"]])
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get collector info: {str(e)}")


@router.get("/rate-limits", response_model=Dict[str, Dict[str, Any]])
async def get_rate_limit_status(pipeline: DataPipeline = Depends(get_pipeline)):
    """
    Get rate limit status for all API sources.
    
    **Admin only** - Monitor API rate limit usage and remaining quotas.
    """
    try:
        return pipeline.rate_limiter.get_all_status()
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get rate limits: {str(e)}")