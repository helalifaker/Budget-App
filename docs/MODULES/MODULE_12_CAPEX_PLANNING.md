# Module 12: CapEx Planning

## Overview

Module 12 manages capital expenditure (CapEx) planning for long-term investments in facilities, equipment, technology infrastructure, and other fixed assets. Unlike operating expenses (Module 11), capital expenditures are capitalized on the balance sheet and depreciated over their useful lives. This module supports multi-year CapEx planning, tracks depreciation schedules, manages project approvals, and ensures investments align with strategic priorities and capacity needs.

**Layer**: Planning Layer (Phase 2)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: CapEx approval workflow, ROI analysis, multi-year investment roadmap, API endpoints (Phase 5-6)

### Purpose

- Plan capital investments in facilities, equipment, and technology
- Track CapEx projects by category, priority, and approval status
- Calculate depreciation schedules for capitalized assets
- Support multi-year CapEx planning (aligned with 5-year strategic plan)
- Ensure CapEx investments address capacity constraints and strategic priorities
- Map CapEx to PCG fixed asset accounts (2xxx series)
- Monitor CapEx spending against approved budget
- Integrate with facility planning (Module 9) for capacity expansion needs

### Key Design Decisions

1. **Project-Based Tracking**: Each CapEx investment tracked as a discrete project
2. **Approval Workflow**: CapEx projects require approval before execution (Working → Approved)
3. **Multi-Year Planning**: Support 1-year and 5-year CapEx roadmaps
4. **Depreciation Calculation**: Automatic depreciation schedule based on useful life and method
5. **Priority-Based Allocation**: CapEx prioritized (Critical, High, Medium, Low) for budget constraint scenarios
6. **Integration with Strategic Plan**: CapEx aligned with Module 18 (5-Year Strategic Plan)
7. **PCG Asset Account Mapping**: Fixed assets categorized by account codes (21xxx, 22xxx, 23xxx)

## Database Schema

### Tables

#### 1. capex_projects

Capital expenditure project planning and tracking.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
project_name          VARCHAR(200) NOT NULL
project_description   TEXT NULL
capex_category        capexcategory NOT NULL         -- ENUM: building, equipment, technology, vehicles, other
priority              capexpriority NOT NULL         -- ENUM: critical, high, medium, low
estimated_cost        NUMERIC(12, 2) NOT NULL
approved_budget       NUMERIC(12, 2) NULL
actual_cost           NUMERIC(12, 2) NULL DEFAULT 0
planned_start_date    DATE NOT NULL
planned_completion    DATE NULL
actual_completion     DATE NULL
project_status        projectstatus NOT NULL         -- ENUM: planned, approved, in_progress, completed, cancelled
useful_life_years     INTEGER NOT NULL               -- Asset useful life for depreciation
depreciation_method   depreciationmethod NOT NULL    -- ENUM: straight_line, declining_balance
asset_account_code    VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
justification         TEXT NULL
strategic_alignment   TEXT NULL                      -- Link to strategic plan objectives
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- estimated_cost > 0
- approved_budget >= 0 (if not null)
- actual_cost >= 0
- useful_life_years > 0
- planned_start_date < planned_completion (if not null)
- If project_status = 'completed', actual_completion IS NOT NULL
- asset_account_code must start with '21', '22', '23', or '24' (fixed asset accounts)

**RLS Policies:**
- Admin: Full access to CapEx planning
- Manager: Read/write for working budget versions, read-only for approved
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (budget_version_id, capex_category, priority)
- Index on project_status for filtering active projects
- Index on asset_account_code for financial consolidation

#### 2. depreciation_schedules

Calculated depreciation schedules for capitalized assets.

