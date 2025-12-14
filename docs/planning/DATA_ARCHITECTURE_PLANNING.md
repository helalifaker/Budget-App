# EFIR Budget App - Data Architecture Planning Document

**Created**: 2025-12-14
**Status**: PLANNING PHASE
**Purpose**: Comprehensive review of calculation engines and data storage strategy

---

## Executive Summary

This document captures the planning phase for restructuring the EFIR Budget App database schema to:
1. Unify budget, actual, and forecast data under a single versioning model
2. Distinguish between calculated data (derived on-the-fly) vs stored data (source of truth)
3. Add cost centers and profit centers for better financial tracking
4. Reduce schema complexity while maintaining functionality

---

## Part 1: Calculation Engines Analysis

The application has **7 calculation engines** in `backend/app/engine/`. Each engine is a pure Python function with Pydantic input/output models.

### 1.1 DHG Engine (Dotation Horaire Globale)

**Location**: `backend/app/engine/dhg/`

**Purpose**: Calculate teaching hours required and teacher FTE based on French education standards.

**Inputs**:
| Field | Type | Source |
|-------|------|--------|
| level_id | UUID | `academic_levels` table |
| level_code | str | `academic_levels` table |
| education_level | enum | primary/secondary |
| number_of_classes | int | Class structure planning |
| subject_hours_list | list | `subject_hours` config table |

**Key Formulas**:
```
total_hours = Σ(number_of_classes × hours_per_subject)
simple_fte = total_hours ÷ standard_hours (18h secondary, 24h primary)
rounded_fte = ceil(simple_fte)
fte_utilization = (simple_fte ÷ rounded_fte) × 100
hsa_needed = dhg_hours - (available_fte × standard_hours)
```

**Outputs**:
- DHGHoursResult: total_hours, subject_breakdown
- FTECalculationResult: simple_fte, rounded_fte, fte_utilization
- TeacherRequirement: total_dhg_hours by subject, hsa_hours
- TRMDGapResult: gap_fte, is_overstaffed

**Data Strategy**: **ALWAYS CALCULATED**
- Never store DHG hours or FTE in database
- Calculate on-demand from class structure + subject hours config
- Cache results with Redis if performance requires it

---

### 1.2 Enrollment Engine

**Location**: `backend/app/engine/enrollment/`

**Purpose**: Project student enrollment across multiple years.

**Inputs**:
| Field | Type | Source |
|-------|------|--------|
| level_id | UUID | `academic_levels` table |
| level_code | str | `academic_levels` table |
| nationality | str | French/Saudi/Other |
| current_enrollment | int | **Base data - STORED** |
| growth_scenario | enum | conservative/base/optimistic |
| custom_growth_rate | Decimal | Optional override |
| years_to_project | int | 1-10 |

**Key Formulas**:
```
projected_enrollment = current × (1 + growth_rate)^years
retention_model: next_year = (current × retention_rate) + new_intake
attrition = current × attrition_rate
```

**Growth Rate Defaults**:
- Conservative: 1% per year
- Base: 4% per year
- Optimistic: 7% per year

**Outputs**:
- EnrollmentProjection: projected_enrollment, growth_rate_applied
- EnrollmentProjectionResult: total_growth_students, total_growth_percent

**Data Strategy**: **MIXED**
- Base enrollment (current_enrollment) → **STORED** (source of truth)
- Growth scenarios/rates → **CONFIG** (stored in config table)
- Projections → **CALCULATED** (derived from base + scenario)
- Historical snapshots → **STORED** (for year-over-year comparison)

---

### 1.3 EOS Engine (End of Service)

**Location**: `backend/app/engine/eos/`

**Purpose**: Calculate End of Service benefits per KSA Labor Law.

**Inputs**:
| Field | Type | Source |
|-------|------|--------|
| hire_date | date | `employees` table |
| termination_date | date | Input or as_of_date for provision |
| basic_salary_sar | Decimal | `salaries` table |
| termination_reason | enum | termination/resignation/end_of_contract/retirement |

**Key Formulas (KSA Labor Law Articles 84-85)**:
```
years_1_to_5_amount = 0.5 × basic_salary × min(years, 5)
years_6_plus_amount = 1.0 × basic_salary × max(years - 5, 0)
gross_eos = years_1_to_5 + years_6_plus

Resignation factors:
- < 2 years:  0% (no EOS)
- 2-5 years:  33%
- 5-10 years: 67%
- > 10 years: 100%

final_eos = gross_eos × resignation_factor
```

**Outputs**:
- EOSResult: years_of_service, gross_eos, final_eos
- EOSProvisionResult: provision_amount (accrued liability)

