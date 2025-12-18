# EFIR Budget App - Database Golden Rules (DB Constitution)

**Created**: 2025-12-14
**Status**: ACTIVE - All new tables and migrations MUST comply
**Applies To**: All tables in `efir_budget` schema

---

## Overview

This document establishes the **non-negotiable rules** for database design in the EFIR Budget Application. Every developer, migration, and code review must enforce these standards.

**Modules Covered**: Auth, Configuration, Planning, Enrollment Projection, Consolidation, Analysis, Strategic, Personnel, Cell/Audit

---

## 1. Non-Negotiables (Apply to Every Table)

### 1.1 Multi-Tenancy & Ownership

| Rule | Requirement |
|------|-------------|
| **MUST** | Every business table includes `organization_id` (FK → `admin_organizations.id`), unless it is a pure lookup shared globally (rare). |
| **MUST** | All queries are organization-scoped (enforced by RLS, not by application "good behavior"). |
| **MUST** | A row is owned by exactly one organization. No "shared rows" across orgs. |

**Exception**: Pure reference/lookup tables that are identical across all organizations (e.g., `ref_academic_cycles`, `ref_nationality_types`) may omit `organization_id`, but these must be explicitly documented and RLS must still be configured appropriately.

### 1.2 Primary Keys, Naming, and Standard Columns

| Rule | Requirement |
|------|-------------|
| **MUST** | Every table has a surrogate PK: `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` |
| **MUST** | FK columns are named `xxx_id` (e.g., `version_id`, `academic_cycle_id`), and **always indexed** |
| **MUST** | Use `snake_case` for all identifiers, plural table names, consistent prefixes for modules (or schemas) |
| **MUST** | Standard metadata on **all mutable business tables** (see below) |

#### Required Metadata Columns

```sql
-- Required on ALL mutable business tables
created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
created_by    UUID        REFERENCES auth.users(id),
updated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),
updated_by    UUID        REFERENCES auth.users(id)

-- Optional: Only if intentionally supporting soft delete
deleted_at    TIMESTAMPTZ
```

**Trigger Requirement**: Use a trigger to automatically update `updated_at` on row modification:

```sql
CREATE OR REPLACE FUNCTION efir_budget.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to each table
CREATE TRIGGER trg_<table_name>_updated_at
    BEFORE UPDATE ON efir_budget.<table_name>
    FOR EACH ROW
    EXECUTE FUNCTION efir_budget.update_updated_at();
```

### 1.3 One Migration Tool Only

| Rule | Requirement |
|------|-------------|
| **MUST** | Single migration authority: **Alembic** is the only migration tool for this project |
| **MUST** | All schema changes go through Alembic migrations in `backend/alembic/versions/` |
| **MUST** | Never make manual DDL changes to production without a corresponding migration |

---

## 2. Data Modeling Rules (Reduce Table Sprawl and Confusion)

### 2.1 Separate "Inputs" from "Outputs"

| Rule | Requirement |
|------|-------------|
| **MUST** | "Input" tables store **editable parameters/assumptions** (e.g., overrides, configs) |
| **MUST** | "Output" tables store **computed results only** (e.g., projections, consolidated statements) |
| **MUST** | Output rows carry **lineage** (see below) |

#### Required Lineage Columns for Output Tables

```sql
-- Required on ALL computed/output tables
computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
computed_by       UUID,                              -- Job ID or user ID
version_id        UUID NOT NULL,                     -- FK to settings_versions
fiscal_year       INT NOT NULL,                      -- Year this data represents

-- Optional but recommended
run_id            UUID,                              -- To reproduce/trace results
inputs_hash       VARCHAR(64)                        -- SHA256 of input parameters
```

**Input vs Output Classification**:

| Type | Examples | Characteristics |
|------|----------|-----------------|
| **Input** | `students_configs`, `students_data`, `settings_class_size_params`, `settings_fee_structure`, `students_overrides` | User-editable, source of truth for calculations |
| **Output** | `students_enrollment_projections`, `students_class_structures`, `teachers_dhg_requirements`, `finance_consolidations` | Computed by engines, read-only for users |

### 2.2 Version/Scenario is a First-Class Dimension Everywhere

| Rule | Requirement |
|------|-------------|
| **MUST** | Any planning/projection/analysis number is tied to `version_id` (FK to `settings_versions`) |
| **MUST** | If relevant, also include `scenario_id` |
| **MUST** | Period (year/term/month) must use a **consistent approach** across all tables |
| **MUST** | Avoid copying the same measure into multiple tables just because a module needs it |

**Standard Period Columns**:

```sql
-- Option A: Simple (recommended for annual planning)
fiscal_year   INT NOT NULL,
period        INT DEFAULT 0,  -- 0=annual, 1-12=monthly, 1-4=quarterly

-- Option B: Reference table (for complex period handling)
period_id     UUID REFERENCES efir_budget.periods(id)
```

### 2.3 Use "Dimensions + Facts" Thinking

| Type | Tables | Description |
|------|--------|-------------|
| **Dimensions** | `ref_academic_cycles`, `ref_academic_levels`, `ref_subjects`, `ref_teacher_categories`, `ref_fee_categories`, `ref_nationality_types`, `admin_organizations` | Stable reference data, rarely changes |
| **Facts** | `students_data`, `finance_data`, `insights_kpi_values` | Transactional/planning data, many rows |

| Rule | Requirement |
|------|-------------|
| **SHOULD** | Facts have **few columns, many rows** (keys + value), not many "wide" columns that multiply maintenance |
| **SHOULD** | Prefer tall/narrow fact tables over wide tables with many nullable columns |

### 2.4 Overrides Follow One Consistent Pattern

| Rule | Requirement |
|------|-------------|
| **MUST** | Each override table clearly states the **key it overrides** (same key columns as base) |
| **MUST** | Include **precedence** (`priority` or `scope_level` column) |
| **MUST** | Include **effective dates** if time-based: `effective_from`, `effective_to` |
| **SHOULD** | Include `reason` / `note` (optional but recommended) |

#### Standard Override Table Structure

```sql
CREATE TABLE efir_budget.<entity>_overrides (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id   UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),

    -- Key columns (what is being overridden)
    <entity>_id       UUID REFERENCES efir_budget.<entity>(id),

    -- Scope level for precedence
    scope_level       VARCHAR(20) NOT NULL,  -- 'global', 'level', 'grade'
    scope_key         VARCHAR(50),           -- The specific level/grade code if applicable

    -- Override values
    <field>_override  <type>,

    -- Precedence and validity
    priority          INT NOT NULL DEFAULT 0,  -- Higher = wins
    effective_from    DATE,
    effective_to      DATE,

    -- Documentation
    reason            TEXT,

    -- Standard metadata
    created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by        UUID REFERENCES auth.users(id),
    updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by        UUID REFERENCES auth.users(id),

    CONSTRAINT uk_<entity>_override UNIQUE(organization_id, <entity>_id, scope_level, scope_key)
);
```

#### Precedence Rules (Highest Wins)

```
Priority Order (highest → lowest):
1. Grade override    (scope_level = 'grade',  scope_key = 'CP')
2. Level override    (scope_level = 'level',  scope_key = 'elementaire')
3. Global override   (scope_level = 'global', scope_key = NULL)
4. Base/default      (no override row exists)
```

### 2.5 No "Mixed Responsibility" Tables

| Rule | Requirement |
|------|-------------|
| **MUST** | A table does **one job**: either configuration, planning input, computed output, audit, or UI preferences |
| **SHOULD** | Keep UI-only tables (`dashboard_*`, `user_preferences`) isolated from core finance logic |

**Table Responsibility Classification**:

| Responsibility | Examples | Can Reference | Can Be Referenced By |
|----------------|----------|---------------|----------------------|
| **Configuration** | `settings_system_configs`, `settings_fee_structure` | Dimensions | Planning, Output |
| **Planning Input** | `students_configs`, `students_overrides` | Configuration, Dimensions | Output |
| **Computed Output** | `students_enrollment_projections`, `finance_consolidations` | Everything | Analysis, UI |
| **Audit** | `admin_cell_changes`, `admin_cell_comments` | Planning, Output | Nothing |
| **UI Preferences** | `insights_dashboard_configs`, `insights_user_preferences` | Dimensions | Nothing |

### 2.6 Unified Versioning (CRITICAL PRINCIPLE)

| Rule | Requirement |
|------|-------------|
| **MUST** | All financial and planning data is versioned through `settings_versions` |
| **MUST** | Different data types (ACTUAL, BUDGET, FORECAST, STRATEGIC, WHAT_IF) are distinguished by `scenario_type`, **NOT by separate tables** |
| **MUST** | Do not create new “actual-only” fact tables; actuals are represented via `scenario_type='ACTUAL'` |
| **SHOULD** | Multi-year plans (STRATEGIC, FORECAST) use one version row with a start/end year (requires schema support; see note below) |
| **MUST** | Fact tables store data per year: `(version_id, fiscal_year)` - the `version_id` prevents year collisions |

#### Scenario Types

| Type | Description | Year Scope | Based On | Workflow |
|------|-------------|------------|----------|----------|
| **ACTUAL** | Imported actuals from Odoo GL | Single year | N/A | imported → validated → locked |
| **BUDGET** | Annual budget planning (N+1) | Single year | Previous BUDGET/ACTUAL | draft → submitted → approved → locked |
| **FORECAST** | Rolling forecast | Multi-year | BUDGET | draft → submitted → approved → archived |
| **STRATEGIC** | 5-Year strategic plan | Multi-year (5Y) | BUDGET | draft → submitted → approved → archived |
| **WHAT_IF** | Scenario analysis / simulations | Varies | Any version | draft → archived |

#### The `settings_versions` Table (formerly `budget_versions`)

