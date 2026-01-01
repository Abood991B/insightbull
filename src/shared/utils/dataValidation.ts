/**
 * Data Validation Utilities
 * 
 * Helper functions to validate data from backend and determine
 * appropriate UI states (empty, partial, full data).
 * 
 * Critical for handling empty database state before pipeline runs.
 */

export interface DataValidationResult {
  isValid: boolean;
  isEmpty: boolean;
  isPartial: boolean;
  message?: string;
  severity: 'error' | 'warning' | 'info' | 'success';
}

/**
 * Validate dashboard data
 * Checks if dashboard has any sentiment data collected
 */
export function validateDashboardData(data: any): DataValidationResult {
  if (!data) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No data received from backend',
      severity: 'error'
    };
  }

  if (data.top_stocks?.length === 0 && data.system_status?.total_sentiment_records === 0) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'Pipeline has not run yet. No sentiment data collected.',
      severity: 'info'
    };
  }

  if (data.top_stocks?.length > 0 && data.top_stocks.length < 5) {
    return {
      isValid: true,
      isEmpty: false,
      isPartial: true,
      message: 'Limited stock data available',
      severity: 'warning'
    };
  }

  return {
    isValid: true,
    isEmpty: false,
    isPartial: false,
    severity: 'success'
  };
}
