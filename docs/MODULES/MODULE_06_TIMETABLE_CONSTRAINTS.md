# Module 6: Timetable Constraints

## Overview

Module 6 defines scheduling rules and constraints that impact teacher workforce requirements and facility utilization. These constraints include parallel class scheduling, AEFE contractual requirements, block scheduling for practical subjects, resource limitations, and teacher workload rules. While not implementing an actual timetable solver, this module captures the parameters that affect peak demand calculations in Module 8 (DHG Workforce Planning).

**Layer**: Configuration Layer (Phase 1)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Timetable solver integration, constraint validation UI, API endpoints (Phase 5-6)

### Purpose

- Define scheduling constraints that affect teacher demand patterns
- Capture AEFE contractual requirements (e.g., Wednesday PM off)
- Specify block scheduling needs for practical subjects
- Set resource capacity limits (labs, special rooms)
- Configure teacher workload constraints
- Calculate peak demand factors for workforce planning
- Support "what-if" scheduling scenario analysis

### Key Design Decisions

1. **Constraint-Driven**: Focus on constraints that impact workforce/facility planning, not full timetable generation
2. **Peak Demand Focus**: Primary purpose is calculating peak teacher demand for Module 8 (DHG)
3. **AEFE Compliance**: Wednesday PM off is hardcoded as mandatory (French school system requirement)
4. **Parallel Classes Option**: Support both parallel (same level simultaneously) and staggered scheduling
5. **Flexible Rule Engine**: JSON-based rule definitions allow complex constraint expressions

## Database Schema

### Tables

#### 1. timetable_constraints

Scheduling rules and constraints configuration.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
constraint_type       constrainttype NOT NULL    -- ENUM: schedule, subject, resource, teacher
constraint_name       VARCHAR(200) NOT NULL
description           TEXT NULL
applies_to            VARCHAR(200) NOT NULL      -- Levels, subjects, or teachers affected
rule_definition       JSONB NOT NULL             -- Detailed constraint parameters
is_mandatory          BOOLEAN NOT NULL DEFAULT true
priority              INTEGER NOT NULL DEFAULT 100
effective_date        DATE NOT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- priority >= 0 AND priority <= 1000 (higher = more important)
- If is_mandatory = true, constraint must be satisfied (hard constraint)
- If is_mandatory = false, constraint is preference (soft constraint)

**RLS Policies:**
- Admin: Full access to timetable constraints
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (budget_version_id, constraint_type)
- Index on priority for conflict resolution

#### 2. school_day_structure

Daily time slot configuration.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
slot_number           INTEGER NOT NULL           -- 1-8 (S1-S6 + breaks)
slot_name             VARCHAR(50) NOT NULL       -- S1, Break, S2, etc.
start_time            TIME NOT NULL
end_time              TIME NOT NULL
duration_minutes      INTEGER NOT NULL
is_teaching_slot      BOOLEAN NOT NULL DEFAULT true
day_of_week           INTEGER NULL               -- 0-6 (Sunday=0), NULL = all days
academic_year         VARCHAR(20) NOT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- slot_number >= 1
- end_time > start_time
- duration_minutes > 0
- day_of_week IN (0,1,2,3,4) for Sunday-Thursday (Saudi work week)
- UNIQUE (budget_version_id, slot_number, day_of_week, academic_year)

**RLS Policies:**
- All authenticated users can read school day structure
- Only admins can modify time slots

**Indexes:**
- Primary key on id
- Index on (budget_version_id, is_teaching_slot)

#### 3. peak_demand_config

Configuration for peak demand factor calculation.

