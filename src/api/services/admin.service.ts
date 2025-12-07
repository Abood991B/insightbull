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
  status: 'online' | 'offline' | 'maintenance' | 'operational' | 'degraded';
  services: {
    database: 'healthy' | 'unhealthy' | 'error';
    sentiment_engine: 'healthy' | 'unhealthy' | 'error';
    data_collection: 'healthy' | 'unhealthy' | 'error';
    real_time_prices?: 'healthy' | 'unhealthy' | 'error';
    scheduler?: 'healthy' | 'unhealthy' | 'error';
  };
  metrics: {
    uptime: string;
    last_collection?: string;
    active_stocks: number;
    total_records: number;
    price_updates?: number;
    sentiment_breakdown?: {
      positive: number;
      neutral: number;
      negative: number;
    };
    news_articles?: number;
    hackernews_posts?: number;
    price_records?: number;
    last_price_update?: string;
  };
  timestamp: string;
}

// Per-source sentiment metrics - REAL data only (no fake estimates)
export interface SourceMetrics {
  sample_count: number;
  avg_confidence: number;
  avg_sentiment_score: number;
  // Sentiment distribution - actual counts from data
  sentiment_distribution: {
    positive: number;
    negative: number;
    neutral: number;
  };
  positive_rate: number;
  negative_rate: number;
  neutral_rate: number;
  // Legacy fields (optional for backwards compatibility)
  accuracy?: number;
  precision?: number;
  recall?: number;
  f1_score?: number;
}

export interface ModelAccuracy {
  overall_accuracy: number;
  model_metrics: {
    finbert_sentiment: { // ProsusAI/finbert (88.3% benchmark accuracy) with optional Gemini AI verification
      accuracy: number;
      precision: number;
      recall: number;
      f1_score: number;
    };
  };
  source_metrics?: Record<string, SourceMetrics>; // Per-source breakdown
  last_evaluation: string;
  evaluation_samples: number;
  evaluation_period: string;
  data_source: string;
  ai_verification?: { // Gemini AI verification info
    enabled: boolean;
    provider: string;
    mode: string;
    estimated_accuracy_with_ai: number;
  };
}

export interface APIConfiguration {
  apis: {
    hackernews: {
      status: 'active' | 'inactive' | 'error' | 'unknown';
      last_test: string | null;
      requires_api_key: boolean;
      error?: string | null;
      enabled?: boolean;
    };
    gdelt: {
      status: 'active' | 'inactive' | 'error' | 'unknown';
      last_test: string | null;
      requires_api_key: boolean;
      error?: string | null;
      enabled?: boolean;
    };
    finnhub: {
      status: 'active' | 'inactive' | 'error' | 'unknown';
      last_test: string | null;
      api_key: string;
      error?: string | null;
      enabled?: boolean;
    };
    newsapi: {
      status: 'active' | 'inactive' | 'error' | 'unknown';
      last_test: string | null;
      api_key: string;
      error?: string | null;
      enabled?: boolean;
    };
    marketaux: {
      status: 'active' | 'inactive' | 'error' | 'unknown';
      last_test: string | null;
      api_key: string;
      error?: string | null;
      enabled?: boolean;
    };
  };
  ai_services?: {
    gemini: {
      status: 'active' | 'inactive' | 'error' | 'unknown';
      last_test: string | null;
      api_key: string;
      api_key_required: boolean;
      error?: string | null;
      enabled?: boolean;
      description?: string;
      verification_mode?: string;
      confidence_threshold?: number;
      ai_verification_stats?: {
        configured: boolean;
        mode: string;
        confidence_threshold: number;
        total_analyzed?: number;
        ai_verified_count?: number;
        ai_verification_rate?: number;
        ai_errors?: number;
        avg_ml_confidence?: number;
        ai_enabled?: boolean;
        gemini_configured?: boolean;
      };
    };
  };
  summary: {
    total_collectors: number;
    total_ai_services: number;
    configured: number;
    active: number;
    enabled?: number;
    disabled?: number;
    ai_configured?: number;
    ai_enabled?: number;
  };
  collector_config?: {
    last_updated: string | null;
    updated_by: string | null;
  };
}

export interface CollectorToggleResponse {
  collector: string;
  enabled: boolean;
  message: string;
  updated_at: string;
  updated_by: string | null;
}

export interface APIKeyUpdate {
  service: 'hackernews' | 'finnhub' | 'newsapi' | 'marketaux' | 'gemini';
  keys: Record<string, string>;
}

// Benchmark interfaces
export interface BenchmarkClassMetrics {
  precision: number;
  recall: number;
  f1_score: number;
  support: number;
}

