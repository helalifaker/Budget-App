# Module 5: Fee Structure Configuration

## Overview

Module 5 defines the complete fee structure for EFIR, including tuition fees by academic level and nationality category, enrollment fees (DAI), registration fees, exam fees, and discount rules. This module serves as the foundation for revenue planning (Module 10) and determines how tuition revenue is calculated based on enrollment projections.

**Layer**: Configuration Layer (Phase 1)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Fee management UI, discount calculators, API endpoints (Phase 5-6)

### Purpose

- Define annual tuition fees by level and nationality category
- Configure enrollment fees (DAI - Droit Annuel d'Inscription)
- Set registration and first enrollment fees for new students
- Establish exam fees (DNB, E.A., Baccalauréat)
- Define discount rules (sibling, staff, scholarship)
- Specify payment schedule by trimester
- Support fee versioning for multi-year planning
- Enable revenue scenario modeling

### Key Design Decisions

1. **Three Nationality Categories**: French (TTC), Saudi (HT/exempt), Other (TTC) reflecting VAT treatment
2. **Level-Based Pricing**: Fees increase from Maternelle to Lycée (higher value for older students)
3. **DAI Standardization**: Enrollment fee (DAI) fixed at 5,000 SAR across all levels
4. **Sibling Discount Rule**: 25% discount on tuition only for 3rd+ child (excludes DAI, registration)
5. **Trimester Payment Schedule**: Revenue recognized in 3 installments (40%, 30%, 30%)
6. **Fee Versioning**: Fee structures versioned per academic year for historical analysis

## Database Schema

### Tables

#### 1. fee_structure

Tuition and enrollment fees by level and nationality.

**Columns:**
```sql
id                        UUID PRIMARY KEY
version_id                UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
level_id                  UUID NOT NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
nationality_category      nationalitycategory NOT NULL  -- ENUM: french, saudi, other
annual_tuition_sar        NUMERIC(10, 2) NOT NULL       -- Annual tuition in SAR
vat_treatment             vattreatment NOT NULL         -- ENUM: ttc, ht
dai_fee_sar               NUMERIC(8, 2) NOT NULL        -- Annual enrollment fee (DAI)
registration_fee_sar      NUMERIC(8, 2) NULL            -- One-time for new students
first_enrollment_fee_sar  NUMERIC(8, 2) NULL            -- First-time enrollment
academic_year             VARCHAR(20) NOT NULL          -- e.g., "2025-2026"
effective_date            DATE NOT NULL
notes                     TEXT NULL
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id             UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id             UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- annual_tuition_sar > 0
- dai_fee_sar >= 0
- registration_fee_sar >= 0
- first_enrollment_fee_sar >= 0
- UNIQUE (version_id, level_id, nationality_category, academic_year)
- CASCADE delete when budget version deleted

**RLS Policies:**
- Admin: Full access to fee structure
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Unique index on (version_id, level_id, nationality_category)
- Index on academic_year for year-based queries

#### 2. exam_fees

Exam registration fees by exam type and nationality.

**Columns:**
```sql
id                        UUID PRIMARY KEY
version_id                UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
exam_type                 examtype NOT NULL             -- ENUM: dnb, ea, baccalaureat
nationality_category      nationalitycategory NOT NULL
exam_fee_sar              NUMERIC(8, 2) NOT NULL
academic_year             VARCHAR(20) NOT NULL
effective_date            DATE NOT NULL
notes                     TEXT NULL
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- exam_fee_sar >= 0
- UNIQUE (version_id, exam_type, nationality_category, academic_year)

**RLS Policies:**
- Same as fee_structure table

**Indexes:**
- Primary key on id
- Index on (version_id, exam_type)

#### 3. discount_rules

Discount policies (sibling, staff, scholarship).

**Columns:**
```sql
id                        UUID PRIMARY KEY
version_id                UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
discount_type             discounttype NOT NULL         -- ENUM: sibling, staff, scholarship, other
discount_name             VARCHAR(100) NOT NULL
discount_pct              NUMERIC(5, 2) NULL            -- Percentage discount (e.g., 25.00)
discount_amount_fixed_sar NUMERIC(10, 2) NULL           -- Or fixed amount
applies_to                VARCHAR(50) NOT NULL          -- tuition, dai, registration, all
min_conditions            JSONB NULL                    -- Conditions (e.g., {sibling_rank: 3})
max_discount_sar          NUMERIC(10, 2) NULL           -- Cap on discount amount
requires_approval         BOOLEAN NOT NULL DEFAULT false
is_active                 BOOLEAN NOT NULL DEFAULT true
effective_date            DATE NOT NULL
notes                     TEXT NULL
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- Either discount_pct OR discount_amount_fixed_sar must be specified (not both null)
- discount_pct between 0 and 100 if specified
- applies_to IN ('tuition', 'dai', 'registration', 'all')

**RLS Policies:**
- All authenticated users can read active discount rules
- Only admins can create/modify discount rules

**Indexes:**
- Primary key on id
- Index on discount_type
- Index on is_active

#### 4. payment_schedule

Trimester payment schedule configuration.

**Columns:**
```sql
id                        UUID PRIMARY KEY
version_id                UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
trimester                 INTEGER NOT NULL              -- 1, 2, 3
period_name               VARCHAR(50) NOT NULL          -- T1, T2, T3
period_months             VARCHAR(50) NOT NULL          -- Sep-Dec, Jan-Mar, Apr-Jun
due_date                  DATE NOT NULL                 -- Payment due date
pct_of_total              NUMERIC(5, 2) NOT NULL        -- Percentage of annual tuition
academic_year             VARCHAR(20) NOT NULL
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- trimester IN (1, 2, 3)
- pct_of_total between 0 and 100
- SUM(pct_of_total) across all trimesters should equal 100 for each academic year
- UNIQUE (version_id, trimester, academic_year)

**RLS Policies:**
- All authenticated users can read payment schedule
- Only admins can modify payment schedule

**Indexes:**
- Primary key on id
- Index on (version_id, academic_year)

### Enums

#### NationalityCategory
```sql
CREATE TYPE efir_budget.nationalitycategory AS ENUM (
    'french',          -- French nationals (TTC - tax inclusive)
    'saudi',           -- Saudi nationals (HT - tax exempt)
    'other'            -- Other nationalities (TTC)
);
```

#### VATTreatment
```sql
CREATE TYPE efir_budget.vattreatment AS ENUM (
    'ttc',             -- Toutes Taxes Comprises (tax inclusive)
    'ht'               -- Hors Taxe (tax exempt)
);
```

#### ExamType
```sql
CREATE TYPE efir_budget.examtype AS ENUM (
    'dnb',             -- Diplôme National du Brevet (3ème)
    'ea',              -- Épreuves Anticipées (1ère - French exam)
    'baccalaureat'     -- Baccalauréat (Terminale)
);
```

#### DiscountType
```sql
CREATE TYPE efir_budget.discounttype AS ENUM (
    'sibling',         -- Family discount (3rd+ child)
    'staff',           -- Staff discount (employees)
    'scholarship',     -- Need-based scholarship
    'other'            -- Other special discounts
);
```

## Data Model

### Sample Fee Structure (2025-2026)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440500",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "level_id": "level-maternelle-ps-uuid",
    "nationality_category": "french",
    "annual_tuition_sar": 30000.00,
    "vat_treatment": "ttc",
    "dai_fee_sar": 5000.00,
    "registration_fee_sar": 1150.00,
    "first_enrollment_fee_sar": 2300.00,
    "academic_year": "2025-2026",
    "effective_date": "2025-09-01",
    "notes": "Maternelle PS - French nationals"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440501",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "level_id": "level-lycee-terminale-uuid",
    "nationality_category": "other",
    "annual_tuition_sar": 46000.00,
    "vat_treatment": "ttc",
    "dai_fee_sar": 5000.00,
    "registration_fee_sar": 1150.00,
    "first_enrollment_fee_sar": 2300.00,
    "academic_year": "2025-2026",
    "effective_date": "2025-09-01",
    "notes": "Lycée Terminale - Other nationalities (highest tier)"
  }
]
```

### Complete Fee Matrix (2025-2026)

| Level | French (TTC) | Saudi (HT) | Other (TTC) | DAI | Registration | First Enrollment |
|-------|--------------|------------|-------------|-----|--------------|------------------|
| Maternelle PS | 30,000 | 34,783 | 40,000 | 5,000 | 1,150 | 2,300 |
| Maternelle MS-GS | 34,500 | 35,650 | 41,000 | 5,000 | 1,150 | 2,300 |
| Élémentaire | 34,500 | 35,650 | 41,000 | 5,000 | 1,150 | 2,300 |
| Collège | 34,500 | 35,650 | 41,000 | 5,000 | 1,150 | 2,300 |
| Lycée | 38,500 | 40,000 | 46,000 | 5,000 | 1,150 | 2,300 |

### Sample Exam Fees

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440510",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "exam_type": "dnb",
    "nationality_category": "french",
    "exam_fee_sar": 287.50,
    "academic_year": "2025-2026",
    "notes": "DNB exam fee for 3ème students"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440511",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "exam_type": "baccalaureat",
    "nationality_category": "french",
    "exam_fee_sar": 1495.00,
    "academic_year": "2025-2026",
    "notes": "Baccalauréat exam fee for Terminale students"
  }
]
```

