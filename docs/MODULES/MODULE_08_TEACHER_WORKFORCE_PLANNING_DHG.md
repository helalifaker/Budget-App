# Module 8: Teacher Workforce Planning (DHG)

## Overview

Module 8 is the **core workforce planning module** for EFIR, implementing the French DHG (Dotation Horaire Globale - Global Hours Allocation) methodology for secondary education and class-based staffing for primary education. This module calculates teacher FTE requirements from class structure and curriculum hours, performs gap analysis (TRMD) against available AEFE and local positions, and determines HSA (overtime) allocation and recruitment needs.

**Layer**: Planning Layer (Phase 2)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: DHG calculation engine, TRMD visualization, recruitment planning tools (Phase 5-6)

### Purpose

- Calculate primary teacher requirements (class-based model with specialists)
- Calculate secondary teacher requirements using DHG hours-based methodology
- Perform gap analysis (TRMD - Tableau de Répartition des Moyens par Discipline)
- Allocate HSA (Heures Supplémentaires Annuelles - overtime) within caps
- Determine recruitment needs and AEFE position requests
- Calculate total personnel costs (integration with Module 4 - Teacher Costs)
- Validate against AEFE H/E (Heures/Élève) ratio benchmarks

### Key Design Decisions

1. **Dual Models**: Primary uses class-based (1 teacher per class + specialists), Secondary uses DHG hours-based
2. **DHG Formula**: Total Hours = Σ(classes × hours_per_subject), FTE = Total Hours ÷ 18 (standard hours)
3. **Gap Analysis (TRMD)**: Required FTE - AEFE Positions - Local Staff = Deficit
4. **HSA Strategy**: Fill small deficits with overtime (max 4h/teacher), recruit for larger gaps
5. **AEFE Structure**: 28 total positions (24 school-paid détachés + 4 AEFE-funded)

## DHG (Dotation Horaire Globale) Methodology

### Overview of DHG

**DHG** is the French education system's method for calculating teacher workforce requirements based on **total teaching hours needed** rather than teacher-to-student ratios. This ensures curriculum coverage and pedagogical quality.

**Key Concepts:**
- **Total Subject Hours**: Sum of (number of classes × hours per week for that subject)
- **Standard Teaching Hours**: 18 hours/week for secondary teachers, 24 hours/week for primary
- **FTE Calculation**: Total Subject Hours ÷ Standard Hours = FTE required
- **H/E Ratio**: Hours per Student ratio - AEFE benchmark for quality validation

**Hours-Based vs. FTE-Based:**
- **Primary (Maternelle + Élémentaire)**: FTE-based (1 generalist per class + specialists)
- **Secondary (Collège + Lycée)**: Hours-based (DHG methodology)

**Example:**
```
Mathématiques in Collège:
- 6ème: 6 classes × 4.5h = 27h
- 5ème: 6 classes × 3.5h = 21h
- 4ème: 5 classes × 3.5h = 17.5h
- 3ème: 4 classes × 3.5h = 14h
Total: 79.5 hours/week
FTE: 79.5 ÷ 18 = 4.42 → Need 5 Math teachers
```

## Database Schema

### Tables

#### 1. primary_workforce_requirements

Primary teacher and ATSEM FTE requirements (class-based model).

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
scenario_name         VARCHAR(50) NULL DEFAULT 'base'
total_primary_classes INTEGER NOT NULL
generalist_fte        INTEGER NOT NULL               -- 1 per class
specialist_fte        INTEGER NOT NULL               -- ~35% of generalist
atsem_fte             INTEGER NOT NULL               -- Maternelle only
total_teaching_fte    INTEGER NOT NULL               -- generalist + specialist
specialist_ratio      NUMERIC(4, 2) NOT NULL DEFAULT 0.35
notes                 TEXT NULL
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- total_teaching_fte = generalist_fte + specialist_fte
- generalist_fte >= total_primary_classes (minimum 1 per class)

**RLS Policies:**
- Admin: Full access
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

#### 2. secondary_dhg_subject_hours