**Data Strategy**: **CALCULATED**
- Employee data (hire_date, salary) → **STORED**
- EOS amounts → **CALCULATED** (always derived from current employee data)
- Budget provisions → Store the scenario-snapshot, not individual EOS

---

### 1.4 GOSI Engine (Social Insurance)

**Location**: `backend/app/engine/gosi/`

**Purpose**: Calculate GOSI contributions per KSA law.

**Inputs**:
| Field | Type | Source |
|-------|------|--------|
| gross_salary_sar | Decimal | `salaries` table |
| nationality | enum | saudi/expatriate (from `employees` table) |

**Key Formulas (2024 Rates)**:
```
Saudi:
  employer_rate = 11.75%
  employee_rate = 9.75%

Expatriate:
  employer_rate = 2% (hazards only)
  employee_rate = 0%

employer_contribution = gross_salary × employer_rate
employee_contribution = gross_salary × employee_rate
net_salary = gross_salary - employee_contribution
total_employer_cost = gross_salary + employer_contribution
```

**Outputs**:
- GOSIResult: employer_contribution, employee_contribution, net_salary
- GOSISummaryResult: totals across all employees

**Data Strategy**: **CALCULATED**
- GOSI rates → **CONFIG** (stored in config table, rarely changes)
- GOSI amounts → **CALCULATED** (derived from salary × nationality)
- Never store per-employee GOSI in database

---

### 1.5 Revenue Engine

**Location**: `backend/app/engine/revenue/`

**Purpose**: Calculate tuition revenue with sibling discounts and trimester distribution.

**Inputs**:
| Field | Type | Source |
|-------|------|--------|
| level_code | str | `academic_levels` table |
| fee_category | enum | french_ttc/saudi_ht/other_ttc |
| tuition_fee | Decimal | `fee_structure` config table |
| dai_fee | Decimal | `fee_structure` config table |
| registration_fee | Decimal | `fee_structure` config table |
| sibling_order | int | Student data (1=eldest, 3rd+ gets discount) |

**Key Formulas**:
```
Sibling Discount (3rd+ child only):
  discount_amount = tuition × 0.25
  net_tuition = tuition - discount
  (DAI and registration NOT discounted)

Trimester Distribution:
  T1 = total_revenue × 40%
  T2 = total_revenue × 30%
  T3 = total_revenue × 30%

total_revenue = net_tuition + dai + registration
```

**Outputs**:
- SiblingDiscount: discount_applicable, discount_amount, net_tuition
- TuitionRevenue: base fees, discounts, net amounts, total
- TrimesterDistribution: T1, T2, T3 amounts
- StudentRevenueResult: complete breakdown

**Data Strategy**: **MIXED**
- Fee structure → **CONFIG** (stored in `fee_structure` table)
- Enrollment counts → **STORED** (in enrollment module)
- Revenue amounts → **CALCULATED** (fee × students)
- Revenue by category aggregations → **CALCULATED**

---

### 1.6 KPI Engine

**Location**: `backend/app/engine/kpi/`

**Purpose**: Calculate key performance indicators for educational and financial metrics.

**Inputs**:
| Field | Type | Source |
|-------|------|--------|
| total_students | int | Enrollment module |
| secondary_students | int | Enrollment module |
| max_capacity | int | Configuration |
| total_teacher_fte | Decimal | DHG engine output |
| dhg_hours_total | Decimal | DHG engine output |
| total_revenue | Decimal | Revenue engine output |
| total_costs | Decimal | Budget consolidation |
| personnel_costs | Decimal | Personnel planning |

**Key Formulas**:
```
student_teacher_ratio = total_students ÷ total_teacher_fte     (target: 12.0)
he_ratio_secondary = dhg_hours ÷ secondary_students            (target: 1.35)
revenue_per_student = total_revenue ÷ total_students           (target: 45,000 SAR)
cost_per_student = total_costs ÷ total_students
margin_percentage = (revenue - costs) ÷ revenue × 100          (target: 10%)
staff_cost_ratio = personnel_costs ÷ total_costs × 100         (target: 70%)
capacity_utilization = students ÷ max_capacity × 100           (target: 90-95%)
```

**Outputs**:
- KPIResult: value, target_value, variance, performance_status
- KPICalculationResult: all 7 KPIs

**Data Strategy**: **ALWAYS CALCULATED**
- KPIs are pure aggregations of other data
- Never store KPI values in database
- Calculate on-demand when displaying dashboards
- Target values → **CONFIG** (stored in config table)

---

### 1.7 Financial Statements Engine

**Location**: `backend/app/engine/financial_statements/`

