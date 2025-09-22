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
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, func, desc, and_, or_, delete, inspect
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
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
    APIConfigResponse, APIKeyUpdateRequest as APIConfigUpdateRequest, APIKeyUpdateResponse as APIConfigUpdateResponse,
    
    # Watchlist schemas
    WatchlistResponse, WatchlistUpdateRequest, WatchlistUpdateResponse,
    
    # Storage schemas
    StorageSettingsResponse, StorageMetrics, StorageSettingsUpdateRequest as RetentionPolicyRequest, StorageSettingsUpdateResponse as RetentionPolicyResponse,
    
    # System logs schemas
    SystemLogsResponse, LogFilters
)
from enum import Enum

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING" 
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
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
    current_admin: AdminUser = Depends(get_current_admin)
):
    """
    Trigger manual data collection for specified symbols.
    Implements manual pipeline execution for admin users.
    """
    try:
        from app.business.pipeline import DataPipeline, PipelineConfig, DateRange
        from datetime import datetime, timedelta
        
        logger.info("Admin triggering manual data collection", admin_user=current_admin.email)
        
        # Get symbols from request or use default
        symbols = request_data.get("symbols", ["AAPL", "GOOGL", "MSFT"]) if request_data else ["AAPL", "GOOGL", "MSFT"]
        
        # Create pipeline config
        config = PipelineConfig(
            symbols=symbols,
            date_range=DateRange(
                start_date=datetime.now() - timedelta(days=1),
                end_date=datetime.now()
            ),
            max_items_per_symbol=10,
            include_reddit=True,
            include_finnhub=True,
            include_newsapi=True,
            include_marketaux=True
        )
        
        # Execute pipeline
        pipeline = DataPipeline()
        result = await pipeline.run_pipeline(config)
        
        return {
            "status": "success",
            "message": "Manual data collection completed",
            "result": {
                "total_items_analyzed": result.total_items_analyzed,
                "total_items_stored": result.total_items_stored,
                "execution_time": result.execution_time
            }
        }
        
    except Exception as e:
        logger.error("Error during manual data collection", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute manual data collection"
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
    
    Returns comprehensive accuracy metrics for all sentiment models
    including VADER and FinBERT performance statistics.
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
        
    except Exception as e:
        logger.error("Error updating API configuration", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update API configuration"
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
            # Get actual database file size
            db_file_path = "./data/insight_stock.db"
            if os.path.exists(db_file_path):
                db_size_bytes = os.path.getsize(db_file_path)
                db_size_gb = db_size_bytes / (1024 ** 3)
            else:
                db_size_gb = 0.0
            
            # Set reasonable limits for database growth (configurable in production)
            max_db_size_gb = 5.0  # 5GB limit for database
            available_space_gb = max_db_size_gb - db_size_gb
            usage_percentage = (db_size_gb / max_db_size_gb) * 100
            
        except Exception as e:
            logger.warning(f"Could not get database file size: {e}, using estimates")
            # Fallback to estimates based on record counts
            db_size_gb = metrics.storage_size_mb / 1024
            max_db_size_gb = 5.0
            available_space_gb = max_db_size_gb - db_size_gb
            usage_percentage = (db_size_gb / max_db_size_gb) * 100
        
        return {
            "current_usage": {
                "total_size_gb": round(db_size_gb, 2),
                "available_space_gb": round(available_space_gb, 2),
                "usage_percentage": round(usage_percentage, 2)
            },
            "retention_policy": {
                "sentiment_data_days": default_retention.sentiment_data_days,
                "stock_price_days": default_retention.price_data_days,
                "log_files_days": default_retention.log_data_days,
                "backup_retention_days": 30
            },
            "auto_cleanup": default_retention.auto_cleanup_enabled,
            "total_records": metrics.total_records,
            "storage_health": "healthy" if usage_percentage < 80 else "warning" if usage_percentage < 95 else "critical"
        }
        
    except Exception as e:
        logger.error("Error retrieving storage metrics", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve storage metrics"
        )


@router.put("/storage", response_model=RetentionPolicyResponse)
async def update_retention_policy(
    retention_policy: RetentionPolicyRequest,
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> RetentionPolicyResponse:
    """
    Update data retention policy.
    Implements U-FR9: Manage Data Storage
    
    Configure automatic data cleanup and retention policies.
    """
    try:
        logger.info("Admin updating retention policy", 
                   admin_user=current_admin.email,
                   policy=retention_policy.dict())
        
        # Convert StorageSettingsUpdateRequest to RetentionPolicy
        from app.presentation.schemas.admin_schemas import RetentionPolicy
        retention_policy_obj = RetentionPolicy(
            sentiment_data_days=retention_policy.sentiment_data_days or 30,
            price_data_days=retention_policy.price_data_days or 90,
            log_data_days=retention_policy.log_data_days or 30,
            auto_cleanup_enabled=retention_policy.auto_cleanup_enabled or True
        )
        
        logger.info("Converted retention policy", policy=retention_policy_obj.dict())
        
        storage_manager = StorageManager(db)
        cleanup_stats = await storage_manager.apply_retention_policy(retention_policy_obj, force_cleanup=True)
        
        logger.info("Retention policy applied", cleanup_stats=cleanup_stats)
        
        return {
            "success": True,
            "message": "Retention policy applied successfully",
            "cleanup_statistics": cleanup_stats,
            "updated_settings": {
                "metrics": {
                    "total_records": cleanup_stats.get("total_records_remaining", 0),
                    "storage_size_mb": 0.0,
                    "sentiment_records": cleanup_stats.get("sentiment_records_remaining", 0),
                    "stock_price_records": cleanup_stats.get("price_records_remaining", 0),
                    "oldest_record": None,
                    "newest_record": None
                },
                "retention_policy": retention_policy_obj.dict(),
                "backup_enabled": False,
                "last_cleanup": datetime.utcnow(),
                "next_cleanup": None
            }
        }
        
    except Exception as e:
        logger.error("Error updating retention policy", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update retention policy"
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
                   filters={"level": level, "component": component, "limit": limit})
        
        admin_service = AdminService(db)
        filters = LogFilters(
            level=level,
            module=component,  # Map component to module (which filters by component column)
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
        
        # Generate filename with timestamp
        filename = f"system_logs_{dt.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
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
            "timestamp": datetime.utcnow().isoformat()
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
            RedditPost, SystemLog
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
            'reddit_posts': RedditPost,
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
            RedditPost, SystemLog
        )
        from sqlalchemy import select, func, text
        
        # Define model mapping
        model_mapping = {
            'stocks_watchlist': StocksWatchlist,
            'sentiment_data': SentimentData,
            'stock_prices': StockPrice,
            'news_articles': NewsArticle,
            'reddit_posts': RedditPost,
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
            RedditPost, SystemLog
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
            'reddit_posts': RedditPost,
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
        yesterday = datetime.utcnow() - timedelta(days=1)
        
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