DHG hours calculation per subject (secondary only).

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
scenario_name         VARCHAR(50) NULL DEFAULT 'base'
subject_id            UUID NOT NULL FOREIGN KEY -> subjects.id (RESTRICT)
total_hours_per_week  NUMERIC(8, 2) NOT NULL
simple_fte            NUMERIC(6, 2) NOT NULL         -- hours ÷ 18
peak_demand_factor    NUMERIC(4, 2) NOT NULL DEFAULT 1.0
adjusted_fte          INTEGER NOT NULL               -- CEIL(simple_fte × peak_factor)
hours_breakdown_json  JSONB NULL                     -- By level detail
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- total_hours_per_week >= 0
- simple_fte = total_hours_per_week ÷ 18
- adjusted_fte >= CEIL(simple_fte × peak_demand_factor)

**Indexes:**
- Primary key on id
- Index on (budget_version_id, subject_id)

#### 3. trmd_gap_analysis

TRMD (Tableau de Répartition des Moyens par Discipline) - staffing gap analysis.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
scenario_name         VARCHAR(50) NULL DEFAULT 'base'
subject_id            UUID NOT NULL FOREIGN KEY -> subjects.id (RESTRICT)
besoins_fte           NUMERIC(6, 2) NOT NULL         -- Required FTE (from DHG)
hp_aefe               NUMERIC(6, 2) NOT NULL DEFAULT 0  -- AEFE positions
hp_local              NUMERIC(6, 2) NOT NULL DEFAULT 0  -- Local staff
deficit_fte           NUMERIC(6, 2) NOT NULL         -- besoins - (hp_aefe + hp_local)
hsa_proposed_hours    NUMERIC(8, 2) NULL             -- Overtime hours to fill gap
recruitment_needed_fte INTEGER NULL                  -- New hires needed
notes                 TEXT NULL
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- deficit_fte = besoins_fte - (hp_aefe + hp_local)
- hsa_proposed_hours >= 0 AND hsa_proposed_hours <= (hp_aefe + hp_local) × 4 (max 4h/teacher)

**Indexes:**
- Primary key on id
- Index on (budget_version_id, subject_id)

#### 4. aefe_position_allocation

AEFE teacher position assignments by subject/level.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
teacher_type          aefeteachertype NOT NULL      -- detache or funded
subject_id            UUID NULL                     -- NULL for primary generalist
level_id              UUID NULL
fte_allocation        NUMERIC(4, 2) NOT NULL
position_status       positionstatus NOT NULL       -- active, requested, withdrawn
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- fte_allocation > 0
- Total AEFE allocations across all subjects should not exceed 28 FTE (EFIR's AEFE quota)

### Enums

#### PositionStatus
```sql
CREATE TYPE efir_budget.positionstatus AS ENUM (
    'active',      -- Currently filled AEFE position
    'requested',   -- New position request to AEFE
    'withdrawn'    -- Position being returned to AEFE
);
```

## Data Model

### Sample Primary Workforce (2025-2026, Period 2)

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440800",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "academic_period_id": "period-2-sep-dec-uuid",
  "scenario_name": "base",
  "total_primary_classes": 36,
  "generalist_fte": 36,
  "specialist_fte": 13,
  "atsem_fte": 11,
  "total_teaching_fte": 49,
  "specialist_ratio": 0.35,
  "notes": "Maternelle (11 classes) + Élémentaire (25 classes) = 36 total"
}
```

### Sample Secondary DHG (Mathématiques)

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440810",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "subject_id": "subject-math-uuid",
  "total_hours_per_week": 79.5,
  "simple_fte": 4.42,
  "peak_demand_factor": 1.0,
  "adjusted_fte": 5,
  "hours_breakdown_json": {
    "6ème": {"classes": 6, "hours_per_class": 4.5, "total": 27.0},
    "5ème": {"classes": 6, "hours_per_class": 3.5, "total": 21.0},
    "4ème": {"classes": 5, "hours_per_class": 3.5, "total": 17.5},
    "3ème": {"classes": 4, "hours_per_class": 3.5, "total": 14.0}
  }
}
```

