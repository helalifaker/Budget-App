# Performance Optimizations

**Version**: 1.0
**Target**: Sub-second response times, 100+ concurrent users

## Database Optimizations

### Indexes

```sql
-- Budget Versions
CREATE INDEX idx_budget_versions_status ON budget_versions(status);
CREATE INDEX idx_budget_versions_fiscal_year ON budget_versions(fiscal_year);
CREATE INDEX idx_budget_versions_created_by ON budget_versions(created_by);

-- Enrollment Plans
CREATE INDEX idx_enrollment_version ON enrollment_plans(budget_version_id);
CREATE INDEX idx_enrollment_level ON enrollment_plans(level_id);
CREATE INDEX idx_enrollment_composite ON enrollment_plans(budget_version_id, level_id, nationality);

-- Class Structure
CREATE INDEX idx_class_structure_version ON class_structures(budget_version_id);
CREATE INDEX idx_class_structure_level ON class_structures(level_id);

-- DHG Calculations
CREATE INDEX idx_dhg_version ON dhg_calculations(budget_version_id);
CREATE INDEX idx_dhg_subject ON dhg_calculations(subject_id);
CREATE INDEX idx_dhg_composite ON dhg_calculations(budget_version_id, subject_id);

-- Revenue Plans
CREATE INDEX idx_revenue_version ON revenue_plans(budget_version_id);
CREATE INDEX idx_revenue_account ON revenue_plans(account_code);
CREATE INDEX idx_revenue_period ON revenue_plans(period);

-- Cost Plans
CREATE INDEX idx_cost_version ON cost_plans(budget_version_id);
CREATE INDEX idx_cost_account ON cost_plans(account_code);

-- Budget vs Actual
CREATE INDEX idx_actuals_version ON actuals(budget_version_id);
CREATE INDEX idx_actuals_period ON actuals(period);
CREATE INDEX idx_actuals_account ON actuals(account_code);
```

### Query Optimization

**Use SELECT RELATED / PREFETCH RELATED**:
```python
# Bad - N+1 queries
enrollments = EnrollmentPlan.objects.filter(budget_version_id=version_id)
for e in enrollments:
    print(e.level.name)  # N queries

# Good - 2 queries total
enrollments = EnrollmentPlan.objects.filter(
    budget_version_id=version_id
).select_related('level', 'budget_version')
```

**Pagination for Large Datasets**:
```python
# Always paginate list endpoints
@router.get("/enrollment/{version_id}")
async def get_enrollment(
    version_id: str,
    page: int = 1,
    page_size: int = 50,
    db: Session = Depends(get_db)
):
    offset = (page - 1) * page_size
    query = db.query(EnrollmentPlan).filter(
        EnrollmentPlan.budget_version_id == version_id
    )
    total = query.count()
    items = query.offset(offset).limit(page_size).all()

    return {
        "data": items,
        "pagination": {
            "page": page,
            "page_size": page_size,
            "total_items": total,
            "total_pages": (total + page_size - 1) // page_size
        }
    }
```

## Backend Caching (Redis)

### Setup

```python
# app/core/cache.py
from redis import Redis
from functools import wraps
import json

redis_client = Redis.from_url("redis://redis:6379/0")

def cached(ttl: int = 300):
    """Cache decorator with TTL in seconds."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            key = f"{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"

            # Check cache
            cached_value = redis_client.get(key)
            if cached_value:
                return json.loads(cached_value)

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            redis_client.setex(key, ttl, json.dumps(result))

            return result
        return wrapper
    return decorator
```

### Usage

```python
from app.core.cache import cached

@cached(ttl=600)  # Cache for 10 minutes
async def get_kpis(version_id: str) -> dict:
    """Expensive KPI calculation - cache results."""
    # ... complex calculations
    return kpis
```

### Cache Invalidation

```python
def invalidate_cache_pattern(pattern: str):
    """Invalidate all keys matching pattern."""
    for key in redis_client.scan_iter(match=pattern):
        redis_client.delete(key)

# After updating enrollment
def update_enrollment(version_id: str, data: dict):
    # ... update database

    # Invalidate related caches
    invalidate_cache_pattern(f"get_enrollment:{version_id}:*")
    invalidate_cache_pattern(f"get_kpis:{version_id}:*")
    invalidate_cache_pattern(f"get_class_structure:{version_id}:*")
```

## Frontend Optimizations

### React Query Caching

```typescript
// lib/api/client.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 minutes
      gcTime: 10 * 60 * 1000,    // 10 minutes
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    },
  },
});
```

### Code Splitting

```typescript
// routes/__root.tsx
import { lazy } from 'react';

// Lazy load heavy modules
const DHGPage = lazy(() => import('./routes/planning/dhg'));
const ConsolidationPage = lazy(() => import('./routes/consolidation/budget'));
const StatementPage = lazy(() => import('./routes/consolidation/statements'));

export function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Router>
        <Route path="/planning/dhg" component={DHGPage} />
        <Route path="/consolidation/budget" component={ConsolidationPage} />
        <Route path="/consolidation/statements" component={StatementPage} />
      </Router>
    </Suspense>
  );
}
```

