/**
 * System Health Alerts Component
 * ===============================
 * 
 * Displays critical system health alerts and warnings.
 * Monitors rate limits, database, pipeline, scheduler, storage, and model accuracy.
 * 
 * Priority 2: HIGH - Critical Functionality
 */

import React, { useState, useEffect } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/shared/components/ui/alert';
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/components/ui/card';
import { Badge } from '@/shared/components/ui/badge';
import { Button } from '@/shared/components/ui/button';
import {
  AlertTriangle,
  AlertCircle,
  CheckCircle,
  XCircle,
  Database,
  Activity,
  Clock,
  HardDrive,
  TrendingDown,
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from 'lucide-react';
import { adminAPI, SystemStatus, ModelAccuracy, StorageSettings } from '../../../api/services/admin.service';

// Types
interface HealthAlert {
  id: string;
  severity: 'critical' | 'warning' | 'info';
  title: string;
  description: string;
  category: 'rate_limit' | 'database' | 'pipeline' | 'scheduler' | 'storage' | 'model' | 'service';
  timestamp: string;
  actionable?: boolean;
  action?: () => void;
  actionLabel?: string;
}

interface SystemHealthAlertsProps {
  systemStatus?: SystemStatus | null;
  modelAccuracy?: ModelAccuracy | null;
  onRefresh?: () => void;
  compact?: boolean;
}

const SystemHealthAlerts: React.FC<SystemHealthAlertsProps> = ({
  systemStatus,
  modelAccuracy,
  onRefresh,
  compact = false,
}) => {
  const [alerts, setAlerts] = useState<HealthAlert[]>([]);
  const [storageInfo, setStorageInfo] = useState<StorageSettings | null>(null);
  const [expanded, setExpanded] = useState<boolean>(true);
  const [loading, setLoading] = useState<boolean>(false);

  // Fetch storage info
  useEffect(() => {
    const fetchStorageInfo = async () => {
      try {
        const data = await adminAPI.getStorageSettings();
        setStorageInfo(data);
      } catch (error) {
        console.error('Failed to fetch storage info:', error);
      }
    };

    fetchStorageInfo();
    // Refresh every 5 minutes
    const interval = setInterval(fetchStorageInfo, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  // Generate alerts based on system status
  useEffect(() => {
    const generatedAlerts: HealthAlert[] = [];

    if (!systemStatus) {
      generatedAlerts.push({
        id: 'no-status',
        severity: 'warning',
        title: 'System Status Unavailable',
        description: 'Unable to retrieve system status information.',
        category: 'service',
        timestamp: new Date().toISOString(),
      });
      setAlerts(generatedAlerts);
      return;
    }

    // Check overall system status
    if (systemStatus.status === 'degraded') {
      generatedAlerts.push({
        id: 'system-degraded',
        severity: 'critical',
        title: 'System Degraded',
        description: 'One or more critical services are experiencing issues.',
        category: 'service',
        timestamp: systemStatus.timestamp,
      });
    }

    // Check individual services
    if (systemStatus.services) {
      // Database
      if (systemStatus.services.database === 'unhealthy' || systemStatus.services.database === 'error') {
        generatedAlerts.push({
          id: 'database-unhealthy',
          severity: 'critical',
          title: 'Database Connectivity Issue',
          description: 'Database connection is failing. Data operations may be affected.',
          category: 'database',
          timestamp: systemStatus.timestamp,
        });
      }

      // Sentiment Engine
      if (systemStatus.services.sentiment_engine === 'unhealthy') {
        generatedAlerts.push({
          id: 'sentiment-unhealthy',
          severity: 'critical',
          title: 'Sentiment Analysis Unavailable',
          description: 'Sentiment engine is not responding. New data cannot be analyzed.',
          category: 'service',
          timestamp: systemStatus.timestamp,
        });
      }

      // Data Collection
      if (systemStatus.services.data_collection === 'unhealthy') {
        generatedAlerts.push({
          id: 'collection-unhealthy',
          severity: 'warning',
          title: 'Data Collection Issues',
          description: 'Data collection service is experiencing problems. Check API configurations.',
          category: 'pipeline',
          timestamp: systemStatus.timestamp,
        });
      }

      // Real-time Prices
      if (systemStatus.services.real_time_prices === 'unhealthy' || systemStatus.services.real_time_prices === 'error') {
        generatedAlerts.push({
          id: 'prices-stopped',
          severity: 'warning',
          title: 'Real-time Prices Issue',
          description: 'Real-time price service is experiencing problems. Price data may be stale.',
          category: 'service',
          timestamp: systemStatus.timestamp,
        });
      }

      // Scheduler
      if (systemStatus.services.scheduler === 'unhealthy') {
        generatedAlerts.push({
          id: 'scheduler-unhealthy',
          severity: 'warning',
          title: 'Scheduler Not Running',
          description: 'Automated data collection jobs are not being executed.',
          category: 'scheduler',
          timestamp: systemStatus.timestamp,
        });
      }
    }

    // Check data staleness (last collection > 6 hours)
    if (systemStatus.metrics.last_collection) {
      const lastCollection = new Date(systemStatus.metrics.last_collection);
      const hoursSinceCollection = (Date.now() - lastCollection.getTime()) / (1000 * 60 * 60);
      
      if (hoursSinceCollection > 6) {
        generatedAlerts.push({
          id: 'data-stale',
          severity: hoursSinceCollection > 24 ? 'critical' : 'warning',
          title: 'Stale Data Detected',
          description: `No new sentiment data collected in ${Math.floor(hoursSinceCollection)} hours.`,
          category: 'pipeline',
          timestamp: systemStatus.timestamp,
          actionable: true,
          action: () => {/* Could trigger manual collection */},
          actionLabel: 'Trigger Collection',
        });
      }
    }

    // Check storage (if available)
    if (storageInfo && storageInfo.current_usage) {
      const usedPercentage = storageInfo.current_usage.usage_percentage;
      
      if (usedPercentage > 95) {
        generatedAlerts.push({
          id: 'storage-critical',
          severity: 'critical',
          title: 'Storage Critical',
          description: `Database storage is ${usedPercentage.toFixed(1)}% full. Auto-cleanup may be triggered soon.`,
          category: 'storage',
          timestamp: new Date().toISOString(),
        });
      } else if (usedPercentage > 80) {
        generatedAlerts.push({
          id: 'storage-warning',
          severity: 'warning',
          title: 'Storage Warning',
          description: `Database storage is ${usedPercentage.toFixed(1)}% full. Consider reviewing retention settings.`,
          category: 'storage',
          timestamp: new Date().toISOString(),
        });
      }
    }

    // Note: Model accuracy alerts removed because modelAccuracy.model_metrics values are 
    // confidence-based estimates, NOT real accuracy. Use the benchmark feature in 
    // Model Accuracy page for ground-truth accuracy measurements.

    // Check rate limiting (if available in metrics)
    if (systemStatus.metrics && (systemStatus.metrics as any).rate_limiting) {
      const rateLimits = (systemStatus.metrics as any).rate_limiting;
      Object.entries(rateLimits).forEach(([source, limits]: [string, any]) => {
        if (limits.remaining !== undefined && limits.remaining < 10) {
          generatedAlerts.push({
            id: `rate-limit-${source}`,
            severity: limits.remaining < 5 ? 'critical' : 'warning',
            title: `${source} Rate Limit Low`,
            description: `Only ${limits.remaining} requests remaining for ${source}. Resets at ${new Date(limits.reset_time).toLocaleTimeString()}.`,
            category: 'rate_limit',
            timestamp: systemStatus.timestamp,
          });
        }
      });
    }

    setAlerts(generatedAlerts);
  }, [systemStatus, modelAccuracy, storageInfo]);

  // Get alert icon
  const getAlertIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircle className="h-5 w-5" />;
      case 'warning':
        return <AlertTriangle className="h-5 w-5" />;
      case 'info':
        return <AlertCircle className="h-5 w-5" />;
      default:
        return <AlertCircle className="h-5 w-5" />;
    }
  };

  // Get category icon
  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'database':
        return <Database className="h-4 w-4" />;
      case 'pipeline':
      case 'service':
        return <Activity className="h-4 w-4" />;
      case 'scheduler':
        return <Clock className="h-4 w-4" />;
      case 'storage':
        return <HardDrive className="h-4 w-4" />;
      case 'model':
        return <TrendingDown className="h-4 w-4" />;
      case 'rate_limit':
        return <AlertTriangle className="h-4 w-4" />;
      default:
        return <AlertCircle className="h-4 w-4" />;
    }
  };

  // Group alerts by severity
  const criticalAlerts = alerts.filter(a => a.severity === 'critical');
  const warningAlerts = alerts.filter(a => a.severity === 'warning');
  const infoAlerts = alerts.filter(a => a.severity === 'info');

  const handleRefresh = async () => {
    setLoading(true);
    if (onRefresh) {
      await onRefresh();
    }
    setLoading(false);
  };

  // If no alerts and not compact, show success message
  if (alerts.length === 0 && !compact) {
    return (
      <Card className="border-l-4 border-l-green-500">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <span>System Health</span>
            </div>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert className="bg-green-50 border-green-200">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertTitle className="text-green-800">All Systems Operational</AlertTitle>
            <AlertDescription className="text-green-700">
              No health alerts detected. All services are running normally.
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  // Compact view for sidebar or small spaces
  if (compact) {
    return (
      <div className="space-y-2">
        {criticalAlerts.length > 0 && (
          <Alert variant="destructive">
            <XCircle className="h-4 w-4" />
            <AlertTitle>Critical Issues ({criticalAlerts.length})</AlertTitle>
            <AlertDescription className="text-xs">
              {criticalAlerts[0].description}
              {criticalAlerts.length > 1 && ` +${criticalAlerts.length - 1} more`}
            </AlertDescription>
          </Alert>
        )}
        {warningAlerts.length > 0 && criticalAlerts.length === 0 && (
          <Alert className="border-yellow-500 bg-yellow-50">
            <AlertTriangle className="h-4 w-4 text-yellow-600" />
            <AlertTitle className="text-yellow-800">Warnings ({warningAlerts.length})</AlertTitle>
            <AlertDescription className="text-xs text-yellow-700">
              {warningAlerts[0].description}
              {warningAlerts.length > 1 && ` +${warningAlerts.length - 1} more`}
            </AlertDescription>
          </Alert>
        )}
      </div>
    );
  }

  // Full view with all details
  return (
    <Card className={`border-l-4 ${criticalAlerts.length > 0 ? 'border-l-red-500' : warningAlerts.length > 0 ? 'border-l-yellow-500' : 'border-l-blue-500'}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {criticalAlerts.length > 0 ? (
              <XCircle className="h-5 w-5 text-red-500" />
            ) : warningAlerts.length > 0 ? (
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
            ) : (
              <AlertCircle className="h-5 w-5 text-blue-500" />
            )}
            <span>System Health Alerts</span>
            <Badge variant={criticalAlerts.length > 0 ? "destructive" : "secondary"}>
              {alerts.length}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleRefresh}
              disabled={loading}
            >
              <RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
            >
              {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>
        </CardTitle>
      </CardHeader>
      
      {expanded && (
        <CardContent className="space-y-4">
          {/* Critical Alerts */}
          {criticalAlerts.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-red-700 flex items-center gap-2">
                <XCircle className="h-4 w-4" />
                Critical Issues ({criticalAlerts.length})
              </h4>
              {criticalAlerts.map((alert) => (
                <Alert key={alert.id} variant="destructive">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getCategoryIcon(alert.category)}
                        <AlertTitle className="text-sm">{alert.title}</AlertTitle>
                      </div>
                      <AlertDescription className="text-xs">
                        {alert.description}
                      </AlertDescription>
                    </div>
                    {alert.actionable && alert.action && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={alert.action}
                        className="ml-2 shrink-0"
                      >
                        {alert.actionLabel || 'Fix'}
                      </Button>
                    )}
                  </div>
                </Alert>
              ))}
            </div>
          )}

          {/* Warning Alerts */}
          {warningAlerts.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-yellow-700 flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" />
                Warnings ({warningAlerts.length})
              </h4>
              {warningAlerts.map((alert) => (
                <Alert key={alert.id} className="border-yellow-500 bg-yellow-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getCategoryIcon(alert.category)}
                        <AlertTitle className="text-sm text-yellow-800">{alert.title}</AlertTitle>
                      </div>
                      <AlertDescription className="text-xs text-yellow-700">
                        {alert.description}
                      </AlertDescription>
                    </div>
                    {alert.actionable && alert.action && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={alert.action}
                        className="ml-2 shrink-0"
                      >
                        {alert.actionLabel || 'Fix'}
                      </Button>
                    )}
                  </div>
                </Alert>
              ))}
            </div>
          )}

          {/* Info Alerts */}
          {infoAlerts.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-semibold text-blue-700 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Information ({infoAlerts.length})
              </h4>
              {infoAlerts.map((alert) => (
                <Alert key={alert.id} className="border-blue-500 bg-blue-50">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        {getCategoryIcon(alert.category)}
                        <AlertTitle className="text-sm text-blue-800">{alert.title}</AlertTitle>
                      </div>
                      <AlertDescription className="text-xs text-blue-700">
                        {alert.description}
                      </AlertDescription>
                    </div>
                  </div>
                </Alert>
              ))}
            </div>
          )}

          {/* Summary Footer */}
          <div className="pt-4 border-t flex items-center justify-between text-xs text-gray-600">
            <span>Last updated: {new Date(systemStatus?.timestamp || Date.now()).toLocaleTimeString()}</span>
            <span>
              {criticalAlerts.length} critical, {warningAlerts.length} warnings, {infoAlerts.length} info
            </span>
          </div>
        </CardContent>
      )}
    </Card>
  );
};

export default SystemHealthAlerts;
