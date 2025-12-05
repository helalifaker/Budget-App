# Module 2: Class Size Parameters

## Overview

Module 2 defines class formation rules that determine how many classes are needed for a given enrollment. These parameters directly drive workforce planning (teacher FTE requirements), facility planning (classroom needs), and financial projections. The module supports cycle-level defaults with level-specific overrides for maximum flexibility.

**Layer**: Configuration Layer (Phase 1)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Parameter management UI, scenario testing, API endpoints (Phase 5-6)

### Purpose

- Define minimum, target, and maximum class sizes by academic cycle/level
- Calculate number of classes needed based on enrollment projections
- Specify ATSEM (classroom assistant) requirements for Maternelle
- Support historical parameter tracking for budget version comparisons
- Enable what-if scenario modeling with different class size assumptions

### Key Design Decisions

1. **Cycle-Level Defaults**: Parameters defined at cycle level (Maternelle, Élémentaire, Collège, Lycée) with level-specific overrides
2. **Three Size Thresholds**: min/target/max approach balances pedagogical quality with financial constraints
3. **ATSEM Requirements**: Maternelle requires 1 ATSEM per class (French regulation compliance)
4. **Version Control**: Parameters versioned with effective dates to support historical analysis
5. **Constraint Validation**: Database enforces min < target ≤ max logic

## Database Schema

### Tables

#### 1. class_size_parameters

Class formation rules by cycle and level with version control.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
cycle_id              UUID NOT NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
level_id              UUID NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
min_class_size        INTEGER NOT NULL
target_class_size     INTEGER NOT NULL
max_class_size        INTEGER NOT NULL
atsem_required        BOOLEAN NOT NULL DEFAULT false
atsem_ratio           NUMERIC(3, 2) NOT NULL DEFAULT 1.0
effective_date        DATE NOT NULL
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- CHECK (min_class_size < target_class_size)
- CHECK (target_class_size <= max_class_size)
- CHECK (min_class_size >= 10 AND min_class_size <= 25)
- CHECK (max_class_size >= 20 AND max_class_size <= 35)
- CHECK (atsem_ratio >= 0 AND atsem_ratio <= 2.0)
- UNIQUE (budget_version_id, cycle_id, level_id, effective_date) - prevents duplicates
- If level_id is NULL, applies to entire cycle (default)
- If level_id is set, overrides cycle default for that specific level

**RLS Policies:**
- Admin: Full access to all class size parameters
- Manager: Read/write parameters for working budget versions
- Viewer: Read-only access to parameters for approved budget versions

**Indexes:**
- Primary key on id
- Index on (budget_version_id, cycle_id) for cycle-level queries
- Index on (budget_version_id, level_id) for level lookups
- Index on effective_date for historical queries

#### 2. atsem_requirements (Calculated View/Materialized Table)

Calculated ATSEM staffing requirements based on Maternelle class count.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
level_id              UUID NOT NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
num_classes           INTEGER NOT NULL
atsem_ratio           NUMERIC(3, 2) NOT NULL
atsem_count           INTEGER NOT NULL            -- Calculated: CEIL(num_classes × atsem_ratio)
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- level_id must be Maternelle level (PS, MS, or GS)
- atsem_count = CEIL(num_classes × atsem_ratio)
- Cascade delete when budget version deleted

**RLS Policies:**
- Inherits from parent budget_version access control

**Indexes:**
- Primary key on id
- Index on (budget_version_id, level_id)

### Enums

No custom enums for this module (uses academic_structure references from Module 1).

## Data Model

