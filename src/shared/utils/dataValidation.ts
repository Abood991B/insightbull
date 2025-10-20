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

  // Check if pipeline has run (no sentiment records)
  if (data.top_stocks?.length === 0 && data.system_status?.total_sentiment_records === 0) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'Pipeline has not run yet. No sentiment data collected.',
      severity: 'info'
    };
  }

  // Check for partial data
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

/**
 * Validate sentiment analysis data
 * Checks if sufficient data points exist for sentiment analysis
 * 
 * @param data - Sentiment data from backend
 * @param minPoints - Minimum recommended data points (default: 5)
 */
export function validateSentimentData(
  data: any,
  minPoints: number = 5
): DataValidationResult {
  if (!data || !data.data_points) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No sentiment data available',
      severity: 'error'
    };
  }

  const pointCount = data.data_points.length;

  if (pointCount === 0) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No data points collected for this stock/timeframe',
      severity: 'info'
    };
  }

  if (pointCount < minPoints) {
    return {
      isValid: true,
      isEmpty: false,
      isPartial: true,
      message: `Only ${pointCount} data points available. At least ${minPoints} recommended.`,
      severity: 'warning'
    };
  }

  // Check data quality if available
  if (data.statistics?.data_quality && data.statistics.data_quality < 50) {
    return {
      isValid: true,
      isEmpty: false,
      isPartial: true,
      message: `Low data quality: ${data.statistics.data_quality.toFixed(0)}%`,
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

/**
 * Validate correlation analysis data
 * Requires minimum data points for statistical significance
 * 
 * @param data - Correlation data from backend
 * @param minPoints - Minimum required data points (default: 10 for correlation)
 */
export function validateCorrelationData(
  data: any,
  minPoints: number = 10
): DataValidationResult {
  if (!data || !data.scatter_data) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No correlation data available',
      severity: 'error'
    };
  }

  const pointCount = data.scatter_data.length;

  if (pointCount < minPoints) {
    return {
      isValid: false,
      isEmpty: pointCount === 0,
      isPartial: pointCount > 0,
      message: `Need ${minPoints} data points for correlation. Currently have ${pointCount}.`,
      severity: pointCount === 0 ? 'error' : 'warning'
    };
  }

  // Check p-value significance (if available)
  if (data.p_value !== undefined && data.p_value > 0.05) {
    return {
      isValid: true,
      isEmpty: false,
      isPartial: true,
      message: 'Correlation is not statistically significant (p > 0.05)',
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

/**
 * Validate stock list
 * Checks if watchlist has any stocks
 */
export function validateStockList(stocks: any[]): DataValidationResult {
  if (!stocks || stocks.length === 0) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No stocks in watchlist',
      severity: 'info'
    };
  }

  const activeStocks = stocks.filter(s => s.is_active);
  if (activeStocks.length === 0) {
    return {
      isValid: false,
      isEmpty: false,
      isPartial: true,
      message: 'No active stocks in watchlist',
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

/**
 * Check if data is sufficient for specific analysis type
 */
export function hasSufficientData(
  dataPoints: number,
  analysisType: 'sentiment' | 'correlation' | 'trend'
): boolean {
  const minRequirements = {
    sentiment: 5,
    correlation: 10,
    trend: 7
  };

  return dataPoints >= minRequirements[analysisType];
}

/**
 * Get user-friendly message for data state
 */
export function getDataStateMessage(validation: DataValidationResult): string {
  if (validation.isEmpty) {
    return 'No data available. Run the data collection pipeline to get started.';
  }
  
  if (validation.isPartial) {
    return validation.message || 'Limited data available. Results may be less accurate.';
  }
  
  return 'Data loaded successfully.';
}

// ============================================================================
// TIMEFRAME & DATA SUFFICIENCY VALIDATION
// ============================================================================

/**
 * Minimum data points required for different analysis types
 */
export const MIN_DATA_POINTS = {
  CORRELATION: 5,      // Need at least 5 points for correlation
  TREND_ANALYSIS: 3,   // Need at least 3 points for trend
  COMPARISON: 2,       // Need at least 2 points for comparison
  SINGLE_POINT: 1,     // Need at least 1 point for display
} as const;

/**
 * Expected data points for each timeframe
 */
export const EXPECTED_DATA_POINTS = {
  '1d': { min: 1, max: 24, recommended: 5 },      // At least 1 point, up to 24 hourly
  '7d': { min: 5, max: 168, recommended: 10 },     // At least 5 points, up to 168 hourly
  '14d': { min: 10, max: 336, recommended: 20 },   // At least 10 points, up to 336 hourly
} as const;

/**
 * Check if data is sufficient for correlation analysis
 */
export function hasEnoughDataForCorrelation(dataPoints: number): boolean {
  return dataPoints >= MIN_DATA_POINTS.CORRELATION;
}

/**
 * Check if data is sufficient for trend analysis
 */
export function hasEnoughDataForTrends(dataPoints: number): boolean {
  return dataPoints >= MIN_DATA_POINTS.TREND_ANALYSIS;
}

/**
 * Check if data is sufficient for comparison
 */
export function hasEnoughDataForComparison(dataPoints: number): boolean {
  return dataPoints >= MIN_DATA_POINTS.COMPARISON;
}

/**
 * Get available timeframes based on data availability
 * @param availableDataPoints Number of data points available in database
 * @returns Array of timeframes that have sufficient data
 */
export function getAvailableTimeframes(availableDataPoints: number): Array<'1d' | '7d' | '14d'> {
  const timeframes: Array<'1d' | '7d' | '14d'> = [];
  
  // 1 day needs at least 1 data point
  if (availableDataPoints >= EXPECTED_DATA_POINTS['1d'].min) {
    timeframes.push('1d');
  }
  
  // 7 days needs at least 5 data points
  if (availableDataPoints >= EXPECTED_DATA_POINTS['7d'].min) {
    timeframes.push('7d');
  }
  
  // 14 days needs at least 10 data points
  if (availableDataPoints >= EXPECTED_DATA_POINTS['14d'].min) {
    timeframes.push('14d');
  }
  
  return timeframes;
}

/**
 * Get warning message for insufficient data
 */
export function getInsufficientDataMessage(
  currentPoints: number,
  requiredPoints: number,
  analysisType: 'correlation' | 'trend' | 'comparison' = 'correlation'
): string {
  const messages = {
    correlation: `Correlation analysis requires at least ${requiredPoints} data points. Currently only ${currentPoints} available.`,
    trend: `Trend analysis requires at least ${requiredPoints} data points. Currently only ${currentPoints} available.`,
    comparison: `Comparison requires at least ${requiredPoints} data points. Currently only ${currentPoints} available.`,
  };
  
  return messages[analysisType];
}

/**
 * Validate timeframe selection based on available data
 */
export function validateTimeframeSelection(
  selectedTimeframe: '1d' | '7d' | '14d',
  availableDataPoints: number
): { isValid: boolean; message?: string; suggestedTimeframe?: '1d' | '7d' | '14d' } {
  const availableTimeframes = getAvailableTimeframes(availableDataPoints);
  
  if (!availableTimeframes.includes(selectedTimeframe)) {
    const timeframeLabels = {
      '1d': '1 Day',
      '7d': '7 Days',
      '14d': '14 Days'
    };
    
    // Suggest the longest available timeframe
    const suggestedTimeframe = availableTimeframes[availableTimeframes.length - 1] || '1d';
    
    return {
      isValid: false,
      message: `Insufficient data for ${timeframeLabels[selectedTimeframe]}. Try "${timeframeLabels[suggestedTimeframe]}" or run the data collection pipeline.`,
      suggestedTimeframe
    };
  }
  
  return { isValid: true };
}

/**
 * Get recommended timeframe based on available data
 * Always defaults to shortest timeframe available
 */
export function getRecommendedTimeframe(availableDataPoints: number): '1d' | '7d' | '14d' {
  const available = getAvailableTimeframes(availableDataPoints);
  return available[0] || '1d';  // Return shortest available, default to 1d
}

/**
 * Calculate data quality score (0-100)
 */
export function calculateDataQualityScore(
  actualPoints: number,
  timeframe: '1d' | '7d' | '14d'
): number {
  const expected = EXPECTED_DATA_POINTS[timeframe];
  const ratio = actualPoints / expected.recommended;
  return Math.min(Math.round(ratio * 100), 100);
}

/**
 * Get timeframe options with disabled state
 */
export interface TimeframeOption {
  value: '1d' | '7d' | '14d';
  label: string;
  disabled: boolean;
  reason?: string;
}

export function getTimeframeOptions(availableDataPoints: number): TimeframeOption[] {
  const available = getAvailableTimeframes(availableDataPoints);
  
  return [
    {
      value: '1d',
      label: '1 Day',
      disabled: !available.includes('1d'),
      reason: available.includes('1d') ? undefined : `Need at least ${EXPECTED_DATA_POINTS['1d'].min} data points`
    },
    {
      value: '7d',
      label: '7 Days',
      disabled: !available.includes('7d'),
      reason: available.includes('7d') ? undefined : `Need at least ${EXPECTED_DATA_POINTS['7d'].min} data points`
    },
    {
      value: '14d',
      label: '14 Days',
      disabled: !available.includes('14d'),
      reason: available.includes('14d') ? undefined : `Need at least ${EXPECTED_DATA_POINTS['14d'].min} data points`
    }
  ];
}
