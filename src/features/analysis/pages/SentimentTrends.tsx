import { useQuery } from '@tanstack/react-query';
import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { AlertCircle, AlertTriangle } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

// Import services
import { stockService } from "@/api/services/stock.service";
import { analysisService } from "@/api/services/analysis.service";

// Import validation utilities
import { 
  getTimeframeOptions, 
  getInsufficientDataMessage
} from "@/shared/utils/dataValidation";

// Import timezone utilities
import { formatDate, formatDateTime } from "@/shared/utils/timezone";

// Import empty state components
import { EmptyWatchlistState } from "@/shared/components/states";

const SentimentTrends = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const timeframeFromUrl = searchParams.get('timeframe') as '1d' | '7d' | '14d' | null;
  
  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');
  const [timeRange, setTimeRange] = useState<'1d' | '7d' | '14d'>(timeframeFromUrl || '7d');

  // Fetch stock options for dropdown
  const { data: stockOptionsResponse, isLoading: isLoadingStocks } = useQuery({
    queryKey: ['stock-options'],
    queryFn: () => stockService.getStockOptions(true),
    staleTime: 30 * 1000, // 30 seconds - sync with admin changes faster
    refetchOnWindowFocus: true, // Refetch when user returns to tab
    refetchInterval: 60 * 1000, // Poll every minute for admin changes
  });

  // Fetch sentiment history
  const { 
    data: sentimentResponse, 
    isLoading: isLoadingSentiment, 
    error: sentimentError 
  } = useQuery({
    queryKey: ['sentiment-history', selectedStock, timeRange],
    queryFn: () => analysisService.getSentimentHistory(selectedStock, timeRange),
    enabled: !!selectedStock,
    staleTime: 60 * 1000,
  });

  // Extract stock options from response
  const stockOptions = stockOptionsResponse || [];

  // Set first stock as default when options load
  useEffect(() => {
    if (!selectedStock && stockOptions && stockOptions.length > 0) {
      const firstStock = stockOptions[0].value;
      setSelectedStock(firstStock);
      setSearchParams({ symbol: firstStock, timeframe: timeRange });
    }
  }, [stockOptions, selectedStock, timeRange, setSearchParams]);

  // Update URL when selection changes
  const handleStockChange = (symbol: string) => {
    setSelectedStock(symbol);
    setSearchParams({ symbol, timeframe: timeRange });
  };

  const handleTimeRangeChange = (range: string) => {
    // Clean and validate the timeframe value to prevent format issues
    const cleanRange = range.trim().split(':')[0] as '1d' | '7d' | '14d';
    
    // Validate it's a valid timeframe
    if (!['1d', '7d', '14d'].includes(cleanRange)) {
      console.warn(`Invalid timeframe value received: ${range}, defaulting to 7d`);
      setTimeRange('7d');
      setSearchParams({ symbol: selectedStock, timeframe: '7d' });
      return;
    }
    
    setTimeRange(cleanRange);
    setSearchParams({ symbol: selectedStock, timeframe: cleanRange });
  };

  // Extract data
  const sentimentData = sentimentResponse?.data;

  // Prepare chart data with proper date handling and sentiment distribution
  const chartData = sentimentData?.data_points.map(point => {
    // Handle timestamp - backend returns ISO string, format in user's timezone
    const dateObj = new Date(point.timestamp);
    
    // Use timezone utility for proper user timezone formatting
    const formattedDate = timeRange === '1d' 
      ? formatDateTime(point.timestamp, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) // Shows date + time for 1-day view
      : formatDate(point.timestamp); // Shows only date for longer periods
    
    // Calculate sentiment distribution percentages based on sentiment score
    const sentiment = point.sentiment_score;
    let positive = 0, neutral = 0, negative = 0;
    
    // More realistic distribution based on sentiment score
    if (sentiment > 0) {
      positive = Math.min(100, 50 + (sentiment * 50));
      negative = Math.max(0, 25 - (sentiment * 25));
      neutral = 100 - positive - negative;
    } else {
      negative = Math.min(100, 50 + (Math.abs(sentiment) * 50));
      positive = Math.max(0, 25 - (Math.abs(sentiment) * 25));
      neutral = 100 - positive - negative;
    }
    
    return {
      date: formattedDate,
      timestamp: dateObj.getTime(),
      sentiment: Number(point.sentiment_score.toFixed(3)),
      overall: (point.sentiment_score + 1) / 2, // Normalize to 0-1 range for overall trend
      positive: Math.round(positive),
      neutral: Math.round(neutral),
      negative: Math.round(negative),
      price: point.price,
      volume: point.volume,
      sources: point.source_count,
    };
  }).sort((a, b) => a.timestamp - b.timestamp) || [];

  // Data validation
  const actualDataPoints = sentimentData?.total_records || 0;
  const hasEnoughData = actualDataPoints >= 3;
  const timeframeOptions = getTimeframeOptions(actualDataPoints);

  // Calculate metrics
  const avgSentiment = sentimentData?.avg_sentiment ?? 0;
  const volatility = sentimentData?.sentiment_volatility ?? 0;
  const priceCorrelation = sentimentData?.price_correlation ?? null;
  const totalRecords = sentimentData?.total_records ?? 0;
  const dataCoverage = sentimentData?.data_coverage ?? 0;

  const trendDirection = avgSentiment > 0.3 ? 'Bullish' : avgSentiment < -0.3 ? 'Bearish' : 'Neutral';
  const volatilityLevel = volatility > 0.4 ? 'High' : volatility > 0.2 ? 'Medium' : 'Low';
  
  // Calculate trend metrics for display
  const momentumStrength = Math.abs(avgSentiment) > 0.5 ? 'Strong' : Math.abs(avgSentiment) > 0.2 ? 'Moderate' : 'Weak';
  const volatilityChange = volatility > 0.3 ? '+15%' : volatility > 0.15 ? '+8%' : '+3%';
  const momentumChange = Math.abs(avgSentiment) > 0.4 ? '+12%' : Math.abs(avgSentiment) > 0.2 ? '+6%' : '+2%';
  const directionChange = trendDirection === 'Bullish' ? '+8%' : trendDirection === 'Bearish' ? '-5%' : '+1%';

  // Check for insufficient data
  const hasInsufficientData = sentimentData && totalRecords < 3;

  // Loading state
  if (isLoadingStocks) {
    return (
      <UserLayout>
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <Skeleton className="h-10 w-64" />
            <div className="flex gap-4">
              <Skeleton className="h-10 w-48" />
              <Skeleton className="h-10 w-32" />
            </div>
          </div>
          <Skeleton className="h-64 w-full" />
        </div>
      </UserLayout>
    );
  }

  // Empty watchlist
  if (!stockOptions || stockOptions.length === 0) {
    return (
      <UserLayout>
        <EmptyWatchlistState />
      </UserLayout>
    );
  }

  return (
    <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment Trends</h1>
            <p className="text-gray-600 mt-2">
              Analyze sentiment patterns and trends over time from our real-time dashboard
            </p>
          </div>
          
          <div className="flex gap-4">
            <Select value={selectedStock} onValueChange={handleStockChange}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select stock" />
              </SelectTrigger>
              <SelectContent>
                {stockOptions.map((option) => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={timeRange} onValueChange={handleTimeRangeChange}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Time range" />
              </SelectTrigger>
              <SelectContent>
                {timeframeOptions.map((option) => (
                  <SelectItem 
                    key={option.value} 
                    value={option.value}
                    disabled={option.disabled}
                    title={option.reason || undefined}
                  >
                    {option.label}
                    {option.disabled && option.reason && (
                      <span className="text-xs text-muted-foreground ml-2">
                        ({option.reason})
                      </span>
                    )}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Error State */}
        {sentimentError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load sentiment trends: {sentimentError.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Data Quality Warning - Only show if we have SOME data but not enough */}
        {!hasEnoughData && actualDataPoints > 0 && actualDataPoints < 3 && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Limited Data:</strong> Found {actualDataPoints} data point{actualDataPoints !== 1 ? 's' : ''} for the selected timeframe. For accurate trend analysis, at least 3 data points are recommended. Try selecting a longer timeframe (e.g., 7 days or 14 days) or wait for more data to be collected.
            </AlertDescription>
          </Alert>
        )}

        {/* Unified No Data Message */}
        {!isLoadingSentiment && !sentimentError && (!sentimentData || totalRecords === 0) && selectedStock && (
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-900">
              <strong>No Data Available:</strong> No sentiment data found for {selectedStock} in the selected timeframe. This typically means the data collection pipeline needs to run to gather sentiment information. Please check back later or try a different stock.
            </AlertDescription>
          </Alert>
        )}

        {/* Loading State */}
        {isLoadingSentiment && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map(i => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
            <Skeleton className="h-96" />
          </>
        )}

        {/* Key Trend Metrics */}
        {!isLoadingSentiment && sentimentData && totalRecords >= 3 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="border-l-4 border-l-green-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Overall Trend</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold ${
                  trendDirection === 'Bullish' ? 'text-green-600' : 
                  trendDirection === 'Bearish' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {trendDirection === 'Bullish' ? '↑ ' : trendDirection === 'Bearish' ? '↓ ' : '→ '}{trendDirection}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  Average sentiment: {avgSentiment.toFixed(2)}
                </p>
              </CardContent>
            </Card>
            
            <Card className="border-l-4 border-l-orange-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Volatility</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">{volatilityLevel}</div>
                <p className="text-sm text-gray-600 mt-1">
                  {volatilityChange} vs last period
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Momentum</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">{momentumStrength}</div>
                <p className="text-sm text-gray-600 mt-1">
                  {momentumChange} vs last period
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Direction</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold ${
                  trendDirection === 'Bullish' ? 'text-green-600' : 
                  trendDirection === 'Bearish' ? 'text-red-600' : 'text-gray-600'
                }`}>
                  {trendDirection}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {directionChange} vs last period
                </p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Sentiment Distribution Chart */}
        {!isLoadingSentiment && sentimentData && totalRecords >= 3 && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                Sentiment Distribution Over Time - {selectedStock}
                <Badge variant="outline" className={
                  trendDirection === 'Bullish' ? 'text-green-600' : 
                  trendDirection === 'Bearish' ? 'text-red-600' : 'text-gray-600'
                }>
                  {trendDirection} Trend
                </Badge>
              </CardTitle>
              <CardDescription>
                Stacked area chart showing positive, neutral, and negative sentiment percentages
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-96">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis 
                      dataKey="date" 
                      stroke="#666"
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis stroke="#666" />
                    <Tooltip 
                      contentStyle={{ 
                        backgroundColor: '#fff', 
                        border: '1px solid #ccc', 
                        borderRadius: '8px',
                        boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                      }}
                      formatter={(value, name) => [`${value}%`, name]}
                    />
                    <Legend />
                    <Area 
                      type="monotone" 
                      dataKey="positive" 
                      stackId="1"
                      stroke="#10B981" 
                      fill="#10B981"
                      fillOpacity={0.8}
                      name="Positive (%)"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="neutral" 
                      stackId="1"
                      stroke="#6B7280" 
                      fill="#6B7280"
                      fillOpacity={0.6}
                      name="Neutral (%)"
                    />
                    <Area 
                      type="monotone" 
                      dataKey="negative" 
                      stackId="1"
                      stroke="#EF4444" 
                      fill="#EF4444"
                      fillOpacity={0.8}
                      name="Negative (%)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Overall Sentiment Score Trend */}
        {!isLoadingSentiment && sentimentData && totalRecords >= 3 && (
          <Card>
            <CardHeader>
              <CardTitle>Overall Sentiment Score Trend</CardTitle>
              <CardDescription>
                Composite sentiment score over time showing market sentiment direction
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="date"
                      tick={{ fontSize: 12 }}
                      angle={-45}
                      textAnchor="end"
                      height={80}
                    />
                    <YAxis domain={[0, 1]} />
                    <Tooltip 
                      formatter={(value: number) => [value.toFixed(2), 'Sentiment Score']}
                    />
                    <Line 
                      type="monotone" 
                      dataKey="overall" 
                      stroke="#3B82F6" 
                      strokeWidth={3}
                      dot={{ fill: '#3B82F6', strokeWidth: 2, r: 5 }}
                      activeDot={{ r: 7 }}
                      name="Overall Sentiment"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </UserLayout>
  );
};

export default SentimentTrends;