### Sample Discount Rules

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440520",
  "version_id": "123e4567-e89b-12d3-a456-426614174000",
  "discount_type": "sibling",
  "discount_name": "Sibling Discount (3rd+ Child)",
  "discount_pct": 25.00,
  "discount_amount_fixed_sar": null,
  "applies_to": "tuition",
  "min_conditions": {
    "sibling_rank": 3,
    "note": "Applies to 3rd, 4th, 5th+ child in family"
  },
  "max_discount_sar": null,
  "requires_approval": false,
  "is_active": true,
  "effective_date": "2025-09-01",
  "notes": "Automatic 25% discount on tuition only (not DAI or registration)"
}
```

### Sample Payment Schedule

```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440530",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "trimester": 1,
    "period_name": "T1",
    "period_months": "Sep-Dec",
    "due_date": "2025-08-20",
    "pct_of_total": 40.00,
    "academic_year": "2025-2026"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440531",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "trimester": 2,
    "period_name": "T2",
    "period_months": "Jan-Mar",
    "due_date": "2026-01-01",
    "pct_of_total": 30.00,
    "academic_year": "2025-2026"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440532",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "trimester": 3,
    "period_name": "T3",
    "period_months": "Apr-Jun",
    "due_date": "2026-04-01",
    "pct_of_total": 30.00,
    "academic_year": "2025-2026"
  }
]
```

## Business Rules

### Fee Structure Rules

1. **Nationality-Based Pricing**: Three distinct pricing tiers based on nationality and VAT treatment
   - French: TTC (tax inclusive) - lowest tier
   - Saudi: HT (tax exempt/hors taxe) - middle tier (adjusted for VAT exemption)
   - Other: TTC (tax inclusive) - highest tier

2. **Level-Based Progression**: Fees increase from Maternelle to Lycée
   - Maternelle PS: Lowest (youngest students)
   - MS-GS through Collège: Mid-tier (consistent across primary and middle school)
   - Lycée: Highest (preparation for Baccalauréat, highest value)

3. **DAI Standardization**: Enrollment fee (DAI) is 5,000 SAR across all levels and nationalities

4. **Fee Immutability**: Once academic year begins, fees cannot be changed for enrolled students (new fee structures apply to new enrollments only)

5. **Annual Review**: Fee structures reviewed and approved annually before enrollment period (typically March-April for September start)

### Discount Rules

1. **Sibling Discount**:
   - 25% discount on tuition for 3rd, 4th, 5th+ child
   - Applies to tuition only (not DAI, registration, or exam fees)
   - Automatic application (no approval required)
   - All siblings must be currently enrolled at EFIR

2. **Staff Discount**:
   - Varies by position and tenure
   - Requires HR approval
   - Manual tracking and application

3. **Scholarship Discount**:
   - Case-by-case basis
   - Requires financial need assessment
   - Requires Board approval for amounts > 50%

4. **Discount Stacking**: Sibling discount can be combined with staff discount (max combined 50%)

5. **Discount Application Order**:
   1. Calculate gross tuition
   2. Apply sibling discount (if applicable)
   3. Apply staff/scholarship discount (if applicable)
   4. Add DAI and other fees (no discounts)

### Payment Schedule Rules

1. **Trimester Distribution**: 40% (T1) + 30% (T2) + 30% (T3) = 100%

2. **Payment Timing**:
   - T1: Due August 20 (before school year starts)
   - T2: Due January 1
   - T3: Due April 1

3. **Late Payment**: Late fees and policies managed separately (not in this module)

4. **Refund Policy**: Pro-rated refunds based on trimester (managed in finance module)

### Exam Fee Rules

1. **DNB (3ème)**: Required for all 3ème students (Diplôme National du Brevet)
2. **E.A. (1ère)**: Required for all 1ère students (Épreuves Anticipées - French exam)
3. **Baccalauréat (Terminale)**: Required for all Terminale students
4. **Nationality-Based**: Different fees for French/Saudi/Other (TTC vs HT)
5. **Exam Opt-Out**: Exam fees only charged for students taking the exam (some may opt for alternative qualifications)

### Validation Rules

1. **Positive Fees**: All fees must be > 0 (cannot have negative or zero tuition)
2. **Trimester Total**: Payment schedule percentages must sum to 100%
3. **Discount Bounds**: Discount percentages between 0% and 100%
4. **Fee Consistency**: Fees within reasonable ranges (e.g., Lycée > Maternelle)
5. **Academic Year Format**: Academic year format "YYYY-YYYY" (e.g., "2025-2026")

## Calculation Examples

### Example 1: Single Student Revenue (Collège, French, Returning)

**Context**: Calculate annual revenue for a returning French student in Collège.

**Given Data:**
- Level: Collège
- Nationality: French
- Tuition: 34,500 SAR (TTC)
- DAI: 5,000 SAR
- Registration: 0 SAR (returning student)
- First Enrollment: 0 SAR (not first time)
- Sibling rank: 1 (first child, no discount)

**Calculation:**
```
Gross tuition:         34,500 SAR
Sibling discount:           0 SAR (1st child)
Net tuition:           34,500 SAR
DAI:                    5,000 SAR
Registration:               0 SAR
First Enrollment:           0 SAR
─────────────────────────────────
Total annual revenue:  39,500 SAR
```

**Result:** Annual revenue per student = 39,500 SAR

### Example 2: New Student Revenue (Lycée, Other, 1st Child)

**Context**: Calculate annual revenue for a new "Other" nationality student in Lycée.

**Given Data:**
- Level: Lycée
- Nationality: Other
- Tuition: 46,000 SAR (TTC - highest tier)
- DAI: 5,000 SAR
- Registration: 1,150 SAR (new student)
- First Enrollment: 2,300 SAR (first time at EFIR)
- Sibling rank: 1 (no discount)

**Calculation:**
```
Gross tuition:         46,000 SAR
Sibling discount:           0 SAR
Net tuition:           46,000 SAR
DAI:                    5,000 SAR
Registration:           1,150 SAR
First Enrollment:       2,300 SAR
─────────────────────────────────
Total annual revenue:  54,450 SAR
```

**Result:** Annual revenue for new Lycée student = 54,450 SAR (highest revenue per student)

### Example 3: Family with 3 Children (Sibling Discount)

**Context**: Calculate total revenue for a family with 3 children (French nationality).

**Family Structure:**
- Child 1: Lycée (38,500 SAR tuition)
- Child 2: Collège (34,500 SAR tuition)
- Child 3: Élémentaire (34,500 SAR tuition) - eligible for 25% discount
- All returning students (no registration/first enrollment fees)

**Calculation:**
```
Child 1 (Lycée, 1st child, no discount):
  Tuition:     38,500 SAR
  DAI:          5,000 SAR
  Subtotal:    43,500 SAR

