// Stock service for API calls
import { BaseService } from './base.service';
import type { StockList, StockDetail } from '../types/stock.types';

class StockService extends BaseService {
  async getAllStocks(params?: {
    limit?: number;
    active_only?: boolean;
  }): Promise<StockList> {
    const queryParams = new URLSearchParams();
    if (params?.limit) queryParams.append('limit', params.limit.toString());
    if (params?.active_only !== undefined) {
      queryParams.append('active_only', params.active_only.toString());
    }
    
    const endpoint = `/stocks${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    const response = await this.get<StockList>(endpoint);
    
    if (response.error || !response.data) {
      throw new Error(response.error || 'Failed to fetch stocks');
    }
    
    return response.data;
  }

  async getStockDetail(symbol: string, timeframe: '1d' | '7d' | '14d' = '7d'): Promise<StockDetail> {
    const response = await this.get<StockDetail>(`/stocks/${symbol}?timeframe=${timeframe}`);
    
    if (response.error || !response.data) {
      throw new Error(response.error || `Failed to fetch stock details for ${symbol}`);
    }
    
    return response.data;
  }
}

export const stockService = new StockService();
