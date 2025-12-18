# EFIR Budget App - Database Schema Design

**Last Updated:** 2025-12-15  
**Database:** PostgreSQL (Supabase)  
**Schema:** `efir_budget` (**single schema; `public` is out of scope**)  

This document describes the **current implemented schema structure** after Phase 3 (schema standardization) and Phase 4 (table consolidation). For authoritative DDL, refer to:
- `backend/alembic/versions/` (migrations)
- `docs/planning/REFACTORING_MASTER_PLAN.md` (refactor source of truth)
- `docs/planning/DB_golden_rules.md` (design rules / constraints)

---

## 1. High-Level Structure

### 1.1 Single Schema + Table Prefixes

All application tables live in `efir_budget` and are organized via prefixes:

- `efir_budget.ref_*` — global reference/lookup tables (shared across orgs)
- `efir_budget.settings_*` — versioning and configuration parameters
- `efir_budget.students_*` — enrollment planning + outputs
- `efir_budget.teachers_*` — employees + DHG planning + outputs
- `efir_budget.finance_*` — financial planning + consolidations + statements
- `efir_budget.insights_*` — KPIs, dashboards, variance analysis (some legacy)
- `efir_budget.admin_*` — org/admin tables + writeback/audit tables

### 1.2 Central Versioning

Versioned data uses:

- `efir_budget.settings_versions` — central version table (formerly `budget_versions`)
- `version_id` — FK column name used everywhere (formerly `budget_version_id`)
- `scenario_type` — enum on `settings_versions` to distinguish ACTUAL/BUDGET/FORECAST/STRATEGIC/WHAT_IF

### 1.3 Multi-Tenancy

Business tables are organization-scoped via `organization_id` referencing:

- `efir_budget.admin_organizations`

Membership/roles are modeled via:

- `efir_budget.user_organizations` (FK to `auth.users`)

### 1.4 Input vs Output Tables

- **Inputs** store editable assumptions/configs (e.g., `students_configs`, `students_data`, `finance_data`).
- **Outputs** store computed/cached results and include lineage (e.g., `students_enrollment_projections`, `finance_statements`).

---

## 2. Canonical Tables by Module (Implemented)

### 2.1 Reference (`ref_*`)

- `ref_academic_cycles`, `ref_academic_levels`
- `ref_subjects`
- `ref_teacher_categories`, `ref_fee_categories`, `ref_nationality_types`
- `ref_kpi_definitions`
- `ref_enrollment_scenarios` (legacy/compat where still present)

### 2.2 Settings (`settings_*`)

- `settings_versions` (central version table; includes `scenario_type`)
- `settings_system_configs`
- `settings_class_size_params`
- `settings_subject_hours_matrix`
- `settings_teacher_cost_params`
- `settings_fee_structure`
- `settings_timetable_constraints`
- `settings_integration`
- `settings_strategic_plans`, `settings_strategic_scenarios`, `settings_strategic_projections`, `settings_strategic_initiatives`

### 2.3 Students (`students_*`) (Phase 4A consolidation)

Inputs:
- `students_configs`
- `students_data`
- `students_overrides`
- `students_calibration`

Outputs (cached + lineage columns):
- `students_enrollment_projections`
- `students_class_structures`

### 2.4 Teachers (`teachers_*`) (Phase 4B consolidation)

- `teachers_employees` (consolidated salary + AEFE columns)
- `teachers_allocations`
- `teachers_dhg_subject_hours` (output + lineage)
- `teachers_dhg_requirements` (output + lineage)

### 2.5 Finance (`finance_*`) (Phase 4C consolidation)

Inputs (unified fact table):
- `finance_data` with `data_type` discriminator (`revenue`, `operating_cost`, `personnel_cost`, `capex`)

Backward-compatible views:
- `vw_finance_revenue`, `vw_finance_operating_costs`, `vw_finance_personnel_costs`, `vw_finance_capex`

Outputs (cached + lineage columns):
- `finance_consolidations`
- `finance_statements`, `finance_statement_lines`

### 2.6 Insights (`insights_*`)

- `insights_kpi_values`
- `insights_dashboard_configs`, `insights_dashboard_widgets`, `insights_user_preferences`
- `insights_variance_explanations`

Some environments may still contain **legacy** tables kept for migration safety:
- `insights_actual_data`, `insights_budget_vs_actual`, `insights_historical_actuals`

### 2.7 Admin (`admin_*`)

- `admin_organizations`
- `admin_integration_logs`
- Writeback/audit: `admin_planning_cells`, `admin_cell_changes`, `admin_cell_comments`
- `admin_historical_comparison_runs`

---

## 3. Naming & Column Conventions

- Schema: always `efir_budget` (never `public`)
- Version FK: `version_id` → `settings_versions(id)`
- Organization FK: `organization_id` → `admin_organizations(id)` (omit only for pure `ref_*` lookups)
- Audit columns: `created_at`, `updated_at`, `created_by_id`, `updated_by_id`, optional `deleted_at`

---

## 4. Notes on “Legacy” Docs and Tables

Some older documentation (and a few tables/views retained for safety) still use pre-refactor names like:
- `budget_versions` (now `settings_versions`), `budget_version_id` (now `version_id`)
- unprefixed tables (e.g., `academic_levels`, `subjects`, `employees`)

Treat those as **historical terminology**; the canonical naming is the prefixed structure above.

