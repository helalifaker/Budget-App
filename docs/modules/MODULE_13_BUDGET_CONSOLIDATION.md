# Module 13: Budget Consolidation

## Overview

Module 13 consolidates all revenue projections (Module 10), operating costs (Module 11), and capital expenditures (Module 12) into a unified annual budget with version management and approval workflow. This module calculates key financial metrics (surplus/deficit, operating margin, EBITDA), supports multiple budget scenarios (conservative, base, optimistic), manages budget approval lifecycle (Working → Submitted → Approved), and enables side-by-side comparison of budget versions for decision-making.

**Layer**: Consolidation Layer (Phase 3)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Budget approval workflow, scenario comparison UI, variance analysis, API endpoints (Phase 5-6)

### Purpose

- Consolidate revenue and cost projections from planning modules (7-12) into unified budget
- Manage budget version lifecycle (Working → Submitted → Approved → Forecast → Superseded)
- Calculate key financial metrics (operating surplus/deficit, operating margin, EBITDA, net margin)
- Support multiple budget scenarios (conservative, base, optimistic) for decision analysis
- Track budget approvals with audit trail (who approved, when)
- Enable side-by-side comparison of budget versions
- Validate budget integrity (revenue - costs = surplus/deficit)
- Prepare consolidated data for financial statements (Module 14)

### Key Design Decisions

1. **Version-Centric**: All budget data versioned for historical tracking and scenario comparison
2. **Approval Workflow**: Formal workflow (Working → Submitted → Approved) with role-based permissions
3. **Auto-Calculation**: Financial metrics calculated automatically from revenue and cost data
4. **Scenario Support**: Multiple scenarios within same fiscal year (conservative, base, optimistic)
5. **Audit Trail**: All approvals, revisions, and status changes tracked with timestamps and users
6. **Validation Rules**: Enforce budget integrity (revenue - costs must balance to surplus/deficit)
7. **Superseded Handling**: Old budgets marked 'superseded' when new version approved

## Database Schema

### Tables

#### 1. settings_versions

Master budget version tracking and approval.

**Columns:**
```sql
id                    UUID PRIMARY KEY
fiscal_year           INTEGER NOT NULL
version_name          VARCHAR(100) NOT NULL
scenario_name         VARCHAR(50) NULL DEFAULT 'base'  -- conservative, base, optimistic
status                budgetstatus NOT NULL            -- ENUM: working, submitted, approved, forecast, superseded
is_baseline           BOOLEAN NOT NULL DEFAULT false
description           TEXT NULL
submitted_date        TIMESTAMPTZ NULL
submitted_by_id       UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
approved_date         TIMESTAMPTZ NULL
approved_by_id        UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
superseded_date       TIMESTAMPTZ NULL
superseded_by_id      UUID NULL FOREIGN KEY -> settings_versions.id (SET NULL)
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- UNIQUE (fiscal_year, version_name)
- Only one is_baseline = true per fiscal_year
- If status = 'submitted', submitted_date IS NOT NULL AND submitted_by_id IS NOT NULL
- If status = 'approved', approved_date IS NOT NULL AND approved_by_id IS NOT NULL
- If status = 'superseded', superseded_date IS NOT NULL AND superseded_by_id IS NOT NULL
- status progression: working → submitted → approved (cannot revert)

**RLS Policies:**
- Admin: Full access to all budget versions
- Manager: Create/edit Working versions, submit for approval, read all versions
- Approver: Approve Submitted versions, read all versions
- Viewer: Read Approved and Forecast versions only

**Indexes:**
- Primary key on id
- Index on (fiscal_year, status)
- Index on (fiscal_year, is_baseline)

#### 2. consolidated_budget

Consolidated budget summary by version.

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL UNIQUE FOREIGN KEY -> settings_versions.id (CASCADE)
total_revenue         NUMERIC(14, 2) NOT NULL
total_operating_costs NUMERIC(14, 2) NOT NULL
total_capex           NUMERIC(14, 2) NOT NULL
operating_surplus     NUMERIC(14, 2) NOT NULL          -- revenue - operating_costs
net_surplus           NUMERIC(14, 2) NOT NULL          -- revenue - operating_costs - capex
operating_margin_pct  NUMERIC(5, 2) NOT NULL           -- operating_surplus / revenue * 100
net_margin_pct        NUMERIC(5, 2) NOT NULL           -- net_surplus / revenue * 100
ebitda                NUMERIC(14, 2) NOT NULL          -- operating_surplus + depreciation
ebitda_margin_pct     NUMERIC(5, 2) NOT NULL           -- ebitda / revenue * 100
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- operating_surplus = total_revenue - total_operating_costs (enforced by trigger)
- net_surplus = total_revenue - total_operating_costs - total_capex
- operating_margin_pct = (operating_surplus / total_revenue) * 100
- net_margin_pct = (net_surplus / total_revenue) * 100

**RLS Policies:**
- Same as settings_versions

**Indexes:**
- Primary key on id
- Index on version_id (unique constraint)

#### 3. budget_line_items

Granular budget detail by account code for consolidation.

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
account_code          VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
account_name          VARCHAR(200) NOT NULL
line_item_type        lineitemtype NOT NULL            -- ENUM: revenue, expense
amount                NUMERIC(12, 2) NOT NULL
cost_center_id        UUID NULL FOREIGN KEY -> cost_centers.id (RESTRICT)
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- If line_item_type = 'revenue', account_code must start with '70', '71', '74', '75', '76', or '77'
- If line_item_type = 'expense', account_code must start with '60', '61', '62', '63', '64', '65', '66', '67', or '68'
- UNIQUE (version_id, account_code, cost_center_id)

**RLS Policies:**
- Same as settings_versions

**Indexes:**
- Primary key on id
- Index on (version_id, line_item_type)
- Index on account_code for account-level summaries

#### 4. budget_approval_log

Audit trail for budget approvals and status changes.

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
action                budgetaction NOT NULL            -- ENUM: created, submitted, approved, rejected, revised, superseded
previous_status       budgetstatus NULL
new_status            budgetstatus NOT NULL
performed_by_id       UUID NOT NULL FOREIGN KEY -> auth.users.id (SET NULL)
performed_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
comment               TEXT NULL
```

