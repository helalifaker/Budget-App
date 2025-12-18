# Phase 3B: Table Rename Mapping

**Status**: PLANNING
**Created**: 2025-12-15
**Purpose**: Comprehensive mapping of all tables to be renamed with module prefixes

---

## Overview

Phase 3B applies the **table prefix convention** from DB_golden_rules.md Section 9.2 to all existing tables in the `efir_budget` schema.

### Prefix Convention

| Module | Prefix | Primary Role |
|--------|--------|--------------|
| Students | `students_*` | Academic Director |
| Teachers | `teachers_*` | HR Manager |
| Finance | `finance_*` | Finance Director |
| Insights | `insights_*` | All (read) |
| Settings | `settings_*` | All (limited) |
| Reference | `ref_*` | Static/lookup data |
| Admin | `admin_*` | Admin only |

---

## Section 1: Reference Tables (STATIC - `ref_*`)

These tables contain globally-shared reference data that doesn't change per organization or version.

| Current Name | New Name | Model File | Notes |
|--------------|----------|------------|-------|
| `academic_cycles` | `ref_academic_cycles` | configuration.py | MAT, ELEM, COLL, LYC |
| `academic_levels` | `ref_academic_levels` | configuration.py | PS, MS, GS, CP... Terminale |
| `subjects` | `ref_subjects` | configuration.py | MATH, FRAN, ANGL, etc. |
| `teacher_categories` | `ref_teacher_categories` | configuration.py | AEFE_DETACHED, AEFE_FUNDED, LOCAL |
| `fee_categories` | `ref_fee_categories` | configuration.py | TUITION, DAI, REGISTRATION |
| `nationality_types` | `ref_nationality_types` | configuration.py | FRENCH, SAUDI, OTHER |
| `kpi_definitions` | `ref_kpi_definitions` | analysis.py | Static KPI catalog |
| `enrollment_scenarios` | `ref_enrollment_scenarios` | enrollment_projection.py | worst, base, best |

**Total**: 8 tables

---

## Section 2: Settings Tables (`settings_*`)

Version-linked configuration tables that define parameters per budget version.

| Current Name | New Name | Model File | Notes |
|--------------|----------|------------|-------|
| `budget_versions` | `settings_versions` | configuration.py | **CRITICAL**: Central versioning table |
| `system_configs` | `settings_system_configs` | configuration.py | Global config params |
| `class_size_params` | `settings_class_size_params` | configuration.py | Min/max/target class sizes |
| `subject_hours_matrix` | `settings_subject_hours_matrix` | configuration.py | Curriculum hours per level |
| `teacher_cost_params` | `settings_teacher_cost_params` | configuration.py | PRRD, salary, HSA rates |
| `fee_structure` | `settings_fee_structure` | configuration.py | Tuition, DAI per level |
| `timetable_constraints` | `settings_timetable_constraints` | configuration.py | Hours/day, breaks |
| `integration_settings` | `settings_integration` | integrations.py | External system configs |
| `strategic_plans` | `settings_strategic_plans` | strategic.py | 5-year plans |
| `strategic_plan_scenarios` | `settings_strategic_scenarios` | strategic.py | Plan scenario variants |
| `strategic_plan_projections` | `settings_strategic_projections` | strategic.py | Projected values |
| `strategic_initiatives` | `settings_strategic_initiatives` | strategic.py | Strategic actions |

**Total**: 12 tables

---

## Section 3: Students Module (`students_*`)

Enrollment planning and class structure tables.

| Current Name | New Name | Model File | Notes |
|--------------|----------|------------|-------|
| `enrollment_plans` | `students_enrollment_plans` | planning.py | Student counts input |
| `enrollment_projections` | `students_enrollment_projections` | enrollment_projection.py | Calculated projections |
| `enrollment_projection_configs` | `students_projection_configs` | enrollment_projection.py | Config per version |
| `enrollment_global_overrides` | `students_global_overrides` | enrollment_projection.py | Global override values |
| `enrollment_level_overrides` | `students_level_overrides` | enrollment_projection.py | Cycle-level overrides |
| `enrollment_grade_overrides` | `students_grade_overrides` | enrollment_projection.py | Grade-level overrides |
| `enrollment_lateral_entry_defaults` | `students_lateral_entry_defaults` | enrollment_projection.py | Lateral entry rates |
| `enrollment_scenario_multipliers` | `students_scenario_multipliers` | enrollment_projection.py | Scenario factors |
| `enrollment_derived_parameters` | `students_derived_parameters` | enrollment_projection.py | Calibration derived |
| `enrollment_parameter_overrides` | `students_parameter_overrides` | enrollment_projection.py | Manual calibration |
| `class_structures` | `students_class_structures` | planning.py | Class formation output |
| `nationality_distributions` | `students_nationality_distributions` | planning.py | Student nationality mix |

**Total**: 12 tables

---

## Section 4: Teachers Module (`teachers_*`)

Personnel, DHG, and workforce planning tables.