### Sample TRMD Gap Analysis (Français)

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440820",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "subject_id": "subject-francais-uuid",
  "besoins_fte": 9.94,
  "hp_aefe": 6.0,
  "hp_local": 3.0,
  "deficit_fte": 0.94,
  "hsa_proposed_hours": 16.92,
  "recruitment_needed_fte": 0,
  "notes": "Deficit filled by HSA (0.94 FTE × 18h = 16.92h distributed across 9 teachers)"
}
```

## Business Rules

### Primary Workforce Rules

1. **Generalist Teachers**: Exactly 1 per primary class (Maternelle + Élémentaire)
2. **Specialist Teachers**: ~35% additional for languages, PE, arts, music
3. **ATSEM**: 1 per Maternelle class (PS, MS, GS)
4. **Standard Hours**: Primary teachers work 24 hours/week (vs 18 for secondary)
5. **No HSA for Primary**: Primary teachers do not receive overtime hours

### Secondary DHG Rules

1. **Standard Teaching Hours**: 18 hours/week for all secondary teachers
2. **DHG Formula**: Total Hours = Σ(classes per level × hours per subject per level)
3. **FTE Calculation**: Simple FTE = Total Hours ÷ 18, then round up
4. **Peak Demand Adjustment**: If parallel classes enabled, multiply by peak factor
5. **Subject Specialization**: Each teacher typically teaches 1-2 subjects only

### TRMD (Gap Analysis) Rules

1. **Besoins (Needs)**: Required FTE from DHG calculation
2. **HP Disponible (Available)**: AEFE positions + Local staff positions
3. **Deficit Calculation**: Besoins - HP Disponible = Deficit
4. **HSA Strategy**: If deficit < 2 FTE and available staff exists, use HSA
5. **Recruitment Trigger**: If deficit ≥ 2 FTE or HSA cap exceeded, recruit

### HSA (Overtime) Rules

1. **HSA Cap**: Maximum 4 hours/week per teacher (exceptionally 2h for some)
2. **Distribution**: Spread HSA across multiple teachers (avoid overloading one teacher)
3. **HSA Calculation**: Deficit FTE × 18 hours = Total HSA hours needed
4. **Payment Period**: HSA paid over 10 months (September-June)
5. **AEFE Exemption**: AEFE teachers do not receive HSA (reassignment or recruitment only)

### AEFE Position Rules

1. **Total Quota**: EFIR has 28 AEFE positions (24 détachés + 4 funded)
2. **Position Allocation**: Assigned by subject and level based on DHG needs
3. **Request Process**: New position requests submitted annually to AEFE
4. **Funding**: Détachés cost school ~41,863 EUR/year (PRRD), funded are free
5. **Stability**: AEFE positions rarely change year-over-year (multi-year commitments)

### H/E Ratio Validation

1. **H/E Ratio**: (Total DHG Hours) ÷ (Total Secondary Students)
2. **AEFE Benchmarks**: Collège 1.27-1.71, Lycée 1.40-1.97 (varies by class size)
3. **Quality Indicator**: Higher H/E = more teaching hours per student = better quality
4. **Validation Check**: Calculate EFIR H/E and compare to AEFE benchmarks
5. **Outliers**: H/E significantly below benchmark indicates understaffing risk

## Calculation Examples

### Example 1: Primary Workforce Calculation

**Context**: Calculate primary teacher requirements for Maternelle + Élémentaire.

**Given Data:**
- Maternelle: 11 classes (PS: 3, MS: 4, GS: 4)
- Élémentaire: 25 classes (CP: 5, CE1: 5, CE2: 5, CM1: 5, CM2: 5)
- Specialist ratio: 35%

**Calculation:**
```
Total primary classes = 11 + 25 = 36 classes

Generalist teachers = 36 FTE (1 per class)

Specialist teachers = CEIL(36 × 0.35) = CEIL(12.6) = 13 FTE
  (Languages, PE, arts, music across all primary)

ATSEM = 11 (1 per Maternelle class)

