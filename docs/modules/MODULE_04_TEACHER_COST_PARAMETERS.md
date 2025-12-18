# Module 4: Teacher Cost Parameters

## Overview

Module 4 defines the salary scales, benefits, allowances, and cost structures for all teaching staff at EFIR, including AEFE detached teachers, AEFE-funded teachers, and local teachers across six position categories. These parameters are essential for calculating total personnel costs based on workforce requirements determined in Module 8 (DHG Workforce Planning).

**Layer**: Configuration Layer (Phase 1)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Salary calculator UI, cost modeling tools, API endpoints (Phase 5-6)

### Purpose

- Define AEFE teacher costs (PRRD contributions and allowances)
- Establish local teacher salary scales by position category
- Configure allowances (housing, transport, responsibility premiums)
- Specify social charges and employer contributions
- Set overtime (HSA) rates and caps
- Support salary increment tracking and historical analysis
- Enable cost scenario modeling (conservative vs. optimistic assumptions)

### Key Design Decisions

1. **Dual Cost Models**: AEFE costs in EUR (then converted to SAR), local costs directly in SAR
2. **Position-Based Structure**: Six distinct position categories with individual salary ranges
3. **Allowance Standardization**: Fixed housing (2,500 SAR) and transport (500 SAR) allowances
4. **Social Charges on Base Only**: Employer contributions calculated on base salary, not total compensation
5. **HSA Flexibility**: Overtime hours configurable per teacher with max cap enforcement
6. **Version Control**: Parameters versioned per budget version for multi-year planning

## Database Schema

### Tables

#### 1. aefe_teacher_costs

AEFE teacher cost parameters (PRRD contributions, allowances).

**Columns:**
```sql
id                        UUID PRIMARY KEY
version_id                UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
teacher_type              aefeteachertype NOT NULL    -- ENUM: detache, funded
grade_echelon             VARCHAR(100) NOT NULL       -- e.g., "Certifié Classe Normale"
prrd_contribution_eur     NUMERIC(12, 2) NOT NULL     -- Annual PRRD in EUR (~41,863)
isvl_allowance_eur        NUMERIC(12, 2) NULL         -- Local living allowance (EUR)
housing_allowance_eur     NUMERIC(10, 2) NULL         -- Housing support (EUR/month)
standard_hours_primary    INTEGER NOT NULL DEFAULT 24
standard_hours_secondary  INTEGER NOT NULL DEFAULT 18
effective_date            DATE NOT NULL
notes                     TEXT NULL
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id             UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id             UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- prrd_contribution_eur > 0
- standard_hours_primary = 24, standard_hours_secondary = 18 (French standard)
- UNIQUE (version_id, teacher_type, grade_echelon, effective_date)
- CASCADE delete when budget version deleted

**RLS Policies:**
- Admin: Full access to AEFE cost parameters
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (version_id, teacher_type)
- Index on effective_date for historical queries

#### 2. local_teacher_costs

Local teacher salary scales and allowances by position category.

**Columns:**
```sql
id                        UUID PRIMARY KEY
version_id                UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
position_category         localteachercategory NOT NULL  -- ENUM: see below
base_salary_min_monthly   NUMERIC(10, 2) NOT NULL       -- Minimum salary (SAR)
base_salary_max_monthly   NUMERIC(10, 2) NOT NULL       -- Maximum salary (SAR)
base_salary_avg_monthly   NUMERIC(10, 2) NOT NULL       -- Average/typical (SAR)
housing_allowance_monthly NUMERIC(8, 2) NOT NULL DEFAULT 2500.00
transport_allowance_monthly NUMERIC(8, 2) NOT NULL DEFAULT 500.00
responsibility_premium_monthly NUMERIC(8, 2) NULL       -- For coordinators, dept heads
social_charges_pct        NUMERIC(5, 2) NOT NULL DEFAULT 0.00  -- Employer contribution %
standard_hours_per_week   INTEGER NOT NULL              -- 18 or 24
max_overtime_hours_weekly INTEGER NOT NULL DEFAULT 4   -- HSA cap
overtime_rate_hourly_sar  NUMERIC(8, 2) NULL            -- HSA rate
effective_date            DATE NOT NULL
notes                     TEXT NULL
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id             UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id             UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- base_salary_min_monthly < base_salary_avg_monthly <= base_salary_max_monthly
- housing_allowance_monthly >= 0
- transport_allowance_monthly >= 0
- social_charges_pct >= 0 AND social_charges_pct <= 0.50 (max 50%)
- standard_hours_per_week IN (18, 24)
- max_overtime_hours_weekly >= 0 AND max_overtime_hours_weekly <= 10
- UNIQUE (version_id, position_category, effective_date)
- CASCADE delete when budget version deleted

