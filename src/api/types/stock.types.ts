// Stock API types matching backend schemas

export interface PriceDataPoint {
  timestamp: string;
  open_price: number | null;
  close_price: number;
  high_price: number | null;
  low_price: number | null;
  volume: number | null;
}

export interface SentimentDataPoint {
  timestamp: string;
  score: number;
  label: string;
  confidence: number | null;
  source: string;
}

export interface StockMetrics {
  avg_sentiment: number;
  sentiment_volatility: number;
  price_change_percent: number | null;
  total_sentiment_records: number;
  data_quality_score: number;
}

export interface StockDetail {
  symbol: string;
  company_name: string;
  sector: string | null;
  price_history: PriceDataPoint[];
  sentiment_history: SentimentDataPoint[];
  metrics: StockMetrics;
  timeframe: string;
  last_updated: string;
  generated_at: string;
}

export interface StockListItem {
  symbol: string;
  company_name: string;
  sector: string | null;
  is_active: boolean;
  latest_sentiment: number | null;
  latest_price: number | null;
  last_updated: string | null;
}

export interface StockList {
  stocks: StockListItem[];
  total_count: number;
  active_count: number;
  generated_at: string;
}
