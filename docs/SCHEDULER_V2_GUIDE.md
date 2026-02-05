# Smart Scheduler V2 - Implementation Guide

## Overview

The new Scheduler Manager V2 replaces the old cron-based scheduler with an intelligent, market-aware preset scheduling system that aligns with the project requirements.

## Key Improvements

### 1. **Human-Readable Schedules** ✅
**Problem Solved:** Users don't understand cron expressions like `*/15 14-20 * * 1-5`

**New Approach:** Clear, business-focused descriptions
- ❌ Old: `*/15 14-20 * * 1-5`
- ✅ New: "Every 30 minutes during market hours (9:30 AM - 4:00 PM ET, Mon-Fri)"

### 2. **Atomic Pipeline Execution** ✅
**Problem Solved:** Separate "Data Collection" and "Sentiment Analysis" jobs don't make sense

**New Approach:** ALL schedules run the FULL pipeline
- Data Collection (4 collectors: NewsAPI, FinHub, Reddit, MarketAux)
- → Sentiment Analysis (FinBERT + VADER)
- → Storage (Database with deduplication)

**Why Atomic?**
- Prevents orphaned raw data without sentiment
- Ensures sentiment analysis uses FRESH data
- Simplifies user mental model
- Aligns with Section 4.7 of the project specification (Data Flow)

### 3. **Smart Preset Schedules** ✅

Four market-aware presets replace arbitrary scheduling:

#### **A. Pre-Market Preparation**
- **Schedule:** Daily at 8:00 AM ET (Mon-Fri)
- **Rationale:** Collect overnight news BEFORE market opens at 9:30 AM
- **Use Case:** Traders get fresh insights for market open

#### **B. Active Trading Updates**
- **Schedule:** Every 30 minutes (9:30 AM - 4:00 PM ET, Mon-Fri)
- **Rationale:** Monitor real-time sentiment during active trading
- **Use Case:** Catch breaking news and social media reactions

#### **C. After-Hours Analysis**
- **Schedule:** 5:00 PM & 8:00 PM ET (Mon-Fri)
- **Rationale:** Capture post-market earnings reports and news
- **Use Case:** After-hours trading sentiment

#### **D. Weekend Deep Analysis**
- **Schedule:** Saturday 10:00 AM ET
- **Rationale:** Weekly comprehensive analysis, prepare for Monday
- **Use Case:** Digest weekend news before market reopens

### 4. **Visual Timeline** ✅
**Problem Solved:** Users don't know when jobs will run

**New Feature:** "Upcoming Pipeline Runs (Next 48 Hours)"
- Shows next 10-15 scheduled runs
- Color-coded by market context (pre-market, active, after-hours, weekend)
- Real-time countdown to next execution
- Clear time zone display (ET = Eastern Time)

### 5. **Collector Health Monitoring** ✅
**Problem Solved:** MarketAux API failing silently (402 Payment Required)

**New Feature:** "Data Collector Health" dashboard
- Real-time status of all 4 collectors
- Shows success: NewsAPI (45 articles), FinHub (32), Reddit (18 posts)
- Shows failure: MarketAux (402 Payment Required - Subscription expired)
- Clear warning when collectors are down
- Graceful degradation (pipeline continues with 3/4 collectors)

**From Logs Analysis:**
```
Error collecting MarketAux news: 402 Payment Required
(All stocks: AAPL, MSFT, GOOGL, AMZN, META, AMD, TSLA, NVDA, MU, AVGO)
```

### 6. **Market Context Awareness** ✅
**New Feature:** Real-time market status badge
- Shows: "Market Open" (green), "Pre-Market" (amber), "After Hours" (orange), "Weekend" (blue), "Market Closed" (gray)
- Displays next market open time when closed
- Icon-based visual indicators (Sun, Sunrise, Sunset, Moon)

## Technical Architecture

### Frontend (`SchedulerManagerV2.tsx`)
**Location:** `src/features/admin/pages/SchedulerManagerV2.tsx`

