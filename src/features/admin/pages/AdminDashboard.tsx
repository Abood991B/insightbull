import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { AdminLayout } from '../../../shared/components/layouts';
import { Card, CardContent, CardHeader, CardTitle } from '../../../shared/components/ui/card';
import { Button } from '../../../shared/components/ui/button';
import { Badge } from '../../../shared/components/ui/badge';
import { Alert, AlertDescription } from '../../../shared/components/ui/alert';
import { Progress } from '../../../shared/components/ui/progress';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "../../../shared/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../../../shared/components/ui/select";
import { Label } from "../../../shared/components/ui/label";
import { useToast } from '../../../shared/hooks/use-toast';
import { formatDateTime } from '@/shared/utils/timezone';
import { adminAPI, SystemStatus, ModelAccuracy, RealTimePriceServiceStatus, PipelineStatus, PipelineProgress, SchedulerHistoryResponse } from '../../../api/services/admin.service';
import { broadcastPipelineEvent } from '@/shared/hooks/usePipelineNotifications';
import SystemHealthAlerts from '../components/SystemHealthAlerts';
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
  Clock,
  Loader2,
  Square,
  Calendar,
  History
} from 'lucide-react';

// Collector Status Interface
interface CollectorStatus {
  name: string;
  status: 'operational' | 'error' | 'warning' | 'not_configured';
  articles?: number;
  posts?: number;
  error?: string;
  lastRun?: string;
}

