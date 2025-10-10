// Analysis service for API calls
import { BaseService } from './base.service';
import type { SentimentHistory, CorrelationAnalysis } from '../types/analysis.types';

class AnalysisService extends BaseService {
  async getSentimentHistory(
    symbol: string,
    timeframe: '1d' | '7d' | '14d' = '7d',
    limit: number = 100
  ): Promise<SentimentHistory> {
    const response = await this.get<SentimentHistory>(
      `/analysis/stocks/${symbol}/sentiment?timeframe=${timeframe}&limit=${limit}`
    );
    
    if (response.error || !response.data) {
      throw new Error(response.error || `Failed to fetch sentiment history for ${symbol}`);
    }
    
    return response.data;
  }

  async getCorrelationAnalysis(
    symbol: string,
    timeframe: '1d' | '7d' | '14d' = '7d'
  ): Promise<CorrelationAnalysis> {
    const response = await this.get<CorrelationAnalysis>(
      `/analysis/stocks/${symbol}/correlation?timeframe=${timeframe}`
    );
    
    if (response.error || !response.data) {
      throw new Error(response.error || `Failed to fetch correlation analysis for ${symbol}`);
    }
    
    return response.data;
  }
}

export const analysisService = new AnalysisService();