**Columns:**
```sql
id                    UUID PRIMARY KEY
capex_project_id      UUID NOT NULL FOREIGN KEY -> capex_projects.id (CASCADE)
fiscal_year           INTEGER NOT NULL              -- Year for depreciation entry
year_number           INTEGER NOT NULL              -- 1, 2, 3... within asset life
opening_book_value    NUMERIC(12, 2) NOT NULL
depreciation_expense  NUMERIC(12, 2) NOT NULL
closing_book_value    NUMERIC(12, 2) NOT NULL
expense_account_code  VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
accumulated_deprec    NUMERIC(12, 2) NOT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- depreciation_expense >= 0
- closing_book_value = opening_book_value - depreciation_expense
- accumulated_deprec >= 0
- year_number >= 1
- UNIQUE (capex_project_id, fiscal_year)

**RLS Policies:**
- All authenticated users can read depreciation schedules
- Only system can write (auto-calculated)

**Indexes:**
- Primary key on id
- Index on (capex_project_id, fiscal_year)
- Index on fiscal_year for annual depreciation summaries

#### 3. capex_budget_summary

Annual CapEx budget summary by category.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
fiscal_year           INTEGER NOT NULL
capex_category        capexcategory NOT NULL
total_planned         NUMERIC(12, 2) NOT NULL
total_approved        NUMERIC(12, 2) NOT NULL
total_actual          NUMERIC(12, 2) NOT NULL DEFAULT 0
project_count         INTEGER NOT NULL
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- total_planned >= 0
- total_approved >= 0
- total_actual >= 0
- project_count >= 0
- UNIQUE (budget_version_id, fiscal_year, capex_category)

**RLS Policies:**
- Same as capex_projects

**Indexes:**
- Primary key on id
- Index on (budget_version_id, fiscal_year)

### Enums

#### CapExCategory
```sql
CREATE TYPE efir_budget.capexcategory AS ENUM (
    'building',         -- Building construction, renovations, improvements
    'equipment',        -- Furniture, lab equipment, classroom equipment
    'technology',       -- Computers, servers, network infrastructure, software
    'vehicles',         -- School buses, administrative vehicles
    'other'             -- Other long-term investments
);
```

#### CapExPriority
```sql
CREATE TYPE efir_budget.capexpriority AS ENUM (
    'critical',         -- Must-have for safety/compliance/operations
    'high',             -- Important for strategic objectives
    'medium',           -- Beneficial but not urgent
    'low'               -- Nice-to-have, deferrable
);
```

#### ProjectStatus
```sql
CREATE TYPE efir_budget.projectstatus AS ENUM (
    'planned',          -- Planned but not yet approved
    'approved',         -- Approved and funded
    'in_progress',      -- Execution underway
    'completed',        -- Project completed
    'cancelled'         -- Project cancelled
);
```

#### DepreciationMethod
```sql
CREATE TYPE efir_budget.depreciationmethod AS ENUM (
    'straight_line',    -- Straight-line depreciation (most common)
    'declining_balance' -- Declining balance (accelerated depreciation)
);
```

## Data Model

### Sample CapEx Projects (2025-2026)

```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440500",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "project_name": "Science Lab Expansion (4th Lab)",
    "project_description": "Add 4th science lab to address overcapacity (121% utilization in Module 9)",
    "capex_category": "building",
    "priority": "critical",
    "estimated_cost": 850000.00,
    "approved_budget": 850000.00,
    "actual_cost": 0,
    "planned_start_date": "2025-06-01",
    "planned_completion": "2025-08-31",
    "actual_completion": null,
    "project_status": "approved",
    "useful_life_years": 20,
    "depreciation_method": "straight_line",
    "asset_account_code": "21310",
    "justification": "Current 3 labs insufficient for Collège+Lycée (925 students). Need 4 labs per Module 9 analysis.",
    "strategic_alignment": "Capacity expansion to accommodate enrollment growth to 1,900 students"
  },
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440501",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "project_name": "Technology Infrastructure Upgrade",
    "project_description": "Replace 120 student computers (5+ years old), upgrade network switches, expand WiFi coverage",
    "capex_category": "technology",
    "priority": "high",
    "estimated_cost": 480000.00,
    "approved_budget": 480000.00,
    "actual_cost": 0,
    "planned_start_date": "2025-07-01",
    "planned_completion": "2025-08-15",
    "actual_completion": null,
    "project_status": "approved",
    "useful_life_years": 5,
    "depreciation_method": "straight_line",
    "asset_account_code": "22180",
    "justification": "Existing computers beyond useful life (5 years). Network capacity insufficient for 1,900 students.",
    "strategic_alignment": "Digital transformation initiative to support blended learning"
  },
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440502",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "project_name": "Classroom Furniture Replacement (15 classrooms)",
    "project_description": "Replace furniture in 15 oldest classrooms (Maternelle and Élémentaire)",
    "capex_category": "equipment",
    "priority": "medium",
    "estimated_cost": 225000.00,
    "approved_budget": null,
    "actual_cost": 0,
    "planned_start_date": "2026-01-01",
    "planned_completion": "2026-03-31",
    "actual_completion": null,
    "project_status": "planned",
    "useful_life_years": 10,
    "depreciation_method": "straight_line",
    "asset_account_code": "21840",
    "justification": "Furniture 10+ years old, showing wear. Not critical but impacts learning environment.",
    "strategic_alignment": "Maintain high-quality learning environment"
  }
]
```

### CapEx Budget Summary (2025-2026)

| Category | Projects | Total Planned (SAR) | Total Approved (SAR) | Total Actual (SAR) | Status |
|----------|----------|---------------------|----------------------|--------------------|--------|
| Building | 2 | 950,000 | 850,000 | 0 | 1 approved, 1 planned |
| Equipment | 3 | 450,000 | 150,000 | 0 | 1 approved, 2 planned |
| Technology | 2 | 680,000 | 480,000 | 0 | 1 approved, 1 planned |
| Vehicles | 1 | 320,000 | 0 | 0 | 1 planned |
| Other | 0 | 0 | 0 | 0 | - |
| **Total** | **8** | **2,400,000** | **1,480,000** | **0** | **38% funding gap** |

### Historical CapEx Spending (EFIR Actual Data)

| Fiscal Year | Building (SAR) | Equipment (SAR) | Technology (SAR) | Vehicles (SAR) | Total CapEx (SAR) | % of Revenue |
|-------------|----------------|-----------------|------------------|----------------|-------------------|--------------|
| 2021 | 450,000 | 120,000 | 180,000 | 0 | 750,000 | 3.3% |
| 2022 | 680,000 | 180,000 | 250,000 | 0 | 1,110,000 | 4.7% |
| 2023 | 520,000 | 210,000 | 320,000 | 0 | 1,050,000 | 4.2% |
| 2024 | 850,000 | 280,000 | 420,000 | 0 | 1,550,000 | 5.5% |
| 2025 (proj) | 950,000 | 450,000 | 680,000 | 320,000 | 2,400,000 | 8.0% |

**5-Year Total**: 6,860,000 SAR CapEx investment (2021-2025)

## Business Rules

### CapEx Project Rules

1. **Capitalization Threshold**: Minimum 10,000 SAR to capitalize (below = operating expense)
2. **Approval Required**: All CapEx projects require explicit approval before execution
3. **Priority-Based Allocation**: If budget constrained, fund Critical first, then High, then Medium, then Low
4. **Multi-Year Projects**: Large projects can span multiple fiscal years (tracked by fiscal_year in depreciation)
5. **Strategic Alignment**: All CapEx projects must align with strategic objectives (documented in strategic_alignment field)

### Asset Classification Rules

1. **Building (PCG 213xx)**:
   - Constructions: 21310
   - Renovations: 21320
   - Useful life: 20-40 years
2. **Equipment (PCG 218xx, 219xx)**:
   - Furniture: 21840
   - Lab equipment: 21850
   - Useful life: 5-15 years
3. **Technology (PCG 221xx)**:
   - Computers: 22180
   - Network infrastructure: 22190
   - Software licenses: 22050
   - Useful life: 3-7 years
4. **Vehicles (PCG 224xx)**:
   - Buses: 22410
   - Administrative vehicles: 22420
   - Useful life: 7-10 years

### Depreciation Rules

1. **Straight-Line Method** (most common):
   - Annual depreciation = Asset cost ÷ Useful life years
   - Same amount each year until fully depreciated
2. **Declining Balance Method** (accelerated):
   - Higher depreciation in early years
   - Declining amount each year
   - Rarely used for EFIR (straight-line preferred)
3. **Depreciation Start**: Begin in fiscal year of asset acquisition
4. **Expense Account**: Depreciation expense → PCG 681xx (Dotations aux amortissements)

### Validation Rules

1. **Positive Costs**: All cost amounts must be > 0 (CapEx threshold: 10,000 SAR minimum)
2. **Useful Life**: Useful life must be > 0 and ≤ 50 years (maximum asset life)
3. **Date Logic**: planned_start_date < planned_completion (if specified)
4. **Completion Date**: If project_status = 'completed', actual_completion IS NOT NULL
5. **Account Code Validity**: Asset accounts must be 21xxx, 22xxx, 23xxx, or 24xxx
6. **Depreciation Sum**: Σ(depreciation_expense) over asset life = asset cost

## Calculation Examples

### Example 1: Science Lab Expansion Depreciation (Straight-Line)

**Context**: Calculate annual depreciation for 4th science lab.

**Given Data**:
- Asset cost: 850,000 SAR
- Useful life: 20 years
- Depreciation method: Straight-line
- Acquisition year: 2025

**Calculation:**
```
Annual depreciation = 850,000 SAR ÷ 20 years = 42,500 SAR per year

