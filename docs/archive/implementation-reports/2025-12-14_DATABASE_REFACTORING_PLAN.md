# EFIR Budget App - Consolidated Database Refactoring Plan

**Created**: 2025-12-14
**Status**: PLANNING - AWAITING USER DECISIONS
**Risk Level**: MEDIUM (phased approach mitigates risk)

---

## Executive Summary

This plan consolidates findings from:
1. Current `DATABASE_SCHEMA.md` (76 tables documented)
2. User's planning document (proposed unified schema)
3. Codebase exploration (7 calculation engines, 12 enrollment tables)

**Key Insight**: The current architecture already follows best practices for calculated vs stored data. The refactoring focuses on:
- Adding cost/profit centers (NEW capability)
- Unifying scenario versioning (SIMPLIFICATION)
- Reducing enrollment tables (12 → 4-6)
- Consolidating financial data tables (6 → 1 unified + views)

---

## Part 0: Module-by-Module Review Decisions

This section documents decisions made during the systematic module review process.

### Configuration Module Review (Completed: 2025-12-14)

**Tables Reviewed**: 15 tables currently under "Configuration"

#### Classification Results

| Table | Classification | Current Module | New Module | Action |
|-------|----------------|----------------|------------|--------|
| `academic_cycles` | STATIC | Configuration | **Admin** | MOVE |
| `academic_levels` | STATIC | Configuration | **Admin** | MOVE |
| `subjects` | STATIC | Configuration | **Admin** | MOVE |
| `teacher_categories` | STATIC | Configuration | **Admin** | MOVE |
| `fee_categories` | STATIC | Configuration | **Admin** | MOVE |
| `nationality_types` | STATIC | Configuration | **Admin** | MOVE |
| `budget_versions` | VERSION-LINKED | Configuration | **Settings** | RENAME to `settings_versions` |
| `system_configs` | ORG-SCOPED | Configuration | **Configuration** | ADD `organization_id` |
| `class_size_params` | VERSION-LINKED | Configuration | **Enrollment (M7)** | MOVE |
| `enrollment_projection_configs` | VERSION-LINKED | Configuration | **Enrollment (M7)** | MOVE |
| `fee_structure` | VERSION-LINKED | Configuration | **Revenue (M10)** | MOVE |
| `teacher_cost_params` | VERSION-LINKED | Configuration | **Workforce/DHG (M8)** | MOVE |
| `subject_hours_matrix` | VERSION-LINKED | Configuration | **Workforce/DHG (M8)** | MOVE |
| `timetable_constraints` | VERSION-LINKED | Configuration | **Workforce/DHG (M8)** | MOVE |
| `dashboard_configs` | UI-LAYER | Configuration | **Analysis (M15-17)** | MOVE, ADD `organization_id` |

#### Key Decisions

1. **STATIC tables → Admin Module**: 6 global lookup tables that are identical across all organizations move to Admin module for centralized management.

2. **VERSION-LINKED tables → Planning Modules**: Tables that change per budget version are allocated to the module that owns their business logic:
   - Enrollment tables → Enrollment Module (M7)
   - Fee tables → Revenue Module (M10)
   - DHG tables → Workforce/DHG Module (M8)

3. **Enrollment vs Revenue**: **KEPT SEPARATE**
   - Rationale: Enrollment is a primary driver feeding multiple modules (Revenue, Class Structure, DHG, Operating Costs)
   - Different teams: Academic/Admissions vs Finance
   - Different questions: "How many students?" vs "How much money?"

4. **Anomalies to Fix**:
   - `system_configs`: Add `organization_id` (currently global, should be org-scoped)
   - `dashboard_configs`: Add `organization_id` and move to Analysis module

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Rename `budget_versions` → `settings_versions`, add `scenario_type` enum | LOW | LOW |
| P1 | Add `organization_id` to `system_configs` | LOW | LOW |
| P1 | Add `organization_id` to `dashboard_configs` | LOW | LOW |
| P2 | Update backend models to reflect new module allocation | MEDIUM | LOW |
| P2 | Update RLS policies for STATIC tables (SELECT-only for users) | MEDIUM | LOW |

---

### Enrollment Module Review (Completed: 2025-12-14)

**Tables Reviewed**: 15 tables currently under "Enrollment"

#### Classification Results

| Table | Classification | Action | Target Table |
|-------|----------------|--------|--------------|
| `enrollment_scenarios` | STATIC | **REMOVE** | Handle via `scenario_code` in configs |
| `enrollment_projection_configs` | VERSION-LINKED | **MERGE** | → `enrollment_configs` |
| `enrollment_scenario_multipliers` | VERSION-LINKED | **MERGE** | → `enrollment_configs` |
| `enrollment_plans` | VERSION-LINKED | **MERGE** | → `enrollment_data` |
| `enrollment_projections` | OUTPUT | **KEEP** | Add lineage columns |
| `nationality_distributions` | VERSION-LINKED | **MERGE** | → `enrollment_data` |
| `enrollment_global_overrides` | OVERRIDE | **MERGE** | → `enrollment_overrides` (scope='global') |
| `enrollment_level_overrides` | OVERRIDE | **MERGE** | → `enrollment_overrides` (scope='cycle') |
| `enrollment_grade_overrides` | OVERRIDE | **MERGE** | → `enrollment_overrides` (scope='level') |
| `enrollment_lateral_entry_defaults` | OVERRIDE | **MERGE** | → `enrollment_overrides` |
| `class_size_params` | VERSION-LINKED | **MERGE** | → `enrollment_overrides` (scope='level') |
| `enrollment_derived_parameters` | CALIBRATION | **MERGE** | → `enrollment_calibration` |
| `enrollment_parameter_overrides` | CALIBRATION | **MERGE** | → `enrollment_calibration` |
| `class_structures` | OUTPUT | **KEEP** | Add lineage columns |
| `historical_actuals` | DEPRECATED | **REMOVE** | Use unified versioning (scenario_type='ACTUAL') |

#### Key Decisions

1. **No `enrollment_scenarios` table**: Handle worst/base/best scenarios via `scenario_code` column in `enrollment_configs`. Simplifies the model.

2. **Unified `enrollment_data`**: Merge `enrollment_plans`, `enrollment_projections` (cached), and `nationality_distributions` into one table with `data_source` column ('manual', 'projected', 'actual', 'imported').

3. **Unified `enrollment_overrides`**: All override layers merged into ONE table using `scope_type` pattern:
   - `scope_type`: 'global' | 'cycle' | 'level'
   - `scope_id`: NULL for global, cycle_id for cycle, level_id for level
   - Includes class size parameters (min/max/target) - merged from `class_size_params`

4. **Single `enrollment_calibration`**: Merge derived parameters + manual overrides into one table with `data_origin` column ('calculated', 'manual_override').

5. **OUTPUT tables follow DB Golden Rules**: Both `enrollment_projections` and `class_structures` must have lineage columns:
   - `computed_at`, `computed_by`, `run_id`, `inputs_hash`
   - `version_id`, `fiscal_year`

6. **`historical_actuals` REMOVED**: Replaced by unified versioning - actuals stored in `enrollment_data` with version having `scenario_type='ACTUAL'`.

#### Final Enrollment Module Structure (6 tables)

```
ENROLLMENT MODULE (M7) ─────────────────────────────────────────

INPUT TABLES (4):
├── enrollment_configs         (VERSION-LINKED)
│   ├── version_id FK
│   ├── scenario_code: 'worst' | 'base' | 'best'
│   ├── base_year, projection_years, school_max_capacity
│   └── lateral_multiplier (from enrollment_scenario_multipliers)
│
├── enrollment_data            (VERSION-LINKED)
│   ├── version_id FK, fiscal_year
│   ├── level_id, nationality_type_id
│   ├── student_count, number_of_classes, avg_class_size
│   └── data_source: 'manual' | 'projected' | 'actual' | 'imported'
│
├── enrollment_overrides       (VERSION-LINKED)
│   ├── version_id FK
│   ├── scope_type: 'global' | 'cycle' | 'level'
│   ├── scope_id (NULL for global, or cycle_id/level_id)
│   ├── Override values: retention_rate, lateral_entry, lateral_multiplier
│   ├── Class sizes: min_class_size, max_class_size, target_class_size, max_divisions
│   └── override_reason TEXT
│
└── enrollment_calibration     (ORG-SCOPED)
    ├── organization_id FK
    ├── grade_code
    ├── data_origin: 'calculated' | 'manual_override'
    ├── Derived: progression_rate, lateral_entry_rate, retention_rate, confidence
    └── Overrides: manual_lateral_rate, manual_retention_rate, override_reason

OUTPUT TABLES (2):
├── enrollment_projections     (OUTPUT with lineage)
│   ├── version_id FK, fiscal_year
│   ├── level_id, nationality_type_id
│   ├── student_count, number_of_classes, avg_class_size
│   └── Lineage: computed_at, computed_by, run_id, inputs_hash
│
└── class_structures           (OUTPUT with lineage)
    ├── version_id FK, fiscal_year
    ├── level_id
    ├── student_count, number_of_classes, avg_class_size
    └── Lineage: computed_at, computed_by, run_id, inputs_hash
```

