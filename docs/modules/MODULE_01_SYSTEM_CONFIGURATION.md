# Module 1: System Configuration

## Overview

Module 1 establishes the foundational configuration for the entire EFIR Budget Planning Application. It defines the organizational structure, academic calendar, fiscal calendar, chart of accounts (French PCG), cost centers, and core system parameters. All other modules depend on the master data defined in this module.

**Layer**: Configuration Layer (Phase 1)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Business logic, configuration UI, API endpoints (Phase 5-6)

### Purpose

- Define school profile and AEFE status
- Establish academic structure (cycles and levels) for French education system
- Configure fiscal and academic calendars
- Define chart of accounts following French Plan Comptable Général (PCG)
- Establish cost centers with budget holder assignments
- Manage currency settings and exchange rates

### Key Design Decisions

1. **French Education Structure**: Hardcoded 4-cycle structure (Maternelle, Élémentaire, Collège, Lycée) with standard French levels
2. **French PCG Compliance**: Chart of accounts follows French accounting standards with IFRS mapping
3. **Dual Currency Support**: Primary currency SAR, secondary EUR for AEFE cost calculations
4. **Version Control**: Configuration parameters are versioned to support historical budget analysis
5. **Cost Center Hierarchy**: Aligned with academic cycles plus administrative functions

## Database Schema

### Tables

#### 1. system_config

Global system configuration and school profile.

**Columns:**
```sql
id                    UUID PRIMARY KEY
school_id             UUID NOT NULL UNIQUE
school_name           VARCHAR(200) NOT NULL
school_name_fr        VARCHAR(200) NOT NULL
aefe_status           aefestatus NOT NULL        -- ENUM: direct, conventionne, homologue
fiscal_year_start     INTEGER NOT NULL           -- Month (1-12), typically 1 for January
academic_year_start   INTEGER NOT NULL           -- Month (1-12), typically 9 for September
base_currency         VARCHAR(3) NOT NULL DEFAULT 'SAR'
secondary_currency    VARCHAR(3) NOT NULL DEFAULT 'EUR'
exchange_rate_sar_eur NUMERIC(10, 6) NOT NULL    -- SAR to EUR rate (e.g., 0.24)
max_capacity          INTEGER NOT NULL           -- Maximum student capacity (~1,875 for EFIR)
is_active             BOOLEAN NOT NULL DEFAULT true
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- fiscal_year_start between 1 and 12
- academic_year_start between 1 and 12
- exchange_rate_sar_eur > 0
- max_capacity > 0
- Only one active system_config record at a time

**RLS Policies:**
- Admin: Full access to system configuration
- Manager: Read-only access to system configuration
- Viewer: Read-only access to system configuration

**Indexes:**
- Primary key on id
- Unique index on school_id

#### 2. academic_structure

Defines academic cycles and levels for French education system.

**Columns:**
```sql
id                UUID PRIMARY KEY
cycle_name        VARCHAR(50) NOT NULL        -- Maternelle, Élémentaire, Collège, Lycée
cycle_name_fr     VARCHAR(50) NOT NULL        -- Same (French native)
cycle_order       INTEGER NOT NULL            -- Display order: 1-4
level_code        VARCHAR(20) NOT NULL        -- PS, MS, GS, CP, CE1, ..., Terminale
level_name        VARCHAR(100) NOT NULL       -- Full level name
level_name_fr     VARCHAR(100) NOT NULL       -- French name
level_order       INTEGER NOT NULL            -- Order within cycle
is_primary        BOOLEAN NOT NULL            -- True for Maternelle + Élémentaire
is_secondary      BOOLEAN NOT NULL            -- True for Collège + Lycée
is_active         BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- Unique (cycle_name, level_code)
- cycle_order between 1 and 4
- level_order > 0
- Exactly one of is_primary or is_secondary must be true

**RLS Policies:**
- All authenticated users can read academic structure
- Only admins can modify academic structure

**Indexes:**
- Primary key on id
- Index on (cycle_name, level_order) for ordered queries
- Index on level_code for lookups

