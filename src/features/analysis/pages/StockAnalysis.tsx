import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { AlertCircle, TrendingUp, TrendingDown, Minus, Info } from "lucide-react";

// Import services
import { stockService } from "@/api/services/stock.service";

// Import chart components
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts';

// Chart colors - Accessible color palette
const SENTIMENT_COLORS = {
  positive: '#059669', // emerald-600 (darker for accessibility)
  negative: '#DC2626', // red-600 (darker for accessibility)
  neutral: '#6B7280'   // gray-500
};

// Import empty state components
import { EmptyWatchlistState } from "@/shared/components/states";

// Import utility functions
import { 
  getSentimentLabel, 
  getSentimentColor, 
  getSentimentBadgeVariant,
  SENTIMENT_THRESHOLDS
} from "@/shared/utils/sentimentUtils";
import { usePipelineNotifications } from "@/shared/hooks/usePipelineNotifications";

// Sentiment Gauge Component - Visual indicator for sentiment score
const SentimentGauge = ({ score }: { score: number }) => {
  // Convert -1 to +1 scale to 0-180 degrees
  const normalizedScore = (score + 1) / 2; // 0 to 1
  const rotation = normalizedScore * 180 - 90; // -90 to 90 degrees
  
  return (
    <div className="relative w-full max-w-[160px] mx-auto">
      {/* Gauge background */}
      <div className="relative h-20 overflow-hidden">
        <div className="absolute inset-0 flex">
          <div className="w-1/3 h-full bg-gradient-to-r from-red-500 to-red-400 rounded-tl-full" />
          <div className="w-1/3 h-full bg-gradient-to-r from-yellow-400 to-yellow-300" />
          <div className="w-1/3 h-full bg-gradient-to-r from-green-400 to-green-500 rounded-tr-full" />
        </div>
        {/* Needle */}
        <div 
          className="absolute bottom-0 left-1/2 w-1 h-16 bg-gray-800 rounded-t-full origin-bottom transition-transform duration-500"
          style={{ transform: `translateX(-50%) rotate(${rotation}deg)` }}
        />
        {/* Center dot */}
        <div className="absolute bottom-0 left-1/2 w-4 h-4 bg-gray-800 rounded-full transform -translate-x-1/2 translate-y-1/2" />
      </div>
      {/* Labels */}
      <div className="flex justify-between text-xs text-gray-500 mt-1 px-1">
        <span>-1.0</span>
        <span>0</span>
        <span>+1.0</span>
      </div>
    </div>
  );
};

// Custom tooltip for pie chart - calculates percentage from total
const CustomPieTooltip = ({ active, payload, totalRecords }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    const percentage = totalRecords > 0 ? ((data.value / totalRecords) * 100).toFixed(1) : '0';
    return (
      <div className="bg-white p-3 shadow-lg rounded-lg border">
        <p className="font-semibold" style={{ color: data.payload.color }}>
          {data.name}
        </p>
        <p className="text-sm text-gray-600">
          Count: {data.value} records
        </p>
        <p className="text-sm text-gray-600">
          {percentage}% of total
        </p>
      </div>
    );
  }
  return null;
};

// Custom tooltip for bar chart
const CustomBarTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-3 shadow-lg rounded-lg border">
        <p className="font-bold text-gray-900">{data.symbol}</p>
        <p className="text-sm text-gray-600">{data.company_name}</p>
        <div className="mt-2 pt-2 border-t">
          <p className="text-sm">
            <span className="text-gray-500">Sentiment Score: </span>
            <span className={`font-semibold ${data.sentiment_score > SENTIMENT_THRESHOLDS.POSITIVE ? 'text-green-600' : data.sentiment_score < SENTIMENT_THRESHOLDS.NEGATIVE ? 'text-red-600' : 'text-gray-600'}`}>
              {data.sentiment_score.toFixed(3)}
            </span>
          </p>
          <p className="text-sm text-gray-500">
            Based on {data.data_points} data points
          </p>
        </div>
      </div>
    );
  }
  return null;
};