#### Table Consolidation Summary

| Before (15 tables) | After (6 tables) | Change |
|--------------------|------------------|--------|
| enrollment_scenarios | REMOVED | -1 |
| enrollment_projection_configs | → enrollment_configs | |
| enrollment_scenario_multipliers | → enrollment_configs | |
| enrollment_plans | → enrollment_data | |
| nationality_distributions | → enrollment_data | |
| enrollment_global_overrides | → enrollment_overrides | |
| enrollment_level_overrides | → enrollment_overrides | |
| enrollment_grade_overrides | → enrollment_overrides | |
| enrollment_lateral_entry_defaults | → enrollment_overrides | |
| class_size_params | → enrollment_overrides | |
| enrollment_derived_parameters | → enrollment_calibration | |
| enrollment_parameter_overrides | → enrollment_calibration | |
| enrollment_projections | KEEP (add lineage) | |
| class_structures | KEEP (add lineage) | |
| historical_actuals | REMOVED | -1 |
| **TOTAL** | **15 → 6** | **-60%** |

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Create `enrollment_configs` with scenario_code | MEDIUM | LOW |
| P0 | Create `enrollment_data` unified table | MEDIUM | MEDIUM |
| P0 | Create `enrollment_overrides` with scope_type | MEDIUM | LOW |
| P0 | Create `enrollment_calibration` merged table | LOW | LOW |
| P1 | Add lineage columns to OUTPUT tables | LOW | LOW |
| P1 | Migrate data from old tables to new structure | HIGH | MEDIUM |
| P2 | Remove deprecated tables after validation | LOW | LOW |
| P2 | Update backend services and APIs | MEDIUM | MEDIUM |

---

### DHG/Workforce Module Review (Completed: 2025-12-14)

**Tables Reviewed**: 12 tables related to DHG and teacher workforce planning

#### Classification Results

| Table | Classification | Current Module | New Module | Action |
|-------|----------------|----------------|------------|--------|
| `subject_hours_matrix` | STATIC | Configuration | **Admin** | RENAME to `curriculum_hours`, MOVE |
| `teacher_cost_params` | VERSION-LINKED | Configuration | **Workforce/DHG (M8)** | MOVE |
| `timetable_constraints` | VERSION-LINKED | Configuration | **Workforce/DHG (M8)** | MOVE |
| `teacher_allocations` | VERSION-LINKED | Planning | **Workforce/DHG (M8)** | MOVE |
| `dhg_subject_hours` | OUTPUT | Planning | **Workforce/DHG (M8)** | ADD lineage columns |
| `dhg_teacher_requirements` | OUTPUT | Planning | **Workforce/DHG (M8)** | ADD lineage columns |

#### Key Decisions

1. **`subject_hours_matrix` → `curriculum_hours` (STATIC)**:
   - Rationale: Contains AEFE/Ministry of Education official curriculum data
   - This data is identical across all organizations and budget versions
   - Renamed to clarify it represents curriculum standards, not configuration
   - Moved to Admin module alongside other STATIC reference tables

2. **Keep separate from `subjects` table**:
   - `subjects`: Subject metadata (name, code)
   - `curriculum_hours`: Hours per subject **per level** (~200 rows)
   - Different grain - cannot merge

3. **DHG vs Personnel SEPARATION**:
   - DHG = Aggregate workforce planning ("How many FTE do we need?")
   - Personnel = Individual employee management ("Who works here?")
   - Different users: DHG used by Academic Director, Personnel used by HR
   - Different timing: DHG is planning, Personnel is operational

4. **HSA configuration**:
   - HSA (overtime) configuration stays in `teacher_cost_params`
   - `hsa_hourly_rate`, `max_hsa_hours_per_teacher` are cost parameters
   - No separate HSA configuration table needed

5. **OUTPUT tables follow DB Golden Rules**:
   - Both `dhg_subject_hours` and `dhg_teacher_requirements` must have lineage columns
   - `computed_at`, `computed_by`, `run_id`, `inputs_hash`

#### Final DHG/Workforce Module Structure (5 tables + 1 STATIC)

```
ADMIN MODULE (STATIC Reference) ─────────────────────────────────
└── curriculum_hours        (AEFE hours per subject/level - ~200 rows)
    (renamed from subject_hours_matrix)

WORKFORCE/DHG MODULE (M8) ───────────────────────────────────────

INPUT TABLES (3):
├── teacher_cost_params     (VERSION-LINKED)
│   ├── version_id FK
│   ├── category_id (AEFE_DETACHED, AEFE_FUNDED, LOCAL)
│   ├── basic_salary_range, prrd_amount_eur
│   └── hsa_hourly_rate, max_hsa_hours
│
├── timetable_constraints   (VERSION-LINKED)
│   ├── version_id FK, level_id
│   ├── max_hours_per_day, min_break_minutes
│   └── max_consecutive_hours
│
└── teacher_allocations     (VERSION-LINKED) - TRMD
    ├── version_id FK, fiscal_year
    ├── employee_id, subject_id, level_id
    └── hours_per_week, is_primary_assignment

OUTPUT TABLES (2):
├── dhg_subject_hours       (OUTPUT with lineage)
│   ├── version_id FK, fiscal_year
│   ├── subject_id, level_id
│   ├── total_hours = class_count × curriculum_hours
│   └── Lineage: computed_at, computed_by, run_id, inputs_hash
│
└── dhg_teacher_requirements (OUTPUT with lineage)
    ├── version_id FK, fiscal_year
    ├── subject_id, category_id
    ├── required_fte = total_hours ÷ standard_hours
    └── Lineage: computed_at, computed_by, run_id, inputs_hash
```

#### Calculation Flow

```
curriculum_hours (STATIC)
        │
        ▼
class_structures × curriculum_hours = dhg_subject_hours
        │
        ▼
dhg_subject_hours ÷ standard_hours = dhg_teacher_requirements (FTE)
        │                                    (18h secondary, 24h primary)
        ▼
teacher_allocations (TRMD) - Actual assignments
        │
        ▼
Gap Analysis = Required FTE - Allocated FTE
```

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Rename `subject_hours_matrix` → `curriculum_hours` | LOW | LOW |
| P0 | Remove `version_id` FK from `curriculum_hours` (make STATIC) | LOW | MEDIUM |
| P1 | Move tables to Workforce/DHG module in backend models | LOW | LOW |
| P1 | Add lineage columns to OUTPUT tables | LOW | LOW |
| P2 | Update RLS for `curriculum_hours` (SELECT-only) | LOW | LOW |
| P2 | Update backend services to use new module structure | MEDIUM | LOW |

---

### Personnel Module Review (Completed: 2025-12-14)

**Tables Reviewed**: 4 tables related to employee management

#### Classification Results

| Table | Classification | Current Module | New Module | Action |
|-------|----------------|----------------|------------|--------|
| `employees` | ORG-SCOPED | Personnel | **Personnel (M14)** | KEEP, add columns |
| `employee_salaries` | VERSION-LINKED | Personnel | **Personnel (M14)** | **MERGE** → `employees` |
| `aefe_positions` | VERSION-LINKED | Personnel | **Personnel (M14)** | **MERGE** → `employees` |
| `eos_provisions` | OUTPUT | Personnel | N/A | **REMOVE** (calculate on demand) |

#### Key Decisions

1. **Consolidate 4 tables → 1 table (`employees`)**:
   - Salary info merged directly into `employees` table
   - AEFE position info merged directly into `employees` table
   - Reduces joins and simplifies queries
   - Historical tracking via unified versioning (ACTUAL versions per period)

2. **Remove `eos_provisions` table**:
   - EOS (End of Service) liability is calculated on demand by EOS engine
   - Value changes with every calculation (depends on current date)
   - If snapshot needed, use version with `scenario_type='ACTUAL'`

3. **GOSI calculated on demand**:
   - No GOSI table ever existed (already correct)
   - GOSI engine calculates based on employee nationality and salary
   - Pure function: `if nationality == 'SAUDI' then employer=12%, employee=10%`

