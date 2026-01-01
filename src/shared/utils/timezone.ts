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

/**
 * Get user timezone from environment or browser default
 */
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
 * 
 * When custom options are provided, they REPLACE the defaults (not merge).
 * This allows for clean chart labels without year/seconds/timezone clutter.
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

    // If custom options provided, use them directly (only add timezone)
    // This allows clean chart labels without year/seconds/timezone clutter
    if (options) {
      return date.toLocaleString('en-US', { 
        ...options, 
        timeZone: options.timeZone || USER_TIMEZONE 
      });
    }

    // Default options for full datetime display
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

    return date.toLocaleString('en-US', defaultOptions);
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

// ============================================================================
// Time Utility Functions (merged from timeUtils.ts)
// ============================================================================

/**
 * Calculate time difference and return human-readable string
 * Works with UTC timestamps from API
 */
export function formatTimeAgo(utcTimestamp: string | Date | null): string {
  if (!utcTimestamp) {
    return 'Never';
  }
  
  // Validate timestamp
  try {
    const testDate = typeof utcTimestamp === 'string' ? new Date(utcTimestamp) : utcTimestamp;
    if (isNaN(testDate.getTime())) {
      return 'Never';
    }
  } catch {
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
