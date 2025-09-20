"""
Timezone utilities for Malaysia/Kuala Lumpur time handling
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# Malaysia timezone is UTC+8
MALAYSIA_TZ = timezone(timedelta(hours=8))


def malaysia_now() -> datetime:
    """Get current time in Malaysia timezone"""
    return datetime.now(MALAYSIA_TZ)


def utc_to_malaysia(utc_dt: datetime) -> datetime:
    """Convert UTC datetime to Malaysia timezone"""
    if utc_dt.tzinfo is None:
        # Assume naive datetime is UTC
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(MALAYSIA_TZ)


def malaysia_to_utc(malaysia_dt: datetime) -> datetime:
    """Convert Malaysia datetime to UTC"""
    if malaysia_dt.tzinfo is None:
        # Assume naive datetime is Malaysia time
        malaysia_dt = malaysia_dt.replace(tzinfo=MALAYSIA_TZ)
    return malaysia_dt.astimezone(timezone.utc)


def format_malaysia_time(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """Format datetime in Malaysia timezone"""
    if dt is None:
        return "N/A"
    
    # Convert to Malaysia time if needed
    if dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)
    
    malaysia_dt = dt.astimezone(MALAYSIA_TZ)
    return malaysia_dt.strftime(format_str)


def malaysia_isoformat(dt: Optional[datetime] = None) -> str:
    """Get ISO format string in Malaysia timezone"""
    if dt is None:
        dt = malaysia_now()
    elif dt.tzinfo is None:
        # Assume naive datetime is UTC
        dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(MALAYSIA_TZ)
    elif dt.tzinfo != MALAYSIA_TZ:
        dt = dt.astimezone(MALAYSIA_TZ)
    
    return dt.isoformat()