#### 3. chart_of_accounts

French Plan Comptable Général (PCG) account definitions with IFRS mapping.

**Columns:**
```sql
id                UUID PRIMARY KEY
account_code      VARCHAR(20) NOT NULL UNIQUE   -- e.g., 70110, 64110, 61310
account_name      VARCHAR(200) NOT NULL         -- French name
account_name_en   VARCHAR(200) NOT NULL         -- English translation
account_type      accounttype NOT NULL          -- ENUM: asset, liability, equity, revenue, expense
account_class     INTEGER NOT NULL              -- PCG Class (1-7)
parent_code       VARCHAR(20) NULL              -- Hierarchical parent
ifrs_mapping      VARCHAR(100) NULL             -- IFRS category mapping
is_active         BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- account_code follows PCG pattern (2-6 digits)
- account_class between 1 and 7
- parent_code must exist in chart_of_accounts if not null

**RLS Policies:**
- All authenticated users can read chart of accounts
- Only admins can create/update account codes

**Indexes:**
- Primary key on id
- Unique index on account_code
- Index on account_type for filtering
- Index on account_class for grouping

#### 4. cost_centers

Budget allocation units aligned with organizational structure.

**Columns:**
```sql
id                    UUID PRIMARY KEY
code                  VARCHAR(20) NOT NULL UNIQUE  -- MAT, ELEM, COL, LYC, ADM, FAC, IT
name                  VARCHAR(100) NOT NULL
name_fr               VARCHAR(100) NOT NULL
description           TEXT NULL
budget_holder_id      UUID NOT NULL FOREIGN KEY -> auth.users.id (RESTRICT)
parent_cost_center_id UUID NULL FOREIGN KEY -> cost_centers.id (SET NULL)
is_active             BOOLEAN NOT NULL DEFAULT true
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- Unique code per cost center
- budget_holder_id must be a valid user (restrict delete if cost center exists)

**RLS Policies:**
- Admin: Full access to all cost centers
- Manager: Read access to all, write access to assigned cost centers
- Viewer: Read-only access to all cost centers

**Indexes:**
- Primary key on id
- Unique index on code
- Index on budget_holder_id for user lookups

#### 5. budget_periods

Fiscal and academic period definitions for budget planning.

**Columns:**
```sql
id                UUID PRIMARY KEY
period_name       VARCHAR(100) NOT NULL          -- e.g., "FY2025", "AY2025-2026"
period_type       periodtype NOT NULL            -- ENUM: fiscal, academic, custom
start_date        DATE NOT NULL
end_date          DATE NOT NULL
is_active         BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- end_date > start_date
- No overlapping periods of same type

**RLS Policies:**
- All authenticated users can read budget periods
- Only admins can create/modify periods

**Indexes:**
- Primary key on id
- Index on (start_date, end_date) for range queries

### Enums

#### AEFEStatus
```sql
CREATE TYPE efir_budget.aefestatus AS ENUM (
    'direct',         -- AEFE Direct (fully managed by AEFE)
    'conventionne',   -- Conventionné (partnership agreement - EFIR status)
    'homologue'       -- Homologué (accredited only)
);
```

#### AccountType
```sql
CREATE TYPE efir_budget.accounttype AS ENUM (
    'asset',          -- Class 1-2: Assets
    'liability',      -- Class 1: Liabilities
    'equity',         -- Class 1: Equity
    'expense',        -- Class 6: Expenses (charges)
    'revenue'         -- Class 7: Revenue (produits)
);
```

#### PeriodType
```sql
CREATE TYPE efir_budget.periodtype AS ENUM (
    'fiscal',         -- Calendar year (January-December)
    'academic',       -- Academic year (September-June)
    'custom'          -- Custom period definition
);
```

## Data Model

### Sample System Config Record

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "school_id": "123e4567-e89b-12d3-a456-426614174000",
  "school_name": "École Française Internationale de Riyad",
  "school_name_fr": "École Française Internationale de Riyad",
  "aefe_status": "conventionne",
  "fiscal_year_start": 1,
  "academic_year_start": 9,
  "base_currency": "SAR",
  "secondary_currency": "EUR",
  "exchange_rate_sar_eur": 0.24,
  "max_capacity": 1875,
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z"
}
```

