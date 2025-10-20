
import React, { useState, useEffect } from 'react';
import AdminLayout from "@/shared/components/layouts/AdminLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Badge } from "@/shared/components/ui/badge";
import { Progress } from "@/shared/components/ui/progress";
import { Button } from "@/shared/components/ui/button";
import { useToast } from "@/shared/hooks/use-toast";
import { adminAPI, ModelAccuracy as ModelAccuracyType } from "../../../api/services/admin.service";
import { RefreshCw, TrendingUp, AlertCircle, Clock, Database } from "lucide-react";

const ModelAccuracy = () => {
  const { toast } = useToast();
  const [modelData, setModelData] = useState<ModelAccuracyType | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [viewType, setViewType] = useState<'overall' | 'latest'>('overall');

  // Load model accuracy data
  const loadModelAccuracy = async (showRefreshToast = false) => {
    try {
      setRefreshing(true);
      const data = await adminAPI.getModelAccuracy(viewType);
      setModelData(data);
      
      if (showRefreshToast) {
        toast({
          title: "Data Updated",
          description: "Model accuracy metrics have been refreshed.",
        });
      }
    } catch (error) {
      console.error('Failed to load model accuracy:', error);
      toast({
        title: "Error",
        description: "Failed to load model accuracy data. Please try again.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    loadModelAccuracy();
  }, []);

  // Reload data when view type changes
  useEffect(() => {
    if (!loading) {
      loadModelAccuracy();
    }
  }, [viewType]);

  // Helper function to get performance badge
  const getPerformanceBadge = (accuracy: number) => {
    if (accuracy >= 0.90) {
      return <Badge className="bg-green-100 text-green-800">Excellent</Badge>;
    } else if (accuracy >= 0.80) {
      return <Badge className="bg-blue-100 text-blue-800">Good</Badge>;
    } else if (accuracy >= 0.70) {
      return <Badge className="bg-yellow-100 text-yellow-800">Fair</Badge>;
    } else {
      return <Badge className="bg-red-100 text-red-800">Poor</Badge>;
    }
  };

  if (loading) {
    return (
      <AdminLayout>
        <div className="flex items-center justify-center h-64">
          <div className="text-gray-500">Loading model accuracy data...</div>
        </div>
      </AdminLayout>
    );
  }
  return (
    <AdminLayout>
      <div className="space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Model Accuracy</h1>
            <p className="text-gray-600 mt-2">Performance metrics for sentiment analysis models</p>
          </div>
          
          <div className="flex gap-3">
            {/* View Type Toggle */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              <Button
                variant={viewType === 'overall' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewType('overall')}
                className="flex items-center gap-2"
              >
                <Database className="h-4 w-4" />
                Overall
              </Button>
              <Button
                variant={viewType === 'latest' ? 'default' : 'ghost'}
                size="sm"
                onClick={() => setViewType('latest')}
                className="flex items-center gap-2"
              >
                <Clock className="h-4 w-4" />
                Latest Run
              </Button>
            </div>
            
            <Button 
              variant="outline" 
              onClick={() => loadModelAccuracy(true)}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
              {refreshing ? 'Refreshing...' : 'Refresh'}
            </Button>
          </div>
        </div>

        {/* View Type Information */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center gap-2">
            {viewType === 'latest' ? (
              <>
                <Clock className="h-5 w-5 text-blue-600" />
                <div>
                  <h3 className="font-medium text-blue-900">Latest Pipeline Run View</h3>
                  <p className="text-sm text-blue-700">
                    Showing performance metrics from the most recent pipeline execution (last 24 hours). 
                    This reflects how well your Enhanced VADER model is performing on newly collected data.
                  </p>
                </div>
              </>
            ) : (
              <>
                <Database className="h-5 w-5 text-blue-600" />
                <div>
                  <h3 className="font-medium text-blue-900">Overall Database View</h3>
                  <p className="text-sm text-blue-700">
                    Showing comprehensive performance metrics from all data in the database (last 30 days). 
                    This provides a broader view of model performance over time.
                  </p>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Overall Performance Summary */}
        {modelData && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <TrendingUp className="h-5 w-5" />
                {viewType === 'latest' ? 'Latest Pipeline Performance' : 'Overall Performance'}
              </CardTitle>
              <CardDescription>
                {modelData.evaluation_period} | Last evaluation: {new Date(modelData.last_evaluation).toLocaleString()}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between mb-4">
                <div>
                  <div className="text-3xl font-bold">
                    {(modelData.overall_accuracy * 100).toFixed(1)}%
                  </div>
                  <p className="text-sm text-gray-600">Overall Accuracy</p>
                </div>
                <div className="text-right">
                  {getPerformanceBadge(modelData.overall_accuracy)}
                  <p className="text-sm text-gray-600 mt-1">
                    {modelData.evaluation_samples.toLocaleString()} samples evaluated
                  </p>
                </div>
              </div>
              <Progress value={modelData.overall_accuracy * 100} className="w-full" />
            </CardContent>
          </Card>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Card>
            <CardHeader>
              <CardTitle>VADER Model</CardTitle>
              <CardDescription>Social media sentiment analysis performance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {modelData ? (
                <>
                  <div className="flex justify-between items-center">
                    <span>Accuracy</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.vader_sentiment.accuracy * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.vader_sentiment.accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Precision</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.vader_sentiment.precision * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.vader_sentiment.precision * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Recall</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.vader_sentiment.recall * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.vader_sentiment.recall * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>F1-Score</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.vader_sentiment.f1_score * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.vader_sentiment.f1_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="pt-2">
                    {getPerformanceBadge(modelData.model_metrics.vader_sentiment.accuracy)}
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center py-4">
                  <AlertCircle className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-gray-500">No data available</span>
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>FinBERT Model</CardTitle>
              <CardDescription>Financial news sentiment analysis performance</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {modelData ? (
                <>
                  <div className="flex justify-between items-center">
                    <span>Accuracy</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.finbert_sentiment.accuracy * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.finbert_sentiment.accuracy * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Precision</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.finbert_sentiment.precision * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.finbert_sentiment.precision * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>Recall</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.finbert_sentiment.recall * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.finbert_sentiment.recall * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span>F1-Score</span>
                    <div className="flex items-center gap-2">
                      <Progress value={modelData.model_metrics.finbert_sentiment.f1_score * 100} className="w-20" />
                      <span className="text-sm font-medium">
                        {(modelData.model_metrics.finbert_sentiment.f1_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                  <div className="pt-2">
                    {getPerformanceBadge(modelData.model_metrics.finbert_sentiment.accuracy)}
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center py-4">
                  <AlertCircle className="h-5 w-5 text-gray-400 mr-2" />
                  <span className="text-gray-500">No data available</span>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {modelData && (
          <Card>
            <CardHeader>
              <CardTitle>Model Evaluation Summary</CardTitle>
              <CardDescription>Performance analysis and recommendations</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="text-center">
                  {getPerformanceBadge(modelData.model_metrics.finbert_sentiment.accuracy)}
                  <p className="text-sm text-gray-600 mt-2">FinBERT performance on financial news</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(modelData.model_metrics.finbert_sentiment.accuracy * 100).toFixed(1)}% accuracy
                  </p>
                </div>
                <div className="text-center">
                  {getPerformanceBadge(modelData.model_metrics.vader_sentiment.accuracy)}
                  <p className="text-sm text-gray-600 mt-2">VADER performance on social media</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(modelData.model_metrics.vader_sentiment.accuracy * 100).toFixed(1)}% accuracy
                  </p>
                </div>
                <div className="text-center">
                  {getPerformanceBadge(modelData.overall_accuracy)}
                  <p className="text-sm text-gray-600 mt-2">Overall system performance</p>
                  <p className="text-xs text-gray-500 mt-1">
                    {(modelData.overall_accuracy * 100).toFixed(1)}% combined accuracy
                  </p>
                </div>
              </div>
              
              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-medium mb-2">Evaluation Details</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Evaluation Period:</span>
                    <span className="ml-2 font-medium">
                      {modelData.evaluation_period}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Last Evaluation:</span>
                    <span className="ml-2 font-medium">
                      {new Date(modelData.last_evaluation).toLocaleDateString()}
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-600">Samples Evaluated:</span>
                    <span className="ml-2 font-medium">
                      {modelData.evaluation_samples.toLocaleString()}
                    </span>
                  </div>
                </div>
                {viewType === 'latest' && modelData.evaluation_samples === 0 && (
                  <div className="mt-3 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
                    <p className="text-sm text-yellow-800">
                      <strong>No recent data found.</strong> Run the pipeline to collect new data and see latest performance metrics.
                    </p>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </AdminLayout>
  );
};

export default ModelAccuracy;