| Current Name | New Name | Model File | Notes |
|--------------|----------|------------|-------|
| `employees` | `teachers_employees` | personnel.py | Employee master data |
| `employee_salaries` | `teachers_employee_salaries` | personnel.py | Salary records |
| `aefe_positions` | `teachers_aefe_positions` | personnel.py | AEFE position tracking |
| `eos_provisions` | `teachers_eos_provisions` | personnel.py | EOS liability snapshots |
| `dhg_subject_hours` | `teachers_dhg_subject_hours` | planning.py | DHG hours output |
| `dhg_teacher_requirements` | `teachers_dhg_requirements` | planning.py | FTE requirements |
| `teacher_allocations` | `teachers_allocations` | planning.py | TRMD allocations |

**Total**: 7 tables

---

## Section 5: Finance Module (`finance_*`)

Revenue, costs, and financial planning tables.

| Current Name | New Name | Model File | Notes |
|--------------|----------|------------|-------|
| `revenue_plans` | `finance_revenue_plans` | planning.py | Revenue line items |
| `personnel_cost_plans` | `finance_personnel_cost_plans` | planning.py | Personnel costs |
| `operating_cost_plans` | `finance_operating_cost_plans` | planning.py | Operating expenses |
| `capex_plans` | `finance_capex_plans` | planning.py | Capital expenditure |
| `budget_consolidations` | `finance_consolidations` | consolidation.py | Consolidated totals |
| `financial_statements` | `finance_statements` | consolidation.py | Statement headers |
| `financial_statement_lines` | `finance_statement_lines` | consolidation.py | Statement line items |

**Total**: 7 tables

---

## Section 6: Insights Module (`insights_*`)

Analytics, KPIs, dashboards, and variance analysis.

| Current Name | New Name | Model File | Notes |
|--------------|----------|------------|-------|
| `kpi_values` | `insights_kpi_values` | analysis.py | Calculated KPIs |
| `dashboard_configs` | `insights_dashboard_configs` | analysis.py | Dashboard layouts |
| `dashboard_widgets` | `insights_dashboard_widgets` | analysis.py | Widget configs |
| `user_preferences` | `insights_user_preferences` | analysis.py | User settings |
| `actual_data` | `insights_actual_data` | analysis.py | Imported actuals |
| `budget_vs_actual` | `insights_budget_vs_actual` | analysis.py | Variance table |
| `variance_explanations` | `insights_variance_explanations` | analysis.py | Variance notes |
| `historical_actuals` | `insights_historical_actuals` | analysis.py | Prior year actuals |

**Total**: 8 tables

---

## Section 7: Admin Module (`admin_*`)

Organizations, audit, and system administration.

| Current Name | New Name | Model File | Notes |
|--------------|----------|------------|-------|
| `organizations` | `admin_organizations` | auth.py | Organization definitions |
| `users` | `admin_users` | auth.py | User profiles (in efir_budget) |
| `integration_logs` | `admin_integration_logs` | integrations.py | Import/export logs |
| `planning_cells` | `admin_planning_cells` | (migration) | Cell-level storage |
| `cell_changes` | `admin_cell_changes` | (migration) | Audit trail |
| `cell_comments` | `admin_cell_comments` | (migration) | Cell annotations |
| `historical_comparison_runs` | `admin_historical_comparison_runs` | (migration) | Compare job runs |

**Total**: 7 tables

---

## Summary

| Module | Count | Status |
|--------|-------|--------|
| Reference (`ref_*`) | 8 | Pending |
| Settings (`settings_*`) | 12 | Pending |
| Students (`students_*`) | 12 | Pending |
| Teachers (`teachers_*`) | 7 | Pending |
| Finance (`finance_*`) | 7 | Pending |
| Insights (`insights_*`) | 8 | Pending |
| Admin (`admin_*`) | 7 | Pending |
| **TOTAL** | **61** | **Pending** |

---

## Phase 3B Additional Tasks

### Task 1: Add `scenario_type` enum to `settings_versions`

```sql
CREATE TYPE efir_budget.scenario_type AS ENUM (
    'ACTUAL',      -- Historical actuals (locked, immutable)
    'BUDGET',      -- Official approved budget
    'FORECAST',    -- Mid-year forecast revisions
    'STRATEGIC',   -- 5-year strategic planning
    'WHAT_IF'      -- Scenario analysis (sandboxed)
);

ALTER TABLE efir_budget.settings_versions
ADD COLUMN scenario_type efir_budget.scenario_type NOT NULL DEFAULT 'BUDGET';
```

### Task 2: Update VersionedMixin FK reference

After renaming `budget_versions` → `settings_versions`, update all foreign keys.

---

## Migration Strategy

1. **Create comprehensive Alembic migration** with all renames
2. **Update SQLAlchemy models** `__tablename__` attributes
3. **Update all services** with new table references
4. **Update all API endpoints**
5. **Update all tests**
6. **Run full test suite**
7. **Update documentation**

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| FK constraint failures | HIGH | Rename in dependency order |
| Index name conflicts | MEDIUM | Rename indexes too |
| RLS policy breaks | HIGH | Update policy definitions |
| Cache key mismatches | LOW | Clear caches after migration |

---

*Document created as part of Phase 3B planning.*