4. **Historical salary tracking via versioning**:
   - No separate salary history table
   - When salary changes, old values captured in ACTUAL version snapshot
   - Compare versions to see salary progression

5. **AEFE position info as employee attributes**:
   - `aefe_position_code`, `aefe_funding_type`, `prrd_eligible`
   - NULL for LOCAL employees
   - Check constraint ensures AEFE columns populated only for AEFE categories

#### Final Personnel Module Structure (1 table)

```
PERSONNEL MODULE (M14) ──────────────────────────────────────────

└── employees               (ORG-SCOPED, consolidated)
    ├── organization_id FK
    │
    ├── Identity: employee_code, first_name, last_name
    ├── Employment: hire_date, termination_date, nationality
    ├── Category: category_id (AEFE_DETACHED, AEFE_FUNDED, LOCAL)
    │
    ├── AEFE Info (merged from aefe_positions):
    │   ├── aefe_position_code (NULL for LOCAL)
    │   ├── aefe_funding_type ('detached' | 'funded' | NULL)
    │   └── prrd_eligible (FALSE for LOCAL)
    │
    ├── Salary Info (merged from employee_salaries):
    │   ├── basic_salary_sar
    │   ├── housing_allowance_sar
    │   ├── transport_allowance_sar
    │   └── effective_from
    │
    ├── Teaching Info (for teachers):
    │   ├── is_teacher, subject_id
    │   └── teaches_secondary, teaches_primary
    │
    └── Status: is_active
```

#### EOS/GOSI Engine Pattern

```python
# EOS: Pure function, no database writes
def calculate_eos(employee: Employee, as_of_date: date) -> EOSResult:
    service_years = (as_of_date - employee.hire_date).days / 365.25
    return EOSResult(
        eos_liability_sar=compute_liability(employee.basic_salary_sar, service_years),
        service_years=service_years
    )

# GOSI: Pure function, no database writes
def calculate_gosi(employee: Employee) -> GOSIResult:
    if employee.nationality == 'SAUDI':
        return GOSIResult(employer_rate=0.12, employee_rate=0.10)
    return GOSIResult(employer_rate=0, employee_rate=0)
```

#### Table Consolidation Summary

| Before (4 tables) | After (1 table) | Change |
|-------------------|-----------------|--------|
| employees | employees (enhanced) | KEEP |
| employee_salaries | → employees | MERGED |
| aefe_positions | → employees | MERGED |
| eos_provisions | REMOVED | DELETED |
| **TOTAL** | **4 → 1** | **-75%** |

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Add salary columns to `employees` table | LOW | LOW |
| P0 | Add AEFE columns to `employees` table | LOW | LOW |
| P1 | Migrate data from `employee_salaries` to `employees` | MEDIUM | MEDIUM |
| P1 | Migrate data from `aefe_positions` to `employees` | MEDIUM | MEDIUM |
| P2 | Drop `eos_provisions` table | LOW | LOW |
| P2 | Drop `employee_salaries` table (after validation) | LOW | LOW |
| P2 | Drop `aefe_positions` table (after validation) | LOW | LOW |
| P2 | Update backend services and APIs | MEDIUM | MEDIUM |

---

### Planning/Consolidation/Analysis Module Review (Completed: 2025-12-14)

**Tables Reviewed**: 20 tables across Planning, Consolidation, and Analysis modules

#### Classification Results

| Table | Classification | Current Module | Action | Notes |
|-------|----------------|----------------|--------|-------|
| `revenue_plans` | FACT | Planning | **MERGE** → `financial_data` | record_type='revenue' |
| `personnel_cost_plans` | FACT | Planning | **MERGE** → `financial_data` | record_type='personnel' |
| `operating_cost_plans` | FACT | Planning | **MERGE** → `financial_data` | record_type='operating' |
| `capex_plans` | FACT | Planning | **MERGE** → `financial_data` | record_type='capex' |
| `budget_consolidations` | OUTPUT | Consolidation | **CONVERT** → VIEW | Computed on demand |
| `financial_statements` | OUTPUT | Consolidation | **KEEP** | Statement headers |
| `financial_statement_lines` | OUTPUT | Consolidation | **KEEP** | Statement line items |
| `kpi_definitions` | STATIC | Analysis | **KEEP** | No org_id (correct pattern) |
| `kpi_values` | OUTPUT | Analysis | **KEEP** | Add lineage columns |
| `dashboard_configs` | UI-LAYER | Analysis | **KEEP** | Add org_id |
| `dashboard_widgets` | UI-LAYER | Analysis | **KEEP** | Needs org_id |
| `user_preferences` | UI-LAYER | Analysis | **KEEP** | Needs org_id |
| `actual_data` | DEPRECATED | Analysis | **REMOVE** | Use unified versioning |
| `budget_vs_actual` | DEPRECATED | Analysis | **CONVERT** → VIEW | Computed on demand |
| `variance_explanations` | AUDIT | Analysis | **KEEP** | Variance notes |
| `historical_actuals` | DEPRECATED | Analysis | **REMOVE** | Use ACTUAL versions |

#### Key Decisions

1. **Consolidate 4 Fact Tables → 1 Unified `financial_data` Table**:
   - `revenue_plans`, `personnel_cost_plans`, `operating_cost_plans`, `capex_plans` → `financial_data`
   - Use `record_type` ENUM discriminator: 'revenue' | 'personnel' | 'operating' | 'capex'
   - CapEx-specific columns (`acquisition_date`, `useful_life_years`) nullable with CHECK constraint
   - Personnel-specific column (`fte_count`) nullable with CHECK constraint
   - Revenue-specific column (`trimester`) nullable with CHECK constraint

2. **Deprecate `actual_data` Table**:
   - Rationale: Use unified versioning - actuals stored in `financial_data` with version having `scenario_type='ACTUAL'`
   - Avoids data duplication and inconsistent schemas

3. **Convert `budget_vs_actual` to VIEW**:
   - Rationale: Variance is always computed fresh from BUDGET vs ACTUAL versions
   - No stale data - always reflects current approved versions
   - View joins `financial_data` for both scenario types and computes variance

4. **Deprecate `historical_actuals` Table**:
   - Rationale: Historical data accessed via ACTUAL versions from previous fiscal years
   - Query: `SELECT * FROM financial_data WHERE version_id IN (SELECT id FROM versions WHERE scenario_type='ACTUAL' AND fiscal_year = ?)`

5. **Convert `budget_consolidations` to VIEW**:
   - Rationale: Aggregations computed on demand - always fresh
   - Groups `financial_data` by version, record_type, account_code
   - No need to maintain separate aggregation table

6. **`kpi_definitions` is Correctly STATIC**:
   - Already has no `organization_id` (correct for global KPI catalog)
   - Can be extended per-org by adding org-specific KPIs to `kpi_values`

7. **UI-LAYER Tables Need `organization_id`**:
   - `dashboard_configs`, `dashboard_widgets`, `user_preferences` need org_id for multi-tenancy
   - Add migration to add `organization_id` FK

#### Final Planning/Consolidation/Analysis Module Structure

```
PLANNING MODULE (Financial Facts) ─────────────────────────────────
└── financial_data               (UNIFIED FACT TABLE)
    ├── version_id FK, fiscal_year
    ├── record_type: 'revenue' | 'personnel' | 'operating' | 'capex'
    ├── account_code, description, category
    ├── amount_sar, quantity, unit_cost_sar
    ├── Type-specific: fte_count, trimester, acquisition_date, useful_life_years
    ├── Allocation: cost_center_id, profit_center_id
    └── Lineage: computed_at, computed_by, run_id, inputs_hash

CONSOLIDATION MODULE ───────────────────────────────────────────────
├── vw_budget_consolidations     (VIEW - replaces table)
│   └── Aggregates financial_data by version, record_type, account
│
├── financial_statements         (OUTPUT)
│   ├── version_id FK, fiscal_year
│   ├── statement_type: 'income' | 'balance' | 'cash_flow'
│   └── Lineage columns
│
└── financial_statement_lines    (OUTPUT - child of statements)
    ├── statement_id FK
    ├── account_code, description, amount_sar
    └── line_order, indent_level

ANALYSIS MODULE ────────────────────────────────────────────────────
├── vw_budget_vs_actual          (VIEW - replaces table)
│   └── Compares approved BUDGET vs ACTUAL versions
│
├── kpi_definitions              (STATIC - no org_id)
│   ├── code, name_fr, name_en
│   ├── formula, unit, target_direction
│   └── category, display_order
│
├── kpi_values                   (OUTPUT)
│   ├── version_id FK, fiscal_year
│   ├── kpi_definition_id FK
│   ├── value, calculation_inputs (JSONB)
│   └── Lineage columns
│
├── dashboard_configs            (UI-LAYER)
│   ├── organization_id FK (ADD)
│   ├── user_id FK, name, layout_config
│   └── is_default, is_shared
│
├── dashboard_widgets            (UI-LAYER)
│   ├── dashboard_config_id FK
│   ├── widget_type, title, config (JSONB)
│   └── position_x, position_y, width, height
│
├── user_preferences             (UI-LAYER)
│   ├── organization_id FK (ADD)
│   ├── user_id FK
│   └── preferences (JSONB)
│
└── variance_explanations        (AUDIT)
    ├── budget_vs_actual reference (via account_code, fiscal_year)
    ├── explanation TEXT
    └── created_by, created_at
```