Child 2 (Collège, 2nd child, no discount):
  Tuition:     34,500 SAR
  DAI:          5,000 SAR
  Subtotal:    39,500 SAR

Child 3 (Élémentaire, 3rd child, 25% sibling discount):
  Gross tuition:          34,500 SAR
  Sibling discount (25%):  8,625 SAR
  Net tuition:            25,875 SAR
  DAI:                     5,000 SAR
  Subtotal:               30,875 SAR

Total family revenue: 43,500 + 39,500 + 30,875 = 113,875 SAR/year
```

**Result:** Family with 3 children pays 113,875 SAR/year (savings of 8,625 SAR from sibling discount).

**Discount Impact:**
- Without discount: 122,500 SAR
- With 25% on 3rd child: 113,875 SAR
- Savings: 8,625 SAR (7% reduction)

### Example 4: Trimester Payment Distribution

**Context**: Distribute annual tuition across 3 trimesters for payment schedule.

**Given Data:**
- Annual tuition: 34,500 SAR
- Payment schedule: T1 (40%), T2 (30%), T3 (30%)

**Calculation:**
```
Total annual tuition: 34,500 SAR

T1 (Sep-Dec, 40%): 34,500 × 0.40 = 13,800 SAR (due Aug 20)
T2 (Jan-Mar, 30%): 34,500 × 0.30 = 10,350 SAR (due Jan 1)
T3 (Apr-Jun, 30%): 34,500 × 0.30 = 10,350 SAR (due Apr 1)
──────────────────────────────────────────────────────
Total:                             34,500 SAR ✓
```

**Result:** Payment installments: 13,800 SAR (T1) + 10,350 SAR (T2) + 10,350 SAR (T3)

**Cash Flow Impact:**
- August 20, 2025: 13,800 SAR received
- January 1, 2026: 10,350 SAR received
- April 1, 2026: 10,350 SAR received

## Integration Points

### Upstream Dependencies

1. **Module 1 (System Configuration)**: Academic structure (levels for fee matrix)
2. **Module 13 (Budget Consolidation)**: Budget version for fee structure versioning

### Downstream Consumers

1. **Module 10 (Revenue Planning)**: PRIMARY CONSUMER - uses fee structure to calculate tuition revenue from enrollment projections
2. **Module 7 (Enrollment Planning)**: Fee structure informs enrollment targets and affordability analysis
3. **Module 13 (Budget Consolidation)**: Revenue rollup from Module 10
4. **Module 14 (Financial Statements)**: Revenue recognition by account code (70110, 70120, 70130, 70140)

### Data Flow

```
Academic Structure (Module 1) → Fee Structure (Module 5)
                                        ↓
              Enrollment by Level × Nationality (Module 7)
                                        ↓
                Revenue Calculation (Module 10)
      Enrollment × Fees - Discounts = Gross Tuition Revenue
                                        ↓
                 Account Mapping (Module 14)
         70110 (T1), 70120 (T2), 70130 (T3), 70140 (DAI)
