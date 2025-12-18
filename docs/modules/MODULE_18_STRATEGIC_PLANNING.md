# Module 18: 5-Year Strategic Planning

## Overview

Module 18 provides the foundation for multi-year strategic planning in the EFIR Budget Planning Application. This module enables the creation of 5-year strategic plans with multiple scenarios, allowing the school to model different growth trajectories and evaluate long-term financial sustainability.

**Layer**: Strategic Layer (Phase 5)
**Status**: Database Foundation Implemented (Phase 5 - Day 3)
**Future Phases**: Business logic (projection calculations, scenario comparison), API endpoints, UI components (Phase 5-6)

### Purpose

- Create and manage 5-year strategic plans (2025-2030, 2026-2031, etc.)
- Model multiple growth scenarios (conservative, base case, optimistic, new campus)
- Project multi-year financials (revenue, costs, CapEx) based on growth assumptions
- Track strategic initiatives and major capital investments
- Support Board-level strategic decision-making and long-term planning

### Key Design Decisions

1. **5-Year Horizon**: Strategic plans span exactly 5 fiscal years (standard strategic planning cycle)
2. **Scenario Modeling**: Each plan contains 2-4 scenarios representing different growth trajectories
3. **Growth-Based Projections**: Financial projections calculated by applying annual growth rates to base year amounts
4. **Initiative Tracking**: Major projects tracked separately with CapEx and operating impact
5. **Plan Status Workflow**: Plans move through draft → approved → archived status

## Database Schema

### Tables

#### 1. strategic_plans (Parent Table)

5-year strategic plan headers with metadata and timeline.

**Columns:**
```sql
id              UUID PRIMARY KEY
name            VARCHAR(200) UNIQUE NOT NULL  -- e.g., 'EFIR Strategic Plan 2025-2030'
description     TEXT NULL                     -- Plan description and key objectives
base_year       INTEGER NOT NULL              -- Starting year (e.g., 2025 for 2025-2030)
status          VARCHAR(20) NOT NULL DEFAULT 'draft'  -- draft, approved, archived
created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id   UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id   UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at      TIMESTAMPTZ NULL              -- Soft delete support
```

**Constraints:**
- Unique constraint on `name` (plan names must be unique)
- Check constraint: `base_year >= 2000 AND base_year <= 2100`
- Soft delete support via `deleted_at`

**RLS Policies:**
- Admin: Full access to all strategic plans
- Manager: Full access (strategic planning is manager-level activity)
- Viewer: Read-only access to approved plans

**Indexes:**
- Primary key on `id`
- Unique index on `name`
- Index on `base_year` for year-based queries
- Index on `status` for filtering by status

**Example:**
```sql
INSERT INTO efir_budget.strategic_plans (
    id, name, description, base_year, status
) VALUES (
    gen_random_uuid(),
    'EFIR Strategic Plan 2025-2030',
    'Five-year strategic plan with enrollment growth to 1,500 students and new secondary campus in Year 4',
    2025,
    'approved'
);
```

#### 2. strategic_plan_scenarios (Child of strategic_plans)

Growth scenarios with underlying assumptions and parameters.

**Columns:**
```sql
id                          UUID PRIMARY KEY
strategic_plan_id           UUID NOT NULL FOREIGN KEY -> strategic_plans.id (CASCADE)
scenario_type               scenariotype NOT NULL     -- base_case, conservative, optimistic, new_campus
name                        VARCHAR(200) NOT NULL
description                 TEXT NULL
enrollment_growth_rate      NUMERIC(5, 4) NOT NULL    -- e.g., 0.0400 = 4.00% per year
fee_increase_rate           NUMERIC(5, 4) NOT NULL    -- e.g., 0.0300 = 3.00% per year
salary_inflation_rate       NUMERIC(5, 4) NOT NULL    -- e.g., 0.0350 = 3.50% per year
operating_inflation_rate    NUMERIC(5, 4) NOT NULL    -- e.g., 0.0250 = 2.50% per year
additional_assumptions      JSONB NULL                -- Exchange rates, capacity limits, etc.
created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id               UUID NULL
updated_by_id               UUID NULL
deleted_at                  TIMESTAMPTZ NULL
```