```sql
CREATE TYPE efir_budget.scenario_type AS ENUM (
    'ACTUAL',      -- Imported from Odoo GL
    'BUDGET',      -- Annual budget planning
    'FORECAST',    -- Rolling forecast
    'STRATEGIC',   -- 5-Year strategic plan
    'WHAT_IF'      -- Scenario analysis
);

-- NOTE: Table renamed from `budget_versions` to `settings_versions` in Phase 3B.
-- FK column renamed from `budget_version_id` to `version_id` across all tables.
CREATE TABLE efir_budget.settings_versions (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id       UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),

    -- Identification
    name                  VARCHAR(100) NOT NULL,
    code                  VARCHAR(50),                -- "BUD-2025", "5Y-2024", "ACT-2024"

    -- Scenario classification
    scenario_type         scenario_type NOT NULL,

    -- Time scope
    fiscal_year           INT NOT NULL,               -- Start year (or only year)
    -- end_fiscal_year is a PLANNED field for multi-year versions (not currently implemented)

    -- Lineage: what was this based on?
    based_on_version_id   UUID REFERENCES efir_budget.settings_versions(id),

    -- Workflow
    status                version_status NOT NULL DEFAULT 'draft',

    -- For ACTUAL imports
    source_system         VARCHAR(50),                -- 'ODOO', 'SKOLENGO', 'MANUAL'
    import_batch_id       UUID,

    -- Standard metadata columns...

    -- Planned constraints for end_fiscal_year live with the planned column
);

-- Only ONE approved ACTUAL per org per year
CREATE UNIQUE INDEX uk_versions_actual_year
ON efir_budget.settings_versions(organization_id, fiscal_year)
WHERE scenario_type = 'ACTUAL' AND status IN ('approved', 'locked');

-- Only ONE approved BUDGET per org per year
CREATE UNIQUE INDEX uk_versions_budget_year
ON efir_budget.settings_versions(organization_id, fiscal_year)
WHERE scenario_type = 'BUDGET' AND status IN ('approved', 'locked');
```

#### Multi-Year Plan: How Year Collisions Are Prevented

**Problem**: Two 5Y plans may both contain year 2029. How do we prevent mixing?

**Solution**: Each plan is ONE version with a unique `version_id`. Fact tables use `(version_id, fiscal_year)`:

```
5Y Plan AAA (2025-2029):
├── fact_table: version_id=AAA, fiscal_year=2029  ← This 2029

5Y Plan BBB (2026-2030):
├── fact_table: version_id=BBB, fiscal_year=2029  ← Different 2029!
```

They never collide because `version_id` is the differentiator.

#### Data Origin Tracking for Multi-Year Plans

A 5Y plan may include inherited data (actuals, budget) plus projected data:

```sql
-- Add to fact tables that support multi-year plans
data_origin VARCHAR(20) DEFAULT 'input'
-- Values: 'input', 'inherited_actual', 'inherited_budget', 'projected', 'calculated'
```

#### Tables Deprecated by Unified Versioning

| Old Table | New Approach |
|-----------|--------------|
| `actual_data` | Use fact tables with `scenario_type='ACTUAL'` version |
| `budget_vs_actual` | VIEW comparing BUDGET and ACTUAL versions |
| `historical_actuals` | Use ACTUAL versions from previous years |

---

## 3. Integrity Rules (Quality by Design)

### 3.1 Constraints Are Mandatory, Not Optional

| Rule | Requirement |
|------|-------------|
| **MUST** | Every FK is a **real FK constraint** in DB (not app-only) |
| **MUST** | Unique constraints reflect **business uniqueness** |
| **MUST** | Check constraints for **common sense validation** |

#### Required Unique Constraints

```sql
-- Reference/lookup tables
CONSTRAINT uk_<table>_code UNIQUE(organization_id, code)
CONSTRAINT uk_<table>_name UNIQUE(organization_id, name)

-- Fact tables
CONSTRAINT uk_<table>_grain UNIQUE(
    organization_id,
    version_id,
    fiscal_year,
    <dimension_keys>...
)
```

#### Required Check Constraints

```sql
-- Percentages (stored as decimal 0-1)
CONSTRAINT ck_<table>_<field>_pct CHECK (<field> >= 0 AND <field> <= 1)

-- Percentages (stored as 0-100)
CONSTRAINT ck_<table>_<field>_pct CHECK (<field> >= 0 AND <field> <= 100)

-- Year range (reasonable bounds)
CONSTRAINT ck_<table>_year CHECK (fiscal_year >= 2020 AND fiscal_year <= 2100)

-- Non-negative counts
CONSTRAINT ck_<table>_<field>_positive CHECK (<field> >= 0)

-- Non-negative amounts
CONSTRAINT ck_<table>_amount_positive CHECK (amount >= 0)
```

### 3.2 Monetary and Numeric Types

| Rule | Requirement |
|------|-------------|
| **MUST** | Use `NUMERIC(p,s)` for money/financial measures (**never FLOAT**) |
| **MUST** | Standard precision: `NUMERIC(18,4)` for amounts, `NUMERIC(10,4)` for rates |
| **MUST** | Store "currency" only if multi-currency exists; otherwise keep currency implicit at organization/system config level |

**Standard Numeric Types**:

```sql
-- Monetary amounts (SAR, EUR)
amount_sar       NUMERIC(18,4)
amount_eur       NUMERIC(18,4)

-- Rates and percentages
rate             NUMERIC(10,4)    -- e.g., 0.1234 = 12.34%
percentage       NUMERIC(5,2)     -- e.g., 12.34 when stored as 0-100

-- Counts (integer values)
student_count    INT
class_count      INT
fte_count        NUMERIC(8,2)     -- FTE can be fractional
hours_count      NUMERIC(8,2)     -- Hours can be fractional
```

### 3.3 Time and Dates

| Rule | Requirement |
|------|-------------|
| **MUST** | Use `TIMESTAMPTZ` for event timestamps (never `TIMESTAMP`) |
| **MUST** | Use `DATE` for business dates (hire_date, effective_date) |
| **MUST** | Define one canonical "planning period" approach |

**Recommended Planning Period Approach**:

```sql
-- For annual budget planning (EFIR standard)
fiscal_year    INT NOT NULL,
period         INT DEFAULT 0,    -- 0=annual, 1-12=monthly if needed

-- For semester/trimester tracking
term           VARCHAR(10),      -- 'T1', 'T2', 'T3' or 'S1', 'S2'
```

---

## 4. Security Rules (Supabase-Ready)

### 4.1 RLS Everywhere

| Rule | Requirement |
|------|-------------|
| **MUST** | RLS **enabled** on all org-owned tables |
| **MUST** | Policies reference `user_organizations` to validate access |
| **MUST** | No direct table access from clients except through RLS-safe policies (or RPC) |

#### Standard RLS Policy Template

```sql
-- Enable RLS
ALTER TABLE efir_budget.<table_name> ENABLE ROW LEVEL SECURITY;

-- Force RLS for table owner too (important for service role)
ALTER TABLE efir_budget.<table_name> FORCE ROW LEVEL SECURITY;

-- SELECT policy (viewers, editors, admins)
CREATE POLICY "Users can view their organization's data"
ON efir_budget.<table_name>
FOR SELECT
TO authenticated
USING (
    organization_id IN (
        SELECT organization_id
        FROM efir_budget.user_organizations
        WHERE user_id = auth.uid()
    )
);

-- INSERT policy (editors, admins only)
CREATE POLICY "Editors can insert their organization's data"
ON efir_budget.<table_name>
FOR INSERT
TO authenticated
WITH CHECK (
    organization_id IN (
        SELECT organization_id
        FROM efir_budget.user_organizations
        WHERE user_id = auth.uid()
        AND role IN ('admin', 'editor')
    )
);

-- UPDATE policy (editors, admins only)
CREATE POLICY "Editors can update their organization's data"
ON efir_budget.<table_name>
FOR UPDATE
TO authenticated
USING (
    organization_id IN (
        SELECT organization_id
        FROM efir_budget.user_organizations
        WHERE user_id = auth.uid()
        AND role IN ('admin', 'editor')
    )
)
WITH CHECK (
    organization_id IN (
        SELECT organization_id
        FROM efir_budget.user_organizations
        WHERE user_id = auth.uid()
        AND role IN ('admin', 'editor')
    )
);

-- DELETE policy (admins only)
CREATE POLICY "Admins can delete their organization's data"
ON efir_budget.<table_name>
FOR DELETE
TO authenticated
USING (
    organization_id IN (
        SELECT organization_id
        FROM efir_budget.user_organizations
        WHERE user_id = auth.uid()
        AND role = 'admin'
    )
);
```

### 4.2 Least Privilege by Role

| Rule | Requirement |
|------|-------------|
| **MUST** | Separate roles (`admin`/`editor`/`viewer`) enforced at DB layer where possible |
| **SHOULD** | Computation outputs are writeable only by service role/jobs, not by end-users |

**Role Permissions Matrix**:

| Role | SELECT | INSERT | UPDATE | DELETE | Notes |
|------|--------|--------|--------|--------|-------|
| `viewer` | ✅ | ❌ | ❌ | ❌ | Read-only access |
| `editor` | ✅ | ✅ | ✅ | ❌ | Can create and modify, not delete |
| `admin` | ✅ | ✅ | ✅ | ✅ | Full access |
| `service_role` | ✅ | ✅ | ✅ | ✅ | Backend jobs only, bypasses RLS |

---

## 5. Performance Rules (So Planning + Cells Don't Explode)

### 5.1 Indexing Is Part of the Table Definition

| Rule | Requirement |
|------|-------------|
| **MUST** | Index **every FK** |
| **MUST** | Composite indexes for main access paths |
| **SHOULD** | Consider partitioning for "cells" style tables |

#### Standard Index Patterns

```sql
-- Every FK gets an index
CREATE INDEX idx_<table>_<fk_column> ON efir_budget.<table>(<fk_column>);

-- Standard composite index for fact tables
CREATE INDEX idx_<table>_org_version_year
ON efir_budget.<table>(organization_id, version_id, fiscal_year);

-- For planning_cells style tables (high volume)
CREATE INDEX idx_<table>_lookup
ON efir_budget.<table>(organization_id, version_id, module, entity_type, entity_id);

-- For time-series queries
CREATE INDEX idx_<table>_created
ON efir_budget.<table>(organization_id, created_at DESC);
```

