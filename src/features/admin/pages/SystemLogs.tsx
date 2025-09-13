
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { useState } from "react";

const SystemLogs = () => {
  const [logLevel, setLogLevel] = useState("all");
  const [timeRange, setTimeRange] = useState("24h");

  const logs = [
    { time: "2024-01-15 14:30:25", level: "INFO", message: "Data collection pipeline started successfully", source: "DataCollector" },
    { time: "2024-01-15 14:25:10", level: "INFO", message: "Sentiment analysis completed for 500 records", source: "SentimentAnalyzer" },
    { time: "2024-01-15 14:20:05", level: "WARNING", message: "Rate limit approaching for Reddit API", source: "ApiManager" },
    { time: "2024-01-15 14:15:30", level: "ERROR", message: "Failed to connect to NewsAPI - timeout", source: "ApiManager" },
    { time: "2024-01-15 14:10:15", level: "INFO", message: "Database backup completed successfully", source: "StorageManager" },
    { time: "2024-01-15 14:05:00", level: "INFO", message: "User accessed admin dashboard", source: "AuthManager" },
    { time: "2024-01-15 14:00:45", level: "WARNING", message: "Storage usage at 75% capacity", source: "StorageManager" },
    { time: "2024-01-15 13:55:20", level: "INFO", message: "Stock watchlist updated - added NVDA", source: "WatchlistManager" },
  ];

  const filteredLogs = logs.filter(log => 
    logLevel === "all" || log.level.toLowerCase() === logLevel.toLowerCase()
  );

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
                <SelectItem value="error">Error</SelectItem>
                <SelectItem value="warning">Warning</SelectItem>
                <SelectItem value="info">Info</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={timeRange} onValueChange={setTimeRange}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Time range" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1h">Last Hour</SelectItem>
                <SelectItem value="24h">Last 24h</SelectItem>
                <SelectItem value="7d">Last 7 Days</SelectItem>
                <SelectItem value="30d">Last 30 Days</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Total Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold">1,247</div>
              <p className="text-sm text-gray-600">Last 24 hours</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Errors</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-red-600">3</div>
              <p className="text-sm text-gray-600">Requires attention</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Warnings</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-yellow-600">12</div>
              <p className="text-sm text-gray-600">Monitor closely</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Info</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-blue-600">1,232</div>
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
            <div className="space-y-3">
              {filteredLogs.map((log, index) => (
                <div key={index} className="border-b pb-3 last:border-b-0">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getLevelBadge(log.level)}
                        <span className="text-sm font-medium">{log.source}</span>
                        <span className="text-xs text-gray-500">{log.time}</span>
                      </div>
                      <p className="text-sm text-gray-700">{log.message}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

export default SystemLogs;
