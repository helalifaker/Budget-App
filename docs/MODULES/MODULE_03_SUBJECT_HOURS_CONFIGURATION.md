# Module 3: Subject Hours Configuration

## Overview

Module 3 defines the curriculum structure and weekly teaching hours required per subject for secondary education (Collège and Lycée). This module is the foundation for DHG (Dotation Horaire Globale) workforce planning calculations, as total subject hours directly determine teacher FTE requirements. The configuration follows the French national curriculum with local adaptations for Saudi Arabia (Arabic language instruction).

**Layer**: Configuration Layer (Phase 1)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Curriculum editor UI, hour optimization tools, API endpoints (Phase 5-6)

### Purpose

- Define all subjects taught at EFIR with French and English names
- Specify weekly teaching hours per subject per level (Collège and Lycée)
- Identify subjects requiring special facilities (labs, sports halls)
- Support block scheduling requirements (2-hour blocks for practical subjects)
- Enable curriculum versioning for academic year changes
- Drive DHG hours calculation for secondary teacher workforce planning

### Key Design Decisions

1. **Secondary Only**: Primary (Maternelle + Élémentaire) uses FTE-based model, not subject hours
2. **Matrix Structure**: Hours defined per (subject, level) combination for granular control
3. **French Curriculum Compliance**: Follows French Ministère de l'Éducation nationale guidelines with AEFE approval
4. **Local Adaptation**: Arabic (LVB - Langue Vivante B) required by Saudi Ministry of Education
5. **Version Control**: Hours matrix versioned per budget version to support curriculum changes

## Database Schema

### Tables

#### 1. subjects

Master catalog of all subjects taught at EFIR.

**Columns:**
```sql
id                        UUID PRIMARY KEY
subject_code              VARCHAR(20) NOT NULL UNIQUE    -- MATH, FRAN, HIST, etc.
subject_name_fr           VARCHAR(200) NOT NULL          -- Mathématiques
subject_name_en           VARCHAR(200) NOT NULL          -- Mathematics
subject_type              subjecttype NOT NULL           -- ENUM: core, elective, local, specialization
requires_special_room     BOOLEAN NOT NULL DEFAULT false
special_room_type         VARCHAR(100) NULL              -- lab, sports_hall, art_studio, etc.
requires_block_schedule   BOOLEAN NOT NULL DEFAULT false -- True for labs, PE (2-hour blocks)
is_active                 BOOLEAN NOT NULL DEFAULT true
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- subject_code must be uppercase alphanumeric (2-6 characters)
- If requires_special_room = true, special_room_type must be specified
- Core subjects cannot be soft-deleted (is_active must remain true)

**RLS Policies:**
- All authenticated users can read subjects
- Only admins can create/update/delete subjects

**Indexes:**
- Primary key on id
- Unique index on subject_code
- Index on subject_type for filtering

#### 2. subject_hours_matrix

Weekly teaching hours per subject per level (secondary only).

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
subject_id            UUID NOT NULL FOREIGN KEY -> subjects.id (RESTRICT)
level_id              UUID NOT NULL FOREIGN KEY -> academic_structure.id (RESTRICT)
hours_per_week        NUMERIC(4, 2) NOT NULL     -- e.g., 4.5, 3.0, 1.5
is_split_group        BOOLEAN NOT NULL DEFAULT false -- True if groups/sections (e.g., LV2, options)
group_count           INTEGER NOT NULL DEFAULT 1  -- Number of groups if split
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- UNIQUE (budget_version_id, subject_id, level_id) - one hours value per subject per level per version
- hours_per_week >= 0 AND hours_per_week <= 10 (reasonable range)
- group_count >= 1
- level_id must be secondary level (Collège or Lycée)
- CASCADE delete when budget version deleted

**RLS Policies:**
- Admin: Full access to subject hours matrix
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Unique index on (budget_version_id, subject_id, level_id)
- Index on subject_id for subject-based queries
- Index on level_id for level-based aggregation

#### 3. subject_hours_summary (Calculated View)

Aggregated view of total hours per subject across all levels.

**Columns:**
```sql
budget_version_id     UUID NOT NULL
subject_id            UUID NOT NULL
subject_code          VARCHAR(20)
subject_name_fr       VARCHAR(200)
total_hours           NUMERIC(10, 2)              -- Sum across all levels
levels_taught         JSONB                       -- Array of {level_code, hours}
```

**Purpose:**
- Quick lookup of total subject hours for DHG calculation
- Reporting and analysis

### Enums

#### SubjectType
```sql
CREATE TYPE efir_budget.subjecttype AS ENUM (
    'core',             -- Core curriculum (Français, Mathématiques, etc.)
    'elective',         -- Elective courses (LV2, options)
    'local',            -- Local requirement (Arabic for Saudi Arabia)
    'specialization'    -- Lycée specializations (enseignements de spécialité)
);
```

## Data Model

### Sample Subjects

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440100",
    "subject_code": "MATH",
    "subject_name_fr": "Mathématiques",
    "subject_name_en": "Mathematics",
    "subject_type": "core",
    "requires_special_room": false,
    "special_room_type": null,
    "requires_block_schedule": false
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440101",
    "subject_code": "PHYS",
    "subject_name_fr": "Physique-Chimie",
    "subject_name_en": "Physics-Chemistry",
    "subject_type": "core",
    "requires_special_room": true,
    "special_room_type": "science_lab",
    "requires_block_schedule": true
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440102",
    "subject_code": "ARAB",
    "subject_name_fr": "Arabe (LVB)",
    "subject_name_en": "Arabic (Foreign Language B)",
    "subject_type": "local",
    "requires_special_room": false,
    "special_room_type": null,
    "requires_block_schedule": false
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440103",
    "subject_code": "EPS",
    "subject_name_fr": "Éducation Physique et Sportive",
    "subject_name_en": "Physical Education and Sports",
    "subject_type": "core",
    "requires_special_room": true,
    "special_room_type": "sports_hall",
    "requires_block_schedule": true
  }
]
```

