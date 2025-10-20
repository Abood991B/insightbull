# Frontend Integration Plan

## Document Overview

**Purpose**: Systematic plan for integrating the fully operational backend API with the React/TypeScript frontend  
**Status**: Backend ✅ Complete | Frontend 🔄 Integration Required | Phase 0 ✅ Complete  
**Priority**: **HIGH** - Remove all mock data and establish real backend connections  
**Primary Reference**: `FYP-Report.md` (Chapter 4: System Design, Section 4.7: Data Models)

### ✅ Phase 0 Complete (January 2025)
Empty state foundation implemented:
- 5 empty state components created (`src/shared/components/states/`)
- 6 validation utilities implemented (`src/shared/utils/dataValidation.ts`)
- Testing page available at `/test-empty-states`
- All components compile without errors
- **See**: `docs/PHASE_0_COMPLETION_REPORT.md` for full details

---

## Table of Contents

1. [Integration Strategy](#integration-strategy)
2. [Mock Data Inventory](#mock-data-inventory)
3. [Backend API Mapping](#backend-api-mapping)
4. [Phase-Based Implementation](#phase-based-implementation)
5. [Service Layer Architecture](#service-layer-architecture)
6. [Testing & Validation](#testing--validation)
7. [Success Criteria](#success-criteria)

---

## Integration Strategy

### Principles
1. **Incremental Integration**: One feature at a time, fully tested before moving forward
2. **Type Safety**: Maintain strict TypeScript typing throughout
3. **Error Handling**: Implement comprehensive error boundaries and user feedback
4. **Loading States**: Add proper loading indicators for all async operations
5. **Data Validation**: Validate all backend responses against expected schemas
6. **Reference FYP-Report.md**: Always verify data structures match Chapter 4 specifications

### Development Workflow
```powershell
# 1. Start Backend (Terminal 1)
cd backend
.\venv\Scripts\activate.bat
python main.py
# Backend: http://localhost:8000
# API Docs: http://localhost:8000/api/docs

# 2. Start Frontend (Terminal 2)
npm run dev
# Frontend: http://localhost:8080

# 3. Verify CORS Configuration
# Check: backend/app/infrastructure/config/settings.py
# allowed_origins should include http://localhost:8080
```

---

## Mock Data Inventory

### Critical Files Requiring Integration

| File | Mock Data Found | Lines | Backend Endpoint | Priority |
|------|----------------|-------|------------------|----------|
| **Dashboard** | | | | |
| `src/features/dashboard/pages/Index.tsx` | `topPositiveStocks`, `topNegativeStocks`, `watchlistStocks` | 8-94 | `/api/dashboard/summary` | **P0** |
| | | | | |
| **Analysis Pages** | | | | |
| `src/features/analysis/pages/SentimentVsPrice.tsx` | `mockData`, hardcoded `stocks` array | 9-17, 19 | `/api/analysis/stocks/{symbol}/sentiment`, `/api/stocks/` | **P0** |
| `src/features/analysis/pages/StockAnalysis.tsx` | `sentimentData`, `stockData` | 10-22 | `/api/stocks/{symbol}`, `/api/analysis/stocks/{symbol}/sentiment` | **P1** |
| `src/features/analysis/pages/CorrelationAnalysis.tsx` | `correlationData`, `stockCorrelations`, hardcoded `stocks` | 9-25, 27 | `/api/analysis/stocks/{symbol}/correlation`, `/api/stocks/` | **P1** |
| `src/features/analysis/pages/SentimentTrends.tsx` | `trendData`, hardcoded `stocks` array | 9-23, 25 | `/api/analysis/stocks/{symbol}/sentiment`, `/api/stocks/` | **P1** |
| | | | | |
| **Admin Pages** | | | | |
| `src/features/admin/pages/AdminDashboard.tsx` | Already uses `adminAPI` | ✅ | `/api/admin/*` | **P2** |
| `src/features/admin/pages/WatchlistManager.tsx` | Already uses `adminAPI` | ✅ | `/api/admin/watchlist` | **P2** |
| `src/features/admin/pages/SystemLogs.tsx` | Already uses `adminAPI` | ✅ | `/api/admin/logs` | **P2** |
| `src/features/admin/pages/StorageSettings.tsx` | Already uses `adminAPI` | ✅ | `/api/admin/storage` | **P2** |
| `src/features/admin/pages/SchedulerManager.tsx` | Already uses `adminAPI` | ✅ | `/api/admin/scheduler` | **P2** |

**Status Legend**:
- ✅ Already integrated with backend
- **P0**: Critical - Core user functionality
- **P1**: High - Key analysis features
- **P2**: Medium - Admin features (mostly complete)

---

## Backend API Mapping

### Available Backend Endpoints

#### 1. Dashboard Routes (`/api/dashboard`)
```typescript
// GET /api/dashboard/summary
interface DashboardSummary {
  market_overview: {
    total_stocks: number;
    average_sentiment: number;
    sentiment_distribution: {
      positive: number;
      neutral: number;
      negative: number;
    };
    market_trend: string;
  };
  top_stocks: Array<{
    symbol: string;
    company_name: string;
    latest_sentiment: number;
    latest_price: number | null;
    sentiment_label: 'positive' | 'neutral' | 'negative';
    price_change_24h: number | null;
  }>;
  recent_movers: Array<{
    symbol: string;
    company_name: string;
    price_change: number;
    sentiment_score: number;
  }>;
  system_status: {
    status: string;
    last_data_update: string;
    total_sentiment_records: number;
    active_stocks: number;
  };
}
```
**Reference**: FYP-Report.md Section 4.3.1 (Dashboard Visualizer) & Section 4.7.1 (Stock Entity)

#### 2. Stock Routes (`/api/stocks`)
```typescript
// GET /api/stocks/
interface StockList {
  stocks: Array<{
    symbol: string;
    company_name: string;
    sector: string;
    is_active: boolean;
    latest_sentiment: number | null;
    latest_price: number | null;
    last_updated: string;
  }>;
  total_count: number;
  active_count: number;
}

// GET /api/stocks/{symbol}
interface StockDetail {
  symbol: string;
  company_name: string;
  sector: string;
  is_active: boolean;
  metrics: {
    avg_sentiment_7d: number;
    avg_sentiment_14d: number;
    sentiment_volatility: number;
    price_correlation: number | null;
  };
  price_data: Array<{
    timestamp: string;
    open_price: number;
    close_price: number;
    high_price: number;
    low_price: number;
    volume: number;
  }>;
  sentiment_data: Array<{
    timestamp: string;
    score: number;
    label: 'positive' | 'neutral' | 'negative';
    model_used: 'finbert' | 'vader';
    source: 'reddit' | 'finnhub' | 'newsapi' | 'marketaux';
  }>;
}
```
**Reference**: FYP-Report.md Section 4.7 (Entity-Relationship Diagram - Stock, StockPrice, SentimentData)

#### 3. Analysis Routes (`/api/analysis`)
```typescript
// GET /api/analysis/stocks/{symbol}/sentiment?timeframe=7d
interface SentimentHistory {
  symbol: string;
  timeframe: string;
  data_points: Array<{
    timestamp: string;
    sentiment_score: number;
    sentiment_label: 'positive' | 'neutral' | 'negative';
    price: number | null;
    volume: number | null;
    source_count: number;
  }>;
  statistics: {
    avg_sentiment: number;
    sentiment_volatility: number;
    price_correlation: number | null;
    data_quality: number;
  };
}

// GET /api/analysis/stocks/{symbol}/correlation?timeframe=7d
interface CorrelationAnalysis {
  symbol: string;
  timeframe: string;
  pearson_correlation: number;
  r_squared: number;
  p_value: number;
  significance_level: string;
  correlation_strength: string;
  trend_direction: string;
  scatter_data: Array<{
    sentiment: number;
    price: number;
    timestamp: string;
  }>;
  time_series: Array<{
    date: string;
    sentiment: number;
    price: number;
  }>;
}
```
**Reference**: FYP-Report.md Section 2.3.4 (Model Evaluation - Pearson Correlation) & Section 4.3.2 (Correlation Calculator)

#### 4. Admin Routes (`/api/admin`)
```typescript
// Already integrated - adminAPI service exists
// Routes: health, watchlist, logs, storage, scheduler, model-accuracy, api-config
```
**Reference**: FYP-Report.md Section 4.3.4 (Admin Panel) & Chapter 5 (Security Implementation)

---

## Phase-Based Implementation

### Phase 1: Core Dashboard (Week 1) - **PRIORITY**
**Goal**: Replace mock data in main dashboard with real backend calls

**Tasks**:
1. **Create Dashboard Service** (`src/api/services/dashboard.service.ts`)
   ```typescript
   import { BaseService } from './base.service';
   import type { DashboardSummary } from '@/api/types/dashboard';

   class DashboardService extends BaseService {
     async getDashboardSummary(): Promise<DashboardSummary> {
       const response = await this.get<DashboardSummary>('/api/dashboard/summary');
       if (response.error) throw new Error(response.error);
       return response.data!;
     }
   }

   export const dashboardService = new DashboardService();
   ```

2. **Update Index.tsx** (`src/features/dashboard/pages/Index.tsx`)
   - Remove hardcoded arrays: `topPositiveStocks`, `topNegativeStocks`, `watchlistStocks`
   - Add React Query hook:
   ```typescript
   import { useQuery } from '@tanstack/react-query';
   import { dashboardService } from '@/api/services/dashboard.service';

   const { data, isLoading, error } = useQuery({
     queryKey: ['dashboard-summary'],
     queryFn: () => dashboardService.getDashboardSummary(),
     refetchInterval: 60000, // Refresh every 60 seconds
   });
   ```
   - Add loading skeleton components
   - Add error boundary with retry logic
   - **Add empty state handling** (see Empty State Patterns section):
   ```typescript
   // Handle empty data from backend (pipeline not run yet)
   if (data && data.top_stocks.length === 0) {
     return <EmptyDashboardState />;
   }
   ```
   - Map backend response to UI components

3. **Type Definitions** (`src/api/types/dashboard.ts`)
   - Define all TypeScript interfaces matching backend schemas
   - Reference FYP-Report.md Section 4.7 for data models

4. **Create Reusable Empty State Component** (`src/shared/components/EmptyState.tsx`)
   ```typescript
   import { ReactNode } from 'react';
   import { Button } from '@/shared/components/ui/button';
   import { Card } from '@/shared/components/ui/card';
   import { Link } from 'react-router-dom';

   interface EmptyStateProps {
     icon: ReactNode;
     title: string;
     description: string;
     actionLabel?: string;
     actionLink?: string;
     secondaryAction?: {
       label: string;
       link: string;
     };
   }

   export function EmptyState({ 
     icon, 
     title, 
     description, 
     actionLabel, 
     actionLink,
     secondaryAction 
   }: EmptyStateProps) {
     return (
       <Card className="max-w-2xl mx-auto mt-12">
         <div className="flex flex-col items-center justify-center py-12 px-6">
           {icon}
           <h2 className="text-2xl font-bold text-gray-900 mt-4 mb-2">
             {title}
           </h2>
           <p className="text-gray-600 text-center mb-6 max-w-md">
             {description}
           </p>
           <div className="flex gap-4">
             {actionLabel && actionLink && (
               <Button asChild>
                 <Link to={actionLink}>{actionLabel}</Link>
               </Button>
             )}
             {secondaryAction && (
               <Button variant="outline" asChild>
                 <Link to={secondaryAction.link}>
                   {secondaryAction.label}
                 </Link>
               </Button>
             )}
           </div>
         </div>
       </Card>
     );
   }
   ```

**Validation**:
- [ ] Dashboard loads without errors
- [ ] Real stock data displays (verify AAPL, MSFT, NVDA appear)
- [ ] Loading states work correctly
- [ ] Error handling displays user-friendly messages
- [ ] Data refreshes every 60 seconds
- [ ] **Empty state displays when no data in backend** ⚠️ **CRITICAL**
- [ ] Empty state provides clear instructions to run pipeline
- [ ] Links to admin panel work from empty state

---

### Phase 2: Stock List & Selection (Week 1-2)
**Goal**: Enable dynamic stock selection from backend watchlist

**Tasks**:
1. **Create Stock Service** (`src/api/services/stock.service.ts`)
   ```typescript
   class StockService extends BaseService {
     async getAllStocks(activeOnly = true): Promise<StockList> {
       return this.get<StockList>(`/api/stocks/?active_only=${activeOnly}`);
     }

     async getStockDetail(symbol: string): Promise<StockDetail> {
       return this.get<StockDetail>(`/api/stocks/${symbol}`);
     }
   }
   ```

2. **Replace Hardcoded Stock Arrays**
   - `SentimentVsPrice.tsx` line 19: Remove `const stocks = [...]`
   - `CorrelationAnalysis.tsx` line 27: Remove `const stocks = [...]`
   - `SentimentTrends.tsx` line 25: Remove `const stocks = [...]`
   - Replace with:
   ```typescript
   const { data: stockList, isLoading: isLoadingStocks } = useQuery({
     queryKey: ['stocks'],
     queryFn: () => stockService.getAllStocks(true),
   });
   
   const stocks = stockList?.stocks.map(s => s.symbol) || [];
   
   // Handle empty watchlist
   if (!isLoadingStocks && stocks.length === 0) {
     return (
       <Alert>
         <AlertCircle className="h-4 w-4" />
         <AlertTitle>No Stocks in Watchlist</AlertTitle>
         <AlertDescription>
           Add stocks to the watchlist in the admin panel to start tracking.
           <Button variant="link" asChild className="mt-2">
             <Link to="/admin/watchlist">Manage Watchlist</Link>
           </Button>
         </AlertDescription>
       </Alert>
     );
   }
   ```

3. **Update Stock Selectors**
   - All `<Select>` components for stock selection should use real data
   - Add loading state to dropdown:
   ```typescript
   <Select 
     value={selectedStock} 
     onValueChange={setSelectedStock}
     disabled={isLoadingStocks || stocks.length === 0}
   >
     <SelectTrigger className="w-48">
       <SelectValue placeholder={
         isLoadingStocks ? "Loading stocks..." : "Select stock"
       } />
     </SelectTrigger>
     <SelectContent>
       {stocks.map((stock) => (
         <SelectItem key={stock} value={stock}>
           {stock}
         </SelectItem>
       ))}
     </SelectContent>
   </Select>
   ```
   - Validate FYP-Report.md Section 4.7.1 for stock entity structure

**Validation**:
- [ ] Stock dropdowns populate from backend
- [ ] Only active watchlist stocks appear
- [ ] Stock selection triggers data fetch
- [ ] Dropdown shows loading state while fetching
- [ ] **Empty watchlist displays alert with admin panel link** ⚠️
- [ ] Dropdown is disabled when no stocks available
- [ ] "Loading stocks..." placeholder appears during fetch

---

### Phase 3: Sentiment vs Price Analysis (Week 2)
**Goal**: Connect sentiment analysis visualizations to backend

**Tasks**:
1. **Create Analysis Service** (`src/api/services/analysis.service.ts`)
   ```typescript
   class AnalysisService extends BaseService {
     async getSentimentHistory(
       symbol: string, 
       timeframe: '1d' | '7d' | '14d'
     ): Promise<SentimentHistory> {
       return this.get<SentimentHistory>(
         `/api/analysis/stocks/${symbol}/sentiment?timeframe=${timeframe}`
       );
     }

     async getCorrelationAnalysis(
       symbol: string, 
       timeframe: '1d' | '7d' | '14d'
     ): Promise<CorrelationAnalysis> {
       return this.get<CorrelationAnalysis>(
         `/api/analysis/stocks/${symbol}/correlation?timeframe=${timeframe}`
       );
     }
   }
   ```

2. **Update SentimentVsPrice.tsx**
   - Remove `mockData` array (line 9-17)
   - Implement dual-axis chart with real data:
   ```typescript
   const { data: sentimentData, isLoading } = useQuery({
     queryKey: ['sentiment-history', selectedStock, timeRange],
     queryFn: () => analysisService.getSentimentHistory(selectedStock, timeRange),
     enabled: !!selectedStock,
   });

   const chartData = sentimentData?.data_points.map(point => ({
     date: new Date(point.timestamp).toLocaleDateString(),
     sentiment: point.sentiment_score,
     price: point.price,
     volume: point.volume,
   })) || [];
   ```

3. **Add Data Quality Indicators**
   - Display `data_quality` percentage from backend
   - Show data source counts
   - Reference FYP-Report.md Section 2.4 (Data Sources)

4. **Implement Empty/Partial Data Handling** ⚠️ **CRITICAL**
   ```typescript
   // No data at all (pipeline not run)
   if (!isLoading && sentimentData?.data_points.length === 0) {
     return <EmptyChartState 
       stockSymbol={selectedStock}
       message="No sentiment data collected yet"
     />;
   }

   // Insufficient data for meaningful analysis
   if (!isLoading && sentimentData?.data_points.length < 5) {
     return (
       <>
         <Alert variant="warning" className="mb-4">
           <Clock className="h-4 w-4" />
           <AlertTitle>Limited Data Available</AlertTitle>
           <AlertDescription>
             Only {sentimentData.data_points.length} data points available.
             Try a shorter time range or wait for more data collection.
           </AlertDescription>
         </Alert>
         {/* Still render chart with available data */}
         <ChartComponent data={chartData} />
       </>
     );
   }
   ```

**Validation**:
- [ ] Charts render with real backend data
- [ ] Time range selection (1d, 7d, 14d) works
- [ ] Dual-axis displays sentiment + price correctly
- [ ] **Empty state shows when no data available** ⚠️
- [ ] **Partial data warning displays when < 5 data points** ⚠️
- [ ] Correlation coefficient displays correctly
- [ ] Data quality indicator shows percentage
- [ ] Empty state links to admin panel for data collection

---

### Phase 4: Correlation Analysis (Week 2-3)
**Goal**: Implement statistical correlation features

**Tasks**:
1. **Update CorrelationAnalysis.tsx**
   - Remove `correlationData` and `stockCorrelations` (lines 9-25)
   - Fetch correlation analysis from backend
   - Display Pearson correlation, R-squared, p-value
   - Show scatter plot with real data
   - Reference FYP-Report.md Section 4.3.2 (Correlation Calculator)

2. **Implement Correlation Metrics Display**
   ```typescript
   const { data: correlation, isLoading } = useQuery({
     queryKey: ['correlation', selectedStock, timeRange],
     queryFn: () => analysisService.getCorrelationAnalysis(selectedStock, timeRange),
     enabled: !!selectedStock,
   });

   // Handle insufficient data for correlation
   if (!isLoading && correlation?.scatter_data.length < 10) {
     return (
       <Alert variant="warning">
         <TrendingUp className="h-4 w-4" />
         <AlertTitle>Insufficient Data for Correlation</AlertTitle>
         <AlertDescription>
           At least 10 data points are needed for meaningful correlation analysis.
           Currently have {correlation?.scatter_data.length || 0} points.
           Please wait for more data collection or try a longer time range.
         </AlertDescription>
       </Alert>
     );
   }

   // Display metrics
   <Card>
     <CardTitle>Pearson Correlation</CardTitle>
     <div>{correlation?.pearson_correlation.toFixed(3)}</div>
     <Badge>{correlation?.correlation_strength}</Badge>
   </Card>
   ```

3. **Add Statistical Significance Indicators**
   - Show p-value and significance level
   - Color-code based on correlation strength
   - Add tooltips explaining metrics
   - Display warning if p-value > 0.05 (not statistically significant)

**Validation**:
- [ ] Pearson correlation calculated correctly
- [ ] R-squared value displays
- [ ] Scatter plot shows sentiment vs price relationship
- [ ] Statistical significance indicators work
- [ ] Multiple stocks can be compared
- [ ] **Warning displays for insufficient data (< 10 points)** ⚠️
- [ ] **P-value significance threshold shown** ⚠️
- [ ] Empty state appears when no correlation data available

---

### Phase 5: Sentiment Trends (Week 3)
**Goal**: Display time-series sentiment trends

**Tasks**:
1. **Update SentimentTrends.tsx**
   - Remove `trendData` array (lines 9-23)
   - Fetch sentiment history
   - Display multi-day trends
   - Show sentiment distribution breakdown
   - **Handle empty trend data**:
   ```typescript
   const { data: trendData, isLoading } = useQuery({
     queryKey: ['sentiment-trends', selectedStock, timeRange],
     queryFn: () => analysisService.getSentimentHistory(selectedStock, timeRange),
     enabled: !!selectedStock,
   });

   // No trend data available
   if (!isLoading && (!trendData || trendData.data_points.length === 0)) {
     return (
       <EmptyState
         icon={<TrendingUp className="w-12 h-12 text-gray-400" />}
         title="No Sentiment Trends Available"
         description={`No sentiment data collected for ${selectedStock} in the selected timeframe. Run the data collection pipeline to populate trends.`}
         actionLabel="Run Data Collection"
         actionLink="/admin/dashboard"
       />
     );
   }
   ```

2. **Add Trend Analysis**
   - Moving averages
   - Sentiment momentum indicators
   - Model breakdown (FinBERT vs VADER)
   - Reference FYP-Report.md Section 2.3.3-2.3.4 (Model Selection)
   - **Show data completeness indicator**:
   ```typescript
   <Badge variant={trendData.statistics.data_quality > 80 ? "success" : "warning"}>
     {trendData.statistics.data_quality.toFixed(0)}% Data Coverage
   </Badge>
   ```

**Validation**:
- [ ] Trend charts display correctly
- [ ] Sentiment distribution pie chart works
- [ ] Model breakdown shows FinBERT/VADER split
- [ ] Time range filtering functions properly
- [ ] **Empty state shows for stocks with no sentiment data** ⚠️
- [ ] **Data completeness badge displays** ⚠️
- [ ] Partial data warning for low coverage (< 50%)

---

### Phase 6: Stock Analysis Details (Week 3-4)
**Goal**: Complete detailed stock analysis page

**Tasks**:
1. **Update StockAnalysis.tsx**
   - Remove `sentimentData` and `stockData` (lines 10-22)
   - Fetch stock detail from backend
   - Display comprehensive metrics
   - Show historical data tables
   - **Implement empty/partial data states**:
   ```typescript
   const { data: stockDetail, isLoading } = useQuery({
     queryKey: ['stock-detail', selectedStock],
     queryFn: () => stockService.getStockDetail(selectedStock),
     enabled: !!selectedStock,
   });

   // No sentiment data but stock exists
   if (stockDetail && stockDetail.sentiment_data.length === 0) {
     return (
       <div>
         <StockHeader stock={stockDetail} />
         <Alert className="mt-4">
           <Database className="h-4 w-4" />
           <AlertTitle>No Sentiment Data Yet</AlertTitle>
           <AlertDescription>
             {stockDetail.company_name} is in the watchlist but no sentiment 
             data has been collected. Run the pipeline to start analysis.
             <Button variant="link" asChild className="mt-2">
               <Link to="/admin/dashboard">Run Pipeline</Link>
             </Button>
           </AlertDescription>
         </Alert>
       </div>
     );
   }

   // No price data
   if (stockDetail && stockDetail.price_data.length === 0) {
     return (
       <Alert variant="warning">
         <AlertTitle>Limited Price Data</AlertTitle>
         <AlertDescription>
           Price data is not available for this stock. 
           Sentiment analysis will be shown without price correlation.
         </AlertDescription>
       </Alert>
     );
   }
   ```

2. **Add Advanced Features**
   - Export data functionality
   - Comparison with market average
   - News/Reddit source breakdown
   - Reference FYP-Report.md Section 2.4 (Data Sources)
   - **Data source availability indicators**:
   ```typescript
   // Show which sources have data
   <div className="flex gap-2">
     {sources.map(source => (
       <Badge 
         key={source} 
         variant={hasData(source) ? "default" : "outline"}
       >
         {source}: {getCount(source)} records
       </Badge>
     ))}
   </div>
   ```

**Validation**:
- [ ] Stock details load correctly
- [ ] Historical data displays in table
- [ ] Charts render with real data
- [ ] Source breakdown shows Reddit/News distribution
- [ ] **Empty sentiment data shows appropriate message** ⚠️
- [ ] **Missing price data handled gracefully** ⚠️
- [ ] **Data source indicators show availability** ⚠️
- [ ] Export works even with partial data

---

### Phase 7: Admin Panel Verification (Week 4)
**Goal**: Verify all admin features work with backend

**Tasks**:
1. **Test Existing Admin Integrations**
   - Dashboard status (already uses `adminAPI`)
   - Watchlist management (already integrated)
   - System logs (already integrated)
   - Storage settings (already integrated)
   - Scheduler (already integrated)

2. **Add Missing Features**
   - Model accuracy display (if not fully integrated)
   - API configuration testing
   - Data collection triggers

**Validation**:
- [ ] All admin pages connect to backend
- [ ] OAuth2 + TOTP authentication works
- [ ] System status reflects real backend state
- [ ] Manual data collection trigger works
- [ ] Reference FYP-Report.md Chapter 5 (Security)

---

## Service Layer Architecture

### File Structure
```
src/api/
├── services/
│   ├── base.service.ts          ✅ Exists - HTTP client foundation
│   ├── admin.service.ts         ✅ Exists - Admin operations
│   ├── dashboard.service.ts     ❌ CREATE - Dashboard data
│   ├── stock.service.ts         ❌ CREATE - Stock information
│   ├── analysis.service.ts      ❌ CREATE - Sentiment analysis
│   └── index.ts                 ❌ CREATE - Barrel exports
├── types/
│   ├── dashboard.ts             ❌ CREATE - Dashboard interfaces
│   ├── stock.ts                 ❌ CREATE - Stock interfaces
│   ├── analysis.ts              ❌ CREATE - Analysis interfaces
│   └── index.ts                 ❌ CREATE - Barrel exports
└── hooks/
    ├── useDashboard.ts          ❌ CREATE - Dashboard queries
    ├── useStocks.ts             ❌ CREATE - Stock queries
    ├── useAnalysis.ts           ❌ CREATE - Analysis queries
    └── index.ts                 ❌ CREATE - Barrel exports
```

### Service Pattern Template
```typescript
// src/api/services/[feature].service.ts
import { BaseService } from './base.service';
import type { /* Types */ } from '@/api/types/[feature]';

class FeatureService extends BaseService {
  private readonly basePath = '/api/[feature]';

  async getResource(id: string): Promise<ResourceType> {
    const response = await this.get<ResourceType>(`${this.basePath}/${id}`);
    if (response.error) {
      throw new Error(response.error);
    }
    return response.data!;
  }

  // Additional methods...
}

export const featureService = new FeatureService();
export type { /* Export types */ };
```

### React Query Hook Pattern
```typescript
// src/api/hooks/use[Feature].ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { featureService } from '../services/feature.service';

export function useFeature(id: string) {
  return useQuery({
    queryKey: ['feature', id],
    queryFn: () => featureService.getResource(id),
    staleTime: 60000, // 1 minute
    retry: 3,
  });
}

export function useFeatureMutation() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: featureService.updateResource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['feature'] });
    },
  });
}
```

---

## Data Validation & Empty States

### Critical: Pre-Pipeline State Handling

**IMPORTANT**: Your backend database is currently empty (pipeline not run yet). Every page MUST handle this gracefully.

### Empty State Decision Tree

```
User Opens Page
    ↓
Backend API Call
    ↓
Response Received
    ↓
┌──────────────────────────────────────┐
│ Check 1: Backend Connection          │
│ - Error 500/503? → Server Error Page │
│ - Network Error? → Connection Lost   │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ Check 2: Watchlist Status             │
│ - stockList.length === 0?             │
│ → "Add Stocks to Watchlist" State    │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ Check 3: Data Availability            │
│ - data_points.length === 0?           │
│ → "Run Pipeline First" State         │
└──────────────┬───────────────────────┘
               ↓
┌──────────────────────────────────────┐
│ Check 4: Data Sufficiency             │
│ - data_points.length < 5?             │
│ → Partial Data Warning (still render)│
└──────────────┬───────────────────────┘
               ↓
          Render Normal UI
```

### Empty State Component Library

Create these reusable components in `src/shared/components/states/`:

#### 1. `EmptyPipelineState.tsx` - **Most Critical**
```typescript
import { PlayCircle, Database } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { Card } from '@/shared/components/ui/card';
import { Link } from 'react-router-dom';

export function EmptyPipelineState() {
  return (
    <Card className="max-w-2xl mx-auto mt-12 p-8">
      <div className="text-center">
        <Database className="w-20 h-20 text-blue-500 mx-auto mb-4" />
        <h2 className="text-2xl font-bold mb-3">
          No Data Collected Yet
        </h2>
        <p className="text-gray-600 mb-6 max-w-md mx-auto">
          The sentiment analysis pipeline hasn't run yet. 
          Start data collection to populate the dashboard with 
          real-time sentiment analysis from Reddit, FinHub, NewsAPI, and Marketaux.
        </p>
        <div className="flex justify-center gap-4">
          <Button asChild size="lg">
            <Link to="/admin/dashboard">
              <PlayCircle className="mr-2 h-4 w-4" />
              Run Data Collection
            </Link>
          </Button>
          <Button variant="outline" asChild size="lg">
            <Link to="/about">Learn More</Link>
          </Button>
        </div>
        <div className="mt-6 p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-800">
            <strong>Admin Access Required:</strong> Data collection 
            requires OAuth2 + TOTP authentication.
          </p>
        </div>
      </div>
    </Card>
  );
}
```

#### 2. `EmptyWatchlistState.tsx`
```typescript
import { ListPlus } from 'lucide-react';
import { Button } from '@/shared/components/ui/button';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';
import { Link } from 'react-router-dom';

export function EmptyWatchlistState() {
  return (
    <Alert className="max-w-2xl mx-auto">
      <ListPlus className="h-5 w-5" />
      <AlertTitle className="text-lg">No Stocks in Watchlist</AlertTitle>
      <AlertDescription className="mt-2">
        Add stocks to the watchlist to start tracking sentiment. 
        The dashboard supports Top 20 IXT Technology stocks including 
        AAPL, MSFT, NVDA, GOOGL, AMZN, META, TSLA, and more.
        <div className="mt-4">
          <Button asChild>
            <Link to="/admin/watchlist">
              <ListPlus className="mr-2 h-4 w-4" />
              Manage Watchlist
            </Link>
          </Button>
        </div>
      </AlertDescription>
    </Alert>
  );
}
```

#### 3. `PartialDataWarning.tsx`
```typescript
import { Clock, TrendingUp } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';
import { Progress } from '@/shared/components/ui/progress';

interface Props {
  dataPoints: number;
  minRequired: number;
  dataQuality?: number;
}

export function PartialDataWarning({ dataPoints, minRequired, dataQuality }: Props) {
  const percentage = (dataPoints / minRequired) * 100;
  
  return (
    <Alert variant="warning" className="mb-4">
      <Clock className="h-4 w-4" />
      <AlertTitle>Limited Data Available</AlertTitle>
      <AlertDescription>
        <div className="space-y-2">
          <p>
            Only {dataPoints} of {minRequired} recommended data points available.
            Results may be less accurate with limited data.
          </p>
          <Progress value={percentage} className="h-2" />
          {dataQuality && (
            <p className="text-xs">
              Data Coverage: {dataQuality.toFixed(0)}%
            </p>
          )}
          <p className="text-xs mt-2">
            💡 Tip: Try a shorter time range or wait for the next pipeline run.
          </p>
        </div>
      </AlertDescription>
    </Alert>
  );
}
```

#### 4. `InsufficientCorrelationData.tsx`
```typescript
import { TrendingUp } from 'lucide-react';
import { Alert, AlertTitle, AlertDescription } from '@/shared/components/ui/alert';

interface Props {
  currentPoints: number;
  requiredPoints: number;
}

export function InsufficientCorrelationData({ currentPoints, requiredPoints }: Props) {
  return (
    <Alert variant="destructive">
      <TrendingUp className="h-4 w-4" />
      <AlertTitle>Insufficient Data for Correlation Analysis</AlertTitle>
      <AlertDescription>
        At least {requiredPoints} data points are needed for meaningful 
        statistical correlation. Currently have {currentPoints} points.
        <ul className="mt-2 ml-4 list-disc text-sm">
          <li>Wait for more pipeline runs to collect data</li>
          <li>Try selecting a longer time range (14d instead of 1d)</li>
          <li>Ensure the stock is in the active watchlist</li>
        </ul>
      </AlertDescription>
    </Alert>
  );
}
```

### Data Validation Helper Functions

Create `src/shared/utils/dataValidation.ts`:

```typescript
/**
 * Data Validation Utilities
 * Handle empty states and insufficient data scenarios
 */

export interface DataValidationResult {
  isValid: boolean;
  isEmpty: boolean;
  isPartial: boolean;
  message?: string;
  severity: 'error' | 'warning' | 'info';
}

/**
 * Validate dashboard data
 */
export function validateDashboardData(data: any): DataValidationResult {
  if (!data) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No data received from backend',
      severity: 'error'
    };
  }

  if (data.top_stocks?.length === 0 && data.system_status?.total_sentiment_records === 0) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'Pipeline has not run yet. No sentiment data collected.',
      severity: 'info'
    };
  }

  return {
    isValid: true,
    isEmpty: false,
    isPartial: false,
    severity: 'info'
  };
}

/**
 * Validate sentiment analysis data
 */
export function validateSentimentData(
  data: any,
  minPoints: number = 5
): DataValidationResult {
  if (!data || !data.data_points) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No sentiment data available',
      severity: 'error'
    };
  }

  const pointCount = data.data_points.length;

  if (pointCount === 0) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No data points collected for this stock/timeframe',
      severity: 'info'
    };
  }

  if (pointCount < minPoints) {
    return {
      isValid: true,
      isEmpty: false,
      isPartial: true,
      message: `Only ${pointCount} data points available. At least ${minPoints} recommended.`,
      severity: 'warning'
    };
  }

  return {
    isValid: true,
    isEmpty: false,
    isPartial: false,
    severity: 'info'
  };
}

/**
 * Validate correlation analysis data
 */
export function validateCorrelationData(
  data: any,
  minPoints: number = 10
): DataValidationResult {
  if (!data || !data.scatter_data) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No correlation data available',
      severity: 'error'
    };
  }

  const pointCount = data.scatter_data.length;

  if (pointCount < minPoints) {
    return {
      isValid: false,
      isEmpty: pointCount === 0,
      isPartial: pointCount > 0,
      message: `Need ${minPoints} data points for correlation. Currently have ${pointCount}.`,
      severity: pointCount === 0 ? 'error' : 'warning'
    };
  }

  // Check p-value significance
  if (data.p_value > 0.05) {
    return {
      isValid: true,
      isEmpty: false,
      isPartial: true,
      message: 'Correlation is not statistically significant (p > 0.05)',
      severity: 'warning'
    };
  }

  return {
    isValid: true,
    isEmpty: false,
    isPartial: false,
    severity: 'info'
  };
}

/**
 * Validate stock list
 */
export function validateStockList(stocks: any[]): DataValidationResult {
  if (!stocks || stocks.length === 0) {
    return {
      isValid: false,
      isEmpty: true,
      isPartial: false,
      message: 'No stocks in watchlist',
      severity: 'info'
    };
  }

  const activeStocks = stocks.filter(s => s.is_active);
  if (activeStocks.length === 0) {
    return {
      isValid: false,
      isEmpty: false,
      isPartial: true,
      message: 'No active stocks in watchlist',
      severity: 'warning'
    };
  }

  return {
    isValid: true,
    isEmpty: false,
    isPartial: false,
    severity: 'info'
  };
}
```

### Usage Example in Components

```typescript
// In any analysis page
import { validateSentimentData } from '@/shared/utils/dataValidation';
import { EmptyPipelineState } from '@/shared/components/states/EmptyPipelineState';
import { PartialDataWarning } from '@/shared/components/states/PartialDataWarning';

function SentimentVsPrice() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['sentiment', symbol, timeframe],
    queryFn: () => analysisService.getSentimentHistory(symbol, timeframe)
  });

  // Validate data
  const validation = validateSentimentData(data, 5);

  // Handle empty state
  if (!isLoading && validation.isEmpty) {
    return <EmptyPipelineState />;
  }

  // Handle partial data
  if (!isLoading && validation.isPartial) {
    return (
      <>
        <PartialDataWarning 
          dataPoints={data.data_points.length}
          minRequired={5}
          dataQuality={data.statistics?.data_quality}
        />
        {/* Still render chart with available data */}
        <ChartComponent data={data.data_points} />
      </>
    );
  }

  // Render normal UI
  return <FullAnalysisView data={data} />;
}
```

## Testing & Validation

### Pre-Integration Testing (Database Empty)

**CRITICAL**: Test all empty states BEFORE running the pipeline:

```powershell
# 1. Start backend with empty database
cd backend
python main.py

# 2. Start frontend
npm run dev

# 3. Test each page systematically
```

**Empty State Testing Checklist**:
- [ ] Dashboard shows "No Data Collected Yet" state
- [ ] All analysis pages show pipeline prompt
- [ ] Stock dropdowns show empty watchlist message
- [ ] Admin panel accessible (OAuth2 working)
- [ ] No JavaScript errors in console
- [ ] All "Run Pipeline" buttons link to `/admin/dashboard`
- [ ] "Manage Watchlist" buttons link to `/admin/watchlist`
- [ ] Empty states are visually appealing (not error-like)

### Manual Testing Checklist

#### 1. Dashboard Testing
- [ ] Navigate to `/` - dashboard loads
- [ ] Verify stock symbols match FYP Report (AAPL, MSFT, NVDA, etc.)
- [ ] Check sentiment scores are between 0-1
- [ ] Confirm prices are realistic (not mock values like 150, 155, etc.)
- [ ] Wait 60 seconds - verify auto-refresh works
- [ ] Disconnect backend - verify error handling

#### 2. Analysis Testing
- [ ] Select different stocks - data changes
- [ ] Change time range (1d, 7d, 14d) - data updates
- [ ] Verify correlation values between -1 and 1
- [ ] Check scatter plot has real data points
- [ ] Compare with backend `/api/docs` - responses match

#### 3. Integration Testing
- [ ] Test with backend running on `localhost:8000`
- [ ] Verify CORS allows frontend on port 8080
- [ ] Check browser console - no 404 or 500 errors
- [ ] Network tab - verify requests to `/api/*`
- [ ] Test on different browsers (Chrome, Firefox, Edge)

#### 4. Data Validation
- [ ] Verify data structures match FYP-Report.md Section 4.7
- [ ] Check sentiment labels: 'positive', 'neutral', 'negative'
- [ ] Confirm model types: 'finbert' or 'vader'
- [ ] Validate timestamp formats (ISO 8601)
- [ ] Ensure prices are positive numbers

### Automated Testing Strategy

#### Unit Tests (React Testing Library)
```typescript
// Example: Dashboard.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Index } from './Index';

test('displays real stock data from backend', async () => {
  const queryClient = new QueryClient();
  render(
    <QueryClientProvider client={queryClient}>
      <Index />
    </QueryClientProvider>
  );

  await waitFor(() => {
    expect(screen.getByText(/NVDA/i)).toBeInTheDocument();
  });
});
```

#### Integration Tests
```typescript
// Test backend connectivity
describe('Backend Integration', () => {
  test('dashboard service fetches real data', async () => {
    const data = await dashboardService.getDashboardSummary();
    expect(data.market_overview.total_stocks).toBeGreaterThan(0);
    expect(data.top_stocks).toHaveLength(10);
  });
});
```

---

## Success Criteria

### Phase Completion Checklist
- [ ] **Phase 1**: Dashboard displays real backend data
- [ ] **Phase 2**: Stock selection uses dynamic watchlist
- [ ] **Phase 3**: Sentiment vs Price charts work with backend
- [ ] **Phase 4**: Correlation analysis shows real statistics
- [ ] **Phase 5**: Sentiment trends display correctly
- [ ] **Phase 6**: Stock analysis page fully integrated
- [ ] **Phase 7**: Admin panel verified operational

### Final Validation
- [ ] Zero hardcoded mock data arrays remain in `src/features/`
- [ ] All API calls use services extending `BaseService`
- [ ] TypeScript types match backend schemas
- [ ] Error handling implemented on all pages
- [ ] Loading states display during async operations
- [ ] Data refreshes automatically (where appropriate)
- [ ] CORS configuration allows frontend-backend communication
- [ ] All features reference FYP-Report.md specifications

### Performance Benchmarks
- [ ] Dashboard loads in < 2 seconds
- [ ] Chart rendering in < 1 second
- [ ] API responses in < 500ms (local development)
- [ ] No memory leaks with React Query
- [ ] Proper cleanup on component unmount

---

## Quick Reference Commands

### Development
```powershell
# Backend
cd backend
.\venv\Scripts\activate.bat
python main.py

# Frontend
npm run dev

# Both terminals side-by-side
# Backend: http://localhost:8000/api/docs
# Frontend: http://localhost:8080
```

### Debugging
```powershell
# Check backend logs
cd backend/logs

# Test specific endpoint
curl http://localhost:8000/api/dashboard/summary

# Check CORS configuration
# backend/app/infrastructure/config/settings.py
```

### Testing
```powershell
# Backend tests
cd backend
pytest tests/test_01_security_auth.py

# Frontend tests (when implemented)
npm test
```

---

## Notes & Considerations

### Data Synchronization
- Backend collects data via scheduled pipeline (APScheduler)
- Frontend should poll for updates (60-second intervals)
- Consider WebSocket for real-time updates (future enhancement)

### Error Scenarios
- **Backend down**: Show cached data with warning banner
- **API rate limits**: Display retry countdown
- **Invalid stock symbol**: Show user-friendly error
- **No data available**: Display empty state with explanation (see Empty State Patterns below)
- **Pipeline not run yet**: Show onboarding message with instructions to run data collection

### Empty State Patterns

When backend returns empty data (before pipeline execution), implement these UI patterns:

#### Pattern 1: Empty Dashboard State
```typescript
// src/features/dashboard/pages/Index.tsx
if (data && data.top_stocks.length === 0) {
  return (
    <EmptyState
      icon={<Database className="w-16 h-16 text-gray-400" />}
      title="No Data Available Yet"
      description="The sentiment analysis pipeline hasn't collected data yet. Run the data collection to populate the dashboard."
      actionLabel="Go to Admin Panel"
      actionLink="/admin/dashboard"
      secondaryAction={{
        label: "Learn More",
        link: "/about"
      }}
    />
  );
}
```

#### Pattern 2: Empty Chart State
```typescript
// For charts with no data
if (!data || data.data_points.length === 0) {
  return (
    <Card>
      <CardContent className="flex flex-col items-center justify-center py-12">
        <BarChart3 className="w-12 h-12 text-gray-400 mb-4" />
        <h3 className="text-lg font-semibold text-gray-700 mb-2">
          No Sentiment Data Available
        </h3>
        <p className="text-sm text-gray-500 text-center max-w-md mb-4">
          No sentiment data has been collected for {selectedStock} yet.
          The data collection pipeline needs to be run first.
        </p>
        <Button variant="outline" asChild>
          <Link to="/admin/dashboard">Run Data Collection</Link>
        </Button>
      </CardContent>
    </Card>
  );
}
```

#### Pattern 3: Empty Stock List
```typescript
// When watchlist exists but no stocks tracked
if (stockList && stockList.stocks.length === 0) {
  return (
    <Alert>
      <AlertCircle className="h-4 w-4" />
      <AlertTitle>No Stocks in Watchlist</AlertTitle>
      <AlertDescription>
        Add stocks to the watchlist in the admin panel to start tracking sentiment.
        <Button variant="link" asChild className="mt-2">
          <Link to="/admin/watchlist">Manage Watchlist</Link>
        </Button>
      </AlertDescription>
    </Alert>
  );
}
```

#### Pattern 4: Partial Data State
```typescript
// When some data exists but not for selected timeframe
if (data && data.data_points.length < 5) {
  return (
    <Alert variant="warning" className="mb-4">
      <Clock className="h-4 w-4" />
      <AlertTitle>Limited Data Available</AlertTitle>
      <AlertDescription>
        Only {data.data_points.length} data points available for this timeframe.
        More data will be collected as the pipeline runs.
        Try selecting a shorter time range or check back later.
      </AlertDescription>
    </Alert>
  );
}
```

### FYP-Report.md Cross-References
- **Chapter 1**: Project overview and objectives
- **Chapter 2**: Literature review on sentiment analysis models
- **Section 2.3.3-2.3.4**: FinBERT + VADER model justification
- **Section 2.4**: Data sources (Reddit, FinHub, NewsAPI, Marketaux)
- **Chapter 3**: Requirements analysis (U-FR1 to U-FR10)
- **Chapter 4**: System design (layered architecture)
- **Section 4.3**: Component specifications
- **Section 4.7**: Entity-Relationship Diagram (data models)
- **Chapter 5**: Security implementation (OAuth2 + TOTP)
- **Chapter 7**: Implementation & testing plan

---

## Contact & Support

**Issues**: Check backend logs in `backend/logs/`  
**API Documentation**: http://localhost:8000/api/docs  
**Primary Reference**: `FYP-Report.md` (6055 lines)  
**Architecture Details**: `docs/BACKEND_REFERENCE.md`  
**Security Setup**: `docs/SECURITY_IMPLEMENTATION.md`

---

---

## Pipeline Onboarding Flow

### First-Time User Experience (No Data State)

When a user first accesses the dashboard with an empty database, provide a clear onboarding flow:

#### Step 1: Dashboard Landing (Empty State)
```
┌────────────────────────────────────────────────────────┐
│  🗄️  No Data Available Yet                             │
│                                                         │
│  The sentiment analysis pipeline hasn't collected      │
│  data yet. Get started in 3 easy steps:                │
│                                                         │
│  1. ✅ Add stocks to watchlist (Admin)                 │
│  2. ▶️  Run data collection pipeline                   │
│  3. 📊 View sentiment analysis results                 │
│                                                         │
│  [Run Data Collection]  [Learn More]                   │
│                                                         │
│  ℹ️  Admin Access Required: OAuth2 + TOTP              │
└────────────────────────────────────────────────────────┘
```

#### Step 2: Admin Dashboard (Pipeline Trigger)
- Clear "Trigger Data Collection" button
- Show estimated collection time (5-10 minutes)
- Display progress indicator during collection
- Show real-time log updates

#### Step 3: Data Population
- Toast notification when pipeline completes
- Automatic dashboard refresh
- Show "Data Updated" timestamp

### Admin Panel Integration for Empty States

All empty states should link to relevant admin sections:

| Empty State | Action Link | Admin Feature |
|-------------|-------------|---------------|
| No watchlist stocks | `/admin/watchlist` | Add stocks to track |
| No pipeline data | `/admin/dashboard` | Trigger data collection |
| API key errors | `/admin/api-config` | Configure API credentials |
| Pipeline failures | `/admin/logs` | View system logs |

### Progressive Data Loading

Handle gradual data population as pipeline runs:

```typescript
// Show progress during initial data collection
interface PipelineProgress {
  status: 'idle' | 'running' | 'completed' | 'failed';
  progress: number; // 0-100
  current_source: 'reddit' | 'finnhub' | 'newsapi' | 'marketaux' | null;
  stocks_processed: number;
  total_stocks: number;
  estimated_completion: string;
}

// Display in UI
{pipelineStatus?.status === 'running' && (
  <Alert variant="info">
    <Loader2 className="h-4 w-4 animate-spin" />
    <AlertTitle>Collecting Data ({pipelineStatus.progress}%)</AlertTitle>
    <AlertDescription>
      Processing {pipelineStatus.current_source}... 
      ({pipelineStatus.stocks_processed}/{pipelineStatus.total_stocks} stocks)
      <Progress value={pipelineStatus.progress} className="mt-2" />
    </AlertDescription>
  </Alert>
)}
```

### Data Quality Indicators

After pipeline runs, show data quality metrics:

```typescript
<Card>
  <CardHeader>
    <CardTitle className="flex items-center gap-2">
      Data Quality Status
      <Badge variant={dataQuality > 80 ? 'success' : 'warning'}>
        {dataQuality}%
      </Badge>
    </CardTitle>
  </CardHeader>
  <CardContent>
    <div className="space-y-2">
      <MetricRow 
        label="Sentiment Records" 
        value={sentimentRecords}
        status={sentimentRecords > 0 ? 'success' : 'warning'}
      />
      <MetricRow 
        label="Price Data Points" 
        value={priceRecords}
        status={priceRecords > 0 ? 'success' : 'warning'}
      />
      <MetricRow 
        label="Last Collection" 
        value={lastUpdate}
        status={isRecent(lastUpdate) ? 'success' : 'warning'}
      />
      <MetricRow 
        label="Active Sources" 
        value={`${activeSources}/4`}
        status={activeSources === 4 ? 'success' : 'warning'}
      />
    </div>
    {dataQuality < 80 && (
      <Button variant="outline" size="sm" className="mt-4 w-full">
        <PlayCircle className="mr-2 h-4 w-4" />
        Run Collection Again
      </Button>
    )}
  </CardContent>
</Card>
```

---

## Quick Start Checklist (For Empty Database)

Use this checklist when starting integration with an empty backend database:

### Phase 0: Pre-Integration Setup ⚠️ **DO FIRST**

- [ ] **Backend Setup**
  - [ ] Backend running on `http://localhost:8000`
  - [ ] Database initialized (Alembic migrations applied)
  - [ ] API docs accessible at `/api/docs`
  - [ ] Database is empty (no pipeline run yet) ✅ **Expected State**

- [ ] **Frontend Setup**
  - [ ] Frontend running on `http://localhost:8080`
  - [ ] CORS configured in backend settings
  - [ ] Environment variables set (`VITE_API_URL`)
  - [ ] React Query DevTools enabled (optional)

- [ ] **Empty State Components Created**
  - [ ] `EmptyPipelineState.tsx`
  - [ ] `EmptyWatchlistState.tsx`
  - [ ] `PartialDataWarning.tsx`
  - [ ] `InsufficientCorrelationData.tsx`
  - [ ] `dataValidation.ts` utility functions

### Phase 0.5: Test Empty States (1 day)

**Before integrating any data, test all empty states:**

- [ ] Dashboard shows empty pipeline state
- [ ] Analysis pages show "Run Pipeline First" message
- [ ] Stock dropdowns handle empty watchlist
- [ ] Correlation page shows insufficient data message
- [ ] All links to admin panel work
- [ ] No console errors with empty backend responses

### Phase 1-7: Integration with Empty State Handling

Each phase now includes:
- ✅ Normal data rendering
- ⚠️ Empty state handling
- ⚠️ Partial data warnings
- ✅ Loading states
- ✅ Error boundaries

### Post-Integration: Pipeline Testing

**After all phases complete, test with data:**

- [ ] Run pipeline from admin panel
- [ ] Verify data appears in dashboard
- [ ] Check all charts populate correctly
- [ ] Confirm auto-refresh works
- [ ] Test with different time ranges
- [ ] Verify correlation calculations
- [ ] Check data quality indicators

---

**Last Updated**: October 17, 2025  
**Version**: 1.1  
**Status**: Ready for Implementation (Empty Database Focus Added)  
**Critical Addition**: Comprehensive empty state handling for pre-pipeline database state
