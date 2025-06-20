import UserLayout from "@/components/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown, DollarSign, Activity, BarChart3, Search, Clock } from "lucide-react";

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
      <div className="space-y-8">
        {/* Enhanced Header */}
        <div className="relative overflow-hidden bg-gradient-to-br from-blue-600 via-blue-700 to-indigo-800 rounded-2xl p-8 text-white shadow-2xl">
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/20 to-transparent"></div>
          <div className="relative z-10">
            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
              <div>
                <h1 className="text-4xl font-bold mb-3 bg-gradient-to-r from-white to-blue-100 bg-clip-text text-transparent">
                  Stock Market Sentiment Dashboard
                </h1>
                <p className="text-blue-100 text-lg leading-relaxed max-w-2xl">
                  Near-real-time sentiment analysis and comprehensive market overview for technology stocks
                </p>
                <div className="flex items-center gap-2 mt-4 text-blue-200">
                  <Clock className="h-4 w-4" />
                  <span className="text-sm">Last updated: Live • Data refreshed every 30 seconds</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <Badge className="bg-green-500/20 text-green-100 border-green-400/30 px-4 py-2">
                  <Activity className="h-4 w-4 mr-2" />
                  20 Active Stocks
                </Badge>
                <Badge className="bg-blue-500/20 text-blue-100 border-blue-400/30 px-4 py-2">
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Near-real-time Analytics
                </Badge>
              </div>
            </div>
          </div>
        </div>

        {/* Enhanced Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card className="bg-gradient-to-br from-green-50 to-emerald-100 border-green-200 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-green-800">Average Sentiment</CardTitle>
              <div className="p-2 bg-green-500 rounded-lg">
                <Activity className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-green-700 mb-1">0.62</div>
              <p className="text-xs text-green-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                +12% from yesterday
              </p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-50 to-sky-100 border-blue-200 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-blue-800">Market Cap</CardTitle>
              <div className="p-2 bg-blue-500 rounded-lg">
                <DollarSign className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-700 mb-1">$15.2T</div>
              <p className="text-xs text-blue-600">Total watchlist value</p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-50 to-violet-100 border-purple-200 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-purple-800">Active Stocks</CardTitle>
              <div className="p-2 bg-purple-500 rounded-lg">
                <TrendingUp className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-700 mb-1">20</div>
              <p className="text-xs text-purple-600">Top Technology Stocks</p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-orange-50 to-amber-100 border-orange-200 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-orange-800">Data Points</CardTitle>
              <div className="p-2 bg-orange-500 rounded-lg">
                <Activity className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-orange-700 mb-1">12.4K</div>
              <p className="text-xs text-orange-600">Last 24 hours</p>
            </CardContent>
          </Card>
        </div>

        {/* Enhanced Top Performers and Stock Lists */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Top Positive Stocks */}
          <Card className="shadow-xl border-0 bg-gradient-to-br from-white to-green-50">
            <CardHeader className="bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-3 text-lg">
                <div className="p-2 bg-white/20 rounded-lg">
                  <TrendingUp className="h-5 w-5" />
                </div>
                Top Positive Sentiment
              </CardTitle>
              <CardDescription className="text-green-100">
                Stocks with highest positive sentiment scores
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                {topPositiveStocks.map((stock, index) => (
                  <div key={stock.symbol} className="flex items-center justify-between p-4 rounded-xl bg-white border border-green-100 hover:shadow-md transition-all duration-200 hover:border-green-200">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-green-100 text-green-700 rounded-full text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900">{stock.symbol}</div>
                        <div className="text-sm text-gray-600 font-medium">${stock.price}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={`${getSentimentBadgeColor(stock.sentiment)} font-medium`}>
                        {(stock.sentiment * 100).toFixed(0)}%
                      </Badge>
                      <div className="text-sm text-green-600 mt-2 font-medium">{stock.change}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Top Negative Stocks */}
          <Card className="shadow-xl border-0 bg-gradient-to-br from-white to-red-50">
            <CardHeader className="bg-gradient-to-r from-red-500 to-rose-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-3 text-lg">
                <div className="p-2 bg-white/20 rounded-lg">
                  <TrendingDown className="h-5 w-5" />
                </div>
                Top Negative Sentiment
              </CardTitle>
              <CardDescription className="text-red-100">
                Stocks with lowest sentiment scores
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                {topNegativeStocks.map((stock, index) => (
                  <div key={stock.symbol} className="flex items-center justify-between p-4 rounded-xl bg-white border border-red-100 hover:shadow-md transition-all duration-200 hover:border-red-200">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-red-100 text-red-700 rounded-full text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900">{stock.symbol}</div>
                        <div className="text-sm text-gray-600 font-medium">${stock.price}</div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={`${getSentimentBadgeColor(stock.sentiment)} font-medium`}>
                        {(stock.sentiment * 100).toFixed(0)}%
                      </Badge>
                      <div className="text-sm text-red-600 mt-2 font-medium">{stock.change}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Stock Price Live Overview */}
          <Card className="shadow-xl border-0 bg-gradient-to-br from-white to-blue-50">
            <CardHeader className="bg-gradient-to-r from-blue-500 to-indigo-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-3 text-lg">
                <div className="p-2 bg-white/20 rounded-lg">
                  <DollarSign className="h-5 w-5" />
                </div>
                Near-real-time Stock Prices
              </CardTitle>
              <CardDescription className="text-blue-100">
                Live price overview (20 technology stocks)
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-3 max-h-80 overflow-y-auto custom-scrollbar">
                {watchlistStocks.map(stock => (
                  <div key={stock.symbol} className="flex items-center justify-between p-3 rounded-lg bg-white border border-blue-100 hover:shadow-sm transition-all duration-200 hover:border-blue-200">
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-gray-900">{stock.symbol}</span>
                      <Badge variant="outline" className={`${getSentimentColor(stock.sentiment)} border-current`}>
                        {(stock.sentiment * 100).toFixed(0)}%
                      </Badge>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900">${stock.price}</div>
                      <div className={`text-sm font-medium ${stock.change.startsWith('+') ? 'text-green-600' : 'text-red-600'}`}>
                        {stock.change}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Enhanced Quick Actions */}
        <div className="bg-gradient-to-br from-gray-50 to-white rounded-2xl p-8 shadow-lg border border-gray-100">
          <div className="text-center mb-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Analytics & Insights</h2>
            <p className="text-gray-600">Explore comprehensive market analysis tools</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <Card className="group hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2 bg-gradient-to-br from-white to-blue-50 border-blue-200" onClick={() => navigate('/analysis')}>
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-3 bg-blue-500 rounded-xl group-hover:bg-blue-600 transition-colors">
                    <Search className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">Stock Analysis</CardTitle>
                </div>
                <CardDescription className="text-gray-600 leading-relaxed">
                  Deep dive into individual stock performance with comprehensive sentiment metrics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full bg-blue-500 hover:bg-blue-600 text-white font-medium py-2.5">
                  Explore Analysis
                </Button>
              </CardContent>
            </Card>
            
            <Card className="group hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2 bg-gradient-to-br from-white to-green-50 border-green-200" onClick={() => navigate('/correlation')}>
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-3 bg-green-500 rounded-xl group-hover:bg-green-600 transition-colors">
                    <BarChart3 className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">Correlation Insights</CardTitle>
                </div>
                <CardDescription className="text-gray-600 leading-relaxed">
                  View dynamic correlation between sentiment and stock prices across markets
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full bg-green-500 hover:bg-green-600 text-white font-medium py-2.5">
                  View Correlations
                </Button>
              </CardContent>
            </Card>
            
            <Card className="group hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2 bg-gradient-to-br from-white to-purple-50 border-purple-200" onClick={() => navigate('/trends')}>
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-3 bg-purple-500 rounded-xl group-hover:bg-purple-600 transition-colors">
                    <Activity className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">Trend Analysis</CardTitle>
                </div>
                <CardDescription className="text-gray-600 leading-relaxed">
                  Analyze sentiment trends over time with advanced temporal analytics
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full bg-purple-500 hover:bg-purple-600 text-white font-medium py-2.5">
                  Analyze Trends
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <style jsx>{`
        .custom-scrollbar::-webkit-scrollbar {
          width: 6px;
        }
        .custom-scrollbar::-webkit-scrollbar-track {
          background: #f1f5f9;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: #cbd5e1;
          border-radius: 3px;
        }
        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: #94a3b8;
        }
      `}</style>
    </UserLayout>;
};

export default Index;
