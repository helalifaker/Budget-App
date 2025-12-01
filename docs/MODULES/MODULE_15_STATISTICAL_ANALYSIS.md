# Module 15: Statistical Analysis & KPIs

## Overview

Module 15 provides the foundation for statistical analysis and Key Performance Indicator (KPI) tracking in the EFIR Budget Planning Application. This module enables the definition of KPI formulas, pre-calculation of KPI values upon budget approval, and structured storage for analysis and reporting.

**Layer**: Analysis Layer (Phase 4)
**Status**: Database Foundation Implemented (Phase 4)
**Future Phases**: Business logic, KPI calculation engine, API endpoints (Phase 5-6)

### Purpose

- Define and catalog KPIs with formulas and target values
- Store pre-calculated KPI values per budget version
- Support educational, financial, operational, and strategic KPI categories
- Provide audit trail for KPI calculations via stored inputs

### Key Design Decisions

1. **Pre-calculation Strategy**: KPIs are calculated once when a budget version is approved and stored in the database (not calculated on-the-fly)
2. **Formula Storage**: Formulas are stored as text for documentation/audit purposes
3. **Calculation Inputs**: JSONB field stores all inputs used in calculation for transparency and debugging
4. **Version Linking**: KPI values are linked to budget versions for historical tracking and comparison

## Database Schema

### Tables

#### 1. kpi_definitions (Reference Data)

Catalog of all KPIs with their formulas, categories, and targets.