**RLS Policies:**
- Admin: Full access to local teacher costs
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (version_id, position_category)
- Index on position_category for category-based queries

#### 3. salary_increments (Historical Tracking)

Annual salary increments and adjustments over time.

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
increment_type        incrementtype NOT NULL     -- ENUM: annual, merit, cola, promotion
position_category     localteachercategory NULL  -- NULL = applies to all AEFE or all local
teacher_type          aefeteachertype NULL       -- For AEFE increments
increment_pct         NUMERIC(5, 2) NOT NULL     -- Percentage increase
increment_amount_fixed NUMERIC(10, 2) NULL       -- Or fixed amount (alternative)
effective_date        DATE NOT NULL
description           TEXT NOT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- increment_pct >= 0 OR increment_amount_fixed >= 0 (at least one specified)
- Either position_category OR teacher_type must be specified (not both)

**RLS Policies:**
- All authenticated users can read increments
- Only admins can create/modify increments

**Indexes:**
- Primary key on id
- Index on effective_date for timeline queries

### Enums

#### AEFETeacherType
```sql
CREATE TYPE efir_budget.aefeteachertype AS ENUM (
    'detache',         -- Détaché/Resident (school pays PRRD ~41,863 EUR)
    'funded'           -- AEFE-funded (no school cost)
);
```

#### LocalTeacherCategory
```sql
CREATE TYPE efir_budget.localteachercategory AS ENUM (
    'professeur_ecoles',        -- Primary teachers (Maternelle + Élémentaire)
    'enseignant_second_degre',  -- Secondary teachers (Collège + Lycée core subjects)
    'enseignant_langue_etrangere', -- Foreign language teachers (English, Spanish)
    'professeur_eps',           -- Physical Education teachers
    'asem',                     -- Preschool classroom assistants (Maternelle)
    'assistant_education'       -- Educational assistants (surveillance, support)
);
```

#### IncrementType
```sql
CREATE TYPE efir_budget.incrementtype AS ENUM (
    'annual',          -- Annual cost of living adjustment
    'merit',           -- Performance-based merit increase
    'cola',            -- Cost of living allowance
    'promotion'        -- Promotion to higher grade/echelon
);
```

## Data Model

