import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AdminLayout } from '../../../shared/components/layouts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../../shared/components/ui/card';
import { Button } from '../../../shared/components/ui/button';
import { Badge } from '../../../shared/components/ui/badge';
import { Alert, AlertDescription } from '../../../shared/components/ui/alert';
import { useToast } from '../../../shared/hooks/use-toast';
import { adminAPI, SystemStatus, ModelAccuracy, RealTimePriceServiceStatus } from '../../../api/services/admin.service';
import { 
  Activity, 
  Database, 
  Server, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  TrendingUp,
  Users,
  RefreshCw,
  Play,
  Settings,
  FileText,
  BarChart3,
  Zap
} from 'lucide-react';

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();
  
  // State management
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [modelAccuracy, setModelAccuracy] = useState<ModelAccuracy | null>(null);
  const [priceServiceStatus, setPriceServiceStatus] = useState<RealTimePriceServiceStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);  
  const [collectingData, setCollectingData] = useState(false);
  const [priceServiceLoading, setPriceServiceLoading] = useState(false);

  // Load dashboard data
  const loadDashboardData = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      
      // Load system status, model accuracy, and price service status in parallel
      const [statusResponse, accuracyResponse, priceServiceResponse] = await Promise.all([
        adminAPI.getSystemStatus(),
        adminAPI.getModelAccuracy(),
        adminAPI.getRealTimePriceServiceStatus()
      ]);
      
      setSystemStatus(statusResponse);
      setModelAccuracy(accuracyResponse);
      setPriceServiceStatus(priceServiceResponse);
      
      if (showRefreshToast) {
        toast({
          title: "Dashboard Updated",
          description: "System status and metrics have been refreshed.",
        });
      }
      
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
      toast({
        title: "Error",
        description: "Failed to load dashboard data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Manual data collection
  const triggerDataCollection = async () => {
    try {
      setCollectingData(true);
      
      await adminAPI.triggerManualCollection();
      
      toast({
        title: "Data Collection Started",
        description: "Manual data collection has been triggered successfully.",
      });
      
      // Refresh dashboard after a delay to show updated metrics
      setTimeout(() => {
        loadDashboardData();
      }, 2000);
      
    } catch (error) {
      console.error('Failed to trigger data collection:', error);
      toast({
        title: "Error",
        description: "Failed to trigger data collection. Please try again.",
        variant: "destructive",
      });
    } finally {
      setCollectingData(false);
    }
  };

  // Real-time price service controls
  const handlePriceServiceControl = async (action: 'start' | 'stop') => {
    try {
      setPriceServiceLoading(true);
      
      if (action === 'start') {
        await adminAPI.startRealTimePriceService();
        toast({
          title: "Price Service Started",
          description: "Real-time price service has been started successfully.",
        });
      } else {
        await adminAPI.stopRealTimePriceService();
        toast({
          title: "Price Service Stopped", 
          description: "Real-time price service has been stopped successfully.",
        });
      }
      
      // Refresh price service status
      setTimeout(async () => {
        try {
          const response = await adminAPI.getRealTimePriceServiceStatus();
          setPriceServiceStatus(response);
        } catch (error) {
          console.error('Failed to refresh price service status:', error);
        }
      }, 1000);
      
    } catch (error) {
      console.error(`Failed to ${action} price service:`, error);
      toast({
        title: "Error",
        description: `Failed to ${action} real-time price service. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setPriceServiceLoading(false);
    }
  };

  const testPriceFetch = async () => {
    try {
      setPriceServiceLoading(true);
      
      const response = await adminAPI.testPriceFetch();
      
      if (response.success) {
        toast({
          title: "Price Fetch Test Successful",
          description: response.message,
        });
      } else {
        toast({
          title: "Price Fetch Test Failed",
          description: response.message,
          variant: "destructive",
        });
      }
      
    } catch (error) {
      console.error('Failed to test price fetch:', error);
      toast({
        title: "Error",
        description: "Failed to test price fetch. Please try again.",
        variant: "destructive",
      });
    } finally {
      setPriceServiceLoading(false);
    }
  };

  // Load data on component mount
  useEffect(() => {
    loadDashboardData();
  }, []);

  // Helper functions
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
      case 'running':
      case 'operational':
        return <CheckCircle className="h-5 w-5 text-green-500" />;
      case 'warning':
      case 'degraded':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
      case 'error':
      case 'offline':
      case 'stopped':
      case 'unhealthy':
        return <XCircle className="h-5 w-5 text-red-500" />;
      case 'not_configured':
        return <AlertTriangle className="h-5 w-5 text-gray-400" />;
      default:
        return <AlertTriangle className="h-5 w-5 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
      case 'running':
      case 'operational':
        return <Badge className="bg-green-100 text-green-800">{status}</Badge>;
      case 'warning':
      case 'degraded':
        return <Badge className="bg-yellow-100 text-yellow-800">{status}</Badge>;
      case 'error':
      case 'offline':
      case 'stopped':
      case 'unhealthy':
        return <Badge className="bg-red-100 text-red-800">{status}</Badge>;
      case 'not_configured':
        return <Badge className="bg-gray-100 text-gray-600">Not Required</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">{status}</Badge>;
    }
  };

  const formatUptime = (uptime: string) => {
    // Parse uptime string and format it nicely
    const match = uptime.match(/(\d+):(\d+):(\d+)/);
    if (match) {
      const [, hours, minutes, seconds] = match;
      return `${hours}h ${minutes}m ${seconds}s`;
    }
    return uptime;
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading dashboard...</div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-600 mt-2">Monitor system health and manage operations</p>
          </div>
          
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => loadDashboardData(true)}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            
            <Button 
              onClick={triggerDataCollection}
              disabled={collectingData}
              className="flex items-center gap-2"
            >
              <Play className="h-4 w-4" />
              {collectingData ? 'Running Pipeline...' : 'Run Pipeline'}
            </Button>
          </div>
        </div>

        {/* System Status Alert */}
        {systemStatus && systemStatus.status !== 'operational' && systemStatus.status !== 'online' && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              System is currently {systemStatus.status}. Some features may be limited.
            </AlertDescription>
          </Alert>
        )}

        {/* System Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Status</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2">
                {systemStatus && getStatusIcon(systemStatus.status)}
                {systemStatus && getStatusBadge(systemStatus.status)}
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                Uptime: {systemStatus ? formatUptime(systemStatus.metrics.uptime) : 'Loading...'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Stocks</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {systemStatus?.metrics.active_stocks || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Stocks being monitored
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Real-Time Prices</CardTitle>
              <Zap className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {systemStatus?.metrics.price_updates || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Live price updates
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Records</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {systemStatus?.metrics.total_records?.toLocaleString() || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Data points collected
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Model Accuracy</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {modelAccuracy ? `${(modelAccuracy.overall_accuracy * 100).toFixed(1)}%` : 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground">
                Overall performance
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Services Status */}
        <Card>
          <CardHeader>
            <CardTitle>Services Status</CardTitle>
            <CardDescription>Current status of system components</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
              {systemStatus?.services && Object.entries(systemStatus.services).map(([service, status]) => (
                <div key={service} className="flex items-center justify-between p-3 border rounded-lg">
                  <div className="flex items-center gap-2">
                    {service === 'database' && <Database className="h-4 w-4" />}
                    {service === 'sentiment_engine' && <BarChart3 className="h-4 w-4" />}
                    {service === 'data_collection' && <Zap className="h-4 w-4" />}
                    {service === 'real_time_prices' && <TrendingUp className="h-4 w-4" />}
                    {service === 'scheduler' && <Activity className="h-4 w-4" />}
                    <span className="capitalize font-medium">
                      {service === 'sentiment_engine' ? 'Sentiment Engine' :
                       service === 'data_collection' ? 'Data Collection' :
                       service === 'real_time_prices' ? 'Real-Time Prices' :
                       service}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(status)}
                    {getStatusBadge(status)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Real-time Price Service Control */}
        {priceServiceStatus && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                Real-time Price Service Control
              </CardTitle>
              <CardDescription>Manage the background stock price fetching service</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">Service Status</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Status:</span>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(priceServiceStatus.service_status.is_running ? 'running' : 'stopped')}
                        <span className={`font-medium ${priceServiceStatus.service_status.is_running ? 'text-green-600' : 'text-red-600'}`}>
                          {priceServiceStatus.service_status.is_running ? 'Running' : 'Stopped'}
                        </span>
                      </div>
                    </div>
                    <div className="flex justify-between">
                      <span>Update Interval:</span>
                      <span className="font-medium">{priceServiceStatus.service_status.update_interval}s</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Market Status:</span>
                      <span className={`font-medium capitalize ${priceServiceStatus.service_status.current_market_status === 'open' ? 'text-green-600' : 'text-red-600'}`}>
                        {priceServiceStatus.service_status.current_market_status}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Active Stocks:</span>
                      <span className="font-medium">{priceServiceStatus.service_status.active_stocks_count}</span>
                    </div>
                    {priceServiceStatus.service_status.next_market_open && (
                      <div className="flex justify-between">
                        <span>Next Market Open:</span>
                        <span className="font-medium text-sm">
                          {new Date(priceServiceStatus.service_status.next_market_open).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-3">Rate Limiting</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Requests/Hour Limit:</span>
                      <span className="font-medium">{priceServiceStatus.service_status.rate_limiting.requests_per_hour}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Current Hour Count:</span>
                      <span className="font-medium">{priceServiceStatus.service_status.rate_limiting.current_hour_count}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Usage:</span>
                      <span className="font-medium">
                        {Math.round((priceServiceStatus.service_status.rate_limiting.current_hour_count / priceServiceStatus.service_status.rate_limiting.requests_per_hour) * 100)}%
                      </span>
                    </div>
                    {priceServiceStatus.service_status.last_request_time && (
                      <div className="flex justify-between">
                        <span>Last Request:</span>
                        <span className="font-medium text-sm">
                          {new Date(priceServiceStatus.service_status.last_request_time).toLocaleString()}
                        </span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
              
              <div className="mt-6 pt-4 border-t">
                <div className="flex gap-3 flex-wrap">
                  {priceServiceStatus.service_status.is_running ? (
                    <Button
                      variant="outline"
                      onClick={() => handlePriceServiceControl('stop')}
                      disabled={priceServiceLoading}
                      className="flex items-center gap-2"
                    >
                      <XCircle className="h-4 w-4" />
                      {priceServiceLoading ? 'Stopping...' : 'Stop Service'}
                    </Button>
                  ) : (
                    <Button
                      onClick={() => handlePriceServiceControl('start')}
                      disabled={priceServiceLoading}
                      className="flex items-center gap-2"
                    >
                      <Play className="h-4 w-4" />
                      {priceServiceLoading ? 'Starting...' : 'Start Service'}
                    </Button>
                  )}
                  
                  <Button
                    variant="outline"
                    onClick={testPriceFetch}
                    disabled={priceServiceLoading}
                    className="flex items-center gap-2"
                  >
                    <Zap className="h-4 w-4" />
                    {priceServiceLoading ? 'Testing...' : 'Test Price Fetch'}
                  </Button>
                  
                  <Button
                    variant="outline"
                    onClick={() => navigate('/admin/scheduler')}
                    className="flex items-center gap-2"
                  >
                    <Settings className="h-4 w-4" />
                    Scheduler Manager
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Model Performance */}
        {modelAccuracy && (
          <Card>
            <CardHeader>
              <CardTitle>Model Performance</CardTitle>
              <CardDescription>
                Last evaluation: {new Date(modelAccuracy.last_evaluation).toLocaleString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h4 className="font-medium mb-3">VADER Sentiment</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Accuracy:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.vader_sentiment.accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Precision:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.vader_sentiment.precision * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Recall:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.vader_sentiment.recall * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>F1 Score:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.vader_sentiment.f1_score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
                
                <div>
                  <h4 className="font-medium mb-3">FinBERT Sentiment</h4>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Accuracy:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.finbert_sentiment.accuracy * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Precision:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.finbert_sentiment.precision * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Recall:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.finbert_sentiment.recall * 100).toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span>F1 Score:</span>
                      <span className="font-medium">{(modelAccuracy.model_metrics.finbert_sentiment.f1_score * 100).toFixed(1)}%</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <div className="mt-4 pt-4 border-t">
                <p className="text-sm text-gray-600">
                  Evaluated on {modelAccuracy.evaluation_samples.toLocaleString()} samples
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Sentiment Analysis Overview */}
        <Card>
          <CardHeader>
            <CardTitle>Sentiment Analysis Overview</CardTitle>
            <CardDescription>Latest sentiment distribution and data storage metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <h4 className="font-medium mb-3">Sentiment Distribution</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                      Positive:
                    </span>
                    <span className="font-medium">{systemStatus?.metrics.sentiment_breakdown?.positive || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                      Neutral:
                    </span>
                    <span className="font-medium">{systemStatus?.metrics.sentiment_breakdown?.neutral || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="flex items-center gap-2">
                      <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                      Negative:
                    </span>
                    <span className="font-medium">{systemStatus?.metrics.sentiment_breakdown?.negative || 0}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Data Storage</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>News Articles:</span>
                    <span className="font-medium">{systemStatus?.metrics.news_articles || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Reddit Posts:</span>
                    <span className="font-medium">{systemStatus?.metrics.reddit_posts || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Price Records:</span>
                    <span className="font-medium">{systemStatus?.metrics.price_records || 0}</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-medium mb-3">Recent Activity</h4>
                <div className="space-y-2">
                  <div className="flex justify-between">
                    <span>Last Collection:</span>
                    <span className="font-medium text-sm">
                      {systemStatus?.metrics.last_collection ? 
                        new Date(systemStatus.metrics.last_collection).toLocaleString() : 
                        'N/A'
                      }
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>Last Price Update:</span>
                    <span className="font-medium text-sm">
                      {systemStatus?.metrics.last_price_update ? 
                        new Date(systemStatus.metrics.last_price_update).toLocaleString() : 
                        'N/A'
                      }
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Actions</CardTitle>
            <CardDescription>Navigate to management pages</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <Button 
                variant="outline" 
                className="h-20 flex flex-col gap-2"
                onClick={() => navigate('/admin/system-logs')}
              >
                <FileText className="h-6 w-6" />
                <span>System Logs</span>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-20 flex flex-col gap-2"
                onClick={() => navigate('/admin/model-accuracy')}
              >
                <BarChart3 className="h-6 w-6" />
                <span>Model Accuracy</span>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-20 flex flex-col gap-2"
                onClick={() => navigate('/admin/api-config')}
              >
                <Settings className="h-6 w-6" />
                <span>API Configuration</span>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-20 flex flex-col gap-2"
                onClick={() => navigate('/admin/watchlist')}
              >
                <Users className="h-6 w-6" />
                <span>Watchlist Manager</span>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-20 flex flex-col gap-2"
                onClick={() => navigate('/admin/storage')}
              >
                <Database className="h-6 w-6" />
                <span>Storage Settings</span>
              </Button>
              
              <Button 
                variant="outline" 
                className="h-20 flex flex-col gap-2"
                onClick={triggerDataCollection}
                disabled={collectingData}
              >
                <Play className="h-6 w-6" />
                <span>{collectingData ? 'Running Pipeline...' : 'Run Pipeline'}</span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Last Collection Info */}
        {systemStatus?.metrics.last_collection && (
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-sm text-gray-600">
                <Activity className="h-4 w-4" />
                <span>
                  Last data collection: {new Date(systemStatus.metrics.last_collection).toLocaleString()}
                </span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  );
};

export default AdminDashboard;