### Sample Class Size Parameters (Cycle Defaults)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440010",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "cycle_id": "cycle-maternelle-uuid",
    "level_id": null,
    "min_class_size": 15,
    "target_class_size": 22,
    "max_class_size": 26,
    "atsem_required": true,
    "atsem_ratio": 1.0,
    "effective_date": "2025-09-01",
    "notes": "Maternelle default parameters for AY 2025-2026"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440011",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "cycle_id": "cycle-elementaire-uuid",
    "level_id": null,
    "min_class_size": 18,
    "target_class_size": 24,
    "max_class_size": 28,
    "atsem_required": false,
    "atsem_ratio": 0.0,
    "effective_date": "2025-09-01",
    "notes": "Élémentaire default parameters for AY 2025-2026"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440012",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "cycle_id": "cycle-college-uuid",
    "level_id": null,
    "min_class_size": 20,
    "target_class_size": 26,
    "max_class_size": 30,
    "atsem_required": false,
    "atsem_ratio": 0.0,
    "effective_date": "2025-09-01",
    "notes": "Collège default parameters for AY 2025-2026"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440013",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "cycle_id": "cycle-lycee-uuid",
    "level_id": null,
    "min_class_size": 20,
    "target_class_size": 26,
    "max_class_size": 32,
    "atsem_required": false,
    "atsem_ratio": 0.0,
    "effective_date": "2025-09-01",
    "notes": "Lycée default parameters (higher max for exam preparation classes)"
  }
]
```

### Sample Level-Specific Override

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440020",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "cycle_id": "cycle-maternelle-uuid",
  "level_id": "level-ps-uuid",
  "min_class_size": 12,
  "target_class_size": 20,
  "max_class_size": 24,
  "atsem_required": true,
  "atsem_ratio": 1.0,
  "effective_date": "2025-09-01",
  "notes": "Petite Section override - smaller class sizes for youngest students"
}
```

### Sample ATSEM Requirements Record

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440030",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "level_id": "level-ps-uuid",
  "num_classes": 3,
  "atsem_ratio": 1.0,
  "atsem_count": 3,
  "calculated_at": "2025-01-15T10:00:00Z"
}
```

## Business Rules

### Class Size Parameter Rules

1. **Size Threshold Ordering**: min_class_size < target_class_size ≤ max_class_size (enforced by CHECK constraint)
2. **Reasonable Ranges**:
   - Minimum class size: 10-25 students
   - Maximum class size: 20-35 students
   - Target should be pedagogically optimal
3. **Cycle Defaults**: Each cycle must have default parameters (level_id = NULL)
4. **Level Override Pattern**: Level-specific parameters override cycle defaults when present
5. **Version Uniqueness**: Only one parameter set per cycle/level per budget version per effective date

### ATSEM Requirement Rules

1. **Maternelle Only**: ATSEM required for all Maternelle classes (PS, MS, GS)
2. **One Per Class**: Standard ratio is 1.0 ATSEM per class
3. **Rounding Up**: atsem_count = CEIL(num_classes × atsem_ratio) to ensure adequate coverage
4. **Shared ATSEM**: In exceptional cases, atsem_ratio can be < 1.0 (e.g., 0.5 for half-time shared between 2 classes)
5. **French Regulation**: ATSEM requirement mandated by French education standards for preschool

### Class Formation Rules

1. **Single Class Logic**: If enrollment ≤ max_class_size, open 1 class
2. **Target-Based Calculation**: Use target_class_size as the basis for dividing enrollment
3. **Max Constraint Check**: Ensure average class size ≤ max_class_size after division
4. **Minimum Viability**: If enrollment < min_class_size, class may not open (subject to business decision)
5. **Balanced Distribution**: Classes should be as evenly sized as possible

### Validation Rules

1. **Effective Date**: Must align with academic year start (typically September 1)
2. **Parameter Consistency**: Parameters must be consistent across all levels within a cycle
3. **Historical Integrity**: Cannot modify parameters for approved budget versions
4. **Cascade Recalculation**: Changing parameters triggers recalculation of enrollment plans, DHG, and costs
5. **Audit Trail**: All parameter changes logged with user and timestamp

## Calculation Examples

### Example 1: Basic Class Formation (Élémentaire)

**Context**: Calculate number of classes needed for CM1 level with 68 enrolled students.

**Given Parameters:**
- Enrollment: 68 students
- Min class size: 18
- Target class size: 24
- Max class size: 28

**Formula:**
```
classes_needed = CEIL(enrollment ÷ target_class_size)
average_size = enrollment ÷ classes_needed
IF average_size > max_class_size THEN classes_needed += 1
```

**Calculation:**
```
Step 1: Target-based calculation
  classes_needed = CEIL(68 ÷ 24) = CEIL(2.83) = 3 classes