### Sample Academic Structure Records

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440001",
    "cycle_name": "Maternelle",
    "cycle_name_fr": "Maternelle",
    "cycle_order": 1,
    "level_code": "PS",
    "level_name": "Petite Section",
    "level_name_fr": "Petite Section",
    "level_order": 1,
    "is_primary": true,
    "is_secondary": false
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440002",
    "cycle_name": "Collège",
    "cycle_name_fr": "Collège",
    "cycle_order": 3,
    "level_code": "6ème",
    "level_name": "Sixième",
    "level_name_fr": "Sixième",
    "level_order": 1,
    "is_primary": false,
    "is_secondary": true
  }
]
```

### Sample Chart of Accounts Records

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440001",
    "account_code": "70110",
    "account_name": "Scolarité Trimestre 1",
    "account_name_en": "Tuition Quarter 1",
    "account_type": "revenue",
    "account_class": 7,
    "parent_code": "701",
    "ifrs_mapping": "Tuition Revenue"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440002",
    "account_code": "64110",
    "account_name": "Salaires enseignement",
    "account_name_en": "Teaching Salaries",
    "account_type": "expense",
    "account_class": 6,
    "parent_code": "641",
    "ifrs_mapping": "Personnel Expenses"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440003",
    "account_code": "64800",
    "account_name": "AEFE salaires résidents",
    "account_name_en": "AEFE Resident Salaries (PRRD)",
    "account_type": "expense",
    "account_class": 6,
    "parent_code": "648",
    "ifrs_mapping": "Personnel Expenses"
  }
]
```

### Sample Cost Center Records

```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440001",
    "code": "MAT",
    "name": "Maternelle",
    "name_fr": "Maternelle",
    "description": "Preschool division (PS, MS, GS)",
    "budget_holder_id": "user-123-456",
    "parent_cost_center_id": null
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440002",
    "code": "COL",
    "name": "Collège",
    "name_fr": "Collège",
    "description": "Middle school division (6ème to 3ème)",
    "budget_holder_id": "user-789-012",
    "parent_cost_center_id": null
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440003",
    "code": "ADM",
    "name": "Administration",
    "name_fr": "Administration",
    "description": "Administrative and support services",
    "budget_holder_id": "user-345-678",
    "parent_cost_center_id": null
  }
]
```

## Business Rules

### System Configuration Rules

1. **Single Active Config**: Only one system_config record can be active at any time
2. **AEFE Status**: EFIR is "Conventionné" (partnership agreement with AEFE)
3. **Calendar Validation**: Fiscal year starts January (month 1), Academic year starts September (month 9)
4. **Capacity Limit**: Maximum student capacity is approximately 1,875 students
5. **Exchange Rate**: SAR to EUR exchange rate must be updated regularly (typically ~0.24)

### Academic Structure Rules

1. **Standard French Structure**: 4 cycles with fixed levels
   - Maternelle: PS, MS, GS (3 levels)
   - Élémentaire: CP, CE1, CE2, CM1, CM2 (5 levels)
   - Collège: 6ème, 5ème, 4ème, 3ème (4 levels)
   - Lycée: 2nde, 1ère, Terminale (3 levels)
2. **Primary/Secondary Classification**: Maternelle + Élémentaire = Primary, Collège + Lycée = Secondary
3. **Level Ordering**: Levels must be ordered sequentially within each cycle
4. **Immutability**: Academic structure should not be modified once budget planning begins

### Chart of Accounts Rules

1. **PCG Compliance**: Account codes must follow French Plan Comptable Général numbering
   - Class 1: Capitaux (Equity + Long-term Liabilities)
   - Class 2: Immobilisations (Fixed Assets)
   - Class 3: Stocks (Inventory - not used for schools)
   - Class 4: Tiers (Receivables/Payables)
   - Class 5: Financiers (Cash/Bank)
   - Class 6: Charges (Expenses)
   - Class 7: Produits (Revenue)
