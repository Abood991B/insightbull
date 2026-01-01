import { useQuery } from '@tanstack/react-query';
import { useState, useEffect, useMemo } from "react";
import { useSearchParams } from "react-router-dom";
import UserLayout from "@/shared/components/layouts/UserLayout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/shared/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/shared/components/ui/select";
import { Alert, AlertDescription } from "@/shared/components/ui/alert";
import { Skeleton } from "@/shared/components/ui/skeleton";
import { 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Activity,
  BarChart3,
  Zap,
  Info,
  AlertCircle
} from 'lucide-react';
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  ComposedChart,
  Line,
  ReferenceLine,
  Legend
} from 'recharts';

import { stockService } from "@/api/services/stock.service";
import { analysisService } from "@/api/services/analysis.service";
import { formatDateTime } from "@/shared/utils/timezone";
import { EmptyWatchlistState } from "@/shared/components/states";

// --- Professional Color Palette ---
const COLORS = {
  primary: '#2563EB',
  positive: '#10B981',
  negative: '#EF4444',
  neutral: '#64748B',
  grid: '#E2E8F0',
  background: '#F8FAFC',
};

// --- Timeframe Options (Synchronized across all pages) ---
const TIMEFRAME_OPTIONS = [
  { value: '1d', label: '1D' },
  { value: '7d', label: '7D' },
  { value: '14d', label: '14D' },
  { value: '30d', label: '30D' },
] as const;

type TimeframeValue = typeof TIMEFRAME_OPTIONS[number]['value'];

// --- Custom Tooltip Component ---
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/95 backdrop-blur-sm p-3 border border-slate-200 shadow-xl rounded-lg text-xs z-50 min-w-[180px]">
        <p className="font-semibold text-slate-700 mb-2 border-b pb-1">{label}</p>
        <div className="space-y-1.5">
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div 
                  className="w-2.5 h-2.5 rounded-full" 
                  style={{ backgroundColor: entry.color || entry.fill }} 
                />
                <span className="text-slate-600">{entry.name}:</span>
              </div>
              <span className="font-mono font-medium text-slate-800">
                {typeof entry.value === 'number' 
                  ? entry.value.toFixed(3)
                  : entry.value}
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }
  return null;
};

// --- Metric Card Component ---
interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: React.ReactNode;
  colorClass: string;
  trend?: 'up' | 'down' | 'neutral';
}

const MetricCard = ({ title, value, subtitle, icon, colorClass, trend }: MetricCardProps) => (
  <Card className="relative overflow-hidden border-0 shadow-sm hover:shadow-md transition-shadow">
    <div className={`absolute top-0 left-0 w-1 h-full ${colorClass}`} />
    <CardContent className="p-4">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-xs font-medium text-slate-500 uppercase tracking-wide">{title}</p>
          <div className="flex items-center gap-2">
            <span className={`text-2xl font-bold ${
              trend === 'up' ? 'text-emerald-600' : 
              trend === 'down' ? 'text-rose-600' : 
              'text-slate-700'
            }`}>
              {value}
            </span>
            {trend && (
              trend === 'up' ? <TrendingUp className="h-4 w-4 text-emerald-500" /> :
              trend === 'down' ? <TrendingDown className="h-4 w-4 text-rose-500" /> :
              <Minus className="h-4 w-4 text-slate-400" />
            )}
          </div>
          {subtitle && <p className="text-xs text-slate-500">{subtitle}</p>}
        </div>
        <div className="p-2 rounded-lg bg-slate-50">
          {icon}
        </div>
      </div>
    </CardContent>
  </Card>
);

