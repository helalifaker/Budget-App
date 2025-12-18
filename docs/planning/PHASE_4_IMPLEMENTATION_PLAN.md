# Phase 4: Table Consolidation - Implementation Plan

**Status**: IN PROGRESS
**Created**: 2025-12-15
**Phase 3 Completed**: 2025-12-15 (59 tables renamed with module prefixes)

---

## Executive Summary

Phase 4 consolidates tables to reduce complexity while maintaining functionality:

| Module | Before | After | Reduction |
|--------|--------|-------|-----------|
| **Enrollment** | 12 tables | 6 tables | -50% |
| **Personnel** | 7 tables | 4 tables | -43% |
| **Financial** | 7 tables | 1 table + 2 views | -71% |
| **Total** | 26 tables | 11 + 2 views | -54% |

---

## Phase 4A: Enrollment Module Consolidation

### Current Tables (12)

```
students_class_structures          # OUTPUT - keep (add lineage)
students_derived_parameters        # CALIBRATION → merge
students_enrollment_plans          # VERSION-LINKED → merge
students_enrollment_projections    # OUTPUT - keep (add lineage)
students_global_overrides          # OVERRIDE → merge
students_grade_overrides           # OVERRIDE → merge
students_lateral_entry_defaults    # OVERRIDE → merge
students_level_overrides           # OVERRIDE → merge
students_nationality_distributions # VERSION-LINKED → merge
students_parameter_overrides       # CALIBRATION → merge
students_projection_configs        # VERSION-LINKED → merge
students_scenario_multipliers      # VERSION-LINKED → merge
```

### Target Tables (6)

```
students_configs                   # NEW: Merged projection_configs + scenario_multipliers
students_data                      # NEW: Merged enrollment_plans + nationality_distributions
students_overrides                 # NEW: Unified global/level/grade overrides + lateral defaults + class_size_params
students_calibration               # NEW: Merged derived_parameters + parameter_overrides
students_projections               # KEEP: Enhanced with lineage columns
students_class_structures          # KEEP: Enhanced with lineage columns
```

### Migration Steps

#### Step 1: Create New Unified Tables

