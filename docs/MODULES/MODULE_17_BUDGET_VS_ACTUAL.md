# Module 17: Budget vs Actual Analysis

## Overview

Module 17 provides the foundation for budget variance analysis in the EFIR Budget Planning Application. This module enables import of actual financial data from external systems (primarily Odoo GL), comparison with budgeted amounts, variance calculation, and tracking of variance explanations for audit and management reporting.

**Layer**: Analysis Layer (Phase 4)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Odoo GL integration, variance calculation engine, variance reporting (Phase 5-6)

### Purpose

- Store actual financial data imported from Odoo general ledger
- Compare actual vs budgeted amounts by account code and period
- Calculate and track variances (amount and percentage)
- Classify variances as favorable, unfavorable, or neutral
- Capture management explanations for significant variances
- Support monthly, quarterly, and year-to-date variance analysis

### Key Design Decisions

1. **Actual Data Source**: Primary source is Odoo GL import, with support for manual entry and system calculations
2. **Period Granularity**: Monthly periods (1-12) for detailed tracking
3. **Account Code Alignment**: Uses same French PCG account codes as budget consolidation
4. **Variance Status**: Automatic classification based on account type (revenue vs expense)
5. **Explanation Tracking**: Separate table for variance explanations with root cause categorization

## Database Schema

### Tables

#### 1. actual_data

Actual financial data imported from external systems or manually entered.

**Columns:**
```sql
id                UUID PRIMARY KEY
fiscal_year       INTEGER NOT NULL              -- e.g., 2025
period            INTEGER NOT NULL              -- 1-12 (monthly)
account_code      VARCHAR(20) NOT NULL          -- French PCG account code
account_name_en   VARCHAR(200) NULL
account_name_fr   VARCHAR(200) NULL
amount_sar        NUMERIC(15, 2) NOT NULL       -- Actual amount in SAR
source            actualdatasource NOT NULL     -- ENUM: odoo_import, manual_entry, system_calc
import_batch_id   UUID NULL                     -- Reference to import batch
import_date       TIMESTAMPTZ NULL              -- When data was imported
notes             TEXT NULL                     -- Import notes or manual entry notes
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id     UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id     UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at        TIMESTAMPTZ NULL              -- Soft delete support
```

**Constraints:**
- Unique constraint on (fiscal_year, period, account_code) - one actual per account per period
- period must be between 1 and 12
- Check constraint: fiscal_year >= 2020 AND fiscal_year <= 2050
- Check constraint: account_code matches French PCG pattern (60xxx-77xxx)

**RLS Policies:**
- Admin: Full access (insert, update, delete)
- Manager: Can insert and update actual data
- All authenticated users: Read access to actual data

**Data Sources:**
- **Odoo Import**: Monthly GL export from Odoo accounting system (primary source)
- **Manual Entry**: Finance team manual adjustments or corrections
- **System Calc**: Calculated actuals (e.g., accruals, allocations)

#### 2. budget_vs_actual