Step 2: Verify average doesn't exceed max
  average_size = 68 ÷ 3 = 22.67 students per class
  Is 22.67 > 28 (max)? No ✓

Step 3: Final allocation
  3 classes with distribution: 23, 23, 22 students
```

**Result:** 3 classes needed for CM1, with average 22.67 students per class (within target of 24).

### Example 2: Maximum Constraint Adjustment (Collège 6ème)

**Context**: Calculate classes for 6ème with 145 students, demonstrating max constraint.

**Given Parameters:**
- Enrollment: 145 students
- Min class size: 20
- Target class size: 26
- Max class size: 30

**Calculation:**
```
Step 1: Target-based calculation
  classes_needed = CEIL(145 ÷ 26) = CEIL(5.58) = 6 classes

Step 2: Verify average doesn't exceed max
  average_size = 145 ÷ 6 = 24.17 students per class
  Is 24.17 > 30 (max)? No ✓

Step 3: Final allocation
  6 classes with distribution: 25, 24, 24, 24, 24, 24 students
```

**Alternative Scenario (if we tried 5 classes):**
```
If classes_needed = 5:
  average_size = 145 ÷ 5 = 29 students per class
  Is 29 > 30 (max)? No, but 29 is very close to max (96.7% of max)

Decision: Keep 6 classes for better pedagogical quality (24.17 avg vs 29 avg)
```

**Result:** 6 classes recommended to maintain quality below max threshold.

### Example 3: ATSEM Calculation (Maternelle)

**Context**: Calculate ATSEM requirements for Maternelle division with enrollment data.

**Given Data:**
- PS (Petite Section): 68 students → 3 classes
- MS (Moyenne Section): 82 students → 4 classes
- GS (Grande Section): 75 students → 3 classes
- ATSEM ratio: 1.0 per class

**Formula:**
```
atsem_count = CEIL(num_classes × atsem_ratio)
```

**Calculation:**
```
PS: CEIL(3 classes × 1.0) = 3 ATSEM
MS: CEIL(4 classes × 1.0) = 4 ATSEM
GS: CEIL(3 classes × 1.0) = 3 ATSEM

Total Maternelle ATSEM: 3 + 4 + 3 = 10 ATSEM
Total Maternelle classes: 3 + 4 + 3 = 10 classes
```

**Result:** 10 ATSEM required for 10 Maternelle classes (1:1 ratio).

**Cost Impact (at 9,900 SAR/month average salary):**
```
Annual ATSEM cost = 10 ATSEM × 9,900 SAR/month × 12 months
                  = 1,188,000 SAR per year
```

## Integration Points

### Upstream Dependencies

1. **Module 1 (System Configuration)**: Academic structure (cycles and levels)
2. **Module 13 (Budget Consolidation)**: Budget version for parameter versioning

### Downstream Consumers

1. **Module 7 (Enrollment Planning)**: Uses class size parameters to calculate class counts from enrollment projections
2. **Module 8 (DHG Workforce Planning)**: Class counts drive teacher FTE requirements
3. **Module 9 (Facility Planning)**: Class counts determine classroom needs
4. **Module 11 (Cost Planning)**: ATSEM requirements drive personnel costs
5. **Module 15 (Statistical Analysis)**: Average class size KPI calculation

### Data Flow

```
Academic Structure (Module 1) → Class Size Parameters (Module 2)
                                        ↓
Enrollment Projections (Module 7) → Class Count Calculation
                                        ↓
                    ┌───────────────────┴───────────────────┐
                    ↓                                       ↓
    DHG Workforce Planning (Module 8)          Facility Planning (Module 9)
    (Teacher FTE requirements)                 (Classroom needs)
                    ↓
         Cost Planning (Module 11)
         (Personnel + ATSEM costs)