**Constraints:**
- Unique constraint on (`strategic_plan_id`, `scenario_type`) - one scenario of each type per plan
- Check constraints on growth rates:
  - `enrollment_growth_rate >= -0.50 AND enrollment_growth_rate <= 1.00` (-50% to +100%)
  - `fee_increase_rate >= -0.20 AND fee_increase_rate <= 0.50` (-20% to +50%)
  - `salary_inflation_rate >= -0.20 AND salary_inflation_rate <= 0.50`
  - `operating_inflation_rate >= -0.20 AND operating_inflation_rate <= 0.50`

**RLS Policies:**
- Admin: Full access to all scenarios
- Manager: Full access to scenarios (via parent plan access)
- Viewer: Read-only access to scenarios in approved plans

**Indexes:**
- Primary key on `id`
- Index on `strategic_plan_id` for parent lookups
- Index on `scenario_type` for filtering by type
- Composite index on (`strategic_plan_id`, `scenario_type`) for unique constraint

**Example:**
```sql
INSERT INTO efir_budget.strategic_plan_scenarios (
    id, strategic_plan_id, scenario_type, name,
    enrollment_growth_rate, fee_increase_rate,
    salary_inflation_rate, operating_inflation_rate
) VALUES (
    gen_random_uuid(),
    '<plan_id>',
    'base_case',
    'Base Case - Steady Growth',
    0.0400,  -- 4% enrollment growth
    0.0300,  -- 3% fee increase
    0.0350,  -- 3.5% salary inflation
    0.0250   -- 2.5% operating inflation
);
```

#### 3. strategic_plan_projections (Child of strategic_plan_scenarios)

Multi-year financial projections by category and year.

**Columns:**
```sql
id                          UUID PRIMARY KEY
strategic_plan_scenario_id  UUID NOT NULL FOREIGN KEY -> strategic_plan_scenarios.id (CASCADE)
year                        INTEGER NOT NULL          -- 1-5 (relative to base_year)
category                    projectioncategory NOT NULL  -- revenue, personnel_costs, etc.
amount_sar                  NUMERIC(15, 2) NOT NULL   -- Projected amount in SAR
calculation_inputs          JSONB NULL                -- Inputs used in calculation
created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id               UUID NULL
updated_by_id               UUID NULL
deleted_at                  TIMESTAMPTZ NULL
```

**Constraints:**
- Unique constraint on (`strategic_plan_scenario_id`, `year`, `category`) - one projection per year/category/scenario
- Check constraint: `year >= 1 AND year <= 5`
- Check constraint: `amount_sar >= 0` (no negative projections)

**RLS Policies:**
- Admin: Full access to all projections
- Manager: Full access to projections (via parent scenario → plan)
- Viewer: Read-only access to projections in approved plans

**Indexes:**
- Primary key on `id`
- Index on `strategic_plan_scenario_id` for scenario lookups
- Index on `year` for year-based queries
- Index on `category` for category filtering
- Composite index on (`strategic_plan_scenario_id`, `year`) for timeline queries

**Example:**
```sql
-- Year 1 (2025) Revenue Projection
INSERT INTO efir_budget.strategic_plan_projections (
    id, strategic_plan_scenario_id, year, category, amount_sar
) VALUES (
    gen_random_uuid(),
    '<scenario_id>',
    1,                      -- Year 1 of plan
    'revenue',              -- Revenue category
    55515000.00             -- 55.5M SAR (base year)
);

-- Year 2 (2026) Revenue Projection (with 4% enrollment + 3% fee increase)
INSERT INTO efir_budget.strategic_plan_projections (
    id, strategic_plan_scenario_id, year, category, amount_sar
) VALUES (
    gen_random_uuid(),
    '<scenario_id>',
    2,                      -- Year 2 of plan
    'revenue',
    59462000.00             -- 55.5M × 1.04 × 1.03 = 59.5M SAR
);
```

#### 4. strategic_initiatives (Child of strategic_plans)

Major projects and capital investments planned within the 5-year horizon.

