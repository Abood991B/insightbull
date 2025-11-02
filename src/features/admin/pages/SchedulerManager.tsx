import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useToast } from "@/shared/hooks/use-toast";
import { formatDateTime } from "@/shared/utils/timezone";
import { 
  adminAPI, 
  SchedulerResponse, 
  ScheduledJob, 
  JobConfig 
} from "../../../api/services/admin.service";
import { 
  RefreshCw, 
  Clock, 
  Play, 
  Pause, 
  X, 
  Plus,
  Calendar,
  Database,
  TrendingUp,
  Settings,
  AlertTriangle,
  CheckCircle,
  XCircle
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Textarea } from "@/shared/components/ui/textarea";

const SchedulerManager = () => {
  const [schedulerData, setSchedulerData] = useState<SchedulerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [operationLoading, setOperationLoading] = useState<{[key: string]: boolean}>({});
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [newJobConfig, setNewJobConfig] = useState<Partial<JobConfig>>({
    job_type: 'data_collection',
    symbols: [],
    lookback_days: 1
  });
  const { toast } = useToast();

  // Load scheduler data
  const loadSchedulerData = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const data = await adminAPI.getScheduledJobs();
      setSchedulerData(data);
      
      if (showRefreshToast) {
        toast({
          title: "Scheduler Updated",
          description: "Scheduler data has been refreshed.",
        });
      }
    } catch (error) {
      console.error('Failed to load scheduler data:', error);
      toast({
        title: "Error",
        description: "Failed to load scheduler data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Job operations
  const performJobOperation = async (jobId: string, action: 'enable' | 'disable' | 'cancel') => {
    try {
      setOperationLoading(prev => ({ ...prev, [jobId]: true }));
      
      await adminAPI.updateScheduledJob(jobId, action);
      
      toast({
        title: "Job Updated",
        description: `Job ${action}d successfully.`,
      });
      
      // Refresh data
      await loadSchedulerData();
      
    } catch (error) {
      console.error(`Failed to ${action} job:`, error);
      toast({
        title: "Operation Failed",
        description: `Failed to ${action} job. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setOperationLoading(prev => ({ ...prev, [jobId]: false }));
    }
  };

  // Create new job
  const createJob = async () => {
    try {
      if (!newJobConfig.name || !newJobConfig.cron_expression || !newJobConfig.job_type) {
        toast({
          title: "Validation Error",
          description: "Please fill in all required fields.",
          variant: "destructive",
        });
        return;
      }

      await adminAPI.createScheduledJob(newJobConfig as JobConfig);
      
      toast({
        title: "Job Created",
        description: `Scheduled job "${newJobConfig.name}" created successfully.`,
      });
      
      setShowCreateDialog(false);
      setNewJobConfig({
        job_type: 'data_collection',
        symbols: [],
        lookback_days: 1
      });
      
      // Refresh data
      await loadSchedulerData();
      
    } catch (error) {
      console.error('Failed to create job:', error);
      toast({
        title: "Error",
        description: "Failed to create scheduled job. Please try again.",
        variant: "destructive",
      });
    }
  };

  // Refresh all scheduled jobs
  const refreshJobs = async () => {
    try {
      setOperationLoading(prev => ({ ...prev, 'refresh': true }));
      
      await adminAPI.refreshScheduledJobs();
      
      toast({
        title: "Jobs Refreshed",
        description: "All scheduled jobs have been refreshed with updated watchlist.",
      });
      
      // Reload data
      await loadSchedulerData();
      
    } catch (error) {
      console.error('Failed to refresh jobs:', error);
      toast({
        title: "Error",
        description: "Failed to refresh scheduled jobs. Please try again.",
        variant: "destructive",
      });
    } finally {
      setOperationLoading(prev => ({ ...prev, 'refresh': false }));
    }
  };

  useEffect(() => {
    loadSchedulerData();
  }, []);

  // Helper functions
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'running':
        return <Clock className="h-4 w-4 text-blue-500 animate-spin" />;
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />;
      case 'cancelled':
        return <X className="h-4 w-4 text-gray-500" />;
      default:
        return <Clock className="h-4 w-4 text-yellow-500" />;
    }
  };

  const getStatusBadge = (status: string, enabled: boolean) => {
    if (!enabled) {
      return <Badge variant="secondary">Disabled</Badge>;
    }
    
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-800">Completed</Badge>;
      case 'running':
        return <Badge className="bg-blue-100 text-blue-800">Running</Badge>;
      case 'failed':
        return <Badge className="bg-red-100 text-red-800">Failed</Badge>;
      case 'cancelled':
        return <Badge className="bg-gray-100 text-gray-800">Cancelled</Badge>;
      default:
        return <Badge className="bg-yellow-100 text-yellow-800">Pending</Badge>;
    }
  };

  const getJobTypeIcon = (jobType: string) => {
    switch (jobType) {
      case 'data_collection':
        return <Database className="h-4 w-4" />;
      case 'sentiment_analysis':
        return <TrendingUp className="h-4 w-4" />;
      case 'full_pipeline':
        return <Settings className="h-4 w-4" />;
      default:
        return <Clock className="h-4 w-4" />;
    }
  };

  const formatJobType = (jobType: string) => {
    switch (jobType) {
      case 'data_collection':
        return 'Data Collection';
      case 'sentiment_analysis':
        return 'Sentiment Analysis';
      case 'full_pipeline':
        return 'Full Pipeline';
      default:
        return jobType;
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading scheduler data...</div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Scheduler Manager</h1>
            <p className="text-gray-600 mt-2">Manage automated data collection and analysis jobs</p>
          </div>
          
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => loadSchedulerData(true)}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
            
            <Button 
              variant="outline"
              onClick={refreshJobs}
              disabled={operationLoading.refresh}
              className="flex items-center gap-2"
            >
              <Settings className={`h-4 w-4 ${operationLoading.refresh ? 'animate-spin' : ''}`} />
              {operationLoading.refresh ? 'Refreshing Jobs...' : 'Refresh Jobs'}
            </Button>
            
            <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
              <DialogTrigger asChild>
                <Button className="flex items-center gap-2">
                  <Plus className="h-4 w-4" />
                  Create Job
                </Button>
              </DialogTrigger>
              <DialogContent className="sm:max-w-[425px]">
                <DialogHeader>
                  <DialogTitle>Create Scheduled Job</DialogTitle>
                  <DialogDescription>
                    Configure a new automated job for data collection or analysis.
                  </DialogDescription>
                </DialogHeader>
                <div className="grid gap-4 py-4">
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="name" className="text-right">
                      Name
                    </Label>
                    <Input
                      id="name"
                      value={newJobConfig.name || ''}
                      onChange={(e) => setNewJobConfig(prev => ({ ...prev, name: e.target.value }))}
                      className="col-span-3"
                      placeholder="Job name"
                    />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="job_type" className="text-right">
                      Type
                    </Label>
                    <Select 
                      value={newJobConfig.job_type} 
                      onValueChange={(value) => setNewJobConfig(prev => ({ ...prev, job_type: value as any }))}
                    >
                      <SelectTrigger className="col-span-3">
                        <SelectValue placeholder="Select job type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="data_collection">Data Collection</SelectItem>
                        <SelectItem value="sentiment_analysis">Sentiment Analysis</SelectItem>
                        <SelectItem value="full_pipeline">Full Pipeline</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="cron" className="text-right">
                      Schedule
                    </Label>
                    <Input
                      id="cron"
                      value={newJobConfig.cron_expression || ''}
                      onChange={(e) => setNewJobConfig(prev => ({ ...prev, cron_expression: e.target.value }))}
                      className="col-span-3"
                      placeholder="0 6 * * * (daily at 6 AM)"
                    />
                  </div>
                  <div className="grid grid-cols-4 items-center gap-4">
                    <Label htmlFor="symbols" className="text-right">
                      Symbols
                    </Label>
                    <Textarea
                      id="symbols"
                      value={newJobConfig.symbols?.join(', ') || ''}
                      onChange={(e) => setNewJobConfig(prev => ({ 
                        ...prev, 
                        symbols: e.target.value.split(',').map(s => s.trim()).filter(s => s)
                      }))}
                      className="col-span-3"
                      placeholder="AAPL, GOOGL, MSFT (leave empty for watchlist)"
                      rows={2}
                    />
                  </div>
                  {(newJobConfig.job_type === 'data_collection' || newJobConfig.job_type === 'full_pipeline') && (
                    <div className="grid grid-cols-4 items-center gap-4">
                      <Label htmlFor="lookback" className="text-right">
                        Lookback Days
                      </Label>
                      <Input
                        id="lookback"
                        type="number"
                        value={newJobConfig.lookback_days || 1}
                        onChange={(e) => setNewJobConfig(prev => ({ ...prev, lookback_days: parseInt(e.target.value) }))}
                        className="col-span-3"
                        min="1"
                        max="30"
                      />
                    </div>
                  )}
                </div>
                <DialogFooter>
                  <Button type="submit" onClick={createJob}>Create Job</Button>
                </DialogFooter>
              </DialogContent>
            </Dialog>
          </div>
        </div>

        {schedulerData && (
          <>
            {/* Scheduler Status */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="h-5 w-5" />
                  Scheduler Status
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-2">
                    {schedulerData.scheduler_running ? (
                      <CheckCircle className="h-4 w-4 text-green-500" />
                    ) : (
                      <XCircle className="h-4 w-4 text-red-500" />
                    )}
                    <span className="font-medium">
                      {schedulerData.scheduler_running ? 'Running' : 'Stopped'}
                    </span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Total Jobs:</span>
                    <span className="ml-2 font-medium">{schedulerData.total_jobs}</span>
                  </div>
                  <div>
                    <span className="text-sm text-gray-500">Active Jobs:</span>
                    <span className="ml-2 font-medium">
                      {schedulerData.jobs.filter(job => job.enabled).length}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Jobs List */}
            <Card>
              <CardHeader>
                <CardTitle>Scheduled Jobs</CardTitle>
                <CardDescription>Manage your automated data collection and analysis jobs</CardDescription>
              </CardHeader>
              <CardContent>
                {schedulerData.jobs.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No scheduled jobs found. Create your first job to get started.
                  </div>
                ) : (
                  <div className="space-y-4">
                    {schedulerData.jobs.map((job) => (
                      <div key={job.job_id} className="border rounded-lg p-4">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              {getJobTypeIcon(job.job_type)}
                              <h3 className="font-semibold">{job.name}</h3>
                              {getStatusBadge(job.status, job.enabled)}
                            </div>
                            
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 text-sm text-gray-600">
                              <div>
                                <span className="font-medium">Type:</span>
                                <span className="ml-1">{formatJobType(job.job_type)}</span>
                              </div>
                              <div>
                                <span className="font-medium">Schedule:</span>
                                <span className="ml-1 font-mono text-xs">{job.trigger_config.cron}</span>
                              </div>
                              <div>
                                <span className="font-medium">Runs:</span>
                                <span className="ml-1">{job.run_count}</span>
                                {job.error_count > 0 && (
                                  <span className="ml-1 text-red-500">({job.error_count} errors)</span>
                                )}
                              </div>
                              <div>
                                <span className="font-medium">Last Run:</span>
                                <span className="ml-1">
                                  {formatDateTime(job.last_run)}
                                </span>
                              </div>
                            </div>
                            
                            {job.parameters.symbols && job.parameters.symbols.length > 0 && (
                              <div className="mt-2 text-sm text-gray-600">
                                <span className="font-medium">Symbols:</span>
                                <span className="ml-1">{job.parameters.symbols.join(', ')}</span>
                              </div>
                            )}
                            
                            {job.last_error && (
                              <Alert className="mt-2">
                                <AlertTriangle className="h-4 w-4" />
                                <AlertDescription className="text-sm">
                                  Last Error: {job.last_error}
                                </AlertDescription>
                              </Alert>
                            )}
                          </div>
                          
                          <div className="flex gap-2 ml-4">
                            {job.enabled ? (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => performJobOperation(job.job_id, 'disable')}
                                disabled={operationLoading[job.job_id]}
                                className="flex items-center gap-1"
                              >
                                <Pause className="h-3 w-3" />
                                Disable
                              </Button>
                            ) : (
                              <Button
                                variant="outline"
                                size="sm"
                                onClick={() => performJobOperation(job.job_id, 'enable')}
                                disabled={operationLoading[job.job_id]}
                                className="flex items-center gap-1"
                              >
                                <Play className="h-3 w-3" />
                                Enable
                              </Button>
                            )}
                            
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => performJobOperation(job.job_id, 'cancel')}
                              disabled={operationLoading[job.job_id]}
                              className="flex items-center gap-1 text-red-600 hover:text-red-700"
                            >
                              <X className="h-3 w-3" />
                              Cancel
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            {/* Cron Help */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Calendar className="h-5 w-5" />
                  Cron Expression Help
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-medium mb-2">Common Patterns:</h4>
                    <ul className="space-y-1 text-gray-600">
                      <li><code className="bg-gray-100 px-1 rounded">0 6 * * *</code> - Daily at 6 AM</li>
                      <li><code className="bg-gray-100 px-1 rounded">0 */6 * * *</code> - Every 6 hours</li>
                      <li><code className="bg-gray-100 px-1 rounded">0 9-17 * * 1-5</code> - Hourly, 9AM-5PM, weekdays</li>
                      <li><code className="bg-gray-100 px-1 rounded">0 0 * * 0</code> - Weekly on Sunday</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium mb-2">Format:</h4>
                    <p className="text-gray-600 mb-2">
                      <code className="bg-gray-100 px-1 rounded">minute hour day month weekday</code>
                    </p>
                    <ul className="space-y-1 text-gray-600 text-xs">
                      <li>minute: 0-59</li>
                      <li>hour: 0-23</li>
                      <li>day: 1-31</li>
                      <li>month: 1-12</li>
                      <li>weekday: 0-6 (0=Sunday)</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </AdminLayout>
  );
};

export default SchedulerManager;