2. **Revenue Accounts**: 70xxx for tuition, 73xxx for other educational revenue
3. **Expense Accounts**: 64xxx for personnel, 61xxx for facilities, 60xxx for supplies
4. **IFRS Mapping**: Required for international financial reporting
5. **Hierarchical Structure**: Accounts can have parent accounts for aggregation

### Cost Center Rules

1. **Budget Holder Assignment**: Every cost center must have an assigned budget holder (user)
2. **Unique Codes**: Cost center codes must be unique (MAT, ELEM, COL, LYC, ADM, FAC, IT)
3. **Cycle Alignment**: Primary cost centers align with academic cycles
4. **Prevent Orphaned Budgets**: Cannot delete budget holder if cost centers are assigned
5. **Hierarchical Structure**: Cost centers can have parent relationships for rollup reporting

### Budget Period Rules

1. **Fiscal Year**: January 1 to December 31 (calendar year)
2. **Academic Year**: September to June (10 months of instruction)
3. **No Overlap**: Budget periods of the same type cannot overlap
4. **Sequential Dates**: end_date must be after start_date
5. **Period Closure**: Periods can be closed to prevent further modifications

### Validation Rules

1. **Exchange Rate Frequency**: Exchange rates should be updated monthly or as needed for AEFE reporting
2. **Capacity Check**: Total enrollment across all levels cannot exceed max_capacity
3. **AEFE Consistency**: AEFE status must match actual partnership agreement
4. **Bilingual Names**: All configuration entities must have both French and English names
5. **Audit Trail**: All configuration changes must be logged with user and timestamp

## Calculation Examples

### Example 1: Exchange Rate Conversion (SAR to EUR)

**Context**: Convert AEFE PRRD contribution from SAR to EUR for reporting.

**Given Data:**
- PRRD cost per AEFE teacher: 41,863 EUR
- Current exchange rate: 0.24 SAR/EUR (1 SAR = 0.24 EUR)

**Formula:**
```
Amount_EUR = Amount_SAR × Exchange_Rate
Amount_SAR = Amount_EUR ÷ Exchange_Rate
```

**Calculation:**
```
PRRD in EUR: 41,863 EUR (given)
Convert to SAR: 41,863 ÷ 0.24 = 174,429 SAR

Verification:
174,429 SAR × 0.24 = 41,863 EUR ✓
```

**Result:** Each AEFE resident teacher costs the school 174,429 SAR per year (PRRD contribution).

### Example 2: Fiscal Period Calculation

**Context**: Calculate the number of budget periods within a fiscal year.

**Given Data:**
- Fiscal year start: January (month 1)
- Academic year start: September (month 9)
- Fiscal year: 2025 (January 1, 2025 to December 31, 2025)

**Fiscal Year Breakdown:**
```
Period 1: January-June (6 months) - Continuation of AY 2024-2025
Summer: July-August (2 months) - Minimal operations
Period 2: September-December (4 months) - Start of AY 2025-2026
```

**Budget Distribution Pattern:**
- Period 1 (Jan-Jun): 40% of annual budget (academic activity + operations)
- Summer (Jul-Aug): 10% of annual budget (reduced operations, maintenance)
- Period 2 (Sep-Dec): 50% of annual budget (new academic year launch, enrollment peak)

**Result:** Fiscal year contains 12 months split across 2 academic years, requiring careful budget allocation.

### Example 3: Account Code Hierarchy

**Context**: Demonstrate PCG account hierarchy for expense aggregation.

**Given Account Structure:**
```
64000: Personnel Expenses (Parent)
  ├─ 641xx: Teaching Staff
  │   ├─ 64110: Teaching Salaries (local)
  │   ├─ 64120: Teaching Benefits
  │   └─ 64130: Teaching Social Charges
  ├─ 648xx: AEFE Costs
  │   ├─ 64800: AEFE PRRD (Resident Salaries)
  │   └─ 64801: AEFE Licensing Fees
  └─ 642xx: Administrative Staff
      ├─ 64210: Admin Salaries
      └─ 64220: Admin Benefits
```

