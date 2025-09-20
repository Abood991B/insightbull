
import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Badge } from "@/shared/components/ui/badge";
import { useToast } from "@/shared/hooks/use-toast";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/shared/components/ui/alert-dialog";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/shared/components/ui/popover";
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from "@/shared/components/ui/command";
import { adminAPI, WatchlistResponse, StockInfo } from "../../../api/services/admin.service";
import { RefreshCw, Plus, Trash2, TrendingUp, Activity, Users, Check, ChevronsUpDown } from "lucide-react";
import { cn } from "@/shared/utils/utils";

const WatchlistManager = () => {
  const [selectedStock, setSelectedStock] = useState("");
  const [selectedCompanyName, setSelectedCompanyName] = useState("");
  const [watchlistData, setWatchlistData] = useState<WatchlistResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [isUpdating, setIsUpdating] = useState(false);
  const [stockToRemove, setStockToRemove] = useState<string | null>(null);
  const [stockToToggle, setStockToToggle] = useState<{stock: string, currentStatus: boolean} | null>(null);
  const [availableStocks, setAvailableStocks] = useState<{ [symbol: string]: string }>({});
  const [stockSearchOpen, setStockSearchOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const { toast } = useToast();

  // Load watchlist and available stocks on component mount
  useEffect(() => {
    loadWatchlist();
    loadAvailableStocks();
  }, []);

  // Load available stocks based on search query with debounce
  useEffect(() => {
    const timer = setTimeout(() => {
      if (searchQuery.trim()) {
        loadAvailableStocks(searchQuery);
      } else {
        loadAvailableStocks();
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery]);

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
        description: error instanceof Error ? error.message : "Failed to load watchlist. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const loadAvailableStocks = async (query?: string) => {
    try {
      const stocks = await adminAPI.searchStockSymbols(query);
      setAvailableStocks(stocks);
    } catch (error) {
      console.error('Failed to load available stocks:', error);
      // Don't show toast for this as it's background loading
    }
  };

  const handleAddStock = async () => {
    const symbol = selectedStock.trim().toUpperCase();
    if (!symbol) {
      toast({
        title: "Invalid Input",
        description: "Please select a valid stock symbol.",
        variant: "destructive",
      });
      return;
    }

    try {
      setIsUpdating(true);
      const response = await adminAPI.addToWatchlist(symbol, selectedCompanyName || undefined);
      
      toast({
        title: "Stock Added",
        description: response.message || `${symbol} has been added to the watchlist.`,
      });
      
      setSelectedStock("");
      setSelectedCompanyName("");
      setStockSearchOpen(false);
      await loadWatchlist(); // Reload the watchlist
    } catch (error) {
      console.error('Failed to add stock:', error);
      const errorMessage = error instanceof Error ? error.message : `Failed to add ${symbol}. Please try again.`;
      toast({
        title: "Error",
        description: errorMessage,
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
      setStockToRemove(null);
    }
  };

  const handleToggleStock = async (stock: string, currentStatus: boolean) => {
    try {
      setIsUpdating(true);
      await adminAPI.toggleStock(stock);
      
      const action = currentStatus ? "deactivated" : "activated";
      toast({
        title: "Stock Updated",
        description: `${stock} has been ${action}.`,
      });
      
      await loadWatchlist(); // Reload the watchlist
    } catch (error) {
      console.error('Failed to toggle stock:', error);
      toast({
        title: "Error",
        description: `Failed to update ${stock}. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setIsUpdating(false);
      setStockToToggle(null);
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

        {/* Watchlist Metrics */}
        {watchlistData && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <TrendingUp className="h-8 w-8 text-blue-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Total Stocks</p>
                    <p className="text-2xl font-bold text-gray-900">{watchlistData.total_stocks}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Activity className="h-8 w-8 text-green-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Active Stocks</p>
                    <p className="text-2xl font-bold text-gray-900">{watchlistData.active_stocks}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
            
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center">
                  <Users className="h-8 w-8 text-purple-600" />
                  <div className="ml-4">
                    <p className="text-sm font-medium text-gray-600">Inactive Stocks</p>
                    <p className="text-2xl font-bold text-gray-900">{watchlistData.total_stocks - watchlistData.active_stocks}</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-5 w-5" />
              Add New Stock
            </CardTitle>
            <CardDescription>Search and select a stock symbol to add to the monitoring list</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex gap-4 items-end">
                <div className="flex-1">
                  <label className="text-sm font-medium text-gray-700 mb-2 block">
                    Select Stock Symbol
                  </label>
                  <Popover open={stockSearchOpen} onOpenChange={setStockSearchOpen}>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        role="combobox"
                        aria-expanded={stockSearchOpen}
                        className="w-full justify-between"
                        disabled={isUpdating}
                      >
                        {selectedStock
                          ? `${selectedStock} - ${selectedCompanyName}`
                          : "Select stock symbol..."}
                        <ChevronsUpDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-full p-0" align="start">
                      <Command>
                        <CommandInput 
                          placeholder="Search stocks..." 
                          value={searchQuery}
                          onValueChange={setSearchQuery}
                        />
                        <CommandList>
                          <CommandEmpty>No stocks found.</CommandEmpty>
                          <CommandGroup>
                            {Object.entries(availableStocks).map(([symbol, companyName]) => (
                              <CommandItem
                                key={symbol}
                                value={`${symbol} ${companyName}`}
                                onSelect={() => {
                                  setSelectedStock(symbol);
                                  setSelectedCompanyName(companyName);
                                  setStockSearchOpen(false);
                                  setSearchQuery("");
                                }}
                              >
                                <Check
                                  className={cn(
                                    "mr-2 h-4 w-4",
                                    selectedStock === symbol ? "opacity-100" : "opacity-0"
                                  )}
                                />
                                <div>
                                  <div className="font-medium">{symbol}</div>
                                  <div className="text-sm text-gray-500">{companyName}</div>
                                </div>
                              </CommandItem>
                            ))}
                          </CommandGroup>
                        </CommandList>
                      </Command>
                    </PopoverContent>
                  </Popover>
                  {selectedStock && (
                    <div className="mt-2 flex items-center justify-between text-sm text-gray-600">
                      <span>Selected: <span className="font-medium">{selectedStock}</span> - {selectedCompanyName}</span>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setSelectedStock("");
                          setSelectedCompanyName("");
                        }}
                        disabled={isUpdating}
                        className="h-6 px-2 text-xs"
                      >
                        Clear
                      </Button>
                    </div>
                  )}
                </div>
                <Button 
                  onClick={handleAddStock} 
                  disabled={!selectedStock.trim() || isUpdating}
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
                    <div className="flex gap-2">
                      <AlertDialog open={stockToToggle?.stock === stock.symbol} onOpenChange={(open) => !open && setStockToToggle(null)}>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setStockToToggle({stock: stock.symbol, currentStatus: stock.is_active})}
                            disabled={isUpdating}
                            className={`${stock.is_active 
                              ? 'text-yellow-600 hover:text-yellow-700 hover:bg-yellow-50' 
                              : 'text-green-600 hover:text-green-700 hover:bg-green-50'
                            }`}
                            title={stock.is_active ? 'Deactivate stock' : 'Activate stock'}
                          >
                            <Activity className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>{stock.is_active ? 'Deactivate' : 'Activate'} Stock</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to {stock.is_active ? 'deactivate' : 'activate'} {stock.symbol} in the watchlist?
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleToggleStock(stock.symbol, stock.is_active)}>
                              {stock.is_active ? 'Deactivate' : 'Activate'}
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                      <AlertDialog open={stockToRemove === stock.symbol} onOpenChange={(open) => !open && setStockToRemove(null)}>
                        <AlertDialogTrigger asChild>
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setStockToRemove(stock.symbol)}
                            disabled={isUpdating}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                            title="Remove from watchlist"
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Remove Stock</AlertDialogTitle>
                            <AlertDialogDescription>
                              Are you sure you want to remove {stock.symbol} from the watchlist? This action cannot be undone.
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction onClick={() => handleRemoveStock(stock.symbol)} className="bg-red-600 hover:bg-red-700">
                              Remove
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </div>
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
