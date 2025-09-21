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
from sqlalchemy import select, func, desc, and_, or_, delete
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
    db: AsyncSession = Depends(get_db),
    current_admin: AdminUser = Depends(get_current_admin)
) -> Dict[str, Any]:
    """
    Get sentiment model accuracy metrics.
    Implements U-FR6: View Model Accuracy
    
    Returns comprehensive accuracy metrics for all sentiment models
    including VADER and FinBERT performance statistics.
    """
    try:
        logger.info("Admin requesting model accuracy metrics", admin_user=current_admin.email)
        
        admin_service = AdminService(db)
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
            "compression_enabled": False,
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
        
        storage_manager = StorageManager(db)
        cleanup_stats = await storage_manager.apply_retention_policy(retention_policy)
        
        return RetentionPolicyResponse(
            success=True,
            applied_policy=retention_policy,
            cleanup_statistics=cleanup_stats,
            timestamp=datetime.utcnow()
        )
        
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