**Constraints:**
- performed_at >= budget_version.created_at

**RLS Policies:**
- All authenticated users can read approval log
- Only system can write (auto-created on status changes)

**Indexes:**
- Primary key on id
- Index on (version_id, performed_at DESC) for audit trail

### Enums

#### BudgetStatus
```sql
CREATE TYPE efir_budget.budgetstatus AS ENUM (
    'working',          -- Draft, editable by managers
    'submitted',        -- Submitted for approval, locked
    'approved',         -- Approved by authority, official budget
    'forecast',         -- Mid-year revised forecast
    'superseded'        -- Replaced by newer version
);
```

#### BudgetAction
```sql
CREATE TYPE efir_budget.budgetaction AS ENUM (
    'created',          -- Budget version created
    'submitted',        -- Submitted for approval
    'approved',         -- Approved by authority
    'rejected',         -- Rejected, returned to working
    'revised',          -- Revised after approval (creates forecast)
    'superseded'        -- Superseded by newer version
);
```

#### LineItemType
```sql
CREATE TYPE efir_budget.lineitemtype AS ENUM (
    'revenue',          -- Revenue line item (70xxx-77xxx)
    'expense'           -- Expense line item (60xxx-68xxx)
);
```

## Data Model

### Sample Budget Versions (2025-2026)

```json
[
  {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "fiscal_year": 2026,
    "version_name": "2026 Approved Budget (Base Scenario)",
    "scenario_name": "base",
    "status": "approved",
    "is_baseline": true,
    "description": "Official 2026 budget based on 1,900 student enrollment projection",
    "submitted_date": "2025-11-15T10:00:00Z",
    "submitted_by_id": "user-manager-uuid",
    "approved_date": "2025-12-01T14:30:00Z",
    "approved_by_id": "user-director-uuid",
    "superseded_date": null,
    "superseded_by_id": null,
    "notes": "Approved by Board on December 1, 2025"
  },
  {
    "id": "223e4567-e89b-12d3-a456-426614174001",
    "fiscal_year": 2026,
    "version_name": "2026 Conservative Scenario",
    "scenario_name": "conservative",
    "status": "working",
    "is_baseline": false,
    "description": "Conservative scenario with 1,800 students (-5% enrollment)",
    "submitted_date": null,
    "submitted_by_id": null,
    "approved_date": null,
    "approved_by_id": null,
    "notes": "What-if scenario for risk planning"
  },
  {
    "id": "323e4567-e89b-12d3-a456-426614174002",
    "fiscal_year": 2026,
    "version_name": "2026 Optimistic Scenario",
    "scenario_name": "optimistic",
    "status": "working",
    "is_baseline": false,
    "description": "Optimistic scenario with 2,000 students (+8% enrollment)",
    "submitted_date": null,
    "submitted_by_id": null,
    "approved_date": null,
    "approved_by_id": null,
    "notes": "What-if scenario for capacity planning"
  }
]
```

