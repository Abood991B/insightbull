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
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

// Import services
import { stockService } from "@/api/services/stock.service";
import { analysisService } from "@/api/services/analysis.service";

// Import empty state components
import { EmptyWatchlistState } from "@/shared/components/states";

// Import validation utilities
import {
  getTimeframeOptions,
  getInsufficientDataMessage
} from "@/shared/utils/dataValidation";

// Import timezone utilities
import { formatDate, formatDateTime } from "@/shared/utils/timezone";

const SentimentVsPrice = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const timeframeFromUrl = searchParams.get('timeframe') as '1d' | '7d' | '14d' | null;

  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');
  const [timeRange, setTimeRange] = useState<'1d' | '7d' | '14d'>(timeframeFromUrl || '7d');  // Default to 7d

  // Fetch stock options for dropdown
  const { data: stockOptionsResponse, isLoading: isLoadingStocks } = useQuery({
    queryKey: ['stock-options'],
    queryFn: () => stockService.getStockOptions(true),
    staleTime: 30 * 1000, // 30 seconds - sync with admin changes faster
    refetchOnWindowFocus: true, // Refetch when user returns to tab
    refetchInterval: 60 * 1000, // Poll every minute for admin changes
  });

  // Fetch correlation analysis for metrics
  const {
    data: correlationResponse,
    isLoading: isLoadingCorrelation,
    error: correlationError
  } = useQuery({
    queryKey: ['correlation-analysis', selectedStock, timeRange],
    queryFn: () => analysisService.getCorrelationAnalysis(selectedStock, timeRange),
    enabled: !!selectedStock,
    staleTime: 60 * 1000,
  });

  // Fetch sentiment history for time series charts (with real timestamps)
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

  // Set first stock as default when options load
  useEffect(() => {
    if (!selectedStock && stockOptionsResponse && stockOptionsResponse.length > 0) {
      const firstStock = stockOptionsResponse[0].value;
      setSelectedStock(firstStock);
      setSearchParams({ symbol: firstStock, timeframe: timeRange });
    }
  }, [stockOptionsResponse, selectedStock, timeRange, setSearchParams]);

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
  const stockOptions = stockOptionsResponse || [];
  const correlationData = correlationResponse?.data;
  const sentimentData = sentimentResponse?.data;

  // Prepare chart data from sentiment history (with real timestamps)
  const chartData = sentimentData?.data_points.map(point => {
    // Use real timestamps from backend
    const dateObj = new Date(point.timestamp);

    // Validate date
    if (isNaN(dateObj.getTime())) {
      console.warn('Invalid timestamp:', point.timestamp);
      return null;
    }

    // Use timezone utility for proper user timezone formatting
    const formattedDate = timeRange === '1d'
      ? formatDateTime(point.timestamp, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) // Shows date + time for 1-day view
      : formatDate(point.timestamp); // Shows only date for longer periods

    return {
      date: formattedDate,
      timestamp: dateObj.getTime(),
      sentiment: Number(point.sentiment_score.toFixed(3)),
      price: point.price ? Number(point.price.toFixed(2)) : null,
      volume: point.volume ? Number(point.volume) : null,
      sources: point.source_count,
      // Add validation flags
      hasPrice: point.price !== null && point.price !== undefined,
      hasVolume: point.volume !== null && point.volume !== undefined && point.volume > 0,
    };
  }).filter(Boolean).sort((a, b) => a.timestamp - b.timestamp) || [];

  // Calculate data quality metrics
  const dataQuality = {
    totalPoints: chartData.length,
    pointsWithPrice: chartData.filter(d => d.hasPrice).length,
    pointsWithVolume: chartData.filter(d => d.hasVolume).length,
    priceDataQuality: chartData.length > 0 ? (chartData.filter(d => d.hasPrice).length / chartData.length * 100) : 0,
    volumeDataQuality: chartData.length > 0 ? (chartData.filter(d => d.hasVolume).length / chartData.length * 100) : 0,
  };

  // Data validation - use sentiment data for validation since that's what we're charting
  const actualDataPoints = sentimentData?.total_records || 0;
  const hasEnoughData = actualDataPoints >= 3; // Match backend requirement
  const timeframeOptions = getTimeframeOptions(actualDataPoints);

  // Calculate insights from correlation_metrics
  const correlation = correlationData?.correlation_metrics.pearson_correlation ?? 0;
  const strength = Math.abs(correlation) > 0.7 ? 'Strong' : Math.abs(correlation) > 0.4 ? 'Moderate' : 'Weak';
  const trend = correlation > 0.5 ? 'Positive' : correlation < -0.5 ? 'Negative' : 'Neutral';
  const pValue = correlationData?.correlation_metrics.p_value ?? 1;
  const sampleSize = correlationData?.correlation_metrics.sample_size ?? 0;

  // More accurate significance calculation
  const getSignificanceLevel = (pVal: number, sampleSz: number) => {
    if (sampleSz < 3) return 'Insufficient Data';
    if (pVal < 0.001) return 'Highly Significant (p < 0.001)';
    if (pVal < 0.01) return 'Very Significant (p < 0.01)';
    if (pVal < 0.05) return 'Significant (p < 0.05)';
    if (pVal < 0.1) return 'Marginally Significant (p < 0.1)';
    return 'Not Significant (p ≥ 0.1)';
  };

  const significanceLevel = getSignificanceLevel(pValue, sampleSize);
  const significanceColor = pValue < 0.05 ? 'text-green-600' : pValue < 0.1 ? 'text-yellow-600' : 'text-red-600';

  // Check if either query is loading
  const isLoading = isLoadingCorrelation || isLoadingSentiment;

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

  // Insufficient data for correlation - use the same threshold as backend (3 points minimum)
  const hasInsufficientData = correlationData && correlationData.correlation_metrics.sample_size < 3;

  return (
    <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment vs Price Analysis</h1>
            <p className="text-gray-600 mt-2">
              Compare sentiment trends with stock price movements from our real-time dashboard
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
        {(correlationError || sentimentError) && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load analysis data: {correlationError?.message || sentimentError?.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Data Quality Warning - Only show if we have SOME data but not enough */}
        {!hasEnoughData && actualDataPoints > 0 && actualDataPoints < 3 && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Limited Data:</strong> Found {actualDataPoints} data point{actualDataPoints !== 1 ? 's' : ''} for the selected timeframe. For accurate sentiment vs price analysis, at least 3 data points are recommended. Try selecting a longer timeframe (e.g., 7 days or 14 days) or wait for more data to be collected.
            </AlertDescription>
          </Alert>
        )}

        {/* Loading State */}
        {isLoading && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map(i => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
            <Skeleton className="h-96" />
          </>
        )}

        {/* Unified No Data Message */}
        {!isLoading && !correlationError && !sentimentError && (!sentimentData || actualDataPoints === 0) && selectedStock && (
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-900">
              <strong>No Data Available:</strong> No sentiment data found for {selectedStock} in the selected timeframe. This typically means the data collection pipeline needs to run to gather sentiment and price information. Please check back later or try a different stock.
            </AlertDescription>
          </Alert>
        )}

        {/* Data Quality Summary */}
        {!isLoading && sentimentData && chartData.length > 0 && (
          <Card className="border-l-4 border-l-indigo-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg flex items-center gap-2">
                Data Quality Summary
                <Badge variant={dataQuality.priceDataQuality > 80 ? "default" : dataQuality.priceDataQuality > 50 ? "secondary" : "destructive"}>
                  {dataQuality.priceDataQuality.toFixed(0)}% Complete
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div>
                  <div className="font-semibold text-gray-700">Total Data Points</div>
                  <div className="text-2xl font-bold text-indigo-600">{dataQuality.totalPoints}</div>
                  <div className="text-xs text-gray-500">
                    Expected for {timeRange}: {timeRange === '1d' ? '24+' : timeRange === '7d' ? '168+' : '336+'} hourly
                  </div>
                </div>
                <div>
                  <div className="font-semibold text-gray-700">Price Data</div>
                  <div className="text-2xl font-bold text-green-600">{dataQuality.pointsWithPrice}</div>
                  <div className="text-xs text-gray-500">{dataQuality.priceDataQuality.toFixed(0)}% coverage</div>
                </div>
                <div>
                  <div className="font-semibold text-gray-700">Volume Data</div>
                  <div className="text-2xl font-bold text-orange-600">{dataQuality.pointsWithVolume}</div>
                  <div className="text-xs text-gray-500">{dataQuality.volumeDataQuality.toFixed(0)}% coverage</div>
                </div>
                <div>
                  <div className="font-semibold text-gray-700">Timeframe</div>
                  <div className="text-2xl font-bold text-purple-600">{timeRange.toUpperCase()}</div>
                  <div className="text-xs text-gray-500">
                    {dataQuality.totalPoints < 10 ? 'Low data count' : 'Adequate data'}
                  </div>
                </div>
              </div>

              {/* Data Quality Warnings */}
              {(dataQuality.totalPoints < 10 || dataQuality.priceDataQuality < 50) && (
                <div className="mt-4 space-y-2">
                  {dataQuality.totalPoints < 10 && (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Low Data Count:</strong> Only {dataQuality.totalPoints} data points found for {timeRange} timeframe.
                        This may indicate that the data collection pipeline needs to run more frequently.
                      </AlertDescription>
                    </Alert>
                  )}

                  {dataQuality.priceDataQuality < 50 && (
                    <Alert>
                      <AlertTriangle className="h-4 w-4" />
                      <AlertDescription>
                        <strong>Missing Price Data:</strong> Only {dataQuality.priceDataQuality.toFixed(0)}% of sentiment data points have corresponding price data.
                        This may be due to market hours, weekends, or data collection timing issues.
                      </AlertDescription>
                    </Alert>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Key Metrics */}
        {!isLoading && correlationData && correlationData.correlation_metrics.sample_size >= 3 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Correlation Strength</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">{strength}</div>
                <p className="text-sm text-gray-600 mt-1">
                  {(correlation * 100).toFixed(0)}% correlation coefficient
                </p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-green-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Trend Direction</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">{trend}</div>
                <p className="text-sm text-gray-600 mt-1">Overall sentiment-price relationship</p>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-purple-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Statistical Significance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${significanceColor}`}>
                  {significanceLevel}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  P-value: {pValue.toFixed(4)} | Sample: {sampleSize}
                </p>
                <div className="mt-2 text-xs text-gray-500">
                  {pValue < 0.05
                    ? 'Statistically reliable correlation'
                    : 'Correlation may be due to chance'
                  }
                </div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-orange-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Data Points</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">
                  {correlationData.correlation_metrics.sample_size}
                </div>
                <p className="text-sm text-gray-600 mt-1">Analysis period: {timeRange}</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Chart */}
        {!isLoading && sentimentData && sentimentData.data_points.length >= 3 && (
          <>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  Sentiment vs Stock Price - {selectedStock}
                  <Badge variant="outline" className="text-blue-600">
                    {strength} Correlation
                  </Badge>
                </CardTitle>
                <CardDescription>
                  Dual-axis comparison showing sentiment scores and stock price movements over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96">
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="date"
                        stroke="#666"
                        tick={{ fontSize: 12 }}
                        angle={-45}
                        textAnchor="end"
                        height={80}
                      />
                      <YAxis
                        yAxisId="left"
                        stroke="#8884d8"
                        label={{ value: 'Sentiment Score', angle: -90, position: 'insideLeft' }}
                      />
                      <YAxis
                        yAxisId="right"
                        orientation="right"
                        stroke="#82ca9d"
                        label={{ value: 'Price ($)', angle: 90, position: 'insideRight' }}
                      />
                      <Tooltip
                        contentStyle={{
                          backgroundColor: '#fff',
                          border: '1px solid #ccc',
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
                        formatter={(value: number, name: string) => {
                          if (name === 'Sentiment Score') {
                            return [value?.toFixed(3) || 'N/A', 'Sentiment Score'];
                          }
                          if (name === 'Stock Price ($)') {
                            return [value ? `$${value.toFixed(2)}` : 'No price data', 'Stock Price'];
                          }
                          return [value, name];
                        }}
                        labelFormatter={(label) => `Time: ${label}`}
                      />
                      <Legend />
                      <Line
                        yAxisId="left"
                        type="monotone"
                        dataKey="sentiment"
                        stroke="#8884d8"
                        strokeWidth={3}
                        name="Sentiment Score"
                        dot={{ fill: '#8884d8', strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6 }}
                        connectNulls
                      />
                      <Line
                        yAxisId="right"
                        type="monotone"
                        dataKey="price"
                        stroke="#82ca9d"
                        strokeWidth={3}
                        name="Stock Price ($)"
                        dot={{ fill: '#82ca9d', strokeWidth: 2, r: 4 }}
                        activeDot={{ r: 6 }}
                        connectNulls
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Trading Volume Analysis */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  Trading Volume Analysis - {selectedStock}
                  <Badge variant="outline" className="text-orange-600">
                    Market Activity
                  </Badge>
                </CardTitle>
                <CardDescription>
                  Analyze how trading volume correlates with sentiment changes | Volume indicates market conviction behind sentiment
                </CardDescription>
              </CardHeader>
              <CardContent>
                {chartData.filter(d => d.hasVolume).length > 0 ? (
                  <>
                    <div className="h-80">
                      <ResponsiveContainer width="100%" height="100%">
                        <LineChart data={chartData.filter(d => d.hasVolume)}>
                          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                          <XAxis
                            dataKey="date"
                            tick={{ fontSize: 12 }}
                            angle={-45}
                            textAnchor="end"
                            height={80}
                          />
                          <YAxis
                            yAxisId="volume"
                            orientation="left"
                            stroke="#f59e0b"
                            label={{ value: 'Trading Volume', angle: -90, position: 'insideLeft' }}
                            tickFormatter={(value) => {
                              if (value >= 1000000) return `${(value / 1000000).toFixed(1)}M`;
                              if (value >= 1000) return `${(value / 1000).toFixed(1)}K`;
                              return value.toString();
                            }}
                          />
                          <YAxis
                            yAxisId="sentiment"
                            orientation="right"
                            stroke="#8884d8"
                            label={{ value: 'Sentiment Score', angle: 90, position: 'insideRight' }}
                            domain={[-1, 1]}
                          />
                          <Tooltip
                            contentStyle={{
                              backgroundColor: '#fff',
                              border: '1px solid #ccc',
                              borderRadius: '8px',
                              boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                            }}
                            formatter={(value: number, name: string) => {
                              if (name === 'Trading Volume') {
                                return [value?.toLocaleString() || 'N/A', 'Trading Volume'];
                              }
                              if (name === 'Sentiment Score') {
                                return [value?.toFixed(3) || 'N/A', 'Sentiment Score'];
                              }
                              return [value, name];
                            }}
                          />
                          <Legend />
                          <Line
                            yAxisId="volume"
                            type="monotone"
                            dataKey="volume"
                            stroke="#f59e0b"
                            strokeWidth={2}
                            dot={{ fill: '#f59e0b', strokeWidth: 2, r: 3 }}
                            activeDot={{ r: 5 }}
                            name="Trading Volume"
                            connectNulls={false}
                          />
                          <Line
                            yAxisId="sentiment"
                            type="monotone"
                            dataKey="sentiment"
                            stroke="#8884d8"
                            strokeWidth={2}
                            dot={{ fill: '#8884d8', strokeWidth: 2, r: 3 }}
                            activeDot={{ r: 5 }}
                            name="Sentiment Score"
                            connectNulls={false}
                          />
                        </LineChart>
                      </ResponsiveContainer>
                    </div>

                    {/* Enhanced Volume Analysis Guide */}
                    <div className="mt-6 space-y-4">
                      <h4 className="font-semibold text-gray-800 text-lg">How to Read This Chart</h4>

                      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        {/* Trading Scenarios */}
                        <div className="space-y-3">
                          <h5 className="font-medium text-gray-700">Trading Volume Scenarios</h5>
                          <div className="space-y-2">
                            <div className="flex items-start gap-3 p-3 bg-green-50 rounded-lg border-l-4 border-green-400">
                              <div className="w-3 h-3 bg-green-500 rounded-full mt-1 flex-shrink-0"></div>
                              <div>
                                <div className="font-medium text-green-800">High Volume + Positive Sentiment</div>
                                <div className="text-sm text-green-700">
                                  <strong>Strong Buy Signal:</strong> Many investors are actively buying, indicating strong confidence in the stock's upward movement.
                                </div>
                              </div>
                            </div>

                            <div className="flex items-start gap-3 p-3 bg-red-50 rounded-lg border-l-4 border-red-400">
                              <div className="w-3 h-3 bg-red-500 rounded-full mt-1 flex-shrink-0"></div>
                              <div>
                                <div className="font-medium text-red-800">High Volume + Negative Sentiment</div>
                                <div className="text-sm text-red-700">
                                  <strong>Strong Sell Signal:</strong> Heavy selling pressure with widespread negative sentiment - potential significant decline.
                                </div>
                              </div>
                            </div>

                            <div className="flex items-start gap-3 p-3 bg-yellow-50 rounded-lg border-l-4 border-yellow-400">
                              <div className="w-3 h-3 bg-yellow-500 rounded-full mt-1 flex-shrink-0"></div>
                              <div>
                                <div className="font-medium text-yellow-800">Low Volume + Any Sentiment</div>
                                <div className="text-sm text-yellow-700">
                                  <strong>Weak Signal:</strong> Few traders are active - sentiment may not translate to significant price movement.
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Investment Insights */}
                        <div className="space-y-3">
                          <h5 className="font-medium text-gray-700">Investment Insights</h5>
                          <div className="space-y-2">
                            <div className="p-3 bg-blue-50 rounded-lg">
                              <div className="font-medium text-blue-800 mb-1">Volume Confirms Trends</div>
                              <div className="text-sm text-blue-700">
                                When sentiment and volume move in the same direction, it suggests the trend is more likely to continue.
                              </div>
                            </div>

                            <div className="p-3 bg-purple-50 rounded-lg">
                              <div className="font-medium text-purple-800 mb-1">Volume Divergence</div>
                              <div className="text-sm text-purple-700">
                                If sentiment is positive but volume is low, the price increase may not be sustainable.
                              </div>
                            </div>

                            <div className="p-3 bg-indigo-50 rounded-lg">
                              <div className="font-medium text-indigo-800 mb-1">Entry/Exit Points</div>
                              <div className="text-sm text-indigo-700">
                                Look for high volume spikes with sentiment changes as potential entry or exit opportunities.
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="text-gray-500 mb-2">No Volume Data Available</div>
                    <div className="text-sm text-gray-600">
                      Trading volume data is not available for the selected timeframe. This may be due to:
                    </div>
                    <ul className="text-sm text-gray-600 mt-2 space-y-1">
                      <li>Market hours (volume only recorded during trading hours)</li>
                      <li>Data collection limitations</li>
                      <li>Weekend or holiday periods</li>
                    </ul>
                  </div>
                )}
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </UserLayout>
  );
};

export default SentimentVsPrice;
