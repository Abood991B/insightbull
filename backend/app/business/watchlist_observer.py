"""
Watchlist Observer Pattern Implementation
========================================

Observer pattern for real-time dashboard updates when watchlist changes occur.
Implements the Observer design pattern as specified in the FYP Report architecture.

This module provides:
- WatchlistObserver interface (Observer pattern)
- Concrete observer implementations for different dashboard components
- Subject interface for watchlist changes
- Event notification system for real-time updates
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Set
from datetime import datetime
from enum import Enum
import asyncio
import structlog

from app.infrastructure.log_system import get_logger

logger = get_logger()


class WatchlistEventType(Enum):
    """Types of watchlist events that can occur"""
    STOCK_ADDED = "stock_added"
    STOCK_REMOVED = "stock_removed"
    WATCHLIST_UPDATED = "watchlist_updated"
    WATCHLIST_CLEARED = "watchlist_cleared"


class WatchlistEvent:
    """
    Event data for watchlist changes
    
    Contains all information about a watchlist change event
    including the type of change, affected stocks, and metadata.
    """
    
    def __init__(
        self,
        event_type: WatchlistEventType,
        stocks_affected: List[str] = None,
        metadata: Dict[str, Any] = None,
        timestamp: datetime = None
    ):
        self.event_type = event_type
        self.stocks_affected = stocks_affected or []
        self.metadata = metadata or {}
        from app.utils.timezone import utc_now
        self.timestamp = timestamp or utc_now()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization"""
        return {
            "event_type": self.event_type.value,
            "stocks_affected": self.stocks_affected,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }


class WatchlistObserver(ABC):
    """
    Abstract Observer interface for watchlist changes
    
    Implements the Observer pattern as specified in the FYP Report.
    All dashboard components that need to react to watchlist changes
    should implement this interface.
    """
    
    @abstractmethod
    async def update(self, event: WatchlistEvent) -> None:
        """
        Handle watchlist change event
        
        Args:
            event: The watchlist change event
        """
        pass
    
    @property
    @abstractmethod
    def observer_id(self) -> str:
        """Unique identifier for this observer"""
        pass


class WatchlistSubject(ABC):
    """
    Abstract Subject interface for watchlist changes
    
    Manages observer registration and notification.
    Classes that trigger watchlist changes should inherit from this.
    """
    
    def __init__(self):
        self._observers: Set[WatchlistObserver] = set()
        self._logger = get_logger()
    
    def attach(self, observer: WatchlistObserver) -> None:
        """
        Attach an observer to receive notifications
        
        Args:
            observer: The observer to register
        """
        self._observers.add(observer)
        self._logger.info("Observer attached", observer_id=observer.observer_id)
    
    def detach(self, observer: WatchlistObserver) -> None:
        """
        Detach an observer from receiving notifications
        
        Args:
            observer: The observer to unregister
        """
        self._observers.discard(observer)
        self._logger.info("Observer detached", observer_id=observer.observer_id)
    
    async def notify(self, event: WatchlistEvent) -> None:
        """
        Notify all observers of a watchlist change
        
        Args:
            event: The watchlist change event
        """
        self._logger.info(
            "Notifying watchlist observers",
            event_type=event.event_type.value,
            observer_count=len(self._observers),
            stocks_affected=event.stocks_affected
        )
        
        # Notify all observers asynchronously
        tasks = []
        for observer in self._observers:
            try:
                task = asyncio.create_task(observer.update(event))
                tasks.append(task)
            except Exception as e:
                self._logger.error(
                    "Error creating notification task",
                    observer_id=observer.observer_id,
                    error=str(e)
                )
        
        # Wait for all notifications to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any notification failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    observer = list(self._observers)[i]
                    self._logger.error(
                        "Observer notification failed",
                        observer_id=observer.observer_id,
                        error=str(result)
                    )


# Concrete Observer Implementations

