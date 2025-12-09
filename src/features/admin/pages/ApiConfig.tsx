import React, { useState, useEffect } from "react";
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Input } from "@/shared/components/ui/input";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Switch } from "@/shared/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Slider } from "@/shared/components/ui/slider";
import { useToast } from "@/shared/hooks/use-toast";
import { formatDate } from "@/shared/utils/timezone";
import { adminAPI, APIConfiguration } from "../../../api/services/admin.service";
import { 
  RefreshCw, Eye, EyeOff, CheckCircle, XCircle, AlertTriangle, 
  Database, Brain, Sparkles, Globe, Newspaper, TrendingUp, MessageSquare,
  Key, ExternalLink
} from "lucide-react";

const ApiConfig = () => {
  const [apiConfig, setApiConfig] = useState<APIConfiguration | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [saving, setSaving] = useState(false);
  const [toggling, setToggling] = useState<{[key: string]: boolean}>({});
  const [showKeys, setShowKeys] = useState<{[key: string]: boolean}>({});
  const [formData, setFormData] = useState<{[key: string]: string}>({});
  const [aiSettings, setAiSettings] = useState<{verification_mode: string; confidence_threshold: number}>({
    verification_mode: 'low_confidence_and_neutral',
    confidence_threshold: 0.85
  });
  const { toast } = useToast();

  const loadApiConfiguration = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const data = await adminAPI.getAPIConfiguration();
      setApiConfig(data);
      
      const initialFormData: {[key: string]: string} = {};
      Object.entries(data.apis).forEach(([key, config]) => {
        if (key !== 'hackernews' && key !== 'gdelt' && key !== 'yfinance') {
          initialFormData[key] = (config as any).api_key || '';
        }
      });
      
      if (data.ai_services?.gemini) {
        initialFormData['gemini'] = data.ai_services.gemini.api_key || '';
        setAiSettings({
          verification_mode: data.ai_services.gemini.verification_mode || 'low_confidence_and_neutral',
          confidence_threshold: data.ai_services.gemini.confidence_threshold || 0.85
        });
      }
      
      setFormData(initialFormData);
      setShowKeys({});
      
      if (showRefreshToast) {
        toast({ title: "Configuration Refreshed", description: "API configuration has been updated." });
      }
    } catch (error) {
      console.error('Failed to load API configuration:', error);
      toast({ title: "Error", description: "Failed to load API configuration.", variant: "destructive" });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const updateApiConfiguration = async (service: string, keys: Record<string, string>) => {
    try {
      setSaving(true);
      await adminAPI.updateAPIConfiguration({ service: service as any, keys });
      toast({ title: "Success", description: `${service} API key updated successfully.` });
      await loadApiConfiguration();
    } catch (error) {
      console.error(`Failed to update ${service}:`, error);
      toast({ title: "Error", description: `Failed to update ${service} API key.`, variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  const toggleCollector = async (collectorName: string, enabled: boolean) => {
    try {
      setToggling(prev => ({ ...prev, [collectorName]: true }));
      await adminAPI.toggleCollector(collectorName, enabled);
      toast({ 
        title: enabled ? "Collector Enabled" : "Collector Disabled", 
        description: `${collectorName} has been ${enabled ? 'enabled' : 'disabled'}.` 
      });
      await loadApiConfiguration();
    } catch (error) {
      console.error(`Failed to toggle ${collectorName}:`, error);
      toast({ title: "Error", description: `Failed to toggle ${collectorName}.`, variant: "destructive" });
    } finally {
      setToggling(prev => ({ ...prev, [collectorName]: false }));
    }
  };

  const toggleAIService = async (serviceName: string, enabled: boolean) => {
    try {
      setToggling(prev => ({ ...prev, [serviceName]: true }));
      await adminAPI.toggleAIService(serviceName, enabled);
      toast({ 
        title: enabled ? "AI Verification Enabled" : "AI Verification Disabled", 
        description: `AI verification has been ${enabled ? 'enabled' : 'disabled'}.` 
      });
      await loadApiConfiguration();
    } catch (error) {
      console.error(`Failed to toggle ${serviceName}:`, error);
      toast({ title: "Error", description: `Failed to toggle AI service.`, variant: "destructive" });
    } finally {
      setToggling(prev => ({ ...prev, [serviceName]: false }));
    }
  };

  const updateAISettings = async () => {
    try {
      setSaving(true);
      await adminAPI.updateAIServiceSettings('gemini', aiSettings);
      toast({ title: "Settings Saved", description: "AI verification settings updated successfully." });
      await loadApiConfiguration();
    } catch (error) {
      console.error('Failed to update AI settings:', error);
      toast({ title: "Error", description: "Failed to update AI settings.", variant: "destructive" });
    } finally {
      setSaving(false);
    }
  };

  useEffect(() => { loadApiConfiguration(); }, []);

  const getCollectorIcon = (name: string) => {
    switch (name) {
      case 'hackernews': return <MessageSquare className="h-5 w-5" />;
      case 'gdelt': return <Globe className="h-5 w-5" />;
      case 'finnhub': return <TrendingUp className="h-5 w-5" />;
      case 'newsapi': return <Newspaper className="h-5 w-5" />;
      case 'yfinance': return <TrendingUp className="h-5 w-5" />;
      default: return <Database className="h-5 w-5" />;
    }
  };

  const getCollectorInfo = (name: string) => {
    switch (name) {
      case 'hackernews': return { displayName: 'Hacker News', description: 'Tech community discussions', requiresKey: false, link: null };
      case 'gdelt': return { displayName: 'GDELT', description: 'Global news (100+ countries)', requiresKey: false, link: null };
      case 'finnhub': return { displayName: 'Finnhub', description: 'Financial market data', requiresKey: true, link: 'https://finnhub.io/register' };
      case 'newsapi': return { displayName: 'NewsAPI', description: 'General news aggregation', requiresKey: true, link: 'https://newsapi.org/register' };
      case 'yfinance': return { displayName: 'Yahoo Finance', description: 'Financial news (unlimited)', requiresKey: false, link: null };
      default: return { displayName: name, description: '', requiresKey: true, link: null };
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      </AdminLayout>
    );
  }

  const geminiConfig = apiConfig?.ai_services?.gemini;

  return (
    <AdminLayout>
      <div className="space-y-8">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">API Configuration</h1>
            <p className="text-gray-500 mt-1">Manage data collectors and AI services</p>
          </div>
          <Button variant="outline" onClick={() => loadApiConfiguration(true)} disabled={refreshing}>
            <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {apiConfig && (
          <>
            {/* AI Services Section - Featured at top */}
            <Card className="border-2 border-purple-200 shadow-lg">
              <CardHeader className="bg-gradient-to-r from-purple-50 to-indigo-50 border-b border-purple-100">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="p-2 bg-purple-100 rounded-lg">
                      <Brain className="h-6 w-6 text-purple-600" />
                    </div>
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        AI Sentiment Verification
                        <Sparkles className="h-4 w-4 text-purple-500" />
                      </CardTitle>
                      <CardDescription>
                        {geminiConfig?.ai_verification_stats?.ai_model_name 
                          ? `${geminiConfig.ai_verification_stats.ai_model_name} AI enhances sentiment analysis accuracy`
                          : 'AI enhances sentiment analysis accuracy'}
                      </CardDescription>
                    </div>
                  </div>
                  {geminiConfig && (
                    <Badge className={
                      geminiConfig.ai_verification_stats?.api_key_status === 'valid' 
                        ? 'bg-green-100 text-green-800' 
                        : geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                          ? 'bg-red-100 text-red-800'
                          : geminiConfig.enabled 
                            ? 'bg-purple-100 text-purple-800' 
                            : 'bg-gray-100 text-gray-600'
                    }>
                      {geminiConfig.ai_verification_stats?.api_key_status === 'valid' 
                        ? 'Valid & Active'
                        : geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                          ? 'Invalid Key'
                          : geminiConfig.enabled ? 'Active' : 'Inactive'}
                    </Badge>
                  )}
                </div>
              </CardHeader>
              
              {geminiConfig && (
                <CardContent className="p-6 space-y-6">
                  {/* API Key Status Alert */}
                  {geminiConfig.ai_verification_stats?.api_key_status === 'invalid' && (
                    <Alert className="border-red-200 bg-red-50">
                      <XCircle className="h-4 w-4 text-red-600" />
                      <AlertDescription className="text-red-800">
                        <strong>Invalid API Key:</strong> {geminiConfig.ai_verification_stats?.last_error || 'The Gemini API key is not working. AI verification is disabled.'}
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {geminiConfig.ai_verification_stats?.api_key_status === 'valid' && (
                    <Alert className="border-green-200 bg-green-50">
                      <CheckCircle className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-800">
                        API key validated successfully. AI verification is ready.
                      </AlertDescription>
                    </Alert>
                  )}
                  
                  {/* Main Toggle - Very Prominent */}
                  <div className={`p-4 rounded-xl border-2 transition-all ${
                    geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                      ? 'bg-red-50 border-red-200'
                      : geminiConfig.enabled 
                        ? 'bg-purple-50 border-purple-300' 
                        : 'bg-gray-50 border-gray-200'
                  }`}>
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-4">
                        <div className={`p-3 rounded-full ${
                          geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                            ? 'bg-red-200'
                            : geminiConfig.enabled ? 'bg-purple-200' : 'bg-gray-200'
                        }`}>
                          <Brain className={`h-6 w-6 ${
                            geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                              ? 'text-red-700'
                              : geminiConfig.enabled ? 'text-purple-700' : 'text-gray-500'
                          }`} />
                        </div>
                        <div>
                          <h3 className={`text-lg font-semibold ${
                            geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                              ? 'text-red-900'
                              : geminiConfig.enabled ? 'text-purple-900' : 'text-gray-700'
                          }`}>
                            AI Verification
                          </h3>
                          <p className="text-sm text-gray-600">
                            {geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                              ? 'API key is invalid - please update with a valid key'
                              : geminiConfig.enabled 
                                ? `${geminiConfig.ai_verification_stats?.ai_model_name || 'AI'} is verifying uncertain predictions` 
                                : 'Enable to improve sentiment accuracy on low-confidence predictions'}
                          </p>
                        </div>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-sm font-medium ${
                          geminiConfig.ai_verification_stats?.api_key_status === 'invalid'
                            ? 'text-red-700'
                            : geminiConfig.enabled ? 'text-purple-700' : 'text-gray-500'
                        }`}>
                          {geminiConfig.ai_verification_stats?.api_key_status === 'invalid' ? 'INVALID' : geminiConfig.enabled ? 'ON' : 'OFF'}
                        </span>
                        <Switch
                          id="ai-toggle"
                          checked={geminiConfig.enabled || false}
                          disabled={toggling['gemini'] || !geminiConfig.api_key || geminiConfig.ai_verification_stats?.api_key_status === 'invalid'}
                          onCheckedChange={(checked) => toggleAIService('gemini', checked)}
                          className="data-[state=checked]:bg-purple-600 scale-125"
                        />
                      </div>
                    </div>
                    {!geminiConfig.api_key && (
                      <p className="text-xs text-amber-600 mt-2 flex items-center gap-1">
                        <AlertTriangle className="h-3 w-3" />
                        Configure API key below to enable AI verification
                      </p>
                    )}
                  </div>

                  <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {/* API Key Section */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-gray-800 flex items-center gap-2">
                        <Key className="h-4 w-4" />
                        API Key
                      </h4>
                      <div className="relative">
                        <Input
                          type={showKeys['gemini'] ? 'text' : 'password'}
                          value={formData['gemini'] || ''}
                          onChange={(e) => setFormData(prev => ({ ...prev, gemini: e.target.value }))}
                          placeholder="Enter Gemini API key"
                          className="pr-10"
                        />
                        <Button
                          variant="ghost"
                          size="sm"
                          className="absolute right-1 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                          onClick={() => setShowKeys(prev => ({ ...prev, gemini: !prev.gemini }))}
                        >
                          {showKeys['gemini'] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                        </Button>
                      </div>
                      <div className="flex items-center justify-between">
                        <a 
                          href="https://aistudio.google.com/app/apikey" 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-xs text-purple-600 hover:underline flex items-center gap-1"
                        >
                          Get free API key <ExternalLink className="h-3 w-3" />
                        </a>
                        <Button 
                          size="sm"
                          onClick={() => updateApiConfiguration('gemini', { api_key: formData['gemini'] })}
                          disabled={saving || !formData['gemini']}
                          className="bg-purple-600 hover:bg-purple-700"
                        >
                          {saving ? 'Saving...' : 'Save Key'}
                        </Button>
                      </div>
                    </div>

                    {/* Settings Section */}
                    <div className="space-y-4">
                      <h4 className="font-medium text-gray-800">Verification Settings</h4>
                      
                      <div className="space-y-3">
                        <div>
                          <label className="text-sm text-gray-600 mb-1.5 block">Verification Mode</label>
                          <Select 
                            value={aiSettings.verification_mode} 
                            onValueChange={(value) => setAiSettings(prev => ({ ...prev, verification_mode: value }))}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue />
                            </SelectTrigger>
                            <SelectContent>
                              <SelectItem value="none">None (ML Only)</SelectItem>
                              <SelectItem value="low_confidence">Low Confidence Only</SelectItem>
                              <SelectItem value="low_confidence_and_neutral">Low Confidence + Neutrals</SelectItem>
                              <SelectItem value="all">All Predictions</SelectItem>
                            </SelectContent>
                          </Select>
                        </div>

                        <div>
                          <div className="flex justify-between mb-1.5">
                            <label className="text-sm text-gray-600">Confidence Threshold</label>
                            <span className="text-sm font-medium text-purple-700">{(aiSettings.confidence_threshold * 100).toFixed(0)}%</span>
                          </div>
                          <Slider
                            value={[aiSettings.confidence_threshold * 100]}
                            onValueChange={([value]) => setAiSettings(prev => ({ ...prev, confidence_threshold: value / 100 }))}
                            min={70}
                            max={95}
                            step={5}
                            className="w-full"
                          />
                          <p className="text-xs text-gray-500 mt-1">ML predictions below this threshold trigger AI verification (Default: 85%)</p>
                        </div>

                        <Button 
                          variant="outline" 
                          size="sm" 
                          onClick={updateAISettings}
                          disabled={saving}
                          className="w-full"
                        >
                          {saving ? 'Saving...' : 'Save Settings'}
                        </Button>
                      </div>
                    </div>
                  </div>

                  {/* Stats */}
                  {geminiConfig.ai_verification_stats && (geminiConfig.ai_verification_stats.total_analyzed || 0) > 0 && (
                    <div className="pt-4 border-t">
                      <h4 className="font-medium text-gray-800 mb-3">Usage Statistics</h4>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-gray-800">
                            {geminiConfig.ai_verification_stats.total_analyzed?.toLocaleString() || 0}
                          </p>
                          <p className="text-xs text-gray-500">Total Analyzed</p>
                        </div>
                        <div className="text-center p-3 bg-purple-50 rounded-lg">
                          <p className="text-2xl font-bold text-purple-700">
                            {geminiConfig.ai_verification_stats.ai_verified_count?.toLocaleString() || 0}
                          </p>
                          <p className="text-xs text-gray-500">AI Verified</p>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-gray-800">
                            {(geminiConfig.ai_verification_stats.ai_verification_rate || 0).toFixed(1)}%
                          </p>
                          <p className="text-xs text-gray-500">Verification Rate</p>
                        </div>
                        <div className="text-center p-3 bg-gray-50 rounded-lg">
                          <p className="text-2xl font-bold text-gray-800">
                            {((geminiConfig.ai_verification_stats.avg_ml_confidence || 0) * 100).toFixed(0)}%
                          </p>
                          <p className="text-xs text-gray-500">Avg Confidence</p>
                        </div>
                      </div>
                    </div>
                  )}
                </CardContent>
              )}
            </Card>

            {/* Data Collectors Section */}
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Database className="h-5 w-5 text-gray-600" />
                <h2 className="text-lg font-semibold text-gray-900">Data Collectors</h2>
                <Badge variant="outline" className="ml-2">
                  {Object.values(apiConfig.apis).filter((c: any) => c.enabled !== false).length}/{Object.keys(apiConfig.apis).length} enabled
                </Badge>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {Object.entries(apiConfig.apis)
                  .sort(([nameA], [nameB]) => {
                    const infoA = getCollectorInfo(nameA);
                    const infoB = getCollectorInfo(nameB);
                    // Free collectors first (requiresKey=false), then API-required
                    if (!infoA.requiresKey && infoB.requiresKey) return -1;
                    if (infoA.requiresKey && !infoB.requiresKey) return 1;
                    return 0;
                  })
                  .map(([name, config]) => {
                  const info = getCollectorInfo(name);
                  const isEnabled = (config as any).enabled !== false;
                  const isToggling = toggling[name] || false;
                  const hasApiKey = !info.requiresKey || !!(config as any).api_key;
                  const canToggle = hasApiKey; // Can only toggle if key is not required OR key is present
                  
                  return (
                    <Card key={name} className={`transition-all ${!isEnabled ? 'opacity-60' : ''}`}>
                      <CardContent className="p-4">
                        {/* Header */}
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className={`p-2 rounded-lg ${isEnabled ? 'bg-blue-100' : 'bg-gray-100'}`}>
                              {getCollectorIcon(name)}
                            </div>
                            <div>
                              <h3 className="font-medium text-gray-900">{info.displayName}</h3>
                              <p className="text-xs text-gray-500">{info.description}</p>
                            </div>
                          </div>
                          <Switch
                            checked={isEnabled}
                            disabled={isToggling || !canToggle}
                            onCheckedChange={(checked) => toggleCollector(name, checked)}
                            className="data-[state=checked]:bg-green-500"
                          />
                        </div>

                        {/* Status */}
                        <div className="flex items-center gap-2 mb-3">
                          {!hasApiKey ? (
                            <>
                              <AlertTriangle className="h-4 w-4 text-amber-500" />
                              <span className="text-sm text-amber-700">API key required</span>
                            </>
                          ) : config.status === 'active' ? (
                            <>
                              <CheckCircle className="h-4 w-4 text-green-500" />
                              <span className="text-sm text-green-700">Connected</span>
                            </>
                          ) : config.status === 'error' ? (
                            <>
                              <XCircle className="h-4 w-4 text-red-500" />
                              <span className="text-sm text-red-700">Error</span>
                            </>
                          ) : (
                            <>
                              <AlertTriangle className="h-4 w-4 text-yellow-500" />
                              <span className="text-sm text-yellow-700">Not configured</span>
                            </>
                          )}
                          {config.last_test && (
                            <span className="text-xs text-gray-400 ml-auto">{formatDate(config.last_test)}</span>
                          )}
                        </div>

                        {/* Error message */}
                        {config.status === 'error' && (config as any).error && (
                          <Alert variant="destructive" className="mb-3 py-2">
                            <AlertDescription className="text-xs">{(config as any).error}</AlertDescription>
                          </Alert>
                        )}

                        {/* API Key input or Free label */}
                        {info.requiresKey ? (
                          <div className="space-y-2">
                            <div className="relative">
                              <Input
                                type={showKeys[name] ? 'text' : 'password'}
                                value={formData[name] || ''}
                                onChange={(e) => setFormData(prev => ({ ...prev, [name]: e.target.value }))}
                                placeholder="API key"
                                className="pr-8 text-sm h-9"
                              />
                              <Button
                                variant="ghost"
                                size="sm"
                                className="absolute right-0.5 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
                                onClick={() => setShowKeys(prev => ({ ...prev, [name]: !prev[name] }))}
                              >
                                {showKeys[name] ? <EyeOff className="h-3 w-3" /> : <Eye className="h-3 w-3" />}
                              </Button>
                            </div>
                            <div className="flex items-center justify-between">
                              {info.link && (
                                <a href={info.link} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                                  Get key <ExternalLink className="h-3 w-3" />
                                </a>
                              )}
                              <Button 
                                size="sm" 
                                variant="outline"
                                onClick={() => updateApiConfiguration(name, { api_key: formData[name] })}
                                disabled={saving || !formData[name]}
                                className="h-7 text-xs ml-auto"
                              >
                                Save
                              </Button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2 p-2 bg-green-50 rounded-lg">
                            <CheckCircle className="h-4 w-4 text-green-600" />
                            <span className="text-sm text-green-700">Free - No API key required</span>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            </div>
          </>
        )}
      </div>
    </AdminLayout>
  );
};

export default ApiConfig;