**Key Components:**
1. **Preset Schedule Configurations** (lines 70-130)
   - 4 preset schedules with rationale
   - Cron expressions hidden from users
   - Market context tags

2. **Collector Health Status** (lines 495-545)
   - Real-time API health monitoring
   - Graceful failure display
   - Last run timestamps

3. **Timeline Visualization** (lines 550-600)
   - Next 48 hours of scheduled runs
   - Color-coded by market period
   - Chronological ordering

4. **Job Operations** (lines 340-385)
   - Enable/Disable presets
   - "Run Now" button for immediate execution
   - Operation loading states

### Backend Integration
**Endpoints Used:**
- `GET /api/admin/scheduler/jobs` - List scheduled jobs
- `PUT /api/admin/scheduler/jobs/{job_id}?action=enable|disable|cancel` - Job operations
- `POST /api/admin/data-collection/manual` - Trigger immediate pipeline run

**Note:** Backend already supports these operations (verified in `backend/app/presentation/routes/admin.py`)

## Migration from Old to New

### Step 1: Test V2 Alongside Old Version ✅ DONE
- New component: `SchedulerManagerV2.tsx`
- Old component: `SchedulerManager.tsx` (kept for reference)
- Route updated: `/admin/scheduler` now uses V2

### Step 2: Verify Against Project Requirements ✅
**Alignment Check:**
- ✅ Section 3.2.15 (UC-15: Scheduled Data Collection) - Implemented
- ✅ Section 4.3 (Business Layer: Scheduler) - Preserved
- ✅ Section 4.7 (Data Flow: Sequential pipeline) - Atomic execution
- ✅ Section 7.3 (Testing: Rate limit handling) - Monitored in UI

### Step 3: Remove Old Implementation (Future)
Once V2 is tested and approved:
1. Delete `src/features/admin/pages/SchedulerManager.tsx`
2. Update imports to remove old component
3. Update documentation references

## User Guide

### For Administrators

**Enabling a Preset Schedule:**
1. Navigate to Admin → Scheduler
2. Find desired preset card (e.g., "Active Trading Updates")
3. Click "Enable" button
4. Verify "Active" badge appears
5. Check "Upcoming Pipeline Runs" for next execution

**Running Pipeline Immediately:**
1. Click "Run Now" on any preset card
2. Toast notification confirms pipeline started
3. Check "Data Collector Health" for results
4. View logs in Admin → System Logs

**Monitoring Collector Health:**
1. Check "Data Collector Health" section
2. Green checkmarks = working
3. Red X = failed (see error message)
4. If MarketAux shows 402: Either upgrade subscription or ignore (3/4 collectors still work)

**Understanding Timeline:**
- Amber dots = Pre-market (before 9:30 AM)
- Green dots = Market hours (9:30 AM - 4:00 PM)
- Orange dots = After-hours (4:00 PM - 8:00 PM)
- Blue dots = Weekend

## Troubleshooting

### Issue: "Job not found" errors in logs
**From Logs:**
```
Failed to cancel job datacoll_826a0d5f - job not found
Failed to cancel job datacoll_dfec3efb - job not found
```

**Cause:** Job IDs regenerate on backend restart, old IDs become stale

**Solution V2:** UI shows current jobs only, no manual ID entry needed

### Issue: MarketAux 402 Payment Required
**From Logs:**
```
Error collecting MarketAux news: 402 Payment Required
```

**Impact:** 25% data loss (1 of 4 collectors down)

**Solution:**
- **Option A:** Upgrade MarketAux subscription
- **Option B:** Disable MarketAux collector in backend
- **Option C:** Accept 3/4 collectors (still functional)

**V2 Handling:** Shows clear warning, pipeline continues gracefully

### Issue: No scheduled runs appearing
**Possible Causes:**
1. Scheduler not started (check "Scheduler Status" = "Running")
2. No presets enabled (enable at least one)
3. Backend jobs not created (check backend logs)

