
import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, AreaChart, Area } from 'recharts';

const trendData = [
  { date: '2024-01-01', positive: 45, neutral: 35, negative: 20 },
  { date: '2024-01-02', positive: 50, neutral: 30, negative: 20 },
  { date: '2024-01-03', positive: 40, neutral: 40, negative: 20 },
  { date: '2024-01-04', positive: 55, neutral: 25, negative: 20 },
  { date: '2024-01-05', positive: 35, neutral: 45, negative: 20 },
];

const stocks = ['All Stocks', 'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN'];

const timeRanges = [
  { value: '1h', label: '1 Hour' },
  { value: '6h', label: '6 Hours' },
  { value: '12h', label: '12 Hours' },
  { value: '1d', label: '1 Day' },
  { value: '3d', label: '3 Days' },
  { value: '7d', label: '7 Days' },
  { value: '14d', label: '14 Days' },
  { value: '30d', label: '30 Days' },
  { value: '90d', label: '90 Days' }
];

const SentimentTrends = () => {
  const [selectedStock, setSelectedStock] = useState('All Stocks');
  const [timeRange, setTimeRange] = useState('7d');
  const [trendDirection, setTrendDirection] = useState('Bullish');
  const [volatility, setVolatility] = useState('Medium');

  // Update trend metrics based on time range
  useEffect(() => {
    // Simulate different trends for different time ranges
    const trendMap: Record<string, { direction: string; volatility: string }> = {
      '1h': { direction: 'Neutral', volatility: 'High' },
      '6h': { direction: 'Bullish', volatility: 'High' },
      '12h': { direction: 'Bullish', volatility: 'Medium' },
      '1d': { direction: 'Bullish', volatility: 'Medium' },
      '3d': { direction: 'Bullish', volatility: 'Medium' },
      '7d': { direction: 'Bullish', volatility: 'Medium' },
      '14d': { direction: 'Bearish', volatility: 'Low' },
      '30d': { direction: 'Neutral', volatility: 'Low' },
      '90d': { direction: 'Bullish', volatility: 'Low' }
    };
    
    const trend = trendMap[timeRange] || { direction: 'Bullish', volatility: 'Medium' };
    setTrendDirection(trend.direction);
    setVolatility(trend.volatility);
  }, [timeRange, selectedStock]);

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment Trends</h1>
            <p className="text-gray-600 mt-2">Analyze sentiment patterns and trends over {timeRanges.find(r => r.value === timeRange)?.label.toLowerCase()}</p>
          </div>
          
          <div className="flex gap-4">
            <Select value={selectedStock} onValueChange={setSelectedStock}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Select stock" />
              </SelectTrigger>
              <SelectContent>
                {stocks.map((stock) => (
                  <SelectItem key={stock} value={stock}>
                    {stock}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Time range" />
              </SelectTrigger>
              <SelectContent>
                {timeRanges.map(range => (
                  <SelectItem key={range.value} value={range.value}>
                    {range.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution Over Time - {selectedStock}</CardTitle>
            <CardDescription>
              Stacked area chart showing positive, neutral, and negative sentiment percentages over {timeRanges.find(r => r.value === timeRange)?.label.toLowerCase()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Legend />
                  <Area 
                    type="monotone" 
                    dataKey="positive" 
                    stackId="1"
                    stroke="#10B981" 
                    fill="#10B981"
                    name="Positive (%)"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="neutral" 
                    stackId="1"
                    stroke="#6B7280" 
                    fill="#6B7280"
                    name="Neutral (%)"
                  />
                  <Area 
                    type="monotone" 
                    dataKey="negative" 
                    stackId="1"
                    stroke="#EF4444" 
                    fill="#EF4444"
                    name="Negative (%)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Trend Direction</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-3xl font-bold ${
                trendDirection === 'Bullish' ? 'text-green-600' : 
                trendDirection === 'Bearish' ? 'text-red-600' : 
                'text-gray-600'
              }`}>
                {trendDirection === 'Bullish' ? '↑' : trendDirection === 'Bearish' ? '↓' : '→'} {trendDirection}
              </div>
              <p className="text-sm text-gray-600">
                {trendDirection === 'Bullish' ? 'Overall sentiment improving' : 
                 trendDirection === 'Bearish' ? 'Overall sentiment declining' : 
                 'Sentiment remains stable'}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Volatility</CardTitle>
            </CardHeader>
            <CardContent>
              <div className={`text-3xl font-bold ${
                volatility === 'High' ? 'text-red-600' : 
                volatility === 'Medium' ? 'text-orange-600' : 
                'text-green-600'
              }`}>
                {volatility}
              </div>
              <p className="text-sm text-gray-600">
                {volatility === 'High' ? 'High sentiment swings' : 
                 volatility === 'Medium' ? 'Moderate sentiment swings' : 
                 'Low sentiment swings'}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Momentum</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">
                {trendDirection === 'Bullish' ? 'Strong' : trendDirection === 'Bearish' ? 'Weak' : 'Neutral'}
              </div>
              <p className="text-sm text-gray-600">
                {trendDirection === 'Bullish' ? 'Positive momentum building' : 
                 trendDirection === 'Bearish' ? 'Negative momentum building' : 
                 'Momentum is balanced'}
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </UserLayout>
  );
};

export default SentimentTrends;