```

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
# Class Size Parameters
GET    /api/v1/budget-versions/:id/class-size-parameters          # Get all parameters for budget version
GET    /api/v1/budget-versions/:id/class-size-parameters/cycle/:cycle_id  # Get cycle defaults
GET    /api/v1/budget-versions/:id/class-size-parameters/level/:level_id  # Get level-specific parameters
POST   /api/v1/budget-versions/:id/class-size-parameters          # Create new parameter set
PUT    /api/v1/budget-versions/:id/class-size-parameters/:param_id # Update parameters
DELETE /api/v1/budget-versions/:id/class-size-parameters/:param_id # Delete parameters

# Class Formation Calculations
POST   /api/v1/calculate-classes                                   # Calculate classes for given enrollment
       Request: { enrollment: number, cycle_id: UUID, level_id?: UUID }
       Response: { classes_needed: number, average_size: number, distribution: number[] }

# ATSEM Requirements
GET    /api/v1/budget-versions/:id/atsem-requirements             # Get ATSEM requirements
POST   /api/v1/budget-versions/:id/calculate-atsem                # Recalculate ATSEM needs

# Scenario Testing
POST   /api/v1/class-size-parameters/scenario                     # Test what-if scenarios
       Request: { enrollment_by_level: {}, custom_parameters: {} }
       Response: { class_count: {}, atsem_count: number, total_cost_impact: number }
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify class_size_parameters model and constraints
2. **Calculation Tests**: Test class formation algorithm with edge cases
3. **ATSEM Tests**: Verify ATSEM calculation logic

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for different roles
2. **Parameter Override Tests**: Test level-specific override logic
3. **Cascade Tests**: Verify recalculation triggers when parameters change

### Test Scenarios

#### Scenario 1: Create Cycle Default Parameters

**Objective:** Create default class size parameters for a cycle.

**Test Data:**
```typescript
const maternelleParams = {
  budget_version_id: testBudgetVersion.id,
  cycle_id: maternelleCycle.id,
  level_id: null,  // Cycle default
  min_class_size: 15,
  target_class_size: 22,
  max_class_size: 26,
  atsem_required: true,
  atsem_ratio: 1.0,
  effective_date: new Date("2025-09-01")
};
```

**Expected Behavior:**
- Parameters created successfully
- Applies to all Maternelle levels (PS, MS, GS) unless overridden

**Example Test Code:**
```typescript
import { describe, it, expect } from 'vitest';
import { ClassSizeParameters } from '@/models';

describe('ClassSizeParameters - Cycle Defaults', () => {
  it('should create cycle default parameters', async () => {
    const params = await ClassSizeParameters.create({
      budget_version_id: testBudgetVersion.id,
      cycle_id: maternelleCycle.id,
      level_id: null,
      min_class_size: 15,
      target_class_size: 22,
      max_class_size: 26,
      atsem_required: true,
      atsem_ratio: 1.0,
      effective_date: new Date("2025-09-01")
    });

    expect(params.id).toBeDefined();
    expect(params.level_id).toBeNull();
    expect(params.target_class_size).toBe(22);
  });
});
```

#### Scenario 2: Level-Specific Override

**Objective:** Test that level-specific parameters override cycle defaults.

**Test Data:**
```typescript
// Cycle default: target = 22
const cycleDefault = { cycle_id: maternelle.id, level_id: null, target_class_size: 22 };

