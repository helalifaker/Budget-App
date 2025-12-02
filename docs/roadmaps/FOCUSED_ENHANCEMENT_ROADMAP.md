# EFIR Budget App - Focused Enhancement Roadmap
**Production-Ready Enhancements for French School Budget Planning**

**Version:** 2.0 - Focused & Pragmatic
**Date:** December 2025
**Status:** Ready for Implementation

---

## Executive Summary

This roadmap focuses on production-ready enhancements that make EFIR Budget App **best-in-class** for French school budget planning, emphasizing:
- ✅ **Performance**: 10-100x faster DHG calculations and KPI dashboards
- ✅ **Reliability**: Production-grade error handling and monitoring
- ✅ **Collaboration**: Real-time multi-user editing (eliminating Excel version conflicts)
- ✅ **Data Accuracy**: Robust validation and audit trails

**Timeline**: 13-18 weeks (3-4.5 months)
**Focus**: EFIR-specific needs (DHG methodology, French PCG, AEFE integration)
**Philosophy**: Specialized tool, not generic platform

---

## Table of Contents

1. [Strategic Principles](#1-strategic-principles)
2. [Error Handling & Observability](#2-error-handling--observability)
3. [Performance Optimizations](#3-performance-optimizations)
4. [Real-Time Writeback & Collaboration](#4-real-time-writeback--collaboration)
5. [Spreading & Data Entry](#5-spreading--data-entry)
6. [Fast Data Processing & Exports](#6-fast-data-processing--exports)
7. [Technology Stack](#7-technology-stack)
8. [Implementation Phases](#8-implementation-phases)
9. [Success Metrics](#9-success-metrics)

---

## 1. Strategic Principles

### What We're Building
**A specialized, best-in-class DHG workforce planning tool for French schools**

- Focus on EFIR's fixed structure (DHG methodology, French PCG, AEFE regulations)
- Real-time collaboration for Finance + Academic directors
- Production-ready reliability and performance
- Data accuracy and audit trails for Board approval

### What We're NOT Building
❌ Generic planning platform (SAC/Anaplan competitor)
❌ Metadata-driven flexible architecture
❌ User-defined formula engine
❌ OLAP/BI semantic layer (Cube.js, dbt)

### Why This Approach?

| Decision | Rationale |
|----------|-----------|
| **Fixed schema** | French education system has rigid rules (DHG, PCG, AEFE) |
| **Hardcoded DHG formulas** | Calculations are well-defined in spec, not ad-hoc |
| **No formula engine** | Security risk + unnecessary complexity |
| **PostgreSQL views over Cube.js** | Simpler, sufficient for single-school app (~50 users) |
| **Real-time writeback** | Solves main Excel pain point (version conflicts) |

---

## 2. Error Handling & Observability

### 2.1 Production-Ready Error Tracking

**Goal**: Catch bugs before they corrupt budget data

| Feature | Implementation | Priority | Effort |
|---------|----------------|----------|--------|
| React Error Boundary | Catch render errors, prevent crashes | 🔴 Critical | 1 day |
| Sentry Integration | Production error monitoring with source maps | 🔴 Critical | 2 days |
| Structured Logging | JSON logs with correlation IDs | 🔴 Critical | 3 days |
| Toast Notifications | User-friendly error messages | 🟡 High | 1 day |
| Health Checks | Liveness/readiness endpoints | 🟡 High | 2 days |

**Total Effort**: ~1.5-2 weeks

#### 2.1.1 Frontend Setup

```typescript
// src/ErrorBoundary.tsx
import { ErrorBoundary } from 'react-error-boundary';
import * as Sentry from '@sentry/react';

function ErrorFallback({ error, resetErrorBoundary }: any) {
  return (
    <div className="error-container">
      <h2>Une erreur est survenue</h2>
      <p>Veuillez rafraîchir la page ou contacter le support.</p>
      <button onClick={resetErrorBoundary}>Réessayer</button>
    </div>
  );
}

export function AppErrorBoundary({ children }: { children: React.ReactNode }) {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, info) => {
        Sentry.captureException(error, { contexts: { react: info } });
      }}
    >
      {children}
    </ErrorBoundary>
  );
}
```

#### 2.1.2 Backend Structured Logging

```python
# app/core/logging.py
import structlog
from fastapi import Request
import uuid

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

async def logging_middleware(request: Request, call_next):
    correlation_id = str(uuid.uuid4())
    structlog.contextvars.bind_contextvars(
        correlation_id=correlation_id,
        path=request.url.path,
        method=request.method
    )

    logger.info("request_started")
    response = await call_next(request)
    logger.info("request_completed", status_code=response.status_code)

    response.headers["X-Correlation-ID"] = correlation_id
    return response
```

#### 2.1.3 Standardized Error Response

```python
# app/core/exceptions.py
from fastapi import HTTPException
from pydantic import BaseModel
from datetime import datetime

class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict | None = None
    correlation_id: str
    timestamp: datetime

class AppException(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict | None = None
    ):
        self.code = code
        super().__init__(status_code=status_code, detail=message)
        self.details = details

# Example usage
if class_size > max_class_size:
    raise AppException(
        status_code=400,
        code="CLASS_SIZE_EXCEEDED",
        message=f"La taille de classe ({class_size}) dépasse le maximum ({max_class_size})",
        details={
            "level": level_code,
            "current_size": class_size,
            "max_size": max_class_size
        }
    )
```

#### 2.1.4 Health Checks

```python
# app/api/v1/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
import redis

router = APIRouter()

@router.get("/health/live")
async def liveness():
    """Basic liveness check - is the server running?"""
    return {"status": "ok"}

@router.get("/health/ready")
async def readiness(db: AsyncSession = Depends(get_db)):
    """Readiness check - can we serve traffic?"""
    checks = {}

    # Check database
    try:
        await db.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Check Redis
    try:
        r = redis.Redis(host='localhost', port=6379)
        r.ping()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
    return {"status": status, "checks": checks}
```

### 2.2 Prometheus Metrics

```python
# app/core/metrics.py
from prometheus_fastapi_instrumentator import Instrumentator

instrumentator = Instrumentator()

# Custom metrics for EFIR
dhg_calculation_duration = instrumentator.histogram(
    "efir_dhg_calculation_duration_seconds",
    "Time to calculate DHG hours",
    labels={"level": "", "status": ""}
)

budget_operation_counter = instrumentator.counter(
    "efir_budget_operations_total",
    "Total budget operations",
    labels={"operation": "", "status": ""}
)
```

**Benefits for EFIR**:
- 🔍 **Debug enrollment → DHG → cost cascade** with correlation IDs
- 🐛 **Catch calculation bugs** before Finance Director sees them
- 📊 **Monitor performance** (DHG calculation time, API response times)
- 🚨 **Proactive alerts** via Sentry when errors spike

---

## 3. Performance Optimizations

### 3.1 Caching Strategy

**Goal**: 10-100x faster DHG calculations and dashboard loads

#### 3.1.1 Redis Setup

```python
# app/core/cache.py
import redis.asyncio as redis
from cashews import cache
import json
from typing import Any

# Initialize Redis
cache.setup("redis://localhost:6379/0")

# Caching decorators
@cache(ttl="1h", key="dhg:{budget_version_id}:{level_id}")
async def get_dhg_calculation(budget_version_id: str, level_id: str):
    """Cache DHG calculations for 1 hour"""
    pass

@cache(ttl="5m", key="kpi:dashboard:{budget_version_id}")
async def get_dashboard_kpis(budget_version_id: str):
    """Cache dashboard KPIs for 5 minutes"""
    pass
```

#### 3.1.2 Cache Invalidation Strategy

**EFIR-Specific Challenge**: Cascading calculations

```
Enrollment change → Invalidate class structure
                 → Invalidate DHG calculations
                 → Invalidate personnel costs
                 → Invalidate KPI dashboard
```

**Solution**: Dependency tracking with Redis pub/sub

```python
# app/core/cache_invalidation.py
import redis.asyncio as redis

class CacheInvalidator:
    """Handles cascading cache invalidation for EFIR"""

    DEPENDENCY_GRAPH = {
        "enrollment": ["class_structure", "revenue"],
        "class_structure": ["dhg_calculations", "facility_needs"],
        "dhg_calculations": ["personnel_costs", "kpi_dashboard"],
        "personnel_costs": ["budget_consolidation", "kpi_dashboard"],
        "revenue": ["budget_consolidation", "kpi_dashboard"]
    }

    @classmethod
    async def invalidate(cls, budget_version_id: str, entity: str):
        """Invalidate entity and all dependents"""
        redis_client = await redis.from_url("redis://localhost:6379")

        # Invalidate this entity
        pattern = f"*:{budget_version_id}:*{entity}*"
        async for key in redis_client.scan_iter(match=pattern):
            await redis_client.delete(key)

        # Recursively invalidate dependents
        for dependent in cls.DEPENDENCY_GRAPH.get(entity, []):
            await cls.invalidate(budget_version_id, dependent)

        await redis_client.close()

# Usage in API endpoints
@router.put("/enrollment/{id}")
async def update_enrollment(id: str, data: EnrollmentUpdate):
    # Update enrollment
    enrollment = await enrollment_service.update(id, data)

    # Invalidate caches
    await CacheInvalidator.invalidate(
        enrollment.budget_version_id,
        "enrollment"
    )

    return enrollment
```

### 3.2 Materialized Views for KPIs

```sql
-- KPI Dashboard Summary
CREATE MATERIALIZED VIEW efir_budget.mv_kpi_dashboard AS
SELECT
    bv.id as budget_version_id,
    bv.fiscal_year,
    bv.status,
    bv.name,

    -- Enrollment metrics
    COUNT(DISTINCT ed.id) FILTER (WHERE ed.nationality = 'French') as french_students,
    COUNT(DISTINCT ed.id) FILTER (WHERE ed.nationality = 'Saudi') as saudi_students,
    COUNT(DISTINCT ed.id) FILTER (WHERE ed.nationality = 'Other') as other_students,
    COUNT(DISTINCT ed.id) as total_students,

    -- DHG metrics
    SUM(dhg.total_hours) as total_dhg_hours,
    SUM(dhg.fte_required) as total_fte_required,
    SUM(dhg.aefe_positions) as aefe_positions,
    SUM(dhg.local_positions) as local_positions,

    -- Financial metrics (SAR)
    SUM(rv.amount_sar) FILTER (WHERE rv.account_code LIKE '70%') as total_revenue,
    SUM(pc.amount_sar) FILTER (WHERE pc.account_code LIKE '64%') as personnel_costs,
    SUM(oc.amount_sar) FILTER (WHERE oc.account_code LIKE '60%' OR oc.account_code LIKE '61%') as operational_costs,

    -- Calculated KPIs
    CASE
        WHEN COUNT(DISTINCT ed.id) > 0
        THEN SUM(rv.amount_sar) / COUNT(DISTINCT ed.id)
        ELSE 0
    END as revenue_per_student,

    CASE
        WHEN SUM(dhg.total_hours) > 0
        THEN COUNT(DISTINCT ed.id) / SUM(dhg.total_hours)
        ELSE 0
    END as students_per_teaching_hour,

    -- Timestamps
    MAX(bv.updated_at) as last_updated

FROM efir_budget.budget_versions bv
LEFT JOIN efir_budget.enrollment_data ed ON ed.budget_version_id = bv.id
LEFT JOIN efir_budget.dhg_calculations dhg ON dhg.budget_version_id = bv.id
LEFT JOIN efir_budget.revenue_projections rv ON rv.budget_version_id = bv.id
LEFT JOIN efir_budget.personnel_costs pc ON pc.budget_version_id = bv.id
LEFT JOIN efir_budget.operational_costs oc ON oc.budget_version_id = bv.id

GROUP BY bv.id, bv.fiscal_year, bv.status, bv.name
WITH DATA;

-- Indexes
CREATE UNIQUE INDEX ON efir_budget.mv_kpi_dashboard(budget_version_id);
CREATE INDEX ON efir_budget.mv_kpi_dashboard(fiscal_year, status);

-- Refresh strategy: After any budget data change
-- Call from Python: await db.execute("REFRESH MATERIALIZED VIEW CONCURRENTLY efir_budget.mv_kpi_dashboard")
```

**Refresh Strategy**:
- **On-demand**: After budget approval/submission
- **Scheduled**: Every 5 minutes during active budget planning season
- **Manual**: Dashboard refresh button

### 3.3 Frontend Performance

#### 3.3.1 React Query Configuration

```typescript
// src/lib/queryClient.ts
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes - data is fresh
      gcTime: 30 * 60 * 1000,         // 30 minutes - keep in cache
      retry: 2,                       // Retry failed requests twice
      refetchOnWindowFocus: false,    // Don't refetch on window focus
      refetchOnReconnect: true,       // Do refetch on reconnect
    },
    mutations: {
      retry: 1,                       // Retry mutations once
    },
  },
});
```

#### 3.3.2 Vite Chunk Splitting

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          // Vendor chunks
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          'tanstack': ['@tanstack/react-query', '@tanstack/react-router'],

          // Large dependencies
          'ag-grid': ['ag-grid-community', 'ag-grid-react'],
          'charts': ['recharts'],

          // Supabase
          'supabase': ['@supabase/supabase-js'],

          // UI library
          'ui': ['@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
        }
      }
    },

    // Target modern browsers for smaller bundles
    target: 'esnext',
    minify: 'terser',

    // Source maps for debugging
    sourcemap: true,
  }
});
```

**Expected Results**:
- Initial load: ~200-300kb (gzipped)
- AG Grid chunk: ~150kb (loaded on-demand)
- Charts chunk: ~100kb (loaded on-demand)

### 3.4 Performance Targets

| Metric | Current | Target | Method |
|--------|---------|--------|--------|
| DHG calculation | 3-5 seconds | <1 second | Redis caching |
| Dashboard load | 5-8 seconds | <2 seconds | Materialized views |
| Grid initial render | 1-2 seconds | <500ms | React Query + chunk splitting |
| API response time (p95) | N/A | <200ms | Caching + indexes |
| Bundle size (initial) | N/A | <300kb gzipped | Code splitting |

---

## 4. Real-Time Writeback & Collaboration

### 4.1 Feature Overview

**Goal**: Eliminate Excel version conflicts, enable Finance + Academic director collaboration

| Feature | Description | Priority | Effort |
|---------|-------------|----------|--------|
| Instant cell save | Edit cell → save immediately | 🔴 Critical | 3 days |
| Multi-user sync | See others' changes in real-time | 🔴 Critical | 5 days |
| Optimistic updates | UI updates before server confirms | 🔴 Critical | 5 days |
| Undo/redo | Revert changes with history | 🟡 High | 10 days |
| Change log | Audit trail for all changes | 🟡 High | 3 days |
| Cell comments | Annotate cells with notes | 🟢 Medium | 5 days |
| Cell locking | Lock approved cells | 🟢 Low | 3 days |

**Total Effort**: 4-6 weeks

### 4.2 Database Schema

#### 4.2.1 Planning Cells Table

```sql
-- Stores all user-editable budget values
CREATE TABLE efir_budget.planning_cells (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_version_id UUID NOT NULL REFERENCES budget_versions(id) ON DELETE CASCADE,

    -- Cell location (no JSONB - fixed schema for EFIR)
    module_code VARCHAR(50) NOT NULL,
    -- Examples: 'enrollment', 'dhg', 'revenue', 'personnel_costs'

    entity_id UUID,
    -- References specific row (enrollment_id, dhg_id, etc.)

    field_name VARCHAR(100) NOT NULL,
    -- Examples: 'student_count', 'tuition_rate', 'salary_amount'

    period_code VARCHAR(20),
    -- Examples: '2025-01', 'P1', 'annual', NULL for non-period data

    -- Value
    value_numeric NUMERIC(18,4),
    value_text TEXT,
    value_type VARCHAR(30) DEFAULT 'input',
    -- Types: 'input', 'calculated', 'imported', 'spread'

    -- Cell state
    is_locked BOOLEAN DEFAULT false,
    lock_reason VARCHAR(200),
    locked_by UUID REFERENCES auth.users(id),
    locked_at TIMESTAMPTZ,

    -- Audit
    modified_by UUID REFERENCES auth.users(id),
    modified_at TIMESTAMPTZ DEFAULT NOW(),

    -- Optimistic locking
    version INT DEFAULT 1,

    -- Unique constraint
    UNIQUE(budget_version_id, module_code, entity_id, field_name, period_code)
);

-- Indexes
CREATE INDEX ix_planning_cells_version ON efir_budget.planning_cells(budget_version_id);
CREATE INDEX ix_planning_cells_module ON efir_budget.planning_cells(module_code, entity_id);
CREATE INDEX ix_planning_cells_period ON efir_budget.planning_cells(period_code) WHERE period_code IS NOT NULL;

-- Enable Supabase Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE efir_budget.planning_cells;

-- RLS Policies
ALTER TABLE efir_budget.planning_cells ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view cells in their organization"
ON efir_budget.planning_cells FOR SELECT
USING (
    budget_version_id IN (
        SELECT id FROM efir_budget.budget_versions
        WHERE organization_id = (SELECT organization_id FROM auth.users WHERE id = auth.uid())
    )
);

CREATE POLICY "Users can edit unlocked cells if budget is draft/submitted"
ON efir_budget.planning_cells FOR UPDATE
USING (
    NOT is_locked
    AND budget_version_id IN (
        SELECT id FROM efir_budget.budget_versions
        WHERE organization_id = (SELECT organization_id FROM auth.users WHERE id = auth.uid())
        AND status IN ('draft', 'submitted')
    )
);
```

#### 4.2.2 Change Log (Undo/Redo)

```sql
-- Tracks all cell changes for undo/redo and audit
CREATE TABLE efir_budget.cell_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cell_id UUID REFERENCES planning_cells(id) ON DELETE SET NULL,
    budget_version_id UUID NOT NULL REFERENCES budget_versions(id),

    -- Change details
    module_code VARCHAR(50) NOT NULL,
    entity_id UUID,
    field_name VARCHAR(100) NOT NULL,
    period_code VARCHAR(20),

    old_value NUMERIC(18,4),
    new_value NUMERIC(18,4),

    change_type VARCHAR(50) NOT NULL,
    -- Types: 'manual', 'spread', 'import', 'formula', 'undo', 'redo'

    -- Session tracking for grouped undo
    session_id UUID NOT NULL,
    sequence_number INT NOT NULL,

    -- Audit
    changed_by UUID REFERENCES auth.users(id),
    changed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Additional context
    context JSONB DEFAULT '{}'
);

-- Indexes
CREATE INDEX ix_cell_changes_cell ON efir_budget.cell_changes(cell_id);
CREATE INDEX ix_cell_changes_session ON efir_budget.cell_changes(session_id, sequence_number);
CREATE INDEX ix_cell_changes_version ON efir_budget.cell_changes(budget_version_id);

-- RLS
ALTER TABLE efir_budget.cell_changes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view changes in their organization"
ON efir_budget.cell_changes FOR SELECT
USING (
    budget_version_id IN (
        SELECT id FROM efir_budget.budget_versions
        WHERE organization_id = (SELECT organization_id FROM auth.users WHERE id = auth.uid())
    )
);
```

#### 4.2.3 Cell Comments

```sql
CREATE TABLE efir_budget.cell_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cell_id UUID NOT NULL REFERENCES planning_cells(id) ON DELETE CASCADE,

    comment_text TEXT NOT NULL,

    -- Threading (optional)
    parent_comment_id UUID REFERENCES cell_comments(id),

    -- Status
    is_resolved BOOLEAN DEFAULT false,
    resolved_by UUID REFERENCES auth.users(id),
    resolved_at TIMESTAMPTZ,

    -- Audit
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX ix_cell_comments_cell ON efir_budget.cell_comments(cell_id);

-- RLS
ALTER TABLE efir_budget.cell_comments ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users can view/add comments in their organization"
ON efir_budget.cell_comments FOR ALL
USING (
    cell_id IN (
        SELECT id FROM efir_budget.planning_cells
        WHERE budget_version_id IN (
            SELECT id FROM efir_budget.budget_versions
            WHERE organization_id = (SELECT organization_id FROM auth.users WHERE id = auth.uid())
        )
    )
);
```

### 4.3 Frontend Implementation

#### 4.3.1 Optimistic Updates Hook

```typescript
// src/hooks/usePlanningWriteback.ts
import { useState, useCallback } from 'react';
import { useSupabaseClient } from '@supabase/auth-helpers-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { v4 as uuidv4 } from 'uuid';

interface CellUpdate {
  cellId?: string;
  budgetVersionId: string;
  moduleCode: string;
  entityId: string;
  fieldName: string;
  periodCode?: string;
  value: number;
}

interface UndoRedoState {
  sessionId: string;
  sequenceNumber: number;
  undoStack: CellUpdate[];
  redoStack: CellUpdate[];
}

export function usePlanningWriteback(budgetVersionId: string) {
  const supabase = useSupabaseClient();
  const queryClient = useQueryClient();

  const [undoState, setUndoState] = useState<UndoRedoState>({
    sessionId: uuidv4(),
    sequenceNumber: 0,
    undoStack: [],
    redoStack: [],
  });

  // Mutation for updating cells
  const updateMutation = useMutation({
    mutationFn: async (update: CellUpdate) => {
      const { data, error } = await supabase
        .from('planning_cells')
        .upsert({
          budget_version_id: update.budgetVersionId,
          module_code: update.moduleCode,
          entity_id: update.entityId,
          field_name: update.fieldName,
          period_code: update.periodCode,
          value_numeric: update.value,
          value_type: 'input',
          modified_at: new Date().toISOString(),
        }, {
          onConflict: 'budget_version_id,module_code,entity_id,field_name,period_code'
        })
        .select()
        .single();

      if (error) throw error;
      return data;
    },

    onSuccess: (data, variables) => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({
        queryKey: ['planning-cells', budgetVersionId]
      });

      // Add to undo stack
      setUndoState(prev => ({
        ...prev,
        sequenceNumber: prev.sequenceNumber + 1,
        undoStack: [...prev.undoStack, variables],
        redoStack: [], // Clear redo stack on new change
      }));
    },

    onError: (error, variables) => {
      toast.error(`Erreur lors de la sauvegarde: ${error.message}`);

      // Revert optimistic update
      queryClient.setQueryData(
        ['planning-cells', budgetVersionId],
        (old: any) => {
          // Revert the change
          return old; // In real implementation, revert specific cell
        }
      );
    }
  });

  // Update cell with optimistic UI
  const updateCell = useCallback(async (update: CellUpdate) => {
    // Optimistic update
    queryClient.setQueryData(
      ['planning-cells', budgetVersionId],
      (old: any) => {
        // Update UI immediately
        // Return updated data structure
        return old;
      }
    );

    // Persist to server
    await updateMutation.mutateAsync(update);
  }, [budgetVersionId, queryClient, updateMutation]);

  // Undo last change
  const undo = useCallback(async () => {
    if (undoState.undoStack.length === 0) return;

    const lastChange = undoState.undoStack[undoState.undoStack.length - 1];

    // TODO: Fetch old value from change log
    // TODO: Apply old value

    setUndoState(prev => ({
      ...prev,
      undoStack: prev.undoStack.slice(0, -1),
      redoStack: [...prev.redoStack, lastChange],
    }));

    toast.success('Annulation effectuée');
  }, [undoState]);

  // Redo last undone change
  const redo = useCallback(async () => {
    if (undoState.redoStack.length === 0) return;

    const lastUndone = undoState.redoStack[undoState.redoStack.length - 1];

    await updateCell(lastUndone);

    setUndoState(prev => ({
      ...prev,
      redoStack: prev.redoStack.slice(0, -1),
    }));

    toast.success('Rétablissement effectué');
  }, [undoState, updateCell]);

  return {
    updateCell,
    undo,
    redo,
    canUndo: undoState.undoStack.length > 0,
    canRedo: undoState.redoStack.length > 0,
  };
}
```

#### 4.3.2 Supabase Realtime Subscription

```typescript
// src/hooks/useRealtimeSync.ts
import { useEffect, useCallback } from 'react';
import { useSupabaseClient } from '@supabase/auth-helpers-react';
import { useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

export function useRealtimeSync(budgetVersionId: string) {
  const supabase = useSupabaseClient();
  const queryClient = useQueryClient();

  useEffect(() => {
    // Subscribe to changes in planning_cells for this budget version
    const channel = supabase
      .channel(`budget:${budgetVersionId}`)
      .on(
        'postgres_changes',
        {
          event: '*',
          schema: 'efir_budget',
          table: 'planning_cells',
          filter: `budget_version_id=eq.${budgetVersionId}`,
        },
        (payload) => {
          console.log('Realtime update:', payload);

          // Update local cache
          queryClient.invalidateQueries({
            queryKey: ['planning-cells', budgetVersionId]
          });

          // Show toast if changed by another user
          if (payload.eventType === 'UPDATE' && payload.new.modified_by !== (window as any).currentUserId) {
            toast.info('Un autre utilisateur a modifié des données', {
              description: `Module: ${payload.new.module_code}`,
              duration: 3000,
            });
          }
        }
      )
      .subscribe();

    return () => {
      supabase.removeChannel(channel);
    };
  }, [budgetVersionId, supabase, queryClient]);
}
```

#### 4.3.3 AG Grid Integration

```typescript
// src/components/PlanningGrid.tsx
import { AgGridReact } from 'ag-grid-react';
import { usePlanningWriteback } from '@/hooks/usePlanningWriteback';
import { useRealtimeSync } from '@/hooks/useRealtimeSync';
import { ColDef } from 'ag-grid-community';

interface PlanningGridProps {
  budgetVersionId: string;
  moduleCode: string;
  data: any[];
}

export function PlanningGrid({ budgetVersionId, moduleCode, data }: PlanningGridProps) {
  const { updateCell, undo, redo, canUndo, canRedo } = usePlanningWriteback(budgetVersionId);
  useRealtimeSync(budgetVersionId);

  const columnDefs: ColDef[] = [
    { field: 'name', headerName: 'Nom', editable: false },
    {
      field: 'value',
      headerName: 'Valeur',
      editable: true,
      cellClass: 'editable-cell',
      valueFormatter: (params) => {
        return new Intl.NumberFormat('fr-FR', {
          style: 'currency',
          currency: 'SAR'
        }).format(params.value);
      }
    },
  ];

  const onCellValueChanged = useCallback(async (event: any) => {
    const { data, colDef, newValue } = event;

    // Update via writeback hook
    await updateCell({
      budgetVersionId,
      moduleCode,
      entityId: data.id,
      fieldName: colDef.field,
      value: newValue,
    });
  }, [budgetVersionId, moduleCode, updateCell]);

  return (
    <div className="flex flex-col h-full">
      {/* Undo/Redo toolbar */}
      <div className="flex gap-2 mb-2">
        <button
          onClick={undo}
          disabled={!canUndo}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          Annuler (Ctrl+Z)
        </button>
        <button
          onClick={redo}
          disabled={!canRedo}
          className="px-3 py-1 bg-gray-200 rounded disabled:opacity-50"
        >
          Rétablir (Ctrl+Y)
        </button>
      </div>

      {/* AG Grid */}
      <div className="ag-theme-quartz flex-1">
        <AgGridReact
          rowData={data}
          columnDefs={columnDefs}
          onCellValueChanged={onCellValueChanged}
          singleClickEdit={true}
          stopEditingWhenCellsLoseFocus={true}
        />
      </div>
    </div>
  );
}
```

**Benefits for EFIR**:
- ✅ **No more version conflicts**: Finance + Academic directors edit simultaneously
- ✅ **Instant feedback**: See changes immediately
- ✅ **Audit trail**: Every change tracked in change log
- ✅ **Undo/Redo**: Easy to experiment with scenarios
- ✅ **Comments**: Annotate assumptions for Board review

---

## 5. Spreading & Data Entry

### 5.1 Spreading Methods

**Goal**: Distribute annual values across periods efficiently

| Method | Use Case | Formula |
|--------|----------|---------|
| **Equal** | Uniform distribution | `value / period_count` |
| **Proportional** | Based on existing ratios | `value * (period_value / total)` |
| **Weighted** | Custom weights per period | `value * weight[period] / sum(weights)` |
| **Seasonal** | School year pattern | Predefined for EFIR (Sep-Jun high, Jul-Aug low) |

**Effort**: 2-3 weeks

### 5.2 Implementation

```python
# app/services/spreading.py
from enum import Enum
from decimal import Decimal

class SpreadMethod(str, Enum):
    EQUAL = "equal"
    PROPORTIONAL = "proportional"
    WEIGHTED = "weighted"
    SEASONAL = "seasonal"

# EFIR-specific seasonal pattern
EFIR_SEASONAL_WEIGHTS = {
    "01": 1.0,  # January
    "02": 1.0,  # February
    "03": 1.0,  # March
    "04": 1.0,  # April
    "05": 1.0,  # May
    "06": 0.8,  # June (end of school year)
    "07": 0.2,  # July (summer, minimal activity)
    "08": 0.3,  # August (preparation for new year)
    "09": 1.2,  # September (start of school year)
    "10": 1.1,  # October
    "11": 1.1,  # November
    "12": 1.0,  # December
}

async def spread_value(
    source_value: Decimal,
    periods: list[str],
    method: SpreadMethod,
    existing_values: dict[str, Decimal] | None = None,
    custom_weights: dict[str, Decimal] | None = None
) -> dict[str, Decimal]:
    """
    Distribute a value across multiple periods

    Args:
        source_value: Total value to spread
        periods: List of period codes (e.g., ['2025-01', '2025-02', ...])
        method: Spreading method
        existing_values: For proportional spreading
        custom_weights: For weighted spreading

    Returns:
        Dictionary of period -> value
    """

    if method == SpreadMethod.EQUAL:
        # Simple equal distribution
        period_value = source_value / len(periods)
        return {period: period_value for period in periods}

    elif method == SpreadMethod.PROPORTIONAL:
        # Distribute based on existing ratios
        if not existing_values:
            raise ValueError("Proportional spreading requires existing values")

        total = sum(existing_values.values())
        if total == 0:
            # Fallback to equal if no existing values
            return {period: source_value / len(periods) for period in periods}

        return {
            period: source_value * (existing_values[period] / total)
            for period in periods
        }

    elif method == SpreadMethod.WEIGHTED:
        # Custom weights
        if not custom_weights:
            raise ValueError("Weighted spreading requires custom weights")

        total_weight = sum(custom_weights.values())
        return {
            period: source_value * (custom_weights[period] / total_weight)
            for period in periods
        }

    elif method == SpreadMethod.SEASONAL:
        # EFIR-specific seasonal pattern
        weights = {
            period: EFIR_SEASONAL_WEIGHTS.get(period[-2:], Decimal(1.0))
            for period in periods
        }
        total_weight = sum(weights.values())
        return {
            period: source_value * (weights[period] / total_weight)
            for period in periods
        }
```

### 5.3 Frontend Spreading Dialog

```typescript
// src/components/SpreadingDialog.tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Select } from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { useState } from 'react';

interface SpreadingDialogProps {
  open: boolean;
  onClose: () => void;
  sourceValue: number;
  periods: string[];
  onSpread: (method: string, result: Record<string, number>) => Promise<void>;
}

export function SpreadingDialog({ open, onClose, sourceValue, periods, onSpread }: SpreadingDialogProps) {
  const [method, setMethod] = useState<'equal' | 'seasonal'>('equal');
  const [preview, setPreview] = useState<Record<string, number>>({});

  const calculatePreview = () => {
    if (method === 'equal') {
      const valuePerPeriod = sourceValue / periods.length;
      setPreview(Object.fromEntries(periods.map(p => [p, valuePerPeriod])));
    } else if (method === 'seasonal') {
      // Call API to get seasonal spread
      // setPreview(result);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Répartir la valeur sur plusieurs périodes</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div>
            <label>Valeur totale: {sourceValue.toLocaleString('fr-FR')} SAR</label>
          </div>

          <div>
            <label>Méthode de répartition</label>
            <Select value={method} onValueChange={setMethod}>
              <option value="equal">Égale (même montant par période)</option>
              <option value="seasonal">Saisonnière (année scolaire EFIR)</option>
            </Select>
          </div>

          <div>
            <Button onClick={calculatePreview}>Prévisualiser</Button>
          </div>

          {Object.keys(preview).length > 0 && (
            <div className="border rounded p-4 max-h-60 overflow-y-auto">
              <h4 className="font-semibold mb-2">Aperçu:</h4>
              {Object.entries(preview).map(([period, value]) => (
                <div key={period} className="flex justify-between py-1">
                  <span>{period}</span>
                  <span>{value.toLocaleString('fr-FR')} SAR</span>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end gap-2">
            <Button variant="outline" onClick={onClose}>Annuler</Button>
            <Button onClick={() => onSpread(method, preview)}>Appliquer</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
```

**EFIR Use Cases**:
- 📅 **Annual budget → Monthly**: Distribute 12-month expenses
- 📊 **Period 1 / Period 2 split**: Jan-Jun vs Sep-Dec academic structure
- 📈 **Multi-year strategic**: Apply growth rates for 5-year plan
- 🎓 **Seasonal pattern**: High activity Sep-Jun, low Jul-Aug

---

## 6. Fast Data Processing & Exports

### 6.1 DuckDB for Fast Exports

**Goal**: 10-100x faster Excel/CSV exports for Board presentations and Odoo/Skolengo imports

```python
# app/services/export_service.py
import duckdb
import polars as pl
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill

async def export_financial_statements_excel(
    budget_version_id: str,
    format: str = "PCG"  # "PCG" or "IFRS"
) -> bytes:
    """
    Generate financial statements Excel with multiple sheets
    Uses DuckDB for fast aggregations
    """

    # Connect to PostgreSQL via DuckDB
    con = duckdb.connect()
    con.execute("""
        INSTALL postgres;
        LOAD postgres;
        ATTACH 'postgresql://user:pass@host/db' AS pg (TYPE POSTGRES);
    """)

    # Query data using DuckDB SQL (10-100x faster than Python loops)
    profit_loss = con.execute("""
        SELECT
            account_code,
            account_name,
            SUM(amount_sar) as total
        FROM pg.efir_budget.revenue_projections
        WHERE budget_version_id = ?
        GROUP BY account_code, account_name
        ORDER BY account_code
    """, [budget_version_id]).df()

    balance_sheet = con.execute("""
        SELECT
            account_code,
            account_name,
            SUM(amount_sar) as total
        FROM pg.efir_budget.balance_sheet_items
        WHERE budget_version_id = ?
        GROUP BY account_code, account_name
        ORDER BY account_code
    """, [budget_version_id]).df()

    # Create Excel with openpyxl
    wb = Workbook()

    # Profit & Loss sheet
    ws_pl = wb.active
    ws_pl.title = "Compte de Résultat"

    # Headers
    ws_pl['A1'] = 'Compte'
    ws_pl['B1'] = 'Libellé'
    ws_pl['C1'] = 'Montant (SAR)'

    # Style headers
    for cell in ws_pl['1:1']:
        cell.font = Font(bold=True)
        cell.fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

    # Write data
    for idx, row in profit_loss.iterrows():
        ws_pl.append([row['account_code'], row['account_name'], row['total']])

    # Balance Sheet sheet
    ws_bs = wb.create_sheet("Bilan")
    # ... similar logic

    # Save to bytes
    from io import BytesIO
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return buffer.getvalue()
```

### 6.2 Polars for Fast Transformations

```python
# app/services/odoo_integration.py
import polars as pl

async def transform_for_odoo_import(budget_version_id: str) -> bytes:
    """
    Transform EFIR budget data to Odoo import format
    Uses Polars for 10-100x faster transformations than Pandas
    """

    # Load data from PostgreSQL
    query = """
        SELECT
            account_code,
            period_code,
            amount_sar,
            account_type
        FROM efir_budget.consolidated_budget
        WHERE budget_version_id = ?
    """

    # Read with Polars (much faster than Pandas)
    df = pl.read_database(query, connection_uri, parameters=[budget_version_id])

    # Transform to Odoo format
    odoo_format = df.select([
        pl.col('account_code').alias('account'),
        pl.col('period_code').str.strptime(pl.Date, '%Y-%m').alias('date'),
        pl.col('amount_sar').alias('debit').map_elements(lambda x: x if x > 0 else 0),
        pl.col('amount_sar').alias('credit').map_elements(lambda x: abs(x) if x < 0 else 0),
        pl.lit('EFIR Budget').alias('ref'),
    ])

    # Export to CSV
    csv_bytes = odoo_format.write_csv().encode('utf-8')

    return csv_bytes
```

**Benefits**:
- ⚡ **10-100x faster** than Pandas/Python loops
- 📊 **Complex Excel exports**: Multiple sheets, formatting, formulas
- 🔄 **Odoo/Skolengo integration**: Fast CSV transformations
- 💼 **Board presentations**: Professional financial statements

---

## 7. Technology Stack

### 7.1 New Frontend Dependencies

```json
{
  "dependencies": {
    // State management
    "zustand": "^5.0.0",              // Lightweight global state
    "immer": "^10.0.0",               // Immutable updates

    // Error handling
    "react-error-boundary": "^4.1.0", // Error boundaries
    "@sentry/react": "^8.40.0",       // Error tracking
    "sonner": "^1.7.0",               // Toast notifications

    // Monitoring
    "@tanstack/react-query-devtools": "^5.55.0"
  },
  "devDependencies": {
    "rollup-plugin-visualizer": "^5.12.0"  // Bundle analysis
  }
}
```

### 7.2 New Backend Dependencies

```toml
[project.dependencies]
# Caching
redis = ">=5.2.0"
hiredis = ">=3.0.0"                     # Redis C bindings for speed
cashews = { version = ">=7.0", extras = ["redis"] }

# Performance
orjson = ">=3.10.0"                     # 10x faster JSON

# Logging & Monitoring
structlog = ">=24.4.0"                  # Structured logging
prometheus-fastapi-instrumentator = ">=7.0.0"
sentry-sdk = { version = ">=2.19.0", extras = ["fastapi"] }

# Data Processing
polars = ">=1.15.0"                     # Fast DataFrames
duckdb = ">=1.1.0"                      # Embedded OLAP
pyarrow = ">=18.0.0"                    # Columnar data
```

### 7.3 Infrastructure

| Component | Version | Purpose | Cost |
|-----------|---------|---------|------|
| PostgreSQL | 17.x | Primary database (via Supabase) | Included |
| Redis | 7.x | Caching layer | ~$30/month |
| Supabase | Latest | Auth, Realtime, RLS | Included |

---

## 8. Implementation Phases

### Phase 1: Foundation & Error Handling (Weeks 1-3)
**Goal**: Production-ready observability

**Tasks**:
- [ ] Add React Error Boundary to root component
- [ ] Configure Sentry (frontend + backend)
- [ ] Implement structlog for backend logging
- [ ] Add correlation IDs to all requests
- [ ] Create standardized error response format
- [ ] Implement health check endpoints (/health/live, /health/ready)
- [ ] Add Prometheus metrics for DHG calculations
- [ ] Test error tracking end-to-end

**Deliverables**:
- ✅ All errors tracked in Sentry
- ✅ Correlation IDs for debugging cascading calculations
- ✅ Health checks for deployment
- ✅ Metrics dashboard (Grafana or Prometheus UI)

**Testing**:
- Trigger various errors and verify Sentry capture
- Test correlation ID flow through enrollment → DHG → costs
- Load test health check endpoints

---

### Phase 2: Performance Optimizations (Weeks 4-7)
**Goal**: 10-100x faster calculations and dashboards

**Tasks**:
**Week 4-5: Caching**
- [ ] Set up Redis (Docker for local, managed for production)
- [ ] Implement caching for DHG calculations (1 hour TTL)
- [ ] Implement caching for KPI dashboard (5 minutes TTL)
- [ ] Build cache invalidation system with dependency tracking
- [ ] Test cache invalidation cascade (enrollment → DHG → KPIs)

**Week 6: Database Optimization**
- [ ] Create materialized view for KPI dashboard
- [ ] Add partial indexes for active/approved data
- [ ] Implement materialized view refresh strategy
- [ ] Analyze slow queries and add indexes

**Week 7: Frontend Performance**
- [ ] Configure React Query with optimal settings
- [ ] Implement Vite chunk splitting
- [ ] Add bundle analyzer
- [ ] Test bundle sizes and load times

**Deliverables**:
- ✅ DHG calculation time: <1 second (vs 3-5 seconds before)
- ✅ Dashboard load time: <2 seconds (vs 5-8 seconds before)
- ✅ Initial bundle: <300kb gzipped

**Testing**:
- Load test with realistic EFIR data (~1,875 students)
- Measure DHG calculation time before/after caching
- Test cache invalidation when enrollment changes

---

### Phase 3: Real-Time Writeback Core (Weeks 8-11)
**Goal**: Multi-user collaboration with instant save

**Tasks**:
**Week 8: Database Schema**
- [ ] Create planning_cells table
- [ ] Create cell_changes table (change log)
- [ ] Add indexes and RLS policies
- [ ] Enable Supabase Realtime on planning_cells

**Week 9-10: Frontend Implementation**
- [ ] Build usePlanningWriteback hook
- [ ] Implement optimistic updates
- [ ] Build useRealtimeSync hook for Supabase Realtime
- [ ] Integrate with AG Grid (onCellValueChanged)
- [ ] Add conflict resolution (last-write-wins with notification)

**Week 11: Undo/Redo**
- [ ] Implement session-based undo stack
- [ ] Add undo/redo UI buttons
- [ ] Test undo/redo across different modules
- [ ] Add keyboard shortcuts (Ctrl+Z, Ctrl+Y)

**Deliverables**:
- ✅ Instant cell save (no "Save" button needed)
- ✅ Multi-user sync (see others' changes in real-time)
- ✅ Optimistic updates (UI updates immediately)
- ✅ Undo/redo with change log

**Testing**:
- Multi-user test: 2-3 users editing simultaneously
- Test conflict resolution
- Test undo/redo for various change types
- Test Realtime sync across different browsers

---

### Phase 4: Spreading & Exports (Weeks 12-15)
**Goal**: Efficient data entry and fast exports

**Tasks**:
**Week 12-13: Spreading Engine**
- [ ] Implement spreading service (equal, proportional, seasonal)
- [ ] Build SpreadingDialog component
- [ ] Add spreading API endpoint
- [ ] Integrate with AG Grid context menu
- [ ] Test EFIR-specific seasonal pattern

**Week 14-15: Fast Exports**
- [ ] Set up DuckDB integration
- [ ] Implement financial statements export (Excel, multiple sheets)
- [ ] Build Odoo import format transformer (Polars)
- [ ] Create Skolengo export format
- [ ] Add export progress indicators

**Deliverables**:
- ✅ Spreading: Equal, proportional, EFIR seasonal
- ✅ Excel exports: <2 seconds for full financial statements
- ✅ Odoo/Skolengo formats ready for import

**Testing**:
- Test spreading with annual budget values
- Verify seasonal pattern matches EFIR school year
- Performance test exports with full budget data
- Validate Odoo/Skolengo import files

---

### Phase 5: Polish & Production Readiness (Weeks 16-18)
**Goal**: Quality assurance and deployment

**Tasks**:
**Week 16: Cell Comments (Optional)**
- [ ] Create cell_comments table
- [ ] Build CommentsDialog component
- [ ] Add comment indicators in grid
- [ ] Test comment threading

**Week 17: E2E Testing**
- [ ] Write Playwright tests for critical flows
  - Enrollment → DHG → Costs cascade
  - Real-time multi-user editing
  - Undo/redo workflow
  - Spreading operations
- [ ] Performance testing with 1,875 students
- [ ] Load testing with 10 concurrent users

**Week 18: Documentation & Training**
- [ ] Update user documentation
- [ ] Create admin guide (Redis, monitoring)
- [ ] Record training videos
- [ ] Prepare go-live checklist

**Deliverables**:
- ✅ All E2E tests passing
- ✅ Performance targets met
- ✅ Documentation complete
- ✅ Ready for production deployment

---

## 9. Success Metrics

### 9.1 Performance Metrics

| Metric | Baseline | Target | Method |
|--------|----------|--------|--------|
| **DHG Calculation Time** | 3-5 sec | <1 sec | Redis caching |
| **Dashboard Load** | 5-8 sec | <2 sec | Materialized views |
| **Grid Render** | 1-2 sec | <500ms | React Query + chunk splitting |
| **Excel Export** | 10-15 sec | <2 sec | DuckDB/Polars |
| **API Response (p95)** | N/A | <200ms | Caching + indexes |
| **Initial Bundle Size** | N/A | <300kb | Code splitting |

### 9.2 Reliability Metrics

| Metric | Target |
|--------|--------|
| **Error Rate** | <0.1% of requests |
| **Uptime** | 99.9% |
| **Cache Hit Rate** | >80% for DHG |
| **Time to Detect Errors** | <5 minutes (Sentry alerts) |

### 9.3 User Experience Metrics

| Metric | Baseline (Excel) | Target (EFIR App) |
|--------|------------------|-------------------|
| **Time to Create Budget** | ~40 hours | <20 hours (-50%) |
| **Version Conflicts** | ~5-10 per budget cycle | 0 (eliminated) |
| **Collaboration** | Email/file sharing | Real-time in-app |
| **Undo Changes** | Manual file versioning | Instant undo/redo |
| **User Satisfaction** | N/A | >4.5/5 |

### 9.4 Business Impact

| Metric | Expected Impact |
|--------|-----------------|
| **Budget Planning Cycle Time** | -50% (from 6 weeks to 3 weeks) |
| **Errors in Budget** | -80% (automated calculations) |
| **Board Approval Time** | -30% (clear audit trail, professional reports) |
| **DHG Compliance** | 100% (enforced validation rules) |

---

## 10. Risks & Mitigation

### 10.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| **Redis infrastructure complexity** | High | Medium | Use managed Redis (Upstash, Railway), monitor carefully |
| **Realtime sync conflicts** | Medium | Medium | Last-write-wins with notifications, clear conflict UI |
| **Cache invalidation bugs** | High | Low | Comprehensive testing of dependency graph, fallback to DB |
| **Performance under load** | Medium | Low | Load testing before launch, scale Redis if needed |

### 10.2 Schedule Risks

| Risk | Impact | Mitigation |
|------|--------|-----------|
| **Underestimated complexity** | +2-4 weeks | Built in 30% buffer (13-18 weeks range) |
| **Dependency on Supabase Realtime** | Blocker | Test Realtime early (Week 8), have fallback (polling) |
| **Redis setup issues** | 1 week delay | Use Docker for local, managed service for prod |

### 10.3 Adoption Risks

| Risk | Mitigation |
|------|-----------|
| **Users prefer Excel** | Training, emphasize collaboration benefits |
| **Learning curve** | Intuitive UI, keyboard shortcuts, video tutorials |
| **Resistance to change** | Pilot with Finance Director first, collect feedback |

---

## 11. Go-Live Checklist

### Pre-Launch (2 weeks before)
- [ ] All tests passing (unit, integration, E2E)
- [ ] Performance benchmarks met
- [ ] Redis configured in production
- [ ] Sentry configured with alerts
- [ ] Materialized view refresh scheduled
- [ ] Backup strategy in place
- [ ] Rollback plan documented

### Week of Launch
- [ ] User training sessions completed
- [ ] Admin training completed
- [ ] Data migration tested
- [ ] Load testing passed
- [ ] Health checks verified
- [ ] Monitoring dashboards configured

### Launch Day
- [ ] Deploy to production
- [ ] Verify health checks
- [ ] Monitor Sentry for errors
- [ ] Monitor Redis performance
- [ ] Stand by for user support

### Post-Launch (1 week after)
- [ ] Collect user feedback
- [ ] Review performance metrics
- [ ] Address any bugs
- [ ] Plan Phase 2 enhancements

---

## 12. Future Enhancements (V2)

**After successful V1 launch and user feedback**:

### High Priority (if requested)
- [ ] Cell locking mechanism
- [ ] Advanced spreading (trend-based, custom formulas)
- [ ] Allocation engine (top-down, bottom-up)
- [ ] Mobile-responsive UI
- [ ] Email notifications for budget approvals

### Medium Priority
- [ ] Scenario comparison (side-by-side view)
- [ ] Advanced dashboards with Recharts
- [ ] Bulk import from Excel
- [ ] API for external integrations

### Low Priority (only if multi-school)
- [ ] Multi-organization support
- [ ] Custom dimensions
- [ ] Formula engine
- [ ] Role-based permissions (beyond RLS)

---

## Appendix A: Technology Decision Matrix

| Technology | Considered | Chosen | Reason |
|------------|-----------|--------|--------|
| **Caching** | Redis, In-memory, Memcached | ✅ Redis | Proven, Supabase-compatible, pub/sub for invalidation |
| **Analytics** | Cube.js, dbt, PostgreSQL views | ✅ PostgreSQL views | Simpler, sufficient for 50 users |
| **Exports** | Pandas, Polars, DuckDB | ✅ Polars + DuckDB | 10-100x faster than Pandas |
| **Error Tracking** | Sentry, Rollbar, Bugsnag | ✅ Sentry | Industry standard, great React integration |
| **Metrics** | Prometheus, Datadog, New Relic | ✅ Prometheus | Open source, FastAPI integration |
| **Architecture** | Metadata-driven, Fixed schema | ✅ Fixed schema | EFIR structure is rigid (DHG, PCG, AEFE) |

---

## Appendix B: Comparison with Original Roadmap

| Feature | Original Roadmap | Focused Roadmap | Change |
|---------|------------------|-----------------|--------|
| **Error Handling** | ✅ Included | ✅ Included | ✅ Same |
| **Performance** | ✅ Included | ✅ Included | ✅ Same |
| **Metadata Architecture** | ✅ 6-9 weeks | ❌ Removed | ⚠️ **Removed** (4-5 months saved) |
| **Formula Engine** | ✅ 4-6 weeks | ❌ Removed | ⚠️ **Removed** (security + complexity) |
| **Real-Time Writeback** | ✅ Included | ✅ Included | ✅ Same (prioritized) |
| **Spreading** | ✅ Included | ✅ Included (simplified) | 🟡 Basic only (equal, seasonal) |
| **Cube.js/dbt** | ✅ Suggested | ❌ Removed | ⚠️ **Use PostgreSQL views** |
| **Timeline** | 22-30 weeks | 13-18 weeks | ✅ **40% faster** |
| **Complexity** | 🔴 Very High | 🟡 Medium | ✅ **Lower risk** |

**Net Result**: 80% of value in 50% of time, with significantly lower risk.

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 2.0 | 2025-12-02 | Claude | Focused roadmap - removed metadata architecture, formula engine |
| 1.0 | 2025-12-02 | Claude | Initial draft (generic SAC-like platform) |

---

**Ready to implement? Let's make EFIR Budget App the best DHG planning tool for French schools! 🚀**