### Sample AEFE Teacher Costs

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440400",
  "version_id": "123e4567-e89b-12d3-a456-426614174000",
  "teacher_type": "detache",
  "grade_echelon": "Certifié Classe Normale",
  "prrd_contribution_eur": 41863.00,
  "isvl_allowance_eur": 0.00,
  "housing_allowance_eur": 0.00,
  "standard_hours_primary": 24,
  "standard_hours_secondary": 18,
  "effective_date": "2025-09-01",
  "notes": "PRRD contribution for AY 2025-2026"
}
```

**Cost Calculation (at exchange rate 0.24 SAR/EUR):**
```
PRRD in EUR: 41,863 EUR
Exchange rate: 1 EUR = 4.17 SAR (1 ÷ 0.24)
PRRD in SAR: 41,863 × 4.17 = 174,569 SAR/year
Monthly cost: 174,569 ÷ 12 = 14,547 SAR/month
```

### Sample Local Teacher Costs (6 Categories)

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440410",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "position_category": "professeur_ecoles",
    "base_salary_min_monthly": 8000.00,
    "base_salary_max_monthly": 12750.00,
    "base_salary_avg_monthly": 12500.00,
    "housing_allowance_monthly": 2500.00,
    "transport_allowance_monthly": 500.00,
    "responsibility_premium_monthly": 0.00,
    "social_charges_pct": 0.00,
    "standard_hours_per_week": 24,
    "max_overtime_hours_weekly": 0,
    "overtime_rate_hourly_sar": null,
    "effective_date": "2025-09-01",
    "notes": "Primary teachers (30 positions at EFIR)"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440411",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "position_category": "enseignant_second_degre",
    "base_salary_min_monthly": 4000.00,
    "base_salary_max_monthly": 12000.00,
    "base_salary_avg_monthly": 12613.00,
    "housing_allowance_monthly": 2500.00,
    "transport_allowance_monthly": 500.00,
    "responsibility_premium_monthly": 1000.00,
    "social_charges_pct": 0.00,
    "standard_hours_per_week": 18,
    "max_overtime_hours_weekly": 4,
    "overtime_rate_hourly_sar": 150.00,
    "effective_date": "2025-09-01",
    "notes": "Secondary teachers (43 positions), HSA allowed"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440412",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "position_category": "asem",
    "base_salary_min_monthly": 5800.00,
    "base_salary_max_monthly": 8500.00,
    "base_salary_avg_monthly": 9900.00,
    "housing_allowance_monthly": 2500.00,
    "transport_allowance_monthly": 500.00,
    "responsibility_premium_monthly": 0.00,
    "social_charges_pct": 0.00,
    "standard_hours_per_week": 35,
    "max_overtime_hours_weekly": 0,
    "overtime_rate_hourly_sar": null,
    "effective_date": "2025-09-01",
    "notes": "Preschool assistants (13 positions, 35h/week)"
  }
]
```

### Local Teacher Salary Matrix (2024-2025 Actual Data)

| Position Category | Count | Base Min | Base Max | Avg Net | Std Hours | HSA Allowed |
|-------------------|-------|----------|----------|---------|-----------|-------------|
| Professeur des écoles | 30 | 8,000 | 12,750 | 12,500 | 24h/week | No |
| Enseignant second degré | 43 | 4,000 | 12,000 | 12,613 | 18h/week | Yes (4h max) |
| Enseignant langue étrangère | 24 | 3,700 | 14,250 | 13,500 | 18h/week | Yes (4h max) |
| Professeur EPS | 4 | 8,500 | 12,250 | 13,062 | 18h/week | Yes (2h max) |
| ASEM | 13 | 5,800 | 8,500 | 9,900 | 35h/week | No |
| Assistant d'éducation | 12 | 7,000 | 9,000 | 10,575 | 35h/week | No |

## Business Rules

### AEFE Teacher Cost Rules

1. **EUR-Based Calculation**: AEFE costs always calculated in EUR, then converted to SAR using current exchange rate (Module 1)
2. **PRRD Only**: School pays only PRRD contribution for détachés (~41,863 EUR/year per teacher)
3. **Funded Teachers**: AEFE-funded teachers have zero cost to school (fully covered by AEFE)
4. **Standard Hours**: Primary 24h/week, Secondary 18h/week (French regulation)
5. **No Overtime**: AEFE teachers do not receive HSA (overtime) - only recruitment or reassignment
6. **Exchange Rate Dependency**: AEFE costs in SAR fluctuate with EUR/SAR exchange rate

### Local Teacher Cost Rules

1. **Total Compensation Formula**:
   ```
   Monthly Gross = Base Salary + Housing Allowance + Transport Allowance + Responsibility Premium
   Annual Base = Monthly Gross × 12 months
   Annual Social Charges = Base Salary × 12 × Social Charges %
   Annual Overtime = Overtime Hours/Year × Hourly Rate
   Total Annual Cost = Annual Base + Annual Social Charges + Annual Overtime
   ```