// PS override: target = 20 (smaller for youngest)
const psOverride = { cycle_id: maternelle.id, level_id: psLevel.id, target_class_size: 20 };
```

**Expected Behavior:**
- When retrieving parameters for PS level, psOverride is returned
- When retrieving for MS or GS levels, cycleDefault is returned

**Example Test Code:**
```typescript
describe('ClassSizeParameters - Level Override', () => {
  it('should use level-specific parameters when available', async () => {
    // Create cycle default
    await ClassSizeParameters.create({
      budget_version_id: testBudgetVersion.id,
      cycle_id: maternelleCycle.id,
      level_id: null,
      target_class_size: 22
    });

    // Create PS override
    await ClassSizeParameters.create({
      budget_version_id: testBudgetVersion.id,
      cycle_id: maternelleCycle.id,
      level_id: psLevel.id,
      target_class_size: 20
    });

    // Retrieve for PS - should get override
    const psParams = await getParametersForLevel(testBudgetVersion.id, psLevel.id);
    expect(psParams.target_class_size).toBe(20);

    // Retrieve for MS - should get cycle default
    const msParams = await getParametersForLevel(testBudgetVersion.id, msLevel.id);
    expect(msParams.target_class_size).toBe(22);
  });
});
```

#### Scenario 3: Class Formation Calculation

**Objective:** Test class formation algorithm with various enrollment scenarios.

**Test Data:**
```typescript
const testCases = [
  { enrollment: 24, target: 24, max: 28, expected_classes: 1, expected_avg: 24 },
  { enrollment: 68, target: 24, max: 28, expected_classes: 3, expected_avg: 22.67 },
  { enrollment: 145, target: 26, max: 30, expected_classes: 6, expected_avg: 24.17 },
  { enrollment: 15, target: 24, max: 28, expected_classes: 1, expected_avg: 15 }
];
```

**Expected Behavior:**
- Correct number of classes calculated
- Average class size within constraints
- Balanced distribution of students

**Example Test Code:**
```typescript
describe('Class Formation Algorithm', () => {
  it('should calculate correct number of classes for various enrollments', () => {
    const testCases = [
      { enrollment: 24, target: 24, max: 28, expected: 1 },
      { enrollment: 68, target: 24, max: 28, expected: 3 },
      { enrollment: 145, target: 26, max: 30, expected: 6 }
    ];

    testCases.forEach(({ enrollment, target, max, expected }) => {
      const result = calculateClasses(enrollment, target, max);
      expect(result.classes_needed).toBe(expected);
      expect(result.average_size).toBeLessThanOrEqual(max);
    });
  });

  it('should distribute students evenly across classes', () => {
    const result = calculateClasses(68, 24, 28);

    expect(result.classes_needed).toBe(3);
    expect(result.distribution).toEqual([23, 23, 22]);
    expect(result.distribution.reduce((a, b) => a + b)).toBe(68);
  });
});
```

#### Scenario 4: ATSEM Calculation

**Objective:** Verify ATSEM requirements calculated correctly for Maternelle.

**Test Data:**
```typescript
const maternelleEnrollment = [
  { level: 'PS', enrollment: 68, target: 22, max: 26, expected_classes: 3 },
  { level: 'MS', enrollment: 82, target: 22, max: 26, expected_classes: 4 },
  { level: 'GS', enrollment: 75, target: 22, max: 26, expected_classes: 3 }
];
const atsem_ratio = 1.0;
```

**Expected Behavior:**
- ATSEM count = CEIL(num_classes × atsem_ratio)
- Total 10 ATSEM for 10 Maternelle classes

**Example Test Code:**
```typescript
describe('ATSEM Calculation', () => {
  it('should calculate ATSEM requirements for Maternelle classes', async () => {
    const maternelleClasses = [
      { level_id: psLevel.id, num_classes: 3 },
      { level_id: msLevel.id, num_classes: 4 },
      { level_id: gsLevel.id, num_classes: 3 }
    ];

    let totalATSEM = 0;
    for (const { level_id, num_classes } of maternelleClasses) {
      const atsemCount = calculateATSEM(num_classes, 1.0);
      totalATSEM += atsemCount;

      expect(atsemCount).toBe(num_classes); // 1:1 ratio
    }

    expect(totalATSEM).toBe(10); // 3 + 4 + 3 = 10 ATSEM
  });
});
```

#### Scenario 5: Constraint Validation

**Objective:** Verify CHECK constraints enforce min < target ≤ max rule.

**Test Data:**
```typescript
const invalidParams = [
  { min: 25, target: 20, max: 28 },  // min > target (invalid)
  { min: 15, target: 30, max: 28 },  // target > max (invalid)
  { min: 15, target: 24, max: 24 },  // target = max (valid)
];
```

**Expected Behavior:**
- Invalid parameter combinations rejected with constraint violation
- Valid combinations accepted

**Example Test Code:**
```typescript
describe('Class Size Constraints', () => {
  it('should reject parameters where min >= target', async () => {
    await expect(
      ClassSizeParameters.create({
        budget_version_id: testBudgetVersion.id,
        cycle_id: elementaireCycle.id,
        min_class_size: 25,
        target_class_size: 20,
        max_class_size: 28
      })
    ).rejects.toThrow('min_class_size < target_class_size');
  });

  it('should reject parameters where target > max', async () => {
    await expect(
      ClassSizeParameters.create({
        budget_version_id: testBudgetVersion.id,
        cycle_id: elementaireCycle.id,
        min_class_size: 15,
        target_class_size: 30,
        max_class_size: 28
      })
    ).rejects.toThrow('target_class_size <= max_class_size');
  });

  it('should accept parameters where target = max', async () => {
    const params = await ClassSizeParameters.create({
      budget_version_id: testBudgetVersion.id,
      cycle_id: elementaireCycle.id,
      min_class_size: 15,
      target_class_size: 24,
      max_class_size: 24
    });

    expect(params.id).toBeDefined();
  });
});
```

#### Scenario 6: Parameter Versioning

**Objective:** Test that parameters are versioned per budget version with effective dates.

**Test Data:**
```typescript
const version2025 = { budget_version_id: version2025.id, target_class_size: 24, effective_date: "2025-09-01" };
const version2026 = { budget_version_id: version2026.id, target_class_size: 26, effective_date: "2026-09-01" };
```

**Expected Behavior:**
- Different budget versions can have different parameters
- Effective date tracks when parameters apply
- Historical parameters preserved for analysis

**Example Test Code:**
```typescript
describe('Parameter Versioning', () => {
  it('should support different parameters per budget version', async () => {
    const version2025 = await createBudgetVersion('2025-2026');
    const version2026 = await createBudgetVersion('2026-2027');

    // 2025 parameters: target = 24
    await ClassSizeParameters.create({
      budget_version_id: version2025.id,
      cycle_id: elementaireCycle.id,
      target_class_size: 24,
      effective_date: new Date("2025-09-01")
    });

    // 2026 parameters: target = 26 (increased capacity)
    await ClassSizeParameters.create({
      budget_version_id: version2026.id,
      cycle_id: elementaireCycle.id,
      target_class_size: 26,
      effective_date: new Date("2026-09-01")
    });

    // Verify different values
    const params2025 = await getParametersForVersion(version2025.id, elementaireCycle.id);
    const params2026 = await getParametersForVersion(version2026.id, elementaireCycle.id);

    expect(params2025.target_class_size).toBe(24);
    expect(params2026.target_class_size).toBe(26);
  });
});
```

#### Scenario 7: RLS Policy - Manager Access

**Objective:** Verify managers can modify parameters for working budget versions only.

**Expected Behavior:**
- Manager can read/write parameters for working versions
- Manager has read-only access to approved versions

**Example Test Code:**
```python
def test_rls_manager_working_version():
    """Test manager can modify parameters for working budget versions."""
    # Setup: working and approved budget versions
    working_version = create_working_budget_version()
    approved_version = create_approved_budget_version()

    # Authenticate as manager
    set_user_role("manager")

    # Manager can create parameters for working version
    working_params = ClassSizeParameters(
        budget_version_id=working_version.id,
        cycle_id=maternelle_cycle.id,
        target_class_size=22
    )
    db.session.add(working_params)
    db.session.commit()
    assert working_params.id is not None

    # Manager cannot modify approved version parameters
    approved_params = ClassSizeParameters.query.filter_by(
        budget_version_id=approved_version.id
    ).first()

    approved_params.target_class_size = 24
    with pytest.raises(PermissionError):
        db.session.commit()
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: class_size_parameters and atsem_requirements tables with RLS policies |
| 1.1 | 2025-12-05 | Claude Code | Enhanced Future Enhancements section with detailed 4-feature roadmap; added reference to MODULE_02_FUTURE_ENHANCEMENTS.md (96-page comprehensive specification) |

