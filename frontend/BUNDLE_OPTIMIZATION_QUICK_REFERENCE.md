# Bundle Optimization Quick Reference

**Last Updated**: December 2, 2025
**Current Bundle Size**: 218KB gzipped (target: <300KB) ✅

---

## Quick Commands

```bash
# Analyze bundle composition (opens visual treemap)
pnpm build:analyze

# Show file sizes after build
pnpm build:stats

# Type check before commit
pnpm typecheck

# Full production build
pnpm build
```

---

## Using Lazy-Loaded Components

### DataTable (AG Grid) - 137KB gzipped

```typescript
// ❌ WRONG: Loads AG Grid upfront
import { DataTable } from '@/components/DataTable'

// ✅ CORRECT: Lazy loads AG Grid on demand
import { DataTableLazy } from '@/components/DataTableLazy'

<DataTableLazy
  rowData={data}
  columnDefs={columns}
  loading={isLoading}
  error={error}
  pagination={true}
/>
```

### Charts (Recharts) - 2KB gzipped

```typescript
// ❌ WRONG: Loads Recharts upfront
import { BarChart, Bar, XAxis } from 'recharts'

// ✅ CORRECT: Lazy loads Recharts on demand
import {
  BarChartLazy,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from '@/components/charts/ChartsLazy'

<ResponsiveContainer width="100%" height={400}>
  <BarChartLazy data={data}>
    <CartesianGrid strokeDasharray="3 3" />
    <XAxis dataKey="name" />
    <YAxis />
    <Tooltip />
    <Bar dataKey="value" fill="#3B82F6" />
  </BarChartLazy>
</ResponsiveContainer>
```

---

## Loading Skeletons

```typescript
import {
  GridSkeleton,        // For AG Grid tables
  ChartSkeleton,       // For Recharts visualizations
  DashboardSkeleton,   // For KPI cards
  FormSkeleton,        // For form sections
  LoadingSpinner,      // Generic spinner
} from '@/components/LoadingSkeleton'

// Example: Lazy loading with skeleton
import { lazy, Suspense } from 'react'

const HeavyComponent = lazy(() => import('./HeavyComponent'))

function MyPage() {
  return (
    <Suspense fallback={<GridSkeleton />}>
      <HeavyComponent />
    </Suspense>
  )
}
```

---

## Bundle Size Limits

| Chunk Type | Limit (gzipped) | Current | Status |
|------------|-----------------|---------|--------|
| Initial Bundle | 300 KB | 218 KB | ✅ |
| Vendor Chunk | 250 KB | 204 KB | ✅ |
| Route Chunk | 50 KB | 9-10 KB | ✅ |
| Lazy Chunk | 150 KB | 137 KB | ✅ |

---

## Common Pitfalls

### 1. Direct Imports of Heavy Libraries
```typescript
// ❌ BAD: Loads entire library upfront
import { AgGridReact } from 'ag-grid-react'
import { BarChart } from 'recharts'

// ✅ GOOD: Use lazy-loaded wrappers
import { DataTableLazy } from '@/components/DataTableLazy'
import { BarChartLazy } from '@/components/charts/ChartsLazy'
```

### 2. Missing Suspense Boundaries
```typescript
// ❌ BAD: No loading state
const HeavyComponent = lazy(() => import('./HeavyComponent'))
<HeavyComponent />

// ✅ GOOD: Suspense with fallback
<Suspense fallback={<LoadingSkeleton />}>
  <HeavyComponent />
</Suspense>
```

### 3. Importing Entire Library
```typescript
// ❌ BAD: Imports all of lodash
import _ from 'lodash'

// ✅ GOOD: Import specific functions
import debounce from 'lodash/debounce'
```

---

## Adding New Lazy-Loaded Components

### Step 1: Create Lazy Wrapper
```typescript
// components/MyHeavyComponentLazy.tsx
import { lazy, Suspense } from 'react'
import { LoadingSkeleton } from './LoadingSkeleton'

const MyHeavyComponent = lazy(() => import('./MyHeavyComponent'))

export function MyHeavyComponentLazy(props: MyHeavyComponentProps) {
  return (
    <Suspense fallback={<LoadingSkeleton />}>
      <MyHeavyComponent {...props} />
    </Suspense>
  )
}
```