### Sample Subject Hours Matrix (Collège 6ème)

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440200",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "subject_id": "550e8400-e29b-41d4-a716-446655440100",
    "level_id": "level-6eme-uuid",
    "hours_per_week": 4.5,
    "is_split_group": false,
    "group_count": 1,
    "notes": "French national curriculum standard for 6ème"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440201",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "subject_id": "550e8400-e29b-41d4-a716-446655440102",
    "level_id": "level-6eme-uuid",
    "hours_per_week": 2.5,
    "is_split_group": true,
    "group_count": 3,
    "notes": "Arabic groups by proficiency level (beginners, intermediate, advanced)"
  }
]
```

### Complete Collège Hours Matrix (2025-2026)

| Subject | Type | 6ème | 5ème | 4ème | 3ème | Special Room |
|---------|------|------|------|------|------|--------------|
| Français | core | 4.5 | 4.5 | 4.5 | 4.0 | None |
| Mathématiques | core | 4.5 | 3.5 | 3.5 | 3.5 | None |
| Histoire-Géographie | core | 3.0 | 3.0 | 3.0 | 3.5 | None |
| Anglais (LV1) | core | 4.0 | 3.0 | 3.0 | 3.0 | None |
| Espagnol (LV2) | elective | - | 2.5 | 2.5 | 2.5 | None |
| Arabic (LVB) | local | 2.5 | 2.5 | 2.5 | 2.5 | None |
| SVT | core | 3.0 | 1.5 | 1.5 | 1.5 | Lab |
| Physique-Chimie | core | - | 1.5 | 1.5 | 1.5 | Lab |
| EPS | core | 4.0 | 3.0 | 3.0 | 3.0 | Sports Hall |
| Arts Plastiques | core | 1.0 | 1.0 | 1.0 | 1.0 | Art Studio |
| Éducation Musicale | core | 1.0 | 1.0 | 1.0 | 1.0 | Music Room |
| Technologie | core | 1.5 | 1.5 | 1.5 | 1.5 | Tech Lab |

## Business Rules

### Subject Definition Rules

1. **Core Subject Protection**: Core subjects cannot be deleted, only deactivated
2. **Subject Code Convention**: Uppercase alphanumeric codes, 2-6 characters (e.g., MATH, FRAN, HIST)
3. **Bilingual Names**: All subjects must have both French and English names
4. **Special Room Requirements**: If requires_special_room = true, special_room_type must be specified
5. **Block Scheduling**: Labs and PE typically require 2-hour consecutive blocks

### Subject Hours Matrix Rules

1. **Secondary Only**: Hours matrix applies only to Collège (6ème-3ème) and Lycée (2nde-Terminale)
2. **Primary Exemption**: Maternelle and Élémentaire use FTE-based workforce model (Module 8)
3. **Hours Range**: Weekly hours per subject must be between 0 and 10 hours (reasonable pedagogical limit)
4. **Curriculum Total**: Total weekly hours per level should not exceed 30 hours (student schedule limit)
5. **Uniqueness**: One hours value per (budget_version, subject, level) combination

### Group Splitting Rules

1. **Language Groups**: Language subjects (LV2, Arabic) often split by proficiency level
2. **Group Count**: is_split_group = true requires group_count ≥ 2
3. **Hour Multiplication**: Total hours = hours_per_week × group_count for workforce calculation
4. **Example**: Arabic LVB with 3 groups of 2.5h each = 7.5h total teaching hours needed

### Curriculum Change Rules

1. **Version Control**: Curriculum changes create new budget version with updated hours matrix
2. **AEFE Approval**: Major curriculum changes require AEFE approval (must align with French standards)
3. **Ministry Compliance**: Arabic hours must meet Saudi Ministry of Education requirements
4. **Cascade Impact**: Hours changes trigger recalculation of DHG and teacher FTE requirements
5. **Historical Preservation**: Previous versions' hours matrix preserved for audit and analysis

### Validation Rules

1. **Level Classification**: Only secondary levels (Collège + Lycée) can have subject hours
2. **Core Curriculum Compliance**: Total hours for core subjects must meet French Ministry minimums
3. **Faculty Expertise Check**: New subjects require verification of qualified teachers available
4. **Room Availability**: Special room requirements validated against facility inventory (Module 9)
5. **Schedule Feasibility**: Total hours validated against weekly schedule capacity

## Calculation Examples

### Example 1: Total Hours for Mathématiques (Collège)

**Context**: Calculate total weekly hours needed for Mathématiques across all Collège levels.

**Given Data (2025-2026):**
- 6ème: 6 classes × 4.5 hours/week = 27 hours
- 5ème: 6 classes × 3.5 hours/week = 21 hours
- 4ème: 5 classes × 3.5 hours/week = 17.5 hours
- 3ème: 4 classes × 3.5 hours/week = 14 hours

**Formula:**
```
Total Hours = Σ(classes_per_level × hours_per_week_per_level)
```

**Calculation:**
```
6ème: 6 × 4.5 = 27.0 hours
5ème: 6 × 3.5 = 21.0 hours
4ème: 5 × 3.5 = 17.5 hours
3ème: 4 × 3.5 = 14.0 hours
─────────────────────────
Total:       79.5 hours/week