**Columns:**
```sql
id                UUID PRIMARY KEY
code              VARCHAR(50) UNIQUE NOT NULL  -- e.g., 'student_teacher_ratio'
name_en           VARCHAR(200) NOT NULL
name_fr           VARCHAR(200) NOT NULL
description_en    TEXT
description_fr    TEXT
category          kpicategory NOT NULL         -- ENUM: educational, financial, operational, strategic
formula_text      TEXT NOT NULL                -- Human-readable formula
target_value      NUMERIC(15, 4) NULL          -- Optional target/benchmark
unit              VARCHAR(50) NOT NULL         -- e.g., 'ratio', 'percent', 'SAR', 'students'
display_order     INTEGER NOT NULL DEFAULT 0
is_active         BOOLEAN NOT NULL DEFAULT true
created_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at        TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

**Constraints:**
- Unique code per KPI definition
- All KPIs must have both English and French names
- Formula text is required for documentation

**RLS Policies:**
- All authenticated users can read KPI definitions
- Only admins can create/update/delete KPI definitions

#### 2. kpi_values (Versioned Data)

Pre-calculated KPI values stored per budget version.

**Columns:**
```sql
id                    UUID PRIMARY KEY
budget_version_id     UUID NOT NULL FOREIGN KEY -> budget_versions.id (CASCADE)
kpi_definition_id     UUID NOT NULL FOREIGN KEY -> kpi_definitions.id (CASCADE)
calculated_value      NUMERIC(15, 4) NOT NULL
calculation_inputs    JSONB NOT NULL            -- Stores all inputs used in calculation
calculated_at         TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
updated_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
created_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
updated_by_id         UUID NULL FOREIGN KEY -> auth.users.id (SET NULL)
deleted_at            TIMESTAMPTZ NULL         -- Soft delete support
```

**Constraints:**
- Unique constraint on (budget_version_id, kpi_definition_id) - one value per KPI per version
- cascade deletes when budget version is deleted
- Soft delete support via deleted_at

**RLS Policies:**
- Admin: Full access to all KPI values
- Manager: Read/write KPI values for working budget versions
- Viewer: Read-only access to KPI values for approved budget versions

**Indexes:**
- Primary key on id
- Index on (budget_version_id, kpi_definition_id) for lookups
- Index on kpi_definition_id for definition-based queries

### Enums

#### KPICategory

```sql
CREATE TYPE efir_budget.kpicategory AS ENUM (
    'educational',    -- Student/teacher ratios, H/E, class sizes
    'financial',      -- Revenue per student, cost per student, surplus/deficit
    'operational',    -- Capacity utilization, staff efficiency
    'strategic'       -- Long-term targets, growth rates
);
```

## Data Model

### Sample KPI Definitions

#### Educational KPIs

| Code | Name (EN) | Category | Formula | Target | Unit |
|------|-----------|----------|---------|--------|------|
| `student_teacher_ratio` | Student-Teacher Ratio | educational | Total Students ÷ Total FTE Teachers | 12.0 | ratio |
| `he_ratio_secondary` | H/E Ratio Secondary | educational | Total DHG Hours ÷ Total Secondary Students | 1.35 | ratio |
| `avg_class_size` | Average Class Size | educational | Total Students ÷ Total Classes | 22.0 | students |

#### Financial KPIs

| Code | Name (EN) | Category | Formula | Target | Unit |
|------|-----------|----------|---------|--------|------|
| `revenue_per_student` | Revenue per Student | financial | Total Revenue ÷ Total Enrollment | 45000.0 | SAR |
| `cost_per_student` | Cost per Student | financial | Total Costs ÷ Total Enrollment | 40000.0 | SAR |
| `surplus_percent` | Budget Surplus % | financial | (Revenue - Costs) ÷ Revenue × 100 | 10.0 | percent |

#### Operational KPIs

| Code | Name (EN) | Category | Formula | Target | Unit |
|------|-----------|----------|---------|--------|------|
| `capacity_utilization` | Capacity Utilization | operational | Total Students ÷ Max Capacity × 100 | 90.0 | percent |
| `staff_cost_ratio` | Staff Cost Ratio | operational | Personnel Costs ÷ Total Costs × 100 | 70.0 | percent |

#### Strategic KPIs

| Code | Name (EN) | Category | Formula | Target | Unit |
|------|-----------|----------|---------|--------|------|
| `enrollment_growth` | Enrollment Growth Rate | strategic | (Current Year - Previous Year) ÷ Previous Year × 100 | 3.0 | percent |
| `fee_increase_rate` | Fee Increase Rate | strategic | (New Fees - Old Fees) ÷ Old Fees × 100 | 2.5 | percent |

### Sample KPI Value Record

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "budget_version_id": "123e4567-e89b-12d3-a456-426614174000",
  "kpi_definition_id": "660e8400-e29b-41d4-a716-446655440001",
  "calculated_value": 12.34,
  "calculation_inputs": {
    "total_students": 1234,
    "total_fte_teachers": 100.0,
    "calculation_date": "2025-01-15T10:00:00Z",
    "source_data": {
      "enrollment_table": "enrollment_plans",
      "dhg_table": "dhg_teacher_requirements"
    }
  },
  "calculated_at": "2025-01-15T10:00:00Z",
  "created_at": "2025-01-15T10:00:00Z"
}
```

## Business Rules

### KPI Definition Rules

1. **Unique Codes**: Each KPI must have a unique code identifier (snake_case convention)
2. **Bilingual Names**: All KPIs must have both English (name_en) and French (name_fr) names
3. **Formula Documentation**: Formula text is required for audit and documentation purposes
4. **Active Status**: Only active KPIs (is_active = true) are calculated on budget approval
5. **Display Order**: Controls the order KPIs appear in reports and dashboards
6. **Target Values**: Optional benchmarks for comparison (can be null for informational KPIs)

### KPI Value Rules

1. **One Value Per KPI Per Version**: Unique constraint ensures only one calculated value per KPI per budget version
2. **Immutability**: Once calculated, KPI values should not be modified (recalculate as new version if needed)
3. **Calculation Transparency**: All inputs used in calculation must be stored in calculation_inputs JSONB field
4. **Versioned Access**: KPI values inherit access control from their parent budget version (working/approved)
5. **Cascade Delete**: If budget version is deleted, all associated KPI values are deleted
6. **Soft Delete**: KPI values support soft delete for audit compliance

### Validation Rules

