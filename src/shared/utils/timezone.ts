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

// DEPRECATED - Legacy functions for backward compatibility
// These will be removed in future versions

/** @deprecated Use formatDateTime instead */
export const formatMalaysiaTime = formatDateTime;

/** @deprecated Use formatDate instead */
export const formatMalaysiaDate = formatDate;

/** @deprecated Use formatTime instead */
export const formatMalaysiaTimeOnly = formatTime;

/** @deprecated Use getCurrentTime instead */
export const getMalaysiaTime = getCurrentTime;

/** @deprecated Use isValidTimestamp instead */
export const isValidDate = isValidTimestamp;

/** @deprecated Use USER_TIMEZONE instead */
export const MALAYSIA_TIMEZONE = USER_TIMEZONE;