/**
 * Backend API Response Schemas
 * 
 * TypeScript interfaces matching EXACTLY with backend Pydantic schemas
 * Source: backend/app/presentation/schemas/
 * 
 * IMPORTANT: These interfaces MUST match backend implementation exactly.
 * Do NOT modify without corresponding backend schema changes.
 * 
 * Last Verified: October 17, 2025
 */

// ============================================================================
// DASHBOARD SCHEMAS (dashboard.py)
// ============================================================================

/**
 * Summary information for a stock displayed on dashboard
 * Backend: StockSummary in dashboard.py
 */
export interface StockSummary {
  symbol: string;                      // Stock symbol (e.g., AAPL)
  company_name: string;                // Company name
  current_price: number | null;        // Latest stock price
  price_change_24h: number | null;     // 24h price change percentage
  sentiment_score: number | null;      // Latest sentiment score (-1.0 to 1.0)
  sentiment_label: string | null;      // Sentiment label (positive/neutral/negative)
  last_updated: string | null;         // Last data update timestamp (ISO string)
}

/**
 * Overall market sentiment metrics
 * Backend: MarketSentimentOverview in dashboard.py
 */
export interface MarketSentimentOverview {
  average_sentiment: number;           // Market-wide average sentiment score
  positive_stocks: number;             // Number of stocks with positive sentiment
  neutral_stocks: number;              // Number of stocks with neutral sentiment
  negative_stocks: number;             // Number of stocks with negative sentiment
  total_stocks: number;                // Total number of tracked stocks
  last_updated: string;                // Last calculation timestamp (ISO string)
}

/**
 * System operational status
 * Backend: SystemStatus in dashboard.py
 */
export interface SystemStatus {
  pipeline_status: string;             // Data collection pipeline status (operational/delayed/stale/no_data)
  last_collection: string | null;      // Last successful data collection (ISO string)
  active_data_sources: string[];       // Currently active data sources (reddit, news)
  total_sentiment_records: number;     // Total sentiment records in database
}

/**
 * Complete dashboard summary response - Implements U-FR1
 * Backend: DashboardSummary in dashboard.py
 * Endpoint: GET /api/dashboard/summary
 */
export interface DashboardSummary {
  market_overview: MarketSentimentOverview;
  top_stocks: StockSummary[];          // Top performing stocks by sentiment
  recent_movers: StockSummary[];       // Stocks with significant recent changes
  system_status: SystemStatus;
  generated_at: string;                // Response generation timestamp (ISO string)
}

// ============================================================================
// STOCK SCHEMAS (stock.py)
// ============================================================================

/**
 * Individual price data point
 * Backend: PriceDataPoint in stock.py
 */
export interface PriceDataPoint {
  timestamp: string;                   // Price timestamp (ISO string)
  open_price: number | null;           // Opening price
  close_price: number;                 // Closing price
  high_price: number | null;           // Highest price
  low_price: number | null;            // Lowest price
  volume: number | null;               // Trading volume
}

/**
 * Individual sentiment data point
 * Backend: SentimentDataPoint in stock.py
 */
export interface SentimentDataPoint {
  timestamp: string;                   // Sentiment timestamp (ISO string)
  score: number;                       // Sentiment score (-1.0 to 1.0)
  label: string;                       // Sentiment label (positive/neutral/negative)
  confidence: number | null;           // Model confidence score
  source: string;                      // Data source (reddit, news, etc.)
}

/**
 * Statistical metrics for a stock
 * Backend: StockMetrics in stock.py
 */
export interface StockMetrics {
  avg_sentiment: number;               // Average sentiment score
  sentiment_volatility: number;        // Sentiment standard deviation
  price_change_percent: number | null; // Price change percentage
  total_sentiment_records: number;     // Number of sentiment records
  data_quality_score: number;          // Data quality score (0.0 to 1.0)
}

/**
 * Detailed stock information - Implements U-FR2 & U-FR3
 * Backend: StockDetail in stock.py
 * Endpoint: GET /api/stocks/{symbol}
 */
