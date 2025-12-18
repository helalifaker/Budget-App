# EFIR Enrollment Projection - Detailed Implementation Plan

## Document Info
- **Version**: 1.1
- **Created**: December 2025
- **Status**: Phase 2 — Core Calculation Engine (in progress)
- **Owner**: Development Team
- **Last Updated**: December 2025 (Phase 2 kickoff)

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Business Requirements](#2-business-requirements)
3. [Technical Architecture](#3-technical-architecture)
4. [Database Schema](#4-database-schema)
5. [Backend Implementation](#5-backend-implementation)
6. [Frontend Implementation](#6-frontend-implementation)
7. [UI/UX Design](#7-uiux-design)
8. [Implementation Phases](#8-implementation-phases)
9. [Testing Strategy](#9-testing-strategy)
10. [Appendices](#appendices)

---

## Phase Progress Update

- Phase 1 (Database Foundation): Design artifacts frozen; ready for database-supabase agent to implement migrations/seed data when scheduled.
- Phase 2 (Core Calculation Engine): Now active focus. Objective is to deliver the retention + lateral-entry engine with override resolution, capacity clamp, and tests to unblock API/service wiring.
- Next gate: Finish Phase 2 verification (unit tests green) → start Phase 3 (Fiscal Year Proration) and Phase 4 (API layer).

---

## 1. Executive Summary

### 1.1 Overview

This document details the implementation of a **dynamic enrollment projection system** for EFIR that uses a **Retention + Lateral Entry** model with a **4-layer override architecture**. The system will **replace the current `/enrollment/planning` manual entry page** while preserving full override capability and a clear step-by-step enrollment planning workflow.

### 1.2 Key Features

| Feature | Description |
|---------|-------------|
| **3 Scenarios** | Worst Case, Base, Best Case |
| **4-Layer Overrides** | Scenario → Global → Level → Grade |
| **Real-time Calculation** | Auto-calculate as parameters change |
| **Capacity Management** | Auto-reduce when over configured capacity (default 1,850) with per-class breakdown |
| **Flexible Capacity** | Capacity is stored per budget version and can be changed at any time |
| **Fiscal Year Proration** | 8/12 prior SY + 4/12 current SY (tuition billed 6/10 + 4/10) |
| **Sparkline Visualization** | Historical trend per level |
| **Validation Workflow** | Cascade to downstream only on validation |

### 1.3 Core Formulas

**Entry Grade (PS):**
```
Students[PS, Y] = PS_Entry × (1 + Entry_Growth_Rate)^(Y - Base_Year)
```

**Other Grades:**
```
Students[G, Y] = Students[G-1, Y-1] × Retention_Rate + Lateral_Entry × Lateral_Multiplier
```

**Retention Rate Definition (Clarification)**:
- `Retention_Rate[G]` is the **grade-to-grade transition probability** from `G-1` in year `Y-1` to `G` in year `Y`.
- PS is an entry grade and **does not use retention**. The first transition rate is `Retention_Rate[MS]` (PS → MS).
- `default_retention` applies to all non-terminal transitions; `terminal_retention` applies only to `Retention_Rate[TLE]` (1ERE → TLE).

**Fiscal Year Proration (Critical):**
```
# Academic → Fiscal (Jan–Dec):
#  - Jan–Aug (8 months): use prior school year (SY N-1)
#  - Sep–Dec (4 months): use current school year (SY N)
Prorated_Enrollment = (SY_N-1 × 8/12) + (SY_N × 4/12)

# Tuition billing remains 10 months:
# Tuition_FY = (SY_N-1 × 6/10) + (SY_N × 4/10), then apply abatement/discounts
```

**Capacity Constraint (configurable):**
```
IF Total > Max_Capacity:
  reduction_factor = Max_Capacity / Total
  FOR EACH grade:
    adjusted_students = ROUND(students × reduction_factor)
    reduction_applied = original - adjusted
```

---

## 2. Business Requirements

### 2.1 Scenario Definitions (3 Scenarios)

| Parameter | Worst Case | Base | Best Case |
|-----------|------------|------|-----------|
| **PS Entry** | 45 | 65 | 85 |
| **Entry Growth Rate** | -2%/year | 0% | +3%/year |
| **Default Retention** | 90% | 96% | 99% |
| **Terminal Retention** | 92% | 98% | 100% |
| **Lateral Multiplier** | 0.3x | 1.0x | 1.5x |
| **Description** | Economic downturn, expat departures | Historical average continuation | Maximum growth, near-capacity |

### 2.2 Base Lateral Entry Values

These are the historical averages for lateral entry (new students joining mid-cycle):

| Grade | Base Lateral Entry | Notes |
|-------|-------------------|-------|
| PS | N/A | Entry grade (manual) |
| MS | 27 | High lateral entry point |
| GS | 20 | Continued lateral entry |
| CP | 12 | Elementary entry point |
| CE1 | 7 | Moderate |
| CE2 | 6 | Moderate |
| CM1 | 5 | Low |
| CM2 | 7 | Low |
| 6EME | 8 | Middle school entry point |
| 5EME | 5 | Low |
| 4EME | 6 | Low |
| 3EME | 6 | Low |
| 2NDE | 8 | High school entry point |
| 1ERE | 6 | Low |
| TLE | 1 | Minimal (terminal grade) |

### 2.3 4-Layer Override Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  LAYER 1: SCENARIO DEFAULTS                                             │
│  ─────────────────────────────────────────────────────────────────────  │
│  Select from: Worst Case | Base | Best Case                             │
│  All parameters derive from scenario selection                          │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 2: GLOBAL OVERRIDES                                              │
│  ─────────────────────────────────────────────────────────────────────  │
│  • PS Entry adjustment: ±20 from scenario default                       │
│  • Retention adjustment: ±5% from scenario default                      │
│  • Lateral multiplier: 0.5x - 1.5x                                      │
│  • Default class size: 20-30                                            │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 3: LEVEL OVERRIDES (per cycle)                                   │
│  ─────────────────────────────────────────────────────────────────────  │
│  For each of: Maternelle, Élémentaire, Collège, Lycée                  │
│  • Class size ceiling: 20-30                                            │
│  • Maximum divisions: 2-10                                              │
├─────────────────────────────────────────────────────────────────────────┤
│  LAYER 4: GRADE OVERRIDES (Highest Priority)                            │
│  ─────────────────────────────────────────────────────────────────────  │
│  For each of 15 grades:                                                 │
│  • Specific retention rate: 85%-100%                                    │
│  • Specific lateral entry count: 0-50                                   │
│  • Maximum divisions: 2-8                                               │
│  • Class size ceiling: 20-30                                            │
└─────────────────────────────────────────────────────────────────────────┘

RESOLUTION ORDER: Grade Override > Level Override > Global Override > Scenario Default
```

### 2.4 Fiscal Year Proration Logic

**Critical Business Rule**: School year runs September-August, but fiscal year is January-December.

When projecting for **Fiscal Year 2026**:
- **January - August 2026** (8 months): Students are in School Year 2025/2026
- **September - December 2026** (4 months): Students are in School Year 2026/2027

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         FISCAL YEAR 2026                                 │
├──────────────────────────────────────────────────────────────────────────┤
│  Jan  Feb  Mar  Apr  May  Jun  Jul  Aug │ Sep  Oct  Nov  Dec             │
│  ←─────── School Year 2025/2026 ───────→│←── School Year 2026/2027 ──→   │
│                 (8 months)               │        (4 months)             │
│                                     │                                    │
│  Use CURRENT enrollment data        │ Use PROJECTED enrollment           │
└──────────────────────────────────────────────────────────────────────────┘
```

**Formula for Fiscal Year Weighted Enrollment:**
```python
def calculate_fiscal_year_enrollment(
    current_school_year_enrollment: int,  # SY 2025/2026
    projected_school_year_enrollment: int  # SY 2026/2027
) -> float:
    """
    Returns weighted average for fiscal year reporting.
    """
    return (current_school_year_enrollment * 8/12) + (projected_school_year_enrollment * 4/12)
```

### 2.5 Nationality Distribution (Per Level)

Enrollment projections produce **total students per grade/level**. Downstream modules require **nationality-level breakdown**.

**Rule**: Each level total is split by nationality using **per-level percentages** from the existing `nationality_distributions` table (Module 7).

**Default (until real data is available):**
- French: **30%**
- Saudi: **2%**
- Other: **68%**

If no distribution record exists for a level in a budget version:
1. System **assumes the default percentages above**
2. System **creates `nationality_distributions` rows** for that version/level with the defaults
3. UI shows these defaults and allows the user to adjust later

**Rounding**:
- `french_count = ROUND(total × french_pct)`
- `saudi_count = ROUND(total × saudi_pct)`
- `other_count = total - french_count - saudi_count` (remainder to Other to preserve totals)

**Note**: Remainder-to-Other preserves totals but may cause minor % drift (±1 student) on small cohorts. This is acceptable for planning; if a fairer split is needed, use a largest‑remainder allocation.

These counts are written into `enrollment_plans` on validation (3 rows per level).

### 2.6 Capacity Management (Flexible)

**School Maximum Capacity**: **Configurable per budget version**, default **1,850 students**.

When projected total exceeds the configured capacity:
1. **Warning displayed** to user
2. **Automatic proportional reduction** applied
3. **Per-class reduction breakdown** shown

```python
def apply_capacity_constraint(
    enrollment_by_grade: dict[str, int],
    max_capacity: int = 1850  # default, overridden by config
) -> tuple[dict[str, int], dict[str, int]]:
    """
    Returns (adjusted_enrollment, reduction_per_grade)
    """
    total = sum(enrollment_by_grade.values())

    if total <= max_capacity:
        return enrollment_by_grade, {}

    reduction_factor = max_capacity / total
    adjusted = {}
    reductions = {}

    for grade, students in enrollment_by_grade.items():
        adjusted_count = round(students * reduction_factor)
        adjusted[grade] = adjusted_count
        reductions[grade] = students - adjusted_count

    return adjusted, reductions
```

### 2.7 Validation and Downstream Cascade

**Workflow States:**
1. **Draft** - Projection in progress, can modify freely
2. **Validated** - Locked, cascades to downstream modules

**Downstream Impact on Validation:**
- `nationality_distributions` populated if missing (default 30/2/68)
- `enrollment_plans` populated (level × nationality counts)
- `class_structures` auto-calculated
- DHG calculations triggered
- Revenue projections updated

---

## 3. Technical Architecture

### 3.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND (React)                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  EnrollmentPlanningPage (replaces /enrollment/planning)                     │
│  ├── WorkflowStepper (Projections → Distribution → Validation)              │
│  ├── ScenarioSelector (3 scenarios)                                         │
│  ├── GlobalOverridesPanel (sliders)                                         │
│  ├── LevelOverridesPanel (per cycle)                                        │
│  ├── GradeOverridesGrid (AG Grid, per grade)                               │
│  ├── ProjectionResultsGrid (5-year view with sparklines)                   │
│  ├── NationalityDistributionPanel (% by level)                              │
│  ├── CapacityWarningBanner (when over configured capacity)                 │
│  └── ValidationButton (cascade to downstream)                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              BACKEND (FastAPI)                              │
├─────────────────────────────────────────────────────────────────────────────┤
│  API Layer                                                                  │
│  └── enrollment_projection_router.py                                        │
│                                                                             │
│  Service Layer                                                              │
│  └── enrollment_projection_service.py                                       │
│                                                                             │
│  Calculation Engine                                                         │
│  └── projection_engine.py (pure functions)                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ SQLAlchemy
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE (PostgreSQL)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│  enrollment_scenarios (3 predefined)                                        │
│  enrollment_lateral_entry_defaults (14 grades)                              │
│  enrollment_projection_configs (per budget version)                         │
│  enrollment_global_overrides (Layer 2)                                      │
│  enrollment_level_overrides (Layer 3)                                       │
│  enrollment_grade_overrides (Layer 4)                                       │
│  enrollment_projections (cached results)                                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
User Interaction
      │
      ▼
┌─────────────────┐
│ Select Scenario │ ──────────────────────────────────────┐
└─────────────────┘                                       │
      │                                                   │
      ▼                                                   │
┌─────────────────┐                                       │
│ Adjust Global   │ ──────────────────────────────────────┤
│ Overrides       │                                       │
└─────────────────┘                                       │
      │                                                   │
      ▼                                                   │
┌─────────────────┐                                       │
│ Adjust Level    │ ──────────────────────────────────────┤
│ Overrides       │                                       │
└─────────────────┘                                       │
      │                                                   │
      ▼                                                   │
┌─────────────────┐                                       │
│ Adjust Grade    │ ──────────────────────────────────────┤
│ Overrides       │                                       │
└─────────────────┘                                       │
      │                                                   │
      │ (debounced, 300ms)                               │
      ▼                                                   │
┌─────────────────┐     ┌─────────────────────────────┐  │
│ AUTO-CALCULATE  │◄────│ Resolve 4-Layer Overrides   │◄─┘
│ Projection      │     └─────────────────────────────┘
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Apply Capacity  │ ── If total > configured capacity (default 1,850)
│ Constraint      │
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Display Results │ ── Real-time update
│ + Sparklines    │
└─────────────────┘
      │
      ▼ (on user action)
┌─────────────────┐
│ VALIDATE        │ ── Locks projection, cascades downstream
└─────────────────┘
```

---

## 4. Database Schema

### 4.1 New Tables

#### Table 1: `enrollment_scenarios` (Seed data - 3 rows)

```sql
CREATE TABLE enrollment_scenarios (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code VARCHAR(20) UNIQUE NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    name_fr VARCHAR(100) NOT NULL,
    description_en TEXT,
    description_fr TEXT,
    ps_entry INTEGER NOT NULL,
    entry_growth_rate NUMERIC(5,4) NOT NULL,
    default_retention NUMERIC(5,4) NOT NULL,
    terminal_retention NUMERIC(5,4) NOT NULL,
    lateral_multiplier NUMERIC(4,2) NOT NULL,
    color_code VARCHAR(7),  -- For UI (e.g., #EF4444 for worst)
    sort_order INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Seed data
INSERT INTO enrollment_scenarios (code, name_en, name_fr, description_en, description_fr,
    ps_entry, entry_growth_rate, default_retention, terminal_retention, lateral_multiplier,
    color_code, sort_order)
VALUES
    ('worst_case', 'Worst Case', 'Pire Cas',
     'Economic downturn, expat departures, competitive pressure',
     'Ralentissement économique, départs d''expatriés, pression concurrentielle',
     45, -0.02, 0.90, 0.92, 0.3, '#EF4444', 1),
    ('base', 'Base', 'Base',
     'Historical average continuation, no significant changes',
     'Continuation de la moyenne historique, pas de changements significatifs',
     65, 0.00, 0.96, 0.98, 1.0, '#3B82F6', 2),
    ('best_case', 'Best Case', 'Meilleur Cas',
     'Maximum growth, strong demand, near-capacity utilization',
     'Croissance maximale, forte demande, utilisation proche de la capacité',
     85, 0.03, 0.99, 1.00, 1.5, '#22C55E', 3);
```

#### Table 2: `enrollment_lateral_entry_defaults` (Seed data - 14 rows)

```sql
CREATE TABLE enrollment_lateral_entry_defaults (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    level_id UUID NOT NULL REFERENCES academic_levels(id),
    base_lateral_entry INTEGER NOT NULL CHECK (base_lateral_entry >= 0),
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(level_id)
);

-- Seed data (after academic_levels exist)
INSERT INTO enrollment_lateral_entry_defaults (level_id, base_lateral_entry, notes)
SELECT id,
  CASE code
    WHEN 'MS' THEN 27
    WHEN 'GS' THEN 20
    WHEN 'CP' THEN 12
    WHEN 'CE1' THEN 7
    WHEN 'CE2' THEN 6
    WHEN 'CM1' THEN 5
    WHEN 'CM2' THEN 7
    WHEN '6EME' THEN 8
    WHEN '5EME' THEN 5
    WHEN '4EME' THEN 6
    WHEN '3EME' THEN 6
    WHEN '2NDE' THEN 8
    WHEN '1ERE' THEN 6
    WHEN 'TLE' THEN 1
  END,
  'Historical average lateral entry'
FROM academic_levels
WHERE code IN (
  'MS','GS','CP','CE1','CE2','CM1','CM2',
  '6EME','5EME','4EME','3EME','2NDE','1ERE','TLE'
);
```

#### Table 3: `enrollment_projection_configs` (Per budget version)

```sql
CREATE TABLE enrollment_projection_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    version_id UUID NOT NULL REFERENCES settings_versions(id),
    scenario_id UUID NOT NULL REFERENCES enrollment_scenarios(id),
    base_year INTEGER NOT NULL,
    projection_years INTEGER NOT NULL DEFAULT 5 CHECK (projection_years BETWEEN 1 AND 10),
    school_max_capacity INTEGER NOT NULL DEFAULT 1850 CHECK (school_max_capacity > 0),
    default_class_size INTEGER NOT NULL DEFAULT 25 CHECK (default_class_size BETWEEN 15 AND 40),
    status VARCHAR(20) NOT NULL DEFAULT 'draft' CHECK (status IN ('draft', 'validated')),
    validated_at TIMESTAMPTZ,
    validated_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(version_id)
);

CREATE INDEX idx_projection_configs_version ON enrollment_projection_configs(version_id);
CREATE INDEX idx_projection_configs_status ON enrollment_projection_configs(status);
```

#### Table 4: `enrollment_global_overrides` (Layer 2)

```sql
CREATE TABLE enrollment_global_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projection_config_id UUID NOT NULL REFERENCES enrollment_projection_configs(id) ON DELETE CASCADE,
    ps_entry_adjustment INTEGER CHECK (ps_entry_adjustment BETWEEN -20 AND 20),
    retention_adjustment NUMERIC(5,4) CHECK (retention_adjustment BETWEEN -0.05 AND 0.05),
    lateral_multiplier_override NUMERIC(4,2) CHECK (lateral_multiplier_override BETWEEN 0.5 AND 1.5),
    class_size_override INTEGER CHECK (class_size_override BETWEEN 20 AND 30),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(projection_config_id)
);
```

#### Table 5: `enrollment_level_overrides` (Layer 3)

```sql
CREATE TABLE enrollment_level_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projection_config_id UUID NOT NULL REFERENCES enrollment_projection_configs(id) ON DELETE CASCADE,
    cycle_id UUID NOT NULL REFERENCES academic_cycles(id),
    class_size_ceiling INTEGER CHECK (class_size_ceiling BETWEEN 20 AND 30),
    max_divisions INTEGER CHECK (max_divisions BETWEEN 2 AND 10),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(projection_config_id, cycle_id)
);

CREATE INDEX idx_level_overrides_config ON enrollment_level_overrides(projection_config_id);
```

#### Table 6: `enrollment_grade_overrides` (Layer 4)

```sql
CREATE TABLE enrollment_grade_overrides (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projection_config_id UUID NOT NULL REFERENCES enrollment_projection_configs(id) ON DELETE CASCADE,
    level_id UUID NOT NULL REFERENCES academic_levels(id),
    retention_rate NUMERIC(5,4) CHECK (retention_rate BETWEEN 0.85 AND 1.00),
    lateral_entry INTEGER CHECK (lateral_entry BETWEEN 0 AND 50),
    max_divisions INTEGER CHECK (max_divisions BETWEEN 2 AND 8),
    class_size_ceiling INTEGER CHECK (class_size_ceiling BETWEEN 20 AND 30),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(projection_config_id, level_id)
);

CREATE INDEX idx_grade_overrides_config ON enrollment_grade_overrides(projection_config_id);
```

#### Table 7: `enrollment_projections` (Cached results)

```sql
CREATE TABLE enrollment_projections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    projection_config_id UUID NOT NULL REFERENCES enrollment_projection_configs(id) ON DELETE CASCADE,
    school_year VARCHAR(9) NOT NULL,  -- '2026/2027'
    fiscal_year INTEGER NOT NULL,
    level_id UUID NOT NULL REFERENCES academic_levels(id),

    -- Projected values
    projected_students INTEGER NOT NULL CHECK (projected_students >= 0),
    divisions INTEGER NOT NULL CHECK (divisions > 0),
    avg_class_size NUMERIC(4,1),

    -- Fiscal year proration
    fiscal_year_weighted_students NUMERIC(6,1),  -- (prev × 8/12) + (curr × 4/12)

    -- Capacity constraint info
    was_capacity_constrained BOOLEAN DEFAULT FALSE,
    original_projection INTEGER,  -- Before capacity reduction
    reduction_applied INTEGER DEFAULT 0,
    reduction_percentage NUMERIC(5,2),

    -- Metadata
    calculation_timestamp TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(projection_config_id, school_year, level_id)
);

CREATE INDEX idx_projections_config ON enrollment_projections(projection_config_id);
CREATE INDEX idx_projections_fiscal_year ON enrollment_projections(fiscal_year);
```

### 4.2 Migration File Structure

```
backend/alembic/versions/
└── 20251212_0001_enrollment_projection_tables.py
```

### 4.3 Row Level Security (RLS)

Apply RLS following the role/version patterns in `docs/database/sql/rls_policies.sql`.

- **Reference tables** (`enrollment_scenarios`, `enrollment_lateral_entry_defaults`): readable by all authenticated users; admin‑only writes.
- **Versioned tables** (`enrollment_projection_configs`, overrides, `enrollment_projections`): access is tied to the linked `settings_versions` status.

**Example policies**

```sql
-- Configs are versioned directly
ALTER TABLE efir_budget.enrollment_projection_configs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "enrollment_projection_configs_admin_all"
  ON efir_budget.enrollment_projection_configs
  FOR ALL TO authenticated
  USING (efir_budget.current_user_role() = 'admin')
  WITH CHECK (efir_budget.current_user_role() = 'admin');

CREATE POLICY "enrollment_projection_configs_manager_working"
  ON efir_budget.enrollment_projection_configs
  FOR ALL TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1 FROM efir_budget.settings_versions v
      WHERE v.id = version_id
      AND bv.status = 'working'
      AND bv.deleted_at IS NULL
    )
  )
  WITH CHECK (same as USING);

CREATE POLICY "enrollment_projection_configs_select"
  ON efir_budget.enrollment_projection_configs
  FOR SELECT TO authenticated
  USING (
    efir_budget.current_user_role() IN ('admin', 'manager')
    OR (
      efir_budget.current_user_role() = 'viewer'
      AND EXISTS (
        SELECT 1 FROM efir_budget.settings_versions v
        WHERE v.id = version_id
        AND bv.status = 'approved'
        AND bv.deleted_at IS NULL
      )
    )
  );

-- Child tables reference projection_config_id, so policies join through configs → versions
ALTER TABLE efir_budget.enrollment_grade_overrides ENABLE ROW LEVEL SECURITY;
CREATE POLICY "enrollment_grade_overrides_manager_working"
  ON efir_budget.enrollment_grade_overrides
  FOR ALL TO authenticated
  USING (
    efir_budget.current_user_role() = 'manager'
    AND EXISTS (
      SELECT 1
      FROM efir_budget.enrollment_projection_configs pc
      JOIN efir_budget.settings_versions v ON v.id = pc.version_id
      WHERE pc.id = projection_config_id
      AND bv.status = 'working'
      AND bv.deleted_at IS NULL
    )
  )
  WITH CHECK (same as USING);
-- Replicate equivalent admin/select policies for all projection child tables.
```

---

## 5. Backend Implementation

### 5.1 File Structure

```
backend/app/
├── engine/
│   └── enrollment/
│       ├── __init__.py
│       ├── projection_engine.py      # Core calculation (pure functions)
│       ├── projection_models.py      # Pydantic models for projection
│       └── fiscal_year_proration.py  # Fiscal year calculations
├── models/
│   └── enrollment_projection.py      # SQLAlchemy models
├── schemas/
│   └── enrollment_projection.py      # API request/response schemas
├── services/
│   └── enrollment_projection_service.py
└── api/
    └── v1/
        └── enrollment_projection.py  # API routes
```

### 5.2 Core Calculation Engine

**File: `backend/app/engine/enrollment/projection_engine.py`**

```python
"""
Enrollment Projection Engine

Pure functions for calculating enrollment projections using
Retention + Lateral Entry model with 4-layer override architecture.
"""

from __future__ import annotations

from decimal import Decimal
from typing import TypedDict

from pydantic import BaseModel, Field


# Grade sequence for cohort flow
GRADE_SEQUENCE: list[str] = [
    'PS', 'MS', 'GS',  # Maternelle
    'CP', 'CE1', 'CE2', 'CM1', 'CM2',  # Élémentaire
    '6EME', '5EME', '4EME', '3EME',  # Collège
    '2NDE', '1ERE', 'TLE'  # Lycée
]

GRADE_TO_CYCLE: dict[str, str] = {
    'PS': 'MAT', 'MS': 'MAT', 'GS': 'MAT',
    'CP': 'ELEM', 'CE1': 'ELEM', 'CE2': 'ELEM', 'CM1': 'ELEM', 'CM2': 'ELEM',
    '6EME': 'COLL', '5EME': 'COLL', '4EME': 'COLL', '3EME': 'COLL',
    '2NDE': 'LYC', '1ERE': 'LYC', 'TLE': 'LYC'
}


class ScenarioParams(BaseModel):
    """Scenario default parameters."""
    ps_entry: int
    entry_growth_rate: Decimal
    default_retention: Decimal
    terminal_retention: Decimal
    lateral_multiplier: Decimal


class GlobalOverrides(BaseModel):
    """Layer 2: Global overrides."""
    ps_entry_adjustment: int | None = None
    retention_adjustment: Decimal | None = None
    lateral_multiplier_override: Decimal | None = None
    class_size_override: int | None = None


class LevelOverride(BaseModel):
    """Layer 3: Level (cycle) overrides."""
    class_size_ceiling: int | None = None
    max_divisions: int | None = None


class GradeOverride(BaseModel):
    """Layer 4: Grade overrides (highest priority)."""
    retention_rate: Decimal | None = None
    lateral_entry: int | None = None
    max_divisions: int | None = None
    class_size_ceiling: int | None = None


class ProjectionInput(BaseModel):
    """Input for projection calculation."""
    base_year_enrollment: dict[str, int]  # grade_code -> student count
    scenario: ScenarioParams
    global_overrides: GlobalOverrides | None = None
    level_overrides: dict[str, LevelOverride] | None = None  # cycle_code -> override
    grade_overrides: dict[str, GradeOverride] | None = None  # grade_code -> override
    base_lateral_entry: dict[str, int]  # grade_code -> lateral entry count
    school_max_capacity: int = Field(default=1850, ge=1)
    default_class_size: int = Field(default=25, ge=15, le=40)
    target_year: int
    base_year: int


class GradeProjection(BaseModel):
    """Projection result for a single grade."""
    grade_code: str
    cycle_code: str
    projected_students: int
    divisions: int
    avg_class_size: Decimal
    original_projection: int | None = None  # Before capacity reduction
    reduction_applied: int = 0
    reduction_percentage: Decimal | None = None


class ProjectionResult(BaseModel):
    """Complete projection result for one year."""
    school_year: str  # '2026/2027'
    fiscal_year: int
    grades: list[GradeProjection]
    total_students: int
    utilization_rate: Decimal
    was_capacity_constrained: bool
    total_reduction_applied: int = 0


def validate_projection_input(input: ProjectionInput) -> list[str]:
    """
    Validate projection input for engine safety.

    Returns a list of human-readable errors (empty if valid).
    Service layer should treat any errors as blocking.
    """
    errors: list[str] = []
    if not input.base_year_enrollment:
        errors.append("base_year_enrollment is empty")
    if input.school_max_capacity <= 0:
        errors.append("school_max_capacity must be positive")
    if any(v < 0 for v in input.base_year_enrollment.values()):
        errors.append("base_year_enrollment contains negative counts")

    unknown_grades = set(input.base_year_enrollment) - set(GRADE_SEQUENCE)
    if unknown_grades:
        errors.append(f"Unknown grade codes in baseline: {sorted(unknown_grades)}")

    unknown_lateral = set(input.base_lateral_entry) - set(GRADE_SEQUENCE)
    if unknown_lateral:
        errors.append(f"Unknown grade codes in base_lateral_entry: {sorted(unknown_lateral)}")

    return errors


def get_effective_retention(
    grade: str,
    scenario: ScenarioParams,
    global_overrides: GlobalOverrides | None,
    grade_overrides: dict[str, GradeOverride] | None,
) -> Decimal:
    """
    Resolve retention rate using 4-layer override priority.

    Priority: Grade Override > Global Override > Scenario Default
    """
    # Layer 4: Grade override (highest priority)
    if grade_overrides and grade in grade_overrides:
        if grade_overrides[grade].retention_rate is not None:
            return grade_overrides[grade].retention_rate

    # Layer 2: Global override (adjustment to scenario default)
    base_retention = (
        scenario.terminal_retention if grade == 'TLE'
        else scenario.default_retention
    )

    if global_overrides and global_overrides.retention_adjustment is not None:
        return base_retention + global_overrides.retention_adjustment

    # Layer 1: Scenario default
    return base_retention


def get_effective_lateral_multiplier(
    grade: str,
    scenario: ScenarioParams,
    global_overrides: GlobalOverrides | None,
) -> Decimal:
    """
    Resolve lateral multiplier using override priority.
    """
    if global_overrides and global_overrides.lateral_multiplier_override is not None:
        return global_overrides.lateral_multiplier_override
    return scenario.lateral_multiplier


def get_effective_class_size(
    grade: str,
    default_class_size: int,
    global_overrides: GlobalOverrides | None,
    level_overrides: dict[str, LevelOverride] | None,
    grade_overrides: dict[str, GradeOverride] | None,
) -> int:
    """
    Resolve class size ceiling using 4-layer priority.
    """
    cycle = GRADE_TO_CYCLE.get(grade, '')

    # Layer 4: Grade override
    if grade_overrides and grade in grade_overrides:
        if grade_overrides[grade].class_size_ceiling is not None:
            return grade_overrides[grade].class_size_ceiling

    # Layer 3: Level override
    if level_overrides and cycle in level_overrides:
        if level_overrides[cycle].class_size_ceiling is not None:
            return level_overrides[cycle].class_size_ceiling

    # Layer 2: Global override
    if global_overrides and global_overrides.class_size_override is not None:
        return global_overrides.class_size_override

    # Default
    return default_class_size


def get_effective_max_divisions(
    grade: str,
    level_overrides: dict[str, LevelOverride] | None,
    grade_overrides: dict[str, GradeOverride] | None,
    default_max: int = 8,
) -> int:
    """
    Resolve max divisions using 4-layer priority.
    """
    cycle = GRADE_TO_CYCLE.get(grade, '')

    # Layer 4: Grade override
    if grade_overrides and grade in grade_overrides:
        if grade_overrides[grade].max_divisions is not None:
            return grade_overrides[grade].max_divisions

    # Layer 3: Level override
    if level_overrides and cycle in level_overrides:
        if level_overrides[cycle].max_divisions is not None:
            return level_overrides[cycle].max_divisions

    return default_max


def get_effective_lateral_entry(
    grade: str,
    base_lateral_entry: dict[str, int],
    lateral_multiplier: Decimal,
    grade_overrides: dict[str, GradeOverride] | None,
) -> int:
    """
    Calculate effective lateral entry count.
    """
    # Layer 4: Grade override (absolute value)
    if grade_overrides and grade in grade_overrides:
        if grade_overrides[grade].lateral_entry is not None:
            return grade_overrides[grade].lateral_entry

    # Apply multiplier to base
    base = base_lateral_entry.get(grade, 0)
    return int(base * float(lateral_multiplier))


def calculate_divisions(students: int, class_size: int, max_divisions: int) -> int:
    """Calculate number of divisions (classes) needed."""
    if students == 0:
        return 0
    divisions = -(-students // class_size)  # Ceiling division
    return min(divisions, max_divisions)


def project_single_year(input: ProjectionInput) -> dict[str, int]:
    """
    Project enrollment for a single target year.

    Assumes input.base_year_enrollment represents the immediately
    preceding school year. For multi‑year projections, call via
    project_multi_year(), which iteratively updates the base.

    Returns: dict[grade_code, projected_students]
    """
    result: dict[str, int] = {}
    years_diff = input.target_year - input.base_year

    # PS entry calculation
    ps_entry = input.scenario.ps_entry
    if input.global_overrides and input.global_overrides.ps_entry_adjustment:
        ps_entry += input.global_overrides.ps_entry_adjustment

    growth = float(input.scenario.entry_growth_rate)
    result['PS'] = round(ps_entry * ((1 + growth) ** years_diff))

    # Cohort progression for other grades
    for i in range(1, len(GRADE_SEQUENCE)):
        grade = GRADE_SEQUENCE[i]
        prev_grade = GRADE_SEQUENCE[i - 1]

        # Get effective parameters
        retention = get_effective_retention(
            grade, input.scenario, input.global_overrides, input.grade_overrides
        )

        lateral_mult = get_effective_lateral_multiplier(
            grade, input.scenario, input.global_overrides
        )

        lateral = get_effective_lateral_entry(
            grade, input.base_lateral_entry, lateral_mult, input.grade_overrides
        )

        # Calculate projection
        prev_enrollment = input.base_year_enrollment.get(prev_grade, 0)
        projected = int(prev_enrollment * float(retention)) + lateral

        # Apply grade capacity constraint
        max_div = get_effective_max_divisions(
            grade, input.level_overrides, input.grade_overrides
        )
        class_size = get_effective_class_size(
            grade, input.default_class_size,
            input.global_overrides, input.level_overrides, input.grade_overrides
        )
        grade_capacity = max_div * class_size

        result[grade] = min(projected, grade_capacity)

    return result


def apply_capacity_constraint(
    enrollment_by_grade: dict[str, int],
    max_capacity: int,
) -> tuple[dict[str, int], dict[str, int], bool]:
    """
    Apply school-wide capacity constraint with proportional reduction.

    Returns: (adjusted_enrollment, reduction_per_grade, was_constrained)
    """
    total = sum(enrollment_by_grade.values())

    if total <= max_capacity:
        return enrollment_by_grade, {g: 0 for g in enrollment_by_grade}, False

    reduction_factor = max_capacity / total
    adjusted: dict[str, int] = {}
    reductions: dict[str, int] = {}

    for grade, students in enrollment_by_grade.items():
        adjusted_count = round(students * reduction_factor)
        adjusted[grade] = adjusted_count
        reductions[grade] = students - adjusted_count

    return adjusted, reductions, True


def project_enrollment(input: ProjectionInput) -> ProjectionResult:
    """
    Complete projection with capacity constraint and full details.
    """
    # Calculate raw projection
    raw_projection = project_single_year(input)

    # Apply capacity constraint
    adjusted, reductions, was_constrained = apply_capacity_constraint(
        raw_projection, input.school_max_capacity
    )

    # Build grade-level results
    grades: list[GradeProjection] = []

    for grade in GRADE_SEQUENCE:
        students = adjusted.get(grade, 0)
        class_size = get_effective_class_size(
            grade, input.default_class_size,
            input.global_overrides, input.level_overrides, input.grade_overrides
        )
        max_div = get_effective_max_divisions(
            grade, input.level_overrides, input.grade_overrides
        )

        divisions = calculate_divisions(students, class_size, max_div)
        avg_size = Decimal(students / divisions) if divisions > 0 else Decimal(0)

        reduction = reductions.get(grade, 0)
        original = raw_projection.get(grade) if was_constrained else None

        grades.append(GradeProjection(
            grade_code=grade,
            cycle_code=GRADE_TO_CYCLE[grade],
            projected_students=students,
            divisions=divisions,
            avg_class_size=round(avg_size, 1),
            original_projection=original,
            reduction_applied=reduction,
            reduction_percentage=(
                Decimal(reduction / original * 100) if original and original > 0
                else None
            ),
        ))

    total = sum(adjusted.values())
    school_year = f"{input.target_year}/{input.target_year + 1}"

    return ProjectionResult(
        school_year=school_year,
        fiscal_year=input.target_year,
        grades=grades,
        total_students=total,
        utilization_rate=Decimal(total / input.school_max_capacity * 100).quantize(Decimal('0.1')),
        was_capacity_constrained=was_constrained,
        total_reduction_applied=sum(reductions.values()),
    )


def project_multi_year(
    input: ProjectionInput,
    years: int = 5,
) -> list[ProjectionResult]:
    """
    Project enrollment for multiple years.

    Uses iterative cohort progression - each year's output
    becomes the base for the next year.
    """
    results: list[ProjectionResult] = []
    current_enrollment = input.base_year_enrollment.copy()

    for year_offset in range(1, years + 1):
        year_input = input.model_copy()
        year_input.base_year_enrollment = current_enrollment
        year_input.target_year = input.base_year + year_offset
        year_input.base_year = input.base_year + year_offset - 1

        result = project_enrollment(year_input)
        results.append(result)

        # Update current enrollment for next iteration
        current_enrollment = {
            g.grade_code: g.projected_students for g in result.grades
        }

    return results
```

### 5.3 Fiscal Year Proration

**File: `backend/app/engine/enrollment/fiscal_year_proration.py`**

```python
"""
Fiscal Year Proration Calculator

Handles the mismatch between school years (Sep-Aug) and fiscal years (Jan-Dec).
"""

from decimal import Decimal
from typing import TypedDict


class FiscalYearProration(TypedDict):
    """Result of fiscal year proration calculation."""
    fiscal_year: int
    previous_school_year: str  # '2025/2026'
    current_school_year: str   # '2026/2027'
    previous_months: int       # 8 (Jan-Aug)
    current_months: int        # 4 (Sep-Dec)
    weighted_enrollment: Decimal


def get_school_years_for_fiscal_year(fiscal_year: int) -> tuple[str, str]:
    """
    Get the two school years that overlap with a fiscal year.

    Example: Fiscal Year 2026
    - Jan-Aug 2026: School Year 2025/2026
    - Sep-Dec 2026: School Year 2026/2027

    Returns: (previous_school_year, current_school_year)
    """
    previous_school_year = f"{fiscal_year - 1}/{fiscal_year}"
    current_school_year = f"{fiscal_year}/{fiscal_year + 1}"
    return previous_school_year, current_school_year


def calculate_fiscal_year_weighted_enrollment(
    previous_school_year_enrollment: int,
    current_school_year_enrollment: int,
    previous_months: int = 8,  # Jan-Aug
    current_months: int = 4,   # Sep-Dec
) -> Decimal:
    """
    Calculate weighted average enrollment for fiscal year reporting.

    Formula: (prev × 8/12) + (curr × 4/12)

    Args:
        previous_school_year_enrollment: Students in ending school year
        current_school_year_enrollment: Students in starting school year
        previous_months: Months of previous school year in fiscal year (default 8)
        current_months: Months of current school year in fiscal year (default 4)

    Returns:
        Weighted average enrollment for the fiscal year
    """
    total_months = previous_months + current_months
    weighted = (
        (previous_school_year_enrollment * previous_months / total_months) +
        (current_school_year_enrollment * current_months / total_months)
    )
    return Decimal(str(weighted)).quantize(Decimal('0.1'))


def calculate_proration_by_grade(
    previous_enrollment: dict[str, int],
    current_enrollment: dict[str, int],
    fiscal_year: int,
) -> dict[str, FiscalYearProration]:
    """
    Calculate fiscal year proration for all grades.

    Args:
        previous_enrollment: dict[grade_code, students] for ending school year
        current_enrollment: dict[grade_code, students] for starting school year
        fiscal_year: The fiscal year being calculated

    Returns:
        dict[grade_code, FiscalYearProration]
    """
    prev_sy, curr_sy = get_school_years_for_fiscal_year(fiscal_year)
    results: dict[str, FiscalYearProration] = {}

    all_grades = set(previous_enrollment.keys()) | set(current_enrollment.keys())

    for grade in all_grades:
        prev_count = previous_enrollment.get(grade, 0)
        curr_count = current_enrollment.get(grade, 0)

        results[grade] = FiscalYearProration(
            fiscal_year=fiscal_year,
            previous_school_year=prev_sy,
            current_school_year=curr_sy,
            previous_months=8,
            current_months=4,
            weighted_enrollment=calculate_fiscal_year_weighted_enrollment(
                prev_count, curr_count
            ),
        )

    return results
```

### 5.4 API Endpoints

**File: `backend/app/api/v1/enrollment_projection.py`**

```python
"""
Enrollment Projection API Routes

Endpoints for managing enrollment projections with 4-layer override architecture.
"""

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_user
from app.schemas.enrollment_projection import (
    ScenarioListResponse,
    ProjectionConfigCreate,
    ProjectionConfigResponse,
    GlobalOverridesUpdate,
    LevelOverridesUpdate,
    GradeOverridesUpdate,
    ProjectionResultsResponse,
    ValidationRequest,
    ValidationResponse,
)
from app.services.enrollment_projection_service import EnrollmentProjectionService


router = APIRouter(prefix="/enrollment-projection", tags=["Enrollment Projection"])


@router.get("/scenarios", response_model=ScenarioListResponse)
async def get_scenarios(
    db: AsyncSession = Depends(get_db),
):
    """
    Get all available enrollment scenarios (Worst, Base, Best).
    """
    service = EnrollmentProjectionService(db)
    scenarios = await service.get_all_scenarios()
    return ScenarioListResponse(scenarios=scenarios)


@router.get("/{version_id}/config", response_model=ProjectionConfigResponse)
async def get_projection_config(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get projection configuration for a budget version.
    Creates default config if none exists.
    """
    service = EnrollmentProjectionService(db)
    config = await service.get_or_create_config(version_id)
    return config


@router.put("/{version_id}/config", response_model=ProjectionConfigResponse)
async def update_projection_config(
    version_id: UUID,
    config: ProjectionConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update projection configuration (scenario selection, base year, etc.).
    Triggers auto-recalculation.
    """
    service = EnrollmentProjectionService(db)
    updated = await service.update_config(version_id, config, current_user.id)
    return updated


@router.put("/{version_id}/global-overrides", response_model=ProjectionConfigResponse)
async def update_global_overrides(
    version_id: UUID,
    overrides: GlobalOverridesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update Layer 2: Global overrides.
    Triggers auto-recalculation.
    """
    service = EnrollmentProjectionService(db)
    updated = await service.update_global_overrides(version_id, overrides)
    return updated


@router.put("/{version_id}/level-overrides", response_model=ProjectionConfigResponse)
async def update_level_overrides(
    version_id: UUID,
    overrides: LevelOverridesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update Layer 3: Level (cycle) overrides.
    Triggers auto-recalculation.
    """
    service = EnrollmentProjectionService(db)
    updated = await service.update_level_overrides(version_id, overrides)
    return updated


@router.put("/{version_id}/grade-overrides", response_model=ProjectionConfigResponse)
async def update_grade_overrides(
    version_id: UUID,
    overrides: GradeOverridesUpdate,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Update Layer 4: Grade overrides (highest priority).
    Triggers auto-recalculation.
    """
    service = EnrollmentProjectionService(db)
    updated = await service.update_grade_overrides(version_id, overrides)
    return updated


@router.get("/{version_id}/results", response_model=ProjectionResultsResponse)
async def get_projection_results(
    version_id: UUID,
    include_fiscal_proration: bool = True,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Get calculated projection results for all years.
    Includes fiscal year proration if requested.
    """
    service = EnrollmentProjectionService(db)
    results = await service.get_projection_results(
        version_id, include_fiscal_proration
    )
    return results


@router.post("/{version_id}/calculate", response_model=ProjectionResultsResponse)
async def calculate_projection(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Force recalculation of projections.
    Normally called automatically when parameters change.
    """
    service = EnrollmentProjectionService(db)
    results = await service.calculate_and_save(version_id)
    return results


@router.post("/{version_id}/validate", response_model=ValidationResponse)
async def validate_projection(
    version_id: UUID,
    request: ValidationRequest,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Validate projection and cascade to downstream modules.

    This action:
    1. Locks the projection (status = 'validated')
    2. Populates enrollment_plans table
    3. Triggers class structure calculation
    4. Enables DHG and revenue calculations
    """
    service = EnrollmentProjectionService(db)
    result = await service.validate_and_cascade(
        version_id, current_user.id, request.confirmation
    )
    return result


@router.post("/{version_id}/unvalidate", response_model=ProjectionConfigResponse)
async def unvalidate_projection(
    version_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """
    Unvalidate projection to allow modifications.
    Requires appropriate permissions.
    """
    service = EnrollmentProjectionService(db)
    result = await service.unvalidate(version_id, current_user.id)
    return result
```

---

## 6. Frontend Implementation

### 6.1 File Structure

```
frontend/src/
├── routes/
│   └── _authenticated/
│       └── enrollment/
│           └── planning.tsx              # Main enrollment planning (projection + distribution)
├── components/
│   └── enrollment/
│       ├── ScenarioSelector.tsx          # 3 scenario cards
│       ├── GlobalOverridesPanel.tsx      # Sliders for Layer 2
│       ├── LevelOverridesPanel.tsx       # Per-cycle settings
│       ├── GradeOverridesGrid.tsx        # AG Grid for Layer 4
│       ├── ProjectionResultsGrid.tsx     # 5-year results with sparklines
│       ├── NationalityDistributionPanel.tsx  # % by level (French/Saudi/Other)
│       ├── CapacityWarningBanner.tsx     # Over-capacity alert
│       ├── ReductionBreakdownModal.tsx   # Per-class reduction details
│       ├── FiscalYearProrationTable.tsx  # Weighted enrollment view
│       └── ValidationConfirmDialog.tsx   # Cascade confirmation
├── services/
│   └── enrollmentProjection.ts           # API service
├── hooks/
│   └── api/
│       └── useEnrollmentProjection.ts    # React Query hooks
└── types/
    └── enrollmentProjection.ts           # TypeScript types
```

**Note on Nationality Distribution Wiring**:
- `NationalityDistributionPanel` reuses existing Module 7 distribution endpoints and hooks (`useEnrollmentWithDistribution`, `useBulkUpsertDistributions`) rather than introducing a parallel API.
- Any distribution change triggers projection recalculation and downstream cache invalidation.

**Note on Historical Data for Sparklines**:
- `historical_data?: number[]` in `GradeProjection` is populated by the backend service.
- Preferred source: query the last 5 **validated** budget versions for the organization and aggregate `enrollment_plans` (or `enrollment_projections` once available) by grade/level.
- If fewer than 5 historical points exist, return available points and let the UI render a shorter sparkline.

### 6.2 TypeScript Types

**Schema alignment reminder**: After implementing or changing backend projection schemas, regenerate frontend types from OpenAPI to prevent drift:
```bash
cd frontend && pnpm generate:types
```

**File: `frontend/src/types/enrollmentProjection.ts`**

```typescript
// Scenarios
export interface EnrollmentScenario {
  id: string;
  code: 'worst_case' | 'base' | 'best_case';
  name_en: string;
  name_fr: string;
  description_en: string;
  description_fr: string;
  ps_entry: number;
  entry_growth_rate: number;
  default_retention: number;
  terminal_retention: number;
  lateral_multiplier: number;
  color_code: string;
  sort_order: number;
}

// Configuration
export interface ProjectionConfig {
  id: string;
  version_id: string;
  scenario_id: string;
  scenario: EnrollmentScenario;
  base_year: number;
  projection_years: number;
  school_max_capacity: number;
  default_class_size: number;
  status: 'draft' | 'validated';
  validated_at: string | null;
  validated_by: string | null;
  global_overrides: GlobalOverrides | null;
  level_overrides: LevelOverride[];
  grade_overrides: GradeOverride[];
}

// Layer 2: Global Overrides
export interface GlobalOverrides {
  ps_entry_adjustment: number | null;
  retention_adjustment: number | null;
  lateral_multiplier_override: number | null;
  class_size_override: number | null;
}

// Layer 3: Level Overrides
export interface LevelOverride {
  cycle_id: string;
  cycle_code: string;
  cycle_name: string;
  class_size_ceiling: number | null;
  max_divisions: number | null;
}

// Layer 4: Grade Overrides
export interface GradeOverride {
  level_id: string;
  level_code: string;
  level_name: string;
  retention_rate: number | null;
  lateral_entry: number | null;
  max_divisions: number | null;
  class_size_ceiling: number | null;
}

// Projection Results
export interface GradeProjection {
  grade_code: string;
  cycle_code: string;
  projected_students: number;
  divisions: number;
  avg_class_size: number;
  original_projection: number | null;
  reduction_applied: number;
  reduction_percentage: number | null;
  // For sparkline
  historical_data?: number[];  // Last 5 years
}

export interface YearProjection {
  school_year: string;
  fiscal_year: number;
  grades: GradeProjection[];
  total_students: number;
  utilization_rate: number;
  was_capacity_constrained: boolean;
  total_reduction_applied: number;
  // Fiscal year proration
  fiscal_weighted_enrollment?: Record<string, number>;
}

export interface ProjectionResults {
  config: ProjectionConfig;
  projections: YearProjection[];
  summary: {
    base_year_total: number;
    final_year_total: number;
    cagr: number;
    years_at_capacity: number;
  };
}

// Slider configurations
export interface SliderConfig {
  min: number;
  max: number;
  step: number;
  default: number;
}

export const SLIDER_CONFIGS = {
  psEntryAdjustment: { min: -20, max: 20, step: 5, default: 0 },
  retentionAdjustment: { min: -0.05, max: 0.05, step: 0.01, default: 0 },
  lateralMultiplier: { min: 0.5, max: 1.5, step: 0.1, default: 1.0 },
  classSize: { min: 20, max: 30, step: 1, default: 25 },
  retention: { min: 0.85, max: 1.00, step: 0.01, default: 0.96 },
  lateralEntry: { min: 0, max: 50, step: 1, default: 0 },
  maxDivisions: { min: 2, max: 8, step: 1, default: 6 },
} as const;
```

### 6.3 API Service

**File: `frontend/src/services/enrollmentProjection.ts`**

```typescript
import { api } from './api';
import type {
  EnrollmentScenario,
  ProjectionConfig,
  GlobalOverrides,
  LevelOverride,
  GradeOverride,
  ProjectionResults,
} from '@/types/enrollmentProjection';

const BASE_PATH = '/planning/enrollment-projection';

export const enrollmentProjectionService = {
  // Get scenarios
  getScenarios: async (): Promise<EnrollmentScenario[]> => {
    const response = await api.get(`${BASE_PATH}/scenarios`);
    return response.data.scenarios;
  },

  // Get/create config
  getConfig: async (versionId: string): Promise<ProjectionConfig> => {
    const response = await api.get(`${BASE_PATH}/${versionId}/config`);
    return response.data;
  },

  // Update config (scenario, base year, etc.)
  updateConfig: async (
    versionId: string,
    config: Partial<ProjectionConfig>
  ): Promise<ProjectionConfig> => {
    const response = await api.put(`${BASE_PATH}/${versionId}/config`, config);
    return response.data;
  },

  // Update global overrides
  updateGlobalOverrides: async (
    versionId: string,
    overrides: GlobalOverrides
  ): Promise<ProjectionConfig> => {
    const response = await api.put(
      `${BASE_PATH}/${versionId}/global-overrides`,
      overrides
    );
    return response.data;
  },

  // Update level overrides
  updateLevelOverrides: async (
    versionId: string,
    overrides: LevelOverride[]
  ): Promise<ProjectionConfig> => {
    const response = await api.put(
      `${BASE_PATH}/${versionId}/level-overrides`,
      { overrides }
    );
    return response.data;
  },

  // Update grade overrides
  updateGradeOverrides: async (
    versionId: string,
    overrides: GradeOverride[]
  ): Promise<ProjectionConfig> => {
    const response = await api.put(
      `${BASE_PATH}/${versionId}/grade-overrides`,
      { overrides }
    );
    return response.data;
  },

  // Get projection results
  getResults: async (
    versionId: string,
    includeFiscalProration = true
  ): Promise<ProjectionResults> => {
    const response = await api.get(`${BASE_PATH}/${versionId}/results`, {
      params: { include_fiscal_proration: includeFiscalProration },
    });
    return response.data;
  },

  // Force recalculation
  calculate: async (versionId: string): Promise<ProjectionResults> => {
    const response = await api.post(`${BASE_PATH}/${versionId}/calculate`);
    return response.data;
  },

  // Validate and cascade
  validate: async (
    versionId: string,
    confirmation: boolean
  ): Promise<{ success: boolean; downstream_updated: string[] }> => {
    const response = await api.post(`${BASE_PATH}/${versionId}/validate`, {
      confirmation,
    });
    return response.data;
  },

  // Unvalidate
  unvalidate: async (versionId: string): Promise<ProjectionConfig> => {
    const response = await api.post(`${BASE_PATH}/${versionId}/unvalidate`);
    return response.data;
  },
};
```

### 6.4 React Query Hooks

**File: `frontend/src/hooks/api/useEnrollmentProjection.ts`**

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { enrollmentProjectionService } from '@/services/enrollmentProjection';
import { useBudgetVersion } from '@/contexts/BudgetVersionProvider';
import { useDebouncedCallback } from 'use-debounce';

// Query keys
export const projectionKeys = {
  all: ['enrollment-projection'] as const,
  scenarios: () => [...projectionKeys.all, 'scenarios'] as const,
  config: (versionId: string) => [...projectionKeys.all, 'config', versionId] as const,
  results: (versionId: string) => [...projectionKeys.all, 'results', versionId] as const,
};

// Scenarios (cached long-term)
export function useEnrollmentScenarios() {
  return useQuery({
    queryKey: projectionKeys.scenarios(),
    queryFn: enrollmentProjectionService.getScenarios,
    staleTime: Infinity, // Never refetch - scenarios don't change
  });
}

// Config
export function useProjectionConfig() {
  const { selectedVersion } = useBudgetVersion();
  const versionId = selectedVersion?.id;

  return useQuery({
    queryKey: projectionKeys.config(versionId!),
    queryFn: () => enrollmentProjectionService.getConfig(versionId!),
    enabled: !!versionId,
  });
}

// Results
export function useProjectionResults() {
  const { selectedVersion } = useBudgetVersion();
  const versionId = selectedVersion?.id;

  return useQuery({
    queryKey: projectionKeys.results(versionId!),
    queryFn: () => enrollmentProjectionService.getResults(versionId!),
    enabled: !!versionId,
  });
}

// Mutations with auto-refetch
export function useUpdateConfig() {
  const queryClient = useQueryClient();
  const { selectedVersion } = useBudgetVersion();
  const versionId = selectedVersion?.id;

  return useMutation({
    mutationFn: (config: Parameters<typeof enrollmentProjectionService.updateConfig>[1]) =>
      enrollmentProjectionService.updateConfig(versionId!, config),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(versionId!) });
      queryClient.invalidateQueries({ queryKey: projectionKeys.results(versionId!) });
    },
  });
}

export function useUpdateGlobalOverrides() {
  const queryClient = useQueryClient();
  const { selectedVersion } = useBudgetVersion();
  const versionId = selectedVersion?.id;

  const mutation = useMutation({
    mutationFn: (overrides: Parameters<typeof enrollmentProjectionService.updateGlobalOverrides>[1]) =>
      enrollmentProjectionService.updateGlobalOverrides(versionId!, overrides),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(versionId!) });
      queryClient.invalidateQueries({ queryKey: projectionKeys.results(versionId!) });
    },
  });

  // Debounced version for sliders
  const debouncedMutate = useDebouncedCallback(mutation.mutate, 300);

  return { ...mutation, debouncedMutate };
}

export function useUpdateLevelOverrides() {
  const queryClient = useQueryClient();
  const { selectedVersion } = useBudgetVersion();
  const versionId = selectedVersion?.id;

  const mutation = useMutation({
    mutationFn: (overrides: Parameters<typeof enrollmentProjectionService.updateLevelOverrides>[1]) =>
      enrollmentProjectionService.updateLevelOverrides(versionId!, overrides),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(versionId!) });
      queryClient.invalidateQueries({ queryKey: projectionKeys.results(versionId!) });
    },
  });

  const debouncedMutate = useDebouncedCallback(mutation.mutate, 300);

  return { ...mutation, debouncedMutate };
}

export function useUpdateGradeOverrides() {
  const queryClient = useQueryClient();
  const { selectedVersion } = useBudgetVersion();
  const versionId = selectedVersion?.id;

  const mutation = useMutation({
    mutationFn: (overrides: Parameters<typeof enrollmentProjectionService.updateGradeOverrides>[1]) =>
      enrollmentProjectionService.updateGradeOverrides(versionId!, overrides),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(versionId!) });
      queryClient.invalidateQueries({ queryKey: projectionKeys.results(versionId!) });
    },
  });

  const debouncedMutate = useDebouncedCallback(mutation.mutate, 300);

  return { ...mutation, debouncedMutate };
}

export function useValidateProjection() {
  const queryClient = useQueryClient();
  const { selectedVersion } = useBudgetVersion();
  const versionId = selectedVersion?.id;

  return useMutation({
    mutationFn: (confirmation: boolean) =>
      enrollmentProjectionService.validate(versionId!, confirmation),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectionKeys.config(versionId!) });
      // Also invalidate downstream queries
      queryClient.invalidateQueries({ queryKey: ['enrollment'] });
      queryClient.invalidateQueries({ queryKey: ['class-structure'] });
    },
  });
}
```

**Debounce and UX refinement (recommended)**:
- Use optimistic updates (`queryClient.setQueryData`) so slider/grid changes update UI immediately.
- Cancel in‑flight recalculation requests when a new debounced mutation fires to avoid stale results flashing.
- Keep debounced window at ~300ms; adjust only if API load proves high.

---

## 7. UI/UX Design

### 7.1 Personas & Planning Steps

**Primary Personas**
1. **Enrollment/Budget Planner (power user)** — builds the draft projection, adjusts assumptions, and owns validation.
2. **Finance Manager (consumer)** — reviews fiscal‑year weighted totals and nationality split for revenue accuracy.
3. **School Leadership (approver)** — checks scenario reasonableness, capacity risk, and authorizes cascade.

**Enrollment Planning Steps (logic)**
1. **Context & baseline**: user lands on `/enrollment/planning` and confirms budget version + base year snapshot. Baseline class size is ~25 per class (from Module 2 `class_size_params.target_class_size`) unless overridden; small cohorts may require later adjustment to avoid opening partial classes.
2. **Select scenario** (Worst/Base/Best) to seed defaults.
3. **Adjust global assumptions (optional)**: PS entry adjustment, retention adjustment, lateral multiplier, default class size, and **max capacity** (default 1,850, editable).
4. **Adjust by cycle (optional)**: per‑cycle class‑size ceilings and max divisions to reflect facility or staffing constraints.
5. **Adjust by grade (optional)**: per‑grade retention, lateral entry, max divisions, and class‑size ceilings.
6. **Review results & iterate**: multi‑year projection table + charts, capacity banner, and per‑grade feasibility. Loop back to steps 2–5 until satisfied.
7. **Set nationality distribution by level**: accept defaults (30% French / 2% Saudi / 68% Other) or edit per level. UI enforces sums = 100% and previews computed counts.
8. **Validate & cascade**: locks config; writes `nationality_distributions` (if missing) and `enrollment_plans`, triggers class‑structure → DHG → revenue cascade.

**State & gates**
- Steps 2–7 run in `draft`. Any change invalidates prior validation.
- Validation enabled only when distributions are valid (100% per level) and no blocking errors exist; warnings are allowed.
- After validation, UI surfaces a clear “Next step: Class Structure” CTA.

**UI mapping**
- Persistent **WorkflowStepper** with 3 macro‑steps:
  - **Projections** (steps 1–6, with accordion substeps and “Optional” badges).
  - **Distribution** (step 7).
  - **Validation** (step 8).
- Header always shows: current step, budget version/year, capacity, status `Draft/Validated`, and last calculation time.
- Advanced overrides (cycle/grade) are collapsed by default with short “Why adjust?” tooltips to avoid overwhelming first‑time users.

### 7.2 Page Layout

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│  Enrollment Projection                                    [Draft] [Validate →]  │
├─────────────────────────────────────────────────────────────────────────────────┤
│                                                                                 │
│  ┌─ STEP 1: Select Scenario ──────────────────────────────────────────────────┐ │
│  │                                                                             │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                         │ │
│  │  │ WORST CASE  │  │    BASE     │  │  BEST CASE  │                         │ │
│  │  │   🔴 45    │  │   🔵 65    │  │   🟢 85    │ ← PS Entry                │ │
│  │  │   -2%/yr   │  │    0%      │  │   +3%/yr   │ ← Growth                  │ │
│  │  │   90% ret  │  │   96% ret  │  │   99% ret  │ ← Retention               │ │
│  │  │   0.3x lat │  │   1.0x lat │  │   1.5x lat │ ← Lateral                 │ │
│  │  │  [Select]  │  │ [Selected] │  │  [Select]  │                           │ │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                         │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ STEP 2: Adjust Global Parameters (Optional) ──────────────────────────────┐ │
│  │                                                                             │ │
│  │  PS Entry Adjustment          Retention Adjustment                          │ │
│  │  ──────●──────────  +5        ────────●────────  +2%                       │ │
│  │  -20            +20           -5%            +5%                            │ │
│  │                                                                             │ │
│  │  Lateral Multiplier           Default Class Size                            │ │
│  │  ────────●────────  1.0x      ────────●────────  25                        │ │
│  │  0.5x           1.5x          20              30                            │ │
│  │                                                                             │ │
│  │  [ Reset to Scenario Defaults ]                                             │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ STEP 3: Fine-tune by Cycle / Grade (Optional) ─────  [Expand/Collapse ▼] ─┐ │
│  │                                                                             │ │
│  │  ┌──────────────────────────────────────────────────────────────────────┐  │ │
│  │  │ Grade │ Retention │ Lateral │ Max Div │ Class Size │ Sparkline     │  │ │
│  │  ├──────────────────────────────────────────────────────────────────────┤  │ │
│  │  │  PS   │    N/A    │   N/A   │    3    │     25     │  ▁▂▃▂▃        │  │ │
│  │  │  MS   │   0.96    │    27   │    3    │     25     │  ▂▁▂▄▃        │  │ │
│  │  │  GS   │   0.96    │    20   │    5    │     25     │  ▃▄▃▄▅        │  │ │
│  │  │  ...  │    ...    │   ...   │   ...   │    ...     │    ...        │  │ │
│  │  └──────────────────────────────────────────────────────────────────────┘  │ │
│  └─────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                 │
│  ┌─ PROJECTION RESULTS ──────────────────────────────────────────────────────┐  │
│  │                                                                            │  │
│  │  ⚠️ CAPACITY WARNING: Projection exceeds capacity by 47 students         │  │
│  │     Proportional reduction applied. [View Details]                         │  │
│  │                                                                            │  │
│  │  ┌────────────────────────────────────────────────────────────────────┐   │  │
│  │  │ Grade │ 2025 │ 2026  │ 2027  │ 2028  │ 2029  │ 2030  │ Sparkline │   │  │
│  │  ├────────────────────────────────────────────────────────────────────┤   │  │
│  │  │  PS   │  65  │   65  │   65  │   65  │   65  │   65  │  ━━━━━━   │   │  │
│  │  │  MS   │  71  │   89  │   89  │   89  │   89  │   89  │  ▁▅▅▅▅▅   │   │  │
│  │  │  GS   │ 124  │   88  │  105  │  105  │  105  │  105  │  ▅▂▃▃▃▃   │   │  │
│  │  │  ...  │ ...  │  ...  │  ...  │  ...  │  ...  │  ...  │   ...     │   │  │
│  │  ├────────────────────────────────────────────────────────────────────┤   │  │
│  │  │ TOTAL │1,747 │1,761  │1,766  │1,767  │1,784  │1,785  │           │   │  │
│  │  │ Util% │94.4% │95.2%  │95.5%  │95.5%  │96.4%  │96.5%  │           │   │  │
│  │  └────────────────────────────────────────────────────────────────────┘   │  │
│  │                                                                            │  │
│  │  [📊 View by Cycle] [📈 View Chart] [📋 Fiscal Year View]                 │  │
│  └────────────────────────────────────────────────────────────────────────────┘  │
│                                                                                 │
└─────────────────────────────────────────────────────────────────────────────────┘
```

### 7.3 Component Specifications

#### 7.3.1 ScenarioSelector

- **3 cards** side-by-side (responsive: stack on mobile)
- **Color coding**: Worst=Red, Base=Blue, Best=Green
- **Selected state**: Border highlight, checkmark icon
- **Hover**: Show full description tooltip
- **Key metrics** visible: PS Entry, Growth Rate, Retention, Lateral

#### 7.3.2 GlobalOverridesPanel

- **4 sliders** with real-time value display
- **Debounced updates** (300ms) for smooth UX
- **"Reset to Defaults"** button
- **Visual feedback**: Slider thumb shows current vs. scenario default
- **Advanced setting**: editable school max capacity (default 1,850) stored in config

#### 7.3.3 GradeOverridesGrid

- **AG Grid** with inline editing
- **Columns**: Grade, Cycle, Retention, Lateral Entry, Max Divisions, Class Size, Sparkline
- **Sparkline column**: Mini line chart showing 5-year historical trend
- **Conditional formatting**: Highlight overridden cells
- **Collapsible by default** (advanced users)

#### 7.3.4 NationalityDistributionPanel

- **Per-level percentage grid** (French / Saudi / Other)
- **Defaults prefilled** to 30% / 2% / 68% for every level
- **Inline edit** with immediate sum validation (must equal 100%)
- **“Apply to All Levels” shortcut** for fast global edits
- **Impact preview**: shows computed counts per nationality for the base year

#### 7.3.5 ProjectionResultsGrid

- **AG Grid** with year columns (2025-2030)
- **Grouped rows** by cycle (collapsible)
- **Sparkline column** for each grade
- **Footer row**: Totals and utilization %
- **Color coding**: Red for over-capacity, green for healthy

#### 7.3.6 CapacityWarningBanner

- **Yellow/orange alert banner** when over configured capacity (default 1,850)
- **Shows**: Total reduction needed, number of grades affected
- **"View Details" button** opens modal with per-class breakdown
- **Auto-hide** when under capacity

#### 7.3.7 Sparkline Implementation

```typescript
// Using recharts (already in repo) for lightweight sparklines
import { LineChart, Line, ResponsiveContainer } from 'recharts';

function GradeSparkline({ data }: { data: number[] }) {
  const points = data.map((v, i) => ({ i, v }));
  return (
    <ResponsiveContainer width={80} height={20}>
      <LineChart data={points}>
        <Line type="monotone" dataKey="v" stroke="#3B82F6" dot={false} strokeWidth={2} />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### 7.4 User Flow

```
1. User navigates to /enrollment/planning
   └── WorkflowStepper shows: Projections → Distribution → Validation
   └── System loads config (or creates default with "Base" scenario)

2. User selects scenario (Worst/Base/Best)
   └── System auto-recalculates projection
   └── Results update in real-time

3. User adjusts global sliders (optional)
   └── Debounced API call (300ms)
   └── Results update

4. User expands grade overrides (optional, advanced)
   └── Edits individual grade parameters
   └── System recalculates

5. User reviews ProjectionResultsGrid (5-year view)
   └── Capacity warning appears if total > configured capacity

6. User switches to Distribution step/tab
   └── Nationality percentages prefilled to 30%/2%/68% by level
   └── User edits % if needed; UI validates sums to 100%

7. User clicks "Validate"
   └── Confirmation dialog appears
   └── Lists downstream impacts
   └── User confirms

8. System validates:
   └── Locks projection (status = validated)
   └── Writes nationality_distributions defaults if missing
   └── Populates enrollment_plans (level × nationality)
   └── Triggers class structure calculation
   └── User can proceed to DHG planning
```

### 7.5 Macro‑Step Acceptance Criteria

#### 7.5.1 Macro‑Step A — Projections

**Entry / baseline**
- Given a budget version with existing `enrollment_plans`, opening `/enrollment/planning` auto‑creates a projection config and seeds `base_year_enrollment` from aggregated plans; UI shows a one‑time “Imported baseline” banner with a reset option.
- Given no existing plans, config is still created with Base scenario; baseline starts at 0 and UI explains that projections are scenario‑driven.

**Scenario & defaults**
- User can select Worst/Base/Best; selection persists to `enrollment_projection_configs.scenario_id`.
- Scenario selection immediately recalculates projections and updates results without page reload.
- “Reset to Scenario Defaults” restores scenario defaults + clears global/cycle/grade overrides.

**Global overrides**
- Sliders allow adjustments within defined bounds and are debounced (≈300ms) for API writes.
- Max capacity is editable, stored per version, defaulting to 1,850 if unset.
- Changing any global parameter triggers recalculation and updates utilization and capacity banner in results.

**Cycle overrides (optional)**
- Per‑cycle class size ceilings and max divisions can be edited.
- Overrides are visually marked and can be cleared individually.
- Resolution order is enforced: Grade > Cycle > Global > Scenario.

**Grade overrides (optional)**
- Inline editing in `GradeOverridesGrid` supports retention, lateral entry, max divisions, class size ceiling within bounds.
- Overridden cells are highlighted, and a “clear override” action restores inherited values.

**Results & feasibility**
- Results grid shows 5‑year school‑year projections with cycle grouping and totals row.
- Fiscal year view is available and uses proration rule (8/12 prior SY + 4/12 current SY).
- Capacity behavior:
  - If total ≤ capacity: banner hidden; `was_capacity_constrained=false`.
  - If total > capacity: banner shows exceedance and proportional reduction is applied; per‑grade reductions are inspectable.
- Divisions and average class sizes shown per grade reflect effective class size ceilings and max divisions.

**Draft state**
- Any projection edit sets config status to `draft` (if previously validated) and surfaces a warning that downstream data is no longer locked.

#### 7.5.2 Macro‑Step B — Distribution

- Distribution step displays per‑level nationality % grid.
- Defaults (30% French / 2% Saudi / 68% Other) are prefilled for all levels where no record exists.
- Each row must sum to 100%:
  - If not, row is marked invalid, and “Validate” action is disabled.
- “Apply to All Levels” updates all rows with the same % values.
- Live preview shows computed nationality counts for the base year totals.
- Saving writes to `nationality_distributions` for the version and invalidates/recalculates projection results and dependent caches.

#### 7.5.3 Macro‑Step C — Validation

- “Validate” button is enabled only when:
  - Distribution sums are valid for all levels with enrollment.
  - No blocking errors exist (see 7.6).
- Confirmation dialog lists downstream impacts: `enrollment_plans`, `class_structures`, DHG, revenue, costs.
- On confirm:
  - Config status becomes `validated`.
  - Missing `nationality_distributions` are created with defaults.
  - `enrollment_plans` are fully populated (3 rows per level) using latest projections + distributions.
  - Cascade to class structure and dependent modules is triggered.
- Post‑validation:
  - Projections and distribution inputs become read‑only with a “Unvalidate to edit” CTA.
  - UI shows success toast and a clear Next Step CTA to `/enrollment/class-structure`.
- “Unvalidate” returns the planner to draft and re‑enables editing.

### 7.6 UI States & Error Handling

**Global states**
- **No version selected**: show empty state prompting version selection; disable all controls.
- **Loading**: skeletons for stepper, scenario cards, grids, and results.
- **API error**: non‑blocking toast + inline retry; keep last good data displayed.

**Blocking errors (disable validation)**
- Distribution row sum ≠ 100% for any level with total enrollment.
- Any projected_students < 0 or divisions < 1 after constraints (should not occur if validators correct; treat as hard error).
- Missing academic structure reference data (levels/cycles) for the version.

**Warnings (allow validation)**
- Capacity constrained in ≥1 projected years.
- Large YoY change vs baseline beyond threshold (flag only).
- Any grade hitting max divisions or class size ceiling (feasibility warning).

**Accessibility / UX**
- Stepper is keyboard navigable and announces current step.
- Inline grid edits support undo/redo and show validation messages near cells.
  - Enable AG Grid undo/redo:
    ```ts
    gridOptions: {
      undoRedoCellEditing: true,
      undoRedoCellEditingLimit: 20,
    }
    ```

---

## 8. Implementation Phases

### Phase 1: Database Foundation
**Status**: Design frozen; migration build pending scheduling.
**Duration**: 1 day
**Deliverables**:
- Migration file with all 7 tables
- Seed data for scenarios and lateral entry defaults
- SQLAlchemy models

**Files**:
- `backend/alembic/versions/20251212_0001_enrollment_projection_tables.py`
- `backend/app/models/enrollment_projection.py`

**Verification**:
- [ ] Migration runs successfully
- [ ] Seed data populated
- [ ] Models import without errors

---

### Phase 2: Core Calculation Engine
**Status**: In progress (current focus).
**Duration**: 1-2 days
**Deliverables**:
- Projection engine with 4-layer override resolution
- Capacity constraint logic
- Unit tests for all formulas

**Files**:
- `backend/app/engine/enrollment/projection_engine.py`
- `backend/app/engine/enrollment/projection_models.py`
- `backend/tests/engine/test_enrollment_projection.py`

**Verification**:
- [ ] Unit tests pass for all scenarios
- [ ] Override priority correctly implemented
- [ ] Capacity reduction works as expected

---

### Phase 3: Fiscal Year Proration
**Duration**: 0.5 days
**Deliverables**:
- Proration calculator
- Integration with projection engine
- Unit tests

**Files**:
- `backend/app/engine/enrollment/fiscal_year_proration.py`
- `backend/tests/engine/test_fiscal_year_proration.py`

**Verification**:
- [ ] Proration formula correct (8/12 + 4/12)
- [ ] School year mapping accurate

---

### Phase 4: API Layer
**Duration**: 1 day
**Deliverables**:
- All API endpoints
- Pydantic schemas
- API tests

**Files**:
- `backend/app/api/v1/enrollment_projection.py`
- `backend/app/schemas/enrollment_projection.py`
- `backend/tests/api/test_enrollment_projection_api.py`

**Verification**:
- [ ] All endpoints respond correctly
- [ ] Validation errors handled
- [ ] Auto-recalculation works

---

### Phase 5: Service Layer & Validation
**Duration**: 1 day
**Deliverables**:
- Service with cascade logic
- Apply nationality distributions (default 30/2/68 if missing) and populate `enrollment_plans`
- Downstream integration (class_structure, DHG, revenue)
- Integration tests
- Cache invalidation on config/overrides/nationality_distribution changes

**Files**:
- `backend/app/services/enrollment_projection_service.py`
- `backend/tests/services/test_enrollment_projection_service.py`

**Verification**:
- [ ] Validation locks projection
- [ ] Cascade populates downstream tables
- [ ] Unvalidate works correctly
- [ ] Projection cache invalidates when any driver changes (config, overrides, distributions)

---

### Phase 5.5: Migration & Replacement Strategy (Cross-cutting)
**Goal**: Replace the legacy `/enrollment/planning` manual-entry flow with the projection-driven planner while keeping downstream modules stable and minimizing user confusion.

**Backend migration**
1. Implement projection tables/models/engine/routes/services (Phases 1–5).
2. **Normalize capacity to configurable 1,850 default**:
   - Treat `1850` as the system default only.
	   - Replace hard-coded `1875` capacity usage across enrollment validators/services, KPI, and dashboard calculations with:
	     - `enrollment_projection_configs.school_max_capacity` when a config exists for the version.
	     - System default (1,850) when no config exists.
	   - Implement a single helper (`DEFAULT_SCHOOL_CAPACITY` + `get_effective_capacity(version_id)`) and use it everywhere capacity is referenced.
	3. Keep `enrollment_plans` as the canonical downstream input. Validation writes projected totals split by nationality into `enrollment_plans`, so existing `ClassStructureService`, DHG, Revenue, KPI, and Cost services require no behavioral changes.
4. Mark legacy growth projection as **legacy**:
   - Endpoint: `/planning/enrollment/{version_id}/project`
   - Engine: `backend/app/engine/enrollment/calculator.py`
   - Not used by UI after migration; retained temporarily for historical comparison/admin tooling.
5. Cascade + cache:
   - Any change to projection config or overrides invalidates dependent caches (Enrollment → Class Structure → DHG → Revenue/Costs).
   - Any change to `nationality_distributions` also invalidates projection results and dependent caches.

**Frontend replacement**
1. Replace contents of `frontend/src/routes/_authenticated/enrollment/planning.tsx`:
   - New page implements `WorkflowStepper` macro‑steps: **Projections → Distribution → Validation**.
   - Manual totals entry UI is removed; totals derive from projections.
   - Retain historical toggle/summary view where it adds context.
2. Reuse existing distribution APIs/hooks for the Distribution step (no parallel API).
3. Enrollment dashboard and navigation continue to link to `/enrollment/planning` (same route), but labels/icons should be updated to “Projections & Planning” if needed.
4. Legacy routes:
   - `/enrollment/validation` deep‑links to the Validation macro‑step in `/enrollment/planning` (or shows a read‑only summary with CTA).
   - Any “Update Projections” quick action remains on `/enrollment/planning`.

**Data/bootstrap behavior**
1. On first open of a budget version with existing manual `enrollment_plans`:
   - Service aggregates existing plans by grade/level to seed `base_year_enrollment`.
   - Creates a default projection config (Base scenario) storing inferred base year totals.
   - UI shows a one‑time banner: “Imported current plan as baseline” with **Reset to Scenario Defaults** action.
2. If no existing plans:
   - Base year enrollment starts at 0; user proceeds with scenarios and overrides.

**Verification**
- [ ] Opening `/enrollment/planning` on an existing version shows imported baseline.
- [ ] Validating produces `enrollment_plans` that match prior manual totals (within rounding).
- [ ] Downstream class structure/DHG/revenue work without UI-side changes.
- [ ] Capacity is consistent across enrollment, KPIs, and dashboards.

---

### Phase 6: Frontend Types & Service
**Duration**: 0.5 days
**Deliverables**:
- TypeScript types
- API service
- React Query hooks

**Files**:
- `frontend/src/types/enrollmentProjection.ts`
- `frontend/src/services/enrollmentProjection.ts`
- `frontend/src/hooks/api/useEnrollmentProjection.ts`

**Verification**:
- [ ] Types match backend schemas
- [ ] Hooks work with mock data

---

### Phase 7: Scenario Selector UI
**Duration**: 0.5 days
**Deliverables**:
- ScenarioSelector component
- Selection state management
- Integration with API

**Files**:
- `frontend/src/components/enrollment/ScenarioSelector.tsx`

**Verification**:
- [ ] 3 scenarios display correctly
- [ ] Selection updates config
- [ ] Visual feedback on selection

---

### Phase 8: Global Overrides Panel
**Duration**: 0.5 days
**Deliverables**:
- Slider components
- Debounced updates
- Reset functionality

**Files**:
- `frontend/src/components/enrollment/GlobalOverridesPanel.tsx`

**Verification**:
- [ ] Sliders work smoothly
- [ ] Debounce prevents excessive API calls
- [ ] Reset works

---

### Phase 9: Grade Overrides Grid
**Duration**: 1 day
**Deliverables**:
- AG Grid with inline editing
- Sparkline column
- Override highlighting

**Files**:
- `frontend/src/components/enrollment/GradeOverridesGrid.tsx`

**Verification**:
- [ ] Grid displays all grades
- [ ] Inline editing works
- [ ] Sparklines render

---

### Phase 10: Projection Results Grid
**Duration**: 1 day
**Deliverables**:
- Multi-year results display
- Sparklines per grade
- Cycle grouping

**Files**:
- `frontend/src/components/enrollment/ProjectionResultsGrid.tsx`

**Verification**:
- [ ] 5-year projection displays
- [ ] Grouping by cycle works
- [ ] Totals correct

---

### Phase 11: Nationality Distribution UI
**Duration**: 0.5 days
**Deliverables**:
- NationalityDistributionPanel (% by level)
- Default seeding (30% / 2% / 68%) display
- Inline validation (sum = 100%)
- API wiring to update `nationality_distributions`

**Files**:
- `frontend/src/components/enrollment/NationalityDistributionPanel.tsx`

**Verification**:
- [ ] Defaults prefilled correctly for all levels
- [ ] Sum validation blocks invalid saves
- [ ] Changes update computed counts preview

---

### Phase 12: Capacity Warning & Reduction UI
**Duration**: 0.5 days
**Deliverables**:
- Warning banner component
- Reduction breakdown modal
- Per-class reduction display

**Files**:
- `frontend/src/components/enrollment/CapacityWarningBanner.tsx`
- `frontend/src/components/enrollment/ReductionBreakdownModal.tsx`

**Verification**:
- [ ] Banner shows when over capacity
- [ ] Breakdown shows per-class reduction
- [ ] Hides when under capacity

---

### Phase 13: Validation Flow
**Duration**: 0.5 days
**Deliverables**:
- Validation button
- Confirmation dialog
- Success/error feedback

**Files**:
- `frontend/src/components/enrollment/ValidationConfirmDialog.tsx`

**Verification**:
- [ ] Confirmation shows downstream impacts
- [ ] Success updates UI to "validated" state
- [ ] Unvalidate works

---

### Phase 14: Main Page Integration
**Duration**: 1 day
**Deliverables**:
- Enrollment planning page assembling all components
- Route registration
- Navigation integration

**Files**:
- `frontend/src/routes/_authenticated/enrollment/planning.tsx`

**Verification**:
- [ ] Page loads correctly
- [ ] All components interact properly
- [ ] Navigation works

---

### Phase 15: E2E Testing & Polish
**Duration**: 1 day
**Deliverables**:
- Playwright E2E tests
- UI polish and responsiveness
- Error handling

**Files**:
- `frontend/tests/e2e/enrollment-projection.spec.ts`

**Verification**:
- [ ] Full user flow works
- [ ] Mobile responsive
- [ ] Error states handled gracefully

---

## 9. Testing Strategy

### 9.1 Unit Tests (Backend)

Cover at minimum:

- PS entry growth:
  - Base scenario PS uses `ps_entry` and `entry_growth_rate`.
  - Global `ps_entry_adjustment` shifts PS only.
- Cohort progression:
  - For each grade `G != PS`, `Students[G, Y]` uses previous grade `G-1` from `Y-1` and `Retention_Rate[G]`.
  - `Retention_Rate[TLE]` uses `terminal_retention`, others use `default_retention`.
- Lateral entry:
  - Base lateral entry applied with scenario/global multiplier.
  - Grade override lateral entry replaces multiplied base.
- Override priority:
  - Grade override > Level override > Global override > Scenario default for retention, class size, max divisions, lateral.
- Per‑grade capacity clamp:
  - Projected students do not exceed `max_divisions × class_size_ceiling`.
  - Zero students yields zero divisions.
- School‑wide capacity constraint:
  - No reduction when total ≤ capacity.
  - Proportional reduction when total > capacity with correct per‑grade reductions.
  - Boundary case: total exactly equals capacity.
- Multi‑year iteration:
  - Year `Y+1` uses year `Y` results as baseline.
  - Baseline dicts with missing grades treat missing as 0 (no crash).
- Input validation:
  - Empty baseline, negative counts, or unknown grade codes return blocking errors.

Concrete tests should include edge/boundary cases: 0 students, 100% retention, 0 lateral entry, and over‑capacity by 1 student.

### 9.2 Integration Tests (API)

Integration test examples below are stubs for the spec; replace `pass` with real assertions when implementing.

```python
# tests/api/test_enrollment_projection_api.py

class TestProjectionAPI:
    """Tests for enrollment_projection.py routes"""

    async def test_get_scenarios_returns_three(self, client):
        """Should return exactly 3 scenarios."""
        pass

    async def test_get_config_creates_default(self, client):
        """Should create default config if none exists."""
        pass

    async def test_update_scenario_triggers_recalculation(self, client):
        """Changing scenario should recalculate results."""
        pass

    async def test_validate_locks_projection(self, client):
        """Validation should set status to 'validated'."""
        pass

    async def test_validate_populates_enrollment_plans(self, client):
        """Validation should populate enrollment_plans table."""
        pass
```

### 9.3 E2E Tests (Frontend)

```typescript
// tests/e2e/enrollment-projection.spec.ts

test.describe('Enrollment Projection', () => {
  test('should display 3 scenario options', async ({ page }) => {
    // ...
  });

  test('should update projection when scenario changes', async ({ page }) => {
    // ...
  });

  test('should show capacity warning when over configured capacity', async ({ page }) => {
    // ...
  });

  test('should validate and show confirmation', async ({ page }) => {
    // ...
  });
});
```

---

## Appendices

### A. Grade Sequence Reference

```
GRADE_SEQUENCE = [
    'PS',   # Petite Section (Maternelle)
    'MS',   # Moyenne Section (Maternelle)
    'GS',   # Grande Section (Maternelle)
    'CP',   # Cours Préparatoire (Élémentaire)
    'CE1',  # Cours Élémentaire 1 (Élémentaire)
    'CE2',  # Cours Élémentaire 2 (Élémentaire)
    'CM1',  # Cours Moyen 1 (Élémentaire)
    'CM2',  # Cours Moyen 2 (Élémentaire)
    '6EME', # Sixième (Collège)
    '5EME', # Cinquième (Collège)
    '4EME', # Quatrième (Collège)
    '3EME', # Troisième (Collège)
    '2NDE', # Seconde (Lycée)
    '1ERE', # Première (Lycée)
    'TLE',  # Terminale (Lycée)
]
```

### B. Historical Enrollment Data (2021-2025)

| Grade | 2021 | 2022 | 2023 | 2024 | 2025 |
|-------|------|------|------|------|------|
| PS | 60 | 67 | 68 | 59 | 65 |
| MS | 94 | 85 | 86 | 109 | 71 |
| GS | 97 | 115 | 95 | 123 | 124 |
| CP | 118 | 103 | 126 | 116 | 126 |
| CE1 | 119 | 116 | 108 | 140 | 118 |
| CE2 | 113 | 120 | 122 | 126 | 132 |
| CM1 | 108 | 123 | 125 | 124 | 121 |
| CM2 | 98 | 112 | 126 | 145 | 121 |
| 6EME | 115 | 99 | 112 | 146 | 151 |
| 5EME | 90 | 117 | 102 | 121 | 139 |
| 4EME | 98 | 96 | 126 | 104 | 120 |
| 3EME | 86 | 101 | 110 | 128 | 103 |
| 2NDE | 77 | 90 | 104 | 130 | 125 |
| 1ERE | 87 | 77 | 102 | 114 | 120 |
| TLE | 74 | 78 | 75 | 109 | 111 |
| **TOTAL** | **1,434** | **1,499** | **1,587** | **1,794** | **1,747** |

### C. Scenario Projection Results (Base Scenario)

| Grade | 2025 | 2026 | 2027 | 2028 | 2029 | 2030 |
|-------|------|------|------|------|------|------|
| PS | 65 | 65 | 65 | 65 | 65 | 65 |
| MS | 71 | 89 | 89 | 89 | 89 | 89 |
| GS | 124 | 88 | 105 | 105 | 105 | 105 |
| CP | 126 | 131 | 96 | 113 | 113 | 113 |
| CE1 | 118 | 128 | 133 | 99 | 115 | 115 |
| CE2 | 132 | 119 | 129 | 134 | 101 | 116 |
| CM1 | 121 | 132 | 119 | 129 | 134 | 102 |
| CM2 | 121 | 123 | 134 | 121 | 131 | 136 |
| 6EME | 151 | 124 | 126 | 137 | 124 | 134 |
| 5EME | 139 | 150 | 124 | 126 | 137 | 124 |
| 4EME | 120 | 139 | 150 | 125 | 127 | 138 |
| 3EME | 103 | 121 | 139 | 150 | 126 | 128 |
| 2NDE | 125 | 107 | 124 | 141 | 152 | 129 |
| 1ERE | 120 | 126 | 109 | 125 | 141 | 152 |
| TLE | 111 | 119 | 124 | 108 | 124 | 139 |
| **TOTAL** | **1,747** | **1,761** | **1,766** | **1,767** | **1,784** | **1,785** |

---

### D. Implementation Checklist (Per File)

#### Backend

- `backend/alembic/versions/20251212_0001_enrollment_projection_tables.py`
  - [ ] Create all 7 projection tables under `efir_budget` schema.
  - [ ] Seed 3 scenarios (Worst/Base/Best) with parameters from Section 2.1.
  - [ ] Seed base lateral entry defaults by grade (Section 2.2).
  - [ ] Ensure `enrollment_projection_configs.school_max_capacity` default = 1850 and editable.

- `backend/app/models/enrollment_projection.py`
  - [ ] SQLAlchemy models for scenarios, configs, global/level/grade overrides, projections cache.
  - [ ] Relationships to `settings_versions`, `ref_academic_cycles`, `ref_academic_levels`, and audit fields.

- `backend/app/engine/enrollment/projection_models.py`
  - [ ] Pydantic models matching engine inputs/outputs (ProjectionInput, ProjectionResult, overrides).
  - [ ] Field bounds aligned with database checks and slider configs.

- `backend/app/engine/enrollment/projection_engine.py`
  - [ ] Implement PS entry growth + cohort retention + lateral entry formulas.
  - [ ] Implement 4‑layer override resolution (Grade > Cycle > Global > Scenario).
  - [ ] Apply per‑grade capacity clamp using effective class size × max divisions.
  - [ ] Apply school‑wide proportional capacity reduction using configurable max capacity.
  - [ ] Implement multi‑year iterative projection (each year feeds next).
  - [ ] Return per‑grade divisions and reduction breakdown.

- `backend/app/engine/enrollment/fiscal_year_proration.py`
  - [ ] Implement school‑year mapping and weighted fiscal enrollment (8/12 + 4/12).
  - [ ] Provide helper to compute proration per grade for result payloads.

- `backend/app/schemas/enrollment_projection.py`
  - [ ] Request/response schemas for scenarios, configs, overrides, results, validate/unvalidate.
  - [ ] Error models for validation and business‑rule failures.

- `backend/app/api/v1/enrollment_projection.py`
  - [ ] CRUD endpoints for config and override layers.
  - [ ] Results endpoint returning multi‑year projections + optional fiscal proration.
  - [ ] Validate/unvalidate endpoints with confirmation gate.
  - [ ] Register router in `backend/app/api/v1/planning.py` under `/planning/enrollment-projection`.

- `backend/app/services/enrollment_projection_service.py`
  - [ ] `get_all_scenarios`, `get_or_create_config`, update overrides.
  - [ ] `calculate_and_save` using engine + writes to `enrollment_projections`.
  - [ ] On any update, invalidate cached projections and dependent caches.
  - [ ] `validate_and_cascade`:
    - [ ] Ensure `nationality_distributions` exist or create defaults 30/2/68.
    - [ ] Split projected totals by nationality and populate `enrollment_plans`.
    - [ ] Trigger class structure calculation and cascade service.
  - [ ] `unvalidate` sets draft and clears downstream lock flags.

- Capacity normalization (existing files)
  - [ ] Replace hard‑coded `1875` with configurable capacity:
    - `backend/app/engine/enrollment/validators.py`
    - `backend/app/services/enrollment_service.py`
    - `backend/app/services/kpi_service.py`
    - `backend/app/services/dashboard_service.py`
    - `backend/app/services/planning_progress_service.py`
    - `backend/app/api/v1/calculations.py`
  - [ ] Source of truth: `enrollment_projection_configs.school_max_capacity` if present, else default 1850.

#### Frontend

- `frontend/src/types/enrollmentProjection.ts`
  - [ ] Types mirror backend schemas; include capacity and fiscal proration fields.

- `frontend/src/services/enrollmentProjection.ts`
  - [ ] Client functions for scenarios/config/overrides/results/validate/unvalidate.

- `frontend/src/hooks/api/useEnrollmentProjection.ts`
  - [ ] React Query hooks with debounced mutations for sliders/grid edits.
  - [ ] Invalidate results on any config/override update.

- `frontend/src/routes/_authenticated/enrollment/planning.tsx`
  - [ ] Replace legacy manual totals UI with projection planner.
  - [ ] Implement `WorkflowStepper` macro‑steps and deep‑linking.
  - [ ] Projections step assembles ScenarioSelector, GlobalOverridesPanel, LevelOverridesPanel, GradeOverridesGrid, ProjectionResultsGrid.
  - [ ] Distribution step renders NationalityDistributionPanel using existing distribution hooks.
  - [ ] Validation step renders ValidationConfirmDialog and read‑only summary when validated.

- Projection components
  - [ ] `frontend/src/components/enrollment/ScenarioSelector.tsx`
  - [ ] `frontend/src/components/enrollment/GlobalOverridesPanel.tsx` (includes capacity input)
  - [ ] `frontend/src/components/enrollment/LevelOverridesPanel.tsx`
  - [ ] `frontend/src/components/enrollment/GradeOverridesGrid.tsx`
  - [ ] `frontend/src/components/enrollment/ProjectionResultsGrid.tsx`
  - [ ] `frontend/src/components/enrollment/CapacityWarningBanner.tsx`
  - [ ] `frontend/src/components/enrollment/ReductionBreakdownModal.tsx`
  - [ ] `frontend/src/components/enrollment/FiscalYearProrationTable.tsx`
  - [ ] `frontend/src/components/enrollment/ValidationConfirmDialog.tsx`

- Distribution component
  - [ ] `frontend/src/components/enrollment/NationalityDistributionPanel.tsx`
    - [ ] Default 30/2/68 prefill when missing.
    - [ ] Sum=100% validation and “Apply to All Levels”.
    - [ ] Base‑year nationality count preview.

- Navigation/legacy adjustments
  - [ ] Update Enrollment dashboard quick action labels to reflect projections.
  - [ ] `/enrollment/validation` route deep‑links to Validation macro‑step or shows read‑only with CTA.

#### Tests

- Backend
  - [ ] `backend/tests/engine/test_enrollment_projection.py`
  - [ ] `backend/tests/engine/test_fiscal_year_proration.py`
  - [ ] `backend/tests/api/test_enrollment_projection_api.py`
  - [ ] `backend/tests/services/test_enrollment_projection_service.py`

- Frontend
  - [ ] Component tests for new projection and distribution panels (Vitest).
  - [ ] `frontend/tests/e2e/enrollment-projection.spec.ts` updated to new `/enrollment/planning` flow.

### E. Future Enhancements (Optional)

The following are valuable follow‑ups but out of scope for Phases 1–15:

- Scenario comparison view (side‑by‑side Worst/Base/Best in results).
- Projection diff view to highlight changes after parameter edits.
- Export projections to Excel for offline budgeting workflows.
- Wire scenario/label language selection into existing i18n/locale infrastructure.

---

*Document Version: 1.1*
*Last Updated: December 2025*