#### Table Consolidation Summary

| Before (20 tables) | After (9 tables + 2 views) | Change |
|--------------------|---------------------------|--------|
| revenue_plans | → financial_data | MERGED |
| personnel_cost_plans | → financial_data | MERGED |
| operating_cost_plans | → financial_data | MERGED |
| capex_plans | → financial_data | MERGED |
| actual_data | REMOVED | DEPRECATED |
| historical_actuals | REMOVED | DEPRECATED |
| budget_vs_actual | → vw_budget_vs_actual | VIEW |
| budget_consolidations | → vw_budget_consolidations | VIEW |
| financial_statements | KEEP | |
| financial_statement_lines | KEEP | |
| kpi_definitions | KEEP (STATIC) | |
| kpi_values | KEEP (OUTPUT) | |
| dashboard_configs | KEEP (UI-LAYER) | Add org_id |
| dashboard_widgets | KEEP (UI-LAYER) | |
| user_preferences | KEEP (UI-LAYER) | Add org_id |
| variance_explanations | KEEP (AUDIT) | |
| **TOTAL** | **16 → 9 + 2 views** | **-44%** |

#### Unified `finance_data` Table Design

> **CANONICAL DESIGN**: See Part 2, Section 2.3 for the complete `efir_budget.finance_data` table definition with all columns, indexes, and views.

The table handles all financial record types (revenue, personnel, operating, capex) using:
- `record_type` enum as discriminator
- `version_id` FK to `settings_versions` (unified versioning)
- `cost_center_id` / `profit_center_id` for allocation tracking
- `data_source` enum (planned/actual/imported/calculated)

**Key Design Decisions**:
1. **Single table over separate tables**: Enables unified reporting, consolidation views, and simpler queries
2. **Type-specific columns are nullable**: CapEx columns (acquisition_date, useful_life_years) only populated for capex records
3. **Cost/Profit center links**: Enables cost allocation and departmental reporting
4. **Table prefix**: Named `finance_data` (not `financial_data`) per module prefix convention

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Create `finance_data` unified table | MEDIUM | LOW |
| P0 | Create `record_type` and `data_source` enums | LOW | LOW |
| P1 | Migrate 4 fact tables → finance_data | HIGH | MEDIUM |
| P2 | Create vw_budget_vs_actual VIEW | LOW | LOW |
| P2 | Create vw_budget_consolidation VIEW | LOW | LOW |
| P2 | Add org_id to dashboard_configs | LOW | LOW |
| P2 | Add org_id to user_preferences | LOW | LOW |
| P3 | Drop deprecated tables | LOW | LOW |
| P3 | Update backend services and APIs | HIGH | MEDIUM |

---

### Strategic Module Review (Completed: 2025-12-14)

**Tables Reviewed**: 4 tables for 5-Year Strategic Planning (Module 18)

#### Classification Results

| Table | Classification | Current Module | Action | Notes |
|-------|----------------|----------------|--------|-------|
| `strategic_plans` | VERSION-LINKED | Strategic | **ENHANCE** | Add org_id, version_id, based_on_version_id |
| `strategic_plan_scenarios` | VERSION-LINKED | Strategic | **KEEP** | Inherits org_id via parent FK |
| `strategic_plan_projections` | OUTPUT | Strategic | **KEEP** | Calculation inputs stored as JSONB |
| `strategic_initiatives` | VERSION-LINKED | Strategic | **KEEP** | Inherits org_id via parent FK |

#### Issues Identified & Fixed

| Issue | Before | After |
|-------|--------|-------|
| Missing multi-tenancy | No `organization_id` on `strategic_plans` | Add `organization_id` FK |
| Global unique constraint | `UNIQUE(name)` | Change to `UNIQUE(organization_id, name)` |
| No version integration | No link to `versions` table | Add `version_id` FK for unified versioning |
| No lineage tracking | Unknown starting point | Add `based_on_version_id` FK |

#### Key Decisions

1. **Add `organization_id` to `strategic_plans`**: Multi-tenancy requirement. Each organization should have isolated strategic plans.

2. **Integrate with Unified Versioning**: Following DB_golden_rules.md Section 2.6, strategic plans should link to `versions` table with `scenario_type='STRATEGIC'`. This enables:
   - Consistent version lifecycle (draft → approved → archived)
   - Historical data retrieval via version_id
   - Lineage tracking back to source BUDGET

3. **Add `based_on_version_id` for Lineage**: Tracks which BUDGET version was the starting point for the strategic plan. Example: "5-Year Plan 2025-2030 was based on approved Budget 2024".

4. **Keep 4 Tables (No Reduction)**: The hierarchical structure is correct:
   - `strategic_plans` → `strategic_plan_scenarios` → `strategic_plan_projections`
   - `strategic_plans` → `strategic_initiatives`

   This pattern is appropriate for scenario modeling (base_case, conservative, optimistic).

5. **Projections Keep `calculation_inputs` JSONB**: Unlike financial_data, strategic projections need to store the calculation inputs (base amounts, growth rates applied) for audit and transparency.

#### Final Strategic Module Structure (4 tables - enhanced)

```
STRATEGIC MODULE (M18) ─────────────────────────────────────────

├── strategic_plans               (VERSION-LINKED, enhanced)
│   ├── organization_id FK        (NEW)
│   ├── version_id FK → versions  (NEW, scenario_type='STRATEGIC')
│   ├── based_on_version_id FK    (NEW, lineage to source BUDGET)
│   ├── name, description, base_year
│   └── status: 'draft' | 'approved' | 'archived'
│
├── strategic_plan_scenarios      (Inherits org via strategic_plan_id)
│   ├── strategic_plan_id FK (CASCADE)
│   ├── scenario_type: base_case, conservative, optimistic, new_campus
│   ├── Growth rates: enrollment, fee, salary, operating
│   └── additional_assumptions JSONB
│
├── strategic_plan_projections    (OUTPUT with calculation inputs)
│   ├── strategic_plan_scenario_id FK (CASCADE)
│   ├── year INT (1-5), category ENUM
│   ├── amount_sar
│   └── calculation_inputs JSONB
│
└── strategic_initiatives         (Inherits org via strategic_plan_id)
    ├── strategic_plan_id FK (CASCADE)
    ├── name, planned_year (1-5)
    ├── capex_amount_sar, operating_impact_sar
    └── status: planned, approved, in_progress, completed, cancelled
```

#### Version Integration Pattern

When creating a strategic plan:

1. Create `versions` row with:
   - `scenario_type = 'STRATEGIC'`
   - `fiscal_year = base_year` (start of 5Y plan)
   - `end_fiscal_year = base_year + 4` (end of 5Y plan)

2. Create `strategic_plans` row with:
   - `version_id` → the version created above
   - `based_on_version_id` → the BUDGET version used as starting point

This enables querying historical strategic plans and comparing projections to actuals.

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Add `organization_id` FK to `strategic_plans` | LOW | MEDIUM |
| P0 | Add `version_id` FK to `strategic_plans` | LOW | LOW |
| P0 | Add `based_on_version_id` FK to `strategic_plans` | LOW | LOW |
| P1 | Change unique constraint `(name)` → `(organization_id, name)` | LOW | LOW |
| P1 | Add CHECK constraint: linked version must have `scenario_type='STRATEGIC'` | LOW | LOW |
| P2 | Update backend services to create version when creating strategic plan | MEDIUM | MEDIUM |
| P2 | Update RLS policies for all strategic tables | MEDIUM | LOW |
| P3 | Migrate existing strategic plans (assign org_id, create versions) | MEDIUM | MEDIUM |

---

