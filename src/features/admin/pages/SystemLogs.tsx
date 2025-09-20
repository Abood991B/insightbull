
import { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { useToast } from "@/shared/hooks/use-toast";
import { adminAPI, SystemLog, SystemLogsResponse } from "@/api/services/admin.service";

const SystemLogs = () => {
  const [logLevel, setLogLevel] = useState("all");
  const [component, setComponent] = useState("all");
  const [timeRange, setTimeRange] = useState("24h");
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const { toast } = useToast();

  const LOGS_PER_PAGE = 50;

  useEffect(() => {
    loadLogs(true);
  }, [logLevel, component, timeRange]);

  const getDateRangeFromTimeRange = (range: string) => {
    const now = new Date();
    let startDate = "";
    let endDate = "";

    switch (range) {
      case "1h":
        startDate = new Date(now.getTime() - 60 * 60 * 1000).toISOString().split('T')[0];
        break;
      case "24h":
        startDate = new Date(now.getTime() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        break;
      case "7d":
        startDate = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        break;
      case "30d":
        startDate = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
        break;
      case "all":
      default:
        // No date filtering for "all"
        break;
    }

    return { startDate, endDate };
  };

  const loadLogs = async (reset = false) => {
    try {
      if (reset) {
        setLoading(true);
        setPage(0);
        setLogs([]);
      } else {
        setLoadingMore(true);
      }

      const currentPage = reset ? 0 : page;
      const offset = currentPage * LOGS_PER_PAGE;
      
      const { startDate, endDate } = getDateRangeFromTimeRange(timeRange);
      
      const response: SystemLogsResponse = await adminAPI.getSystemLogs(
        logLevel === "all" ? undefined : logLevel,
        component === "all" ? undefined : component,
        startDate || undefined,
        endDate || undefined,
        LOGS_PER_PAGE,
        offset
      );

      if (reset) {
        setLogs(response.logs);
      } else {
        setLogs(prev => [...prev, ...response.logs]);
      }
      
      setTotalCount(response.total_count);
      setHasMore(response.logs.length === LOGS_PER_PAGE);
      setPage(currentPage + 1);

    } catch (error) {
      console.error('Failed to load logs:', error);
      toast({
        title: "Error",
        description: "Failed to load system logs. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  };

  const loadMoreLogs = () => {
    if (!loadingMore && hasMore) {
      loadLogs(false);
    }
  };

  const refreshLogs = () => {
    loadLogs(true);
  };

  const downloadLogs = async () => {
    try {
      setDownloading(true);
      const { startDate, endDate } = getDateRangeFromTimeRange(timeRange);
      
      const blob = await adminAPI.downloadSystemLogs(
        logLevel === "all" ? undefined : logLevel,
        component === "all" ? undefined : component,
        startDate || undefined,
        endDate || undefined
      );
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `system_logs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      toast({
        title: "Success",
        description: "System logs downloaded successfully.",
      });
    } catch (error) {
      console.error('Failed to download logs:', error);
      toast({
        title: "Error",
        description: "Failed to download system logs. Please try again.",
        variant: "destructive",
      });
    } finally {
      setDownloading(false);
    }
  };

  const clearLogs = async () => {
    if (!window.confirm('Are you sure you want to clear all system logs? This action cannot be undone.')) {
      return;
    }
    
    try {
      setClearing(true);
      await adminAPI.clearSystemLogs();
      
      toast({
        title: "Success",
        description: "System logs cleared successfully.",
      });
      
      // Refresh the logs list
      loadLogs(true);
    } catch (error) {
      console.error('Failed to clear logs:', error);
      toast({
        title: "Error",
        description: "Failed to clear system logs. Please try again.",
        variant: "destructive",
      });
    } finally {
      setClearing(false);
    }
  };

  const getUniqueComponents = () => {
    // Get components from current logs
    const logComponents = logs.map(log => log.component).filter(Boolean);
    const uniqueLogComponents = Array.from(new Set(logComponents));
    
    // Always include common system components
    const systemComponents = [
      'admin_service',
      'system_service', 
      'data_collector',
      'pipeline',
      'sentiment_engine',
      'auth_service',
      'watchlist_service',
      'api_routes',
      'system'
    ];
    
    // Combine and deduplicate
    const allComponents = [...systemComponents, ...uniqueLogComponents];
    return Array.from(new Set(allComponents)).sort();
  };

  const filteredLogs = logs.filter(log => {
    const levelMatch = logLevel === 'all' || log.level === logLevel;
    const componentMatch = component === 'all' || log.component === component;
    return levelMatch && componentMatch;
  });

  const getLogStats = () => {
    const errorCount = logs.filter(log => log.level === 'ERROR' || log.level === 'CRITICAL').length;
    const warningCount = logs.filter(log => log.level === 'WARNING').length;
    const infoCount = logs.filter(log => log.level === 'INFO' || log.level === 'DEBUG').length;
    
    return {
      total: totalCount || logs.length,
      errors: errorCount,
      warnings: warningCount,
      info: infoCount
    };
  };

  const stats = getLogStats();

  const getLevelBadge = (level: string) => {
    switch (level) {
      case "CRITICAL":
        return <Badge className="bg-red-600 text-white">CRITICAL</Badge>;
      case "ERROR":
        return <Badge className="bg-red-100 text-red-800">ERROR</Badge>;
      case "WARNING":
        return <Badge className="bg-yellow-100 text-yellow-800">WARNING</Badge>;
      case "INFO":
        return <Badge className="bg-blue-100 text-blue-800">INFO</Badge>;
      case "DEBUG":
        return <Badge className="bg-gray-100 text-gray-800">DEBUG</Badge>;
      default:
        return <Badge variant="outline">{level}</Badge>;
    }
  };

  const getComponentIcon = (component: string) => {
    // Removed emojis for professional FYP presentation
    return "";
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Logs</h1>
            <p className="text-gray-600 mt-2">Monitor system activity and debug issues</p>
          </div>
          
          {/* Action Buttons */}
          <div className="flex gap-3">
            <Button onClick={refreshLogs} disabled={loading} variant="outline">
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
            
            <Button onClick={downloadLogs} disabled={downloading} variant="outline">
              {downloading ? 'Downloading...' : 'Download CSV'}
            </Button>
            
            <Button onClick={clearLogs} disabled={clearing} variant="destructive">
              {clearing ? 'Clearing...' : 'Clear All Logs'}
            </Button>
          </div>
        </div>

        {/* Filters Card */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Filters</CardTitle>
            <CardDescription>Filter logs by level, component, and date range</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {/* Log Level Filter */}
              <div className="space-y-2">
                <Label htmlFor="log-level">Log Level</Label>
                <Select value={logLevel} onValueChange={setLogLevel}>
                  <SelectTrigger id="log-level">
                    <SelectValue placeholder="Select level" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Levels</SelectItem>
                    <SelectItem value="DEBUG">Debug</SelectItem>
                    <SelectItem value="INFO">Info</SelectItem>
                    <SelectItem value="WARNING">Warning</SelectItem>
                    <SelectItem value="ERROR">Error</SelectItem>
                    <SelectItem value="CRITICAL">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              {/* Component Filter */}
              <div className="space-y-2">
                <Label htmlFor="component">Component</Label>
                <Select value={component} onValueChange={setComponent}>
                  <SelectTrigger id="component">
                    <SelectValue placeholder="Select component" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Components</SelectItem>
                    {getUniqueComponents().map(comp => {
                      const icon = getComponentIcon(comp);
                      const displayName = comp === 'admin_service' ? 'Admin Service' :
                                        comp === 'data_collector' ? 'Data Collector' :
                                        comp === 'pipeline' ? 'Pipeline' :
                                        comp === 'system_service' ? 'System Service' :
                                        comp === 'sentiment_engine' ? 'Sentiment Engine' :
                                        comp === 'auth_service' ? 'Auth Service' :
                                        comp === 'watchlist_service' ? 'Watchlist Service' :
                                        comp === 'api_routes' ? 'API Routes' :
                                        comp === 'system' ? 'System Core' :
                                        comp;
                      return (
                        <SelectItem key={comp} value={comp}>
                          {displayName}
                        </SelectItem>
                      );
                    })}
                  </SelectContent>
                </Select>
              </div>

              {/* Time Range Filter */}
              <div className="space-y-2">
                <Label htmlFor="time-range">Time Range</Label>
                <Select value={timeRange} onValueChange={setTimeRange}>
                  <SelectTrigger id="time-range">
                    <SelectValue placeholder="Select time range" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1h">Last Hour</SelectItem>
                    <SelectItem value="24h">Last 24 Hours</SelectItem>
                    <SelectItem value="7d">Last 7 Days</SelectItem>
                    <SelectItem value="30d">Last 30 Days</SelectItem>
                    <SelectItem value="all">All Time</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Clear Filters Button */}
            <div className="mt-4 pt-4 border-t">
              <Button 
                variant="ghost" 
                size="sm"
                onClick={() => {
                  setLogLevel("all");
                  setComponent("all");
                  setTimeRange("24h");
                }}
              >
                Clear All Filters
              </Button>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Total Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">{stats.total.toLocaleString()}</div>
              <p className="text-sm text-gray-600">All time</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">{stats.errors}</div>
              <p className="text-sm text-gray-600">
                {stats.errors > 0 ? 'Requires attention' : 'All clear'}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Warnings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-600">{stats.warnings}</div>
              <p className="text-sm text-gray-600">
                {stats.warnings > 0 ? 'Monitor closely' : 'No warnings'}
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Info</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">{stats.info}</div>
              <p className="text-sm text-gray-600">Normal operations</p>
            </CardContent>
          </Card>
        </div>

        {/* System Logs Display */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <div>
              <CardTitle>System Logs</CardTitle>
              <CardDescription>
                {filteredLogs.length > 0 
                  ? `Showing ${filteredLogs.length} of ${totalCount} logs`
                  : 'No logs found matching current filters'
                }
              </CardDescription>
            </div>
            {filteredLogs.length > 0 && (
              <div className="text-sm text-gray-500">
                Last updated: {new Date().toLocaleTimeString()}
              </div>
            )}
          </CardHeader>
          <CardContent>
            {loading && logs.length === 0 ? (
              <div className="flex justify-center py-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <div className="text-gray-500">Loading system logs...</div>
                </div>
              </div>
            ) : (
              <div className="space-y-1">
                {filteredLogs.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 mb-2">📋</div>
                    <div className="text-gray-500 font-medium">No logs found</div>
                    <div className="text-sm text-gray-400 mt-1">
                      Try adjusting your filters or check back later
                    </div>
                  </div>
                ) : (
                  <>
                    {/* Log Entries */}
                    <div className="space-y-2">
                      {filteredLogs.map((log, index) => (
                        <div key={index} className="group hover:bg-gray-50 rounded-lg p-3 border border-gray-100 transition-colors">
                          <div className="flex items-start gap-3">
                            {/* Level Badge */}
                            <div className="flex-shrink-0 mt-0.5">
                              {getLevelBadge(log.level)}
                            </div>
                            
                            {/* Log Content */}
                            <div className="flex-1 min-w-0">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-sm font-medium text-gray-900 truncate">
                                  {log.component || 'Unknown'}
                                </span>
                                <span className="text-xs text-gray-500 flex-shrink-0">
                                  {new Date(log.timestamp).toLocaleString()}
                                </span>
                              </div>
                              
                              <p className="text-sm text-gray-700 leading-relaxed">
                                {log.message}
                              </p>
                              
                              {/* Additional Info */}
                              {(log.function || log.line_number) && (
                                <div className="mt-1 text-xs text-gray-400">
                                  {log.function && `${log.function}()`}
                                  {log.function && log.line_number && ' • '}
                                  {log.line_number && `Line ${log.line_number}`}
                                </div>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                    
                    {/* Load More Button */}
                    {hasMore && (
                      <div className="flex justify-center pt-6">
                        <Button 
                          variant="outline" 
                          onClick={loadMoreLogs}
                          disabled={loadingMore}
                          className="min-w-32"
                        >
                          {loadingMore ? (
                            <>
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current mr-2"></div>
                              Loading...
                            </>
                          ) : (
                            'Load More Logs'
                          )}
                        </Button>
                      </div>
                    )}
                  </>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

export default SystemLogs;
