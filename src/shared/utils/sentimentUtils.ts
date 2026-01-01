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
