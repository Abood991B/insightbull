// Analysis API types matching backend schemas

export interface SentimentTrendPoint {
  timestamp: string;
  sentiment_score: number;
  price: number | null;
  volume: number | null;
  source_count: number;
}

export interface SentimentHistory {
  symbol: string;
  timeframe: string;
  data_points: SentimentTrendPoint[];
  avg_sentiment: number;
  sentiment_volatility: number;
  price_correlation: number | null;
  total_records: number;
  data_coverage: number;
}

export interface CorrelationMetrics {
  pearson_correlation: number;
  p_value: number;
  confidence_interval: [number, number];
  sample_size: number;
  r_squared: number;
}

export interface CorrelationAnalysis {
  symbol: string;
  timeframe: string;
  correlation_metrics: CorrelationMetrics;
  sentiment_trend: string;
  price_trend: string;
  scatter_data: Array<{ sentiment: number; price: number }>;
  trend_line: {
    slope: number;
    intercept: number;
    r_squared: number;
  };
  analysis_period: {
    start: string;
    end: string;
  };
  data_quality: number;
  last_updated: string;
}