### Cost/Profit Center Module Design (NEW MODULE) (Completed: 2025-12-14)

**Purpose**: Add two new financial dimensions for expense and revenue attribution.

#### Module Overview

```
┌────────────────────────────────────────────────────────────────────────────┐
│                       COST/PROFIT CENTER MODULE                            │
├────────────────────────────────────────────────────────────────────────────┤
│  PROFIT CENTERS (5)                    COST CENTERS (2-level hierarchy)    │
│  ├── Maternelle                        ├── Teaching                        │
│  ├── Élémentaire                       │   ├── Primary Teachers            │
│  ├── Collège                           │   ├── Secondary Teachers          │
│  ├── Lycée                             │   └── Language Teachers           │
│  └── Autres Activités                  ├── Administrative                  │
│      (Sports, After-school)            │   ├── Direction                   │
│                                        │   └── Admin Staff                 │
│  4 academic cycles + 1 for Other       ├── Support Services                │
│                                        │   ├── IT & Technology             │
│                                        │   └── Maintenance                 │
│                                        └── Overhead                        │
│                                            ├── Facilities                  │
│                                            └── General Services            │
└────────────────────────────────────────────────────────────────────────────┘
```

#### Table Structure (4 NEW tables + 3 ENUMs)

| Table | Classification | Has org_id? | Has version_id? | Purpose |
|-------|----------------|-------------|-----------------|---------|
| `profit_centers` | ORG-SCOPED | YES | NO | Revenue attribution by academic cycle |
| `cost_centers` | ORG-SCOPED | YES | NO | Expense attribution by department |
| `allocation_rules` | VERSION-LINKED | YES (via version) | YES | How costs are allocated |
| `allocation_rule_targets` | VERSION-LINKED | (inherited) | (inherited) | Target profit centers per rule |

#### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **5 Profit Centers** | 4 academic cycles (Maternelle, Élémentaire, Collège, Lycée) + 1 for Other Activities (sports, after-school) |
| **2-level hierarchy max** | Simple structure; can extend later if needed |
| **Centers are ORG-SCOPED** | Stable organization structure, not versioned |
| **Rules are VERSION-LINKED** | Allocation percentages can change per budget version |
| **No cross-org templates** | Single organization (EFIR); templates can be added later |
| **No allocation_results table** | Allocated data stored in `financial_data` with `profit_center_id` set |
| **Calculation in engine** | Allocation engine computes on demand; results stored with lineage |

#### ENUMs to Create

```sql
-- Cost center classification
CREATE TYPE efir_budget.cost_center_category AS ENUM (
    'teaching',        -- Teaching departments
    'administrative',  -- Admin & direction
    'support',         -- Support services (IT, maintenance)
    'overhead'         -- Facilities, general
);

-- Allocation method
CREATE TYPE efir_budget.allocation_method AS ENUM (
    'proportional_enrollment',   -- By student count per profit center
    'proportional_fte',          -- By teacher FTE per profit center
    'proportional_revenue',      -- By revenue amount per profit center
    'fixed_percentage',          -- Fixed % split (defined in targets)
    'step_down'                  -- Cascade allocation
);

-- Allocation base (for proportional methods)
CREATE TYPE efir_budget.allocation_base AS ENUM (
    'enrollment',   -- Student count
    'fte',          -- Full-time equivalent
    'revenue',      -- Revenue amount
    'headcount',    -- Employee count
    'square_meters' -- Facility space
);
```

#### Integration with Existing Tables

The `financial_data` table (Section 8.9 of DB_golden_rules.md) already has:
```sql
cost_center_id UUID REFERENCES efir_budget.cost_centers(id),
profit_center_id UUID REFERENCES efir_budget.profit_centers(id),
```

Financial records are tagged with source cost center; the allocation engine computes and sets `profit_center_id`.

#### Default Seed Data

**Profit Centers (5)**:
| Code | Name (FR) | Name (EN) | Cycle |
|------|-----------|-----------|-------|
| PC-MAT | Maternelle | Preschool | Maternelle |
| PC-ELEM | Élémentaire | Elementary | Élémentaire |
| PC-COL | Collège | Middle School | Collège |
| PC-LYC | Lycée | High School | Lycée |
| PC-OTHER | Autres Activités | Other Activities | (none) |

**Cost Centers (4 Level-1 + 9 Level-2)**:
| Code | Name (FR) | Category | Parent |
|------|-----------|----------|--------|
| CC-TEACH | Enseignement | teaching | - |
| CC-TCH-PRI | Enseignants Primaire | teaching | CC-TEACH |
| CC-TCH-SEC | Enseignants Secondaire | teaching | CC-TEACH |
| CC-TCH-LNG | Enseignants Langues | teaching | CC-TEACH |
| CC-ADMIN | Administration | administrative | - |
| CC-ADM-DIR | Direction | administrative | CC-ADMIN |
| CC-ADM-SEC | Secrétariat | administrative | CC-ADMIN |
| CC-SUPP | Support | support | - |
| CC-SUP-IT | Informatique | support | CC-SUPP |
| CC-SUP-MNT | Maintenance | support | CC-SUPP |
| CC-OVER | Frais Généraux | overhead | - |
| CC-OVR-FAC | Bâtiments | overhead | CC-OVER |
| CC-OVR-GEN | Services Généraux | overhead | CC-OVER |

#### Migration Actions Required

| Priority | Action | Effort | Risk |
|----------|--------|--------|------|
| P0 | Create `cost_center_category` ENUM | LOW | LOW |
| P0 | Create `allocation_method` ENUM | LOW | LOW |
| P0 | Create `allocation_base` ENUM | LOW | LOW |
| P0 | Create `profit_centers` table | LOW | LOW |
| P0 | Create `cost_centers` table | LOW | LOW |
| P1 | Create `allocation_rules` table | LOW | LOW |
| P1 | Create `allocation_rule_targets` table | LOW | LOW |
| P1 | Add FK references to `financial_data` | LOW | LOW |
| P2 | Create seed data migration for EFIR | MEDIUM | LOW |
| P2 | Implement allocation calculation engine | MEDIUM | MEDIUM |
| P3 | Build Admin UI for CRUD operations | HIGH | LOW |

---

## Part 1: Gap Analysis - Current vs Proposed

### 1.1 What Already Exists (No Changes Needed)

| Aspect | Current State | Notes |
|--------|---------------|-------|
| **Calculation Engines** | 7 pure function engines | DHG, GOSI, EOS, Revenue, KPI never store results |
| **Caching** | Redis with dependency graph | Invalidation cascade works correctly |
| **Versioning** | `settings_versions` table | Supports working/submitted/approved/forecast (rename from budget_versions) |
| **Multi-tenancy** | `organizations` + `user_organizations` | RLS policies in place |
| **Reference Data** | 13 reference tables | academic_cycles, subjects, etc. |

### 1.2 What Needs to Change

| Area | Current | Proposed | Effort |
|------|---------|----------|--------|
| **Scenario Types** | `settings_versions.status` only | Add `scenario_type` enum (BUDGET/ACTUAL/FORECAST/WHAT_IF/STRATEGIC) | LOW |
| **Cost Centers** | None | New `cost_centers` + `profit_centers` tables | MEDIUM |
| **Financial Data** | 6 separate tables | Unified `financial_data` table | HIGH |
| **Enrollment** | 12 tables | 4-6 tables (JSONB consolidation) | MEDIUM |
| **Actual Data** | `actual_data` separate from budgets | Link to `scenario_versions` | LOW |

### 1.3 Tables to ADD (New Capabilities)

```
NEW TABLES:
├── profit_centers (cycle-based revenue attribution)
├── cost_centers (department-based cost tracking)
├── allocation_bases (student_count, fte_count, floor_area)
├── allocation_rules (how to distribute shared costs)
└── allocation_rule_targets (distribution percentages)
```

### 1.4 Tables to CONSOLIDATE (Reduce Complexity)

```
CONSOLIDATE:
├── Enrollment (12 → 4-6 tables)
│   ├── KEEP: enrollment_scenarios (reference)
│   ├── KEEP: enrollment_projection_configs (add JSONB overrides)
│   ├── KEEP: enrollment_projections (cached results)
│   ├── MERGE: enrollment_calibration_cache (derived + overrides)
│   └── DROP: 6 separate override tables → JSONB in config
│
├── Financial Data (6 → 1 + views)
│   ├── NEW: financial_data (unified)
│   ├── DROP: revenue_plans → financial_data WHERE record_type='revenue'
│   ├── DROP: personnel_cost_plans → financial_data WHERE record_type='personnel'
│   ├── DROP: operating_cost_plans → financial_data WHERE record_type='operating'
│   ├── DROP: capex_plans → financial_data WHERE record_type='capex'
│   └── DROP: actual_data → financial_data WHERE data_source='actual'
│
└── Analysis (3 → 1 + views)
    ├── DROP: budget_consolidations → VIEW (real-time aggregation)
    └── DROP: budget_vs_actual → VIEW (calculated variance)
```

