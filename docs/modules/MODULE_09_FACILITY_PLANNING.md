# Module 9: Facility Planning

## Overview

Module 9 manages facility requirements and associated costs based on class structure, enrollment projections, and academic operations. This module tracks classroom needs, special room allocations, facility utilization rates, rental costs, and maintenance expenses. It ensures the school has adequate physical infrastructure to accommodate planned enrollment while optimizing space utilization and controlling facility-related costs.

**Layer**: Planning Layer (Phase 2)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Facility utilization analytics, space optimization tools, API endpoints (Phase 5-6)

### Purpose

- Calculate classroom requirements based on class structure (from Module 7)
- Track special room needs (science labs, computer labs, art rooms, gymnasiums, libraries)
- Monitor facility utilization rates and capacity constraints
- Project facility rental costs for external spaces
- Estimate maintenance and utilities costs based on occupied space
- Support scenario analysis for facility expansion or consolidation
- Ensure compliance with educational space standards

### Key Design Decisions

1. **Driver-Based Calculation**: Classroom needs automatically calculated from enrollment and class structure (Module 7)
2. **Room Type Classification**: Standard classrooms vs. special-purpose rooms with different cost structures
3. **Utilization Tracking**: Monitor occupancy rates to identify underutilized or overcrowded spaces
4. **External Rental Support**: Track costs for rented facilities (e.g., gymnasium, sports fields)
5. **Dual Period Structure**: Separate facility needs for Period 1 (Jan-Jun) and Period 2 (Sep-Dec) reflecting enrollment changes
6. **Capacity Constraint**: Total facility capacity ~1,875 students (73 classrooms + special rooms)

## Database Schema

### Tables

#### 1. facility_requirements

Classroom and special room requirements by budget period.

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
room_type             roomtype NOT NULL                -- ENUM: standard, lab, computer, art, gym, library, admin
room_name             VARCHAR(200) NULL
rooms_required        INTEGER NOT NULL
rooms_available       INTEGER NOT NULL
utilization_rate      NUMERIC(5, 2) NOT NULL            -- Percentage (0-100)
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- rooms_required >= 0
- rooms_available >= 0
- utilization_rate >= 0 AND utilization_rate <= 100
- utilization_rate = (rooms_required / rooms_available) × 100 (if rooms_available > 0)
- UNIQUE (version_id, academic_period_id, room_type, room_name)

**RLS Policies:**
- Admin: Full access to facility planning
- Manager: Read/write for working budget versions
- Viewer: Read-only for approved budget versions

**Indexes:**
- Primary key on id
- Index on (version_id, academic_period_id)
- Index on room_type for filtering by facility category

#### 2. facility_costs

Rental and operational costs for facilities.

**Columns:**
```sql
id                    UUID PRIMARY KEY
version_id            UUID NOT NULL FOREIGN KEY -> settings_versions.id (CASCADE)
academic_period_id    UUID NOT NULL FOREIGN KEY -> budget_periods.id (RESTRICT)
cost_category         facilitycostcategory NOT NULL    -- ENUM: rental, maintenance, utilities, security
cost_item_name        VARCHAR(200) NOT NULL
cost_driver           VARCHAR(100) NULL                -- e.g., "per_sqm", "per_classroom", "fixed"
driver_quantity       NUMERIC(10, 2) NULL
cost_per_unit         NUMERIC(12, 2) NOT NULL
total_cost            NUMERIC(12, 2) NOT NULL
account_code          VARCHAR(20) NOT NULL FOREIGN KEY -> chart_of_accounts.code (RESTRICT)
currency              VARCHAR(3) NOT NULL DEFAULT 'SAR'
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
```

**Constraints:**
- cost_per_unit >= 0
- total_cost >= 0
- If cost_driver IS NOT NULL, then total_cost = driver_quantity × cost_per_unit
- account_code must start with '61' (Services extérieurs) or '62' (Autres services extérieurs)

**RLS Policies:**
- Same as facility_requirements

**Indexes:**
- Primary key on id
- Index on (version_id, academic_period_id, cost_category)
- Index on account_code for financial consolidation

#### 3. facility_inventory

Current facility inventory and capacity.

