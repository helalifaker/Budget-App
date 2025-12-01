# Module 10: Revenue Planning

## Overview

Module 10 projects all revenue streams for the school budget based on enrollment forecasts and fee structures. This module calculates tuition revenue by nationality category and level, registration fees, enrollment fees for new students, sibling discounts, and other revenue sources (cafeteria, extracurricular activities, facility rentals). Revenue is recognized by trimester following French accounting standards (40% T1, 30% T2, 30% T3).

**Layer**: Planning Layer (Phase 2)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Revenue optimization, payment tracking integration, API endpoints (Phase 5-6)

### Purpose

- Calculate tuition revenue from enrollment projections (Module 7) and fee structures (Module 5)
- Project registration fees (DAI - Droit Annuel d'Inscription) for all students
- Calculate enrollment fees for new students only
- Apply sibling discounts (25% on tuition for 3rd+ child, excluding DAI and enrollment fees)
- Track other revenue sources (cafeteria, extracurricular, facility rentals)
- Recognize revenue by trimester (T1: 40%, T2: 30%, T3: 30%)
- Map revenue to French PCG account codes (70xxx-77xxx series)
- Support scenario analysis for revenue projections

### Key Design Decisions

1. **Driver-Based Calculation**: Revenue automatically calculated from enrollment × fee structures
2. **Nationality-Based Pricing**: Three fee tiers (French TTC, Saudi HT, Other TTC) from Module 5
3. **New vs. Returning**: Enrollment fees charged only to new students
4. **Sibling Discount Logic**: 25% discount on tuition for 3rd+ child (not DAI, not enrollment fees)
5. **Trimester Recognition**: Revenue split 40%/30%/30% across T1/T2/T3 for accounting compliance
6. **Dual Period Structure**: Separate revenue projections for Period 1 (Jan-Jun) and Period 2 (Sep-Dec)
7. **PCG Account Mapping**: Tuition → 70110 (T1), 70120 (T2), 70130 (T3); DAI → 70210; Enrollment → 70220

## Database Schema

### Tables

#### 1. revenue_projections

Detailed revenue projections by source, period, and trimester.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
revenue_category      revenuecategory NOT NULL       -- ENUM: tuition, dai, enrollment, other
revenue_subcategory   VARCHAR(100) NULL              -- e.g., "Cafeteria", "Extracurricular"
account_code          VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
trimester             INTEGER NULL                   -- 1, 2, 3 (NULL for non-tuition revenue)
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
- trimester IN (1, 2, 3) OR trimester IS NULL
- If revenue_category = 'tuition', then trimester IS NOT NULL
- account_code must start with '70', '71', '74', '75', '76', or '77' (revenue accounts)
- UNIQUE (budget_version_id, academic_period_id, revenue_category, account_code, trimester)

**RLS Policies:**
- Admin: Full access to revenue planning
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (budget_version_id, academic_period_id, revenue_category)
- Index on account_code for financial consolidation
- Index on trimester for revenue recognition reporting

#### 2. tuition_revenue_detail

Granular tuition revenue breakdown by level and nationality.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
level_id              UUID NOT NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
nationality_category  nationalitycategory NOT NULL
student_count         INTEGER NOT NULL
fee_per_student       NUMERIC(10, 2) NOT NULL
sibling_discount_pct  NUMERIC(5, 2) NOT NULL DEFAULT 0
total_revenue_gross   NUMERIC(12, 2) NOT NULL
total_discount        NUMERIC(12, 2) NOT NULL DEFAULT 0
total_revenue_net     NUMERIC(12, 2) NOT NULL
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- student_count >= 0
- fee_per_student >= 0
- sibling_discount_pct >= 0 AND sibling_discount_pct <= 100
- total_revenue_gross = student_count × fee_per_student
- total_discount = total_revenue_gross × (sibling_discount_pct / 100)
- total_revenue_net = total_revenue_gross - total_discount
- UNIQUE (budget_version_id, academic_period_id, level_id, nationality_category)

**RLS Policies:**
- Same as revenue_projections

**Indexes:**
- Primary key on id
- Index on (budget_version_id, academic_period_id)
- Index on level_id for level-based aggregation
- Index on nationality_category for nationality analysis

#### 3. other_revenue_sources

Non-tuition revenue sources (cafeteria, extracurricular, rentals).

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
revenue_source_name   VARCHAR(200) NOT NULL
revenue_driver        VARCHAR(100) NULL              -- e.g., "per_student", "per_meal", "fixed"
driver_quantity       NUMERIC(10, 2) NULL
revenue_per_unit      NUMERIC(10, 2) NOT NULL
total_revenue         NUMERIC(12, 2) NOT NULL
account_code          VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- revenue_per_unit >= 0
- total_revenue >= 0
- If revenue_driver IS NOT NULL, then total_revenue = driver_quantity × revenue_per_unit
- account_code must start with '70', '74', '75', '76', or '77'

**RLS Policies:**
- Same as revenue_projections

**Indexes:**
- Primary key on id
- Index on (budget_version_id, academic_period_id)
- Index on account_code

### Enums

#### RevenueCategory
```sql
CREATE TYPE efir_budget.revenuecategory AS ENUM (
    'tuition',          -- Scolarité (tuition fees)
    'dai',              -- Droit Annuel d'Inscription (annual registration fee)
    'enrollment',       -- Frais d'inscription (one-time enrollment fee for new students)
    'other'             -- Cafeteria, extracurricular, rentals, etc.
);
```

## Data Model

### Sample Revenue Projections (2025-2026, Period 2)

```json
[
  {
    "id": "770e8400-e29b-41d4-a716-446655440100",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "revenue_category": "tuition",
    "revenue_subcategory": "Tuition - All levels",
    "account_code": "70110",
    "trimester": 1,
    "amount": 10560000.00,
    "currency": "SAR",
    "notes": "T1 tuition revenue (40% of annual)"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440101",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "revenue_category": "dai",
    "revenue_subcategory": "Annual Registration (DAI)",
    "account_code": "70210",
    "trimester": null,
    "amount": 950000.00,
    "currency": "SAR",
    "notes": "DAI: 1,900 students × 500 SAR average"
  },
  {
    "id": "770e8400-e29b-41d4-a716-446655440102",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "revenue_category": "enrollment",
    "revenue_subcategory": "New Student Enrollment Fees",
    "account_code": "70220",
    "trimester": null,
    "amount": 225000.00,
    "currency": "SAR",
    "notes": "Enrollment fees: 150 new students × 1,500 SAR"
  }
]
```

### Sample Tuition Revenue Detail (6ème, Period 2)

```json
[
  {
    "id": "880e8400-e29b-41d4-a716-446655440200",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "level_id": "level-6eme-uuid",
    "nationality_category": "french",
    "student_count": 46,
    "fee_per_student": 11000.00,
    "sibling_discount_pct": 5.00,
    "total_revenue_gross": 506000.00,
    "total_discount": 25300.00,
    "total_revenue_net": 480700.00,
    "currency": "SAR",
    "notes": "6ème French students with 5% avg sibling discount"
  },
  {
    "id": "880e8400-e29b-41d4-a716-446655440201",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "level_id": "level-6eme-uuid",
    "nationality_category": "other",
    "student_count": 99,
    "fee_per_student": 18500.00,
    "sibling_discount_pct": 4.00,
    "total_revenue_gross": 1831500.00,
    "total_discount": 73260.00,
    "total_revenue_net": 1758240.00,
    "currency": "SAR",
    "notes": "6ème Other nationality with 4% avg sibling discount"
  }
]
```

### Historical Revenue Trends (EFIR Actual Data)

| Academic Year | Enrollment | Tuition Revenue (SAR) | DAI Revenue (SAR) | Other Revenue (SAR) | Total Revenue (SAR) |
|---------------|------------|----------------------|------------------|---------------------|---------------------|
| 2021-2022 | 1,434 | 21,510,000 | 717,000 | 430,200 | 22,657,200 |
| 2022-2023 | 1,499 | 22,485,000 | 749,500 | 449,700 | 23,684,200 |
| 2023-2024 | 1,587 | 23,805,000 | 793,500 | 476,100 | 25,074,600 |
| 2024-2025 | 1,796 | 26,940,000 | 898,000 | 538,800 | 28,376,800 |
| 2025-2026 (proj) | 1,900 | 28,500,000 | 950,000 | 570,000 | 30,020,000 |

**Revenue Growth Rate (2024-2025 → 2025-2026)**: +5.8%

### Fee Structure by Nationality (2025-2026)

| Level | French TTC (SAR) | Saudi HT (SAR) | Other TTC (SAR) |
|-------|------------------|----------------|-----------------|
| Maternelle (PS-GS) | 8,800 | 14,520 | 14,520 |
| Élémentaire (CP-CM2) | 9,900 | 16,335 | 16,335 |
| Collège (6ème-3ème) | 11,000 | 18,150 | 18,500 |
| Lycée (2nde-Terminale) | 12,100 | 19,965 | 22,275 |

**DAI (Annual Registration)**: 500 SAR per student (all nationalities)
**Enrollment Fee**: 1,500 SAR per new student (one-time)

## Business Rules

### Tuition Revenue Rules

1. **Auto-Calculation**: Tuition revenue = Σ(enrollment × fee) by level and nationality
2. **Nationality Pricing**: Three tiers based on Module 5 fee structure
   - French: TTC pricing (includes tax, lowest tier)
   - Saudi: HT pricing (tax-exempt, middle tier)
   - Other: TTC pricing (highest tier)
3. **Sibling Discount**: 25% on tuition for 3rd child and beyond
   - Applied only to tuition fees
   - **Not** applied to DAI or enrollment fees
   - Calculated per family (requires family grouping)
4. **Trimester Recognition**: Revenue split across 3 trimesters
   - T1 (Sep-Dec): 40% of annual tuition
   - T2 (Jan-Mar): 30% of annual tuition
   - T3 (Apr-Jun): 30% of annual tuition
5. **Account Code Mapping**:
   - Tuition T1: 70110 (Ventes de produits finis - Trimestre 1)
   - Tuition T2: 70120 (Ventes de produits finis - Trimestre 2)
   - Tuition T3: 70130 (Ventes de produits finis - Trimestre 3)

### DAI (Registration Fee) Rules

1. **Universal Application**: All students pay DAI (new and returning)
2. **Flat Rate**: 500 SAR per student (all levels, all nationalities)
3. **No Discount**: Sibling discount does NOT apply to DAI
4. **Single Payment**: Paid once per year (typically at enrollment confirmation)
5. **Account Code**: 70210 (Prestations de services - DAI)

### Enrollment Fee Rules

1. **New Students Only**: Charged only to new enrollments (not returning students)
2. **One-Time Fee**: 1,500 SAR per new student
3. **No Discount**: Sibling discount does NOT apply to enrollment fees
4. **Account Code**: 70220 (Prestations de services - Inscription)

### Other Revenue Rules

1. **Cafeteria Revenue**: Typically 20-30% of students participate
   - Driver: per_student participating
   - Average: 150 SAR per student per month
2. **Extracurricular Activities**: Optional programs (sports, music, art)
   - Driver: per_enrollment
   - Average: 500-2,000 SAR per activity per student per year
3. **Facility Rentals**: Renting school facilities to external organizations
   - Driver: per_event or fixed monthly
   - Account code: 75200 (Revenus des immeubles non affectés)

### Validation Rules

1. **Positive Revenue**: All revenue amounts must be >= 0
2. **Trimester Sum**: T1 + T2 + T3 must equal 100% of annual tuition
3. **Enrollment Match**: Student counts must match Module 7 enrollment projections
4. **Fee Consistency**: Fees must match Module 5 fee structure configuration
5. **Discount Bounds**: Sibling discount percentage between 0% and 25%
6. **Account Code Validity**: Revenue accounts must be 70xxx-77xxx series

## Calculation Examples

### Example 1: Tuition Revenue for 6ème (Collège)

**Context**: Calculate total tuition revenue for 6ème level in Period 2.

**Given Data** (from Module 7 enrollment):
- French students: 46
- Saudi students: 0
- Other students: 99
- Total: 145 students

**Fee Structure** (from Module 5):
- French TTC: 11,000 SAR
- Saudi HT: 18,150 SAR
- Other TTC: 18,500 SAR

**Sibling Discount Assumptions**:
- French: 5% average (weighted discount across all families)
- Other: 4% average

**Calculation:**
```
French revenue (gross) = 46 × 11,000 = 506,000 SAR
French discount = 506,000 × 5% = 25,300 SAR
French revenue (net) = 506,000 - 25,300 = 480,700 SAR

Saudi revenue = 0 × 18,150 = 0 SAR

Other revenue (gross) = 99 × 18,500 = 1,831,500 SAR
Other discount = 1,831,500 × 4% = 73,260 SAR
Other revenue (net) = 1,831,500 - 73,260 = 1,758,240 SAR

Total 6ème tuition revenue (net) = 480,700 + 0 + 1,758,240 = 2,238,940 SAR
```

**Result**: 2,238,940 SAR annual tuition revenue for 6ème

### Example 2: Trimester Revenue Recognition (6ème)

**Context**: Recognize 6ème tuition revenue across 3 trimesters.

**Given Data**:
- Total annual tuition (6ème): 2,238,940 SAR (from Example 1)

**Trimester Split** (40%/30%/30%):
```
T1 revenue (40%) = 2,238,940 × 0.40 = 895,576 SAR → Account 70110
T2 revenue (30%) = 2,238,940 × 0.30 = 671,682 SAR → Account 70120
T3 revenue (30%) = 2,238,940 × 0.30 = 671,682 SAR → Account 70130

Total: 895,576 + 671,682 + 671,682 = 2,238,940 SAR ✓
```

**Result**:
- T1 (Sep-Dec): 895,576 SAR
- T2 (Jan-Mar): 671,682 SAR
- T3 (Apr-Jun): 671,682 SAR

### Example 3: DAI Revenue (All Students)

**Context**: Calculate total DAI revenue for all enrolled students.

**Given Data**:
- Total enrollment: 1,900 students (all levels)
- DAI fee: 500 SAR per student

**Calculation:**
```
DAI revenue = 1,900 students × 500 SAR = 950,000 SAR

Account code: 70210 (DAI)
No trimester split (recognized once per year)
```

**Result**: 950,000 SAR total DAI revenue

### Example 4: Enrollment Fee Revenue (New Students Only)

**Context**: Calculate enrollment fee revenue from new students.

**Given Data** (from Module 7):
- Total enrollment: 1,900 students
- New students: 150 (returning students: 1,750)
- Enrollment fee: 1,500 SAR per new student

**Calculation:**
```
Enrollment fee revenue = 150 new students × 1,500 SAR = 225,000 SAR

Account code: 70220 (Inscription)
No trimester split (one-time payment at enrollment)
```

**Result**: 225,000 SAR enrollment fee revenue

### Example 5: Total Revenue Projection (2025-2026)

**Context**: Calculate total school revenue for 2025-2026 academic year.

**Given Data**:
- Tuition revenue (all levels): 28,500,000 SAR (calculated from full enrollment × fees)
- DAI revenue: 950,000 SAR (Example 3)
- Enrollment fees: 225,000 SAR (Example 4)
- Cafeteria revenue: 350,000 SAR (estimated 30% participation × 150 SAR/month × 10 months)
- Extracurricular revenue: 150,000 SAR (estimated)
- Facility rentals: 70,000 SAR (estimated)

**Calculation:**
```
Total revenue = Tuition + DAI + Enrollment + Other
              = 28,500,000 + 950,000 + 225,000 + (350,000 + 150,000 + 70,000)
              = 28,500,000 + 950,000 + 225,000 + 570,000
              = 30,245,000 SAR

Revenue breakdown:
- Tuition: 28,500,000 SAR (94.2%)
- DAI: 950,000 SAR (3.1%)
- Enrollment: 225,000 SAR (0.7%)
- Other: 570,000 SAR (1.9%)
```

**Result**: 30,245,000 SAR total projected revenue for 2025-2026

## Integration Points

### Upstream Dependencies

1. **Module 5 (Fee Structure Configuration)**: Fee rates by level and nationality
2. **Module 7 (Enrollment Planning)**: Student counts by level, nationality, and new/returning status

### Downstream Consumers

1. **Module 13 (Budget Consolidation)**: Revenue projections feed into overall budget
2. **Module 14 (Financial Statements)**: Revenue recognized in income statement
3. **Module 17 (Budget vs Actual)**: Revenue actuals compared to projections

### Data Flow

```
Fee Structure (Module 5)      Enrollment Planning (Module 7)
        ↓                                ↓
    Fee Rates              Student Counts (by level, nationality, new/returning)
        ↓                                ↓
        └────────────┬───────────────────┘
                     ↓
          Revenue Planning (Module 10)
         ┌────────────┼────────────┐
         ↓            ↓            ↓
      Tuition       DAI      Enrollment Fees
         ↓            ↓            ↓
         └────────────┴────────────┘
                     ↓
        Trimester Recognition (T1/T2/T3)
                     ↓
        Budget Consolidation (Module 13)
                     ↓
        Financial Statements (Module 14)
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions/:id/revenue-projections
POST   /api/v1/budget-versions/:id/revenue-projections
GET    /api/v1/budget-versions/:id/tuition-revenue-detail
POST   /api/v1/calculate-tuition-revenue
       Request: { enrollment_data, fee_structure, sibling_discount_pct }
       Response: { total_revenue, revenue_by_level, revenue_by_nationality }
GET    /api/v1/budget-versions/:id/revenue-summary
       Response: { tuition, dai, enrollment, other, total }
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Tuition Revenue Calculation
```typescript
const enrollment = { french: 46, saudi: 0, other: 99 };
const fees = { french: 11000, saudi: 18150, other: 18500 };
const discount = { french: 0.05, other: 0.04 };

const revenue = calculateTuitionRevenue(enrollment, fees, discount);
expect(revenue.total_net).toBe(2238940);
```

#### Scenario 2: Trimester Recognition
```typescript
const annualTuition = 2238940;
const trimesters = recognizeByTrimester(annualTuition, [0.40, 0.30, 0.30]);

expect(trimesters.t1).toBeCloseTo(895576, 0);
expect(trimesters.t2).toBeCloseTo(671682, 0);
expect(trimesters.t3).toBeCloseTo(671682, 0);
expect(trimesters.t1 + trimesters.t2 + trimesters.t3).toBe(annualTuition);
```

#### Scenario 3: Sibling Discount Application
```typescript
const tuitionRevenue = 506000;
const siblingDiscountPct = 5;

const discount = tuitionRevenue * (siblingDiscountPct / 100);
expect(discount).toBe(25300);

const netRevenue = tuitionRevenue - discount;
expect(netRevenue).toBe(480700);
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: revenue_projections, tuition_revenue_detail, other_revenue_sources tables |

## Future Enhancements (Phase 5-6)

1. **Payment Tracking Integration**: Link projected revenue to actual payments received
2. **Revenue Optimization**: Suggest optimal fee structures to maximize revenue within market constraints
3. **Scenario Modeling**: Compare revenue under different enrollment scenarios (conservative, base, optimistic)
4. **Family Grouping**: Automated sibling discount calculation based on family relationships
5. **Revenue Forecasting**: ML-based revenue predictions using historical trends
6. **Discount Analytics**: Track sibling discount utilization and impact on revenue
7. **Payment Plan Support**: Model revenue timing for families on installment plans
8. **Scholarship Management**: Track scholarship awards and impact on net tuition revenue
9. **Revenue Dashboards**: Visual analytics of revenue trends, concentration by level/nationality
10. **Integration with Accounting**: Sync revenue projections with Odoo for budget vs actual comparison

## Notes

- **Phase 4 Scope**: Database foundation only - revenue projection and calculation
- **Business Logic**: Revenue optimization and payment tracking deferred to Phase 5-6
- **Tuition Dominance**: Tuition revenue represents ~94% of total revenue, making enrollment projections critical
- **Sibling Discount Impact**: Estimated 4-5% revenue reduction from sibling discounts (~1.4M SAR annually)
- **Growth Trajectory**: EFIR revenue growing at ~5-6% annually, aligned with enrollment growth
- **Currency**: All revenue in SAR (primary currency for EFIR operations)
- **Data Source**: Fee structures and revenue calculations based on EFIR actual data (2024-2025)