// Timeframe options with labels
const TIMEFRAME_OPTIONS = [
  { value: '1d', label: '1D' },
  { value: '7d', label: '7D' },
  { value: '14d', label: '14D' },
  { value: '30d', label: '30D' },
] as const;

type TimeframeValue = typeof TIMEFRAME_OPTIONS[number]['value'];

const StockAnalysis = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const timeframeFromUrl = searchParams.get('timeframe') as TimeframeValue | null;
  
  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');
  const [timeframe, setTimeframe] = useState<TimeframeValue>(
    timeframeFromUrl && ['1d', '7d', '14d', '30d'].includes(timeframeFromUrl) 
      ? timeframeFromUrl 
      : '7d'
  );

  // Listen for pipeline completion events and refetch data
  usePipelineNotifications(() => {
    // Query invalidation is handled by the hook
  });

  // Fetch stock list for dropdown
  const { data: stockListResponse, isLoading: isLoadingList } = useQuery({
    queryKey: ['stocks-list'],
    queryFn: () => stockService.getAllStocks(100, true),
    staleTime: 30 * 1000,
    refetchOnWindowFocus: true,
    refetchInterval: 60 * 1000,
  });

  // Fetch selected stock analysis data with timeframe
  // Each timeframe gets its own cache entry, refetches when timeframe changes
  const { data: stockAnalysisResponse, isLoading: isLoadingAnalysis, error, isFetching } = useQuery({
    queryKey: ['stock-analysis', selectedStock, timeframe],
    queryFn: () => stockService.getStockAnalysis(selectedStock, timeframe),
    enabled: !!selectedStock,
    staleTime: 30 * 1000, // 30 seconds cache per timeframe
    refetchOnMount: true,
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
    setSearchParams({ symbol, timeframe });
  };

  // Handle timeframe change
  const handleTimeframeChange = (value: TimeframeValue) => {
    setTimeframe(value);
    if (selectedStock) {
      setSearchParams({ symbol: selectedStock, timeframe: value });
    }
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

  // Helper function to get sentiment icon
  const getSentimentIcon = (score: number) => {
    if (score > SENTIMENT_THRESHOLDS.POSITIVE) return <TrendingUp className="h-5 w-5 text-green-600" />;
    if (score < SENTIMENT_THRESHOLDS.NEGATIVE) return <TrendingDown className="h-5 w-5 text-red-600" />;
    return <Minus className="h-5 w-5 text-gray-500" />;
  };

  // Prepare pie chart data with filtering for zero values
  const getPieChartData = () => {
    if (!stockAnalysis?.sentiment_distribution) return [];
    const { positive, negative, neutral } = stockAnalysis.sentiment_distribution;
    return [
      { name: 'Positive', value: positive, color: SENTIMENT_COLORS.positive },
      { name: 'Negative', value: negative, color: SENTIMENT_COLORS.negative },
      { name: 'Neutral', value: neutral, color: SENTIMENT_COLORS.neutral }
    ].filter(item => item.value > 0);
  };

  // Prepare bar chart data with color coding
  const getBarChartData = () => {
    if (!stockAnalysis?.top_performers) return [];
    return stockAnalysis.top_performers.map((performer: any) => ({
      ...performer,
      fill: performer.sentiment_score > SENTIMENT_THRESHOLDS.POSITIVE ? SENTIMENT_COLORS.positive : 
            performer.sentiment_score < SENTIMENT_THRESHOLDS.NEGATIVE ? SENTIMENT_COLORS.negative : 
            SENTIMENT_COLORS.neutral
    }));
  };

  return (
    <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900">Stock Analysis</h1>
            <p className="text-slate-500 text-sm mt-1">
              Comprehensive sentiment analysis and performance metrics
            </p>
          </div>
          
          <div className="flex flex-wrap items-center gap-3 bg-white p-2 rounded-lg border shadow-sm">
            {/* Stock Selector */}
            <Select value={selectedStock} onValueChange={handleStockChange}>
              <SelectTrigger className="w-[140px] md:w-[200px] h-9">
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

            {/* Timeframe Selector - Button Style */}
            <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
              {TIMEFRAME_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleTimeframeChange(option.value)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                    timeframe === option.value
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>
            
            {/* Loading indicator */}
            {isFetching && !isLoadingAnalysis && (
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>
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
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {[1, 2, 3].map(i => (
                    <Skeleton key={i} className="h-32" />
                  ))}
                </div>
              </CardContent>
            </Card>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Skeleton className="h-80" />
              <Skeleton className="h-80" />
            </div>
          </div>
        )}

        {/* Stock Overview - Redesigned with 3 key metrics */}
        {!isLoadingAnalysis && stockAnalysis && (
          <Card className="border-l-4 border-l-blue-500 overflow-hidden">
            <CardHeader className="pb-2">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div className="flex items-center gap-3">
                  <CardTitle className="text-xl">
                    {stockAnalysis.symbol}
                  </CardTitle>
                  <Badge 
                    variant={getSentimentBadgeVariant(stockAnalysis.stock_overview.sentiment_score)}
                    className="text-sm"
                  >
                    {getSentimentLabel(stockAnalysis.stock_overview.sentiment_score)}
                  </Badge>
                  {/* Market Status Badge */}
                  <Badge 
                    variant="outline"
                    className={`text-xs ${
                      stockAnalysis.stock_overview.market_status === 'Open' ? 'border-green-500 text-green-600' : 
                      stockAnalysis.stock_overview.market_status === 'Pre-Market' ? 'border-blue-500 text-blue-600' :
                      stockAnalysis.stock_overview.market_status === 'After-Hours' ? 'border-orange-500 text-orange-600' :
                      'border-gray-400 text-gray-500'
                    }`}
                  >
                    {stockAnalysis.stock_overview.market_status}
                  </Badge>
                </div>
                <span className="text-sm text-gray-500">
                  {stockAnalysis.stock_overview.company_name} • {stockAnalysis.stock_overview.sector}
                </span>
              </div>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Current Price */}
                <div className="text-center p-5 bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl">
                  <p className="text-sm font-medium text-blue-700 mb-1">Current Price</p>
                  <p className="text-4xl font-bold text-blue-600">
                    ${stockAnalysis.stock_overview.current_price}
                  </p>
                  <p className={`text-sm font-medium mt-2 ${stockAnalysis.stock_overview.price_change_24h >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    {stockAnalysis.stock_overview.price_change_24h >= 0 ? '↑' : '↓'} {Math.abs(stockAnalysis.stock_overview.price_change_24h).toFixed(2)}% (24h)
                  </p>
                </div>

                {/* Sentiment Score with Gauge */}
                <div className="text-center p-5 bg-gradient-to-br from-gray-50 to-gray-100 rounded-xl">
                  <p className="text-sm font-medium text-gray-700 mb-1">
                    Sentiment Score
                    <span className="ml-1 text-xs font-normal text-gray-500">
                      ({TIMEFRAME_OPTIONS.find(t => t.value === timeframe)?.label})
                    </span>
                  </p>
                  <SentimentGauge score={stockAnalysis.stock_overview.sentiment_score} />
                  <div className="flex items-center justify-center gap-2 mt-2">
                    {getSentimentIcon(stockAnalysis.stock_overview.sentiment_score)}
                    <span className={`text-lg font-bold ${getSentimentColor(stockAnalysis.stock_overview.sentiment_score)}`}>
                      {stockAnalysis.stock_overview.sentiment_score >= 0 ? '+' : ''}{stockAnalysis.stock_overview.sentiment_score.toFixed(3)}
                    </span>
                  </div>
                  <p className="text-xs text-gray-500 mt-1">
                    Scale: -1.0 (bearish) to +1.0 (bullish)
                  </p>
                </div>

                {/* Sentiment Distribution Summary */}
                <div className="text-center p-5 bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl">
                  <p className="text-sm font-medium text-purple-700 mb-3">Sentiment Breakdown</p>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 flex items-center gap-1">
                        <span className="w-3 h-3 rounded-full bg-green-500"></span> Positive
                      </span>
                      <span className="font-semibold text-green-600">
                        {stockAnalysis.sentiment_distribution.positive_percent?.toFixed(0) || 0}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 flex items-center gap-1">
                        <span className="w-3 h-3 rounded-full bg-gray-400"></span> Neutral
                      </span>
                      <span className="font-semibold text-gray-600">
                        {stockAnalysis.sentiment_distribution.neutral_percent?.toFixed(0) || 0}%
                      </span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-gray-600 flex items-center gap-1">
                        <span className="w-3 h-3 rounded-full bg-red-500"></span> Negative
                      </span>
                      <span className="font-semibold text-red-600">
                        {stockAnalysis.sentiment_distribution.negative_percent?.toFixed(0) || 0}%
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-gray-500 mt-3">
                    Based on {stockAnalysis.sentiment_distribution.total} records
                    <br />
                    <span className="text-gray-400">
                      (Last {timeframe === '1d' ? '24 hours' : timeframe === '7d' ? '7 days' : timeframe === '14d' ? '14 days' : '30 days'})
                    </span>
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Charts Section - Improved Layout */}
        {!isLoadingAnalysis && stockAnalysis && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Sentiment Distribution Donut Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  Sentiment Distribution
                  <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    {stockAnalysis.symbol}
                  </span>
                </CardTitle>
                <CardDescription>
                  Proportion of positive, neutral, and negative sentiment records
                </CardDescription>
              </CardHeader>
              <CardContent>
                {stockAnalysis.sentiment_distribution.total > 0 ? (
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={getPieChartData()}
                          cx="50%"
                          cy="50%"
                          innerRadius={55}
                          outerRadius={85}
                          paddingAngle={3}
                          dataKey="value"
                          label={({ name, percent }) => 
                            percent > 0.05 ? `${(percent * 100).toFixed(0)}%` : ''
                          }
                          labelLine={false}
                        >
                          {getPieChartData().map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} stroke="white" strokeWidth={2} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomPieTooltip totalRecords={stockAnalysis.sentiment_distribution.total} />} />
                        <Legend 
                          verticalAlign="bottom" 
                          height={36}
                          formatter={(value, entry: any) => (
                            <span className="text-sm text-gray-700">{value}</span>
                          )}
                        />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-72 flex flex-col items-center justify-center text-gray-500">
                    <Info className="h-12 w-12 text-gray-300 mb-3" />
                    <p>No sentiment data available</p>
                    <p className="text-sm text-gray-400 mt-1">Run the data pipeline to collect sentiment</p>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Top Sentiment Performers - Horizontal Bar Chart */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  Watchlist Comparison
                  <span className="text-xs font-normal text-gray-500 bg-gray-100 px-2 py-1 rounded">
                    Top 5
                  </span>
                </CardTitle>
                <CardDescription>
                  Compare sentiment scores across your watchlist stocks
                </CardDescription>
              </CardHeader>
              <CardContent>
                {stockAnalysis.top_performers.length > 0 ? (
                  <div className="h-72">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart 
                        data={getBarChartData()} 
                        layout="vertical"
                        margin={{ left: 10, right: 30, top: 5, bottom: 5 }}
                      >
                        <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} />
                        <XAxis 
                          type="number" 
                          domain={[-1, 1]} 
                          tickFormatter={(v) => v.toFixed(1)}
                          tick={{ fontSize: 12 }}
                        />
                        <YAxis 
                          type="category" 
                          dataKey="symbol" 
                          width={50}
                          tick={{ fontSize: 12, fontWeight: 500 }}
                        />
                        <Tooltip content={<CustomBarTooltip />} />
                        <Bar 
                          dataKey="sentiment_score" 
                          radius={[0, 4, 4, 0]}
                        >
                          {getBarChartData().map((entry: any, index: number) => (
                            <Cell key={`cell-${index}`} fill={entry.fill} />
                          ))}
                        </Bar>
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                ) : (
                  <div className="h-72 flex flex-col items-center justify-center text-gray-500">
                    <Info className="h-12 w-12 text-gray-300 mb-3" />
                    <p>No comparison data available</p>
                    <p className="text-sm text-gray-400 mt-1">Add more stocks to your watchlist</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Watchlist Overview Table - Enhanced */}
        {!isLoadingAnalysis && stockAnalysis && (
          <Card>
            <CardHeader>
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                <div>
                  <CardTitle>Watchlist Overview</CardTitle>
                  <CardDescription>All monitored stocks with real-time metrics</CardDescription>
                </div>
                <Badge variant="outline" className="w-fit">
                  {stockAnalysis.watchlist_overview.length} stocks
                </Badge>
              </div>
            </CardHeader>
            <CardContent>
              {stockAnalysis.watchlist_overview.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b bg-gray-50">
                        <th className="text-left py-3 px-4 font-semibold text-gray-700 text-sm">Symbol</th>
                        <th className="text-left py-3 px-4 font-semibold text-gray-700 text-sm">Company</th>
                        <th className="text-right py-3 px-4 font-semibold text-gray-700 text-sm">Price</th>
                        <th className="text-right py-3 px-4 font-semibold text-gray-700 text-sm">24h Change</th>
                        <th className="text-center py-3 px-4 font-semibold text-gray-700 text-sm">Sentiment</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stockAnalysis.watchlist_overview.map((stock: any) => (
                        <tr 
                          key={stock.symbol} 
                          className={`border-b transition-colors cursor-pointer ${
                            stock.symbol === selectedStock 
                              ? 'bg-blue-50 hover:bg-blue-100' 
                              : 'hover:bg-gray-50'
                          }`}
                          onClick={() => handleStockChange(stock.symbol)}
                        >
                          <td className="py-3 px-4">
                            <span className={`font-bold ${stock.symbol === selectedStock ? 'text-blue-600' : 'text-gray-900'}`}>
                              {stock.symbol}
                            </span>
                          </td>
                          <td className="py-3 px-4 text-gray-600 text-sm">{stock.company_name}</td>
                          <td className="py-3 px-4 text-right font-medium text-gray-900">${stock.price}</td>
                          <td className={`py-3 px-4 text-right font-medium ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                            <span className="inline-flex items-center gap-1">
                              {stock.change >= 0 ? <TrendingUp className="h-3 w-3" /> : <TrendingDown className="h-3 w-3" />}
                              {stock.change >= 0 ? '+' : ''}{stock.change}%
                            </span>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center justify-center gap-2">
                              {/* Visual sentiment bar */}
                              <div className="w-20 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div 
                                  className={`h-full rounded-full transition-all ${
                                    stock.sentiment > SENTIMENT_THRESHOLDS.POSITIVE ? 'bg-green-500' : 
                                    stock.sentiment < SENTIMENT_THRESHOLDS.NEGATIVE ? 'bg-red-500' : 
                                    'bg-gray-400'
                                  }`}
                                  style={{ 
                                    width: `${((stock.sentiment + 1) / 2) * 100}%`,
                                    marginLeft: stock.sentiment < 0 ? 'auto' : 0
                                  }}
                                />
                              </div>
                              <span className={`text-sm font-semibold min-w-[50px] text-right ${
                                stock.sentiment > SENTIMENT_THRESHOLDS.POSITIVE ? 'text-green-600' : 
                                stock.sentiment < SENTIMENT_THRESHOLDS.NEGATIVE ? 'text-red-600' : 
                                'text-gray-500'
                              }`}>
                                {stock.sentiment >= 0 ? '+' : ''}{stock.sentiment.toFixed(2)}
                              </span>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="text-center py-12 text-gray-500">
                  <Info className="h-12 w-12 text-gray-300 mx-auto mb-3" />
                  <p>No watchlist data available</p>
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
              <strong>No Data Available:</strong> No analysis data found for {selectedStock}. 
              Run the data collection pipeline to gather sentiment analysis from news sources and social media.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </UserLayout>
  );
};

export default StockAnalysis;
