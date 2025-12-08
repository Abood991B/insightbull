"""
Admin Routes
============

FastAPI routes for admin panel functionality.
Implements FYP Report Phase 8 requirements U-FR6 through U-FR10.

This module provides REST API endpoints for:
- Model accuracy evaluation (U-FR6)
- API configuration management (U-FR7) 
- Stock watchlist management (U-FR8)
- Data storage settings (U-FR9)
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_, or_, delete, inspect
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.utils.timezone import utc_now, to_naive_utc
from uuid import uuid4
from app.data_access.database import get_db
from app.presentation.dependencies.auth_dependencies import get_current_admin_user as get_current_admin
from app.infrastructure.security.auth_service import AdminUser
from app.infrastructure.log_system import LogSystem

logger = LogSystem()
from app.presentation.schemas.admin_schemas import (
    # Model accuracy schemas
    ModelAccuracyResponse,
    
    # API configuration schemas  
    APIConfigResponse, APIKeyUpdateRequest as APIConfigUpdateRequest,
    
    # Watchlist schemas
    WatchlistResponse, WatchlistUpdateRequest, WatchlistUpdateResponse,
    
    # Storage schemas
    StorageSettingsResponse, StorageMetrics,
    
    # System logs schemas
    SystemLogsResponse, LogFilters, LogLevel
)
from enum import Enum

# LogLevel enum imported from schemas
from app.service.admin_service import AdminService
from app.service.storage_service import StorageManager
from app.service.system_service import SystemService
from app.infrastructure.log_system import get_logger
from app.presentation.controllers.oauth_controller import router as oauth_router



logger = get_logger()
router = APIRouter(prefix="/admin", tags=["admin"])

# Include OAuth routes
router.include_router(oauth_router)


# Health check endpoint for admin services
@router.get("/health")
async def admin_health():
    """Admin service health check"""
    return {"status": "healthy", "service": "admin"}


# Manual data collection endpoint
@router.post("/data-collection/manual")
async def trigger_manual_collection(
    request_data: Optional[Dict[str, Any]] = None,
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Trigger manual FULL PIPELINE execution for specified symbols.
    This runs: Collection → Preprocessing → Sentiment Analysis → Storage
    """
    try:
        from app.business.pipeline import DataPipeline, PipelineConfig, DateRange
        from datetime import datetime, timedelta
        
        logger.info("Admin triggering manual FULL PIPELINE execution", admin_user=current_admin.email)
        
        # Get symbols from request or use dynamic active watchlist
        if request_data and request_data.get("symbols"):
            symbols = request_data["symbols"]
        else:
            from app.data_access.models import StocksWatchlist
            from sqlalchemy import select
            symbols = []
            try:
                result = await db.execute(
                    select(StocksWatchlist.symbol).where(StocksWatchlist.is_active == True)
                )
                symbols = [row[0] for row in result.all()]
            except Exception:
                symbols = []
            if not symbols:
                symbols = ["AAPL", "GOOGL", "MSFT"]  # final fallback only if DB empty
        
        # Get timeframe from request (default to 1 day)
        days_back = 1
        if request_data and request_data.get("days_back"):
            try:
                days_back = int(request_data["days_back"])
                if days_back < 1: days_back = 1
                if days_back > 30: days_back = 30  # Cap at 30 days to prevent overload
            except (ValueError, TypeError):
                days_back = 1

        # Create pipeline config for FULL PIPELINE execution
        config = PipelineConfig(
            symbols=symbols,
            date_range=DateRange(
                start_date=to_naive_utc(utc_now() - timedelta(days=days_back)),
                end_date=to_naive_utc(utc_now())
            ),
            max_items_per_symbol=50,  # Increased for more comprehensive data collection
            include_hackernews=True,
            include_finnhub=True,
            include_newsapi=True,
            include_marketaux=True,
            parallel_collectors=True
        )
        
        # Execute COMPLETE pipeline (Collection → Processing → Sentiment → Storage)
        pipeline = DataPipeline()
        result = await pipeline.run_pipeline(config)
        
        # Build comprehensive response
        response = {
            "status": "success" if result.status.value == "completed" else "partial",
            "message": f"Full pipeline execution completed for {len(symbols)} symbols",
            "pipeline_id": result.pipeline_id,
            "execution_summary": {
                "symbols_processed": len(symbols),
                "data_collection": {
                    "total_items_collected": result.total_items_collected,
                    "collectors_used": len(result.collector_stats),
                    "successful_collectors": len([s for s in result.collector_stats if s.success])
                },
                "text_processing": {
                    "items_processed": result.total_items_processed,
                    "processing_success_rate": f"{(result.total_items_processed / result.total_items_collected * 100):.1f}%" if result.total_items_collected > 0 else "0%"
                },
                "sentiment_analysis": {
                    "items_analyzed": result.total_items_analyzed,
                    "analysis_success_rate": f"{(result.total_items_analyzed / result.total_items_processed * 100):.1f}%" if result.total_items_processed > 0 else "0%"
                },
                "data_storage": {
                    "items_stored": result.total_items_stored or 0,
                    "storage_success_rate": f"{((result.total_items_stored or 0) / result.total_items_analyzed * 100):.1f}%" if result.total_items_analyzed > 0 else "0%"
                }
            },
            "execution_time_seconds": result.execution_time,
            "timestamp": utc_now().isoformat()
        }
        
        # Add warning if pipeline didn't complete successfully
        if result.status.value != "completed":
            response["warning"] = f"Pipeline status: {result.status.value}"
            if result.error_message:
                response["error_details"] = result.error_message
        
        logger.info(f"Full pipeline execution completed", 
                   pipeline_id=result.pipeline_id,
                   collected=result.total_items_collected,
                   processed=result.total_items_processed,
                   analyzed=result.total_items_analyzed,
                   stored=result.total_items_stored)
        
        return response
        
    except Exception as e:
        logger.error("Error during manual full pipeline execution", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute full pipeline: {str(e)}"
        )


