
import AdminLayout from "@/components/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { useState } from "react";
import { useToast } from "@/hooks/use-toast";

const WatchlistManager = () => {
  const [newStock, setNewStock] = useState("");
  const { toast } = useToast();

  const magnificentSeven = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META', 'AMZN'];
  const topIXT = ['ADBE', 'CRM', 'INTC', 'ORCL', 'IBM', 'CSCO', 'QCOM', 'TXN', 'AVGO', 'AMD'];

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

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>Magnificent Seven</CardTitle>
              <CardDescription>The seven largest tech companies by market cap</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {magnificentSeven.map((stock) => (
                  <div key={stock} className="flex items-center gap-2">
                    <Badge variant="outline">{stock}</Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveStock(stock)}
                      className="text-red-600 hover:text-red-700"
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
              <CardTitle>Top 20 IXT Stocks</CardTitle>
              <CardDescription>Additional technology stocks being monitored</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                {topIXT.map((stock) => (
                  <div key={stock} className="flex items-center gap-2">
                    <Badge variant="outline">{stock}</Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveStock(stock)}
                      className="text-red-600 hover:text-red-700"
                    >
                      ×
                    </Button>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Watchlist Statistics</CardTitle>
            <CardDescription>Overview of monitored stocks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">27</div>
                <p className="text-sm text-gray-600">Total Stocks</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">25</div>
                <p className="text-sm text-gray-600">Active</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">2</div>
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
