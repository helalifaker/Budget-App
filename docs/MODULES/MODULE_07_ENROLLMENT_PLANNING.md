# Module 7: Enrollment Planning

## Overview

Module 7 is the primary driver for the entire budget planning process, as enrollment projections determine class structure, workforce requirements, facility needs, and revenue. This module captures student enrollment forecasts by level and nationality for both budget periods (Period 1: Jan-Jun, Period 2: Sep-Dec), calculates class formation, and tracks new vs. returning students for fee revenue calculations.

**Layer**: Planning Layer (Phase 2)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Enrollment forecasting tools, scenario modeling, API endpoints (Phase 5-6)

### Purpose

- Project student enrollment by academic level and nationality category
- Calculate class structure based on enrollment and class size parameters (Module 2)
- Track new vs. returning students for revenue calculations
- Support multiple enrollment scenarios (conservative, base, optimistic)
- Monitor actual vs. projected enrollment for forecast accuracy
- Drive downstream modules: Revenue (Module 10), Workforce (Module 8), Facility (Module 9)

### Key Design Decisions

1. **Dual Period Structure**: Separate projections for Period 1 (Jan-Jun) and Period 2 (Sep-Dec) reflecting academic year transition
2. **Nationality Granularity**: Enrollment broken down by French/Saudi/Other for revenue planning (different fee structures)
3. **New vs. Returning**: Track new enrollments separately for registration fee calculations
4. **Scenario Support**: Multiple enrollment scenarios within same budget version (conservative/base/optimistic)
5. **Capacity Constraint**: Total enrollment capped at ~1,875 students (school maximum capacity)

## Database Schema

### Tables

#### 1. enrollment_projections

Student enrollment forecasts by level, nationality, and period.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
level_id              UUID NOT NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
nationality_category  nationalitycategory NOT NULL
scenario_name         VARCHAR(50) NULL DEFAULT 'base'  -- conservative, base, optimistic
projected_count       INTEGER NOT NULL
new_students          INTEGER NOT NULL DEFAULT 0
returning_students    INTEGER NOT NULL DEFAULT 0
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- projected_count >= 0
- new_students >= 0
- returning_students >= 0
- projected_count = new_students + returning_students (enforced by trigger)
- UNIQUE (budget_version_id, academic_period_id, level_id, nationality_category, scenario_name)

**RLS Policies:**
- Admin: Full access
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (budget_version_id, academic_period_id, scenario_name)
- Index on level_id for level-based aggregation

#### 2. class_structure (Calculated from Enrollment)

Number of classes per level based on enrollment and class size parameters.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
level_id              UUID NOT NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
scenario_name         VARCHAR(50) NULL DEFAULT 'base'
total_enrollment      INTEGER NOT NULL
num_classes           INTEGER NOT NULL
avg_class_size        NUMERIC(5, 2) NOT NULL
atsem_needed          INTEGER NOT NULL DEFAULT 0
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- total_enrollment >= 0
- num_classes >= 0
- If total_enrollment > 0 then num_classes >= 1
- avg_class_size = total_enrollment / num_classes (calculated field)

**RLS Policies:**
- Same as enrollment_projections

**Indexes:**
- Primary key on id
- Index on (budget_version_id, academic_period_id, scenario_name)

## Data Model