**Columns:**
```sql
id                    UUID PRIMARY KEY
school_id             UUID NOT NULL FOREIGN KEY -> system_configuration.school_id (RESTRICT)
room_type             roomtype NOT NULL
room_identifier       VARCHAR(100) NOT NULL            -- e.g., "Room 101", "Science Lab A"
building_name         VARCHAR(200) NULL
floor_number          INTEGER NULL
capacity_students     INTEGER NOT NULL DEFAULT 0
area_sqm              NUMERIC(8, 2) NULL
is_available          BOOLEAN NOT NULL DEFAULT true
ownership_status      ownershipstatus NOT NULL         -- ENUM: owned, rented, shared
notes                 TEXT NULL
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- capacity_students >= 0
- area_sqm > 0 (if not null)
- UNIQUE (school_id, room_identifier)

**RLS Policies:**
- All authenticated users can read facility inventory
- Only admins can modify facility inventory

**Indexes:**
- Primary key on id
- Index on (school_id, room_type, is_available)

### Enums

#### RoomType
```sql
CREATE TYPE efir_budget.roomtype AS ENUM (
    'standard',      -- Regular classroom
    'lab',           -- Science laboratory
    'computer',      -- Computer lab
    'art',           -- Art/music room
    'gym',           -- Gymnasium/sports facility
    'library',       -- Library/media center
    'admin'          -- Administrative office
);
```

#### FacilityCostCategory
```sql
CREATE TYPE efir_budget.facilitycostcategory AS ENUM (
    'rental',        -- External facility rental (e.g., sports complex)
    'maintenance',   -- Repairs, cleaning, upkeep
    'utilities',     -- Electricity, water, AC
    'security'       -- Security services, surveillance
);
```

#### OwnershipStatus
```sql
CREATE TYPE efir_budget.ownershipstatus AS ENUM (
    'owned',         -- School-owned facility
    'rented',        -- Long-term rental
    'shared'         -- Shared with other organizations
);
```

## Data Model

### Sample Facility Requirements (2025-2026, Period 2)

```json
[
  {
    "id": "550e8400-e29b-41d4-a716-446655440900",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "room_type": "standard",
    "room_name": "General Classrooms",
    "rooms_required": 73,
    "rooms_available": 75,
    "utilization_rate": 97.33,
    "notes": "73 classes total (Maternelle to Lycée)"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440901",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "room_type": "lab",
    "room_name": "Science Labs",
    "rooms_required": 3,
    "rooms_available": 3,
    "utilization_rate": 100.00,
    "notes": "Physics, Chemistry, SVT labs for Collège and Lycée"
  },
  {
    "id": "550e8400-e29b-41d4-a716-446655440902",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "room_type": "computer",
    "room_name": "Computer Labs",
    "rooms_required": 2,
    "rooms_available": 2,
    "utilization_rate": 100.00,
    "notes": "Technology and digital literacy classes"
  }
]
```

### Sample Facility Costs (2025-2026, Period 2)

```json
[
  {
    "id": "660e8400-e29b-41d4-a716-446655440910",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_category": "rental",
    "cost_item_name": "Sports Complex Rental (Gymnasium)",
    "cost_driver": "per_month",
    "driver_quantity": 4,
    "cost_per_unit": 15000.00,
    "total_cost": 60000.00,
    "account_code": "61320",
    "currency": "SAR",
    "notes": "Sep-Dec rental for PE classes (no on-site gym)"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440911",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_category": "maintenance",
    "cost_item_name": "Classroom Maintenance",
    "cost_driver": "per_classroom",
    "driver_quantity": 73,
    "cost_per_unit": 500.00,
    "total_cost": 36500.00,
    "account_code": "61550",
    "currency": "SAR",
    "notes": "Quarterly maintenance for 73 classrooms"
  },
  {
    "id": "660e8400-e29b-41d4-a716-446655440912",
    "version_id": "123e4567-e89b-12d3-a456-426614174000",
    "academic_period_id": "period-2-sep-dec-uuid",
    "cost_category": "utilities",
    "cost_item_name": "Air Conditioning (AC)",
    "cost_driver": "per_sqm",
    "driver_quantity": 12500.00,
    "cost_per_unit": 3.20,
    "total_cost": 40000.00,
    "account_code": "62260",
    "currency": "SAR",
    "notes": "AC costs for 12,500 sqm (Sep-Dec period, higher usage)"
  }
]
```

### Facility Inventory (EFIR Actual)

| Room Type | Quantity | Capacity (Total) | Area (sqm) | Ownership | Utilization (2024-2025) |
|-----------|----------|------------------|------------|-----------|-------------------------|
| Standard Classrooms | 75 | 1,875 (avg 25/room) | 10,500 | Owned | 97.3% (73 used) |
| Science Labs | 3 | 75 (avg 25/lab) | 450 | Owned | 100% |
| Computer Labs | 2 | 50 (avg 25/lab) | 300 | Owned | 100% |
| Art Rooms | 2 | 50 (avg 25/room) | 300 | Owned | 100% |
| Gymnasium | 0 | 0 | 0 | N/A | Rented externally |
| Library | 1 | 100 | 500 | Owned | N/A |
| Administrative | 15 | N/A | 750 | Owned | N/A |
| **Total** | **98** | **2,150** | **12,800 sqm** | - | **97.3%** |

## Business Rules

### Facility Requirement Rules

1. **Auto-Calculation**: Standard classroom requirements automatically calculated from class structure (Module 7)
2. **Room Type Standards**:
   - Standard classroom: 140 sqm, capacity 25-30 students
   - Science lab: 150 sqm, capacity 25 students (2-hour block sessions)
   - Computer lab: 150 sqm, capacity 25 students
   - Art room: 150 sqm, capacity 25 students
3. **Utilization Thresholds**:
   - Optimal: 85-95% utilization
   - Warning: >95% utilization (overcrowded, limited flexibility)
   - Alert: <70% utilization (underutilized, inefficient)
4. **Special Room Ratios**:
   - Science labs: 1 lab per 150-200 secondary students
   - Computer labs: 1 lab per 300 students
   - Gymnasium: Required for PE (EFIR rents externally as no on-site facility)

### Facility Cost Rules

1. **Cost Drivers**:
   - Rental: Fixed monthly costs (e.g., gymnasium rental)
   - Maintenance: Per classroom or per sqm
   - Utilities: Per sqm (AC, electricity, water)
   - Security: Fixed monthly costs or per sqm
2. **Account Code Mapping**:
   - Rental: 61320 (Locations immobilières)
   - Maintenance: 61550 (Entretien et réparations sur biens immobiliers)
   - Utilities: 62260 (Honoraires)
   - Security: 62270 (Frais de gardiennage)
3. **Cost Allocation**: Costs allocated proportionally by period based on school days (Period 1: 40%, Summer: 10%, Period 2: 50%)
4. **External Rentals**: Track separately from owned facilities with explicit ownership_status = 'rented'

### Validation Rules

1. **Capacity Constraint**: rooms_required ≤ rooms_available (cannot exceed physical capacity)
2. **Positive Values**: All counts, areas, and costs must be >= 0
3. **Utilization Bounds**: utilization_rate between 0% and 100%
4. **Driver Consistency**: If cost_driver specified, total_cost must equal driver_quantity × cost_per_unit
5. **Account Code Validity**: Facility costs must use valid PCG codes (61xxx or 62xxx series)

## Calculation Examples

### Example 1: Standard Classroom Requirements

**Context**: Calculate classroom needs for 2025-2026 based on class structure.

**Given Data** (from Module 7):
- Maternelle: 12 classes
- Élémentaire: 27 classes
- Collège: 21 classes
- Lycée: 13 classes
- Total: 73 classes

**Calculation:**
```
Standard classrooms required = Total classes = 73 classrooms