#### Partitioning Consideration

For high-volume tables (`planning_cells`, `cell_changes`), consider:

```sql
-- Partition by organization_id (for multi-tenant isolation)
CREATE TABLE efir_budget.planning_cells (
    ...
) PARTITION BY HASH (organization_id);

-- Or partition by fiscal_year (for time-based archival)
CREATE TABLE efir_budget.planning_cells (
    ...
) PARTITION BY RANGE (fiscal_year);
```

### 5.2 Avoid Storing the Same Calculation in Three Places

| Rule | Requirement |
|------|-------------|
| **MUST** | One canonical **source of truth** per metric |
| **SHOULD** | Use views/materialized views for derived reporting |
| **SHOULD** | Persist only if you can justify refresh strategy + lineage |

**Calculation Storage Strategy**:

| Data Type | Storage | Refresh Strategy |
|-----------|---------|------------------|
| **Source inputs** | Table | User-driven (immediate save) |
| **Expensive calculations** | Materialized View | On-demand or scheduled |
| **Real-time aggregations** | View | Always fresh |
| **Historical snapshots** | Table | On version lock/approval |

---

## 6. Audit & Traceability Rules (Critical for EFIR)

### 6.1 User-Editable Data Must Be Auditable

| Rule | Requirement |
|------|-------------|
| **MUST** | Any user-editable numeric input is auditable |
| **MUST** | Track: who changed it, when, old vs new, reason/comment (optional) |
| **MUST** | Computation runs are traceable |

#### Cell-Level Audit (Existing Pattern)

The `cell_changes` table provides cell-level audit. Ensure it captures:

```sql
-- Required fields for cell_changes
cell_id          UUID NOT NULL,       -- Reference to planning_cells
changed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
changed_by       UUID NOT NULL,       -- User who made change
old_value        JSONB,               -- Previous value
new_value        JSONB,               -- New value
change_reason    TEXT                 -- Optional explanation
```

#### Table-Level Audit (Generic Pattern)

For tables that don't use the cell pattern:

```sql
CREATE TABLE efir_budget.audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    table_name      VARCHAR(100) NOT NULL,
    record_id       UUID NOT NULL,
    action          VARCHAR(10) NOT NULL,  -- 'INSERT', 'UPDATE', 'DELETE'
    changed_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by      UUID,
    old_values      JSONB,
    new_values      JSONB,

    CONSTRAINT ck_audit_action CHECK (action IN ('INSERT', 'UPDATE', 'DELETE'))
);

CREATE INDEX idx_audit_log_table_record
ON efir_budget.audit_log(table_name, record_id);

CREATE INDEX idx_audit_log_org_time
ON efir_budget.audit_log(organization_id, changed_at DESC);
```

### 6.2 Computation Run Traceability

| Rule | Requirement |
|------|-------------|
| **MUST** | Output tables include computation lineage |
| **SHOULD** | Store `run_id` to group related computations |
| **SHOULD** | Store `inputs_hash` to detect if recalculation needed |

```sql
-- Add to all computed output tables
computed_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
computed_by       UUID,                    -- User or job that triggered
run_id            UUID,                    -- Groups related outputs
version_id        UUID NOT NULL,           -- FK to settings_versions
fiscal_year       INT NOT NULL,            -- Year this data represents
inputs_hash       VARCHAR(64)              -- SHA256 of input parameters
```

---

## 7. Governance Rules (How the Team Works)

### 7.1 "Definition of Done" for Any New Table

A table **cannot be merged** unless it has:

| Requirement | How to Verify |
|-------------|---------------|
| ✅ PK/FKs defined | Check DDL |
| ✅ All FKs indexed | Check indexes |
| ✅ RLS policies (if org-owned) | Check `pg_policies` |
| ✅ Unique constraints | Check constraints |
| ✅ Check constraints | Check constraints |
| ✅ Seed strategy documented (if lookup) | Check migration or seed file |
| ✅ Grain documented | Check table comment |

#### Table Comment Template

Every table must have a comment documenting its grain:

```sql
COMMENT ON TABLE efir_budget.<table_name> IS
'<Description>. One row represents <grain definition>.';

-- Examples:
COMMENT ON TABLE efir_budget.students_enrollment_projections IS
'Cached enrollment projections. One row represents projected student count for one grade in one fiscal year.';

COMMENT ON TABLE efir_budget.settings_fee_structure IS
'Fee amounts configuration. One row represents fee amount for one level, nationality, and fee category combination.';
```

### 7.2 Naming + Documentation

| Rule | Requirement |
|------|-------------|
| **MUST** | Every table has a short "grain" comment in DB |
| **MUST** | No ambiguous names like `data`, `config2`, `temp_*` |
| **MUST** | Consistent naming conventions |

#### Naming Conventions

| Element | Convention | Example |
|---------|------------|---------|
| Tables | `snake_case`, plural | `students_enrollment_projections` |
| Columns | `snake_case` | `fiscal_year`, `created_at` |
| FKs | `<referenced_table_singular>_id` | `version_id` |
| PKs | Always `id` | `id UUID PRIMARY KEY` |
| Indexes | `idx_<table>_<columns>` | `idx_students_enrollment_projections_version_year` |
| Unique constraints | `uk_<table>_<columns>` | `uk_fee_structure_level_nat_cat` |
| Check constraints | `ck_<table>_<rule>` | `ck_fee_structure_amount_positive` |
| Foreign keys | `fk_<table>_<referenced>` | `fk_students_enrollment_projections_version` |

---

## 8. Module Table Allocation Rules

### 8.1 Table Classification Types

Every table in the EFIR Budget App falls into one of these categories:

| Classification | Definition | Has org_id? | Has version_id? | Module Location |
|----------------|------------|-------------|-----------------|-----------------|
| **STATIC** | Global reference/lookup data, identical across all orgs | NO | NO | Settings (`ref_*`) |
| **VERSION-LINKED** | Configuration that changes per budget version | YES (via version) | YES | Planning Modules |
| **ORG-SCOPED** | Organization-specific settings, not versioned | YES | NO | Configuration Module |
| **OUTPUT** | Computed results from calculation engines | YES (via version) | YES | Same as input module |
| **UI-LAYER** | User interface preferences and layouts | YES | NO | Analysis Module |
| **AUDIT** | Change tracking and history | YES | NO | Audit Module |

### 8.2 STATIC Tables (Reference / `ref_*`)

**Definition**: Global reference data that is:
- Identical across ALL organizations (seeded once)
- Never changes per budget version
- Based on French education system standards
- Managed only by system administrators

| Table | Purpose | Records |
|-------|---------|---------|
| `ref_academic_cycles` | Education cycles (Maternelle, Élémentaire, Collège, Lycée) | 4 |
| `ref_academic_levels` | Grade levels (PS → Terminale) | 15 |
| `ref_subjects` | French curriculum subjects | ~30 |
| `settings_subject_hours_matrix` | AEFE-defined hours per subject per level (STATIC content, stored as a settings table) | ~200 |
| `ref_teacher_categories` | Employment types (AEFE_DETACHED, AEFE_FUNDED, LOCAL) | 3 |
| `ref_fee_categories` | Fee types (TUITION, DAI, REGISTRATION, etc.) | ~5 |
| `ref_nationality_types` | Fee tiers (FRENCH, SAUDI, OTHER) | 3 |

**Rules for STATIC tables**:
| Rule | Requirement |
|------|-------------|
| **MUST** | NO `organization_id` column (truly global) |
| **MUST** | NO `version_id` column |
| **MUST** | Include `code` column with UNIQUE constraint |
| **MUST** | Include bilingual names (`name_fr`, `name_en`) |
| **MUST** | Be seeded via migration, not user input |
| **MUST** | Have RLS policies that allow SELECT for all authenticated users |
| **MUST NOT** | Allow INSERT/UPDATE/DELETE except by admin role |

### 8.3 VERSION-LINKED Tables (Planning Modules)

**Definition**: Configuration that varies per budget version and drives calculations.

**Allocation by Module**:

| Module | Tables | Purpose |
|--------|--------|---------|
| **Settings** | `settings_versions` | Central version control |
| **Students (M7)** | `students_configs`, `students_data`, `students_overrides`, `students_calibration` | Enrollment planning inputs + overrides |
| **Teachers (M8)** | `teachers_allocations` | Teacher allocation planning inputs |
| **Settings (M2-6)** | `settings_class_size_params`, `settings_subject_hours_matrix`, `settings_teacher_cost_params`, `settings_fee_structure`, `settings_timetable_constraints` | Versioned configuration inputs |
| **Personnel** | `teachers_employees` | Employee registry with salary & AEFE info |
| **Finance** | `finance_data` | Unified financial planning fact table |

**Rules for VERSION-LINKED tables**:
| Rule | Requirement |
|------|-------------|
| **MUST** | Include `version_id` FK to `settings_versions` table |
| **MUST** | Inherit `organization_id` through version FK (or include directly) |
| **MUST** | Have unique constraint including `version_id` |
| **SHOULD** | Include `is_active` for soft-disable without deletion |

### 8.4 Module Boundaries (Enrollment vs Revenue)

**Decision**: Enrollment and Revenue are **SEPARATE** modules.

**Rationale**: Enrollment is a **primary driver** that feeds multiple downstream modules:

```
                    ┌─────────────────────────┐
                    │      ENROLLMENT         │
                    │  (how many students?)   │
                    └───────────┬─────────────┘
                                │
           ┌────────────────────┼────────────────────┐
           │                    │                    │
           ▼                    ▼                    ▼
    ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
    │   REVENUE   │     │    CLASS    │     │  OPERATING  │
    │  students   │     │  STRUCTURE  │     │    COSTS    │
    │  × fees     │     │  # classes  │     │  utilities  │
    └─────────────┘     └──────┬──────┘     └─────────────┘
                               │
                               ▼
                        ┌─────────────┐
                        │ DHG/WORKFORCE │
                        │ teacher needs │
                        └─────────────┘
```