1. **Numeric Precision**: All calculated values stored with 4 decimal places (NUMERIC(15, 4))
2. **Target Validation**: If target_value is set, calculated_value should be compared against it for status
3. **Unit Consistency**: Unit must match the KPI definition unit for reporting consistency
4. **Timestamp Tracking**: calculated_at timestamp records when KPI was computed
5. **Audit Trail**: created_by_id and updated_by_id track who triggered the calculation

## Calculation Examples

### Example 1: Student-Teacher Ratio

**KPI Definition:**
- Code: `student_teacher_ratio`
- Formula: `Total Students ÷ Total FTE Teachers`
- Target: 12.0
- Unit: ratio

**Calculation (Budget Version 2025-2026):**

```python
# Inputs
total_students = 1234  # from enrollment_plans
total_fte_teachers = 102.8  # from dhg_teacher_requirements

# Calculation
calculated_value = total_students / total_fte_teachers
# = 1234 / 102.8
# = 12.00 (rounded to 2 decimals)

# Store in kpi_values
{
  "calculated_value": 12.00,
  "calculation_inputs": {
    "total_students": 1234,
    "total_fte_teachers": 102.8,
    "enrollment_query": "SELECT SUM(student_count) FROM enrollment_plans WHERE budget_version_id = ?",
    "fte_query": "SELECT SUM(fte_required) FROM dhg_teacher_requirements WHERE budget_version_id = ?"
  }
}
```

**Comparison to Target:**
- Calculated: 12.00
- Target: 12.0
- Status: On Target ✓

### Example 2: Revenue per Student

**KPI Definition:**
- Code: `revenue_per_student`
- Formula: `Total Revenue ÷ Total Enrollment`
- Target: 45000.0
- Unit: SAR

**Calculation (Budget Version 2025-2026):**

```python
# Inputs
total_revenue_sar = 55_515_000  # from revenue_plans
total_enrollment = 1234  # from enrollment_plans

# Calculation
calculated_value = total_revenue_sar / total_enrollment
# = 55,515,000 / 1234
# = 44,991.90 SAR

# Store in kpi_values
{
  "calculated_value": 44991.90,
  "calculation_inputs": {
    "total_revenue_sar": 55515000,
    "total_enrollment": 1234,
    "revenue_query": "SELECT SUM(amount_sar) FROM revenue_plans WHERE budget_version_id = ?",
    "enrollment_query": "SELECT SUM(student_count) FROM enrollment_plans WHERE budget_version_id = ?"
  }
}
```

**Comparison to Target:**
- Calculated: 44,991.90 SAR
- Target: 45,000.0 SAR
- Variance: -8.10 SAR (-0.02%)
- Status: Slightly Below Target ⚠️

### Example 3: H/E Ratio Secondary

**KPI Definition:**
- Code: `he_ratio_secondary`
- Formula: `Total DHG Hours ÷ Total Secondary Students`
- Target: 1.35
- Unit: ratio

**Calculation (Budget Version 2025-2026):**

```python
# Inputs
total_dhg_hours = 960.5  # from dhg_subject_hours (Collège + Lycée)
total_secondary_students = 721  # from enrollment_plans (6ème to Terminale)

# Calculation
calculated_value = total_dhg_hours / total_secondary_students
# = 960.5 / 721
# = 1.332

# Store in kpi_values
{
  "calculated_value": 1.332,
  "calculation_inputs": {
    "total_dhg_hours": 960.5,
    "total_secondary_students": 721,
    "levels_included": ["6ème", "5ème", "4ème", "3ème", "2nde", "1ère", "Terminale"],
    "dhg_query": "SELECT SUM(hours_required) FROM dhg_subject_hours WHERE budget_version_id = ? AND level_id IN (...)",
    "enrollment_query": "SELECT SUM(student_count) FROM enrollment_plans WHERE budget_version_id = ? AND level_id IN (...)"
  }
}
```

