// Dashboard API types matching backend schemas

export interface StockSummary {
  symbol: string;
  company_name: string;
  current_price: number | null;
  price_change_24h: number | null;
  sentiment_score: number | null;
  sentiment_label: string | null;
  last_updated: string | null;
}

export interface MarketSentimentOverview {
  average_sentiment: number;
  positive_stocks: number;
  neutral_stocks: number;
  negative_stocks: number;
  total_stocks: number;
  last_updated: string;
}

export interface SystemStatus {
  pipeline_status: string;
  last_collection: string | null;
  active_data_sources: string[];
  total_sentiment_records: number;
}

export interface DashboardSummary {
  market_overview: MarketSentimentOverview;
  top_stocks: StockSummary[];
  recent_movers: StockSummary[];
  system_status: SystemStatus;
  generated_at: string;
}