**Columns:**
```sql
id                      UUID PRIMARY KEY
strategic_plan_id       UUID NOT NULL FOREIGN KEY -> strategic_plans.id (CASCADE)
name                    VARCHAR(200) NOT NULL
description             TEXT NULL
planned_year            INTEGER NOT NULL          -- 1-5 (when to execute)
capex_amount_sar        NUMERIC(15, 2) NOT NULL DEFAULT 0.00  -- One-time CapEx
operating_impact_sar    NUMERIC(15, 2) NOT NULL DEFAULT 0.00  -- Annual operating cost
status                  initiativestatus NOT NULL DEFAULT 'planned'
additional_details      JSONB NULL                -- Milestones, dependencies, risks
created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id           UUID NULL
updated_by_id           UUID NULL
deleted_at              TIMESTAMPTZ NULL
```

**Constraints:**
- Check constraint: `planned_year >= 1 AND planned_year <= 5`
- Check constraint: `capex_amount_sar >= 0`
- No unique constraints (multiple initiatives can be planned for same year)

**RLS Policies:**
- Admin: Full access to all initiatives
- Manager: Full access to initiatives (via parent plan)
- Viewer: Read-only access to initiatives in approved plans

**Indexes:**
- Primary key on `id`
- Index on `strategic_plan_id` for plan lookups
- Index on `name` for searching
- Index on `planned_year` for timeline views
- Index on `status` for filtering
- Composite index on (`strategic_plan_id`, `planned_year`) for plan timeline

**Example:**
```sql
INSERT INTO efir_budget.strategic_initiatives (
    id, strategic_plan_id, name, description,
    planned_year, capex_amount_sar, operating_impact_sar, status
) VALUES (
    gen_random_uuid(),
    '<plan_id>',
    'New Science Laboratory',
    'State-of-the-art science lab with equipment for physics, chemistry, biology',
    2,                      -- Year 2 (2026)
    2500000.00,             -- 2.5M SAR CapEx (construction + equipment)
    150000.00,              -- 150K SAR/year operating cost (maintenance, supplies)
    'approved'
);
```

### Enums

#### ScenarioType

Defines the types of growth scenarios for strategic planning.

```sql
CREATE TYPE efir_budget.scenariotype AS ENUM (
    'base_case',      -- Expected trajectory (3-5% enrollment growth)
    'conservative',   -- Slower growth (0-2% enrollment growth)
    'optimistic',     -- Expansion scenario (6-8% enrollment growth)
    'new_campus'      -- Major capital investment (new facility)
);
```

**Use Cases:**
- **base_case**: Primary planning scenario, most likely outcome
- **conservative**: Risk planning, economic downturn scenario
- **optimistic**: Growth planning, market expansion scenario
- **new_campus**: Facility expansion, capacity doubling scenario

#### InitiativeStatus

Tracks the lifecycle status of strategic initiatives.

```sql
CREATE TYPE efir_budget.initiativestatus AS ENUM (
    'planned',        -- Initiative planned but not yet approved
    'approved',       -- Approved for execution
    'in_progress',    -- Currently being executed
    'completed',      -- Successfully completed
    'cancelled'       -- Cancelled or deferred
);
```

**Status Workflow:**
```
planned → approved → in_progress → completed
                ↓
            cancelled
```

#### ProjectionCategory

Financial projection categories for multi-year planning.

```sql
CREATE TYPE efir_budget.projectioncategory AS ENUM (
    'revenue',              -- Total operating revenue
    'personnel_costs',      -- All personnel expenses
    'operating_costs',      -- Operating expenses (non-personnel)
    'capex',                -- Capital expenditures
    'depreciation'          -- Depreciation expense
);
```

**Category Definitions:**
- **revenue**: Total tuition + fees + ancillary (from Module 10)
- **personnel_costs**: Teaching + admin + support salaries (from Module 11)
- **operating_costs**: Facilities, utilities, supplies, etc. (from Module 11)
- **capex**: Equipment, IT, furniture, building (from Module 12)
- **depreciation**: Depreciation of capital assets (accounting)

## Business Rules

### Strategic Plan Rules

1. **Plan Naming Convention**: `"EFIR Strategic Plan {base_year}-{base_year+4}"`
   - Example: "EFIR Strategic Plan 2025-2030"

2. **Base Year Range**: `2000 ≤ base_year ≤ 2100`

3. **Plan Status Workflow**:
   ```
   draft → approved → archived
   ```
   - Draft: Plan in development
   - Approved: Plan approved by Board
   - Archived: Plan completed or superseded