Variance analysis comparing budget to actual amounts.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
fiscal_year           INTEGER NOT NULL
period                INTEGER NOT NULL           -- 1-12 monthly, 0 for annual
account_code          VARCHAR(20) NOT NULL       -- French PCG account code
account_name_en       VARCHAR(200) NULL
account_name_fr       VARCHAR(200) NULL
budget_amount_sar     NUMERIC(15, 2) NOT NULL
actual_amount_sar     NUMERIC(15, 2) NOT NULL
variance_sar          NUMERIC(15, 2) NOT NULL    -- Actual - Budget
variance_percent      NUMERIC(7, 2) NOT NULL     -- (Variance / Budget) × 100
variance_status       variancestatus NOT NULL    -- ENUM: favorable, unfavorable, neutral
is_revenue            BOOLEAN NOT NULL           -- true for revenue accounts (70xxx-77xxx)
ytd_budget_sar        NUMERIC(15, 2) NULL        -- Year-to-date budget
ytd_actual_sar        NUMERIC(15, 2) NULL        -- Year-to-date actual
ytd_variance_sar      NUMERIC(15, 2) NULL        -- YTD variance
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at            TIMESTAMPTZ NULL           -- Soft delete support
```

**Constraints:**
- Unique constraint on (budget_version_id, fiscal_year, period, account_code)
- period between 0 and 12 (0 = annual total, 1-12 = monthly)
- Check constraint: fiscal_year >= 2020 AND fiscal_year <= 2050
- variance_sar = actual_amount_sar - budget_amount_sar (enforced by calculation)
- variance_percent = (variance_sar / budget_amount_sar) × 100 (if budget > 0)

**RLS Policies:**
- Admin: Full access to all variance records
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Variance Status Logic:**

| Account Type | Variance Sign | Status |
|--------------|---------------|--------|
| Revenue (70xxx-77xxx) | Positive (actual > budget) | Favorable |
| Revenue | Negative (actual < budget) | Unfavorable |
| Expense (60xxx-68xxx) | Positive (actual > budget) | Unfavorable |
| Expense | Negative (actual < budget) | Favorable |

#### 3. variance_explanations

Management explanations for significant variances.

**Columns:**
```sql
id                      UUID PRIMARY KEY
budget_vs_actual_id     UUID NOT NULL FOREIGN KEY -> budget_vs_actual.id (CASCADE)
explanation_text        TEXT NOT NULL                 -- Detailed explanation
root_cause              VARCHAR(100) NOT NULL         -- Root cause category
action_plan             TEXT NULL                     -- Corrective action plan
responsible_party       VARCHAR(200) NULL             -- Department or person responsible
explained_date          DATE NOT NULL DEFAULT CURRENT_DATE
created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id           UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id           UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at              TIMESTAMPTZ NULL              -- Soft delete support
```

**Constraints:**
- Unique constraint on budget_vs_actual_id (one explanation per variance record)
- explanation_text must not be empty
- root_cause must not be empty

**RLS Policies:**
- Admin: Full access
- Manager: Can add/edit explanations for working budget versions
- Viewer: Read-only access to explanations for approved budgets

**Common Root Causes:**
- `enrollment_variance`: Enrollment higher/lower than projected
- `fee_adjustment`: Fee changes not reflected in budget
- `staffing_change`: Unplanned hiring or attrition
- `cost_inflation`: Higher than budgeted inflation rates
- `timing_difference`: Revenue/cost recognized in different period
- `one_time_expense`: Unbudgeted one-time cost
- `exchange_rate`: Currency fluctuation impact (AEFE costs)
- `efficiency_gain`: Cost savings from operational improvements
- `forecast_error`: Original budget assumption was incorrect

### Enums

#### ActualDataSource

```sql
CREATE TYPE efir_budget.actualdatasource AS ENUM (
    'odoo_import',      -- Imported from Odoo GL export
    'manual_entry',     -- Manually entered by finance team
    'system_calc'       -- Calculated by system (accruals, allocations)
);
```

#### VarianceStatus

```sql
CREATE TYPE efir_budget.variancestatus AS ENUM (
    'favorable',        -- Positive variance (revenue up or expense down)
    'unfavorable',      -- Negative variance (revenue down or expense up)
    'neutral',          -- Variance within threshold (e.g., ±5%)
    'not_applicable'    -- No variance analysis (e.g., no budget or no actual)
);
```

## Data Model

### Sample Actual Data Records

#### Odoo Import: Tuition Revenue (Account 70110)

```json
{
  "id": "act-001",
  "fiscal_year": 2025,
  "period": 9,
  "account_code": "70110",
  "account_name_en": "Tuition Revenue - Trimester 1",
  "account_name_fr": "Frais de Scolarité - Trimestre 1",
  "amount_sar": 22206000.00,
  "source": "odoo_import",
  "import_batch_id": "batch-2025-09-15",
  "import_date": "2025-09-15T08:00:00Z",
  "notes": "September GL export - Trimester 1 invoicing complete"
}
```

#### Manual Entry: Adjustment for Bad Debt

```json
{
  "id": "act-002",
  "fiscal_year": 2025,
  "period": 9,
  "account_code": "68700",
  "account_name_en": "Bad Debt Expense",
  "account_name_fr": "Dotations aux Provisions pour Créances Douteuses",
  "amount_sar": 125000.00,
  "source": "manual_entry",
  "import_batch_id": null,
  "import_date": null,
  "notes": "Manual adjustment for uncollectible tuition - 5 families",
  "created_by_id": "user-finance-manager"
}
```

### Sample Budget vs Actual Record

```json
{
  "id": "bva-001",
  "budget_version_id": "bv-2025-approved",
  "fiscal_year": 2025,
  "period": 9,
  "account_code": "70110",
  "account_name_en": "Tuition Revenue - Trimester 1",
  "account_name_fr": "Frais de Scolarité - Trimestre 1",
  "budget_amount_sar": 22515000.00,
  "actual_amount_sar": 22206000.00,
  "variance_sar": -309000.00,
  "variance_percent": -1.37,
  "variance_status": "unfavorable",
  "is_revenue": true,
  "ytd_budget_sar": 22515000.00,
  "ytd_actual_sar": 22206000.00,
  "ytd_variance_sar": -309000.00
}
```

### Sample Variance Explanation

```json
{
  "id": "exp-001",
  "budget_vs_actual_id": "bva-001",
  "explanation_text": "Tuition revenue variance of -309,000 SAR (-1.37%) due to lower than projected enrollment in 6ème and 5ème. Budgeted enrollment was 1,255 students, actual enrollment is 1,234 students (21 fewer students). Average tuition per student: 18,000 SAR. Variance calculation: 21 × 18,000 = 378,000 SAR shortfall, partially offset by higher enrollment in Lycée levels (+3 students at premium tuition rates).",
  "root_cause": "enrollment_variance",
  "action_plan": "Marketing campaign planned for January 2026 to attract new students for Trimester 2. Early bird discount (10%) offered for new enrollments before December 15. Outreach to French expat community through embassy and cultural center.",
  "responsible_party": "Admissions Department",
  "explained_date": "2025-09-20"
}
```

## Business Rules

### Actual Data Rules

1. **Unique Period Data**: One actual amount per account code per period per fiscal year
2. **Period Validation**: Period must be 1-12 for monthly data
3. **Account Code Alignment**: Must use same French PCG codes as budget (60xxx-77xxx)
4. **Import Batching**: All Odoo imports tagged with import_batch_id for tracking
5. **Manual Entry Audit**: Manual entries require notes explaining the reason
6. **Overwrite Protection**: Importing new actuals for same period overwrites previous (with audit trail)

### Budget vs Actual Rules

1. **One Record Per Comparison**: Unique (budget_version_id, fiscal_year, period, account_code)
2. **Automatic Calculation**:
   - variance_sar = actual_amount_sar - budget_amount_sar
   - variance_percent = (variance_sar ÷ budget_amount_sar) × 100
3. **Variance Status Logic**:
   - Revenue accounts (70xxx-77xxx): Positive variance = Favorable
   - Expense accounts (60xxx-68xxx): Negative variance = Favorable
4. **Period 0 for Annual**: Period 0 used for full fiscal year totals
5. **YTD Calculations**: Year-to-date fields accumulate from period 1 to current period
6. **Version Linking**: Variance records linked to specific budget version for comparison

### Variance Explanation Rules

1. **Significant Variance Threshold**: Explanations required for:
   - Absolute variance > 100,000 SAR, OR
   - Percentage variance > ±10%
2. **One Explanation Per Variance**: Unique constraint on budget_vs_actual_id
3. **Root Cause Required**: Must select from predefined root cause categories
4. **Action Plan for Unfavorable**: Unfavorable variances require action plan
5. **Responsible Party**: Must identify department or person accountable
6. **Timely Explanation**: Explanations should be provided within 10 business days of variance identification

## Calculation Examples

### Example 1: Tuition Revenue Variance

**Budget (Account 70110 - Tuition T1):**
- Enrollment: 1,255 students
- Average tuition: 18,000 SAR
- Budgeted revenue: 1,255 × 18,000 = 22,515,000 SAR

**Actual (Period 9 - September):**
- Enrollment: 1,234 students
- Average tuition: 18,000 SAR
- Actual revenue: 22,206,000 SAR

**Variance Calculation:**
```python
budget_amount = 22_515_000.00
actual_amount = 22_206_000.00

