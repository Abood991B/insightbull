
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const sentimentData = [
  { name: 'Positive', value: 45, color: '#10B981' },
  { name: 'Neutral', value: 35, color: '#6B7280' },
  { name: 'Negative', value: 20, color: '#EF4444' },
];

const stockData = [
  { stock: 'MSFT', name: 'Microsoft Corp', sentiment: 0.8, price: 378.9, change: 3.1 },
  { stock: 'NVDA', name: 'NVIDIA Corp', sentiment: 0.9, price: 875.3, change: 5.7 },
  { stock: 'AAPL', name: 'Apple Inc.', sentiment: 0.7, price: 175.5, change: 2.3 },
  { stock: 'AVGO', name: 'Broadcom Inc', sentiment: 0.6, price: 142.8, change: -1.2 },
  { stock: 'ORCL', name: 'Oracle Corp.', sentiment: 0.7, price: 248.2, change: 1.8 },
  { stock: 'PLTR', name: 'Palantir Technologies Inc.', sentiment: 0.5, price: 45.2, change: -2.8 },
  { stock: 'IBM', name: 'International Business Machines', sentiment: 0.6, price: 185.4, change: 0.9 },
  { stock: 'CSCO', name: 'Cisco Systems Inc.', sentiment: 0.5, price: 58.7, change: -0.5 },
  { stock: 'CRM', name: 'Salesforce Inc.', sentiment: 0.7, price: 285.6, change: 2.1 },
  { stock: 'INTU', name: 'Intuit Inc.', sentiment: 0.8, price: 695.8, change: 3.4 },
];

const StockAnalysis = () => {
  const [selectedStock, setSelectedStock] = useState('MSFT');

  const currentStock = stockData.find(s => s.stock === selectedStock) || stockData[0];

  return (
    <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Stock Analysis</h1>
            <p className="text-gray-600 mt-2">Detailed analysis of individual stock performance and sentiment from our near-real-time dashboard</p>
          </div>
          
          <Select value={selectedStock} onValueChange={setSelectedStock}>
            <SelectTrigger className="w-64">
              <SelectValue placeholder="Select stock" />
            </SelectTrigger>
            <SelectContent>
              {stockData.map((stock) => (
                <SelectItem key={stock.stock} value={stock.stock}>
                  {stock.stock} - {stock.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Stock Overview */}
        <Card className="border-l-4 border-l-blue-500">
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              {selectedStock} - {currentStock.name}
              <Badge variant={currentStock.change > 0 ? "default" : "destructive"} className="text-sm">
                {currentStock.change > 0 ? "+" : ""}{currentStock.change}%
              </Badge>
            </CardTitle>
            <CardDescription>Near-real-time stock information and sentiment analysis</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-blue-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Current Price</p>
                <p className="text-3xl font-bold text-blue-600">${currentStock.price}</p>
              </div>
              <div className="text-center p-4 bg-green-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Sentiment Score</p>
                <p className="text-3xl font-bold text-green-600">{currentStock.sentiment}</p>
              </div>
              <div className="text-center p-4 bg-purple-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">24h Change</p>
                <p className={`text-3xl font-bold ${currentStock.change > 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {currentStock.change > 0 ? "+" : ""}{currentStock.change}%
                </p>
              </div>
              <div className="text-center p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">Market Status</p>
                <Badge className="bg-green-100 text-green-800 text-lg px-3 py-1">Open</Badge>
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

          {/* Top Performers */}
          <Card>
            <CardHeader>
              <CardTitle>Top Sentiment Performers</CardTitle>
              <CardDescription>Highest sentiment scores in our watchlist</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stockData.slice(0, 5)}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="stock" />
                    <YAxis domain={[0, 1]} />
                    <Tooltip />
                    <Bar dataKey="sentiment" fill="#3B82F6" name="Sentiment Score" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Enhanced Stock Details Table */}
        <Card>
          <CardHeader>
            <CardTitle>Watchlist Overview</CardTitle>
            <CardDescription>Complete view of all monitored technology stocks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-4 px-4 font-semibold text-gray-700">Stock</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-700">Company</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-700">Price</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-700">Change</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-700">Sentiment</th>
                    <th className="text-left py-4 px-4 font-semibold text-gray-700">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {stockData.map((stock) => (
                    <tr key={stock.stock} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-bold text-blue-600">{stock.stock}</td>
                      <td className="py-4 px-4 text-gray-800">{stock.name}</td>
                      <td className="py-4 px-4 font-semibold">${stock.price}</td>
                      <td className="py-4 px-4">
                        <span className={`font-semibold ${stock.change > 0 ? "text-green-600" : "text-red-600"}`}>
                          {stock.change > 0 ? "+" : ""}{stock.change}%
                        </span>
                      </td>
                      <td className="py-4 px-4">
                        <div className="flex items-center gap-3">
                          <span className="font-semibold">{stock.sentiment}</span>
                          <div className="w-24 bg-gray-200 rounded-full h-3">
                            <div 
                              className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-300" 
                              style={{ width: `${stock.sentiment * 100}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className="text-green-600 border-green-600">Active</Badge>
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
