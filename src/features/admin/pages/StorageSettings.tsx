
import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Progress } from "@/shared/components/ui/progress";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useToast } from "@/shared/hooks/use-toast";
import { adminAPI, StorageSettings as StorageSettingsType } from "../../../api/services/admin.service";
import { 
  RefreshCw, 
  Database, 
  HardDrive, 
  Archive, 
  Trash2, 
  Download,
  AlertTriangle,
  CheckCircle,
  XCircle
} from "lucide-react";

const StorageSettings = () => {
  const [storageSettings, setStorageSettings] = useState<StorageSettingsType | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [operationLoading, setOperationLoading] = useState<{[key: string]: boolean}>({});
  const { toast } = useToast();

  // Load storage settings
  const loadStorageSettings = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const data = await adminAPI.getStorageSettings();
      setStorageSettings(data);
      
      if (showRefreshToast) {
        toast({
          title: "Settings Updated",
          description: "Storage settings have been refreshed.",
        });
      }
    } catch (error) {
      console.error('Failed to load storage settings:', error);
      toast({
        title: "Error",
        description: "Failed to load storage settings. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Update storage configuration
  const updateStorageConfiguration = async (config: Partial<StorageSettingsType>) => {
    try {
      setUpdating(true);
      await adminAPI.updateStorageSettings(config);
      
      toast({
        title: "Configuration Updated",
        description: "Storage configuration has been updated successfully.",
      });
      
      // Refresh settings
      await loadStorageSettings();
    } catch (error) {
      console.error('Failed to update storage configuration:', error);
      toast({
        title: "Error",
        description: "Failed to update storage configuration. Please try again.",
        variant: "destructive",
      });
    } finally {
      setUpdating(false);
    }
  };

  // Storage operations
  const performStorageOperation = async (operation: string) => {
    try {
      setOperationLoading(prev => ({ ...prev, [operation]: true }));
      
      switch (operation) {
        case 'backup':
          await adminAPI.createBackup();
          toast({
            title: "Backup Created",
            description: "Manual backup has been created successfully.",
          });
          break;
        case 'cleanup':
          await adminAPI.triggerCleanup();
          toast({
            title: "Cleanup Complete",
            description: "Storage cleanup has been completed successfully.",
          });
          break;
        default:
          throw new Error('Unknown operation');
      }
      
      // Refresh settings after operation
      await loadStorageSettings();
      
    } catch (error) {
      console.error(`Failed to perform ${operation} operation:`, error);
      toast({
        title: "Operation Failed",
        description: `Failed to ${operation}. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setOperationLoading(prev => ({ ...prev, [operation]: false }));
    }
  };

  useEffect(() => {
    loadStorageSettings();
  }, []);

  // Helper functions
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
      case 'offline':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'healthy':
      case 'online':
        return <Badge className="bg-green-100 text-green-800">Online</Badge>;
      case 'warning':
        return <Badge className="bg-yellow-100 text-yellow-800">Warning</Badge>;
      case 'error':
      case 'offline':
        return <Badge className="bg-red-100 text-red-800">Offline</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  const formatBytes = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading storage settings...</div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Storage Settings</h1>
            <p className="text-gray-600 mt-2">Configure data storage and backup options</p>
          </div>
          
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => loadStorageSettings(true)}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </div>

        {storageSettings && (
          <>
            {/* Storage Overview Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Storage Usage</CardTitle>
                  <HardDrive className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm">Used</span>
                      <span className="text-sm font-medium">
                        {formatBytes(storageSettings.current_usage.total_size_gb * 1024 * 1024 * 1024)}
                      </span>
                    </div>
                    <Progress value={storageSettings.current_usage.usage_percentage} />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{storageSettings.current_usage.usage_percentage.toFixed(1)}% used</span>
                      <span>
                        {formatBytes(storageSettings.current_usage.available_space_gb * 1024 * 1024 * 1024)} available
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Auto Cleanup</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(storageSettings.auto_cleanup ? 'healthy' : 'warning')}
                    {getStatusBadge(storageSettings.auto_cleanup ? 'healthy' : 'warning')}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {storageSettings.auto_cleanup ? 'Enabled' : 'Disabled'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Compression</CardTitle>
                  <Archive className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    {getStatusIcon(storageSettings.compression_enabled ? 'healthy' : 'warning')}
                    {getStatusBadge(storageSettings.compression_enabled ? 'healthy' : 'warning')}
                  </div>
                  <p className="text-sm text-gray-600 mt-2">
                    {storageSettings.compression_enabled ? 'Enabled' : 'Disabled'}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Retention Policy */}
            <Card>
              <CardHeader>
                <CardTitle>Data Retention Policy</CardTitle>
                <CardDescription>Configure how long different types of data are stored</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Sentiment Data</label>
                    <div className="text-2xl font-bold">
                      {storageSettings.retention_policy.sentiment_data_days}
                    </div>
                    <p className="text-xs text-gray-500">days retention</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Stock Price Data</label>
                    <div className="text-2xl font-bold">
                      {storageSettings.retention_policy.stock_price_days}
                    </div>
                    <p className="text-xs text-gray-500">days retention</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Log Files</label>
                    <div className="text-2xl font-bold">
                      {storageSettings.retention_policy.log_files_days}
                    </div>
                    <p className="text-xs text-gray-500">days retention</p>
                  </div>
                  <div className="space-y-2">
                    <label className="text-sm font-medium">Backup Files</label>
                    <div className="text-2xl font-bold">
                      {storageSettings.retention_policy.backup_retention_days}
                    </div>
                    <p className="text-xs text-gray-500">days retention</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Storage Operations */}
            <Card>
              <CardHeader>
                <CardTitle>Storage Operations</CardTitle>
                <CardDescription>Backup and maintenance operations</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <Button 
                    variant="outline" 
                    className="justify-start h-16 flex flex-col gap-1"
                    onClick={() => performStorageOperation('backup')}
                    disabled={operationLoading.backup}
                  >
                    <div className="flex items-center gap-2">
                      <Archive className="h-4 w-4" />
                      <span>{operationLoading.backup ? 'Creating Backup...' : 'Create Manual Backup'}</span>
                    </div>
                    <span className="text-xs text-gray-500">Create a backup of all data</span>
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    className="justify-start h-16 flex flex-col gap-1"
                    onClick={() => performStorageOperation('cleanup')}
                    disabled={operationLoading.cleanup}
                  >
                    <div className="flex items-center gap-2">
                      <Trash2 className="h-4 w-4" />
                      <span>{operationLoading.cleanup ? 'Cleaning Up...' : 'Clean Old Data'}</span>
                    </div>
                    <span className="text-xs text-gray-500">Remove old data per retention policy</span>
                  </Button>
                </div>
              </CardContent>
            </Card>

            {/* Configuration Settings */}
            <Card>
              <CardHeader>
                <CardTitle>Configuration Settings</CardTitle>
                <CardDescription>Adjust storage behavior and performance</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Auto Cleanup</label>
                        <p className="text-xs text-gray-500">Automatically clean old data</p>
                      </div>
                      <Button
                        variant={storageSettings.auto_cleanup ? "default" : "outline"}
                        size="sm"
                        onClick={() => updateStorageConfiguration({ 
                          auto_cleanup: !storageSettings.auto_cleanup 
                        })}
                        disabled={updating}
                      >
                        {storageSettings.auto_cleanup ? 'Enabled' : 'Disabled'}
                      </Button>
                    </div>
                    
                    <div className="flex items-center justify-between">
                      <div>
                        <label className="text-sm font-medium">Data Compression</label>
                        <p className="text-xs text-gray-500">Compress stored data to save space</p>
                      </div>
                      <Button
                        variant={storageSettings.compression_enabled ? "default" : "outline"}
                        size="sm"
                        onClick={() => updateStorageConfiguration({ 
                          compression_enabled: !storageSettings.compression_enabled 
                        })}
                        disabled={updating}
                      >
                        {storageSettings.compression_enabled ? 'Enabled' : 'Disabled'}
                      </Button>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Storage Usage Warning */}
            {storageSettings.current_usage.usage_percentage > 80 && (
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Storage usage is high ({storageSettings.current_usage.usage_percentage.toFixed(1)}%). 
                  Consider running cleanup operations or increasing storage capacity.
                </AlertDescription>
              </Alert>
            )}
          </>
        )}
      </div>
    </AdminLayout>
  );
};

export default StorageSettings;
