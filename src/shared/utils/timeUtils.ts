/**
 * Time Utility Functions
 * ======================
 * Helper functions for time-related operations
 * Works with UTC timestamps from API
 */

import { formatDateTime as formatDateTimeWithTz, isValidTimestamp } from './timezone';

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
      return formatDateTimeWithTz(past, {
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

/**
 * Format timestamp as readable date string
 * NOTE: This function is kept for backward compatibility
 * Consider using formatDateTime from timezone.ts directly
 * @deprecated Use formatDateTime from timezone.ts instead
 */
export function formatDateTime(timestamp: string | Date | null): string {
  if (!timestamp) return 'N/A';
  
  return formatDateTimeWithTz(timestamp, {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
}
