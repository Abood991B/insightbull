
import { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { useToast } from "@/shared/hooks/use-toast";
import { adminAPI, SystemLog, SystemLogsResponse } from "@/api/services/admin.service";

const SystemLogs = () => {
  const [logLevel, setLogLevel] = useState("all");
  const [component, setComponent] = useState("all");
  const [logs, setLogs] = useState<SystemLog[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(0);
  const [hasMore, setHasMore] = useState(true);
  const { toast } = useToast();

  const LOGS_PER_PAGE = 50;

  useEffect(() => {
    loadLogs(true);
  }, [logLevel, component]);

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
      
      const response: SystemLogsResponse = await adminAPI.getSystemLogs(
        logLevel === "all" ? undefined : logLevel,
        component === "all" ? undefined : component,
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

  const getUniqueComponents = () => {
    const components = logs.map(log => log.component).filter(Boolean);
    return Array.from(new Set(components)).sort();
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
      case "ERROR":
        return <Badge className="bg-red-100 text-red-800">ERROR</Badge>;
      case "WARNING":
        return <Badge className="bg-yellow-100 text-yellow-800">WARNING</Badge>;
      case "INFO":
        return <Badge className="bg-blue-100 text-blue-800">INFO</Badge>;
      default:
        return <Badge variant="outline">{level}</Badge>;
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">System Logs</h1>
            <p className="text-gray-600 mt-2">Monitor system activity and debug issues</p>
          </div>
          
          <div className="flex gap-4">
            <Select value={logLevel} onValueChange={setLogLevel}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Log level" />
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
            
            <Select value={component} onValueChange={setComponent}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Component" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Components</SelectItem>
                {getUniqueComponents().map(comp => (
                  <SelectItem key={comp} value={comp}>{comp}</SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button onClick={refreshLogs} disabled={loading}>
              {loading ? 'Loading...' : 'Refresh'}
            </Button>
          </div>
        </div>

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

        <Card>
          <CardHeader>
            <CardTitle>Recent System Logs</CardTitle>
            <CardDescription>Latest system events and messages</CardDescription>
          </CardHeader>
          <CardContent>
            {loading && logs.length === 0 ? (
              <div className="flex justify-center py-8">
                <div className="text-gray-500">Loading logs...</div>
              </div>
            ) : (
              <div className="space-y-3">
                {filteredLogs.length === 0 ? (
                  <div className="text-center py-8 text-gray-500">
                    No logs found matching the current filters.
                  </div>
                ) : (
                  filteredLogs.map((log, index) => (
                    <div key={index} className="border-b pb-3 last:border-b-0">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            {getLevelBadge(log.level)}
                            <span className="text-sm font-medium">{log.component}</span>
                            <span className="text-xs text-gray-500">
                              {new Date(log.timestamp).toLocaleString()}
                            </span>
                          </div>
                          <p className="text-sm text-gray-700">{log.message}</p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
                
                {hasMore && !loading && (
                  <div className="flex justify-center pt-4">
                    <Button 
                      variant="outline" 
                      onClick={loadMoreLogs}
                      disabled={loadingMore}
                    >
                      {loadingMore ? 'Loading...' : 'Load More'}
                    </Button>
                  </div>
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