Total teaching FTE = 36 + 13 = 49 FTE
Total staff (including ATSEM) = 49 + 11 = 60 FTE
```

**Result:** 49 teaching FTE + 11 ATSEM = 60 total primary staff

### Example 2: Secondary DHG Calculation (Mathématiques)

**Context**: Calculate Math teacher requirements for Collège using DHG.

**Given Class Structure:**
- 6ème: 6 classes
- 5ème: 6 classes
- 4ème: 5 classes
- 3ème: 4 classes

**Hours Matrix (from Module 3):**
- 6ème: 4.5 hours/week
- 5ème: 3.5 hours/week
- 4ème: 3.5 hours/week
- 3ème: 3.5 hours/week

**DHG Calculation:**
```
6ème: 6 classes × 4.5h = 27.0 hours
5ème: 6 classes × 3.5h = 21.0 hours
4ème: 5 classes × 3.5h = 17.5 hours
3ème: 4 classes × 3.5h = 14.0 hours
───────────────────────────────────
Total hours/week:     79.5 hours

Simple FTE = 79.5 ÷ 18 = 4.42 FTE
Adjusted FTE = CEIL(4.42 × 1.0) = 5 FTE

Result: Need 5 Mathématiques teachers for Collège
```

### Example 3: Arabic (LVB) with Group Splitting

**Context**: Calculate Arabic teacher requirements with proficiency grouping.

**Given Data:**
- Arabic offered in all Collège levels
- 2.5 hours/week per level
- 3 proficiency groups per level (beginners, intermediate, advanced)

**Calculation:**
```
Hours per level (single group): 2.5h
Groups per level: 3
Hours per level (all groups): 2.5h × 3 = 7.5h

6ème: 7.5 hours
5ème: 7.5 hours
4ème: 7.5 hours
3ème: 7.5 hours
─────────────────
Total: 30.0 hours/week

FTE = 30.0 ÷ 18 = 1.67 → 2 Arabic teachers needed
```

**Alternative Staffing:**
```
Option 1: 2 full-time teachers (2 × 18h = 36h capacity, 30h used = 83% utilization)
Option 2: 1 full-time (18h) + 12h HSA = 30h covered
```

### Example 4: TRMD Gap Analysis (Français)

**Context**: Perform gap analysis for Français (French language).

**Given Data:**
- Required FTE (from DHG): 9.94 FTE
- AEFE positions: 6 FTE
- Local staff: 3 FTE

**TRMD Calculation:**
```
Besoins (Required): 9.94 FTE
HP AEFE:            6.00 FTE
HP Local:           3.00 FTE
HP Disponible:      9.00 FTE
─────────────────────────
Deficit:            0.94 FTE

Convert deficit to hours: 0.94 × 18 = 16.92 hours/week

HSA Strategy:
  Available teachers: 6 + 3 = 9 teachers
  HSA per teacher: 16.92 ÷ 9 = 1.88 hours/teacher
  Is 1.88h < 4h cap? Yes ✓

Conclusion: Fill gap with HSA (no recruitment needed)
```

**Result:** Deficit of 0.94 FTE filled by distributing 17 HSA hours across 9 teachers (~2h each).

### Example 5: H/E Ratio Validation (Collège)

**Context**: Validate EFIR Collège staffing against AEFE H/E benchmarks.

**Given Data:**
- Total Collège students: 540
- Total DHG hours (all subjects): 719.5 hours/week
- Average class size: ~26 students

**H/E Calculation:**
```
H/E Ratio = Total DHG Hours ÷ Total Students
         = 719.5 ÷ 540
         = 1.33 hours per student

AEFE Benchmark (class size 26): 1.27 H/E

Comparison:
  EFIR actual: 1.33
  AEFE benchmark: 1.27
  Variance: +0.06 (+4.7% above benchmark) ✓