2. **Allowance Standardization**:
   - Housing allowance: 2,500 SAR/month (standard for all)
   - Transport allowance: 500 SAR/month (standard for all)
   - Responsibility premium: Variable by role (coordinators, department heads)

3. **Social Charges**: Calculated only on base salary, not total compensation

4. **Overtime (HSA) Rules**:
   - Secondary teachers only (Collège + Lycée)
   - Capped at max_overtime_hours_weekly per teacher (typically 2-4 hours)
   - Paid over 10 months (September-June, excludes July-August)
   - Hourly rate varies by position category (~150 SAR/hour)

5. **Salary Ranges**:
   - min_salary: New hires or entry-level
   - avg_salary: Typical experienced teacher
   - max_salary: Senior teachers with longevity

### Increment Application Rules

1. **Annual Increments**: Applied at start of academic year (September 1)
2. **Increment Types**: Annual COLA, merit-based, promotion-based
3. **Percentage vs. Fixed**: Either percentage increase OR fixed amount, not both
4. **Cascade Impact**: Salary changes trigger recalculation of personnel costs (Module 11)
5. **AEFE vs. Local**: AEFE increments managed by AEFE (school absorbs PRRD increases), local increments set by school

### Validation Rules

1. **Salary Ordering**: min < avg ≤ max for each position category
2. **Standard Hours**: Must be 18 (secondary) or 24 (primary) to align with DHG calculations
3. **HSA Cap Enforcement**: Overtime hours cannot exceed max_overtime_hours_weekly
4. **Social Charges Range**: 0% to 50% (typical ~10-20%)
5. **Position Consistency**: Standard hours must match position type (primary=24, secondary=18)

## Calculation Examples

### Example 1: AEFE Teacher Annual Cost

**Context**: Calculate annual cost for one AEFE détaché teacher in SAR.

**Given Data:**
- PRRD contribution: 41,863 EUR/year
- Exchange rate: 0.24 SAR/EUR (i.e., 1 SAR = 0.24 EUR, or 1 EUR = 4.17 SAR)
- Teacher type: Détaché (school pays)

**Formula:**
```
Cost_SAR = Cost_EUR × Exchange_Rate_Inverse
Exchange_Rate_Inverse = 1 ÷ 0.24 = 4.17 SAR/EUR
```

**Calculation:**
```
Annual cost in EUR: 41,863 EUR
Convert to SAR: 41,863 × 4.17 = 174,569 SAR

Monthly cost: 174,569 ÷ 12 = 14,547 SAR/month
```

**Result:** Each AEFE détaché teacher costs the school 174,569 SAR per year (or 14,547 SAR/month).

**EFIR Context (24 AEFE détachés):**
```
Total AEFE personnel cost = 24 teachers × 174,569 SAR = 4,189,656 SAR/year
```

### Example 2: Local Secondary Teacher Full Annual Cost

**Context**: Calculate total annual cost for one secondary teacher with overtime.

**Given Data:**
- Position: Enseignant second degré
- Base salary: 12,613 SAR/month (average)
- Housing allowance: 2,500 SAR/month
- Transport allowance: 500 SAR/month
- Responsibility premium: 1,000 SAR/month (department head)
- Social charges: 0% (no employer contributions in Saudi Arabia typically)
- Overtime: 4 hours/week × 36 weeks = 144 hours/year
- Overtime rate: 150 SAR/hour