**Purpose**: Generate formatted financial statements (Income Statement, Balance Sheet, Cash Flow).

**Inputs**:
| Field | Type | Source |
|-------|------|--------|
| budget_version_id | UUID | Budget version |
| consolidation_entries | list | Budget consolidation |
| statement_format | enum | french_pcg/ifrs |

**Key Formulas**:
```
Income Statement:
  operating_result = total_revenue - total_expenses
  net_result = operating_result

Balance Sheet:
  total_assets = Σ asset_entries
  is_balanced = (total_assets == total_liabilities + total_equity)

Cash Flow:
  net_cash_change = operating + investing + financing
```

**Outputs**:
- IncomeStatementResult: lines, totals, operating_result, net_result
- BalanceSheetResult: assets_lines, liabilities_lines, is_balanced
- CashFlowResult: cash flows by category

**Data Strategy**: **CALCULATED**
- Statement lines → **CALCULATED** (formatted from consolidation entries)
- Totals → **CALCULATED** (aggregated from entries)
- Consolidation entries → **STORED** (source financial data)

---

## Part 2: Calculated vs Stored Data Summary

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

## Part 3: Proposed Schema Changes

### 3.1 Unified Scenario Version Table

Replace multiple version concepts with a single `scenario_versions` table:

```sql
CREATE TYPE scenario_type AS ENUM ('BUDGET', 'ACTUAL', 'FORECAST', 'WHAT_IF');
CREATE TYPE scenario_status AS ENUM ('draft', 'submitted', 'approved', 'locked', 'archived');

CREATE TABLE scenario_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    fiscal_year INT NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    scenario_type scenario_type NOT NULL,
    status scenario_status NOT NULL DEFAULT 'draft',
    version_number INT NOT NULL DEFAULT 1,
    parent_version_id UUID REFERENCES scenario_versions(id),
    is_baseline BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID NOT NULL,
    approved_at TIMESTAMPTZ,
    approved_by UUID,
    notes TEXT,

    CONSTRAINT unique_org_year_type_version
        UNIQUE(organization_id, fiscal_year, scenario_type, version_number)
);
```

### 3.2 Unified Financial Data Table

Replace 6 separate financial tables with one unified table:

```sql
CREATE TYPE record_type AS ENUM ('revenue', 'personnel', 'operating', 'capex');
CREATE TYPE data_source AS ENUM ('planned', 'actual', 'imported', 'calculated');

CREATE TABLE financial_data (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    scenario_version_id UUID NOT NULL REFERENCES scenario_versions(id),
    record_type record_type NOT NULL,
    account_code VARCHAR(20) NOT NULL,
    description TEXT NOT NULL,
    category VARCHAR(50),
    subcategory VARCHAR(50),

    -- Amounts
    amount_sar NUMERIC(15,2) NOT NULL,
    quantity NUMERIC(10,2),
    unit_cost_sar NUMERIC(12,2),

    -- Cost allocation
    cost_center_id UUID REFERENCES cost_centers(id),
    profit_center_id UUID REFERENCES profit_centers(id),

    -- Metadata
    data_source data_source NOT NULL,
    is_calculated BOOLEAN DEFAULT FALSE,
    calculation_driver VARCHAR(100),
    period_type VARCHAR(10) DEFAULT 'annual',
    period_value INT DEFAULT 0,

    -- Audit
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    created_by UUID NOT NULL,

    INDEX idx_financial_scenario (scenario_version_id),
    INDEX idx_financial_account (account_code),
    INDEX idx_financial_type (record_type)
);
```

### 3.3 Cost Centers and Profit Centers

New tables for cost allocation:

```sql
CREATE TYPE cost_center_type AS ENUM ('educational', 'administrative', 'support', 'overhead');

CREATE TABLE profit_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    code VARCHAR(20) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    cycle_id UUID REFERENCES academic_cycles(id),
    parent_id UUID REFERENCES profit_centers(id),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT NOT NULL,

    CONSTRAINT unique_profit_center_code UNIQUE(organization_id, code)
);

-- Default profit centers:
-- PC-MAT (Maternelle), PC-ELEM (Elementary), PC-COLL (Collège),
-- PC-LYC (Lycée), PC-ADMIN (Administration), PC-CANTINA (Cantine),
-- PC-TRANSPORT, PC-EXTRACUR (Extracurricular), PC-CONSOL (Consolidated)

CREATE TABLE cost_centers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    code VARCHAR(20) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    center_type cost_center_type NOT NULL,
    cycle_id UUID REFERENCES academic_cycles(id),
    parent_id UUID REFERENCES cost_centers(id),
    default_profit_center_id UUID REFERENCES profit_centers(id),
    is_active BOOLEAN DEFAULT TRUE,
    sort_order INT NOT NULL,

    CONSTRAINT unique_cost_center_code UNIQUE(organization_id, code)
);

-- Default cost centers:
-- CC-TEACH-MAT, CC-TEACH-ELEM, CC-TEACH-SEC (Teaching by level)
-- CC-ADMIN-DIR, CC-ADMIN-FIN, CC-ADMIN-HR (Administrative)
-- CC-SUPPORT-IT, CC-SUPPORT-MAINT (Support services)
-- CC-OVERHEAD (Shared costs to allocate)
```