Available classrooms: 75

Utilization rate = (73 ÷ 75) × 100 = 97.33%
```

**Result**:
- 73 classrooms required
- 75 classrooms available
- 97.33% utilization (optimal range: 85-95%, slightly high but acceptable)
- 2 spare classrooms for flexibility

### Example 2: Science Lab Requirements (Secondary Only)

**Context**: Determine science lab needs for Collège and Lycée.

**Given Data**:
- Collège enrollment: 540 students (21 classes)
- Lycée enrollment: 385 students (13 classes)
- Total secondary: 925 students
- Lab capacity: 25 students per session
- Standard: 1 lab per 150-200 secondary students

**Calculation:**
```
Labs needed (by student ratio) = 925 ÷ 175 (midpoint) = 5.29 → 6 labs ideal

Labs needed (by class count) = 3 subjects (Physics, Chemistry, SVT) with block scheduling
- Peak demand: Max 2 simultaneous lab sessions (constraint from Module 6)
- Available labs: 3

Utilization check:
- 34 total classes (Collège + Lycée)
- Each class needs ~3 lab hours/week (Physics, Chemistry, SVT combined)
- Total lab hours needed: 34 × 3 = 102 hours/week
- Available lab hours: 3 labs × 28 hours/week = 84 hours
- Utilization: 102 ÷ 84 = 121% → OVERCAPACITY (need 4 labs, not 3)
```

**Result**:
- Current: 3 labs available
- Needed: 4 labs (based on scheduling constraints)
- **Recommendation**: Add 1 science lab or stagger schedules to reduce peak demand

### Example 3: Gymnasium Rental Cost (Period 2: Sep-Dec)

**Context**: Calculate external gymnasium rental for PE classes.

**Given Data**:
- EFIR has no on-site gymnasium (ownership_status = N/A, must rent)
- Period 2: September-December = 4 months
- Rental rate: 15,000 SAR/month (external sports complex)
- PE hours needed: All students (1,900) × 2 hours/week average

**Calculation:**
```
Rental cost (Sep-Dec) = 4 months × 15,000 SAR/month = 60,000 SAR