**Calculation:**
```
Step 1: Monthly gross compensation
  Base:               12,613 SAR
  Housing:             2,500 SAR
  Transport:             500 SAR
  Responsibility:      1,000 SAR
  ────────────────────────────
  Monthly gross:      16,613 SAR

Step 2: Annual base compensation
  Annual base = 16,613 × 12 = 199,356 SAR

Step 3: Social charges
  Social charges = 12,613 × 12 × 0.00 = 0 SAR (0% rate)

Step 4: Annual overtime (HSA)
  Overtime hours: 4 hours/week × 36 weeks = 144 hours
  Overtime cost: 144 × 150 = 21,600 SAR

Step 5: Total annual employer cost
  Annual base:        199,356 SAR
  Social charges:           0 SAR
  Overtime:            21,600 SAR
  ────────────────────────────
  Total annual cost:  220,956 SAR
```

**Result:** One secondary teacher with 4h/week overtime costs 220,956 SAR/year.

**Breakdown:**
- Base compensation: 199,356 SAR (90.2%)
- Overtime (HSA): 21,600 SAR (9.8%)

### Example 3: ASEM (Preschool Assistant) Annual Cost

**Context**: Calculate annual cost for one ASEM (no overtime).

**Given Data:**
- Position: ASEM
- Base salary: 9,900 SAR/month (average)
- Housing allowance: 2,500 SAR/month
- Transport allowance: 500 SAR/month
- Responsibility premium: 0 SAR
- Social charges: 0%
- Overtime: Not applicable (35h/week contract, no HSA)

**Calculation:**
```
Monthly gross compensation:
  Base:               9,900 SAR
  Housing:            2,500 SAR
  Transport:            500 SAR
  ──────────────────────────
  Monthly gross:     12,900 SAR

Annual cost:
  12,900 × 12 = 154,800 SAR/year
```

**Result:** One ASEM costs 154,800 SAR/year.

**EFIR Context (13 ASEM positions):**
```
Total ASEM cost = 13 × 154,800 = 2,012,400 SAR/year
```

### Example 4: Total Personnel Cost Scenario (Simplified)

**Context**: Calculate total teaching personnel cost for simplified scenario.

**Given Workforce (simplified):**
- AEFE détachés: 24 positions @ 174,569 SAR each
- AEFE funded: 4 positions @ 0 SAR (no cost to school)
- Local secondary teachers: 43 positions @ 220,956 SAR each (with HSA)
- Local primary teachers: 30 positions @ 192,000 SAR each (base only, no HSA)
- ASEM: 13 positions @ 154,800 SAR each

**Calculation:**
```
AEFE détachés:       24 × 174,569 =  4,189,656 SAR
AEFE funded:          4 × 0       =          0 SAR
Local secondary:     43 × 220,956 =  9,501,108 SAR
Local primary:       30 × 192,000 =  5,760,000 SAR
ASEM:                13 × 154,800 =  2,012,400 SAR
───────────────────────────────────────────────────
Total teaching personnel:         21,463,164 SAR/year
```

**Result:** Total annual teaching personnel cost: ~21.5 million SAR.

**Breakdown by Category:**
- AEFE: 4,189,656 SAR (19.5%)
- Local teachers: 15,261,108 SAR (71.1%)
- ASEM: 2,012,400 SAR (9.4%)

## Integration Points

### Upstream Dependencies

1. **Module 1 (System Configuration)**: Exchange rates for AEFE cost conversion (EUR to SAR)
2. **Module 13 (Budget Consolidation)**: Budget version for cost parameter versioning

### Downstream Consumers

1. **Module 8 (DHG Workforce Planning)**: Uses cost parameters to calculate total personnel costs based on FTE requirements
2. **Module 11 (Cost Planning)**: Applies cost parameters to actual staffing allocations
3. **Module 15 (Statistical Analysis)**: Cost per student KPI calculations

### Data Flow

