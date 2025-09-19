/**
 * Admin API Service
 * =================
 * 
 * Centralized API service for all admin dashboard operations.
 * Handles authentication, system monitoring, configuration, and management.
 */

// Base Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Import auth service for token management
import { authService } from '@/features/admin/services/auth.service';

// Types and Interfaces
export interface SystemStatus {
  status: 'online' | 'offline' | 'maintenance';
  services: {
    database: 'healthy' | 'warning' | 'error';
    api: 'healthy' | 'warning' | 'error';
    pipeline: 'running' | 'stopped' | 'error';
    storage: 'healthy' | 'warning' | 'error';
  };
  metrics: {
    uptime: string;
    last_collection: string;
    active_stocks: number;
    total_records: number;
  };
}

export interface ModelAccuracy {
  overall_accuracy: number;
  model_metrics: {
    vader_sentiment: {
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
    };
    finbert_sentiment: {
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
    };
  };
  last_evaluation: string;
  evaluation_samples: number;
}

export interface APIConfiguration {
  apis: {
    reddit: {
      status: 'active' | 'inactive' | 'error';
      configured: boolean;
      last_test: string;
    };
    finnhub: {
      status: 'active' | 'inactive' | 'error';
      configured: boolean;
      last_test: string;
    };
    newsapi: {
      status: 'active' | 'inactive' | 'error';
      configured: boolean;
      last_test: string;
    };
    marketaux: {
      status: 'active' | 'inactive' | 'error';
      configured: boolean;
      last_test: string;
    };
  };
  last_updated: string;
}

export interface APIKeyUpdate {
  service: 'reddit' | 'finnhub' | 'newsapi' | 'marketaux';
  keys: Record<string, string>;
}

export interface StorageSettings {
  current_usage: {
    total_size_gb: number;
    available_space_gb: number;
    usage_percentage: number;
  };
  retention_policy: {
    sentiment_data_days: number;
    stock_price_days: number;
    log_files_days: number;
    backup_retention_days: number;
  };
  auto_cleanup: boolean;
  compression_enabled: boolean;
}

export interface SystemLog {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  component: string;
  message: string;
  details?: Record<string, any>;
}

export interface SystemLogsResponse {
  logs: SystemLog[];
  total_count: number;
  filters_applied: {
    level?: string;
    component?: string;
    limit: number;
    offset: number;
  };
}

export interface StockInfo {
  symbol: string;
  company_name: string;
  sector: string;
  is_active: boolean;
  added_date: string;
}

export interface WatchlistResponse {
  stocks: StockInfo[];
  total_stocks: number;
  active_stocks: number;
  last_updated: string;
}

export interface ManualCollectionRequest {
  stock_symbols?: string[];
  data_sources?: string[];
  priority?: 'low' | 'normal' | 'high';
}

export interface ManualCollectionResponse {
  job_id: string;
  status: 'initiated' | 'running' | 'completed' | 'failed';
  estimated_completion: string;
  symbols_targeted: string[];
  message: string;
}

// Utility Functions
const getAuthHeaders = () => {
  // Get token from admin auth service session
  const session = authService.getSession();
  const token = session?.accessToken || localStorage.getItem('admin_token');
  
  return {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json',
  };
};

const handleApiResponse = async (response: Response) => {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
  }
  return response.json();
};

/**
 * Admin API Service Class
 */
class AdminAPIService {
  
  // ============================================================================
  // AUTHENTICATION & SESSION MANAGEMENT
  // ============================================================================
  
