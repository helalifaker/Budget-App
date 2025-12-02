# EFIR Budget App - Technical Enhancement Roadmap

**Version:** 1.0
**Date:** December 2025
**Status:** Draft for Review

---

## Executive Summary

This document outlines technical enhancements to transform the EFIR Budget Planning Application into a flexible, enterprise-grade planning platform with SAP Analytics Cloud (SAC)-like capabilities, including real-time writeback, dynamic dimensions, and formula-driven calculations.

---

## Table of Contents

1. [Error Handling & Observability](#1-error-handling--observability)
2. [Performance Optimizations](#2-performance-optimizations)
3. [Data Treatment & Analytics](#3-data-treatment--analytics)
4. [Metadata-Driven Architecture](#4-metadata-driven-architecture)
5. [Real-Time Writeback (SAC-Style)](#5-real-time-writeback-sac-style)
6. [Technology Requirements](#6-technology-requirements)
7. [Implementation Phases](#7-implementation-phases)

---

## 1. Error Handling & Observability

### 1.1 Frontend Error Handling

| Feature | Description | Priority |
|---------|-------------|----------|
| React Error Boundary | Global error boundary to prevent app crashes | 🔴 High |
| Error Tracking (Sentry) | Production error monitoring with source maps | 🔴 High |
| Toast Notifications | User-friendly error messages | 🟡 Medium |
| Offline Detection | Handle network failures gracefully | 🟢 Low |

**Required Packages:**
```json
{
  "react-error-boundary": "^4.1.0",
  "@sentry/react": "^8.40.0",
  "sonner": "^1.7.0"
}
```

### 1.2 Backend Logging & Monitoring

| Feature | Description | Priority |
|---------|-------------|----------|
| Structured Logging | JSON-formatted logs with correlation IDs | 🔴 High |
| Global Exception Handler | Consistent API error responses | 🔴 High |
| Metrics/Monitoring | Prometheus metrics for performance tracking | 🟡 Medium |
| Health Checks | Liveness and readiness endpoints | 🟡 Medium |

**Required Packages:**
```toml
structlog = ">=24.4.0"
prometheus-fastapi-instrumentator = ">=7.0.0"
```

### 1.3 Error Response Format

Standardized error response structure:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Class size exceeds maximum limit",
    "details": {
      "field": "max_class_size",
      "value": 35,
      "constraint": "max_class_size <= 30"
    },
    "correlation_id": "req_abc123",
    "timestamp": "2025-12-02T10:30:00Z"
  }
}
```

---

## 2. Performance Optimizations

### 2.1 Frontend Performance

| Feature | Description | Priority |
|---------|-------------|----------|
| React Query Configuration | Stale time, GC time, retry policies | 🔴 High |
| Vite Chunk Splitting | Separate bundles for AG Grid, Recharts | 🔴 High |
| React Query DevTools | Debug queries in development | 🟡 Medium |
| Bundle Analysis | Monitor bundle size | 🟡 Medium |

**React Query Configuration:**
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,      // 5 minutes
      gcTime: 30 * 60 * 1000,         // 30 minutes
      retry: 2,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

**Vite Chunk Splitting:**
```typescript
build: {
  rollupOptions: {
    output: {
      manualChunks: {
        'ag-grid': ['ag-grid-community', 'ag-grid-react'],
        'charts': ['recharts'],
        'vendor': ['react', 'react-dom'],
        'supabase': ['@supabase/supabase-js'],
      }
    }
  }
}
```

### 2.2 Backend Performance

| Feature | Description | Priority |
|---------|-------------|----------|
| Redis Caching | Cache DHG calculations, KPIs | 🔴 High |
| orjson Serialization | 10x faster JSON responses | 🟡 Medium |
| Connection Pooling | Optimize database connections | 🟡 Medium |
| Async Everywhere | Ensure all I/O is non-blocking | 🟡 Medium |

**Required Packages:**
```toml
redis = ">=5.2.0"
hiredis = ">=3.0.0"
orjson = ">=3.10.0"
cashews = { version = ">=7.0", extras = ["redis"] }
```

**Caching Strategy:**

| Data Type | TTL | Invalidation Trigger |
|-----------|-----|---------------------|
| DHG Calculations | 1 hour | Class structure change |
| KPI Values | 24 hours | Budget approval |
| Dashboard Widgets | 5 minutes | Manual refresh |
| Budget Consolidation | Permanent | Version-keyed |
| Exchange Rates | 1 hour | External API |

### 2.3 Database Performance

| Feature | Description | Priority |
|---------|-------------|----------|
| Materialized Views | Pre-compute KPIs, aggregations | 🔴 High |
| Partial Indexes | Index only active/approved data | 🔴 High |
| BRIN Indexes | Time-series data optimization | 🟡 Medium |
| Query Optimization | Analyze slow queries | 🟡 Medium |

**Materialized Views:**
```sql
-- KPI Summary View
CREATE MATERIALIZED VIEW efir_budget.mv_kpi_summary AS
SELECT
    bv.id as budget_version_id,
    bv.fiscal_year,
    bv.status,
    COUNT(DISTINCT ed.student_id) as total_students,
    SUM(dhg.total_hours) as total_dhg_hours,
    SUM(pc.amount_sar) as total_personnel_costs,
    SUM(rv.amount_sar) as total_revenue
FROM efir_budget.budget_versions bv
LEFT JOIN efir_budget.enrollment_data ed ON ed.budget_version_id = bv.id
LEFT JOIN efir_budget.dhg_calculations dhg ON dhg.budget_version_id = bv.id
LEFT JOIN efir_budget.personnel_costs pc ON pc.budget_version_id = bv.id
LEFT JOIN efir_budget.revenue_projections rv ON rv.budget_version_id = bv.id
GROUP BY bv.id, bv.fiscal_year, bv.status
WITH DATA;

CREATE UNIQUE INDEX ON efir_budget.mv_kpi_summary(budget_version_id);
REFRESH MATERIALIZED VIEW CONCURRENTLY efir_budget.mv_kpi_summary;
```

**Partial Indexes:**
```sql
-- Only index approved budgets for dashboard queries
CREATE INDEX ix_budget_versions_approved
ON efir_budget.budget_versions(fiscal_year, status)
WHERE status = 'approved';

-- Only index material variances for alerts
CREATE INDEX ix_variance_material
ON efir_budget.budget_vs_actual(budget_version_id, period)
WHERE is_material = true;

-- Index active dimension members only
CREATE INDEX ix_dimension_members_active
ON efir_budget.dimension_members(dimension_id, code)
WHERE is_active = true;
```

---

## 3. Data Treatment & Analytics

### 3.1 Semantic Layer / OLAP Options

| Option | Use Case | Complexity |
|--------|----------|------------|
| **Cube.js** | Full semantic layer with caching | 🔴 High |
| **dbt** | Data transformations + documentation | 🟡 Medium |
| **PostgreSQL Views** | Simple aggregations | 🟢 Low |

**Cube.js Benefits for EFIR:**
- Pre-aggregations for DHG hours by subject/level
- Consistent KPI definitions across dashboards
- API-level caching
- Multi-tenant data isolation

### 3.2 In-Memory Analytics

| Tool | Purpose | Priority |
|------|---------|----------|
| DuckDB | Embedded OLAP for reports/exports | 🟡 Medium |
| PyArrow | Columnar data for fast aggregations | 🟡 Medium |
| Polars | 10-100x faster data transformations | 🟡 Medium |

**Required Packages:**
```toml
duckdb = ">=1.1.0"
pyarrow = ">=18.0.0"
polars = ">=1.15.0"
```

**Use Cases:**
- Generate financial statements without hitting PostgreSQL
- Fast Excel/CSV exports with complex calculations
- Odoo/Skolengo import transformations

### 3.3 Calculation Engine Optimizations

| Feature | Description | Priority |
|---------|-------------|----------|
| Numba JIT | Compile numeric loops | 🟢 Optional |
| Database Aggregations | Push calculations to PostgreSQL | 🟡 Medium |
| Batch Processing | Process multiple cells together | 🟡 Medium |

---

## 4. Metadata-Driven Architecture

### 4.1 Overview

Transform from rigid schema to flexible, configuration-driven model:

```
Traditional:                    Metadata-Driven:
┌─────────────────┐            ┌─────────────────────────┐
│ accounts        │            │ dimensions              │
│ cost_centers    │   ──►      │ dimension_members       │
│ periods         │            │ planning_facts          │
│ (fixed tables)  │            │ (flexible structure)    │
└─────────────────┘            └─────────────────────────┘
```

### 4.2 Dimension Registry

**Purpose:** Allow users to create custom dimensions (accounts, cost centers, projects) without code changes.

```sql
-- Dimension definitions
CREATE TABLE efir_budget.dimensions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_fr VARCHAR(200),
    dimension_type VARCHAR(50) NOT NULL,
    -- Types: 'account', 'time', 'organization', 'version', 'custom'

    parent_dimension_id UUID REFERENCES dimensions(id),

    -- Flexible schema
    attributes_schema JSONB DEFAULT '{}',
    -- Example: {"has_hierarchy": true, "max_depth": 4}

    validation_rules JSONB DEFAULT '{}',
    -- Example: {"code_pattern": "^[0-9]{5}$", "required_fields": ["name"]}

    -- Protection
    is_system BOOLEAN DEFAULT false,
    is_editable BOOLEAN DEFAULT true,

    -- Audit
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Dimension members (hierarchy nodes)
CREATE TABLE efir_budget.dimension_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    dimension_id UUID NOT NULL REFERENCES dimensions(id) ON DELETE CASCADE,

    code VARCHAR(100) NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_fr VARCHAR(200),

    -- Hierarchy
    parent_member_id UUID REFERENCES dimension_members(id),
    level_depth INT DEFAULT 0,
    path LTREE, -- For efficient hierarchy queries

    -- Flexible attributes
    attributes JSONB DEFAULT '{}',
    -- Example for Account: {"account_type": "expense", "is_detail": true}

    -- Display
    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,

    -- Constraints
    UNIQUE(dimension_id, code),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX ix_dim_members_dimension ON efir_budget.dimension_members(dimension_id);
CREATE INDEX ix_dim_members_parent ON efir_budget.dimension_members(parent_member_id);
CREATE INDEX ix_dim_members_path ON efir_budget.dimension_members USING GIST(path);
```

### 4.3 Planning Facts Table

**Purpose:** Store all planning values with flexible dimension keys.

```sql
CREATE TABLE efir_budget.planning_facts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_version_id UUID NOT NULL REFERENCES budget_versions(id),

    -- Flexible dimension keys (JSONB)
    dimension_keys JSONB NOT NULL,
    -- Example: {"account": "60110", "period": "2025-01", "cost_center": "teaching"}

    -- Value storage
    value NUMERIC(18,4),
    value_type VARCHAR(30) DEFAULT 'amount',
    -- Types: 'amount', 'quantity', 'rate', 'percentage', 'text'

    -- Formula support
    is_calculated BOOLEAN DEFAULT false,
    formula TEXT,
    -- Example: "=SUM(children)" or "=[revenue] - [costs]"

    -- Metadata
    metadata JSONB DEFAULT '{}',
    -- Example: {"source": "import", "confidence": 0.95}

    -- Audit
    modified_by UUID REFERENCES auth.users(id),
    modified_at TIMESTAMPTZ DEFAULT NOW(),

    -- Optimistic locking
    version INT DEFAULT 1,

    -- Constraints
    UNIQUE(budget_version_id, dimension_keys)
);

-- GIN index for JSONB queries
CREATE INDEX ix_facts_dimension_keys ON efir_budget.planning_facts
    USING GIN(dimension_keys jsonb_path_ops);

-- Composite index for common queries
CREATE INDEX ix_facts_version_keys ON efir_budget.planning_facts(budget_version_id, dimension_keys);
```

### 4.4 Variable & Formula Engine

**Purpose:** Allow users to define custom calculations without code.

```sql
CREATE TABLE efir_budget.variables (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    name_fr VARCHAR(200),
    description TEXT,

    -- Variable type
    variable_type VARCHAR(50) NOT NULL,
    -- Types: 'input', 'calculated', 'lookup', 'driver'

    data_type VARCHAR(50) NOT NULL,
    -- Types: 'number', 'currency', 'percentage', 'integer', 'text', 'date'

    -- For calculated variables
    formula TEXT,
    -- Example: "[tuition_rate] * [enrollment_count]"
    -- Example: "SUM([revenue]) - SUM([costs])"

    -- Dimension applicability
    applies_to_dimensions JSONB DEFAULT '[]',
    -- Example: ["account", "period"] - this variable exists per account-period combination

    -- Default value
    default_value JSONB,

    -- Validation
    validation_rules JSONB DEFAULT '{}',
    -- Example: {"min": 0, "max": 1000000, "required": true}

    -- Display
    format_pattern VARCHAR(50),
    -- Example: "#,##0.00", "0.0%"

    sort_order INT DEFAULT 0,
    is_active BOOLEAN DEFAULT true,

    -- Audit
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Variable dependencies for calculation order
CREATE TABLE efir_budget.variable_dependencies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    variable_id UUID NOT NULL REFERENCES variables(id) ON DELETE CASCADE,
    depends_on_variable_id UUID NOT NULL REFERENCES variables(id),
    UNIQUE(variable_id, depends_on_variable_id)
);
```

### 4.5 Dynamic UI Generation

**AG Grid Dynamic Columns:**
```typescript
interface DimensionConfig {
  code: string;
  name: string;
  dataType: 'number' | 'currency' | 'percentage' | 'text';
  editable: boolean;
  validationRules?: ValidationRule[];
}

function generateColumnDefs(dimensions: DimensionConfig[]): ColDef[] {
  return dimensions.map(dim => ({
    field: dim.code,
    headerName: dim.name,
    editable: dim.editable,
    cellEditor: getCellEditor(dim.dataType),
    valueFormatter: getValueFormatter(dim.dataType),
    valueParser: getValueParser(dim.dataType),
    cellClass: dim.editable ? 'editable-cell' : 'readonly-cell',
  }));
}
```

---

## 5. Real-Time Writeback (SAC-Style)

### 5.1 Feature Overview

| SAC Feature | Description | Implementation |
|-------------|-------------|----------------|
| Instant Cell Save | Edit cell, save immediately | AG Grid + Supabase |
| Multi-User Sync | See others' changes in real-time | Supabase Realtime |
| Undo/Redo | Revert changes with history | AG Grid + Change Log |
| Cell Comments | Annotate cells with notes | Custom renderer + table |
| Cell Locking | Prevent edits to specific cells | RLS + metadata |
| Spreading | Distribute values across periods | Custom formula engine |
| Allocation | Top-down/bottom-up distribution | Custom formula engine |
| Data Actions | Automated calculations on change | Backend triggers |

### 5.2 Planning Cells Table

```sql
CREATE TABLE efir_budget.planning_cells (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    budget_version_id UUID NOT NULL REFERENCES budget_versions(id),

    -- Dimension keys
    dimension_keys JSONB NOT NULL,

    -- Value
    value NUMERIC(18,4),
    value_type VARCHAR(30) DEFAULT 'input',
    -- Types: 'input', 'calculated', 'spread', 'allocated', 'imported'

    -- Formula (for calculated cells)
    formula TEXT,
    formula_references JSONB DEFAULT '[]',
    -- Stores cell references for dependency tracking

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

    UNIQUE(budget_version_id, dimension_keys)
);

-- Enable Supabase Realtime
ALTER PUBLICATION supabase_realtime ADD TABLE efir_budget.planning_cells;
```

### 5.3 Cell Comments

```sql
CREATE TABLE efir_budget.cell_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cell_id UUID NOT NULL REFERENCES planning_cells(id) ON DELETE CASCADE,

    comment_text TEXT NOT NULL,

    -- Threading
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
```

### 5.4 Change Log (Undo/Redo Support)

```sql
CREATE TABLE efir_budget.cell_changes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cell_id UUID REFERENCES planning_cells(id) ON DELETE SET NULL,

    -- Change details
    old_value NUMERIC(18,4),
    new_value NUMERIC(18,4),
    change_type VARCHAR(50) NOT NULL,
    -- Types: 'manual', 'spread', 'allocation', 'formula', 'import', 'undo', 'redo'

    -- Session tracking (for grouped undo)
    session_id UUID NOT NULL,
    sequence_number INT NOT NULL,

    -- Audit
    changed_by UUID REFERENCES auth.users(id),
    changed_at TIMESTAMPTZ DEFAULT NOW(),

    -- Additional context
    context JSONB DEFAULT '{}'
    -- Example: {"spread_method": "equal", "source_cell": "uuid"}
);

CREATE INDEX ix_cell_changes_cell ON efir_budget.cell_changes(cell_id);
CREATE INDEX ix_cell_changes_session ON efir_budget.cell_changes(session_id, sequence_number);
```

### 5.5 Spreading & Allocation Engine

**Spread Methods:**

| Method | Description | Formula |
|--------|-------------|---------|
| Equal | Distribute evenly | `value / period_count` |
| Proportional | Based on existing ratios | `value * (period_value / total)` |
| Trend | Apply growth rate | `base * (1 + rate)^n` |
| Seasonal | Based on seasonal pattern | `value * seasonal_factor[period]` |
| Custom | User-defined weights | `value * weight[period] / sum(weights)` |

**Allocation Methods:**

| Method | Description | Direction |
|--------|-------------|-----------|
| Top-Down | Parent to children | Distribute parent value to children |
| Bottom-Up | Children to parent | Aggregate children to parent |
| Cross-Dim | Across dimensions | Allocate across cost centers |

### 5.6 Frontend Writeback Hook

```typescript
// hooks/usePlanningWriteback.ts
interface WritebackConfig {
  budgetVersionId: string;
  onOptimisticUpdate: (cellKey: string, value: number) => void;
  onRemoteChange: (cell: PlanningCell) => void;
  onError: (error: Error, cellKey: string) => void;
}

interface WritebackResult {
  updateCell: (cellKey: string, value: number) => Promise<void>;
  spreadValues: (config: SpreadConfig) => Promise<void>;
  undo: () => Promise<void>;
  redo: () => Promise<void>;
  canUndo: boolean;
  canRedo: boolean;
}

function usePlanningWriteback(config: WritebackConfig): WritebackResult {
  // Implementation with:
  // 1. Optimistic updates
  // 2. Debounced persistence
  // 3. Conflict resolution
  // 4. Undo/redo stack
  // 5. Supabase Realtime subscription
}
```

---

## 6. Technology Requirements

### 6.1 Frontend Packages

```json
{
  "dependencies": {
    "react": "19.2.0",
    "react-dom": "19.2.0",
    "@tanstack/react-query": "5.55.4",
    "ag-grid-community": "34.3.1",
    "ag-grid-react": "34.3.1",
    "@supabase/supabase-js": "~2.86.0",

    "zustand": "^5.0.0",
    "immer": "^10.0.0",
    "react-error-boundary": "^4.1.0",
    "@sentry/react": "^8.40.0",
    "sonner": "^1.7.0",

    "@rjsf/core": "^5.x",
    "@rjsf/validator-ajv8": "^5.x",
    "expr-eval": "^2.0.0",

    "react-router-dom": "^7.0.0",
    "@tanstack/react-query-devtools": "^5.55.0"
  },
  "devDependencies": {
    "msw": "^2.6.0",
    "rollup-plugin-visualizer": "^5.12.0"
  }
}
```

### 6.2 Backend Packages

```toml
[project.dependencies]
# Core
fastapi = "0.123.0"
uvicorn = { version = "0.34.0", extras = ["standard"] }
pydantic = "2.12.0"

# Database
sqlalchemy = "2.0.36"
asyncpg = "0.30.0"

# Caching
redis = ">=5.2.0"
hiredis = ">=3.0.0"
cashews = { version = ">=7.0", extras = ["redis"] }

# Performance
orjson = ">=3.10.0"

# Logging & Monitoring
structlog = ">=24.4.0"
prometheus-fastapi-instrumentator = ">=7.0.0"
sentry-sdk = { version = ">=2.19.0", extras = ["fastapi"] }

# Formula Engine
simpleeval = ">=1.0.0"
lark = ">=1.2.0"

# Data Processing
polars = ">=1.15.0"
duckdb = ">=1.1.0"
pyarrow = ">=18.0.0"

# Validation
jsonschema = ">=4.23.0"

[project.optional-dependencies]
dev = [
    "ruff>=0.8.2",
    "mypy>=1.14.1",
    "pytest>=8.3.3",
    "pytest-cov>=6.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.27.2"
]
```

### 6.3 Database Extensions

```sql
-- Required PostgreSQL extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "ltree";      -- For hierarchies
CREATE EXTENSION IF NOT EXISTS "pg_trgm";    -- For fuzzy search
CREATE EXTENSION IF NOT EXISTS "btree_gin";  -- For composite GIN indexes
```

### 6.4 Infrastructure Requirements

| Component | Requirement | Purpose |
|-----------|-------------|---------|
| PostgreSQL | 17.x | Primary database |
| Redis | 7.x | Caching layer |
| Supabase | Latest | Auth, Realtime, RLS |

---

## 7. Implementation Phases

### Phase 1: Foundation (Weeks 1-3)
**Focus:** Error handling, performance basics

- [ ] Add React Error Boundary
- [ ] Configure Sentry (frontend + backend)
- [ ] Add structlog for backend logging
- [ ] Configure React Query with optimal settings
- [ ] Implement Vite chunk splitting
- [ ] Add Redis caching for DHG calculations

### Phase 2: Database Optimization (Weeks 4-5)
**Focus:** Query performance

- [ ] Create materialized views for KPIs
- [ ] Add partial indexes for active data
- [ ] Implement BRIN indexes for time-series
- [ ] Set up materialized view refresh strategy

### Phase 3: Metadata Architecture (Weeks 6-9)
**Focus:** Dynamic dimensions

- [ ] Create dimensions and dimension_members tables
- [ ] Build Dimension Manager UI
- [ ] Migrate existing accounts to dimension model
- [ ] Implement dynamic AG Grid column generation
- [ ] Create planning_facts table with JSONB keys

### Phase 4: Formula Engine (Weeks 10-12)
**Focus:** User-defined calculations

- [ ] Create variables table
- [ ] Implement safe formula parser (simpleeval)
- [ ] Build Variable Builder UI
- [ ] Add formula validation and dependency tracking
- [ ] Implement recalculation engine

### Phase 5: Real-Time Writeback (Weeks 13-16)
**Focus:** SAC-style editing

- [ ] Create planning_cells table
- [ ] Enable Supabase Realtime
- [ ] Implement optimistic updates hook
- [ ] Add cell comments feature
- [ ] Implement undo/redo with change log
- [ ] Add cell locking mechanism

### Phase 6: Spreading & Allocation (Weeks 17-19)
**Focus:** Advanced data entry

- [ ] Implement spreading engine (equal, proportional, trend)
- [ ] Build spreading UI in AG Grid context menu
- [ ] Implement allocation engine (top-down, bottom-up)
- [ ] Add allocation wizard UI

### Phase 7: Polish & Testing (Weeks 20-22)
**Focus:** Quality assurance

- [ ] End-to-end testing with Playwright
- [ ] Performance testing with large datasets
- [ ] Multi-user concurrent editing tests
- [ ] Documentation and training materials

---

## Appendix A: Architecture Diagrams

### Current vs. Target Architecture

```
CURRENT STATE:
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend                                                  │
│  ├── Static forms                                               │
│  ├── Hard-coded grids                                           │
│  └── Manual API calls                                           │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Backend                                                 │
│  ├── Fixed endpoints per entity                                 │
│  ├── Hard-coded calculations                                    │
│  └── No caching                                                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL                                                      │
│  ├── Fixed schema                                               │
│  ├── No materialized views                                      │
│  └── Basic indexes                                              │
└─────────────────────────────────────────────────────────────────┘


TARGET STATE:
┌─────────────────────────────────────────────────────────────────┐
│  React Frontend                                                  │
│  ├── Dynamic forms (JSON Schema)                                │
│  ├── Metadata-driven grids                                      │
│  ├── Real-time writeback                                        │
│  ├── Optimistic updates                                         │
│  └── Error boundary + Sentry                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            ▼                 ▼                 ▼
┌───────────────────┐ ┌───────────────┐ ┌───────────────────────┐
│ Supabase Realtime │ │ Redis Cache   │ │ FastAPI Backend       │
│ (WebSocket)       │ │ (DHG, KPIs)   │ │ ├── Metadata engine   │
└───────────────────┘ └───────────────┘ │ ├── Formula engine    │
                              │         │ ├── Structured logging│
                              │         │ └── Prometheus metrics│
                              │         └───────────────────────┘
                              │                   │
                              ▼                   ▼
┌─────────────────────────────────────────────────────────────────┐
│  PostgreSQL + Supabase                                          │
│  ├── Dimension registry (flexible schema)                       │
│  ├── Planning facts (JSONB keys)                                │
│  ├── Materialized views (KPIs, aggregations)                    │
│  ├── Partial + BRIN indexes                                     │
│  ├── RLS policies                                               │
│  └── Realtime enabled                                           │
└─────────────────────────────────────────────────────────────────┘
```

### Writeback Data Flow

```
User edits cell
       │
       ▼
┌──────────────────┐
│ AG Grid captures │
│ onCellValueChanged│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Optimistic Update│────►│ UI reflects      │
│ (instant)        │     │ change immediately│
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│ Validate value   │
│ (client-side)    │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Recalculate      │
│ dependents       │
│ (formulas, totals)│
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Persist to       │
│ Supabase         │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐     ┌──────────────────┐
│ Supabase Realtime│────►│ Other users see  │
│ broadcasts change│     │ update instantly │
└────────┬─────────┘     └──────────────────┘
         │
         ▼
┌──────────────────┐
│ Log change for   │
│ undo/redo        │
└──────────────────┘
```

---

## Appendix B: Glossary

| Term | Definition |
|------|------------|
| **Dimension** | A category for organizing data (e.g., Account, Period, Cost Center) |
| **Dimension Member** | A specific value within a dimension (e.g., "60110" in Account) |
| **Fact** | A measurable value at the intersection of dimensions |
| **Writeback** | Saving changes directly from the grid to the database |
| **Spreading** | Distributing a value across multiple periods |
| **Allocation** | Distributing a value across a hierarchy |
| **Optimistic Update** | Updating UI before server confirms the change |
| **Materialized View** | Pre-computed query results stored in database |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-02 | Claude | Initial draft |