export interface BenchmarkResult {
  dataset_name: string;
  dataset_size: number;
  evaluated_at: string;
  model_name: string;
  model_version: string;
  accuracy: number;
  macro_precision: number;
  macro_recall: number;
  macro_f1: number;
  weighted_f1: number;
  class_metrics: {
    positive: BenchmarkClassMetrics;
    negative: BenchmarkClassMetrics;
    neutral: BenchmarkClassMetrics;
  };
  confusion_matrix: {
    positive: { positive: number; negative: number; neutral: number };
    negative: { positive: number; negative: number; neutral: number };
    neutral: { positive: number; negative: number; neutral: number };
  };
  processing_time_seconds: number;
  avg_confidence: number;
  comparison_with_previous?: {
    previous_model: string;
    previous_accuracy: number;
    accuracy_improvement: number;
    improvement_percentage: number;
  };
  ai_verification?: {
    enabled: boolean;
    provider: string;
    mode: string;
    confidence_threshold: number;
    estimated_accuracy_with_ai: number;
    note: string;
  };
}

export interface BenchmarkDatasetInfo {
  available: boolean;
  path: string;
  total_samples?: number;
  distribution?: Record<string, number>;
  message?: string;
  error?: string;
}

export interface BenchmarkResponse {
  has_benchmark: boolean;
  benchmark?: BenchmarkResult;
  dataset_info: BenchmarkDatasetInfo;
  message?: string;
}

export interface BenchmarkRunResponse {
  success: boolean;
  message: string;
  results: BenchmarkResult;
}

export interface StorageSettings {
  current_usage: {
    total_size_gb: number;
    total_size_mb: number;
    available_space_gb: number;
    usage_percentage: number;
  };
  total_records: number;
  sentiment_records: number;
  stock_price_records: number;
  oldest_record: string | null;
  newest_record: string | null;
  storage_health: 'healthy' | 'warning' | 'critical';
}

export interface SystemLog {
  timestamp: string;
  level: 'DEBUG' | 'INFO' | 'WARNING' | 'ERROR' | 'CRITICAL';
  component: string;
  message: string;
  function?: string;
  line_number?: number;
  logger?: string;
  module?: string;
  extra_data?: Record<string, any>;
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
  status: 'success' | 'partial' | 'failed';
  message: string;
  pipeline_id: string;
  execution_summary?: {
    symbols_processed: number;
    data_collection: {
      total_items_collected: number;
      collectors_used: number;
      successful_collectors: number;
    };
    text_processing: {
      items_processed: number;
      processing_success_rate: string;
    };
    sentiment_analysis: {
      items_analyzed: number;
      analysis_success_rate: string;
    };
    data_storage: {
      items_stored: number;
      storage_success_rate: string;
    };
  };
  execution_time_seconds: number;
  timestamp: string;
  warning?: string;
  error_details?: string;
}

export interface ScheduledJob {
  job_id: string;
  name: string;
  job_type: string;
  trigger_config: Record<string, any>;
  parameters: Record<string, any>;
  status: string;
  created_at: string;
  last_run: string | null;
  next_run: string | null;
  run_count: number;
  error_count: number;
  last_error: string | null;
  enabled: boolean;
}

// Sentiment Engine Metrics
export interface SentimentEngineMetrics {
  engine_status: {
    initialized: boolean;
    available_models: string[];
    total_models: number;
    engine_health: 'healthy' | 'degraded' | 'critical';
  };
  overall_performance: {
    total_texts_processed: number;
    successful_analyses: number;
    failed_analyses: number;
    success_rate_percent: number;
    avg_processing_time_ms: number;
    total_processing_time_sec: number;
  };
  model_configuration: {
    finbert_enabled: boolean;
    ensemble_finbert_enabled: boolean;
    finbert_calibration_enabled: boolean;
    finbert_type: string;
    default_batch_size: number;
  };
  model_usage: {
    finbert: {
      session_count: number;
      database_count: number;
      percentage_of_total: number;
      used_for: string[];
      model_type: string;
      features: string[];
    };
  };
  database_statistics: {
    total_sentiment_records: number;
    finbert_records: number;
  };
  timestamp: string;
}

export interface SchedulerResponse {
  jobs: ScheduledJob[];
  total_jobs: number;
  scheduler_running: boolean;
}

export interface JobConfig {
  job_type: 'data_collection' | 'sentiment_analysis' | 'full_pipeline';
  name: string;
  cron_expression: string;
  symbols: string[];
  lookback_days?: number;
}

export interface DatabaseSchema {
  database_name: string;
  total_tables: number;
  tables: {
    [tableName: string]: {
      model_name: string;
      record_count: number;
      columns: {
        name: string;
        type: string;
        nullable: boolean;
        primary_key: boolean;
        default?: string;
      }[];
      foreign_keys: {
        constrained_columns: string[];
        referred_table: string;
        referred_columns: string[];
      }[];
      indexes: {
        name: string;
        column_names: string[];
        unique: boolean;
      }[];
    };
  };
}