```
Exchange Rate (Module 1) → AEFE Cost Calculation (Module 4)
                                     ↓
         Teacher FTE Requirements (Module 8 - DHG)
                                     ↓
   Cost Parameters (Module 4) × FTE → Total Personnel Cost
                                     ↓
                  Cost Planning (Module 11)
                  Account: 64110 (Teaching salaries)
                  Account: 64800 (AEFE PRRD)
```

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
# AEFE Teacher Costs
GET    /api/v1/budget-versions/:id/aefe-costs              # Get AEFE cost parameters
POST   /api/v1/budget-versions/:id/aefe-costs              # Create AEFE cost entry
PUT    /api/v1/budget-versions/:id/aefe-costs/:cost_id     # Update AEFE cost
GET    /api/v1/aefe-costs/convert-to-sar                   # Convert EUR to SAR using current rate
       Query: ?amount_eur=41863

# Local Teacher Costs
GET    /api/v1/budget-versions/:id/local-teacher-costs     # Get all local cost parameters
GET    /api/v1/budget-versions/:id/local-teacher-costs/category/:category  # Get specific category
POST   /api/v1/budget-versions/:id/local-teacher-costs     # Create local cost entry
PUT    /api/v1/budget-versions/:id/local-teacher-costs/:cost_id  # Update local cost

# Cost Calculations
POST   /api/v1/calculate-teacher-cost                      # Calculate annual cost
       Request: { teacher_type, position_category, base_salary, overtime_hours, ... }
       Response: { monthly_gross, annual_base, annual_overtime, total_annual_cost }

# Salary Increments
GET    /api/v1/budget-versions/:id/salary-increments       # Get increments for version
POST   /api/v1/budget-versions/:id/salary-increments       # Apply increment
       Request: { increment_type, increment_pct, effective_date, ... }

# Cost Modeling
POST   /api/v1/cost-scenarios                              # Model cost scenarios
       Request: { aefe_count, local_by_category: {}, salary_assumptions: {} }
       Response: { total_cost, breakdown_by_category, sensitivity_analysis }
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify aefe_teacher_costs and local_teacher_costs models
2. **Enum Tests**: Verify AEFETeacherType, LocalTeacherCategory, IncrementType enums
3. **Calculation Tests**: Test cost calculation formulas

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for different roles
2. **Exchange Rate Integration**: Test EUR to SAR conversion using Module 1 rates
3. **Increment Application**: Test salary increment workflows

### Test Scenarios

#### Scenario 1: Create AEFE Cost Parameters

**Objective:** Create AEFE teacher cost record with PRRD contribution.

**Test Data:**
```typescript
const aefeCost = {
  version_id: testVersion.id,
  teacher_type: AEFETeacherType.DETACHE,
  grade_echelon: "Certifié Classe Normale",
  prrd_contribution_eur: 41863.00,
  standard_hours_primary: 24,
  standard_hours_secondary: 18,
  effective_date: new Date("2025-09-01")
};
```

**Expected Behavior:**
- Record created successfully
- Standard hours default to 24 (primary) and 18 (secondary)

**Example Test Code:**
```typescript
import { describe, it, expect } from 'vitest';
import { AEFETeacherCost, AEFETeacherType } from '@/models';

describe('AEFE Teacher Costs', () => {
  it('should create AEFE cost parameters', async () => {
    const cost = await AEFETeacherCost.create({
      version_id: testVersion.id,
      teacher_type: AEFETeacherType.DETACHE,
      grade_echelon: "Certifié Classe Normale",
      prrd_contribution_eur: 41863.00,
      effective_date: new Date("2025-09-01")
    });

    expect(cost.id).toBeDefined();
    expect(cost.prrd_contribution_eur).toBe(41863.00);
    expect(cost.standard_hours_secondary).toBe(18);
  });
});
```

#### Scenario 2: EUR to SAR Conversion

**Objective:** Test AEFE cost conversion from EUR to SAR.

**Test Data:**
```typescript
const prrd_eur = 41863;
const exchange_rate_sar_eur = 0.24; // 1 SAR = 0.24 EUR
const expected_sar = 41863 / 0.24; // 174,429 SAR
```

**Expected Behavior:**
- Conversion uses exchange rate from Module 1
- Result: 174,429 SAR