```sql
-- students_configs: Merge projection_configs + scenario_multipliers
CREATE TABLE efir_budget.students_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id) ON DELETE CASCADE,
    scenario_code VARCHAR(20) NOT NULL DEFAULT 'base',  -- 'worst', 'base', 'best'

    -- From projection_configs
    base_year INTEGER NOT NULL,
    projection_years INTEGER NOT NULL DEFAULT 5,
    school_max_capacity INTEGER NOT NULL DEFAULT 1850,
    default_class_size INTEGER NOT NULL DEFAULT 25,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',
    validated_at TIMESTAMPTZ,
    validated_by UUID,

    -- From scenario_multipliers
    lateral_multiplier NUMERIC(5,2) NOT NULL DEFAULT 1.00,

    -- Audit columns
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID,
    updated_by_id UUID,
    deleted_at TIMESTAMPTZ,

    UNIQUE(version_id, scenario_code, deleted_at)
);

-- students_data: Unified enrollment data
CREATE TABLE efir_budget.students_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id) ON DELETE CASCADE,
    fiscal_year INTEGER NOT NULL,
    level_id UUID NOT NULL REFERENCES efir_budget.ref_academic_levels(id),

    -- Enrollment counts
    student_count INTEGER NOT NULL DEFAULT 0,
    number_of_classes INTEGER,
    avg_class_size NUMERIC(5,2),

    -- Nationality breakdown (from nationality_distributions)
    french_pct NUMERIC(5,2) DEFAULT 0,
    saudi_pct NUMERIC(5,2) DEFAULT 0,
    other_pct NUMERIC(5,2) DEFAULT 0,

    -- Data source tracking
    data_source VARCHAR(20) NOT NULL DEFAULT 'manual',  -- 'manual', 'projected', 'actual', 'imported'

    -- Audit columns
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID,
    updated_by_id UUID,
    deleted_at TIMESTAMPTZ,

    UNIQUE(version_id, fiscal_year, level_id, data_source, deleted_at)
);

-- students_overrides: Unified override layers
CREATE TYPE efir_budget.override_scope AS ENUM ('global', 'cycle', 'level');

CREATE TABLE efir_budget.students_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    config_id UUID NOT NULL REFERENCES efir_budget.students_configs(id) ON DELETE CASCADE,

    -- Scope definition
    scope_type efir_budget.override_scope NOT NULL,
    scope_id UUID,  -- NULL for global, cycle_id for cycle, level_id for level

    -- Override values (from various override tables)
    ps_entry_adjustment INTEGER,
    retention_adjustment NUMERIC(5,4),
    retention_rate NUMERIC(5,4),
    lateral_entry INTEGER,
    lateral_multiplier_override NUMERIC(5,2),

    -- Class size constraints (from class_size_params)
    min_class_size INTEGER,
    max_class_size INTEGER,
    target_class_size INTEGER,
    max_divisions INTEGER,
    class_size_ceiling INTEGER,

    -- Audit
    override_reason TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID,
    updated_by_id UUID,
    deleted_at TIMESTAMPTZ,

    UNIQUE(config_id, scope_type, scope_id, deleted_at)
);

-- students_calibration: Unified calibration parameters
CREATE TYPE efir_budget.calibration_origin AS ENUM ('calculated', 'manual_override');

CREATE TABLE efir_budget.students_calibration (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
    grade_code VARCHAR(10) NOT NULL,

    -- Data origin tracking
    data_origin efir_budget.calibration_origin NOT NULL DEFAULT 'calculated',

    -- Derived parameters (from students_derived_parameters)
    progression_rate NUMERIC(5,4),
    lateral_entry_rate NUMERIC(5,4),
    retention_rate NUMERIC(5,4),
    confidence VARCHAR(20) DEFAULT 'low',
    std_deviation NUMERIC(10,6),
    years_used INTEGER DEFAULT 0,
    source_years JSONB DEFAULT '[]'::jsonb,
    calculated_at TIMESTAMPTZ DEFAULT now(),

    -- Manual overrides (from students_parameter_overrides)
    override_lateral_rate BOOLEAN DEFAULT FALSE,
    manual_lateral_rate NUMERIC(5,4),
    override_retention_rate BOOLEAN DEFAULT FALSE,
    manual_retention_rate NUMERIC(5,4),
    override_fixed_lateral BOOLEAN DEFAULT FALSE,
    manual_fixed_lateral INTEGER,
    override_reason TEXT,

    -- Audit columns
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_by_id UUID,
    updated_by_id UUID,
    deleted_at TIMESTAMPTZ,

    UNIQUE(organization_id, grade_code, deleted_at)
);
```

#### Step 2: Add Lineage Columns to OUTPUT Tables

```sql
-- Add lineage columns to students_projections (formerly students_enrollment_projections)
ALTER TABLE efir_budget.students_enrollment_projections
ADD COLUMN IF NOT EXISTS computed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS computed_by UUID,
ADD COLUMN IF NOT EXISTS run_id UUID,
ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64);

-- Add lineage columns to students_class_structures
ALTER TABLE efir_budget.students_class_structures
ADD COLUMN IF NOT EXISTS computed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS computed_by UUID,
ADD COLUMN IF NOT EXISTS run_id UUID,
ADD COLUMN IF NOT EXISTS inputs_hash VARCHAR(64);
```

#### Step 3: Migrate Data