Annualized (36 weeks): 79.5 × 36 = 2,862 hours/year
```

**Result:** Mathématiques requires 79.5 weekly teaching hours across Collège.

**Workforce Impact (Module 8 - DHG):**
```
Teacher FTE = Total Hours ÷ 18 (standard hours/week)
            = 79.5 ÷ 18
            = 4.42 FTE
            → Need 5 Mathématiques teachers for Collège
```

### Example 2: Arabic (LVB) with Group Splitting

**Context**: Calculate total hours for Arabic with proficiency-based grouping.

**Given Data:**
- Arabic offered in all Collège levels (6ème-3ème)
- 2.5 hours/week per level
- Students split into 3 proficiency groups per level
- Class structure: 6ème(6), 5ème(6), 4ème(5), 3ème(4) = 21 total classes

**Group Distribution:**
```
Each level's students divided into 3 groups:
- Beginners (débutants)
- Intermediate (intermédiaires)
- Advanced (avancés)
```

**Calculation:**
```
Hours per level per group: 2.5 hours/week

6ème: 3 groups × 2.5 hours = 7.5 hours
5ème: 3 groups × 2.5 hours = 7.5 hours
4ème: 3 groups × 2.5 hours = 7.5 hours
3ème: 3 groups × 2.5 hours = 7.5 hours
──────────────────────────────────────
Total Arabic hours: 30.0 hours/week

