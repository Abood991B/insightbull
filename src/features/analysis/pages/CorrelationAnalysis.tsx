
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { useState } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, BarChart, Bar } from 'recharts';

const correlationData = [
  { sentiment: 0.2, price: 142, volume: 800 },
  { sentiment: 0.4, price: 148, volume: 1200 },
  { sentiment: 0.6, price: 155, volume: 1400 },
  { sentiment: 0.8, price: 162, volume: 1600 },
  { sentiment: 0.9, price: 168, volume: 1800 },
  { sentiment: 0.3, price: 145, volume: 900 },
  { sentiment: 0.7, price: 158, volume: 1500 },
];

const stockCorrelations = [
  { stock: 'NVDA', correlation: 0.85, significance: 'High' },
  { stock: 'MSFT', correlation: 0.75, significance: 'High' },
  { stock: 'AAPL', correlation: 0.68, significance: 'Medium' },
  { stock: 'AVGO', correlation: 0.45, significance: 'Medium' },
  { stock: 'ORCL', correlation: 0.32, significance: 'Low' },
];

const stocks = ['MSFT', 'NVDA', 'AAPL', 'AVGO', 'ORCL', 'PLTR', 'IBM', 'CSCO', 'CRM', 'INTU', 'NOW', 'AMD', 'ACN', 'TXN', 'QCOM', 'ADBE', 'AMAT', 'PANW', 'MU', 'CRWD'];

const CorrelationAnalysis = () => {
  const [selectedStock, setSelectedStock] = useState('MSFT');
  const [timeRange, setTimeRange] = useState('7d');

  const getSignificanceColor = (significance: string) => {
    switch(significance) {
      case 'High': return 'text-green-600';
      case 'Medium': return 'text-yellow-600';
      case 'Low': return 'text-red-600';
      default: return 'text-gray-600';
    }
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

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Pearson Correlation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">0.75</div>
              <p className="text-sm text-gray-600">Strong positive correlation</p>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">R-Squared</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">0.56</div>
              <p className="text-sm text-gray-600">Variance explained</p>
            </CardContent>
          </Card>
          
          <Card className="border-l-4 border-l-purple-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Significance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">p &lt; 0.01</div>
              <p className="text-sm text-gray-600">Statistically significant</p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-orange-500">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Sample Size</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-600">2,847</div>
              <p className="text-sm text-gray-600">Data points analyzed</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Main Scatter Plot */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-3">
                Correlation Scatter Plot - {selectedStock}
                <Badge variant="outline" className="text-blue-600">
                  R = 0.75
                </Badge>
              </CardTitle>
              <CardDescription>
                Relationship between sentiment scores and stock prices
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <ScatterChart data={correlationData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis 
                      dataKey="sentiment" 
                      name="Sentiment Score" 
                      domain={[0, 1]}
                      label={{ value: 'Sentiment Score', position: 'insideBottom', offset: -5 }}
                    />
                    <YAxis 
                      dataKey="price" 
                      name="Stock Price"
                      label={{ value: 'Stock Price ($)', angle: -90, position: 'insideLeft' }}
                    />
                    <Tooltip 
                      cursor={{ strokeDasharray: '3 3' }}
                      formatter={(value, name) => [
                        name === 'price' ? `$${value}` : value,
                        name === 'price' ? 'Stock Price' : 'Sentiment Score'
                      ]}
                    />
                    <Scatter dataKey="price" fill="#3B82F6">
                      {correlationData.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.sentiment > 0.6 ? '#10B981' : entry.sentiment > 0.4 ? '#F59E0B' : '#EF4444'} 
                        />
                      ))}
                    </Scatter>
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Cross-Stock Comparison */}
          <Card>
            <CardHeader>
              <CardTitle>Cross-Stock Correlations</CardTitle>
              <CardDescription>
                Correlation strength across different stocks
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-80">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={stockCorrelations} layout="horizontal">
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis type="number" domain={[0, 1]} />
                    <YAxis dataKey="stock" type="category" width={60} />
                    <Tooltip 
                      formatter={(value: number) => [`${(value * 100).toFixed(0)}%`, 'Correlation']}
                    />
                    <Bar dataKey="correlation" radius={[0, 4, 4, 0]}>
                      {stockCorrelations.map((entry, index) => (
                        <Cell 
                          key={`cell-${index}`} 
                          fill={entry.correlation > 0.7 ? '#10B981' : entry.correlation > 0.5 ? '#F59E0B' : '#EF4444'} 
                        />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Detailed Analysis Table */}
        <Card>
          <CardHeader>
            <CardTitle>Detailed Correlation Metrics</CardTitle>
            <CardDescription>Statistical analysis for each stock in our watchlist</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b-2 border-gray-200">
                    <th className="text-left py-4 px-4 font-semibold">Stock</th>
                    <th className="text-left py-4 px-4 font-semibold">Correlation</th>
                    <th className="text-left py-4 px-4 font-semibold">R-Squared</th>
                    <th className="text-left py-4 px-4 font-semibold">Significance</th>
                    <th className="text-left py-4 px-4 font-semibold">Trend</th>
                  </tr>
                </thead>
                <tbody>
                  {stockCorrelations.map((item) => (
                    <tr key={item.stock} className="border-b hover:bg-gray-50 transition-colors">
                      <td className="py-4 px-4 font-bold text-blue-600">{item.stock}</td>
                      <td className="py-4 px-4 font-semibold">{item.correlation.toFixed(2)}</td>
                      <td className="py-4 px-4">{(item.correlation * item.correlation).toFixed(2)}</td>
                      <td className="py-4 px-4">
                        <Badge variant="outline" className={getSignificanceColor(item.significance)}>
                          {item.significance}
                        </Badge>
                      </td>
                      <td className="py-4 px-4">
                        <span className={item.correlation > 0.5 ? 'text-green-600' : 'text-red-600'}>
                          {item.correlation > 0.5 ? '↗ Positive' : '↘ Negative'}
                        </span>
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

export default CorrelationAnalysis;
