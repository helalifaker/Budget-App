# Module 11: Cost Planning

## Overview

Module 11 consolidates all operational expenses for the school budget, integrating personnel costs from Module 8, facility costs from Module 9, and projecting all other operational expenses. This module categorizes costs by French PCG account codes (60xxx-68xxx), supports driver-based cost modeling, tracks cost centers for departmental allocation, and ensures all expenses are properly budgeted across the two academic periods.

**Layer**: Planning Layer (Phase 2)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Cost optimization analytics, variance analysis tools, API endpoints (Phase 5-6)

### Purpose

- Consolidate personnel costs calculated in Module 8 (DHG Workforce Planning)
- Integrate facility costs from Module 9 (Facility Planning)
- Project all other operational expenses (supplies, utilities, professional services, etc.)
- Categorize costs by PCG account codes for French accounting compliance
- Support driver-based cost modeling (per-student, per-FTE, per-sqm, fixed)
- Track costs by cost center for departmental budgeting
- Allocate costs across academic periods (Period 1: Jan-Jun, Period 2: Sep-Dec)
- Enable scenario analysis for cost optimization

### Key Design Decisions

1. **Integration-First**: Personnel and facility costs pulled from Modules 8 and 9 (not re-entered)
2. **Driver-Based Modeling**: Costs automatically calculated from drivers (student count, FTE, area, etc.)
3. **PCG Compliance**: All costs mapped to French Chart of Accounts (60xxx-68xxx expense accounts)
4. **Cost Center Allocation**: Costs assigned to departments for management reporting
5. **Dual Currency Support**: SAR primary, EUR for AEFE-related costs
6. **Period Allocation**: Costs split across Period 1 (Jan-Jun) and Period 2 (Sep-Dec) based on activity patterns
7. **Three-Tier Cost Categories**: Personnel, Facility, and Other Operating Expenses

## Database Schema

### Tables

#### 1. cost_projections

Master table for all cost projections by category and period.

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
cost_category         costcategory NOT NULL          -- ENUM: personnel, facility, operating
cost_subcategory      VARCHAR(100) NULL              -- e.g., "Teaching Supplies", "Professional Development"
account_code          VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
cost_center_id        UUID NULL FOREIGN KEY -> cost_centers.id (RESTRICT)
amount                NUMERIC(12, 2) NOT NULL
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- amount >= 0
- account_code must start with '60', '61', '62', '63', '64', '65', '66', '67', or '68' (expense accounts)
- UNIQUE (version_id, academic_period_id, cost_category, account_code, cost_center_id)

**RLS Policies:**
- Admin: Full access to cost planning
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (version_id, academic_period_id, cost_category)
- Index on account_code for financial consolidation
- Index on cost_center_id for departmental reporting

#### 2. driver_based_costs

Costs calculated from operational drivers (enrollment, FTE, area, etc.).

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
cost_item_name        VARCHAR(200) NOT NULL
cost_driver           VARCHAR(100) NOT NULL         -- e.g., "per_student", "per_fte", "per_sqm", "fixed"
driver_quantity       NUMERIC(10, 2) NOT NULL
cost_per_unit         NUMERIC(12, 2) NOT NULL
total_cost            NUMERIC(12, 2) NOT NULL
account_code          VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
cost_center_id        UUID NULL FOREIGN KEY -> cost_centers.id (RESTRICT)
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- cost_per_unit >= 0
- total_cost >= 0
- driver_quantity >= 0
- total_cost = driver_quantity × cost_per_unit (enforced by trigger)
- UNIQUE (version_id, academic_period_id, cost_item_name, cost_driver)

**RLS Policies:**
- Same as cost_projections

**Indexes:**
- Primary key on id
- Index on (version_id, academic_period_id, cost_driver)
- Index on account_code

#### 3. personnel_cost_summary

