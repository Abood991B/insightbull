
import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Badge } from "@/shared/components/ui/badge";
import { useToast } from "@/shared/hooks/use-toast";
import { adminAPI, WatchlistResponse, StockInfo } from "../../../api/services/admin.service";
import { RefreshCw, Plus, Trash2, TrendingUp, Activity, Users } from "lucide-react";

const WatchlistManager = () => {
  const [newStock, setNewStock] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [watchlistData, setWatchlistData] = useState<WatchlistResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const { toast } = useToast();

  // Load watchlist on component mount
  useEffect(() => {
    loadWatchlist();
  }, []);

  const loadWatchlist = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const data = await adminAPI.getWatchlist();
      setWatchlistData(data);
      
      if (showRefreshToast) {
        toast({
          title: "Watchlist Updated",
          description: "Watchlist has been refreshed successfully.",
        });
      }
    } catch (error) {
      console.error('Failed to load watchlist:', error);
      toast({
        title: "Error",
        description: "Failed to load watchlist. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleAddStock = async () => {
    if (!newStock.trim()) return;
    
    try {
      setIsUpdating(true);
      await adminAPI.addToWatchlist(newStock.toUpperCase(), companyName || undefined);
      
      toast({
        title: "Stock Added",
        description: `${newStock.toUpperCase()} has been added to the watchlist.`,
      });
      
      setNewStock("");
      setCompanyName("");
      await loadWatchlist(); // Reload the watchlist
    } catch (error) {
      console.error('Failed to add stock:', error);
      toast({
        title: "Error",
        description: `Failed to add ${newStock.toUpperCase()}. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  const handleRemoveStock = async (stock: string) => {
    try {
      setIsUpdating(true);
      await adminAPI.removeFromWatchlist(stock);
      
      toast({
        title: "Stock Removed",
        description: `${stock} has been removed from the watchlist.`,
      });
      
      await loadWatchlist(); // Reload the watchlist
    } catch (error) {
      console.error('Failed to remove stock:', error);
      toast({
        title: "Error",
        description: `Failed to remove ${stock}. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Watchlist Manager</h1>
            <p className="text-gray-600 mt-2">Manage the list of stocks being monitored</p>
          </div>
          
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => loadWatchlist(true)}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Add New Stock
            </CardTitle>
            <CardDescription>Add a new stock symbol to the monitoring list</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-4">
                <Input
                  value={newStock}
                  onChange={(e) => setNewStock(e.target.value.toUpperCase())}
                  placeholder="Enter stock symbol (e.g., NVDA)"
                  className="flex-1"
                  disabled={isUpdating}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddStock()}
                />
                <Input
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Company name (optional)"
                  className="flex-1"
                  disabled={isUpdating}
                  onKeyPress={(e) => e.key === 'Enter' && handleAddStock()}
                />
                <Button 
                  onClick={handleAddStock} 
                  disabled={!newStock.trim() || isUpdating}
                  className="flex items-center gap-2"
                >
                  <Plus className="h-4 w-4" />
                  {isUpdating ? "Adding..." : "Add Stock"}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5" />
              Current Watchlist ({watchlistData?.stocks.length || 0} Stocks)
            </CardTitle>
            <CardDescription>
              Stocks currently being monitored for sentiment analysis
              {watchlistData?.last_updated && (
                <span className="block text-xs mt-1">
                  Last updated: {new Date(watchlistData.last_updated).toLocaleString()}
                </span>
              )}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="flex justify-center py-8">
                <div className="text-gray-500">Loading watchlist...</div>
              </div>
            ) : !watchlistData?.stocks.length ? (
              <div className="text-center py-8 text-gray-500">
                No stocks in watchlist. Add some stocks to get started.
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {watchlistData.stocks.map((stock, index) => (
                  <div key={stock.symbol} className="flex items-center justify-between p-3 border rounded-lg hover:bg-gray-50">
                    <div className="flex items-center gap-3">
                      <span className="text-sm font-medium text-gray-500">#{index + 1}</span>
                      <div>
                        <div className="flex items-center gap-2">
                          <Badge variant="outline" className="font-medium">{stock.symbol}</Badge>
                          {stock.is_active ? (
                            <Badge className="bg-green-100 text-green-800 text-xs">Active</Badge>
                          ) : (
                            <Badge className="bg-gray-100 text-gray-800 text-xs">Inactive</Badge>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 mt-1">{stock.company_name}</p>
                        <p className="text-xs text-gray-500">{stock.sector}</p>
                        <p className="text-xs text-gray-400">
                          Added: {new Date(stock.added_date).toLocaleDateString()}
                        </p>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveStock(stock.symbol)}
                      disabled={isUpdating}
                      className="text-red-600 hover:text-red-700 hover:bg-red-50"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5" />
              Watchlist Statistics
            </CardTitle>
            <CardDescription>Overview of monitored stocks</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600">
                  {watchlistData?.total_stocks || 0}
                </div>
                <p className="text-sm text-gray-600">Total Stocks</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600">
                  {watchlistData?.active_stocks || 0}
                </div>
                <p className="text-sm text-gray-600">Active</p>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-yellow-600">
                  {(watchlistData?.total_stocks || 0) - (watchlistData?.active_stocks || 0)}
                </div>
                <p className="text-sm text-gray-600">Inactive</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </AdminLayout>
  );
};

export default WatchlistManager;
