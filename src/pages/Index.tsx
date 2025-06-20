import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown, DollarSign, Activity } from "lucide-react";
const topPositiveStocks = [{
  symbol: 'NVDA',
  sentiment: 0.85,
  change: '+2.4%',
  price: 875.28
}, {
  symbol: 'PLTR',
  sentiment: 0.82,
  change: '+1.8%',
  price: 248.42
}, {
  symbol: 'AAPL',
  sentiment: 0.78,
  change: '+1.2%',
  price: 192.53
}, {
  symbol: 'AVGO',
  sentiment: 0.75,
  change: '+0.9%',
  price: 1650.34
}, {
  symbol: 'MSFT',
  sentiment: 0.72,
  change: '+0.7%',
  price: 420.45
}];
const topNegativeStocks = [{
  symbol: 'INTC',
  sentiment: 0.25,
  change: '-2.1%',
  price: 23.45
}, {
  symbol: 'IBM',
  sentiment: 0.32,
  change: '-1.8%',
  price: 182.76
}, {
  symbol: 'CSCO',
  sentiment: 0.38,
  change: '-1.2%',
  price: 56.12
}, {
  symbol: 'ORCL',
  sentiment: 0.42,
  change: '-0.8%',
  price: 175.34
}, {
  symbol: 'TXN',
  sentiment: 0.45,
  change: '-0.5%',
  price: 196.87
}];
const watchlistStocks = [{
  symbol: 'MSFT',
  name: 'Microsoft Corp',
  price: 420.45,
  change: '+0.7%',
  sentiment: 0.72
}, {
  symbol: 'NVDA',
  name: 'NVIDIA Corp',
  price: 875.28,
  change: '+2.4%',
  sentiment: 0.85
}, {
  symbol: 'AAPL',
  name: 'Apple Inc.',
  price: 192.53,
  change: '+0.5%',
  sentiment: 0.68
}, {
  symbol: 'AVGO',
  name: 'Broadcom Inc.',
  price: 1650.34,
  change: '+1.5%',
  sentiment: 0.73
}, {
  symbol: 'ORCL',
  name: 'Oracle Corp.',
  price: 175.34,
  change: '-0.8%',
  sentiment: 0.42
}, {
  symbol: 'PLTR',
  name: 'Palantir Technologies Inc.',
  price: 248.42,
  change: '+1.8%',
  sentiment: 0.82
}, {
  symbol: 'IBM',
  name: 'International Business Machines',
  price: 182.76,
  change: '-1.8%',
  sentiment: 0.32
}, {
  symbol: 'CSCO',
  name: 'Cisco Systems Inc.',
  price: 56.12,
  change: '-1.2%',
  sentiment: 0.38
}, {
  symbol: 'CRM',
  name: 'Salesforce Inc.',
  price: 267.89,
  change: '+1.1%',
  sentiment: 0.70
}, {
  symbol: 'INTU',
  name: 'Intuit Inc.',
  price: 556.78,
  change: '+0.8%',
  sentiment: 0.62
}, {
  symbol: 'NOW',
  name: 'ServiceNow Inc.',
  price: 789.45,
  change: '+1.3%',
  sentiment: 0.76
}, {
  symbol: 'AMD',
  name: 'Advanced Micro Devices Inc.',
  price: 140.67,
  change: '+0.9%',
  sentiment: 0.64
}, {
  symbol: 'ACN',
  name: 'Accenture PLC',
  price: 345.23,
  change: '+0.6%',
  sentiment: 0.59
}, {
  symbol: 'TXN',
  name: 'Texas Instruments Inc.',
  price: 196.87,
  change: '-0.5%',
  sentiment: 0.45
}, {
  symbol: 'QCOM',
  name: 'Qualcomm Inc.',
  price: 157.23,
  change: '+0.4%',
  sentiment: 0.58
}, {
  symbol: 'ADBE',
  name: 'Adobe Inc.',
  price: 556.78,
  change: '+0.8%',
  sentiment: 0.62
}, {
  symbol: 'AMAT',
  name: 'Applied Materials Inc.',
  price: 189.34,
  change: '+0.2%',
  sentiment: 0.55
}, {
  symbol: 'PANW',
  name: 'Palo Alto Networks Inc.',
  price: 345.67,
  change: '+1.4%',
  sentiment: 0.74
}, {
  symbol: 'MU',
  name: 'Micron Technology Inc.',
  price: 98.45,
  change: '-0.3%',
  sentiment: 0.48
}, {
  symbol: 'CRWD',
  name: 'CrowdStrike Holdings Inc.',
  price: 278.90,
  change: '+1.6%',
  sentiment: 0.79
}];
const Index = () => {
  const navigate = useNavigate();
  const getSentimentColor = (sentiment: number) => {
    if (sentiment >= 0.7) return 'text-green-600';
    if (sentiment >= 0.5) return 'text-yellow-600';
    return 'text-red-600';
  };
  const getSentimentBadgeColor = (sentiment: number) => {
    if (sentiment >= 0.7) return 'bg-green-100 text-green-800';
    if (sentiment >= 0.5) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };
  return <UserLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Stock Market Sentiment Dashboard</h1>
            <p className="text-gray-600 mt-2">Near-real-time sentiment analysis and market overview</p>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Average Sentiment</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">0.62</div>
              <p className="text-xs text-muted-foreground">+12% from yesterday</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Market Cap</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-blue-600">$15.2T</div>
              <p className="text-xs text-muted-foreground">Total watchlist value</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Stocks</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">20</div>
              <p className="text-xs text-muted-foreground">Top Technology Stocks</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Data Points</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">12.4K</div>
              <p className="text-xs text-muted-foreground">Last 24 hours</p>
            </CardContent>
          </Card>
        </div>

        {/* Top Performers and Stock Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Top Positive Stocks */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-green-600" />
                Top Positive Sentiment
              </CardTitle>
              <CardDescription>Stocks with highest positive sentiment</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topPositiveStocks.map((stock, index) => <div key={stock.symbol} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                      <div>
                        <div className="font-semibold">{stock.symbol}</div>
                        <div className="text-sm text-gray-600">${stock.price}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={getSentimentBadgeColor(stock.sentiment)}>
                        {(stock.sentiment * 100).toFixed(0)}%
                      </Badge>
                      <div className="text-sm text-green-600 mt-1">{stock.change}</div>
                    </div>
                  </div>)}
              </div>
            </CardContent>
          </Card>

          {/* Top Negative Stocks */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingDown className="h-5 w-5 text-red-600" />
                Top Negative Sentiment
              </CardTitle>
              <CardDescription>Stocks with lowest sentiment scores</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {topNegativeStocks.map((stock, index) => <div key={stock.symbol} className="flex items-center justify-between p-2 rounded hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                      <div>
                        <div className="font-semibold">{stock.symbol}</div>
                        <div className="text-sm text-gray-600">${stock.price}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={getSentimentBadgeColor(stock.sentiment)}>
                        {(stock.sentiment * 100).toFixed(0)}%
                      </Badge>
                      <div className="text-sm text-red-600 mt-1">{stock.change}</div>
                    </div>
                  </div>)}
              </div>
            </CardContent>
          </Card>

          {/* Stock Price Live Overview */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-blue-600" />
                Live Stock Prices
              </CardTitle>
              <CardDescription>Real-time price overview (20 stocks)</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-2 max-h-64 overflow-y-auto">
                {watchlistStocks.map(stock => <div key={stock.symbol} className="flex items-center justify-between p-2 rounded hover:bg-gray-50 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{stock.symbol}</span>
                      <Badge variant="outline" className={getSentimentColor(stock.sentiment)}>
                        {(stock.sentiment * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <div className="text-right">
                      <div className="font-medium">${stock.price}</div>
                      <div className={stock.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}>
                        {stock.change}
                      </div>
                    </div>
                  </div>)}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/analysis')}>
            <CardHeader>
              <CardTitle className="text-lg">Stock Analysis</CardTitle>
              <CardDescription>Deep dive into individual stock performance</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">Explore Analysis</Button>
            </CardContent>
          </Card>
          
          <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/correlation')}>
            <CardHeader>
              <CardTitle className="text-lg">Correlation Insights</CardTitle>
              <CardDescription>View dynamic correlation between sentiment and prices</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">View Correlations</Button>
            </CardContent>
          </Card>
          
          <Card className="hover:shadow-lg transition-shadow cursor-pointer" onClick={() => navigate('/trends')}>
            <CardHeader>
              <CardTitle className="text-lg">Trend Analysis</CardTitle>
              <CardDescription>Analyze sentiment trends over time</CardDescription>
            </CardHeader>
            <CardContent>
              <Button className="w-full">Analyze Trends</Button>
            </CardContent>
          </Card>
        </div>
      </div>
    </UserLayout>;
};
export default Index;