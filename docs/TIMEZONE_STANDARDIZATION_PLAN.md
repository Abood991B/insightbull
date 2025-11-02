# Timezone Standardization Implementation Plan

## Executive Summary

This document outlines a comprehensive, phased approach to resolve timezone conflicts between UTC and Malaysia Time (MYT) across the Insight Stock Dashboard system. The plan eliminates hardcoded static timezone implementations and establishes a dynamic, configuration-driven timezone management system following industry best practices.

---

## Problem Analysis

### Current Issues Identified

1. **Mixed Timezone Usage in Backend**:
   - `datetime.utcnow()` used in 38+ locations (pipeline, scheduler, processor)
   - `malaysia_now()` hardcoded helper forcing UTC+8 in 10+ locations
   - Database columns using `DateTime(timezone=True)` but inconsistent timestamp creation
   - `func.now()` server defaults may use system timezone, not UTC

2. **Static Malaysia Timezone Implementation**:
   - `MALAYSIA_TZ = timezone(timedelta(hours=8))` hardcoded in `backend/app/utils/timezone.py`
   - No support for daylight saving time or dynamic timezone configuration
   - Assumes all users want Malaysia time

3. **Frontend Timezone Inconsistencies**:
   - `timezone.ts` hardcodes `'Asia/Kuala_Lumpur'` timezone
   - `timeUtils.ts` uses browser's local timezone
   - `toLocaleString()` calls in admin pages mix 'en-MY' and 'en-US' locales
   - 20+ components manually formatting dates with mixed approaches

4. **API Response Timezone Ambiguity**:
   - Some endpoints return timestamps with `utc_to_malaysia()` conversion
   - Others return raw UTC timestamps
   - Inconsistent `.isoformat()` usage (some with timezone, some naive)

5. **Deprecated Python API**:
   - `datetime.utcnow()` is deprecated in Python 3.12+ (should use `datetime.now(timezone.utc)`)

### Root Causes

- **Lack of Timezone Policy**: No documented standard for how system handles time
- **Mixed Responsibilities**: Backend converting times instead of leaving to frontend
- **Static Configuration**: Timezone hardcoded instead of configurable
- **No Separation of Concerns**: Storage, transmission, and display timezones mixed

---

## Architecture Principles

### Golden Rules for Timezone Handling

1. **Store in UTC**: All database timestamps stored in UTC
2. **Transmit in UTC**: All API responses use ISO 8601 with UTC timezone
3. **Display in User Timezone**: Frontend converts UTC to user's preferred timezone
4. **Configuration Over Hardcoding**: User timezone preference via environment variable
5. **Timezone-Aware Always**: Never use naive datetimes

### Recommended Pattern

```
[Database: UTC] → [Backend: UTC] → [API: UTC ISO 8601] → [Frontend: User Timezone]
```

---

## Implementation Phases

## Phase 1: Audit and Documentation (1-2 hours)

### Outcome
Complete inventory of all timezone-related code and dependencies.

### Tasks

#### 1.1 Backend Audit
- [ ] List all files using `datetime.utcnow()`, `datetime.now()`, `malaysia_now()`
- [ ] Identify all timezone conversion points
- [ ] Document all API endpoints returning timestamps
- [ ] Review database model timestamp columns

#### 1.2 Frontend Audit
- [ ] List all components using `formatMalaysiaTime`, `toLocaleString()`
- [ ] Identify timezone-specific formatting logic
- [ ] Review API response timestamp handling

#### 1.3 Test Audit
- [ ] Identify tests with hardcoded dates/times
- [ ] Review test fixtures with timezone assumptions

### Files to Audit

**Backend:**
- `backend/app/utils/timezone.py` (complete rewrite needed)
- `backend/app/business/pipeline.py` (38+ datetime usages)
- `backend/app/business/scheduler.py` (scheduler job timestamps)
- `backend/app/service/system_service.py` (utc_to_malaysia conversions)
- `backend/app/service/watchlist_service.py` (malaysia_now usage)
- `backend/app/infrastructure/log_system.py` (log timestamps)
- `backend/app/presentation/routes/**/*.py` (API response formatting)

**Frontend:**
- `src/shared/utils/timezone.ts` (static Malaysia timezone)
- `src/shared/utils/timeUtils.ts` (mixed timezone handling)
- `src/features/admin/pages/*.tsx` (20+ components with toLocaleString)
- `src/features/dashboard/pages/Index.tsx` (dashboard timestamps)

**Tests:**
- `backend/tests/test_*.py` (all test files with datetime usage)

---

## Phase 2: Backend UTC Standardization (4-6 hours)

### Outcome
Backend exclusively uses UTC for all internal operations and database storage.

### Tasks

#### 2.1 Refactor Core Timezone Utilities

**File:** `backend/app/utils/timezone.py`

**Actions:**
1. Remove `MALAYSIA_TZ = timezone(timedelta(hours=8))` static constant
2. Deprecate `malaysia_now()`, `utc_to_malaysia()`, `malaysia_to_utc()` functions
3. Create new UTC-only utility functions:

```python
"""
Timezone utilities for consistent UTC handling
"""
from datetime import datetime, timezone
from typing import Optional

def utc_now() -> datetime:
    """Get current time in UTC (timezone-aware)."""
    return datetime.now(timezone.utc)

def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """
    Ensure datetime is timezone-aware UTC.
    
    - If already UTC: return as-is
    - If naive: assume UTC and make aware
    - If other timezone: convert to UTC
    """
    if dt is None:
        return None
    
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    elif dt.tzinfo != timezone.utc:
        # Convert to UTC
        return dt.astimezone(timezone.utc)
    
    return dt

def to_iso_string(dt: Optional[datetime]) -> Optional[str]:
    """
    Convert datetime to ISO 8601 string with UTC timezone.
    
    Example: "2025-11-02T14:30:45.123456+00:00"
    """
    if dt is None:
        return None
    
    utc_dt = ensure_utc(dt)
    return utc_dt.isoformat()

def parse_iso_string(iso_string: Optional[str]) -> Optional[datetime]:
    """
    Parse ISO 8601 string to timezone-aware UTC datetime.
    """
    if not iso_string:
        return None
    
    try:
        dt = datetime.fromisoformat(iso_string)
        return ensure_utc(dt)
    except (ValueError, TypeError):
        return None
```

