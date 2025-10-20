/**
 * Time Utility Functions
 * Provides consistent time formatting across the application
 */

/**
 * Calculate time difference and return human-readable string
 * Handles ISO 8601 timestamps with proper timezone awareness
 * @param timestamp ISO timestamp string or Date object
 * @returns Formatted time difference (e.g., "2 minutes ago", "3 hours ago")
 */
export function formatTimeAgo(timestamp: string | Date | null): string {
  if (!timestamp) return 'Never';
  
  try {
    const now = new Date();
    let past: Date;
    
    // Ensure we properly parse ISO strings
    if (typeof timestamp === 'string') {
      // Handle ISO 8601 format with potential timezone info
      past = new Date(timestamp);
      
      // Validate the date was parsed correctly
      if (isNaN(past.getTime())) {
        console.warn('Invalid timestamp format:', timestamp);
        return 'Invalid date';
      }
    } else {
      past = timestamp;
    }
    
    const diffMs = now.getTime() - past.getTime();
    
    // If difference is negative (future date), handle it
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
      return past.toLocaleDateString();
    }
  } catch (error) {
    console.error('Error formatting timestamp:', error, timestamp);
    return 'Unable to format';
  }
}

/**
 * Format timestamp as readable date string
 * @param timestamp ISO timestamp string or Date object
 * @returns Formatted date (e.g., "Oct 17, 2025 at 3:45 PM")
 */
export function formatDateTime(timestamp: string | Date | null): string {
  if (!timestamp) return 'N/A';
  
  const date = new Date(timestamp);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true
  });
}

/**
 * Check if timestamp is within last N hours
 * @param timestamp ISO timestamp string or Date object
 * @param hours Number of hours to check
 * @returns True if timestamp is within the specified hours
 */
export function isWithinHours(timestamp: string | Date | null, hours: number): boolean {
  if (!timestamp) return false;
  
  const now = new Date();
  const past = new Date(timestamp);
  const diffMs = now.getTime() - past.getTime();
  const diffHours = diffMs / (1000 * 60 * 60);
  
  return diffHours <= hours;
}
