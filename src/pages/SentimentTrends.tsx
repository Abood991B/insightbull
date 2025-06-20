
import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const trendData = [
  { date: '2024-01-01', positive: 45, neutral: 35, negative: 20 },
  { date: '2024-01-02', positive: 50, neutral: 30, negative: 20 },
  { date: '2024-01-03', positive: 40, neutral: 40, negative: 20 },
  { date: '2024-01-04', positive: 55, neutral: 25, negative: 20 },
  { date: '2024-01-05', positive: 35, neutral: 45, negative: 20 },
];

const stocks = ['All Stocks', 'MSFT', 'NVDA', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'IBM', 'CSCO', 'CRM', 'INTU', 'NOW', 'AMD', 'ACN', 'TXN', 'QCOM', 'ADBE', 'AMAT', 'PANW', 'MU', 'CRWD'];

const SentimentTrends = () => {
  const [selectedStock, setSelectedStock] = useState('All Stocks');
  const [timeRange, setTimeRange] = useState('7d');

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment Trends</h1>
            <p className="text-gray-600 mt-2">Analyze sentiment patterns and trends over time</p>
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

        <Card>
          <CardHeader>
            <CardTitle>Sentiment Distribution Over Time - {selectedStock}</CardTitle>
            <CardDescription>
              Stacked area chart showing positive, neutral, and negative sentiment percentages
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
              <div className="text-3xl font-bold text-green-600">↑ Bullish</div>
              <p className="text-sm text-gray-600">Overall sentiment improving</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Volatility</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">Medium</div>
              <p className="text-sm text-gray-600">Moderate sentiment swings</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Momentum</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">Strong</div>
              <p className="text-sm text-gray-600">Positive momentum building</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </UserLayout>
  );
};

export default SentimentTrends;