4. **Unique Plan Names**: No two plans can have the same name

5. **Soft Delete**: Plans are never hard-deleted (audit trail)

### Scenario Rules

6. **One Scenario Per Type Per Plan**: Each plan can have at most one scenario of each type
   - Example: One BASE_CASE, one CONSERVATIVE, one OPTIMISTIC per plan

7. **Growth Rate Constraints**:
   - Enrollment: -50% to +100% per year (typically 0-8%)
   - Fee Increase: -20% to +50% per year (typically 2-6%)
   - Salary Inflation: -20% to +50% per year (typically 2-5%)
   - Operating Inflation: -20% to +50% per year (typically 2-4%)

8. **Realistic Growth Rates** (Business Validation):
   - Conservative: 0-2% enrollment, 2-3% fees
   - Base Case: 3-5% enrollment, 3-4% fees
   - Optimistic: 6-8% enrollment, 4-6% fees

### Projection Rules

9. **5-Year Projection Period**: Years 1-5 only

10. **One Projection Per Year/Category/Scenario**: Unique constraint on (scenario_id, year, category)

11. **Non-Negative Amounts**: All projected amounts must be ≥ 0

12. **5 Required Categories**: Each year should have projections for all 5 categories

13. **Year 1 = Base Year**: Year 1 projections typically match current budget amounts

### Initiative Rules

14. **Initiative Timing**: `1 ≤ planned_year ≤ 5`

15. **Non-Negative CapEx**: Capital expenditure amounts must be ≥ 0

16. **Operating Impact Can Be Positive or Negative**: New programs add cost, efficiency initiatives reduce cost

17. **Status Transitions**: Follow defined workflow (planned → approved → in_progress → completed)

18. **CapEx Adds to Projections**: Initiative CapEx amounts should be included in capex projections for the planned year

19. **Operating Impact Is Recurring**: Operating impact applies from planned year onwards (not one-time)

## Calculation Formulas

### Multi-Year Revenue Projection

**Formula:**
```
Year 1: Revenue₁ = Current Budget Revenue (base amount)
Year 2: Revenue₂ = Revenue₁ × (1 + enrollment_growth) × (1 + fee_increase)
Year 3: Revenue₃ = Revenue₂ × (1 + enrollment_growth) × (1 + fee_increase)
Year 4: Revenue₄ = Revenue₃ × (1 + enrollment_growth) × (1 + fee_increase)
Year 5: Revenue₅ = Revenue₄ × (1 + enrollment_growth) × (1 + fee_increase)
```

**Example (BASE_CASE Scenario):**
```
Assumptions:
- enrollment_growth_rate = 0.04 (4% per year)
- fee_increase_rate = 0.03 (3% per year)
- Base revenue (2025) = 55,515,000 SAR

Year 1 (2025): 55,515,000 SAR (base year)
Year 2 (2026): 55,515,000 × 1.04 × 1.03 = 59,462,112 SAR
Year 3 (2027): 59,462,112 × 1.04 × 1.03 = 63,656,952 SAR
Year 4 (2028): 63,656,952 × 1.04 × 1.03 = 68,116,441 SAR
Year 5 (2029): 68,116,441 × 1.04 × 1.03 = 72,857,913 SAR

Total 5-Year Revenue: 319,608,418 SAR
Compound Annual Growth Rate (CAGR): 7.0% per year
```

### Multi-Year Cost Projection

**Formula (Personnel Costs):**
```
Year 1: Personnel₁ = Current Budget Personnel Costs (base amount)
Year 2: Personnel₂ = Personnel₁ × (1 + enrollment_growth) × (1 + salary_inflation)
...
Year 5: Personnel₅ = Personnel₄ × (1 + enrollment_growth) × (1 + salary_inflation)

Note: Personnel costs grow with both enrollment (more teachers) and salary inflation
```

**Formula (Operating Costs):**
```
Year 1: Operating₁ = Current Budget Operating Costs (base amount)
Year 2: Operating₂ = Operating₁ × (1 + operating_inflation)
...
Year 5: Operating₅ = Operating₄ × (1 + operating_inflation)

Note: Operating costs grow only with inflation, not enrollment (fixed facilities)
```