Note: Groups may have unequal sizes based on student proficiency distribution
```

**Workforce Impact:**
```
Teacher FTE = 30.0 ÷ 18 = 1.67 FTE
→ Need 2 Arabic teachers (1 full-time + 1 part-time)

Alternative: 1 full-time (18h) + HSA (12h overtime) = 30h covered
```

**Result:** Arabic requires 30 weekly hours due to group splitting, necessitating 2 teachers.

### Example 3: Weekly Schedule Validation for 6ème

**Context**: Verify total weekly hours for 6ème students comply with 30-hour limit.

**Given Hours Matrix for 6ème:**
```
Français:             4.5 hours
Mathématiques:        4.5 hours
Histoire-Géographie:  3.0 hours
Anglais (LV1):        4.0 hours
Arabic (LVB):         2.5 hours
SVT:                  3.0 hours
EPS:                  4.0 hours
Arts Plastiques:      1.0 hours
Éducation Musicale:   1.0 hours
Technologie:          1.5 hours
```

**Calculation:**
```
Total weekly hours = 4.5 + 4.5 + 3.0 + 4.0 + 2.5 + 3.0 + 4.0 + 1.0 + 1.0 + 1.5
                   = 29.0 hours/week
```

**Validation:**
```
Maximum allowed: 30 hours/week
Actual total:    29 hours/week
Margin:          1.0 hour (3.3%)

Status: COMPLIANT ✓
```

**Result:** 6ème schedule is valid with 29 weekly hours, leaving 1-hour margin for flexibility.

## Integration Points

### Upstream Dependencies

1. **Module 1 (System Configuration)**: Academic structure (levels for Collège and Lycée)
2. **Module 13 (Budget Consolidation)**: Budget version for hours matrix versioning

### Downstream Consumers

1. **Module 8 (DHG Workforce Planning)**: PRIMARY CONSUMER - uses subject hours to calculate teacher FTE requirements
2. **Module 9 (Facility Planning)**: Special room requirements drive facility needs
3. **Module 6 (Timetable Constraints)**: Block scheduling requirements inform timetable generation
4. **Module 11 (Cost Planning)**: Workforce FTE (derived from subject hours) drives personnel costs

### Data Flow

```
Academic Structure (Module 1) → Subject Hours Matrix (Module 3)
                                        ↓
                    Class Structure (Module 7 - enrollment → classes)
                                        ↓
                        DHG Calculation (Module 8)
                Total Hours = Σ(classes × hours_per_level)
                                        ↓
            Teacher FTE = Total Hours ÷ 18 (standard hours/week)
                                        ↓
                    Workforce Requirements (Module 8)
                                        ↓
                    Personnel Cost Planning (Module 11)
