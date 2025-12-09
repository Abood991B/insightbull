"""
Collector Configuration Service
===============================

Manages the enabled/disabled state of data collectors.
Stores configuration in a JSON file for persistence.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
from app.utils.timezone import utc_now
from app.infrastructure.log_system import get_logger

# Get structured logger
logger = get_logger()

# Configuration file path - points to backend/data directory
CONFIG_FILE = Path(__file__).parent.parent.parent / "data" / "collector_config.json"

# Default configuration
DEFAULT_CONFIG = {
    "collectors": {
        "hackernews": {
            "enabled": True,
            "display_name": "Hacker News",
            "requires_api_key": False,
            "description": "Tech community data from news.ycombinator.com"
        },
        "gdelt": {
            "enabled": True,
            "display_name": "GDELT",
            "requires_api_key": False,
            "description": "Global news from 100+ countries in 65 languages"
        },
        "finnhub": {
            "enabled": True,
            "display_name": "FinHub",
            "requires_api_key": True,
            "description": "Financial market data and news"
        },
        "newsapi": {
            "enabled": True,
            "display_name": "NewsAPI",
            "requires_api_key": True,
            "description": "General news data collection"
        },
        "yfinance": {
            "enabled": True,
            "display_name": "Yahoo Finance",
            "requires_api_key": False,
            "description": "Free financial news from Yahoo Finance"
        }
    },
    "ai_services": {
        "gemini": {
            "enabled": True,
            "display_name": "Gemma 3 27B AI",
            "requires_api_key": True,
            "description": "AI sentiment verification for improved accuracy",
            "verification_mode": "low_confidence_and_neutral",
            "confidence_threshold": 0.85
        }
    },
    "last_updated": None,
    "updated_by": None
}


class CollectorConfigService:
    """Service for managing collector enable/disable configuration."""
    
    def __init__(self):
        self._ensure_config_exists()
        logger.info(
            "Collector config service initialized",
            component="collector_config",
            config_file=str(CONFIG_FILE)
        )
    
    def _ensure_config_exists(self) -> None:
        """Ensure the configuration file exists with default values."""
        if not CONFIG_FILE.exists():
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            self._save_config(DEFAULT_CONFIG)
            logger.info(
                "Created default collector configuration file",
                component="collector_config",
                config_file=str(CONFIG_FILE)
            )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(
                "Failed to load collector config, using defaults",
                component="collector_config",
                error=str(e)
            )
            return DEFAULT_CONFIG.copy()
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    
    def get_all_collector_configs(self) -> Dict[str, Any]:
        """Get all collector configurations."""
        config = self._load_config()
        return {
            "collectors": config.get("collectors", DEFAULT_CONFIG["collectors"]),
            "last_updated": config.get("last_updated"),
            "updated_by": config.get("updated_by")
        }
    
    def get_collector_config(self, collector_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific collector."""
        config = self._load_config()
        return config.get("collectors", {}).get(collector_name.lower())
    
    def is_collector_enabled(self, collector_name: str) -> bool:
        """Check if a collector is enabled."""
        collector_config = self.get_collector_config(collector_name)
        if collector_config is None:
            return True  # Default to enabled if not found
        return collector_config.get("enabled", True)
    
    def set_collector_enabled(
        self, 
        collector_name: str, 
        enabled: bool, 
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enable or disable a specific collector."""
        config = self._load_config()
        
        collector_name = collector_name.lower()
        if collector_name not in config.get("collectors", {}):
            logger.error(
                "Attempted to toggle unknown collector",
                component="collector_config",
                collector=collector_name,
                action="toggle_failed"
            )
            raise ValueError(f"Unknown collector: {collector_name}")
        
        previous_state = config["collectors"][collector_name].get("enabled", True)
        config["collectors"][collector_name]["enabled"] = enabled
        config["last_updated"] = utc_now().isoformat()
        config["updated_by"] = updated_by
        
        self._save_config(config)
        
        # Log the state change
        action = "enabled" if enabled else "disabled"
        logger.info(
            f"Collector {action}: {collector_name}",
            component="collector_config",
            collector=collector_name,
            action=f"collector_{action}",
            previous_state=previous_state,
            new_state=enabled,
            updated_by=updated_by
        )
        
        return {
            "collector": collector_name,
            "enabled": enabled,
            "message": f"Collector '{collector_name}' has been {'enabled' if enabled else 'disabled'}",
            "updated_at": config["last_updated"],
            "updated_by": updated_by
        }
    
    def get_enabled_collectors(self) -> list:
        """Get list of enabled collector names."""
        config = self._load_config()
        return [
            name for name, cfg in config.get("collectors", {}).items()
            if cfg.get("enabled", True)
        ]
    
    def get_disabled_collectors(self) -> list:
        """Get list of disabled collector names."""
        config = self._load_config()
        return [
            name for name, cfg in config.get("collectors", {}).items()
            if not cfg.get("enabled", True)
        ]
    
    # ============================================================================
    # AI SERVICES MANAGEMENT
    # ============================================================================
    
    def get_ai_service_config(self, service_name: str) -> Optional[Dict[str, Any]]:
        """Get configuration for a specific AI service."""
        config = self._load_config()
        return config.get("ai_services", {}).get(service_name.lower())
    
    def is_ai_service_enabled(self, service_name: str) -> bool:
        """Check if an AI service is enabled."""
        service_config = self.get_ai_service_config(service_name)
        if service_config is None:
            return False
        return service_config.get("enabled", False)
    
    def set_ai_service_enabled(
        self, 
        service_name: str, 
        enabled: bool, 
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Enable or disable a specific AI service."""
        config = self._load_config()
        
        service_name = service_name.lower()
        
        # Ensure ai_services section exists
        if "ai_services" not in config:
            config["ai_services"] = DEFAULT_CONFIG.get("ai_services", {})
        
        if service_name not in config.get("ai_services", {}):
            logger.error(
                "Attempted to toggle unknown AI service",
                component="collector_config",
                service=service_name,
                action="toggle_failed"
            )
            raise ValueError(f"Unknown AI service: {service_name}")
        
        previous_state = config["ai_services"][service_name].get("enabled", False)
        config["ai_services"][service_name]["enabled"] = enabled
        config["last_updated"] = utc_now().isoformat()
        config["updated_by"] = updated_by
        
        self._save_config(config)
        
        # Log the state change
        action = "enabled" if enabled else "disabled"
        logger.info(
            f"AI service {action}: {service_name}",
            component="collector_config",
            service=service_name,
            action=f"ai_service_{action}",
            previous_state=previous_state,
            new_state=enabled,
            updated_by=updated_by
        )
        
        return {
            "service": service_name,
            "enabled": enabled,
            "message": f"AI service '{service_name}' has been {'enabled' if enabled else 'disabled'}",
            "updated_at": config["last_updated"],
            "updated_by": updated_by
        }
    
    def update_ai_service_settings(
        self,
        service_name: str,
        verification_mode: Optional[str] = None,
        confidence_threshold: Optional[float] = None,
        updated_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update AI service settings like verification mode and threshold."""
        config = self._load_config()
        
        service_name = service_name.lower()
        
        if "ai_services" not in config:
            config["ai_services"] = DEFAULT_CONFIG.get("ai_services", {})
        
        if service_name not in config.get("ai_services", {}):
            raise ValueError(f"Unknown AI service: {service_name}")
        
        if verification_mode is not None:
            valid_modes = ["none", "low_confidence", "low_confidence_and_neutral", "all"]
            if verification_mode not in valid_modes:
                raise ValueError(f"Invalid verification mode. Must be one of: {valid_modes}")
            config["ai_services"][service_name]["verification_mode"] = verification_mode
        
        if confidence_threshold is not None:
            if not 0.0 <= confidence_threshold <= 1.0:
                raise ValueError("Confidence threshold must be between 0.0 and 1.0")
            config["ai_services"][service_name]["confidence_threshold"] = confidence_threshold
        
        config["last_updated"] = utc_now().isoformat()
        config["updated_by"] = updated_by
        
        self._save_config(config)
        
        logger.info(
            f"AI service settings updated: {service_name}",
            component="collector_config",
            service=service_name,
            verification_mode=verification_mode,
            confidence_threshold=confidence_threshold,
            updated_by=updated_by
        )
        
        return {
            "service": service_name,
            "settings": config["ai_services"][service_name],
            "message": f"AI service '{service_name}' settings updated",
            "updated_at": config["last_updated"]
        }
    
    def get_all_ai_services(self) -> Dict[str, Any]:
        """Get all AI service configurations."""
        config = self._load_config()
        return config.get("ai_services", DEFAULT_CONFIG.get("ai_services", {}))


# Singleton instance
_collector_config_service: Optional[CollectorConfigService] = None


def get_collector_config_service() -> CollectorConfigService:
    """Get the singleton collector config service instance."""
    global _collector_config_service
    if _collector_config_service is None:
        _collector_config_service = CollectorConfigService()
    return _collector_config_service
