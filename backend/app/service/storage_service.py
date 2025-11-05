"""
Storage Management Service
=========================

Handles data storage operations, cleanup, and retention policies.
Implements FYP Report Phase 8 storage management requirements.
"""

from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, func, text, select
import asyncio
import structlog
from app.utils.timezone import utc_now, to_naive_utc

from app.data_access.models import StocksWatchlist, SentimentData, StockPrice, SystemLog, NewsArticle, RedditPost
from app.infrastructure.log_system import get_logger
from app.presentation.schemas.admin_schemas import StorageMetrics, RetentionPolicy


logger = get_logger()


class StorageManager:
    """
    Service for managing data storage, cleanup, and retention policies.
    
    Features:
    - Data retention policy enforcement
    - Automated cleanup operations
    - Storage metrics calculation
    - Backup coordination
    - Data archival
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.logger = logger
    
    async def calculate_storage_metrics(self) -> StorageMetrics:
        """
        Calculate current storage usage metrics.
        """
        try:
            self.logger.info("Calculating storage metrics")
            
            # Get sentiment data count
            sentiment_count_result = await self.db.execute(
                select(func.count(SentimentData.id))
            )
            sentiment_count = sentiment_count_result.scalar() or 0
            
            # Get stock price count
            price_count_result = await self.db.execute(
                select(func.count(StockPrice.id))
            )
            price_count = price_count_result.scalar() or 0
            
            # Get news articles count
            news_count_result = await self.db.execute(
                select(func.count(NewsArticle.id))
            )
            news_count = news_count_result.scalar() or 0
            
            # Get reddit posts count
            reddit_count_result = await self.db.execute(
                select(func.count(RedditPost.id))
            )
            reddit_count = reddit_count_result.scalar() or 0
            
            # Get timestamp ranges from sentiment data
            oldest_sentiment_result = await self.db.execute(
                select(func.min(SentimentData.created_at))
            )
            oldest_record = oldest_sentiment_result.scalar()
            
            newest_sentiment_result = await self.db.execute(
                select(func.max(SentimentData.created_at))
            )
            newest_record = newest_sentiment_result.scalar()
            
            # Calculate total records - only count processed data (sentiment + prices)
            # Note: news_articles and reddit_posts are raw data that gets processed into sentiment_data
            # We keep them for audit/reprocessing but don't count them as separate data points
            total_records = sentiment_count + price_count
            
            # Estimated storage calculation (in MB):
            # - Sentiment records: ~0.5KB each
            # - Price records: ~0.2KB each  
            # - News articles: ~2KB each (raw storage, kept for audit)
            # - Reddit posts: ~1KB each (raw storage, kept for audit)
            estimated_size_mb = (
                (sentiment_count * 0.0005) + 
                (price_count * 0.0002) + 
                (news_count * 0.002) + 
                (reddit_count * 0.001)
            )
            
            return StorageMetrics(
                total_records=total_records,
                storage_size_mb=round(estimated_size_mb, 2),
                sentiment_records=sentiment_count,
                stock_price_records=price_count,
                oldest_record=oldest_record,
                newest_record=newest_record
            )
            
        except Exception as e:
            self.logger.error("Error calculating storage metrics", error=str(e))
            raise
    
    async def apply_retention_policy(self, policy: RetentionPolicy, force_cleanup: bool = False) -> Dict[str, int]:
        """
        Apply data retention policy and clean up old records.
        
        Args:
            policy: Retention policy configuration
            force_cleanup: Force cleanup even if auto_cleanup is disabled
            
        Returns:
            Dictionary with cleanup statistics
        """
        try:
            self.logger.info("Applying retention policy", policy=policy.dict(), force_cleanup=force_cleanup)
            
            cleanup_stats = {
                "sentiment_records_deleted": 0,
                "price_records_deleted": 0,
                "log_records_deleted": 0,
                "news_records_deleted": 0,
                "reddit_records_deleted": 0
            }
            
            # Always run cleanup when explicitly requested via admin panel
            if policy.auto_cleanup_enabled or force_cleanup:
                self.logger.info("Running data cleanup", policy=policy.dict())
                
                # Clean up old sentiment data
                sentiment_cutoff = to_naive_utc(utc_now() - timedelta(days=policy.sentiment_data_days))
                sentiment_delete_result = await self.db.execute(
                    delete(SentimentData).where(SentimentData.created_at < sentiment_cutoff)
                )
                cleanup_stats["sentiment_records_deleted"] = sentiment_delete_result.rowcount
                self.logger.info(f"Deleted {sentiment_delete_result.rowcount} sentiment records older than {sentiment_cutoff}")
                
                # Clean up old price data
                price_cutoff = to_naive_utc(utc_now() - timedelta(days=policy.price_data_days))
                price_delete_result = await self.db.execute(
                    delete(StockPrice).where(StockPrice.created_at < price_cutoff)
                )
                cleanup_stats["price_records_deleted"] = price_delete_result.rowcount
                self.logger.info(f"Deleted {price_delete_result.rowcount} price records older than {price_cutoff}")
                
                # Clean up old log data
                log_cutoff = to_naive_utc(utc_now() - timedelta(days=policy.log_data_days))
                log_delete_result = await self.db.execute(
                    delete(SystemLog).where(SystemLog.timestamp < log_cutoff)
                )
                cleanup_stats["log_records_deleted"] = log_delete_result.rowcount
                self.logger.info(f"Deleted {log_delete_result.rowcount} log records older than {log_cutoff}")
                
                # Clean up old news articles (optional - same retention as sentiment)
                news_delete_result = await self.db.execute(
                    delete(NewsArticle).where(NewsArticle.published_at < sentiment_cutoff)
                )
                cleanup_stats["news_records_deleted"] = news_delete_result.rowcount
                
                # Clean up old reddit posts (optional - same retention as sentiment)
                reddit_delete_result = await self.db.execute(
                    delete(RedditPost).where(RedditPost.created_utc < sentiment_cutoff)
                )
                cleanup_stats["reddit_records_deleted"] = reddit_delete_result.rowcount
                
                await self.db.commit()
                
                self.logger.info("Retention policy applied successfully", stats=cleanup_stats)
            else:
                self.logger.info("Auto cleanup disabled, skipping data cleanup")
            
            return cleanup_stats
            
        except Exception as e:
            self.logger.error("Error applying retention policy", error=str(e))
            await self.db.rollback()
            raise
    
    async def create_data_backup(self) -> Dict[str, Any]:
        """
        Create a backup of current data.
        
        Returns:
            Backup metadata
        """
        try:
            self.logger.info("Creating data backup")
            
            backup_timestamp = utc_now()
            # Format backup ID with date for better readability
            date_str = backup_timestamp.strftime("%Y%m%d_%H%M%S")
            backup_id = f"Insight_stock_backup_{date_str}"
            
            # Get current data counts for backup metadata
            metrics = await self.calculate_storage_metrics()
            
            # Implement actual backup logic
            success = await self._create_database_backup(backup_id, backup_timestamp)
            
            backup_metadata = {
                "backup_id": backup_id,
                "timestamp": backup_timestamp,
                "total_records": metrics.total_records,
                "size_mb": metrics.storage_size_mb,
                "status": "completed" if success else "failed",
                "location": f"./data/backups/{backup_id}.db"
            }
            
            self.logger.info("Data backup created", metadata=backup_metadata)
            return backup_metadata
            
        except Exception as e:
            self.logger.error("Error creating data backup", error=str(e))
            raise
    
    async def get_storage_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive storage health report.
        """
        try:
            self.logger.info("Generating storage health report")
            
            metrics = await self.calculate_storage_metrics()
            
            # Calculate actual growth rate from historical data
            growth_rate_mb_per_day = await self._calculate_storage_growth_rate()
            
            # Calculate projected storage needs based on available disk space
            days_until_full = await self._calculate_days_until_full(growth_rate_mb_per_day)
            
            # Check for data quality issues
            data_quality_issues = []
            
            # Check for duplicate sentiment records by stock and raw text
            duplicate_sentiment_result = await self.db.execute(
                text("""
                    SELECT COUNT(*) FROM (
                        SELECT stock_id, raw_text, COUNT(*) 
                        FROM sentiment_data 
                        WHERE raw_text IS NOT NULL
                        GROUP BY stock_id, raw_text 
                        HAVING COUNT(*) > 1
                    ) duplicates
                """)
            )
            duplicate_count = duplicate_sentiment_result.scalar() or 0
            
            if duplicate_count > 0:
                data_quality_issues.append(f"{duplicate_count} duplicate sentiment records found")
            
            # Check for missing stock names
            unnamed_stocks_result = await self.db.execute(
                select(func.count(StocksWatchlist.id)).where(StocksWatchlist.name.is_(None))
            )
            unnamed_count = unnamed_stocks_result.scalar() or 0
            
            if unnamed_count > 0:
                data_quality_issues.append(f"{unnamed_count} stocks missing company names")
            
            # Check for sentiment records without stock associations
            orphaned_sentiment_result = await self.db.execute(
                select(func.count(SentimentData.id)).where(SentimentData.stock_id.is_(None))
            )
            orphaned_count = orphaned_sentiment_result.scalar() or 0
            
            if orphaned_count > 0:
                data_quality_issues.append(f"{orphaned_count} sentiment records without stock associations")
            
            return {
                "metrics": metrics.dict(),
                "growth_rate_mb_per_day": growth_rate_mb_per_day,
                "projected_days_until_full": days_until_full,
                "data_quality_issues": data_quality_issues,
                "health_score": 85 if not data_quality_issues else 70,  # Simple scoring
                "recommendations": [
                    "Set up automated cleanup for old data",
                    "Monitor growth rate trends"
                ]
            }
            
        except Exception as e:
            self.logger.error("Error generating storage health report", error=str(e))
            raise
    
    async def optimize_database(self) -> Dict[str, Any]:
        """
        Perform database optimization operations.
        """
        try:
            self.logger.info("Starting database optimization")
            
            optimization_results = {
                "operations_performed": [],
                "time_taken_seconds": 0,
                "space_reclaimed_mb": 0
            }
            
            start_time = utc_now()
            
            # Implement actual database optimization operations
            operations_performed = []
            space_reclaimed_mb = 0.0
            
            # Vacuum operations to reclaim space
            space_reclaimed_mb += await self._vacuum_database(operations_performed)
            
            # Rebuild indexes for better performance
            await self._rebuild_indexes(operations_performed)
            
            # Update table statistics
            await self._update_statistics(operations_performed)
            
            # Clean up temporary data and orphaned records
            space_reclaimed_mb += await self._cleanup_orphaned_data(operations_performed)
            
            optimization_results["operations_performed"] = operations_performed
            
            end_time = utc_now()
            optimization_results["time_taken_seconds"] = (end_time - start_time).total_seconds()
            optimization_results["space_reclaimed_mb"] = round(space_reclaimed_mb, 2)
            
            self.logger.info("Database optimization completed", results=optimization_results)
            return optimization_results
            
        except Exception as e:
            self.logger.error("Error during database optimization", error=str(e))
            raise
    
    async def _calculate_storage_growth_rate(self) -> float:
        """Calculate daily storage growth rate from historical data."""
        try:
            # SQLite compatible query
            result = await self.db.execute(text("""
                SELECT DATE(created_at) as date, COUNT(*) as daily_count 
                FROM sentiment_data 
                WHERE created_at >= datetime('now', '-7 days')
                GROUP BY DATE(created_at)
                ORDER BY date
            """))
            
            daily_counts = [row.daily_count for row in result.fetchall()]
            if len(daily_counts) < 2:
                return 2.5  # Default estimate
                
            # Estimate MB per record (average text size + metadata)
            avg_mb_per_record = 0.002  # ~2KB per sentiment record
            avg_daily_records = sum(daily_counts) / len(daily_counts)
            
            return round(avg_daily_records * avg_mb_per_record, 2)
            
        except Exception:
            return 2.5  # Default fallback
    
    async def _calculate_days_until_full(self, growth_rate_mb_per_day: float) -> int:
        """Calculate days until storage is full based on growth rate."""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024 ** 3)
            
            if growth_rate_mb_per_day <= 0:
                return 9999  # Essentially unlimited
                
            days_until_full = int((free_gb * 1024) / growth_rate_mb_per_day)
            return min(days_until_full, 9999)  # Cap at reasonable max
            
        except Exception:
            return 365  # Default fallback
    
    async def _create_database_backup(self, backup_id: str, timestamp: datetime) -> bool:
        """Create actual database backup."""
        try:
            import shutil
            import os
            
            # Create backups directory if it doesn't exist
            backup_dir = "./data/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            # Source database file
            source_db = "./data/insight_stock.db"
            
            # Backup file path
            backup_file = f"{backup_dir}/{backup_id}.db"
            
            if os.path.exists(source_db):
                # Create a copy of the database file
                shutil.copy2(source_db, backup_file)
                
                # Verify backup was created
                if os.path.exists(backup_file):
                    backup_size = os.path.getsize(backup_file)
                    self.logger.info(f"Database backup created successfully: {backup_file} ({backup_size} bytes)")
                    return True
                else:
                    self.logger.error("Backup file was not created")
                    return False
            else:
                self.logger.error("Source database file not found")
                return False
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    async def _vacuum_database(self, operations: List[str]) -> float:
        """Perform database vacuum operations."""
        try:
            # SQLite vacuum operations
            await self.db.execute(text("VACUUM"))
            await self.db.execute(text("ANALYZE"))
            
            operations.append("Vacuumed database and updated statistics")
            return 5.2  # Estimate space reclaimed
            
        except Exception as e:
            self.logger.error(f"Vacuum failed: {e}")
            return 0.0
    
    async def _rebuild_indexes(self, operations: List[str]) -> None:
        """Rebuild database indexes."""
        try:
            # SQLite reindex operations
            await self.db.execute(text("REINDEX"))
            operations.append("Rebuilt all database indexes")
            
        except Exception as e:
            self.logger.error(f"Index rebuild failed: {e}")
    
    async def _update_statistics(self, operations: List[str]) -> None:
        """Update table statistics."""
        try:
            # SQLite analyze operations
            await self.db.execute(text("ANALYZE"))
            operations.append("Updated database statistics")
            
        except Exception as e:
            self.logger.error(f"Statistics update failed: {e}")
    
    async def _cleanup_orphaned_data(self, operations: List[str]) -> float:
        """Clean up orphaned data and temporary records."""
        try:
            # Remove orphaned sentiment data without corresponding stocks
            result = await self.db.execute(text("""
                DELETE FROM sentiment_data 
                WHERE stock_id NOT IN (SELECT id FROM stocks_watchlist)
            """))
            
            orphaned_count = result.rowcount
            operations.append(f"Removed {orphaned_count} orphaned sentiment records")
            
            # Estimate space reclaimed (rough calculation)
            return orphaned_count * 0.002  # ~2KB per record
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            return 0.0