Aggregated personnel costs from Module 8 (read-only view or materialized).

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
personnel_category    personnelcategory NOT NULL    -- ENUM: aefe_detached, aefe_funded, local_teacher, administrative, support
staff_count           INTEGER NOT NULL
total_salary_cost     NUMERIC(12, 2) NOT NULL
total_benefits_cost   NUMERIC(12, 2) NOT NULL
total_allowances      NUMERIC(12, 2) NOT NULL
total_personnel_cost  NUMERIC(12, 2) NOT NULL
currency              VARCHAR(3) NOT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- staff_count >= 0
- total_personnel_cost = total_salary_cost + total_benefits_cost + total_allowances
- UNIQUE (version_id, academic_period_id, personnel_category)

**RLS Policies:**
- Same as cost_projections

**Indexes:**
- Primary key on id
- Index on (version_id, academic_period_id)

### Enums

#### CostCategory
```sql
CREATE TYPE efir_budget.costcategory AS ENUM (
    'personnel',        -- All personnel costs (from Module 8)
    'facility',         -- Facility costs (from Module 9)
    'operating'         -- Other operating expenses
);
```

#### PersonnelCategory
```sql
CREATE TYPE efir_budget.personnelcategory AS ENUM (
    'aefe_detached',    -- AEFE Détachés (school pays PRRD)
    'aefe_funded',      -- AEFE Résidents (fully funded by AEFE)
    'local_teacher',    -- Local recruited teachers
    'administrative',   -- Administrative staff
    'support'           -- Support staff (maintenance, security, etc.)
);
```

## Data Model

### Sample Cost Projections (2025-2026, Period 2)

```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440300",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_category": "personnel",
    "cost_subcategory": "Teaching Staff - All categories",
    "account_code": "64110",
    "cost_center_id": "cost-center-academic-uuid",
    "amount": 5250000.00,
    "currency": "SAR",
    "notes": "Period 2 teaching staff costs (AEFE + Local)"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440301",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_category": "facility",
    "cost_subcategory": "Facility Costs (Rental, Maintenance, Utilities)",
    "account_code": "61550",
    "cost_center_id": "cost-center-operations-uuid",
    "amount": 156500.00,
    "currency": "SAR",
    "notes": "Period 2 facility costs from Module 9"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440302",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_category": "operating",
    "cost_subcategory": "Teaching Supplies and Materials",
    "account_code": "60220",
    "cost_center_id": "cost-center-academic-uuid",
    "amount": 142500.00,
    "currency": "SAR",
    "notes": "Period 2 teaching supplies: 1,900 students × 75 SAR per student"
  }
]
```

### Sample Driver-Based Costs (2025-2026, Period 2)

```json
[
  {
    "id": "990e8400-e29b-41d4-a716-446655440400",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_item_name": "Teaching Supplies",
    "cost_driver": "per_student",
    "driver_quantity": 1900,
    "cost_per_unit": 75.00,
    "total_cost": 142500.00,
    "account_code": "60220",
    "cost_center_id": "cost-center-academic-uuid",
    "currency": "SAR",
    "notes": "Books, materials, supplies per student per period"
  },
  {
    "id": "990e8400-e29b-41d4-a716-446655440401",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_item_name": "Professional Development (Teachers)",
    "cost_driver": "per_fte",
    "driver_quantity": 85,
    "cost_per_unit": 1500.00,
    "total_cost": 127500.00,
    "account_code": "62470",
    "cost_center_id": "cost-center-academic-uuid",
    "currency": "SAR",
    "notes": "Training budget: 85 FTE × 1,500 SAR per FTE per period"
  },
  {
    "id": "990e8400-e29b-41d4-a716-446655440402",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_item_name": "Technology Support Services",
    "cost_driver": "fixed",
    "driver_quantity": 1,
    "cost_per_unit": 80000.00,
    "total_cost": 80000.00,
    "account_code": "61150",
    "cost_center_id": "cost-center-it-uuid",
    "currency": "SAR",
    "notes": "IT support and maintenance contract (Period 2)"
  }
]
```

### Operational Cost Structure (EFIR Actual 2024-2025)

