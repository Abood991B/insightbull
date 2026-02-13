/**
 * Scheduler Manager V2 - Smart Preset Scheduling
 * ==============================================
 * 
 * Improved scheduler UI with:
 * - Human-readable preset schedules (no raw cron)
 * - Atomic pipeline execution (data collection + sentiment analysis together)
 * - Next run timeline visualization
 * - Collector health monitoring
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
  ScheduledJob,
  SchedulerHistoryResponse
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
    description: 'Full pipeline run when pre-market opens',
    icon: <Sunrise className="h-5 w-5" />,
    schedule: `Daily at 5 PM ${timezoneName} (Mon-Fri)`,
    cronExpression: '0 9 * * 0-4', // 9 AM UTC Mon-Fri = 5 PM GMT+8 = 4 AM ET
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-amber-500',
    marketContext: 'pre-market',
    rationale: 'Collect overnight news right as pre-market trading begins (4 AM ET). Gives traders fresh insights before the main session.'
  },
  {
    id: 'market-active',
    name: 'Active Trading Updates',
    description: 'Frequent updates during market hours',
    icon: <Activity className="h-5 w-5" />,
    schedule: `Every 45 minutes (10 PM - 5 AM ${timezoneName}, Mon-Fri)`,
    cronExpression: '0,45 14-20 * * 0-4', // Every 45 min, 2-8:59 PM UTC Mon-Fri
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-green-500',
    marketContext: 'market-hours',
    rationale: 'Monitor real-time sentiment shifts during active trading (9:30 AM - 4 PM ET). Catches breaking news while respecting Gemma 3 27B rate limits.'
  },
  {
    id: 'after-hours-evening',
    name: 'After-Hours Analysis',
    description: `Post-market sentiment 2 hours after close`,
    icon: <Sunset className="h-5 w-5" />,
    schedule: `Daily at 7 AM ${timezoneName} (Tue-Sat)`,
    cronExpression: '0 23 * * 0-4', // 11 PM UTC Mon-Fri = 7 AM GMT+8 = 6 PM ET
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-orange-500',
    marketContext: 'after-hours',
    rationale: 'Capture post-market news and earnings reports 2 hours after market close (6 PM ET).'
  },
  {
    id: 'overnight-summary',
    name: 'Overnight Summary',
    description: `Final summary after after-hours ends`,
    icon: <Moon className="h-5 w-5" />,
    schedule: `Daily at 9 AM ${timezoneName} (Tue-Sat)`,
    cronExpression: '0 1 * * 1-5', // 1 AM UTC Tue-Sat = 9 AM GMT+8 = 8 PM ET Mon-Fri
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-indigo-500',
    marketContext: 'after-hours',
    rationale: 'Final summary after all after-hours trading concludes (8 PM ET). Complete daily recap.'
  },
  {
    id: 'weekend-deep',
    name: 'Weekend Deep Analysis',
    description: 'Comprehensive weekly analysis',
    icon: <BarChart3 className="h-5 w-5" />,
    schedule: `Sunday at 6 PM ${timezoneName}`,
    cronExpression: '0 10 * * 6', // Sunday 10 AM UTC = Sunday 6 PM GMT+8
    jobType: 'full_pipeline',
    enabled: true,
    color: 'bg-blue-500',
    marketContext: 'weekend',
    rationale: 'Weekly comprehensive analysis on Sunday evening. Process accumulated weekend news to prepare for Monday pre-market (opens 5 PM your time).'
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
  const [runHistory, setRunHistory] = useState<SchedulerHistoryResponse | null>(null);
  const [lastEventTimestamp, setLastEventTimestamp] = useState<string | null>(null);
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
  // Job Event Polling (for notifications)
  // ============================================================================
  
  const checkJobEvents = async () => {
    try {
      const response = await adminAPI.getJobEvents(lastEventTimestamp || undefined);
      
      if (response.events && response.events.length > 0) {
        // Update last timestamp to avoid duplicate notifications
        setLastEventTimestamp(response.events[0].timestamp);
        
        // Show toast for each new event
        for (const event of response.events) {
          if (event.type === 'started') {
            toast({
              title: `Job Started: ${event.job_name}`,
              description: "Pipeline execution in progress...",
            });
          } else if (event.type === 'completed') {
            const duration = event.details.duration_seconds 
              ? `${Math.round(event.details.duration_seconds)}s` 
              : '';
            toast({
              title: `Job Completed: ${event.job_name}`,
              description: `Finished successfully ${duration}`,
            });
            // Refresh data after completion
            loadSchedulerData(false);
          } else if (event.type === 'failed') {
            toast({
              title: `Job Failed: ${event.job_name}`,
              description: event.details.error || "An error occurred",
              variant: "destructive",
            });
          }
        }
      }
    } catch (error) {
      // Silently ignore polling errors
      if (import.meta.env.DEV) {
        console.debug('Job event polling error:', error);
      }
    }
  };

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
      
      // Fetch run history (last 7 days)
      loadRunHistory();
      
      if (showRefreshToast) {
        toast({
          title: "Scheduler Updated",
          description: "Scheduler data has been refreshed.",
        });
      }
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('Failed to load scheduler data:', error);
      }
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

  const loadRunHistory = async () => {
    try {
      const history = await adminAPI.getSchedulerHistory(7);
      setRunHistory(history);
    } catch (error) {
      if (import.meta.env.DEV) {
        console.error('Failed to load run history:', error);
      }
    }
  };

  useEffect(() => {
    loadSchedulerData();
    // Auto-refresh scheduler data every 30 seconds
    const schedulerInterval = setInterval(() => loadSchedulerData(), 30000);
    
    // Update market status every 10 seconds (backend fetches real data)
    const marketInterval = setInterval(() => updateMarketStatus(), 10000);
    
    // Poll for job events every 5 seconds (for notifications)
    const eventInterval = setInterval(() => checkJobEvents(), 5000);
    
    return () => {
      clearInterval(schedulerInterval);
      clearInterval(marketInterval);
      clearInterval(eventInterval);
    };
  }, [lastEventTimestamp]);

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
      if (import.meta.env.DEV) {
        console.error('Failed to update market status:', error);
      }
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
        const jobName = job.name.toLowerCase();
        
        // Classify by job name (more reliable than hour-based detection)
        let type: TimelineEvent['type'] = 'overnight';
        let color = 'bg-gray-500';
        
        if (jobName.includes('weekend') || jobName.includes('deep')) {
          type = 'weekend';
          color = 'bg-blue-500';
        } else if (jobName.includes('pre-market') || jobName.includes('preparation')) {
          type = 'pre-market';
          color = 'bg-amber-500';
        } else if (jobName.includes('active') || jobName.includes('trading')) {
          type = 'market-hours';
          color = 'bg-green-500';
        } else if (jobName.includes('after-hours') || jobName.includes('after hours')) {
          type = 'after-hours';
          color = 'bg-orange-500';
        } else if (jobName.includes('overnight') || jobName.includes('summary')) {
          type = 'overnight';
          color = 'bg-purple-500';
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
        
        // Determine if it's a news source or hackernews based on name
        const isHackerNews = collector.name.toLowerCase() === 'hackernews' || collector.name.toLowerCase() === 'hacker news';
        
        return {
          name: collector.name,
          status,
          articles: !isHackerNews ? collector.items_collected : undefined,
          posts: isHackerNews ? collector.items_collected : undefined,
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
      if (import.meta.env.DEV) {
        console.error('Failed to fetch collector health:', error);
      }
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
      if (import.meta.env.DEV) {
        console.error(`Failed to ${action} job:`, error);
      }
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
      if (import.meta.env.DEV) {
        console.error('Failed to run job:', error);
      }
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

        {/* Pipeline Run History (Last 7 Days) */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Pipeline Run History (Last 7 Days)
            </CardTitle>
            <CardDescription>
              Track daily pipeline execution statistics
            </CardDescription>
          </CardHeader>
          <CardContent>
            {!runHistory || Object.keys(runHistory.history).length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">
                <Activity className="h-8 w-8 mx-auto mb-2 opacity-50" />
                <p>No pipeline runs recorded yet</p>
                <p className="text-sm">History will appear after scheduled jobs execute</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* Summary Stats */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-blue-600">{runHistory.summary.total_runs}</div>
                    <div className="text-xs text-muted-foreground">Total Runs</div>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-green-600">{runHistory.summary.successful_runs}</div>
                    <div className="text-xs text-muted-foreground">Successful</div>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-red-600">{runHistory.summary.failed_runs}</div>
                    <div className="text-xs text-muted-foreground">Failed</div>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {runHistory.summary.avg_duration_seconds > 0 
                        ? `${Math.round(runHistory.summary.avg_duration_seconds)}s` 
                        : 'N/A'}
                    </div>
                    <div className="text-xs text-muted-foreground">Avg Duration</div>
                  </div>
                </div>

                {/* Daily Breakdown */}
                <div className="space-y-2">
                  <h4 className="text-sm font-medium text-muted-foreground">Daily Breakdown</h4>
                  {Object.entries(runHistory.history)
                    .sort(([a], [b]) => b.localeCompare(a)) // Sort by date descending
                    .slice(0, 7) // Show last 7 days
                    .map(([date, jobs]) => {
                      const totalRuns = Object.values(jobs).flat().length;
                      const successfulRuns = Object.values(jobs).flat().filter(r => r.status === 'completed').length;
                      
                      return (
                        <div key={date} className="flex items-center justify-between p-2 border rounded hover:bg-gray-50">
                          <div className="flex items-center gap-2">
                            <Calendar className="h-4 w-4 text-muted-foreground" />
                            <span className="font-medium">
                              {new Date(date).toLocaleDateString('en-US', {
                                weekday: 'short',
                                month: 'short',
                                day: 'numeric'
                              })}
                            </span>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-sm text-muted-foreground">
                              {Object.keys(jobs).length} jobs
                            </span>
                            <Badge variant={successfulRuns === totalRuns ? 'default' : 'secondary'}>
                              {successfulRuns}/{totalRuns} runs
                            </Badge>
                          </div>
                        </div>
                      );
                    })}
                </div>
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
                    
                    {/* Running Status */}
                    {matchingJob?.status === 'running' && (
                      <div className="flex items-center gap-2 text-sm text-green-600 font-medium animate-pulse">
                        <RefreshCw className="h-4 w-4 animate-spin" />
                        Running...
                      </div>
                    )}
                    
                    {matchingJob?.next_run && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Next run:</strong> {formatDateTime(matchingJob.next_run)}
                      </div>
                    )}
                    {matchingJob?.last_run && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Last run:</strong> {formatDateTime(matchingJob.last_run)}
                        {matchingJob.last_duration_seconds && (
                          <span className="ml-1">({Math.round(matchingJob.last_duration_seconds)}s)</span>
                        )}
                      </div>
                    )}
                    
                    {/* Today's run count */}
                    {matchingJob && (matchingJob.today_run_count ?? 0) > 0 && (
                      <div className="text-sm text-muted-foreground">
                        <strong>Runs today:</strong> {matchingJob.today_run_count}
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
            Each run processes all 5 collectors (NewsAPI, FinHub, Hacker News, GDELT, Yahoo Finance) sequentially.
          </AlertDescription>
        </Alert>
      </div>
    </AdminLayout>
  );
};

export default SchedulerManagerV2;
