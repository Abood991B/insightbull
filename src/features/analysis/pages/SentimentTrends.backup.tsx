
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';

const trendData = [
  { date: '2024-01-01', positive: 45, neutral: 35, negative: 20, overall: 0.6 },
  { date: '2024-01-02', positive: 50, neutral: 30, negative: 20, overall: 0.7 },
  { date: '2024-01-03', positive: 40, neutral: 40, negative: 20, overall: 0.5 },
  { date: '2024-01-04', positive: 55, neutral: 25, negative: 20, overall: 0.8 },
  { date: '2024-01-05', positive: 35, neutral: 45, negative: 20, overall: 0.4 },
  { date: '2024-01-06', positive: 60, neutral: 25, negative: 15, overall: 0.9 },
  { date: '2024-01-07', positive: 48, neutral: 32, negative: 20, overall: 0.6 },
];

const trendMetrics = [
  { metric: 'Volatility', value: 'Medium', change: '+5%', color: 'text-orange-600' },
  { metric: 'Momentum', value: 'Strong', change: '+12%', color: 'text-blue-600' },
  { metric: 'Direction', value: 'Bullish', change: '+8%', color: 'text-green-600' },
];

const stocks = ['All Stocks', 'MSFT', 'NVDA', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'IBM', 'CSCO', 'CRM', 'INTU', 'NOW', 'AMD', 'ACN', 'TXN', 'QCOM', 'ADBE', 'AMAT', 'PANW', 'MU', 'CRWD'];

const SentimentTrends = () => {
  const [selectedStock, setSelectedStock] = useState('All Stocks');
  const [timeRange, setTimeRange] = useState('7d');

  const avgSentiment = trendData.reduce((sum, item) => sum + item.overall, 0) / trendData.length;
  const trendDirection = avgSentiment > 0.6 ? 'Bullish' : avgSentiment < 0.4 ? 'Bearish' : 'Neutral';

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment Trends</h1>
            <p className="text-gray-600 mt-2">Analyze sentiment patterns and trends over time from our near-real-time dashboard</p>
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
                <SelectItem value="1d">1 Day</SelectItem>
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="14d">14 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Key Trend Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Overall Trend</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">↑ {trendDirection}</div>
              <p className="text-sm text-gray-600">Average sentiment: {avgSentiment.toFixed(2)}</p>
            </CardContent>
          </Card>
          
          {trendMetrics.map((metric) => (
            <Card key={metric.metric} className="border-l-4 border-l-gray-300">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg">{metric.metric}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className={`text-3xl font-bold ${metric.color}`}>{metric.value}</div>
                <p className="text-sm text-gray-600">{metric.change} vs last period</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Trend Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              Sentiment Distribution Over Time - {selectedStock}
              <Badge variant="outline" className="text-green-600">
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
                <AreaChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" stroke="#666" />
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

        {/* Overall Sentiment Trend Line */}
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
                <LineChart data={trendData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
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
      </div>
    </UserLayout>
  );
};

export default SentimentTrends;
