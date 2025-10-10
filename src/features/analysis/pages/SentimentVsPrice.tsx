import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';
import { useStocks } from "@/features/analysis/hooks/useStocks";
import { useSentimentHistory } from "@/features/analysis/hooks/useAnalysis";
import { Activity, AlertCircle } from "lucide-react";
import { format } from "date-fns";

const SentimentVsPrice = () => {
  const { data: stocksList, isLoading: isLoadingList } = useStocks({ active_only: true });
  const [selectedStock, setSelectedStock] = useState('');
  const [timeRange, setTimeRange] = useState<'1d' | '7d' | '14d'>('7d');

  // Set initial stock when list loads
  useEffect(() => {
    if (stocksList && stocksList.stocks.length > 0 && !selectedStock) {
      setSelectedStock(stocksList.stocks[0].symbol);
    }
  }, [stocksList, selectedStock]);

  const { data: sentimentHistory, isLoading, error } = useSentimentHistory(selectedStock, timeRange);

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

  const correlation = sentimentHistory?.price_correlation || 0;
  const trend = correlation > 0.5 ? 'Positive' : correlation < -0.5 ? 'Negative' : 'Neutral';
  const strength = Math.abs(correlation) > 0.7 ? 'Strong' : Math.abs(correlation) > 0.4 ? 'Moderate' : 'Weak';

  // Format data for charts
  const chartData = sentimentHistory?.data_points.map(point => ({
    date: format(new Date(point.timestamp), 'MMM dd HH:mm'),
    sentiment: ((point.sentiment_score + 1) / 2), // Convert from -1,1 to 0,1
    price: point.price,
    volume: point.volume,
  })) || [];

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment vs Price Analysis</h1>
            <p className="text-gray-600 mt-2">Compare sentiment trends with stock price movements from our near-real-time dashboard</p>
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
              Failed to load sentiment data: {error instanceof Error ? error.message : 'Unknown error'}
            </AlertDescription>
          </Alert>
        )}

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Correlation Strength</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{strength}</div>
              <p className="text-sm text-gray-600 mt-1">
                {sentimentHistory ? `${(Math.abs(correlation) * 100).toFixed(0)}% correlation coefficient` : 'Loading...'}
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
              <CardTitle className="text-lg">Data Coverage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">
                {sentimentHistory ? `${(sentimentHistory.data_coverage * 100).toFixed(0)}%` : 'N/A'}
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {sentimentHistory ? `${sentimentHistory.total_records} data points` : 'Loading...'}
              </p>
            </CardContent>
          </Card>
        </div>

        {isLoading && (
          <div className="flex items-center justify-center py-12">
            <Activity className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        )}

        {sentimentHistory && chartData.length > 0 && (
          <>
            {/* Main Chart */}
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
                        interval="preserveStartEnd"
                      />
                      <YAxis yAxisId="left" stroke="#8884d8" domain={[0, 1]} />
                      <YAxis yAxisId="right" orientation="right" stroke="#82ca9d" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: '#fff', 
                          border: '1px solid #ccc', 
                          borderRadius: '8px',
                          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)'
                        }}
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
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Secondary Analysis */}
            <Card>
              <CardHeader>
                <CardTitle>Volume vs Sentiment Analysis</CardTitle>
                <CardDescription>
                  Trading volume correlation with sentiment changes
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 12 }}
                        interval="preserveStartEnd"
                      />
                      <YAxis />
                      <Tooltip />
                      <Area 
                        type="monotone" 
                        dataKey="volume" 
                        stroke="#f59e0b" 
                        fill="#fbbf24" 
                        fillOpacity={0.6}
                        name="Trading Volume"
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </>
        )}

        {sentimentHistory && chartData.length === 0 && (
          <Card>
            <CardContent className="py-12 text-center text-gray-500">
              No data available for the selected time range
            </CardContent>
          </Card>
        )}
      </div>
    </UserLayout>
  );
};

export default SentimentVsPrice;