```sql
-- Migrate projection_configs + scenario_multipliers → students_configs
INSERT INTO efir_budget.students_configs (
    id, version_id, scenario_code, base_year, projection_years,
    school_max_capacity, default_class_size, status, validated_at, validated_by,
    lateral_multiplier, created_at, updated_at, created_by_id, updated_by_id, deleted_at
)
SELECT
    pc.id,
    pc.version_id,
    COALESCE(es.code, 'base') as scenario_code,
    pc.base_year,
    pc.projection_years,
    pc.school_max_capacity,
    pc.default_class_size,
    pc.status,
    pc.validated_at,
    pc.validated_by,
    COALESCE(sm.lateral_multiplier, 1.00) as lateral_multiplier,
    pc.created_at,
    pc.updated_at,
    pc.created_by_id,
    pc.updated_by_id,
    pc.deleted_at
FROM efir_budget.students_projection_configs pc
LEFT JOIN efir_budget.ref_enrollment_scenarios es ON es.id = pc.scenario_id
LEFT JOIN efir_budget.students_scenario_multipliers sm
    ON sm.scenario_code = COALESCE(es.code, 'base');

-- Migrate overrides → students_overrides
-- Global overrides
INSERT INTO efir_budget.students_overrides (
    config_id, scope_type, scope_id,
    ps_entry_adjustment, retention_adjustment, lateral_multiplier_override, max_class_size,
    created_at, updated_at, created_by_id, updated_by_id, deleted_at
)
SELECT
    go.projection_config_id,
    'global'::efir_budget.override_scope,
    NULL,
    go.ps_entry_adjustment,
    go.retention_adjustment,
    go.lateral_multiplier_override,
    go.class_size_override,
    go.created_at,
    go.updated_at,
    go.created_by_id,
    go.updated_by_id,
    go.deleted_at
FROM efir_budget.students_global_overrides go;

-- Level overrides
INSERT INTO efir_budget.students_overrides (
    config_id, scope_type, scope_id,
    class_size_ceiling, max_divisions,
    created_at, updated_at, created_by_id, updated_by_id, deleted_at
)
SELECT
    lo.projection_config_id,
    'cycle'::efir_budget.override_scope,
    lo.cycle_id,
    lo.class_size_ceiling,
    lo.max_divisions,
    lo.created_at,
    lo.updated_at,
    lo.created_by_id,
    lo.updated_by_id,
    lo.deleted_at
FROM efir_budget.students_level_overrides lo;

-- Grade overrides
INSERT INTO efir_budget.students_overrides (
    config_id, scope_type, scope_id,
    retention_rate, lateral_entry, max_divisions, class_size_ceiling,
    created_at, updated_at, created_by_id, updated_by_id, deleted_at
)
SELECT
    gro.projection_config_id,
    'level'::efir_budget.override_scope,
    gro.level_id,
    gro.retention_rate,
    gro.lateral_entry,
    gro.max_divisions,
    gro.class_size_ceiling,
    gro.created_at,
    gro.updated_at,
    gro.created_by_id,
    gro.updated_by_id,
    gro.deleted_at
FROM efir_budget.students_grade_overrides gro;

-- Migrate calibration data
INSERT INTO efir_budget.students_calibration (
    organization_id, grade_code, data_origin,
    progression_rate, lateral_entry_rate, retention_rate, confidence, std_deviation,
    years_used, source_years, calculated_at,
    created_at, updated_at, created_by_id, updated_by_id, deleted_at
)
SELECT
    dp.organization_id,
    dp.grade_code,
    'calculated'::efir_budget.calibration_origin,
    dp.progression_rate,
    dp.lateral_entry_rate,
    dp.retention_rate,
    dp.confidence,
    dp.std_deviation,
    dp.years_used,
    dp.source_years,
    dp.calculated_at,
    dp.created_at,
    dp.updated_at,
    dp.created_by_id,
    dp.updated_by_id,
    dp.deleted_at
FROM efir_budget.students_derived_parameters dp;

-- Update with manual overrides
UPDATE efir_budget.students_calibration c
SET
    data_origin = CASE
        WHEN po.override_lateral_rate OR po.override_retention_rate OR po.override_fixed_lateral
        THEN 'manual_override'::efir_budget.calibration_origin
        ELSE c.data_origin
    END,
    override_lateral_rate = po.override_lateral_rate,
    manual_lateral_rate = po.manual_lateral_rate,
    override_retention_rate = po.override_retention_rate,
    manual_retention_rate = po.manual_retention_rate,
    override_fixed_lateral = po.override_fixed_lateral,
    manual_fixed_lateral = po.manual_fixed_lateral,
    override_reason = po.override_reason
FROM efir_budget.students_parameter_overrides po
WHERE po.organization_id = c.organization_id
  AND po.grade_code = c.grade_code;
```

