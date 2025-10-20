# Empty State Handling Guide

## Critical Context

**Your backend database is currently EMPTY** - the data collection pipeline has not been run yet. This means:
- ❌ No sentiment data in database
- ❌ No stock price history
- ❌ No Reddit posts or news articles
- ❌ No correlation calculations possible
- ✅ Backend API is running and functional
- ✅ Database schema is ready

**Every frontend page MUST handle this gracefully.**

---

## Quick Decision Tree

```
Is backend responding?
├─ NO  → ConnectionErrorState
└─ YES → Is watchlist empty?
         ├─ YES → EmptyWatchlistState
         └─ NO  → Does data exist?
                  ├─ NO  → EmptyPipelineState
                  └─ YES → Is data sufficient?
                           ├─ NO  → PartialDataWarning
                           └─ YES → Render normal UI
```

---

## Empty State Components (Create These First!)

### Location: `src/shared/components/states/`

### 1. EmptyPipelineState.tsx ⭐ **MOST IMPORTANT**
**When to use**: Backend responds but has no sentiment data  
**Where**: Dashboard, all analysis pages on first load

```typescript
import { Database, PlayCircle } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { Card } from '@/shared/components/ui/card';
import { Link } from 'react-router-dom';

export function EmptyPipelineState() {
  return (
    <Card className="max-w-2xl mx-auto mt-12 p-8 text-center">
      <Database className="w-20 h-20 text-blue-500 mx-auto mb-4" />
      <h2 className="text-2xl font-bold mb-3">No Data Collected Yet</h2>
      <p className="text-gray-600 mb-6 max-w-md mx-auto">
        The sentiment analysis pipeline hasn't run yet. 
        Start data collection to populate the dashboard.
      </p>
      <Button asChild size="lg">
        <Link to="/admin/dashboard">
          <PlayCircle className="mr-2 h-4 w-4" />
          Run Data Collection
        </Link>
      </Button>
    </Card>
  );
}
```

**Usage in any page**:
```typescript
if (!isLoading && data?.data_points.length === 0) {
  return <EmptyPipelineState />;
}
```

---

### 2. EmptyWatchlistState.tsx
**When to use**: Watchlist has no stocks  
**Where**: Analysis pages when stock dropdown is empty

```typescript
import { ListPlus } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';
import { Button } from '@/shared/components/ui/button';
import { Link } from 'react-router-dom';

export function EmptyWatchlistState() {
  return (
    <Alert className="max-w-2xl mx-auto">
      <ListPlus className="h-5 w-5" />
      <AlertTitle className="text-lg">No Stocks in Watchlist</AlertTitle>
      <AlertDescription>
        Add stocks to track sentiment. Supports AAPL, MSFT, NVDA, and more.
        <Button asChild className="mt-4">
          <Link to="/admin/watchlist">Manage Watchlist</Link>
        </Button>
      </AlertDescription>
    </Alert>
  );
}
```

---

### 3. PartialDataWarning.tsx
**When to use**: Some data exists but insufficient for full analysis  
**Where**: Charts with < 5-10 data points

```typescript
import { Clock } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';
import { Progress } from '@/shared/components/ui/progress';

interface Props {
  dataPoints: number;
  minRequired: number;
  dataQuality?: number;
}

export function PartialDataWarning({ dataPoints, minRequired, dataQuality }: Props) {
  return (
    <Alert variant="warning" className="mb-4">
      <Clock className="h-4 w-4" />
      <AlertTitle>Limited Data Available</AlertTitle>
      <AlertDescription>
        Only {dataPoints} of {minRequired} recommended points.
        <Progress value={(dataPoints / minRequired) * 100} className="mt-2" />
        <p className="text-xs mt-2">
          💡 Try a shorter time range or wait for next pipeline run.
        </p>
      </AlertDescription>
    </Alert>
  );
}
```

---

### 4. InsufficientCorrelationData.tsx
**When to use**: Not enough points for correlation (< 10)  
**Where**: Correlation analysis page specifically

```typescript
import { TrendingUp } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';

interface Props {
  currentPoints: number;
}

export function InsufficientCorrelationData({ currentPoints }: Props) {
  return (
    <Alert variant="destructive">
      <TrendingUp className="h-4 w-4" />
      <AlertTitle>Insufficient Data for Correlation</AlertTitle>
      <AlertDescription>
        Need at least 10 data points. Currently have {currentPoints}.
        <ul className="mt-2 ml-4 list-disc text-sm">
          <li>Wait for more pipeline runs</li>
          <li>Try a longer time range (14d)</li>
          <li>Ensure stock is in active watchlist</li>
        </ul>
      </AlertDescription>
    </Alert>
  );
}
```

---

## Data Validation Utility

### Location: `src/shared/utils/dataValidation.ts`

```typescript
export function validateSentimentData(data: any, minPoints: number = 5) {
  if (!data || !data.data_points) {
    return { isValid: false, isEmpty: true, message: 'No data available' };
  }

  if (data.data_points.length === 0) {
    return { isValid: false, isEmpty: true, message: 'Pipeline not run' };
  }

  if (data.data_points.length < minPoints) {
    return { 
      isValid: true, 
      isPartial: true, 
      message: `Only ${data.data_points.length} points` 
    };
  }

  return { isValid: true, isEmpty: false, isPartial: false };
}

export function validateCorrelationData(data: any, minPoints: number = 10) {
  if (!data?.scatter_data || data.scatter_data.length < minPoints) {
    return {
      isValid: false,
      currentPoints: data?.scatter_data?.length || 0,
      minRequired: minPoints
    };
  }
  return { isValid: true };
}
```