**Aggregation Calculation:**
```
Teaching Staff Total (641xx):
  64110: 16,355,839 SAR
  64120: 2,450,000 SAR
  64130: 3,200,000 SAR
  ────────────────────────
  641xx: 22,005,839 SAR

AEFE Costs Total (648xx):
  64800: 7,080,587 SAR (PRRD)
  64801: 4,005,266 SAR (Licensing)
  ────────────────────────
  648xx: 11,085,853 SAR

Administrative Staff (642xx):
  64210: 5,272,255 SAR
  64220: 1,200,000 SAR
  ────────────────────────
  642xx: 6,472,255 SAR

Total Personnel Expenses (64000):
  641xx + 648xx + 642xx = 39,563,947 SAR
```

**Result:** Hierarchical account structure enables flexible reporting at multiple aggregation levels (detail codes, 5-digit, 4-digit, 3-digit, class level).

## Integration Points

### Upstream Dependencies

**None** - Module 1 is the foundation module with no upstream dependencies.

### Downstream Consumers

1. **Module 2 (Class Size Parameters)**: Uses academic structure (cycles, levels)
2. **Module 3 (Subject Hours)**: Uses academic structure for secondary curriculum
3. **Module 4 (Teacher Costs)**: Uses exchange rates for AEFE cost conversions
4. **Module 5 (Fee Structure)**: Uses academic structure for fee matrix
5. **Module 7 (Enrollment Planning)**: Uses academic structure and capacity limits
6. **Module 8 (DHG Workforce)**: Uses primary/secondary classification
7. **Module 10 (Revenue Planning)**: Uses chart of accounts for revenue mapping
8. **Module 11 (Cost Planning)**: Uses chart of accounts and cost centers
9. **Module 13 (Budget Consolidation)**: Uses budget periods and cost centers
10. **Module 14 (Financial Statements)**: Uses chart of accounts and IFRS mapping

### Data Flow

```
System Config → Academic Structure → All Planning Modules
              ↓
        Exchange Rates → AEFE Cost Calculations (Module 4, 11)
              ↓
   Chart of Accounts → Cost/Revenue Planning → Financial Statements
              ↓
      Cost Centers → Budget Allocation → Reporting
```

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
# System Configuration
GET    /api/v1/system-config                  # Get active system configuration
PUT    /api/v1/system-config                  # Update system configuration (admin only)
PATCH  /api/v1/system-config/exchange-rate    # Update exchange rate

# Academic Structure
GET    /api/v1/academic-structure              # Get all cycles and levels
GET    /api/v1/academic-structure/cycles       # Get cycles only
GET    /api/v1/academic-structure/levels/:code # Get specific level details

# Chart of Accounts
GET    /api/v1/chart-of-accounts               # List all accounts
GET    /api/v1/chart-of-accounts/:code         # Get account by code
POST   /api/v1/chart-of-accounts               # Create new account (admin only)
PUT    /api/v1/chart-of-accounts/:code         # Update account (admin only)
GET    /api/v1/chart-of-accounts/hierarchy     # Get hierarchical account tree

# Cost Centers
GET    /api/v1/cost-centers                    # List all cost centers
GET    /api/v1/cost-centers/:code              # Get cost center by code
POST   /api/v1/cost-centers                    # Create cost center (admin only)
PUT    /api/v1/cost-centers/:code              # Update cost center
GET    /api/v1/cost-centers/by-holder/:user_id # Get cost centers by budget holder

# Budget Periods
GET    /api/v1/budget-periods                  # List all periods
GET    /api/v1/budget-periods/active           # Get active period
POST   /api/v1/budget-periods                  # Create period (admin only)
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify SQLAlchemy model definitions and relationships
2. **Enum Tests**: Verify AEFEStatus, AccountType, PeriodType enum values
3. **Constraint Tests**: Test unique constraints, foreign keys, and check constraints

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for all user roles
2. **Exchange Rate Updates**: Test exchange rate update workflow
3. **Account Hierarchy**: Test parent-child account relationships