| Module | Primary Question | Managed By | Feeds Into |
|--------|------------------|------------|------------|
| **Enrollment (M7)** | "How many students?" | Academic/Admissions | Revenue, Class Structure, DHG, Operating Costs |
| **Revenue (M10)** | "How much money?" | Finance | Budget Consolidation |

### 8.5 Module Structure (Current, Phase 4+)

This section provides a narrative structure view. The authoritative module-to-table mapping is in Section 9.2.

```
SETTINGS (Reference + Configuration) ───────────────────────────────────────────
├── ref_*                        (STATIC: cycles, levels, subjects, categories)
├── settings_versions             (CENTRAL version table, scenario_type enum)
└── settings_*                    (versioned configuration: fees, hours, costs)

STUDENTS (Enrollment + Class Structure) ────────────────────────────────────────
├── students_configs              (per-version+scenario settings)
├── students_data                 (enrollment facts by year/level)
├── students_overrides            (override layers per config/scope)
├── students_calibration          (org-scoped calibration by grade)
├── students_enrollment_projections (OUTPUT with lineage)
└── students_class_structures     (OUTPUT with lineage)

TEACHERS (DHG + Workforce + Employees) ─────────────────────────────────────────
├── teachers_employees            (employee master data incl salary/AEFE)
├── teachers_allocations          (planning input allocations)
├── teachers_dhg_subject_hours    (OUTPUT with lineage)
└── teachers_dhg_requirements     (OUTPUT with lineage)

FINANCE (Revenue + Costs + Statements) ─────────────────────────────────────────
├── finance_data                  (unified fact table, data_type discriminator)
├── vw_finance_*                  (backward-compatible views)
├── finance_consolidations        (OUTPUT)
├── finance_statements            (OUTPUT)
└── finance_statement_lines       (OUTPUT)

INSIGHTS (KPIs + Dashboards) ───────────────────────────────────────────────────
└── insights_*                    (kpis, dashboards, variance analysis)

ADMIN (Org + Audit) ────────────────────────────────────────────────────────────
└── admin_*                       (organizations, cells, audit, integration logs)
```

### 8.6 Students Module Structure (Detailed)

**Implemented (Phase 4A)**: Enrollment tables consolidated into 4 INPUT tables + 2 OUTPUT tables.

#### Input Tables

| Table | Classification | Purpose | Grain / Uniqueness |
|-------|----------------|---------|--------------------|
| `students_configs` | VERSION-LINKED | Scenario settings (base_year, capacity, multipliers) | One row per `(version_id, scenario_code)` |
| `students_data` | VERSION-LINKED | Enrollment facts + nationality breakdown | One row per `(version_id, fiscal_year, level_id, nationality_type_id)` |
| `students_overrides` | VERSION-LINKED | Override layers (retention, lateral, class size constraints) | One row per `(config_id, scope_type, scope_id)` |
| `students_calibration` | ORG-SCOPED | Derived calibration + manual overrides | One row per `(organization_id, grade_code)` |

#### Output Tables (Must Include Lineage)

| Table | Purpose | Lineage Columns |
|-------|---------|-----------------|
| `students_enrollment_projections` | Cached projected student counts | `computed_at`, `computed_by`, `run_id`, `inputs_hash`, `version_id` |
| `students_class_structures` | Cached class formation results | `computed_at`, `computed_by`, `run_id`, `inputs_hash`, `version_id` |

#### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **No dedicated “scenario header” table** | Scenario handling via `students_configs.scenario_code` (supports multiple scenarios per version) |
| **Overrides key off `config_id`** | Allows different override sets per scenario without duplicating versions |
| **`scope_type` pattern** | One override table supports global/cycle/level scopes |
| **No “actual-only” enrollment tables** | Use unified versioning (`settings_versions.scenario_type='ACTUAL'`) |

#### `data_source` Values

`students_data.data_source` tracks the origin of each enrollment row:

| Value | Meaning |
|-------|---------|
| `'manual'` | User-entered data |
| `'projected'` | Engine-calculated projection |
| `'actual'` | From approved ACTUAL version |
| `'imported'` | External import (Skolengo, etc.) |

### 8.7 Teachers (DHG/Workforce) Module Structure (Detailed)

**Key Design Principle**: DHG outputs are computed from `students_class_structures × settings_subject_hours_matrix`.

#### Reference / Input Tables

| Table | Classification | Purpose |
|-------|----------------|---------|
| `settings_subject_hours_matrix` | STATIC content (stored as settings) | Official hours per subject per level |
| `settings_teacher_cost_params` | VERSION-LINKED | Teacher cost parameters (PRRD/HSA, category costs) |
| `settings_timetable_constraints` | VERSION-LINKED | Constraints by level (max hours/day, breaks) |
| `teachers_allocations` | VERSION-LINKED | Planning input: teacher assignments by subject/level |

#### Output Tables (Computed with Lineage)

| Table | Purpose | Lineage Columns |
|-------|---------|-----------------|
| `teachers_dhg_subject_hours` | Total hours required per subject/level | `computed_at`, `computed_by`, `run_id`, `inputs_hash`, `version_id` |
| `teachers_dhg_requirements` | FTE requirements per subject | `computed_at`, `computed_by`, `run_id`, `inputs_hash`, `version_id` |

#### Calculation Flow

```
settings_subject_hours_matrix (official hours per subject/level)
            ×
students_class_structures (computed class counts)
            =
teachers_dhg_subject_hours (output)
            ÷ standard_hours (18h secondary / 24h primary)
            =
teachers_dhg_requirements (output)
```

---

### 8.8 Personnel Module Structure (Detailed)

**Consolidation Decision**: 4 tables → 1 table (`employees` consolidated)

**Key Design Principle**: EOS and GOSI are calculated on demand by engines, not stored.

#### Consolidated Table

| Table | Purpose | Key Columns | Unique Constraint |
|-------|---------|-------------|-------------------|
| `employees` | Unified employee registry with salary and AEFE position info | See below | `(organization_id, employee_code)` |

#### `employees` Table Structure (Consolidated)

```sql
CREATE TABLE efir_budget.teachers_employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
    version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id) ON DELETE CASCADE,

    -- Identity
    employee_code VARCHAR(20) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,

    -- Employment
    hire_date DATE NOT NULL,
    termination_date DATE,
    nationality VARCHAR(50) NOT NULL,  -- For GOSI calculation

    -- Category (determines calculation rules)
    category_id UUID NOT NULL REFERENCES efir_budget.ref_teacher_categories(id),
    -- category determines: AEFE_DETACHED, AEFE_FUNDED, LOCAL

    -- AEFE Position Info (merged from aefe_positions)
    aefe_position_code VARCHAR(20),     -- NULL for LOCAL employees
    aefe_funding_type VARCHAR(20),      -- 'detached' | 'funded' | NULL
    prrd_eligible BOOLEAN DEFAULT FALSE,

    -- Salary Info (merged from employee_salaries)
    basic_salary_sar NUMERIC(18,4),
    housing_allowance_sar NUMERIC(18,4),
    transport_allowance_sar NUMERIC(18,4),
    other_allowances_sar NUMERIC(18,4),
    effective_from DATE,

    -- Teaching Info (for teachers only)
    is_teacher BOOLEAN DEFAULT FALSE,
    subject_id UUID REFERENCES efir_budget.ref_subjects(id),
    teaches_secondary BOOLEAN DEFAULT FALSE,  -- 18h standard
    teaches_primary BOOLEAN DEFAULT FALSE,    -- 24h standard

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Standard metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id),

    CONSTRAINT uk_employee_code UNIQUE(organization_id, employee_code),
    -- NOTE: Complex AEFE validation done via trigger (CHECK can't have subqueries)
    -- See trigger function: efir_budget.validate_aefe_employee_data()
    CONSTRAINT ck_aefe_funding_type CHECK (
        aefe_funding_type IS NULL
        OR aefe_funding_type IN ('detached', 'funded')
    )
);

-- Trigger function for complex AEFE validation (subqueries not allowed in CHECK)
CREATE OR REPLACE FUNCTION efir_budget.validate_aefe_employee_data()
RETURNS TRIGGER AS $$
DECLARE
    category_code TEXT;
BEGIN
    -- Look up the category code for validation
    SELECT code INTO category_code
    FROM efir_budget.teacher_categories
    WHERE id = NEW.category_id;

    -- Rule 1: LOCAL employees must NOT have AEFE fields
    IF category_code = 'LOCAL' THEN
        IF NEW.aefe_position_code IS NOT NULL OR NEW.aefe_funding_type IS NOT NULL THEN
            RAISE EXCEPTION 'LOCAL category employees cannot have AEFE position code or funding type';
        END IF;
    END IF;

    -- Rule 2: Non-LOCAL employees (AEFE) must have funding_type set
    IF category_code IN ('AEFE_DETACHED', 'AEFE_FUNDED') THEN
        IF NEW.aefe_funding_type IS NULL THEN
            RAISE EXCEPTION 'AEFE employees must have aefe_funding_type set';
        END IF;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validate_aefe_employee
    BEFORE INSERT OR UPDATE ON efir_budget.employees
    FOR EACH ROW
    EXECUTE FUNCTION efir_budget.validate_aefe_employee_data();
```

#### Tables Removed (Merged into `employees`)

| Old Table | Merged Into | Migration Notes |
|-----------|-------------|-----------------|
| `employee_salaries` | `employees` | Salary columns added directly; historical salaries via unified versioning |
| `aefe_positions` | `employees` | AEFE-specific columns added; only populated for AEFE employees |
| `eos_provisions` | **REMOVED** | Calculated on demand by EOS engine; version-based snapshots via versioning |

