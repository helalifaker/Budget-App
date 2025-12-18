# EFIR Budget App - Module Architecture Design

**Version**: 1.0
**Date**: 2024-12-14
**Status**: APPROVED (Option C - Domain-Driven with Finance)

---

## Executive Summary

This document defines the unified 6-module architecture for the EFIR Budget App, replacing the previous fragmented 18-module documentation structure with a cohesive, role-aligned design.

### The 6 Modules

| Module | Icon | Color | Primary Role | Purpose |
|--------|------|-------|--------------|---------|
| **Students** | GraduationCap | sage | Academic Director | Enrollment lifecycle, projections, class formation |
| **Teachers** | Users | wine | HR Manager | Workforce management, DHG planning, positions |
| **Finance** | Wallet | gold | Finance Director | Revenue, costs, CapEx, financial statements |
| **Insights** | BarChart3 | slate | All (read) | KPIs, dashboards, variance analysis |
| **Settings** | Settings | neutral | All (limited) | Configuration, parameters, strategic planning |
| **Admin** | Shield | neutral-dark | Admin only | User management, imports, audit logs |

---

## Module Details

### 1. Students Module

**Purpose**: Everything related to student enrollment, projections, and class formation.

**Frontend Routes**:
```
/students/planning         → Enrollment projections
/students/class-structure  → Class formation
/students/validation       → Data validation
/students/settings         → Entry point rates, retention
```

**Backend Engines**:
- `enrollment/projection_engine.py` - Cohort-based projections
- `enrollment/calibration_engine.py` - Year-over-year calibration
- `enrollment/lateral_optimizer.py` - Inter-level movement optimization

**Database Tables** (`students.*`):
- `enrollment_projections` - Projected student counts
- `enrollment_calibrations` - Historical calibration data
- `class_structures` - Class formation results
- `enrollment_settings` - Entry point rates, retention rates
- `lateral_movements` - Inter-level movements

**Data Flow**: Students → Teachers (DHG needs) → Finance (revenue calculation)

---

### 2. Teachers Module

**Purpose**: Employee management, DHG planning, requirements, and gap analysis.

**Frontend Routes**:
```
/teachers/employees        → Employee master data
/teachers/dhg              → DHG planning overview
/teachers/requirements     → DHG requirements
/teachers/gap-analysis     → TRMD gap analysis
/teachers/positions        → AEFE positions
/teachers/settings         → HSA limits, standard hours
```

**Backend Engines**:
- `dhg/calculator.py` - DHG hours and FTE calculation
- `eos/calculator.py` - End of Service provisions
- `gosi/calculator.py` - GOSI contributions

**Database Tables** (`teachers.*`):
- `employees` - Employee master data
- `employee_contracts` - Contract details
- `dhg_requirements` - DHG hour requirements
- `dhg_allocations` - Teacher allocations
- `aefe_positions` - AEFE-funded positions
- `position_assignments` - Position-to-employee mapping
- `eos_provisions` - EOS liability tracking
- `gosi_contributions` - GOSI calculations

**Data Flow**: Students → Teachers → Finance (personnel costs)

---

### 3. Finance Module

**Purpose**: All financial aspects - revenue planning, cost planning, CapEx, and financial statements.

**Frontend Routes**:
```
/finance/revenue           → Revenue planning
/finance/costs             → Cost planning
/finance/capex             → Capital expenditures
/finance/statements        → Financial statements (PCG/IFRS)
/finance/settings          → Fee structures, cost parameters
```

**Backend Engines**:
- `revenue/calculator.py` - Fee-based revenue projections
- `costs/calculator.py` - Personnel and operational costs (NEW)
- `financial_statements/calculator.py` - PCG/IFRS statement generation

**Database Tables** (`finance.*`):
- `revenue_projections` - Fee-based revenue
- `revenue_distributions` - Trimester distribution
- `cost_items` - All cost types
- `capex_items` - Capital expenditures
- `budget_lines` - Consolidated budget
- `financial_statements` - Generated statements
- `statement_mappings` - Account code mappings

**Data Flow**: Students + Teachers → Finance → Insights

---

### 4. Insights Module

**Purpose**: KPIs, dashboards, variance analysis, and reporting.

**Frontend Routes**:
```
/insights/kpis             → Key performance indicators
/insights/dashboards       → Dashboard views
/insights/variance         → Budget vs actual
/insights/reports          → Report generation
```

**Backend Engines**:
- `kpi/calculator.py` - KPI calculations
- `variance/calculator.py` - Variance analysis (NEW)

**Database Tables** (`insights.*`):
- `kpi_values` - Calculated KPIs
- `kpi_thresholds` - Warning/alert levels
- `dashboard_configs` - Saved dashboard layouts
- `variance_analyses` - Budget vs actual comparisons
- `reports` - Generated reports

**Data Flow**: All modules → Insights (read-only consumption)

---

### 5. Settings Module

**Purpose**: System configuration, parameters, and strategic planning.

**Frontend Routes**:
```
/settings/versions         → Budget version management
/settings/academic-years   → Year definitions
/settings/class-sizes      → Min/max/target sizes
/settings/subject-hours    → Hours per subject per level
/settings/fees             → Fee structure
/settings/strategic        → 5-year planning
```