// --- Main Component ---
const SentimentTrends = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const timeframeFromUrl = searchParams.get('timeframe') as TimeframeValue | null;
  
  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');
  const [timeRange, setTimeRange] = useState<TimeframeValue>(
    timeframeFromUrl && ['1d', '7d', '14d', '30d'].includes(timeframeFromUrl) 
      ? timeframeFromUrl 
      : '7d'
  );

  // --- Data Fetching ---
  const { data: stockOptionsResponse, isLoading: isLoadingStocks } = useQuery({
    queryKey: ['stock-options'],
    queryFn: () => stockService.getStockOptions(true),
    staleTime: 30000,
  });

  const { 
    data: sentimentResponse, 
    isLoading: isLoadingSentiment, 
    error: sentimentError,
    isFetching
  } = useQuery({
    queryKey: ['sentiment-history', selectedStock, timeRange],
    queryFn: () => analysisService.getSentimentHistory(selectedStock, timeRange),
    enabled: !!selectedStock,
    staleTime: 60000,
  });

  // Extract options
  const stockOptions = stockOptionsResponse || [];

  // --- Effects ---
  useEffect(() => {
    if (!selectedStock && stockOptions.length > 0) {
      const firstStock = stockOptions[0].value;
      setSelectedStock(firstStock);
      setSearchParams({ symbol: firstStock, timeframe: timeRange });
    }
  }, [stockOptions, selectedStock, timeRange, setSearchParams]);

  // --- Handlers ---
  const handleStockChange = (symbol: string) => {
    setSelectedStock(symbol);
    setSearchParams({ symbol, timeframe: timeRange });
  };

  const handleTimeRangeChange = (range: string) => {
    const validRange = range as TimeframeValue;
    setTimeRange(validRange);
    setSearchParams({ symbol: selectedStock, timeframe: validRange });
  };

  // --- Data Processing ---
  const sentimentData = sentimentResponse?.data;

  // Process chart data using BUCKETING approach (same as SentimentVsPrice)
  // This aggregates multiple sentiment points within the same time window
  // Pipeline runs process multiple articles at once - we aggregate them per bucket
  const chartData = useMemo(() => {
    if (!sentimentData?.data_points?.length) return [];

    const dataPoints = sentimentData.data_points;
    
    // Bucket size matches pipeline schedule
    // 1-day: 45-min buckets (matches 45-min pipeline runs)
    // 7d/14d/30d: 1-hour buckets for cleaner visualization
    const bucketMs = timeRange === '1d' 
      ? 45 * 60 * 1000  // 45-minute buckets
      : 60 * 60 * 1000; // 1-hour buckets

    const bucketMap = new Map<number, {
      timestamp: number;
      sentiments: number[];
    }>();

    // Floor timestamp to bucket boundary
    const getBucketKey = (ts: number) => Math.floor(ts / bucketMs) * bucketMs;

    // Aggregate ALL sentiment scores into buckets
    dataPoints.forEach(point => {
      const ts = new Date(point.timestamp).getTime();
      const bucketKey = getBucketKey(ts);
      
      if (!bucketMap.has(bucketKey)) {
        bucketMap.set(bucketKey, {
          timestamp: bucketKey,
          sentiments: []
        });
      }
      bucketMap.get(bucketKey)!.sentiments.push(point.sentiment_score);
    });

    // Convert buckets to chart format with proper label formatting
    return Array.from(bucketMap.values())
      .map((bucket) => {
        const avgSentiment = bucket.sentiments.reduce((a, b) => a + b, 0) / bucket.sentiments.length;
        const maxSentiment = Math.max(...bucket.sentiments);
        const minSentiment = Math.min(...bucket.sentiments);
        
        // Format label using the timezone utility (same as SentimentVsPrice)
        const label = formatDateTime(new Date(bucket.timestamp).toISOString(), {
          month: 'short',
          day: 'numeric',
          hour: '2-digit',
          minute: '2-digit'
        });
        
        return {
          timestamp: bucket.timestamp,
          date: label,
          sentiment: avgSentiment,
          high: maxSentiment,
          low: minSentiment,
          count: bucket.sentiments.length,
          fill: avgSentiment >= 0 ? COLORS.positive : COLORS.negative
        };
      })
      .sort((a, b) => a.timestamp - b.timestamp);
  }, [sentimentData, timeRange]);

  // Calculate aggregates for distribution chart
  // Uses hourly breakdown for 1d timeframe or when all data is from same day
  // Uses daily breakdown for longer timeframes with multi-day data
  const dailyData = useMemo(() => {
    if (!sentimentData?.data_points?.length) return [];

    const dataPoints = sentimentData.data_points;
    
    // Check if all data is from the same day
    const dates = new Set(dataPoints.map(p => 
      new Date(p.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
    ));
    const allSameDay = dates.size === 1;
    
    // Use hourly breakdown for 1d timeframe or when all data is from same day
    const useHourly = timeRange === '1d' || allSameDay;
    
    const aggregateMap = new Map<string, { 
      positive: number; 
      negative: number; 
      neutral: number; 
      total: number;
      timestamp: number;
    }>();

    dataPoints.forEach(point => {
      const date = new Date(point.timestamp);
      let key: string;
      
      if (useHourly) {
        // Hourly breakdown
        const hour = date.getHours();
        const hourStr = `${hour.toString().padStart(2, '0')}:00`;
        const dayStr = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        key = allSameDay ? hourStr : `${dayStr} ${hourStr}`;
      } else {
        // Daily breakdown
        key = date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      }
      
      if (!aggregateMap.has(key)) {
        aggregateMap.set(key, { 
          positive: 0, 
          negative: 0, 
          neutral: 0, 
          total: 0,
          timestamp: date.getTime()
        });
      }
      
      const entry = aggregateMap.get(key)!;
      entry.total++;
      
      if (point.sentiment_score > 0.05) {
        entry.positive++;
      } else if (point.sentiment_score < -0.05) {
        entry.negative++;
      } else {
        entry.neutral++;
      }
    });

    return Array.from(aggregateMap.entries())
      .map(([label, data]) => ({
        date: label,
        positive: data.total > 0 ? Math.round((data.positive / data.total) * 100) : 0,
        neutral: data.total > 0 ? Math.round((data.neutral / data.total) * 100) : 0,
        negative: data.total > 0 ? Math.round((data.negative / data.total) * 100) : 0,
        total: data.total,
        timestamp: data.timestamp
      }))
      .sort((a, b) => a.timestamp - b.timestamp);
  }, [sentimentData, timeRange]);

  // --- Metrics Calculation ---
  const metrics = useMemo(() => {
    if (!sentimentData) return null;

    const avgSentiment = sentimentData.avg_sentiment ?? 0;
    const volatility = sentimentData.sentiment_volatility ?? 0;
    const totalRecords = sentimentData.total_records ?? 0;
    const dataCoverage = sentimentData.data_coverage ?? 0;

    // Determine trend
    let trend: 'up' | 'down' | 'neutral' = 'neutral';
    if (avgSentiment > 0.1) trend = 'up';
    else if (avgSentiment < -0.1) trend = 'down';

    // Determine trend label
    let trendLabel = 'Neutral';
    if (avgSentiment > 0.3) trendLabel = 'Bullish';
    else if (avgSentiment > 0.1) trendLabel = 'Positive';
    else if (avgSentiment < -0.3) trendLabel = 'Bearish';
    else if (avgSentiment < -0.1) trendLabel = 'Negative';

    // Volatility level
    let volatilityLabel = 'Low';
    if (volatility > 0.4) volatilityLabel = 'High';
    else if (volatility > 0.2) volatilityLabel = 'Medium';

    // Momentum strength
    let momentumLabel = 'Weak';
    if (Math.abs(avgSentiment) > 0.5) momentumLabel = 'Strong';
    else if (Math.abs(avgSentiment) > 0.2) momentumLabel = 'Moderate';

    return {
      avgSentiment,
      volatility,
      totalRecords,
      dataCoverage,
      trend,
      trendLabel,
      volatilityLabel,
      momentumLabel
    };
  }, [sentimentData]);

  const hasData = sentimentData && sentimentData.total_records > 0;
  const hasChartData = chartData.length > 0;

  // --- Loading State ---
  if (isLoadingStocks) {
    return (
      <UserLayout>
        <div className="space-y-6 p-4 md:p-6">
          <Skeleton className="h-10 w-64" />
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
          </div>
          <Skeleton className="h-80" />
        </div>
      </UserLayout>
    );
  }

  // --- Empty Watchlist ---
  if (!stockOptions.length) {
    return <UserLayout><EmptyWatchlistState /></UserLayout>;
  }

  return (
    <UserLayout>
      <div className="space-y-6 p-4 md:p-6">
        
        {/* === HEADER === */}
        <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900">
              Sentiment Trends
            </h1>
            <p className="text-slate-500 text-sm mt-1">
              Analyze sentiment patterns and momentum over time
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 bg-white p-2 rounded-lg border shadow-sm">
            {/* Stock Selector */}
            <Select value={selectedStock} onValueChange={handleStockChange}>
              <SelectTrigger className="w-[140px] md:w-[160px] h-9">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                {stockOptions.map(option => (
                  <SelectItem key={option.value} value={option.value}>
                    {option.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            {/* Timeframe Selector */}
            <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
              {TIMEFRAME_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => handleTimeRangeChange(option.value)}
                  className={`px-3 py-1.5 text-xs font-medium rounded-md transition-all ${
                    timeRange === option.value
                      ? 'bg-white text-blue-600 shadow-sm'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  {option.label}
                </button>
              ))}
            </div>

            {/* Loading Indicator */}
            {isFetching && (
              <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
            )}
          </div>
        </div>

        {/* === ERROR STATE === */}
        {sentimentError && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              Failed to load sentiment data. Please try again.
            </AlertDescription>
          </Alert>
        )}

        {/* === LOADING STATE === */}
        {isLoadingSentiment && (
          <div className="space-y-6">
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map(i => <Skeleton key={i} className="h-24" />)}
            </div>
            <Skeleton className="h-[400px]" />
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Skeleton className="h-[320px]" />
              <Skeleton className="h-[320px]" />
            </div>
          </div>
        )}

        {/* === NO DATA STATE === */}
        {!isLoadingSentiment && !hasData && selectedStock && (
          <Alert className="border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-800">
              No sentiment data available for <strong>{selectedStock}</strong> in the selected timeframe. 
              Run the data pipeline to collect sentiment data.
            </AlertDescription>
          </Alert>
        )}

        {/* === METRICS CARDS === */}
        {!isLoadingSentiment && metrics && hasData && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              title="Overall Trend"
              value={metrics.trendLabel}
              subtitle={`Score: ${metrics.avgSentiment >= 0 ? '+' : ''}${metrics.avgSentiment.toFixed(3)}`}
              icon={<TrendingUp className="h-5 w-5 text-slate-600" />}
              colorClass="bg-emerald-500"
              trend={metrics.trend}
            />
            <MetricCard
              title="Volatility"
              value={metrics.volatilityLabel}
              subtitle={`Std Dev: ${metrics.volatility.toFixed(3)}`}
              icon={<Activity className="h-5 w-5 text-slate-600" />}
              colorClass="bg-amber-500"
            />
            <MetricCard
              title="Momentum"
              value={metrics.momentumLabel}
              subtitle={`Strength: ${(Math.abs(metrics.avgSentiment) * 100).toFixed(1)}%`}
              icon={<Zap className="h-5 w-5 text-slate-600" />}
              colorClass="bg-blue-500"
            />
            <MetricCard
              title="Data Points"
              value={metrics.totalRecords.toLocaleString()}
              subtitle={`Coverage: ${(metrics.dataCoverage * 100).toFixed(0)}%`}
              icon={<BarChart3 className="h-5 w-5 text-slate-600" />}
              colorClass="bg-purple-500"
            />
          </div>
        )}

        {/* === MAIN CHART: Sentiment Timeline === */}
        {!isLoadingSentiment && hasChartData && (
          <Card className="shadow-sm border-slate-200">
            <CardHeader className="pb-2 border-b border-slate-100">
              <CardTitle className="text-base flex items-center gap-2">
                <Activity className="h-4 w-4 text-blue-500" />
                Sentiment Timeline
              </CardTitle>
              <CardDescription>
                Individual sentiment scores over time
              </CardDescription>
            </CardHeader>
            <CardContent className="pt-4">
              <div style={{ width: '100%', height: 400 }}>
                <ResponsiveContainer>
                  <ComposedChart data={chartData} margin={{ top: 20, right: 30, left: 10, bottom: 60 }}>
                    <defs>
                      <linearGradient id="sentimentGradient" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor={COLORS.primary} stopOpacity={0.3}/>
                        <stop offset="95%" stopColor={COLORS.primary} stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.grid} />
                    <XAxis 
                      dataKey="date" 
                      tick={{ fontSize: 10, fill: '#64748b' }}
                      axisLine={false}
                      tickLine={false}
                      angle={-45}
                      textAnchor="end"
                      height={60}
                      interval={chartData.length > 20 ? Math.floor(chartData.length / 10) : 0}
                    />
                    <YAxis 
                      domain={[-1, 1]}
                      tick={{ fontSize: 11, fill: '#64748b' }}
                      axisLine={false}
                      tickLine={false}
                      tickFormatter={(val) => val.toFixed(1)}
                      width={40}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend wrapperStyle={{ fontSize: '12px', paddingTop: '10px' }} />
                    <ReferenceLine y={0} stroke={COLORS.neutral} strokeDasharray="3 3" />
                    
                    {/* Sentiment Area with visible dots */}
                    <Area
                      type="monotone"
                      dataKey="sentiment"
                      stroke={COLORS.primary}
                      fill="url(#sentimentGradient)"
                      strokeWidth={2}
                      name="Avg Sentiment"
                      dot={{ fill: COLORS.primary, r: 3, strokeWidth: 0 }}
                      activeDot={{ fill: COLORS.primary, r: 5, strokeWidth: 2, stroke: '#fff' }}
                      connectNulls
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>
        )}

        {/* === SECONDARY CHARTS ROW === */}
        {!isLoadingSentiment && hasChartData && dailyData.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Distribution Chart */}
            <Card className="shadow-sm border-slate-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <BarChart3 className="h-4 w-4 text-purple-500" />
                  Sentiment Distribution
                </CardTitle>
                <CardDescription>
                  Percentage breakdown by {dailyData.length > 0 && dailyData[0].date.includes(':') ? 'hour' : 'day'}
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <div style={{ width: '100%', height: 280 }}>
                  <ResponsiveContainer>
                    <AreaChart data={dailyData} margin={{ top: 10, right: 10, left: 0, bottom: 40 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.grid} />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 10, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                        angle={-45}
                        textAnchor="end"
                        height={50}
                      />
                      <YAxis 
                        domain={[0, 100]}
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(val) => `${val}%`}
                        width={45}
                      />
                      <Tooltip 
                        formatter={(value: number, name: string) => [`${value}%`, name]}
                        contentStyle={{ 
                          backgroundColor: 'white', 
                          border: '1px solid #e2e8f0',
                          borderRadius: '8px',
                          fontSize: '12px'
                        }}
                      />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <Area 
                        type="monotone" 
                        dataKey="positive" 
                        stackId="1"
                        stroke={COLORS.positive}
                        fill={COLORS.positive}
                        fillOpacity={0.8}
                        name="Positive"
                        dot={{ fill: COLORS.positive, r: 3, strokeWidth: 1, stroke: '#fff' }}
                        activeDot={{ fill: COLORS.positive, r: 5, strokeWidth: 2, stroke: '#fff' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="neutral" 
                        stackId="1"
                        stroke={COLORS.neutral}
                        fill={COLORS.neutral}
                        fillOpacity={0.6}
                        name="Neutral"
                        dot={{ fill: COLORS.neutral, r: 3, strokeWidth: 1, stroke: '#fff' }}
                        activeDot={{ fill: COLORS.neutral, r: 5, strokeWidth: 2, stroke: '#fff' }}
                      />
                      <Area 
                        type="monotone" 
                        dataKey="negative" 
                        stackId="1"
                        stroke={COLORS.negative}
                        fill={COLORS.negative}
                        fillOpacity={0.8}
                        name="Negative"
                        dot={{ fill: COLORS.negative, r: 3, strokeWidth: 1, stroke: '#fff' }}
                        activeDot={{ fill: COLORS.negative, r: 5, strokeWidth: 2, stroke: '#fff' }}
                      />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>

            {/* Sentiment Momentum Chart */}
            <Card className="shadow-sm border-slate-200">
              <CardHeader className="pb-2">
                <CardTitle className="text-base flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-500" />
                  Sentiment Momentum
                </CardTitle>
                <CardDescription>
                  Per-bucket sentiment range: <span className="text-emerald-600 font-medium">High</span> = most positive, 
                  <span className="text-blue-600 font-medium"> Avg</span> = mean score, 
                  <span className="text-rose-600 font-medium"> Low</span> = most negative
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-4">
                <div style={{ width: '100%', height: 280 }}>
                  <ResponsiveContainer>
                    <ComposedChart data={chartData} margin={{ top: 10, right: 10, left: 0, bottom: 40 }}>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.grid} />
                      <XAxis 
                        dataKey="date" 
                        tick={{ fontSize: 10, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                        angle={-45}
                        textAnchor="end"
                        height={50}
                        interval={chartData.length > 20 ? Math.floor(chartData.length / 8) : 0}
                      />
                      <YAxis 
                        domain={[-1, 1]}
                        tick={{ fontSize: 11, fill: '#64748b' }}
                        axisLine={false}
                        tickLine={false}
                        tickFormatter={(val) => val.toFixed(1)}
                        width={40}
                      />
                      <Tooltip content={<CustomTooltip />} />
                      <Legend wrapperStyle={{ fontSize: '11px' }} />
                      <ReferenceLine y={0} stroke={COLORS.neutral} strokeDasharray="3 3" />
                      
                      {/* High Line */}
                      <Line
                        type="monotone"
                        dataKey="high"
                        stroke={COLORS.positive}
                        strokeWidth={1.5}
                        dot={false}
                        name="High"
                        strokeDasharray="4 2"
                        connectNulls
                      />
                      
                      {/* Average Line */}
                      <Line
                        type="monotone"
                        dataKey="sentiment"
                        stroke={COLORS.primary}
                        strokeWidth={2}
                        dot={{ fill: COLORS.primary, r: 3 }}
                        activeDot={{ fill: COLORS.primary, r: 5, strokeWidth: 2, stroke: '#fff' }}
                        name="Avg"
                        connectNulls
                      />
                      
                      {/* Low Line */}
                      <Line
                        type="monotone"
                        dataKey="low"
                        stroke={COLORS.negative}
                        strokeWidth={1.5}
                        dot={false}
                        name="Low"
                        strokeDasharray="4 2"
                        connectNulls
                      />
                    </ComposedChart>
                  </ResponsiveContainer>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* === INSIGHTS CARD === */}
        {!isLoadingSentiment && metrics && hasData && (
          <Card className="shadow-sm border-slate-200 bg-slate-50">
            <CardContent className="p-4">
              <div className="flex items-start gap-3">
                <Info className="h-5 w-5 text-blue-500 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-slate-600 space-y-1">
                  <p>
                    <strong>Analysis Summary:</strong> {selectedStock} shows a{' '}
                    <span className={metrics.trend === 'up' ? 'text-emerald-600 font-medium' : metrics.trend === 'down' ? 'text-rose-600 font-medium' : 'text-slate-600'}>
                      {metrics.trendLabel.toLowerCase()}
                    </span>{' '}
                    sentiment trend with{' '}
                    <span className="font-medium">{metrics.volatilityLabel.toLowerCase()}</span> volatility 
                    over the selected {timeRange === '1d' ? '24-hour' : timeRange === '7d' ? '7-day' : timeRange === '14d' ? '14-day' : '30-day'} period.
                  </p>
                  <p className="text-xs text-slate-500">
                    Based on {metrics.totalRecords.toLocaleString()} sentiment data points with {(metrics.dataCoverage * 100).toFixed(0)}% data coverage.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

      </div>
    </UserLayout>
  );
};

export default SentimentTrends;
