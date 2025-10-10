import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useState } from "react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { useStocks, useStockDetail } from "@/features/analysis/hooks/useStocks";
import { Activity, AlertCircle } from "lucide-react";

const StockAnalysis = () => {
  const { data: stocksList, isLoading: isLoadingList } = useStocks({ active_only: true });
  const [selectedStock, setSelectedStock] = useState('');
  const [timeframe, setTimeframe] = useState<'1d' | '7d' | '14d'>('7d');

  // Set initial stock when list loads
  useState(() => {
    if (stocksList && stocksList.stocks.length > 0 && !selectedStock) {
      setSelectedStock(stocksList.stocks[0].symbol);
    }
  });

  const { data: stockDetail, isLoading: isLoadingDetail, error } = useStockDetail(selectedStock, timeframe);

  if (isLoadingList) {
    return (
      <UserLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <Activity className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <p className="text-lg text-gray-600">Loading stocks...</p>
          </div>
        </div>
      </UserLayout>
    );
  }

  if (!stocksList || stocksList.stocks.length === 0) {
    return (
      <UserLayout>
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>No stocks available for analysis.</AlertDescription>
        </Alert>
      </UserLayout>
    );
  }

  // Calculate sentiment distribution
  const sentimentData = stockDetail ? [
    { 
      name: 'Positive', 
      value: stockDetail.sentiment_history.filter(s => s.score > 0.1).length,
      color: '#10B981' 
    },
    { 
      name: 'Neutral', 
      value: stockDetail.sentiment_history.filter(s => s.score >= -0.1 && s.score <= 0.1).length,
      color: '#6B7280' 
    },
    { 
      name: 'Negative', 
      value: stockDetail.sentiment_history.filter(s => s.score < -0.1).length,
      color: '#EF4444' 
    },
  ] : [];

  // Top performers data
  const topPerformersData = stocksList.stocks
    .filter(s => s.latest_sentiment !== null)
    .sort((a, b) => (b.latest_sentiment || 0) - (a.latest_sentiment || 0))
    .slice(0, 5)
    .map(s => ({
      stock: s.symbol,
      sentiment: ((s.latest_sentiment || 0) + 1) / 2 // Convert from -1,1 to 0,1
    }));

  return (
    <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Stock Analysis</h1>
            <p className="text-gray-600 mt-2">Detailed analysis of individual stock performance and sentiment from our near-real-time dashboard</p>
          </div>
          
          <div className="flex gap-4">
            <Select value={selectedStock} onValueChange={setSelectedStock}>
              <SelectTrigger className="w-64">
                <SelectValue placeholder="Select stock" />
              </SelectTrigger>
              <SelectContent>
                {stocksList.stocks.map((stock) => (
                  <SelectItem key={stock.symbol} value={stock.symbol}>
                    {stock.symbol} - {stock.company_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={timeframe} onValueChange={(v) => setTimeframe(v as '1d' | '7d' | '14d')}>
              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1d">1 Day</SelectItem>
                <SelectItem value="7d">7 Days</SelectItem>
                <SelectItem value="14d">14 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load stock details: {error instanceof Error ? error.message : 'Unknown error'}
            </AlertDescription>
          </Alert>
        )}

        {isLoadingDetail && (
          <div className="flex items-center justify-center py-12">
            <Activity className="h-8 w-8 animate-spin text-blue-600" />
          </div>
        )}

        {stockDetail && (
          <>
            {/* Stock Overview */}
            <Card className="border-l-4 border-l-blue-500">
              <CardHeader>
                <CardTitle className="flex items-center gap-3">
                  {stockDetail.symbol} - {stockDetail.company_name}
                  <Badge variant={
                    stockDetail.metrics.price_change_percent && stockDetail.metrics.price_change_percent > 0 
                      ? "default" 
                      : "destructive"
                  } className="text-sm">
                    {stockDetail.metrics.price_change_percent 
                      ? `${stockDetail.metrics.price_change_percent > 0 ? '+' : ''}${stockDetail.metrics.price_change_percent.toFixed(2)}%`
                      : 'N/A'
                    }
                  </Badge>
                </CardTitle>
                <CardDescription>Near-real-time stock information and sentiment analysis</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
                  <div className="text-center p-4 bg-blue-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Current Price</p>
                    <p className="text-3xl font-bold text-blue-600">
                      ${stockDetail.price_history[0]?.close_price.toFixed(2) || 'N/A'}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-green-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Sentiment Score</p>
                    <p className="text-3xl font-bold text-green-600">
                      {stockDetail.metrics.avg_sentiment.toFixed(2)}
                    </p>
                  </div>
                  <div className="text-center p-4 bg-purple-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Price Change</p>
                    <p className={`text-3xl font-bold ${
                      stockDetail.metrics.price_change_percent && stockDetail.metrics.price_change_percent > 0 
                        ? 'text-green-600' 
                        : 'text-red-600'
                    }`}>
                      {stockDetail.metrics.price_change_percent 
                        ? `${stockDetail.metrics.price_change_percent > 0 ? '+' : ''}${stockDetail.metrics.price_change_percent.toFixed(2)}%`
                        : 'N/A'
                      }
                    </p>
                  </div>
                  <div className="text-center p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Data Quality</p>
                    <Badge className="bg-green-100 text-green-800 text-lg px-3 py-1">
                      {(stockDetail.metrics.data_quality_score * 100).toFixed(0)}%
                    </Badge>
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
                  <CardDescription>
                    Breakdown of sentiment analysis for {selectedStock} ({stockDetail.metrics.total_sentiment_records} records)
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="h-64">
                    {sentimentData.some(d => d.value > 0) ? (
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
                    ) : (
                      <div className="flex items-center justify-center h-full text-gray-500">
                        No sentiment data available
                      </div>
                    )}
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
                      <BarChart data={topPerformersData}>
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
                        <th className="text-left py-4 px-4 font-semibold text-gray-700">Sentiment</th>
                        <th className="text-left py-4 px-4 font-semibold text-gray-700">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stocksList.stocks.map((stock) => (
                        <tr key={stock.symbol} className="border-b hover:bg-gray-50 transition-colors">
                          <td className="py-4 px-4 font-bold text-blue-600">{stock.symbol}</td>
                          <td className="py-4 px-4 text-gray-800">{stock.company_name}</td>
                          <td className="py-4 px-4 font-semibold">
                            ${stock.latest_price?.toFixed(2) || 'N/A'}
                          </td>
                          <td className="py-4 px-4">
                            <div className="flex items-center gap-3">
                              <span className="font-semibold">
                                {stock.latest_sentiment?.toFixed(2) || 'N/A'}
                              </span>
                              {stock.latest_sentiment !== null && (
                                <div className="w-24 bg-gray-200 rounded-full h-3">
                                  <div 
                                    className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-300" 
                                    style={{ width: `${((stock.latest_sentiment + 1) / 2) * 100}%` }}
                                  ></div>
                                </div>
                              )}
                            </div>
                          </td>
                          <td className="py-4 px-4">
                            <Badge 
                              variant="outline" 
                              className={stock.is_active ? "text-green-600 border-green-600" : "text-gray-600 border-gray-600"}
                            >
                              {stock.is_active ? 'Active' : 'Inactive'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </UserLayout>
  );
};

export default StockAnalysis;