export interface TableData {
  table_name: string;
  total_records: number;
  returned_records: number;
  offset: number;
  limit: number;
  data: Record<string, any>[];
}

export interface DatabaseStats {
  total_records: number;
  table_counts: { [tableName: string]: number };
  file_size: {
    bytes: number;
    mb: number;
    gb: number;
  };
  recent_activity: {
    sentiment_records_24h: number;
    log_entries_24h: number;
  };
  database_file: string;
}

// Real-time Price Service Types
export interface RealTimePriceServiceStatus {
  success: boolean;
  service_status: {
    service_name: string;
    is_running: boolean;
    update_interval: number;
    market_hours_only: boolean;
    current_market_status: 'open' | 'closed';
    next_market_open?: string;
    active_stocks_count: number;
    rate_limiting: {
      requests_per_minute: number;
      requests_per_hour: number;
      current_hour_count: number;
    };
    last_request_time?: string;
  };
}

export interface ServiceOperationResponse {
  success: boolean;
  message: string;
}

export interface RealTimePriceServiceConfig {
  update_interval?: number;
}

export interface TestPriceFetchResponse {
  success: boolean;
  message: string;
  data?: {
    current_price: number;
    previous_close: number;
    open_price: number;
    high_price: number;
    low_price: number;
    volume: number;
  };
}

export interface CollectorHealthInfo {
  name: string;
  status: 'operational' | 'error' | 'warning' | 'not_configured';
  source: string;
  requires_api_key: boolean;
  configured: boolean;
  last_run: string | null;
  items_collected: number;
  error: string | null;
}

export interface CollectorHealthResponse {
  collectors: CollectorHealthInfo[];
  summary: {
    total_collectors: number;
    operational: number;
    not_configured: number;
    error: number;
    coverage_percentage: number;
    total_items_24h: number;
  };
}

export interface MarketStatus {
  is_open: boolean;
  current_period: 'pre-market' | 'market-hours' | 'after-hours' | 'overnight' | 'weekend';
  current_time_et: string;
  weekday: number;
  next_open: string | null;
  next_close: string | null;
  market_hours: {
    pre_market: string;
    market_hours: string;
    after_hours: string;
    overnight: string;
  };
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
    startDate?: string,
    endDate?: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<SystemLogsResponse> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    if (level) params.append('level', level);
    if (component) params.append('component', component);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await fetch(`${API_BASE_URL}/api/admin/logs?${params}`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async downloadSystemLogs(
    level?: string,
    component?: string,
    startDate?: string,
    endDate?: string
  ): Promise<Blob> {
    const params = new URLSearchParams();
    
    if (level) params.append('level', level);
    if (component) params.append('component', component);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    const response = await fetch(`${API_BASE_URL}/api/admin/logs/download?${params}`, {
      headers: getAuthHeaders(),
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    return response.blob();
  }

  async clearSystemLogs(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/logs/clear?confirm=true`, {
      method: 'DELETE',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // MODEL ACCURACY & PERFORMANCE
  // ============================================================================
  
  async getModelAccuracy(viewType: 'overall' | 'latest' = 'overall'): Promise<ModelAccuracy> {
    const response = await fetch(`${API_BASE_URL}/api/admin/models/accuracy?view_type=${viewType}`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch model accuracy');
    }

    return response.json();
  }

  async getBenchmarkResults(): Promise<BenchmarkResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/models/benchmark`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch benchmark results');
    }

    return response.json();
  }

  async runBenchmark(force: boolean = false): Promise<BenchmarkRunResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/models/benchmark/run?force=${force}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Failed to run benchmark');
    }

    return response.json();
  }

