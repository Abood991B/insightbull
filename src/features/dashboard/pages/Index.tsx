import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { useNavigate } from "react-router-dom";
import { TrendingUp, TrendingDown, DollarSign, Activity, BarChart3, Search, Clock, AlertCircle } from "lucide-react";
import { useDashboard } from "@/features/dashboard/hooks/useDashboard";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";

const Index = () => {
  const navigate = useNavigate();
  const { data: dashboard, isLoading, error } = useDashboard();

  const getSentimentColor = (sentiment: number | null) => {
    if (!sentiment) return 'text-gray-600';
    if (sentiment >= 0.1) return 'text-green-600';
    if (sentiment >= -0.1) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getSentimentBadgeColor = (sentiment: number | null) => {
    if (!sentiment) return 'bg-gray-100 text-gray-800';
    if (sentiment >= 0.1) return 'bg-green-100 text-green-800';
    if (sentiment >= -0.1) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const formatSentiment = (score: number | null) => {
    if (score === null) return 'N/A';
    return ((score + 1) * 50).toFixed(0);
  };

  if (isLoading) {
    return (
      <UserLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <Activity className="h-12 w-12 animate-spin text-blue-600 mx-auto" />
            <p className="text-lg text-gray-600">Loading dashboard data...</p>
          </div>
        </div>
      </UserLayout>
    );
  }

  if (error) {
    return (
      <UserLayout>
        <Alert variant="destructive" className="max-w-2xl mx-auto mt-8">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Failed to load dashboard data: {error instanceof Error ? error.message : 'Unknown error'}
            <Button 
              onClick={() => window.location.reload()} 
              variant="outline" 
              size="sm" 
              className="ml-4"
            >
              Retry
            </Button>
          </AlertDescription>
        </Alert>
      </UserLayout>
    );
  }

  if (!dashboard) {
    return null;
  }

  const { market_overview, top_stocks, recent_movers, system_status } = dashboard;

  return (
    <UserLayout>
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
                  <span className="text-sm">
                    Last updated: {system_status.last_collection 
                      ? new Date(system_status.last_collection).toLocaleString() 
                      : 'N/A'}
                  </span>
                </div>
              </div>
              <div className="flex flex-wrap gap-3">
                <Badge className="bg-green-500/20 text-green-100 border-green-400/30 px-4 py-2">
                  <Activity className="h-4 w-4 mr-2" />
                  {market_overview.total_stocks} Active Stocks
                </Badge>
                <Badge className={`${
                  system_status.pipeline_status === 'operational' 
                    ? 'bg-green-500/20 text-green-100 border-green-400/30' 
                    : 'bg-yellow-500/20 text-yellow-100 border-yellow-400/30'
                } px-4 py-2`}>
                  <TrendingUp className="h-4 w-4 mr-2" />
                  {system_status.pipeline_status === 'operational' ? 'Live' : 'Delayed'}
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
              <div className="text-3xl font-bold text-green-700 mb-1">
                {market_overview.average_sentiment.toFixed(2)}
              </div>
              <p className="text-xs text-green-600 flex items-center">
                <TrendingUp className="h-3 w-3 mr-1" />
                Market sentiment score
              </p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-50 to-sky-100 border-blue-200 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-blue-800">Positive Stocks</CardTitle>
              <div className="p-2 bg-blue-500 rounded-lg">
                <TrendingUp className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-700 mb-1">
                {market_overview.positive_stocks}
              </div>
              <p className="text-xs text-blue-600">
                {((market_overview.positive_stocks / market_overview.total_stocks) * 100).toFixed(0)}% of watchlist
              </p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-50 to-violet-100 border-purple-200 hover:shadow-lg transition-all duration-300 transform hover:-translate-y-1">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-3">
              <CardTitle className="text-sm font-medium text-purple-800">Active Stocks</CardTitle>
              <div className="p-2 bg-purple-500 rounded-lg">
                <DollarSign className="h-4 w-4 text-white" />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-purple-700 mb-1">
                {market_overview.total_stocks}
              </div>
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
              <div className="text-3xl font-bold text-orange-700 mb-1">
                {(system_status.total_sentiment_records / 1000).toFixed(1)}K
              </div>
              <p className="text-xs text-orange-600">Total sentiment records</p>
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
                {top_stocks.slice(0, 5).map((stock, index) => (
                  <div 
                    key={stock.symbol} 
                    className="flex items-center justify-between p-4 rounded-xl bg-white border border-green-100 hover:shadow-md transition-all duration-200 hover:border-green-200"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-green-100 text-green-700 rounded-full text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900">{stock.symbol}</div>
                        <div className="text-sm text-gray-600 font-medium">
                          ${stock.current_price?.toFixed(2) || 'N/A'}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={`${getSentimentBadgeColor(stock.sentiment_score)} font-medium`}>
                        {formatSentiment(stock.sentiment_score)}%
                      </Badge>
                      <div className={`text-sm mt-2 font-medium ${
                        stock.price_change_24h && stock.price_change_24h > 0 
                          ? 'text-green-600' 
                          : 'text-red-600'
                      }`}>
                        {stock.price_change_24h 
                          ? `${stock.price_change_24h > 0 ? '+' : ''}${stock.price_change_24h.toFixed(2)}%`
                          : 'N/A'
                        }
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Recent Price Movers */}
          <Card className="shadow-xl border-0 bg-gradient-to-br from-white to-yellow-50">
            <CardHeader className="bg-gradient-to-r from-yellow-500 to-orange-600 text-white rounded-t-lg">
              <CardTitle className="flex items-center gap-3 text-lg">
                <div className="p-2 bg-white/20 rounded-lg">
                  <Activity className="h-5 w-5" />
                </div>
                Recent Price Movers
              </CardTitle>
              <CardDescription className="text-yellow-100">
                Stocks with significant price movements
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-4">
                {recent_movers.map((stock, index) => (
                  <div 
                    key={stock.symbol} 
                    className="flex items-center justify-between p-4 rounded-xl bg-white border border-yellow-100 hover:shadow-md transition-all duration-200 hover:border-yellow-200"
                  >
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-8 h-8 bg-yellow-100 text-yellow-700 rounded-full text-sm font-bold">
                        {index + 1}
                      </div>
                      <div>
                        <div className="font-bold text-gray-900">{stock.symbol}</div>
                        <div className="text-sm text-gray-600 font-medium">
                          ${stock.current_price?.toFixed(2) || 'N/A'}
                        </div>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge className={`${getSentimentBadgeColor(stock.sentiment_score)} font-medium`}>
                        {formatSentiment(stock.sentiment_score)}%
                      </Badge>
                      <div className={`text-sm mt-2 font-medium ${
                        stock.price_change_24h && stock.price_change_24h > 0 
                          ? 'text-green-600' 
                          : 'text-red-600'
                      }`}>
                        {stock.price_change_24h 
                          ? `${stock.price_change_24h > 0 ? '+' : ''}${stock.price_change_24h.toFixed(2)}%`
                          : 'N/A'
                        }
                      </div>
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
                All Watchlist Stocks
              </CardTitle>
              <CardDescription className="text-blue-100">
                Complete stock overview
              </CardDescription>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-3 max-h-80 overflow-y-auto custom-scrollbar">
                {top_stocks.map(stock => (
                  <div 
                    key={stock.symbol} 
                    className="flex items-center justify-between p-3 rounded-lg bg-white border border-blue-100 hover:shadow-sm transition-all duration-200 hover:border-blue-200"
                  >
                    <div className="flex items-center gap-3">
                      <span className="font-bold text-gray-900">{stock.symbol}</span>
                      <Badge 
                        variant="outline" 
                        className={`${getSentimentColor(stock.sentiment_score)} border-current`}
                      >
                        {formatSentiment(stock.sentiment_score)}%
                      </Badge>
                    </div>
                    <div className="text-right">
                      <div className="font-bold text-gray-900">
                        ${stock.current_price?.toFixed(2) || 'N/A'}
                      </div>
                      <div className={`text-sm font-medium ${
                        stock.price_change_24h && stock.price_change_24h > 0 
                          ? 'text-green-600' 
                          : 'text-red-600'
                      }`}>
                        {stock.price_change_24h 
                          ? `${stock.price_change_24h > 0 ? '+' : ''}${stock.price_change_24h.toFixed(2)}%`
                          : 'N/A'
                        }
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
            <Card 
              className="group hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2 bg-gradient-to-br from-white to-blue-50 border-blue-200" 
              onClick={() => navigate('/analysis')}
            >
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
            
            <Card 
              className="group hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2 bg-gradient-to-br from-white to-green-50 border-green-200" 
              onClick={() => navigate('/correlation')}
            >
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

            <Card 
              className="group hover:shadow-xl transition-all duration-300 cursor-pointer transform hover:-translate-y-2 bg-gradient-to-br from-white to-purple-50 border-purple-200" 
              onClick={() => navigate('/sentiment-vs-price')}
            >
              <CardHeader className="pb-4">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-3 bg-purple-500 rounded-xl group-hover:bg-purple-600 transition-colors">
                    <Activity className="h-6 w-6 text-white" />
                  </div>
                  <CardTitle className="text-xl text-gray-900">Sentiment vs Price</CardTitle>
                </div>
                <CardDescription className="text-gray-600 leading-relaxed">
                  Compare sentiment trends with price movements over time
                </CardDescription>
              </CardHeader>
              <CardContent>
                <Button className="w-full bg-purple-500 hover:bg-purple-600 text-white font-medium py-2.5">
                  Compare Trends
                </Button>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      <style>{`
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
    </UserLayout>
  );
};

export default Index;