```

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
# Subjects
GET    /api/v1/subjects                            # List all subjects
GET    /api/v1/subjects/:id                        # Get subject details
POST   /api/v1/subjects                            # Create subject (admin only)
PUT    /api/v1/subjects/:id                        # Update subject (admin only)
DELETE /api/v1/subjects/:id                        # Soft delete subject (admin only)
GET    /api/v1/subjects/by-type/:type              # Filter by subject type

# Subject Hours Matrix
GET    /api/v1/budget-versions/:id/subject-hours   # Get complete hours matrix
GET    /api/v1/budget-versions/:id/subject-hours/level/:level_id  # Hours for specific level
POST   /api/v1/budget-versions/:id/subject-hours   # Create hours entry
PUT    /api/v1/budget-versions/:id/subject-hours/:entry_id  # Update hours
DELETE /api/v1/budget-versions/:id/subject-hours/:entry_id  # Delete hours entry

# Aggregations & Calculations
GET    /api/v1/budget-versions/:id/subject-hours/summary  # Total hours per subject
POST   /api/v1/subject-hours/calculate-total       # Calculate total hours for scenario
       Request: { subject_id, class_structure: {} }
       Response: { total_hours, fte_required }

# Curriculum Templates
GET    /api/v1/curriculum-templates                # Get standard French curriculum templates
POST   /api/v1/budget-versions/:id/apply-template  # Apply curriculum template to budget version
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify subjects and subject_hours_matrix models
2. **Enum Tests**: Verify SubjectType enum values
3. **Constraint Tests**: Test unique constraints and check constraints

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for different roles
2. **Hours Calculation Tests**: Test total hours aggregation
3. **Cascade Tests**: Verify budget version deletion cascades

### Test Scenarios

#### Scenario 1: Create Subject

**Objective:** Create a new subject with all required fields.

**Test Data:**
```typescript
const subject = {
  subject_code: "MATH",
  subject_name_fr: "Mathématiques",
  subject_name_en: "Mathematics",
  subject_type: SubjectType.CORE,
  requires_special_room: false,
  requires_block_schedule: false
};
```

**Expected Behavior:**
- Subject created successfully
- subject_code stored in uppercase
- is_active defaults to true

**Example Test Code:**
```typescript
import { describe, it, expect } from 'vitest';
import { Subject, SubjectType } from '@/models';