class DashboardObserver(WatchlistObserver):
    """
    Observer for main dashboard updates
    
    Handles watchlist changes that affect the main dashboard display.
    Updates stock tiles, metrics, and overview information.
    """
    
    def __init__(self):
        self._observer_id = "dashboard_observer"
        self._logger = get_logger()
    
    @property
    def observer_id(self) -> str:
        return self._observer_id
    
    async def update(self, event: WatchlistEvent) -> None:
        """Handle dashboard updates for watchlist changes"""
        try:
            self._logger.info(
                "Dashboard processing watchlist event",
                event_type=event.event_type.value,
                stocks_affected=event.stocks_affected
            )
            
            # Simulate dashboard update operations
            if event.event_type == WatchlistEventType.STOCK_ADDED:
                await self._handle_stock_added(event.stocks_affected)
            elif event.event_type == WatchlistEventType.STOCK_REMOVED:
                await self._handle_stock_removed(event.stocks_affected)
            elif event.event_type == WatchlistEventType.WATCHLIST_UPDATED:
                await self._handle_watchlist_updated(event)
            elif event.event_type == WatchlistEventType.WATCHLIST_CLEARED:
                await self._handle_watchlist_cleared()
                
        except Exception as e:
            self._logger.error("Dashboard observer update failed", error=str(e))
            raise
    
    async def _handle_stock_added(self, stocks: List[str]) -> None:
        """Handle stocks being added to watchlist"""
        self._logger.info("Dashboard updating for added stocks", stocks=stocks)
        # In a real implementation, this would:
        # - Fetch initial data for new stocks
        # - Add stock tiles to dashboard
        # - Update summary metrics
        # - Trigger UI refresh
        
    async def _handle_stock_removed(self, stocks: List[str]) -> None:
        """Handle stocks being removed from watchlist"""
        self._logger.info("Dashboard updating for removed stocks", stocks=stocks)
        # In a real implementation, this would:
        # - Remove stock tiles from dashboard
        # - Update summary metrics
        # - Clean up cached data
        # - Trigger UI refresh
        
    async def _handle_watchlist_updated(self, event: WatchlistEvent) -> None:
        """Handle general watchlist updates"""
        self._logger.info("Dashboard processing watchlist update", metadata=event.metadata)
        # In a real implementation, this would:
        # - Refresh entire watchlist display
        # - Update all metrics and summaries
        # - Re-sort/re-organize dashboard layout
        
    async def _handle_watchlist_cleared(self) -> None:
        """Handle watchlist being cleared"""
        self._logger.info("Dashboard processing watchlist cleared")
        # In a real implementation, this would:
        # - Remove all stock tiles
        # - Reset dashboard to empty state
        # - Clear all cached data
        # - Show empty state message


class AnalyticsObserver(WatchlistObserver):
    """
    Observer for analytics dashboard updates
    
    Handles watchlist changes that affect analytical displays,
    charts, and correlation calculations.
    """
    
    def __init__(self):
        self._observer_id = "analytics_observer"
        self._logger = get_logger()
    
    @property
    def observer_id(self) -> str:
        return self._observer_id
    
    async def update(self, event: WatchlistEvent) -> None:
        """Handle analytics updates for watchlist changes"""
        try:
            self._logger.info(
                "Analytics processing watchlist event",
                event_type=event.event_type.value,
                stocks_affected=event.stocks_affected
            )
            
            # Process analytics updates based on event type
            if event.event_type in [WatchlistEventType.STOCK_ADDED, WatchlistEventType.STOCK_REMOVED]:
                await self._recalculate_correlations(event.stocks_affected)
                await self._update_analytics_charts()
            elif event.event_type == WatchlistEventType.WATCHLIST_UPDATED:
                await self._refresh_all_analytics()
            elif event.event_type == WatchlistEventType.WATCHLIST_CLEARED:
                await self._clear_analytics_data()
                
        except Exception as e:
            self._logger.error("Analytics observer update failed", error=str(e))
            raise
    
    async def _recalculate_correlations(self, stocks: List[str]) -> None:
        """Recalculate stock correlations"""
        self._logger.info("Recalculating correlations for stocks", stocks=stocks)
        # In a real implementation, this would:
        # - Fetch historical data for affected stocks
        # - Recalculate correlation matrices
        # - Update correlation charts and heatmaps
        # - Cache new correlation data
    
    async def _update_analytics_charts(self) -> None:
        """Update analytics charts and visualizations"""
        self._logger.info("Updating analytics charts")
        # In a real implementation, this would:
        # - Refresh sentiment trend charts
        # - Update performance comparison charts
        # - Recalculate technical indicators
        # - Update chart data sources
    
    async def _refresh_all_analytics(self) -> None:
        """Refresh all analytics data and displays"""
        self._logger.info("Refreshing all analytics data")
        # In a real implementation, this would:
        # - Reload all analytical calculations
        # - Refresh all charts and visualizations
        # - Update analytical summaries
        # - Recalculate all metrics
    
    async def _clear_analytics_data(self) -> None:
        """Clear all analytics data"""
        self._logger.info("Clearing analytics data")
        # In a real implementation, this would:
        # - Clear all chart data
        # - Reset analytical calculations
        # - Show empty state for analytics
        # - Clear cached calculations


