// Dashboard service for API calls
import { BaseService } from './base.service';
import type { DashboardSummary } from '../types/dashboard.types';

class DashboardService extends BaseService {
  async getDashboardSummary(): Promise<DashboardSummary> {
    const response = await this.get<DashboardSummary>('/dashboard/summary');
    
    if (response.error || !response.data) {
      throw new Error(response.error || 'Failed to fetch dashboard summary');
    }
    
    return response.data;
  }
}

export const dashboardService = new DashboardService();