### 3.4 Cost Allocation Rules

For allocating shared costs:

```sql
CREATE TYPE allocation_method AS ENUM ('proportional', 'fixed', 'direct', 'step_down');

CREATE TABLE allocation_bases (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    code VARCHAR(30) NOT NULL UNIQUE,
    name_en VARCHAR(100) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    description TEXT
);

-- Example bases: student_count, class_count, floor_area, fte_count, revenue

CREATE TABLE allocation_rules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(100) NOT NULL,
    source_cost_center_id UUID NOT NULL REFERENCES cost_centers(id),
    allocation_base_id UUID NOT NULL REFERENCES allocation_bases(id),
    allocation_method allocation_method NOT NULL DEFAULT 'proportional',
    fiscal_year INT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE allocation_rule_targets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    allocation_rule_id UUID NOT NULL REFERENCES allocation_rules(id),
    target_cost_center_id UUID NOT NULL REFERENCES cost_centers(id),
    fixed_percentage NUMERIC(5,2),

    CONSTRAINT unique_rule_target UNIQUE(allocation_rule_id, target_cost_center_id)
);
```

### 3.5 Simplified Employee/Salary Structure

```sql
CREATE TABLE employees (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    employee_code VARCHAR(20) NOT NULL,
    full_name VARCHAR(200) NOT NULL,
    nationality VARCHAR(20) NOT NULL,  -- 'saudi' or 'expatriate' (determines GOSI)
    employee_type VARCHAR(20) NOT NULL, -- 'aefe' or 'local'
    category VARCHAR(30) NOT NULL,      -- 'teacher', 'administrative', 'support'
    aefe_position_type VARCHAR(20),     -- 'detached' or 'funded' (NULL for local)
    cycle_id UUID REFERENCES academic_cycles(id),
    subject_id UUID REFERENCES subjects(id),
    hire_date DATE NOT NULL,
    fte NUMERIC(4,2) DEFAULT 1.00,
    is_active BOOLEAN DEFAULT TRUE,
    is_placeholder BOOLEAN DEFAULT FALSE,

    CONSTRAINT unique_employee_code UNIQUE(organization_id, employee_code)
);

CREATE TABLE salaries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employee_id UUID NOT NULL REFERENCES employees(id),
    scenario_version_id UUID NOT NULL REFERENCES scenario_versions(id),
    basic_salary_sar NUMERIC(12,2) NOT NULL,
    housing_allowance_sar NUMERIC(12,2) DEFAULT 0,
    transport_allowance_sar NUMERIC(12,2) DEFAULT 0,
    other_allowances_sar NUMERIC(12,2) DEFAULT 0,
    effective_date DATE NOT NULL,

    -- GOSI is CALCULATED, not stored
    -- EOS is CALCULATED, not stored

    CONSTRAINT unique_employee_scenario UNIQUE(employee_id, scenario_version_id)
);
```

---

## Part 4: Views for Calculated Data

Instead of storing calculated data, create database views:

### 4.1 Budget vs Actual View

```sql
CREATE VIEW vw_budget_vs_actual AS
SELECT
    b.account_code,
    b.description,
    b.amount_sar AS budget_amount,
    COALESCE(a.amount_sar, 0) AS actual_amount,
    b.amount_sar - COALESCE(a.amount_sar, 0) AS variance_amount,
    CASE
        WHEN b.amount_sar = 0 THEN 0
        ELSE ROUND((b.amount_sar - COALESCE(a.amount_sar, 0)) / b.amount_sar * 100, 2)
    END AS variance_percent
FROM financial_data b
LEFT JOIN financial_data a
    ON a.account_code = b.account_code
    AND a.scenario_version_id IN (
        SELECT id FROM scenario_versions WHERE scenario_type = 'ACTUAL'
    )
WHERE b.scenario_version_id IN (
    SELECT id FROM scenario_versions
    WHERE scenario_type = 'BUDGET' AND is_baseline = TRUE
);
```

### 4.2 Consolidation View