**Comparison to Target:**
- Calculated: 1.332
- Target: 1.35
- Variance: -0.018 (-1.3%)
- Status: Slightly Below Target ⚠️

## Integration Points

### Upstream Dependencies

1. **budget_versions**: Parent table for version control
2. **enrollment_plans**: Total student counts for ratio calculations
3. **dhg_subject_hours**: Hours data for H/E ratios
4. **dhg_teacher_requirements**: FTE data for staffing ratios
5. **revenue_plans**: Revenue data for financial KPIs
6. **personnel_cost_plans**: Cost data for financial KPIs
7. **operating_cost_plans**: Operating cost data
8. **capex_plans**: Capital expenditure data

### Downstream Dependencies

1. **dashboard_widgets**: KPI values displayed in dashboard widgets
2. **financial_statements**: Some KPIs may appear in statement notes
3. **Reports**: KPI values used in executive reports and analysis

### External Systems

- **Export**: KPI data exported to Excel/PDF reports for stakeholder review
- **AEFE Reporting**: Educational KPIs (H/E ratios, class sizes) reported to AEFE

## API Endpoints (Future Implementation)

### Planned Endpoints (Phase 5-6)

```
GET    /api/v1/kpi-definitions              # List all KPI definitions
GET    /api/v1/kpi-definitions/:id          # Get KPI definition by ID
POST   /api/v1/kpi-definitions              # Create new KPI definition (admin only)
PUT    /api/v1/kpi-definitions/:id          # Update KPI definition (admin only)
DELETE /api/v1/kpi-definitions/:id          # Soft delete KPI definition (admin only)

GET    /api/v1/budget-versions/:id/kpis     # Get all KPI values for a budget version
GET    /api/v1/kpis/:definition_id/history  # Get KPI value history across versions
POST   /api/v1/budget-versions/:id/calculate-kpis  # Trigger KPI recalculation (manager only)
```

## Testing Strategy

### Unit Tests

1. **Model Tests**: Verify SQLAlchemy model definitions and relationships
2. **Constraint Tests**: Test unique constraints, foreign keys, and check constraints
3. **Enum Tests**: Verify KPICategory enum values

### Integration Tests

1. **RLS Policy Tests**: Verify row-level security for all user roles
2. **Cascade Delete Tests**: Ensure proper cascade behavior
3. **Soft Delete Tests**: Verify soft delete functionality

### Test Scenarios

#### Scenario 1: Create KPI Definition

```python
def test_create_kpi_definition():
    """Test creating a new KPI definition."""
    kpi_def = KPIDefinition(
        code="student_teacher_ratio",
        name_en="Student-Teacher Ratio",
        name_fr="Ratio Élèves-Enseignants",
        description_en="Total students divided by total FTE teachers",
        description_fr="Total élèves divisé par total ETP enseignants",
        category=KPICategory.EDUCATIONAL,
        formula_text="Total Students ÷ Total FTE Teachers",
        target_value=Decimal("12.0"),
        unit="ratio",
        display_order=1
    )
    db.session.add(kpi_def)
    db.session.commit()

    assert kpi_def.id is not None
    assert kpi_def.code == "student_teacher_ratio"
    assert kpi_def.is_active is True
```

#### Scenario 2: Calculate and Store KPI Value

```python
def test_calculate_kpi_value():
    """Test calculating and storing a KPI value."""
    # Setup: budget version and KPI definition exist
    budget_version = create_test_budget_version()
    kpi_def = create_test_kpi_definition("student_teacher_ratio")

    # Calculate
    total_students = 1234
    total_fte = 102.8
    calculated_value = Decimal(str(total_students / total_fte))

    # Store
    kpi_value = KPIValue(
        budget_version_id=budget_version.id,
        kpi_definition_id=kpi_def.id,
        calculated_value=calculated_value,
        calculation_inputs={
            "total_students": total_students,
            "total_fte_teachers": total_fte
        }
    )
    db.session.add(kpi_value)
    db.session.commit()

    assert kpi_value.id is not None
    assert kpi_value.calculated_value == Decimal("12.00")
```