### Sample Enrollment Projections (2025-2026, Period 2 - Sep start)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440700",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "level_id": "level-6eme-uuid",
    "nationality_category": "french",
    "scenario_name": "base",
    "projected_count": 46,
    "new_students": 8,
    "returning_students": 38,
    "notes": "6ème French students, September 2025 start"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440701",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "level_id": "level-6eme-uuid",
    "nationality_category": "other",
    "scenario_name": "base",
    "projected_count": 99,
    "new_students": 15,
    "returning_students": 84,
    "notes": "6ème Other nationality students"
  }
]
```

### Historical Enrollment Trends (EFIR Actual Data)

| Academic Year | Maternelle | Élémentaire | Collège | Lycée | Total | Growth Rate |
|---------------|------------|-------------|---------|-------|-------|-------------|
| 2021-2022 | 251 | 556 | 389 | 238 | 1,434 | -6.4% |
| 2022-2023 | 267 | 574 | 413 | 245 | 1,499 | +4.8% |
| 2023-2024 | 249 | 607 | 450 | 281 | 1,587 | +5.9% |
| 2024-2025 | 280 | 650 | 510 | 356 | 1,796 | +13.2% |
| 2025-2026 (proj) | 295 | 680 | 540 | 385 | 1,900 | +5.8% |

### Nationality Distribution (2023-2024 Baseline)

| Nationality | Students | Percentage | Fee Tier |
|-------------|----------|------------|----------|
| French | 503 | 31.7% | TTC (lowest) |
| Saudi | 60 | 3.8% | HT (middle) |
| Other | 1,024 | 64.5% | TTC (highest) |

## Business Rules

### Enrollment Projection Rules

1. **Dual Period Requirement**: Projections needed for both Period 1 (Jan-Jun) and Period 2 (Sep-Dec)
2. **New + Returning = Total**: projected_count = new_students + returning_students (enforced)
3. **Capacity Constraint**: Σ(all levels) ≤ 1,875 students (maximum school capacity)
4. **Re-enrollment Rate**: Historical average ~85-90% (used for returning student projections)
5. **Growth Assumptions**: Conservative (2%), Base (5%), Optimistic (8%) scenarios

### Class Structure Calculation Rules

1. **Auto-Calculation**: Class structure automatically calculated when enrollment changes
2. **Class Size Parameters**: Uses Module 2 (target/max class sizes) for calculation
3. **ATSEM Allocation**: Maternelle levels get 1 ATSEM per class
4. **Rounding Logic**: Classes rounded up to ensure all students accommodated
5. **Minimum Viability**: If enrollment < min_class_size, business decision required

### Validation Rules

1. **Positive Counts**: All enrollment counts must be >= 0
2. **Realistic Growth**: Year-over-year growth capped at ±20% (outliers flagged for review)
3. **Level Progression**: Students generally progress to next level (retention ~95%)
4. **Nationality Consistency**: Nationality distribution should remain relatively stable year-over-year
5. **Scenario Coherence**: Conservative < Base < Optimistic for all levels

## Calculation Examples

### Example 1: Class Structure Calculation (6ème)

**Context:** Calculate classes needed for 6ème with 145 total students.

**Given Data:**
- Total enrollment: 145 students
- Target class size: 26 (from Module 2)
- Max class size: 30

**Calculation:**
```
Classes needed = CEIL(145 ÷ 26) = CEIL(5.58) = 6 classes
Average size = 145 ÷ 6 = 24.17 students/class ✓ (within target)
```

**Result:** 6 classes needed, avg 24.17 students per class.

### Example 2: Total Enrollment Projection (2025-2026)

**Context:** Project total enrollment for AY 2025-2026 using 5% growth.

**Historical Baseline (2024-2025):**
- Total: 1,796 students

**Projection (5% growth):**
```
Total 2025-2026 = 1,796 × 1.05 = 1,886 students

Capacity check: 1,886 < 1,875? NO - EXCEEDS CAPACITY
Adjusted projection: 1,875 students (capped at capacity)
```

**Result:** Project 1,875 students (capacity limit), not 1,886.

## Integration Points

### Upstream Dependencies

1. **Module 1 (System Configuration)**: Academic structure (levels), capacity limits
2. **Module 2 (Class Size Parameters)**: Class formation rules

### Downstream Consumers

1. **Module 8 (DHG Workforce Planning)**: Class counts drive teacher FTE requirements
2. **Module 9 (Facility Planning)**: Class counts determine classroom needs
3. **Module 10 (Revenue Planning)**: Enrollment × fees = tuition revenue
4. **Module 11 (Cost Planning)**: Student counts drive per-student costs

### Data Flow

```
Enrollment Projections (Module 7)
        ↓
Class Structure Calculation (uses Module 2 parameters)
        ↓
    ┌───┴────┬──────────┬──────────┐
    ↓        ↓          ↓          ↓
Workforce  Facility  Revenue   Cost Planning
(Module 8) (Module 9) (Module 10) (Module 11)
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions/:id/enrollment-projections
POST   /api/v1/budget-versions/:id/enrollment-projections
GET    /api/v1/budget-versions/:id/class-structure
POST   /api/v1/calculate-class-structure
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Enrollment Projection Creation
```typescript
const enrollment = await EnrollmentProjection.create({
  budget_version_id: testVersion.id,
  level_id: collegeLevel.id,
  nationality_category: NationalityCategory.FRENCH,
  projected_count: 145,
  new_students: 20,
  returning_students: 125
});
expect(enrollment.projected_count).toBe(145);
```

#### Scenario 2: Class Structure Calculation
```typescript
const result = calculateClasses(145, 26, 30);
expect(result.num_classes).toBe(6);
expect(result.avg_size).toBeCloseTo(24.17, 1);
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation |

## Future Enhancements (Phase 5-6)

1. **Enrollment Forecasting Tool**: ML-based enrollment predictions using historical trends
2. **Scenario Modeling**: Side-by-side comparison of conservative/base/optimistic scenarios
3. **Actual vs. Projected Tracking**: Monitor forecast accuracy and adjust models
4. **Cohort Analysis**: Track student progression through grade levels
5. **Capacity Planning**: Optimize enrollment mix to maximize revenue within capacity

## Notes

- **Phase 4 Scope**: Database foundation only
- **Business Logic**: Enrollment forecasting tools in Phase 5-6
- **Primary Driver**: Enrollment is THE primary input driving all other budget modules
- **Capacity Constraint**: ~1,875 student maximum (facilities-limited)
- **Historical Accuracy**: EFIR has grown 13.2% (2024-2025) - strong demand indicates continued growth potential