### Memoization

```typescript
// components/grids/EnrollmentGrid.tsx
import { useMemo } from 'react';

export function EnrollmentGrid({ data }: { data: EnrollmentPlan[] }) {
  // Memoize column definitions
  const columnDefs = useMemo(() => [
    { field: 'level_name', headerName: 'Level', sortable: true },
    { field: 'nationality', headerName: 'Nationality', sortable: true },
    { field: 'student_count', headerName: 'Students', editable: true },
  ], []);

  // Memoize expensive calculations
  const totals = useMemo(() => {
    return data.reduce((acc, item) => acc + item.student_count, 0);
  }, [data]);

  return <AgGridReact columnDefs={columnDefs} rowData={data} />;
}
```

### Virtual Scrolling (AG Grid)

```typescript
// AG Grid handles virtualization automatically for large datasets
<AgGridReact
  rowData={data}
  columnDefs={columnDefs}
  rowModelType="infinite"  // For very large datasets
  cacheBlockSize={100}
  maxBlocksInCache={10}
/>
```

## API Response Optimization

### Field Selection

```python
# Allow clients to select only needed fields
@router.get("/enrollment/{version_id}")
async def get_enrollment(
    version_id: str,
    fields: Optional[str] = None,  # e.g., "id,level_name,student_count"
    db: Session = Depends(get_db)
):
    query = db.query(EnrollmentPlan).filter(
        EnrollmentPlan.budget_version_id == version_id
    )

    if fields:
        # Only load specified columns
        field_list = fields.split(',')
        query = query.options(load_only(*field_list))

    return query.all()
```

### Compression

```python
# app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Response Streaming

```python
from fastapi.responses import StreamingResponse

@router.get("/export/enrollment/{version_id}")
async def export_enrollment(version_id: str):
    """Stream large Excel export instead of loading into memory."""
    def generate():
        # Fetch data in chunks
        offset = 0
        while True:
            chunk = get_enrollment_chunk(version_id, offset, 1000)
            if not chunk:
                break
            yield chunk
            offset += 1000

    return StreamingResponse(generate(), media_type="application/vnd.ms-excel")
```

## Database Connection Pooling

```python
# app/core/database.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,  # Number of connections
    max_overflow=10,  # Allow burst connections
    pool_pre_ping=True,  # Verify connection before use
    pool_recycle=3600,  # Recycle connections after 1 hour
)
```

## Monitoring & Profiling

### Backend Profiling

```python
# app/middleware/profiling.py
from fastapi import Request
import time

@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)

    # Log slow requests
    if process_time > 1.0:
        logger.warning(f"Slow request: {request.url} took {process_time:.2f}s")

    return response
```

### Frontend Performance Monitoring

```typescript
// lib/monitoring/performance.ts
export function measurePerformance(name: string, fn: () => void) {
  const start = performance.now();
  fn();
  const duration = performance.now() - start;

  // Send to analytics
  if (duration > 100) {
    console.warn(`Slow operation: ${name} took ${duration}ms`);
  }

  // Send to Sentry or similar
  if (window.PerformanceObserver) {
    // Track Core Web Vitals
    new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) {
        console.log(`${entry.name}: ${entry.value}ms`);
      }
    }).observe({ entryTypes: ['measure'] });
  }
}
```

## CDN & Static Assets

### Nginx Configuration

```nginx
# Cache static assets aggressively
location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
    expires 1y;
    add_header Cache-Control "public, immutable";
    access_log off;
}

# Gzip compression
gzip on;
gzip_vary on;
gzip_min_length 1024;
gzip_types text/css application/javascript application/json image/svg+xml;
```

### CDN (CloudFlare)

1. Point DNS to CloudFlare
2. Enable caching for static assets
3. Enable auto-minification for JS/CSS/HTML
4. Enable Brotli compression
5. Use CloudFlare Workers for edge caching

## Load Testing

### k6 Load Test

```javascript
// load-test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 50 },   // Ramp up to 50 users
    { duration: '5m', target: 100 },  // Stay at 100 users
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% of requests under 500ms
    http_req_failed: ['rate<0.01'],   // Less than 1% failure rate
  },
};

export default function () {
  const res = http.get('http://localhost:8000/api/v1/configuration/budget-versions');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

Run: `k6 run load-test.js`

## Performance Benchmarks

Target metrics:
- **API Response Time**: < 200ms (p95)
- **Page Load Time**: < 2s (LCP)
- **Time to Interactive**: < 3s
- **Database Query Time**: < 50ms (p95)
- **Concurrent Users**: 100+
- **Throughput**: 1000+ req/min

---

**End of Performance Optimizations**
