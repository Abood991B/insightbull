// API type definitions
export interface Stock {
  symbol: string;
  name: string;
  price: number;
  change: number;
  changePercent: number;
  volume: number;
  marketCap: number;
  lastUpdated: Date;
}

export interface SentimentData {
  id: string;
  stockSymbol: string;
  sentiment: 'positive' | 'negative' | 'neutral';
  score: number;
  source: string;
  timestamp: Date;
  content?: string;
}

export interface PriceData {
  symbol: string;
  date: Date;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CorrelationData {
  symbol1: string;
  symbol2: string;
  correlation: number;
  period: string;
  lastCalculated: Date;
}

export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user';
  createdAt: Date;
}

export interface ApiConfig {
  id: string;
  name: string;
  endpoint: string;
  apiKey?: string;
  enabled: boolean;
  rateLimit: number;
  lastChecked: Date;
}