```

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
# Fee Structure
GET    /api/v1/budget-versions/:id/fee-structure          # Get complete fee matrix
GET    /api/v1/budget-versions/:id/fee-structure/level/:level_id  # Fees for specific level
POST   /api/v1/budget-versions/:id/fee-structure          # Create fee entry
PUT    /api/v1/budget-versions/:id/fee-structure/:fee_id  # Update fee
DELETE /api/v1/budget-versions/:id/fee-structure/:fee_id  # Delete fee

# Exam Fees
GET    /api/v1/budget-versions/:id/exam-fees              # Get all exam fees
POST   /api/v1/budget-versions/:id/exam-fees              # Create exam fee

# Discount Rules
GET    /api/v1/budget-versions/:id/discount-rules         # Get all discount rules
GET    /api/v1/discount-rules/active                      # Get active discounts
POST   /api/v1/budget-versions/:id/discount-rules         # Create discount rule

# Revenue Calculations
POST   /api/v1/calculate-student-revenue                  # Calculate revenue for single student
       Request: { level_id, nationality, is_new, sibling_rank }
       Response: { gross_tuition, discounts, net_tuition, total_revenue }

POST   /api/v1/calculate-family-revenue                   # Calculate revenue for family
       Request: { students: [{level_id, nationality, ...}] }
       Response: { total_family_revenue, total_discounts, breakdown_by_child }

# Payment Schedule
GET    /api/v1/budget-versions/:id/payment-schedule       # Get trimester schedule
PUT    /api/v1/budget-versions/:id/payment-schedule       # Update payment percentages
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify fee_structure, exam_fees, discount_rules models
2. **Enum Tests**: Verify NationalityCategory, VATTreatment, ExamType, DiscountType enums
3. **Calculation Tests**: Test revenue calculation formulas

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for different roles
2. **Discount Application Tests**: Test discount calculation logic
3. **Payment Schedule Tests**: Verify trimester distribution

### Test Scenarios

#### Scenario 1: Create Fee Structure Entry

**Objective:** Create fee structure record for a level-nationality combination.

**Test Data:**
```typescript
const feeEntry = {
  version_id: testVersion.id,
  level_id: collegeLevel.id,
  nationality_category: NationalityCategory.FRENCH,
  annual_tuition_sar: 34500.00,
  vat_treatment: VATTreatment.TTC,
  dai_fee_sar: 5000.00,
  registration_fee_sar: 1150.00,
  first_enrollment_fee_sar: 2300.00,
  academic_year: "2025-2026",
  effective_date: new Date("2025-09-01")
};
```

**Expected Behavior:**
- Record created successfully
- Unique constraint prevents duplicates

**Example Test Code:**
```typescript
import { describe, it, expect } from 'vitest';
import { FeeStructure, NationalityCategory, VATTreatment } from '@/models';