**Example (BASE_CASE Scenario):**
```
Assumptions:
- enrollment_growth_rate = 0.04 (4% per year)
- salary_inflation_rate = 0.035 (3.5% per year)
- operating_inflation_rate = 0.025 (2.5% per year)
- Base personnel costs (2025) = 28,500,000 SAR
- Base operating costs (2025) = 18,300,000 SAR

Personnel Costs:
Year 1 (2025): 28,500,000 SAR
Year 2 (2026): 28,500,000 × 1.04 × 1.035 = 30,663,600 SAR
Year 3 (2027): 30,663,600 × 1.04 × 1.035 = 32,993,474 SAR
Year 4 (2028): 32,993,474 × 1.04 × 1.035 = 35,500,376 SAR
Year 5 (2029): 35,500,376 × 1.04 × 1.035 = 38,197,605 SAR
Total: 165,855,055 SAR

Operating Costs:
Year 1 (2025): 18,300,000 SAR
Year 2 (2026): 18,300,000 × 1.025 = 18,757,500 SAR
Year 3 (2027): 18,757,500 × 1.025 = 19,226,438 SAR
Year 4 (2028): 19,226,438 × 1.025 = 19,707,099 SAR
Year 5 (2029): 19,707,099 × 1.025 = 20,199,776 SAR
Total: 96,190,813 SAR
```

### Initiative Impact on Projections

**CapEx Impact (One-Time):**
```
CapEx_projection[year] += initiative.capex_amount_sar (if year == planned_year)
```

**Operating Impact (Recurring):**
```
Operating_projection[year] += initiative.operating_impact_sar (if year >= planned_year)
```

**Example:**
```
Initiative: "New Science Lab"
Planned Year: 2 (2026)
CapEx: 2,500,000 SAR
Operating Impact: +150,000 SAR/year

Impact on Projections:
Year 1 (2025): No impact
Year 2 (2026): +2,500,000 SAR to CapEx, +150,000 SAR to Operating
Year 3 (2027): +150,000 SAR to Operating
Year 4 (2028): +150,000 SAR to Operating
Year 5 (2029): +150,000 SAR to Operating
```

### Net Result Projection

**Formula:**
```
Net_Result[year] = Revenue[year] - Personnel_Costs[year] - Operating_Costs[year] - Depreciation[year]
```

**5-Year Cumulative Surplus:**
```
Cumulative_Surplus = Σ(Net_Result[year]) for year 1 to 5
```

**Example (BASE_CASE Scenario):**
```
Year 1: 55.5M - 28.5M - 18.3M - 2.0M = 6.7M SAR surplus
Year 2: 59.5M - 30.7M - 18.8M - 2.1M = 7.9M SAR surplus
Year 3: 63.7M - 33.0M - 19.2M - 2.2M = 9.3M SAR surplus
Year 4: 68.1M - 35.5M - 19.7M - 2.3M = 10.6M SAR surplus
Year 5: 72.9M - 38.2M - 20.2M - 2.4M = 12.1M SAR surplus

5-Year Cumulative Surplus: 46.6M SAR
Average Annual Margin: 14.6%
```

## Example Use Cases

### Use Case 1: Create Strategic Plan with 3 Scenarios

**Scenario**: EFIR creates a 5-year strategic plan (2025-2030) with three scenarios to present to the Board.

**Step 1: Create Strategic Plan**
```sql
INSERT INTO efir_budget.strategic_plans (
    id, name, description, base_year, status
) VALUES (
    '123e4567-e89b-12d3-a456-426614174000'::uuid,
    'EFIR Strategic Plan 2025-2030',
    'Five-year strategic plan with enrollment growth scenarios and new campus evaluation',
    2025,
    'draft'
);
```

**Step 2: Create Conservative Scenario**
```sql
INSERT INTO efir_budget.strategic_plan_scenarios (
    id, strategic_plan_id, scenario_type, name,
    enrollment_growth_rate, fee_increase_rate, salary_inflation_rate, operating_inflation_rate
) VALUES (
    '223e4567-e89b-12d3-a456-426614174001'::uuid,
    '123e4567-e89b-12d3-a456-426614174000'::uuid,
    'conservative',
    'Conservative - Slower Growth',
    0.0100,  -- 1% enrollment growth
    0.0250,  -- 2.5% fee increase
    0.0300,  -- 3% salary inflation
    0.0200   -- 2% operating inflation
);
```