export interface StockDetail {
  symbol: string;                      // Stock symbol
  company_name: string;                // Company name
  sector: string | null;               // Business sector
  price_history: PriceDataPoint[];     // Historical price data
  sentiment_history: SentimentDataPoint[]; // Historical sentiment data
  metrics: StockMetrics;               // Statistical metrics
  timeframe: string;                   // Data timeframe (1d, 7d, 14d)
  last_updated: string;                // Last data update (ISO string)
  generated_at: string;                // Response generation timestamp (ISO string)
}

/**
 * Stock list item for /api/stocks endpoint
 * Backend: StockListItem in stock.py
 */
export interface StockListItem {
  symbol: string;                      // Stock symbol
  company_name: string;                // Company name
  sector: string | null;               // Business sector
  is_active: boolean;                  // Whether stock is actively tracked
  latest_sentiment: number | null;     // Latest sentiment score
  latest_price: number | null;         // Latest stock price
  last_updated: string | null;         // Last update timestamp (ISO string)
}

/**
 * List of all tracked stocks - Implements U-FR3
 * Backend: StockList in stock.py
 * Endpoint: GET /api/stocks/
 */
export interface StockList {
  stocks: StockListItem[];
  total_count: number;                 // Total number of stocks
  active_count: number;                // Number of actively tracked stocks
  generated_at: string;                // Response generation timestamp (ISO string)
}

// ============================================================================
// ANALYSIS SCHEMAS (analysis.py)
// ============================================================================

/**
 * Sentiment trend data point for time series analysis
 * Backend: SentimentTrendPoint in analysis.py
 */
export interface SentimentTrendPoint {
  timestamp: string;                   // Data timestamp (ISO string)
  sentiment_score: number;             // Sentiment score (-1.0 to 1.0)
  price: number | null;                // Stock price at timestamp
  volume: number | null;               // Trading volume
  source_count: number;                // Number of sentiment sources
}

/**
 * Historical sentiment data with price correlation - Implements U-FR4
 * Backend: SentimentHistory in analysis.py
 * Endpoint: GET /api/analysis/sentiment-history
 */
export interface SentimentHistory {
  symbol: string;                      // Stock symbol
  timeframe: string;                   // Data timeframe
  data_points: SentimentTrendPoint[];  // Time series data points
  avg_sentiment: number;               // Average sentiment score
  sentiment_volatility: number;        // Sentiment standard deviation
  price_correlation: number | null;    // Sentiment-price correlation
  total_records: number;               // Total number of data points
  data_coverage: number;               // Data coverage percentage
  generated_at: string;                // Response generation timestamp (ISO string)
}

/**
 * Statistical correlation metrics
 * Backend: CorrelationMetrics in analysis.py
 */
export interface CorrelationMetrics {
  pearson_correlation: number;         // Pearson correlation coefficient (-1.0 to 1.0)
  p_value: number;                     // Statistical significance p-value
  confidence_interval: [number, number]; // 95% confidence interval [lower, upper]
  sample_size: number;                 // Number of data points used
  r_squared: number;                   // Coefficient of determination
}

/**
 * Real-time correlation analysis - Implements U-FR5
 * Backend: CorrelationAnalysis in analysis.py
 * Endpoint: GET /api/analysis/correlation
 */
export interface CorrelationAnalysis {
  symbol: string;                      // Stock symbol
  timeframe: string;                   // Analysis timeframe
  correlation_metrics: CorrelationMetrics; // Statistical correlation metrics
  sentiment_trend: string;             // Sentiment trend (increasing/decreasing/stable)
  price_trend: string;                 // Price trend (increasing/decreasing/stable)
  scatter_data: Array<{ [key: string]: number }>; // Scatter plot data points
  trend_line: { [key: string]: any };  // Regression trend line parameters
  analysis_period: {                   // Analysis start and end dates
    start: string;
    end: string;
  };
  data_quality: number;                // Data quality score (0.0 to 1.0)
  last_updated: string;                // Last data update (ISO string)
  generated_at: string;                // Response generation timestamp (ISO string)
}

/**
 * Trend analysis for sentiment and price movements
 * Backend: TrendAnalysis in analysis.py
 */