### Sample Consolidated Budget (Base Scenario 2025-2026)

```json
{
  "id": "cb0e8400-e29b-41d4-a716-446655440600",
  "version_id": "123e4567-e89b-12d3-a456-426614174000",
  "total_revenue": 30245000.00,
  "total_operating_costs": 23930000.00,
  "total_capex": 1480000.00,
  "operating_surplus": 6315000.00,
  "net_surplus": 4835000.00,
  "operating_margin_pct": 20.88,
  "net_margin_pct": 15.99,
  "ebitda": 7133500.00,
  "ebitda_margin_pct": 23.58,
  "currency": "SAR",
  "calculated_at": "2025-12-01T15:00:00Z"
}
```

### Budget Comparison (2025-2026 Scenarios)

| Metric | Conservative (1,800) | Base (1,900) | Optimistic (2,000) | Variance (Base vs Cons) |
|--------|----------------------|--------------|---------------------|-------------------------|
| **Revenue** | 28,800,000 | 30,245,000 | 31,850,000 | +1,445,000 (+5.0%) |
| - Tuition | 27,180,000 | 28,500,000 | 30,000,000 | +1,320,000 (+4.9%) |
| - DAI | 900,000 | 950,000 | 1,000,000 | +50,000 (+5.6%) |
| - Enrollment | 180,000 | 225,000 | 270,000 | +45,000 (+25.0%) |
| - Other | 540,000 | 570,000 | 580,000 | +30,000 (+5.6%) |
| **Operating Costs** | 23,100,000 | 23,930,000 | 24,850,000 | +830,000 (+3.6%) |
| - Personnel | 14,850,000 | 15,750,000 | 16,800,000 | +900,000 (+6.1%) |
| - Facility | 1,150,000 | 1,200,000 | 1,280,000 | +50,000 (+4.3%) |
| - Operating | 7,100,000 | 6,980,000 | 6,770,000 | -120,000 (-1.7%) |
| **CapEx** | 1,200,000 | 1,480,000 | 2,100,000 | +280,000 (+23.3%) |
| **Operating Surplus** | 5,700,000 | 6,315,000 | 7,000,000 | +615,000 (+10.8%) |
| **Net Surplus** | 4,500,000 | 4,835,000 | 4,900,000 | +335,000 (+7.4%) |
| **Operating Margin** | 19.79% | 20.88% | 21.98% | +1.09% |
| **Net Margin** | 15.63% | 15.99% | 15.38% | +0.36% |

## Business Rules

### Budget Version Rules

1. **Version Lifecycle**: Working → Submitted → Approved (cannot revert to earlier status)
2. **Single Baseline**: Only one is_baseline = true per fiscal year
3. **Version Naming**: Convention "YYYY [Scenario] [Status]" (e.g., "2026 Base Approved")
4. **Scenario Support**: Multiple scenarios allowed within same fiscal year (conservative, base, optimistic)
5. **Superseded Handling**: When new version approved, mark previous approved version as 'superseded'

### Budget Approval Rules

1. **Submission Requirements**: Working budget must pass validation before submission
   - Total revenue > 0
   - Total costs > 0
   - All required modules complete (Enrollment, Revenue, Costs, CapEx)
2. **Approval Authority**: Only users with 'Approver' role can approve budgets
3. **Approval Lock**: Once approved, budget is locked (read-only except for forecast revision)
4. **Audit Trail**: All status changes logged in budget_approval_log with user and timestamp
5. **Rejection Handling**: Rejected budgets revert to 'working' status for revision

### Financial Metric Rules

1. **Operating Surplus**: Revenue - Operating Costs (excludes CapEx)
2. **Net Surplus**: Revenue - Operating Costs - CapEx (includes CapEx)
3. **Operating Margin**: (Operating Surplus ÷ Revenue) × 100
4. **Net Margin**: (Net Surplus ÷ Revenue) × 100
5. **EBITDA**: Operating Surplus + Depreciation Expense
6. **EBITDA Margin**: (EBITDA ÷ Revenue) × 100

### Validation Rules

1. **Budget Balance**: Σ(revenue line items) - Σ(expense line items) = Operating Surplus
2. **Account Code Validity**: Revenue accounts (70xxx-77xxx), expense accounts (60xxx-68xxx)
3. **Positive Revenue**: Total revenue must be > 0
4. **Realistic Margins**: Operating margin between 10-30% (outside range triggers warning)
5. **Enrollment Consistency**: Student counts must match Module 7 enrollment projections
6. **Fee Consistency**: Revenue calculations must use Module 5 fee structures

