
import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Label } from "@/shared/components/ui/label";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useToast } from "@/shared/hooks/use-toast";
import { adminAPI, APIConfiguration } from "../../../api/services/admin.service";
import { RefreshCw, Eye, EyeOff, CheckCircle, XCircle, AlertTriangle, Settings } from "lucide-react";

const ApiConfig = () => {
  const [apiConfig, setApiConfig] = useState<APIConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [showKeys, setShowKeys] = useState<{[key: string]: boolean}>({});
  const [formData, setFormData] = useState<{[key: string]: string}>({});
  const { toast } = useToast();

  // Load API configuration
  const loadApiConfiguration = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const data = await adminAPI.getAPIConfiguration();
      setApiConfig(data);
      
      // Initialize form data with existing keys (masked for configured ones)
      const initialFormData: {[key: string]: string} = {};
      Object.entries(data.apis).forEach(([key, config]) => {
        initialFormData[key] = config.configured ? '••••••••' : '';
      });
      setFormData(initialFormData);
      
      if (showRefreshToast) {
        toast({
          title: "Configuration Updated",
          description: "API configuration has been refreshed.",
        });
      }
    } catch (error) {
      console.error('Failed to load API configuration:', error);
      toast({
        title: "Error",
        description: "Failed to load API configuration. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Update API configuration
  const updateApiConfiguration = async (service: 'reddit' | 'finnhub' | 'newsapi' | 'marketaux', keys: Record<string, string>) => {
    try {
      setSaving(true);
      await adminAPI.updateAPIConfiguration({ service, keys });
      
      toast({
        title: "API Configuration Updated",
        description: `${service} API configuration has been updated successfully.`,
      });
      
      // Refresh configuration
      await loadApiConfiguration();
      
      // Reset form data for this service
      setFormData(prev => ({
        ...prev,
        [service]: '••••••••'
      }));
      
    } catch (error) {
      console.error(`Failed to update ${service} API configuration:`, error);
      toast({
        title: "Error",
        description: `Failed to update ${service} API configuration. Please try again.`,
        variant: "destructive",
      });
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => {
    loadApiConfiguration();
  }, []);

  // Helper functions
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
        return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'rate_limited':
        return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
      case 'error':
      case 'invalid':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-green-100 text-green-800">Active</Badge>;
      case 'rate_limited':
        return <Badge className="bg-yellow-100 text-yellow-800">Rate Limited</Badge>;
      case 'error':
        return <Badge className="bg-red-100 text-red-800">Error</Badge>;
      case 'invalid':
        return <Badge className="bg-red-100 text-red-800">Invalid Key</Badge>;
      default:
        return <Badge className="bg-gray-100 text-gray-800">Unknown</Badge>;
    }
  };

  const toggleKeyVisibility = (apiName: string) => {
    setShowKeys(prev => ({
      ...prev,
      [apiName]: !prev[apiName]
    }));
  };

  const handleInputChange = (apiName: string, value: string) => {
    setFormData(prev => ({
      ...prev,
      [apiName]: value
    }));
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading API configuration...</div>
        </div>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">API Configuration</h1>
            <p className="text-gray-600 mt-2">Manage external API keys and connections</p>
          </div>
          
          <div className="flex gap-3">
            <Button 
              variant="outline" 
              onClick={() => loadApiConfiguration(true)}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </div>

        {apiConfig && (
          <>
            {/* API Status Overview */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-5 w-5" />
                  API Status Overview
                </CardTitle>
                <CardDescription>
                  Current status of all external API connections
                  <br />
                  <span className="text-xs">Last updated: {new Date(apiConfig.last_updated).toLocaleString()}</span>
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  {Object.entries(apiConfig.apis).map(([apiName, config]) => (
                    <div key={apiName} className="flex items-center justify-between p-3 border rounded-lg">
                      <div>
                        <h3 className="font-medium capitalize">{apiName}</h3>
                        <p className="text-xs text-gray-500">
                          Last test: {new Date(config.last_test).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex items-center gap-2">
                        {getStatusIcon(config.status)}
                        {getStatusBadge(config.status)}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* API Configuration Forms */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {Object.entries(apiConfig.apis).map(([apiName, config]) => (
                <Card key={apiName}>
                  <CardHeader>
                    <CardTitle className="capitalize flex items-center justify-between">
                      {apiName === 'finnhub' ? 'FinHub API' : 
                       apiName === 'newsapi' ? 'NewsAPI' : 
                       apiName === 'marketaux' ? 'Marketaux API' : 
                       'Reddit API'}
                      <div className="flex items-center gap-2">
                        {getStatusIcon(config.status)}
                        {config.configured && (
                          <Badge variant="outline" className="text-xs">
                            Configured
                          </Badge>
                        )}
                      </div>
                    </CardTitle>
                    <CardDescription>
                      {apiName === 'reddit' && 'Configuration for Reddit social media data collection'}
                      {apiName === 'finnhub' && 'Configuration for financial market data'}
                      {apiName === 'newsapi' && 'Configuration for general news data collection'}
                      {apiName === 'marketaux' && 'Configuration for financial news and market data'}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div>
                      <Label htmlFor={`${apiName}-key`}>
                        {apiName === 'reddit' ? 'Client ID & Secret' : 'API Key'}
                      </Label>
                      <div className="relative">
                        <Input
                          id={`${apiName}-key`}
                          type={showKeys[apiName] ? 'text' : 'password'}
                          value={formData[apiName] || ''}
                          onChange={(e) => handleInputChange(apiName, e.target.value)}
                          placeholder={
                            apiName === 'reddit' ? 'Enter Reddit client credentials' :
                            apiName === 'finnhub' ? 'Enter FinHub API key' :
                            apiName === 'newsapi' ? 'Enter NewsAPI key' :
                            'Enter Marketaux API key'
                          }
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="absolute right-2 top-1/2 transform -translate-y-1/2 h-6 w-6 p-0"
                          onClick={() => toggleKeyVisibility(apiName)}
                          type="button"
                        >
                          {showKeys[apiName] ? 
                            <EyeOff className="h-3 w-3" /> : 
                            <Eye className="h-3 w-3" />
                          }
                        </Button>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <Button 
                        onClick={() => {
                          const keys = apiName === 'reddit' 
                            ? { client_id: formData[apiName], client_secret: formData[apiName] }
                            : { api_key: formData[apiName] };
                          updateApiConfiguration(apiName as any, keys);
                        }}
                        disabled={saving || !formData[apiName] || formData[apiName] === '••••••••'}
                        className="flex-1"
                      >
                        {saving ? 'Updating...' : `Update ${apiName === 'finnhub' ? 'FinHub' : apiName === 'newsapi' ? 'NewsAPI' : apiName === 'marketaux' ? 'Marketaux' : 'Reddit'}`}
                      </Button>
                    </div>

                    {config.status === 'error' && (
                      <Alert>
                        <AlertTriangle className="h-4 w-4" />
                        <AlertDescription>
                          There was an issue with this API configuration. Please check your credentials and try again.
                        </AlertDescription>
                      </Alert>
                    )}
                  </CardContent>
                </Card>
              ))}
            </div>
          </>
        )}
      </div>
    </AdminLayout>
  );
};

export default ApiConfig;