  async getSentimentEngineMetrics(): Promise<SentimentEngineMetrics> {
    const response = await fetch(`${API_BASE_URL}/api/admin/models/sentiment-engine-metrics`, {
      headers: getAuthHeaders(),
    });

    if (!response.ok) {
      throw new Error('Failed to fetch sentiment engine metrics');
    }

    return response.json();
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

  async toggleCollector(collectorName: string, enabled: boolean): Promise<CollectorToggleResponse> {
    const response = await fetch(
      `${API_BASE_URL}/api/admin/config/collectors/${collectorName}?enabled=${enabled}`,
      {
        method: 'PUT',
        headers: getAuthHeaders(),
      }
    );
    return handleApiResponse(response);
  }

  // ============================================================================
  // AI SERVICES MANAGEMENT
  // ============================================================================

  async toggleAIService(serviceName: string, enabled: boolean): Promise<any> {
    const response = await fetch(
      `${API_BASE_URL}/api/admin/config/ai-services/${serviceName}/toggle?enabled=${enabled}`,
      {
        method: 'PUT',
        headers: getAuthHeaders(),
      }
    );
    return handleApiResponse(response);
  }

  async updateAIServiceSettings(
    serviceName: string, 
    settings: { verification_mode?: string; confidence_threshold?: number }
  ): Promise<any> {
    const params = new URLSearchParams();
    if (settings.verification_mode) params.append('verification_mode', settings.verification_mode);
    if (settings.confidence_threshold !== undefined) params.append('confidence_threshold', settings.confidence_threshold.toString());
    
    const response = await fetch(
      `${API_BASE_URL}/api/admin/config/ai-services/${serviceName}/settings?${params.toString()}`,
      {
        method: 'PUT',
        headers: getAuthHeaders(),
      }
    );
    return handleApiResponse(response);
  }

  async getAIServicesConfig(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/config/ai-services`, {
      headers: getAuthHeaders(),
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

  async searchStockSymbols(query?: string): Promise<{ [symbol: string]: string }> {
    const url = query 
      ? `${API_BASE_URL}/api/admin/stocks/search?query=${encodeURIComponent(query)}`
      : `${API_BASE_URL}/api/admin/stocks/search`;
    
    const response = await fetch(url, {
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

  async toggleStock(symbol: string): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/watchlist`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({
        action: 'toggle',
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

  async createBackup(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/storage/backup`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
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

  // ============================================================================
  // SCHEDULER MANAGEMENT
  // ============================================================================
  
  async getScheduledJobs(): Promise<SchedulerResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/scheduler/jobs`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async createScheduledJob(jobConfig: JobConfig): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/scheduler/jobs`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(jobConfig),
    });
    return handleApiResponse(response);
  }

  async updateScheduledJob(jobId: string, action: 'enable' | 'disable' | 'cancel'): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/scheduler/jobs/${jobId}?action=${action}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async getJobStatus(jobId: string): Promise<ScheduledJob> {
    const response = await fetch(`${API_BASE_URL}/api/admin/scheduler/jobs/${jobId}`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async refreshScheduledJobs(): Promise<any> {
    const response = await fetch(`${API_BASE_URL}/api/admin/scheduler/refresh`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // REAL-TIME PRICE SERVICE MANAGEMENT
  // ============================================================================

  async getRealTimePriceServiceStatus(): Promise<RealTimePriceServiceStatus> {
    const response = await fetch(`${API_BASE_URL}/api/admin/realtime-price-service/status`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async startRealTimePriceService(): Promise<ServiceOperationResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/realtime-price-service/start`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async stopRealTimePriceService(): Promise<ServiceOperationResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/realtime-price-service/stop`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async updateRealTimePriceServiceConfig(config: RealTimePriceServiceConfig): Promise<ServiceOperationResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/realtime-price-service/config`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify(config),
    });
    return handleApiResponse(response);
  }

  async testPriceFetch(symbol?: string): Promise<TestPriceFetchResponse> {
    const params = symbol ? `?symbol=${symbol}` : '';
    const response = await fetch(`${API_BASE_URL}/api/admin/realtime-price-service/test-fetch${params}`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // DATA COLLECTOR HEALTH
  // ============================================================================
  
  async getCollectorHealth(): Promise<CollectorHealthResponse> {
    const response = await fetch(`${API_BASE_URL}/api/admin/collectors/health`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // MARKET STATUS
  // ============================================================================
  
  async getMarketStatus(): Promise<MarketStatus> {
    const response = await fetch(`${API_BASE_URL}/api/admin/market/status`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // ============================================================================
  // DATABASE INSPECTION
  // ============================================================================
  
  async getDatabaseSchema(): Promise<DatabaseSchema> {
    const response = await fetch(`${API_BASE_URL}/api/admin/database/schema`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async getTableData(
    tableName: string,
    limit: number = 100,
    offset: number = 0
  ): Promise<TableData> {
    const params = new URLSearchParams({
      limit: limit.toString(),
      offset: offset.toString(),
    });
    
    const response = await fetch(`${API_BASE_URL}/api/admin/database/tables/${tableName}/data?${params}`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  async getDatabaseStats(): Promise<DatabaseStats> {
    const response = await fetch(`${API_BASE_URL}/api/admin/database/stats`, {
      headers: getAuthHeaders(),
    });
    return handleApiResponse(response);
  }

  // Database cleanup utilities removed - using unified Stock table structure
}

// Export singleton instance
export const adminAPI = new AdminAPIService();
export default adminAPI;