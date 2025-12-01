# Module 14: Financial Statements

## Overview

Module 14 generates formal financial statements from the consolidated budget (Module 13) following French accounting standards (Plan Comptable Général - PCG) with IFRS mapping for international reporting. This module produces three primary financial statements: Income Statement (Compte de Résultat), Balance Sheet (Bilan), and Cash Flow Statement (Tableau de Flux de Trésorerie). All statements are generated from the approved budget and support multi-period comparison, trimester-based revenue recognition, and export to external accounting systems.

**Layer**: Consolidation Layer (Phase 3)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: IFRS conversion, financial ratio analysis, export to Odoo, API endpoints (Phase 5-6)

### Purpose

- Generate Income Statement from revenue and expense line items (French PCG format)
- Generate Balance Sheet showing assets, liabilities, and equity
- Generate Cash Flow Statement (operating, investing, financing activities)
- Support French PCG accounting standards with IFRS mapping
- Enable multi-period comparison (budget vs prior year, budget vs actual)
- Track depreciation and amortization schedules
- Calculate key financial ratios (current ratio, debt-to-equity, return on assets)
- Export financial statements to accounting system (Odoo integration)

### Key Design Decisions

1. **French PCG Primary**: All statements follow French PCG format (legally required for French schools)
2. **IFRS Mapping**: Secondary IFRS mapping for international reporting and consolidation
3. **Auto-Generation**: Financial statements auto-generated from Module 13 consolidated budget
4. **Trimester Recognition**: Revenue recognized across T1/T2/T3 (40%/30%/30%) per French standards
5. **Budget vs Actual**: Support comparison of budgeted vs actual financial statements
6. **Non-Cash Adjustments**: Depreciation and amortization tracked separately
7. **Balance Sheet Rollover**: Opening balances from prior year closing balances

## Database Schema

### Tables

#### 1. income_statement

Income statement (Compte de Résultat) following French PCG.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
statement_type        statementtype NOT NULL DEFAULT 'budget'  -- ENUM: budget, actual, forecast
fiscal_year           INTEGER NOT NULL
-- Revenue (Classe 7)
revenue_tuition       NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 701xx
revenue_dai           NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 702xx
revenue_enrollment    NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 702xx
revenue_other         NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 74xxx, 75xxx, 76xxx, 77xxx
total_revenue         NUMERIC(12, 2) NOT NULL
-- Operating Expenses (Classe 6)
expense_materials     NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 60xxx
expense_services      NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 61xxx, 62xxx
expense_taxes         NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 63xxx
expense_personnel     NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 64xxx, 65xxx
expense_depreciation  NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 681xx
expense_other         NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 66xxx, 67xxx, 68xxx (excl 681)
total_expenses        NUMERIC(12, 2) NOT NULL
-- Results
operating_result      NUMERIC(12, 2) NOT NULL                  -- total_revenue - total_expenses
financial_result      NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 76xxx - 66xxx
exceptional_result    NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 77xxx - 67xxx
net_result            NUMERIC(12, 2) NOT NULL                  -- operating + financial + exceptional
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
generated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
notes                 TEXT NULL
```

**Constraints:**
- total_revenue = revenue_tuition + revenue_dai + revenue_enrollment + revenue_other
- total_expenses = expense_materials + expense_services + expense_taxes + expense_personnel + expense_depreciation + expense_other
- operating_result = total_revenue - total_expenses
- net_result = operating_result + financial_result + exceptional_result
- UNIQUE (budget_version_id, statement_type)

**RLS Policies:**
- Admin: Full access to all financial statements
- Manager: Read all statements, write for working/forecast versions
- Viewer: Read approved/forecast statements only

**Indexes:**
- Primary key on id
- Index on (budget_version_id, statement_type)
- Index on fiscal_year for multi-year comparison

#### 2. balance_sheet

Balance sheet (Bilan) following French PCG.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
statement_type        statementtype NOT NULL DEFAULT 'budget'
fiscal_year           INTEGER NOT NULL
statement_date        DATE NOT NULL                            -- End of fiscal period
-- Assets (Actif)
assets_fixed          NUMERIC(12, 2) NOT NULL DEFAULT 0        -- Classe 2 (Immobilisations)
assets_current        NUMERIC(12, 2) NOT NULL DEFAULT 0        -- Classe 3, 4, 5 (Stocks, Créances, Trésorerie)
total_assets          NUMERIC(12, 2) NOT NULL
-- Liabilities (Passif)
equity_capital        NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 101xx (Capital)
equity_reserves       NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 106xx (Réserves)
equity_retained       NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 11xxx (Report à nouveau)
equity_result         NUMERIC(12, 2) NOT NULL DEFAULT 0        -- 12xxx (Résultat de l'exercice)
total_equity          NUMERIC(12, 2) NOT NULL
liabilities_long_term NUMERIC(12, 2) NOT NULL DEFAULT 0        -- Classe 1 (excl equity)
liabilities_current   NUMERIC(12, 2) NOT NULL DEFAULT 0        -- Classe 4 (Dettes)
total_liabilities     NUMERIC(12, 2) NOT NULL
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
generated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
notes                 TEXT NULL
```