Depreciation schedule:
Year 1 (2025): Opening 850,000 | Depreciation 42,500 | Closing 807,500
Year 2 (2026): Opening 807,500 | Depreciation 42,500 | Closing 765,000
Year 3 (2027): Opening 765,000 | Depreciation 42,500 | Closing 722,500
...
Year 20 (2044): Opening 42,500 | Depreciation 42,500 | Closing 0

Total depreciation over 20 years: 42,500 × 20 = 850,000 SAR ✓
```

**Result**: 42,500 SAR annual depreciation expense for 20 years

### Example 2: Technology Infrastructure Depreciation

**Context**: Calculate depreciation for computer and network upgrade.

**Given Data**:
- Asset cost: 480,000 SAR
- Useful life: 5 years
- Depreciation method: Straight-line
- Acquisition year: 2025

**Calculation:**
```
Annual depreciation = 480,000 SAR ÷ 5 years = 96,000 SAR per year

Depreciation schedule:
Year 1 (2025): Opening 480,000 | Depreciation 96,000 | Closing 384,000
Year 2 (2026): Opening 384,000 | Depreciation 96,000 | Closing 288,000
Year 3 (2027): Opening 288,000 | Depreciation 96,000 | Closing 192,000
Year 4 (2028): Opening 192,000 | Depreciation 96,000 | Closing 96,000
Year 5 (2029): Opening 96,000 | Depreciation 96,000 | Closing 0