variance_sar = actual_amount - budget_amount
# = 22,206,000 - 22,515,000
# = -309,000 SAR

variance_percent = (variance_sar / budget_amount) * 100
# = (-309,000 / 22,515,000) × 100
# = -1.37%

# Status determination
is_revenue = True  # Account 70110 is revenue
if is_revenue:
    if variance_sar > 0:
        variance_status = "favorable"
    else:
        variance_status = "unfavorable"  # ← This case
# Status: Unfavorable (revenue below budget)
```

**Result:**
- Variance: -309,000 SAR (-1.37%)
- Status: Unfavorable
- Root Cause: enrollment_variance (21 fewer students)

### Example 2: Personnel Cost Variance

**Budget (Account 64110 - Teaching Salaries):**
- Budgeted FTE: 102.8
- Average salary: 15,000 SAR/month
- Budgeted cost (September): 102.8 × 15,000 = 1,542,000 SAR

**Actual (Period 9 - September):**
- Actual FTE: 98.5 (4 unfilled positions)
- Actual cost: 1,477,500 SAR

**Variance Calculation:**
```python
budget_amount = 1_542_000.00
actual_amount = 1_477_500.00

variance_sar = actual_amount - budget_amount
# = 1,477,500 - 1,542,000
# = -64,500 SAR

