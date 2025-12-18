# EFIR Budget App - Database Schema (Current)

**Schema:** `efir_budget` (single schema)  
**Last Updated:** 2025-12-15  

This is a **current-state overview** of the implemented schema after:
- Phase 3: `version_id` standardization + table prefixes + `scenario_type` enum
- Phase 4: Enrollment/Personnel/Finance consolidations

For authoritative DDL, use `backend/alembic/versions/`.

---

## Critical Constraints

- `public` schema: **never touch** (belongs to another project)
- `efir_budget` schema: **only schema** for this app

---

## Table Prefix Convention

All tables live in `efir_budget` and are organized by prefix:

- `ref_*` — global lookup/reference tables (shared across organizations)
- `settings_*` — versioning + configuration parameters
- `students_*` — enrollment planning inputs + outputs
- `teachers_*` — employees + DHG planning inputs + outputs
- `finance_*` — financial planning inputs + consolidation + statements
- `insights_*` — KPIs + dashboards + variance analysis (some legacy)
- `admin_*` — admin/org + writeback/audit tables

---

## Central Tables

- `efir_budget.settings_versions` — central version table (formerly `budget_versions`)
  - All versioned tables reference this via `version_id` (formerly `budget_version_id`)
  - Includes `scenario_type` enum: ACTUAL/BUDGET/FORECAST/STRATEGIC/WHAT_IF
- `efir_budget.admin_organizations` — organization/tenant table
- `efir_budget.user_organizations` — user-to-organization membership (FK to `auth.users`)

---

## Canonical Tables by Domain

**Reference (`ref_*`)**
- `ref_academic_cycles`, `ref_academic_levels`
- `ref_subjects`
- `ref_teacher_categories`, `ref_fee_categories`, `ref_nationality_types`
- `ref_kpi_definitions`

**Settings (`settings_*`)**
- `settings_system_configs`
- `settings_class_size_params`
- `settings_subject_hours_matrix`
- `settings_teacher_cost_params`
- `settings_fee_structure`
- `settings_timetable_constraints`
- `settings_integration`
- `settings_strategic_plans`, `settings_strategic_scenarios`, `settings_strategic_projections`, `settings_strategic_initiatives`

**Students (`students_*`)**
- Inputs: `students_configs`, `students_data`, `students_overrides`, `students_calibration`
- Outputs (cached + lineage): `students_enrollment_projections`, `students_class_structures`

**Teachers (`teachers_*`)**
- `teachers_employees` (consolidated salary + AEFE columns)
- `teachers_allocations`
- Outputs (cached + lineage): `teachers_dhg_subject_hours`, `teachers_dhg_requirements`

**Finance (`finance_*`)**
- Input: `finance_data` (unified fact table; discriminator `data_type`)
- Backward-compatible views: `vw_finance_revenue`, `vw_finance_operating_costs`, `vw_finance_personnel_costs`, `vw_finance_capex`
- Outputs (cached + lineage): `finance_consolidations`, `finance_statements`, `finance_statement_lines`

**Insights (`insights_*`)**
- `insights_kpi_values`
- `insights_dashboard_configs`, `insights_dashboard_widgets`, `insights_user_preferences`
- `insights_variance_explanations`

**Admin (`admin_*`)**
- `admin_integration_logs`
- Writeback/audit: `admin_planning_cells`, `admin_cell_changes`, `admin_cell_comments`
- `admin_historical_comparison_runs`

---

## Legacy / Transitional Tables

Some environments may still contain legacy tables kept for migration safety (not canonical for new development), e.g.:
- `insights_actual_data`, `insights_budget_vs_actual`, `insights_historical_actuals`
- `finance_revenue_plans`, `finance_operating_cost_plans`, `finance_personnel_cost_plans`, `finance_capex_plans`

**Note**: References to `budget_versions` or `budget_version_id` in legacy code represent the former naming convention. Current standard uses `settings_versions` and `version_id`.

---

## Related Docs

- `docs/database/schema_design.md` (design overview)
- `docs/planning/REFACTORING_MASTER_PLAN.md` (refactor source of truth)
- `docs/planning/DB_golden_rules.md` (schema conventions)