### Step 2: Update Vite Config (if vendor library)
```typescript
// vite.config.ts
build: {
  rollupOptions: {
    output: {
      manualChunks: (id) => {
        if (id.includes('heavy-library')) {
          return 'heavy-library'
        }
      }
    }
  }
},
optimizeDeps: {
  exclude: ['heavy-library'] // Don't pre-bundle
}
```

### Step 3: Use in Routes
```typescript
import { MyHeavyComponentLazy } from '@/components/MyHeavyComponentLazy'

<MyHeavyComponentLazy data={data} />
```

---

## Monitoring Bundle Size

### Before Commit
```bash
# Check bundle size
pnpm build:stats

# Verify no TypeScript errors
pnpm typecheck

# Verify no lint errors (on your files)
pnpm lint
```

### CI/CD Check (Add to GitHub Actions)
```yaml
- name: Check bundle size
  run: |
    cd frontend
    pnpm build
    # Get gzipped size of main chunk
    SIZE=$(gzip -c dist/assets/index-*.js | wc -c | awk '{print int($1/1024)}')
    echo "Main bundle: ${SIZE}KB gzipped"
    if [ $SIZE -gt 300 ]; then
      echo "❌ Bundle too large: ${SIZE}KB > 300KB"
      exit 1
    fi
    echo "✅ Bundle size OK: ${SIZE}KB"
```

---

## Troubleshooting

### Build Fails with "terser not found"
```bash
# Install terser
pnpm add -D terser
```

### Large Initial Bundle Warning
```
(!) Some chunks are larger than 600 kB after minification.
```

**Solution**: Check if you're importing heavy libraries directly. Use lazy loading.

### TypeScript Error: Cannot find module
```typescript
// Ensure lazy import uses .then()
const Component = lazy(() =>
  import('./Component').then(m => ({ default: m.Component }))
)
```

### Suspense Boundary Not Working
```typescript
// Ensure Suspense wraps the lazy component, not inside it
<Suspense fallback={<Skeleton />}>
  <LazyComponent />
</Suspense>
```

---

## Performance Tips

### 1. Preload Critical Routes
```typescript
// In router configuration
const router = createRouter({
  routes: [
    {
      path: '/planning',
      component: lazy(() => import('./routes/planning')),
      // Preload when hovering over link
      loader: () => import('./routes/planning')
    }
  ]
})
```

### 2. Dynamic Imports in Event Handlers
```typescript
// Only load heavy library when needed
async function handleExport() {
  const { exportToExcel } = await import('./export-utils')
  exportToExcel(data)
}
```

### 3. Use Web Workers for Heavy Computation
```typescript
// Offload heavy calculations to worker
const worker = new Worker(
  new URL('./calculation.worker.ts', import.meta.url),
  { type: 'module' }
)
```

---

## Current Bundle Composition

```
Initial Bundle (218 KB gzipped):
├── react-vendor (204 KB) - React, ReactDOM, TanStack
├── index (6 KB)           - Main entry point
├── utils (8 KB)           - Utility libraries
└── ui (0.2 KB)            - UI components

Lazy-Loaded Chunks:
├── ag-grid (138 KB)       - Planning/config pages
├── charts (2 KB)          - Analysis pages
├── forms (14 KB)          - Form pages
├── supabase (40 KB)       - Auth/data operations
├── sentry (73 KB)         - Error monitoring
└── vendor (120 KB)        - Additional libraries

Route Chunks:
├── routes-planning (9 KB)
├── routes-analysis (10 KB)
├── routes-consolidation (3 KB)
├── routes-configuration (3 KB)
└── routes-strategic (3 KB)
```

---

## Resources

- [Phase 2.5 Implementation Summary](./PHASE_2.5_CODE_SPLITTING_SUMMARY.md)
- [Vite Code Splitting Docs](https://vitejs.dev/guide/features.html#code-splitting)
- [React Lazy Loading](https://react.dev/reference/react/lazy)
- [Bundle Size Best Practices](https://web.dev/your-first-performance-budget/)

---

**Questions?** Check the comprehensive [Phase 2.5 Summary](./PHASE_2.5_CODE_SPLITTING_SUMMARY.md)