**Step 3: Create Base Case Scenario**
```sql
INSERT INTO efir_budget.strategic_plan_scenarios (
    id, strategic_plan_id, scenario_type, name,
    enrollment_growth_rate, fee_increase_rate, salary_inflation_rate, operating_inflation_rate
) VALUES (
    '323e4567-e89b-12d3-a456-426614174002'::uuid,
    '123e4567-e89b-12d3-a456-426614174000'::uuid,
    'base_case',
    'Base Case - Steady Growth',
    0.0400,  -- 4% enrollment growth
    0.0300,  -- 3% fee increase
    0.0350,  -- 3.5% salary inflation
    0.0250   -- 2.5% operating inflation
);
```

**Step 4: Create Optimistic Scenario**
```sql
INSERT INTO efir_budget.strategic_plan_scenarios (
    id, strategic_plan_id, scenario_type, name,
    enrollment_growth_rate, fee_increase_rate, salary_inflation_rate, operating_inflation_rate
) VALUES (
    '423e4567-e89b-12d3-a456-426614174003'::uuid,
    '123e4567-e89b-12d3-a456-426614174000'::uuid,
    'optimistic',
    'Optimistic - Market Expansion',
    0.0700,  -- 7% enrollment growth
    0.0500,  -- 5% fee increase
    0.0400,  -- 4% salary inflation
    0.0300   -- 3% operating inflation
);
```

**Step 5: Calculate and Insert Projections for Each Scenario**
(Business logic implementation - see Phase 5 calculation engines)

### Use Case 2: Add Strategic Initiative

**Scenario**: EFIR plans to build a new science laboratory in Year 2 (2026).

```sql
INSERT INTO efir_budget.strategic_initiatives (
    id, strategic_plan_id, name, description,
    planned_year, capex_amount_sar, operating_impact_sar, status,
    additional_details
) VALUES (
    '523e4567-e89b-12d3-a456-426614174004'::uuid,
    '123e4567-e89b-12d3-a456-426614174000'::uuid,
    'New Science Laboratory',
    'State-of-the-art science lab with equipment for physics, chemistry, biology. Capacity for 120 students.',
    2,  -- Year 2 (2026)
    2500000.00,  -- 2.5M SAR CapEx
    150000.00,   -- 150K SAR/year operating cost
    'planned',
    '{
        "milestones": [
            {"phase": "Design", "duration": "3 months", "cost": 100000},
            {"phase": "Construction", "duration": "9 months", "cost": 2000000},
            {"phase": "Equipment", "duration": "2 months", "cost": 400000}
        ],
        "dependencies": ["Board approval", "Zoning permit"],
        "risks": ["Construction delays", "Cost overruns"]
    }'::jsonb
);
```

### Use Case 3: Compare Scenarios

**Query: Compare 5-Year Revenue Across All Scenarios**
```sql
SELECT
    sp.name AS plan_name,
    sps.scenario_type,
    sps.name AS scenario_name,
    SUM(spp.amount_sar) AS total_5_year_revenue
FROM efir_budget.strategic_plans sp
JOIN efir_budget.strategic_plan_scenarios sps ON sp.id = sps.strategic_plan_id
JOIN efir_budget.strategic_plan_projections spp ON sps.id = spp.strategic_plan_scenario_id
WHERE sp.id = '123e4567-e89b-12d3-a456-426614174000'::uuid
  AND spp.category = 'revenue'
  AND sp.deleted_at IS NULL
  AND sps.deleted_at IS NULL
  AND spp.deleted_at IS NULL
GROUP BY sp.name, sps.scenario_type, sps.name
ORDER BY sps.scenario_type;
```

**Expected Results:**
```
plan_name                      | scenario_type | scenario_name                    | total_5_year_revenue
-------------------------------|---------------|----------------------------------|---------------------
EFIR Strategic Plan 2025-2030  | conservative  | Conservative - Slower Growth     | 294,500,000 SAR
EFIR Strategic Plan 2025-2030  | base_case     | Base Case - Steady Growth        | 319,600,000 SAR
EFIR Strategic Plan 2025-2030  | optimistic    | Optimistic - Market Expansion    | 356,200,000 SAR
```