**Example Test Code:**
```typescript
describe('AEFE Cost Conversion', () => {
  it('should convert AEFE cost from EUR to SAR', async () => {
    const systemConfig = await SystemConfig.findOne();
    const exchangeRate = systemConfig.exchange_rate_sar_eur;

    const prrd_eur = 41863;
    const prrd_sar = prrd_eur / exchangeRate;

    expect(prrd_sar).toBeCloseTo(174429, 0); // Allow rounding
  });
});
```

#### Scenario 3: Local Teacher Cost Calculation

**Objective:** Calculate total annual cost for local teacher with all components.

**Test Data:**
```typescript
const teacherCost = {
  base_salary: 12613,
  housing_allowance: 2500,
  transport_allowance: 500,
  responsibility_premium: 1000,
  social_charges_pct: 0.00,
  overtime_hours_annual: 144,
  overtime_rate: 150
};
```

**Expected Behavior:**
- Monthly gross: 16,613 SAR
- Annual base: 199,356 SAR
- Overtime: 21,600 SAR
- Total: 220,956 SAR

**Example Test Code:**
```typescript
describe('Local Teacher Cost Calculation', () => {
  it('should calculate total annual cost with all components', () => {
    const monthlyGross = 12613 + 2500 + 500 + 1000;
    const annualBase = monthlyGross * 12;
    const socialCharges = 12613 * 12 * 0.00;
    const overtime = 144 * 150;
    const totalCost = annualBase + socialCharges + overtime;

    expect(monthlyGross).toBe(16613);
    expect(annualBase).toBe(199356);
    expect(overtime).toBe(21600);
    expect(totalCost).toBe(220956);
  });
});
```

#### Scenario 4: Salary Range Validation

**Objective:** Ensure salary min < avg ≤ max constraint is enforced.

**Test Data:**
```typescript
const invalidSalary = {
  base_salary_min_monthly: 12000,
  base_salary_avg_monthly: 10000, // Invalid: avg < min
  base_salary_max_monthly: 15000
};
```

**Expected Behavior:**
- Invalid record rejected with constraint violation

**Example Test Code:**
```typescript
describe('Salary Range Validation', () => {
  it('should reject salary parameters where min > avg', async () => {
    await expect(
      LocalTeacherCost.create({
        version_id: testVersion.id,
        position_category: LocalTeacherCategory.ENSEIGNANT_SECOND_DEGRE,
        base_salary_min_monthly: 12000,
        base_salary_avg_monthly: 10000,
        base_salary_max_monthly: 15000,
        effective_date: new Date("2025-09-01")
      })
    ).rejects.toThrow('base_salary_min_monthly < base_salary_avg_monthly');
  });
});
```

#### Scenario 5: HSA (Overtime) Cap Enforcement

**Objective:** Validate overtime hours don't exceed max cap.

**Test Data:**
```typescript
const overtimeScenario = {
  max_overtime_hours_weekly: 4,
  actual_overtime_hours_weekly: 6  // Exceeds cap
};
```

**Expected Behavior:**
- Warning or error when overtime exceeds max
- Business logic caps overtime at max value

**Example Test Code:**
```typescript
describe('Overtime Cap Enforcement', () => {
  it('should cap overtime hours at maximum allowed', () => {
    const maxOvertimeWeekly = 4;
    const requestedOvertime = 6;

    const actualOvertime = Math.min(requestedOvertime, maxOvertimeWeekly);

    expect(actualOvertime).toBe(4);
  });

  it('should warn when requested overtime exceeds cap', () => {
    const maxOvertimeWeekly = 4;
    const requestedOvertime = 6;

    const exceedsMax = requestedOvertime > maxOvertimeWeekly;

    expect(exceedsMax).toBe(true);
    // In real implementation, would log warning
  });
});
```

#### Scenario 6: Salary Increment Application

**Objective:** Apply annual increment to base salaries.

