
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";

const AdminDashboard = () => {
  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Admin Dashboard</h1>
          <p className="text-gray-600 mt-2">System overview and management tools</p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">System Status</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className="bg-green-100 text-green-800">Online</Badge>
              <p className="text-sm text-gray-600 mt-2">All systems operational</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Data Pipeline</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className="bg-blue-100 text-blue-800">Running</Badge>
              <p className="text-sm text-gray-600 mt-2">Last run: 5 minutes ago</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">API Status</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className="bg-green-100 text-green-800">Connected</Badge>
              <p className="text-sm text-gray-600 mt-2">All APIs responding</p>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader>
              <CardTitle className="text-lg">Storage</CardTitle>
            </CardHeader>
            <CardContent>
              <Badge className="bg-yellow-100 text-yellow-800">75% Full</Badge>
              <p className="text-sm text-gray-600 mt-2">12.3GB / 16GB used</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Recent Activity</CardTitle>
              <CardDescription>Latest system events and operations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <div className="flex justify-between">
                  <span className="text-sm">Data collection completed</span>
                  <span className="text-xs text-gray-500">2 min ago</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Sentiment analysis processed</span>
                  <span className="text-xs text-gray-500">5 min ago</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">Database backup created</span>
                  <span className="text-xs text-gray-500">1 hour ago</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm">API configuration updated</span>
                  <span className="text-xs text-gray-500">3 hours ago</span>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Quick Actions</CardTitle>
              <CardDescription>Common administrative tasks</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-3">
                <div className="p-3 border rounded hover:bg-gray-50 cursor-pointer">
                  <h4 className="font-medium">Model Accuracy</h4>
                  <p className="text-xs text-gray-600">View performance metrics</p>
                </div>
                <div className="p-3 border rounded hover:bg-gray-50 cursor-pointer">
                  <h4 className="font-medium">API Config</h4>
                  <p className="text-xs text-gray-600">Manage API keys</p>
                </div>
                <div className="p-3 border rounded hover:bg-gray-50 cursor-pointer">
                  <h4 className="font-medium">Watchlist</h4>
                  <p className="text-xs text-gray-600">Update stock list</p>
                </div>
                <div className="p-3 border rounded hover:bg-gray-50 cursor-pointer">
                  <h4 className="font-medium">System Logs</h4>
                  <p className="text-xs text-gray-600">View system logs</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </AdminLayout>
  );
};

export default AdminDashboard;