#### 2.2 Update Business Layer

**Files:**
- `backend/app/business/pipeline.py`
- `backend/app/business/scheduler.py`
- `backend/app/business/processor.py`
- `backend/app/business/data_collector.py`
- `backend/app/business/watchlist_observer.py`

**Actions:**
1. Replace all `datetime.utcnow()` with `utc_now()` from new utilities
2. Replace all `datetime.now()` with `utc_now()`
3. Remove all `malaysia_now()` imports and calls
4. Ensure all datetime comparisons use timezone-aware UTC datetimes

**Example Refactor:**
```python
# OLD (pipeline.py line 410)
start_time = datetime.utcnow()

# NEW
from app.utils.timezone import utc_now
start_time = utc_now()
```

```python
# OLD (pipeline.py line 1196)
created_utc = malaysia_now()  # Use Malaysia timezone

# NEW
created_utc = utc_now()  # Store in UTC
```

#### 2.3 Update Service Layer

**Files:**
- `backend/app/service/system_service.py`
- `backend/app/service/watchlist_service.py`
- `backend/app/infrastructure/log_system.py`

**Actions:**
1. Remove all `utc_to_malaysia()` conversion calls
2. Replace with direct UTC timestamp usage
3. Update log timestamp generation to UTC

**Example Refactor:**
```python
# OLD (system_service.py line 240-241)
last_collection_display = utc_to_malaysia(last_sentiment).isoformat() if last_sentiment else None
last_price_update_display = utc_to_malaysia(last_price).isoformat() if last_price else None

# NEW
from app.utils.timezone import to_iso_string
last_collection_display = to_iso_string(last_sentiment)
last_price_update_display = to_iso_string(last_price)
```

#### 2.4 Update Presentation Layer (API Routes)

**Files:**
- `backend/app/presentation/routes/pipeline.py`
- `backend/app/presentation/routes/stocks.py`
- `backend/app/presentation/routes/admin.py` (if exists)

**Actions:**
1. Replace all `datetime.utcnow()` with `utc_now()`
2. Ensure all timestamp fields in Pydantic schemas use ISO 8601 strings
3. Add response model serialization config for datetime fields

**Example Refactor:**
```python
# OLD (pipeline.py line 166, 310)
end_date = datetime.utcnow()
"timestamp": datetime.utcnow().isoformat()

# NEW
from app.utils.timezone import utc_now
end_date = utc_now()
"timestamp": utc_now().isoformat()
```

#### 2.5 Update Data Access Layer

**Files:**
- `backend/app/data_access/repositories/stock_repository.py`
- `backend/app/data_access/repositories/sentiment_repository.py`

**Actions:**
1. Replace `datetime.utcnow()` with `utc_now()`
2. Ensure all datetime filters use timezone-aware UTC

---

## Phase 3: Dynamic Timezone Configuration (2-3 hours)

### Outcome
System supports configurable user timezone preference via environment variables.

### Tasks

#### 3.1 Add Configuration Settings

**File:** `backend/app/infrastructure/config/settings.py`

**Actions:**
Add new timezone configuration fields:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # Timezone Configuration
    default_user_timezone: str = Field(
        default="Asia/Kuala_Lumpur",
        description="Default timezone for user-facing displays (IANA timezone name)"
    )
    
    # Optional: Allow per-user timezone preferences in future
    enable_user_timezone_preference: bool = Field(
        default=False,
        description="Enable per-user timezone preference (future feature)"
    )
```

#### 3.2 Create Timezone Configuration Service

**New File:** `backend/app/service/timezone_service.py`

```python
"""
Timezone Service
================
Provides timezone configuration and conversion for API responses.
"""
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from app.infrastructure.config.settings import get_settings
from app.utils.timezone import ensure_utc

class TimezoneService:
    """Service for timezone configuration and conversion."""
    
    def __init__(self):
        self.settings = get_settings()
    
    def get_user_timezone(self, user_timezone_override: Optional[str] = None) -> ZoneInfo:
        """
        Get user timezone preference.
        
        Args:
            user_timezone_override: Optional user-specific timezone override
        
        Returns:
            ZoneInfo object for user's timezone
        """
        tz_name = user_timezone_override or self.settings.default_user_timezone
        
        try:
            return ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            # Fallback to UTC if timezone not found
            return ZoneInfo("UTC")
    
    def format_for_user(
        self, 
        utc_datetime: Optional[datetime],
        user_timezone_override: Optional[str] = None,
        format_str: Optional[str] = None
    ) -> Optional[str]:
        """
        Format UTC datetime for user's timezone.
        
        NOTE: This should generally NOT be used in API responses.
        API should return UTC ISO strings and let frontend handle display.
        This is for server-side rendering or email notifications only.
        
        Args:
            utc_datetime: UTC datetime to format
            user_timezone_override: Optional user-specific timezone
            format_str: Optional strftime format string
        
        Returns:
            Formatted datetime string in user's timezone
        """
        if utc_datetime is None:
            return None
        
        utc_dt = ensure_utc(utc_datetime)
        user_tz = self.get_user_timezone(user_timezone_override)
        
        local_dt = utc_dt.astimezone(user_tz)
        
        if format_str:
            return local_dt.strftime(format_str)
        else:
            # Return ISO format with user's timezone
            return local_dt.isoformat()

# Singleton instance
_timezone_service = None

def get_timezone_service() -> TimezoneService:
    """Get timezone service singleton."""
    global _timezone_service
    if _timezone_service is None:
        _timezone_service = TimezoneService()
    return _timezone_service
```

#### 3.3 Update Environment Configuration

**File:** `.env` (create if not exists)

```bash
# Timezone Configuration
DEFAULT_USER_TIMEZONE=Asia/Kuala_Lumpur

# Alternative examples:
# DEFAULT_USER_TIMEZONE=America/New_York
# DEFAULT_USER_TIMEZONE=Europe/London
# DEFAULT_USER_TIMEZONE=UTC
```

**File:** `README.md` or `docs/CONFIGURATION.md`

Add documentation:
```markdown
### Timezone Configuration