| Cost Category | Annual Budget (SAR) | % of Total | Key Drivers |
|---------------|---------------------|------------|-------------|
| **Personnel** | 15,750,000 | 65.8% | 85 FTE staff |
| - Teaching Staff | 12,600,000 | 52.6% | 73 teaching FTE |
| - Administrative | 2,100,000 | 8.8% | 8 admin FTE |
| - Support Staff | 1,050,000 | 4.4% | 4 support FTE |
| **Facility** | 1,200,000 | 5.0% | 12,500 sqm, rentals |
| - Rental (Gymnasium) | 150,000 | 0.6% | Fixed monthly |
| - Maintenance | 440,000 | 1.8% | Per classroom |
| - Utilities | 610,000 | 2.5% | Per sqm |
| **Operating** | 6,980,000 | 29.2% | Various drivers |
| - Teaching Supplies | 285,000 | 1.2% | Per student (150 SAR) |
| - Professional Development | 255,000 | 1.1% | Per FTE (3,000 SAR) |
| - Technology | 1,200,000 | 5.0% | Fixed + per student |
| - Insurance | 450,000 | 1.9% | Fixed |
| - Professional Services | 890,000 | 3.7% | Legal, audit, consulting |
| - Marketing | 380,000 | 1.6% | Fixed |
| - Administrative Supplies | 190,000 | 0.8% | Fixed |
| - Other | 3,330,000 | 13.9% | Various |
| **Total Operating Costs** | **23,930,000** | **100.0%** | - |

## Business Rules

### Cost Integration Rules

1. **Personnel Costs**: Automatically imported from Module 8 (DHG Workforce Planning)
   - No manual override - costs calculated from FTE and salary parameters
   - AEFE costs in EUR converted to SAR using configured exchange rate
   - Local staff costs calculated directly in SAR
2. **Facility Costs**: Automatically imported from Module 9 (Facility Planning)
   - Rental, maintenance, utilities costs pulled from Module 9
   - No duplication - facility costs entered once in Module 9
3. **Operating Costs**: Manually entered or driver-based calculation
   - Driver-based costs recalculate when drivers change (enrollment, FTE, etc.)
   - Fixed costs remain constant across periods

### Driver-Based Cost Rules

1. **Per-Student Drivers**:
   - Teaching supplies: 75 SAR per student per period (150 SAR annual)
   - Technology devices: Amortized over 3 years
   - Cafeteria subsidies: Per participating student
2. **Per-FTE Drivers**:
   - Professional development: 1,500 SAR per FTE per period (3,000 SAR annual)
   - Benefits: Percentage of base salary
   - Uniforms/equipment: One-time or annual per FTE
3. **Per-Sqm Drivers**:
   - Utilities (AC, electricity): 3.20 SAR per sqm per month (higher in Sep-Dec)
   - Cleaning: 2.00 SAR per sqm per month
   - Maintenance: 0.50 SAR per sqm per month
4. **Fixed Drivers**:
   - Insurance: Fixed annual premium
   - Professional services: Fixed contracts (audit, legal)
   - Technology licenses: Fixed annual subscriptions

### Cost Allocation Rules

1. **Period Allocation**: Costs split between periods based on activity patterns
   - Teaching costs: Period 1 (55%), Period 2 (45%) - aligned with school days
   - Facility costs: Period 1 (40%), Period 2 (50%), Summer (10%)
   - Fixed costs: Allocated evenly across 12 months
2. **Cost Center Assignment**:
   - Academic: Teaching staff, supplies, professional development
   - Operations: Facility, maintenance, utilities, security
   - IT: Technology, licenses, support services
   - Administration: Admin staff, professional services, insurance

### Validation Rules

1. **Positive Costs**: All cost amounts must be >= 0
2. **Driver Consistency**: If cost_driver specified, total_cost = driver_quantity × cost_per_unit
3. **Account Code Validity**: Expense accounts must be 60xxx-68xxx series
4. **No Duplication**: Personnel and facility costs must not be re-entered in operating expenses
5. **Cost Center Validity**: Cost center must exist in system configuration

## Calculation Examples

### Example 1: Teaching Supplies (Per-Student Driver)

**Context**: Calculate teaching supplies cost for Period 2.

**Given Data**:
- Total enrollment: 1,900 students
- Cost per student: 75 SAR per period (150 SAR annual)
- Period 2: Sep-Dec