Annualized rental cost:
- Period 1 (Jan-Jun): 6 months × 15,000 = 90,000 SAR
- Summer (Jul-Aug): 0 SAR (school closed)
- Period 2 (Sep-Dec): 4 months × 15,000 = 60,000 SAR
- Total annual: 150,000 SAR
```

**Result**:
- Period 2 cost: 60,000 SAR
- Annual cost: 150,000 SAR
- Account code: 61320 (Locations immobilières)

### Example 4: Classroom Maintenance Cost (Per Classroom Driver)

**Context**: Estimate quarterly maintenance costs for all classrooms.

**Given Data**:
- Total classrooms in use: 73
- Maintenance cost: 500 SAR per classroom per quarter
- Period 2: Sep-Dec (1 quarter for maintenance billing)

**Calculation:**
```
Total maintenance cost (Period 2) = 73 classrooms × 500 SAR/classroom = 36,500 SAR

Breakdown:
- Cost driver: "per_classroom"
- Driver quantity: 73
- Cost per unit: 500 SAR
- Total cost: 73 × 500 = 36,500 SAR

Annual maintenance:
- 4 quarters × 36,500 SAR = 146,000 SAR (assuming stable 73 classrooms)
```

**Result**:
- Period 2 maintenance: 36,500 SAR
- Annual maintenance: 146,000 SAR
- Account code: 61550 (Entretien et réparations)

### Example 5: Air Conditioning (Utility Cost per Sqm)

**Context**: Calculate AC utility costs for Period 2 based on occupied area.

**Given Data**:
- Total occupied area: 12,500 sqm (73 classrooms + labs + common areas)
- AC cost: 3.20 SAR per sqm per month (higher in Sep-Dec due to heat)
- Period 2: Sep-Dec = 4 months

**Calculation:**
```
Monthly AC cost = 12,500 sqm × 3.20 SAR/sqm = 40,000 SAR

Period 2 AC cost (Sep-Dec) = 40,000 SAR/month × 4 months = 160,000 SAR