---

## Implementation Pattern for Every Page

### Standard Pattern (Copy-Paste Template)

```typescript
import { useQuery } from '@tanstack/react-query';
import { EmptyPipelineState } from '@/shared/components/states/EmptyPipelineState';
import { PartialDataWarning } from '@/shared/components/states/PartialDataWarning';
import { validateSentimentData } from '@/shared/utils/dataValidation';

function MyAnalysisPage() {
  // 1. Fetch data
  const { data, isLoading, error } = useQuery({
    queryKey: ['sentiment', selectedStock, timeRange],
    queryFn: () => analysisService.getSentimentHistory(selectedStock, timeRange),
    enabled: !!selectedStock
  });

  // 2. Handle loading
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  // 3. Handle errors
  if (error) {
    return <ErrorState error={error} />;
  }

  // 4. Validate data
  const validation = validateSentimentData(data, 5);

  // 5. Handle empty state (CRITICAL!)
  if (validation.isEmpty) {
    return <EmptyPipelineState />;
  }

  // 6. Handle partial data
  if (validation.isPartial) {
    return (
      <>
        <PartialDataWarning 
          dataPoints={data.data_points.length}
          minRequired={5}
        />
        {/* Still render chart with available data */}
        <ChartComponent data={data.data_points} />
      </>
    );
  }

  // 7. Render normal UI
  return <FullAnalysisView data={data} />;
}
```

---

## Page-Specific Implementations

### Dashboard (Index.tsx)

```typescript
const { data } = useQuery({
  queryKey: ['dashboard-summary'],
  queryFn: () => dashboardService.getDashboardSummary()
});

// Empty check
if (data && data.top_stocks.length === 0) {
  return <EmptyPipelineState />;
}

// Render normally
return (
  <div>
    <TopStocksGrid stocks={data.top_stocks} />
    <MarketOverview overview={data.market_overview} />
  </div>
);
```

### SentimentVsPrice.tsx

```typescript
const { data: sentimentData } = useQuery({
  queryKey: ['sentiment', symbol, timeframe],
  queryFn: () => analysisService.getSentimentHistory(symbol, timeframe)
});

// Empty pipeline
if (!sentimentData || sentimentData.data_points.length === 0) {
  return <EmptyPipelineState />;
}

// Partial data
if (sentimentData.data_points.length < 5) {
  return (
    <>
      <PartialDataWarning 
        dataPoints={sentimentData.data_points.length}
        minRequired={5}
      />
      <LineChart data={sentimentData.data_points} />
    </>
  );
}

// Normal render
return <DualAxisChart data={sentimentData} />;
```

### CorrelationAnalysis.tsx

```typescript
const { data: correlation } = useQuery({
  queryKey: ['correlation', symbol, timeframe],
  queryFn: () => analysisService.getCorrelationAnalysis(symbol, timeframe)
});

// Validate correlation-specific requirements
const validation = validateCorrelationData(correlation, 10);

if (!validation.isValid) {
  return (
    <InsufficientCorrelationData 
      currentPoints={validation.currentPoints}
    />
  );
}

// Render correlation analysis
return <CorrelationView data={correlation} />;
```

---

## Testing Checklist (Empty Database)

Before running pipeline, verify:

- [ ] Dashboard shows `EmptyPipelineState`
- [ ] No JavaScript errors in console
- [ ] "Run Data Collection" button links to `/admin/dashboard`
- [ ] All analysis pages show empty state
- [ ] Stock dropdowns handle empty watchlist
- [ ] No 404 errors from API calls
- [ ] Loading states work correctly
- [ ] Error boundaries catch unexpected issues

---

## Admin Panel Flow for Data Collection

1. User sees empty state
2. Clicks "Run Data Collection" → `/admin/dashboard`
3. Admin authenticates (OAuth2 + TOTP)
4. Clicks "Trigger Data Collection"
5. Pipeline runs (5-10 minutes)
6. Frontend auto-refreshes
7. Data appears in dashboard

---

## Common Mistakes to Avoid

❌ **DON'T**: Assume backend always has data  
✅ **DO**: Check for empty arrays/null values

❌ **DON'T**: Show error messages for empty data  
✅ **DO**: Show informative empty states

❌ **DON'T**: Disable features when data is missing  
✅ **DO**: Guide users to run pipeline

❌ **DON'T**: Render charts with empty data  
✅ **DO**: Show empty state component

---

## Quick Reference

| Scenario | Component | Action Link |
|----------|-----------|-------------|
| No sentiment data | `EmptyPipelineState` | `/admin/dashboard` |
| No watchlist stocks | `EmptyWatchlistState` | `/admin/watchlist` |
| < 5 data points | `PartialDataWarning` | Show data anyway |
| < 10 points (correlation) | `InsufficientCorrelationData` | Don't render |
| Backend error | `ErrorBoundary` | Retry button |

---

## Priority Order

1. **Create empty state components** (1 hour)
2. **Create validation utilities** (30 min)
3. **Update Dashboard page** (1 hour) - Most visible
4. **Update all analysis pages** (2-3 hours)
5. **Test with empty backend** (1 hour)
6. **Run pipeline and test with data** (Final validation)

---

**Remember**: The backend works perfectly, but the database is empty. Every page needs to handle this gracefully before the pipeline runs for the first time!