**Constraints:**
- total_assets = assets_fixed + assets_current
- total_equity = equity_capital + equity_reserves + equity_retained + equity_result
- total_liabilities = total_equity + liabilities_long_term + liabilities_current
- total_assets = total_liabilities (fundamental accounting equation)
- UNIQUE (budget_version_id, statement_type, statement_date)

**RLS Policies:**
- Same as income_statement

**Indexes:**
- Primary key on id
- Index on (budget_version_id, statement_type, statement_date)

#### 3. cash_flow_statement

Cash flow statement (Tableau de Flux de Trésorerie).

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
statement_type        statementtype NOT NULL DEFAULT 'budget'
fiscal_year           INTEGER NOT NULL
-- Operating Activities (Activités opérationnelles)
cash_from_operations  NUMERIC(12, 2) NOT NULL DEFAULT 0
depreciation_addback  NUMERIC(12, 2) NOT NULL DEFAULT 0
working_capital_chg   NUMERIC(12, 2) NOT NULL DEFAULT 0
net_operating_cash    NUMERIC(12, 2) NOT NULL
-- Investing Activities (Activités d'investissement)
capex_investments     NUMERIC(12, 2) NOT NULL DEFAULT 0
asset_disposals       NUMERIC(12, 2) NOT NULL DEFAULT 0
net_investing_cash    NUMERIC(12, 2) NOT NULL
-- Financing Activities (Activités de financement)
equity_contributions  NUMERIC(12, 2) NOT NULL DEFAULT 0
loan_proceeds         NUMERIC(12, 2) NOT NULL DEFAULT 0
loan_repayments       NUMERIC(12, 2) NOT NULL DEFAULT 0
net_financing_cash    NUMERIC(12, 2) NOT NULL
-- Cash Summary
net_cash_change       NUMERIC(12, 2) NOT NULL
opening_cash          NUMERIC(12, 2) NOT NULL DEFAULT 0
closing_cash          NUMERIC(12, 2) NOT NULL
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
generated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
notes                 TEXT NULL
```

**Constraints:**
- net_operating_cash = cash_from_operations + depreciation_addback + working_capital_chg
- net_investing_cash = asset_disposals - capex_investments (negative = cash outflow)
- net_financing_cash = equity_contributions + loan_proceeds - loan_repayments
- net_cash_change = net_operating_cash + net_investing_cash + net_financing_cash
- closing_cash = opening_cash + net_cash_change
- UNIQUE (budget_version_id, statement_type)

**RLS Policies:**
- Same as income_statement

**Indexes:**
- Primary key on id
- Index on (budget_version_id, statement_type)

#### 4. financial_ratios

Calculated financial ratios for analysis.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
statement_type        statementtype NOT NULL DEFAULT 'budget'
fiscal_year           INTEGER NOT NULL
-- Profitability Ratios
operating_margin_pct  NUMERIC(5, 2) NOT NULL
net_margin_pct        NUMERIC(5, 2) NOT NULL
return_on_assets_pct  NUMERIC(5, 2) NOT NULL
return_on_equity_pct  NUMERIC(5, 2) NOT NULL
-- Liquidity Ratios
current_ratio         NUMERIC(5, 2) NOT NULL
quick_ratio           NUMERIC(5, 2) NOT NULL
cash_ratio            NUMERIC(5, 2) NOT NULL
-- Leverage Ratios
debt_to_equity        NUMERIC(5, 2) NOT NULL
debt_to_assets        NUMERIC(5, 2) NOT NULL
-- Efficiency Ratios
revenue_per_student   NUMERIC(10, 2) NOT NULL
cost_per_student      NUMERIC(10, 2) NOT NULL
surplus_per_student   NUMERIC(10, 2) NOT NULL
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- current_ratio = current_assets / current_liabilities (if current_liabilities > 0)
- debt_to_equity = total_liabilities / total_equity (if total_equity > 0)

**RLS Policies:**
- Same as income_statement

**Indexes:**
- Primary key on id
- Index on (budget_version_id, statement_type)

### Enums

#### StatementType
```sql
CREATE TYPE efir_budget.statementtype AS ENUM (
    'budget',           -- Budget forecast
    'actual',           -- Actual results (from accounting system)
    'forecast'          -- Mid-year revised forecast
);
```

## Data Model

### Sample Income Statement (2025-2026 Budget)

```json
{
  "id": "is0e8400-e29b-41d4-a716-446655440700",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "statement_type": "budget",
  "fiscal_year": 2026,
  "revenue_tuition": 28500000.00,
  "revenue_dai": 950000.00,
  "revenue_enrollment": 225000.00,
  "revenue_other": 570000.00,
  "total_revenue": 30245000.00,
  "expense_materials": 285000.00,
  "expense_services": 7920000.00,
  "expense_taxes": 0.00,
  "expense_personnel": 15750000.00,
  "expense_depreciation": 818500.00,
  "expense_other": 0.00,
  "total_expenses": 24773500.00,
  "operating_result": 5471500.00,
  "financial_result": 0.00,
  "exceptional_result": 0.00,
  "net_result": 5471500.00,
  "currency": "SAR",
  "generated_at": "2025-12-01T16:00:00Z",
  "notes": "Note: Expense total includes depreciation. Operating costs (Module 11) = 23,930,000 + depreciation 818,500 + facility 25,000 = 24,773,500"
}
```

### Sample Balance Sheet (2025-2026 Budget, Year-End)

```json
{
  "id": "bs0e8400-e29b-41d4-a716-446655440800",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "statement_type": "budget",
  "fiscal_year": 2026,
  "statement_date": "2026-12-31",
  "assets_fixed": 18500000.00,
  "assets_current": 8200000.00,
  "total_assets": 26700000.00,
  "equity_capital": 10000000.00,
  "equity_reserves": 5000000.00,
  "equity_retained": 3500000.00,
  "equity_result": 5471500.00,
  "total_equity": 23971500.00,
  "liabilities_long_term": 0.00,
  "liabilities_current": 2728500.00,
  "total_liabilities": 26700000.00,
  "currency": "SAR",
  "generated_at": "2025-12-01T16:00:00Z",
  "notes": "Assets = Liabilities check: 26,700,000 = 26,700,000 ✓"
}
```

### Sample Cash Flow Statement (2025-2026 Budget)

```json
{
  "id": "cf0e8400-e29b-41d4-a716-446655440900",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "statement_type": "budget",
  "fiscal_year": 2026,
  "cash_from_operations": 5471500.00,
  "depreciation_addback": 818500.00,
  "working_capital_chg": -500000.00,
  "net_operating_cash": 5790000.00,
  "capex_investments": 1480000.00,
  "asset_disposals": 0.00,
  "net_investing_cash": -1480000.00,
  "equity_contributions": 0.00,
  "loan_proceeds": 0.00,
  "loan_repayments": 0.00,
  "net_financing_cash": 0.00,
  "net_cash_change": 4310000.00,
  "opening_cash": 3500000.00,
  "closing_cash": 7810000.00,
  "currency": "SAR",
  "generated_at": "2025-12-01T16:00:00Z",
  "notes": "Strong operating cash flow of 5.79M SAR, CapEx investment 1.48M SAR, net cash increase 4.31M SAR"
}
```

### Financial Statement Presentation (French PCG Format)

#### Income Statement (Compte de Résultat) - 2025-2026

| Account | Description | Amount (SAR) | % of Revenue |
|---------|-------------|--------------|--------------|
| **PRODUITS D'EXPLOITATION (Classe 7)** | | | |
| 701xx | Ventes de produits finis (Tuition) | 28,500,000 | 94.2% |
| 702xx | DAI + Enrollment | 1,175,000 | 3.9% |
| 74xxx-77xxx | Autres produits (Cafeteria, Other) | 570,000 | 1.9% |
| **Total Produits** | | **30,245,000** | **100.0%** |
| **CHARGES D'EXPLOITATION (Classe 6)** | | | |
| 60xxx | Achats (Materials, Supplies) | 285,000 | 0.9% |
| 61xxx | Services extérieurs (Facility, Rental) | 1,200,000 | 4.0% |
| 62xxx | Autres services ext. (Professional services) | 6,720,000 | 22.2% |
| 64xxx | Charges de personnel (Salaries, Benefits) | 15,750,000 | 52.1% |
| 681xx | Dotations amortissements (Depreciation) | 818,500 | 2.7% |
| **Total Charges** | | **24,773,500** | **81.9%** |
| **RÉSULTAT D'EXPLOITATION** | | **5,471,500** | **18.1%** |
| **RÉSULTAT FINANCIER** | | 0 | 0.0% |
| **RÉSULTAT EXCEPTIONNEL** | | 0 | 0.0% |
| **RÉSULTAT NET** | | **5,471,500** | **18.1%** |

#### Balance Sheet (Bilan) - As of December 31, 2026

| ACTIF (Assets) | Amount (SAR) | PASSIF (Liabilities) | Amount (SAR) |
|----------------|--------------|----------------------|--------------|
| **ACTIF IMMOBILISÉ** | | **CAPITAUX PROPRES** | |
| Immobilisations corporelles | 18,500,000 | Capital | 10,000,000 |
| | | Réserves | 5,000,000 |
| | | Report à nouveau | 3,500,000 |
| | | Résultat de l'exercice | 5,471,500 |
| **Total Immobilisé** | **18,500,000** | **Total Capitaux Propres** | **23,971,500** |
| **ACTIF CIRCULANT** | | **DETTES** | |
| Créances clients | 4,500,000 | Dettes fournisseurs | 1,200,000 |
| Autres créances | 1,200,000 | Dettes fiscales/sociales | 1,028,500 |
| Trésorerie | 2,500,000 | Autres dettes | 500,000 |
| **Total Circulant** | **8,200,000** | **Total Dettes** | **2,728,500** |
| **TOTAL ACTIF** | **26,700,000** | **TOTAL PASSIF** | **26,700,000** |

## Business Rules

### Income Statement Rules

1. **Revenue Recognition**: Tuition revenue recognized across T1/T2/T3 (40%/30%/30%)
2. **Expense Matching**: Operating expenses matched to revenue period
3. **Depreciation**: Non-cash expense calculated from Module 12 depreciation schedules
4. **PCG Classification**: All line items classified by French PCG account codes
5. **Operating Result**: Primary performance metric (excludes financial and exceptional items)

### Balance Sheet Rules

1. **Fundamental Equation**: Assets = Liabilities + Equity (must always balance)
2. **Fixed Assets**: Net book value = Cost - Accumulated Depreciation
3. **Current Assets**: Cash, receivables, inventory (< 1 year)
4. **Equity Rollover**: Opening equity = Prior year closing equity + current year result
5. **Receivables**: Tuition receivables based on payment timing assumptions

### Cash Flow Statement Rules

1. **Indirect Method**: Start with net result, adjust for non-cash items (depreciation)
2. **Operating Activities**: Net result + depreciation + working capital changes
3. **Investing Activities**: CapEx outflows from Module 12
4. **Financing Activities**: Equity contributions, loan proceeds/repayments
5. **Cash Reconciliation**: Closing cash = Opening cash + Net cash change

### Financial Ratio Rules

1. **Profitability**:
   - Operating margin = Operating result ÷ Total revenue
   - Net margin = Net result ÷ Total revenue
   - ROA = Net result ÷ Total assets
   - ROE = Net result ÷ Total equity
2. **Liquidity**:
   - Current ratio = Current assets ÷ Current liabilities (target: > 1.5)
   - Quick ratio = (Current assets - Inventory) ÷ Current liabilities
   - Cash ratio = Cash ÷ Current liabilities
3. **Leverage**:
   - Debt-to-equity = Total liabilities ÷ Total equity (target: < 0.5)
   - Debt-to-assets = Total liabilities ÷ Total assets

## Calculation Examples

### Example 1: Operating Result Calculation

**Context**: Calculate operating result from revenue and expenses.

**Given Data**:
- Total revenue: 30,245,000 SAR
- Total expenses: 24,773,500 SAR

**Calculation:**
```
Operating result = Total revenue - Total expenses
                 = 30,245,000 - 24,773,500
                 = 5,471,500 SAR

Operating margin = (Operating result ÷ Total revenue) × 100
                 = (5,471,500 ÷ 30,245,000) × 100
                 = 18.09%
```

**Result**: 5,471,500 SAR operating result (18.09% margin)

### Example 2: Balance Sheet Equation Validation

**Context**: Validate fundamental accounting equation.

**Given Data**:
- Total assets: 26,700,000 SAR
- Total equity: 23,971,500 SAR
- Total liabilities (debt): 2,728,500 SAR

**Validation:**
```
Assets = Liabilities + Equity
26,700,000 = 2,728,500 + 23,971,500
26,700,000 = 26,700,000 ✓

Balance sheet balances correctly
```

**Result**: Balance sheet equation validated

### Example 3: Cash Flow from Operations (Indirect Method)

**Context**: Calculate operating cash flow using indirect method.

**Given Data**:
- Net result: 5,471,500 SAR
- Depreciation (non-cash): 818,500 SAR
- Working capital change: -500,000 SAR (increase in receivables)

**Calculation:**
```
Cash from operations = Net result + Depreciation + Working capital change
                     = 5,471,500 + 818,500 + (-500,000)
                     = 5,790,000 SAR

Note: Depreciation added back (non-cash expense)
Working capital increase = cash outflow (more receivables)
```

**Result**: 5,790,000 SAR cash from operations

### Example 4: Net Cash Change Reconciliation

**Context**: Reconcile cash flow activities to net cash change.

**Given Data**:
- Operating cash flow: 5,790,000 SAR
- Investing cash flow: -1,480,000 SAR (CapEx)
- Financing cash flow: 0 SAR

**Calculation:**
```
Net cash change = Operating + Investing + Financing
                = 5,790,000 + (-1,480,000) + 0
                = 4,310,000 SAR

Closing cash = Opening cash + Net cash change
             = 3,500,000 + 4,310,000
             = 7,810,000 SAR
```

**Result**: Net cash increase of 4,310,000 SAR, closing cash 7,810,000 SAR

### Example 5: Financial Ratios Calculation

**Context**: Calculate key financial ratios for analysis.

**Given Data** (from financial statements):
- Total revenue: 30,245,000 SAR
- Operating result: 5,471,500 SAR
- Net result: 5,471,500 SAR
- Total assets: 26,700,000 SAR
- Total equity: 23,971,500 SAR
- Current assets: 8,200,000 SAR
- Current liabilities: 2,728,500 SAR

**Calculation:**
```
Profitability:
Operating margin = (5,471,500 ÷ 30,245,000) × 100 = 18.09%
Net margin = (5,471,500 ÷ 30,245,000) × 100 = 18.09%
ROA = (5,471,500 ÷ 26,700,000) × 100 = 20.49%
ROE = (5,471,500 ÷ 23,971,500) × 100 = 22.83%

Liquidity:
Current ratio = 8,200,000 ÷ 2,728,500 = 3.01 (healthy, > 1.5 target)
Quick ratio = (8,200,000 - 0) ÷ 2,728,500 = 3.01 (no inventory)
Cash ratio = 2,500,000 ÷ 2,728,500 = 0.92

Leverage:
Debt-to-equity = 2,728,500 ÷ 23,971,500 = 0.11 (low leverage, < 0.5 target)
Debt-to-assets = 2,728,500 ÷ 26,700,000 = 0.10 (10% debt-financed)

Assessment: Strong profitability (18% margin), excellent liquidity (3.0 current ratio), minimal debt (0.11 debt-to-equity)
```

**Result**: All ratios within healthy ranges - financially strong position

## Integration Points

### Upstream Dependencies

1. **Module 13 (Budget Consolidation)**: Consolidated revenue, costs, and financial metrics
2. **Module 10 (Revenue Planning)**: Revenue line items by account code
3. **Module 11 (Cost Planning)**: Expense line items by account code
4. **Module 12 (CapEx Planning)**: Fixed assets, depreciation schedules, CapEx cash flows
5. **Module 1 (System Configuration)**: Chart of accounts (PCG and IFRS mapping)

### Downstream Consumers

1. **Module 15 (Statistical Analysis)**: Financial KPIs and trend analysis
2. **Module 16 (Dashboards)**: Visual financial performance dashboards
3. **Module 17 (Budget vs Actual)**: Comparison of budgeted vs actual financial statements
4. **External Systems**: Export to Odoo accounting system, AEFE reporting

### Data Flow

```
Module 13 (Consolidation) → Consolidated Budget
        ↓
Module 10 (Revenue) → Revenue Line Items
Module 11 (Costs) → Expense Line Items
Module 12 (CapEx) → Fixed Assets, Depreciation
        ↓
Financial Statements (Module 14)
┌───────┴────────┬──────────┐
↓                ↓          ↓
Income       Balance    Cash Flow
Statement    Sheet      Statement
↓                ↓          ↓
└────────────────┴──────────┘
        ↓
Financial Ratios & Analysis
        ↓
Dashboards (Module 16)
        ↓
Budget vs Actual (Module 17)
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions/:id/income-statement
GET    /api/v1/budget-versions/:id/balance-sheet
GET    /api/v1/budget-versions/:id/cash-flow-statement
GET    /api/v1/budget-versions/:id/financial-ratios
POST   /api/v1/generate-financial-statements
       Request: { budget_version_id, statement_type }
       Response: { income_statement, balance_sheet, cash_flow }
POST   /api/v1/export-to-odoo
       Request: { budget_version_id, format }
       Response: { export_status, file_url }
GET    /api/v1/compare-periods
       Request: { budget_version_ids: [id1, id2] }
       Response: { comparative_statements, variance_analysis }
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Income Statement Calculation
```typescript
const revenue = 30245000;
const expenses = 24773500;

const operatingResult = revenue - expenses;
expect(operatingResult).toBe(5471500);

const operatingMargin = (operatingResult / revenue) * 100;
expect(operatingMargin).toBeCloseTo(18.09, 2);
```

#### Scenario 2: Balance Sheet Equation
```typescript
const assets = 26700000;
const equity = 23971500;
const liabilities = 2728500;

expect(assets).toBe(equity + liabilities);
expect(assets).toBe(26700000);
```

#### Scenario 3: Cash Flow Reconciliation
```typescript
const netResult = 5471500;
const depreciation = 818500;
const workingCapitalChg = -500000;

const operatingCash = netResult + depreciation + workingCapitalChg;
expect(operatingCash).toBe(5790000);

const capex = 1480000;
const netCashChange = operatingCash - capex;
expect(netCashChange).toBe(4310000);
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: income_statement, balance_sheet, cash_flow_statement, financial_ratios tables |

## Future Enhancements (Phase 5-6)

1. **IFRS Conversion**: Automatic conversion from French PCG to IFRS for international reporting
2. **Multi-Period Comparison**: Side-by-side comparison of 3-5 years of financial statements
3. **Ratio Trend Analysis**: Visualize financial ratio trends over time
4. **Export to Odoo**: Automated export of approved budgets to Odoo accounting system
5. **AEFE Reporting**: Generate AEFE-specific financial reports and statistics
6. **Notes to Financial Statements**: Rich text notes and disclosures for each statement section
7. **Audit Trail**: Track all changes to financial statements with version history
8. **Scenario Comparison**: Compare financial statements across different budget scenarios
9. **Financial Dashboards**: Interactive dashboards with drill-down to account detail
10. **Automated Validation**: Cross-check financial statements for accuracy and compliance

## Notes

- **Phase 4 Scope**: Database foundation only - financial statement generation from consolidated budget
- **Business Logic**: IFRS conversion and multi-period comparison deferred to Phase 5-6
- **French PCG Primary**: All statements follow French accounting standards (legal requirement for French schools)
- **Strong Financial Position**: 18% operating margin, 3.0 current ratio, 0.11 debt-to-equity ratio
- **Cash Flow Positive**: 5.79M SAR operating cash flow, 4.31M SAR net cash increase
- **AEFE Compliance**: Financial statements align with AEFE reporting requirements
- **Data Source**: Financial statement structure and calculations based on French PCG and EFIR actual data