**Columns:**
```sql
id                        UUID PRIMARY KEY
budget_version_id         UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
parallel_classes_enabled  BOOLEAN NOT NULL DEFAULT false
wednesday_pm_off          BOOLEAN NOT NULL DEFAULT true  -- AEFE requirement
morning_core_subjects     BOOLEAN NOT NULL DEFAULT true  -- Core subjects before noon
max_consecutive_hours     INTEGER NOT NULL DEFAULT 3
lab_capacity_limit        INTEGER NOT NULL DEFAULT 2     -- Max simultaneous lab classes
academic_year             VARCHAR(20) NOT NULL
notes                     TEXT NULL
created_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at                TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- max_consecutive_hours between 1 and 6
- lab_capacity_limit >= 1

**RLS Policies:**
- Same as timetable_constraints

**Indexes:**
- Primary key on id
- Index on budget_version_id

### Enums

#### ConstraintType
```sql
CREATE TYPE efir_budget.constrainttype AS ENUM (
    'schedule',    -- Scheduling patterns (parallel classes, time preferences)
    'subject',     -- Subject-specific (block scheduling, room requirements)
    'resource',    -- Resource limits (lab capacity, room availability)
    'teacher'      -- Teacher workload (max consecutive, breaks, AEFE rules)
);
```

## Data Model

### Sample Timetable Constraints

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440600",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "constraint_type": "teacher",
    "constraint_name": "Wednesday PM Off (AEFE)",
    "description": "AEFE teachers contractually off Wednesday afternoon",
    "applies_to": "All AEFE teachers",
    "rule_definition": {
      "day": "Wednesday",
      "period": "PM",
      "slots_blocked": ["S5", "S6"],
      "reason": "AEFE contract requirement"
    },
    "is_mandatory": true,
    "priority": 1000,
    "effective_date": "2025-09-01"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440601",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "constraint_type": "subject",
    "constraint_name": "Science Lab Block Scheduling",
    "description": "Physics-Chemistry and SVT require 2-hour consecutive blocks",
    "applies_to": "Physique-Chimie, SVT",
    "rule_definition": {
      "subjects": ["PHYS", "SVT"],
      "block_duration_hours": 2,
      "requires_consecutive_slots": true,
      "room_type_required": "science_lab"
    },
    "is_mandatory": true,
    "priority": 900,
    "effective_date": "2025-09-01"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440602",
    "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
    "constraint_type": "schedule",
    "constraint_name": "Parallel Classes (Same Level)",
    "description": "All classes of same level taught simultaneously for efficiency",
    "applies_to": "All levels",
    "rule_definition": {
      "enabled": false,
      "note": "If enabled, all 6ème classes get Math at same time, all 5ème at same time, etc.",
      "impact": "Increases peak teacher demand but simplifies scheduling"
    },
    "is_mandatory": false,
    "priority": 500,
    "effective_date": "2025-09-01"
  }
]
```

### Sample School Day Structure (EFIR)

```json
[
  {"slot_number": 1, "slot_name": "S1", "start_time": "07:30", "end_time": "08:30", "duration_minutes": 60, "is_teaching_slot": true},
  {"slot_number": 2, "slot_name": "S2", "start_time": "08:30", "end_time": "09:30", "duration_minutes": 60, "is_teaching_slot": true},
  {"slot_number": 3, "slot_name": "Break", "start_time": "09:30", "end_time": "09:45", "duration_minutes": 15, "is_teaching_slot": false},
  {"slot_number": 4, "slot_name": "S3", "start_time": "09:45", "end_time": "10:45", "duration_minutes": 60, "is_teaching_slot": true},
  {"slot_number": 5, "slot_name": "S4", "start_time": "10:45", "end_time": "11:45", "duration_minutes": 60, "is_teaching_slot": true},
  {"slot_number": 6, "slot_name": "Lunch", "start_time": "11:45", "end_time": "12:30", "duration_minutes": 45, "is_teaching_slot": false},
  {"slot_number": 7, "slot_name": "S5", "start_time": "12:30", "end_time": "13:30", "duration_minutes": 60, "is_teaching_slot": true},
  {"slot_number": 8, "slot_name": "S6", "start_time": "13:30", "end_time": "14:30", "duration_minutes": 60, "is_teaching_slot": true}
]
```

**Total Teaching Slots per Day:** 6 hours (S1-S6)
**Total Teaching Slots per Week:** 30 hours (6 slots × 5 days)

### Sample Peak Demand Config

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440610",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "parallel_classes_enabled": false,
  "wednesday_pm_off": true,
  "morning_core_subjects": true,
  "max_consecutive_hours": 3,
  "lab_capacity_limit": 2,
  "academic_year": "2025-2026",
  "notes": "Conservative scheduling: staggered classes, strict break requirements"
}
```

## Business Rules

### Timetable Constraint Rules

1. **Hard vs. Soft Constraints**: is_mandatory=true means must be satisfied, false means preference
2. **Priority-Based Conflict Resolution**: Higher priority (900-1000) constraints take precedence
3. **AEFE Wednesday PM**: Mandatory constraint, cannot be overridden (contractual requirement)
4. **Block Scheduling**: 2-hour blocks required for labs (Physique-Chimie, SVT)
5. **Constraint Versioning**: Constraints tied to budget version for historical tracking

### School Day Structure Rules

1. **Fixed Schedule**: 7:30-14:30 (7 hours total including breaks)
2. **Teaching Slots**: 6 × 1-hour slots per day = 6 hours
3. **Saudi Work Week**: Sunday-Thursday (5 days), Friday-Saturday weekend
4. **Break Requirements**: 15-minute break mid-morning, 45-minute lunch
5. **Slot Immutability**: Time slot structure rarely changes (requires admin approval)

### Peak Demand Rules

1. **Parallel Classes Impact**: If enabled, peak demand = max(classes per level)
   - Example: 6 classes of 6ème need 6 teachers simultaneously for same subject
2. **Wednesday PM Reduction**: Reduces effective weekly teaching slots by 20% (2 of 10 PM slots)
3. **Lab Capacity Constraint**: Max 2 simultaneous lab classes limits science scheduling
4. **Morning Core Subjects**: Concentrates demand in AM slots (S1-S4)
5. **Max Consecutive Hours**: Teachers cannot teach > 3 consecutive hours without break

### Calculation Rules

1. **Available Weekly Slots**: 30 hours (6 slots/day × 5 days) - Wednesday PM (2 hours) = 28 hours effective
2. **Peak Demand Factor**: Multiplier for teacher requirements when parallel scheduling used
3. **Room Utilization**: Special rooms (labs) have capacity constraints affecting scheduling

## Calculation Examples

### Example 1: Peak Demand Factor (Parallel Classes Enabled)

**Context**: Calculate peak teacher demand when parallel classes are enabled for Collège Mathématiques.

**Given Data:**
- Collège levels: 6ème (6 classes), 5ème (6 classes), 4ème (5 classes), 3ème (4 classes)
- Parallel classes: Enabled
- Subject: Mathématiques (all Collège levels)

**Formula:**
```
peak_demand_factor = max(classes_per_level)
```

**Calculation:**
```
6ème: 6 classes
5ème: 6 classes
4ème: 5 classes
3ème: 4 classes