**Backend Engines**: None (reference data only)

**Database Tables** (`settings.*`):
- `versions` - Budget versions (CENTRAL - all modules reference this)
- `academic_years` - Year definitions
- `grade_levels` - PS to Terminale
- `subjects` - Subject catalog
- `class_size_params` - Min/max/target class sizes
- `subject_hours_config` - Hours per subject per level
- `fee_structures` - Tuition, DAI, registration fees
- `cost_parameters` - GOSI rates, EOS rules
- `strategic_plans` - 5-year projections

**Data Flow**: Settings → All other modules (reference data)

---

### 6. Admin Module

**Purpose**: System administration, user management, and audit.

**Frontend Routes**:
```
/admin/users               → User management
/admin/imports             → Data imports
/admin/audit               → Audit logs
/admin/system              → System health
```

**Backend Engines**: None (system operations only)

**Database Tables** (`admin.*`):
- `users` - User accounts
- `user_roles` - Role assignments
- `audit_logs` - Change tracking
- `import_jobs` - Data import history
- `import_errors` - Import error tracking
- `system_health` - System monitoring

**Access**: Admin role only

---

## Role-Based Access Matrix

| Module | Admin | Finance Dir | HR Manager | Academic Dir | Viewer |
|--------|-------|-------------|------------|--------------|--------|
| Students | CRUD | R | R | CRUD | R |
| Teachers | CRUD | R | CRUD | R | R |
| Finance | CRUD | CRUD | R | R | R |
| Insights | CRUD | RU | R | R | R |
| Settings | CRUD | RU* | RU* | RU* | R |
| Admin | CRUD | - | - | - | - |

*RU = Read + limited Update (version-specific settings only)

---

## Data Flow Diagram

```
┌────────────────────────────────────────────────────────────────┐
│                         Settings                                │
│  (versions, parameters, academic years, subjects)              │
└─────────────────────────────┬──────────────────────────────────┘
                              │ version_id (FK)
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          Students                               │
│  (enrollment projections, class structure, lateral movements)  │
└─────────────────────────────┬──────────────────────────────────┘
                              │ student counts, class counts
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          Teachers                               │
│  (DHG requirements, employees, positions, EOS/GOSI)            │
└─────────────────────────────┬──────────────────────────────────┘
                              │ FTE needs, personnel costs
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                           Finance                               │
│  (revenue, costs, CapEx, financial statements)                 │
└─────────────────────────────┬──────────────────────────────────┘
                              │ all financial data
                              ▼
┌────────────────────────────────────────────────────────────────┐
│                          Insights                               │
│  (KPIs, dashboards, variance analysis, reports)                │
└────────────────────────────────────────────────────────────────┘

Admin (users, audit, imports) ──── spans all modules ────
```

---

## Engine-Module Ownership

Each calculation engine is owned by exactly ONE module:

| Module | Owned Engines |
|--------|---------------|
| Students | `enrollment/projection_engine.py`, `enrollment/calibration_engine.py`, `enrollment/lateral_optimizer.py` |
| Teachers | `dhg/calculator.py`, `eos/calculator.py`, `gosi/calculator.py` |
| Finance | `revenue/calculator.py`, `costs/calculator.py` (NEW), `financial_statements/calculator.py` |
| Insights | `kpi/calculator.py`, `variance/calculator.py` (NEW) |
| Settings | None (reference data only) |
| Admin | None (system operations only) |

---

## API Route Structure

```
/api/v1/students/...     (enrollment, class-structure, calibration)
/api/v1/teachers/...     (employees, dhg, positions, eos, gosi)
/api/v1/finance/...      (revenue, costs, capex, statements)
/api/v1/insights/...     (kpis, dashboards, variance, reports)
/api/v1/settings/...     (versions, parameters, config)
/api/v1/admin/...        (users, imports, audit)
```

---

## Migration Strategy

### Phase 1: Documentation (This Session)
- Update `DB_golden_rules.md` with new module structure
- Update `engine_golden_rules.md` with module ownership
- Create this module architecture document

### Phase 2: Frontend (Low Risk)
- Update `ModuleContext.tsx` with new module definitions
- Update `AppSidebar.tsx` with new module navigation
- Update route structure to match new modules

### Phase 3: Database Schemas (Medium Risk)
- Create PostgreSQL schemas (`students`, `teachers`, `finance`, etc.)
- Write migration to move tables to new schemas
- Update RLS policies per schema

### Phase 4: API Routes (Medium Risk)
- Create new route structure
- Add deprecation warnings to old routes
- Maintain backwards compatibility for 2-3 releases

### Phase 5: Engine Organization (Optional)
- Reorganize engine folders to match module structure
- Update imports across codebase

---

## Benefits

1. **Clear Mental Model**: 6 modules vs 18 - easier to understand and navigate
2. **Role-Aligned**: Each role has a primary module they own
3. **Scalable**: Add new modules without restructuring existing ones
4. **Testable**: Isolated engines per module with clear boundaries
5. **Maintainable**: Clear ownership boundaries reduce coupling
6. **Consistent**: Same structure across frontend, backend, and database

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-12-14 | Initial design based on Option C (Domain-Driven) |