## Future Enhancements

**Status**: Planned for future implementation (comprehensive specification available)

**Documentation**: See [MODULE_02_FUTURE_ENHANCEMENTS.md](./MODULE_02_FUTURE_ENHANCEMENTS.md) for complete technical specifications, implementation plans, and estimates.

### Four Major Enhancement Features

#### 1. Visual Distribution 📊 (Week 1, 5 days)
Interactive charts and visualizations for data-driven planning:
- **Student Distribution Chart**: Bar chart showing students per class by level, color-coded by utilization
- **Cost Breakdown Chart**: Stacked bar chart of personnel costs by cycle (Teachers, ATSEM, Admin)
- **AEFE Comparison Chart**: Line chart comparing current class sizes vs AEFE benchmarks
- **Trend Chart**: Multi-year historical view of class size evolution
- **Export Capability**: PNG, PDF, and Excel formats for board presentations
- **Business Value**: Visual feedback for capacity planning, cost transparency, stakeholder communication

#### 2. Scenario Modeling 🎯 (Week 2, 6-7 days)
What-if analysis tool for comparing different class size strategies:
- **Create Scenarios**: Conservative, Base, Optimistic, or Custom parameter sets
- **Side-by-Side Comparison**: Compare 2-4 scenarios with cost/FTE/capacity impacts
- **Impact Analysis**: Automatic recalculation of classes, teacher FTE, and costs
- **Scenario Actions**: Copy, edit, delete, or accept scenarios
- **Database Changes**: 2 new tables (`class_size_scenarios`, `class_size_scenario_params`)
- **Business Value**: Risk planning, decision support, budget flexibility

