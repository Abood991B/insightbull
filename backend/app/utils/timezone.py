"""
Timezone Utilities for Consistent UTC Handling
==============================================

This module provides timezone-aware datetime utilities that enforce UTC
as the single source of truth for all internal operations and database storage.

Architecture:
- All timestamps stored in UTC
- All API responses use UTC ISO 8601 format
- Frontend handles timezone conversion for display
- No hardcoded timezone offsets

Migration Note:
- This replaces the old malaysia_now() and utc_to_malaysia() functions
- All deprecated functions remain for backward compatibility with warnings
"""
from datetime import datetime, timezone
from typing import Optional
import warnings


def utc_now() -> datetime:
    """
    Get current time in UTC (timezone-aware).
    
    This is the replacement for datetime.utcnow() which is deprecated in Python 3.12+.
    Always returns a timezone-aware datetime in UTC.
    
    Returns:
        datetime: Current UTC time with timezone information
        
    Example:
        >>> now = utc_now()
        >>> now.tzinfo
        datetime.timezone.utc
    """
    return datetime.now(timezone.utc)


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure datetime is timezone-aware UTC.
    
    Conversion rules:
    - If already UTC: return as-is
    - If naive: assume UTC and make aware
    - If other timezone: convert to UTC
    - If None: return None
    
    Args:
        dt: Datetime to convert (can be None, naive, or timezone-aware)
        
    Returns:
        Optional[datetime]: Timezone-aware UTC datetime or None
        
    Example:
        >>> naive_dt = datetime(2025, 11, 2, 14, 30, 45)
        >>> aware_dt = ensure_utc(naive_dt)
        >>> aware_dt.tzinfo
        datetime.timezone.utc
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Naive datetime - assume UTC and make aware
        return dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        # Convert from other timezone to UTC
        return dt.astimezone(timezone.utc)
    
    return dt


def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO 8601 string with UTC timezone.
    
    Output format: "2025-11-02T14:30:45.123456+00:00"
    
    Args:
        dt: Datetime to convert (automatically converted to UTC)
        
    Returns:
        Optional[str]: ISO 8601 formatted UTC string or None
        
    Example:
        >>> dt = utc_now()
        >>> iso = to_iso_string(dt)
        >>> iso
        '2025-11-02T14:30:45.123456+00:00'
    """
    if dt is None:
        return None
    
    utc_dt = ensure_utc(dt)
    return utc_dt.isoformat()


def to_naive_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Convert datetime to naive UTC datetime for SQLite compatibility.
    
    SQLite doesn't natively support timezone-aware datetimes. This function
    converts timezone-aware datetimes to naive UTC for database operations.
    
    Args:
        dt: Datetime to convert (can be None, naive, or timezone-aware)
        
    Returns:
        Optional[datetime]: Naive UTC datetime or None
        
    Example:
        >>> aware_dt = utc_now()
        >>> naive_dt = to_naive_utc(aware_dt)
        >>> naive_dt.tzinfo is None
        True
    """
    if dt is None:
        return None
    
    # First ensure it's UTC
    utc_dt = ensure_utc(dt)
    
    # Remove timezone info to make it naive
    return utc_dt.replace(tzinfo=None)


def parse_iso_string(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO 8601 string to timezone-aware UTC datetime.
    
    Handles various ISO 8601 formats and ensures result is UTC.
    
    Args:
        iso_string: ISO 8601 formatted datetime string
        
    Returns:
        Optional[datetime]: Timezone-aware UTC datetime or None
        
    Example:
        >>> dt = parse_iso_string("2025-11-02T14:30:45+00:00")
        >>> dt.tzinfo
        datetime.timezone.utc
    """
    if not iso_string:
        return None
    
    try:
        dt = datetime.fromisoformat(iso_string)
        return ensure_utc(dt)
    except (ValueError, TypeError) as e:
        warnings.warn(f"Failed to parse ISO string '{iso_string}': {e}")
        return None


# ============================================================================
# DEPRECATED FUNCTIONS - For Backward Compatibility Only
# ============================================================================
# These functions are kept for backward compatibility during migration.
# They will be removed in a future version.
# All new code should use utc_now(), ensure_utc(), and to_iso_string().
# ============================================================================

def malaysia_now() -> datetime:
    """
    DEPRECATED: Use utc_now() instead.
    
    This function returns UTC time, not Malaysia time.
    It exists only for backward compatibility during migration.
    
    Raises:
        DeprecationWarning: This function is deprecated
        
    Returns:
        datetime: Current UTC time (not Malaysia time despite the name)
    """
    warnings.warn(
        "malaysia_now() is deprecated. Use utc_now() for UTC timestamps. "
        "Frontend should handle timezone display conversion.",
        DeprecationWarning,
        stacklevel=2
    )
    return utc_now()


def utc_to_malaysia(utc_dt: datetime) -> datetime:
    """
    DEPRECATED: Backend should not convert timezones for display.
    
    This function now returns the datetime as-is in UTC.
    Frontend is responsible for timezone conversion and display.
    
    Raises:
        DeprecationWarning: This function is deprecated
        
    Returns:
        datetime: UTC datetime (no conversion performed)
    """
    warnings.warn(
        "utc_to_malaysia() is deprecated. Backend should return UTC timestamps. "
        "Use to_iso_string() for API responses. Frontend handles display conversion.",
        DeprecationWarning,
        stacklevel=2
    )
    return ensure_utc(utc_dt)


def malaysia_to_utc(malaysia_dt: datetime) -> datetime:
    """
    DEPRECATED: Use ensure_utc() instead.
    
    This function converts any datetime to UTC, regardless of source timezone.
    
    Raises:
        DeprecationWarning: This function is deprecated
        
    Returns:
        datetime: UTC datetime
    """
    warnings.warn(
        "malaysia_to_utc() is deprecated. Use ensure_utc() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return ensure_utc(malaysia_dt)


def format_malaysia_time(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    DEPRECATED: Backend should not format for specific timezones.
    
    This function now formats in UTC with ISO 8601.
    Frontend handles timezone-specific formatting.
    
    Raises:
        DeprecationWarning: This function is deprecated
        
    Returns:
        str: ISO 8601 formatted UTC string or "N/A"
    """
    warnings.warn(
        "format_malaysia_time() is deprecated. Use to_iso_string() for API responses. "
        "Frontend handles timezone-specific formatting.",
        DeprecationWarning,
        stacklevel=2
    )
    if dt is None:
        return "N/A"
    return to_iso_string(dt) or "N/A"


def malaysia_isoformat(dt: Optional[datetime] = None) -> str:
    """
    DEPRECATED: Use to_iso_string() instead.
    
    This function returns UTC ISO format, not Malaysia timezone.
    
    Raises:
        DeprecationWarning: This function is deprecated
        
    Returns:
        str: ISO 8601 formatted UTC string
    """
    warnings.warn(
        "malaysia_isoformat() is deprecated. Use to_iso_string() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    if dt is None:
        dt = utc_now()
    return to_iso_string(dt) or ""


# Export public API
__all__ = [
    # New API (recommended)
    'utc_now',
    'ensure_utc',
    'to_iso_string',
    'parse_iso_string',
    # Deprecated (backward compatibility)
    'malaysia_now',
    'utc_to_malaysia',
    'malaysia_to_utc',
    'format_malaysia_time',
    'malaysia_isoformat',
]