**Calculation:**
```
Teaching supplies cost = 1,900 students × 75 SAR/student = 142,500 SAR

Cost driver: "per_student"
Driver quantity: 1,900
Cost per unit: 75 SAR
Total cost: 142,500 SAR
Account code: 60220 (Fournitures scolaires)
```

**Result**: 142,500 SAR for Period 2 teaching supplies

### Example 2: Professional Development (Per-FTE Driver)

**Context**: Calculate professional development budget for all staff.

**Given Data**:
- Total FTE: 85 (teaching + admin + support)
- Budget per FTE: 1,500 SAR per period (3,000 SAR annual)
- Period 2: Sep-Dec

**Calculation:**
```
Professional development cost = 85 FTE × 1,500 SAR/FTE = 127,500 SAR

Cost driver: "per_fte"
Driver quantity: 85
Cost per unit: 1,500 SAR
Total cost: 127,500 SAR
Account code: 62470 (Formation professionnelle)
```

**Result**: 127,500 SAR for Period 2 professional development

### Example 3: Technology Support (Fixed Cost)

**Context**: Calculate IT support contract cost for Period 2.

**Given Data**:
- IT support contract: 240,000 SAR annual
- Period 2: Sep-Dec = 4 months

**Calculation:**
```
Period 2 allocation = 240,000 SAR × (4 months ÷ 12 months) = 80,000 SAR

Cost driver: "fixed"
Driver quantity: 1
Cost per unit: 80,000 SAR
Total cost: 80,000 SAR
Account code: 61150 (Entretien et réparations sur biens mobiliers - IT)
```

**Result**: 80,000 SAR for Period 2 technology support

### Example 4: Total Operating Costs (Period 2)

**Context**: Calculate total operating costs for Period 2.

**Given Data**:
- Personnel costs (from Module 8): 5,250,000 SAR
- Facility costs (from Module 9): 156,500 SAR
- Operating expenses:
  - Teaching supplies: 142,500 SAR
  - Professional development: 127,500 SAR
  - Technology: 80,000 SAR
  - Insurance: 75,000 SAR (allocated 4/12 months)
  - Professional services: 148,333 SAR (audit, legal)
  - Marketing: 63,333 SAR
  - Administrative supplies: 31,667 SAR
  - Other: 555,000 SAR

**Calculation:**
```
Operating expenses total:
142,500 + 127,500 + 80,000 + 75,000 + 148,333 + 63,333 + 31,667 + 555,000
= 1,223,333 SAR

Total Period 2 costs:
Personnel: 5,250,000 SAR (65.8%)
Facility: 156,500 SAR (2.0%)
Operating: 1,223,333 SAR (15.3%)
---
Total: 6,629,833 SAR (Period 2 only)

Annual total (estimated):
Period 1: 9,250,000 SAR (55% of annual for teaching, 40% for facility)
Period 2: 6,629,833 SAR (45% of annual for teaching, 50% for facility)
Summer: Minimal (10% of facility costs only)
---
Annual estimated: ~23,930,000 SAR
```

**Result**: 6,629,833 SAR total operating costs for Period 2

### Example 5: Cost per Student Analysis

**Context**: Calculate cost per student to monitor efficiency.

**Given Data**:
- Total annual operating costs: 23,930,000 SAR
- Total enrollment: 1,900 students

**Calculation:**
```
Cost per student = 23,930,000 SAR ÷ 1,900 students = 12,595 SAR per student

Breakdown by category:
- Personnel: 15,750,000 ÷ 1,900 = 8,289 SAR per student (65.8%)
- Facility: 1,200,000 ÷ 1,900 = 632 SAR per student (5.0%)
- Operating: 6,980,000 ÷ 1,900 = 3,674 SAR per student (29.2%)

Benchmark comparison:
- EFIR cost per student: 12,595 SAR
- AEFE benchmark (similar schools): 12,000-14,000 SAR
- EFIR is within normal range ✓
```

**Result**: 12,595 SAR cost per student (within AEFE benchmark range)

## Integration Points

### Upstream Dependencies