describe('Subject Model', () => {
  it('should create subject with required fields', async () => {
    const subject = await Subject.create({
      subject_code: "MATH",
      subject_name_fr: "Mathématiques",
      subject_name_en: "Mathematics",
      subject_type: SubjectType.CORE,
      requires_special_room: false,
      requires_block_schedule: false
    });

    expect(subject.id).toBeDefined();
    expect(subject.subject_code).toBe("MATH");
    expect(subject.is_active).toBe(true);
  });
});
```

#### Scenario 2: Subject Hours Matrix Entry

**Objective:** Create hours matrix entry for subject-level combination.

**Test Data:**
```typescript
const hoursEntry = {
  budget_version_id: testVersion.id,
  subject_id: mathSubject.id,
  level_id: sixiemeLevel.id,
  hours_per_week: 4.5,
  is_split_group: false,
  group_count: 1
};
```

**Expected Behavior:**
- Hours entry created
- Unique constraint prevents duplicates
- hours_per_week validated (0-10 range)

**Example Test Code:**
```typescript
describe('Subject Hours Matrix', () => {
  it('should create hours entry for subject-level combination', async () => {
    const entry = await SubjectHoursMatrix.create({
      budget_version_id: testVersion.id,
      subject_id: mathSubject.id,
      level_id: sixiemeLevel.id,
      hours_per_week: 4.5,
      is_split_group: false,
      group_count: 1
    });

    expect(entry.id).toBeDefined();
    expect(entry.hours_per_week).toBe(4.5);
  });

  it('should prevent duplicate entries for same subject-level-version', async () => {
    await SubjectHoursMatrix.create({
      budget_version_id: testVersion.id,
      subject_id: mathSubject.id,
      level_id: sixiemeLevel.id,
      hours_per_week: 4.5
    });

    await expect(
      SubjectHoursMatrix.create({
        budget_version_id: testVersion.id,
        subject_id: mathSubject.id,
        level_id: sixiemeLevel.id,
        hours_per_week: 5.0  // Different hours, same combination
      })
    ).rejects.toThrow('unique constraint');
  });
});
```

#### Scenario 3: Total Hours Calculation

**Objective:** Calculate total weekly hours for a subject across all levels.

**Test Data:**
```typescript
const mathClasses = {
  "6ème": 6,
  "5ème": 6,
  "4ème": 5,
  "3ème": 4
};
const mathHours = {
  "6ème": 4.5,
  "5ème": 3.5,
  "4ème": 3.5,
  "3ème": 3.5
};
```

**Expected Behavior:**
- Total = (6×4.5) + (6×3.5) + (5×3.5) + (4×3.5) = 79.5 hours

**Example Test Code:**
```typescript
describe('Subject Hours Calculation', () => {
  it('should calculate total hours for subject across levels', () => {
    const classStructure = [
      { level: "6ème", classes: 6, hours: 4.5 },
      { level: "5ème", classes: 6, hours: 3.5 },
      { level: "4ème", classes: 5, hours: 3.5 },
      { level: "3ème", classes: 4, hours: 3.5 }
    ];

    const totalHours = calculateTotalSubjectHours(classStructure);

    expect(totalHours).toBe(79.5);
  });
});
```

#### Scenario 4: Group Splitting Calculation

**Objective:** Calculate total hours for subject with group splitting.

**Test Data:**
```typescript
const arabicEntry = {
  subject_id: arabicSubject.id,
  level_id: sixiemeLevel.id,
  hours_per_week: 2.5,
  is_split_group: true,
  group_count: 3
};
```

**Expected Behavior:**
- Total hours per level = hours_per_week × group_count = 2.5 × 3 = 7.5 hours

**Example Test Code:**
```typescript
describe('Group Splitting', () => {
  it('should multiply hours by group count for split groups', () => {
    const entry = {
      hours_per_week: 2.5,
      is_split_group: true,
      group_count: 3
    };

    const totalHours = entry.is_split_group
      ? entry.hours_per_week * entry.group_count
      : entry.hours_per_week;

    expect(totalHours).toBe(7.5);
  });
});
```

#### Scenario 5: Weekly Schedule Validation

**Objective:** Validate total weekly hours per level doesn't exceed 30-hour limit.

**Test Data:**
```typescript
const sixiemeSchedule = [
  { subject: "Français", hours: 4.5 },
  { subject: "Mathématiques", hours: 4.5 },
  { subject: "Histoire-Géographie", hours: 3.0 },
  { subject: "Anglais", hours: 4.0 },
  { subject: "Arabic", hours: 2.5 },
  { subject: "SVT", hours: 3.0 },
  { subject: "EPS", hours: 4.0 },
  { subject: "Arts Plastiques", hours: 1.0 },
  { subject: "Éducation Musicale", hours: 1.0 },
  { subject: "Technologie", hours: 1.5 }
];
```

**Expected Behavior:**
- Total = 29.0 hours
- Validation passes (≤ 30 hours)

**Example Test Code:**
```typescript
describe('Weekly Schedule Validation', () => {
  it('should validate total hours per level <= 30', () => {
    const sixiemeHours = [4.5, 4.5, 3.0, 4.0, 2.5, 3.0, 4.0, 1.0, 1.0, 1.5];
    const total = sixiemeHours.reduce((sum, h) => sum + h, 0);

    expect(total).toBeLessThanOrEqual(30);
    expect(total).toBe(29.0);
  });

  it('should reject level schedule exceeding 30 hours', () => {
    const invalidSchedule = [5, 5, 4, 4, 3, 3, 3, 2, 2, 2]; // Total 33 hours

    const total = invalidSchedule.reduce((sum, h) => sum + h, 0);

    expect(() => {
      if (total > 30) throw new Error('Schedule exceeds 30-hour limit');
    }).toThrow();
  });
});
```

#### Scenario 6: Special Room Requirements

**Objective:** Identify subjects requiring special facilities.

**Test Data:**
```typescript
const physicsChemistry = {
  subject_code: "PHYS",
  subject_name_fr: "Physique-Chimie",
  requires_special_room: true,
  special_room_type: "science_lab",
  requires_block_schedule: true
};
```

**Expected Behavior:**
- Subject flagged for lab requirement
- Block scheduling requirement noted
- Integration with Module 9 (Facility Planning)

**Example Test Code:**
```typescript
describe('Special Room Requirements', () => {
  it('should identify subjects requiring special facilities', async () => {
    const subject = await Subject.create({
      subject_code: "PHYS",
      subject_name_fr: "Physique-Chimie",
      subject_name_en: "Physics-Chemistry",
      subject_type: SubjectType.CORE,
      requires_special_room: true,
      special_room_type: "science_lab",
      requires_block_schedule: true
    });

    const subjectsNeedingLabs = await Subject.findAll({
      where: {
        requires_special_room: true,
        special_room_type: "science_lab"
      }
    });

    expect(subjectsNeedingLabs.length).toBeGreaterThan(0);
    expect(subjectsNeedingLabs.some(s => s.subject_code === "PHYS")).toBe(true);
  });
});
```

#### Scenario 7: RLS Policy - Manager Access

**Objective:** Verify managers can modify hours matrix for working budget versions.

**Expected Behavior:**
- Manager can create/update hours for working versions
- Manager has read-only access to approved versions

**Example Test Code:**
```python
def test_rls_manager_subject_hours():
    """Test manager can modify subject hours for working versions."""
    # Setup: working budget version
    working_version = create_working_budget_version()

    # Authenticate as manager
    set_user_role("manager")

    # Manager can create hours entry
    hours_entry = SubjectHoursMatrix(
        budget_version_id=working_version.id,
        subject_id=math_subject.id,
        level_id=sixieme_level.id,
        hours_per_week=Decimal("4.5")
    )
    db.session.add(hours_entry)
    db.session.commit()

    assert hours_entry.id is not None

    # Manager can update hours
    hours_entry.hours_per_week = Decimal("5.0")
    db.session.commit()

    refreshed = db.session.query(SubjectHoursMatrix).filter_by(id=hours_entry.id).first()
    assert refreshed.hours_per_week == Decimal("5.0")
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: subjects and subject_hours_matrix tables with RLS policies |