## Calculation Examples

### Example 1: Operating Surplus Calculation (Base Scenario)

**Context**: Calculate operating surplus for 2025-2026 base scenario.

**Given Data**:
- Total revenue: 30,245,000 SAR (from Module 10)
- Total operating costs: 23,930,000 SAR (from Module 11)

**Calculation:**
```
Operating surplus = Total revenue - Total operating costs
                  = 30,245,000 - 23,930,000
                  = 6,315,000 SAR

Operating margin = (Operating surplus ÷ Total revenue) × 100
                 = (6,315,000 ÷ 30,245,000) × 100
                 = 20.88%
```

**Result**: 6,315,000 SAR operating surplus (20.88% margin)

### Example 2: Net Surplus Calculation (Including CapEx)

**Context**: Calculate net surplus after CapEx for base scenario.

**Given Data**:
- Operating surplus: 6,315,000 SAR (from Example 1)
- Total CapEx: 1,480,000 SAR (from Module 12)

**Calculation:**
```
Net surplus = Operating surplus - Total CapEx
            = 6,315,000 - 1,480,000
            = 4,835,000 SAR

Net margin = (Net surplus ÷ Total revenue) × 100
           = (4,835,000 ÷ 30,245,000) × 100
           = 15.99%
```

**Result**: 4,835,000 SAR net surplus (15.99% margin)

### Example 3: EBITDA Calculation

**Context**: Calculate EBITDA for base scenario.

**Given Data**:
- Operating surplus: 6,315,000 SAR
- Total depreciation expense: 818,500 SAR (from Module 12)

**Calculation:**
```
EBITDA = Operating surplus + Depreciation expense
       = 6,315,000 + 818,500
       = 7,133,500 SAR

EBITDA margin = (EBITDA ÷ Total revenue) × 100
              = (7,133,500 ÷ 30,245,000) × 100
              = 23.58%
```

**Result**: 7,133,500 SAR EBITDA (23.58% margin)

### Example 4: Scenario Comparison (Conservative vs Base)

**Context**: Compare conservative scenario to base scenario.

**Given Data**:
- Conservative revenue: 28,800,000 SAR (1,800 students)
- Base revenue: 30,245,000 SAR (1,900 students)
- Conservative operating surplus: 5,700,000 SAR
- Base operating surplus: 6,315,000 SAR

**Calculation:**
```
Revenue variance = 30,245,000 - 28,800,000 = +1,445,000 SAR (+5.0%)
Operating surplus variance = 6,315,000 - 5,700,000 = +615,000 SAR (+10.8%)

Variance analysis:
- 100 additional students generate +1,445,000 SAR revenue (+5.0%)
- Variable costs increase by +830,000 SAR (+3.6%)
- Operating surplus increases by +615,000 SAR (+10.8%)
- Operating leverage: Surplus growth (10.8%) > Revenue growth (5.0%)

Interpretation: Positive operating leverage - incremental students highly profitable
```

**Result**: Base scenario +615,000 SAR better operating surplus than conservative

### Example 5: Budget Validation Check

**Context**: Validate budget integrity before submission.

**Given Data** (Base scenario line items):
- Revenue line items: Σ = 30,245,000 SAR
- Expense line items: Σ = 23,930,000 SAR
- Expected operating surplus: 6,315,000 SAR

**Validation:**
```
Budget balance check:
Σ(revenue) - Σ(expense) = Operating surplus
30,245,000 - 23,930,000 = 6,315,000 ✓

Revenue validation:
Total revenue > 0: 30,245,000 > 0 ✓

Operating margin validation:
Operating margin = 20.88%
Target range: 10-30%
20.88% within range ✓

Module completeness:
✓ Module 7 (Enrollment): 1,900 students projected
✓ Module 10 (Revenue): 30,245,000 SAR calculated
✓ Module 11 (Costs): 23,930,000 SAR calculated
✓ Module 12 (CapEx): 1,480,000 SAR planned

Validation result: PASS - Budget ready for submission
```

**Result**: Budget passes all validation checks, ready for submission

## Integration Points

### Upstream Dependencies

1. **Module 7 (Enrollment Planning)**: Student counts for validation
2. **Module 10 (Revenue Planning)**: Total revenue and line item detail
3. **Module 11 (Cost Planning)**: Total operating costs and line item detail
4. **Module 12 (CapEx Planning)**: Total CapEx and depreciation expense
5. **Module 1 (System Configuration)**: Chart of accounts, cost centers