---

## Part 2: Calculation Engines - Data Strategy

### 2.1 ALWAYS CALCULATED (Never Store)

These values should NEVER be stored in the database. They are always derived from source data:

| Data | Engine | Reason |
|------|--------|--------|
| DHG hours | DHG | Derived from classes × subject_hours |
| Teacher FTE | DHG | Derived from dhg_hours ÷ standard_hours |
| HSA allocation | DHG | Derived from gap between need and available |
| GOSI amounts | GOSI | Derived from salary × nationality |
| EOS amounts | EOS | Derived from salary × service_years |
| KPIs | KPI | Pure aggregations from other data |
| Statement totals | Financial | Sum of line items |
| Revenue amounts | Revenue | fee × enrollment_count |
| Budget vs Actual variance | Analysis | budget - actual |

### 2.2 STORED (Source of Truth)

These values are the source of truth and MUST be stored:

| Data | Table | Notes |
|------|-------|-------|
| Employee info | employees | hire_date, nationality, category |
| Salary data | salaries | basic_salary, allowances (by scenario) |
| Fee structure | fee_structure | tuition, DAI, registration by level |
| Subject hours | subject_hours | hours per week per subject per level |
| Class size config | class_size_parameters | min, max, target sizes |
| Base enrollment | enrollment_data | actual student counts |
| Actual financial data | financial_data | imported from Odoo/external |
| Budget line items | financial_data | planned amounts by account |

### 2.3 CACHED (Expensive Calculations)

For performance, these calculated values may be cached (Redis with TTL):

| Data | Cache TTL | Invalidation Trigger |
|------|-----------|---------------------|
| DHG hours by level | 15 minutes | Class structure change |
| Enrollment projections | 30 minutes | Base enrollment change |
| KPI dashboard | 5 minutes | Any financial change |
| Financial statements | 60 minutes | Consolidation change |

---

## Part 3: Phased Implementation Plan

### Phase 0: Quick Wins (2-3 days, LOW risk)

**Goal**: Add scenario_type without breaking existing functionality

**Changes**:
1. Rename `budget_versions` → `settings_versions` (with table prefix)
2. Add `scenario_type` enum column
3. Default existing records to 'BUDGET'
4. Update API to accept scenario_type parameter
5. Rename FK column `budget_version_id` → `version_id` in all versioned tables

**Migration**:
```sql
-- Step 1: Add scenario type enum
CREATE TYPE efir_budget.scenario_type AS ENUM ('BUDGET', 'ACTUAL', 'FORECAST', 'STRATEGIC', 'WHAT_IF');

-- Step 2: Rename table (before adding column)
-- NOTE: Implemented migrations rename budget_versions -> settings_versions and standardize prefixes.
-- In a legacy DB you may still need:
-- ALTER TABLE efir_budget.budget_versions RENAME TO settings_versions;

-- Step 3: Add column with default
ALTER TABLE efir_budget.settings_versions
ADD COLUMN scenario_type efir_budget.scenario_type NOT NULL DEFAULT 'BUDGET';

-- Step 4: Update existing actuals (if any imported)
UPDATE efir_budget.settings_versions
SET scenario_type = 'ACTUAL'
WHERE status = 'approved' AND name LIKE '%Actual%';

-- Step 5: Rename FK columns in all versioned tables (example)
-- ALTER TABLE efir_budget.enrollment_projections
--   RENAME COLUMN budget_version_id TO version_id;
-- (Repeat for all 29 versioned tables via VersionedMixin)
```

**Files to Modify**:
- `backend/app/models/base.py` - Update VersionedMixin (`budget_version_id` → `version_id`)
- `backend/app/models/configuration.py` - Rename table, add scenario_type column
- `backend/app/schemas/configuration.py` - Update BudgetVersion → Version schemas
- `backend/alembic/versions/` - New migration file

---

### Phase 1: Add Cost/Profit Centers (1 week, LOW risk)

**Goal**: Enable cost allocation tracking without breaking existing functionality

**New Tables**:

```sql
-- Enums
CREATE TYPE cost_center_type AS ENUM ('educational', 'administrative', 'support', 'overhead');
CREATE TYPE allocation_method AS ENUM ('proportional', 'fixed', 'direct', 'step_down');

-- Profit Centers (revenue attribution by cycle/service)
CREATE TABLE efir_budget.finance_profit_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
    code VARCHAR(20) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    cycle_id UUID REFERENCES efir_budget.academic_cycles(id),
    parent_id UUID REFERENCES efir_budget.profit_centers(id),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uk_profit_center_code UNIQUE(organization_id, code)
);

-- Default Profit Centers:
-- PC-MAT, PC-ELEM, PC-COLL, PC-LYC, PC-ADMIN, PC-CANTINA, PC-TRANSPORT

-- Cost Centers (expense attribution by department)
CREATE TABLE efir_budget.cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
    code VARCHAR(20) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    center_type cost_center_type NOT NULL,
    cycle_id UUID REFERENCES efir_budget.academic_cycles(id),
    parent_id UUID REFERENCES efir_budget.cost_centers(id),
    default_profit_center_id UUID REFERENCES efir_budget.profit_centers(id),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uk_cost_center_code UNIQUE(organization_id, code)
);

-- Default Cost Centers:
-- CC-TEACH-MAT, CC-TEACH-ELEM, CC-TEACH-SEC (Teaching by level)
-- CC-ADMIN-DIR, CC-ADMIN-FIN, CC-ADMIN-HR (Administrative)
-- CC-SUPPORT-IT, CC-SUPPORT-MAINT (Support services)
-- CC-OVERHEAD (Shared costs to allocate)

-- Allocation Bases
CREATE TABLE efir_budget.allocation_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
    code VARCHAR(30) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    description TEXT,
    CONSTRAINT uk_allocation_base_code UNIQUE(organization_id, code)
);

-- Default Bases: student_count, class_count, floor_area, fte_count, revenue

-- Allocation Rules
CREATE TABLE efir_budget.allocation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
    name VARCHAR(100) NOT NULL,
    source_cost_center_id UUID NOT NULL REFERENCES efir_budget.cost_centers(id),
    allocation_base_id UUID NOT NULL REFERENCES efir_budget.allocation_bases(id),
    allocation_method allocation_method NOT NULL DEFAULT 'proportional',
    fiscal_year INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Allocation Rule Targets
CREATE TABLE efir_budget.allocation_rule_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    allocation_rule_id UUID NOT NULL REFERENCES efir_budget.allocation_rules(id),
    target_cost_center_id UUID NOT NULL REFERENCES efir_budget.cost_centers(id),
    fixed_percentage NUMERIC(5,2),
    CONSTRAINT uk_rule_target UNIQUE(allocation_rule_id, target_cost_center_id)
);
```

**Files to Create**:
- `backend/app/models/cost_centers.py` - SQLAlchemy models
- `backend/app/schemas/cost_centers.py` - Pydantic schemas
- `backend/app/api/v1/cost_centers.py` - CRUD endpoints
- `backend/app/services/cost_allocation_service.py` - Allocation logic
- `backend/alembic/versions/YYYYMMDD_add_cost_centers.py` - Migration

**Seed Data**: Default profit/cost centers for EFIR school

---

### Phase 2: Consolidate Enrollment Tables (1-2 weeks, MEDIUM risk)

**Goal**: Reduce 12 enrollment tables to 4-6 using JSONB

**Current Tables** (12):
1. `enrollment_scenarios` - KEEP (reference)
2. `enrollment_lateral_entry_defaults` - MERGE into scenarios
3. `enrollment_projection_configs` - KEEP (add JSONB overrides)
4. `enrollment_global_overrides` - MERGE into config JSONB
5. `enrollment_level_overrides` - MERGE into config JSONB
6. `enrollment_grade_overrides` - MERGE into config JSONB
7. `enrollment_projections` - KEEP (results cache)
8. `enrollment_derived_parameters` - MERGE into calibration
9. `enrollment_parameter_overrides` - MERGE into calibration
10. `enrollment_scenario_multipliers` - MERGE into scenarios
11. (external: academic_levels)
12. (external: historical_actuals)