Peak demand = max(6, 6, 5, 4) = 6 classes

Implication: Need 6 Mathématiques teachers available simultaneously during peak slot
```

**Result:** Peak demand factor = 6 (need 6 teachers at same time for 6ème and 5ème)

### Example 2: Available Teaching Slots (With AEFE Wednesday PM Off)

**Context**: Calculate effective weekly teaching slots considering Wednesday PM off.

**Given Data:**
- Teaching slots per day: 6 hours
- Days per week: 5 (Sunday-Thursday)
- Wednesday PM off: Yes (AEFE requirement)
- Wednesday PM slots: 2 (S5, S6)

**Calculation:**
```
Total weekly slots = 6 slots/day × 5 days = 30 hours

Wednesday PM reduction = 2 slots blocked

Effective weekly slots = 30 - 2 = 28 hours available
```

**Result:** Teachers have 28 effective weekly teaching slots (reduced from 30 due to Wednesday PM off).

**Impact on Workforce:**
```
If teacher standard hours = 18h/week
Utilization = 18 ÷ 28 = 64.3% of available slots
```

## Integration Points

### Upstream Dependencies

1. **Module 1 (System Configuration)**: Academic structure, work week definition
2. **Module 3 (Subject Hours)**: Block scheduling requirements by subject

### Downstream Consumers

1. **Module 8 (DHG Workforce Planning)**: Peak demand factor affects teacher FTE calculations
2. **Module 9 (Facility Planning)**: Resource constraints inform room utilization
3. **Future Timetable Generation**: Constraints feed into automated timetabling (Phase 5-6)

### Data Flow

```
Timetable Constraints (Module 6) → Peak Demand Factor
                                           ↓
                   DHG Workforce Planning (Module 8)
           Teacher FTE × Peak Factor = Adjusted FTE Requirements
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions/:id/timetable-constraints
POST   /api/v1/budget-versions/:id/timetable-constraints
GET    /api/v1/budget-versions/:id/school-day-structure
POST   /api/v1/calculate-peak-demand
       Request: { class_structure, parallel_enabled }
       Response: { peak_demand_factor, affected_subjects }
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Peak Demand Calculation (Parallel Classes)

**Test Data:**
```typescript
const classStructure = { "6ème": 6, "5ème": 6, "4ème": 5, "3ème": 4 };
const parallelEnabled = true;
```

**Expected:**
```typescript
const peakDemand = Math.max(...Object.values(classStructure));
expect(peakDemand).toBe(6);
```

#### Scenario 2: Available Slots Calculation

**Test Data:**
```typescript
const slotsPerDay = 6;
const daysPerWeek = 5;
const wednesdayPMOff = true;
```

**Expected:**
```typescript
const totalSlots = slotsPerDay * daysPerWeek;
const blockedSlots = wednesdayPMOff ? 2 : 0;
const availableSlots = totalSlots - blockedSlots;
expect(availableSlots).toBe(28);
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: timetable_constraints, school_day_structure, peak_demand_config tables |

## Future Enhancements (Phase 5-6)

1. **Timetable Solver Integration**: Automated timetable generation respecting all constraints
2. **Constraint Validation UI**: Visual interface for testing constraint conflicts
3. **Peak Demand Visualization**: Heatmap showing teacher demand by day/slot
4. **What-If Scenarios**: Model impact of different scheduling approaches
5. **Teacher Preference Integration**: Incorporate teacher availability and preferences
6. **Room Booking System**: Real-time facility allocation based on constraints
7. **Conflict Detection**: Automated detection of impossible constraint combinations
8. **Optimization Engine**: Suggest optimal schedule balancing all constraints

## Notes

- **Phase 4 Scope**: Database foundation only - constraint storage, no timetable solver
- **Business Logic**: Actual timetable generation deferred to Phase 5-6
- **Peak Demand Focus**: Primary purpose is workforce planning input, not scheduling
- **AEFE Compliance**: Wednesday PM off is non-negotiable (French contract requirement)
- **Constraint Evolution**: Constraints may change as scheduling philosophy evolves