class DataCollectionObserver(WatchlistObserver):
    """
    Observer for data collection pipeline updates
    
    Handles watchlist changes that affect which stocks
    need to be included in data collection processes.
    """
    
    def __init__(self):
        self._observer_id = "data_collection_observer"
        self._logger = get_logger()
    
    @property
    def observer_id(self) -> str:
        return self._observer_id
    
    async def update(self, event: WatchlistEvent) -> None:
        """Handle data collection updates for watchlist changes"""
        try:
            self._logger.info(
                "Data collection processing watchlist event",
                event_type=event.event_type.value,
                stocks_affected=event.stocks_affected
            )
            
            # Update data collection targets based on event
            if event.event_type == WatchlistEventType.STOCK_ADDED:
                await self._add_collection_targets(event.stocks_affected)
            elif event.event_type == WatchlistEventType.STOCK_REMOVED:
                await self._remove_collection_targets(event.stocks_affected)
            elif event.event_type == WatchlistEventType.WATCHLIST_UPDATED:
                await self._update_collection_schedule()
            elif event.event_type == WatchlistEventType.WATCHLIST_CLEARED:
                await self._clear_collection_targets()
                
        except Exception as e:
            self._logger.error("Data collection observer update failed", error=str(e))
            raise
    
    async def _add_collection_targets(self, stocks: List[str]) -> None:
        """Add stocks to data collection targets"""
        self._logger.info("Adding stocks to collection targets", stocks=stocks)
        # Refresh scheduler with updated watchlist
        await self._refresh_data_collection_scheduler()
    
    async def _remove_collection_targets(self, stocks: List[str]) -> None:
        """Remove stocks from data collection targets"""
        self._logger.info("Removing stocks from collection targets", stocks=stocks)
        # Refresh scheduler with updated watchlist
        await self._refresh_data_collection_scheduler()
    
    async def _update_collection_schedule(self) -> None:
        """Update data collection schedule"""
        self._logger.info("Updating data collection schedule")
        # Refresh scheduler with updated watchlist
        await self._refresh_data_collection_scheduler()
    
    async def _clear_collection_targets(self) -> None:
        """Clear all data collection targets"""
        self._logger.info("Clearing all collection targets")
        # Refresh scheduler with updated watchlist
        await self._refresh_data_collection_scheduler()
    
    async def _refresh_data_collection_scheduler(self) -> None:
        """Refresh the data collection scheduler with updated watchlist"""
        try:
            # Import here to avoid circular imports
            from app.business.scheduler import Scheduler
            
            # Get scheduler instance (assuming singleton pattern)
            # Note: In a production system, you might want to inject this dependency
            scheduler = Scheduler()
            if scheduler._is_running:
                await scheduler.refresh_scheduled_jobs()
                self._logger.info("Successfully refreshed data collection scheduler")
            else:
                self._logger.warning("Scheduler is not running, cannot refresh jobs")
                
        except Exception as e:
            self._logger.error("Failed to refresh data collection scheduler", error=str(e))


# Observer Manager and Factory

class WatchlistObserverManager:
    """
    Manager for watchlist observers
    
    Provides centralized management of observer registration,
    notification, and lifecycle management.
    """
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._observers: Dict[str, WatchlistObserver] = {}
            self._logger = get_logger()
            self._initialized = True
    
    def register_default_observers(self) -> None:
        """Register default system observers (only once)"""
        # Check if observers are already registered
        if len(self._observers) >= 3:  # We expect 3 default observers
            return
            
        observers = [
            DashboardObserver(),
            AnalyticsObserver(),
            DataCollectionObserver()
        ]
        
        for observer in observers:
            if observer.observer_id not in self._observers:
                self._observers[observer.observer_id] = observer
                self._logger.info("Registered default observer", observer_id=observer.observer_id)
    
    def get_observer(self, observer_id: str) -> Optional[WatchlistObserver]:
        """Get observer by ID"""
        return self._observers.get(observer_id)
    
    def get_all_observers(self) -> List[WatchlistObserver]:
        """Get all registered observers"""
        return list(self._observers.values())
    
    def register_observer(self, observer: WatchlistObserver) -> None:
        """Register a new observer"""
        self._observers[observer.observer_id] = observer
        self._logger.info("Registered observer", observer_id=observer.observer_id)
    
    def unregister_observer(self, observer_id: str) -> None:
        """Unregister an observer"""
        if observer_id in self._observers:
            del self._observers[observer_id]
            self._logger.info("Unregistered observer", observer_id=observer_id)


# Global observer manager instance
observer_manager = WatchlistObserverManager()
observer_manager.register_default_observers()