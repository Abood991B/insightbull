/**
 * Sentiment Utility Functions
 * Provides consistent sentiment classification and formatting across the application
 */

/**
 * Sentiment thresholds matching backend logic
 * These values determine how sentiment scores are classified into labels
 * Updated to 0.05 to better capture weak sentiment signals
 */
export const SENTIMENT_THRESHOLDS = {
  POSITIVE: 0.05,    // Scores > 0.05 are positive
  NEGATIVE: -0.05,   // Scores < -0.05 are negative
  // Between -0.05 and 0.05 is neutral
} as const;

/**
 * Get sentiment label from numeric score
 * Matches backend classification logic
 * 
 * @param score Sentiment score from -1.0 to 1.0
 * @returns Sentiment label: "Positive", "Neutral", or "Negative"
 */
export function getSentimentLabel(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'Unknown';
  
  if (score > SENTIMENT_THRESHOLDS.POSITIVE) return 'Positive';
  if (score < SENTIMENT_THRESHOLDS.NEGATIVE) return 'Negative';
  return 'Neutral';
}

/**
 * Get color class for sentiment display
 * 
 * @param score Sentiment score from -1.0 to 1.0
 * @returns Tailwind color class
 */
export function getSentimentColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'text-gray-600';
  
  if (score > SENTIMENT_THRESHOLDS.POSITIVE) return 'text-green-600';
  if (score < SENTIMENT_THRESHOLDS.NEGATIVE) return 'text-red-600';
  return 'text-yellow-600';
}

/**
 * Get background color class for sentiment display
 * 
 * @param score Sentiment score from -1.0 to 1.0
 * @returns Tailwind background color class
 */
export function getSentimentBgColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'bg-gray-100';
  
  if (score > SENTIMENT_THRESHOLDS.POSITIVE) return 'bg-green-100';
  if (score < SENTIMENT_THRESHOLDS.NEGATIVE) return 'bg-red-100';
  return 'bg-yellow-100';
}

/**
 * Get Badge variant for sentiment
 * 
 * @param score Sentiment score from -1.0 to 1.0
 * @returns Badge variant type
 */
export function getSentimentBadgeVariant(score: number | null | undefined): "default" | "destructive" | "secondary" | "outline" {
  if (score === null || score === undefined) return 'outline';
  
  if (score > SENTIMENT_THRESHOLDS.POSITIVE) return 'default';  // Green
  if (score < SENTIMENT_THRESHOLDS.NEGATIVE) return 'destructive';  // Red
  return 'secondary';  // Yellow/Gray
}

/**
 * Format sentiment score for display
 * 
 * @param score Sentiment score from -1.0 to 1.0
 * @param decimals Number of decimal places (default 2)
 * @returns Formatted score string
 */
export function formatSentimentScore(score: number | null | undefined, decimals: number = 2): string {
  if (score === null || score === undefined) return 'N/A';
  return score.toFixed(decimals);
}

/**
 * Format sentiment as percentage
 * 
 * @param score Sentiment score from -1.0 to 1.0
 * @returns Formatted percentage string
 */
export function formatSentimentPercentage(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'N/A';
  const percentage = Math.abs(score * 100);
  const sign = score >= 0 ? '+' : '-';
  return `${sign}${percentage.toFixed(0)}%`;
}

/**
 * Get emoji for sentiment (for visual enhancement)
 * 
 * @param score Sentiment score from -1.0 to 1.0
 * @returns Emoji string
 */
export function getSentimentEmoji(score: number | null | undefined): string {
  if (score === null || score === undefined) return '❔';
  
  if (score > SENTIMENT_THRESHOLDS.POSITIVE) return '😊';
  if (score < SENTIMENT_THRESHOLDS.NEGATIVE) return '😟';
  return '😐';
}