**Interpretation**: Optimistic scenario generates 61.7M SAR more revenue over 5 years compared to conservative scenario.

### Use Case 4: Track Initiative Progress

**Query: List All Initiatives by Status**
```sql
SELECT
    sp.name AS plan_name,
    si.name AS initiative_name,
    si.planned_year,
    sp.base_year + si.planned_year - 1 AS execution_year,
    si.capex_amount_sar,
    si.operating_impact_sar,
    si.status
FROM efir_budget.strategic_initiatives si
JOIN efir_budget.strategic_plans sp ON si.strategic_plan_id = sp.id
WHERE sp.id = '123e4567-e89b-12d3-a456-426614174000'::uuid
  AND si.deleted_at IS NULL
ORDER BY si.planned_year, si.status;
```

**Example Results:**
```
plan_name                      | initiative_name           | planned_year | execution_year | capex_amount_sar | operating_impact_sar | status
-------------------------------|---------------------------|--------------|----------------|------------------|----------------------|------------
EFIR Strategic Plan 2025-2030  | ERP System Implementation | 1            | 2025           | 800,000          | 200,000              | in_progress
EFIR Strategic Plan 2025-2030  | New Science Laboratory    | 2            | 2026           | 2,500,000        | 150,000              | planned
EFIR Strategic Plan 2025-2030  | Secondary Campus          | 4            | 2028           | 15,000,000       | 3,500,000            | planned
```

## Integration Points

### Upstream Dependencies

Module 18 consumes data from:

1. **Module 10 (Revenue Planning)**: Base year revenue amounts for Year 1 projections
2. **Module 11 (Personnel & Operating Costs)**: Base year cost amounts for Year 1 projections
3. **Module 12 (CapEx Planning)**: Historical CapEx patterns for depreciation calculations
4. **Module 13 (Budget Consolidation)**: Consolidated budget totals as baseline

**Integration Pattern:**
```
Budget Consolidation (approved version) → Base Year Amounts → Strategic Projections
```

### Downstream Consumers

Module 18 feeds data to:

1. **Module 15 (KPIs)**: Long-term KPI projections (e.g., projected student-teacher ratio in Year 5)
2. **Module 16 (Dashboards)**: Strategic planning dashboards showing scenario comparisons
3. **Board Reports**: Executive summaries for strategic decision-making

### Cross-Module Calculations

**Example: Year 5 Projected Enrollment**
```sql
-- Calculate Year 5 enrollment from base enrollment + 5 years of growth
WITH base_enrollment AS (
    SELECT SUM(student_count) AS total_students
    FROM efir_budget.enrollment_plans ep
    JOIN efir_budget.settings_versions v ON ep.version_id = v.id
    WHERE bv.fiscal_year = 2025
      AND bv.status = 'approved'
      AND ep.deleted_at IS NULL
      AND bv.deleted_at IS NULL
),
scenario_growth AS (
    SELECT enrollment_growth_rate
    FROM efir_budget.strategic_plan_scenarios
    WHERE id = '<scenario_id>'
)
SELECT
    be.total_students * POWER(1 + sg.enrollment_growth_rate, 5) AS year_5_projected_enrollment
FROM base_enrollment be
CROSS JOIN scenario_growth sg;

-- Example: 1,234 students × (1.04)^5 = 1,502 students in Year 5
```

## Testing Scenarios

### Test Scenario 1: Create Complete Strategic Plan

**Objective**: Verify all 4 tables work together correctly

**Steps:**
1. Create strategic plan (draft status)
2. Create 3 scenarios (conservative, base_case, optimistic)
3. Create 5-year projections for each scenario (5 years × 5 categories × 3 scenarios = 75 projections)
4. Create 3 strategic initiatives
5. Verify all data inserted correctly
6. Verify RLS policies enforce access control
7. Approve strategic plan
8. Verify viewers can now see the plan

**Expected Results:**
- All inserts succeed
- Unique constraints prevent duplicate scenarios
- Check constraints validate growth rates
- Soft delete works correctly

### Test Scenario 2: Projection Calculation

**Objective**: Verify projection formulas are correct

**Steps:**
1. Create base_case scenario with known growth rates:
   - Enrollment: 4% per year
   - Fee Increase: 3% per year
