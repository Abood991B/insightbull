
import AdminLayout from "@/components/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

const StorageSettings = () => {
  const [storageType, setStorageType] = useState("sqlite");
  const { toast } = useToast();

  const handleSaveSettings = () => {
    toast({
      title: "Settings Updated",
      description: "Storage configuration has been updated successfully.",
    });
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Storage Settings</h1>
          <p className="text-gray-600 mt-2">Configure data storage and backup options</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Storage Usage</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm">Used</span>
                  <span className="text-sm font-medium">12.3 GB</span>
                </div>
                <Progress value={75} />
                <div className="flex justify-between text-xs text-gray-500">
                  <span>12.3 GB used</span>
                  <span>16 GB total</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Database Status</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className="bg-green-100 text-green-800 mb-2">Online</Badge>
              <p className="text-sm text-gray-600">SQLite database operational</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Last Backup</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-lg font-semibold">2 hours ago</div>
              <p className="text-sm text-gray-600">Automatic backup completed</p>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Storage Configuration</CardTitle>
            <CardDescription>Select your preferred data storage method</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-2">Storage Type</label>
              <Select value={storageType} onValueChange={setStorageType}>
                <SelectTrigger className="w-64">
                  <SelectValue placeholder="Select storage type" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="sqlite">SQLite Database</SelectItem>
                  <SelectItem value="local">Local File Storage</SelectItem>
                  <SelectItem value="postgresql">PostgreSQL</SelectItem>
                  <SelectItem value="mysql">MySQL</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <Button onClick={handleSaveSettings}>Save Configuration</Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Data Management</CardTitle>
            <CardDescription>Backup and maintenance operations</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Button variant="outline" className="justify-start">
                Create Manual Backup
              </Button>
              <Button variant="outline" className="justify-start">
                Export Data
              </Button>
              <Button variant="outline" className="justify-start">
                Clean Old Data
              </Button>
              <Button variant="outline" className="justify-start text-red-600 hover:text-red-700">
                Reset Database
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Storage Statistics</CardTitle>
            <CardDescription>Detailed breakdown of data usage</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span>Sentiment Data</span>
                <div className="flex items-center gap-2">
                  <Progress value={60} className="w-20" />
                  <span className="text-sm">7.2 GB</span>
                </div>
              </div>
              <div className="flex justify-between">
                <span>Stock Price Data</span>
                <div className="flex items-center gap-2">
                  <Progress value={25} className="w-20" />
                  <span className="text-sm">3.1 GB</span>
                </div>
              </div>
              <div className="flex justify-between">
                <span>System Logs</span>
                <div className="flex items-center gap-2">
                  <Progress value={15} className="w-20" />
                  <span className="text-sm">2.0 GB</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

export default StorageSettings;
