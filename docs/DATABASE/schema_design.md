# EFIR Budget Planning - Database Schema Design

**Version:** 1.0
**Date:** 2025-11-30
**Schema:** `efir_budget` (isolated from other applications)
**Database:** PostgreSQL 17.x via Supabase

## Table of Contents
1. [Design Principles](#design-principles)
2. [Common Patterns](#common-patterns)
3. [Configuration Layer (Modules 1-6)](#configuration-layer)
4. [Planning Layer (Modules 7-12)](#planning-layer)
5. [Consolidation Layer (Modules 13-14)](#consolidation-layer)
6. [Analysis & Strategic Layers (Modules 15-18)](#analysis-strategic-layer)
7. [Row Level Security (RLS)](#row-level-security)
8. [Indexes & Performance](#indexes-performance)

---

## Design Principles

### 1. Schema Isolation
- All tables reside in `efir_budget` schema to avoid conflicts with other applications in Supabase
- Database search path: `efir_budget, public`

### 2. Audit Trail
All tables include:
```sql
created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
created_by UUID REFERENCES auth.users(id)
updated_by UUID REFERENCES auth.users(id)
```

### 3. Version Management
Budget data supports multiple versions:
- `Working`: Active editing
- `Submitted`: Pending approval
- `Approved`: Locked for reference
- `Forecast`: Mid-year revision
- `Superseded`: Historical version

### 4. Soft Deletes
Tables use `deleted_at` for soft deletes to maintain audit history

### 5. Multi-Currency Support
- Primary currency: SAR (Saudi Riyal)
- Exchange rates stored for EUR conversions (AEFE teacher costs)

### 6. Driver-Based Calculations
Most values are calculated from drivers (enrollment, FTE, square meters) rather than manual entry

---

## Common Patterns

### Base Mixin Fields
```python
class AuditMixin:
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID
    updated_by_id: UUID

class SoftDeleteMixin:
    deleted_at: datetime | None

class VersionedMixin:
    budget_version_id: UUID  # Foreign key to budget_versions
```

### Naming Conventions
- Tables: `snake_case`, plural (e.g., `academic_levels`, `subject_hours`)
- Primary keys: `id` (UUID)
- Foreign keys: `{table}_id` (e.g., `level_id`, `subject_id`)
- Timestamps: `{action}_at` (e.g., `created_at`, `submitted_at`)

---

## Configuration Layer

### Module 1: System Configuration

#### `system_configs`
Global system parameters

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| key | VARCHAR(100) | Config key (unique) |
| value | JSONB | Config value (flexible structure) |
| category | VARCHAR(50) | Category (currency, locale, academic, etc.) |
| description | TEXT | Human-readable description |
| is_active | BOOLEAN | Whether config is active |
| ...audit fields... |

**Example Data:**
```json
{
  "key": "DEFAULT_CURRENCY",
  "value": {"code": "SAR", "symbol": "ر.س"},
  "category": "currency"
}
{
  "key": "EUR_TO_SAR_RATE",
  "value": {"rate": 4.05, "effective_date": "2025-09-01"},
  "category": "currency"
}
{
  "key": "STANDARD_TEACHING_HOURS_PRIMARY",
  "value": {"hours": 24},
  "category": "academic"
}
{
  "key": "STANDARD_TEACHING_HOURS_SECONDARY",
  "value": {"hours": 18},
  "category": "academic"
}
```

#### `budget_versions`
Version control for budgets

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Version name (e.g., "Budget 2025-2026") |
| fiscal_year | INTEGER | Fiscal year (e.g., 2026) |
| academic_year | VARCHAR(20) | Academic year (e.g., "2025-2026") |
| status | ENUM | working, submitted, approved, forecast, superseded |
| submitted_at | TIMESTAMP | When submitted for approval |
| submitted_by_id | UUID | User who submitted |
| approved_at | TIMESTAMP | When approved |
| approved_by_id | UUID | User who approved |
| notes | TEXT | Version notes |
| is_baseline | BOOLEAN | Whether this is the baseline version |
| parent_version_id | UUID | Parent version (for forecasts) |
| ...audit fields... |

**Business Rules:**
- Only one version can be `status = 'working'` per fiscal year
- Approved versions are read-only
- Forecast versions must have a parent approved version

---

### Module 2: Class Size Parameters

#### `academic_cycles`
Academic cycle definitions (Maternelle, Élémentaire, Collège, Lycée)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code | VARCHAR(20) | Cycle code (MAT, ELEM, COLL, LYC) |
| name_fr | VARCHAR(100) | French name |
| name_en | VARCHAR(100) | English name |
| sort_order | INTEGER | Display order |
| requires_atsem | BOOLEAN | Whether ATSEM is required (Maternelle) |
| ...audit fields... |

#### `academic_levels`
Academic levels (PS, MS, GS, CP, CE1... Terminale)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| cycle_id | UUID | FK to academic_cycles |
| code | VARCHAR(20) | Level code (PS, MS, GS, CP, etc.) |
| name_fr | VARCHAR(100) | French name |
| name_en | VARCHAR(100) | English name |
| sort_order | INTEGER | Display order within cycle |
| is_secondary | BOOLEAN | Whether this is secondary (DHG applicable) |
| ...audit fields... |

#### `class_size_params`
Class size parameters per level and version

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| level_id | UUID | FK to academic_levels (NULL for cycle defaults) |
| cycle_id | UUID | FK to academic_cycles (NULL if level-specific) |
| min_class_size | INTEGER | Minimum viable class size |
| target_class_size | INTEGER | Target/optimal class size |
| max_class_size | INTEGER | Maximum allowed class size |
| notes | TEXT | Parameter notes |
| ...audit fields... |

**Business Rules:**
- `min_class_size < target_class_size ≤ max_class_size`
- Level-specific params override cycle defaults
- Maternelle typically: min=15, target=22, max=25
- Élémentaire: min=18, target=24, max=28
- Secondary: min=15, target=24, max=30

---

### Module 3: Subject Hours Configuration

#### `subjects`
Subject catalog

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code | VARCHAR(20) | Subject code (MATH, FRAN, ANGL, etc.) |
| name_fr | VARCHAR(100) | French name |
| name_en | VARCHAR(100) | English name |
| category | VARCHAR(50) | Category (core, specialty, elective) |
| is_active | BOOLEAN | Whether subject is active |
| ...audit fields... |

#### `subject_hours_matrix`
Subject hours per level (DHG hours/week)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| subject_id | UUID | FK to subjects |
| level_id | UUID | FK to academic_levels |
| hours_per_week | DECIMAL(4,2) | Hours per week per class |
| is_split | BOOLEAN | Whether classes are split (half-size groups) |
| notes | TEXT | Configuration notes |
| ...audit fields... |

**Example Data:**
```
Mathématiques - 6ème: 4.5 hours/week
Français - 6ème: 5 hours/week
Anglais - 6ème: 4 hours/week
```

**Business Rules:**
- Only applicable to secondary levels (Collège, Lycée)
- Hours must be > 0 and ≤ 12 (realistic max per subject)
- Split classes count as double hours for DHG calculation

---

### Module 4: Teacher Costs Configuration

#### `teacher_categories`
Teacher employment categories

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code | VARCHAR(20) | Category code (AEFE_DETACHED, AEFE_FUNDED, LOCAL) |
| name_fr | VARCHAR(100) | French name |
| name_en | VARCHAR(100) | English name |
| description | TEXT | Category description |
| is_aefe | BOOLEAN | Whether AEFE-affiliated |
| ...audit fields... |

**Categories:**
- `AEFE_DETACHED`: AEFE detached teachers (school pays PRRD)
- `AEFE_FUNDED`: AEFE fully funded teachers (no school cost)
- `LOCAL`: Locally recruited teachers

#### `teacher_cost_params`
Teacher cost parameters per category and version

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| category_id | UUID | FK to teacher_categories |
| cycle_id | UUID | FK to academic_cycles (NULL for all) |
| prrd_contribution_eur | DECIMAL(10,2) | PRRD contribution per teacher (EUR) |
| avg_salary_sar | DECIMAL(10,2) | Average salary for local teachers (SAR) |
| social_charges_rate | DECIMAL(5,4) | Social charges rate (e.g., 0.21 for 21%) |
| benefits_allowance_sar | DECIMAL(10,2) | Benefits/allowances per teacher |
| hsa_hourly_rate_sar | DECIMAL(8,2) | HSA (overtime) hourly rate |
| max_hsa_hours | DECIMAL(4,2) | Max HSA hours per teacher (2-4) |
| notes | TEXT | Parameter notes |
| ...audit fields... |

**Business Rules:**
- AEFE PRRD contribution ~41,863 EUR/teacher/year
- Local teacher costs vary by cycle (primary vs secondary)
- HSA capped at 2-4 hours per teacher per week

---

### Module 5: Fee Structure Configuration

#### `fee_categories`
Fee category definitions

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code | VARCHAR(20) | Category code (TUITION, DAI, REGISTRATION, etc.) |
| name_fr | VARCHAR(100) | French name |
| name_en | VARCHAR(100) | English name |
| account_code | VARCHAR(20) | PCG account code (70xxx) |
| is_recurring | BOOLEAN | Whether charged annually |
| allows_sibling_discount | BOOLEAN | Whether sibling discount applies |
| ...audit fields... |

**Categories:**
- `TUITION`: Tuition fees (70110-70130 by trimester)
- `DAI`: Droit Annuel d'Inscription (enrollment fee)
- `REGISTRATION`: One-time registration fee
- `TRANSPORT`: Transportation fees
- `CANTEEN`: Canteen/lunch fees

#### `nationality_types`
Nationality-based fee tiers

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code | VARCHAR(20) | Type code (FRENCH, SAUDI, OTHER) |
| name_fr | VARCHAR(100) | French name |
| name_en | VARCHAR(100) | English name |
| vat_applicable | BOOLEAN | Whether VAT applies (Saudi: no, Others: yes) |
| sort_order | INTEGER | Display order |
| ...audit fields... |

#### `fee_structure`
Fee amounts per level, nationality, and category

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| level_id | UUID | FK to academic_levels |
| nationality_type_id | UUID | FK to nationality_types |
| fee_category_id | UUID | FK to fee_categories |
| amount_sar | DECIMAL(10,2) | Fee amount in SAR |
| trimester | INTEGER | Trimester (1-3) for tuition, NULL for others |
| notes | TEXT | Fee notes |
| ...audit fields... |

**Business Rules:**
- Tuition split: T1=40%, T2=30%, T3=30%
- Sibling discount (25%) applies from 3rd child onward
- Discount only on tuition, not DAI or registration

---

### Module 6: Timetable Constraints

#### `timetable_constraints`
Scheduling constraints per level

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| level_id | UUID | FK to academic_levels |
| total_hours_per_week | DECIMAL(5,2) | Total student hours per week |
| max_hours_per_day | DECIMAL(4,2) | Maximum hours per day |
| days_per_week | INTEGER | School days per week (typically 5) |
| requires_lunch_break | BOOLEAN | Whether lunch break required |
| min_break_duration_minutes | INTEGER | Minimum break duration |
| notes | TEXT | Constraint notes |
| ...audit fields... |

**Business Rules:**
- Primary: typically 24-26 hours/week
- Secondary: typically 28-35 hours/week
- Max hours/day: 6-7 hours

---

## Planning Layer

### Module 7: Enrollment Planning

#### `enrollment_plans`
Enrollment projections per level, nationality, and version

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| level_id | UUID | FK to academic_levels |
| nationality_type_id | UUID | FK to nationality_types |
| student_count | INTEGER | Projected number of students |
| notes | TEXT | Enrollment notes |
| ...audit fields... |

**Business Rules:**
- Total enrollment capped at ~1,875 students (facility capacity)
- Enrollment drives all downstream calculations

---

### Module 8: Class Structure Planning

#### `class_structures`
Calculated class formations

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| level_id | UUID | FK to academic_levels |
| total_students | INTEGER | Total students (sum of enrollment by level) |
| number_of_classes | INTEGER | Number of classes formed |
| avg_class_size | DECIMAL(5,2) | Average class size |
| requires_atsem | BOOLEAN | Whether ATSEM required |
| atsem_count | INTEGER | Number of ATSEM needed |
| calculation_method | VARCHAR(50) | Method used (target, min, max) |
| notes | TEXT | Class formation notes |
| ...audit fields... |

**Calculation Logic:**
```python
# Simple division method (most common)
number_of_classes = ceil(total_students / target_class_size)

# Constraint: max_class_size not exceeded
avg_class_size = total_students / number_of_classes
if avg_class_size > max_class_size:
    number_of_classes += 1
```

---

### Module 9: DHG Workforce Planning

#### `dhg_subject_hours`
DHG hours calculation per subject and level

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| subject_id | UUID | FK to subjects |
| level_id | UUID | FK to academic_levels |
| number_of_classes | INTEGER | Classes at this level (from class_structures) |
| hours_per_class_per_week | DECIMAL(4,2) | Hours per class (from subject_hours_matrix) |
| total_hours_per_week | DECIMAL(6,2) | Total hours (classes × hours) |
| ...audit fields... |

**Calculation:**
```
total_hours_per_week = number_of_classes × hours_per_class_per_week
```

#### `dhg_teacher_requirements`
Teacher FTE requirements per subject

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| subject_id | UUID | FK to subjects |
| total_hours_per_week | DECIMAL(6,2) | Sum of DHG hours for subject |
| standard_teaching_hours | DECIMAL(4,2) | Standard hours (18h secondary) |
| simple_fte | DECIMAL(5,2) | Hours ÷ Standard hours |
| rounded_fte | INTEGER | Rounded up FTE (ceiling) |
| hsa_hours | DECIMAL(5,2) | Overtime hours needed |
| ...audit fields... |

**Calculation (Secondary):**
```
simple_fte = total_hours_per_week / 18
rounded_fte = ceil(simple_fte)
hsa_hours = max(0, total_hours_per_week - (rounded_fte × 18))
```

#### `teacher_allocations`
Actual teacher assignments (TRMD - Gap Analysis)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| subject_id | UUID | FK to subjects |
| cycle_id | UUID | FK to academic_cycles (primary grouping) |
| category_id | UUID | FK to teacher_categories |
| fte_count | DECIMAL(5,2) | Number of FTE allocated |
| notes | TEXT | Allocation notes |
| ...audit fields... |

**TRMD Logic:**
```
Besoins (Need) = dhg_teacher_requirements.rounded_fte
Moyens (Available) = SUM(teacher_allocations.fte_count WHERE category IN (AEFE, LOCAL))
Déficit = Besoins - Moyens
```

---

### Module 10: Revenue Planning

#### `revenue_plans`
Revenue projections

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| account_code | VARCHAR(20) | PCG revenue account (70xxx-77xxx) |
| description | TEXT | Line item description |
| category | VARCHAR(50) | Category (tuition, fees, other) |
| amount_sar | DECIMAL(12,2) | Revenue amount |
| is_calculated | BOOLEAN | Whether auto-calculated from drivers |
| calculation_driver | VARCHAR(100) | Driver reference (e.g., "enrollment") |
| trimester | INTEGER | Trimester (1-3) or NULL |
| notes | TEXT | Revenue notes |
| ...audit fields... |

**Auto-Calculated Revenue:**
- Tuition: `enrollment × fee_structure.amount_sar`
- By trimester, level, nationality

---

### Module 11: Cost Planning (Personnel & Operating)

#### `personnel_cost_plans`
Personnel cost projections

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| account_code | VARCHAR(20) | PCG expense account (64xxx) |
| description | TEXT | Cost description |
| category_id | UUID | FK to teacher_categories (or other staff) |
| cycle_id | UUID | FK to academic_cycles (or NULL for admin) |
| fte_count | DECIMAL(5,2) | Number of FTE |
| unit_cost_sar | DECIMAL(10,2) | Cost per FTE |
| total_cost_sar | DECIMAL(12,2) | Total cost (FTE × unit) |
| is_calculated | BOOLEAN | Whether auto-calculated |
| calculation_driver | VARCHAR(100) | Driver (e.g., "dhg_allocation") |
| notes | TEXT | Cost notes |
| ...audit fields... |

**Account Codes:**
- `64110`: Teaching salaries
- `64120`: Administrative salaries
- `64130`: Support staff salaries
- `64500`: Social charges

#### `operating_cost_plans`
Operating expense projections

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| account_code | VARCHAR(20) | PCG expense account (60xxx-68xxx) |
| description | TEXT | Expense description |
| category | VARCHAR(50) | Category (supplies, utilities, maintenance) |
| amount_sar | DECIMAL(12,2) | Expense amount |
| is_calculated | BOOLEAN | Whether auto-calculated from driver |
| calculation_driver | VARCHAR(100) | Driver (e.g., "enrollment", "square_meters") |
| notes | TEXT | Expense notes |
| ...audit fields... |

---

### Module 12: Capital Expenditure (CapEx) Planning

#### `capex_plans`
Capital expenditure projections

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| account_code | VARCHAR(20) | PCG account code (20xxx-21xxx assets) |
| description | TEXT | Asset description |
| category | VARCHAR(50) | Category (equipment, IT, furniture, building) |
| quantity | INTEGER | Number of units |
| unit_cost_sar | DECIMAL(10,2) | Cost per unit |
| total_cost_sar | DECIMAL(12,2) | Total cost |
| acquisition_date | DATE | Expected acquisition date |
| useful_life_years | INTEGER | Depreciation life |
| notes | TEXT | CapEx notes |
| ...audit fields... |

---

## Consolidation Layer

### Module 13: Budget Consolidation

#### `budget_consolidation`
Consolidated budget summary

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| total_revenue_sar | DECIMAL(14,2) | Total revenue |
| total_personnel_cost_sar | DECIMAL(14,2) | Total personnel costs |
| total_operating_cost_sar | DECIMAL(14,2) | Total operating costs |
| total_capex_sar | DECIMAL(14,2) | Total CapEx |
| total_expenses_sar | DECIMAL(14,2) | Total expenses |
| net_result_sar | DECIMAL(14,2) | Net result (revenue - expenses) |
| calculated_at | TIMESTAMP | When consolidation was run |
| ...audit fields... |

**Calculation:**
```
total_revenue = SUM(revenue_plans.amount_sar)
total_personnel_cost = SUM(personnel_cost_plans.total_cost_sar)
total_operating_cost = SUM(operating_cost_plans.amount_sar)
total_capex = SUM(capex_plans.total_cost_sar)
total_expenses = total_personnel_cost + total_operating_cost + total_capex
net_result = total_revenue - total_expenses
```

---

### Module 14: Financial Statements

#### `financial_statements`
Generated financial statements

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| statement_type | VARCHAR(50) | Type (income_statement, balance_sheet, cash_flow) |
| format | VARCHAR(20) | Format (PCG, IFRS) |
| account_code | VARCHAR(20) | Account code |
| account_name | TEXT | Account description |
| amount_sar | DECIMAL(14,2) | Amount |
| parent_account_code | VARCHAR(20) | Parent account (for hierarchical) |
| level | INTEGER | Hierarchy level (1=section, 2=subsection, etc.) |
| sort_order | INTEGER | Display order |
| ...audit fields... |

**Statement Types:**
- `income_statement`: Compte de résultat (PCG/IFRS)
- `balance_sheet`: Bilan
- `cash_flow`: Tableau de trésorerie

---

## Analysis & Strategic Layer

### Module 15: Statistical Analysis (KPIs)

#### `kpi_definitions`
KPI catalog

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| code | VARCHAR(50) | KPI code (H_E_RATIO, REVENUE_PER_STUDENT, etc.) |
| name_fr | VARCHAR(100) | French name |
| name_en | VARCHAR(100) | English name |
| category | VARCHAR(50) | Category (enrollment, financial, workforce) |
| formula | TEXT | Calculation formula (human-readable) |
| unit | VARCHAR(20) | Unit (ratio, SAR, %, count) |
| target_value | DECIMAL(10,2) | Target/benchmark value |
| ...audit fields... |

#### `kpi_values`
Calculated KPI values per version

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions |
| kpi_definition_id | UUID | FK to kpi_definitions |
| value | DECIMAL(12,4) | KPI value |
| variance_from_target | DECIMAL(12,4) | Difference from target |
| calculated_at | TIMESTAMP | Calculation timestamp |
| ...audit fields... |

**Key KPIs:**
- `H_E_RATIO`: Hours per student (workforce efficiency)
- `E_D_RATIO`: Students per class (class size efficiency)
- `REVENUE_PER_STUDENT`: Total revenue / enrollment
- `COST_PER_STUDENT`: Total expenses / enrollment
- `PERSONNEL_COST_PCT`: Personnel cost % of total expenses

---

### Module 16: Dashboard Configuration

#### `dashboards`
Dashboard definitions

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Dashboard name |
| description | TEXT | Dashboard description |
| user_role | VARCHAR(50) | Target role (admin, manager, viewer) |
| is_default | BOOLEAN | Whether default for role |
| layout_config | JSONB | Layout configuration (widgets, positions) |
| ...audit fields... |

#### `dashboard_widgets`
Widget configurations

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| dashboard_id | UUID | FK to dashboards |
| widget_type | VARCHAR(50) | Widget type (kpi_card, chart, table, etc.) |
| title | VARCHAR(100) | Widget title |
| data_source | VARCHAR(100) | Data source reference |
| config | JSONB | Widget-specific configuration |
| position_x | INTEGER | Grid X position |
| position_y | INTEGER | Grid Y position |
| width | INTEGER | Grid width |
| height | INTEGER | Grid height |
| ...audit fields... |

---

### Module 17: Budget vs Actual Analysis

#### `actual_data`
Actual financial data (imported from Odoo)

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| fiscal_year | INTEGER | Fiscal year |
| period | INTEGER | Period (1-12 for months) |
| account_code | VARCHAR(20) | PCG account code |
| amount_sar | DECIMAL(14,2) | Actual amount |
| import_date | TIMESTAMP | When imported |
| source | VARCHAR(50) | Source system (odoo, manual) |
| notes | TEXT | Import notes |
| ...audit fields... |

#### `budget_vs_actual`
Variance analysis

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| budget_version_id | UUID | FK to budget_versions (approved baseline) |
| account_code | VARCHAR(20) | PCG account code |
| period | INTEGER | Period (1-12) |
| budget_amount_sar | DECIMAL(14,2) | Budgeted amount |
| actual_amount_sar | DECIMAL(14,2) | Actual amount |
| variance_sar | DECIMAL(14,2) | Variance (actual - budget) |
| variance_pct | DECIMAL(7,4) | Variance % |
| calculated_at | TIMESTAMP | Calculation timestamp |
| ...audit fields... |

---

### Module 18: 5-Year Strategic Plan

#### `strategic_scenarios`
Strategic planning scenarios

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| name | VARCHAR(100) | Scenario name (Conservative, Base, Optimistic) |
| description | TEXT | Scenario description |
| start_year | INTEGER | Start year |
| end_year | INTEGER | End year (typically start + 4) |
| assumptions | JSONB | Key assumptions (enrollment growth rate, etc.) |
| is_baseline | BOOLEAN | Whether baseline scenario |
| ...audit fields... |

#### `strategic_plan_enrollment`
5-year enrollment projections

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| scenario_id | UUID | FK to strategic_scenarios |
| fiscal_year | INTEGER | Projection year |
| level_id | UUID | FK to academic_levels |
| nationality_type_id | UUID | FK to nationality_types |
| projected_students | INTEGER | Student count projection |
| growth_rate | DECIMAL(5,4) | Year-over-year growth rate |
| ...audit fields... |

#### `strategic_plan_financials`
5-year financial projections

| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| scenario_id | UUID | FK to strategic_scenarios |
| fiscal_year | INTEGER | Projection year |
| total_revenue_sar | DECIMAL(14,2) | Projected revenue |
| total_expenses_sar | DECIMAL(14,2) | Projected expenses |
| net_result_sar | DECIMAL(14,2) | Projected net result |
| cumulative_result_sar | DECIMAL(14,2) | Cumulative result from start |
| ...audit fields... |

---

## Row Level Security (RLS)

### User Roles
- **Admin**: Full access to all data
- **Budget Manager**: Read/write access to working versions, read-only for approved
- **Viewer**: Read-only access to approved versions only

### RLS Policies

#### `budget_versions` Table
```sql
-- Admin: Full access
CREATE POLICY admin_all ON efir_budget.budget_versions
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM auth.users u
      WHERE u.id = auth.uid()
      AND u.raw_user_meta_data->>'role' = 'admin'
    )
  );

-- Budget Manager: Read/write working, read-only others
CREATE POLICY manager_working ON efir_budget.budget_versions
  FOR ALL
  TO authenticated
  USING (
    status = 'working'
    AND EXISTS (
      SELECT 1 FROM auth.users u
      WHERE u.id = auth.uid()
      AND u.raw_user_meta_data->>'role' IN ('admin', 'manager')
    )
  );

CREATE POLICY manager_readonly ON efir_budget.budget_versions
  FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM auth.users u
      WHERE u.id = auth.uid()
      AND u.raw_user_meta_data->>'role' IN ('admin', 'manager', 'viewer')
    )
  );
```

#### Generic Versioned Data Tables
All tables with `budget_version_id` inherit access from parent version:

```sql
CREATE POLICY version_access ON efir_budget.{table_name}
  FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM efir_budget.budget_versions bv
      WHERE bv.id = budget_version_id
      -- User has access to this version based on budget_versions RLS
    )
  );
```

---

## Indexes & Performance

### Primary Indexes
All tables have:
- Primary key index on `id` (UUID)
- Index on `created_at` for audit queries
- Indexes on foreign keys for join performance

### Composite Indexes

#### Enrollment & Planning
```sql
CREATE INDEX idx_enrollment_version_level
  ON efir_budget.enrollment_plans(budget_version_id, level_id);

CREATE INDEX idx_class_structure_version_level
  ON efir_budget.class_structures(budget_version_id, level_id);
```

#### Financial Data
```sql
CREATE INDEX idx_revenue_version_account
  ON efir_budget.revenue_plans(budget_version_id, account_code);

CREATE INDEX idx_cost_version_account
  ON efir_budget.personnel_cost_plans(budget_version_id, account_code);
```

#### DHG Calculations
```sql
CREATE INDEX idx_dhg_hours_version_subject_level
  ON efir_budget.dhg_subject_hours(budget_version_id, subject_id, level_id);

CREATE INDEX idx_teacher_req_version_subject
  ON efir_budget.dhg_teacher_requirements(budget_version_id, subject_id);
```

### Unique Constraints

```sql
-- System configs: unique key per system
ALTER TABLE efir_budget.system_configs
  ADD CONSTRAINT uk_config_key UNIQUE (key);

-- Academic levels: unique code
ALTER TABLE efir_budget.academic_levels
  ADD CONSTRAINT uk_level_code UNIQUE (code);

-- Enrollment: one record per version/level/nationality
ALTER TABLE efir_budget.enrollment_plans
  ADD CONSTRAINT uk_enrollment_version_level_nat
  UNIQUE (budget_version_id, level_id, nationality_type_id);
```

---

## Triggers

### Audit Timestamp Trigger
```sql
CREATE OR REPLACE FUNCTION efir_budget.update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all tables with updated_at
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON efir_budget.{table_name}
  FOR EACH ROW
  EXECUTE FUNCTION efir_budget.update_updated_at();
```

### Version Lock Trigger
```sql
-- Prevent modification of approved budget versions
CREATE OR REPLACE FUNCTION efir_budget.prevent_approved_modification()
RETURNS TRIGGER AS $$
BEGIN
  IF OLD.status = 'approved' AND NEW.status != OLD.status THEN
    RAISE EXCEPTION 'Cannot modify approved budget version';
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER lock_approved_versions
  BEFORE UPDATE ON efir_budget.budget_versions
  FOR EACH ROW
  EXECUTE FUNCTION efir_budget.prevent_approved_modification();
```

---

## Schema Migration Plan

### Phase 1: Core Infrastructure
1. Create `efir_budget` schema
2. Create base tables: `system_configs`, `budget_versions`, `academic_cycles`, `academic_levels`
3. Create Configuration Layer tables (Modules 1-6)
4. Seed reference data (cycles, levels, subjects, nationalities)

### Phase 2: Planning Layer
5. Create Planning Layer tables (Modules 7-12)
6. Set up calculation dependencies

### Phase 3: Consolidation & Analysis
7. Create Consolidation Layer tables (Modules 13-14)
8. Create Analysis & Strategic tables (Modules 15-18)

### Phase 4: Security & Performance
9. Implement RLS policies
10. Create indexes
11. Add triggers

---

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-11-30 | System | Initial schema design for all 18 modules |

