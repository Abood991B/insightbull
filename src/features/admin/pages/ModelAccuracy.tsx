import React, { useState, useEffect } from 'react';
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import { Button } from "@/shared/components/ui/button";
import { SENTIMENT_THRESHOLDS } from "@/shared/utils/sentimentUtils";
import { Tabs, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { useToast } from "@/shared/hooks/use-toast";
import { formatDateTime } from "@/shared/utils/timezone";
import { adminAPI, ModelAccuracy as ModelAccuracyType, SentimentEngineMetrics, SourceMetrics, BenchmarkResponse } from "../../../api/services/admin.service";
import { 
  RefreshCw, TrendingUp, Clock, Database, CheckCircle, 
  Cpu, BarChart3, Activity, Globe, MessageSquare, Newspaper, Brain, Sparkles,
  Play, Target, AlertTriangle, Info
} from "lucide-react";

// Source display configuration
const SOURCE_CONFIG: Record<string, { label: string; icon: React.ReactNode; color: string }> = {
  hackernews: { label: 'HackerNews', icon: <MessageSquare className="h-4 w-4" />, color: 'orange' },
  finnhub: { label: 'Finnhub', icon: <TrendingUp className="h-4 w-4" />, color: 'blue' },
  newsapi: { label: 'NewsAPI', icon: <Newspaper className="h-4 w-4" />, color: 'purple' },
  gdelt: { label: 'GDELT', icon: <Globe className="h-4 w-4" />, color: 'indigo' },
  yfinance: { label: 'Yahoo Finance', icon: <TrendingUp className="h-4 w-4" />, color: 'violet' },
};

const ModelAccuracy = () => {
  const { toast } = useToast();
  const [modelData, setModelData] = useState<ModelAccuracyType | null>(null);
  const [engineMetrics, setEngineMetrics] = useState<SentimentEngineMetrics | null>(null);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [runningBenchmark, setRunningBenchmark] = useState(false);
  const [viewType, setViewType] = useState<'overall' | 'latest'>('overall');

  const loadModelAccuracy = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const [accuracy, metrics, benchmark] = await Promise.all([
        adminAPI.getModelAccuracy(viewType),
        adminAPI.getSentimentEngineMetrics(),
        adminAPI.getBenchmarkResults()
      ]);
      setModelData(accuracy);
      setEngineMetrics(metrics);
      setBenchmarkData(benchmark);
      
      if (showRefreshToast) {
        toast({
          title: "Data Updated",
          description: "Metrics have been refreshed.",
        });
      }
    } catch (error) {
      console.error('Failed to load model accuracy:', error);
      toast({
        title: "Error",
        description: "Failed to load metrics data.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const runBenchmark = async (force: boolean = false) => {
    try {
      setRunningBenchmark(true);
      toast({
        title: "Running Benchmark",
        description: "Evaluating model on Financial PhraseBank dataset (5,057 samples). This may take 1-2 minutes...",
      });

      const result = await adminAPI.runBenchmark(force);
      
      if (result.success) {
        toast({
          title: "Benchmark Complete",
          description: `Model accuracy: ${(result.results.accuracy * 100).toFixed(1)}% on ${result.results.dataset_size} samples`,
        });
        await loadModelAccuracy();
      }
    } catch (error: any) {
      console.error('Failed to run benchmark:', error);
      toast({
        title: "Benchmark Failed",
        description: error.message || "Failed to run benchmark evaluation.",
        variant: "destructive",
      });
    } finally {
      setRunningBenchmark(false);
    }
  };

  useEffect(() => {
    loadModelAccuracy();
  }, []);

  useEffect(() => {
    if (!loading) {
      loadModelAccuracy();
    }
  }, [viewType]);

  // Get confidence badge color
  const getConfidenceBadge = (confidence: number) => {
    if (confidence >= 0.85) return <Badge className="bg-green-100 text-green-800">{(confidence * 100).toFixed(1)}%</Badge>;
    if (confidence >= 0.85) return <Badge className="bg-blue-100 text-blue-800">{(confidence * 100).toFixed(1)}%</Badge>;
    if (confidence >= 0.60) return <Badge className="bg-yellow-100 text-yellow-800">{(confidence * 100).toFixed(1)}%</Badge>;
    return <Badge className="bg-red-100 text-red-800">{(confidence * 100).toFixed(1)}%</Badge>;
  };

  // Get performance level color
  const getPerformanceColor = (value: number) => {
    if (value >= 0.90) return 'text-green-600';
    if (value >= 0.80) return 'text-blue-600';
    if (value >= 0.70) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Simplified source card - shows REAL metrics only
  const SourceCard = ({ sourceKey, metrics }: { sourceKey: string; metrics: SourceMetrics }) => {
    const config = SOURCE_CONFIG[sourceKey] || { label: sourceKey, icon: <Activity className="h-4 w-4" />, color: 'gray' };
    const total = metrics.sentiment_distribution.positive + metrics.sentiment_distribution.negative + metrics.sentiment_distribution.neutral;
    
    const bgColors: Record<string, string> = {
      orange: 'bg-orange-100',
      blue: 'bg-blue-100',
      purple: 'bg-purple-100',
      green: 'bg-green-100',
      indigo: 'bg-indigo-100',
      gray: 'bg-gray-100'
    };
    
    return (
      <Card className="hover:shadow-md transition-shadow">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <div className={`p-2 rounded-lg ${bgColors[config.color] || 'bg-gray-100'}`}>
                {config.icon}
              </div>
              <div>
                <CardTitle className="text-base">{config.label}</CardTitle>
                <p className="text-xs text-gray-500">{metrics.sample_count.toLocaleString()} samples</p>
              </div>
            </div>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Model Confidence - REAL metric */}
          <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
            <div>
              <p className="text-xs text-gray-500">Model Confidence</p>
              <p className="text-lg font-bold text-gray-900">{(metrics.avg_confidence * 100).toFixed(1)}%</p>
            </div>
            {getConfidenceBadge(metrics.avg_confidence)}
          </div>
          
          {/* Average sentiment - REAL metric */}
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Avg Sentiment Score</span>
            <span className={`font-semibold ${
              metrics.avg_sentiment_score > SENTIMENT_THRESHOLDS.POSITIVE ? 'text-green-600' : 
              metrics.avg_sentiment_score < SENTIMENT_THRESHOLDS.NEGATIVE ? 'text-red-600' : 'text-gray-600'
            }`}>
              {metrics.avg_sentiment_score > 0 ? '+' : ''}{metrics.avg_sentiment_score.toFixed(3)}
            </span>
          </div>
          
          {/* Sentiment distribution - REAL metric */}
          <div className="space-y-2">
            <div className="text-xs text-gray-500 font-medium">Sentiment Distribution</div>
            <div className="flex h-4 rounded-full overflow-hidden bg-gray-100">
              {total > 0 && (
                <>
                  <div 
                    className="bg-green-500 transition-all flex items-center justify-center" 
                    style={{ width: `${metrics.positive_rate}%` }}
                    title={`Positive: ${metrics.positive_rate}%`}
                  />
                  <div 
                    className="bg-gray-400 transition-all" 
                    style={{ width: `${metrics.neutral_rate}%` }}
                    title={`Neutral: ${metrics.neutral_rate}%`}
                  />
                  <div 
                    className="bg-red-500 transition-all" 
                    style={{ width: `${metrics.negative_rate}%` }}
                    title={`Negative: ${metrics.negative_rate}%`}
                  />
                </>
              )}
            </div>
            <div className="flex justify-between text-xs text-gray-600">
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-green-500"></span>
                Positive {metrics.positive_rate}%
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-gray-400"></span>
                Neutral {metrics.neutral_rate}%
              </span>
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-red-500"></span>
                Negative {metrics.negative_rate}%
              </span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
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

  // Get benchmark accuracy or show N/A
  const benchmarkAccuracy = benchmarkData?.benchmark?.accuracy;
  const aiAccuracy = benchmarkData?.benchmark?.ai_verification?.estimated_accuracy_with_ai;

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Sentiment Analysis Performance</h1>
            <p className="text-gray-500 text-sm mt-1">ProsusAI/finbert with Gemma 3 27B AI verification</p>
          </div>
          
          <div className="flex items-center gap-3">
            <Tabs value={viewType} onValueChange={(v) => setViewType(v as 'overall' | 'latest')}>
              <TabsList>
                <TabsTrigger value="overall" className="flex items-center gap-2">
                  <Database className="h-4 w-4" />
                  Overall
                </TabsTrigger>
                <TabsTrigger value="latest" className="flex items-center gap-2">
                  <Clock className="h-4 w-4" />
                  Latest Run
                </TabsTrigger>
              </TabsList>
            </Tabs>
            
            <Button 
              variant="outline" 
              size="sm"
              onClick={() => loadModelAccuracy(true)}
              disabled={refreshing}
            >
              <RefreshCw className={`h-4 w-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
              Refresh
            </Button>
          </div>
        </div>

        {/* Key Metrics - REAL numbers only */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* Verified Accuracy from Benchmark */}
          <Card className="border-2 border-blue-200 bg-blue-50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-blue-700 font-medium">Verified Accuracy</p>
                  <p className="text-3xl font-bold text-blue-900">
                    {benchmarkAccuracy ? `${(benchmarkAccuracy * 100).toFixed(1)}%` : 'Run Benchmark'}
                  </p>
                  <p className="text-xs text-blue-600 mt-1">Ground truth tested</p>
                </div>
                <div className="p-3 bg-blue-200 rounded-full">
                  <Target className="h-6 w-6 text-blue-700" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* With AI Verification */}
          <Card className="border-2 border-purple-200 bg-purple-50">
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-purple-700 font-medium">With AI Verification</p>
                  <p className="text-3xl font-bold text-purple-900">
                    {aiAccuracy ? `${(aiAccuracy * 100).toFixed(1)}%` : 'Run Benchmark'}
                  </p>
                  <p className="text-xs text-purple-600 mt-1">Gemma 3 27B-enhanced</p>
                </div>
                <div className="p-3 bg-purple-200 rounded-full">
                  <Brain className="h-6 w-6 text-purple-700" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Total Samples Analyzed */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Total Analyzed</p>
                  <p className="text-3xl font-bold text-gray-900">
                    {modelData?.evaluation_samples?.toLocaleString() || '0'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Sentiment records</p>
                </div>
                <div className="p-3 bg-gray-100 rounded-full">
                  <BarChart3 className="h-6 w-6 text-gray-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Overall Confidence */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Overall Confidence</p>
                  <p className="text-3xl font-bold text-indigo-600">
                    {modelData?.overall_confidence ? `${(modelData.overall_confidence * 100).toFixed(1)}%` : 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Avg model certainty</p>
                </div>
                <div className="p-3 bg-indigo-100 rounded-full">
                  <Sparkles className="h-6 w-6 text-indigo-600" />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Processing Success Rate */}
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">Success Rate</p>
                  <p className="text-3xl font-bold text-green-600">
                    {engineMetrics ? `${engineMetrics.overall_performance.success_rate_percent.toFixed(1)}%` : 'N/A'}
                  </p>
                  <p className="text-xs text-gray-500 mt-1">Processing success</p>
                </div>
                <div className="p-3 bg-green-100 rounded-full">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Ground Truth Benchmark - THE REAL ACCURACY */}
        <Card className="border-2 border-blue-300 shadow-lg">
          <CardHeader className="bg-gradient-to-r from-blue-50 to-indigo-50 border-b">
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-xl">
                  <Target className="h-6 w-6 text-blue-600" />
                  Ground Truth Benchmark
                </CardTitle>
                <CardDescription className="mt-1">
                  The ONLY reliable accuracy measurement - tested against 5,057 labeled financial sentences
                </CardDescription>
              </div>
              <div className="flex gap-2">
                <Button
                  onClick={() => runBenchmark(false)}
                  disabled={runningBenchmark}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  {runningBenchmark ? (
                    <>
                      <RefreshCw className="h-4 w-4 mr-2 animate-spin" />
                      Running...
                    </>
                  ) : (
                    <>
                      <Play className="h-4 w-4 mr-2" />
                      Run Benchmark
                    </>
                  )}
                </Button>
                {benchmarkData?.has_benchmark && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => runBenchmark(true)}
                    disabled={runningBenchmark}
                  >
                    Re-run
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent className="p-6">
            {benchmarkData?.has_benchmark && benchmarkData.benchmark ? (
              <div className="space-y-6">
                {/* Main Accuracy Display */}
                <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                  <div className="text-center p-4 bg-blue-50 rounded-xl border-2 border-blue-200">
                    <p className="text-xs text-blue-600 uppercase tracking-wide mb-1 font-medium">Accuracy</p>
                    <p className={`text-3xl font-bold ${getPerformanceColor(benchmarkData.benchmark.accuracy)}`}>
                      {(benchmarkData.benchmark.accuracy * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-center p-4 bg-white rounded-xl border">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Precision</p>
                    <p className={`text-2xl font-bold ${getPerformanceColor(benchmarkData.benchmark.macro_precision)}`}>
                      {(benchmarkData.benchmark.macro_precision * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-center p-4 bg-white rounded-xl border">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Recall</p>
                    <p className={`text-2xl font-bold ${getPerformanceColor(benchmarkData.benchmark.macro_recall)}`}>
                      {(benchmarkData.benchmark.macro_recall * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-center p-4 bg-white rounded-xl border">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">F1-Score</p>
                    <p className={`text-2xl font-bold ${getPerformanceColor(benchmarkData.benchmark.macro_f1)}`}>
                      {(benchmarkData.benchmark.macro_f1 * 100).toFixed(1)}%
                    </p>
                  </div>
                  <div className="text-center p-4 bg-white rounded-xl border">
                    <p className="text-xs text-gray-500 uppercase tracking-wide mb-1">Test Samples</p>
                    <p className="text-2xl font-bold text-gray-900">
                      {benchmarkData.benchmark.dataset_size.toLocaleString()}
                    </p>
                  </div>
                </div>

                {/* Per-Class Performance */}
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">Performance by Sentiment Class</h4>
                  <div className="grid grid-cols-3 gap-4">
                    {['positive', 'negative', 'neutral'].map((cls) => {
                      const metrics = benchmarkData.benchmark!.class_metrics[cls as keyof typeof benchmarkData.benchmark.class_metrics];
                      const colorMap: Record<string, { bg: string; border: string; text: string }> = {
                        positive: { bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800' },
                        negative: { bg: 'bg-red-50', border: 'border-red-200', text: 'text-red-800' },
                        neutral: { bg: 'bg-gray-50', border: 'border-gray-200', text: 'text-gray-800' }
                      };
                      const colors = colorMap[cls];
                      return (
                        <div key={cls} className={`p-4 rounded-lg border-2 ${colors.bg} ${colors.border}`}>
                          <p className={`font-semibold capitalize ${colors.text}`}>{cls}</p>
                          <div className="grid grid-cols-3 gap-3 mt-3">
                            <div>
                              <p className="text-xs text-gray-500">Precision</p>
                              <p className="text-lg font-bold">{(metrics.precision * 100).toFixed(1)}%</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">Recall</p>
                              <p className="text-lg font-bold">{(metrics.recall * 100).toFixed(1)}%</p>
                            </div>
                            <div>
                              <p className="text-xs text-gray-500">F1</p>
                              <p className="text-lg font-bold">{(metrics.f1_score * 100).toFixed(1)}%</p>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>

                {/* AI Verification Enhancement */}
                {benchmarkData.benchmark.ai_verification && (
                  <div className="p-4 bg-purple-50 rounded-xl border-2 border-purple-200">
                    <div className="flex items-start gap-3">
                      <div className="p-2 bg-purple-200 rounded-lg">
                        <Brain className="h-5 w-5 text-purple-700" />
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2">
                          <h4 className="font-semibold text-purple-900">AI Verification Enhancement</h4>
                          <Badge className="bg-purple-200 text-purple-800">
                            <Sparkles className="h-3 w-3 mr-1" />
                            {benchmarkData.benchmark.ai_verification.provider}
                          </Badge>
                        </div>
                        <p className="text-sm text-purple-700 mt-1">
                          Estimated accuracy with AI verification:{' '}
                          <span className="font-bold">{(benchmarkData.benchmark.ai_verification.estimated_accuracy_with_ai * 100).toFixed(1)}%</span>
                        </p>
                        <div className="flex gap-4 mt-2 text-xs text-purple-600">
                          <span>Mode: {benchmarkData.benchmark.ai_verification.mode}</span>
                          <span>Threshold: {(benchmarkData.benchmark.ai_verification.confidence_threshold * 100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Benchmark Info */}
                <div className="flex flex-wrap justify-between items-center text-xs text-gray-500 pt-4 border-t gap-2">
                  <span>Model: {benchmarkData.benchmark.model_name}</span>
                  <span>Dataset: Financial PhraseBank</span>
                  <span>Evaluated: {formatDateTime(benchmarkData.benchmark.evaluated_at)}</span>
                  <span>Time: {benchmarkData.benchmark.processing_time_seconds.toFixed(1)}s</span>
                </div>
              </div>
            ) : (
              <div className="text-center py-12">
                <Target className="h-16 w-16 mx-auto text-blue-200 mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Benchmark Results Yet</h3>
                <p className="text-gray-500 mb-6 max-w-md mx-auto">
                  Run the benchmark to measure real model accuracy against labeled financial sentences.
                  This is the only way to know true performance.
                </p>
                {!benchmarkData?.dataset_info?.available && (
                  <Alert className="max-w-md mx-auto mb-4">
                    <AlertTriangle className="h-4 w-4" />
                    <AlertDescription>
                      Dataset may need to be downloaded. Check: {benchmarkData?.dataset_info?.path}
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Data Source Statistics - REAL metrics only */}
        <div>
          <div className="flex items-center gap-2 mb-4">
            <Activity className="h-5 w-5 text-gray-600" />
            <h2 className="text-lg font-semibold text-gray-900">Data Source Statistics</h2>
          </div>
          <Alert className="mb-4 bg-blue-50 border-blue-200">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              These show real metrics from your data: sample counts, model confidence, and sentiment distribution.
              For actual accuracy, use the benchmark above.
            </AlertDescription>
          </Alert>
          
          {modelData?.source_metrics && Object.keys(modelData.source_metrics).length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(modelData.source_metrics)
                .sort((a, b) => b[1].sample_count - a[1].sample_count)
                .map(([sourceKey, metrics]) => (
                  <SourceCard key={sourceKey} sourceKey={sourceKey} metrics={metrics} />
                ))}
            </div>
          ) : (
            <Card>
              <CardContent className="py-12 text-center">
                <Activity className="h-12 w-12 mx-auto text-gray-300 mb-4" />
                <p className="text-gray-500">
                  {viewType === 'latest' 
                    ? 'No data collected in the last 24 hours. Run the pipeline to collect data.'
                    : 'No sentiment data available. Run the pipeline to start collecting.'}
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Engine Status */}
        {engineMetrics && (
          <Card className="bg-gray-50">
            <CardContent className="py-4">
              <div className="flex flex-wrap items-center justify-between gap-4 text-sm">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <span className={`w-3 h-3 rounded-full ${
                      engineMetrics.engine_status.engine_health === 'healthy' ? 'bg-green-500' :
                      engineMetrics.engine_status.engine_health === 'degraded' ? 'bg-yellow-500' : 'bg-red-500'
                    }`}></span>
                    <span className="font-medium capitalize">{engineMetrics.engine_status.engine_health}</span>
                  </div>
                  <span className="text-gray-400">|</span>
                  <span className="text-gray-600">
                    {engineMetrics.overall_performance.total_texts_processed.toLocaleString()} texts processed
                  </span>
                  <span className="text-gray-400">|</span>
                  <span className="text-gray-600">
                    Avg {engineMetrics.overall_performance.avg_processing_time_ms.toFixed(0)}ms/text
                  </span>
                </div>
                <div className="flex items-center gap-2 text-gray-600">
                  <Cpu className="h-4 w-4" />
                  <span>ProsusAI/finbert</span>
                  <span className="text-gray-400">+</span>
                  <Brain className="h-4 w-4 text-purple-600" />
                  <span>Gemma 3 27B</span>
                </div>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  );
};

export default ModelAccuracy;