#### EOS/GOSI Calculation (On-Demand)

EOS and GOSI are **never stored**. They are calculated by pure function engines when needed:

```python
# EOS Calculation (backend/app/engine/eos/)
def calculate_eos(employee: Employee, as_of_date: date) -> EOSResult:
    """Pure function - no database writes"""
    service_years = calculate_service_years(employee.hire_date, as_of_date)
    return EOSResult(
        eos_liability_sar=compute_eos_liability(employee.basic_salary_sar, service_years),
        service_years=service_years
    )

# GOSI Calculation (backend/app/engine/gosi/)
def calculate_gosi(employee: Employee) -> GOSIResult:
    """Pure function - no database writes"""
    if employee.nationality == 'SAUDI':
        return GOSIResult(
            employer_contribution=employee.basic_salary_sar * 0.12,
            employee_contribution=employee.basic_salary_sar * 0.10
        )
    else:
        return GOSIResult(employer_contribution=0, employee_contribution=0)
```

#### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **4 tables → 1 table** | Reduces joins; salary and AEFE info are attributes of an employee |
| **No `eos_provisions` table** | EOS liability changes with each calculation; snapshot via versioning if needed |
| **Salary history via versioning** | Create ACTUAL version snapshot when salary changes; compare versions for history |
| **AEFE columns nullable** | Only populated for AEFE employees; NULL for LOCAL employees |
| **`category_id` as discriminator** | Teacher category determines AEFE rules, PRRD eligibility, calculation logic |

#### Historical Salary Tracking

Instead of separate `employee_salaries` history table:

1. When salary changes, create new version snapshot (if needed for audit)
2. Employee salary columns reflect **current** values
3. Historical comparison via `scenario_type='ACTUAL'` versions from different periods

```
Version A (2024 ACTUAL): employees.basic_salary_sar = 15000
Version B (2025 ACTUAL): employees.basic_salary_sar = 16500
→ Salary change = Version B - Version A = 1500 (10% increase)
```

---

### 8.9 Planning/Consolidation/Analysis Module Structure (Detailed)

**Implemented (Phase 4C)**: Financial planning tables are consolidated into one canonical fact table plus
backward-compatible views.

**Canonical**:
- `efir_budget.finance_data` (discriminator: `data_type` = `revenue` | `operating_cost` | `personnel_cost` | `capex`)

**Backward-compatible views**:
- `efir_budget.vw_finance_revenue`
- `efir_budget.vw_finance_operating_costs`
- `efir_budget.vw_finance_personnel_costs`
- `efir_budget.vw_finance_capex`

**Outputs (cached + lineage)**:
- `efir_budget.finance_consolidations`
- `efir_budget.finance_statements`
- `efir_budget.finance_statement_lines`

**Authoritative references**:
- Migration: `backend/alembic/versions/20251215_0700_phase_4c_financial_consolidation.py`
- Model: `backend/app/models/finance_unified.py`

#### Legacy: pre-Phase-4C `financial_data` design (DO NOT USE)

This legacy design is kept for historical context only. The implemented schema uses:
- `efir_budget.finance_data` (Phase 4C unified fact table + `vw_finance_*` views)
- `efir_budget.settings_versions` (central versions table)

Do not build new work against `financial_data` or `efir_budget.versions` naming.

Legacy SQL and view definitions are intentionally omitted to prevent copy/paste drift.
If you need the implemented DDL/views, use:
- `backend/alembic/versions/20251215_0700_phase_4c_financial_consolidation.py`

---

### 8.10 Strategic Module Structure (Detailed)

**Consolidation Decision**: 4 tables → 4 tables (no reduction, but enhanced with org_id and version integration)

**Key Design Principle**: Strategic plans integrate with unified versioning. Each 5-year plan links to a `settings_versions` row with `scenario_type='STRATEGIC'`, enabling historical data retrieval and lineage tracking.

#### Issues Fixed

| Issue | Before | After |
|-------|--------|-------|
| Missing multi-tenancy | No `organization_id` on `strategic_plans` | Add `organization_id` FK |
| Global unique constraint | `UNIQUE(name)` | Change to `UNIQUE(organization_id, name)` |
| No version integration | No link to `settings_versions` | Add `version_id` FK |
| No lineage tracking | Unknown starting point | Add `based_on_version_id` FK |

#### Table Structure (Enhanced)

```
STRATEGIC MODULE (M18) ─────────────────────────────────────────

├── settings_strategic_plans      (VERSION-LINKED, enhanced)
│   ├── organization_id FK        (NEW: multi-tenancy)
│   ├── version_id FK → settings_versions  (NEW: unified versioning)
│   │   └── version.scenario_type = 'STRATEGIC'
│   │   └── version.fiscal_year = base_year
│   │   └── version.end_fiscal_year = base_year + 4
│   ├── based_on_version_id FK    (NEW: lineage - which BUDGET was starting point?)
│   ├── name, description
│   ├── base_year (start year, e.g., 2025)
│   ├── status: 'draft' | 'approved' | 'archived'
│   └── Standard metadata columns
│
├── settings_strategic_scenarios  (Inherits org_id via parent FK)
│   ├── strategic_plan_id FK (CASCADE)
│   ├── scenario_type ENUM: base_case, conservative, optimistic, new_campus
│   ├── name, description
│   ├── Growth rates: enrollment_growth_rate, fee_increase_rate
│   ├── Inflation: salary_inflation_rate, operating_inflation_rate
│   └── additional_assumptions JSONB
│
├── settings_strategic_projections (OUTPUT with lineage)
│   ├── strategic_plan_scenario_id FK (CASCADE)
│   ├── year INT (1-5)
│   ├── category ENUM: revenue, personnel_costs, operating_costs, capex, depreciation
│   ├── amount_sar NUMERIC(15,2)
│   └── calculation_inputs JSONB (lineage)
│
└── settings_strategic_initiatives (Inherits org_id via parent FK)
    ├── strategic_plan_id FK (CASCADE)
    ├── name, description
    ├── planned_year (1-5)
    ├── capex_amount_sar, operating_impact_sar
    └── status ENUM: planned, approved, in_progress, completed, cancelled
```

#### Version Integration Design

When a strategic plan is created, create a corresponding `settings_versions` row
(`scenario_type='STRATEGIC'`) and link `settings_strategic_plans.version_id` to it.

#### Lineage Tracking

The `based_on_version_id` tracks which BUDGET version was the starting point:

```
Strategic Plan: "5Y-2025-2030"
├── version_id → settings_versions (scenario_type='STRATEGIC', 2025-2029)
├── based_on_version_id → settings_versions (scenario_type='BUDGET', 2024)
│   └── "This strategic plan was based on approved Budget 2024 data"
│
└── Child Data:
    ├── scenarios (base_case, conservative, optimistic)
    ├── projections (5 years × 5 categories × N scenarios)
    └── initiatives (N projects)
```

#### Data Retrieval Pattern

To retrieve strategic plan data, join `settings_strategic_plans` to `settings_versions` on `version_id`,
and query child tables via their parent FKs. Example SQL is intentionally omitted to prevent drift.

#### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Add `organization_id` to `strategic_plans`** | Multi-tenancy: each org has their own strategic plans |
| **Add `version_id` FK** | Unified versioning: strategic plans are versioned via `settings_versions` |
| **Add `based_on_version_id` FK** | Lineage: tracks which BUDGET was the starting point for projections |
| **Keep 4 tables (no reduction)** | Hierarchical structure is correct: plan → scenarios → projections, plan → initiatives |
| **Change unique constraint** | Per-org unique names: `UNIQUE(organization_id, name)` instead of global `UNIQUE(name)` |
| **Projections store computed values** | Unlike `finance_data`, projections are scenario-specific and need JSONB for calculation_inputs |
| **No separate OUTPUT tables** | Projections and initiatives ARE the outputs of strategic planning - stored for scenario comparison |

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Add `organization_id` FK to `settings_strategic_plans` | LOW | MEDIUM |
| P0 | Add `version_id` FK to `settings_strategic_plans` | LOW | LOW |
| P0 | Add `based_on_version_id` FK to `settings_strategic_plans` | LOW | LOW |
| P1 | Change unique constraint from `(name)` to `(organization_id, name)` | LOW | LOW |
| P1 | Add constraint: version must have `scenario_type='STRATEGIC'` | LOW | LOW |
| P2 | Update backend services to create version when creating strategic plan | MEDIUM | MEDIUM |
| P2 | Update RLS policies for strategic tables | MEDIUM | LOW |
| P3 | Migrate existing strategic plans (assign org_id, create versions) | MEDIUM | MEDIUM |

---

### 8.11 Cost/Profit Center Module Structure (Detailed)

**Design Decision**: NEW MODULE - Adds two financial dimensions for expense and revenue attribution.

**Key Design Principle**:
- **Cost Centers** and **Profit Centers** are **ORG-SCOPED** (stable reference data, not versioned)
- **Allocation Rules** are **VERSION-LINKED** (can change per budget version)
- Historical tracking via unified versioning in `finance_data.version_id`, not separate tables

#### Module Purpose

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       COST/PROFIT CENTER MODULE                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                            │
│  PROFIT CENTERS (Revenue Attribution)     COST CENTERS (Expense Attribution)
│  ├── Maternelle (PS, MS, GS)              ├── Teaching                     │
│  ├── Élémentaire (CP-CM2)                 │   ├── Primary Teachers         │
│  ├── Collège (6ème-3ème)                  │   ├── Secondary Teachers       │
│  ├── Lycée (2nde-Term)                    │   └── Language Teachers        │
│  └── Autres Activités (Sports, etc.)      ├── Administrative               │
│                                           │   ├── Direction                │
│  Revenue flows INTO profit centers        │   └── Admin Staff              │
│  based on student enrollment              ├── Support Services             │
│                                           │   ├── IT & Technology          │
│  4 academic cycles + 1 for Other          │   └── Maintenance              │
│                                           └── Overhead                     │
│                                               ├── Facilities               │
│                                               └── General Services         │
│                                                                            │
│  Expenses flow OUT OF cost centers                                         │
│  and may be allocated TO profit centers                                    │
│                                                                            │
├────────────────────────────────────────────────────────────────────────────┤
│                         ALLOCATION RULES                                   │
│  Map costs to profit centers using:                                        │
│  • Proportional (by enrollment, by FTE)                                    │
│  • Fixed percentage                                                        │
│  • Step-down (cascade allocation)                                          │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Tables Classification

