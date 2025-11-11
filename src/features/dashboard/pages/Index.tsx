import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useState, useEffect } from 'react';
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown, Activity, Clock, AlertCircle, RefreshCw, Search, BarChart3, TrendingUpIcon } from "lucide-react";
import { MarketCountdown } from "@/shared/components/MarketCountdown";

// Import services and types
import { dashboardService } from "@/api/services/dashboard.service";
import type { DashboardSummary, StockSummary } from "@/api/types/backend-schemas";

// Import empty state components
import {EmptyPipelineState, PartialDataWarning } from "@/shared/components/states";
import { validateDashboardData } from "@/shared/utils/dataValidation";
import DashboardSkeleton from "@/features/dashboard/components/DashboardSkeleton";

// Import utility functions
import { formatTimeAgo } from "@/shared/utils/timeUtils";

const Index = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [lastRefresh, setLastRefresh] = useState<number>(Date.now());

  // Fetch dashboard data with React Query
  // Use shorter refetch interval (30 seconds) to catch pipeline updates quickly
  const { data: response, isLoading, error, refetch } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: () => dashboardService.getDashboardSummary(),
    refetchInterval: 30000, // Refresh every 30 seconds (more aggressive)
    retry: 2,
  });

  // Force refetch when user focuses window (e.g., switching back from admin panel)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        refetch();
        setLastRefresh(Date.now());
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [refetch]);

  // Loading state
  if (isLoading) {
    return (
      <UserLayout>
        <DashboardSkeleton />
      </UserLayout>
    );
  }

  // Error state
  if (error || response?.error) {
    return (
      <UserLayout>
        <Alert variant="destructive" className="mb-6">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load dashboard data: {error?.message || response?.error}
            <Button 
              variant="outline" 
              size="sm" 
              className="ml-4"
              onClick={() => refetch()}
            >
              <RefreshCw className="h-4 w-4 mr-2" />
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </UserLayout>
    );
  }

  // Extract data from response
  const data = response?.data;

  // Validate data
  const validation = validateDashboardData(data);

  // Empty state (pipeline not run)
  if (validation.isEmpty) {
    return (
      <UserLayout>
        <EmptyPipelineState />
      </UserLayout>
    );
  }

  // If we get here, data exists
  const { market_overview, top_stocks, system_status } = data!;

  // Split stocks for display
  const topPositive = top_stocks
    .filter(s => (s.sentiment_score ?? 0) > 0)
    .sort((a, b) => (b.sentiment_score ?? 0) - (a.sentiment_score ?? 0))
    .slice(0, 5);
    
  const topNegative = top_stocks
    .filter(s => (s.sentiment_score ?? 0) < 0)
    .sort((a, b) => (a.sentiment_score ?? 0) - (b.sentiment_score ?? 0))
    .slice(0, 5);

  // Helper functions
  const formatPrice = (price: number | null) => {
    return price !== null ? `$${price.toFixed(2)}` : 'N/A';
  };

  const formatChange = (change: number | null) => {
    if (change === null) return 'N/A';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  const formatMarketCap = (stocks: StockSummary[]) => {
    // Real Market Cap = Stock Price × Shares Outstanding
    // Since we don't have shares outstanding data from APIs, we'll use typical values
    // for tech companies (ranges from ~300M for small caps to ~16B for mega caps like AAPL)
    
    const typicalSharesOutstanding: Record<string, number> = {
      'AAPL': 15204100000,   // Apple: ~15.2B shares
      'MSFT': 7430000000,    // Microsoft: ~7.43B shares
      'GOOGL': 5840000000,   // Alphabet (Class A): ~5.84B shares
      'GOOG': 5840000000,    // Alphabet (Class C): ~5.84B shares
      'AMZN': 10190000000,   // Amazon: ~10.19B shares
      'NVDA': 24460000000,   // NVIDIA: ~24.46B shares (after splits)
      'META': 2550000000,    // Meta: ~2.55B shares
      'TSLA': 3178000000,    // Tesla: ~3.18B shares
      'AVGO': 460000000,     // Broadcom: ~460M shares
      'ORCL': 2710000000,    // Oracle: ~2.71B shares
      'CSCO': 4020000000,    // Cisco: ~4.02B shares
      'ADBE': 450000000,     // Adobe: ~450M shares
      'CRM': 970000000,      // Salesforce: ~970M shares
      'INTC': 4140000000,    // Intel: ~4.14B shares
      'AMD': 1620000000,     // AMD: ~1.62B shares
      'QCOM': 1120000000,    // Qualcomm: ~1.12B shares
      'TXN': 910000000,      // Texas Instruments: ~910M shares
      'AMAT': 870000000,     // Applied Materials: ~870M shares
      'MU': 1110000000,      // Micron: ~1.11B shares
      'LRCX': 136000000,     // Lam Research: ~136M shares
    };
    
    let totalMarketCap = 0;
    
    for (const stock of stocks) {
      const price = stock.current_price ?? 0;
      const shares = typicalSharesOutstanding[stock.symbol] || 1000000000; // Default 1B shares for unknown
      
      // Market Cap = Price × Shares Outstanding
      totalMarketCap += price * shares;
    }
    
    if (totalMarketCap === 0) return '$0.0T';
    
    // Format based on magnitude
    if (totalMarketCap >= 1000000000000) {
      return `$${(totalMarketCap / 1000000000000).toFixed(1)}T`;
    } else if (totalMarketCap >= 1000000000) {
      return `$${(totalMarketCap / 1000000000).toFixed(1)}B`;
    } else if (totalMarketCap >= 1000000) {
      return `$${(totalMarketCap / 1000000).toFixed(1)}M`;
    } else {
      return `$${totalMarketCap.toFixed(0)}`;
    }
  };

  const formatDataPoints = (count: number) => {
    if (count >= 1000000) {
      return `${(count / 1000000).toFixed(1)}M`;
    } else if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    } else {
      return count.toString();
    }
  };

  // Format pipeline status
  const getPipelineStatusDisplay = (status: string) => {
    const statusMap: Record<string, { text: string; color: string }> = {
      'operational': { text: 'Operational', color: 'text-green-600' },
      'delayed': { text: 'Delayed', color: 'text-yellow-600' },
      'stale': { text: 'Data Stale', color: 'text-orange-600' },
      'no_data': { text: 'No Data Collected', color: 'text-gray-600' }
    };
    return statusMap[status] || { text: status, color: 'text-gray-600' };
  };

  // Check if data is partial
  const showWarning = validation.isPartial;

  return (
    <UserLayout>
      <div className="space-y-8">
        {/* Partial Data Warning */}
        {showWarning && (
          <PartialDataWarning 
            dataPoints={top_stocks.length}
            minRequired={5}
          />
        )}

        {/* Header */}
        <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 rounded-2xl p-8 text-white shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-transparent"></div>
          <div className="relative z-10">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div>
                <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
                  Stock Market Sentiment Dashboard
                </h1>
                <p className="text-blue-100 text-lg leading-relaxed max-w-2xl">
                  Near-real-time sentiment analysis and comprehensive market overview for technology stocks
                </p>
                <div className="flex items-center gap-2 mt-4 text-blue-200">
                  <Clock className="h-4 w-4" />
                  <span className="text-sm">
                    Last updated: {formatTimeAgo(system_status.last_collection)}
                  </span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => refetch()}
                    className="ml-2 text-blue-200 hover:text-white hover:bg-white/20"
                    title="Refresh dashboard data"
                  >
                    <RefreshCw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <Badge className="bg-green-500/20 text-green-100 border-green-400/30 px-4 py-2">
                  <Activity className="h-4 w-4 mr-2" />
                  {market_overview.total_stocks} Active Stocks
                </Badge>
                <Badge className={`px-4 py-2 ${
                  system_status.pipeline_status === 'operational' 
                    ? 'bg-green-500/20 text-green-100 border-green-400/30'
                    : system_status.pipeline_status === 'no_data'
                    ? 'bg-gray-500/20 text-gray-100 border-gray-400/30'
                    : 'bg-yellow-500/20 text-yellow-100 border-yellow-400/30'
                }`}>
                  <TrendingUp className="h-4 w-4 mr-2" />
                  {getPipelineStatusDisplay(system_status.pipeline_status).text.toUpperCase()}
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Market Status Countdown - Prominent Position */}
        <Card className="bg-gradient-to-br from-amber-50 to-yellow-50 border-l-4 border-l-amber-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-amber-600" />
              Market Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <MarketCountdown />
          </CardContent>
        </Card>

        {/* Stats Cards - MATCHING SCREENSHOT */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Average Sentiment */}
          <Card className="bg-gradient-to-br from-green-50 to-emerald-100 border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Average Sentiment</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-gray-900 mb-1">
                {market_overview.average_sentiment.toFixed(2)}
              </div>
              <p className="text-sm text-gray-600">
                Across {market_overview.total_stocks} stocks
              </p>
            </CardContent>
          </Card>

          {/* Market Cap */}
          <Card className="bg-gradient-to-br from-blue-50 to-sky-100 border-l-4 border-l-blue-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Market Cap</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-gray-900 mb-1">
                {formatMarketCap(top_stocks)}
              </div>
              <p className="text-sm text-gray-600">
                Combined market capitalization
              </p>
            </CardContent>
          </Card>

          {/* Active Stocks */}
          <Card className="bg-gradient-to-br from-purple-50 to-violet-100 border-l-4 border-l-purple-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Active Stocks</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-gray-900 mb-1">
                {market_overview.total_stocks}
              </div>
              <p className="text-sm text-gray-600">
                Top Technology Stocks
              </p>
            </CardContent>
          </Card>

          {/* Data Points */}
          <Card className="bg-gradient-to-br from-orange-50 to-amber-100 border-l-4 border-l-orange-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium text-gray-600">Data Points</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-4xl font-bold text-gray-900 mb-1">
                {formatDataPoints(system_status.total_sentiment_records)}
              </div>
              <p className="text-sm text-gray-600">
                Total sentiment records
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Three Column Layout - MATCHING SCREENSHOT */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top Positive Sentiment - GREEN BOX */}
          <Card className="bg-gradient-to-br from-green-50 to-emerald-50 border-t-4 border-t-green-500">
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                <CardTitle className="text-lg">Top Positive Sentiment</CardTitle>
              </div>
              <CardDescription>Stocks with highest positive sentiment scores</CardDescription>
            </CardHeader>
            <CardContent>
              {topPositive.length > 0 ? (
                <div className="space-y-3">
                  {topPositive.map((stock, index) => (
                    <div
                      key={stock.symbol}
                      className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => navigate(`/analysis?symbol=${stock.symbol}`)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-green-100 text-green-700 font-bold text-sm">
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-bold text-gray-900">{stock.symbol}</div>
                          <div className="text-sm text-gray-600">{formatPrice(stock.current_price)}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-green-600 text-lg">
                          {((stock.sentiment_score ?? 0) * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-600">{formatChange(stock.price_change_24h)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No positive sentiment stocks</p>
              )}
            </CardContent>
          </Card>

          {/* Top Negative Sentiment - RED BOX */}
          <Card className="bg-gradient-to-br from-red-50 to-rose-50 border-t-4 border-t-red-500">
            <CardHeader>
              <div className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-red-600" />
                <CardTitle className="text-lg">Top Negative Sentiment</CardTitle>
              </div>
              <CardDescription>Stocks with lowest sentiment scores</CardDescription>
            </CardHeader>
            <CardContent>
              {topNegative.length > 0 ? (
                <div className="space-y-3">
                  {topNegative.map((stock, index) => (
                    <div
                      key={stock.symbol}
                      className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => navigate(`/analysis?symbol=${stock.symbol}`)}
                    >
                      <div className="flex items-center gap-3">
                        <div className="flex items-center justify-center w-8 h-8 rounded-full bg-red-100 text-red-700 font-bold text-sm">
                          {index + 1}
                        </div>
                        <div>
                          <div className="font-bold text-gray-900">{stock.symbol}</div>
                          <div className="text-sm text-gray-600">{formatPrice(stock.current_price)}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-red-600 text-lg">
                          -{Math.abs((stock.sentiment_score ?? 0) * 100).toFixed(0)}%
                        </div>
                        <div className="text-xs text-gray-600">{formatChange(stock.price_change_24h)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No negative sentiment stocks</p>
              )}
            </CardContent>
          </Card>

          {/* Near-real-time Stock Prices - BLUE BOX - DYNAMIC SCROLLABLE LIST */}
          <Card className="bg-gradient-to-br from-blue-50 to-sky-50 border-t-4 border-t-blue-500">
            <CardHeader>
              <div className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-lg">Near-real-time Stock Prices</CardTitle>
              </div>
              <CardDescription>Live price overview ({top_stocks.length} technology stocks)</CardDescription>
            </CardHeader>
            <CardContent>
              {top_stocks.length > 0 ? (
                <div className="space-y-3 max-h-[400px] overflow-y-auto pr-2">
                  {top_stocks.map((stock) => (
                    <div
                      key={stock.symbol}
                      className="flex items-center justify-between p-3 bg-white rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                      onClick={() => navigate(`/analysis?symbol=${stock.symbol}`)}
                    >
                      <div className="flex items-center gap-3">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-bold text-gray-900">{stock.symbol}</span>
                            {stock.sentiment_label && stock.sentiment_score !== null && (
                              <Badge 
                                className={`text-xs ${
                                  stock.sentiment_label === 'positive' 
                                    ? 'bg-green-100 text-green-700' 
                                    : stock.sentiment_label === 'negative'
                                    ? 'bg-red-100 text-red-700'
                                    : 'bg-gray-100 text-gray-700'
                                }`}
                              >
                                {(stock.sentiment_score ?? 0) > 0 ? '+' : ''}{((stock.sentiment_score ?? 0) * 100).toFixed(0)}%
                              </Badge>
                            )}
                          </div>
                          <div className="text-sm text-gray-600">{stock.company_name}</div>
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-bold text-gray-900 text-lg">
                          {formatPrice(stock.current_price)}
                        </div>
                        <div className={`text-sm font-semibold ${
                          (stock.price_change_24h ?? 0) >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatChange(stock.price_change_24h)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-4">No stock data available</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Analytics & Insights */}
        <div className="mt-8">
          <h2 className="text-2xl font-bold mb-2">Analytics & Insights</h2>
          <p className="text-gray-600 mb-6">Explore comprehensive market analysis tools</p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Stock Analysis Card */}
            <Card className="border-t-4 border-t-blue-500 hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Search className="h-6 w-6 text-blue-600" />
                  </div>
                  <CardTitle className="text-lg">Stock Analysis</CardTitle>
                </div>
                <CardDescription>
                  Deep dive into individual stock performance with comprehensive sentiment metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  className="w-full bg-blue-600 hover:bg-blue-700"
                  onClick={() => navigate('/analysis')}
                >
                  Explore Analysis
                </Button>
              </CardContent>
            </Card>

            {/* Correlation Insights Card */}
            <Card className="border-t-4 border-t-green-500 hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <BarChart3 className="h-6 w-6 text-green-600" />
                  </div>
                  <CardTitle className="text-lg">Correlation Insights</CardTitle>
                </div>
                <CardDescription>
                  View dynamic correlation between sentiment and stock prices across markets
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  className="w-full bg-green-600 hover:bg-green-700"
                  onClick={() => navigate('/correlation')}
                >
                  View Correlations
                </Button>
              </CardContent>
            </Card>

            {/* Trend Analysis Card */}
            <Card className="border-t-4 border-t-purple-500 hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-center gap-3 mb-2">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <TrendingUpIcon className="h-6 w-6 text-purple-600" />
                  </div>
                  <CardTitle className="text-lg">Trend Analysis</CardTitle>
                </div>
                <CardDescription>
                  Analyze sentiment trends over time with advanced temporal analytics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  className="w-full bg-purple-600 hover:bg-purple-700"
                  onClick={() => navigate('/trends')}
                >
                  Analyze Trends
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* System Status */}
        <Card>
          <CardHeader>
            <CardTitle>System Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <span className="text-sm text-gray-600">Pipeline Status:</span>
                <p className={`font-semibold ${getPipelineStatusDisplay(system_status.pipeline_status).color}`}>
                  {getPipelineStatusDisplay(system_status.pipeline_status).text}
                </p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Total Records:</span>
                <p className="font-semibold">{system_status.total_sentiment_records.toLocaleString()}</p>
              </div>
              <div>
                <span className="text-sm text-gray-600">Data Sources:</span>
                <p className="font-semibold">{system_status.active_data_sources.join(', ')}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </UserLayout>
  );
};

export default Index;
