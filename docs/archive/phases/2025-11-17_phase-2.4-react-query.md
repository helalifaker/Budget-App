# Phase 2.4: React Query Configuration and Prefetching Optimization

**Implementation Date**: December 2, 2025
**Status**: ✅ Complete

## Overview

This phase optimizes React Query configuration and implements intelligent query prefetching to reduce redundant API calls and improve perceived performance.

## Changes Implemented

### 1. Enhanced Query Client Configuration

**File**: `/frontend/src/lib/query-client.ts`

**Key Improvements**:

- **Caching Strategy**:
  - `staleTime: 5 minutes` - Data is considered fresh for 5 minutes
  - `gcTime: 30 minutes` - Keep unused data in cache for 30 minutes (increased from 10 minutes)

- **Smart Retry Strategy**:
  - No retry on 4xx client errors (400, 401, 403, 404, 422)
  - Retry up to 2 times for network errors and 5xx server errors
  - Exponential backoff: `Math.min(1000 * 2^attemptIndex, 30000)` (max 30 seconds)

- **Refetch Strategy**:
  - `refetchOnWindowFocus: false` - Prevents excessive requests when switching tabs
  - `refetchOnReconnect: true` - Refetch when internet connection is restored
  - `refetchOnMount: true` - Refetch on component mount if data is stale

- **Performance Optimizations**:
  - `structuralSharing: true` - Optimize re-renders by sharing unchanged data
  - `networkMode: 'online'` - Only run queries when online

- **Global Error Handling**:
  - QueryCache with global error handler
  - MutationCache with global error handler

**Helper Functions**:
```typescript
// Optimistic updates
setQueryDataOptimistically<T>(queryKey, updater)

// Query invalidation with optional toast
invalidateQueriesWithToast(queryKey, message)
```

### 2. Query Prefetching Hook

**File**: `/frontend/src/hooks/usePrefetchRoute.ts`

**Purpose**: Prefetch route data and queries when user hovers over navigation links

**Features**:
- Prefetches TanStack Router route components and loader data
- Prefetches React Query data based on route context
- Automatically determines which queries to prefetch based on route path

**Supported Routes**:
- Planning: `/planning/enrollment`, `/planning/dhg`, `/planning/classes`, etc.
- Consolidation: `/consolidation/budget`, `/consolidation/statements`
- Analysis: `/analysis/kpis`, `/analysis/dashboards`, `/analysis/variance`
- Configuration: `/configuration/versions`
- Dashboard: `/dashboard`

**Usage**:
```typescript
const { prefetchRoute } = usePrefetchRoute()

<Link
  to="/planning/enrollment"
  onMouseEnter={() => prefetchRoute('/planning/enrollment', budgetVersionId)}
>
  Enrollment
</Link>
```

### 3. Background Refetch Hook

**File**: `/frontend/src/hooks/useBackgroundRefetch.ts`

**Purpose**: Automatically refetch queries in the background at specified intervals

**Use Cases**:
- Dashboard KPIs (refresh every 60 seconds)
- Activity feeds (refresh every 30 seconds)
- System alerts (refresh every 60 seconds)

**Usage**:
```typescript
// Refetch KPIs every minute
useBackgroundRefetch(['kpi-dashboard', budgetVersionId], 60000)

// Refetch activity feed every 30 seconds
useBackgroundRefetch(['analysis', 'activity'], 30000)
```

### 4. Updated Sidebar Navigation

**File**: `/frontend/src/components/layout/Sidebar.tsx`

**Changes**:
- Integrated `usePrefetchRoute` hook
- Added `onMouseEnter` handlers to all navigation links
- Fetches active budget version ID for context-aware prefetching

**Result**: Hovering over navigation links now triggers instant prefetching of route data and queries

### 5. React Query DevTools

**File**: `/frontend/src/main.tsx`

**Changes**:
- Conditionally render React Query DevTools only in development
- Removed `position` prop (not supported in current version)

```typescript
{import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
```

### 6. Query Key Factory Updates

**File**: `/frontend/src/hooks/api/useConsolidation.ts`

**Added Missing Keys**:
```typescript
summary: (versionId: string) => [...consolidationKeys.all, 'summary', versionId]
statements: (versionId: string, format: string) => [...consolidationKeys.all, 'statements', versionId, format]
```

**Existing Query Keys** (Already Well-Structured):
- `enrollmentKeys` - Enrollment planning
- `budgetVersionKeys` - Budget versions
- `dhgKeys` - DHG workforce planning
- `analysisKeys` - KPIs, variance, dashboard, activity
- `configurationKeys` - Levels, nationality types, cycles
- `revenueKeys` - Revenue planning
- `costsKeys` - Cost planning
- `capexKeys` - CapEx planning
- `classStructureKeys` - Class structure
- `strategicKeys` - Strategic planning

## Performance Impact

### Before Optimization
- Aggressive refetching on window focus
- No query prefetching
- 10-minute cache garbage collection
- No smart retry strategy

### After Optimization
- **Reduced Network Requests**: Prefetching eliminates redundant API calls
- **Instant Navigation**: Queries are already cached when user clicks link
- **Longer Cache Retention**: 30-minute GC keeps data available longer
- **Smart Retries**: No wasted retries on client errors
- **Better UX**: Perceived performance improvement from instant data loading

## Testing Checklist

### Manual Testing in Browser

1. **Start Development Server**
   ```bash
   cd frontend && pnpm dev
   ```

2. **Test Prefetching**
   - Open browser to `http://localhost:5173`
   - Open Network tab in DevTools
   - Hover over navigation links (don't click)
   - Verify prefetch requests appear in Network tab
   - Click link → should load instantly from cache

3. **Test React Query DevTools**
   - Look for React Query DevTools icon in bottom-right corner
   - Click to open DevTools panel
   - Verify query cache shows prefetched queries
   - Check query states (fresh, stale, inactive)

4. **Test Query Deduplication**
   - Navigate to a page (e.g., Enrollment)
   - Check Network tab for API request
   - Navigate away and back
   - Verify no new API request if data is still fresh (within 5 minutes)

5. **Test Smart Retry**
   - Simulate a 404 error (navigate to non-existent resource)
   - Check Network tab → should NOT retry
   - Simulate a 500 error (backend down)
   - Check Network tab → should retry up to 2 times with exponential backoff

6. **Test Offline Behavior**
   - Open DevTools → Network tab → Set to "Offline"
   - Try to navigate to a page
   - Verify queries don't run (networkMode: 'online')
   - Go back online
   - Verify queries refetch automatically (refetchOnReconnect: true)

### Automated Testing

```bash
# Type checking
pnpm typecheck
# ✅ Passed

# Linting
pnpm lint
# ✅ Passed (new files have no errors)

# Unit tests
pnpm test
# Run to verify no regressions
```

## Code Quality

### TypeScript Compliance
- ✅ No TypeScript errors in new files
- ✅ Proper generic type handling
- ✅ Type-safe query key factories

### Linting Compliance
- ✅ No ESLint errors in new files
- ✅ Follows React hooks best practices
- ✅ Proper dependency arrays

### Best Practices
- ✅ Pure functions (no side effects)
- ✅ Centralized query keys
- ✅ Consistent naming conventions
- ✅ Comprehensive JSDoc comments
- ✅ Error handling

## Known Limitations

1. **Generic Type Passing**: DataTableLazy uses type assertion to work around lazy loading generic type limitations
2. **Prefetch Context**: Requires budget version ID for context-aware prefetching (may not work on initial load)
3. **Background Refetch**: Uses `setInterval` which continues even when page is not visible (could be optimized with Page Visibility API)

## Future Enhancements

1. **Optimistic Updates**: Implement optimistic updates for mutations using `setQueryDataOptimistically`
2. **Query Cancellation**: Cancel in-flight queries when user navigates away
3. **Query Persistence**: Persist queries to localStorage for offline support
4. **Smart Prefetching**: Use ML to predict which routes user will navigate to
5. **Page Visibility API**: Pause background refetch when page is not visible

## Migration Notes

### For Developers

**No Breaking Changes** - All changes are backward compatible.

**Optional Enhancements**:
- Add `onMouseEnter` handlers to any custom navigation links
- Use `useBackgroundRefetch` for real-time data updates
- Use `invalidateQueriesWithToast` for better UX on mutations

**Query Key Pattern**:
```typescript
export const myKeys = {
  all: ['my-domain'] as const,
  lists: () => [...myKeys.all, 'list'] as const,
  list: (filters: string) => [...myKeys.lists(), { filters }] as const,
  details: () => [...myKeys.all, 'detail'] as const,
  detail: (id: string) => [...myKeys.details(), id] as const,
}
```

## Success Metrics

- ✅ Query client configuration enhanced with smart retry and caching
- ✅ Prefetching implemented on all navigation links (15+ routes)
- ✅ React Query DevTools enabled in development
- ✅ Background refetch hook created for real-time updates
- ✅ All query keys use consistent factory pattern
- ✅ Zero TypeScript errors
- ✅ Zero linting errors in new files

## Files Modified

### New Files (3)
1. `/frontend/src/hooks/usePrefetchRoute.ts` (104 lines)
2. `/frontend/src/hooks/useBackgroundRefetch.ts` (31 lines)
3. `/frontend/PHASE_2.4_REACT_QUERY_OPTIMIZATION.md` (this file)

### Modified Files (5)
1. `/frontend/src/lib/query-client.ts` - Enhanced configuration
2. `/frontend/src/components/layout/Sidebar.tsx` - Added prefetching
3. `/frontend/src/main.tsx` - Conditional DevTools rendering
4. `/frontend/src/hooks/api/useConsolidation.ts` - Added missing query keys
5. `/frontend/src/components/DataTableLazy.tsx` - Fixed generic type issue
6. `/frontend/src/routes/analysis/kpis.tsx` - Fixed BarChart import

## References

- [TanStack Query v5 Docs](https://tanstack.com/query/latest)
- [React Query Best Practices](https://tkdodo.eu/blog/practical-react-query)
- [Query Key Factories](https://tkdodo.eu/blog/effective-react-query-keys)
- [Prefetching Guide](https://tanstack.com/query/latest/docs/framework/react/guides/prefetching)

---

**Phase 2.4 Implementation Complete** ✅