describe('Fee Structure', () => {
  it('should create fee structure entry', async () => {
    const fee = await FeeStructure.create({
      version_id: testVersion.id,
      level_id: collegeLevel.id,
      nationality_category: NationalityCategory.FRENCH,
      annual_tuition_sar: 34500.00,
      vat_treatment: VATTreatment.TTC,
      dai_fee_sar: 5000.00,
      academic_year: "2025-2026",
      effective_date: new Date("2025-09-01")
    });

    expect(fee.id).toBeDefined();
    expect(fee.annual_tuition_sar).toBe(34500.00);
  });
});
```

#### Scenario 2: Sibling Discount Calculation

**Objective:** Test 25% sibling discount on 3rd child tuition.

**Test Data:**
```typescript
const tuition = 34500;
const siblingRank = 3;
const discountPct = 25;
```

**Expected Behavior:**
- 3rd child gets 25% discount
- Discount = 8,625 SAR
- Net tuition = 25,875 SAR

**Example Test Code:**
```typescript
describe('Sibling Discount Calculation', () => {
  it('should apply 25% discount to 3rd+ child tuition', () => {
    const tuition = 34500;
    const siblingRank = 3;

    const discount = siblingRank >= 3 ? tuition * 0.25 : 0;
    const netTuition = tuition - discount;

    expect(discount).toBe(8625);
    expect(netTuition).toBe(25875);
  });

  it('should not apply discount to 1st or 2nd child', () => {
    const tuition = 34500;

    const discount1st = 1 >= 3 ? tuition * 0.25 : 0;
    const discount2nd = 2 >= 3 ? tuition * 0.25 : 0;

    expect(discount1st).toBe(0);
    expect(discount2nd).toBe(0);
  });
});
```

#### Scenario 3: Family Revenue Calculation

**Objective:** Calculate total revenue for family with 3 children including sibling discount.

**Test Data:**
```typescript
const family = [
  { level: "Lycée", tuition: 38500, siblingRank: 1 },
  { level: "Collège", tuition: 34500, siblingRank: 2 },
  { level: "Élémentaire", tuition: 34500, siblingRank: 3 }
];
const daiPerChild = 5000;
```

**Expected Behavior:**
- Total revenue = 113,875 SAR
- Discount savings = 8,625 SAR

**Example Test Code:**
```typescript
describe('Family Revenue Calculation', () => {
  it('should calculate total family revenue with sibling discount', () => {
    const children = [
      { tuition: 38500, siblingRank: 1, dai: 5000 },
      { tuition: 34500, siblingRank: 2, dai: 5000 },
      { tuition: 34500, siblingRank: 3, dai: 5000 }
    ];

    let totalRevenue = 0;
    let totalDiscount = 0;

    children.forEach(child => {
      const discount = child.siblingRank >= 3 ? child.tuition * 0.25 : 0;
      const netTuition = child.tuition - discount;
      totalRevenue += netTuition + child.dai;
      totalDiscount += discount;
    });

    expect(totalDiscount).toBe(8625);
    expect(totalRevenue).toBe(113875);
  });
});
```

#### Scenario 4: Payment Schedule Distribution

**Objective:** Validate trimester payment distribution sums to 100%.

**Test Data:**
```typescript
const paymentSchedule = [
  { trimester: 1, pct: 40 },
  { trimester: 2, pct: 30 },
  { trimester: 3, pct: 30 }
];
```

**Expected Behavior:**
- Sum of percentages = 100%

**Example Test Code:**
```typescript
describe('Payment Schedule Validation', () => {
  it('should validate trimester percentages sum to 100', () => {
    const schedule = [
      { trimester: 1, pct: 40 },
      { trimester: 2, pct: 30 },
      { trimester: 3, pct: 30 }
    ];

    const total = schedule.reduce((sum, t) => sum + t.pct, 0);

    expect(total).toBe(100);
  });
});
```

#### Scenario 5: New Student Revenue (All Fees)

**Objective:** Calculate revenue for new student including all one-time fees.

**Test Data:**
```typescript
const newStudent = {
  level: "Lycée",
  nationality: "Other",
  tuition: 46000,
  dai: 5000,
  registration: 1150,
  firstEnrollment: 2300,
  isNew: true,
  siblingRank: 1
};
```

**Expected Behavior:**
- Total revenue = 54,450 SAR

**Example Test Code:**
```typescript
describe('New Student Revenue', () => {
  it('should include all fees for new student', () => {
    const student = {
      tuition: 46000,
      dai: 5000,
      registration: 1150,
      firstEnrollment: 2300,
      isNew: true,
      siblingRank: 1
    };

    const discount = student.siblingRank >= 3 ? student.tuition * 0.25 : 0;
    const netTuition = student.tuition - discount;

    const total = netTuition + student.dai +
                  (student.isNew ? student.registration + student.firstEnrollment : 0);

    expect(total).toBe(54450);
  });
});
```

#### Scenario 6: Fee Level Progression Validation

**Objective:** Ensure Lycée fees > Collège fees > Maternelle fees.

**Test Data:**
```typescript
const fees = {
  maternellePS: { french: 30000, other: 40000 },
  college: { french: 34500, other: 41000 },
  lycee: { french: 38500, other: 46000 }
};
```

**Expected Behavior:**
- Lycée > Collège > Maternelle PS for each nationality

**Example Test Code:**
```typescript
describe('Fee Level Progression', () => {
  it('should enforce Lycée > Collège > Maternelle fee structure', () => {
    const fees = {
      maternellePS: { french: 30000, other: 40000 },
      college: { french: 34500, other: 41000 },
      lycee: { french: 38500, other: 46000 }
    };

    // French fees
    expect(fees.lycee.french).toBeGreaterThan(fees.college.french);
    expect(fees.college.french).toBeGreaterThan(fees.maternellePS.french);

    // Other fees
    expect(fees.lycee.other).toBeGreaterThan(fees.college.other);
    expect(fees.college.other).toBeGreaterThan(fees.maternellePS.other);
  });
});
```

#### Scenario 7: RLS Policy - Manager Access

**Objective:** Verify managers can modify fee structure for working budget versions.

**Expected Behavior:**
- Manager can read/write fees for working versions
- Manager has read-only access to approved versions

**Example Test Code:**
```python
def test_rls_manager_fee_structure():
    """Test manager can modify fee structure for working versions."""
    # Setup: working budget version
    working_version = create_working_budget_version()

    # Authenticate as manager
    set_user_role("manager")

    # Manager can create fee entry
    fee = FeeStructure(
        version_id=working_version.id,
        level_id=college_level.id,
        nationality_category=NationalityCategory.FRENCH,
        annual_tuition_sar=Decimal("34500.00"),
        vat_treatment=VATTreatment.TTC,
        dai_fee_sar=Decimal("5000.00"),
        academic_year="2025-2026"
    )
    db.session.add(fee)
    db.session.commit()

    assert fee.id is not None

    # Manager can update fee
    fee.annual_tuition_sar = Decimal("35000.00")
    db.session.commit()

    refreshed = db.session.query(FeeStructure).filter_by(id=fee.id).first()
    assert refreshed.annual_tuition_sar == Decimal("35000.00")
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: fee_structure, exam_fees, discount_rules, payment_schedule tables with RLS policies |

