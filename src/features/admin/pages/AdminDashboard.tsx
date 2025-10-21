import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { AdminLayout } from '../../../shared/components/layouts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../shared/components/ui/card';
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
  RefreshCw,
  Play,
  Settings,
  BarChart3,
  Zap,
  Shield,
  Bell,
  Info,
  Clock
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

      // Load all dashboard data in parallel
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

  // Manual full pipeline execution
  const triggerDataCollection = async () => {
    try {
      setCollectingData(true);

      const result = await adminAPI.triggerManualCollection();

      if (result.status === 'success') {
        toast({
          title: "Full Pipeline Completed",
          description: `Successfully processed ${result.execution_summary?.data_collection?.total_items_collected || 0} items through complete pipeline (collection → processing → sentiment → storage)`,
        });
      } else if (result.status === 'partial') {
        toast({
          title: "Pipeline Completed with Issues",
          description: result.message || "Pipeline completed but some steps may have had issues.",
          variant: "destructive",
        });
      } else {
        toast({
          title: "Pipeline Failed",
          description: result.message || "Pipeline execution failed.",
          variant: "destructive",
        });
      }

      // Refresh dashboard after a delay to show updated metrics
      setTimeout(() => {
        loadDashboardData();
      }, 3000);

    } catch (error) {
      console.error('Failed to trigger full pipeline:', error);
      toast({
        title: "Pipeline Error",
        description: "Failed to execute full pipeline. Please try again.",
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
      <div className="space-y-8">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Control Center</h1>
            <p className="text-gray-600 mt-2">Comprehensive monitoring and management dashboard</p>
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
              className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700"
            >
              <Play className="h-4 w-4" />
              {collectingData ? 'Running Pipeline...' : 'Execute Pipeline'}
            </Button>
          </div>
        </div>

        {/* System Overview Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-6">
          <Card className="border-l-4 border-l-blue-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">System Status</CardTitle>
              <Shield className="h-4 w-4 text-blue-500" />
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

          <Card className="border-l-4 border-l-green-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Stocks</CardTitle>
              <TrendingUp className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">
                {systemStatus?.metrics.active_stocks || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Stocks being monitored
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-purple-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Live Updates</CardTitle>
              <Zap className="h-4 w-4 text-purple-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-purple-600">
                {systemStatus?.metrics.price_updates || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Real-time price feeds
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-orange-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Data Records</CardTitle>
              <Database className="h-4 w-4 text-orange-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-orange-600">
                {systemStatus?.metrics.total_records?.toLocaleString() || 0}
              </div>
              <p className="text-xs text-muted-foreground">
                Total data points
              </p>
            </CardContent>
          </Card>

          <Card className="border-l-4 border-l-indigo-500">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sentiment Accuracy</CardTitle>
              <BarChart3 className="h-4 w-4 text-indigo-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-indigo-600">
                {modelAccuracy ? `${(modelAccuracy.overall_accuracy * 100).toFixed(1)}%` : 'N/A'}
              </div>
              <p className="text-xs text-muted-foreground">
                VADER + FinBERT models
              </p>
            </CardContent>
          </Card>
        </div>


        {/* Enhanced Services Status & Control */}
        <Card className="border-2 border-gray-200 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-gray-50 to-slate-50 border-b">
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <Server className="h-5 w-5 text-gray-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Services Management</h3>
                  <p className="text-sm text-gray-600">Monitor and control system components</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => loadDashboardData(true)}
                  disabled={refreshing}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className={`h-3 w-3 ${refreshing ? 'animate-spin' : ''}`} />
                  Refresh
                </Button>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="p-6 space-y-6">
            {/* Services Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {systemStatus?.services && Object.entries(systemStatus.services).map(([service, status]) => {
                const getServiceDetails = (serviceName: string) => {
                  switch (serviceName) {
                    case 'database':
                      return {
                        icon: <Database className="h-6 w-6" />,
                        name: 'Database Engine',
                        description: 'SQLite database with optimized queries and indexing',
                        color: status === 'healthy' ? 'text-green-600' : 'text-red-600',
                        bgColor: status === 'healthy' ? 'bg-green-50' : 'bg-red-50',
                        borderColor: status === 'healthy' ? 'border-green-200' : 'border-red-200',
                        accentColor: 'bg-green-500'
                      };
                    case 'sentiment_engine':
                      return {
                        icon: <BarChart3 className="h-6 w-6" />,
                        name: 'Sentiment Analysis Engine',
                        description: 'VADER & FinBERT models with ensemble prediction',
                        color: status === 'healthy' ? 'text-blue-600' : 'text-yellow-600',
                        bgColor: status === 'healthy' ? 'bg-blue-50' : 'bg-yellow-50',
                        borderColor: status === 'healthy' ? 'border-blue-200' : 'border-yellow-200',
                        accentColor: 'bg-blue-500'
                      };
                    case 'data_collection':
                      return {
                        icon: <Zap className="h-6 w-6" />,
                        name: 'Data Collection Hub',
                        description: 'Multi-source aggregation: Reddit, News, Financial APIs',
                        color: status === 'healthy' ? 'text-purple-600' : 'text-red-600',
                        bgColor: status === 'healthy' ? 'bg-purple-50' : 'bg-red-50',
                        borderColor: status === 'healthy' ? 'border-purple-200' : 'border-red-200',
                        accentColor: 'bg-purple-500'
                      };
                    case 'real_time_prices':
                      return {
                        icon: <TrendingUp className="h-6 w-6" />,
                        name: 'Live Price Feed',
                        description: 'Real-time market data with intelligent rate limiting',
                        color: priceServiceStatus?.service_status?.is_running ? 'text-emerald-600' : 'text-gray-600',
                        bgColor: priceServiceStatus?.service_status?.is_running ? 'bg-emerald-50' : 'bg-gray-50',
                        borderColor: priceServiceStatus?.service_status?.is_running ? 'border-emerald-200' : 'border-gray-200',
                        accentColor: 'bg-emerald-500'
                      };
                    default:
                      return {
                        icon: <Activity className="h-6 w-6" />,
                        name: service.charAt(0).toUpperCase() + service.slice(1),
                        description: 'System service component',
                        color: status === 'healthy' ? 'text-green-600' : 'text-red-600',
                        bgColor: status === 'healthy' ? 'bg-green-50' : 'bg-red-50',
                        borderColor: status === 'healthy' ? 'border-green-200' : 'border-red-200',
                        accentColor: 'bg-gray-500'
                      };
                  }
                };

                const serviceDetails = getServiceDetails(service);

                return (
                  <div
                    key={service}
                    className={`relative p-6 border-2 rounded-xl hover:shadow-xl transition-all duration-300 ${serviceDetails.bgColor} ${serviceDetails.borderColor} group`}
                  >
                    {/* Accent Bar */}
                    <div className={`absolute top-0 left-0 w-full h-1 ${serviceDetails.accentColor} rounded-t-lg`}></div>

                    {/* Service Header */}
                    <div className="flex items-start justify-between mb-4">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-xl bg-white shadow-md group-hover:shadow-lg transition-shadow ${serviceDetails.color}`}>
                          {serviceDetails.icon}
                        </div>
                        <div>
                          <h3 className="font-bold text-lg text-gray-900">{serviceDetails.name}</h3>
                          <p className="text-sm text-gray-600 mt-1 leading-relaxed">{serviceDetails.description}</p>
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        {getStatusIcon(status)}
                        {getStatusBadge(status)}
                      </div>
                    </div>

                    {/* Service Metrics */}
                    <div className="bg-white rounded-xl p-5 shadow-md border border-gray-100">
                      {service === 'real_time_prices' && priceServiceStatus && (
                        <div className="space-y-3">
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Status:</span>
                              <span className={`font-medium ${priceServiceStatus.service_status.is_running ? 'text-green-600' : 'text-red-600'}`}>
                                {priceServiceStatus.service_status.is_running ? 'Running' : 'Stopped'}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Market:</span>
                              <span className={`font-medium capitalize ${priceServiceStatus.service_status.current_market_status === 'open' ? 'text-green-600' : 'text-red-600'}`}>
                                {priceServiceStatus.service_status.current_market_status}
                              </span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Interval:</span>
                              <span className="font-medium">{priceServiceStatus.service_status.update_interval}s</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Rate Usage:</span>
                              <span className="font-medium">
                                {Math.round((priceServiceStatus.service_status.rate_limiting.current_hour_count / priceServiceStatus.service_status.rate_limiting.requests_per_hour) * 100)}%
                              </span>
                            </div>
                          </div>

                          {priceServiceStatus.service_status.next_market_open && (
                            <div className="pt-2 border-t">
                              <div className="flex justify-between text-sm">
                                <span className="text-gray-600">Next Market Open:</span>
                                <span className="font-medium text-blue-600">
                                  {new Date(priceServiceStatus.service_status.next_market_open).toLocaleString('en-MY', {
                                    timeZone: 'Asia/Kuala_Lumpur',
                                    month: 'short',
                                    day: 'numeric',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </span>
                              </div>
                            </div>
                          )}

                          {/* Price Service Controls */}
                          <div className="flex gap-3 pt-4 border-t border-gray-200">
                            {priceServiceStatus.service_status.is_running ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => handlePriceServiceControl('stop')}
                                disabled={priceServiceLoading}
                                className="flex items-center gap-2 text-red-600 border-red-300 hover:bg-red-50 hover:border-red-400 transition-colors"
                              >
                                <XCircle className="h-4 w-4" />
                                {priceServiceLoading ? 'Stopping...' : 'Stop Service'}
                              </Button>
                            ) : (
                              <Button
                                size="sm"
                                onClick={() => handlePriceServiceControl('start')}
                                disabled={priceServiceLoading}
                                className="flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 shadow-md"
                              >
                                <Play className="h-4 w-4" />
                                {priceServiceLoading ? 'Starting...' : 'Start Service'}
                              </Button>
                            )}

                            <Button
                              variant="outline"
                              size="sm"
                              onClick={testPriceFetch}
                              disabled={priceServiceLoading}
                              className="flex items-center gap-2 border-gray-300 hover:bg-gray-50"
                            >
                              <Zap className="h-4 w-4" />
                              Test Fetch
                            </Button>
                          </div>
                        </div>
                      )}

                      {service === 'data_collection' && (
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">API Keys:</span>
                            <span className="font-medium text-green-600">Configured</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Last Collection:</span>
                            <span className="font-medium">
                              {systemStatus?.metrics.last_collection ?
                                new Date(systemStatus.metrics.last_collection).toLocaleString('en-MY', {
                                  timeZone: 'Asia/Kuala_Lumpur',
                                  month: 'short',
                                  day: 'numeric',
                                  hour: '2-digit',
                                  minute: '2-digit'
                                }) :
                                'Never'
                              }
                            </span>
                          </div>

                        </div>
                      )}

                      {service === 'database' && (
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Total Records:</span>
                            <span className="font-medium text-blue-600">{systemStatus?.metrics.total_records?.toLocaleString() || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Active Stocks:</span>
                            <span className="font-medium text-green-600">{systemStatus?.metrics.active_stocks || 0}</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">Price Records:</span>
                            <span className="font-medium text-purple-600">{systemStatus?.metrics.price_records?.toLocaleString() || 0}</span>
                          </div>
                        </div>
                      )}

                      {service === 'sentiment_engine' && modelAccuracy && (
                        <div className="space-y-2 text-sm">
                          <div className="flex justify-between">
                            <span className="text-gray-600">Overall Accuracy:</span>
                            <span className="font-medium text-blue-600">{(modelAccuracy.overall_accuracy * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">VADER Model:</span>
                            <span className="font-medium text-orange-600">{(modelAccuracy.model_metrics.vader_sentiment.accuracy * 100).toFixed(1)}%</span>
                          </div>
                          <div className="flex justify-between">
                            <span className="text-gray-600">FinBERT Model:</span>
                            <span className="font-medium text-green-600">{(modelAccuracy.model_metrics.finbert_sentiment.accuracy * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Global Actions */}
            <div className="flex justify-center pt-6 border-t border-gray-200">
              <div className="flex gap-4">
                <Button
                  variant="outline"
                  onClick={() => navigate('/admin/scheduler')}
                  className="flex items-center gap-2 px-6 py-2 border-gray-300 hover:bg-gray-50"
                >
                  <Settings className="h-4 w-4" />
                  Scheduler Manager
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/admin/logs')}
                  className="flex items-center gap-2 px-6 py-2 border-gray-300 hover:bg-gray-50"
                >
                  <Activity className="h-4 w-4" />
                  System Logs
                </Button>
                <Button
                  variant="outline"
                  onClick={() => navigate('/admin/storage')}
                  className="flex items-center gap-2 px-6 py-2 border-gray-300 hover:bg-gray-50"
                >
                  <Database className="h-4 w-4" />
                  Storage Manager
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>



        {/* Analytics & Performance Overview */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Sentiment Analysis Overview */}
          <Card className="border-2 border-gray-200 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-green-50 to-emerald-50 border-b">
              <CardTitle className="flex items-center gap-3">
                <div className="p-2 bg-green-100 rounded-lg">
                  <BarChart3 className="h-5 w-5 text-green-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Sentiment Analytics</h3>
                  <p className="text-sm text-gray-600">AI-powered sentiment distribution</p>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-4 text-gray-800">Current Distribution</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                      <span className="flex items-center gap-3">
                        <div className="w-4 h-4 bg-green-500 rounded-full shadow-sm"></div>
                        <span className="font-medium text-green-800">Positive Sentiment</span>
                      </span>
                      <span className="font-bold text-green-700 text-lg">{systemStatus?.metrics.sentiment_breakdown?.positive || 0}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <span className="flex items-center gap-3">
                        <div className="w-4 h-4 bg-gray-500 rounded-full shadow-sm"></div>
                        <span className="font-medium text-gray-800">Neutral Sentiment</span>
                      </span>
                      <span className="font-bold text-gray-700 text-lg">{systemStatus?.metrics.sentiment_breakdown?.neutral || 0}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                      <span className="flex items-center gap-3">
                        <div className="w-4 h-4 bg-red-500 rounded-full shadow-sm"></div>
                        <span className="font-medium text-red-800">Negative Sentiment</span>
                      </span>
                      <span className="font-bold text-red-700 text-lg">{systemStatus?.metrics.sentiment_breakdown?.negative || 0}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <h4 className="font-semibold mb-3 text-gray-800">Model Performance</h4>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-blue-50 rounded-lg border border-blue-200">
                      <div className="text-2xl font-bold text-blue-600">
                        {modelAccuracy ? `${(modelAccuracy.model_metrics.vader_sentiment.accuracy * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div className="text-sm text-blue-700 font-medium">VADER</div>
                    </div>
                    <div className="text-center p-3 bg-indigo-50 rounded-lg border border-indigo-200">
                      <div className="text-2xl font-bold text-indigo-600">
                        {modelAccuracy ? `${(modelAccuracy.model_metrics.finbert_sentiment.accuracy * 100).toFixed(1)}%` : 'N/A'}
                      </div>
                      <div className="text-sm text-indigo-700 font-medium">FinBERT</div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Data Storage & Activity */}
          <Card className="border-2 border-gray-200 shadow-lg">
            <CardHeader className="bg-gradient-to-r from-blue-50 to-cyan-50 border-b">
              <CardTitle className="flex items-center gap-3">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Database className="h-5 w-5 text-blue-600" />
                </div>
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">Data Storage</h3>
                  <p className="text-sm text-gray-600">Storage metrics and recent activity</p>
                </div>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-6">
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-4 text-gray-800">Storage Breakdown</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-3 bg-purple-50 rounded-lg border border-purple-200">
                      <span className="font-medium text-purple-800">News Articles</span>
                      <span className="font-bold text-purple-700 text-lg">{systemStatus?.metrics.news_articles?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-orange-50 rounded-lg border border-orange-200">
                      <span className="font-medium text-orange-800">Reddit Posts</span>
                      <span className="font-bold text-orange-700 text-lg">{systemStatus?.metrics.reddit_posts?.toLocaleString() || 0}</span>
                    </div>
                    <div className="flex items-center justify-between p-3 bg-teal-50 rounded-lg border border-teal-200">
                      <span className="font-medium text-teal-800">Price Records</span>
                      <span className="font-bold text-teal-700 text-lg">{systemStatus?.metrics.price_records?.toLocaleString() || 0}</span>
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-gray-200">
                  <h4 className="font-semibold mb-3 text-gray-800">Recent Activity</h4>
                  <div className="space-y-3">
                    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-600">Last Data Collection</span>
                        <Clock className="h-4 w-4 text-gray-400" />
                      </div>
                      <div className="text-sm font-semibold text-gray-800">
                        {systemStatus?.metrics.last_collection ?
                          new Date(systemStatus.metrics.last_collection).toLocaleString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: true
                          }) :
                          'No recent activity'
                        }
                      </div>
                    </div>
                    <div className="p-3 bg-gray-50 rounded-lg border border-gray-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-sm font-medium text-gray-600">Last Price Update</span>
                        <TrendingUp className="h-4 w-4 text-gray-400" />
                      </div>
                      <div className="text-sm font-semibold text-gray-800">
                        {systemStatus?.metrics.last_price_update ?
                          new Date(systemStatus.metrics.last_price_update).toLocaleString('en-US', {
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit',
                            hour12: true
                          }) :
                          'No recent updates'
                        }
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>



      </div>
    </AdminLayout>
  );
};

export default AdminDashboard;