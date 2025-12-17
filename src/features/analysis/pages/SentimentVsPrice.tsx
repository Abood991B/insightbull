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
  Info,
  ArrowUpRight,
  ArrowDownRight,
  Activity,
  Calendar,
  Zap
} from 'lucide-react';
import {
  AreaChart,
  Area,
  Bar,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ComposedChart,
  Cell,
  ReferenceLine,
  Brush,
  Legend
} from 'recharts';

// Import services
import { stockService } from "@/api/services/stock.service";
import { analysisService } from "@/api/services/analysis.service";

// Import utilities
import { formatDateTime } from "@/shared/utils/timezone";
import { EmptyWatchlistState } from "@/shared/components/states";

// --- Timeframe Options (Synchronized across all pages) ---
const TIMEFRAME_OPTIONS = [
  { value: '1d', label: '1D' },
  { value: '7d', label: '7D' },
  { value: '14d', label: '14D' },
  { value: '30d', label: '30D' },
] as const;

type TimeframeValue = typeof TIMEFRAME_OPTIONS[number]['value'];

// Professional Financial Colors
const COLORS = {
  price: '#2563EB',     // Standard Blue
  priceFill: '#3B82F6', // Lighter Blue fill
  positive: '#10B981',  // Emerald Green
  negative: '#EF4444',  // Rose Red
  neutral: '#94A3B8',   // Slate Gray
  grid: '#E2E8F0',      // Light Gray border
};

// --- Custom Tooltip Component ---
const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    // Get article count from the data point
    const dataPoint = payload[0]?.payload;
    const articleCount = dataPoint?.articleCount || 0;
    
    return (
      <div className="bg-white/95 backdrop-blur-sm p-3 border border-slate-200 shadow-xl rounded-lg text-xs z-50">
        <p className="font-semibold text-slate-700 mb-2 border-b pb-1">{label}</p>
        <div className="space-y-1">
          {payload.map((entry: any, index: number) => (
            <div key={index} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color || entry.fill }} />
                <span className="text-slate-500 capitalize">{entry.name}:</span>
              </div>
              <span className="font-mono font-medium text-slate-700">
                {typeof entry.value === 'number' 
                  ? entry.name.includes('Change') || entry.name.includes('%') 
                    ? `${entry.value > 0 ? '+' : ''}${entry.value.toFixed(2)}%`
                    : entry.name.toLowerCase().includes('price') && !entry.name.includes('Change')
                      ? `$${entry.value.toFixed(2)}` 
                      : entry.value.toFixed(2)
                  : entry.value}
              </span>
            </div>
          ))}
          {articleCount > 0 && (
            <div className="flex items-center justify-between gap-4 pt-1 border-t border-slate-100 mt-1">
              <span className="text-slate-400">Articles analyzed:</span>
              <span className="font-mono font-medium text-slate-600">{articleCount}</span>
            </div>
          )}
        </div>
      </div>
    );
  }
  return null;
};