export interface TrendAnalysis {
  direction: string;                   // Trend direction (up/down/stable)
  strength: number;                    // Trend strength (0.0 to 1.0)
  duration_days: number;               // Trend duration in days
  confidence: number;                  // Trend confidence score (0.0 to 1.0)
}

/**
 * Multi-stock comparison analysis
 * Backend: ComparisonAnalysis in analysis.py
 * Endpoint: GET /api/analysis/comparison
 */
export interface ComparisonAnalysis {
  stocks: string[];                    // Stock symbols being compared
  timeframe: string;                   // Comparison timeframe
  sentiment_rankings: Array<{ [key: string]: any }>; // Stocks ranked by sentiment
  correlation_matrix: { [symbol: string]: { [symbol: string]: number } }; // Correlation matrix
  performance_metrics: { [symbol: string]: { [metric: string]: number } }; // Performance metrics
  generated_at: string;                // Response generation timestamp (ISO string)
}

// ============================================================================
// VALIDATION HELPERS
// ============================================================================

/**
 * Type guard to check if dashboard summary has data
 */
export function hasDashboardData(data: DashboardSummary | null | undefined): data is DashboardSummary {
  return !!data && data.top_stocks.length > 0;
}

/**
 * Type guard to check if stock list has data
 */
export function hasStockListData(data: StockList | null | undefined): data is StockList {
  return !!data && data.stocks.length > 0;
}

/**
 * Type guard to check if sentiment history has sufficient data
 */
export function hasSufficientSentimentData(
  data: SentimentHistory | null | undefined,
  minPoints: number = 5
): data is SentimentHistory {
  return !!data && data.data_points.length >= minPoints;
}

/**
 * Type guard to check if correlation analysis has sufficient data
 */
export function hasSufficientCorrelationData(
  data: CorrelationAnalysis | null | undefined,
  minPoints: number = 10
): data is CorrelationAnalysis {
  return !!data && data.scatter_data.length >= minPoints;
}

// ============================================================================
// NOTES FOR DEVELOPERS
// ============================================================================

/**
 * CRITICAL IMPLEMENTATION NOTES:
 * 
 * 1. BACKEND IS SOURCE OF TRUTH
 *    - These interfaces match backend/app/presentation/schemas/ EXACTLY
 *    - Backend uses 'company_name' (not 'name' in frontend)
 *    - Backend uses snake_case for all field names
 * 
 * 2. DATABASE MODEL vs API SCHEMA
 *    - Database model (StocksWatchlist) has 'name' field
 *    - API schemas expose it as 'company_name'
 *    - Backend routes map: stock.name → StockSummary.company_name
 * 
 * 3. TIMESTAMP HANDLING
 *    - All datetime fields from backend are ISO 8601 strings
 *    - Convert to Date objects in components: new Date(timestamp)
 *    - Use date-fns or similar for formatting
 * 
 * 4. NULL vs UNDEFINED
 *    - Backend Pydantic Optional[T] → TypeScript T | null
 *    - Use null checks: if (data.field !== null) { ... }
 *    - React Query returns undefined for missing data
 * 
 * 5. SENTIMENT LABELS
 *    - Backend returns lowercase: "positive", "neutral", "negative"
 *    - Frontend should handle case-insensitively
 * 
 * 6. EMPTY STATES
 *    - Empty arrays are valid responses (pipeline not run)
 *    - Always validate data before rendering charts
 *    - Use validation utilities from dataValidation.ts
 * 
 * 7. ENDPOINT PATHS
 *    - Dashboard: GET /api/dashboard/summary
 *    - Stock List: GET /api/stocks/ (root with trailing slash)
 *    - Stock Detail: GET /api/stocks/{symbol}
 *    - Sentiment History: GET /api/analysis/sentiment-history?symbol=X&timeframe=7d
 *    - Correlation: GET /api/analysis/correlation?symbol=X&timeframe=7d
 * 
 * 8. UPDATING THIS FILE
 *    - When backend schemas change, update this file FIRST
 *    - Run backend tests to verify schema compatibility
 *    - Update validation utilities if data structure changes
 *    - Notify team of breaking changes
 */