#### 3. Optimization Calculator 🤖 (Week 3, 7 days)
AI-powered recommendations for optimal class size parameters:
- **Three Optimization Goals**:
  - Minimize Cost (maximize class sizes within limits)
  - Maximize Quality (minimize class sizes for better student-teacher ratios)
  - Balanced Approach (optimal cost-quality tradeoff)
- **Constraint Configuration**: AEFE benchmarks, custom min/max overrides, budget ceilings
- **Recommendation Output**: Suggested parameters with cost savings, FTE impact, and confidence scores
- **AEFE Compliance**: Automatic checking of H/E ratios and quality standards
- **Business Value**: 5-15% cost savings, data-driven decisions, objective parameter selection

#### 4. Real-time Integration ⚡ (Week 4, 4 days)
Live synchronization and collaborative editing:
- **Parameter Synchronization**: Real-time updates when other users modify parameters
- **Enrollment Change Propagation**: Auto-recalculate classes when enrollment data changes
- **User Presence Indicators**: See who else is viewing/editing the same budget
- **Conflict Detection**: Optimistic locking with version tracking (HTTP 409 Conflict)
- **Connection Status**: Live/Connecting/Disconnected badge with auto-reconnect
- **Business Value**: Collaboration, data consistency, conflict prevention

### Implementation Overview

**Total Effort**: 3-4 weeks (phased implementation)

**Technical Approach**:
- **Backend**: 3 new calculation engines (distribution, comparison, optimization)
- **Database**: 3 new tables for scenarios and recommendations
- **Frontend**: 10+ new components (charts, dialogs, presence indicators)
- **Infrastructure**: Leverages existing Recharts, Supabase Realtime, and calculation engines
- **Testing**: 80%+ coverage target with comprehensive unit, integration, and E2E tests

**Implementation Order** (lowest risk first):
1. Visual Distribution (immediate value, no database changes)
2. Scenario Modeling (foundation for optimization)
3. Optimization Calculator (complex algorithm)
4. Real-time Integration (polish feature)

**Key Benefits**:
- Transform Module 2 from parameter management into intelligent planning platform
- Enable data-driven decision making with visual feedback
- Support multiple "what-if" scenarios for risk planning
- Provide AI-powered optimization recommendations
- Enable real-time collaboration for multi-user teams

For detailed technical specifications, database schemas, API endpoints, testing strategies, and implementation estimates, see the complete [Future Enhancements Documentation](./MODULE_02_FUTURE_ENHANCEMENTS.md).

## Notes

- **Phase 4 Scope**: This module implements database foundation (tables, constraints, RLS policies, migrations)
- **Business Logic**: Class formation calculations and parameter management UI will be implemented in Phases 5-6
- **ATSEM Requirement**: Mandated by French education regulations for all Maternelle classes
- **Pedagogical Quality**: Target class sizes balance educational quality with financial sustainability
- **Flexibility**: Level-specific overrides allow fine-tuning for special cases (e.g., smaller PS classes)
- **Cost Impact**: Class size parameters directly impact teacher FTE requirements and therefore personnel costs
- **AEFE Benchmarks**: Class sizes should align with AEFE recommendations for quality French education
- **Regulatory Compliance**: Maximum class sizes must comply with local Saudi regulations and AEFE standards
