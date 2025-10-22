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
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

// Import services
import { stockService } from "@/api/services/stock.service";
import { analysisService } from "@/api/services/analysis.service";

// Import validation utilities
import { 
  getTimeframeOptions, 
  getInsufficientDataMessage
} from "@/shared/utils/dataValidation";

// Import empty state components
import { EmptyWatchlistState } from "@/shared/components/states";

const CorrelationAnalysis = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const timeframeFromUrl = searchParams.get('timeframe') as '1d' | '7d' | '14d' | null;
  
  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');
  const [timeRange, setTimeRange] = useState<'1d' | '7d' | '14d'>(timeframeFromUrl || '7d');  // Default to 7d

  // Fetch stock options for dropdown
  const { data: stockOptions, isLoading: isLoadingStocks } = useQuery({
    queryKey: ['stock-options'],
    queryFn: () => stockService.getStockOptions(true),
    staleTime: 5 * 60 * 1000,
  });

  // Fetch correlation analysis
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
  const correlationData = correlationResponse?.data;

  // Prepare scatter plot data - scatter_data doesn't include timestamps, just sentiment/price pairs
  const scatterData = correlationData?.scatter_data || [];

  // Data validation - use actual sample size from backend
  const actualDataPoints = correlationData?.correlation_metrics.sample_size || 0;
  const hasEnoughData = actualDataPoints >= 3; // Match backend requirement
  const timeframeOptions = getTimeframeOptions(actualDataPoints);

  // Calculate metrics with proper calculations
  const pearsonCorrelation = correlationData?.correlation_metrics.pearson_correlation ?? 0;
  const rSquared = correlationData?.correlation_metrics.r_squared ?? (pearsonCorrelation * pearsonCorrelation);
  const pValue = correlationData?.correlation_metrics.p_value ?? 1;
  const sampleSize = correlationData?.correlation_metrics.sample_size ?? 0;
  
  const correlationStrength = Math.abs(pearsonCorrelation) > 0.7 ? 'Strong' : 
                              Math.abs(pearsonCorrelation) > 0.4 ? 'Moderate' : 'Weak';
  const correlationDirection = pearsonCorrelation > 0 ? 'Positive' : pearsonCorrelation < 0 ? 'Negative' : 'None';
  
  // More detailed significance calculation
  const getSignificanceLevel = (pVal: number, sampleSz: number) => {
    if (sampleSz < 3) return 'Insufficient Data';
    if (pVal < 0.001) return 'p < 0.001';
    if (pVal < 0.01) return 'p < 0.01';
    if (pVal < 0.05) return 'p < 0.05';
    if (pVal < 0.1) return 'p < 0.1';
    return 'Not Significant';
  };
  
  const significanceLevel = getSignificanceLevel(pValue, sampleSize);
  const significanceColor = pValue < 0.05 ? 'text-green-600' : pValue < 0.1 ? 'text-yellow-600' : 'text-red-600';

  // Check for insufficient data - use backend threshold of 3 points
  const hasInsufficientData = correlationData && sampleSize < 3;

  // Helper function to get color for scatter points
  const getScatterPointColor = (sentiment: number) => {
    if (sentiment > 0.3) return '#10B981'; // green
    if (sentiment > -0.3) return '#F59E0B'; // yellow
    return '#EF4444'; // red
  };

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
            <h1 className="text-3xl font-bold text-gray-900">Correlation Analysis</h1>
            <p className="text-gray-600 mt-2">
              Statistical analysis of sentiment-price relationships from our real-time dashboard
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
        {correlationError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load correlation analysis: {correlationError.message}
            </AlertDescription>
          </Alert>
        )}

        {/* Data Quality Warning - Only show if we have SOME data but not enough */}
        {!hasEnoughData && actualDataPoints > 0 && actualDataPoints < 3 && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <strong>Limited Data:</strong> Found {actualDataPoints} data point{actualDataPoints !== 1 ? 's' : ''} for the selected timeframe, but correlation analysis requires at least 3 points for statistical validity. Try selecting a longer timeframe (e.g., 7 days or 14 days) or wait for more data to be collected.
            </AlertDescription>
          </Alert>
        )}

        {/* Unified No Data Message */}
        {!isLoadingCorrelation && !correlationError && (!correlationData || sampleSize === 0) && selectedStock && (
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-900">
              <strong>No Data Available:</strong> No correlation data found for {selectedStock} in the selected timeframe. This typically means the data collection pipeline needs to run to gather sentiment and price information. Please check back later or try a different stock.
            </AlertDescription>
          </Alert>
        )}

        {/* Loading State */}
        {isLoadingCorrelation && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              {[1, 2, 3, 4].map(i => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
            <Skeleton className="h-96" />
          </>
        )}

        {/* Key Metrics */}
        {!isLoadingCorrelation && correlationData && sampleSize >= 3 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Card className="border-l-4 border-l-blue-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Pearson Correlation</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-blue-600">
                  {pearsonCorrelation.toFixed(2)}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  {correlationStrength} {correlationDirection.toLowerCase()} correlation
                </p>
              </CardContent>
            </Card>
            
            <Card className="border-l-4 border-l-green-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">R-Squared</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-green-600">
                  {rSquared.toFixed(2)}
                </div>
                <p className="text-sm text-gray-600 mt-1">Variance explained</p>
              </CardContent>
            </Card>
            
            <Card className="border-l-4 border-l-purple-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Significance</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-2xl font-bold ${significanceColor}`}>
                  {significanceLevel}
                </div>
                <p className="text-sm text-gray-600 mt-1">
                  P-value: {pValue.toFixed(4)}
                </p>
                <div className="mt-2 text-xs text-gray-500">
                  {pValue < 0.05 
                    ? 'Statistically reliable' 
                    : 'May be due to chance'
                  }
                </div>
              </CardContent>
            </Card>

            <Card className="border-l-4 border-l-orange-500">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">Sample Size</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-orange-600">
                  {sampleSize.toLocaleString()}
                </div>
                <p className="text-sm text-gray-600 mt-1">Data points analyzed</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Main Charts - Two Column Layout */}
        {!isLoadingCorrelation && correlationData && sampleSize >= 3 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Scatter Plot */}
            <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                Correlation Scatter Plot - {selectedStock}
                <Badge variant="outline" className="text-blue-600">
                  R = {pearsonCorrelation.toFixed(2)}
                </Badge>
              </CardTitle>
              <CardDescription>
                Relationship between sentiment scores and stock prices | {new Date(correlationData.analysis_period.start).toLocaleDateString()} to {new Date(correlationData.analysis_period.end).toLocaleDateString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="sentiment" 
                      name="Sentiment Score"
                      type="number"
                      domain={['dataMin - 0.1', 'dataMax + 0.1']}
                      label={{ value: 'Sentiment Score', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis 
                      dataKey="price" 
                      name="Stock Price"
                      type="number"
                      label={{ value: 'Stock Price ($)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      cursor={{ strokeDasharray: '3 3' }}
                      formatter={(value: number, name: string) => [
                        name === 'price' ? `$${value.toFixed(2)}` : value.toFixed(3),
                        name === 'price' ? 'Stock Price' : 'Sentiment Score'
                      ]}
                    />
                    <Scatter data={scatterData} fill="#3B82F6">
                      {scatterData.map((entry: any, index: number) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={getScatterPointColor(entry.sentiment)} 
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-4 flex gap-6 justify-center text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                  <span>Positive Sentiment (&gt; 0.3)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <span>Neutral Sentiment (-0.3 to 0.3)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <span>Negative Sentiment (&lt; -0.3)</span>
                </div>
              </div>
            </CardContent>
            </Card>

            {/* Correlation Strength Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Correlation Strength Analysis</CardTitle>
                <CardDescription>
                  Statistical breakdown and interpretation
                </CardDescription>
              </CardHeader>
              <CardContent>
                {correlationData ? (
                  <div className="space-y-4">
                    {/* Correlation Strength Meter */}
                    <div className="space-y-3">
                      <div className="flex justify-between items-center">
                        <span className="text-sm font-medium text-gray-700">Correlation Strength</span>
                        <span className="text-sm text-gray-500">{Math.abs(pearsonCorrelation).toFixed(3)}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-3">
                        <div 
                          className={`h-3 rounded-full transition-all duration-500 ${
                            Math.abs(pearsonCorrelation) > 0.7 ? 'bg-green-500' : 
                            Math.abs(pearsonCorrelation) > 0.4 ? 'bg-yellow-500' : 'bg-red-500'
                          }`}
                          style={{ width: `${Math.abs(pearsonCorrelation) * 100}%` }}
                        />
                      </div>
                      <div className="flex justify-between text-xs text-gray-500">
                        <span>Weak (0.0)</span>
                        <span>Moderate (0.5)</span>
                        <span>Strong (1.0)</span>
                      </div>
                    </div>

                    {/* Statistical Breakdown */}
                    <div className="grid grid-cols-2 gap-3">
                      <div className="bg-blue-50 p-3 rounded-lg">
                        <div className="text-xs font-medium text-blue-800">Explained Variance</div>
                        <div className="text-lg font-bold text-blue-600">{(rSquared * 100).toFixed(1)}%</div>
                        <div className="text-xs text-blue-600">R² = {rSquared.toFixed(3)}</div>
                      </div>
                      
                      <div className="bg-purple-50 p-3 rounded-lg">
                        <div className="text-xs font-medium text-purple-800">Significance</div>
                        <div className="text-lg font-bold text-purple-600">
                          {pValue < 0.001 ? 'p < 0.001' : 
                           pValue < 0.01 ? 'p < 0.01' : 
                           pValue < 0.05 ? 'p < 0.05' : 'Not Sig.'}
                        </div>
                        <div className="text-xs text-purple-600">P-value: {pValue.toFixed(4)}</div>
                      </div>
                    </div>

                    {/* Interpretation */}
                    <div className="bg-gray-50 p-3 rounded-lg">
                      <div className="text-xs font-medium text-gray-800 mb-1">Interpretation</div>
                      <div className="text-xs text-gray-600">
                        {Math.abs(pearsonCorrelation) > 0.7 ? 
                          'Strong correlation - sentiment is a reliable predictor of price movements.' :
                          Math.abs(pearsonCorrelation) > 0.4 ?
                          'Moderate correlation - sentiment has some predictive value.' :
                          'Weak correlation - sentiment may not strongly predict price movements.'
                        }
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="flex items-center justify-center h-32 text-gray-500">
                    No correlation data available
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        )}

        {/* Correlation Summary Table */}
        {!isLoadingCorrelation && correlationData && sampleSize >= 3 && (
          <Card>
            <CardHeader>
              <CardTitle>Correlation Summary - {selectedStock}</CardTitle>
              <CardDescription>Complete statistical breakdown for {timeRange} timeframe analysis</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b-2 border-gray-200">
                      <th className="text-left py-4 px-4 font-semibold">Metric</th>
                      <th className="text-left py-4 px-4 font-semibold">Value</th>
                      <th className="text-left py-4 px-4 font-semibold">Interpretation</th>
                      <th className="text-left py-4 px-4 font-semibold">Quality</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-semibold text-blue-600">Pearson Correlation</td>
                      <td className="py-4 px-4 font-mono text-lg">{pearsonCorrelation.toFixed(4)}</td>
                      <td className="py-4 px-4">
                        <span className={pearsonCorrelation > 0 ? 'text-green-600' : 'text-red-600'}>
                          {correlationStrength} {correlationDirection} relationship
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className={
                          Math.abs(pearsonCorrelation) > 0.7 ? 'text-green-600' : 
                          Math.abs(pearsonCorrelation) > 0.4 ? 'text-yellow-600' : 'text-red-600'
                        }>
                          {Math.abs(pearsonCorrelation) > 0.7 ? 'Excellent' : 
                           Math.abs(pearsonCorrelation) > 0.4 ? 'Good' : 'Weak'}
                        </Badge>
                      </td>
                    </tr>
                    
                    <tr className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-semibold text-green-600">R-Squared</td>
                      <td className="py-4 px-4 font-mono text-lg">{rSquared.toFixed(4)}</td>
                      <td className="py-4 px-4">
                        {(rSquared * 100).toFixed(1)}% of price variance explained by sentiment
                      </td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className={
                          rSquared > 0.5 ? 'text-green-600' : 
                          rSquared > 0.25 ? 'text-yellow-600' : 'text-red-600'
                        }>
                          {rSquared > 0.5 ? 'High' : rSquared > 0.25 ? 'Moderate' : 'Low'}
                        </Badge>
                      </td>
                    </tr>
                    
                    <tr className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-semibold text-purple-600">P-Value</td>
                      <td className="py-4 px-4 font-mono text-lg">{pValue.toFixed(6)}</td>
                      <td className="py-4 px-4">
                        {pValue < 0.05 ? 'Statistically significant result' : 'Result may be due to chance'}
                      </td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className={significanceColor}>
                          {pValue < 0.001 ? 'Very High' : 
                           pValue < 0.01 ? 'High' : 
                           pValue < 0.05 ? 'Significant' : 
                           pValue < 0.1 ? 'Marginal' : 'Not Significant'}
                        </Badge>
                      </td>
                    </tr>
                    
                    <tr className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-semibold text-orange-600">Sample Size</td>
                      <td className="py-4 px-4 font-mono text-lg">{sampleSize}</td>
                      <td className="py-4 px-4">
                        {sampleSize >= 30 ? 'Large sample - reliable results' : 
                         sampleSize >= 10 ? 'Adequate sample size' : 'Small sample - interpret cautiously'}
                      </td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className={
                          sampleSize >= 30 ? 'text-green-600' : 
                          sampleSize >= 10 ? 'text-yellow-600' : 'text-red-600'
                        }>
                          {sampleSize >= 30 ? 'Excellent' : sampleSize >= 10 ? 'Good' : 'Limited'}
                        </Badge>
                      </td>
                    </tr>
                    
                    <tr className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-semibold text-indigo-600">Confidence Interval</td>
                      <td className="py-4 px-4 font-mono text-lg">
                        [{correlationData.correlation_metrics.confidence_interval[0].toFixed(3)}, {correlationData.correlation_metrics.confidence_interval[1].toFixed(3)}]
                      </td>
                      <td className="py-4 px-4">
                        95% confidence range for true correlation
                      </td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className="text-indigo-600">
                          95% CI
                        </Badge>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Analysis Summary */}
        {!isLoadingCorrelation && correlationData && sampleSize >= 3 && (
          <Card>
            <CardHeader>
              <CardTitle>Analysis Summary</CardTitle>
              <CardDescription>
                Analysis period: {new Date(correlationData.analysis_period.start).toLocaleDateString()} to {new Date(correlationData.analysis_period.end).toLocaleDateString()} | 
                Data quality: {(correlationData.data_quality * 100).toFixed(0)}%
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
                    <div>
                      <p className="font-semibold">Sentiment Trend</p>
                      <p className="text-gray-600">{correlationData.sentiment_trend}</p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-green-500 mt-2"></div>
                    <div>
                      <p className="font-semibold">Price Trend</p>
                      <p className="text-gray-600">{correlationData.price_trend}</p>
                    </div>
                  </div>
                </div>
                <div className="space-y-3">
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-purple-500 mt-2"></div>
                    <div>
                      <p className="font-semibold">Data Quality</p>
                      <p className="text-gray-600">
                        {(correlationData.data_quality * 100).toFixed(0)}% - 
                        {correlationData.data_quality > 0.8 ? ' Excellent' : 
                         correlationData.data_quality > 0.6 ? ' Good' : 
                         correlationData.data_quality > 0.4 ? ' Fair' : ' Poor'}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 rounded-full bg-orange-500 mt-2"></div>
                    <div>
                      <p className="font-semibold">Confidence Interval (95%)</p>
                      <p className="text-gray-600">
                        [{correlationData.correlation_metrics.confidence_interval[0].toFixed(2)}, {correlationData.correlation_metrics.confidence_interval[1].toFixed(2)}]
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </UserLayout>
  );
};

export default CorrelationAnalysis;