# U-FR6: Model Accuracy Evaluation
@router.get("/models/accuracy")
async def get_model_accuracy(
    view_type: str = "overall",  # "overall" or "latest"
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get sentiment model accuracy metrics.
    Implements U-FR6: View Model Accuracy
    
    Args:
        view_type: "overall" for all-time metrics, "latest" for latest pipeline run
    
    Returns comprehensive accuracy metrics for FinBERT sentiment model
    with per-source breakdown and AI verification statistics.
    """
    try:
        logger.info("Admin requesting model accuracy metrics", 
                   admin_user=current_admin.email, 
                   view_type=view_type)
        
        admin_service = AdminService(db)
        if view_type == "latest":
            accuracy_data = await admin_service.get_latest_pipeline_accuracy_metrics()
        else:
            accuracy_data = await admin_service.get_model_accuracy_metrics()
        
        return accuracy_data
        
    except Exception as e:
        logger.error("Error retrieving model accuracy", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve model accuracy metrics"
        )


@router.get("/models/benchmark")
async def get_benchmark_results(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get ground truth benchmark evaluation results.
    
    Returns comprehensive accuracy metrics from evaluating ProsusAI/finbert
    against the Financial PhraseBank dataset (5,057 labeled sentences).
    This provides real accuracy, precision, recall, and F1-score metrics.
    """
    try:
        logger.info("Admin requesting benchmark results", admin_user=current_admin.email)
        
        from app.service.benchmark_service import get_benchmark_service
        
        benchmark_service = get_benchmark_service()
        results = benchmark_service.get_last_benchmark()
        dataset_info = benchmark_service.get_dataset_info()
        
        if results:
            return {
                "has_benchmark": True,
                "benchmark": results,
                "dataset_info": dataset_info
            }
        else:
            return {
                "has_benchmark": False,
                "message": "No benchmark results found. Click 'Run Benchmark' to evaluate model accuracy.",
                "dataset_info": dataset_info
            }
        
    except Exception as e:
        logger.error("Error retrieving benchmark results", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve benchmark results"
        )


@router.post("/models/benchmark/run")
async def run_benchmark_evaluation(
    force: bool = Query(False, description="Force re-run even if results exist"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Run benchmark evaluation of ProsusAI/finbert against Financial PhraseBank.
    
    This evaluates the sentiment model on ground truth data (5,057 samples)
    and stores the results for display on the Model Accuracy page.
    """
    try:
        logger.info("Admin triggering benchmark evaluation", 
                   admin_user=current_admin.email,
                   force=force)
        
        from app.service.benchmark_service import get_benchmark_service
        
        benchmark_service = get_benchmark_service()
        
        # Check if dataset is available
        if not benchmark_service.check_dataset_available():
            dataset_info = benchmark_service.get_dataset_info()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Benchmark dataset not available: {dataset_info.get('message', 'Unknown error')}"
            )
        
        # Check if results already exist
        if not force:
            existing = benchmark_service.get_last_benchmark()
            if existing:
                return {
                    "success": True,
                    "message": "Benchmark results already exist. Use force=true to re-run.",
                    "results": existing
                }
        
        # Run benchmark evaluation
        result = await benchmark_service.run_benchmark()
        
        # Convert dataclass to dict
        from dataclasses import asdict
        results_dict = asdict(result)
        
        logger.info("Benchmark evaluation completed", 
                   accuracy=f"{result.accuracy:.1%}",
                   dataset_size=result.dataset_size)
        
        return {
            "success": True,
            "message": "Benchmark evaluation completed successfully",
            "results": results_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error running benchmark evaluation", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run benchmark evaluation: {str(e)}"
        )


# U-FR7: API Configuration Management
@router.get("/config/apis")
async def get_api_configuration(
    db: AsyncSession = Depends(get_db), 
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get current API configuration settings.
    Implements U-FR7: Manage API Configuration
    
    Returns encrypted API keys status and configuration for all data sources.
    """
    try:
        logger.info("Admin requesting API configuration", admin_user=current_admin.email)
        
        admin_service = AdminService(db)
        config_data = await admin_service.get_api_configuration_status()
        
        return config_data
        
    except Exception as e:
        logger.error("Error retrieving API configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve API configuration"
        )


@router.get("/models/sentiment-engine-metrics")
async def get_sentiment_engine_metrics(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get real-time sentiment engine performance metrics.
    Phase 5: Deployment & Monitoring
    
    Returns comprehensive statistics on:
    - Model usage (FinBERT-Tone unified model)
    - Processing performance (speed, success rate)
    - Current configuration
    - Per-model statistics
    """
    try:
        logger.info("Admin requesting sentiment engine metrics", admin_user=current_admin.email)
        
        from app.service.sentiment_processing import get_sentiment_engine
        
        # Get sentiment engine singleton
        engine = get_sentiment_engine()
        
        # Get engine statistics
        stats = engine.get_stats()
        config = engine.config
        
        # Calculate per-model metrics (now unified to FinBERT-Tone)
        finbert_usage = stats.model_usage.get("FinBERT-Tone", 0) + stats.model_usage.get("FinBERT", 0)
        total_usage = finbert_usage if finbert_usage > 0 else 1  # Prevent division by zero
        
        # Get database sentiment counts for accuracy context
        from app.data_access.models import SentimentData
        total_sentiments = await db.scalar(
            select(func.count()).select_from(SentimentData)
        )
        
        # Count all sentiment records (now all processed by FinBERT-Tone)
        finbert_count = await db.scalar(
            select(func.count())
            .select_from(SentimentData)
        )
        
        # Calculate successful and failed analyses
        successful_analyses = stats.total_texts_processed - stats.error_count
        failed_analyses = stats.error_count
        
        return {
            "engine_status": {
                "initialized": engine.is_initialized,
                "available_models": ["FinBERT-Tone"],
                "total_models": 1,
                "engine_health": "healthy" if stats.success_rate > 90 else "degraded" if stats.success_rate > 70 else "critical"
            },
            "overall_performance": {
                "total_texts_processed": stats.total_texts_processed,
                "successful_analyses": successful_analyses,
                "failed_analyses": failed_analyses,
                "success_rate_percent": round(stats.success_rate, 2),
                "avg_processing_time_ms": round(stats.avg_processing_time * 1000, 2),
                "total_processing_time_sec": round(stats.total_processing_time, 2)
            },
            "model_configuration": {
                "finbert_enabled": config.enable_finbert,
                "ensemble_finbert_enabled": config.use_ensemble_finbert,
                "finbert_calibration_enabled": config.finbert_use_calibration,
                "finbert_type": "FinBERT-Tone (yiyanghkust/finbert-tone)",
                "default_batch_size": config.default_batch_size
            },
            "model_usage": {
                "finbert": {
                    "session_count": finbert_usage,
                    "database_count": finbert_count or 0,
                    "percentage_of_total": 100.0,
                    "used_for": ["All Sources: HackerNews, FinHub, Marketaux, NewsAPI, GDELT"],
                    "model_type": "FinBERT-Tone",
                    "features": [
                        "95.7% average confidence across all sources",
                        "Financial domain pre-training",
                        "Advanced preprocessing (entity recognition)",
                        "Number standardization ($1.5B → $1,500,000,000)",
                        "16 financial abbreviation expansions (P/E, EPS, ROI, etc.)",
                        "Company name normalization (AAPL → Apple)",
                        "Intelligent truncation (keyword-based)",
                        "Noise filtering (ads, promotional content)",
                        "GPU acceleration support"
                    ]
                }
            },
            "database_statistics": {
                "total_sentiment_records": total_sentiments or 0,
                "finbert_records": finbert_count or 0
            },
            "timestamp": utc_now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error retrieving sentiment engine metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve sentiment engine metrics: {str(e)}"
        )


# U-FR7 (continued): API Configuration Management
@router.put("/config/apis")
async def update_api_configuration(
    config_update: APIConfigUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Update API configuration settings.
    Implements U-FR7: Manage API Configuration
    
    Updates API keys and configuration for data collection sources.
    """
    try:
        logger.info("Admin updating API configuration", 
                   admin_user=current_admin.email,
                   service=config_update.service)
        
        admin_service = AdminService(db)
        update_result = await admin_service.update_api_configuration(config_update)
        
        return update_result
    
    except ValueError as e:
        # Validation errors (e.g., invalid API key)
        logger.warning("API key validation failed", error=str(e), service=config_update.service)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
        
    except Exception as e:
        logger.error("Error updating API configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API configuration"
        )


# ============================================================================
# COLLECTOR ENABLE/DISABLE CONFIGURATION
# ============================================================================

@router.get("/config/collectors")
async def get_collector_configuration(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get current collector enable/disable configuration.
    
    Returns the enabled/disabled status for all data collectors,
    allowing admins to control which collectors run in the pipeline.
    """
    try:
        logger.info("Admin requesting collector configuration", admin_user=current_admin.email)
        
        from app.service.collector_config_service import get_collector_config_service
        config_service = get_collector_config_service()
        
        return config_service.get_all_collector_configs()
        
    except Exception as e:
        logger.error("Error retrieving collector configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve collector configuration"
        )


@router.put("/config/collectors/{collector_name}")
async def toggle_collector(
    collector_name: str,
    enabled: bool = Query(..., description="Whether to enable or disable the collector"),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Enable or disable a specific data collector.
    
    This allows admins to temporarily disable collectors without removing
    API keys, useful for:
    - Troubleshooting data collection issues
    - Reducing API usage
    - Temporarily disabling problematic sources
    """
    try:
        logger.info(
            f"Admin {'enabling' if enabled else 'disabling'} collector: {collector_name}",
            admin_user=current_admin.email,
            collector=collector_name,
            enabled=enabled
        )
        
        from app.service.collector_config_service import get_collector_config_service
        config_service = get_collector_config_service()
        
        result = config_service.set_collector_enabled(
            collector_name=collector_name,
            enabled=enabled,
            updated_by=current_admin.email
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error toggling collector", error=str(e), collector=collector_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle collector: {str(e)}"
        )


# ============================================================================
# AI SERVICES MANAGEMENT
# ============================================================================

@router.put("/config/ai-services/{service_name}/toggle")
async def toggle_ai_service(
    service_name: str,
    enabled: bool = Query(..., description="Whether to enable or disable the AI service"),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Enable or disable a specific AI service (e.g., Gemini for sentiment verification).
    
    This allows admins to control AI-powered features without removing API keys.
    """
    try:
        logger.info(
            f"Admin {'enabling' if enabled else 'disabling'} AI service: {service_name}",
            admin_user=current_admin.email,
            service=service_name,
            enabled=enabled
        )
        
        from app.service.collector_config_service import get_collector_config_service
        config_service = get_collector_config_service()
        
        result = config_service.set_ai_service_enabled(
            service_name=service_name,
            enabled=enabled,
            updated_by=current_admin.email
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error toggling AI service", error=str(e), service=service_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle AI service: {str(e)}"
        )


@router.put("/config/ai-services/{service_name}/settings")
async def update_ai_service_settings(
    service_name: str,
    verification_mode: Optional[str] = Query(None, description="Verification mode: none, low_confidence, low_confidence_and_neutral, all"),
    confidence_threshold: Optional[float] = Query(None, ge=0.0, le=1.0, description="Confidence threshold (0.0-1.0)"),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Update AI service settings like verification mode and confidence threshold.
    
    Verification modes:
    - none: No AI verification (ML only)
    - low_confidence: Verify only low-confidence predictions
    - low_confidence_and_neutral: Verify low-confidence + all neutral predictions (recommended)
    - all: Verify all predictions (highest accuracy, highest cost)
    """
    try:
        logger.info(
            f"Admin updating AI service settings: {service_name}",
            admin_user=current_admin.email,
            service=service_name,
            verification_mode=verification_mode,
            confidence_threshold=confidence_threshold
        )
        
        from app.service.collector_config_service import get_collector_config_service
        config_service = get_collector_config_service()
        
        result = config_service.update_ai_service_settings(
            service_name=service_name,
            verification_mode=verification_mode,
            confidence_threshold=confidence_threshold,
            updated_by=current_admin.email
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error("Error updating AI service settings", error=str(e), service=service_name)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update AI service settings: {str(e)}"
        )


@router.get("/config/ai-services")
async def get_ai_services_config(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """Get all AI services configuration."""
    try:
        from app.service.collector_config_service import get_collector_config_service
        config_service = get_collector_config_service()
        
        return config_service.get_all_ai_services()
        
    except Exception as e:
        logger.error("Error retrieving AI services configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve AI services configuration"
        )


# U-FR8: Stock Watchlist Management
@router.get("/watchlist", response_model=WatchlistResponse)
async def get_stock_watchlist(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> WatchlistResponse:
    """
    Get current stock watchlist.
    Implements U-FR8: Update Stock Watchlist
    
    Returns the complete list of stocks being monitored for sentiment analysis.
    """
    try:
        logger.info("Admin requesting stock watchlist", admin_user=current_admin.email)
        
        admin_service = AdminService(db)
        watchlist_data = await admin_service.get_stock_watchlist()
        
        logger.info(f"Watchlist data retrieved: {len(watchlist_data.stocks)} stocks")
        
        return watchlist_data
        
    except Exception as e:
        logger.error("Error retrieving stock watchlist", error=str(e))
        import traceback
        logger.error("Full traceback", traceback=traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve stock watchlist: {str(e)}"
        )


@router.put("/watchlist", response_model=WatchlistUpdateResponse)
async def update_stock_watchlist(
    watchlist_update: WatchlistUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> WatchlistUpdateResponse:
    """
    Update stock watchlist configuration.
    Implements U-FR8: Update Stock Watchlist
    
    Add or remove stocks from the monitoring watchlist.
    """
    try:
        logger.info("Admin updating stock watchlist", 
                   admin_user=current_admin.email,
                   action=watchlist_update.action,
                   symbol=watchlist_update.symbol)
        
        admin_service = AdminService(db)
        update_result = await admin_service.update_stock_watchlist(watchlist_update)
        
        return update_result
        
    except Exception as e:
        logger.error("Error updating stock watchlist", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update stock watchlist"
        )


@router.get("/stocks/search")
async def search_stock_symbols(
    q: Optional[str] = Query(None, description="Search query for stock symbols"),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, str]:
    """
    Search available stock symbols.
    Returns a dictionary of symbol -> company name pairs.
    """
    try:
        from app.service.watchlist_service import WatchlistService
        
        if q:
            # Search for matching symbols
            results = WatchlistService.search_symbols(q)
            # Limit results to prevent overwhelming the frontend
            limited_results = dict(list(results.items())[:20])
            return limited_results
        else:
            # Return all available symbols (first 50 for performance)
            all_symbols = WatchlistService.get_all_symbols()
            limited_results = dict(list(all_symbols.items())[:50])
            return limited_results
            
    except Exception as e:
        logger.error("Error searching stock symbols", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search stock symbols"
        )


# U-FR9: Data Storage Management
@router.get("/storage")
async def get_storage_metrics(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get current storage usage metrics.
    Implements U-FR9: Manage Data Storage
    
    Returns comprehensive storage statistics and usage information.
    """
    try:
        logger.info("Admin requesting storage metrics", admin_user=current_admin.email)
        
        storage_manager = StorageManager(db)
        metrics = await storage_manager.calculate_storage_metrics()
        
        # Import the required schemas
        from app.presentation.schemas.admin_schemas import StorageSettingsResponse, RetentionPolicy
        from datetime import datetime, timedelta
        
        # Create a default retention policy for now
        default_retention = RetentionPolicy(
            sentiment_data_days=90,
            price_data_days=365,
            log_data_days=30,
            auto_cleanup_enabled=True
        )
        
        # Get actual database file size information
        import os
        
        try:
            # Get actual database file size - backend/data/insight_stock.db
            db_file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "data", "insight_stock.db")
            if os.path.exists(db_file_path):
                db_size_bytes = os.path.getsize(db_file_path)
                db_size_gb = db_size_bytes / (1024 ** 3)
                db_size_mb = db_size_bytes / (1024 ** 2)
            else:
                db_size_gb = 0.0
                db_size_mb = 0.0
            
            # Set reasonable limits for database growth (configurable in production)
            max_db_size_gb = 5.0  # 5GB limit for database
            available_space_gb = max_db_size_gb - db_size_gb
            usage_percentage = (db_size_gb / max_db_size_gb) * 100 if max_db_size_gb > 0 else 0
            
        except Exception as e:
            logger.warning(f"Could not get database file size: {e}, using estimates")
            # Fallback to estimates based on record counts
            db_size_mb = metrics.storage_size_mb
            db_size_gb = db_size_mb / 1024
            max_db_size_gb = 5.0
            available_space_gb = max_db_size_gb - db_size_gb
            usage_percentage = (db_size_gb / max_db_size_gb) * 100 if max_db_size_gb > 0 else 0
        
        return {
            "current_usage": {
                "total_size_gb": round(db_size_gb, 2),
                "total_size_mb": round(db_size_mb, 2),
                "available_space_gb": round(available_space_gb, 2),
                "usage_percentage": round(usage_percentage, 2)
            },
            "total_records": metrics.total_records,
            "sentiment_records": metrics.sentiment_records,
            "stock_price_records": metrics.stock_price_records,
            "oldest_record": metrics.oldest_record.isoformat() if metrics.oldest_record else None,
            "newest_record": metrics.newest_record.isoformat() if metrics.newest_record else None,
            "storage_health": "healthy" if usage_percentage < 80 else "warning" if usage_percentage < 95 else "critical"
        }
        
    except Exception as e:
        logger.error("Error retrieving storage metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage metrics"
        )


@router.post("/storage/optimize")
async def optimize_database(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Perform database optimization operations.
    Implements U-FR9: Manage Data Storage
    
    Runs database maintenance tasks like VACUUM, index rebuilding, etc.
    """
    try:
        logger.info("Admin starting database optimization", admin_user=current_admin.email)
        
        storage_manager = StorageManager(db)
        optimization_results = await storage_manager.optimize_database()
        
        return {
            "success": True,
            "message": "Database optimization completed successfully",
            "results": optimization_results
        }
        
    except Exception as e:
        logger.error("Error during database optimization", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to optimize database"
        )


@router.post("/storage/backup")
async def create_backup(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Create a manual backup of the database.
    Implements U-FR9: Manage Data Storage
    
    Creates a backup of all critical data.
    """
    try:
        logger.info("Administrator initiated manual backup", admin_user=current_admin.email)
        
        storage_manager = StorageManager(db)
        backup_metadata = await storage_manager.create_data_backup()
        
        return {
            "success": True,
            "message": "Backup created successfully",
            "backup_info": backup_metadata
        }
        
    except Exception as e:
        logger.error("Error creating backup", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create backup"
        )



# U-FR10: System Logs Viewing
@router.get("/logs", response_model=SystemLogsResponse)
async def get_system_logs(
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    component: Optional[str] = Query(None, description="Filter by component"),
    time_period: Optional[str] = Query(None, description="Time period filter (1h, 6h, 24h, 7d, 30d)"),
    search_term: Optional[str] = Query(None, description="Search term in message"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of logs to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> SystemLogsResponse:
    """
    Get system logs with filtering options.
    Implements U-FR10: View System Logs
    
    Returns filtered system logs for monitoring and debugging.
    """
    try:
        logger.info("Admin requesting system logs", 
                   admin_user=current_admin.email,
                   filters={"level": level, "component": component, "time_period": time_period, "limit": limit})
        
        # Parse time period to start_time and end_time
        start_time = None
        end_time = None
        
        if time_period:
            now = utc_now()
            
            time_mappings = {
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6), 
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30)
            }
            
            if time_period in time_mappings:
                start_time = now - time_mappings[time_period]
                end_time = now
        
        # Parse custom date filters if provided
        if start_date:
            try:
                start_time = datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                pass
                
        if end_date:
            try:
                end_time = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            except ValueError:
                pass
        
        admin_service = AdminService(db)
        filters = LogFilters(
            level=level,
            start_time=start_time,
            end_time=end_time,
            logger=search_term,  # Use search_term for logger filtering
            module=component,  # Map component to module (which filters by component column)
            search_term=search_term,
            limit=limit,
            offset=offset
        )
        logs_data = await admin_service.get_system_logs(filters)
        
        return logs_data
        
    except Exception as e:
        logger.error("Error retrieving system logs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system logs"
        )



@router.get("/logs/download")
async def download_system_logs(
    level: Optional[LogLevel] = Query(None, description="Filter by log level"),
    component: Optional[str] = Query(None, description="Filter by component"),
    start_date: Optional[str] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date filter (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Download system logs as CSV file - Simplified version.
    """
    try:
        from fastapi.responses import StreamingResponse
        import csv
        import io
        from datetime import datetime as dt
        from app.data_access.models import SystemLog
        
        logger.info("Administrator initiated system logs export", admin_user=current_admin.email)
        
        # Build direct database query
        query = select(SystemLog).order_by(SystemLog.timestamp.desc())
        
        # Apply filters directly
        if level:
            query = query.where(SystemLog.level == level.value)
        if component:
            query = query.where(SystemLog.component.ilike(f"%{component}%"))
        if start_date:
            start_time = dt.strptime(start_date, "%Y-%m-%d")
            query = query.where(SystemLog.timestamp >= start_time)
        if end_date:
            end_time = dt.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
            query = query.where(SystemLog.timestamp <= end_time)
        
        # Limit for export
        query = query.limit(10000)
        
        # Execute query
        result = await db.execute(query)
        logs = result.scalars().all()
        
        logger.info(f"Retrieved {len(logs)} logs for download")
        
        # Create CSV content
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(['Timestamp', 'Level', 'Component', 'Logger', 'Message', 'Function', 'Line'])
        
        # Handle empty logs case
        if not logs:
            writer.writerow(['No logs found', '', '', '', 'No logs match the current filters', '', ''])
        else:
            # Write log entries directly from database models
            for log in logs:
                writer.writerow([
                    log.timestamp.isoformat() if log.timestamp else '',
                    log.level or '',
                    log.component or '',
                    log.logger or '',
                    log.message or '',
                    log.function or '',
                    str(log.line_number) if log.line_number else ''
                ])
        
        output.seek(0)
        
        # Generate filename with timestamp using utc_now()
        filename = f"system_logs_{utc_now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode('utf-8')),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error("Error downloading system logs", error=str(e), traceback=error_details)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to download system logs: {str(e)}"
        )


@router.delete("/logs/clear")
async def clear_system_logs(
    confirm: bool = Query(False, description="Confirmation required to clear logs"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Clear all system logs with confirmation.
    Implements U-FR10: Clear System Logs
    """
    try:
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Confirmation required. Set confirm=true to proceed."
            )
        
        logger.warning("Admin clearing all system logs", 
                      admin_user=current_admin.email,
                      action="CLEAR_ALL_LOGS")
        
        # Import here to avoid circular imports
        from app.data_access.models import SystemLog
        from sqlalchemy import delete, select, func
        
        # Count logs before deletion
        count_result = await db.execute(select(func.count()).select_from(SystemLog))
        logs_count = count_result.scalar()
        
        # Delete all logs
        delete_stmt = delete(SystemLog)
        await db.execute(delete_stmt)
        await db.commit()
        
        logger.warning(f"System logs cleared by admin", 
                      admin_user=current_admin.email,
                      logs_deleted=logs_count,
                      component="admin_service")
        
        return {
            "success": True,
            "message": f"Successfully cleared {logs_count} system logs",
            "logs_deleted": logs_count,
            "timestamp": utc_now().isoformat()
        }
        
    except Exception as e:
        logger.error("Error clearing system logs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear system logs"
        )


@router.get("/system/status")
async def get_system_status(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive system status information.
    
    Returns overall system health, service status, and operational metrics.
    """
    try:
        logger.info("Admin requesting system status", admin_user=current_admin.email)
        
        system_service = SystemService(db)
        status_data = await system_service.get_system_status()
        
        return status_data
        
    except Exception as e:
        logger.error("Error retrieving system status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )




@router.post("/data-collection/trigger")
async def trigger_manual_collection(
    stock_symbols: Optional[List[str]] = None,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Manually trigger data collection process.
    
    Initiates immediate data collection for specified stocks or default watchlist.
    """
    try:
        logger.info("Admin triggering manual data collection", 
                   admin_user=current_admin.email,
                   stock_symbols=stock_symbols)
        
        system_service = SystemService(db)
        collection_result = await system_service.trigger_data_collection(stock_symbols)
        
        return collection_result
        
    except Exception as e:
        logger.error("Error triggering data collection", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to trigger data collection"
        )


# ============================================================================
# SCHEDULER MANAGEMENT
# ============================================================================

@router.get("/scheduler/jobs")
async def get_scheduled_jobs(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get all scheduled jobs and their status.
    
    Returns comprehensive information about all scheduled jobs including
    their configuration, status, and execution history.
    """
    try:
        logger.info("Admin requesting scheduled jobs", admin_user=current_admin.email)
        
        from app.business.scheduler import Scheduler
        scheduler = Scheduler()
        
        jobs = scheduler.list_jobs()
        
        # Convert jobs to serializable format
        jobs_data = []
        for job in jobs:
            jobs_data.append({
                "job_id": job.job_id,
                "name": job.name,
                "job_type": job.job_type,
                "trigger_config": job.trigger_config,
                "parameters": job.parameters,
                "status": job.status.value,
                "created_at": job.created_at.isoformat(),
                "last_run": job.last_run.isoformat() if job.last_run else None,
                "next_run": job.next_run.isoformat() if job.next_run else None,
                "run_count": job.run_count,
                "error_count": job.error_count,
                "last_error": job.last_error,
                "enabled": job.enabled
            })
        
        return {
            "jobs": jobs_data,
            "total_jobs": len(jobs_data),
            "scheduler_running": scheduler._is_running
        }
        
    except Exception as e:
        logger.error("Error retrieving scheduled jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve scheduled jobs"
        )


@router.post("/scheduler/jobs")
async def create_scheduled_job(
    job_config: Dict[str, Any],
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Create a new scheduled job.
    
    Args:
        job_config: Job configuration including type, schedule, and parameters
    """
    try:
        logger.info("Admin creating scheduled job", 
                   admin_user=current_admin.email,
                   job_type=job_config.get("job_type"))
        
        from app.business.scheduler import Scheduler
        scheduler = Scheduler()
        
        job_type = job_config.get("job_type")
        name = job_config.get("name")
        cron_expression = job_config.get("cron_expression")
        symbols = job_config.get("symbols", [])
        
        # Log the job creation attempt
        logger.info(f"Admin {current_admin.email} creating scheduled job", 
                   job_type=job_type, name=name, cron=cron_expression)
        
        if not all([job_type, name, cron_expression]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields: job_type, name, cron_expression"
            )
        
        # Create job based on type
        if job_type == "data_collection":
            lookback_days = job_config.get("lookback_days", 1)
            job_id = await scheduler.schedule_data_collection(
                name=name,
                cron_expression=cron_expression,
                symbols=symbols,
                lookback_days=lookback_days
            )
        elif job_type == "sentiment_analysis":
            job_id = await scheduler.schedule_sentiment_analysis(
                name=name,
                cron_expression=cron_expression,
                symbols=symbols
            )
        elif job_type == "full_pipeline":
            lookback_days = job_config.get("lookback_days", 7)
            job_id = await scheduler.schedule_full_pipeline(
                name=name,
                cron_expression=cron_expression,
                symbols=symbols,
                lookback_days=lookback_days
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown job type: {job_type}"
            )
        
        # Log successful job creation to system logs
        logger.info(f"Scheduled job '{name}' created successfully by admin {current_admin.email}", 
                   job_id=job_id, job_type=job_type, symbols=symbols)
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Scheduled job '{name}' created successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error creating scheduled job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create scheduled job"
        )


@router.put("/scheduler/jobs/{job_id}")
async def update_scheduled_job(
    job_id: str,
    action: str = Query(..., description="Action to perform: enable, disable, or cancel"),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Update a scheduled job (enable, disable, cancel).
    
    Args:
        job_id: ID of the job to update
        action: Action to perform (enable, disable, cancel)
    """
    try:
        logger.info("Admin updating scheduled job", 
                   admin_user=current_admin.email,
                   job_id=job_id,
                   action=action)
        
        from app.business.scheduler import Scheduler
        scheduler = Scheduler()
        
        if action == "enable":
            success = scheduler.enable_job(job_id)
            message = "Job enabled successfully"
        elif action == "disable":
            success = scheduler.disable_job(job_id)
            message = "Job disabled successfully"
        elif action == "cancel":
            success = scheduler.cancel_job(job_id)
            message = "Job cancelled successfully"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown action: {action}"
            )
        
        if not success:
            logger.warning(f"Failed to {action} job {job_id} - job not found", 
                          admin_user=current_admin.email)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        # Log successful job operation
        logger.info(f"Job {job_id} {action}d successfully by admin {current_admin.email}", 
                   job_id=job_id, action=action)
        
        return {
            "success": True,
            "message": message
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating scheduled job", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update scheduled job"
        )


@router.get("/scheduler/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get detailed status of a specific scheduled job.
    
    Args:
        job_id: ID of the job to query
    """
    try:
        logger.info("Admin requesting job status", 
                   admin_user=current_admin.email,
                   job_id=job_id)
        
        from app.business.scheduler import Scheduler
        scheduler = Scheduler()
        
        job = scheduler.get_job_status(job_id)
        
        if not job:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        return {
            "job_id": job.job_id,
            "name": job.name,
            "job_type": job.job_type,
            "trigger_config": job.trigger_config,
            "parameters": job.parameters,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "last_run": job.last_run.isoformat() if job.last_run else None,
            "next_run": job.next_run.isoformat() if job.next_run else None,
            "run_count": job.run_count,
            "error_count": job.error_count,
            "last_error": job.last_error,
            "enabled": job.enabled
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving job status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve job status"
        )


@router.post("/scheduler/refresh")
async def refresh_scheduled_jobs(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Refresh all scheduled jobs with updated watchlist.
    
    This is useful when the watchlist is updated and scheduled jobs
    need to be refreshed to use the new stock symbols.
    """
    try:
        logger.info("Admin refreshing scheduled jobs", admin_user=current_admin.email)
        
        from app.business.scheduler import Scheduler
        scheduler = Scheduler()
        
        await scheduler.refresh_scheduled_jobs()
        
        return {
            "success": True,
            "message": "Scheduled jobs refreshed successfully"
        }
        
    except Exception as e:
        logger.error("Error refreshing scheduled jobs", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve real-time price service status"
        )


# ============================================================================
# DATA COLLECTOR HEALTH MONITORING
# ============================================================================

@router.get("/collectors/health")
async def get_collector_health(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get real-time health status of all data collectors with actual collection stats.
    
    Returns information about each collector's operational status,
    items collected from last pipeline run, and any errors encountered.
    """
    try:
        logger.info("Admin requesting collector health", admin_user=current_admin.email)
        
        from app.data_access.models import NewsArticle, HackerNewsPost
        from sqlalchemy import select, func
        from datetime import timedelta
        from app.infrastructure.security.api_key_manager import SecureAPIKeyLoader
        from fastapi import status as http_status
        
        collector_health = []
        
        # Load API keys to check configuration
        try:
            key_loader = SecureAPIKeyLoader()
            keys = key_loader.load_api_keys()
        except Exception as e:
            logger.warning(f"Could not load API keys for health check: {e}")
            keys = {}
        
        # Get data from last 24 hours to show recent activity
        last_24_hours = utc_now() - timedelta(hours=24)
        
        # Query SentimentData to get actual processed counts by source
        # This is more accurate than querying raw tables because:
        # 1. It reflects items that successfully passed through the pipeline
        # 2. It uses created_at (processing time) rather than published_at (which might be old)
        from app.data_access.models import SentimentData
        
        sentiment_counts = await db.execute(
            select(SentimentData.source, func.count(SentimentData.id))
            .where(SentimentData.created_at >= last_24_hours)
            .group_by(SentimentData.source)
        )
        
        # Convert to dictionary for easy lookup
        # source is stored as lowercase in SentimentData
        counts_by_source = {row[0].lower(): row[1] for row in sentiment_counts.all()}
        
        hn_count = counts_by_source.get('hackernews', 0)
        finnhub_count = counts_by_source.get('finnhub', 0)
        newsapi_count = counts_by_source.get('newsapi', 0)
        marketaux_count = counts_by_source.get('marketaux', 0)
        gdelt_count = counts_by_source.get('gdelt', 0)
        
        # Define collectors with their configuration requirements
        collectors = [
            {
                "name": "HackerNews",
                "internal_name": "hackernews",
                "source": "community",
                "items_collected": hn_count,
                "api_key_required": False,  # HackerNews API is free and unlimited
                "api_key_configured": True  # Always available
            },
            {
                "name": "GDELT",
                "internal_name": "gdelt",
                "source": "news",
                "items_collected": gdelt_count,
                "api_key_required": False,  # GDELT API is free and unlimited
                "api_key_configured": True  # Always available
            },
            {
                "name": "FinHub",
                "internal_name": "finnhub",
                "source": "news",
                "items_collected": finnhub_count,
                "api_key_required": True,
                "api_key_configured": bool(keys.get('finnhub_api_key'))
            },
            {
                "name": "NewsAPI",
                "internal_name": "newsapi",
                "source": "news",
                "items_collected": newsapi_count,
                "api_key_required": True,
                "api_key_configured": bool(keys.get('news_api_key'))
            },
            {
                "name": "MarketAux",
                "internal_name": "marketaux",
                "source": "news",
                "items_collected": marketaux_count,
                "api_key_required": True,
                "api_key_configured": bool(keys.get('marketaux_api_key'))
            }
        ]
        
        # Build health info for each collector
        for collector in collectors:
            collector_status = "operational" if collector["api_key_configured"] else "not_configured"
            
            health_info = {
                "name": collector["name"],
                "status": collector_status,
                "source": collector["source"],
                "requires_api_key": collector["api_key_required"],
                "configured": collector["api_key_configured"],
                "last_run": None,
                "items_collected": collector["items_collected"],
                "error": None if collector["api_key_configured"] else "API key not configured"
            }
            
            collector_health.append(health_info)
        
        # Calculate summary stats
        operational_count = len([c for c in collector_health if c["status"] == "operational"])
        total_count = len(collector_health)
        coverage_percentage = round((operational_count / total_count) * 100) if total_count > 0 else 0
        total_items = sum(c["items_collected"] for c in collector_health)
        
        return {
            "collectors": collector_health,
            "summary": {
                "total_collectors": total_count,
                "operational": operational_count,
                "not_configured": len([c for c in collector_health if c["status"] == "not_configured"]),
                "error": len([c for c in collector_health if c["status"] == "error"]),
                "coverage_percentage": coverage_percentage,
                "total_items_24h": total_items
            }
        }
        
    except Exception as e:
        logger.error("Error retrieving collector health", error=str(e))
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve collector health status: {str(e)}"
        )


@router.post("/realtime-price-service/start")
async def start_realtime_price_service(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Start the real-time price service.
    """
    try:
        logger.info("Admin starting real-time price service", admin_user=current_admin.email)
        
        from app.service.price_service import price_service
        
        if price_service.is_running:
            return {
                "success": False,
                "message": "Real-time price service is already running"
            }
        
        await price_service.start()
        
        logger.info(f"Real-time price service started by admin {current_admin.email}")
        
        return {
            "success": True,
            "message": "Real-time price service started successfully"
        }
        
    except Exception as e:
        logger.error("Error starting real-time price service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start real-time price service"
        )


# ============================================================================
# REAL-TIME PRICE SERVICE MANAGEMENT  
# ============================================================================

@router.get("/realtime-price-service/status")
async def get_realtime_price_service_status(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get real-time price service status and configuration.
    
    Returns comprehensive information about the background price fetching service.
    """
    try:
        logger.info("Admin requesting real-time price service status", admin_user=current_admin.email)
        
        from app.service.price_service import price_service
        
        status_data = price_service.get_service_status()
        
        return {
            "success": True,
            "service_status": status_data
        }
        
    except Exception as e:
        logger.error("Error retrieving real-time price service status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve real-time price service status"
        )


@router.post("/realtime-price-service/stop")
async def stop_realtime_price_service(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Stop the real-time price service.
    """
    try:
        logger.info("Admin stopping real-time price service", admin_user=current_admin.email)
        
        from app.service.price_service import price_service
        
        if not price_service.is_running:
            return {
                "success": False,
                "message": "Real-time price service is not running"
            }
        
        await price_service.stop()
        
        logger.info(f"Real-time price service stopped by admin {current_admin.email}")
        
        return {
            "success": True,
            "message": "Real-time price service stopped successfully"
        }
        
    except Exception as e:
        logger.error("Error stopping real-time price service", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to stop real-time price service"
        )


@router.put("/realtime-price-service/config")
async def update_realtime_price_service_config(
    config_update: Dict[str, Any],
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Update real-time price service configuration.
    
    Args:
        config_update: Configuration updates (e.g., {"update_interval": 60})
    """
    try:
        logger.info("Admin updating real-time price service config", 
                   admin_user=current_admin.email,
                   config=config_update)
        
        from app.service.price_service import price_service
        
        success = await price_service.update_configuration(config_update)
        
        if success:
            logger.info(f"Real-time price service config updated by admin {current_admin.email}", 
                       config=config_update)
            return {
                "success": True,
                "message": "Real-time price service configuration updated successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to update configuration - invalid settings"
            }
        
    except Exception as e:
        logger.error("Error updating real-time price service config", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update real-time price service configuration"
        )


@router.post("/realtime-price-service/test-fetch")
async def test_price_fetch(
    symbol: Optional[str] = Query(None, description="Test price fetch for specific symbol"),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Test price fetching for a specific symbol or all watchlist symbols.
    """
    try:
        logger.info("Admin testing price fetch", 
                   admin_user=current_admin.email,
                   symbol=symbol)
        
        from app.service.price_service import price_service
        
        if symbol:
            # Test single symbol
            price_data = await price_service.fetch_single_stock_price(symbol)
            if price_data:
                return {
                    "success": True,
                    "message": f"Successfully fetched price for {symbol}",
                    "data": price_data
                }
            else:
                return {
                    "success": False,
                    "message": f"Failed to fetch price for {symbol}"
                }
        else:
            # Test fetching all watchlist symbols
            await price_service._fetch_and_update_prices()
            return {
                "success": True,
                "message": "Successfully triggered price fetch for all watchlist symbols"
            }
        
    except Exception as e:
        logger.error("Error testing price fetch", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to test price fetch"
        )


@router.post("/realtime-price-service/update-market-caps")
async def update_market_caps(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Fetch and update market cap information for all watchlist stocks.
    This should be run once to populate market cap data.
    """
    try:
        logger.info("Admin triggering market cap update", admin_user=current_admin.email)
        
        from app.service.price_service import price_service
        
        # Trigger market cap update
        result = await price_service.fetch_and_update_market_caps()
        
        if result.get('success'):
            return {
                "success": True,
                "message": f"Market cap update completed: {result['updated_count']}/{result['total_stocks']} stocks updated",
                "data": {
                    "updated_count": result['updated_count'],
                    "total_stocks": result['total_stocks'],
                    "failed_symbols": result.get('failed_symbols', [])
                }
            }
        else:
            return {
                "success": False,
                "message": result.get('message', 'Failed to update market caps')
            }
        
    except Exception as e:
        logger.error("Error updating market caps", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update market caps: {str(e)}"
        )


@router.get("/realtime-price-service/debug")
async def debug_price_service(
    current_admin: AdminUser = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get detailed debug information about the price service.
    """
    try:
        logger.info("Admin requesting price service debug info", admin_user=current_admin.email)
        
        from app.service.price_service import price_service
        from app.data_access.models import StocksWatchlist, StockPrice
        from sqlalchemy import select, func, desc
        
        # Get service status
        service_status = price_service.get_service_status()
        
        # Get watchlist stocks
        watchlist_result = await db.execute(
            select(StocksWatchlist).where(StocksWatchlist.is_active == True)
        )
        watchlist_stocks = watchlist_result.scalars().all()
        
        # Get latest price records
        latest_prices_result = await db.execute(
            select(StockPrice.symbol, StockPrice.price, StockPrice.price_timestamp)
            .order_by(StockPrice.price_timestamp.desc())
            .limit(10)
        )
        latest_prices = latest_prices_result.all()
        
        # Get total price records count
        total_prices_result = await db.execute(select(func.count()).select_from(StockPrice))
        total_price_records = total_prices_result.scalar()
        
        # Check market hours
        is_market_open = price_service.is_market_hours()
        
        # Test a single stock price fetch
        test_symbol = "AAPL"
        test_price_data = None
        try:
            test_price_data = await price_service.fetch_single_stock_price(test_symbol)
        except Exception as e:
            test_price_data = {"error": str(e)}
        
        return {
            "service_status": service_status,
            "market_status": {
                "is_open": is_market_open,
                "current_time_et": utc_now().isoformat()
            },
            "watchlist": {
                "total_stocks": len(watchlist_stocks),
                "symbols": [stock.symbol for stock in watchlist_stocks]
            },
            "database": {
                "total_price_records": total_price_records,
                "latest_prices": [
                    {
                        "symbol": p.symbol,
                        "price": float(p.price),
                        "timestamp": p.price_timestamp.isoformat()
                    }
                    for p in latest_prices
                ]
            },
            "test_fetch": {
                "symbol": test_symbol,
                "result": test_price_data
            }
        }
        
    except Exception as e:
        logger.error("Error getting price service debug info", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get debug information"
        )


@router.get("/market/status")
async def get_market_status(
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive market status including current period, next open/close times.
    
    Returns:
        - is_open: Boolean indicating if market is currently open
        - current_period: One of 'pre-market', 'market-hours', 'after-hours', 'overnight', 'weekend'
        - current_time_et: Current time in Eastern timezone
        - next_open: Next market open time (if closed)
        - next_close: Next market close time (if open)
        - market_hours: Standard market hours configuration
    """
    try:
        import pytz
        from datetime import datetime, timedelta
        
        logger.info("Admin requesting market status", admin_user=current_admin.email)
        
        # Get current time in Eastern timezone
        eastern = pytz.timezone('US/Eastern')
        now = datetime.now(pytz.UTC).astimezone(eastern)
        
        weekday = now.weekday()  # 0=Monday, 6=Sunday
        hour = now.hour
        minute = now.minute
        
        # Determine current period
        is_open = False
        current_period = 'overnight'
        
        if weekday >= 5:  # Weekend
            current_period = 'weekend'
        else:  # Weekday
            if hour >= 4 and (hour < 9 or (hour == 9 and minute < 30)):
                current_period = 'pre-market'
            elif (hour == 9 and minute >= 30) or (9 < hour < 16):
                current_period = 'market-hours'
                is_open = True
            elif 16 <= hour < 20:
                current_period = 'after-hours'
            else:  # 20:00 - 04:00
                current_period = 'overnight'
        
        # Calculate next market open
        next_open = None
        next_close = None
        
        if is_open:
            # Market is open, calculate next close (4 PM today)
            next_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        else:
            # Market is closed, calculate next open (9:30 AM)
            days_ahead = 0
            
            if weekday == 6:  # Sunday
                days_ahead = 1
            elif weekday == 5:  # Saturday
                days_ahead = 2
            elif hour >= 16:  # After market close on weekday
                if weekday == 4:  # Friday
                    days_ahead = 3  # Skip to Monday
                else:
                    days_ahead = 1
            # else: before market open today, days_ahead = 0
            
            next_open = now.replace(hour=9, minute=30, second=0, microsecond=0) + timedelta(days=days_ahead)
        
        return {
            "is_open": is_open,
            "current_period": current_period,
            "current_time_et": now.isoformat(),
            "weekday": weekday,
            "next_open": next_open.isoformat() if next_open else None,
            "next_close": next_close.isoformat() if next_close else None,
            "market_hours": {
                "pre_market": "04:00 - 09:30 ET",
                "market_hours": "09:30 - 16:00 ET",
                "after_hours": "16:00 - 20:00 ET",
                "overnight": "20:00 - 04:00 ET"
            }
        }
        
    except Exception as e:
        logger.error("Error getting market status", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get market status"
        )


# ============================================================================
# DATABASE INSPECTION
# ============================================================================

@router.get("/database/schema")
async def get_database_schema(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get database schema information including tables, columns, and relationships.
    
    Returns comprehensive information about the database structure.
    """
    try:
        logger.info("Admin requesting database schema", admin_user=current_admin.email)
        
        from app.data_access.models import (
            StocksWatchlist, SentimentData, StockPrice, NewsArticle,
            HackerNewsPost, SystemLog
        )
        
        # Get database inspector
        def get_table_info(sync_session):
            inspector = inspect(sync_session.bind)
            return inspector.get_table_names()
        
        # Get all table names
        table_names = await db.run_sync(get_table_info)
        
        tables_info = {}
        
        # Define model mapping
        model_mapping = {
            'stocks_watchlist': StocksWatchlist,
            'sentiment_data': SentimentData,
            'stock_prices': StockPrice,
            'news_articles': NewsArticle,
            'hackernews_posts': HackerNewsPost,
            'system_logs': SystemLog
        }
        
        for table_name in table_names:
            if table_name in model_mapping:
                model = model_mapping[table_name]
                
                # Get columns info
                def get_columns(sync_session):
                    inspector = inspect(sync_session.bind)
                    return inspector.get_columns(table_name)
                
                def get_foreign_keys(sync_session):
                    inspector = inspect(sync_session.bind)
                    return inspector.get_foreign_keys(table_name)
                
                def get_indexes(sync_session):
                    inspector = inspect(sync_session.bind)
                    return inspector.get_indexes(table_name)
                
                columns = await db.run_sync(get_columns)
                foreign_keys = await db.run_sync(get_foreign_keys)
                indexes = await db.run_sync(get_indexes)
                
                # Get record count
                from sqlalchemy import select, func
                count_result = await db.execute(select(func.count()).select_from(model))
                record_count = count_result.scalar()
                
                tables_info[table_name] = {
                    'model_name': model.__name__,
                    'record_count': record_count,
                    'columns': [
                        {
                            'name': col['name'],
                            'type': str(col['type']),
                            'nullable': col['nullable'],
                            'primary_key': col.get('primary_key', False),
                            'default': str(col.get('default')) if col.get('default') else None
                        }
                        for col in columns
                    ],
                    'foreign_keys': [
                        {
                            'constrained_columns': fk['constrained_columns'],
                            'referred_table': fk['referred_table'],
                            'referred_columns': fk['referred_columns']
                        }
                        for fk in foreign_keys
                    ],
                    'indexes': [
                        {
                            'name': idx['name'],
                            'column_names': idx['column_names'],
                            'unique': idx['unique']
                        }
                        for idx in indexes
                    ]
                }
        
        return {
            'database_name': 'insight_stock.db',
            'total_tables': len(tables_info),
            'tables': tables_info
        }
        
    except Exception as e:
        logger.error("Error retrieving database schema", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve database schema: {str(e)}"
        )


@router.get("/database/tables/{table_name}/data")
async def get_table_data(
    table_name: str,
    limit: int = Query(100, ge=1, le=1000, description="Number of records to return"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get data from a specific table with pagination.
    
    Args:
        table_name: Name of the table to query
        limit: Maximum number of records to return
        offset: Number of records to skip
    """
    try:
        logger.info("Admin requesting table data", 
                   admin_user=current_admin.email,
                   table_name=table_name,
                   limit=limit,
                   offset=offset)
        
        from app.data_access.models import (
            StocksWatchlist, SentimentData, StockPrice, NewsArticle,
            HackerNewsPost, SystemLog
        )
        from sqlalchemy import select, func, text
        
        # Define model mapping
        model_mapping = {
            'stocks_watchlist': StocksWatchlist,
            'sentiment_data': SentimentData,
            'stock_prices': StockPrice,
            'news_articles': NewsArticle,
            'hackernews_posts': HackerNewsPost,
            'system_logs': SystemLog
        }
        
        if table_name not in model_mapping:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Table {table_name} not found"
            )
        
        model = model_mapping[table_name]
        
        # Get total count
        count_result = await db.execute(select(func.count()).select_from(model))
        total_count = count_result.scalar()
        
        # Get data with pagination
        query = select(model).offset(offset).limit(limit)
        
        # Add ordering by id or created_at if available
        if hasattr(model, 'created_at'):
            query = query.order_by(model.created_at.desc())
        elif hasattr(model, 'id'):
            query = query.order_by(model.id.desc())
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        # Convert records to dictionaries
        data = []
        for record in records:
            record_dict = {}
            for column in model.__table__.columns:
                value = getattr(record, column.name)
                # Convert datetime objects to ISO strings
                if hasattr(value, 'isoformat'):
                    value = value.isoformat()
                # Convert UUID objects to strings
                elif hasattr(value, 'hex'):
                    value = str(value)
                record_dict[column.name] = value
            data.append(record_dict)
        
        return {
            'table_name': table_name,
            'total_records': total_count,
            'returned_records': len(data),
            'offset': offset,
            'limit': limit,
            'data': data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error retrieving table data", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve table data"
        )


@router.get("/database/stats")
async def get_database_statistics(
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get comprehensive database statistics.
    
    Returns record counts, storage usage, and other database metrics.
    """
    try:
        logger.info("Admin requesting database statistics", admin_user=current_admin.email)
        
        from app.data_access.models import (
            StocksWatchlist, SentimentData, StockPrice, NewsArticle,
            HackerNewsPost, SystemLog
        )
        from sqlalchemy import select, func
        import os
        
        # Get record counts for each table
        stats = {}
        
        models = {
            'stocks_watchlist': StocksWatchlist,
            'sentiment_data': SentimentData,
            'stock_prices': StockPrice,
            'news_articles': NewsArticle,
            'hackernews_posts': HackerNewsPost,
            'system_logs': SystemLog
        }
        
        total_records = 0
        for table_name, model in models.items():
            count_result = await db.execute(select(func.count()).select_from(model))
            count = count_result.scalar()
            stats[table_name] = count
            total_records += count
        
        # Get database file size
        import os
        db_file_path = "./data/insight_stock.db"
        file_size_bytes = 0
        if os.path.exists(db_file_path):
            file_size_bytes = os.path.getsize(db_file_path)
        else:
            # Try alternative paths
            alternative_paths = ["../data/insight_stock.db", "data/insight_stock.db", "insight_stock.db"]
            for alt_path in alternative_paths:
                if os.path.exists(alt_path):
                    db_file_path = alt_path
                    file_size_bytes = os.path.getsize(alt_path)
                    break
        
        file_size_mb = file_size_bytes / (1024 * 1024)
        file_size_gb = file_size_bytes / (1024 * 1024 * 1024)
        
        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = to_naive_utc(utc_now() - timedelta(days=1))
        
        recent_sentiment = await db.execute(
            select(func.count()).select_from(SentimentData)
            .where(SentimentData.created_at >= yesterday)
        )
        recent_sentiment_count = recent_sentiment.scalar()
        
        recent_logs = await db.execute(
            select(func.count()).select_from(SystemLog)
            .where(SystemLog.timestamp >= yesterday)
        )
        recent_logs_count = recent_logs.scalar()
        
        return {
            'total_records': total_records,
            'table_counts': stats,
            'file_size': {
                'bytes': file_size_bytes,
                'mb': round(file_size_mb, 2),
                'gb': round(file_size_gb, 4)
            },
            'recent_activity': {
                'sentiment_records_24h': recent_sentiment_count,
                'log_entries_24h': recent_logs_count
            },
            'database_file': db_file_path
        }
        
    except Exception as e:
        logger.error("Error retrieving database statistics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve database statistics"
        )





# Database cleanup utilities removed - using unified Stock table structure