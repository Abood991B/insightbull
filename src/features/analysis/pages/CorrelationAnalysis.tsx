import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useState, useEffect } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { useStocks } from "@/features/analysis/hooks/useStocks";
import { useCorrelationAnalysis } from "@/features/analysis/hooks/useAnalysis";
import { Activity, AlertCircle } from "lucide-react";

const CorrelationAnalysis = () => {
  const { data: stocksList, isLoading: isLoadingList } = useStocks({ active_only: true });
  const [selectedStock, setSelectedStock] = useState('');
  const [timeRange, setTimeRange] = useState<'1d' | '7d' | '14d'>('7d');

  // Set initial stock when list loads
  useEffect(() => {
    if (stocksList && stocksList.stocks.length > 0 && !selectedStock) {
      setSelectedStock(stocksList.stocks[0].symbol);
    }
  }, [stocksList, selectedStock]);

  const { data: correlationData, isLoading, error } = useCorrelationAnalysis(selectedStock, timeRange);

  if (isLoadingList) {
    return (
      <UserLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <Activity className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <p className="text-lg text-gray-600">Loading stocks...</p>
          </div>
        </div>
      </UserLayout>
    );
  }

  if (!stocksList || stocksList.stocks.length === 0) {
    return (
      <UserLayout>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>No stocks available for analysis.</AlertDescription>
        </Alert>
      </UserLayout>
    );
  }

  const getSignificanceColor = (pValue: number) => {
    if (pValue < 0.01) return 'text-green-600';
    if (pValue < 0.05) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getTrendIcon = (trend: string) => {
    return trend === 'increasing' ? '↗' : trend === 'decreasing' ? '↘' : '→';
  };

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Correlation Analysis</h1>
            <p className="text-gray-600 mt-2">Statistical analysis of sentiment-price relationships from our near-real-time dashboard</p>
          </div>
          
          <div className="flex gap-4">
            <Select value={selectedStock} onValueChange={setSelectedStock}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select stock" />
              </SelectTrigger>
              <SelectContent>
                {stocksList.stocks.map((stock) => (
                  <SelectItem key={stock.symbol} value={stock.symbol}>
                    {stock.symbol}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={timeRange} onValueChange={(v) => setTimeRange(v as '1d' | '7d' | '14d')}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1d">1 Day</SelectItem>
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="14d">14 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load correlation data: {error instanceof Error ? error.message : 'Unknown error'}
            </AlertDescription>
          </Alert>
        )}

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Activity className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        )}

        {correlationData && (
          <>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <Card className="border-l-4 border-l-blue-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Pearson Correlation</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-600">
                    {correlationData.correlation_metrics.pearson_correlation.toFixed(2)}
                  </div>
                  <p className="text-sm text-gray-600">
                    {Math.abs(correlationData.correlation_metrics.pearson_correlation) > 0.7 
                      ? 'Strong' 
                      : Math.abs(correlationData.correlation_metrics.pearson_correlation) > 0.4 
                        ? 'Moderate' 
                        : 'Weak'
                    } correlation
                  </p>
                </CardContent>
              </Card>
              
              <Card className="border-l-4 border-l-green-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">R-Squared</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">
                    {correlationData.correlation_metrics.r_squared.toFixed(2)}
                  </div>
                  <p className="text-sm text-gray-600">Variance explained</p>
                </CardContent>
              </Card>
              
              <Card className="border-l-4 border-l-purple-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">P-Value</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className={`text-3xl font-bold ${getSignificanceColor(correlationData.correlation_metrics.p_value)}`}>
                    {correlationData.correlation_metrics.p_value.toFixed(3)}
                  </div>
                  <p className="text-sm text-gray-600">
                    {correlationData.correlation_metrics.p_value < 0.05 ? 'Statistically significant' : 'Not significant'}
                  </p>
                </CardContent>
              </Card>

              <Card className="border-l-4 border-l-orange-500">
                <CardHeader className="pb-3">
                  <CardTitle className="text-lg">Sample Size</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-orange-600">
                    {correlationData.correlation_metrics.sample_size.toLocaleString()}
                  </div>
                  <p className="text-sm text-gray-600">Data points analyzed</p>
                </CardContent>
              </Card>
            </div>

            {/* Main Scatter Plot */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  Correlation Scatter Plot - {selectedStock}
                  <Badge variant="outline" className="text-blue-600">
                    R = {correlationData.correlation_metrics.pearson_correlation.toFixed(2)}
                  </Badge>
                </CardTitle>
                <CardDescription>
                  Relationship between sentiment scores and stock prices
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-96">
                  {correlationData.scatter_data.length > 0 ? (
                    <ResponsiveContainer width="100%" height="100%">
                      <ScatterChart data={correlationData.scatter_data}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis 
                          dataKey="sentiment" 
                          name="Sentiment Score" 
                          domain={[-1, 1]}
                          label={{ value: 'Sentiment Score', position: 'insideBottom', offset: -5 }}
                        />
                        <YAxis 
                          dataKey="price" 
                          name="Stock Price"
                          label={{ value: 'Stock Price ($)', angle: -90, position: 'insideLeft' }}
                        />
                        <Tooltip 
                          cursor={{ strokeDasharray: '3 3' }}
                          formatter={(value: any, name: string) => [
                            name === 'price' ? `$${value.toFixed(2)}` : value.toFixed(3),
                            name === 'price' ? 'Stock Price' : 'Sentiment Score'
                          ]}
                        />
                        <Scatter dataKey="price" fill="#3B82F6">
                          {correlationData.scatter_data.map((entry, index) => (
                            <Cell 
                              key={`cell-${index}`} 
                              fill={entry.sentiment > 0.1 ? '#10B981' : entry.sentiment > -0.1 ? '#F59E0B' : '#EF4444'} 
                            />
                          ))}
                        </Scatter>
                      </ScatterChart>
                    </ResponsiveContainer>
                  ) : (
                    <div className="flex items-center justify-center h-full text-gray-500">
                      No correlation data available
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Trend Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Trend Analysis</CardTitle>
                <CardDescription>Directional trends in sentiment and price</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="p-6 bg-blue-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">Sentiment Trend</h3>
                      <span className="text-2xl">{getTrendIcon(correlationData.sentiment_trend)}</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-600 capitalize">
                      {correlationData.sentiment_trend}
                    </p>
                  </div>
                  <div className="p-6 bg-green-50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900">Price Trend</h3>
                      <span className="text-2xl">{getTrendIcon(correlationData.price_trend)}</span>
                    </div>
                    <p className="text-2xl font-bold text-green-600 capitalize">
                      {correlationData.price_trend}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Detailed Metrics */}
            <Card>
              <CardHeader>
                <CardTitle>Detailed Correlation Metrics</CardTitle>
                <CardDescription>Statistical analysis for {selectedStock}</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Confidence Interval (95%)</p>
                      <p className="text-lg font-semibold">
                        [{correlationData.correlation_metrics.confidence_interval[0].toFixed(3)}, {correlationData.correlation_metrics.confidence_interval[1].toFixed(3)}]
                      </p>
                    </div>
                    <div className="p-4 border rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Data Quality</p>
                      <p className="text-lg font-semibold">
                        {(correlationData.data_quality * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                  <div className="p-4 border rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Analysis Period</p>
                    <p className="text-lg font-semibold">
                      {new Date(correlationData.analysis_period.start).toLocaleDateString()} - {new Date(correlationData.analysis_period.end).toLocaleDateString()}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </UserLayout>
  );
};

export default CorrelationAnalysis;