const SentimentVsPrice = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const symbolFromUrl = searchParams.get('symbol');
  const timeframeFromUrl = searchParams.get('timeframe') as TimeframeValue | null;

  const [selectedStock, setSelectedStock] = useState(symbolFromUrl || '');
  const [timeRange, setTimeRange] = useState<TimeframeValue>(
    timeframeFromUrl && ['1d', '7d', '14d', '30d'].includes(timeframeFromUrl) 
      ? timeframeFromUrl 
      : '7d'
  );

  // --- 1. Data Fetching ---
  const { data: stockOptionsResponse, isLoading: isLoadingStocks } = useQuery({
    queryKey: ['stock-options'],
    queryFn: () => stockService.getStockOptions(true),
    staleTime: 30000,
  });

  const { data: stockDetailResponse, isLoading: isLoadingDetail } = useQuery({
    queryKey: ['stock-detail', selectedStock, timeRange],
    queryFn: () => stockService.getStockDetail(selectedStock, timeRange),
    enabled: !!selectedStock,
  });

  const { data: sentimentResponse, isLoading: isLoadingSentiment } = useQuery({
    queryKey: ['sentiment-history', selectedStock, timeRange],
    queryFn: () => analysisService.getSentimentHistory(selectedStock, timeRange),
    enabled: !!selectedStock,
  });

  // --- 2. Effects ---
  useEffect(() => {
    if (!selectedStock && stockOptionsResponse?.length) {
      const first = stockOptionsResponse[0].value;
      setSelectedStock(first);
      setSearchParams({ symbol: first, timeframe: timeRange });
    }
  }, [stockOptionsResponse, selectedStock, timeRange, setSearchParams]);

  const handleStockChange = (val: string) => {
    setSelectedStock(val);
    setSearchParams({ symbol: val, timeframe: timeRange });
  };

  const handleTimeChange = (val: string) => {
    const range = val as TimeframeValue;
    setTimeRange(range);
    setSearchParams({ symbol: selectedStock, timeframe: range });
  };

  // --- 3. Data Processing ---
  const stockOptions = stockOptionsResponse || [];
  const stockDetail = stockDetailResponse?.data;
  const sentimentHistory = sentimentResponse?.data;

  // UNIFIED TIMELINE: Price from YFinance intervals, Sentiment aggregated by pipeline runs
  // 
  // KEY INSIGHT: Each pipeline run processes MULTIPLE news articles per stock.
  // Example: TSLA had 33 articles with scores from -0.97 to +0.95 in the SAME minute.
  // This is CORRECT - different articles have different sentiments.
  // 
  // SOLUTION: Aggregate all articles from each pipeline run into a single sentiment value.
  // - Pipeline runs every 45 minutes during market hours (optimized for Gemma 3 27B 30 RPM limit)
  // - Use 45-minute buckets for 1-day view (matches pipeline schedule)
  // - Use 1-hour buckets for multi-day views
  const chartData = useMemo(() => {
    if (!stockDetail?.price_history) return [];

    // Bucket size matches pipeline schedule and YFinance intervals
    // 1-day: 45-min buckets (matches 45-min pipeline runs)
    // 7d/14d: 1-hour buckets (matches YFinance 1h interval)
    const bucketMs = timeRange === '1d' 
      ? 45 * 60 * 1000  // 45-minute buckets for 1-day
      : 60 * 60 * 1000; // 1-hour buckets for 7d/14d

    // Create a map of time buckets using PRICE data as the authoritative timeline
    const bucketMap = new Map<number, {
      timestamp: number;
      date: string;
      price: number | null;
      sentiments: number[];
    }>();

    // Helper to get bucket key (floor to bucket boundary)
    const getBucketKey = (ts: number) => Math.floor(ts / bucketMs) * bucketMs;

    // Step 1: Create buckets from PRICE history (YFinance provides clean intervals)
    stockDetail.price_history.forEach(point => {
      const ts = new Date(point.timestamp).getTime();
      const bucketKey = getBucketKey(ts);
      
      // Use the LAST price in each bucket (close price concept)
      if (!bucketMap.has(bucketKey)) {
        bucketMap.set(bucketKey, {
          timestamp: bucketKey,
          date: formatDateTime(new Date(bucketKey).toISOString(), { 
            month: 'short', 
            day: 'numeric', 
            hour: '2-digit', 
            minute: '2-digit' 
          }),
          price: point.close_price,
          sentiments: []
        });
      } else {
        // Update to latest price in bucket
        bucketMap.get(bucketKey)!.price = point.close_price;
      }
    });

    // Step 2: Aggregate ALL sentiment articles from each pipeline run into buckets
    // Each bucket represents one pipeline run's aggregated sentiment
    if (sentimentHistory?.data_points) {
      sentimentHistory.data_points.forEach(point => {
        const ts = new Date(point.timestamp).getTime();
        const bucketKey = getBucketKey(ts);
        
        // Add to existing bucket or find nearest
        if (bucketMap.has(bucketKey)) {
          bucketMap.get(bucketKey)!.sentiments.push(point.sentiment_score);
        } else {
          // Find nearest bucket within 1 bucket span
          const maxDiff = bucketMs;
          let nearestKey: number | null = null;
          let minDiff = Infinity;
          
          bucketMap.forEach((_, key) => {
            const diff = Math.abs(key - bucketKey);
            if (diff < minDiff && diff <= maxDiff) {
              minDiff = diff;
              nearestKey = key;
            }
          });
          
          if (nearestKey !== null) {
            bucketMap.get(nearestKey)!.sentiments.push(point.sentiment_score);
          }
        }
      });
    }

    // Step 3: Convert to chart format
    // Sentiment = AVERAGE of all articles in that pipeline run (represents overall market mood)
    return Array.from(bucketMap.values())
      .map(bucket => {
        const avgSentiment = bucket.sentiments.length > 0 
          ? bucket.sentiments.reduce((a, b) => a + b, 0) / bucket.sentiments.length 
          : null;
        
        return {
          timestamp: bucket.timestamp,
          date: bucket.date,
          price: bucket.price,
          sentiment: avgSentiment,
          articleCount: bucket.sentiments.length,  // Number of articles analyzed
          fill: avgSentiment !== null
            ? avgSentiment > 0 ? COLORS.positive : COLORS.negative
            : COLORS.neutral
        };
      })
      .sort((a, b) => a.timestamp - b.timestamp);
  }, [stockDetail, sentimentHistory, timeRange]);

  // Chart 2 Data: Daily Aggregated Impact (Easier to read)
  const dailyImpactData = useMemo(() => {
    if (!stockDetail?.price_history || !sentimentHistory?.data_points) return [];
    
    // Group by Day
    const dailyMap = new Map();
    
    // Aggregate Price
    stockDetail.price_history.forEach(p => {
      const day = new Date(p.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      if (!dailyMap.has(day)) dailyMap.set(day, { open: p.open_price || p.close_price, close: p.close_price, sentimentSum: 0, count: 0 });
      dailyMap.get(day).close = p.close_price; // Keep updating to get final close
    });

    // Aggregate Sentiment
    sentimentHistory.data_points.forEach(s => {
      const day = new Date(s.timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
      if (dailyMap.has(day)) {
        const entry = dailyMap.get(day);
        entry.sentimentSum += s.sentiment_score;
        entry.count += 1;
      }
    });

    return Array.from(dailyMap.entries())
      .map(([date, d]) => ({
        date,
        priceChange: ((d.close - d.open) / d.open) * 100,
        avgSentiment: d.count > 0 ? d.sentimentSum / d.count : 0,
        hasData: d.count > 0
      }))
      .filter(d => d.hasData) // Only show days with news
      .slice(timeRange === '30d' ? -30 : -14); // Adjust max days based on timeframe
  }, [stockDetail, sentimentHistory, timeRange]);

  const isLoading = isLoadingStocks || isLoadingDetail || isLoadingSentiment;

  // --- 4. Render ---
  if (isLoading) return <UserLayout><div className="p-8"><Skeleton className="h-96 w-full" /></div></UserLayout>;
  if (!stockOptions.length) return <UserLayout><EmptyWatchlistState /></UserLayout>;

  return (
    <UserLayout>
      <div className="space-y-6">
        
        {/* HEADER */}
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
          <div>
            <h1 className="text-2xl md:text-3xl font-bold text-slate-900">Sentiment vs Price Analysis</h1>
            <p className="text-slate-500 text-sm mt-1">Visualize how news sentiment impacts real-time market price</p>
          </div>

          <div className="flex flex-wrap items-center gap-3 bg-white p-2 rounded-lg border shadow-sm">
            {/* Stock Selector */}
            <Select value={selectedStock} onValueChange={handleStockChange}>
              <SelectTrigger className="w-[140px] md:w-[160px] h-9">
                <SelectValue placeholder="Stock" />
              </SelectTrigger>
              <SelectContent>
                {stockOptions.map(o => <SelectItem key={o.value} value={o.value}>{o.label}</SelectItem>)}
              </SelectContent>
            </Select>

            {/* Timeframe Selector - Button Style */}
            <div className="inline-flex rounded-lg border border-slate-200 bg-slate-50 p-0.5">
              {TIMEFRAME_OPTIONS.map(option => (
                <button
                  key={option.value}
                  onClick={() => handleTimeChange(option.value)}
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
          </div>
        </div>

        {/* PRIMARY VISUALIZATION: Unified Dual-Axis Chart */}
        <Card className="shadow-sm border-slate-200">
          <CardHeader className="pb-2 border-b border-slate-50">
            <CardTitle className="text-base flex items-center gap-2">
              <Activity className="h-4 w-4 text-blue-500" />
              Price & Sentiment Timeline
            </CardTitle>
            <CardDescription>
              Blue line: Stock Price • Bars: Aggregated Sentiment ({timeRange === '1d' ? '45-min' : 'hourly'} intervals)
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4">
            <div className="h-[450px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <ComposedChart data={chartData} margin={{top:20, right:60, left:20, bottom:40}}>
                  <defs>
                    <linearGradient id="colorPrice" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLORS.price} stopOpacity={0.1}/>
                      <stop offset="95%" stopColor={COLORS.price} stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.grid} />
                  <XAxis 
                    dataKey="date" 
                    tick={{fontSize: 10, fill: '#64748b'}} 
                    minTickGap={80}
                    axisLine={false}
                    tickLine={false}
                    angle={-20}
                    textAnchor="end"
                    height={50}
                  />
                  {/* Left Y-Axis: Sentiment */}
                  <YAxis 
                    yAxisId="sentiment"
                    orientation="left" 
                    domain={[-1, 1]} 
                    tick={{fontSize: 11, fill: '#64748b'}} 
                    width={40}
                    ticks={[-1, -0.5, 0, 0.5, 1]}
                    axisLine={false}
                    tickLine={false}
                    label={{ value: 'Sentiment', angle: -90, position: 'insideLeft', style: {fontSize: 10, fill: '#64748b'} }}
                  />
                  {/* Right Y-Axis: Price */}
                  <YAxis 
                    yAxisId="price"
                    orientation="right" 
                    domain={['auto', 'auto']} 
                    tick={{fontSize: 11, fill: '#64748b'}} 
                    width={60}
                    tickFormatter={(val) => `$${val.toFixed(0)}`}
                    axisLine={false}
                    tickLine={false}
                    label={{ value: 'Price', angle: 90, position: 'insideRight', style: {fontSize: 10, fill: '#64748b'} }}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend wrapperStyle={{fontSize: '12px'}} />
                  <ReferenceLine yAxisId="sentiment" y={0} stroke={COLORS.grid} strokeDasharray="3 3" />
                  
                  {/* Sentiment Bars */}
                  <Bar 
                    yAxisId="sentiment" 
                    dataKey="sentiment" 
                    name="Avg Sentiment" 
                    barSize={timeRange === '1d' ? 8 : 12} 
                    radius={[3, 3, 0, 0]}
                  >
                    {chartData.map((entry, index) => (
                      <Cell 
                        key={`cell-${index}`} 
                        fill={entry.fill} 
                        opacity={entry.sentiment !== null ? 0.8 : 0}
                      />
                    ))}
                  </Bar>
                  
                  {/* Price Line */}
                  <Area 
                    yAxisId="price"
                    type="monotone" 
                    dataKey="price" 
                    stroke={COLORS.price} 
                    fill="url(#colorPrice)" 
                    strokeWidth={2}
                    name="Stock Price"
                    connectNulls
                  />
                </ComposedChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* SECONDARY VISUALIZATION: Daily Impact (Replaces Momentum) */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Card className="lg:col-span-2 shadow-sm border-slate-200">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <Calendar className="h-4 w-4 text-purple-500" />
                Daily Impact Analysis
              </CardTitle>
              <CardDescription>Does daily sentiment (Bar) align with daily price direction (Line)?</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="h-[300px] w-full mt-2">
                <ResponsiveContainer width="100%" height="100%">
                  <ComposedChart data={dailyImpactData}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke={COLORS.grid} />
                    <XAxis dataKey="date" tick={{fontSize: 11, fill: '#64748b'}} axisLine={false} tickLine={false} />
                    <YAxis 
                      yAxisId="left"
                      orientation="left"
                      tick={{fontSize: 11, fill: '#64748b'}}
                      tickFormatter={(val) => val.toFixed(1)}
                      label={{ value: 'Avg Sentiment', angle: -90, position: 'insideLeft', style: {fontSize: 10, fill: '#64748b'} }}
                    />
                    <YAxis 
                      yAxisId="right" 
                      orientation="right"
                      tick={{fontSize: 11, fill: '#64748b'}}
                      tickFormatter={(val) => `${val}%`}
                      label={{ value: 'Price Change %', angle: 90, position: 'insideRight', style: {fontSize: 10, fill: '#64748b'} }}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Legend iconSize={8} wrapperStyle={{fontSize: '12px'}} />
                    <ReferenceLine y={0} yAxisId="left" stroke={COLORS.grid} />
                    
                    <Bar yAxisId="left" dataKey="avgSentiment" name="Avg Sentiment" barSize={30} radius={[4, 4, 0, 0]}>
                      {dailyImpactData.map((entry, index) => (
                        <Cell key={`index-${index}`} fill={entry.avgSentiment >= 0 ? COLORS.positive : COLORS.negative} opacity={0.8} />
                      ))}
                    </Bar>
                    <Line 
                      yAxisId="right"
                      type="monotone" 
                      dataKey="priceChange" 
                      name="Price Change %"
                      stroke={COLORS.price} 
                      strokeWidth={2}
                      dot={{r: 4, fill: 'white', stroke: COLORS.price, strokeWidth: 2}}
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* Context Card */}
          <Card className="shadow-sm border-slate-200">
            <CardHeader>
              <CardTitle className="text-base">Analysis Context</CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div>
                <div className="flex justify-between mb-2">
                  <span className="text-sm text-slate-600">Event Volume</span>
                  <span className="text-sm font-bold text-slate-900">{sentimentHistory?.total_records || 0}</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2">
                  <div 
                    className="bg-blue-500 h-2 rounded-full" 
                    style={{ width: `${Math.min(100, (sentimentHistory?.total_records || 0) * 2)}%` }}
                  ></div>
                </div>
                <p className="text-xs text-slate-500 mt-2">
                  {(sentimentHistory?.total_records || 0) > 10 
                    ? "High volume ensures reliable trend detection." 
                    : "Low data volume. Trends may be volatile."}
                </p>
              </div>

              <div className="pt-4 border-t border-slate-100">
                <div className="flex items-center gap-3 mb-4">
                  <div className="p-2 bg-blue-50 rounded-lg"><Zap className="h-4 w-4 text-blue-600" /></div>
                  <div>
                    <p className="text-xs text-slate-500">Data Quality</p>
                    <p className="font-semibold text-slate-700">
                      {(sentimentHistory?.data_coverage || 0) > 0.5 ? 'Good' : 'Limited'} Coverage
                    </p>
                  </div>
                </div>
                
                <Alert className="bg-slate-50 border-slate-200 py-3">
                  <Info className="h-4 w-4 text-slate-500" />
                  <AlertDescription className="text-xs text-slate-600 ml-2">
                    Chart shows continuous pricing vs event-based sentiment. Gaps in bars indicate no news.
                  </AlertDescription>
                </Alert>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Empty State */}
        {!isLoading && !chartData.length && (
          <Alert className="border-blue-200 bg-blue-50">
            <Info className="h-4 w-4 text-blue-600" />
            <AlertDescription className="text-blue-900">
              No data available. The system is initializing or the stock has no recent activity.
            </AlertDescription>
          </Alert>
        )}
      </div>
    </UserLayout>
  );
};

export default SentimentVsPrice;