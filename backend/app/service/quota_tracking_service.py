"""
Quota Tracking Service
======================

Tracks daily API usage for rate-limited data sources.
Automatically disables sources when quotas are near exhaustion.

Supports:
- NewsAPI: 100 requests/day
- YFinance: Unlimited (tracked for monitoring)
- Any other sources with daily quotas

Features:
- Real-time usage tracking
- Auto-disable at configurable threshold (default 90%)
- Daily reset at midnight UTC
- Persistent storage in JSON file
- Warning notifications when approaching limits
"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from app.utils.timezone import utc_now
from app.infrastructure.log_system import get_logger

# Get structured logger
logger = get_logger()

# Quota tracking file path - points to backend/data directory
QUOTA_FILE = Path(__file__).parent.parent.parent / "data" / "quota_tracking.json"


@dataclass
class SourceQuota:
    """Quota configuration and usage for a data source"""
    name: str
    daily_limit: int
    current_usage: int
    last_reset: str  # ISO format date
    is_exhausted: bool
    warning_threshold: float  # 0.0-1.0 (e.g., 0.8 = 80%)
    auto_disable_threshold: float  # 0.0-1.0 (e.g., 0.9 = 90%)
    
    @property
    def remaining(self) -> int:
        return max(0, self.daily_limit - self.current_usage)
    
    @property
    def usage_percent(self) -> float:
        if self.daily_limit == 0:
            return 0.0
        return self.current_usage / self.daily_limit
    
    def should_warn(self) -> bool:
        return self.usage_percent >= self.warning_threshold
    
    def should_disable(self) -> bool:
        return self.usage_percent >= self.auto_disable_threshold


# Default quota configurations for all 5 data sources + Gemini AI
DEFAULT_QUOTAS: Dict[str, Dict[str, Any]] = {
    # HackerNews Algolia API - Very generous, no auth required
    "hackernews": {
        "daily_limit": 7200,           # 2 req/sec * 3600 = 7200/hr, very generous
        "warning_threshold": 0.85,
        "auto_disable_threshold": 0.95
    },
    # GDELT DOC 2.0 API - Free, no auth required
    "gdelt": {
        "daily_limit": 3600,           # 1 req/sec courteous limit
        "warning_threshold": 0.85,
        "auto_disable_threshold": 0.95
    },
    # Finnhub API - Free tier: 60 calls/minute
    "finnhub": {
        "daily_limit": 3600,           # 60/min realistic daily usage
        "warning_threshold": 0.8,
        "auto_disable_threshold": 0.95
    },
    # NewsAPI - Free tier: 100 requests/day (very limited)
    "newsapi": {
        "daily_limit": 100,
        "warning_threshold": 0.7,      # Warn early at 70%
        "auto_disable_threshold": 0.9  # Disable at 90%
    },
    # YFinance - Unlimited but track for monitoring
    "yfinance": {
        "daily_limit": 10000,          # Soft limit for monitoring
        "warning_threshold": 0.9,
        "auto_disable_threshold": 0.99
    },
    # Gemma 3 27B - Google AI Studio (actual limits)
    # 30 RPM, 15k TPM, 14,400 RPD (requests per day)
    "gemini": {
        "daily_limit": 14400,          # Actual RPD limit
        "warning_threshold": 0.8,      # Warn at 80% (11,520 requests)
        "auto_disable_threshold": 0.95 # Disable at 95% (13,680 requests)
    }
}


class QuotaTrackingService:
    """
    Service for tracking and managing API quota usage.
    
    Features:
    - Track usage per source per day
    - Auto-reset at midnight UTC
    - Auto-disable when quota exhausted
    - Warning system for approaching limits
    - Integration with collector config service
    """
    
    def __init__(self):
        self._ensure_quota_file_exists()
        self._check_and_reset_daily()
        logger.info(
            "Quota tracking service initialized",
            component="quota_tracking",
            quota_file=str(QUOTA_FILE)
        )
    
    def _ensure_quota_file_exists(self) -> None:
        """Ensure the quota tracking file exists with defaults."""
        if not QUOTA_FILE.exists():
            QUOTA_FILE.parent.mkdir(parents=True, exist_ok=True)
            initial_data = self._create_initial_quotas()
            self._save_quotas(initial_data)
            logger.info(
                "Created initial quota tracking file",
                component="quota_tracking"
            )
    
    def _create_initial_quotas(self) -> Dict[str, Any]:
        """Create initial quota tracking data."""
        today = date.today().isoformat()
        quotas = {}
        
        for source, config in DEFAULT_QUOTAS.items():
            quotas[source] = {
                "name": source,
                "daily_limit": config["daily_limit"],
                "current_usage": 0,
                "last_reset": today,
                "is_exhausted": False,
                "warning_threshold": config["warning_threshold"],
                "auto_disable_threshold": config["auto_disable_threshold"]
            }
        
        return {
            "quotas": quotas,
            "last_updated": utc_now().isoformat()
        }
    
    def _load_quotas(self) -> Dict[str, Any]:
        """Load quota data from file."""
        try:
            with open(QUOTA_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(
                "Failed to load quota file, creating new one",
                component="quota_tracking",
                error=str(e)
            )
            return self._create_initial_quotas()
    
    def _save_quotas(self, data: Dict[str, Any]) -> None:
        """Save quota data to file."""
        data["last_updated"] = utc_now().isoformat()
        with open(QUOTA_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    
    def _check_and_reset_daily(self) -> None:
        """Check if quotas need daily reset."""
        data = self._load_quotas()
        today = date.today().isoformat()
        reset_performed = False
        
        for source, quota in data.get("quotas", {}).items():
            if quota.get("last_reset") != today:
                # Reset for new day
                quota["current_usage"] = 0
                quota["last_reset"] = today
                quota["is_exhausted"] = False
                reset_performed = True
                logger.info(
                    f"Daily quota reset for {source}",
                    component="quota_tracking",
                    source=source,
                    daily_limit=quota["daily_limit"]
                )
        
        if reset_performed:
            self._save_quotas(data)
            # Re-enable sources that were auto-disabled
            self._reenable_exhausted_sources()
    
    def _reenable_exhausted_sources(self) -> None:
        """Re-enable sources that were auto-disabled due to quota exhaustion."""
        try:
            from app.service.collector_config_service import get_collector_config_service
            config_service = get_collector_config_service()
            
            for source in DEFAULT_QUOTAS.keys():
                # Check if source was disabled due to quota
                quota = self.get_source_quota(source)
                if quota and not quota.is_exhausted:
                    # Re-enable if it was disabled
                    if not config_service.is_collector_enabled(source):
                        config_service.set_collector_enabled(
                            source, 
                            True, 
                            "quota_tracking_daily_reset"
                        )
                        logger.info(
                            f"Re-enabled {source} after daily quota reset",
                            component="quota_tracking",
                            source=source
                        )
        except Exception as e:
            logger.warning(
                "Failed to re-enable exhausted sources",
                component="quota_tracking",
                error=str(e)
            )
    
    def get_source_quota(self, source: str) -> Optional[SourceQuota]:
        """Get quota information for a specific source."""
        data = self._load_quotas()
        quota_data = data.get("quotas", {}).get(source.lower())
        
        if not quota_data:
            return None
        
        return SourceQuota(
            name=quota_data["name"],
            daily_limit=quota_data["daily_limit"],
            current_usage=quota_data["current_usage"],
            last_reset=quota_data["last_reset"],
            is_exhausted=quota_data["is_exhausted"],
            warning_threshold=quota_data["warning_threshold"],
            auto_disable_threshold=quota_data["auto_disable_threshold"]
        )
    
    def get_all_quotas(self) -> Dict[str, SourceQuota]:
        """Get all quota information."""
        data = self._load_quotas()
        quotas = {}
        
        for source, quota_data in data.get("quotas", {}).items():
            quotas[source] = SourceQuota(
                name=quota_data["name"],
                daily_limit=quota_data["daily_limit"],
                current_usage=quota_data["current_usage"],
                last_reset=quota_data["last_reset"],
                is_exhausted=quota_data["is_exhausted"],
                warning_threshold=quota_data["warning_threshold"],
                auto_disable_threshold=quota_data["auto_disable_threshold"]
            )
        
        return quotas
    
    def record_usage(self, source: str, requests_made: int = 1) -> Dict[str, Any]:
        """
        Record API usage for a source.
        
        Args:
            source: Source name (newsapi, finnhub, yfinance, etc.)
            requests_made: Number of requests to record
            
        Returns:
            Status dict with quota info and any warnings
        """
        self._check_and_reset_daily()
        
        data = self._load_quotas()
        source = source.lower()
        
        if source not in data.get("quotas", {}):
            # Source not tracked, return success
            return {
                "success": True,
                "tracked": False,
                "message": f"Source {source} not quota-tracked"
            }
        
        quota = data["quotas"][source]
        quota["current_usage"] += requests_made
        
        result = {
            "success": True,
            "tracked": True,
            "source": source,
            "current_usage": quota["current_usage"],
            "daily_limit": quota["daily_limit"],
            "remaining": max(0, quota["daily_limit"] - quota["current_usage"]),
            "usage_percent": round(quota["current_usage"] / quota["daily_limit"] * 100, 1),
            "warnings": []
        }
        
        # Check thresholds
        usage_ratio = quota["current_usage"] / quota["daily_limit"]
        
        if usage_ratio >= quota["auto_disable_threshold"] and not quota["is_exhausted"]:
            # Auto-disable source
            quota["is_exhausted"] = True
            result["auto_disabled"] = True
            result["warnings"].append(f"{source} quota exhausted ({quota['current_usage']}/{quota['daily_limit']})")
            
            # Disable via collector config service
            self._auto_disable_source(source)
            
            logger.warning(
                f"Auto-disabled {source} due to quota exhaustion",
                component="quota_tracking",
                source=source,
                usage=quota["current_usage"],
                limit=quota["daily_limit"]
            )
        
        elif usage_ratio >= quota["warning_threshold"]:
            result["warning"] = True
            result["warnings"].append(f"{source} approaching quota limit ({quota['current_usage']}/{quota['daily_limit']})")
            
            logger.info(
                f"Quota warning for {source}",
                component="quota_tracking",
                source=source,
                usage=quota["current_usage"],
                limit=quota["daily_limit"],
                percent=result["usage_percent"]
            )
        
        self._save_quotas(data)
        return result
    
    def _auto_disable_source(self, source: str) -> None:
        """Disable a source via collector config service."""
        try:
            from app.service.collector_config_service import get_collector_config_service
            config_service = get_collector_config_service()
            config_service.set_collector_enabled(
                source, 
                False, 
                "quota_tracking_auto_disable"
            )
        except Exception as e:
            logger.error(
                f"Failed to auto-disable {source}",
                component="quota_tracking",
                error=str(e)
            )
    
    def can_make_request(self, source: str, num_requests: int = 1) -> Dict[str, Any]:
        """
        Check if a source can make more requests.
        
        Args:
            source: Source name
            num_requests: Number of requests planned
            
        Returns:
            Dict with 'allowed' bool and reason
        """
        self._check_and_reset_daily()
        
        source = source.lower()
        quota = self.get_source_quota(source)
        
        if not quota:
            return {"allowed": True, "reason": "not_tracked", "remaining": None}
        
        if quota.is_exhausted:
            return {
                "allowed": False, 
                "reason": "quota_exhausted",
                "remaining": quota.remaining,
                "resets_at": "midnight UTC"
            }
        
        if quota.remaining < num_requests:
            return {
                "allowed": False,
                "reason": "insufficient_quota",
                "remaining": quota.remaining,
                "requested": num_requests
            }
        
        # Check if this would exhaust the quota
        new_usage = quota.current_usage + num_requests
        if new_usage / quota.daily_limit >= quota.auto_disable_threshold:
            return {
                "allowed": True,
                "warning": True,
                "reason": "will_exhaust_quota",
                "remaining": quota.remaining
            }
        
        return {"allowed": True, "reason": "ok", "remaining": quota.remaining}
    
    def handle_rate_limit_error(self, source: str, error_message: str = "") -> Dict[str, Any]:
        """
        Handle a rate limit error (429) from an API.
        
        This immediately marks the source as exhausted and disables it
        to prevent further requests until the next daily reset.
        
        Args:
            source: Source name that hit rate limit
            error_message: Error message from the API
            
        Returns:
            Result dict with action taken
        """
        source = source.lower()
        data = self._load_quotas()
        
        if source not in data.get("quotas", {}):
            # Not a tracked source, just log it
            logger.warning(
                f"Rate limit hit for untracked source: {source}",
                component="quota_tracking",
                source=source,
                error=error_message
            )
            return {"success": True, "action": "logged_only", "tracked": False}
        
        # Mark as exhausted
        data["quotas"][source]["is_exhausted"] = True
        # Set usage to limit (we don't know exact count, but it's at limit)
        data["quotas"][source]["current_usage"] = data["quotas"][source]["daily_limit"]
        
        self._save_quotas(data)
        
        # Auto-disable the source
        self._auto_disable_source(source)
        
        logger.error(
            f"Rate limit (429) received from {source} - source disabled until midnight UTC",
            component="quota_tracking",
            source=source,
            error=error_message,
            action="auto_disabled"
        )
        
        return {
            "success": True,
            "action": "disabled",
            "source": source,
            "message": f"{source} disabled due to rate limit (429). Will re-enable at midnight UTC.",
            "resets_at": "midnight UTC"
        }
    
    def get_quota_summary(self) -> Dict[str, Any]:
        """Get a summary of all quota statuses."""
        self._check_and_reset_daily()
        quotas = self.get_all_quotas()
        
        summary = {
            "date": date.today().isoformat(),
            "sources": {},
            "warnings": [],
            "exhausted": []
        }
        
        for source, quota in quotas.items():
            summary["sources"][source] = {
                "usage": quota.current_usage,
                "limit": quota.daily_limit,
                "remaining": quota.remaining,
                "percent_used": round(quota.usage_percent * 100, 1),
                "is_exhausted": quota.is_exhausted,
                "status": "exhausted" if quota.is_exhausted else (
                    "warning" if quota.should_warn() else "ok"
                )
            }
            
            if quota.is_exhausted:
                summary["exhausted"].append(source)
            elif quota.should_warn():
                summary["warnings"].append(source)
        
        return summary
    
    def reset_source_quota(self, source: str) -> Dict[str, Any]:
        """
        Manually reset quota for a source (admin function).
        
        Args:
            source: Source name to reset
            
        Returns:
            Result dict
        """
        data = self._load_quotas()
        source = source.lower()
        
        if source not in data.get("quotas", {}):
            return {"success": False, "error": f"Unknown source: {source}"}
        
        data["quotas"][source]["current_usage"] = 0
        data["quotas"][source]["is_exhausted"] = False
        data["quotas"][source]["last_reset"] = date.today().isoformat()
        
        self._save_quotas(data)
        
        # Re-enable if disabled
        self._reenable_exhausted_sources()
        
        logger.info(
            f"Manual quota reset for {source}",
            component="quota_tracking",
            source=source
        )
        
        return {"success": True, "source": source, "message": "Quota reset successfully"}
    
    def estimate_daily_capacity(self, num_symbols: int, runs_per_day: int) -> Dict[str, Any]:
        """
        Estimate if current quotas can handle planned workload.
        
        Args:
            num_symbols: Number of symbols in watchlist
            runs_per_day: Expected pipeline runs per day
            
        Returns:
            Capacity analysis per source
        """
        analysis = {}
        
        for source, config in DEFAULT_QUOTAS.items():
            daily_limit = config["daily_limit"]
            
            # Calculate expected requests
            # Most sources: 1 request per symbol per run
            requests_per_run = num_symbols
            
            total_daily = requests_per_run * runs_per_day
            remaining = daily_limit - total_daily
            
            status = "ok" if remaining > 10 else ("warning" if remaining >= 0 else "exceeded")
            
            analysis[source] = {
                "daily_limit": daily_limit,
                "requests_per_run": requests_per_run,
                "runs_per_day": runs_per_day,
                "total_daily": total_daily,
                "remaining": remaining,
                "status": status,
                "recommendation": self._get_recommendation(source, status, remaining)
            }
        
        return analysis
    
    def _get_recommendation(self, source: str, status: str, remaining: int) -> str:
        """Get recommendation based on quota status."""
        if status == "ok":
            return f"Sufficient quota ({remaining} remaining)"
        elif status == "warning":
            return f"Near limit - consider reducing run frequency or using free sources"
        else:
            return f"Quota exceeded by {abs(remaining)} - use smart source selection or upgrade API plan"


# Singleton instance
_quota_service: Optional[QuotaTrackingService] = None


def get_quota_tracking_service() -> QuotaTrackingService:
    """Get the singleton quota tracking service instance."""
    global _quota_service
    if _quota_service is None:
        _quota_service = QuotaTrackingService()
    return _quota_service
