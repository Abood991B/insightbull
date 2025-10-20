/**
 * Dashboard Service
 * 
 * Handles all dashboard-related API calls for the main dashboard view.
 * Implements U-FR1: View Sentiment Dashboard
 * 
 * Backend Endpoint: GET /api/dashboard/summary
 * Backend Schema: backend/app/presentation/schemas/dashboard.py
 */

import { BaseService, ApiResponse } from './base.service';
import { DashboardSummary } from '@/api/types/backend-schemas';

/**
 * Service for dashboard data operations
 */
class DashboardService extends BaseService {
  /**
   * Get complete dashboard summary with market overview, top stocks, and system status
   * 
   * @returns Promise<ApiResponse<DashboardSummary>> API response wrapper with dashboard data
   * @throws Error if API request fails
   * 
   * Response includes:
   * - market_overview: Market-wide sentiment metrics
   * - top_stocks: Top performing stocks by sentiment (sorted descending)
   * - recent_movers: Stocks with significant price changes (>2%)
   * - system_status: Pipeline status and data collection info
   * 
   * @example
   * ```typescript
   * const response = await dashboardService.getDashboardSummary();
   * if (response.data) {
   *   console.log(`Total stocks: ${response.data.market_overview.total_stocks}`);
   *   console.log(`Top performer: ${response.data.top_stocks[0]?.symbol}`);
   * }
   * ```
   */
  async getDashboardSummary(): Promise<ApiResponse<DashboardSummary>> {
    return this.get<DashboardSummary>('/api/dashboard/summary');
  }
}

// Export singleton instance
export const dashboardService = new DashboardService();