## Future Enhancements (Phase 5-6)

1. **Curriculum Editor UI**: Visual interface for managing subject hours matrix by level
2. **Curriculum Templates**: Pre-configured templates (French standard, IB, local adaptations)
3. **Hours Optimization Tool**: Recommend optimal hours distribution based on AEFE guidelines
4. **Visual Schedule Builder**: Drag-and-drop weekly schedule creation
5. **Conflict Detection**: Identify scheduling conflicts (special rooms, block requirements)
6. **Historical Comparison**: Compare curriculum hours across academic years
7. **AEFE Compliance Check**: Validate hours matrix against French national curriculum minimums
8. **Group Balancing Tool**: Optimize student distribution across language proficiency groups
9. **FTE Impact Calculator**: Real-time preview of teacher FTE changes when adjusting hours
10. **Bulk Import/Export**: Import hours matrix from Excel, export for AEFE reporting

## Notes

- **Phase 4 Scope**: This module implements database foundation (tables, constraints, RLS policies, migrations)
- **Business Logic**: Curriculum management UI and hours calculation engine will be implemented in Phases 5-6
- **French Curriculum Compliance**: Hours must align with French Ministère de l'Éducation nationale standards
- **AEFE Approval**: Major curriculum changes require AEFE approval before implementation
- **Secondary Focus**: This module applies only to Collège and Lycée (primary uses FTE-based model)
- **DHG Foundation**: Subject hours are the PRIMARY INPUT for DHG workforce planning calculations
- **Local Requirements**: Arabic hours must satisfy Saudi Ministry of Education mandates
- **Group Flexibility**: Group splitting allows flexible language instruction by proficiency level
- **Room Planning Integration**: Special room requirements feed directly into facility planning (Module 9)