1. **Module 8 (DHG Workforce Planning)**: Personnel costs (salaries, benefits, allowances)
2. **Module 9 (Facility Planning)**: Facility costs (rental, maintenance, utilities)
3. **Module 7 (Enrollment Planning)**: Student count for per-student driver-based costs
4. **Module 1 (System Configuration)**: Chart of accounts, cost centers, currency exchange rates

### Downstream Consumers

1. **Module 13 (Budget Consolidation)**: All costs consolidated into overall budget
2. **Module 14 (Financial Statements)**: Costs recognized in income statement by account code
3. **Module 17 (Budget vs Actual)**: Cost actuals compared to projections

### Data Flow

```
Module 8 (Workforce) → Personnel Costs
Module 9 (Facility) → Facility Costs
Module 7 (Enrollment) → Driver Quantities
        ↓                    ↓
        └────────┬───────────┘
                 ↓
      Cost Planning (Module 11)
      ┌──────────┼──────────┐
      ↓          ↓          ↓
  Personnel  Facility  Operating
      ↓          ↓          ↓
      └──────────┴──────────┘
               ↓
  Budget Consolidation (Module 13)
               ↓
  Financial Statements (Module 14)
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions/:id/cost-projections
POST   /api/v1/budget-versions/:id/cost-projections
GET    /api/v1/budget-versions/:id/driver-based-costs
POST   /api/v1/calculate-driver-based-costs
       Request: { drivers: { enrollment, fte, area }, cost_parameters }
       Response: { calculated_costs, total_by_category }
GET    /api/v1/budget-versions/:id/cost-summary
       Response: { personnel, facility, operating, total, cost_per_student }
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Driver-Based Cost Calculation
```typescript
const supplies = {
  cost_driver: "per_student",
  driver_quantity: 1900,
  cost_per_unit: 75
};

const totalCost = calculateDriverCost(supplies);
expect(totalCost).toBe(142500); // 1,900 × 75
```

#### Scenario 2: Personnel Cost Integration
```typescript
const personnelCosts = await getPersonnelCosts(budgetVersionId, periodId);
const costProjection = await integratePersonnelCosts(personnelCosts);

expect(costProjection.cost_category).toBe("personnel");
expect(costProjection.amount).toBe(personnelCosts.total);
```

#### Scenario 3: Cost per Student
```typescript
const totalCosts = 23930000;
const enrollment = 1900;

const costPerStudent = totalCosts / enrollment;
expect(costPerStudent).toBeCloseTo(12595, 0);
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: cost_projections, driver_based_costs, personnel_cost_summary tables |

## Future Enhancements (Phase 5-6)

1. **Cost Optimization Engine**: Recommend cost reduction opportunities while maintaining quality
2. **Variance Analysis**: Automated analysis of budget vs actual with explanations
3. **Scenario Modeling**: Compare costs under different enrollment/staffing scenarios
4. **Benchmarking**: Compare EFIR costs to other AEFE schools (cost per student, ratios)
5. **Predictive Analytics**: Forecast cost trends based on historical data
6. **Cost Allocation Refinement**: More granular cost center allocations for departmental budgeting
7. **Real-time Cost Tracking**: Integration with accounting system for live cost monitoring
8. **Cost Dashboards**: Visual analytics of cost trends, concentration by category
9. **Budget Alerts**: Notify when costs exceed thresholds or projected budget
10. **Driver Sensitivity Analysis**: Model impact of driver changes (enrollment ±10%, FTE ±5%, etc.)

## Notes

- **Phase 4 Scope**: Database foundation only - cost projection and consolidation
- **Business Logic**: Cost optimization and variance analysis deferred to Phase 5-6
- **Integration Critical**: Personnel and facility costs must integrate seamlessly (no duplication)
- **Driver-Based Emphasis**: ~40% of operating costs driver-based for dynamic budgeting
- **Cost per Student**: Key efficiency metric monitored against AEFE benchmarks (12,000-14,000 SAR)
- **PCG Compliance**: All costs mapped to French Chart of Accounts for consolidated reporting
- **Data Source**: Cost structures and parameters based on EFIR actual data (2024-2025)
