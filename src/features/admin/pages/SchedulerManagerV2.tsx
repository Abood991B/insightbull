/**
 * Scheduler Manager V2 - Smart Preset Scheduling
 * ==============================================
 * 
 * Improved scheduler UI with:
 * - Human-readable preset schedules (no raw cron)
 * - Atomic pipeline execution (data collection + sentiment analysis together)
 * - Next run timeline visualization
 * - Collector health monitoring (MarketAux API failure handling)
 * - Market context awareness
 * 
 * Aligns with FYP-Report.md Section 4 (System Design) and Section 7 (Implementation Plan)
 */

import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useToast } from "@/shared/hooks/use-toast";
import { formatDateTime, USER_TIMEZONE } from "@/shared/utils/timezone";
import { MarketCountdown } from "@/shared/components/MarketCountdown";
import { 
  adminAPI, 
  SchedulerResponse, 
  ScheduledJob 
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
  AlertTriangle,
  CheckCircle,
  XCircle,
  Sun,
  Moon,
  Sunrise,
  Sunset,
  CloudOff,
  Activity,
  BarChart3,
  Zap
} from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/shared/components/ui/dialog";

// ============================================================================
// Types & Interfaces
// ============================================================================

interface PresetSchedule {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  schedule: string; // Human-readable schedule
  cronExpression: string;
  jobType: 'full_pipeline'; // Always full pipeline (atomic execution)
  enabled: boolean;
  color: string;
  marketContext: 'pre-market' | 'market-hours' | 'after-hours' | 'weekend';
  rationale: string; // Why this schedule exists
}

interface CollectorStatus {
  name: string;
  status: 'success' | 'failed' | 'unknown';
  articles?: number;
  posts?: number;
  error?: string;
  lastRun?: string;
}