2. Calculate Year 1-5 revenue projections manually
3. Compare with database-stored projections
4. Verify compound growth is applied correctly

**Expected Results:**
- Projections match manual calculations within rounding tolerance (±1 SAR)
- Year 5 revenue = Base revenue × (1.04 × 1.03)^4

### Test Scenario 3: Scenario Comparison

**Objective**: Verify scenario comparison queries work correctly

**Steps:**
1. Create 3 scenarios with different growth assumptions
2. Generate projections for all 3 scenarios
3. Query total 5-year revenue for each scenario
4. Query total 5-year surplus for each scenario
5. Calculate delta between optimistic and conservative

**Expected Results:**
- Optimistic scenario has highest revenue
- Conservative scenario has lowest revenue
- Delta calculations are accurate

### Test Scenario 4: Initiative Impact

**Objective**: Verify initiatives correctly impact projections

**Steps:**
1. Create scenario with baseline projections
2. Add initiative with CapEx = 2M SAR in Year 2
3. Add initiative with Operating Impact = +150K SAR/year from Year 3
4. Verify CapEx projection for Year 2 increases by 2M
5. Verify Operating projections for Years 3-5 increase by 150K

**Expected Results:**
- Initiative CapEx appears in correct year
- Operating impact is recurring from planned year onwards

### Test Scenario 5: RLS Policy Enforcement

**Objective**: Verify Row Level Security policies work correctly

**Steps:**
1. Create plan with status = 'draft'
2. Test as Admin: Should see all plans
3. Test as Manager: Should see all plans
4. Test as Viewer: Should NOT see draft plans
5. Approve plan (status = 'approved')
6. Test as Viewer: Should now see approved plan
7. Archive plan (status = 'archived')
8. Test as Viewer: Should NOT see archived plans

**Expected Results:**
- Admins always have full access
- Managers have full access to all plans
- Viewers only see approved plans

## API Endpoints (Future - Phase 5)

### Strategic Plans

```
POST   /api/v1/strategic/plans               Create new strategic plan
GET    /api/v1/strategic/plans                List all plans (filtered by status/RLS)
GET    /api/v1/strategic/plans/{id}           Get plan details
PUT    /api/v1/strategic/plans/{id}           Update plan
DELETE /api/v1/strategic/plans/{id}           Soft delete plan
POST   /api/v1/strategic/plans/{id}/approve   Approve plan (status → 'approved')
```

### Scenarios

```
POST   /api/v1/strategic/scenarios                        Create scenario
GET    /api/v1/strategic/scenarios?plan_id={id}           List scenarios for plan
GET    /api/v1/strategic/scenarios/{id}                   Get scenario details
PUT    /api/v1/strategic/scenarios/{id}                   Update scenario
DELETE /api/v1/strategic/scenarios/{id}                   Soft delete scenario
POST   /api/v1/strategic/scenarios/{id}/calculate         Trigger projection calculation
```

### Projections

```
GET    /api/v1/strategic/projections?scenario_id={id}               Get all projections for scenario
GET    /api/v1/strategic/projections?scenario_id={id}&year={1-5}    Get projections for specific year
GET    /api/v1/strategic/projections/compare?scenario_ids={id1},{id2}  Compare scenarios side-by-side
```

### Initiatives

```
POST   /api/v1/strategic/initiatives                  Create initiative
GET    /api/v1/strategic/initiatives?plan_id={id}     List initiatives for plan
GET    /api/v1/strategic/initiatives/{id}             Get initiative details
PUT    /api/v1/strategic/initiatives/{id}             Update initiative
DELETE /api/v1/strategic/initiatives/{id}             Soft delete initiative
PUT    /api/v1/strategic/initiatives/{id}/status      Update initiative status
```

## Version History

| Version | Date       | Author      | Changes                                      |
|---------|------------|-------------|----------------------------------------------|
| 1.0.0   | 2025-12-01 | Claude Code | Initial documentation for Module 18          |
|         |            |             | - 4 tables defined                           |
|         |            |             | - 3 enums defined                            |
|         |            |             | - 16 RLS policies documented                 |
|         |            |             | - Business rules and formulas documented     |
|         |            |             | - Example use cases and test scenarios       |

---

**Module 18: 5-Year Strategic Planning** - Complete Database Foundation Documentation