| Table | Classification | Has org_id? | Has version_id? | Purpose |
|-------|----------------|-------------|-----------------|---------|
| `finance_profit_centers` | ORG-SCOPED | YES | NO | Revenue attribution by academic cycle |
| `finance_cost_centers` | ORG-SCOPED | YES | NO | Expense attribution by department/function |
| `finance_allocation_rules` | VERSION-LINKED | YES (via version) | YES | How costs are allocated to profit centers |
| `finance_allocation_rule_targets` | VERSION-LINKED | (inherited) | (inherited) | Target profit centers for each rule |

#### Table Structures

##### `finance_profit_centers` Table (ORG-SCOPED) (PLANNED)

```sql
CREATE TABLE efir_budget.finance_profit_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),

    -- Identity
    code VARCHAR(20) NOT NULL,              -- 'PC-MAT', 'PC-ELEM', 'PC-COL', 'PC-LYC'
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,

    -- Hierarchy (optional, 2 levels max)
    parent_id UUID REFERENCES efir_budget.finance_profit_centers(id),

    -- Link to academic cycle (for automatic revenue attribution)
    cycle_id UUID REFERENCES efir_budget.ref_academic_cycles(id),

    -- Display
    sort_order INT NOT NULL DEFAULT 0,
    description TEXT,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Standard metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id),

    -- Constraints
    CONSTRAINT uk_profit_center_code UNIQUE(organization_id, code),
    CONSTRAINT uk_profit_center_name UNIQUE(organization_id, name_fr),
    CONSTRAINT ck_profit_center_no_self_parent CHECK (parent_id != id),
    CONSTRAINT ck_profit_center_hierarchy_depth CHECK (
        -- Level 1: parent_id IS NULL
        -- Level 2: parent_id IS NOT NULL AND parent has NULL parent
        -- Enforced via trigger for deeper validation
        TRUE
    )
);

CREATE INDEX idx_finance_profit_centers_org ON efir_budget.finance_profit_centers(organization_id);
CREATE INDEX idx_finance_profit_centers_parent ON efir_budget.finance_profit_centers(parent_id);
CREATE INDEX idx_finance_profit_centers_cycle ON efir_budget.finance_profit_centers(cycle_id);

COMMENT ON TABLE efir_budget.finance_profit_centers IS
'Revenue attribution centers. One row represents one profit center (typically one per academic cycle).';
```

##### `finance_cost_centers` Table (ORG-SCOPED) (PLANNED)

```sql
CREATE TYPE efir_budget.finance_cost_center_category AS ENUM (
    'teaching',        -- Teaching departments
    'administrative',  -- Admin & direction
    'support',         -- Support services (IT, maintenance)
    'overhead'         -- Facilities, general
);

CREATE TABLE efir_budget.finance_cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),

    -- Identity
    code VARCHAR(20) NOT NULL,              -- 'CC-TCH-PRI', 'CC-ADM-DIR'
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,

    -- Classification
    category finance_cost_center_category NOT NULL,

    -- Hierarchy (2 levels max)
    parent_id UUID REFERENCES efir_budget.finance_cost_centers(id),

    -- Display
    sort_order INT NOT NULL DEFAULT 0,
    description TEXT,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Standard metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id),

    -- Constraints
    CONSTRAINT uk_cost_center_code UNIQUE(organization_id, code),
    CONSTRAINT uk_cost_center_name UNIQUE(organization_id, name_fr),
    CONSTRAINT ck_cost_center_no_self_parent CHECK (parent_id != id)
);

CREATE INDEX idx_finance_cost_centers_org ON efir_budget.finance_cost_centers(organization_id);
CREATE INDEX idx_finance_cost_centers_parent ON efir_budget.finance_cost_centers(parent_id);
CREATE INDEX idx_finance_cost_centers_category ON efir_budget.finance_cost_centers(category);

COMMENT ON TABLE efir_budget.finance_cost_centers IS
'Expense attribution centers. One row represents one cost center (department/function).';
```

##### `finance_allocation_rules` Table (VERSION-LINKED)

```sql
CREATE TYPE efir_budget.finance_allocation_method AS ENUM (
    'proportional_enrollment',   -- By student count per profit center
    'proportional_fte',          -- By teacher FTE per profit center
    'proportional_revenue',      -- By revenue amount per profit center
    'fixed_percentage',          -- Fixed % split (defined in targets)
    'step_down'                  -- Cascade: first to A, remainder to B
);

CREATE TYPE efir_budget.finance_allocation_base AS ENUM (
    'enrollment',   -- Student count
    'fte',          -- Full-time equivalent
    'revenue',      -- Revenue amount
    'headcount',    -- Employee count
    'square_meters' -- Facility space
);

CREATE TABLE efir_budget.finance_allocation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Version linkage (VERSION-LINKED pattern)
    version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id),

    -- Identity
    code VARCHAR(20) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,

    -- Source: which cost center is being allocated?
    cost_center_id UUID NOT NULL REFERENCES efir_budget.finance_cost_centers(id),

    -- Method
    allocation_method efir_budget.finance_allocation_method NOT NULL,
    allocation_base efir_budget.finance_allocation_base,        -- Required for proportional methods

    -- Scope (optional: apply only to specific record types/accounts)
    applies_to_data_type efir_budget.finance_data_type, -- NULL = all types
    account_code_pattern VARCHAR(50),       -- SQL LIKE pattern, e.g., '60%' for expenses

    -- Execution order (for step-down method)
    execution_order INT NOT NULL DEFAULT 0,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    -- Standard metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES auth.users(id),

    -- Constraints
    CONSTRAINT uk_allocation_rule_code UNIQUE(version_id, code),
    CONSTRAINT ck_allocation_base_required CHECK (
        (allocation_method IN ('proportional_enrollment', 'proportional_fte',
                               'proportional_revenue') AND allocation_base IS NOT NULL)
        OR
        (allocation_method IN ('fixed_percentage', 'step_down') AND allocation_base IS NULL)
    )
);

CREATE INDEX idx_finance_allocation_rules_version ON efir_budget.finance_allocation_rules(version_id);
CREATE INDEX idx_finance_allocation_rules_cost_center ON efir_budget.finance_allocation_rules(cost_center_id);

COMMENT ON TABLE efir_budget.finance_allocation_rules IS
'Cost allocation rules per budget version. One row represents one rule mapping a cost center to profit centers.';
```

##### `finance_allocation_rule_targets` Table (Child of finance_allocation_rules)

```sql
CREATE TABLE efir_budget.finance_allocation_rule_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Parent rule
    allocation_rule_id UUID NOT NULL REFERENCES efir_budget.finance_allocation_rules(id) ON DELETE CASCADE,

    -- Target profit center
    profit_center_id UUID NOT NULL REFERENCES efir_budget.finance_profit_centers(id),

    -- For fixed_percentage method: the allocation percentage (0-100)
    percentage NUMERIC(5,2),

    -- For step_down method: order of allocation
    step_order INT,

    -- Standard metadata
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),

    -- Constraints
    CONSTRAINT uk_allocation_target UNIQUE(allocation_rule_id, profit_center_id),
    CONSTRAINT ck_percentage_range CHECK (percentage IS NULL OR (percentage >= 0 AND percentage <= 100))
);

CREATE INDEX idx_finance_allocation_rule_targets_rule ON efir_budget.finance_allocation_rule_targets(allocation_rule_id);
CREATE INDEX idx_finance_allocation_rule_targets_profit ON efir_budget.finance_allocation_rule_targets(profit_center_id);

COMMENT ON TABLE efir_budget.finance_allocation_rule_targets IS
'Target profit centers for each allocation rule. For fixed_percentage, includes the percentage per profit center.';
```

#### Default Seed Data (EFIR School)