### Test Scenarios

#### Scenario 1: Create System Configuration

**Objective:** Verify system configuration record creation with all required fields.

**Test Data:**
```typescript
const systemConfig = {
  school_id: uuid(),
  school_name: "École Française Internationale de Riyad",
  school_name_fr: "École Française Internationale de Riyad",
  aefe_status: AEFEStatus.CONVENTIONNE,
  fiscal_year_start: 1,
  academic_year_start: 9,
  base_currency: "SAR",
  secondary_currency: "EUR",
  exchange_rate_sar_eur: 0.24,
  max_capacity: 1875
};
```

**Expected Behavior:**
- Record created successfully with generated UUID
- Timestamps auto-populated
- is_active defaults to true

**Example Test Code:**
```typescript
import { describe, it, expect } from 'vitest';
import { SystemConfig, AEFEStatus } from '@/models';

describe('SystemConfig Model', () => {
  it('should create system configuration with all required fields', async () => {
    const config = await SystemConfig.create({
      school_name: "École Française Internationale de Riyad",
      school_name_fr: "École Française Internationale de Riyad",
      aefe_status: AEFEStatus.CONVENTIONNE,
      fiscal_year_start: 1,
      academic_year_start: 9,
      base_currency: "SAR",
      secondary_currency: "EUR",
      exchange_rate_sar_eur: 0.24,
      max_capacity: 1875
    });

    expect(config.id).toBeDefined();
    expect(config.school_name).toBe("École Française Internationale de Riyad");
    expect(config.aefe_status).toBe(AEFEStatus.CONVENTIONNE);
    expect(config.is_active).toBe(true);
    expect(config.created_at).toBeDefined();
  });
});
```

#### Scenario 2: Validate Academic Structure

**Objective:** Ensure academic structure contains all 15 levels across 4 cycles.

**Test Data:**
```typescript
const expectedStructure = [
  { cycle: "Maternelle", levels: ["PS", "MS", "GS"], count: 3 },
  { cycle: "Élémentaire", levels: ["CP", "CE1", "CE2", "CM1", "CM2"], count: 5 },
  { cycle: "Collège", levels: ["6ème", "5ème", "4ème", "3ème"], count: 4 },
  { cycle: "Lycée", levels: ["2nde", "1ère", "Terminale"], count: 3 }
];
```

**Expected Behavior:**
- Total of 15 levels across 4 cycles
- Primary flag set for Maternelle + Élémentaire (8 levels)
- Secondary flag set for Collège + Lycée (7 levels)
- Levels ordered sequentially within cycle

**Example Test Code:**
```typescript
describe('Academic Structure', () => {
  it('should contain all 15 levels across 4 cycles', async () => {
    const structure = await AcademicStructure.findAll();

    expect(structure.length).toBe(15);

    const cycles = groupBy(structure, 'cycle_name');
    expect(Object.keys(cycles).length).toBe(4);

    const primaryLevels = structure.filter(s => s.is_primary);
    expect(primaryLevels.length).toBe(8); // Maternelle (3) + Élémentaire (5)

    const secondaryLevels = structure.filter(s => s.is_secondary);
    expect(secondaryLevels.length).toBe(7); // Collège (4) + Lycée (3)
  });
});
```

#### Scenario 3: Chart of Accounts Hierarchy

**Objective:** Test parent-child account relationships and hierarchy traversal.

**Test Data:**
```typescript
const accounts = [
  { code: "64", name: "Personnel", parent_code: null, account_class: 6 },
  { code: "641", name: "Teaching Staff", parent_code: "64", account_class: 6 },
  { code: "64110", name: "Teaching Salaries", parent_code: "641", account_class: 6 }
];
```

**Expected Behavior:**
- Parent account can be retrieved from child
- Hierarchy depth of 3 levels (64 → 641 → 64110)
- Account class consistent across hierarchy