Annual AC cost (seasonal variation):
- Period 1 (Jan-Jun): 6 months × 35,000 SAR/month = 210,000 SAR (lower rate, 2.80 SAR/sqm)
- Summer (Jul-Aug): 2 months × 20,000 SAR/month = 40,000 SAR (minimal usage, 1.60 SAR/sqm)
- Period 2 (Sep-Dec): 4 months × 40,000 SAR/month = 160,000 SAR (peak rate, 3.20 SAR/sqm)
- Total annual: 410,000 SAR
```

**Result**:
- Period 2 AC cost: 160,000 SAR
- Annual AC cost: 410,000 SAR
- Cost driver: "per_sqm"
- Driver quantity: 12,500 sqm
- Account code: 62260 (Honoraires - utilities)

## Integration Points

### Upstream Dependencies

1. **Module 1 (System Configuration)**: School capacity limits, facility inventory
2. **Module 7 (Enrollment Planning)**: Class structure determines classroom requirements
3. **Module 6 (Timetable Constraints)**: Peak demand constraints affect special room utilization

### Downstream Consumers

1. **Module 11 (Cost Planning)**: Facility costs feed into operational expense budget
2. **Module 12 (CapEx Planning)**: Facility expansion needs trigger capital expenditure projects
3. **Module 13 (Budget Consolidation)**: Facility costs consolidated into overall budget

### Data Flow

```
Enrollment Planning (Module 7)
        ↓
Class Structure (73 classes)
        ↓
Facility Requirements (Module 9)
    ┌───┴────┬──────────────┐
    ↓        ↓              ↓
Classrooms Special Rooms  Costs
(73 needed) (Labs, etc.)  (Rental, Maintenance, Utilities)
    ↓        ↓              ↓
    └────────┴──────────────┘
              ↓
    Cost Planning (Module 11)
              ↓
    Budget Consolidation (Module 13)
```

## API Endpoints (Future Implementation)

```
GET    /api/v1/budget-versions/:id/facility-requirements
POST   /api/v1/budget-versions/:id/facility-requirements
GET    /api/v1/budget-versions/:id/facility-costs
POST   /api/v1/budget-versions/:id/facility-costs
GET    /api/v1/facility-inventory
POST   /api/v1/calculate-facility-utilization
       Request: { class_structure, room_inventory }
       Response: { utilization_by_type, overcapacity_warnings }
```

## Testing Strategy

### Test Scenarios

#### Scenario 1: Classroom Auto-Calculation
```typescript
const classStructure = { total_classes: 73 };
const availableRooms = 75;

const requirements = await calculateFacilityRequirements(classStructure);
expect(requirements.rooms_required).toBe(73);
expect(requirements.utilization_rate).toBeCloseTo(97.33, 2);
```

#### Scenario 2: Facility Cost with Driver
```typescript
const cost = {
  cost_driver: "per_classroom",
  driver_quantity: 73,
  cost_per_unit: 500
};

const totalCost = calculateFacilityCost(cost);
expect(totalCost).toBe(36500); // 73 × 500
```

#### Scenario 3: Utilization Warning
```typescript
const requirements = { rooms_required: 72, rooms_available: 75 };
const utilization = (72 / 75) * 100; // 96%

expect(utilization).toBeGreaterThan(95); // Overcapacity warning
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | System | Initial documentation: facility_requirements, facility_costs, facility_inventory tables |

## Future Enhancements (Phase 5-6)

1. **Space Optimization Tool**: Recommend optimal room allocation to maximize utilization
2. **Scenario Modeling**: Compare facility needs under different enrollment scenarios
3. **Capacity Planning**: Multi-year facility expansion roadmap based on strategic plan
4. **Utilization Heatmaps**: Visual representation of room usage by day/time slot
5. **Automated Alerts**: Notify when utilization exceeds thresholds (overcrowding or underuse)
6. **Integration with Timetable**: Real-time room booking based on generated timetables
7. **Cost Forecasting**: Predict maintenance and utility costs based on age of facilities
8. **Sustainability Metrics**: Track energy efficiency, carbon footprint, green building compliance

## Notes

- **Phase 4 Scope**: Database foundation only - facility requirement tracking and cost projection
- **Business Logic**: Facility optimization tools deferred to Phase 5-6
- **Critical Constraint**: EFIR has no on-site gymnasium - external rental required (150,000 SAR/year)
- **Utilization Target**: Optimal range 85-95% - current 97.3% indicates near-capacity operation
- **Expansion Consideration**: With enrollment growth (1,796 → 1,900 projected), may need additional classrooms or second shift scheduling
- **Data Source**: Facility inventory and costs based on EFIR actual data (2024-2025)