**Target Tables** (4):

```sql
-- 1. enrollment_scenarios (enhanced)
ALTER TABLE efir_budget.enrollment_scenarios
ADD COLUMN lateral_entry_defaults JSONB DEFAULT '{}',
ADD COLUMN scenario_multipliers JSONB DEFAULT '{}';
-- Migrate data from enrollment_lateral_entry_defaults, enrollment_scenario_multipliers

-- 2. enrollment_projection_configs (enhanced with JSONB overrides)
ALTER TABLE efir_budget.enrollment_projection_configs
ADD COLUMN overrides JSONB DEFAULT '{
  "global": {},
  "levels": {},
  "grades": {}
}';
-- Migrate data from enrollment_global_overrides, enrollment_level_overrides, enrollment_grade_overrides

-- 3. enrollment_projections (unchanged)
-- Keep as-is for cached projection results

-- 4. enrollment_calibration_data (new, merged)
CREATE TABLE efir_budget.enrollment_calibration_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES efir_budget.admin_organizations(id),
    grade_code VARCHAR(10) NOT NULL,
    data_type VARCHAR(20) NOT NULL, -- 'derived' or 'override'

    -- Derived parameters
    progression_rate NUMERIC(6,4),
    lateral_entry_rate NUMERIC(6,4),
    retention_rate NUMERIC(6,4),
    confidence VARCHAR(10) DEFAULT 'low',
    std_deviation NUMERIC(6,4),
    years_used INT DEFAULT 0,
    source_years JSONB DEFAULT '[]',

    -- Override parameters
    override_lateral_rate BOOLEAN DEFAULT FALSE,
    manual_lateral_rate NUMERIC(6,4),
    override_retention_rate BOOLEAN DEFAULT FALSE,
    manual_retention_rate NUMERIC(6,4),
    override_fixed_lateral BOOLEAN DEFAULT FALSE,
    manual_fixed_lateral INT,
    override_reason TEXT,

    calculated_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    CONSTRAINT uk_calibration_org_grade_type UNIQUE(organization_id, grade_code, data_type)
);
-- Migrate data from enrollment_derived_parameters, enrollment_parameter_overrides
```

**Migration Strategy**:
1. Create new JSONB columns/tables
2. Migrate existing data with reversible migration
3. Update service layer to read/write JSONB
4. Keep old tables for 2 weeks (rollback safety)
5. Drop old tables after validation

**Files to Modify**:
- `backend/app/models/enrollment_projection.py` - Add JSONB columns
- `backend/app/schemas/enrollment_projection.py` - Update schemas
- `backend/app/services/enrollment_projection_service.py` - Use JSONB
- `backend/app/engine/enrollment/projection_engine.py` - No changes (pure functions)

---

### Phase 3: Unify Financial Data Tables (2-3 weeks, HIGH risk)

**Goal**: Replace 6 financial tables with 1 unified table + views

**Current Tables** (6):
- `revenue_plans`
- `personnel_cost_plans`
- `operating_cost_plans`
- `capex_plans`
- `actual_data`
- `budget_consolidations`

**Target Structure**:

```sql
-- Enums
CREATE TYPE record_type AS ENUM ('revenue', 'personnel', 'operating', 'capex');
CREATE TYPE data_source AS ENUM ('planned', 'actual', 'imported', 'calculated');

-- Unified financial data table
-- NOTE: Column renamed from scenario_version_id to version_id for consistency
CREATE TABLE efir_budget.finance_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES efir_budget.settings_versions(id),
    record_type record_type NOT NULL,
    account_code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50),
    subcategory VARCHAR(50),

    -- Amounts
    amount_sar NUMERIC(15,2) NOT NULL,
    quantity NUMERIC(10,2),
    unit_cost_sar NUMERIC(12,2),

    -- Cost allocation (from Phase 1)
    cost_center_id UUID REFERENCES efir_budget.cost_centers(id),
    profit_center_id UUID REFERENCES efir_budget.profit_centers(id),

    -- Metadata
    data_source data_source NOT NULL,
    is_calculated BOOLEAN DEFAULT FALSE,
    calculation_driver VARCHAR(100),
    period_type VARCHAR(10) DEFAULT 'annual',
    period_value INT DEFAULT 0,

    -- Links to source entities (optional)
    employee_id UUID REFERENCES efir_budget.employees(id),
    level_id UUID REFERENCES efir_budget.academic_levels(id),

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by_id UUID,
    updated_by_id UUID,
    deleted_at TIMESTAMPTZ
);

-- Indexes
CREATE INDEX idx_finance_version ON efir_budget.finance_data(version_id);
CREATE INDEX idx_finance_account ON efir_budget.finance_data(account_code);
CREATE INDEX idx_finance_type ON efir_budget.finance_data(record_type);
CREATE INDEX idx_finance_cost_center ON efir_budget.finance_data(cost_center_id);
CREATE INDEX idx_finance_profit_center ON efir_budget.finance_data(profit_center_id);

-- Budget vs Actual View (replaces stored table)
CREATE OR REPLACE VIEW efir_budget.vw_budget_vs_actual AS
SELECT
    b.account_code,
    b.description,
    b.category,
    b.amount_sar AS budget_amount,
    COALESCE(a.amount_sar, 0) AS actual_amount,
    b.amount_sar - COALESCE(a.amount_sar, 0) AS variance_amount,
    CASE
        WHEN b.amount_sar = 0 THEN 0
        ELSE ROUND((b.amount_sar - COALESCE(a.amount_sar, 0)) / b.amount_sar * 100, 2)
    END AS variance_percent,
    b.cost_center_id,
    b.profit_center_id
FROM efir_budget.finance_data b
LEFT JOIN efir_budget.finance_data a
    ON a.account_code = b.account_code
    AND a.version_id IN (
        SELECT id FROM efir_budget.settings_versions
        WHERE scenario_type = 'ACTUAL' AND fiscal_year = (
            SELECT fiscal_year FROM efir_budget.settings_versions WHERE id = b.version_id
        )
    )
WHERE b.data_source = 'planned';

-- Consolidation View (replaces stored table)
CREATE OR REPLACE VIEW efir_budget.vw_budget_consolidation AS
SELECT
    sv.id AS version_id,
    sv.name AS version_name,
    sv.fiscal_year,
    sv.scenario_type,
    fd.record_type,
    fd.account_code,
    fd.description,
    SUM(fd.amount_sar) AS total_amount,
    fd.cost_center_id,
    fd.profit_center_id,
    cc.name_en AS cost_center_name,
    pc.name_en AS profit_center_name
FROM efir_budget.settings_versions sv
JOIN efir_budget.finance_data fd ON fd.version_id = sv.id
LEFT JOIN efir_budget.finance_cost_centers cc ON cc.id = fd.cost_center_id
LEFT JOIN efir_budget.finance_profit_centers pc ON pc.id = fd.profit_center_id
GROUP BY
    sv.id, sv.name, sv.fiscal_year, sv.scenario_type,
    fd.record_type, fd.account_code, fd.description,
    fd.cost_center_id, fd.profit_center_id,
    cc.name_en, pc.name_en;
```

**Migration Strategy**:
1. Create `finance_data` table (unified financial data with `version_id` FK)
2. Migrate revenue_plans → finance_data (record_type='revenue')
3. Migrate personnel_cost_plans → finance_data (record_type='personnel')
4. Migrate operating_cost_plans → finance_data (record_type='operating')
5. Migrate capex_plans → finance_data (record_type='capex')
6. Migrate actual_data → finance_data (data_source='actual')
7. Create views for consolidation and budget_vs_actual
8. Update all API endpoints
9. Keep old tables for rollback (2 weeks)
10. Drop old tables after validation

**Files to Modify**:
- `backend/app/models/planning.py` - Replace 4 models with 1
- `backend/app/models/consolidation.py` - Replace stored tables with view access
- `backend/app/schemas/planning.py` - Unified schemas
- `backend/app/api/v1/planning.py` - Update endpoints
- `backend/app/api/v1/costs.py` - Update endpoints
- `backend/app/services/cost_service.py` - Use unified table
- `backend/app/services/revenue_service.py` - Use unified table
- `backend/app/services/consolidation_service.py` - Use views

---

### Phase 4: Simplify Employee/Salary Structure (1 week, LOW risk)

**Goal**: Clarify AEFE vs Local distinction, remove redundancy