Total depreciation over 5 years: 96,000 × 5 = 480,000 SAR ✓
```

**Result**: 96,000 SAR annual depreciation expense for 5 years

### Example 3: Total Annual Depreciation Expense (2026)

**Context**: Calculate total depreciation expense for fiscal year 2026 considering all capitalized assets.

**Given Data** (Active assets in 2026):
- Science lab (2025, year 2 of 20): 42,500 SAR
- Technology upgrade (2025, year 2 of 5): 96,000 SAR
- Existing building (2015, year 12 of 30): 280,000 SAR (8.4M original cost ÷ 30)
- Existing equipment (2020-2024, various): 180,000 SAR
- Existing technology (2022-2024, various): 220,000 SAR

**Calculation:**
```
Total 2026 depreciation expense:
Science lab: 42,500 SAR
Technology 2025: 96,000 SAR
Building: 280,000 SAR
Equipment: 180,000 SAR
Technology (old): 220,000 SAR
---
Total: 818,500 SAR

Account code: 68110 (Dotations aux amortissements sur immobilisations)
Impact on income statement: 818,500 SAR non-cash expense
```

**Result**: 818,500 SAR total depreciation expense for 2026

### Example 4: CapEx Budget Allocation (Priority-Based)

**Context**: Allocate 1,500,000 SAR CapEx budget across planned projects using priority.

**Given Data** (All planned projects):
- Critical: Science lab (850,000 SAR)
- High: Technology upgrade (480,000 SAR)
- High: Lab equipment (150,000 SAR)
- Medium: Furniture replacement (225,000 SAR)
- Medium: Library expansion (100,000 SAR)
- Low: Buses (320,000 SAR)
- Low: Parking expansion (75,000 SAR)
- Total requested: 2,200,000 SAR

**Calculation:**
```
Available budget: 1,500,000 SAR

