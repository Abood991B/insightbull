# Admin Dashboard - Prioritized TODO List

**Date:** October 23, 2025  
**Analysis:** Complete system review completed

---

## 🎯 PRIORITIZED ACTION PLAN

### ⭐ **PRIORITY 1: CRITICAL - Must Fix First**

#### 1. FIX: Deactivate Button Removing Stocks (2-3 hours)
**Problem:** Button calls `removeFromWatchlist()` instead of `toggleStock()`
**Impact:** Permanent data deletion instead of soft delete
**Solution:** Change `WatchlistManager.tsx` line 143 to use `adminAPI.toggleStock()`

#### 2. FIX: Prevent Orphaned Sentiment Data (3-4 hours)
**Problem:** Deleted stocks lose historical sentiment linkage
**Recommendation:** Remove "Remove" button entirely, keep only Deactivate/Activate
**Alternative:** Add safeguards in `watchlist_service.py` to prevent deletion if sentiment exists

#### 3. FIX: Active Stocks Not Syncing to User Dashboard (2-3 hours)
**Problem:** 5-minute cache shows stale stock options
**Solution:** Reduce `staleTime` to 30s and add `refetchOnWindowFocus: true` in all analysis pages

---

### ⚡ **PRIORITY 2: HIGH - Critical Functionality**

#### 4. ADD: System Health Alert Section (4-5 hours)
**Status:** Backend health check exists, needs UI component
**Create:** `SystemHealthAlerts.tsx` component
**Monitor:** Rate limits, database, pipeline status, scheduler, storage, model accuracy

#### 5. FIX: Remove ALL UTC, Use Malaysia Time Only (3-4 hours)
**Found:** 205 UTC references across 38 files
**Solution:** 
- Global replace `datetime.utcnow()` with `malaysia_now()`  
- Update all models to use `malaysia_now()` as default

#### 6. TEST & FIX: Scheduler Manager (3-4 hours)
**Test:** Create job, update job, delete job, enable/disable, manual trigger
**Add:** Job execution history table
**Add:** Cron expression validator with preview of next 5 runs

#### 7. TEST & FIX: Storage Settings (3-4 hours)
**Test:** Retention policies, manual cleanup, storage stats accuracy
**Add:** Confirmation dialogs for destructive actions
**Add:** Data export before cleanup
**Add:** Database VACUUM capability

---

### 🔧 **PRIORITY 3: MEDIUM - Enhancements**

#### 8. ENHANCE: Rate Limiter & Pipeline (5-6 hours)
**Bottleneck:** NewsAPI free tier (100 requests/day)
**Solutions:**
- Implement request batching (10 stocks per query)
- Add priority-based scheduling (high-volume stocks first)
- Implement adaptive rate limiting
- Add request queue with exponential backoff

#### 9. IMPROVE: Sentiment Models - Hybrid Approach (8-10 hours)
**Current:** Standalone VADER & FinBERT
**Enhancement:**
- Create ensemble model combining both
- Add confidence-weighted scoring
- Financial domain fine-tuning for FinBERT
- Context-aware analysis

---

### 💅 **PRIORITY 4: LOW - Polish & Alignment**

#### 10. ENHANCE: Admin Dashboard Professional UI (6-8 hours)
**Improvements:**
- Consistent color scheme
- Modern glassmorphism effects
- Better data visualizations
- Responsive design refinement
- Loading states & animations

#### 11. VERIFY: Alignment with FYP Report & Architecture (4-5 hours)
**Check:** All functional requirements implemented
**Verify:** Architecture matches documentation
**Update:** Any outdated documentation

---

## 📋 RECOMMENDED EXECUTION ORDER

### **Week 1: Critical Fixes**
**Day 1-2:**
1. Fix Deactivate Button (Priority 1.1)
2. Fix Orphaned Sentiment Data (Priority 1.2)
3. Fix User Dashboard Sync (Priority 1.3)

**Day 3-4:**
4. Add System Health Alerts (Priority 2.4)
5. Remove UTC Timezone References (Priority 2.5)

**Day 5:**
6. Test & Fix Scheduler Manager (Priority 2.6)

### **Week 2: High Priority Features**
**Day 1:**
7. Test & Fix Storage Settings (Priority 2.7)

**Day 2-3:**
8. Enhance Rate Limiter & Pipeline (Priority 3.8)

**Day 4-5:**
9. Improve Sentiment Models (Priority 3.9)

### **Week 3: Polish**
**Day 1-3:**
10. Professional UI Enhancements (Priority 4.10)

**Day 4-5:**
11. FYP Report Alignment (Priority 4.11)

---

## 🔧 QUICK FIXES (Can Do Immediately)

### Fix 1: Deactivate Button
```typescript
// src/features/admin/pages/WatchlistManager.tsx:143
// CHANGE FROM:
await adminAPI.removeFromWatchlist(stock);
// TO:
await adminAPI.toggleStock(stock);
```

### Fix 2: User Dashboard Cache
```typescript
// In all analysis pages, change:
staleTime: 5 * 60 * 1000,
// TO:
staleTime: 30 * 1000,
refetchOnWindowFocus: true,
```

### Fix 3: Timezone Quick Fix
```python
# Run this command in backend/:
grep -rl "datetime.utcnow()" app/ | xargs sed -i 's/datetime.utcnow()/malaysia_now()/g'
# Then add imports where needed
```

---

## 📊 IMPACT ASSESSMENT

| Priority | Item | Impact | Effort | ROI |
|----------|------|--------|--------|-----|
| 1 | Deactivate Button | CRITICAL | Low | ⭐⭐⭐⭐⭐ |
| 1 | Orphaned Data | CRITICAL | Medium | ⭐⭐⭐⭐⭐ |
| 1 | Dashboard Sync | CRITICAL | Low | ⭐⭐⭐⭐⭐ |
| 2 | Health Alerts | HIGH | Medium | ⭐⭐⭐⭐ |
| 2 | Timezone Fix | HIGH | Medium | ⭐⭐⭐⭐ |
| 2 | Scheduler Test | HIGH | Medium | ⭐⭐⭐⭐ |
| 2 | Storage Test | HIGH | Medium | ⭐⭐⭐⭐ |
| 3 | Rate Limiter | MEDIUM | High | ⭐⭐⭐ |
| 3 | Model Improve | MEDIUM | High | ⭐⭐⭐ |
| 4 | UI Polish | LOW | High | ⭐⭐ |
| 4 | Documentation | LOW | Medium | ⭐⭐ |

---

## ✅ SUCCESS CRITERIA

### Priority 1 Complete When:
- ✅ Deactivate button works without data loss
- ✅ Re-adding stocks preserves historical sentiment
- ✅ User dashboard updates within 30 seconds

### Priority 2 Complete When:
- ✅ Health alerts visible and actionable
- ✅ Zero UTC references in codebase
- ✅ Scheduler creates/updates/deletes jobs correctly
- ✅ Storage cleanup works with confirmations

### Priority 3 Complete When:
- ✅ Pipeline handles 50+ stocks efficiently
- ✅ Model accuracy >75% on test set

### Priority 4 Complete When:
- ✅ UI looks professional and consistent
- ✅ All FYP requirements verified

---

**NEXT STEP:** Start with Priority 1.1 (Deactivate Button Fix) - 30 minutes to implement!