**Example Test Code:**
```typescript
describe('Chart of Accounts Hierarchy', () => {
  it('should support parent-child account relationships', async () => {
    const parent = await ChartOfAccounts.create({ code: "64", name: "Personnel", account_class: 6 });
    const child = await ChartOfAccounts.create({ code: "641", name: "Teaching Staff", parent_code: "64", account_class: 6 });
    const grandchild = await ChartOfAccounts.create({ code: "64110", name: "Teaching Salaries", parent_code: "641", account_class: 6 });

    const parentOfGrandchild = await ChartOfAccounts.findOne({ where: { code: grandchild.parent_code } });
    expect(parentOfGrandchild?.code).toBe("641");

    const ancestors = await grandchild.getAncestors(); // Custom method
    expect(ancestors.map(a => a.code)).toEqual(["641", "64"]);
  });
});
```

#### Scenario 4: Cost Center Budget Holder Assignment

**Objective:** Verify cost center requires valid budget holder and prevents deletion.

**Test Data:**
```typescript
const budgetHolder = { id: uuid(), email: "director@efir.sa", role: "admin" };
const costCenter = { code: "MAT", name: "Maternelle", budget_holder_id: budgetHolder.id };
```

**Expected Behavior:**
- Cost center creation requires valid budget_holder_id
- Cannot delete user if they are assigned as budget holder (RESTRICT constraint)
- Can reassign budget holder to different user

**Example Test Code:**
```typescript
describe('Cost Center Budget Holder', () => {
  it('should prevent deletion of user assigned as budget holder', async () => {
    const user = await createTestUser({ role: 'manager' });
    const costCenter = await CostCenter.create({
      code: "MAT",
      name: "Maternelle",
      name_fr: "Maternelle",
      budget_holder_id: user.id
    });

    // Attempt to delete user
    await expect(user.destroy()).rejects.toThrow('FOREIGN KEY constraint');

    // Reassign cost center to different user
    const newUser = await createTestUser({ role: 'manager' });
    costCenter.budget_holder_id = newUser.id;
    await costCenter.save();

    // Now can delete original user
    await user.destroy();
    expect(await User.findByPk(user.id)).toBeNull();
  });
});
```

#### Scenario 5: Budget Period Non-Overlap Validation

**Objective:** Ensure budget periods of same type cannot overlap.

**Test Data:**
```typescript
const fiscalYear2025 = {
  period_name: "FY2025",
  period_type: PeriodType.FISCAL,
  start_date: "2025-01-01",
  end_date: "2025-12-31"
};
const overlappingPeriod = {
  period_name: "FY2025-Q4",
  period_type: PeriodType.FISCAL,
  start_date: "2025-10-01",  // Overlaps with FY2025
  end_date: "2025-12-31"
};
```

**Expected Behavior:**
- First period created successfully
- Second period creation fails with constraint violation
- Different period types can overlap (fiscal vs academic)

**Example Test Code:**
```typescript
describe('Budget Period Non-Overlap', () => {
  it('should prevent overlapping periods of same type', async () => {
    const period1 = await BudgetPeriod.create({
      period_name: "FY2025",
      period_type: PeriodType.FISCAL,
      start_date: new Date("2025-01-01"),
      end_date: new Date("2025-12-31")
    });

    // Attempt to create overlapping period
    await expect(
      BudgetPeriod.create({
        period_name: "FY2025-Q4",
        period_type: PeriodType.FISCAL,
        start_date: new Date("2025-10-01"),
        end_date: new Date("2025-12-31")
      })
    ).rejects.toThrow('overlapping budget periods');
  });

  it('should allow overlapping periods of different types', async () => {
    const fiscalPeriod = await BudgetPeriod.create({
      period_name: "FY2025",
      period_type: PeriodType.FISCAL,
      start_date: new Date("2025-01-01"),
      end_date: new Date("2025-12-31")
    });

    const academicPeriod = await BudgetPeriod.create({
      period_name: "AY2024-2025",
      period_type: PeriodType.ACADEMIC,
      start_date: new Date("2024-09-01"),
      end_date: new Date("2025-06-30")
    });

    expect(fiscalPeriod.id).toBeDefined();
    expect(academicPeriod.id).toBeDefined();
  });
});
```