variance_percent = (variance_sar / budget_amount) * 100
# = (-64,500 / 1,542,000) × 100
# = -4.18%

# Status determination
is_revenue = False  # Account 64110 is expense
if not is_revenue:
    if variance_sar < 0:  # Actual < Budget for expense
        variance_status = "favorable"  # ← This case
    else:
        variance_status = "unfavorable"
# Status: Favorable (expense below budget)
```

**Result:**
- Variance: -64,500 SAR (-4.18%)
- Status: Favorable
- Root Cause: staffing_change (recruitment delays)

### Example 3: Year-to-Date Variance

**Scenario**: Calculate YTD variance for Operating Costs (Account 62300) as of Period 6 (June)

**Monthly Data (Jan-Jun):**

| Period | Budget SAR | Actual SAR | Variance SAR |
|--------|------------|------------|--------------|
| 1      | 85,000     | 87,200     | +2,200       |
| 2      | 85,000     | 83,500     | -1,500       |
| 3      | 85,000     | 89,300     | +4,300       |
| 4      | 90,000     | 91,800     | +1,800       |
| 5      | 90,000     | 88,200     | -1,800       |
| 6      | 90,000     | 92,500     | +2,500       |

**YTD Calculation (June):**
```python
ytd_budget_sar = sum([85000, 85000, 85000, 90000, 90000, 90000])
# = 525,000 SAR

ytd_actual_sar = sum([87200, 83500, 89300, 91800, 88200, 92500])
# = 532,500 SAR

ytd_variance_sar = ytd_actual_sar - ytd_budget_sar
# = 532,500 - 525,000
# = +7,500 SAR

ytd_variance_percent = (ytd_variance_sar / ytd_budget_sar) * 100
# = (7,500 / 525,000) × 100
# = +1.43%

# Status: Unfavorable (expense above budget)
```

**Result:**
- YTD Variance: +7,500 SAR (+1.43%)
- Status: Unfavorable
- Root Cause: cost_inflation (utilities and supplies)

## Integration Points

### Upstream Dependencies

1. **Odoo General Ledger**: Primary source for actual data (monthly GL export)
2. **budget_consolidations**: Source for budgeted amounts by account code
3. **budget_versions**: Parent table for variance analysis versioning

### Downstream Dependencies

1. **dashboard_widgets**: Variance data displayed in dashboard variance tables
2. **financial_statements**: Actual data used in financial statement generation
3. **Reports**: Variance reports for management review

### External Systems

**Odoo Integration (Future Phase 5-6):**
```
1. Monthly GL Export from Odoo
   - Format: CSV or Excel
   - Frequency: Monthly (within 5 business days of month end)
   - Fields: account_code, account_name, debit, credit, balance, period

2. Data Transformation
   - Map Odoo account codes to EFIR account codes
   - Convert debits/credits to signed amounts (SAR)
   - Validate data completeness and accuracy

3. Import Process
   - Create import_batch_id (UUID)
   - Insert actual_data records with source='odoo_import'
   - Trigger variance calculation for all accounts
   - Generate variance report for finance manager review

4. Error Handling
   - Log unmapped account codes
   - Alert on missing periods or accounts
   - Validate amount reasonability (outlier detection)