interface TimelineEvent {
  jobId: string;
  jobName: string;
  scheduledTime: Date;
  type: 'pre-market' | 'market-hours' | 'after-hours' | 'weekend' | 'overnight';
  color: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Convert ET time to user's local timezone for display
 * Uses proper timezone conversion accounting for DST differences
 */
const convertETTimeToUserTimezone = (etHour: number, etMinute: number = 0): string => {
  // Create a date in the user's current timezone
  const now = new Date();
  
  // Create a date representing the ET time
  // We'll use a formatter to get the current ET time and adjust from there
  const etFormatter = new Intl.DateTimeFormat('en-US', {
    timeZone: 'America/New_York',
    hour: 'numeric',
    minute: 'numeric',
    hour12: false
  });
  
  // Parse current ET time to understand offset
  const etNowParts = etFormatter.formatToParts(now);
  const currentETHour = parseInt(etNowParts.find(p => p.type === 'hour')?.value || '0');
  const currentETMinute = parseInt(etNowParts.find(p => p.type === 'minute')?.value || '0');
  
  // Calculate hour difference from current ET time to target ET time
  const hourDiff = etHour - currentETHour;
  const minuteDiff = etMinute - currentETMinute;
  
  // Apply that difference to the current UTC time
  const targetDate = new Date(now);
  targetDate.setHours(targetDate.getHours() + hourDiff);
  targetDate.setMinutes(targetDate.getMinutes() + minuteDiff);
  
  // Format in user's timezone
  return targetDate.toLocaleTimeString("en-US", {
    hour: 'numeric',
    minute: etMinute > 0 ? '2-digit' : undefined,
    hour12: true,
    timeZone: USER_TIMEZONE,
  });
};

/**
 * Get timezone abbreviation for user's timezone
 */
const getUserTimezoneAbbr = (): string => {
  const now = new Date();
  const formatted = now.toLocaleTimeString("en-US", {
    timeZone: USER_TIMEZONE,
    timeZoneName: 'short'
  });
  const match = formatted.match(/\b([A-Z]{3,4})\b/);
  return match ? match[1] : '';
};

// ============================================================================
// Preset Schedule Configurations
// ============================================================================

const timezoneName = getUserTimezoneAbbr();

const PRESET_SCHEDULES: PresetSchedule[] = [
  {
    id: 'pre-market',
    name: 'Pre-Market Preparation',
    description: 'Full pipeline run before market opens',
    icon: <Sunrise className="h-5 w-5" />,
    schedule: `Daily at ${convertETTimeToUserTimezone(8)} ${timezoneName} (Mon-Fri)`,
    cronExpression: '0 13 * * 1-5', // 8:00 AM ET = 13:00 UTC (Standard Time)
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-amber-500',
    marketContext: 'pre-market',
    rationale: 'Collect overnight news and sentiment BEFORE market opens. Gives traders fresh insights for the market opening bell.'
  },
  {
    id: 'market-active',
    name: 'Active Trading Updates',
    description: 'Frequent updates during market hours',
    icon: <Activity className="h-5 w-5" />,
    schedule: `Every 30 minutes (${convertETTimeToUserTimezone(9, 30)} - ${convertETTimeToUserTimezone(16)} ${timezoneName}, Mon-Fri)`,
    cronExpression: '*/30 14-20 * * 1-5', // 9:30 AM-4:00 PM ET = 14:30-20:59 UTC (Standard Time) - runs at :00 and :30
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-green-500',
    marketContext: 'market-hours',
    rationale: 'Monitor real-time sentiment shifts during active trading. Catches breaking news and social media reactions immediately.'
  },
  {
    id: 'after-hours-evening',
    name: 'After-Hours Analysis',
    description: `Post-market sentiment at ${convertETTimeToUserTimezone(17)} ${timezoneName}`,
    icon: <Sunset className="h-5 w-5" />,
    schedule: `Daily at ${convertETTimeToUserTimezone(17)} ${timezoneName} (Mon-Fri)`,
    cronExpression: '0 22 * * 1-5', // 5:00 PM ET = 22:00 UTC (Standard Time)
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-orange-500',
    marketContext: 'after-hours',
    rationale: 'Capture immediate post-market news and earnings reports. Critical for after-hours trading sentiment.'
  },
  {
    id: 'after-hours-late',
    name: 'After-Hours Late Evening',
    description: `Late evening sentiment at ${convertETTimeToUserTimezone(20)} ${timezoneName}`,
    icon: <Moon className="h-5 w-5" />,
    schedule: `Daily at ${convertETTimeToUserTimezone(20)} ${timezoneName} (Mon-Fri)`,
    cronExpression: '0 1 * * 2-6', // 8:00 PM ET Mon-Fri = 01:00 UTC Tue-Sat (Standard Time)
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-indigo-500',
    marketContext: 'after-hours',
    rationale: 'Late evening news catch-up. Ensures comprehensive coverage of extended hours activity and breaking news.'
  },
  {
    id: 'weekend-deep',
    name: 'Weekend Deep Analysis',
    description: 'Comprehensive weekly analysis',
    icon: <BarChart3 className="h-5 w-5" />,
    schedule: `Saturday at ${convertETTimeToUserTimezone(10)} ${timezoneName}`,
    cronExpression: '0 15 * * 6', // Saturday 10:00 AM ET = 15:00 UTC (Standard Time)
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-blue-500',
    marketContext: 'weekend',
    rationale: 'Weekly comprehensive analysis. Process accumulated weekend news to prepare for Monday market open.'
  }
];

// ============================================================================
// Main Component
// ============================================================================

const SchedulerManagerV2 = () => {
  const [schedulerData, setSchedulerData] = useState<SchedulerResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [operationLoading, setOperationLoading] = useState<{[key: string]: boolean}>({});
  const [presetSchedules, setPresetSchedules] = useState<PresetSchedule[]>(PRESET_SCHEDULES);
  const [collectorHealth, setCollectorHealth] = useState<CollectorStatus[]>([]);
  const [timelineEvents, setTimelineEvents] = useState<TimelineEvent[]>([]);
  const [marketStatus, setMarketStatus] = useState<{
    isOpen: boolean;
    currentPeriod: string;
    nextOpen: string | null;
    nextClose: string | null;
  }>({
    isOpen: false,
    currentPeriod: 'unknown',
    nextOpen: null,
    nextClose: null
  });
  const { toast } = useToast();

  // ============================================================================
  // Data Loading
  // ============================================================================

  const loadSchedulerData = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const data = await adminAPI.getScheduledJobs();
      setSchedulerData(data);
      
      // Update market status
      updateMarketStatus();
      
      // Build timeline from scheduled jobs
      buildTimeline(data.jobs || []);
      
      // Fetch collector health from backend API
      updateCollectorHealth();
      
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

  useEffect(() => {
    loadSchedulerData();
    // Auto-refresh scheduler data every 30 seconds
    const schedulerInterval = setInterval(() => loadSchedulerData(), 30000);
    
    // Update market status every 10 seconds (backend fetches real data)
    const marketInterval = setInterval(() => updateMarketStatus(), 10000);
    
    return () => {
      clearInterval(schedulerInterval);
      clearInterval(marketInterval);
    };
  }, []);

  // ============================================================================
  // Market Status & Timeline
  // ============================================================================

  const updateMarketStatus = async () => {
    try {
      const status = await adminAPI.getMarketStatus();
      
      // Format next open time for display
      let nextOpenDisplay = null;
      if (status.next_open) {
        const nextOpen = new Date(status.next_open);
        nextOpenDisplay = nextOpen.toLocaleString("en-US", { 
          weekday: 'short', 
          month: 'short', 
          day: 'numeric', 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: true,
          timeZone: USER_TIMEZONE,
          timeZoneName: 'short'
        });
      }
      
      let nextCloseDisplay = null;
      if (status.next_close) {
        const nextClose = new Date(status.next_close);
        nextCloseDisplay = nextClose.toLocaleString("en-US", { 
          weekday: 'short', 
          month: 'short', 
          day: 'numeric', 
          hour: '2-digit', 
          minute: '2-digit',
          hour12: true,
          timeZone: USER_TIMEZONE,
          timeZoneName: 'short'
        });
      }
      
      setMarketStatus({
        isOpen: status.is_open,
        currentPeriod: status.current_period,
        nextOpen: nextOpenDisplay,
        nextClose: nextCloseDisplay
      });
    } catch (error) {
      console.error('Failed to update market status:', error);
      // Keep existing status on error
    }
  };


  const buildTimeline = (jobs: ScheduledJob[]) => {
    const now = new Date();
    const next48Hours = new Date(now.getTime() + 48 * 60 * 60 * 1000);
    
    const events: TimelineEvent[] = jobs
      .filter(job => {
        if (!job.next_run) return false;
        const nextRunDate = new Date(job.next_run);
        if (isNaN(nextRunDate.getTime())) return false;
        return nextRunDate > now && nextRunDate <= next48Hours;
      })
      .map(job => {
        const scheduledTime = new Date(job.next_run!);
        const hour = scheduledTime.getHours();
        
        let type: TimelineEvent['type'] = 'overnight';
        let color = 'bg-gray-500';
        
        if (scheduledTime.getDay() === 0 || scheduledTime.getDay() === 6) {
          type = 'weekend';
          color = 'bg-blue-500';
        } else if (hour >= 7 && hour < 9) {
          type = 'pre-market';
          color = 'bg-amber-500';
        } else if (hour >= 9 && hour < 16) {
          type = 'market-hours';
          color = 'bg-green-500';
        } else if (hour >= 16 && hour < 20) {
          type = 'after-hours';
          color = 'bg-orange-500';
        }
        
        return {
          jobId: job.job_id,
          jobName: job.name,
          scheduledTime,
          type,
          color
        };
      })
      .sort((a, b) => a.scheduledTime.getTime() - b.scheduledTime.getTime());
    
    setTimelineEvents(events);
  };

  const updateCollectorHealth = async () => {
    try {
      const response = await adminAPI.getCollectorHealth();
      
      // Transform backend response to match our UI format
      const collectors: CollectorStatus[] = response.collectors.map(collector => {
        // Map status to our simpler format
        const status: 'success' | 'failed' | 'unknown' = 
          collector.status === 'operational' ? 'success' : 
          collector.status === 'error' ? 'failed' : 
          'unknown';
        
        // Determine if it's a news source or reddit based on name
        const isReddit = collector.name.toLowerCase() === 'reddit';
        
        return {
          name: collector.name,
          status,
          articles: !isReddit ? collector.items_collected : undefined,
          posts: isReddit ? collector.items_collected : undefined,
          error: collector.error || undefined,
          lastRun: collector.last_run ? formatDateTime(collector.last_run, {
            hour: '2-digit',
            minute: '2-digit',
            hour12: true
          }) : undefined,
        };
      });
      
      setCollectorHealth(collectors);
    } catch (error) {
      console.error('Failed to fetch collector health:', error);
      // Fallback to empty array on error
      setCollectorHealth([]);
    }
  };

  // ============================================================================
  // Job Operations
  // ============================================================================

  const performJobOperation = async (jobId: string, action: 'enable' | 'disable' | 'cancel') => {
    try {
      setOperationLoading(prev => ({ ...prev, [jobId]: true }));
      
      await adminAPI.updateScheduledJob(jobId, action);
      
      toast({
        title: "Job Updated",
        description: `Job ${action}d successfully.`,
      });
      
      await loadSchedulerData();
      
    } catch (error) {
      console.error(`Failed to ${action} job:`, error);
      toast({
        title: "Error",
        description: `Failed to ${action} job. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setOperationLoading(prev => ({ ...prev, [jobId]: false }));
    }
  };

  const runJobNow = async (jobId: string) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`run-${jobId}`]: true }));
      
      // Trigger manual pipeline execution
      await adminAPI.triggerManualCollection({
        stock_symbols: [], // Backend will use current watchlist
        priority: 'high'
      });
      
      toast({
        title: "Pipeline Started",
        description: "Full pipeline execution has been triggered.",
      });
      
      await loadSchedulerData();
      
    } catch (error) {
      console.error('Failed to run job:', error);
      toast({
        title: "Error",
        description: "Failed to trigger pipeline execution.",
        variant: "destructive",
      });
    } finally {
      setOperationLoading(prev => ({ ...prev, [`run-${jobId}`]: false }));
    }
  };

  // ============================================================================
  // UI Helper Functions
  // ============================================================================

  const getMarketStatusBadge = () => {
    const { isOpen, currentPeriod } = marketStatus;
    
    const statusConfig: Record<string, { label: string; color: string; icon: React.ReactNode }> = {
      'market-hours': { label: 'Market Open', color: 'bg-green-500', icon: <Sun className="h-3 w-3" /> },
      'pre-market': { label: 'Pre-Market', color: 'bg-amber-500', icon: <Sunrise className="h-3 w-3" /> },
      'after-hours': { label: 'After Hours', color: 'bg-orange-500', icon: <Sunset className="h-3 w-3" /> },
      'weekend': { label: 'Weekend', color: 'bg-blue-500', icon: <Moon className="h-3 w-3" /> },
      'overnight': { label: 'Market Closed', color: 'bg-gray-500', icon: <Moon className="h-3 w-3" /> }
    };
    
    const config = statusConfig[currentPeriod] || statusConfig['overnight'];
    
    return (
      <Badge className={`${config.color} text-white flex items-center gap-1`}>
        {config.icon}
        {config.label}
      </Badge>
    );
  };

  const getCollectorStatusIcon = (status: string) => {
    switch (status) {
      case 'success': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      default: return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    }
  };

  // ============================================================================
  // Render
  // ============================================================================

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold">Smart Scheduler</h1>
            <p className="text-muted-foreground mt-1">
              Intelligent pipeline scheduling with market-aware presets
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => loadSchedulerData(true)}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Market Status Bar with Prominent Countdown */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <Activity className="h-5 w-5 text-muted-foreground" />
                  <span className="font-medium">Market Status:</span>
                  {getMarketStatusBadge()}
                </div>
              </div>
              {marketStatus.nextOpen && (
                <div className="text-sm text-muted-foreground mt-2">
                  Next open: <span className="font-medium">{marketStatus.nextOpen}</span>
                </div>
              )}
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
            <CardContent className="pt-6">
              <MarketCountdown variant="card" />
            </CardContent>
          </Card>
        </div>

        {/* Compact Collector Health Status */}
        <Card>
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="flex items-center gap-2 text-base">
                <Database className="h-4 w-4" />
                Data Sources (Last 24h)
              </CardTitle>
              <Badge variant="outline" className="text-xs">
                {collectorHealth.filter(c => c.status === 'success').length}/{collectorHealth.length} Active
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {collectorHealth.map((collector) => (
                <div key={collector.name} className="border rounded-md p-2 text-center">
                  <div className="flex items-center justify-center gap-1 mb-1">
                    {getCollectorStatusIcon(collector.status)}
                    <span className="text-sm font-medium">{collector.name}</span>
                  </div>
                  <div className="text-lg font-bold text-gray-900">
                    {collector.articles || collector.posts || 0}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {collector.posts ? 'posts' : 'articles'}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Upcoming Pipeline Runs - Timeline */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Calendar className="h-5 w-5" />
              Upcoming Pipeline Runs (Next 48 Hours)
            </CardTitle>
            <CardDescription>
              Visual timeline of scheduled pipeline executions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {timelineEvents.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                No scheduled runs in the next 48 hours
              </div>
            ) : (
              <div className="space-y-3">
                {timelineEvents.map((event, index) => (
                  <div key={`${event.jobId}-${index}`} className="flex items-center gap-4 p-3 border rounded-lg hover:bg-gray-50 transition-colors">
                    <div className={`w-3 h-3 rounded-full ${event.color}`} />
                    <div className="flex-1">
                      <div className="font-medium">{event.jobName}</div>
                      <div className="text-sm text-muted-foreground">
                        {event.scheduledTime.toLocaleString("en-US", {
                          weekday: 'short',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          hour12: true,
                          timeZone: USER_TIMEZONE,
                          timeZoneName: 'short'
                        })}
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs">
                      {event.type.replace('-', ' ')}
                    </Badge>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Preset Schedules */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {presetSchedules.map((preset) => {
            // Find matching job from backend using exact name match
            const matchingJob = schedulerData?.jobs?.find(job => 
              job.name === preset.name
            );
            
            return (
              <Card key={preset.id} className="relative overflow-hidden">
                <div className={`absolute top-0 left-0 w-1 h-full ${preset.color}`} />
                <CardHeader className="pl-6">
                  <CardTitle className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {preset.icon}
                      {preset.name}
                    </div>
                    {matchingJob ? (
                      <Badge variant={matchingJob.enabled ? "default" : "secondary"}>
                        {matchingJob.enabled ? "Active" : "Inactive"}
                      </Badge>
                    ) : (
                      <Badge variant="destructive">
                        Not Configured
                      </Badge>
                    )}
                  </CardTitle>
                  <CardDescription>{preset.description}</CardDescription>
                </CardHeader>
                <CardContent className="pl-6 space-y-4">
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{preset.schedule}</span>
                    </div>
                    <div className="text-sm text-muted-foreground bg-gray-50 p-3 rounded-md">
                      <strong>Why?</strong> {preset.rationale}
                    </div>
                    
                    {matchingJob?.next_run && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Next run:</strong> {formatDateTime(matchingJob.next_run)}
                      </div>
                    )}
                    {matchingJob?.last_run && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Last run:</strong> {formatDateTime(matchingJob.last_run)}
                      </div>
                    )}
                  </div>
                  
                  <div className="flex gap-2 flex-wrap">
                    {matchingJob ? (
                      <>
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => runJobNow(matchingJob.job_id)}
                          disabled={operationLoading[`run-${matchingJob.job_id}`]}
                        >
                          <Play className="h-3 w-3 mr-1" />
                          Run Now
                        </Button>
                        <Button
                          size="sm"
                          variant={matchingJob.enabled ? "destructive" : "default"}
                          onClick={() => performJobOperation(
                            matchingJob.job_id, 
                            matchingJob.enabled ? 'disable' : 'enable'
                          )}
                          disabled={operationLoading[matchingJob.job_id]}
                        >
                          {matchingJob.enabled ? (
                            <>
                              <Pause className="h-3 w-3 mr-1" />
                              Disable
                            </>
                          ) : (
                            <>
                              <Play className="h-3 w-3 mr-1" />
                              Enable
                            </>
                          )}
                        </Button>
                      </>
                    ) : (
                      <Alert className="bg-yellow-50 border-yellow-200">
                        <AlertTriangle className="h-4 w-4 text-yellow-600" />
                        <AlertDescription className="text-yellow-800 text-sm">
                          Job not configured in backend. Please restart the backend to initialize this schedule.
                        </AlertDescription>
                      </Alert>
                    )}
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Technical Details */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Scheduler Statistics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold">
                  {schedulerData?.jobs?.filter(j => j.enabled).length || 0}
                </div>
                <div className="text-sm text-muted-foreground">Active Jobs</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold">{schedulerData?.total_jobs || 0}</div>
                <div className="text-sm text-muted-foreground">Total Jobs</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold">
                  {collectorHealth.filter(c => c.status === 'success').length}/{collectorHealth.length}
                </div>
                <div className="text-sm text-muted-foreground">Collectors Online</div>
              </div>
              <div className="text-center p-4 border rounded-lg">
                <div className="text-2xl font-bold text-green-600">
                  {schedulerData?.scheduler_running ? "Running" : "Stopped"}
                </div>
                <div className="text-sm text-muted-foreground">Scheduler Status</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Important Notes */}
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>Pipeline Execution Model:</strong> All schedules run the FULL pipeline 
            (Data Collection -&gt; Sentiment Analysis -&gt; Storage) as an atomic operation. 
            This ensures data consistency and proper sentiment analysis of fresh data.
            Each run processes all 4 collectors (NewsAPI, FinHub, Reddit, MarketAux*) sequentially.
          </AlertDescription>
        </Alert>
      </div>
    </AdminLayout>
  );
};

export default SchedulerManagerV2;