```sql
-- Profit Centers (5: 4 academic cycles + Other Activities)
INSERT INTO efir_budget.finance_profit_centers (organization_id, code, name_fr, name_en, cycle_id, sort_order) VALUES
(<org_id>, 'PC-MAT',   'Maternelle',        'Preschool',         <cycle_maternelle_id>,  1),
(<org_id>, 'PC-ELEM',  'Élémentaire',       'Elementary',        <cycle_elementaire_id>, 2),
(<org_id>, 'PC-COL',   'Collège',           'Middle School',     <cycle_college_id>,     3),
(<org_id>, 'PC-LYC',   'Lycée',             'High School',       <cycle_lycee_id>,       4),
(<org_id>, 'PC-OTHER', 'Autres Activités',  'Other Activities',  NULL,                   5);
-- Note: PC-OTHER has cycle_id=NULL as it spans all cycles (sports, after-school, etc.)

-- Cost Centers (Level 1: Categories)
INSERT INTO efir_budget.finance_cost_centers (organization_id, code, name_fr, name_en, category, parent_id, sort_order) VALUES
(<org_id>, 'CC-TEACH', 'Enseignement',  'Teaching',        'teaching',       NULL, 1),
(<org_id>, 'CC-ADMIN', 'Administration','Administration',  'administrative', NULL, 2),
(<org_id>, 'CC-SUPP',  'Support',       'Support',         'support',        NULL, 3),
(<org_id>, 'CC-OVER',  'Frais Généraux','Overhead',        'overhead',       NULL, 4);

-- Cost Centers (Level 2: Sub-departments under Teaching)
INSERT INTO efir_budget.finance_cost_centers (organization_id, code, name_fr, name_en, category, parent_id, sort_order) VALUES
(<org_id>, 'CC-TCH-PRI', 'Enseignants Primaire',     'Primary Teachers',     'teaching', <CC-TEACH-id>, 1),
(<org_id>, 'CC-TCH-SEC', 'Enseignants Secondaire',   'Secondary Teachers',   'teaching', <CC-TEACH-id>, 2),
(<org_id>, 'CC-TCH-LNG', 'Enseignants Langues',      'Language Teachers',    'teaching', <CC-TEACH-id>, 3);

-- Cost Centers (Level 2: Sub-departments under Admin)
INSERT INTO efir_budget.finance_cost_centers (organization_id, code, name_fr, name_en, category, parent_id, sort_order) VALUES
(<org_id>, 'CC-ADM-DIR', 'Direction',    'Direction',   'administrative', <CC-ADMIN-id>, 1),
(<org_id>, 'CC-ADM-SEC', 'Secrétariat', 'Admin Staff', 'administrative', <CC-ADMIN-id>, 2);

-- Cost Centers (Level 2: Sub-departments under Support)
INSERT INTO efir_budget.finance_cost_centers (organization_id, code, name_fr, name_en, category, parent_id, sort_order) VALUES
(<org_id>, 'CC-SUP-IT',  'Informatique',   'IT & Technology', 'support', <CC-SUPP-id>, 1),
(<org_id>, 'CC-SUP-MNT', 'Maintenance',    'Maintenance',     'support', <CC-SUPP-id>, 2);

-- Cost Centers (Level 2: Sub-departments under Overhead)
INSERT INTO efir_budget.finance_cost_centers (organization_id, code, name_fr, name_en, category, parent_id, sort_order) VALUES
(<org_id>, 'CC-OVR-FAC', 'Bâtiments',        'Facilities',       'overhead', <CC-OVER-id>, 1),
(<org_id>, 'CC-OVR-GEN', 'Services Généraux','General Services', 'overhead', <CC-OVER-id>, 2);
```

#### Integration with `finance_data`

Planned additions: tag financial facts with cost/profit centers inside `finance_data` (Section 8.9):

```sql
ALTER TABLE efir_budget.finance_data
    ADD COLUMN cost_center_id UUID REFERENCES efir_budget.finance_cost_centers(id),
    ADD COLUMN profit_center_id UUID REFERENCES efir_budget.finance_profit_centers(id);
```

Financial records can be tagged with their source cost center and (if known) target profit center. The allocation engine computes final allocations and stores results in the same `finance_data` table with appropriate lineage.

#### Calculation Engine Pattern

Allocation is computed by a pure function engine (not stored in separate tables):

```python
# backend/app/engine/allocation/

class AllocationInput(BaseModel):
    version_id: UUID
    fiscal_year: int
    finance_data: list[FinanceDataRow]
    allocation_rules: list[AllocationRule]
    profit_centers: list[ProfitCenter]
    enrollment_by_profit_center: dict[UUID, int]  # For proportional allocation

class AllocationOutput(BaseModel):
    allocated_records: list[FinanceDataRow]
    allocation_summary: dict[str, Decimal]  # Per profit center totals

def allocate_costs(inputs: AllocationInput) -> AllocationOutput:
    """
    Pure function - applies allocation rules to financial data.

    Results stored in finance_data table with:
    - profit_center_id set to target profit center (PLANNED column)
    - is_calculated = True
    - calculation_driver = f'allocation_rule:{rule.code}'
    - computed_at, computed_by, run_id for lineage
    """
    ...
```

#### Historical Tracking (Via Unified Versioning)

**No separate `allocation_results` table**. Historical allocation is tracked via:

1. **Version-specific rules**: `finance_allocation_rules` are tied to `version_id`
2. **Version-specific data**: `finance_data` stores allocated amounts with `version_id` and `profit_center_id`
3. **Comparing versions**: View allocations for Budget 2024 vs Budget 2025 by querying different versions

```sql
-- Compare overhead allocation between two budget versions
SELECT
    pc.name_en AS profit_center,
    v.name AS version_name,
    SUM(fd.amount_sar) AS allocated_overhead
FROM efir_budget.finance_data fd
JOIN efir_budget.finance_profit_centers pc ON pc.id = fd.profit_center_id
JOIN efir_budget.settings_versions v ON v.id = fd.version_id
JOIN efir_budget.finance_cost_centers cc ON cc.id = fd.cost_center_id
WHERE cc.category = 'overhead'
  AND v.id IN (<budget_2024_id>, <budget_2025_id>)
  AND fd.is_calculated = TRUE
GROUP BY pc.name_en, v.name
ORDER BY pc.name_en, v.name;
```

#### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Profit centers = 5 (4 cycles + Other)** | 4 academic cycles (Maternelle, Élémentaire, Collège, Lycée) + 1 for Other Activities (sports, after-school, etc.) |
| **2-level hierarchy max** | Keeps structure simple; deeper hierarchies can be added later if needed |
| **Centers are ORG-SCOPED** | Cost/profit centers are stable organization structure, not versioned |
| **Rules are VERSION-LINKED** | Allocation percentages can change per budget version |
| **No cross-org templates** | Single organization for now; templates can be added later |
| **No allocation_results table** | Allocated data stored in `finance_data` with `profit_center_id` set (planned column) |
| **Calculation in engine, not DB** | Allocation engine computes on demand; results stored with lineage |
| **cycle_id on finance_profit_centers** | Auto-map revenue to profit center based on student's academic cycle |

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Create `finance_cost_center_category` ENUM | LOW | LOW |
| P0 | Create `finance_allocation_method` ENUM | LOW | LOW |
| P0 | Create `finance_allocation_base` ENUM | LOW | LOW |
| P0 | Create `finance_profit_centers` table | LOW | LOW |
| P0 | Create `finance_cost_centers` table | LOW | LOW |
| P1 | Create `finance_allocation_rules` table | LOW | LOW |
| P1 | Create `finance_allocation_rule_targets` table | LOW | LOW |
| P1 | Add cost/profit center columns to `finance_data` | LOW | LOW |
| P2 | Create seed data migration for EFIR | MEDIUM | LOW |
| P2 | Implement allocation calculation engine | MEDIUM | MEDIUM |
| P3 | Build Admin UI for CRUD operations | HIGH | LOW |

---

## 9. Unified Module Architecture (6 Modules)

### 9.1 Overview

The EFIR Budget App uses a **6-module architecture** that unifies the frontend UI, backend engines, and database tables into a cohesive, role-aligned design.

> **CRITICAL**: All tables exist in the **single `efir_budget` schema**. The `public` schema belongs to another project on the same Supabase instance and MUST NEVER be touched. We use **table name prefixes** to organize tables by module.

| Module | UI Label | Color | Table Prefix | Primary Role |
|--------|----------|-------|--------------|--------------|
| **Students** | Students | sage | `students_*` | Academic Director |
| **Teachers** | Teachers | wine | `teachers_*` | HR Manager |
| **Finance** | Finance | gold | `finance_*` | Finance Director |
| **Insights** | Insights | slate | `insights_*` | All (read) |
| **Settings** | Settings | neutral | `settings_*` or `ref_*` | All (limited) |
| **Admin** | Admin | neutral-dark | `admin_*` | Admin only |

### 9.2 Module-to-Table Mapping

Each module owns tables with a dedicated **prefix** within the `efir_budget` schema:

#### Students Module (prefix: `students_`)
```sql
efir_budget.students_configs               -- Projection settings + scenario multipliers (INPUT)
efir_budget.students_data                  -- Enrollment facts + nationality breakdown (INPUT)
efir_budget.students_overrides             -- Override layers (global/cycle/level) (INPUT)
efir_budget.students_calibration           -- Derived calibration + manual overrides (INPUT)
efir_budget.students_enrollment_projections -- Cached enrollment projections (OUTPUT)
efir_budget.students_class_structures      -- Cached class structures (OUTPUT)
```

#### Teachers Module (prefix: `teachers_`)
```sql
efir_budget.teachers_employees             -- Employee master data (consolidated)
efir_budget.teachers_dhg_requirements      -- DHG hour requirements by subject
efir_budget.teachers_dhg_subject_hours     -- DHG subject hours (per level/subject)
efir_budget.teachers_allocations           -- Teacher allocations (planning input)
-- Legacy tables may still exist for migration safety (e.g., teachers_employee_salaries, teachers_aefe_positions)
```

#### Finance Module (prefix: `finance_`)
```sql
efir_budget.finance_data                   -- Unified fact table (revenue, costs, capex)
efir_budget.finance_consolidations         -- Consolidated budget outputs
efir_budget.finance_statements             -- Generated financial statements (OUTPUT)
efir_budget.finance_statement_lines        -- Statement line outputs (OUTPUT)
-- Backward-compatible views exist for the old plan tables (vw_finance_*)
```

#### Insights Module (prefix: `insights_`)
```sql
efir_budget.insights_kpi_values            -- Calculated KPI values
efir_budget.insights_dashboard_configs     -- Saved dashboard layouts
efir_budget.insights_dashboard_widgets     -- Widgets per dashboard
efir_budget.insights_user_preferences      -- Saved user preferences
efir_budget.insights_budget_vs_actual      -- Variance analysis (legacy; may be replaced by a view)
efir_budget.insights_variance_explanations -- Explanations/notes
efir_budget.insights_actual_data           -- Legacy actuals cache (deprecated by unified versioning)
efir_budget.insights_historical_actuals    -- Legacy historical actuals (deprecated by unified versioning)
```

#### Settings Module (prefix: `settings_` or `ref_`)
```sql
efir_budget.settings_versions              -- Budget versions (CENTRAL - all modules reference)
efir_budget.ref_academic_cycles            -- Academic cycles (STATIC reference)
efir_budget.ref_academic_levels            -- Academic levels (STATIC reference)
efir_budget.ref_subjects                   -- Subject catalog (STATIC reference)
efir_budget.settings_class_size_params     -- Min/max/target class sizes
efir_budget.settings_subject_hours_matrix  -- Hours per subject per level
efir_budget.settings_fee_structure         -- Tuition, DAI, registration fees
efir_budget.settings_teacher_cost_params   -- Teacher cost parameters
efir_budget.settings_timetable_constraints -- Timetable constraints
efir_budget.settings_strategic_plans       -- 5-year projections
```