Status: EFIR exceeds AEFE quality benchmark (good)
```

**Interpretation:** EFIR provides 1.33 hours of teaching per student, slightly above AEFE standard of 1.27, indicating strong pedagogical quality.

## Integration Points

### Upstream Dependencies

1. **Module 7 (Enrollment Planning)**: Class structure by level
2. **Module 3 (Subject Hours)**: Hours matrix for DHG calculation
3. **Module 2 (Class Size Parameters)**: ATSEM requirements
4. **Module 4 (Teacher Costs)**: Salary scales for cost calculation
5. **Module 6 (Timetable Constraints)**: Peak demand factors

### Downstream Consumers

1. **Module 11 (Cost Planning)**: Personnel costs (FTE × cost parameters)
2. **Module 13 (Budget Consolidation)**: Workforce summary rollup
3. **HR/Recruitment**: Hiring needs and AEFE position requests

### Data Flow

```
Enrollment → Class Structure (Module 7)
      +
Subject Hours Matrix (Module 3)
      ↓
DHG Calculation (Module 8)
Total Hours → FTE Requirements
      ↓
TRMD Gap Analysis
Required FTE - Available Positions = Deficit
      ↓
HSA Allocation + Recruitment Needs
      ↓
Personnel Cost Calculation (Module 11)
FTE × Cost Parameters (Module 4)
```

## API Endpoints (Future Implementation)

```
POST   /api/v1/budget-versions/:id/calculate-primary-workforce
POST   /api/v1/budget-versions/:id/calculate-secondary-dhg
POST   /api/v1/budget-versions/:id/calculate-trmd-gap
GET    /api/v1/budget-versions/:id/workforce-summary
GET    /api/v1/budget-versions/:id/he-ratio-validation
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Primary Workforce Calculation
```typescript
const result = calculatePrimaryWorkforce({
  totalClasses: 36,
  specialistRatio: 0.35,
  maternelleClasses: 11
});
expect(result.generalist_fte).toBe(36);
expect(result.specialist_fte).toBe(13);
expect(result.atsem_fte).toBe(11);
```

#### Scenario 2: Secondary DHG Hours Aggregation
```typescript
const dhg = calculateDHG({
  "6ème": { classes: 6, hours: 4.5 },
  "5ème": { classes: 6, hours: 3.5 }
});
expect(dhg.total_hours).toBe(48.0); // 27 + 21
expect(dhg.simple_fte).toBeCloseTo(2.67, 2);
```

#### Scenario 3: TRMD Gap Analysis
```typescript
const trmd = calculateTRMD({
  besoins: 9.94,
  aefe: 6,
  local: 3
});
expect(trmd.deficit).toBeCloseTo(0.94, 2);
expect(trmd.hsa_proposed).toBeCloseTo(16.92, 2);
```

#### Scenario 4: HSA Cap Enforcement
```typescript
const deficit = 5; // FTE
const availableTeachers = 10;
const hsaHours = deficit * 18; // 90 hours
const hsaPerTeacher = hsaHours / availableTeachers; // 9 hours
expect(hsaPerTeacher).toBeGreaterThan(4); // Exceeds cap
// Should trigger recruitment, not HSA
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: DHG methodology, TRMD gap analysis, workforce tables |

## Future Enhancements (Phase 5-6)

1. **DHG Calculation Engine**: Automated DHG calculation from enrollment changes
2. **TRMD Visualization**: Interactive gap analysis dashboard with drill-down
3. **HSA Optimizer**: Optimal distribution of overtime across available teachers
4. **Recruitment Planning**: Automated job posting generation for deficit positions
5. **AEFE Position Manager**: Track AEFE position lifecycle (request, allocation, renewal)
6. **H/E Ratio Monitoring**: Real-time comparison to AEFE benchmarks with alerts
7. **What-If Scenarios**: Model workforce impact of enrollment/curriculum changes
8. **Multi-Year Staffing**: Project staffing needs for 5-year strategic plan

## Notes

- **Phase 4 Scope**: Database foundation only
- **DHG Methodology**: Core of French education workforce planning - must be implemented exactly as specified
- **AEFE Dependency**: EFIR's 28 AEFE positions are critical cost advantage (vs all-local staffing)
- **TRMD Tool**: Essential for annual budget planning and AEFE reporting
- **H/E Validation**: Quality indicator - EFIR should maintain or exceed AEFE benchmarks
- **Cost Driver**: Workforce is largest cost component (~50-60% of budget)
