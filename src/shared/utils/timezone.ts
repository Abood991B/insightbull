/**
 * Timezone utilities for Malaysia/Kuala Lumpur time formatting
 */

// Malaysia timezone identifier
export const MALAYSIA_TIMEZONE = 'Asia/Kuala_Lumpur';

/**
 * Format date/time in Malaysia timezone
 */
export const formatMalaysiaTime = (
  dateString: string | Date | null | undefined,
  options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZoneName: 'short'
  }
): string => {
  try {
    // Handle null/undefined values
    if (!dateString) {
      return 'Never';
    }
    
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    
    // Check if date is valid
    if (isNaN(date.getTime())) {
      return 'Invalid Date';
    }
    
    return date.toLocaleString('en-MY', {
      ...options,
      timeZone: MALAYSIA_TIMEZONE
    });
  } catch (error) {
    console.error('Error formatting Malaysia time:', error);
    return 'Invalid Date';
  }
};

/**
 * Format date only in Malaysia timezone
 */
export const formatMalaysiaDate = (dateString: string | Date | null | undefined): string => {
  return formatMalaysiaTime(dateString, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    timeZone: MALAYSIA_TIMEZONE
  });
};

/**
 * Format time only in Malaysia timezone
 */
export const formatMalaysiaTimeOnly = (dateString: string | Date): string => {
  return formatMalaysiaTime(dateString, {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
    timeZone: MALAYSIA_TIMEZONE
  });
};

/**
 * Get current time in Malaysia timezone
 */
export const getMalaysiaTime = (): string => {
  return formatMalaysiaTime(new Date());
};

/**
 * Check if a date string is valid
 */
export const isValidDate = (dateString: string | Date): boolean => {
  try {
    const date = typeof dateString === 'string' ? new Date(dateString) : dateString;
    return !isNaN(date.getTime());
  } catch {
    return false;
  }
};