**Solution:**
1. Restart backend: `python main.py`
2. Enable desired presets in V2 UI
3. Click "Refresh" button

## Technical Notes

### Cron Expression Translation
Old cron → New preset mapping:

| Old Cron | New Preset | Frequency |
|----------|------------|-----------|
| `*/15 14-20 * * 1-5` | Active Trading | Every 30 min (market hours) |
| `0 */2 * * *` | After-Hours | 5 PM & 8 PM daily |
| `0 9-16 * * 1-5` | (Removed) | Merged into Active Trading |
| `0 2 * * 0` | Weekend Deep | Saturday 10 AM |
| `0 13 * * 1-5` | Pre-Market | 8 AM daily (NEW) |

**Why Changes?**
- More user-friendly frequencies
- Better aligned with market activity patterns
- Reduced API rate limit stress (was 15 min, now 30 min during market)

### Rate Limit Considerations
**API Limits (from project specification):**
- NewsAPI: 100 requests/day
- FinHub: 60 requests/minute
- Reddit: 60 requests/minute  
- MarketAux: Currently down (402)

**V2 Frequency Impact:**
- Pre-Market: 1 run/day = 4 requests (1 per collector)
- Active Trading: ~14 runs/day (30 min intervals × 6.5 hrs) = 56 requests
- After-Hours: 2 runs/day = 8 requests
- Weekend: 1 run/week = 4 requests

**Total:** ~68 requests/day per collector (well within limits)

## Future Enhancements

### Phase 2 (Post-V2 Testing)
1. **Custom Schedule Builder**
   - Allow admins to create custom presets
   - Drag-and-drop timeline editor
   - Save custom presets to database

2. **Collector Configuration**
   - Enable/disable specific collectors per preset
   - Configure lookback days per preset
   - Per-collector rate limit settings

3. **Advanced Timeline Features**
   - Job execution history graph
   - Success/failure rate statistics
   - Estimated next run duration

4. **Smart Rate Limiting**
   - Auto-adjust frequency based on API usage
   - Predictive rate limit warnings
   - Collector rotation strategies

## Files Modified

### New Files
- `src/features/admin/pages/SchedulerManagerV2.tsx` (new implementation)
- `docs/SCHEDULER_V2_GUIDE.md` (this file)

### Updated Files
- `src/App.tsx` (routing to V2)
- `src/features/admin/index.ts` (export V2)

### Preserved Files (for reference)
- `src/features/admin/pages/SchedulerManager.tsx` (old implementation)

## Alignment with Project Requirements

### Section 3.2.15 - Use Case UC-15: Scheduled Data Collection ✅
> "The system schedules data collection tasks to run at regular intervals"

**V2 Implementation:** 4 preset schedules with clear intervals

### Section 4.3 - Business Layer: Scheduler Component ✅
> "Scheduler component coordinates with DataCollector and Pipeline"

**V2 Implementation:** All presets trigger full pipeline (atomic execution)

### Section 4.7 - Data Flow Diagram ✅
> "Sequential flow: Data Collection → Text Processing → Sentiment Analysis → Storage"

**V2 Implementation:** Enforced via `job_type: 'full_pipeline'`

### Section 7.3 - Testing: Rate Limit Handling ✅
> "Manages API requests to ensure compliance with rate limits"

**V2 Implementation:** Collector health monitoring + graceful failure display

## Conclusion

Scheduler Manager V2 provides a **significantly improved user experience** by:
1. Eliminating confusing cron expressions
2. Providing market-aware intelligent presets
3. Visualizing upcoming pipeline runs
4. Monitoring collector health in real-time
5. Maintaining atomic pipeline execution for data consistency

The implementation aligns with project specifications while addressing real-world issues identified in production logs (MarketAux failures, job ID staleness).

**Status:** ✅ Ready for testing
**Next Step:** Test all 4 presets with real backend, verify collector health monitoring
