
import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useState, useEffect } from "react";
import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

const correlationData = [
  { sentiment: 0.2, price: 142 },
  { sentiment: 0.4, price: 148 },
  { sentiment: 0.6, price: 155 },
  { sentiment: 0.8, price: 162 },
  { sentiment: 0.9, price: 168 },
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

const CorrelationAnalysis = () => {
  const [selectedStock, setSelectedStock] = useState('AAPL');
  const [timeRange, setTimeRange] = useState('7d');
  const [correlationStrength, setCorrelationStrength] = useState(0.75);

  // Update correlation strength based on time range
  useEffect(() => {
    // Simulate different correlation strengths for different time ranges
    const correlationMap: Record<string, number> = {
      '1h': 0.45,
      '6h': 0.52,
      '12h': 0.61,
      '1d': 0.68,
      '3d': 0.72,
      '7d': 0.75,
      '14d': 0.71,
      '30d': 0.68,
      '90d': 0.63
    };
    setCorrelationStrength(correlationMap[timeRange] || 0.75);
  }, [timeRange, selectedStock]);

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Correlation Analysis</h1>
            <p className="text-gray-600 mt-2">Dynamic correlation between sentiment and stock prices over {timeRanges.find(r => r.value === timeRange)?.label.toLowerCase()}</p>
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

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Pearson Correlation</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{correlationStrength.toFixed(2)}</div>
              <p className="text-sm text-gray-600">
                {correlationStrength > 0.7 ? 'Strong positive correlation' : 
                 correlationStrength > 0.5 ? 'Moderate positive correlation' : 
                 'Weak positive correlation'}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">R-Squared</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-600">{(correlationStrength * correlationStrength).toFixed(2)}</div>
              <p className="text-sm text-gray-600">Variance explained</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Significance</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-600">p &lt; 0.01</div>
              <p className="text-sm text-gray-600">Statistically significant</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Correlation Scatter Plot - {selectedStock}</CardTitle>
            <CardDescription>
              Scatter plot showing the relationship between sentiment scores and stock prices over {timeRanges.find(r => r.value === timeRange)?.label.toLowerCase()}
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart data={correlationData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis 
                    dataKey="sentiment" 
                    name="Sentiment Score" 
                    domain={[0, 1]}
                  />
                  <YAxis 
                    dataKey="price" 
                    name="Stock Price" 
                  />
                  <Tooltip cursor={{ strokeDasharray: '3 3' }} />
                  <Scatter dataKey="price" fill="#8884d8" />
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>
    </UserLayout>
  );
};

export default CorrelationAnalysis;