Priority allocation:
1. Critical: Science lab 850,000 SAR ✓ (Remaining: 650,000 SAR)
2. High: Technology upgrade 480,000 SAR ✓ (Remaining: 170,000 SAR)
3. High: Lab equipment 150,000 SAR ✓ (Remaining: 20,000 SAR)
4. Medium: Furniture 225,000 SAR ✗ (Insufficient funds)
5. Medium: Library 100,000 SAR ✗ (Not funded)
6. Low: Buses 320,000 SAR ✗ (Not funded)
7. Low: Parking 75,000 SAR ✗ (Not funded)

Approved projects: 3 (Science lab, Technology, Lab equipment)
Approved budget: 1,480,000 SAR
Remaining: 20,000 SAR (insufficient for next project)
Deferred projects: 4 (Furniture, Library, Buses, Parking)
```

**Result**: Approved 3 projects (1,480,000 SAR), deferred 4 projects (720,000 SAR)

### Example 5: CapEx as % of Revenue

**Context**: Calculate CapEx spending as percentage of revenue to assess investment intensity.

**Given Data**:
- Total revenue (2025-2026): 30,020,000 SAR (from Module 10)
- Total CapEx approved: 1,480,000 SAR

**Calculation:**
```
CapEx as % of revenue = (1,480,000 ÷ 30,020,000) × 100 = 4.93%

Benchmark comparison:
- EFIR 2025-2026: 4.93%
- EFIR historical average: 4.4% (2021-2024)
- AEFE schools benchmark: 4-6% of revenue
- Assessment: Within normal range ✓

CapEx intensity trend:
2021: 3.3%
2022: 4.7%
2023: 4.2%
2024: 5.5%
2025: 4.93% (projected, limited by budget constraints)
```

**Result**: CapEx = 4.93% of revenue (within AEFE benchmark 4-6%)

## Integration Points

### Upstream Dependencies

1. **Module 9 (Facility Planning)**: Facility expansion needs drive building CapEx
2. **Module 7 (Enrollment Planning)**: Enrollment growth informs capacity investment needs
3. **Module 1 (System Configuration)**: Chart of accounts for asset classification, cost centers

### Downstream Consumers

1. **Module 13 (Budget Consolidation)**: CapEx cash outflows included in cash flow statement
2. **Module 14 (Financial Statements)**: Depreciation expense in income statement, fixed assets on balance sheet
3. **Module 18 (5-Year Strategic Plan)**: Multi-year CapEx roadmap aligned with strategic objectives

### Data Flow

```
Facility Planning (Module 9) → Capacity Gaps
Enrollment Planning (Module 7) → Growth Projections
Strategic Plan (Module 18) → Strategic Priorities
        ↓                          ↓
        └──────────┬───────────────┘
                   ↓
        CapEx Planning (Module 12)
        ┌──────────┼──────────┐
        ↓          ↓          ↓
    Projects  Approval  Depreciation
        ↓          ↓          ↓
        └──────────┴──────────┘
                   ↓
    Budget Consolidation (Module 13)
                   ↓
    Financial Statements (Module 14)
    - Income Statement (depreciation expense)
    - Balance Sheet (fixed assets)
    - Cash Flow (CapEx cash outflows)
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions/:id/capex-projects
POST   /api/v1/budget-versions/:id/capex-projects
PUT    /api/v1/capex-projects/:id/approve
GET    /api/v1/capex-projects/:id/depreciation-schedule
POST   /api/v1/calculate-depreciation
       Request: { asset_cost, useful_life, method }
       Response: { annual_depreciation, schedule }
