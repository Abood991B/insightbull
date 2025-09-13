
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Badge } from "@/shared/components/ui/badge";
import { useState } from "react";
import { useToast } from "@/shared/hooks/use-toast";

const WatchlistManager = () => {
  const [newStock, setNewStock] = useState("");
  const { toast } = useToast();

  const currentWatchlist = [
    { symbol: 'MSFT', name: 'Microsoft Corp' },
    { symbol: 'NVDA', name: 'NVIDIA Corp' },
    { symbol: 'AAPL', name: 'Apple Inc.' },
    { symbol: 'AVGO', name: 'Broadcom Inc.' },
    { symbol: 'ORCL', name: 'Oracle Corp.' },
    { symbol: 'PLTR', name: 'Palantir Technologies Inc.' },
    { symbol: 'IBM', name: 'International Business Machines' },
    { symbol: 'CSCO', name: 'Cisco Systems Inc.' },
    { symbol: 'CRM', name: 'Salesforce Inc.' },
    { symbol: 'INTU', name: 'Intuit Inc.' },
    { symbol: 'NOW', name: 'ServiceNow Inc.' },
    { symbol: 'AMD', name: 'Advanced Micro Devices Inc.' },
    { symbol: 'ACN', name: 'Accenture PLC' },
    { symbol: 'TXN', name: 'Texas Instruments Inc.' },
    { symbol: 'QCOM', name: 'Qualcomm Inc.' },
    { symbol: 'ADBE', name: 'Adobe Inc.' },
    { symbol: 'AMAT', name: 'Applied Materials Inc.' },
    { symbol: 'PANW', name: 'Palo Alto Networks Inc.' },
    { symbol: 'MU', name: 'Micron Technology Inc.' },
    { symbol: 'CRWD', name: 'CrowdStrike Holdings Inc.' }
  ];

  const handleAddStock = () => {
    if (newStock.trim()) {
      toast({
        title: "Stock Added",
        description: `${newStock.toUpperCase()} has been added to the watchlist.`,
      });
      setNewStock("");
    }
  };

  const handleRemoveStock = (stock: string) => {
    toast({
      title: "Stock Removed",
      description: `${stock} has been removed from the watchlist.`,
    });
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Watchlist Manager</h1>
          <p className="text-gray-600 mt-2">Manage the list of stocks being monitored</p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Add New Stock</CardTitle>
            <CardDescription>Add a new stock symbol to the monitoring list</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex gap-4">
              <Input
                value={newStock}
                onChange={(e) => setNewStock(e.target.value)}
                placeholder="Enter stock symbol (e.g., NVDA)"
                className="flex-1"
              />
              <Button onClick={handleAddStock}>Add Stock</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Current Watchlist (20 Stocks)</CardTitle>
            <CardDescription>Technology stocks currently being monitored</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {currentWatchlist.map((stock, index) => (
                <div key={stock.symbol} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                  <div className="flex items-center gap-3">
                    <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                    <div>
                      <Badge variant="outline" className="font-medium">{stock.symbol}</Badge>
                      <p className="text-xs text-gray-600 mt-1">{stock.name}</p>
                    </div>
                  </div>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => handleRemoveStock(stock.symbol)}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50"
                  >
                    ×
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Watchlist Statistics</CardTitle>
            <CardDescription>Overview of monitored stocks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">20</div>
                <p className="text-sm text-gray-600">Total Stocks</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">20</div>
                <p className="text-sm text-gray-600">Active</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">0</div>
                <p className="text-sm text-gray-600">Issues</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

export default WatchlistManager;