### Downstream Consumers

1. **Module 14 (Financial Statements)**: Consolidated budget feeds into income statement, balance sheet, cash flow
2. **Module 17 (Budget vs Actual)**: Approved budget compared to actuals
3. **Module 18 (5-Year Strategic Plan)**: Annual budgets aggregate into multi-year plan

### Data Flow

```
Module 7 (Enrollment) → Student Counts
Module 10 (Revenue) → Revenue Projections
Module 11 (Costs) → Operating Cost Projections
Module 12 (CapEx) → CapEx and Depreciation
        ↓              ↓
        └──────────────┴──────────────┐
                                      ↓
                Budget Consolidation (Module 13)
                ┌──────────┼──────────┐
                ↓          ↓          ↓
        Consolidated  Financial  Approval
           Budget     Metrics   Workflow
                ↓          ↓          ↓
                └──────────┴──────────┘
                          ↓
              Financial Statements (Module 14)
                          ↓
              Budget vs Actual (Module 17)
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions
GET    /api/v1/budget-versions/:id
POST   /api/v1/budget-versions
PUT    /api/v1/budget-versions/:id/submit
PUT    /api/v1/budget-versions/:id/approve
PUT    /api/v1/budget-versions/:id/reject
GET    /api/v1/budget-versions/:id/consolidated
GET    /api/v1/budget-versions/:id/line-items
GET    /api/v1/budget-versions/:id/approval-log
POST   /api/v1/compare-budgets
       Request: { version_ids: [id1, id2, id3] }
       Response: { comparison_table, variance_analysis }
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Operating Surplus Calculation
```typescript
const revenue = 30245000;
const operatingCosts = 23930000;

const operatingSurplus = revenue - operatingCosts;
expect(operatingSurplus).toBe(6315000);

const operatingMargin = (operatingSurplus / revenue) * 100;
expect(operatingMargin).toBeCloseTo(20.88, 2);
```

#### Scenario 2: Budget Validation
```typescript
const budget = {
  revenue_line_items: [{ amount: 28500000 }, { amount: 950000 }, ...],
  expense_line_items: [{ amount: 15750000 }, { amount: 1200000 }, ...]
};

const validation = validateBudget(budget);
expect(validation.balance_check).toBe(true);
expect(validation.margin_in_range).toBe(true);
expect(validation.ready_for_submission).toBe(true);
```

#### Scenario 3: Budget Approval Workflow
```typescript
const budget = await getBudgetVersion(budgetId);
expect(budget.status).toBe("working");

await submitBudget(budgetId, managerId);
const submitted = await getBudgetVersion(budgetId);
expect(submitted.status).toBe("submitted");
expect(submitted.submitted_by_id).toBe(managerId);

await approveBudget(budgetId, approverId);
const approved = await getBudgetVersion(budgetId);
expect(approved.status).toBe("approved");
expect(approved.approved_by_id).toBe(approverId);
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: budget_versions, consolidated_budget, budget_line_items, budget_approval_log tables |

## Future Enhancements (Phase 5-6)

1. **Budget Approval Workflow UI**: Visual workflow with notifications and approval requests
2. **Scenario Comparison Dashboard**: Side-by-side comparison with variance analysis
3. **Budget Templates**: Reusable budget templates based on prior years
4. **Automated Alerts**: Notify when budgets pending approval or approaching deadlines
5. **Budget Commentary**: Rich text commentary and assumptions documentation
6. **Revision History**: Track all changes to budget versions with diff comparison
7. **Budget Lock Controls**: Granular permissions for editing vs viewing budget sections
8. **Multi-Year Consolidation**: Roll up annual budgets into 5-year strategic plan
9. **Budget Variance Alerts**: Notify when actuals deviate significantly from budget
10. **Integration with Accounting**: Sync approved budget to accounting system (Odoo)

## Notes

- **Phase 4 Scope**: Database foundation only - budget consolidation and version management
- **Business Logic**: Approval workflow UI and scenario comparison dashboards deferred to Phase 5-6
- **Critical Metrics**: Operating margin (20.88%) and net margin (15.99%) within healthy range
- **Positive Surplus**: Base scenario projects 4.8M SAR net surplus - financially sustainable
- **Operating Leverage**: Incremental students highly profitable (surplus growth > revenue growth)
- **Scenario Planning**: Conservative/base/optimistic scenarios enable risk-adjusted planning
- **Data Source**: Financial metrics and consolidation logic based on EFIR actual data (2024-2025)
