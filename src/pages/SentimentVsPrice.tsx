
import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useEffect } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { date: '2024-01-01', sentiment: 0.6, price: 150 },
  { date: '2024-01-02', sentiment: 0.7, price: 155 },
  { date: '2024-01-03', sentiment: 0.5, price: 148 },
  { date: '2024-01-04', sentiment: 0.8, price: 162 },
  { date: '2024-01-05', sentiment: 0.4, price: 145 },
];

const stocks = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN'];

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

const SentimentVsPrice = () => {
  const [selectedStock, setSelectedStock] = useState('AAPL');
  const [timeRange, setTimeRange] = useState('7d');
  const [filteredData, setFilteredData] = useState(mockData);

  // Filter data based on time range and stock selection
  useEffect(() => {
    // In a real app, this would filter based on actual dates and stock
    // For demo purposes, we'll use the mock data
    setFilteredData(mockData);
  }, [timeRange, selectedStock]);

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment vs Price Analysis</h1>
            <p className="text-gray-600 mt-2">Compare sentiment trends with stock price movements over {timeRanges.find(r => r.value === timeRange)?.label.toLowerCase()}</p>
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
            <CardTitle>Sentiment vs Stock Price - {selectedStock}</CardTitle>
            <CardDescription>
              Dual-axis comparison showing sentiment scores and stock price movements over {timeRanges.find(r => r.value === timeRange)?.label.toLowerCase()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={filteredData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Legend />
                  <Line 
                    yAxisId="left"
                    type="monotone" 
                    dataKey="sentiment" 
                    stroke="#8884d8" 
                    strokeWidth={2}
                    name="Sentiment Score"
                  />
                  <Line 
                    yAxisId="right"
                    type="monotone" 
                    dataKey="price" 
                    stroke="#82ca9d" 
                    strokeWidth={2}
                    name="Stock Price ($)"
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

export default SentimentVsPrice;
