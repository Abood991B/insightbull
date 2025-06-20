
import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const mockData = [
  { date: '2024-01-01', sentiment: 0.6, price: 150 },
  { date: '2024-01-02', sentiment: 0.7, price: 155 },
  { date: '2024-01-03', sentiment: 0.5, price: 148 },
  { date: '2024-01-04', sentiment: 0.8, price: 162 },
  { date: '2024-01-05', sentiment: 0.4, price: 145 },
];

const stocks = ['MSFT', 'NVDA', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'IBM', 'CSCO', 'CRM', 'INTU', 'NOW', 'AMD', 'ACN', 'TXN', 'QCOM', 'ADBE', 'AMAT', 'PANW', 'MU', 'CRWD'];

const SentimentVsPrice = () => {
  const [selectedStock, setSelectedStock] = useState('MSFT');
  const [timeRange, setTimeRange] = useState('7d');

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Sentiment vs Price Analysis</h1>
            <p className="text-gray-600 mt-2">Compare sentiment trends with stock price movements</p>
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
            <CardTitle>Sentiment vs Stock Price - {selectedStock}</CardTitle>
            <CardDescription>
              Dual-axis comparison showing sentiment scores and stock price movements
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={mockData}>
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