GET    /api/v1/budget-versions/:id/capex-summary
       Response: { by_category, by_priority, total_planned, total_approved }
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Straight-Line Depreciation
```typescript
const asset = { cost: 850000, usefulLife: 20 };
const schedule = calculateDepreciation(asset, "straight_line");

expect(schedule.annualDepreciation).toBe(42500);
expect(schedule.totalYears).toBe(20);
expect(schedule.schedule[0].closingValue).toBe(807500);
expect(schedule.schedule[19].closingValue).toBe(0);
```

#### Scenario 2: Priority-Based Allocation
```typescript
const budget = 1500000;
const projects = [
  { priority: "critical", cost: 850000 },
  { priority: "high", cost: 480000 },
  { priority: "high", cost: 150000 },
  { priority: "medium", cost: 225000 }
];

const allocated = allocateCapExBudget(projects, budget);
expect(allocated.approved.length).toBe(3);
expect(allocated.totalApproved).toBe(1480000);
expect(allocated.deferred.length).toBe(1);
```

#### Scenario 3: CapEx as % of Revenue
```typescript
const capex = 1480000;
const revenue = 30020000;

const percentage = (capex / revenue) * 100;
expect(percentage).toBeCloseTo(4.93, 2);
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: capex_projects, depreciation_schedules, capex_budget_summary tables |

## Future Enhancements (Phase 5-6)

1. **CapEx Approval Workflow**: Multi-level approval process with notifications and audit trail
2. **ROI Analysis**: Calculate return on investment for CapEx projects (especially revenue-generating assets)
3. **Multi-Year CapEx Roadmap**: Visual timeline showing planned investments over 5 years
4. **Asset Lifecycle Management**: Track assets from acquisition through depreciation to disposal
5. **CapEx Optimization**: Recommend optimal timing and prioritization for CapEx investments
6. **Budget Variance Tracking**: Monitor actual vs budgeted CapEx spending by project
7. **Integration with Procurement**: Link CapEx projects to purchase orders and vendor contracts
8. **Scenario Modeling**: Model impact of different CapEx scenarios on financial statements
9. **Dashboards**: Visual analytics of CapEx spending trends, depreciation schedules
10. **Asset Registry**: Comprehensive fixed asset register with maintenance history

## Notes

- **Phase 4 Scope**: Database foundation only - CapEx project tracking and depreciation calculation
- **Business Logic**: Approval workflow and ROI analysis deferred to Phase 5-6
- **Depreciation Method**: Straight-line preferred for EFIR (simpler, consistent expense recognition)
- **Capitalization Threshold**: 10,000 SAR minimum (below = operating expense in Module 11)
- **CapEx Intensity**: EFIR historically invests 4-6% of revenue in CapEx, aligned with AEFE benchmarks
- **Critical Investment**: 4th science lab (850,000 SAR) addresses overcapacity identified in Module 9
- **Data Source**: CapEx projects and historical spending based on EFIR actual data (2021-2025)
