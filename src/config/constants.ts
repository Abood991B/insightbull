// Application constants
export const APP_NAME = 'Insight Stock Dashboard';
export const APP_VERSION = '1.0.0';

// API configuration
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
export const API_TIMEOUT = 30000; // 30 seconds

// Feature flags
export const FEATURES = {
  ENABLE_ADMIN: true,
  ENABLE_ANALYTICS: true,
  ENABLE_EXPORT: true,
};

// Chart configuration
export const CHART_COLORS = {
  primary: '#8884d8',
  secondary: '#82ca9d',
  tertiary: '#ffc658',
  quaternary: '#ff7c7c',
};

// Pagination
export const DEFAULT_PAGE_SIZE = 10;
export const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];
