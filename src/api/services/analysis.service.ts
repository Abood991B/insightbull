import { BaseService, type ApiResponse } from './base.service';
import type { 
  CorrelationAnalysis,
  SentimentHistory
} from '@/api/types/backend-schemas';

/**
 * Analysis Service
 * 
 * Handles API calls for sentiment analysis, correlation analysis,
 * and sentiment vs price data.
 * 
 * Backend endpoints:
 * - GET /api/analysis/stocks/{symbol}/correlation?timeframe={timeframe}
 * - GET /api/analysis/stocks/{symbol}/sentiment?timeframe={timeframe}
 */
class AnalysisService extends BaseService {
  private readonly ENDPOINTS = {
    CORRELATION: '/api/analysis/stocks',
    SENTIMENT_HISTORY: '/api/analysis/stocks',
  };

  /**
   * Get correlation analysis for a specific stock
   * 
   * @param symbol - Stock symbol (e.g., 'AAPL')
   * @param timeframe - Time period ('1d', '7d', '14d', '30d')
   * @returns Correlation analysis data including sentiment/price history and correlation coefficient
   * 
   * @example
   * const result = await analysisService.getCorrelationAnalysis('AAPL', '7d');
   * if (result.success && result.data) {
   *   console.log('Correlation:', result.data.correlation_coefficient);
   *   console.log('Data points:', result.data.data_points.length);
   * }
   */
  async getCorrelationAnalysis(
    symbol: string,
    timeframe: '1d' | '7d' | '14d' | '30d' = '7d'
  ): Promise<ApiResponse<CorrelationAnalysis>> {
    return this.get<CorrelationAnalysis>(
      `${this.ENDPOINTS.CORRELATION}/${symbol}/correlation?timeframe=${timeframe}`
    );
  }

  /**
   * Get sentiment history for a specific stock
   * 
   * @param symbol - Stock symbol (e.g., 'AAPL')
   * @param timeframe - Time period ('1d', '7d', '14d', '30d')
   * @returns Sentiment history data with time series points
   * 
   * @example
   * const result = await analysisService.getSentimentHistory('AAPL', '7d');
   * if (result.success && result.data) {
   *   console.log('Avg sentiment:', result.data.avg_sentiment);
   *   console.log('Data points:', result.data.data_points.length);
   * }
   */
  async getSentimentHistory(
    symbol: string,
    timeframe: '1d' | '7d' | '14d' | '30d' = '7d'
  ): Promise<ApiResponse<SentimentHistory>> {
    return this.get<SentimentHistory>(
      `${this.ENDPOINTS.SENTIMENT_HISTORY}/${symbol}/sentiment?timeframe=${timeframe}`
    );
  }
}

// Export singleton instance
export const analysisService = new AnalysisService();
