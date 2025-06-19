
import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const sentimentData = [
  { name: 'Positive', value: 45, color: '#10B981' },
  { name: 'Neutral', value: 35, color: '#6B7280' },
  { name: 'Negative', value: 20, color: '#EF4444' },
];

const stockPerformance = [
  { stock: 'AAPL', sentiment: 0.7, price: 175.5, change: 2.3 },
  { stock: 'GOOGL', sentiment: 0.6, price: 142.8, change: -1.2 },
  { stock: 'MSFT', sentiment: 0.8, price: 378.9, change: 3.1 },
  { stock: 'TSLA', sentiment: 0.4, price: 248.2, change: -2.8 },
  { stock: 'NVDA', sentiment: 0.9, price: 875.3, change: 5.7 },
];

const StockAnalysis = () => {
  const [selectedStock, setSelectedStock] = useState('AAPL');

  return (
    <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Stock Analysis</h1>
            <p className="text-gray-600 mt-2">Detailed analysis of individual stock performance and sentiment</p>
          </div>
          
          <Select value={selectedStock} onValueChange={setSelectedStock}>
            <SelectTrigger className="w-48">
              <SelectValue placeholder="Select stock" />
            </SelectTrigger>
            <SelectContent>
              {stockPerformance.map((stock) => (
                <SelectItem key={stock.stock} value={stock.stock}>
                  {stock.stock}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Stock Overview */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              {selectedStock} - Apple Inc.
              <Badge variant={stockPerformance.find(s => s.stock === selectedStock)?.change > 0 ? "default" : "destructive"}>
                {stockPerformance.find(s => s.stock === selectedStock)?.change > 0 ? "+" : ""}
                {stockPerformance.find(s => s.stock === selectedStock)?.change}%
              </Badge>
            </CardTitle>
            <CardDescription>Real-time stock information and sentiment analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <p className="text-sm text-gray-600">Current Price</p>
                <p className="text-3xl font-bold">${stockPerformance.find(s => s.stock === selectedStock)?.price}</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Sentiment Score</p>
                <p className="text-3xl font-bold text-green-600">
                  {stockPerformance.find(s => s.stock === selectedStock)?.sentiment}
                </p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600">Market Status</p>
                <Badge className="bg-green-100 text-green-800">Open</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Sentiment Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Sentiment Distribution</CardTitle>
              <CardDescription>Breakdown of sentiment analysis for {selectedStock}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={sentimentData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {sentimentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Stock Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Stock Performance Comparison</CardTitle>
              <CardDescription>Sentiment scores across different stocks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stockPerformance}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="stock" />
                    <YAxis />
                    <Tooltip />
                    <Legend />
                    <Bar dataKey="sentiment" fill="#3B82F6" name="Sentiment Score" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Stock Details Table */}
        <Card>
          <CardHeader>
            <CardTitle>Stock Performance Overview</CardTitle>
            <CardDescription>Comprehensive view of all monitored stocks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-semibold">Stock</th>
                    <th className="text-left py-3 px-4 font-semibold">Price</th>
                    <th className="text-left py-3 px-4 font-semibold">Change</th>
                    <th className="text-left py-3 px-4 font-semibold">Sentiment</th>
                    <th className="text-left py-3 px-4 font-semibold">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {stockPerformance.map((stock) => (
                    <tr key={stock.stock} className="border-b hover:bg-gray-50">
                      <td className="py-3 px-4 font-medium">{stock.stock}</td>
                      <td className="py-3 px-4">${stock.price}</td>
                      <td className="py-3 px-4">
                        <span className={stock.change > 0 ? "text-green-600" : "text-red-600"}>
                          {stock.change > 0 ? "+" : ""}{stock.change}%
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        <div className="flex items-center gap-2">
                          <span>{stock.sentiment}</span>
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-600 h-2 rounded-full" 
                              style={{ width: `${stock.sentiment * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="py-3 px-4">
                        <Badge variant="outline" className="text-green-600">Active</Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>
    </UserLayout>
  );
};

export default StockAnalysis;
