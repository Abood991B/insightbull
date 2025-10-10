
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Area, AreaChart } from 'recharts';

const mockData = [
  { date: '2024-01-01', sentiment: 0.6, price: 150, volume: 1200 },
  { date: '2024-01-02', sentiment: 0.7, price: 155, volume: 1400 },
  { date: '2024-01-03', sentiment: 0.5, price: 148, volume: 1100 },
  { date: '2024-01-04', sentiment: 0.8, price: 162, volume: 1600 },
  { date: '2024-01-05', sentiment: 0.4, price: 145, volume: 900 },
  { date: '2024-01-06', sentiment: 0.9, price: 168, volume: 1800 },
  { date: '2024-01-07', sentiment: 0.6, price: 158, volume: 1300 },
];

const stocks = ['MSFT', 'NVDA', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'IBM', 'CSCO', 'CRM', 'INTU', 'NOW', 'AMD', 'ACN', 'TXN', 'QCOM', 'ADBE', 'AMAT', 'PANW', 'MU', 'CRWD'];

const SentimentVsPrice = () => {
  const [selectedStock, setSelectedStock] = useState('MSFT');
  const [timeRange, setTimeRange] = useState('7d');

  const correlation = 0.75;
  const trend = correlation > 0.5 ? 'Positive' : correlation < -0.5 ? 'Negative' : 'Neutral';
  const strength = Math.abs(correlation) > 0.7 ? 'Strong' : Math.abs(correlation) > 0.4 ? 'Moderate' : 'Weak';

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

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Correlation Strength</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{strength}</div>
              <p className="text-sm text-gray-600 mt-1">{(correlation * 100).toFixed(0)}% correlation coefficient</p>
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
              <CardTitle className="text-lg">Analysis Period</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">{timeRange === '1d' ? '24h' : timeRange === '7d' ? '1 Week' : '2 Weeks'}</div>
              <p className="text-sm text-gray-600 mt-1">Data collection window</p>
            </CardContent>
          </Card>
        </div>

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
                <LineChart data={mockData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="date" stroke="#666" />
                  <YAxis yAxisId="left" stroke="#8884d8" />
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
                <AreaChart data={mockData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
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
      </div>
    </UserLayout>
  );
};

export default SentimentVsPrice;