```sql
CREATE VIEW vw_budget_consolidation AS
SELECT
    sv.id AS scenario_version_id,
    sv.name AS version_name,
    sv.fiscal_year,
    sv.scenario_type,
    fd.record_type,
    fd.account_code,
    fd.description,
    SUM(fd.amount_sar) AS total_amount,
    fd.cost_center_id,
    fd.profit_center_id
FROM scenario_versions sv
JOIN financial_data fd ON fd.scenario_version_id = sv.id
GROUP BY
    sv.id, sv.name, sv.fiscal_year, sv.scenario_type,
    fd.record_type, fd.account_code, fd.description,
    fd.cost_center_id, fd.profit_center_id;
```

---

## Part 5: Migration Strategy

### Phase 0: Quick Wins (2 days, LOW risk)
1. Add `scenario_type` column to `budget_versions`
2. Link `actual_data` to scenario versions
3. No breaking changes, backward compatible

### Phase 1: Add Cost/Profit Centers (1 week, LOW risk)
1. Create new tables: profit_centers, cost_centers, allocation_*
2. Add foreign keys to existing tables
3. Seed default data
4. No removal of existing functionality

### Phase 2: Unify Financial Data (2-3 weeks, MEDIUM risk)
1. Create new `financial_data` table
2. Migrate data from:
   - revenue_plans
   - personnel_cost_plans
   - operating_cost_plans
   - capex_plans
   - actual_data
3. Update API endpoints
4. Keep old tables temporarily for rollback

### Phase 3: Remove Redundant Tables (1-2 weeks, LOW risk)
1. Replace `budget_vs_actual` with view
2. Replace `budget_consolidations` with view
3. Remove duplicate storage
4. Update frontend to use new endpoints

### Phase 4: Enrollment Simplification (Optional, 1-2 weeks)
1. Reduce enrollment tables from 12 to 4
2. This is the highest risk phase
3. May be deferred to future iteration

---

## Part 6: Impact Analysis

### Lines of Code Impact

| Area | Current LOC | Estimated Change |
|------|-------------|------------------|
| Models (SQLAlchemy) | ~3,500 | -500 (fewer tables) |
| Schemas (Pydantic) | ~2,000 | +300 (unified schemas) |
| API Endpoints | ~4,000 | +500 (new endpoints) |
| Services | ~2,500 | +200 (migration logic) |
| **Net Impact** | ~12,000 | **+500 LOC** |

Note: The goal is not to reduce code, but to improve architecture.

### Risk Assessment

| Phase | Risk Level | Mitigation |
|-------|------------|------------|
| Phase 0 | LOW | Backward compatible, no data migration |
| Phase 1 | LOW | New tables only, no existing data touched |
| Phase 2 | MEDIUM | Staged migration, keep old tables for rollback |
| Phase 3 | LOW | Views are transparent to application |
| Phase 4 | HIGH | Defer if time constrained |

---

## Part 7: Decision Points

### Decisions Needed Before Implementation

1. **Versioning granularity**: Should salaries have their own version tracking, or inherit from scenario?

2. **Cost allocation timing**: Calculate allocations on-demand or pre-calculate on scenario lock?

3. **Historical data retention**: How many years of actuals to keep in unified table?

4. **AEFE position handling**: Confirm that AEFE is just an employee_type, not a separate entity.

5. **GOSI rate storage**: Single config row or rate-by-date for historical changes?

6. **Enrollment module scope**: Full simplification (12→4 tables) or minimal (keep as-is)?

---

## Appendix A: Current Table Count by Module

| Module | Current Tables | Proposed Tables | Reduction |
|--------|---------------|-----------------|-----------|
| Auth/Users | 2 | 2 | 0% |
| Configuration | 13 | 13 | 0% |
| Planning | 10 | 4 | -60% |
| Enrollment | 12 | 4-12 (decision needed) | 0-67% |
| Strategic | 4 | 4 | 0% |
| Consolidation | 3 | 1 + views | -67% |
| Personnel | 4 | 3 | -25% |
| Analysis | 9 | 6 + views | -33% |
| Integration | 2 | 2 | 0% |
| **New: Cost Centers** | 0 | 4-6 | +4-6 |
| **TOTAL** | **~54** | **~38-46** | **~15-30%** |

---

## Appendix B: Engine Dependencies

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

1. **User Review**: Review this document and confirm decisions in Part 7
2. **Phase 0 Implementation**: Add scenario_type to existing tables
3. **Phase 1 Implementation**: Create cost/profit center tables
4. **Iterative Refinement**: Each phase includes testing and validation

---

*Document Version: 1.0*
*Last Updated: 2025-12-14*