  async validateToken(): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/admin/auth/validate`, {
        method: 'POST',
        headers: getAuthHeaders(),
      });
      return response.ok;
    } catch (error) {
      console.error('Token validation failed:', error);
      return false;
    }
  }

  async verifySession(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/auth/verify`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async refreshToken(refreshToken: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // SYSTEM MONITORING & STATUS
  // ============================================================================
  
  async getSystemStatus(): Promise<SystemStatus> {
    const response = await fetch(`${API_BASE_URL}/api/admin/system/status`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async getSystemLogs(
    level?: string,
    component?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<SystemLogsResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (level) params.append('level', level);
    if (component) params.append('component', component);

    const response = await fetch(`${API_BASE_URL}/api/admin/logs?${params}`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // MODEL ACCURACY & PERFORMANCE
  // ============================================================================
  
  async getModelAccuracy(): Promise<ModelAccuracy> {
    const response = await fetch(`${API_BASE_URL}/api/admin/models/accuracy`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async triggerModelRetraining(): Promise<any> {
    // TODO: Implement model retraining endpoint in backend
    return Promise.resolve({
      success: true,
      message: 'Model retraining functionality not yet implemented',
      timestamp: new Date().toISOString()
    });
  }

  // ============================================================================
  // API CONFIGURATION MANAGEMENT
  // ============================================================================
  
  async getAPIConfiguration(): Promise<APIConfiguration> {
    const response = await fetch(`${API_BASE_URL}/api/admin/config/apis`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async updateAPIConfiguration(apiKeyUpdate: APIKeyUpdate): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/config/apis`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(apiKeyUpdate),
    });
    return handleApiResponse(response);
  }

  async testAPIConnection(service: string): Promise<any> {
    // TODO: Implement API connection test endpoint in backend
    return Promise.resolve({
      success: true,
      service: service,
      status: 'connected',
      message: `API connection test for ${service} not yet implemented`,
      timestamp: new Date().toISOString()
    });
  }

  // ============================================================================
  // WATCHLIST MANAGEMENT
  // ============================================================================
  
  async getWatchlist(): Promise<WatchlistResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/watchlist`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async addToWatchlist(symbol: string, companyName?: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/watchlist`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        action: 'add',
        symbol: symbol.toUpperCase(),
        company_name: companyName,
      }),
    });
    return handleApiResponse(response);
  }

  async removeFromWatchlist(symbol: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/watchlist`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        action: 'remove',
        symbol: symbol.toUpperCase(),
      }),
    });
    return handleApiResponse(response);
  }

  async activateStock(symbol: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/watchlist`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        action: 'activate',
        symbol: symbol.toUpperCase(),
      }),
    });
    return handleApiResponse(response);
  }

  async deactivateStock(symbol: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/watchlist`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        action: 'deactivate',
        symbol: symbol.toUpperCase(),
      }),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // STORAGE MANAGEMENT
  // ============================================================================
  
  async getStorageSettings(): Promise<StorageSettings> {
    const response = await fetch(`${API_BASE_URL}/api/admin/storage`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async updateStorageSettings(settings: Partial<StorageSettings>): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/storage`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(settings),
    });
    return handleApiResponse(response);
  }

  async triggerCleanup(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/storage/optimize`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async createBackup(): Promise<any> {
    // TODO: Implement backup endpoint in backend
    return Promise.resolve({
      success: true,
      message: 'Backup functionality not yet implemented',
      timestamp: new Date().toISOString()
    });
  }

  // ============================================================================
  // DATA COLLECTION MANAGEMENT
  // ============================================================================
  
  async triggerManualCollection(request?: ManualCollectionRequest): Promise<ManualCollectionResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/data-collection/manual`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(request || {}),
    });
    return handleApiResponse(response);
  }

  async getCollectionStatus(jobId?: string): Promise<any> {
    const url = jobId 
      ? `${API_BASE_URL}/api/admin/data-collection/status/${jobId}`
      : `${API_BASE_URL}/api/admin/data-collection/status`;
    
    const response = await fetch(url, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async stopCollection(jobId: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/data-collection/stop/${jobId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // PIPELINE MANAGEMENT
  // ============================================================================
  
  async getPipelineStatus(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/pipeline/status`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async startPipeline(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/pipeline/start`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async stopPipeline(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/pipeline/stop`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async restartPipeline(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/pipeline/restart`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }
}

// Export singleton instance
export const adminAPI = new AdminAPIService();
export default adminAPI;