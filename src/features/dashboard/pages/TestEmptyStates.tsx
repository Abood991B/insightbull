import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Button } from "@/shared/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/shared/components/ui/tabs";
import { useState } from "react";

// Import all empty state components
import {
  EmptyState,
  EmptyPipelineState,
  EmptyWatchlistState,
  PartialDataWarning,
  InsufficientCorrelationData
} from "@/shared/components/states";

// Import validation utilities
import {
  validateDashboardData,
  validateSentimentData,
  validateCorrelationData,
  validateStockList,
  hasSufficientData,
  getDataStateMessage
} from "@/shared/utils/dataValidation";

import { Database, TrendingUp, BarChart3, AlertCircle } from "lucide-react";

/**
 * Empty State Testing Page
 * 
 * DEVELOPMENT ONLY - Test all empty state components and validation logic
 * Navigate to /test-empty-states to view this page
 */
export function TestEmptyStates() {
  const [selectedTab, setSelectedTab] = useState("components");

  return (
    <UserLayout>
      <div className="space-y-6">
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-6">
          <div className="flex">
            <AlertCircle className="h-5 w-5 text-yellow-400 mr-3" />
            <div>
              <p className="text-sm font-medium text-yellow-800">
                Development Testing Page
              </p>
              <p className="text-sm text-yellow-700 mt-1">
                This page is for testing empty state components before integration.
                Remove from production build.
              </p>
            </div>
          </div>
        </div>

        <div>
          <h1 className="text-3xl font-bold text-gray-900">Empty State Testing</h1>
          <p className="text-gray-600 mt-2">
            Test all empty state components and data validation utilities
          </p>
        </div>

        <Tabs value={selectedTab} onValueChange={setSelectedTab}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="components">Components</TabsTrigger>
            <TabsTrigger value="validation">Validation</TabsTrigger>
            <TabsTrigger value="usage">Usage Examples</TabsTrigger>
          </TabsList>

          <TabsContent value="components" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>1. EmptyPipelineState (Most Critical)</CardTitle>
                <CardDescription>
                  Display when backend has no sentiment data (pipeline not run yet)
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EmptyPipelineState />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>2. EmptyWatchlistState</CardTitle>
                <CardDescription>
                  Display when watchlist has no stocks
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EmptyWatchlistState />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>3. PartialDataWarning</CardTitle>
                <CardDescription>
                  Display when some data exists but insufficient for optimal analysis
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">With 3/5 data points:</p>
                  <PartialDataWarning 
                    dataPoints={3} 
                    minRequired={5} 
                  />
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">With data quality metric:</p>
                  <PartialDataWarning 
                    dataPoints={7} 
                    minRequired={10} 
                    dataQuality={45}
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>4. InsufficientCorrelationData</CardTitle>
                <CardDescription>
                  Display when correlation analysis requires more data points
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div>
                  <p className="text-sm font-medium mb-2">With 3/10 required points:</p>
                  <InsufficientCorrelationData currentPoints={3} />
                </div>
                <div>
                  <p className="text-sm font-medium mb-2">With 8/15 required points:</p>
                  <InsufficientCorrelationData 
                    currentPoints={8} 
                    requiredPoints={15} 
                  />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>5. Generic EmptyState</CardTitle>
                <CardDescription>
                  Reusable component for custom empty states
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EmptyState
                  icon={<BarChart3 className="w-16 h-16 text-gray-400" />}
                  title="Custom Empty State"
                  description="This is a generic empty state component that can be customized with any icon, title, and description."
                  actionLabel="Primary Action"
                  actionLink="/admin/dashboard"
                  secondaryAction={{
                    label: "Secondary Action",
                    link: "/about"
                  }}
                />
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="validation" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Data Validation Utilities</CardTitle>
                <CardDescription>
                  Test validation functions with different data scenarios
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Dashboard Validation */}
                <div>
                  <h3 className="font-semibold mb-3">1. Dashboard Data Validation</h3>
                  <div className="space-y-2 text-sm">
                    <TestValidation
                      label="Empty dashboard (no data)"
                      result={validateDashboardData({ top_stocks: [], system_status: { total_sentiment_records: 0 } })}
                    />
                    <TestValidation
                      label="Partial dashboard (< 5 stocks)"
                      result={validateDashboardData({ top_stocks: [{}, {}, {}], system_status: { total_sentiment_records: 100 } })}
                    />
                    <TestValidation
                      label="Full dashboard (10+ stocks)"
                      result={validateDashboardData({ top_stocks: Array(10).fill({}), system_status: { total_sentiment_records: 1000 } })}
                    />
                  </div>
                </div>

                {/* Sentiment Validation */}
                <div>
                  <h3 className="font-semibold mb-3">2. Sentiment Data Validation</h3>
                  <div className="space-y-2 text-sm">
                    <TestValidation
                      label="No data points"
                      result={validateSentimentData({ data_points: [] })}
                    />
                    <TestValidation
                      label="Partial data (3 points)"
                      result={validateSentimentData({ data_points: [{}, {}, {}] })}
                    />
                    <TestValidation
                      label="Sufficient data (10 points)"
                      result={validateSentimentData({ data_points: Array(10).fill({}) })}
                    />
                    <TestValidation
                      label="Low quality data (30%)"
                      result={validateSentimentData({ 
                        data_points: Array(10).fill({}), 
                        statistics: { data_quality: 30 } 
                      })}
                    />
                  </div>
                </div>

                {/* Correlation Validation */}
                <div>
                  <h3 className="font-semibold mb-3">3. Correlation Data Validation</h3>
                  <div className="space-y-2 text-sm">
                    <TestValidation
                      label="No correlation data"
                      result={validateCorrelationData({ scatter_data: [] })}
                    />
                    <TestValidation
                      label="Insufficient data (5 points)"
                      result={validateCorrelationData({ scatter_data: Array(5).fill({}) })}
                    />
                    <TestValidation
                      label="Sufficient but not significant (p > 0.05)"
                      result={validateCorrelationData({ 
                        scatter_data: Array(15).fill({}), 
                        p_value: 0.08 
                      })}
                    />
                    <TestValidation
                      label="Sufficient and significant"
                      result={validateCorrelationData({ 
                        scatter_data: Array(15).fill({}), 
                        p_value: 0.01 
                      })}
                    />
                  </div>
                </div>

                {/* Stock List Validation */}
                <div>
                  <h3 className="font-semibold mb-3">4. Stock List Validation</h3>
                  <div className="space-y-2 text-sm">
                    <TestValidation
                      label="Empty watchlist"
                      result={validateStockList([])}
                    />
                    <TestValidation
                      label="Watchlist with inactive stocks"
                      result={validateStockList([{ is_active: false }, { is_active: false }])}
                    />
                    <TestValidation
                      label="Watchlist with active stocks"
                      result={validateStockList([{ is_active: true }, { is_active: true }])}
                    />
                  </div>
                </div>

                {/* Data Sufficiency */}
                <div>
                  <h3 className="font-semibold mb-3">5. Data Sufficiency Checks</h3>
                  <div className="space-y-2 text-sm">
                    <div className="p-2 bg-gray-50 rounded">
                      Sentiment (5 required): {hasSufficientData(3, 'sentiment') ? '✅ Yes' : '❌ No (3 points)'}
                    </div>
                    <div className="p-2 bg-gray-50 rounded">
                      Correlation (10 required): {hasSufficientData(8, 'correlation') ? '✅ Yes' : '❌ No (8 points)'}
                    </div>
                    <div className="p-2 bg-gray-50 rounded">
                      Trend (7 required): {hasSufficientData(10, 'trend') ? '✅ Yes' : '❌ No (10 points)'}
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="usage" className="space-y-6 mt-6">
            <Card>
              <CardHeader>
                <CardTitle>Usage Patterns</CardTitle>
                <CardDescription>
                  Example code for implementing empty states in components
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <UsageExample
                    title="Dashboard Page Pattern"
                    code={`const { data, isLoading } = useQuery({
  queryKey: ['dashboard-summary'],
  queryFn: () => dashboardService.getDashboardSummary()
});

if (isLoading) return <LoadingSkeleton />;

if (data && data.top_stocks.length === 0) {
  return <EmptyPipelineState />;
}

return <DashboardContent data={data} />;`}
                  />

                  <UsageExample
                    title="Analysis Page with Validation"
                    code={`const { data } = useQuery({
  queryKey: ['sentiment', symbol, timeframe],
  queryFn: () => analysisService.getSentimentHistory(symbol, timeframe)
});

const validation = validateSentimentData(data, 5);

if (validation.isEmpty) {
  return <EmptyPipelineState />;
}

if (validation.isPartial) {
  return (
    <>
      <PartialDataWarning 
        dataPoints={data.data_points.length}
        minRequired={5}
      />
      <ChartComponent data={data} />
    </>
  );
}

return <FullAnalysisView data={data} />;`}
                  />

                  <UsageExample
                    title="Stock Selection with Empty Watchlist"
                    code={`const { data: stockList, isLoading } = useQuery({
  queryKey: ['stocks'],
  queryFn: () => stockService.getAllStocks(true)
});

if (!isLoading && stockList?.stocks.length === 0) {
  return <EmptyWatchlistState />;
}

return (
  <Select disabled={isLoading}>
    {/* Stock options */}
  </Select>
);`}
                  />
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </UserLayout>
  );
}

// Helper component for displaying validation results
function TestValidation({ label, result }: { label: string; result: any }) {
  const statusColors = {
    error: 'text-red-600 bg-red-50 border-red-200',
    warning: 'text-yellow-600 bg-yellow-50 border-yellow-200',
    info: 'text-blue-600 bg-blue-50 border-blue-200',
    success: 'text-green-600 bg-green-50 border-green-200'
  };

  return (
    <div className={`p-3 rounded border ${statusColors[result.severity]}`}>
      <div className="font-medium">{label}</div>
      <div className="text-xs mt-1 space-y-1">
        <div>Valid: {result.isValid ? '✅' : '❌'} | Empty: {result.isEmpty ? '✅' : '❌'} | Partial: {result.isPartial ? '✅' : '❌'}</div>
        {result.message && <div className="italic">{result.message}</div>}
      </div>
    </div>
  );
}

// Helper component for usage examples
function UsageExample({ title, code }: { title: string; code: string }) {
  return (
    <div>
      <h3 className="font-semibold mb-2">{title}</h3>
      <pre className="text-xs bg-gray-900 text-gray-100 p-4 rounded overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
}

export default TestEmptyStates;