```

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
# Actual Data
GET    /api/v1/actuals                         # List actual data (with filters)
GET    /api/v1/actuals/:fiscal_year/:period    # Get actuals for specific period
POST   /api/v1/actuals/import                  # Import actual data (Odoo batch)
POST   /api/v1/actuals/manual                  # Manual entry of actual data
PUT    /api/v1/actuals/:id                     # Update actual data record
DELETE /api/v1/actuals/:id                     # Soft delete actual data

# Budget vs Actual
GET    /api/v1/variance/:budget_version_id                    # Get all variances for budget
GET    /api/v1/variance/:budget_version_id/:period            # Get variances for specific period
POST   /api/v1/variance/:budget_version_id/calculate          # Calculate variances
GET    /api/v1/variance/:budget_version_id/ytd                # Get YTD variances
GET    /api/v1/variance/:budget_version_id/significant        # Get significant variances only

# Variance Explanations
GET    /api/v1/variance/:id/explanation                       # Get explanation for variance
POST   /api/v1/variance/:id/explanation                       # Add explanation
PUT    /api/v1/variance/:id/explanation                       # Update explanation
DELETE /api/v1/variance/:id/explanation                       # Delete explanation
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify SQLAlchemy model definitions and relationships
2. **Constraint Tests**: Test unique constraints, foreign keys, check constraints
3. **Enum Tests**: Verify ActualDataSource and VarianceStatus enum values
4. **Calculation Tests**: Verify variance calculation formulas

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for all user roles
2. **Cascade Delete Tests**: Ensure proper cascade behavior
3. **Import Tests**: Test Odoo data import and transformation
4. **Variance Calculation Tests**: End-to-end variance calculation

### Test Scenarios

#### Scenario 1: Import Actual Data from Odoo

```python
def test_import_odoo_actuals():
    """Test importing actual data from Odoo GL export."""
    import_batch_id = str(uuid.uuid4())

    actual = ActualData(
        fiscal_year=2025,
        period=9,
        account_code="70110",
        account_name_en="Tuition Revenue - T1",
        account_name_fr="Frais de Scolarité - T1",
        amount_sar=Decimal("22206000.00"),
        source=ActualDataSource.ODOO_IMPORT,
        import_batch_id=import_batch_id,
        import_date=datetime.now(timezone.utc),
        notes="September GL export"
    )
    db.session.add(actual)
    db.session.commit()

    assert actual.id is not None
    assert actual.source == ActualDataSource.ODOO_IMPORT
```

#### Scenario 2: Calculate Variance

```python
def test_calculate_variance():
    """Test variance calculation for budget vs actual."""
    budget_version = create_approved_budget_version()

    # Create budget amount (from budget_consolidations)
    budget_amount = Decimal("22515000.00")

    # Create actual amount
    actual = create_actual_data(
        fiscal_year=2025,
        period=9,
        account_code="70110",
        amount_sar=Decimal("22206000.00")
    )

    # Calculate variance
    variance_sar = actual.amount_sar - budget_amount
    variance_percent = (variance_sar / budget_amount) * 100

    # Determine status (revenue account)
    is_revenue = actual.account_code.startswith("7")
    if is_revenue:
        variance_status = VarianceStatus.FAVORABLE if variance_sar > 0 else VarianceStatus.UNFAVORABLE
    else:
        variance_status = VarianceStatus.FAVORABLE if variance_sar < 0 else VarianceStatus.UNFAVORABLE

    # Store variance
    bva = BudgetVsActual(
        budget_version_id=budget_version.id,
        fiscal_year=2025,
        period=9,
        account_code="70110",
        budget_amount_sar=budget_amount,
        actual_amount_sar=actual.amount_sar,
        variance_sar=variance_sar,
        variance_percent=variance_percent,
        variance_status=variance_status,
        is_revenue=is_revenue
    )
    db.session.add(bva)
    db.session.commit()

    assert bva.variance_sar == Decimal("-309000.00")
    assert bva.variance_percent == Decimal("-1.37")
    assert bva.variance_status == VarianceStatus.UNFAVORABLE