The system stores all timestamps in UTC internally and in the database.
User-facing timestamps can be displayed in a configurable timezone.

**Environment Variable:**
- `DEFAULT_USER_TIMEZONE`: IANA timezone name (default: `Asia/Kuala_Lumpur`)
  - Examples: `Asia/Tokyo`, `America/New_York`, `Europe/London`, `UTC`
  - See full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

**Note:** Frontend is responsible for timezone conversion and display.
Backend APIs always return UTC timestamps in ISO 8601 format.
```

---

## Phase 4: API Response Standardization (2-3 hours)

### Outcome
All API endpoints return consistent UTC ISO 8601 timestamps.

### Tasks

#### 4.1 Create Response Serialization Utilities

**File:** `backend/app/presentation/schemas/base.py`

```python
"""
Base schemas with consistent datetime serialization
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_serializer

class TimestampMixin(BaseModel):
    """Mixin for models with timestamp fields."""
    
    @field_serializer('*', mode='plain')
    def serialize_datetime(self, value, _info):
        """
        Serialize all datetime fields to ISO 8601 UTC strings.
        
        Automatically handles:
        - datetime objects → ISO string with UTC timezone
        - None → None
        - Other types → as-is
        """
        if isinstance(value, datetime):
            from app.utils.timezone import to_iso_string
            return to_iso_string(value)
        return value

class BaseResponseSchema(TimestampMixin):
    """Base schema for all API responses with consistent datetime handling."""
    
    class Config:
        json_encoders = {
            datetime: lambda v: to_iso_string(v) if v else None
        }
```

#### 4.2 Update Response Schemas

**Files:**
- `backend/app/presentation/schemas/*.py` (all schema files)

**Actions:**
1. Inherit from `BaseResponseSchema` for all response models
2. Add type hints for all timestamp fields as `datetime`
3. Remove manual `.isoformat()` calls in route handlers

**Example:**
```python
# OLD
class StockSummaryResponse(BaseModel):
    symbol: str
    last_updated: str  # Manual string field

# In route handler:
return {
    "symbol": stock.symbol,
    "last_updated": stock.updated_at.isoformat() if stock.updated_at else None
}

# NEW
from app.presentation.schemas.base import BaseResponseSchema

class StockSummaryResponse(BaseResponseSchema):
    symbol: str
    last_updated: Optional[datetime] = None  # Type-safe datetime field

# In route handler:
return StockSummaryResponse(
    symbol=stock.symbol,
    last_updated=stock.updated_at  # Auto-serialized by Pydantic
)
```

#### 4.3 Update All Route Handlers

**Files:**
- `backend/app/presentation/routes/stocks.py`
- `backend/app/presentation/routes/pipeline.py`
- `backend/app/presentation/routes/admin.py`
- `backend/app/presentation/routes/system.py`

**Actions:**
1. Remove manual timestamp formatting
2. Return datetime objects directly in responses
3. Let Pydantic schemas handle serialization

#### 4.4 Add Response Validation

**New File:** `backend/tests/test_api_response_timestamps.py`

```python
"""
Test API response timestamp format consistency
"""
import pytest
from datetime import datetime

def test_timestamp_format_is_iso8601_utc(client):
    """All API timestamp fields should be ISO 8601 UTC strings."""
    response = client.get("/api/stocks/summary")
    data = response.json()
    
    # Check timestamp format
    if 'last_updated' in data:
        timestamp = data['last_updated']
        # Should parse as ISO 8601
        dt = datetime.fromisoformat(timestamp)
        # Should be UTC (ends with +00:00 or Z)
        assert timestamp.endswith('+00:00') or timestamp.endswith('Z')

def test_all_endpoints_return_utc_timestamps(client):
    """Verify all endpoints return UTC timestamps."""
    endpoints = [
        "/api/stocks/summary",
        "/api/system/status",
        "/api/admin/logs",
        # ... add all endpoints with timestamps
    ]
    
    for endpoint in endpoints:
        response = client.get(endpoint)
        # Verify all datetime fields are UTC ISO strings
        # ... validation logic
```

---

## Phase 5: Frontend Timezone Handling (3-4 hours)

### Outcome
Frontend dynamically converts UTC timestamps to user's preferred timezone.

### Tasks

#### 5.1 Refactor Timezone Utilities

**File:** `src/shared/utils/timezone.ts`

**Complete Rewrite:**

```typescript
/**
 * Timezone Utilities for Frontend
 * ================================
 * 
 * Handles conversion of UTC timestamps from API to user's preferred timezone.
 * Timezone preference can be configured via environment variable.
 * 
 * Architecture:
 * - API always sends UTC ISO 8601 timestamps
 * - Frontend converts to user's timezone for display
 * - Never modify timestamps before sending to API
 */

// Get user timezone from environment or browser default
const getUserTimezone = (): string => {
  // Check environment variable first (e.g., VITE_USER_TIMEZONE)
  const envTimezone = import.meta.env.VITE_USER_TIMEZONE;
  
  if (envTimezone) {
    return envTimezone;
  }
  
  // Fallback to browser's timezone
  try {
    return Intl.DateTimeFormat().resolvedOptions().timeZone;
  } catch {
    // Ultimate fallback
    return 'UTC';
  }
};

export const USER_TIMEZONE = getUserTimezone();

/**
 * Format UTC timestamp for display in user's timezone
 */
export const formatDateTime = (
  utcTimestamp: string | Date | null | undefined,
  options?: Intl.DateTimeFormatOptions
): string => {
  if (!utcTimestamp) {
    return 'Never';
  }

  try {
    const date = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
    
    if (isNaN(date.getTime())) {
      console.warn('Invalid timestamp:', utcTimestamp);
      return 'Invalid Date';
    }

    const defaultOptions: Intl.DateTimeFormatOptions = {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      timeZoneName: 'short',
      timeZone: USER_TIMEZONE,
    };

    return date.toLocaleString('en-US', { ...defaultOptions, ...options });
  } catch (error) {
    console.error('Error formatting datetime:', error, utcTimestamp);
    return 'Error formatting date';
  }
};

/**
 * Format date only (no time)
 */
export const formatDate = (utcTimestamp: string | Date | null | undefined): string => {
  return formatDateTime(utcTimestamp, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: USER_TIMEZONE,
  });
};

/**
 * Format time only (no date)
 */
export const formatTime = (utcTimestamp: string | Date | null | undefined): string => {
  return formatDateTime(utcTimestamp, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: USER_TIMEZONE,
  });
};

/**
 * Get current time in user's timezone
 */
export const getCurrentTime = (): string => {
  return formatDateTime(new Date());
};

/**
 * Validate if a timestamp string is valid
 */
export const isValidTimestamp = (timestamp: string | Date | null | undefined): boolean => {
  if (!timestamp) return false;
  try {
    const date = typeof timestamp === 'string' ? new Date(timestamp) : timestamp;
    return !isNaN(date.getTime());
  } catch {
    return false;
  }
};

/**
 * Get timezone info for display
 */
export const getTimezoneInfo = (): {
  timezone: string;
  offset: string;
  abbreviation: string;
} => {
  const now = new Date();
  const formatter = new Intl.DateTimeFormat('en-US', {
    timeZone: USER_TIMEZONE,
    timeZoneName: 'short',
  });
  
  const parts = formatter.formatToParts(now);
  const tzPart = parts.find(part => part.type === 'timeZoneName');
  
  return {
    timezone: USER_TIMEZONE,
    offset: new Date().toLocaleTimeString('en-US', {
      timeZone: USER_TIMEZONE,
      timeZoneName: 'longOffset'
    }).split(' ').pop() || '',
    abbreviation: tzPart?.value || '',
  };
};
```

#### 5.2 Update timeUtils.ts

**File:** `src/shared/utils/timeUtils.ts`

```typescript
/**
 * Time Utility Functions
 * ======================
 * Helper functions for time-related operations
 */

import { formatDateTime, isValidTimestamp } from './timezone';

/**
 * Calculate time difference and return human-readable string
 * Works with UTC timestamps from API
 */
export function formatTimeAgo(utcTimestamp: string | Date | null): string {
  if (!utcTimestamp || !isValidTimestamp(utcTimestamp)) {
    return 'Never';
  }

  try {
    const now = new Date();
    const past = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
    
    const diffMs = now.getTime() - past.getTime();
    
    if (diffMs < 0) {
      return 'In the future';
    }

    const diffSeconds = Math.floor(diffMs / 1000);
    const diffMinutes = Math.floor(diffSeconds / 60);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffSeconds < 60) {
      return 'Just now';
    } else if (diffMinutes < 60) {
      return `${diffMinutes} minute${diffMinutes !== 1 ? 's' : ''} ago`;
    } else if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    } else if (diffDays < 30) {
      return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
    } else {
      // For older dates, show full date in user's timezone
      return formatDateTime(past, {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    }
  } catch (error) {
    console.error('Error in formatTimeAgo:', error, utcTimestamp);
    return 'Unable to format';
  }
}

/**
 * Check if timestamp is within last N hours
 */
export function isWithinHours(utcTimestamp: string | Date | null, hours: number): boolean {
  if (!utcTimestamp || !isValidTimestamp(utcTimestamp)) {
    return false;
  }

  const now = new Date();
  const past = new Date(utcTimestamp);
  const diffHours = (now.getTime() - past.getTime()) / (1000 * 60 * 60);

  return diffHours >= 0 && diffHours <= hours;
}
```

#### 5.3 Update Frontend Components

**Actions for ALL Components:**

1. Replace `formatMalaysiaTime` → `formatDateTime`
2. Replace `formatMalaysiaDate` → `formatDate`
3. Replace manual `toLocaleString()` → use `formatDateTime` with options
4. Update imports to use new timezone utilities

**Example Refactors:**

**File:** `src/features/admin/pages/SystemLogs.tsx` (line 466)

```typescript
// OLD
return timestamp.toLocaleString('en-MY', {
  timeZone: 'Asia/Kuala_Lumpur',
  // ... options
});

// NEW
import { formatDateTime } from '@/shared/utils/timezone';

return formatDateTime(timestamp, {
  // ... options (no timeZone needed, handled automatically)
});
```

**File:** `src/features/admin/pages/AdminDashboard.tsx` (line 530, 591)

```typescript
// OLD
{new Date(priceServiceStatus.service_status.next_market_open).toLocaleString('en-MY', {
  timeZone: 'Asia/Kuala_Lumpur'
})}

// NEW
import { formatDateTime } from '@/shared/utils/timezone';

{formatDateTime(priceServiceStatus.service_status.next_market_open)}
```

**File:** `src/features/admin/pages/ApiConfig.tsx` (line 193)

```typescript
// OLD
import { formatMalaysiaTime, formatMalaysiaDate } from "@/shared/utils/timezone";
Last test: {formatMalaysiaDate(config.last_test)}

// NEW
import { formatDate } from "@/shared/utils/timezone";
Last test: {formatDate(config.last_test)}
```

#### 5.4 Add Environment Variable Configuration

**File:** `.env` (root directory)

```bash
# User Timezone Configuration
# IANA timezone name - see https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
VITE_USER_TIMEZONE=Asia/Kuala_Lumpur

# Examples for other regions:
# VITE_USER_TIMEZONE=America/New_York
# VITE_USER_TIMEZONE=Europe/London
# VITE_USER_TIMEZONE=Asia/Tokyo
# VITE_USER_TIMEZONE=UTC
```

**File:** `.env.example`

```bash
# Timezone Configuration
VITE_USER_TIMEZONE=Asia/Kuala_Lumpur
```

#### 5.5 Update TypeScript Configuration

**File:** `src/vite-env.d.ts`

```typescript
/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  readonly VITE_ADMIN_EMAILS: string;
  readonly VITE_SESSION_TIMEOUT: string;
  
  // Timezone configuration
  readonly VITE_USER_TIMEZONE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
```

---

## Phase 6: Remove Hardcoded References (2-3 hours)

### Outcome
All static Malaysia timezone references eliminated.

### Tasks

#### 6.1 Backend Cleanup

**Files to Delete/Deprecate:**
- [ ] Remove `MALAYSIA_TZ` constant from `backend/app/utils/timezone.py`
- [ ] Remove `malaysia_now()` function
- [ ] Remove `utc_to_malaysia()` function
- [ ] Remove `malaysia_to_utc()` function
- [ ] Remove `format_malaysia_time()` function
- [ ] Remove `malaysia_isoformat()` function

**Deprecation Strategy:**
If immediate deletion causes issues, add deprecation warnings:

```python
import warnings

def malaysia_now() -> datetime:
    """
    DEPRECATED: Use utc_now() instead.
    This function will be removed in the next major version.
    """
    warnings.warn(
        "malaysia_now() is deprecated, use utc_now() from app.utils.timezone",
        DeprecationWarning,
        stacklevel=2
    )
    from app.utils.timezone import utc_now
    return utc_now()
```

#### 6.2 Frontend Cleanup

**Files to Update:**
- [ ] `src/shared/utils/timezone.ts` - complete rewrite (done in Phase 5)
- [ ] Remove all imports of old functions:
  - `formatMalaysiaTime` → `formatDateTime`
  - `formatMalaysiaDate` → `formatDate`
  - `formatMalaysiaTimeOnly` → `formatTime`
  - `getMalaysiaTime` → `getCurrentTime`

**Search and Replace Operations:**

```bash
# In src/ directory
# Find all usages of old functions
grep -r "formatMalaysiaTime" src/
grep -r "formatMalaysiaDate" src/
grep -r "MALAYSIA_TIMEZONE" src/
grep -r "Asia/Kuala_Lumpur" src/

# Replace with new functions
# formatMalaysiaTime → formatDateTime
# formatMalaysiaDate → formatDate
```

#### 6.3 Remove Hardcoded Locale

**Files with `toLocaleString('en-MY')`:**
- `src/features/admin/pages/SystemLogs.tsx`
- `src/features/admin/pages/AdminDashboard.tsx`

**Actions:**
Replace all `toLocaleString('en-MY', { timeZone: 'Asia/Kuala_Lumpur' })` with `formatDateTime()`

#### 6.4 Update Import Statements

**Before:**
```typescript
import { formatMalaysiaTime, formatMalaysiaDate, MALAYSIA_TIMEZONE } from "@/shared/utils/timezone";
```

**After:**
```typescript
import { formatDateTime, formatDate, formatTime } from "@/shared/utils/timezone";
```

---

## Phase 7: Database Schema Updates (1-2 hours)

### Outcome
Database models explicitly use timezone-aware UTC types.

### Tasks

#### 7.1 Review Current Schema

**File:** `backend/app/data_access/models/__init__.py`

**Current State:**
- All timestamp columns already use `DateTime(timezone=True)`
- `server_default=func.now()` may use system timezone (risk)

**Verification Needed:**
Check if SQLAlchemy's `func.now()` returns UTC or local time in your database.

#### 7.2 Update Server Defaults (If Needed)

If `func.now()` doesn't guarantee UTC, update to explicit UTC default:

```python
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from datetime import timezone

class StocksWatchlist(Base):
    # OLD
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # NEW (if func.now() is not UTC)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

**Note:** SQLite's `func.now()` returns UTC by default, but PostgreSQL may vary based on server configuration.

#### 7.3 Create Migration (If Schema Changes)

```bash
cd backend
alembic revision --autogenerate -m "Ensure all timestamps use UTC"
alembic upgrade head
```

#### 7.4 Data Migration Script (If Needed)

If existing data has timezone ambiguity, create a data migration script:

**New File:** `backend/scripts/migrate_timestamps_to_utc.py`

```python
"""
Migrate timestamps to ensure UTC consistency
"""
import asyncio
from sqlalchemy import select, update
from app.data_access.database.connection import get_db_session
from app.data_access.models import StocksWatchlist, SentimentData, StockPrice
from app.utils.timezone import ensure_utc

async def migrate_timestamps():
    """Ensure all timestamps are UTC timezone-aware."""
    async with get_db_session() as session:
        # Example: Update stocks_watchlist timestamps
        stocks = await session.execute(select(StocksWatchlist))
        
        for stock in stocks.scalars():
            if stock.created_at and stock.created_at.tzinfo is None:
                # Assume naive timestamps are UTC
                stock.created_at = ensure_utc(stock.created_at)
            if stock.updated_at and stock.updated_at.tzinfo is None:
                stock.updated_at = ensure_utc(stock.updated_at)
        
        await session.commit()
        print("Timestamp migration complete")

if __name__ == "__main__":
    asyncio.run(migrate_timestamps())
```

---

## Phase 8: Update Tests (3-4 hours)

### Outcome
All tests use UTC timestamps and timezone-aware assertions.

### Tasks

#### 8.1 Update Test Fixtures

**Files:**
- `backend/tests/conftest.py`

**Actions:**
Create UTC timestamp fixtures:

```python
import pytest
from datetime import datetime, timezone
from app.utils.timezone import utc_now

@pytest.fixture
def utc_timestamp():
    """Provide current UTC timestamp for tests."""
    return utc_now()

@pytest.fixture
def mock_utc_datetime(monkeypatch):
    """Mock datetime.now to return fixed UTC time."""
    fixed_time = datetime(2025, 11, 2, 14, 30, 45, tzinfo=timezone.utc)
    
    class MockDatetime:
        @classmethod
        def now(cls, tz=None):
            return fixed_time
    
    monkeypatch.setattr('datetime.datetime', MockDatetime)
    return fixed_time
```

#### 8.2 Update Test Files

**Files to Update:**
- `backend/tests/test_01_security_auth.py`
- `backend/tests/test_03_collector_encryption.py`
- `backend/tests/test_04_data_collection.py`
- `backend/tests/test_05_sentiment_analysis.py`
- `backend/tests/test_06_pipeline_orchestration.py`
- `backend/tests/test_08_integration_suite.py`

**Actions:**

1. Replace `datetime.utcnow()` with `utc_now()`:

```python
# OLD
from datetime import datetime
timestamp = datetime.utcnow()

# NEW
from app.utils.timezone import utc_now
timestamp = utc_now()
```

2. Update timestamp assertions:

```python
# OLD
assert item.timestamp > datetime.utcnow() - timedelta(hours=1)

# NEW
from app.utils.timezone import utc_now
assert item.timestamp > utc_now() - timedelta(hours=1)
```

3. Update mock data creation:

```python
# OLD
'timestamp': datetime.utcnow().isoformat()

# NEW
from app.utils.timezone import utc_now
'timestamp': utc_now().isoformat()
```

#### 8.3 Add Timezone-Specific Tests

**New File:** `backend/tests/test_timezone_handling.py`

```python
"""
Test timezone handling consistency
"""
import pytest
from datetime import datetime, timezone, timedelta
from app.utils.timezone import utc_now, ensure_utc, to_iso_string, parse_iso_string

def test_utc_now_returns_timezone_aware():
    """utc_now() should return timezone-aware UTC datetime."""
    now = utc_now()
    assert now.tzinfo is not None
    assert now.tzinfo == timezone.utc

def test_ensure_utc_with_naive_datetime():
    """ensure_utc() should convert naive datetime to UTC."""
    naive_dt = datetime(2025, 11, 2, 14, 30, 45)
    aware_dt = ensure_utc(naive_dt)
    
    assert aware_dt.tzinfo == timezone.utc
    assert aware_dt.year == 2025
    assert aware_dt.month == 11
    assert aware_dt.day == 2

def test_ensure_utc_with_other_timezone():
    """ensure_utc() should convert other timezones to UTC."""
    from zoneinfo import ZoneInfo
    
    # Create datetime in Malaysia time (UTC+8)
    myt_dt = datetime(2025, 11, 2, 22, 30, 45, tzinfo=ZoneInfo("Asia/Kuala_Lumpur"))
    
    # Convert to UTC
    utc_dt = ensure_utc(myt_dt)
    
    assert utc_dt.tzinfo == timezone.utc
    # 22:30 MYT = 14:30 UTC
    assert utc_dt.hour == 14

def test_to_iso_string_format():
    """to_iso_string() should return ISO 8601 UTC string."""
    dt = datetime(2025, 11, 2, 14, 30, 45, 123456, tzinfo=timezone.utc)
    iso_string = to_iso_string(dt)
    
    assert iso_string is not None
    assert '+00:00' in iso_string or 'Z' in iso_string.upper()
    assert '2025-11-02' in iso_string
    assert '14:30:45' in iso_string

def test_parse_iso_string_roundtrip():
    """parse_iso_string() should parse ISO string back to UTC datetime."""
    original_dt = utc_now()
    iso_string = to_iso_string(original_dt)
    parsed_dt = parse_iso_string(iso_string)
    
    assert parsed_dt is not None
    assert parsed_dt.tzinfo == timezone.utc
    # Should be within 1 second (microsecond precision)
    assert abs((parsed_dt - original_dt).total_seconds()) < 1

def test_api_response_timestamp_format(client):
    """API responses should return UTC ISO 8601 timestamps."""
    response = client.get("/api/system/status")
    data = response.json()
    
    # Check timestamp fields
    if 'last_collection' in data.get('metrics', {}):
        timestamp = data['metrics']['last_collection']
        # Should be parseable as ISO 8601
        dt = parse_iso_string(timestamp)
        assert dt is not None
        assert dt.tzinfo == timezone.utc
```

#### 8.4 Frontend Test Updates

If you have frontend tests (Jest/Vitest):

**File:** `src/shared/utils/__tests__/timezone.test.ts`

```typescript
import { describe, it, expect } from 'vitest';
import { formatDateTime, formatDate, formatTime, isValidTimestamp } from '../timezone';

describe('Timezone Utilities', () => {
  it('should format UTC timestamp correctly', () => {
    const utcTimestamp = '2025-11-02T14:30:45.000Z';
    const formatted = formatDateTime(utcTimestamp);
    
    expect(formatted).toBeTruthy();
    expect(formatted).not.toBe('Invalid Date');
  });

  it('should handle null/undefined timestamps', () => {
    expect(formatDateTime(null)).toBe('Never');
    expect(formatDateTime(undefined)).toBe('Never');
  });

  it('should validate timestamps correctly', () => {
    expect(isValidTimestamp('2025-11-02T14:30:45.000Z')).toBe(true);
    expect(isValidTimestamp('invalid')).toBe(false);
    expect(isValidTimestamp(null)).toBe(false);
  });

  it('should format date without time', () => {
    const utcTimestamp = '2025-11-02T14:30:45.000Z';
    const formatted = formatDate(utcTimestamp);
    
    expect(formatted).toContain('Nov');
    expect(formatted).toContain('2');
    expect(formatted).toContain('2025');
    expect(formatted).not.toContain(':');
  });
});
```

---

## Phase 9: Validation and Testing (2-3 hours)

### Outcome
Complete system verification of timezone handling.

### Tasks

#### 9.1 Manual Testing Checklist

**Backend API Testing:**

- [ ] Test `/api/system/status` - verify timestamps are UTC ISO 8601
- [ ] Test `/api/stocks/summary` - verify last_updated is UTC
- [ ] Test `/api/admin/logs` - verify log timestamps are UTC
- [ ] Test pipeline execution - verify all logged timestamps are UTC
- [ ] Test data collection - verify collected data timestamps are UTC

**Frontend Display Testing:**

- [ ] Dashboard: Verify "Last updated" shows user timezone
- [ ] Admin Dashboard: Verify all timestamps display in user timezone
- [ ] System Logs: Verify log timestamps display in user timezone
- [ ] Model Accuracy: Verify evaluation timestamps display correctly
- [ ] Scheduler Manager: Verify job run times display correctly

**Configuration Testing:**

- [ ] Change `VITE_USER_TIMEZONE` to different values, verify display updates
- [ ] Test with `UTC` timezone
- [ ] Test with `America/New_York` timezone
- [ ] Test with `Europe/London` timezone
- [ ] Test without `VITE_USER_TIMEZONE` (should use browser default)

#### 9.2 Automated Test Suite

**Run Backend Tests:**
```bash
cd backend
pytest tests/test_timezone_handling.py -v
pytest tests/ -k "timestamp" -v
pytest tests/ -v  # Run all tests
```

**Run Frontend Tests:**
```bash
npm run test  # Or vitest
```

#### 9.3 Integration Testing

**Test Scenario 1: End-to-End Pipeline**
1. Run full data collection pipeline
2. Verify all timestamps in database are UTC
3. Check API responses return UTC ISO strings
4. Verify frontend displays in user timezone

**Test Scenario 2: Timezone Configuration Change**
1. Set `DEFAULT_USER_TIMEZONE=America/New_York` in backend
2. Set `VITE_USER_TIMEZONE=America/New_York` in frontend
3. Verify timestamps display in EST/EDT
4. Change back to Asia/Kuala_Lumpur
5. Verify timestamps update correctly

**Test Scenario 3: Cross-Timezone Data Collection**
1. Collect data with current configuration
2. Change timezone configuration
3. Query old data
4. Verify timestamps display correctly in new timezone

#### 9.4 Performance Testing

**Database Query Performance:**
```python
# Test that timezone-aware queries are efficient
import time
from app.utils.timezone import utc_now
from datetime import timedelta

start_time = time.time()

# Query last 24 hours of data
cutoff = utc_now() - timedelta(days=1)
results = await sentiment_repo.get_recent_sentiment(cutoff)

elapsed = time.time() - start_time
assert elapsed < 1.0, f"Query took {elapsed}s, should be < 1s"
```

#### 9.5 Create Validation Report

**New File:** `docs/TIMEZONE_VALIDATION_REPORT.md`

```markdown
# Timezone Standardization Validation Report

## Test Summary
- Date: [Date]
- Tester: [Name]
- Environment: [Development/Staging/Production]

## Backend Validation

### API Response Format
- [ ] All timestamp fields return ISO 8601 format
- [ ] All timestamps include timezone information (+00:00 or Z)
- [ ] No timestamps return naive datetime strings

### Database Storage
- [ ] All timestamp columns are timezone-aware
- [ ] All timestamps stored as UTC
- [ ] No naive datetimes in database

### Code Compliance
- [ ] No usage of `datetime.utcnow()` (deprecated)
- [ ] All datetime creation uses `utc_now()`
- [ ] No hardcoded Malaysia timezone references

## Frontend Validation

### Display Consistency
- [ ] All timestamps display in configured user timezone
- [ ] Timezone abbreviation shown correctly
- [ ] Relative times (e.g., "2 hours ago") work correctly

### Configuration
- [ ] `VITE_USER_TIMEZONE` environment variable respected
- [ ] Fallback to browser timezone works
- [ ] Changing timezone updates display without cache issues

## Test Results

| Component | Test Case | Status | Notes |
|-----------|-----------|--------|-------|
| API /system/status | Timestamp format | ✅ Pass | |
| Dashboard | Last updated display | ✅ Pass | |
| Admin Logs | Log timestamp display | ✅ Pass | |
| ... | ... | ... | |

## Issues Found

1. [Issue description]
   - Severity: High/Medium/Low
   - Status: Fixed/In Progress/Backlog
   
## Recommendations

1. [Recommendation 1]
2. [Recommendation 2]

## Sign-off

- Backend Lead: [Name] - [Date]
- Frontend Lead: [Name] - [Date]
- QA: [Name] - [Date]
```

---

## Rollback Plan

### If Issues Occur During Implementation

#### Phase 1-2 Rollback (Backend Changes)
1. Revert Git commits for timezone utility changes
2. Restore old `timezone.py` file from backup
3. Revert business/service layer changes
4. Run database rollback if migrations were applied:
   ```bash
   alembic downgrade -1
   ```

#### Phase 3-5 Rollback (Frontend Changes)
1. Revert Git commits for frontend utility changes
2. Restore old `timezone.ts` and `timeUtils.ts` from backup
3. Revert component changes
4. Clear browser cache and rebuild:
   ```bash
   npm run build
   ```

#### Database Rollback
```bash
cd backend
alembic downgrade [revision_hash]
```

#### Emergency Hotfix
If production is affected:
1. Deploy last known good version
2. Clear Redis cache if using caching
3. Restart backend services
4. Monitor error logs

---

## Post-Implementation Checklist

### Documentation Updates

- [ ] Update `README.md` with timezone configuration instructions
- [ ] Update `docs/BACKEND_REFERENCE.md` with new timezone utilities
- [ ] Update `docs/FRONTEND_INTEGRATION_PLAN.md` if needed
- [ ] Update `FYP-Report.md` if timezone handling is documented
- [ ] Create `docs/TIMEZONE_GUIDE.md` for future developers

### Code Quality

- [ ] All linting errors resolved
- [ ] All type errors resolved (TypeScript strict mode)
- [ ] No deprecation warnings in console
- [ ] Code coverage maintained or improved

### Deployment

- [ ] Update `.env.example` files with timezone configuration
- [ ] Update deployment scripts if needed
- [ ] Document timezone configuration in deployment guide
- [ ] Test deployment in staging environment

### Monitoring

- [ ] Add logging for timezone conversions if needed
- [ ] Monitor error rates after deployment
- [ ] Set up alerts for timestamp parsing errors
- [ ] Review logs for timezone-related warnings

---

## Benefits After Implementation

### Technical Benefits

1. **Standards Compliance**: Follows industry best practices (UTC storage, ISO 8601)
2. **Maintainability**: Single source of truth for timezone handling
3. **Scalability**: Easy to support multiple user timezones in future
4. **Testability**: Timezone logic centralized and testable
5. **Future-Proof**: Ready for Python 3.12+ (deprecated datetime.utcnow removed)

### User Benefits

1. **Consistency**: All timestamps display in user's preferred timezone
2. **Clarity**: Timezone abbreviations shown explicitly
3. **Configurability**: Users can set preferred timezone via environment variable
4. **Accuracy**: No more UTC/MYT confusion

### Development Benefits

1. **Clear Separation**: Backend handles storage, frontend handles display
2. **No Magic**: No implicit timezone conversions
3. **Easy Debugging**: All timestamps traceable to UTC source
4. **Reduced Bugs**: Eliminates timezone-related edge cases

---

## Timeline Estimate

| Phase | Duration | Dependencies | Team |
|-------|----------|--------------|------|
| Phase 1: Audit | 1-2 hours | None | Backend + Frontend |
| Phase 2: Backend UTC | 4-6 hours | Phase 1 | Backend |
| Phase 3: Configuration | 2-3 hours | Phase 2 | Backend + DevOps |
| Phase 4: API Standardization | 2-3 hours | Phase 2, 3 | Backend |
| Phase 5: Frontend | 3-4 hours | Phase 4 | Frontend |
| Phase 6: Cleanup | 2-3 hours | Phase 2, 5 | Backend + Frontend |
| Phase 7: Database | 1-2 hours | Phase 2 | Backend |
| Phase 8: Tests | 3-4 hours | Phase 2-7 | Backend + Frontend |
| Phase 9: Validation | 2-3 hours | All | QA + All |

**Total Estimated Time:** 20-30 hours

**Recommended Approach:** 
- Complete Phases 1-4 (Backend) in one session
- Complete Phases 5-6 (Frontend) in another session  
- Complete Phases 7-9 (Finalization) in final session

---

## Success Criteria

### Must Have
- ✅ All database timestamps stored in UTC
- ✅ All API responses return UTC ISO 8601 timestamps
- ✅ Frontend displays timestamps in configured user timezone
- ✅ No hardcoded Malaysia timezone references
- ✅ All tests pass with new timezone handling
- ✅ No regressions in existing functionality

### Should Have
- ✅ Timezone configurable via environment variable
- ✅ Clear documentation for timezone configuration
- ✅ Logging for timezone operations
- ✅ Performance maintained or improved

### Nice to Have
- ✅ Per-user timezone preferences (future feature)
- ✅ Timezone selector in UI (future feature)
- ✅ Automatic timezone detection (future feature)

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking existing API contracts | Medium | High | Thorough testing, gradual rollout |
| Data migration issues | Low | High | Backup database, test migration script |
| Frontend display bugs | Medium | Medium | Comprehensive UI testing |
| Performance regression | Low | Medium | Performance testing, query optimization |
| User confusion during transition | Low | Low | Clear documentation, changelog |

---

## Support and Maintenance

### After Implementation

1. **Monitor Error Logs**: Watch for timezone parsing errors in first week
2. **User Feedback**: Collect feedback on timestamp display
3. **Documentation**: Ensure all developers understand new timezone system
4. **Training**: Brief team on new timezone utilities and best practices

### Long-Term Maintenance

1. **Regular Review**: Periodically audit timezone handling code
2. **Update Dependencies**: Keep `zoneinfo` and timezone libraries updated
3. **Best Practices**: Enforce timezone standards in code reviews
4. **Testing**: Include timezone tests in CI/CD pipeline

---

## Appendix

### A. Timezone Standards Reference

**ISO 8601 Format:**
```
2025-11-02T14:30:45.123456+00:00  (UTC with explicit +00:00)
2025-11-02T14:30:45.123456Z       (UTC with Z suffix)
```

**IANA Timezone Database:**
- Full list: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
- Examples: `Asia/Kuala_Lumpur`, `America/New_York`, `Europe/London`, `UTC`

### B. Python Timezone Best Practices

```python
# ✅ GOOD: Timezone-aware UTC
from datetime import datetime, timezone
now = datetime.now(timezone.utc)

# ❌ BAD: Deprecated in Python 3.12+
now = datetime.utcnow()  # Returns naive datetime

# ✅ GOOD: Parse ISO string with timezone
dt = datetime.fromisoformat("2025-11-02T14:30:45+00:00")

# ❌ BAD: Parse without timezone handling
dt = datetime.strptime(s, "%Y-%m-%d %H:%M:%S")  # Naive datetime
```

### C. JavaScript Timezone Best Practices

```typescript
// ✅ GOOD: Parse ISO string (automatically handles timezone)
const date = new Date("2025-11-02T14:30:45.000Z");

// ✅ GOOD: Format with specific timezone
const formatted = date.toLocaleString('en-US', {
  timeZone: 'Asia/Kuala_Lumpur'
});

// ❌ BAD: Manual timezone offset calculation
const offset = 8 * 60 * 60 * 1000;  // Hardcoded UTC+8
const localDate = new Date(date.getTime() + offset);
```

### D. SQLAlchemy Timezone Configuration

```python
# Ensure PostgreSQL returns UTC timestamps
from sqlalchemy import create_engine

engine = create_engine(
    "postgresql://...",
    connect_args={
        "options": "-c timezone=utc"
    }
)

# For SQLite (UTC by default, but explicit)
engine = create_engine("sqlite:///...", echo=False)
# SQLite's datetime() function returns UTC
```

### E. Common Timezone Pitfalls

1. **Mixing Naive and Aware Datetimes**
   - Always use timezone-aware datetimes
   - Never compare naive with aware datetimes

2. **Assuming Local Time**
   - Never assume datetime.now() is UTC
   - Always specify timezone explicitly

3. **Ignoring DST**
   - Use proper timezone libraries (zoneinfo, pytz)
   - Don't hardcode UTC offsets

4. **Browser Timezone Assumptions**
   - User's browser may be in different timezone than preference
   - Always allow timezone configuration

---

## Conclusion

This implementation plan provides a comprehensive, phased approach to resolving timezone conflicts in the Insight Stock Dashboard system. By following this plan:

1. **Eliminates Confusion**: Single source of truth (UTC in backend/database)
2. **Improves Flexibility**: Dynamic timezone configuration
3. **Enhances User Experience**: Displays in user's preferred timezone
4. **Ensures Maintainability**: Clear separation of concerns
5. **Future-Proofs System**: Ready for multi-timezone support

The plan is designed to be executed incrementally with clear rollback points, minimizing risk while maximizing benefits.

---

**Document Version:** 1.0  
**Last Updated:** November 2, 2025  
**Next Review:** After Phase 9 completion