#### Admin Module (prefix: `admin_`)
```sql
efir_budget.admin_organizations            -- Organization definitions
efir_budget.user_organizations             -- User-org assignments (FK to auth.users)
efir_budget.admin_planning_cells           -- Planning cell registry (writeback)
efir_budget.admin_cell_changes             -- Audit/change tracking
efir_budget.admin_cell_comments            -- Comments/notes
efir_budget.admin_integration_logs         -- Integration logs
efir_budget.admin_historical_comparison_runs -- Historical comparison runs
-- NOTE: Users are in auth.users (Supabase Auth), not in efir_budget schema
```

### 9.3 Cross-Module Reference Rules

| Rule | Requirement |
|------|-------------|
| **MUST** | `version_id` is the ONLY foreign key that crosses module boundaries |
| **MUST** | All data tables reference `efir_budget.settings_versions` via `version_id` |
| **MUST** | Cross-module data flows through services, not direct table references |
| **MUST NOT** | Create direct FKs between tables with different prefixes (except version_id) |

### 9.4 Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         Settings                                │
│  (versions, parameters, academic years, subjects)              │
│  Tables: efir_budget.settings_*, efir_budget.ref_*             │
└─────────────────────────────┬──────────────────────────────────┘
                              │ version_id (FK)
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          Students                               │
│  (enrollment projections, class structure, lateral movements)  │
│  Tables: efir_budget.students_*                                │
└─────────────────────────────┬──────────────────────────────────┘
                              │ student counts, class counts
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          Teachers                               │
│  (DHG requirements, employees, positions, allocations)         │
│  Tables: efir_budget.teachers_*                                │
└─────────────────────────────┬──────────────────────────────────┘
                              │ FTE needs, personnel costs
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                           Finance                               │
│  (revenue, costs, CapEx, financial statements)                 │
│  Tables: efir_budget.finance_*                                 │
└─────────────────────────────┬──────────────────────────────────┘
                              │ all financial data
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          Insights                               │
│  (KPIs, dashboards, variance analysis, reports)                │
│  Tables: efir_budget.insights_*                                │
└────────────────────────────────────────────────────────────────┘

Admin (organizations, users, audit) ─── Tables: efir_budget.admin_* ───
```

### 9.5 Module-to-Old-Section Mapping

This table maps the new 6 modules to existing DB_golden_rules sections:

| New Module | Old Sections | Tables |
|------------|--------------|--------|
| **Students** | 8.6 Students | students_* (configs, data, overrides, outputs) |
| **Teachers** | 8.7 Teachers + 8.8 Personnel | teachers_* (employees, allocations, dhg_*) |
| **Finance** | 8.9 Finance + 8.11 Cost/Profit | finance_data, finance_* outputs, finance_* centers/rules |
| **Insights** | 8.9 (KPI/Dashboard parts) | insights_* (kpis, dashboards, variance) |
| **Settings** | 8.3 Config + 8.10 Strategic + 8.2 STATIC | settings_versions, settings_*, ref_* |
| **Admin** | 8.2 Admin | admin_* (orgs, audit, integration) |

### 9.6 Role-Based Access by Module

| Module | Admin | Finance Dir | HR Manager | Academic Dir | Viewer |
|--------|-------|-------------|------------|--------------|--------|
| Students | CRUD | R | R | CRUD | R |
| Teachers | CRUD | R | CRUD | R | R |
| Finance | CRUD | CRUD | R | R | R |
| Insights | CRUD | RU | R | R | R |
| Settings | CRUD | RU* | RU* | RU* | R |
| Admin | CRUD | - | - | - | - |

*RU = Read + limited Update (version-specific settings only)

### 9.7 Table Prefix Migration Strategy

> **Note**: We use table name prefixes instead of separate PostgreSQL schemas.
> The `efir_budget` schema is our only schema. The `public` schema MUST NOT be touched.

**Implemented (Phase 3B)**: Table-prefix renames are performed via Alembic migration:
- `backend/alembic/versions/20251215_0400_phase_3b_table_prefixes_scenario_type.py`

Examples (historical old → new):
```sql
-- Enrollment outputs
enrollment_projections      → students_enrollment_projections
class_structures            → students_class_structures

-- Central version table
budget_versions             → settings_versions

-- Employees
employees                   → teachers_employees
```

**Do not** run ad-hoc `ALTER TABLE ... RENAME` in production; always ship renames via migrations.

---

## Appendix A: Table Classification

### Tables Requiring organization_id

All business tables except pure global lookups:

```
Admin:     admin_organizations, user_organizations
Settings:  settings_versions, settings_system_configs
Students:  students_data, students_configs, students_overrides, students_calibration,
           students_enrollment_projections, students_class_structures
Teachers:  teachers_employees, teachers_allocations, teachers_dhg_subject_hours, teachers_dhg_requirements
Finance:   finance_data, finance_consolidations, finance_statements, finance_statement_lines
Insights:  insights_kpi_values, insights_dashboard_configs, insights_dashboard_widgets, insights_user_preferences,
           insights_variance_explanations
Audit:     admin_planning_cells, admin_cell_changes, admin_cell_comments

Legacy/Deprecated (still present in some environments):
Insights:  insights_actual_data, insights_budget_vs_actual, insights_historical_actuals
Finance:   finance_revenue_plans, finance_operating_cost_plans, finance_personnel_cost_plans, finance_capex_plans
```

### Pure Global Lookups (No organization_id)

```
ref_academic_cycles      - Same cycles for all French schools
ref_academic_levels      - Same levels for all French schools
ref_subjects             - Standard French curriculum subjects
ref_teacher_categories   - AEFE_DETACHED, AEFE_FUNDED, LOCAL
ref_fee_categories       - TUITION, DAI, REGISTRATION, etc.
ref_nationality_types    - FRENCH, SAUDI, OTHER
ref_kpi_definitions      - Standard KPI catalog (can be extended per-org)
```

---

## Appendix B: Quick Reference Checklist

### New Table Checklist

```markdown
- [ ] UUID PK with gen_random_uuid()
- [ ] organization_id FK (unless global lookup)
- [ ] version_id FK (for versioned data) + fiscal_year column
- [ ] All FK columns indexed
- [ ] created_at, created_by, updated_at, updated_by columns
- [ ] updated_at trigger
- [ ] Unique constraints for business keys
- [ ] Check constraints for data validation
- [ ] NUMERIC(18,4) for monetary amounts
- [ ] TIMESTAMPTZ for timestamps
- [ ] RLS enabled with SELECT/INSERT/UPDATE/DELETE policies
- [ ] Table comment documenting grain
- [ ] Alembic migration created
```

### Migration Checklist

```markdown
- [ ] Forward migration tested
- [ ] Rollback migration tested
- [ ] Indexes created for new FKs
- [ ] RLS policies added
- [ ] Seed data included (if lookup table)
- [ ] Existing data migrated correctly
```

---

**Document Version**: 1.8
**Last Updated**: 2025-12-14
**Maintainer**: Database Team

### Changelog
- v1.8 (2025-12-14): Added Section 9 (Unified Module Architecture) - defined 6-module structure (Students, Teachers, Finance, Insights, Settings, Admin) with PostgreSQL schema mapping, cross-module reference rules, data flow diagram, role-based access matrix, and migration strategy; updated to align with MODULE_ARCHITECTURE_DESIGN.md
- v1.7 (2025-12-14): Added Section 8.11 (Cost/Profit Center Module) - NEW module with 4 tables: `profit_centers` (5: 4 cycles + Other Activities), `cost_centers` (2-level hierarchy with categories), `allocation_rules` (VERSION-LINKED), `allocation_rule_targets`; includes 3 new ENUMs (`cost_center_category`, `allocation_method`, `allocation_base`), calculation engine pattern, integration with `financial_data`, default seed data for EFIR, updated Appendix A
- v1.6 (2025-12-14): Added Section 8.10 (Strategic Module) - added `organization_id`, `version_id`, `based_on_version_id` to `strategic_plans` for multi-tenancy and unified versioning integration, documented lineage tracking pattern and data retrieval queries, updated Appendix A with Strategic module details
- v1.5 (2025-12-14): Added Section 8.9 (Planning/Consolidation/Analysis) - consolidated 4 fact tables → 1 unified `financial_data` table with `record_type` discriminator, deprecated `actual_data`/`historical_actuals`/`budget_vs_actual` (table), converted `budget_vs_actual` and `budget_consolidations` to VIEWs, updated Appendix A
- v1.4 (2025-12-14): Added Sections 8.7 (DHG/Workforce) and 8.8 (Personnel) - `subject_hours_matrix` renamed to `curriculum_hours` (now STATIC), DHG separated from Personnel, Personnel consolidated 4→1 table (`employees` with salary/AEFE info merged), EOS/GOSI calculated on demand (not stored), updated Appendix A with new module allocation
- v1.3 (2025-12-14): Added Section 8.6 Enrollment Module Structure - consolidated 15→6 tables (4 INPUT + 2 OUTPUT), documented key decisions (no enrollment_scenarios, unified enrollment_data, scope_type pattern, class_size in overrides, single calibration table, historical_actuals removal), updated Appendix A table listings
- v1.2 (2025-12-14): Added Section 8 Module Table Allocation Rules - classified tables as STATIC/VERSION-LINKED/ORG-SCOPED, defined module boundaries, documented Enrollment vs Revenue separation decision
- v1.1 (2025-12-14): Added Section 2.6 Unified Versioning, renamed `budget_versions` to `versions`, updated all FK references to use `version_id`
- v1.0 (2025-12-14): Initial DB Constitution