```

#### Scenario 3: Add Variance Explanation

```python
def test_add_variance_explanation():
    """Test adding explanation for significant variance."""
    bva = create_budget_vs_actual_record()

    explanation = VarianceExplanation(
        budget_vs_actual_id=bva.id,
        explanation_text="Enrollment variance: 21 fewer students than budgeted",
        root_cause="enrollment_variance",
        action_plan="Marketing campaign for Trimester 2 enrollment",
        responsible_party="Admissions Department"
    )
    db.session.add(explanation)
    db.session.commit()

    assert explanation.id is not None
    assert explanation.root_cause == "enrollment_variance"
```

#### Scenario 4: YTD Variance Calculation

```python
def test_ytd_variance_calculation():
    """Test year-to-date variance calculation."""
    budget_version = create_approved_budget_version()

    # Create monthly variances (Jan-Jun)
    monthly_data = [
        (1, 85000, 87200),
        (2, 85000, 83500),
        (3, 85000, 89300),
        (4, 90000, 91800),
        (5, 90000, 88200),
        (6, 90000, 92500)
    ]

    for period, budget, actual in monthly_data:
        create_budget_vs_actual(
            budget_version_id=budget_version.id,
            fiscal_year=2025,
            period=period,
            account_code="62300",
            budget_amount_sar=budget,
            actual_amount_sar=actual
        )

    # Calculate YTD for June (period 6)
    ytd_budget = sum([b for _, b, _ in monthly_data])
    ytd_actual = sum([a for _, _, a in monthly_data])
    ytd_variance = ytd_actual - ytd_budget

    # Update period 6 record with YTD values
    bva_june = db.session.query(BudgetVsActual).filter_by(
        budget_version_id=budget_version.id,
        period=6,
        account_code="62300"
    ).first()

    bva_june.ytd_budget_sar = Decimal(str(ytd_budget))
    bva_june.ytd_actual_sar = Decimal(str(ytd_actual))
    bva_june.ytd_variance_sar = Decimal(str(ytd_variance))
    db.session.commit()

    assert bva_june.ytd_variance_sar == Decimal("7500.00")
```

#### Scenario 5: RLS - Manager Can Update Actuals

```python
def test_rls_manager_update_actuals():
    """Test that managers can insert and update actual data."""
    # Simulate manager role
    set_user_role("manager")

    # Manager can insert actual data
    actual = ActualData(
        fiscal_year=2025,
        period=9,
        account_code="70110",
        amount_sar=Decimal("22206000.00"),
        source=ActualDataSource.MANUAL_ENTRY,
        notes="Manual adjustment"
    )
    db.session.add(actual)
    db.session.commit()

    assert actual.id is not None

    # Manager can update
    actual.amount_sar = Decimal("22210000.00")
    db.session.commit()

    refreshed = db.session.query(ActualData).filter_by(id=actual.id).first()
    assert refreshed.amount_sar == Decimal("22210000.00")
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | Claude (Phase 4) | Initial database schema implementation: actual_data, budget_vs_actual, variance_explanations tables, RLS policies, migration scripts |

## Future Enhancements (Phase 5-6)

1. **Odoo GL Integration**: Automated monthly import from Odoo general ledger
2. **Variance Calculation Engine**: Automatic variance calculation on actual data import
3. **Alert System**: Notify managers when significant variances are detected
4. **Variance Trend Analysis**: Track variance patterns over time (recurring issues)
5. **Forecast Revision**: Update budget forecasts based on actual performance
6. **Drill-Down Reports**: Detailed variance analysis by department, program, level
7. **Root Cause Analytics**: AI-powered root cause suggestion based on historical patterns
8. **Action Plan Tracking**: Track completion of corrective action plans
9. **Export to Excel**: Variance reports with charts and commentary
10. **AEFE Reporting**: Submit variance explanations to AEFE for significant deviations

## Notes

- **Phase 4 Scope**: This module currently implements only the database foundation (tables, constraints, RLS policies, migration)
- **Business Logic**: Odoo integration, variance calculation engine, and reporting will be implemented in Phases 5-6
- **French PCG Alignment**: All account codes follow French Plan Comptable Général for AEFE compliance
- **Monthly Granularity**: Supports monthly variance tracking (periods 1-12) with YTD calculations
- **Audit Trail**: All actual data imports and manual entries tracked with source, batch ID, and timestamps
- **Management by Exception**: Focus on significant variances (>100K SAR or >±10%) requiring explanations
