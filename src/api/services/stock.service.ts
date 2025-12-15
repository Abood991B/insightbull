/**
 * Stock Service
 * 
 * Handles all stock-related API calls for stock list and details.
 * Implements U-FR3: Filter by Stock
 * 
 * Backend Endpoints:
 * - GET /api/stocks/ - List all stocks
 * - GET /api/stocks/{symbol} - Get stock detail
 * 
 * Backend Schema: backend/app/presentation/schemas/stock.py
 */

import { BaseService, ApiResponse } from './base.service';
import { StockList, StockDetail } from '@/api/types/backend-schemas';

/**
 * Service for stock data operations
 */
class StockService extends BaseService {
  /**
   * Get all tracked stocks in the watchlist
   * 
   * @param limit - Maximum number of stocks to return (default: 20, max: 100)
   * @param activeOnly - Only return actively tracked stocks (default: true)
   * @returns Promise<ApiResponse<StockList>> List of stocks with latest data
   * 
   * Response includes:
   * - stocks: Array of stock items with symbol, name, sector, sentiment, price
   * - total_count: Total number of stocks in watchlist
   * - active_count: Number of actively tracked stocks
   * 
   * @example
   * ```typescript
   * const response = await stockService.getAllStocks();
   * if (response.data) {
   *   console.log(`Found ${response.data.stocks.length} stocks`);
   *   const activeStocks = response.data.stocks.filter(s => s.is_active);
   * }
   * ```
   */
  async getAllStocks(limit: number = 20, activeOnly: boolean = true): Promise<ApiResponse<StockList>> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      active_only: activeOnly.toString(),
    });
    return this.get<StockList>(`/api/stocks/?${params.toString()}`);
  }

  /**
   * Get detailed information for a specific stock
   * 
   * @param symbol - Stock symbol (e.g., "AAPL", "MSFT")
   * @param timeframe - Data timeframe: "1d", "7d", or "14d" (default: "7d")
   * @returns Promise<ApiResponse<StockDetail>> Detailed stock data
   * 
   * Response includes:
   * - price_history: Historical price data points
   * - sentiment_history: Historical sentiment data points
   * - metrics: Statistical metrics (avg sentiment, volatility, price change)
   * 
   * @example
   * ```typescript
   * const response = await stockService.getStockDetail('AAPL', '7d');
   * if (response.data) {
   *   console.log(`AAPL avg sentiment: ${response.data.metrics.avg_sentiment}`);
   *   console.log(`Data points: ${response.data.sentiment_history.length}`);
   * }
   * ```
   */
  async getStockDetail(symbol: string, timeframe: '1d' | '7d' | '14d' | '30d' = '7d'): Promise<ApiResponse<StockDetail>> {
    return this.get<StockDetail>(`/api/stocks/${symbol}?timeframe=${timeframe}`);
  }

  /**
   * Get comprehensive stock analysis dashboard data
   * 
   * @param symbol - Stock symbol (e.g., "AAPL", "MSFT")
   * @param timeframe - Analysis timeframe: "1d", "7d", "14d", or "30d" (default: "7d")
   * @returns Promise<ApiResponse<any>> Complete analysis dashboard data
   * 
   * Response includes:
   * - stock_overview: Current price, sentiment score, 24h change, market status
   * - sentiment_distribution: Pie chart data (positive/negative/neutral counts)
   * - top_performers: Bar chart data (top 5 stocks by sentiment)
   * - watchlist_overview: Table data (all stocks with prices, changes, sentiment)
   * 
   * @example
   * ```typescript
   * const response = await stockService.getStockAnalysis('AAPL', '7d');
   * if (response.data) {
   *   console.log(`Current price: $${response.data.stock_overview.current_price}`);
   *   console.log(`Sentiment distribution:`, response.data.sentiment_distribution);
   *   console.log(`Top performers:`, response.data.top_performers);
   * }
   * ```
   */
  async getStockAnalysis(symbol: string, timeframe: '1d' | '7d' | '14d' | '30d' = '7d'): Promise<ApiResponse<any>> {
    return this.get<any>(`/api/stocks/${symbol}/analysis?timeframe=${timeframe}`);
  }

  /**
   * Get list of stock symbols only (lightweight)
   * Useful for dropdowns/selectors
   * 
   * @param activeOnly - Only return active stocks (default: true)
   * @returns Promise<string[]> Array of stock symbols
   * 
   * @example
   * ```typescript
   * const symbols = await stockService.getStockSymbols();
   * // Returns: ['AAPL', 'MSFT', 'NVDA', ...]
   * ```
   */
  async getStockSymbols(activeOnly: boolean = true): Promise<string[]> {
    const response = await this.getAllStocks(100, activeOnly);
    if (response.data) {
      return response.data.stocks.map(stock => stock.symbol);
    }
    return [];
  }

  /**
   * Get stock options for Select components
   * Returns formatted options with label and value
   * 
   * @param activeOnly - Only return active stocks (default: true)
   * @returns Promise<Array<{value: string, label: string}>>
   * 
   * @example
   * ```typescript
   * const options = await stockService.getStockOptions();
   * // Returns: [{ value: 'AAPL', label: 'AAPL - Apple Inc.' }, ...]
   * ```
   */
  async getStockOptions(activeOnly: boolean = true): Promise<Array<{ value: string; label: string }>> {
    const response = await this.getAllStocks(100, activeOnly);
    if (response.data) {
      return response.data.stocks.map(stock => ({
        value: stock.symbol,
        label: `${stock.symbol} - ${stock.company_name}`,
      }));
    }
    return [];
  }
}

// Export singleton instance
export const stockService = new StockService();