**Test Data:**
```typescript
const increment = {
  increment_type: IncrementType.ANNUAL,
  position_category: LocalTeacherCategory.ENSEIGNANT_SECOND_DEGRE,
  increment_pct: 3.0, // 3% COLA
  effective_date: new Date("2025-09-01")
};

const currentSalary = 12613;
```

**Expected Behavior:**
- New salary = 12613 × 1.03 = 12,991 SAR

**Example Test Code:**
```typescript
describe('Salary Increment Application', () => {
  it('should apply percentage increment to base salary', () => {
    const currentSalary = 12613;
    const incrementPct = 3.0;

    const newSalary = currentSalary * (1 + incrementPct / 100);

    expect(newSalary).toBeCloseTo(12991, 0);
  });
});
```

#### Scenario 7: RLS Policy - Manager Access

**Objective:** Verify managers can modify cost parameters for working budget versions.

**Expected Behavior:**
- Manager can read/write cost parameters for working versions
- Manager has read-only access to approved versions

**Example Test Code:**
```python
def test_rls_manager_teacher_costs():
    """Test manager can modify cost parameters for working versions."""
    # Setup: working budget version
    working_version = create_working_budget_version()

    # Authenticate as manager
    set_user_role("manager")

    # Manager can create local teacher cost
    teacher_cost = LocalTeacherCost(
        version_id=working_version.id,
        position_category=LocalTeacherCategory.ENSEIGNANT_SECOND_DEGRE,
        base_salary_avg_monthly=Decimal("12613.00"),
        effective_date=date(2025, 9, 1)
    )
    db.session.add(teacher_cost)
    db.session.commit()

    assert teacher_cost.id is not None

    # Manager can update parameters
    teacher_cost.base_salary_avg_monthly = Decimal("13000.00")
    db.session.commit()

    refreshed = db.session.query(LocalTeacherCost).filter_by(id=teacher_cost.id).first()
    assert refreshed.base_salary_avg_monthly == Decimal("13000.00")
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: aefe_teacher_costs, local_teacher_costs, salary_increments tables with RLS policies |

## Future Enhancements (Phase 5-6)

1. **Salary Calculator UI**: Interactive tool for modeling teacher costs with different assumptions
2. **Cost Scenario Modeling**: Compare conservative vs. optimistic salary scenarios
3. **Increment Forecasting**: Project future salary costs with expected increments
4. **Exchange Rate Sensitivity**: Analyze impact of EUR/SAR fluctuations on AEFE costs
5. **Benchmark Comparison**: Compare EFIR salaries to regional and AEFE network averages
6. **Total Compensation Statements**: Generate detailed compensation breakdowns for HR
7. **Budget Holder Cost Allocation**: Allocate personnel costs to cost centers by assignment
8. **Historical Cost Tracking**: Trend analysis of teacher costs over multiple years
9. **Merit Pay Modeling**: Simulate impact of performance-based pay structures
10. **Retirement/Turnover Planning**: Model cost impacts of expected staff changes

## Notes

- **Phase 4 Scope**: This module implements database foundation (tables, constraints, RLS policies, migrations)
- **Business Logic**: Cost calculation engine and salary modeling UI will be implemented in Phases 5-6
- **AEFE Dependency**: AEFE costs subject to French government decisions (PRRD rates set annually by AEFE)
- **Exchange Rate Volatility**: AEFE costs in SAR fluctuate with EUR/SAR exchange rate (monthly updates recommended)
- **No Social Charges**: Saudi Arabia typically has no employer social security contributions (0% in examples)
- **HSA Secondary Only**: Overtime (HSA) applies only to secondary teachers (Collège + Lycée), not primary
- **Allowance Standardization**: Housing (2,500 SAR) and transport (500 SAR) are standardized across all positions
- **Cost Driver**: Teacher costs represent ~50-60% of total operating expenses, making this a critical cost driver
- **Workforce Integration**: Cost parameters must align with FTE requirements from Module 8 (DHG) for accurate budgeting
