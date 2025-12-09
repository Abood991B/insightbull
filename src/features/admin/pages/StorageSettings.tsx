
import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { Progress } from "@/shared/components/ui/progress";
import { useToast } from "@/shared/hooks/use-toast";
import { 
  adminAPI, 
  StorageSettings as StorageSettingsType,
  DatabaseSchema,
  TableData,
  DatabaseStats
} from "../../../api/services/admin.service";
import { 
  RefreshCw, 
  Database, 
  HardDrive, 
  Archive,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Table,
  Eye,
  ChevronRight,
  ChevronDown,
  Download
} from "lucide-react";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/shared/components/ui/collapsible";
import {
  Table as TableComponent,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/shared/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/shared/components/ui/dialog";

const StorageSettings = () => {
  const [storageSettings, setStorageSettings] = useState<StorageSettingsType | null>(null);
  const [databaseSchema, setDatabaseSchema] = useState<DatabaseSchema | null>(null);
  const [databaseStats, setDatabaseStats] = useState<DatabaseStats | null>(null);
  const [selectedTableData, setSelectedTableData] = useState<TableData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [operationLoading, setOperationLoading] = useState<{[key: string]: boolean}>({});
  const [expandedTables, setExpandedTables] = useState<{[key: string]: boolean}>({});
  const [showTableDialog, setShowTableDialog] = useState(false);
  const [tableDataLoading, setTableDataLoading] = useState(false);
  const { toast } = useToast();

  // Load storage settings
  const loadStorageSettings = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const [storageData, schemaData, statsData] = await Promise.all([
        adminAPI.getStorageSettings(),
        adminAPI.getDatabaseSchema(),
        adminAPI.getDatabaseStats()
      ]);
      
      setStorageSettings(storageData);
      setDatabaseSchema(schemaData);
      setDatabaseStats(statsData);
      
      if (showRefreshToast) {
        toast({
          title: "Settings Updated",
          description: "Storage settings and database info have been refreshed.",
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

  // Load table data
  const loadTableData = async (tableName: string) => {
    try {
      setTableDataLoading(true);
      const data = await adminAPI.getTableData(tableName, 50, 0);
      setSelectedTableData(data);
      setShowTableDialog(true);
    } catch (error) {
      console.error('Failed to load table data:', error);
      toast({
        title: "Error",
        description: "Failed to load table data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setTableDataLoading(false);
    }
  };

  // Export table to CSV
  const exportTableToCSV = async (tableName: string) => {
    try {
      setOperationLoading(prev => ({ ...prev, [`export-${tableName}`]: true }));
      await adminAPI.exportTableToCSV(tableName, 10000);
      toast({
        title: "Export Successful",
        description: `${tableName} has been exported to CSV format.`,
      });
    } catch (error) {
      console.error('Failed to export table:', error);
      toast({
        title: "Export Failed",
        description: "Failed to export table to CSV. Please try again.",
        variant: "destructive",
      });
    } finally {
      setOperationLoading(prev => ({ ...prev, [`export-${tableName}`]: false }));
    }
  };

  // Toggle table expansion
  const toggleTableExpansion = (tableName: string) => {
    setExpandedTables(prev => ({
      ...prev,
      [tableName]: !prev[tableName]
    }));
  };

  // Database cleanup functions removed - using unified Stock table structure

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
            <p className="text-gray-600 mt-2">View storage metrics, manage backups, and clean old data</p>
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
                        {storageSettings.current_usage.total_size_mb 
                          ? `${storageSettings.current_usage.total_size_mb.toFixed(2)} MB`
                          : '0 MB'}
                      </span>
                    </div>
                    <Progress value={storageSettings.current_usage.usage_percentage || 0} />
                    <div className="flex justify-between text-xs text-gray-500">
                      <span>{(storageSettings.current_usage.usage_percentage || 0).toFixed(1)}% used</span>
                      <span>
                        {storageSettings.current_usage.available_space_gb 
                          ? `${storageSettings.current_usage.available_space_gb.toFixed(2)} GB`
                          : '5.00 GB'} available
                      </span>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Total Records</CardTitle>
                  <Database className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <div className="text-2xl font-bold">{storageSettings.total_records?.toLocaleString() || 0}</div>
                  <p className="text-xs text-gray-500 mt-2">
                    Sentiment: {storageSettings.sentiment_records?.toLocaleString() || 0} | 
                    Prices: {storageSettings.stock_price_records?.toLocaleString() || 0}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">Storage Health</CardTitle>
                  {getStatusIcon(storageSettings.storage_health || 'healthy')}
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(storageSettings.storage_health || 'healthy')}
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    {storageSettings.oldest_record && storageSettings.newest_record
                      ? `Data from ${new Date(storageSettings.oldest_record).toLocaleDateString()} to ${new Date(storageSettings.newest_record).toLocaleDateString()}`
                      : 'No data available'}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Storage Operations */}
            <Card>
              <CardHeader>
                <CardTitle>Storage Operations</CardTitle>
                <CardDescription>Manage database backups</CardDescription>
              </CardHeader>
              <CardContent>
                <Button 
                  variant="outline" 
                  className="w-full justify-start h-20 flex flex-col items-start gap-1 p-4"
                  onClick={() => performStorageOperation('backup')}
                  disabled={operationLoading.backup}
                >
                  <div className="flex items-center gap-2">
                    <Archive className="h-5 w-5" />
                    <span className="font-semibold">{operationLoading.backup ? 'Creating Backup...' : 'Create Manual Backup'}</span>
                  </div>
                  <span className="text-xs text-gray-500 text-left">Create a backup of the entire database</span>
                </Button>
              </CardContent>
            </Card>

            {/* Database Type Information */}
            <Card>
              <CardHeader>
                <CardTitle>Database Configuration</CardTitle>
                <CardDescription>Current database storage solution</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Database className="h-5 w-5 text-blue-600" />
                      <div>
                        <div className="font-medium">SQLite Database</div>
                        <div className="text-sm text-gray-500">Local file-based database storage</div>
                      </div>
                    </div>
                    <Badge className="bg-green-100 text-green-800">Active</Badge>
                  </div>
                  
                  <div className="text-sm text-gray-600">
                    <div className="mb-1"><strong>Storage Location:</strong></div>
                    <code className="text-xs bg-gray-100 px-2 py-1 rounded">backend/data/insight_stock.db</code>
                    <p className="mt-2 text-xs">All sentiment data, stock prices, and system logs are stored in the SQLite database file.</p>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Database Schema and Data */}
            {databaseSchema && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Database className="h-5 w-5" />
                    Database Schema
                  </CardTitle>
                  <CardDescription>
                    View database structure, tables, and data
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Database Overview */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-gray-50 rounded-lg">
                      <div>
                        <div className="text-sm font-medium text-gray-500">Database</div>
                        <div className="text-lg font-semibold">{databaseSchema.database_name}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-500">Total Tables</div>
                        <div className="text-lg font-semibold">{databaseSchema.total_tables}</div>
                      </div>
                      <div>
                        <div className="text-sm font-medium text-gray-500">Total Records</div>
                        <div className="text-lg font-semibold">
                          {databaseStats ? databaseStats.total_records.toLocaleString() : 'Loading...'}
                        </div>
                      </div>
                    </div>

                    {/* Tables List */}
                    <div className="space-y-2">
                      {Object.entries(databaseSchema.tables).map(([tableName, tableInfo]) => (
                        <Collapsible 
                          key={tableName}
                          open={expandedTables[tableName]}
                          onOpenChange={() => toggleTableExpansion(tableName)}
                        >
                          <CollapsibleTrigger asChild>
                            <div className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                              <div className="flex items-center gap-3">
                                {expandedTables[tableName] ? (
                                  <ChevronDown className="h-4 w-4" />
                                ) : (
                                  <ChevronRight className="h-4 w-4" />
                                )}
                                <Table className="h-4 w-4" />
                                <div>
                                  <div className="font-medium">{tableName}</div>
                                  <div className="text-sm text-gray-500">
                                    {tableInfo.record_count.toLocaleString()} records | {tableInfo.columns.length} columns
                                  </div>
                                </div>
                              </div>
                              <div className="flex items-center gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    exportTableToCSV(tableName);
                                  }}
                                  disabled={operationLoading[`export-${tableName}`]}
                                  className="flex items-center gap-1"
                                >
                                  <Download className="h-3 w-3" />
                                  {operationLoading[`export-${tableName}`] ? 'Exporting...' : 'Download CSV'}
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={(e) => {
                                    e.stopPropagation();
                                    loadTableData(tableName);
                                  }}
                                  disabled={tableDataLoading}
                                  className="flex items-center gap-1"
                                >
                                  <Eye className="h-3 w-3" />
                                  View Data
                                </Button>
                              </div>
                            </div>
                          </CollapsibleTrigger>
                          <CollapsibleContent>
                            <div className="ml-6 mt-2 p-4 border-l-2 border-gray-200">
                              <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
                                {/* Columns */}
                                <div>
                                  <h4 className="font-medium mb-2">Columns ({tableInfo.columns.length})</h4>
                                  <div className="space-y-1 max-h-40 overflow-y-auto">
                                    {tableInfo.columns.map((column) => (
                                      <div key={column.name} className="flex items-center justify-between text-sm p-2 bg-gray-50 rounded">
                                        <div className="flex items-center gap-2">
                                          <span className="font-medium">{column.name}</span>
                                          {column.primary_key && (
                                            <Badge variant="outline" className="text-xs">PK</Badge>
                                          )}
                                        </div>
                                        <div className="text-gray-500">
                                          {column.type}
                                          {!column.nullable && <span className="text-red-500 ml-1">*</span>}
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                </div>

                                {/* Relationships & Indexes */}
                                <div className="space-y-4">
                                  {tableInfo.foreign_keys.length > 0 && (
                                    <div>
                                      <h4 className="font-medium mb-2">Foreign Keys ({tableInfo.foreign_keys.length})</h4>
                                      <div className="space-y-1 max-h-20 overflow-y-auto">
                                        {tableInfo.foreign_keys.map((fk, index) => (
                                          <div key={index} className="text-sm p-2 bg-blue-50 rounded">
                                            <span className="font-medium">{fk.constrained_columns.join(', ')}</span>
                                            <span className="text-gray-500"> -&gt; </span>
                                            <span>{fk.referred_table}.{fk.referred_columns.join(', ')}</span>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}

                                  {tableInfo.indexes.length > 0 && (
                                    <div>
                                      <h4 className="font-medium mb-2">Indexes ({tableInfo.indexes.length})</h4>
                                      <div className="space-y-1 max-h-20 overflow-y-auto">
                                        {tableInfo.indexes.map((index) => (
                                          <div key={index.name} className="text-sm p-2 bg-green-50 rounded">
                                            <div className="flex items-center justify-between">
                                              <span className="font-medium">{index.name}</span>
                                              {index.unique && (
                                                <Badge variant="outline" className="text-xs">UNIQUE</Badge>
                                              )}
                                            </div>
                                            <div className="text-gray-500">{index.column_names.join(', ')}</div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          </CollapsibleContent>
                        </Collapsible>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Database Statistics */}
            {databaseStats && (
              <Card>
                <CardHeader>
                  <CardTitle>Database Statistics</CardTitle>
                  <CardDescription>Detailed database usage and activity metrics</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    {Object.entries(databaseStats.table_counts).map(([tableName, count]) => (
                      <div key={tableName} className="p-3 border rounded-lg">
                        <div className="text-sm font-medium text-gray-500 capitalize">
                          {tableName.replace('_', ' ')}
                        </div>
                        <div className="text-lg font-semibold">{count.toLocaleString()}</div>
                      </div>
                    ))}
                  </div>
                  
                  <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="p-3 bg-blue-50 rounded-lg">
                      <div className="text-sm font-medium text-blue-700">Recent Activity (24h)</div>
                      <div className="text-sm text-blue-600 mt-1">
                        {databaseStats.recent_activity.sentiment_records_24h} sentiment records, {' '}
                        {databaseStats.recent_activity.log_entries_24h} log entries
                      </div>
                    </div>
                    <div className="p-3 bg-green-50 rounded-lg">
                      <div className="text-sm font-medium text-green-700">File Size</div>
                      <div className="text-sm text-green-600 mt-1">
                        {databaseStats.file_size.mb} MB ({databaseStats.file_size.gb.toFixed(4)} GB)
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Table Data Dialog */}
            <Dialog open={showTableDialog} onOpenChange={setShowTableDialog}>
              <DialogContent className="max-w-6xl max-h-[80vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>
                    {selectedTableData ? `${selectedTableData.table_name} Data` : 'Table Data'}
                  </DialogTitle>
                  <DialogDescription>
                    {selectedTableData && (
                      `Showing ${selectedTableData.returned_records} of ${selectedTableData.total_records.toLocaleString()} records`
                    )}
                  </DialogDescription>
                </DialogHeader>
                {selectedTableData && (
                  <div className="mt-4">
                    <TableComponent>
                      <TableHeader>
                        <TableRow>
                          {Object.keys(selectedTableData.data[0] || {}).map((column) => (
                            <TableHead key={column} className="font-medium">
                              {column}
                            </TableHead>
                          ))}
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedTableData.data.map((row, index) => (
                          <TableRow key={index}>
                            {Object.values(row).map((value, cellIndex) => (
                              <TableCell key={cellIndex} className="max-w-xs truncate">
                                {value !== null && value !== undefined ? String(value) : '-'}
                              </TableCell>
                            ))}
                          </TableRow>
                        ))}
                      </TableBody>
                    </TableComponent>
                    {selectedTableData.total_records > selectedTableData.returned_records && (
                      <div className="mt-4 text-sm text-gray-500 text-center">
                        Showing first {selectedTableData.returned_records} records. 
                        Total: {selectedTableData.total_records.toLocaleString()}
                      </div>
                    )}
                  </div>
                )}
              </DialogContent>
            </Dialog>

            {/* Database cleanup section removed - using unified Stock table structure */}

            {/* Storage Usage Warning */}
            {storageSettings.current_usage.usage_percentage > 80 && (
              <Card className="border-yellow-200 bg-yellow-50">
                <CardContent className="pt-6">
                  <div className="flex items-start gap-3">
                    <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
                    <div>
                      <p className="font-medium text-yellow-900">High Storage Usage</p>
                      <p className="text-sm text-yellow-800 mt-1">
                        Storage usage is at {storageSettings.current_usage.usage_percentage.toFixed(1)}%. 
                        Consider increasing storage capacity or archiving old data.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        )}
      </div>
    </AdminLayout>
  );
};

export default StorageSettings;