#### Scenario 6: Exchange Rate Update Workflow

**Objective:** Test exchange rate update mechanism and audit trail.

**Test Data:**
```typescript
const initialRate = 0.24;
const updatedRate = 0.25;
```

**Expected Behavior:**
- Exchange rate can be updated by admin
- updated_at timestamp reflects change
- updated_by_id records who made the change

**Example Test Code:**
```typescript
describe('Exchange Rate Update', () => {
  it('should update exchange rate with audit trail', async () => {
    const admin = await createTestUser({ role: 'admin' });
    const config = await SystemConfig.findOne();

    expect(config.exchange_rate_sar_eur).toBe(0.24);

    // Update exchange rate
    config.exchange_rate_sar_eur = 0.25;
    config.updated_by_id = admin.id;
    await config.save();

    const updated = await SystemConfig.findByPk(config.id);
    expect(updated.exchange_rate_sar_eur).toBe(0.25);
    expect(updated.updated_by_id).toBe(admin.id);
    expect(updated.updated_at).not.toBe(config.created_at);
  });
});
```

#### Scenario 7: RLS Policy - Admin Full Access

**Objective:** Verify admin role has full access to all configuration data.

**Expected Behavior:**
- Admin can read, create, update, delete all configuration entities
- No restrictions on system_config, academic_structure, chart_of_accounts, cost_centers

**Example Test Code:**
```python
def test_rls_admin_full_access():
    """Test that admin role has full access to system configuration."""
    # Setup: authenticate as admin
    set_user_role("admin")

    # Admin can read system config
    config = db.session.query(SystemConfig).first()
    assert config is not None

    # Admin can update exchange rate
    config.exchange_rate_sar_eur = Decimal("0.25")
    db.session.commit()

    # Admin can create new account code
    new_account = ChartOfAccounts(
        account_code="64999",
        account_name="Test Account",
        account_name_en="Test Account",
        account_type=AccountType.EXPENSE,
        account_class=6
    )
    db.session.add(new_account)
    db.session.commit()

    assert new_account.id is not None
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: system_config, academic_structure, chart_of_accounts, cost_centers, budget_periods tables with RLS policies |

## Future Enhancements (Phase 5-6)

1. **Configuration UI**: Admin interface for managing system configuration, accounts, and cost centers
2. **Exchange Rate API Integration**: Automatic exchange rate updates from external API (e.g., ECB, SAMA)
3. **Account Import/Export**: Bulk import of chart of accounts from Excel template
4. **Cost Center Budgeting**: Assign budget amounts to cost centers for allocation tracking
5. **Calendar Management**: Visual calendar editor for fiscal and academic periods
6. **Multi-School Support**: Extend system to support multiple schools (AEFE network)
7. **Audit Log**: Comprehensive audit log for all configuration changes
8. **Version History**: Track historical versions of configuration parameters
9. **Validation Dashboard**: Dashboard showing configuration health checks and warnings
10. **AEFE Sync**: Synchronize AEFE status and exchange rates with AEFE central system

## Notes

- **Phase 4 Scope**: This module currently implements the database foundation (tables, constraints, RLS policies, migrations)
- **Business Logic**: Configuration management UI and API endpoints will be implemented in Phases 5-6
- **Immutability**: Academic structure should be considered immutable once budget planning begins to prevent data inconsistencies
- **Exchange Rates**: Exchange rates should be updated monthly or before major AEFE cost calculations
- **Bilingual Support**: All configuration entities support both French and English for EFIR's bilingual environment
- **PCG Compliance**: Chart of accounts strictly follows French Plan Comptable Général for accounting compliance
- **AEFE Integration**: System designed to align with AEFE reporting requirements and partnership obligations