**Changes**:
```sql
-- Simplify employees table
ALTER TABLE efir_budget.employees
ADD COLUMN employee_type VARCHAR(20) NOT NULL DEFAULT 'local',
ADD COLUMN aefe_position_type VARCHAR(20);

-- Add constraint
ALTER TABLE efir_budget.employees
ADD CONSTRAINT ck_aefe_position_type
CHECK (
    (employee_type = 'local' AND aefe_position_type IS NULL) OR
    (employee_type = 'aefe' AND aefe_position_type IN ('detached', 'funded'))
);
```

**Files to Modify**:
- `backend/app/models/planning.py` - Update Employee model
- `backend/app/schemas/planning.py` - Update schemas
- `backend/app/services/employee_service.py` - Update logic

---

## Part 4: Decision Points (User Input Needed)

### Decision 1: Enrollment Table Reduction Scope
- **A)** Full JSONB consolidation: 12 → 4 tables *(recommended)*
- **B)** Partial: 12 → 6 tables (keep FK-validated overrides)
- **C)** No change: Keep 12 tables

### Decision 2: Financial Data Migration Timing
- **A)** Big bang: Migrate all 6 tables at once
- **B)** Phased: Revenue → Costs → Actuals *(recommended)*
- **C)** Parallel: Keep both schemas, deprecate old over time

### Decision 3: Cost Allocation Calculation
- **A)** On-demand only (always calculate when viewing)
- **B)** Pre-calculate on scenario lock
- **C)** Hybrid: Pre-calculate for approved, on-demand for draft *(recommended)*

### Decision 4: Historical Data Retention
- **A)** Keep all history in unified table *(recommended initially)*
- **B)** Archive to separate table after 5 years
- **C)** Soft delete with retention policy

### Decision 5: GOSI Rate Storage
- **A)** Single config row (current rate only)
- **B)** Rate-by-date table (historical rate changes) *(recommended)*

---

## Part 5: Impact Summary

### Table Count Changes

| Module | Current | After Phase 0-1 | After Phase 2 | After Phase 3-4 | Net Change |
|--------|---------|-----------------|---------------|-----------------|------------|
| Auth/Config | 11 | 11 | 11 | 11 | 0 |
| Configuration | 13 | 13 | 13 | 13 | 0 |
| **Cost Centers** | 0 | **+5** | 5 | 5 | **+5** |
| **Enrollment** | 12 | 12 | **4** | 4 | **-8** |
| Planning | 10 | 10 | 10 | 10 | 0 |
| **Financial Data** | 6 | 6 | 6 | **1** | **-5** |
| Consolidation | 3 | 3 | 3 | **1 + 2 views** | **-2** |
| Analysis | 9 | 9 | 9 | 9 | 0 |
| Strategic | 4 | 4 | 4 | 4 | 0 |
| Personnel | 4 | 4 | 4 | 4 | 0 |
| **TOTAL** | **~76** | **~81** | **~73** | **~66** | **~-10** |

### Risk Matrix

| Phase | Risk | Impact | Likelihood | Mitigation |
|-------|------|--------|------------|------------|
| 0 | Schema change | LOW | LOW | Backward compatible, default value |
| 1 | New tables | LOW | LOW | Additive only, no existing data touched |
| 2 | JSONB migration | MEDIUM | MEDIUM | Reversible migration, dual schema period |
| 3 | Financial data unification | HIGH | MEDIUM | Phased migration, extensive testing |
| 4 | Employee simplification | LOW | LOW | Minimal changes, constraint additions |

### Timeline Estimate

| Phase | Duration | Dependencies | Team |
|-------|----------|--------------|------|
| Phase 0 | 2-3 days | None | Backend |
| Phase 1 | 1 week | Phase 0 | Backend + DB |
| Phase 2 | 1-2 weeks | Phase 1 | Backend + Frontend |
| Phase 3 | 2-3 weeks | Phase 2 | Full stack |
| Phase 4 | 1 week | Phase 3 | Backend |
| **TOTAL** | **6-8 weeks** | - | - |

---

## Part 6: Files Changed Summary

### New Files to Create
```
backend/app/models/cost_centers.py
backend/app/schemas/cost_centers.py
backend/app/api/v1/cost_centers.py
backend/app/services/cost_allocation_service.py
backend/alembic/versions/YYYYMMDD_0100_add_scenario_type.py
backend/alembic/versions/YYYYMMDD_0200_add_cost_centers.py
backend/alembic/versions/YYYYMMDD_0300_consolidate_enrollment.py
backend/alembic/versions/YYYYMMDD_0400_unify_financial_data.py
backend/alembic/versions/YYYYMMDD_0500_simplify_employees.py
```

### Files to Modify (Major)
```
backend/app/models/configuration.py - Add scenario_type
backend/app/models/enrollment_projection.py - JSONB overrides
backend/app/models/planning.py - Unified financial_data
backend/app/models/consolidation.py - View access
backend/app/services/enrollment_projection_service.py
backend/app/services/consolidation_service.py
backend/app/services/cost_service.py
backend/app/services/revenue_service.py
backend/app/api/v1/planning.py
backend/app/api/v1/costs.py
```

### Files Unchanged (Calculation Engines)
```
backend/app/engine/dhg/* - Pure functions, no DB access
backend/app/engine/gosi/* - Pure functions
backend/app/engine/eos/* - Pure functions
backend/app/engine/kpi/* - Pure functions
backend/app/engine/revenue/* - Pure functions
backend/app/engine/financial_statements/* - Pure functions
backend/app/engine/enrollment/* - Pure functions (input models may change)
```

---

## Appendix A: Engine Dependencies Diagram

```
                     ┌──────────────┐
                     │ Configuration │
                     │ (fee_structure│
                     │  subject_hours│
                     │  class_sizes) │
                     └──────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              │             │             │
              ▼             ▼             ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │Enrollment│ │   DHG    │ │  Revenue │
        │  Engine  │ │  Engine  │ │  Engine  │
        └────┬─────┘ └────┬─────┘ └────┬─────┘
             │            │            │
             │     ┌──────┴──────┐     │
             │     │             │     │
             │     ▼             │     │
             │ ┌──────────┐     │     │
             │ │Personnel │     │     │
             │ │(GOSI,EOS)│     │     │
             │ └────┬─────┘     │     │
             │      │           │     │
             └──────┼───────────┼─────┘
                    │           │
                    ▼           ▼
              ┌──────────────────────┐
              │  Budget Consolidation │
              │   (financial_data)    │
              └──────────┬───────────┘
                         │
              ┌──────────┼──────────┐
              │          │          │
              ▼          ▼          ▼
        ┌──────────┐ ┌────────┐ ┌──────────┐
        │Financial │ │  KPI   │ │Budget vs │
        │Statements│ │ Engine │ │  Actual  │
        └──────────┘ └────────┘ └──────────┘
```

---

## Next Steps

1. **User Review**: Confirm decisions in Part 4
2. **Phase 0**: Add scenario_type (quick win)
3. **Phase 1**: Add cost/profit centers
4. **Iterate**: Each phase includes testing before next phase

---

*Document Version: 1.5*
*Last Updated: 2025-12-14*

### Changelog
- v1.5 (2025-12-14): Added Cost/Profit Center Module Design (NEW MODULE) - 4 new tables (`profit_centers`, `cost_centers`, `allocation_rules`, `allocation_rule_targets`), 3 new ENUMs (`cost_center_category`, `allocation_method`, `allocation_base`), 5 profit centers (4 academic cycles + Other Activities), 2-level cost center hierarchy, ORG-SCOPED centers with VERSION-LINKED allocation rules, integration with `financial_data` table, default seed data for EFIR
- v1.4 (2025-12-14): Added Strategic Module Review - enhanced `strategic_plans` with `organization_id`, `version_id`, `based_on_version_id` for multi-tenancy and unified versioning integration, documented lineage tracking pattern and version integration design, 4 tables kept (no reduction needed due to hierarchical scenario modeling structure)
- v1.3 (2025-12-14): Added Planning/Consolidation/Analysis Module Review - consolidated 4 fact tables → 1 unified `financial_data` table with `record_type` discriminator, deprecated `actual_data`/`historical_actuals`, converted `budget_vs_actual` and `budget_consolidations` to VIEWs, identified UI-LAYER tables needing org_id
- v1.2 (2025-12-14): Added DHG/Workforce Module Review (subject_hours_matrix → curriculum_hours STATIC, 5 DHG tables + 1 STATIC) and Personnel Module Review (4→1 table consolidation, EOS/GOSI on-demand)
- v1.1 (2025-12-14): Added Enrollment Module Review (15→6 tables consolidation)
- v1.0 (2025-12-14): Initial refactoring plan with Configuration Module Review