const AdminDashboard: React.FC = () => {
  const navigate = useNavigate();
  const { toast } = useToast();

  // State management
  const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
  const [modelAccuracy, setModelAccuracy] = useState<ModelAccuracy | null>(null);
  const [priceServiceStatus, setPriceServiceStatus] = useState<RealTimePriceServiceStatus | null>(null);
  const [collectorHealth, setCollectorHealth] = useState<CollectorStatus[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [collectingData, setCollectingData] = useState(false);
  const [priceServiceLoading, setPriceServiceLoading] = useState(false);
  const [collectionDays, setCollectionDays] = useState<string>("1");
  const [isRunDialogOpen, setIsRunDialogOpen] = useState(false);
  
  // Pipeline status tracking
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [pipelineProgress, setPipelineProgress] = useState<PipelineProgress | null>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  
  // Scheduler run history
  const [runHistory, setRunHistory] = useState<SchedulerHistoryResponse | null>(null);

  // Load dashboard data
  const loadDashboardData = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);

      // Load all dashboard data in parallel
      // Use "latest" view type for model accuracy to get recent confidence
      const [statusResponse, accuracyResponse, priceServiceResponse, historyResponse] = await Promise.all([
        adminAPI.getSystemStatus(),
        adminAPI.getModelAccuracy("latest"),
        adminAPI.getRealTimePriceServiceStatus(),
        adminAPI.getSchedulerHistory(7).catch(() => null) // Don't fail if history unavailable
      ]);

      setSystemStatus(statusResponse);
      setModelAccuracy(accuracyResponse);
      setPriceServiceStatus(priceServiceResponse);
      if (historyResponse) {
        setRunHistory(historyResponse);
      }

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

  // Check pipeline status and update progress
  const checkPipelineStatus = useCallback(async () => {
    try {
      const status = await adminAPI.getPipelineStatus();
      setPipelineStatus(status);
      
      if (status.is_running && status.progress) {
        setPipelineProgress(status.progress);
        setCollectingData(true);
      } else if (status.status === 'completed' || status.status === 'failed' || status.status === 'cancelled') {
        // Pipeline finished - stop polling
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        
        // If we were collecting and it just finished, show toast
        if (collectingData) {
          const progress = status.progress;
          if (status.status === 'completed') {
            toast({
              title: "Pipeline Completed",
              description: `Collected ${progress?.items_collected || 0}, analyzed ${progress?.items_analyzed || 0}, stored ${progress?.items_stored || 0} items`,
            });
            
            // Broadcast pipeline completion event
            broadcastPipelineEvent({
              type: 'pipeline_completed',
              summary: {
                analyzed: progress?.items_analyzed || 0,
                stored: progress?.items_stored || 0,
                status: 'success'
              }
            });
            
            // Refresh dashboard data
            loadDashboardData(false);
            updateCollectorHealth();
          } else {
            toast({
              title: status.status === 'failed' ? "Pipeline Failed" : "Pipeline Cancelled",
              description: progress?.message || "Pipeline execution ended",
              variant: "destructive",
            });
          }
          setCollectingData(false);
          setPipelineProgress(null);
        }
      }
    } catch (error) {
      console.error('Failed to check pipeline status:', error);
    }
  }, [collectingData, toast]);

  // Start polling for pipeline status
  const startPipelinePolling = useCallback(() => {
    // Clear any existing interval
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    // Poll every 2 seconds while pipeline is running
    pollingIntervalRef.current = setInterval(checkPipelineStatus, 2000);
    
    // Also check immediately
    checkPipelineStatus();
  }, [checkPipelineStatus]);

  // Stop polling
  const stopPipelinePolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  // Update collector health status
  const updateCollectorHealth = async () => {
    try {
      const response = await adminAPI.getCollectorHealth();
      
      // Transform backend response to match our UI format
      const collectors = response.collectors.map(collector => ({
        name: collector.name,
        status: collector.status,
        articles: collector.source === 'news' ? collector.items_collected : undefined,
        posts: (collector.source === 'hackernews' || collector.source === 'community') ? collector.items_collected : undefined,
        error: collector.error,
        lastRun: collector.last_run,
      }));
      
      setCollectorHealth(collectors);
    } catch (error) {
      console.error('Failed to fetch collector health:', error);
      // Fallback to empty array on error
      setCollectorHealth([]);
    }
  };

  // Manual full pipeline execution (non-blocking)
  const triggerDataCollection = () => {
    setCollectingData(true);
    setIsRunDialogOpen(false);
    
    toast({
      title: "Pipeline Started",
      description: "Data collection pipeline is running. Progress will be shown below.",
    });

    // Start polling for status updates
    startPipelinePolling();

    // Fire and forget - don't await, let polling handle status updates
    adminAPI.triggerManualCollection({ days_back: parseInt(collectionDays) })
      .catch(error => {
        console.error('Pipeline failed:', error);
        stopPipelinePolling();
        setCollectingData(false);
        setPipelineProgress(null);
        toast({
          title: "Pipeline Error",
          description: error.message || "Pipeline execution failed.",
          variant: "destructive",
        });
      });
  };

  // Cancel pipeline
  const cancelPipeline = async () => {
    try {
      await adminAPI.stopPipeline();
      toast({
        title: "Pipeline Cancelled",
        description: "Pipeline execution has been cancelled.",
      });
    } catch (error) {
      console.error('Failed to cancel pipeline:', error);
      toast({
        title: "Error",
        description: "Failed to cancel pipeline.",
        variant: "destructive",
      });
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
    updateCollectorHealth();
    
    // Check if pipeline is already running on mount
    checkPipelineStatus();
    
    // Cleanup polling on unmount
    return () => {
      stopPipelinePolling();
    };
  }, []);

  // Auto-refresh dashboard data every 30 seconds (catches pipeline completion)
  useEffect(() => {
    const refreshInterval = setInterval(() => {
      // Only auto-refresh if not currently collecting data or refreshing
      if (!collectingData && !refreshing) {
        loadDashboardData(false); // Silent refresh (no toast)
        updateCollectorHealth();
      }
    }, 30000); // 30 seconds

    return () => clearInterval(refreshInterval);
  }, [collectingData, refreshing]);

  // Start/stop pipeline status polling based on collectingData state
  useEffect(() => {
    if (collectingData) {
      startPipelinePolling();
    } else {
      stopPipelinePolling();
    }
  }, [collectingData, startPipelinePolling, stopPipelinePolling]);

  // Refetch when user switches back to admin tab (visibility detection)
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && !loading) {
        loadDashboardData(false); // Silent refresh
        updateCollectorHealth();
        // Check pipeline status when returning to tab
        checkPipelineStatus();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
  }, [loading, checkPipelineStatus]);

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
        {/* Header - Compact */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
            <p className="text-gray-500 text-sm">System monitoring and control</p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadDashboardData(true)}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-1.5 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>

            <Dialog open={isRunDialogOpen} onOpenChange={setIsRunDialogOpen}>
              <DialogTrigger asChild>
                <Button
                  size="sm"
                  disabled={collectingData}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Play className="h-4 w-4 mr-1.5" />
                  {collectingData ? 'Running...' : 'Run Pipeline'}
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Run Data Pipeline</DialogTitle>
                  <DialogDescription>
                    Manually trigger the data collection and analysis pipeline.
                    Choose a timeframe to look back for news and data.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="timeframe" className="text-right">
                      Timeframe
                    </Label>
                    <Select
                      value={collectionDays}
                      onValueChange={setCollectionDays}
                    >
                      <SelectTrigger className="col-span-3">
                        <SelectValue placeholder="Select timeframe" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="1">Last 24 Hours</SelectItem>
                        <SelectItem value="3">Last 3 Days</SelectItem>
                        <SelectItem value="7">Last 7 Days</SelectItem>
                        <SelectItem value="30">Last 30 Days</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
                <DialogFooter>
                  <Button variant="outline" onClick={() => setIsRunDialogOpen(false)}>Cancel</Button>
                  <Button onClick={triggerDataCollection} disabled={collectingData}>
                    {collectingData ? (
                      <>
                        <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                        Running...
                      </>
                    ) : (
                      <>
                        <Play className="mr-2 h-4 w-4" />
                        Start Pipeline
                      </>
                    )}
                  </Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {/* Pipeline Progress Bar - Shows when pipeline is running */}
        {collectingData && pipelineProgress && (
          <Card className="border-blue-200 bg-blue-50/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
                  <span className="font-medium text-blue-900">Pipeline Running</span>
                  <Badge variant="outline" className="bg-blue-100 text-blue-700 border-blue-300">
                    {pipelineProgress.current_stage}
                  </Badge>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-sm text-blue-700 font-medium">
                    {pipelineProgress.overall_progress}%
                  </span>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={cancelPipeline}
                    className="h-7 px-2 text-red-600 border-red-300 hover:bg-red-50"
                  >
                    <Square className="h-3 w-3 mr-1" />
                    Cancel
                  </Button>
                </div>
              </div>
              <Progress value={pipelineProgress.overall_progress} className="h-2 mb-2" />
              <div className="flex justify-between text-xs text-blue-700">
                <span>{pipelineProgress.message}</span>
                <div className="flex gap-4">
                  <span>Collected: {pipelineProgress.items_collected}</span>
                  <span>Analyzed: {pipelineProgress.items_analyzed}</span>
                  <span>Stored: {pipelineProgress.items_stored}</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* System Health Alerts - Compact */}
        <SystemHealthAlerts
          systemStatus={systemStatus}
          modelAccuracy={modelAccuracy}
          onRefresh={() => loadDashboardData(false)}
          compact={true}
        />

        {/* Quick Stats Row */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {/* System Status */}
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className={`p-2 rounded-lg ${systemStatus?.status === 'operational' ? 'bg-green-100' : 'bg-yellow-100'}`}>
                <Shield className={`h-5 w-5 ${systemStatus?.status === 'operational' ? 'text-green-600' : 'text-yellow-600'}`} />
              </div>
              <div>
                <p className="text-xs text-gray-500">Status</p>
                <p className={`font-semibold ${systemStatus?.status === 'operational' ? 'text-green-600' : 'text-yellow-600'}`}>
                  {systemStatus?.status === 'operational' ? 'Online' : systemStatus?.status || 'N/A'}
                </p>
              </div>
            </div>
          </Card>

          {/* Active Stocks */}
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-blue-100">
                <TrendingUp className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Stocks</p>
                <p className="font-semibold text-blue-600">{systemStatus?.metrics.active_stocks || 0}</p>
              </div>
            </div>
          </Card>

          {/* Total Records */}
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-purple-100">
                <Database className="h-5 w-5 text-purple-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Records</p>
                <p className="font-semibold text-purple-600">{systemStatus?.metrics.total_records?.toLocaleString() || 0}</p>
              </div>
            </div>
          </Card>

          {/* Model Confidence (Latest) */}
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-indigo-100">
                <BarChart3 className="h-5 w-5 text-indigo-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Confidence</p>
                <p className="font-semibold text-indigo-600">
                  {modelAccuracy?.overall_confidence ? `${(modelAccuracy.overall_confidence * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </div>
            </div>
          </Card>

          {/* Price Updates */}
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-emerald-100">
                <Zap className="h-5 w-5 text-emerald-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Price Updates</p>
                <p className="font-semibold text-emerald-600">{systemStatus?.metrics.price_updates || 0}</p>
              </div>
            </div>
          </Card>

          {/* Uptime */}
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-orange-100">
                <Clock className="h-5 w-5 text-orange-600" />
              </div>
              <div>
                <p className="text-xs text-gray-500">Uptime</p>
                <p className="font-semibold text-orange-600 text-sm">
                  {systemStatus ? formatUptime(systemStatus.metrics.uptime) : 'N/A'}
                </p>
              </div>
            </div>
          </Card>
        </div>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Left Column - Data Collectors */}
          <Card className="lg:col-span-2">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <CardTitle className="text-base flex items-center gap-2">
                  <Database className="h-4 w-4 text-blue-600" />
                  Data Collectors
                </CardTitle>
                <Button variant="ghost" size="sm" onClick={updateCollectorHealth}>
                  <RefreshCw className="h-3 w-3" />
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {collectorHealth.some(c => c.status === 'error') && (
                <Alert className="mb-4 py-2 bg-red-50 border-red-200">
                  <AlertTriangle className="h-3 w-3 text-red-600" />
                  <AlertDescription className="text-xs text-red-700">
                    {collectorHealth.find(c => c.status === 'error')?.name} unavailable
                  </AlertDescription>
                </Alert>
              )}
              
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {collectorHealth.map((collector) => {
                  const styles: Record<string, { emoji: string; bg: string; border: string }> = {
                    hackernews: { emoji: '🔶', bg: 'bg-orange-50', border: 'border-orange-200' },
                    gdelt: { emoji: '🌐', bg: 'bg-blue-50', border: 'border-blue-200' },
                    finnhub: { emoji: '📊', bg: 'bg-indigo-50', border: 'border-indigo-200' },
                    finhub: { emoji: '📊', bg: 'bg-indigo-50', border: 'border-indigo-200' },
                    newsapi: { emoji: '📰', bg: 'bg-purple-50', border: 'border-purple-200' },
                  };
                  const style = styles[collector.name.toLowerCase()] || { emoji: '📡', bg: 'bg-gray-50', border: 'border-gray-200' };
                  
                  return (
                    <div
                      key={collector.name}
                      className={`relative p-3 rounded-lg border ${
                        collector.status === 'operational' ? `${style.bg} ${style.border}` : 'bg-red-50 border-red-200'
                      }`}
                    >
                      <div className={`absolute top-2 right-2 h-2 w-2 rounded-full ${
                        collector.status === 'operational' ? 'bg-green-500' : 'bg-red-500'
                      }`} />
                      <div className="flex items-center gap-1.5 mb-1">
                        <span className="text-sm">{style.emoji}</span>
                        <span className="font-medium text-xs text-gray-800">{collector.name}</span>
                      </div>
                      <p className="text-lg font-bold text-gray-900">
                        {collector.articles ?? collector.posts ?? 0}
                      </p>
                      <p className="text-[10px] text-gray-500">
                        {collector.posts !== undefined ? 'posts' : 'articles'}
                      </p>
                    </div>
                  );
                })}
              </div>
              
              <div className="mt-3 pt-3 border-t flex justify-between items-center text-xs">
                <span className="text-gray-500">
                  <span className="inline-block w-2 h-2 rounded-full bg-green-500 mr-1"></span>
                  {collectorHealth.filter(c => c.status === 'operational').length}/{collectorHealth.length} operational
                </span>
                <span className="text-gray-500">
                  Coverage: {collectorHealth.length > 0 ? Math.round((collectorHealth.filter(c => c.status === 'operational').length / collectorHealth.length) * 100) : 0}%
                </span>
              </div>
            </CardContent>
          </Card>

          {/* Right Column - Sentiment Distribution */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-base flex items-center gap-2">
                <BarChart3 className="h-4 w-4 text-green-600" />
                Sentiment Distribution
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center justify-between p-2 bg-green-50 rounded-lg">
                <span className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                  Positive
                </span>
                <span className="font-bold text-green-700">{systemStatus?.metrics.sentiment_breakdown?.positive || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-gray-50 rounded-lg">
                <span className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 bg-gray-500 rounded-full"></div>
                  Neutral
                </span>
                <span className="font-bold text-gray-700">{systemStatus?.metrics.sentiment_breakdown?.neutral || 0}</span>
              </div>
              <div className="flex items-center justify-between p-2 bg-red-50 rounded-lg">
                <span className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  Negative
                </span>
                <span className="font-bold text-red-700">{systemStatus?.metrics.sentiment_breakdown?.negative || 0}</span>
              </div>
              
              <div className="pt-3 border-t">
                <p className="text-xs text-gray-500 mb-2">Model Confidence</p>
                <div className="grid grid-cols-1 gap-2">
                  <div className="text-center p-2 bg-blue-50 rounded-lg">
                    <p className="text-lg font-bold text-blue-600">
                      {modelAccuracy?.overall_confidence ? `${(modelAccuracy.overall_confidence * 100).toFixed(1)}%` : 'N/A'}
                    </p>
                    <p className="text-[10px] text-blue-600">Latest Pipeline Confidence</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Services Row */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <Server className="h-4 w-4 text-gray-600" />
                System Services
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Database */}
              <div className={`p-4 rounded-lg border-2 ${
                systemStatus?.services?.database === 'healthy' ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Database className={`h-4 w-4 ${systemStatus?.services?.database === 'healthy' ? 'text-green-600' : 'text-red-600'}`} />
                    <span className="font-medium text-sm">Database</span>
                  </div>
                  {getStatusIcon(systemStatus?.services?.database || 'unknown')}
                </div>
                <p className="text-xs text-gray-600">Records: {systemStatus?.metrics.total_records?.toLocaleString() || 0}</p>
              </div>

              {/* Sentiment Engine */}
              <div className={`p-4 rounded-lg border-2 ${
                systemStatus?.services?.sentiment_engine === 'healthy' ? 'bg-blue-50 border-blue-200' : 'bg-yellow-50 border-yellow-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <BarChart3 className={`h-4 w-4 ${systemStatus?.services?.sentiment_engine === 'healthy' ? 'text-blue-600' : 'text-yellow-600'}`} />
                    <span className="font-medium text-sm">Sentiment</span>
                  </div>
                  {getStatusIcon(systemStatus?.services?.sentiment_engine || 'unknown')}
                </div>
                <p className="text-xs text-gray-600">
                  Confidence: {modelAccuracy?.overall_confidence ? `${(modelAccuracy.overall_confidence * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </div>

              {/* Data Collection */}
              <div className={`p-4 rounded-lg border-2 ${
                systemStatus?.services?.data_collection === 'healthy' ? 'bg-purple-50 border-purple-200' : 'bg-red-50 border-red-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Zap className={`h-4 w-4 ${systemStatus?.services?.data_collection === 'healthy' ? 'text-purple-600' : 'text-red-600'}`} />
                    <span className="font-medium text-sm">Collection</span>
                  </div>
                  {getStatusIcon(systemStatus?.services?.data_collection || 'unknown')}
                </div>
                <p className="text-xs text-gray-600">
                  Last: {systemStatus?.metrics.last_collection 
                    ? formatDateTime(systemStatus.metrics.last_collection, { hour: '2-digit', minute: '2-digit' })
                    : 'Never'}
                </p>
              </div>

              {/* Price Service */}
              <div className={`p-4 rounded-lg border-2 ${
                priceServiceStatus?.service_status?.is_running ? 'bg-emerald-50 border-emerald-200' : 'bg-gray-50 border-gray-200'
              }`}>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <TrendingUp className={`h-4 w-4 ${priceServiceStatus?.service_status?.is_running ? 'text-emerald-600' : 'text-gray-500'}`} />
                    <span className="font-medium text-sm">Prices</span>
                  </div>
                  {priceServiceStatus?.service_status?.is_running 
                    ? <CheckCircle className="h-4 w-4 text-green-500" />
                    : <XCircle className="h-4 w-4 text-gray-400" />
                  }
                </div>
                <div className="flex gap-1">
                  <Button
                    size="sm"
                    variant={priceServiceStatus?.service_status?.is_running ? "outline" : "default"}
                    className="h-6 text-xs px-2"
                    onClick={() => handlePriceServiceControl(priceServiceStatus?.service_status?.is_running ? 'stop' : 'start')}
                    disabled={priceServiceLoading}
                  >
                    {priceServiceStatus?.service_status?.is_running ? 'Stop' : 'Start'}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline"
                    className="h-6 text-xs px-2"
                    onClick={testPriceFetch}
                    disabled={priceServiceLoading}
                  >
                    Test
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Pipeline Run History */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base flex items-center gap-2">
                <History className="h-4 w-4 text-indigo-600" />
                Pipeline Run History (7 Days)
              </CardTitle>
              {runHistory?.summary && (
                <div className="flex gap-2">
                  <Badge variant="outline" className="text-xs">
                    {runHistory.summary.total_runs} runs
                  </Badge>
                  <Badge className="bg-green-100 text-green-800 text-xs">
                    {runHistory.summary.successful_runs} success
                  </Badge>
                  {runHistory.summary.failed_runs > 0 && (
                    <Badge className="bg-red-100 text-red-800 text-xs">
                      {runHistory.summary.failed_runs} failed
                    </Badge>
                  )}
                </div>
              )}
            </div>
          </CardHeader>
          <CardContent>
            {!runHistory || Object.keys(runHistory.history).length === 0 ? (
              <div className="text-center py-6 text-gray-500">
                <Calendar className="h-8 w-8 mx-auto mb-2 text-gray-400" />
                <p className="text-sm">No pipeline runs recorded yet</p>
                <p className="text-xs mt-1">Run the pipeline to start tracking history</p>
              </div>
            ) : (
              <div className="space-y-3">
                {Object.entries(runHistory.history)
                  .sort(([a], [b]) => b.localeCompare(a)) // Sort by date descending
                  .slice(0, 3) // Show last 3 days
                  .map(([date, jobs]) => {
                    const totalRuns = Object.values(jobs).reduce((sum, runs) => sum + runs.length, 0);
                    const successRuns = Object.values(jobs).reduce(
                      (sum, runs) => sum + runs.filter(r => r.status === 'completed').length, 0
                    );
                    const failedRuns = totalRuns - successRuns;
                    
                    return (
                      <div key={date} className="border rounded-lg p-3">
                        <div className="flex items-center justify-between mb-2">
                          <span className="font-medium text-sm">{date}</span>
                          <div className="flex gap-1">
                            <Badge variant="outline" className="text-xs">{totalRuns} runs</Badge>
                            {successRuns > 0 && (
                              <Badge className="bg-green-100 text-green-800 text-xs">{successRuns} ✓</Badge>
                            )}
                            {failedRuns > 0 && (
                              <Badge className="bg-red-100 text-red-800 text-xs">{failedRuns} ✗</Badge>
                            )}
                          </div>
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2">
                          {Object.entries(jobs).map(([jobName, runs]) => (
                            <div key={jobName} className="text-xs p-2 bg-gray-50 rounded">
                              <div className="font-medium truncate" title={jobName}>
                                {jobName.replace(' Updates', '').replace(' Analysis', '').replace(' Preparation', '')}
                              </div>
                              <div className="flex items-center gap-1 mt-1">
                                <span className="text-green-600">{runs.filter(r => r.status === 'completed').length}✓</span>
                                {runs.filter(r => r.status !== 'completed').length > 0 && (
                                  <span className="text-red-600">{runs.filter(r => r.status !== 'completed').length}✗</span>
                                )}
                                {runs.length > 0 && (
                                  <span className="text-gray-400 ml-auto">
                                    {Math.round(runs.reduce((s, r) => s + r.duration_seconds, 0) / runs.length)}s avg
                                  </span>
                                )}
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                {runHistory.summary && (
                  <div className="flex items-center justify-between pt-2 border-t text-xs text-gray-500">
                    <span>Avg duration: {runHistory.summary.avg_duration_seconds.toFixed(1)}s</span>
                    <Button 
                      variant="link" 
                      size="sm" 
                      className="h-auto p-0 text-xs"
                      onClick={() => navigate('/admin/scheduler')}
                    >
                      View Full History →
                    </Button>
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Navigation */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <Button variant="outline" onClick={() => navigate('/admin/scheduler')} className="h-auto py-3 flex-col gap-1">
            <Settings className="h-5 w-5 text-gray-600" />
            <span className="text-xs">Scheduler</span>
          </Button>
          <Button variant="outline" onClick={() => navigate('/admin/logs')} className="h-auto py-3 flex-col gap-1">
            <Activity className="h-5 w-5 text-gray-600" />
            <span className="text-xs">Logs</span>
          </Button>
          <Button variant="outline" onClick={() => navigate('/admin/storage')} className="h-auto py-3 flex-col gap-1">
            <Database className="h-5 w-5 text-gray-600" />
            <span className="text-xs">Storage</span>
          </Button>
          <Button variant="outline" onClick={() => navigate('/admin/model-accuracy')} className="h-auto py-3 flex-col gap-1">
            <BarChart3 className="h-5 w-5 text-gray-600" />
            <span className="text-xs">Benchmark</span>
          </Button>
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminDashboard;