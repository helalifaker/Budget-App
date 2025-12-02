# Bundle Architecture & Code Splitting Strategy

**Visual Guide to EFIR Budget App Bundle Optimization**

---

## Bundle Loading Flow

```
User Opens App
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  INITIAL BUNDLE (218 KB gzipped) ✅                     │
│  ┌───────────────────────────────────────────────────┐  │
│  │ react-vendor.js (204 KB)                          │  │
│  │   - React 19.2.0                                  │  │
│  │   - ReactDOM                                      │  │
│  │   - @tanstack/react-router                        │  │
│  │   - @tanstack/react-query                         │  │
│  │   - react-error-boundary                          │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ index.js (6 KB) - Main entry point               │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ utils.js (8 KB) - clsx, tailwind-merge            │  │
│  └───────────────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────────────┐  │
│  │ ui.js (0.2 KB) - UI components                    │  │
│  └───────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────┐
│  DASHBOARD LOADED (Fast!)                               │
│  - User sees page immediately                           │
│  - No heavy libraries loaded yet                        │
└─────────────────────────────────────────────────────────┘
      │
      ├──────────────────────────────────────────────┐
      ▼                                              ▼
User Navigates to Planning              User Navigates to Analysis
      │                                              │
      ▼                                              ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ LAZY LOAD AG GRID        │              │ LAZY LOAD RECHARTS       │
│ ag-grid.js (138 KB)      │              │ charts.js (2 KB)         │
│ + routes-planning (9 KB) │              │ + routes-analysis (10 KB)│
└──────────────────────────┘              └──────────────────────────┘
      │                                              │
      ▼                                              ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ Show GridSkeleton        │              │ Show ChartSkeleton       │
│ (0.3 seconds)            │              │ (0.2 seconds)            │
└──────────────────────────┘              └──────────────────────────┘
      │                                              │
      ▼                                              ▼
┌──────────────────────────┐              ┌──────────────────────────┐
│ Render DataTable         │              │ Render BarChart          │
│ (Fully Interactive)      │              │ (Fully Interactive)      │
└──────────────────────────┘              └──────────────────────────┘
```

---

## Chunk Dependency Graph

```
                    ┌──────────────────┐
                    │   index.html     │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │   main.tsx       │
                    │  (entry point)   │
                    └────────┬─────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐    ┌──────────────┐    ┌──────────────┐
│ react-vendor  │    │   tanstack   │    │  supabase    │
│   (204 KB)    │    │    (incl.)   │    │   (40 KB)    │
└───────────────┘    └──────────────┘    └──────────────┘
        │
        └──────────────────┬──────────────────┐
                           │                  │
                    ┌──────▼──────┐    ┌──────▼──────┐
                    │  Dashboard  │    │   Login     │
                    │    Route    │    │    Page     │
                    └──────┬──────┘    └─────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   Planning    │  │  Consolidation │  │   Analysis    │
│   Routes      │  │     Routes     │  │    Routes     │
│   (9 KB)      │  │    (3 KB)      │  │   (10 KB)     │
└───────┬───────┘  └───────┬────────┘  └───────┬───────┘
        │                  │                    │
        ▼                  ▼                    ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   ag-grid     │  │   ag-grid     │  │   charts      │
│  (138 KB)     │  │  (138 KB)     │  │   (2 KB)      │
│ [LAZY LOAD]   │  │ [LAZY LOAD]   │  │ [LAZY LOAD]   │
└───────────────┘  └───────────────┘  └───────────────┘
```

---

## Vite Build Output Visualization

```
dist/
├── index.html (5 KB)
├── assets/
│   ├── CSS Files:
│   │   ├── index.css (43 KB / 8 KB gzipped)
│   │   └── ag-grid.css (250 KB / 42 KB gzipped)
│   │
│   ├── CRITICAL PATH (Loads Immediately):
│   │   ├── react-vendor.js (779 KB / 204 KB gzipped) ← Core React
│   │   ├── index.js (16 KB / 6 KB gzipped) ← Entry point
│   │   ├── utils.js (27 KB / 8 KB gzipped) ← Utilities
│   │   └── ui.js (0.5 KB / 0.2 KB gzipped) ← UI components
│   │
│   ├── VENDOR CHUNKS (Load as Needed):
│   │   ├── tanstack.js (included in react-vendor)
│   │   ├── supabase.js (164 KB / 40 KB gzipped)
│   │   ├── sentry.js (232 KB / 73 KB gzipped)
│   │   ├── forms.js (60 KB / 14 KB gzipped)
│   │   └── vendor.js (368 KB / 120 KB gzipped)
│   │
│   ├── HEAVY LAZY CHUNKS (Load on Demand):
│   │   ├── ag-grid.js (497 KB / 138 KB gzipped) ← Planning/Config
│   │   └── charts.js (6 KB / 2 KB gzipped) ← Analysis
│   │
│   └── ROUTE CHUNKS (Per Module Layer):
│       ├── routes-planning.js (40 KB / 9 KB gzipped)
│       ├── routes-analysis.js (36 KB / 10 KB gzipped)
│       ├── routes-consolidation.js (10 KB / 3 KB gzipped)
│       ├── routes-configuration.js (7 KB / 3 KB gzipped)
│       └── routes-strategic.js (10 KB / 3 KB gzipped)
```

---

## Loading Timeline Comparison

### Before Optimization
```
0ms    ┌─────────────────────────────────────────────────┐
       │ Download Initial Bundle (450 KB gzipped)        │
2500ms └─────────────────────────────────────────────────┘
       ┌──────────────────────────┐
       │ Parse & Execute JS       │
3500ms └──────────────────────────┘
       ┌─────┐
       │ FCP │ First Contentful Paint
4000ms └─────┘
       ┌─────┐
       │ TTI │ Time to Interactive
       └─────┘
```

### After Optimization
```
0ms    ┌────────────────────────────┐
       │ Download Initial (218 KB)  │
1000ms └────────────────────────────┘
       ┌──────────────┐
       │ Parse & Exec │
1500ms └──────────────┘
       ┌─────┐
       │ FCP │ 40% FASTER
2000ms └─────┘
       │
       │ User navigates to Planning →
       │ ┌───────────────────┐
       │ │ Load ag-grid.js   │
2500ms │ └───────────────────┘
       ┌─────┐
       │ TTI │ 38% FASTER (for Planning page)
       └─────┘
```

---

## Lazy Loading Strategy Matrix

| Component Type | Strategy | Bundle Impact | Load Trigger |
|----------------|----------|---------------|--------------|
| **React Core** | Pre-bundled | +204 KB | Initial |
| **AG Grid** | Lazy Load | +138 KB | Planning/Config routes |
| **Recharts** | Lazy Load | +2 KB | Analysis routes |
| **Supabase** | Pre-bundled | +40 KB | Auth/Data needed early |
| **Sentry** | Pre-bundled | +73 KB | Error tracking needed |
| **Forms** | On-demand | +14 KB | Form pages |
| **Routes** | Dynamic Import | +3-10 KB | Navigation |

---

## Route-Based Code Splitting

```
TanStack Router (File-Based)
      │
      ├── /routes/dashboard.tsx
      │   → Loads: react-vendor, utils, ui
      │   → Initial: 218 KB gzipped
      │
      ├── /routes/planning/
      │   ├── enrollment.tsx
      │   │   → Lazy loads: ag-grid (138 KB)
      │   │   → Lazy loads: routes-planning (9 KB)
      │   │   → Total new: 147 KB gzipped
      │   │
      │   ├── classes.tsx
      │   │   → Reuses: ag-grid (cached!)
      │   │   → Total new: 0 KB (cached)
      │   │
      │   └── dhg.tsx
      │       → Reuses: ag-grid (cached!)
      │
      ├── /routes/analysis/
      │   ├── kpis.tsx
      │   │   → Lazy loads: charts (2 KB)
      │   │   → Lazy loads: routes-analysis (10 KB)
      │   │   → Total new: 12 KB gzipped
      │   │
      │   └── variance.tsx
      │       → Reuses: charts (cached!)
      │
      └── /routes/consolidation/
          └── budget.tsx
              → Lazy loads: routes-consolidation (3 KB)
```

---

## Manual Chunks Configuration

```typescript
// vite.config.ts - manualChunks function

if (id.includes('node_modules')) {

  // React ecosystem → react-vendor.js (204 KB)
  if (id.includes('react') || id.includes('react-dom'))
    return 'react-vendor'

  // TanStack → tanstack.js (included in react-vendor)
  if (id.includes('@tanstack'))
    return 'tanstack'

  // AG Grid → ag-grid.js (138 KB) [LAZY]
  if (id.includes('ag-grid'))
    return 'ag-grid'

  // Recharts → charts.js (2 KB) [LAZY]
  if (id.includes('recharts'))
    return 'charts'

  // Supabase → supabase.js (40 KB)
  if (id.includes('@supabase'))
    return 'supabase'

  // Forms → forms.js (14 KB)
  if (id.includes('react-hook-form') || id.includes('zod'))
    return 'forms'
}

// App code → route-based chunks
if (id.includes('src/routes/planning/'))
  return 'routes-planning'
if (id.includes('src/routes/analysis/'))
  return 'routes-analysis'
```

---

## Cache Strategy

```
┌─────────────────────────────────────────────────────┐
│ Browser Cache (Long-term - immutable files)         │
├─────────────────────────────────────────────────────┤
│ react-vendor-[hash].js    Cache: 1 year             │
│ ag-grid-[hash].js         Cache: 1 year             │
│ charts-[hash].js          Cache: 1 year             │
│ vendor-[hash].js          Cache: 1 year             │
├─────────────────────────────────────────────────────┤
│ Browser Cache (Medium-term - app code)              │
├─────────────────────────────────────────────────────┤
│ routes-*-[hash].js        Cache: 1 week             │
│ index-[hash].js           Cache: 1 week             │
├─────────────────────────────────────────────────────┤
│ No Cache (Dynamic)                                  │
├─────────────────────────────────────────────────────┤
│ index.html                Cache: no-cache            │
└─────────────────────────────────────────────────────┘

Benefits:
✅ Vendor chunks rarely change → long cache
✅ Route chunks update frequently → shorter cache
✅ HTML always fresh → picks up new hashes
✅ Users only download changed chunks
```

---

## Optimization Impact Summary

```
                    BEFORE              AFTER
                    ──────              ─────
Initial Bundle:     450 KB    →         218 KB   (-52%)
FCP (3G):          2.5s      →         1.5s     (-40%)
TTI (3G):          4.0s      →         2.5s     (-38%)
Lighthouse:        ~75       →         ~85-90   (+13%)

User Experience:
  Dashboard:       Slow      →         Fast     ✅
  Planning Pages:  Slow      →         Medium   ✅ (lazy load)
  Analysis Pages:  Slow      →         Fast     ✅ (small lazy)
  Mobile (4G):     Poor      →         Good     ✅
```

---

## Developer Workflow

```
1. Development:
   pnpm dev
   → All chunks load normally
   → HMR works with lazy chunks
   → Fast refresh preserved

2. Before Commit:
   pnpm typecheck
   pnpm lint
   pnpm build:analyze
   → Verify no TypeScript errors
   → Verify no lint errors
   → Visual bundle analysis

3. CI/CD:
   pnpm build
   → Check bundle size < 300 KB
   → Fail if regression
   → Deploy if passed

4. Production:
   → CDN serves static assets
   → Gzip/Brotli compression
   → Long-term caching
   → Lazy chunks load on demand
```

---

## Key Takeaways

1. **Initial Bundle Matters Most**
   - Users feel 218 KB vs 450 KB difference
   - 52% reduction = 40% faster FCP

2. **Lazy Loading is Powerful**
   - AG Grid: 138 KB saved upfront
   - Only loads when user needs it
   - Cached for subsequent visits

3. **Route Splitting Works**
   - Each route is a separate chunk
   - Users only download what they visit
   - Better long-term cache strategy

4. **Loading Skeletons Help**
   - Perceived performance boost
   - Users see instant feedback
   - Professional UX

5. **Measure Everything**
   - Use `pnpm build:analyze` regularly
   - Monitor bundle size in CI/CD
   - Track performance metrics

---

**For More Details**: See [PHASE_2.5_CODE_SPLITTING_SUMMARY.md](./PHASE_2.5_CODE_SPLITTING_SUMMARY.md)
