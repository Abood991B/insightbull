import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { AlertCircle } from "lucide-react";

// Import services and types
import { stockService } from "@/api/services/stock.service";
import type { StockDetail, StockList } from "@/api/types/backend-schemas";

// Import chart components
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Chart colors
const SENTIMENT_COLORS = {
  positive: '#10B981', // green-500
  negative: '#EF4444', // red-500
  neutral: '#6B7280'   // gray-500
};

// Import empty state components
import { EmptyWatchlistState } from "@/shared/components/states";

// Import utility functions
import { 
  getSentimentLabel, 
  getSentimentColor, 
  getSentimentBadgeVariant 
} from "@/shared/utils/sentimentUtils";
import { usePipelineNotifications } from "@/shared/hooks/usePipelineNotifications";

const StockAnalysis = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');

  // Listen for pipeline completion events and refetch data
  usePipelineNotifications(() => {
    // Query invalidation is handled by the hook, just need to be present
  });

  // Fetch stock list for dropdown
  const { data: stockListResponse, isLoading: isLoadingList } = useQuery({
    queryKey: ['stocks-list'],
    queryFn: () => stockService.getAllStocks(100, true),
    staleTime: 30 * 1000, // 30 seconds - sync with admin changes faster
    refetchOnWindowFocus: true, // Refetch when user returns to tab
    refetchInterval: 60 * 1000, // Poll every minute for admin changes
  });

  // Fetch selected stock analysis data
  const { data: stockAnalysisResponse, isLoading: isLoadingAnalysis, error } = useQuery({
    queryKey: ['stock-analysis', selectedStock],
    queryFn: () => stockService.getStockAnalysis(selectedStock, '7d'),
    enabled: !!selectedStock, // Only fetch if stock is selected
    staleTime: 60 * 1000, // Cache for 1 minute
  });

  // Set first stock as default when list loads
  useEffect(() => {
    if (!selectedStock && stockListResponse?.data?.stocks.length) {
      const firstStock = stockListResponse.data.stocks[0].symbol;
      setSelectedStock(firstStock);
      setSearchParams({ symbol: firstStock });
    }
  }, [stockListResponse, selectedStock, setSearchParams]);

  // Handle stock selection
  const handleStockChange = (symbol: string) => {
    setSelectedStock(symbol);
    setSearchParams({ symbol });
  };

  // Extract data
  const stockList = stockListResponse?.data;
  const stockAnalysis = stockAnalysisResponse?.data;

  // Loading state for dropdown
  if (isLoadingList) {
    return (
      <UserLayout>
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <Skeleton className="h-10 w-64" />
            <Skeleton className="h-10 w-48" />
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      </UserLayout>
    );
  }

  // Empty watchlist state
  if (!stockList || stockList.stocks.length === 0) {
    return (
      <UserLayout>
        <EmptyWatchlistState />
      </UserLayout>
    );
  }

  // Find current stock in list
  const currentStockInfo = stockList.stocks.find(s => s.symbol === selectedStock);

  // Helper functions
  const formatPrice = (price: number | null) => {
    return price !== null ? `$${price.toFixed(2)}` : 'N/A';
  };

  const formatChange = (change: number | null) => {
    if (change === null) return 'N/A';
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}%`;
  };

  return (
    <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Stock Analysis</h1>
            <p className="text-gray-600 mt-2">
              Detailed analysis of individual stock performance and sentiment from our real-time dashboard
            </p>
          </div>
          
          <Select value={selectedStock} onValueChange={handleStockChange}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select stock" />
            </SelectTrigger>
            <SelectContent>
              {stockList.stocks.map((stock) => (
                <SelectItem key={stock.symbol} value={stock.symbol}>
                  {stock.symbol} - {stock.company_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Error State */}
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load stock details: {error.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Loading Analysis State */}
        {isLoadingAnalysis && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <Skeleton className="h-6 w-48" />
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  {[1, 2, 3, 4].map(i => (
                    <Skeleton key={i} className="h-24" />
                  ))}
                </div>
              </CardContent>
            </Card>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Skeleton className="h-80" />
              <Skeleton className="h-80" />
            </div>
            <Skeleton className="h-96" />
          </div>
        )}

        {/* Stock Overview */}
        {!isLoadingAnalysis && stockAnalysis && (
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                {stockAnalysis.symbol} - {stockAnalysis.stock_overview.company_name}
                <Badge 
                  variant={getSentimentBadgeVariant(stockAnalysis.stock_overview.sentiment_score)}
                  className="text-sm"
                >
                  {getSentimentLabel(stockAnalysis.stock_overview.sentiment_score)}
                </Badge>
              </CardTitle>
              <CardDescription>
                Real-time stock information and sentiment analysis | Sector: {stockAnalysis.stock_overview.sector}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                {/* Current Price */}
                <div className="text-center p-4 bg-blue-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Current Price</p>
                  <p className="text-3xl font-bold text-blue-600">
                    ${stockAnalysis.stock_overview.current_price}
                  </p>
                </div>

                {/* Sentiment Score */}
                <div className="text-center p-4 bg-green-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Sentiment Score</p>
                  <p className={`text-3xl font-bold ${getSentimentColor(stockAnalysis.stock_overview.sentiment_score)}`}>
                    {stockAnalysis.stock_overview.sentiment_score.toFixed(2)}
                  </p>
                </div>

                {/* 24h Change */}
                <div className="text-center p-4 bg-purple-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">24h Change</p>
                  <p className={`text-3xl font-bold ${stockAnalysis.stock_overview.price_change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {stockAnalysis.stock_overview.price_change_24h >= 0 ? '+' : ''}{stockAnalysis.stock_overview.price_change_24h}%
                  </p>
                </div>

                {/* Market Status */}
                <div className="text-center p-4 bg-yellow-50 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Market Status</p>
                  <p className={`text-3xl font-bold ${
                    stockAnalysis.stock_overview.market_status === 'Open' ? 'text-green-600' : 
                    stockAnalysis.stock_overview.market_status === 'Pre-Market' ? 'text-blue-600' :
                    stockAnalysis.stock_overview.market_status === 'After-Hours' ? 'text-orange-600' :
                    'text-gray-600'
                  }`}>
                    {stockAnalysis.stock_overview.market_status}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Charts Section */}
        {!isLoadingAnalysis && stockAnalysis && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sentiment Distribution Pie Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Sentiment Distribution</CardTitle>
                <CardDescription>Breakdown of sentiment analysis for {stockAnalysis.symbol}</CardDescription>
              </CardHeader>
              <CardContent>
                {stockAnalysis.sentiment_distribution.total > 0 ? (
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={[
                            { name: 'Positive', value: stockAnalysis.sentiment_distribution.positive, color: SENTIMENT_COLORS.positive },
                            { name: 'Negative', value: stockAnalysis.sentiment_distribution.negative, color: SENTIMENT_COLORS.negative },
                            { name: 'Neutral', value: stockAnalysis.sentiment_distribution.neutral, color: SENTIMENT_COLORS.neutral }
                          ]}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                          outerRadius={80}
                          fill="#8884d8"
                          dataKey="value"
                        >
                          {[
                            { name: 'Positive', value: stockAnalysis.sentiment_distribution.positive, color: SENTIMENT_COLORS.positive },
                            { name: 'Negative', value: stockAnalysis.sentiment_distribution.negative, color: SENTIMENT_COLORS.negative },
                            { name: 'Neutral', value: stockAnalysis.sentiment_distribution.neutral, color: SENTIMENT_COLORS.neutral }
                          ].map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                    <div className="mt-4 text-center text-sm text-gray-600">
                      Total: {stockAnalysis.sentiment_distribution.total} sentiment records
                    </div>
                  </div>
                ) : (
                  <div className="h-80 flex items-center justify-center text-gray-500">
                    No sentiment data available
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Top Sentiment Performers Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle>Top Sentiment Performers</CardTitle>
                <CardDescription>Highest sentiment scores in watchlist</CardDescription>
              </CardHeader>
              <CardContent>
                {stockAnalysis.top_performers.length > 0 ? (
                  <div className="h-80">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={stockAnalysis.top_performers}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="symbol" />
                        <YAxis />
                        <Tooltip 
                          formatter={(value, name) => [value, 'Sentiment Score']}
                          labelFormatter={(label) => `Stock: ${label}`}
                        />
                        <Bar dataKey="sentiment_score" fill="#3B82F6" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-80 flex items-center justify-center text-gray-500">
                    No performance data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Watchlist Overview Table */}
        {!isLoadingAnalysis && stockAnalysis && (
          <Card>
            <CardHeader>
              <CardTitle>Watchlist Overview</CardTitle>
              <CardDescription>Complete view of all monitored technology stocks</CardDescription>
            </CardHeader>
            <CardContent>
              {stockAnalysis.watchlist_overview.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Stock</th>
                        <th className="text-left py-3 px-4 font-medium text-gray-900">Company</th>
                        <th className="text-right py-3 px-4 font-medium text-gray-900">Price</th>
                        <th className="text-right py-3 px-4 font-medium text-gray-900">Change</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-900">Sentiment</th>
                        <th className="text-center py-3 px-4 font-medium text-gray-900">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stockAnalysis.watchlist_overview.map((stock, index) => (
                        <tr key={stock.symbol} className={`border-b hover:bg-gray-50 ${stock.symbol === selectedStock ? 'bg-blue-50' : ''}`}>
                          <td className="py-3 px-4">
                            <button
                              onClick={() => handleStockChange(stock.symbol)}
                              className="text-blue-600 hover:text-blue-800 font-medium"
                            >
                              {stock.symbol}
                            </button>
                          </td>
                          <td className="py-3 px-4 text-gray-900">{stock.company_name}</td>
                          <td className="py-3 px-4 text-right font-medium">${stock.price}</td>
                          <td className={`py-3 px-4 text-right font-medium ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            {stock.change >= 0 ? '+' : ''}{stock.change}%
                          </td>
                          <td className="py-3 px-4 text-center">
                            <div className="flex items-center justify-center">
                              <div className={`w-16 h-2 rounded-full ${getSentimentColor(stock.sentiment)} bg-current opacity-20`}>
                                <div 
                                  className={`h-full rounded-full ${getSentimentColor(stock.sentiment)} bg-current`}
                                  style={{ width: `${Math.abs(stock.sentiment) * 100}%` }}
                                />
                              </div>
                              <span className={`ml-2 text-sm font-medium ${getSentimentColor(stock.sentiment)}`}>
                                {stock.sentiment.toFixed(1)}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-center">
                            <Badge variant="secondary" className="text-xs">
                              {stock.status}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  No watchlist data available
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* No Analysis Data Warning */}
        {!isLoadingAnalysis && !stockAnalysis && !error && selectedStock && (
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-900">
              <strong>No Data Available:</strong> No analysis data found for {selectedStock}. This typically means the data collection pipeline needs to run to gather sentiment analysis from news sources and social media. Please check back later or try a different stock.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </UserLayout>
  );
};

export default StockAnalysis;