#### Step 4: Drop Old Tables (After Validation)

```sql
-- Only after validating data migration
DROP TABLE IF EXISTS efir_budget.students_projection_configs CASCADE;
DROP TABLE IF EXISTS efir_budget.students_scenario_multipliers CASCADE;
DROP TABLE IF EXISTS efir_budget.students_global_overrides CASCADE;
DROP TABLE IF EXISTS efir_budget.students_level_overrides CASCADE;
DROP TABLE IF EXISTS efir_budget.students_grade_overrides CASCADE;
DROP TABLE IF EXISTS efir_budget.students_lateral_entry_defaults CASCADE;
DROP TABLE IF EXISTS efir_budget.students_derived_parameters CASCADE;
DROP TABLE IF EXISTS efir_budget.students_parameter_overrides CASCADE;
```

---

## Phase 4B: Personnel Module Consolidation

### Current Tables (7)

```
teachers_employees                 # ORG-SCOPED - keep (enhance)
teachers_employee_salaries         # VERSION-LINKED → merge into employees
teachers_aefe_positions            # VERSION-LINKED → merge into employees
teachers_eos_provisions            # OUTPUT → REMOVE (calculate on demand)
teachers_allocations               # VERSION-LINKED - keep
teachers_dhg_requirements          # OUTPUT - keep (add lineage)
teachers_dhg_subject_hours         # OUTPUT - keep (add lineage)
```

### Target Tables (4)

```
teachers_employees                 # ENHANCED: with salary + AEFE columns
teachers_allocations               # KEEP
teachers_dhg_requirements          # KEEP (add lineage)
teachers_dhg_subject_hours         # KEEP (add lineage)
```

### Migration Steps

1. Add salary columns to `teachers_employees`
2. Add AEFE position columns to `teachers_employees`
3. Migrate data from `teachers_employee_salaries`
4. Migrate data from `teachers_aefe_positions`
5. Drop `teachers_eos_provisions` (calculated on demand)
6. Drop merged tables after validation

---

## Phase 4C: Financial Module Consolidation

### Current Tables (7)

```
finance_revenue_plans              # FACT → merge
finance_personnel_cost_plans       # FACT → merge
finance_operating_cost_plans       # FACT → merge
finance_capex_plans                # FACT → merge
finance_consolidations             # OUTPUT → convert to VIEW
finance_statements                 # OUTPUT - keep
finance_statement_lines            # OUTPUT - keep
```

### Target Structure (1 table + 2 views)

```
finance_data                       # NEW: Unified fact table
vw_finance_consolidations          # VIEW: Aggregated view
finance_statements                 # KEEP
finance_statement_lines            # KEEP
```

### Migration Steps

1. Create `finance_data` unified fact table with `record_type` enum
2. Migrate data from 4 fact tables
3. Create `vw_finance_consolidations` view
4. Update services to use new structure
5. Drop old tables after validation

---

## Implementation Order

1. **Phase 4A**: Enrollment (highest impact, most complex)
2. **Phase 4B**: Personnel (medium complexity)
3. **Phase 4C**: Financial (medium complexity)

Each phase:
1. Create migration with new tables
2. Migrate data
3. Update SQLAlchemy models
4. Update services
5. Update APIs
6. Run tests
7. Drop old tables (separate migration)

---

## Risk Mitigation

1. **Backup before each migration**
2. **Test data migration in staging first**
3. **Keep old tables until fully validated**
4. **Create backward compatibility shims in services**
5. **Run full test suite after each step**

---

## Timeline Estimate

| Phase | Effort | Duration |
|-------|--------|----------|
| 4A: Enrollment | HIGH | 2-3 days |
| 4B: Personnel | MEDIUM | 1-2 days |
| 4C: Financial | MEDIUM | 1-2 days |
| Testing & Validation | HIGH | 2 days |
| **Total** | | **6-9 days** |