## Future Enhancements (Phase 5-6)

1. **Fee Calculator UI**: Interactive tool for modeling revenue scenarios with different fee structures
2. **Discount Manager**: Visual interface for managing and approving discounts
3. **Family Portal Integration**: Allow families to view fees and payment schedule online
4. **Fee Comparison Tool**: Compare EFIR fees to other AEFE schools in region
5. **Revenue Forecasting**: Project revenue based on enrollment targets and fee assumptions
6. **Payment Plan Options**: Support custom payment plans (monthly, quarterly)
7. **Scholarship Workflow**: Automated workflow for scholarship application and approval
8. **Fee Increase Modeling**: Model impact of fee increases on enrollment and revenue
9. **Multi-Currency Support**: Display fees in EUR, USD for international families
10. **Historical Fee Tracking**: Trend analysis of fee changes over multiple years

## Notes

- **Phase 4 Scope**: This module implements database foundation (tables, constraints, RLS policies, migrations)
- **Business Logic**: Revenue calculation engine and fee management UI will be implemented in Phases 5-6
- **DAI (Droit Annuel d'Inscription)**: Mandatory annual enrollment fee, standardized at 5,000 SAR
- **Sibling Discount Exclusion**: 25% discount applies only to tuition, not DAI, registration, or exam fees
- **VAT Treatment**: French and Other pay TTC (tax inclusive), Saudi pay HT (tax exempt) with adjusted pricing
- **Nationality Distribution**: EFIR student body is ~32% French, ~4% Saudi, ~64% Other (pricing reflects market positioning)
- **Revenue Driver**: Tuition fees are the PRIMARY revenue source (~80-90% of total revenue)
- **Affordability Balance**: Fee structure balances mission (accessible French education) with financial sustainability
- **Competitive Positioning**: EFIR fees competitive with other international schools in Riyadh while maintaining AEFE quality standards
