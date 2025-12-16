import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Badge } from "@/shared/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/shared/components/ui/alert";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { 
  AlertCircle, 
  AlertTriangle, 
  Info,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import { 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip as RechartsTooltip, 
  ResponsiveContainer, 
  Cell,
  ReferenceLine,
  Line,
  ComposedChart
} from 'recharts';

// Import services
import { stockService } from "@/api/services/stock.service";
import { analysisService } from "@/api/services/analysis.service";

// Import timezone utilities
import { formatDate } from "@/shared/utils/timezone";

// Import empty state components
import { EmptyWatchlistState } from "@/shared/components/states";

// --- Types ---
type TimeframeValue = '1d' | '7d' | '14d' | '30d';

// --- Helper Functions ---
const getCorrelationColor = (r: number): string => {
  const absR = Math.abs(r);
  if (absR >= 0.7) return r > 0 ? 'text-green-600' : 'text-red-600';
  if (absR >= 0.4) return r > 0 ? 'text-green-500' : 'text-red-500';
  if (absR >= 0.2) return 'text-amber-500';
  return 'text-slate-400';
};

const getCorrelationLabel = (r: number): string => {
  const absR = Math.abs(r);
  const direction = r > 0.05 ? 'Positive' : r < -0.05 ? 'Negative' : 'None';
  if (absR >= 0.7) return `Strong ${direction}`;
  if (absR >= 0.4) return `Moderate ${direction}`;
  if (absR >= 0.2) return `Weak ${direction}`;
  return 'No Correlation';
};

const getScatterColor = (sentiment: number): string => {
  if (sentiment > 0.3) return '#10B981';
  if (sentiment > 0) return '#6EE7B7';
  if (sentiment > -0.3) return '#F59E0B';
  return '#EF4444';
};

// Check if price data has variance
const hasPriceVariance = (data: any[]): boolean => {
  if (!data || data.length < 2) return false;
  const prices = data.map(d => d.price).filter(p => p != null);
  if (prices.length < 2) return false;
  const min = Math.min(...prices);
  const max = Math.max(...prices);
  return max - min > 0.01; // Allow for tiny floating point differences
};

// Check if sentiment data has variance
const hasSentimentVariance = (data: any[]): boolean => {
  if (!data || data.length < 2) return false;
  const sentiments = data.map(d => d.sentiment).filter(s => s != null);
  if (sentiments.length < 2) return false;
  const min = Math.min(...sentiments);
  const max = Math.max(...sentiments);
  return max - min > 0.01;
};

// --- Custom Tooltip ---
const ScatterTooltip = ({ active, payload }: any) => {
  if (!active || !payload?.[0]) return null;
  const { sentiment, price } = payload[0].payload;
  return (
    <div className="bg-white border rounded-lg shadow-lg p-3 text-sm">
      <div className="flex justify-between gap-4">
        <span className="text-slate-500">Sentiment:</span>
        <span className={`font-medium ${sentiment > 0.3 ? 'text-green-600' : sentiment < -0.3 ? 'text-red-600' : 'text-amber-600'}`}>
          {sentiment.toFixed(3)}
        </span>
      </div>
      <div className="flex justify-between gap-4">
        <span className="text-slate-500">Price:</span>
        <span className="font-medium text-blue-600">${price.toFixed(2)}</span>
      </div>
    </div>
  );
};

// --- Data Issue Alert ---
interface DataIssueAlertProps {
  hasPrice: boolean;
  hasSentiment: boolean;
  priceVariance: boolean;
  sentimentVariance: boolean;
  sampleSize: number;
  uniqueDays: number;
}

const DataIssueAlert = ({ hasPrice, hasSentiment, priceVariance, sentimentVariance, sampleSize, uniqueDays }: DataIssueAlertProps) => {
  const issues: string[] = [];
  
  if (!hasPrice) issues.push("No price data available");
  if (!hasSentiment) issues.push("No sentiment data available");
  if (hasPrice && !priceVariance) issues.push("Price has no variation (same value for all records)");
  if (hasSentiment && !sentimentVariance) issues.push("Sentiment has no variation");
  if (sampleSize < 10) issues.push(`Only ${sampleSize} data points (recommend 10+ for reliable analysis)`);
  if (uniqueDays < 3) issues.push(`Data spans only ${uniqueDays} day(s) (recommend 3+ days for meaningful correlation)`);

  if (issues.length === 0) return null;

  const cannotCalculate = !priceVariance || !sentimentVariance || sampleSize < 3;

  return (
    <Alert className={cannotCalculate ? "border-red-200 bg-red-50" : "border-amber-200 bg-amber-50"}>
      <AlertTriangle className={`h-4 w-4 ${cannotCalculate ? 'text-red-600' : 'text-amber-600'}`} />
      <AlertTitle className={cannotCalculate ? "text-red-900" : "text-amber-900"}>
        {cannotCalculate ? "Correlation Cannot Be Calculated" : "Data Quality Notice"}
      </AlertTitle>
      <AlertDescription className={cannotCalculate ? "text-red-800" : "text-amber-800"}>
        <ul className="list-disc list-inside mt-1 space-y-0.5">
          {issues.map((issue, i) => <li key={i}>{issue}</li>)}
        </ul>
        {cannotCalculate && (
          <p className="mt-2 font-medium">
            Correlation requires both price and sentiment to have variation across multiple data points.
            Try selecting a longer timeframe or wait for more data collection.
          </p>
        )}
      </AlertDescription>
    </Alert>
  );
};

// --- Main Component ---
const CorrelationAnalysis = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const timeframeFromUrl = searchParams.get('timeframe') as TimeframeValue | null;
  
  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');
  const [timeRange, setTimeRange] = useState<TimeframeValue>(
    timeframeFromUrl && ['1d', '7d', '14d', '30d'].includes(timeframeFromUrl) 
      ? timeframeFromUrl 
      : '7d'
  );

  // Fetch stock options
  const { data: stockOptions = [], isLoading: isLoadingStocks } = useQuery({
    queryKey: ['stock-options'],
    queryFn: () => stockService.getStockOptions(true),
    staleTime: 30 * 1000,
  });

  // Fetch correlation data
  const { 
    data: correlationResponse, 
    isLoading: isLoadingCorrelation, 
    error: correlationError 
  } = useQuery({
    queryKey: ['correlation-analysis', selectedStock, timeRange],
    queryFn: () => analysisService.getCorrelationAnalysis(selectedStock, timeRange),
    enabled: !!selectedStock,
    staleTime: 60 * 1000,
  });

  // Auto-select first stock
  useEffect(() => {
    if (!selectedStock && stockOptions.length > 0) {
      const first = stockOptions[0].value;
      setSelectedStock(first);
      setSearchParams({ symbol: first, timeframe: timeRange });
    }
  }, [stockOptions, selectedStock, timeRange, setSearchParams]);

  const handleStockChange = (symbol: string) => {
    setSelectedStock(symbol);
    setSearchParams({ symbol, timeframe: timeRange });
  };

  const handleTimeRangeChange = (range: TimeframeValue) => {
    setTimeRange(range);
    setSearchParams({ symbol: selectedStock, timeframe: range });
  };

  // Process data
  const data = correlationResponse?.data;
  const scatterData = useMemo(() => {
    if (!data?.scatter_data) return [];
    return data.scatter_data.map((d: any) => ({
      sentiment: Number(d.sentiment) || 0,
      price: Number(d.price) || 0
    }));
  }, [data]);

  // Calculate data quality metrics
  const dataMetrics = useMemo(() => {
    const priceVar = hasPriceVariance(scatterData);
    const sentVar = hasSentimentVariance(scatterData);
    const uniquePrices = new Set(scatterData.map((d: any) => d.price.toFixed(2))).size;
    
    return {
      hasData: scatterData.length > 0,
      sampleSize: scatterData.length,
      hasPriceVariance: priceVar,
      hasSentimentVariance: sentVar,
      uniqueDays: uniquePrices, // Proxy: unique prices ≈ unique days for daily data
      canCalculateCorrelation: priceVar && sentVar && scatterData.length >= 3
    };
  }, [scatterData]);

  // Extract metrics
  const metrics = data?.correlation_metrics;
  const r = metrics?.pearson_correlation ?? 0;
  const pValue = metrics?.p_value ?? 1;
  const rSquared = metrics?.r_squared ?? 0;
  const sampleSize = metrics?.sample_size ?? 0;
  const ci = metrics?.confidence_interval ?? [0, 0];

  // Calculate regression line
  const regressionLine = useMemo(() => {
    if (!dataMetrics.canCalculateCorrelation || scatterData.length < 2) return null;
    
    const n = scatterData.length;
    let sumX = 0, sumY = 0, sumXY = 0, sumX2 = 0;
    scatterData.forEach((p: any) => {
      sumX += p.sentiment;
      sumY += p.price;
      sumXY += p.sentiment * p.price;
      sumX2 += p.sentiment * p.sentiment;
    });
    
    const meanX = sumX / n;
    const meanY = sumY / n;
    const denom = sumX2 - n * meanX * meanX;
    if (Math.abs(denom) < 0.0001) return null;
    
    const slope = (sumXY - n * meanX * meanY) / denom;
    const intercept = meanY - slope * meanX;
    
    const xMin = Math.min(...scatterData.map((p: any) => p.sentiment)) - 0.05;
    const xMax = Math.max(...scatterData.map((p: any) => p.sentiment)) + 0.05;
    
    return [
      { sentiment: xMin, price: slope * xMin + intercept },
      { sentiment: xMax, price: slope * xMax + intercept }
    ];
  }, [scatterData, dataMetrics.canCalculateCorrelation]);

  // Chart domains
  const domains = useMemo(() => {
    if (!scatterData.length) return { x: [-1, 1] as [number, number], y: [0, 100] as [number, number] };
    const sents = scatterData.map((p: any) => p.sentiment);
    const prices = scatterData.map((p: any) => p.price);
    const xPad = (Math.max(...sents) - Math.min(...sents)) * 0.15 || 0.1;
    const yPad = (Math.max(...prices) - Math.min(...prices)) * 0.15 || Math.max(...prices) * 0.05;
    return {
      x: [Math.max(-1, Math.min(...sents) - xPad), Math.min(1, Math.max(...sents) + xPad)] as [number, number],
      y: [Math.max(0, Math.min(...prices) - yPad), Math.max(...prices) + yPad] as [number, number]
    };
  }, [scatterData]);

  // Loading states
  if (isLoadingStocks) {
    return (
      <UserLayout>
        <div className="space-y-4">
          <Skeleton className="h-10 w-64" />
          <Skeleton className="h-[400px]" />
        </div>
      </UserLayout>
    );
  }

  if (!stockOptions.length) {
    return <UserLayout><EmptyWatchlistState /></UserLayout>;
  }

  return (
    <UserLayout>
      <div className="space-y-4">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Correlation Analysis</h1>
            <p className="text-sm text-slate-500">Sentiment vs. Price relationship for {selectedStock}</p>
          </div>
          
          <div className="flex items-center gap-2 bg-white p-1.5 rounded-lg border">
            <Select value={selectedStock} onValueChange={handleStockChange}>
              <SelectTrigger className="w-[130px] h-8 text-sm">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {stockOptions.map((opt) => (
                  <SelectItem key={opt.value} value={opt.value}>{opt.label}</SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <div className="flex border rounded-md">
              {(['1d', '7d', '14d', '30d'] as const).map(tf => (
                <button
                  key={tf}
                  onClick={() => handleTimeRangeChange(tf)}
                  className={`px-2.5 py-1 text-xs font-medium transition-colors ${
                    timeRange === tf 
                      ? 'bg-blue-600 text-white' 
                      : 'text-slate-600 hover:bg-slate-100'
                  } ${tf === '1d' ? 'rounded-l-md' : ''} ${tf === '30d' ? 'rounded-r-md' : ''}`}
                >
                  {tf.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Error State */}
        {correlationError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{(correlationError as Error).message}</AlertDescription>
          </Alert>
        )}

        {/* Loading */}
        {isLoadingCorrelation && (
          <div className="space-y-4">
            <div className="grid grid-cols-4 gap-4">
              {[1,2,3,4].map(i => <Skeleton key={i} className="h-24" />)}
            </div>
            <Skeleton className="h-[350px]" />
          </div>
        )}

        {/* Data Issue Alert */}
        {!isLoadingCorrelation && data && (
          <DataIssueAlert
            hasPrice={scatterData.some((d: any) => d.price > 0)}
            hasSentiment={scatterData.some((d: any) => d.sentiment !== 0)}
            priceVariance={dataMetrics.hasPriceVariance}
            sentimentVariance={dataMetrics.hasSentimentVariance}
            sampleSize={sampleSize}
            uniqueDays={dataMetrics.uniqueDays}
          />
        )}

        {/* Main Content */}
        {!isLoadingCorrelation && data && (
          <>
            {/* Metrics Row */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              <Card>
                <CardHeader className="pb-1 pt-3 px-4">
                  <CardTitle className="text-xs font-medium text-slate-500">Correlation (r)</CardTitle>
                </CardHeader>
                <CardContent className="pb-3 px-4">
                  <div className={`text-2xl font-bold ${dataMetrics.canCalculateCorrelation ? getCorrelationColor(r) : 'text-slate-300'}`}>
                    {dataMetrics.canCalculateCorrelation ? r.toFixed(3) : '—'}
                  </div>
                  <p className="text-xs text-slate-500">
                    {dataMetrics.canCalculateCorrelation ? getCorrelationLabel(r) : 'Insufficient variance'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-1 pt-3 px-4">
                  <CardTitle className="text-xs font-medium text-slate-500">R² (Explained)</CardTitle>
                </CardHeader>
                <CardContent className="pb-3 px-4">
                  <div className={`text-2xl font-bold ${dataMetrics.canCalculateCorrelation ? 'text-blue-600' : 'text-slate-300'}`}>
                    {dataMetrics.canCalculateCorrelation ? `${(rSquared * 100).toFixed(1)}%` : '—'}
                  </div>
                  <p className="text-xs text-slate-500">
                    {dataMetrics.canCalculateCorrelation ? 'of price variance' : 'Insufficient data'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-1 pt-3 px-4">
                  <CardTitle className="text-xs font-medium text-slate-500">P-Value</CardTitle>
                </CardHeader>
                <CardContent className="pb-3 px-4">
                  <div className={`text-2xl font-bold ${
                    !dataMetrics.canCalculateCorrelation ? 'text-slate-300' :
                    pValue < 0.05 ? 'text-green-600' : 'text-amber-500'
                  }`}>
                    {dataMetrics.canCalculateCorrelation ? (pValue < 0.001 ? '<0.001' : pValue.toFixed(3)) : '—'}
                  </div>
                  <p className="text-xs text-slate-500">
                    {!dataMetrics.canCalculateCorrelation ? 'N/A' : pValue < 0.05 ? 'Significant' : 'Not significant'}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-1 pt-3 px-4">
                  <CardTitle className="text-xs font-medium text-slate-500">Sample Size</CardTitle>
                </CardHeader>
                <CardContent className="pb-3 px-4">
                  <div className={`text-2xl font-bold ${sampleSize >= 30 ? 'text-green-600' : sampleSize >= 10 ? 'text-amber-500' : 'text-red-500'}`}>
                    {sampleSize}
                  </div>
                  <p className="text-xs text-slate-500">
                    {sampleSize >= 30 ? 'Good' : sampleSize >= 10 ? 'Limited' : 'Insufficient'}
                  </p>
                </CardContent>
              </Card>
            </div>

            {/* Scatter Plot */}
            <Card>
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle className="text-base">Sentiment vs. Price</CardTitle>
                    {data.analysis_period && (
                      <p className="text-xs text-slate-500 mt-0.5">
                        {formatDate(data.analysis_period.start)} — {formatDate(data.analysis_period.end)}
                      </p>
                    )}
                  </div>
                  <div className="flex items-center gap-3 text-xs">
                    <span className="flex items-center gap-1">
                      {data.sentiment_trend?.includes('increas') ? <TrendingUp className="h-3 w-3 text-green-500" /> :
                       data.sentiment_trend?.includes('decreas') ? <TrendingDown className="h-3 w-3 text-red-500" /> :
                       <Minus className="h-3 w-3 text-slate-400" />}
                      Sentiment: {data.sentiment_trend || 'stable'}
                    </span>
                    <span className="flex items-center gap-1">
                      {data.price_trend?.includes('increas') ? <TrendingUp className="h-3 w-3 text-green-500" /> :
                       data.price_trend?.includes('decreas') ? <TrendingDown className="h-3 w-3 text-red-500" /> :
                       <Minus className="h-3 w-3 text-slate-400" />}
                      Price: {data.price_trend || 'stable'}
                    </span>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="h-[320px]">
                  <ResponsiveContainer width="100%" height="100%">
                    <ComposedChart margin={{ top: 10, right: 20, bottom: 30, left: 50 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis 
                        type="number"
                        dataKey="sentiment"
                        domain={domains.x}
                        tickFormatter={(v) => v.toFixed(1)}
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        label={{ value: 'Sentiment Score', position: 'bottom', offset: 15, style: { fontSize: 11, fill: '#64748b' } }}
                      />
                      <YAxis 
                        type="number"
                        dataKey="price"
                        domain={domains.y}
                        tickFormatter={(v) => `$${v.toFixed(0)}`}
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        label={{ value: 'Price ($)', angle: -90, position: 'insideLeft', offset: 10, style: { fontSize: 11, fill: '#64748b' } }}
                      />
                      <RechartsTooltip content={<ScatterTooltip />} />
                      <ReferenceLine x={0} stroke="#cbd5e1" strokeDasharray="4 4" />
                      
                      {/* Regression line */}
                      {regressionLine && (
                        <Line 
                          data={regressionLine}
                          dataKey="price"
                          stroke={r > 0 ? '#22c55e' : r < 0 ? '#ef4444' : '#94a3b8'}
                          strokeWidth={2}
                          strokeDasharray="6 3"
                          dot={false}
                        />
                      )}
                      
                      {/* Data points */}
                      <Scatter data={scatterData} fill="#3B82F6">
                        {scatterData.map((_: any, i: number) => (
                          <Cell key={i} fill={getScatterColor(scatterData[i].sentiment)} />
                        ))}
                      </Scatter>
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
                
                {/* Compact Legend */}
                <div className="flex justify-center gap-4 mt-2 text-xs text-slate-500">
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-green-500" /> Positive
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Neutral
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-2.5 h-2.5 rounded-full bg-red-500" /> Negative
                  </span>
                  {regressionLine && (
                    <span className="flex items-center gap-1">
                      <span className="w-4 h-0.5 bg-slate-400" style={{borderTop: '2px dashed'}} /> Trend
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Summary - Only show if meaningful correlation exists */}
            {dataMetrics.canCalculateCorrelation && Math.abs(r) >= 0.1 && (
              <Card className="bg-slate-50">
                <CardContent className="py-4">
                  <div className="flex items-start gap-3">
                    <Info className="h-5 w-5 text-blue-500 mt-0.5 shrink-0" />
                    <div className="text-sm text-slate-700">
                      <p>
                        <strong>Result:</strong> {getCorrelationLabel(r)} correlation (r = {r.toFixed(3)}) 
                        between sentiment and price for {selectedStock}.
                        {pValue < 0.05 
                          ? ` This relationship is statistically significant (p < 0.05).`
                          : ` However, this result is not statistically significant (p = ${pValue.toFixed(3)}).`
                        }
                      </p>
                      <p className="mt-1 text-slate-500">
                        Sentiment explains approximately {(rSquared * 100).toFixed(1)}% of price variation.
                        95% CI: [{ci[0]?.toFixed(3)}, {ci[1]?.toFixed(3)}]
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Quick Reference - Collapsible */}
            <details className="group">
              <summary className="cursor-pointer text-sm text-slate-500 hover:text-slate-700 flex items-center gap-1">
                <span className="group-open:rotate-90 transition-transform">▶</span>
                How to interpret these results
              </summary>
              <div className="mt-2 p-3 bg-slate-50 rounded-lg text-xs text-slate-600 grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <strong>Correlation (r)</strong>
                  <p>-1 to +1 scale. ±0.7+ strong, ±0.4+ moderate, below weak.</p>
                </div>
                <div>
                  <strong>R² (Explained)</strong>
                  <p>% of price movement explained by sentiment. Higher = better predictor.</p>
                </div>
                <div>
                  <strong>P-Value</strong>
                  <p>Below 0.05 = statistically significant (unlikely due to chance).</p>
                </div>
                <div>
                  <strong>Sample Size</strong>
                  <p>30+ ideal, 10+ acceptable. More data = more reliable results.</p>
                </div>
              </div>
            </details>
          </>
        )}

        {/* No Data State */}
        {!isLoadingCorrelation && !correlationError && !data && selectedStock && (
          <Alert className="border-blue-200 bg-blue-50">
            <AlertCircle className="h-4 w-4 text-blue-600" />
            <AlertTitle className="text-blue-900">No Data Available</AlertTitle>
            <AlertDescription className="text-blue-800">
              No data found for {selectedStock} in the {timeRange} timeframe.
              The data collection pipeline may need to run. Try a longer timeframe or check back later.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </UserLayout>
  );
};

export default CorrelationAnalysis;