#### Scenario 3: Unique Constraint Enforcement

```python
def test_one_kpi_value_per_version():
    """Test that only one KPI value can exist per KPI per version."""
    budget_version = create_test_budget_version()
    kpi_def = create_test_kpi_definition("student_teacher_ratio")

    # Create first KPI value
    kpi_value1 = KPIValue(
        budget_version_id=budget_version.id,
        kpi_definition_id=kpi_def.id,
        calculated_value=Decimal("12.00"),
        calculation_inputs={}
    )
    db.session.add(kpi_value1)
    db.session.commit()

    # Attempt to create duplicate
    kpi_value2 = KPIValue(
        budget_version_id=budget_version.id,
        kpi_definition_id=kpi_def.id,  # Same KPI, same version
        calculated_value=Decimal("12.50"),
        calculation_inputs={}
    )
    db.session.add(kpi_value2)

    with pytest.raises(IntegrityError):
        db.session.commit()
```

#### Scenario 4: RLS Policy - Manager Access

```python
def test_rls_manager_working_version():
    """Test that managers can access KPI values for working versions."""
    # Setup: working budget version with KPI values
    working_version = create_working_budget_version()
    kpi_value = create_test_kpi_value(working_version.id)

    # Simulate manager role
    set_user_role("manager")

    # Manager can read
    result = db.session.query(KPIValue).filter_by(id=kpi_value.id).first()
    assert result is not None

    # Manager can update
    result.calculated_value = Decimal("13.00")
    db.session.commit()

    # Verify update
    refreshed = db.session.query(KPIValue).filter_by(id=kpi_value.id).first()
    assert refreshed.calculated_value == Decimal("13.00")
```

#### Scenario 5: RLS Policy - Viewer Restrictions

```python
def test_rls_viewer_approved_only():
    """Test that viewers can only access approved budget KPI values."""
    # Setup: one working, one approved budget version
    working_version = create_working_budget_version()
    approved_version = create_approved_budget_version()
    kpi_def = create_test_kpi_definition("student_teacher_ratio")

    kpi_working = create_test_kpi_value(working_version.id, kpi_def.id)
    kpi_approved = create_test_kpi_value(approved_version.id, kpi_def.id)

    # Simulate viewer role
    set_user_role("viewer")

    # Viewer cannot see working KPI values
    result_working = db.session.query(KPIValue).filter_by(id=kpi_working.id).first()
    assert result_working is None

    # Viewer can see approved KPI values
    result_approved = db.session.query(KPIValue).filter_by(id=kpi_approved.id).first()
    assert result_approved is not None
```

## Version History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-12-01 | Claude (Phase 4) | Initial database schema implementation: kpi_definitions and kpi_values tables, RLS policies, migration scripts |

## Future Enhancements (Phase 5-6)

1. **KPI Calculation Engine**: Implement business logic to calculate KPIs from source data
2. **Automatic Calculation**: Trigger KPI calculation when budget version is approved
3. **Comparison Reports**: Compare KPI values across budget versions and fiscal years
4. **Trend Analysis**: Show KPI trends over time (5-year view)
5. **Alert System**: Notify managers when KPIs fall outside target ranges
6. **Dashboard Integration**: Display KPIs in real-time dashboards with visualizations
7. **Export to Excel**: Export KPI reports with charts and historical trends
8. **AEFE Integration**: Automatic submission of educational KPIs to AEFE reporting system

## Notes

- **Phase 4 Scope**: This module currently implements only the database foundation (tables, constraints, RLS policies, migration)
- **Business Logic**: KPI calculation logic, API endpoints, and UI will be implemented in Phases 5-6
- **Bilingual Support**: All KPI definitions must support both English and French for EFIR's bilingual environment
- **Historical Tracking**: By linking to budget_versions, the system maintains a complete history of KPI values for trend analysis
- **Audit Compliance**: calculation_inputs JSONB field provides full audit trail for how each KPI was calculated
