# Engine Golden Rules

**Version:** 1.4
**Date:** 2025-12-15
**Scope:** All calculation engines in `/backend/app/engine/`

---

## Overview

These rules define the architectural standards for EFIR Budget Planning calculation engines. All engines MUST comply with these rules. Exceptions require documented approval.

---

## Rule 1: Deterministic Core (Pure Function Engine)

### Principle
The engine must behave like:
```python
outputs = calculate_*(inputs: InputModel) -> OutputModel
```

### Requirements
- **No hidden state** - no reliance on request order, time, randomness, or global mutable variables
- **Same inputs → same outputs** - bit-for-bit identical within the rounding policy
- **Zero side effects** - no DB calls, no file I/O, no network calls, no logging inside compute functions

### Implementation
```python
# CORRECT - Pure function
def calculate_dhg_hours(dhg_input: DHGInput) -> DHGHoursResult:
    # Only uses input data, returns result
    total_hours = Decimal("0")
    for subject in dhg_input.subject_hours_list:
        total_hours += subject.hours_per_week * dhg_input.number_of_classes
    return DHGHoursResult(total_hours=total_hours, ...)

# WRONG - Side effects
def calculate_dhg_hours(dhg_input: DHGInput) -> DHGHoursResult:
    db.log_calculation(...)  # ❌ DB call
    result = ...
    cache.set(key, result)   # ❌ Cache mutation
    return result
```

### Enforcement
- **Directory boundary**: `backend/app/engine/` has ZERO imports from `app/database`, `app/api`, `app/services`
- **CI check**: Static analysis to detect forbidden imports

---

## Rule 2: Numeric Policy (Decimal with Standard Precision)

### Principle
Financial engines fail from inconsistent precision. Use one policy everywhere.

### EFIR Standard Policy

| Type | Storage | Python Type | Precision |
|------|---------|-------------|-----------|
| **Money (SAR)** | Decimal | `Decimal` | 2 decimal places |
| **Money (EUR)** | Decimal | `Decimal` | 2 decimal places |
| **Rates (%)** | Decimal | `Decimal` | 4 decimal places (0.0001 = 0.01%) |
| **FTE** | Decimal | `Decimal` | 2 decimal places |
| **Hours** | Decimal | `Decimal` | 2 decimal places |
| **Counts (students, classes)** | Integer | `int` | Exact |

### Rounding Helper
```python
from decimal import Decimal, ROUND_HALF_UP

def quantize_money(value: Decimal) -> Decimal:
    """Standard money rounding to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

def quantize_rate(value: Decimal) -> Decimal:
    """Standard rate rounding to 4 decimal places."""
    return value.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

def quantize_fte(value: Decimal) -> Decimal:
    """Standard FTE rounding to 2 decimal places."""
    return value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
```

### Forbidden
- ❌ **NEVER use `float` for money** - precision loss
- ❌ **NEVER mix `float` and `Decimal`** - implicit conversion errors
- ❌ **NEVER use different rounding modes** without explicit justification

### Enforcement
- Type hints: `Decimal` for all financial fields
- Pydantic validators: `ge=Decimal("0")` not `ge=0`
- Code review: Flag any `float` in engine code

---

## Rule 3: Version Awareness (Aligned with DB Golden Rules)

### Principle
All calculations are scoped to a specific **version**. The version provides:
- Fiscal year context
- School year mapping
- Locked/editable state
- Historical comparison baseline
- Scenario type (ACTUAL, BUDGET, FORECAST, STRATEGIC, WHAT_IF)

### Alignment with DB Golden Rules
Per **DB_golden_rules.md Section 2.6**, the table has been **renamed to `settings_versions`** and uses `version_id` as the FK column name.

| Old Name | New Name | Notes |
|----------|----------|-------|
| `budget_versions` | `settings_versions` | Table renamed in Phase 3B |
| `budget_version_id` | `version_id` | FK column renamed |

### Requirements
```python
# Every engine input should be traceable to a version
class EnrollmentInput(BaseModel):
    version_id: UUID | None  # Required for production, optional for unit tests
    fiscal_year: int          # e.g., 2026
    # ... other fields
```

### Fiscal Year Proration
EFIR uses fiscal years (Jan-Dec) but school years (Sep-Aug):
```
Fiscal Year 2026 =
    School Year 2025-2026 (Jan-Aug 2026): 8 months weight
  + School Year 2026-2027 (Sep-Dec 2026): 4 months weight

Weighted enrollment = (SY_2025_26 × 8 + SY_2026_27 × 4) / 12
```

### Enforcement
- All API endpoints require `version_id` parameter
- Engine functions accept fiscal year or school year explicitly

---

## Rule 4: Time Axis Consistency

### Principle
One canonical timeline, aligned across all calculations.

### EFIR Time Axis
```python
# Standard projection horizon
START_YEAR = 2024
END_YEAR = 2034  # 10-year projection (expandable to 30)
YEARS = list(range(START_YEAR, END_YEAR + 1))

# Index helper
def year_to_index(year: int) -> int:
    """Convert year to array index."""
    if year < START_YEAR or year > END_YEAR:
        raise ValueError(f"Year {year} outside projection horizon")
    return year - START_YEAR

# All schedules return arrays aligned to this axis
def get_cpi_factors() -> list[Decimal]:
    """Returns CPI factors for each year in YEARS."""
    return [Decimal("1.00"), Decimal("1.02"), ...]  # len = len(YEARS)
```

### Requirements
- Multi-year projections return `list[YearResult]` aligned to `YEARS`
- Single-year calculations specify the year explicitly
- No year-specific logic scattered in code - centralize in `time_axis.py`

---

## Rule 5: Dependency Graph (DAG)

### Principle
Structure calculations as a Directed Acyclic Graph:
```
Enrollment → Class Structure → DHG Hours → Teacher FTE → Personnel Costs
                                                              ↓
Revenue ←──────────────────────────────────────────── Budget Consolidation
                                                              ↓
                                                      Financial Statements → KPIs
```

### Requirements

1. **Explicit dependencies**: Each engine declares what it needs
   ```python
   # In dhg/calculator.py
   DEPENDS_ON = ["enrollment", "class_structure"]
   PRODUCES = ["dhg_hours", "teacher_fte"]
   ```

2. **No reverse dependencies**: Lower-level engines never import from higher-level
   - ✅ `dhg` can import from `enrollment`
   - ❌ `enrollment` cannot import from `dhg`

3. **Cache invalidation follows the graph**:
   - Change enrollment → invalidate class_structure, dhg, personnel_costs, consolidation
   - Change fee structure → invalidate revenue, consolidation only

### Enforcement
- Import linter to verify no reverse dependencies
- Redis cache keys include dependency version hashes

---

## Rule 6: Pydantic I/O Models (Type Safety)

### Principle
Every engine function uses Pydantic models for inputs and outputs.

### Standard Pattern
```python
from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from uuid import UUID

class DHGInput(BaseModel):
    """Input for DHG calculation."""
    level_id: UUID
    level_code: str
    number_of_classes: int = Field(..., ge=0, le=50)
    subject_hours_list: list[SubjectHours]

    model_config = ConfigDict(
        frozen=True,  # Immutable after creation
        validate_assignment=True,
    )

class DHGResult(BaseModel):
    """Output from DHG calculation."""
    total_hours: Decimal
    subject_breakdown: dict[str, Decimal]
    # ... validation info
```

### Requirements
- ✅ Use `ConfigDict()` (Pydantic v2), not `class Config:` (v1)
- ✅ All fields have `Field(...)` with description
- ✅ Use `frozen=True` for immutable results
- ✅ Include `json_schema_extra` with examples

---

## Rule 7: Validation Layer

### Principle
Separate validation from calculation. Validate early, fail fast.

### Standard Pattern
```python
# validators.py
class InvalidDHGInputError(ValueError):
    """Raised when DHG input validation fails."""
    pass

def validate_dhg_input(input: DHGInput) -> None:
    """Validate input before calculation. Raises on failure."""
    if input.number_of_classes > 50:
        raise InvalidDHGInputError(
            f"Number of classes must be ≤ 50, got {input.number_of_classes}"
        )
    # ... more validations

# calculator.py
def calculate_dhg_hours(input: DHGInput) -> DHGResult:
    validate_dhg_input(input)  # Fail fast
    # ... calculation logic
```

### Validation Categories
1. **Structural**: Field types, required fields (handled by Pydantic)
2. **Business rules**: Cross-field constraints, domain limits
3. **Sanity checks**: Unreasonable values (salary > 1M SAR)

---

## Rule 8: Auditability (Calculation Lineage)

### Principle
Every output should be traceable. Auditors need to understand how numbers were derived.

### Requirements
```python
class KPIResult(BaseModel):
    # The calculated value
    value: Decimal

    # Audit metadata
    calculation_breakdown: str | None = Field(
        None,
        description="Human-readable calculation explanation"
    )
    formula_used: str | None = Field(
        None,
        description="Formula name or reference"
    )
    input_hash: str | None = Field(
        None,
        description="Hash of inputs for reproducibility"
    )
```

### Example Breakdown
```
Service: 5y 11m = 5.92 years
Years 1-5: 0.5 × SAR 10,000 × 5.00 = SAR 25,000.00
Years 6+: 1.0 × SAR 10,000 × 0.92 = SAR 9,166.67
Gross EOS: SAR 34,166.67
Resignation factor (5-10yr): 67%
Final EOS: SAR 22,891.67
```

### Enforcement
- Major calculations MUST include `calculation_breakdown`
- Financial statements include account code references

---

## Rule 9: Testing Invariants

### Principle
Financial models have mathematical truths that must always hold.

### Required Invariants

1. **Balance Sheet Balance**
   ```python
   def test_balance_sheet_balances():
       assert abs(total_assets - (total_liabilities + total_equity)) < Decimal("0.01")
   ```

2. **Cash Flow Reconciliation**
   ```python
   def test_cash_reconciles():
       calculated_closing = opening_cash + net_cash_flow
       assert abs(calculated_closing - bs_cash) < Decimal("0.01")
   ```

3. **Roll-Forward Consistency** (debt, depreciation, provisions)
   ```python
   def test_debt_rollforward():
       calculated = opening + additions - repayments
       assert abs(calculated - closing) < Decimal("0.01")
   ```

4. **Revenue = Students × Fees** (with discounts)
   ```python
   def test_revenue_ties():
       calculated = sum(student.net_tuition for student in students)
       assert abs(calculated - total_tuition_revenue) < Decimal("0.01")
   ```

### Golden Master Tests
- Snapshot a known-good calculation
- Fail if outputs change unexpectedly
- Update snapshots explicitly with review

---

## Rule 10: Module Structure

### Standard Engine Directory
```
engine/
├── __init__.py          # Public exports only
├── models.py            # Pydantic I/O models
├── calculator.py        # Pure calculation functions
├── validators.py        # Validation functions + exceptions
└── constants.py         # Domain constants (rates, limits)
```

### Standard Function Pattern
```python
def calculate_*(inputs: InputModel) -> OutputModel:
    """
    [One-line description].

    Formula:
        [Mathematical formula]

    Args:
        inputs: [Description]

    Returns:
        [Description]

    Raises:
        Invalid*Error: If validation fails

    Example:
        >>> result = calculate_*(InputModel(...))
        >>> result.value
        Decimal('123.45')
    """
    # 1. Validate
    validate_*(inputs)

    # 2. Calculate
    result = ...

    # 3. Return (no side effects)
    return OutputModel(...)
```

---

## Rule 11: No Circular Dependencies

### Principle
The calculation graph must be acyclic. If circularity exists (e.g., cash ↔ interest), isolate it.

### Current Status
EFIR has NO circular dependencies. The flow is linear:
```
Enrollment → Class Structure → DHG → Personnel Costs → Revenue → Consolidation → Statements → KPIs
```

### If Circularity Is Needed (Future)
```python
def converge_cash_interest(
    initial_cash: Decimal,
    interest_rate: Decimal,
    max_iterations: int = 10,
    tolerance: Decimal = Decimal("0.01"),
) -> ConvergenceResult:
    """Iterate until cash and interest stabilize."""
    for iteration in range(max_iterations):
        new_cash = calculate_cash(interest)
        new_interest = calculate_interest(new_cash)
        residual = abs(new_cash - previous_cash)
        if residual < tolerance:
            return ConvergenceResult(
                converged=True,
                iterations=iteration,
                residual=residual,
                cash=new_cash,
            )
    # Did not converge - this is an error
    raise ConvergenceError(f"Did not converge after {max_iterations} iterations")
```

---

## Rule 12: Performance Awareness

### Principle
Set expectations, measure, and prevent regressions.

### EFIR Performance Budgets

| Operation | Target | Max |
|-----------|--------|-----|
| Single-year enrollment projection | < 50ms | 200ms |
| Full DHG calculation (all levels) | < 100ms | 500ms |
| Complete budget consolidation | < 500ms | 2s |
| All KPIs | < 100ms | 500ms |

### Requirements
- **No N+1 patterns**: Bulk operations, not per-item loops with DB calls
- **Cache expensive schedules**: CPI factors, depreciation tables
- **Profile before optimizing**: Use `cProfile`, not guesses

### Enforcement (Future)
- CI performance tests for critical paths
- Alert on regression > 20%

---

## Rule 13: Multi-Currency Support (SAR/EUR)

### Principle
EFIR operates in SAR but has EUR costs (AEFE contributions).

### Requirements
```python
class MoneyAmount(BaseModel):
    amount: Decimal
    currency: Literal["SAR", "EUR"]

class CurrencyConversion(BaseModel):
    from_currency: Literal["SAR", "EUR"]
    to_currency: Literal["SAR", "EUR"]
    rate: Decimal  # e.g., 4.05 SAR/EUR
    rate_date: date
```

### Rules
- Store amounts with explicit currency
- Convert at consolidation time, not calculation time
- Use rate from budget version (locked at version approval)
- Document conversion in audit trail

---

## Rule 14: Module-Engine Ownership

### Principle
Each calculation engine is owned by exactly ONE module. Cross-module calculations flow through services, not direct engine imports. This aligns with the 6-module architecture defined in DB_golden_rules.md Section 9.

### Module-Engine Ownership Table

> **Note**: All tables are in the `efir_budget` schema. The table prefix indicates module ownership.

| Module | Owned Engines | Table Prefix | Primary Role |
|--------|---------------|--------------|--------------|
| **Students** | `enrollment/`, `calibration/` | `students_*` | Academic Director |
| **Teachers** | `dhg/`, `eos/`, `gosi/` | `teachers_*` | HR Manager |
| **Finance** | `revenue/`, `costs/`, `financial_statements/` | `finance_*` | Finance Director |
| **Insights** | `kpi/`, `variance/` | `insights_*` | All (read) |
| **Settings** | (none - reference data only) | `settings_*`, `ref_*` | All (limited) |
| **Admin** | (none - system operations only) | `admin_*` | Admin only |

### Engine Directory Structure (Aligned with Modules)

```
engine/
├── students/                    # Students Module
│   ├── enrollment/              # Enrollment projections
│   │   ├── projection_engine.py
│   │   ├── calibration_engine.py
│   │   └── lateral_optimizer.py
│   └── class_structure/         # Class formation (future)
│
├── teachers/                    # Teachers Module
│   ├── dhg/                     # DHG hours calculation
│   ├── eos/                     # End of Service
│   └── gosi/                    # GOSI contributions
│
├── finance/                     # Finance Module
│   ├── revenue/                 # Revenue calculations
│   ├── costs/                   # Cost calculations (future)
│   └── financial_statements/    # PCG/IFRS statements
│
├── insights/                    # Insights Module
│   ├── kpi/                     # KPI calculations
│   └── variance/                # Variance analysis (future)
│
└── shared/                      # Shared utilities (no module ownership)
    ├── time_axis.py
    ├── quantize.py
    └── currency.py
```

### Module Isolation Rules

| Rule | Requirement |
|------|-------------|
| **MUST** | Each engine folder is owned by exactly one module |
| **MUST** | Engines NEVER import from engines in other modules |
| **MUST** | Engines NEVER access database tables from other modules |
| **MUST NOT** | Have implicit dependencies on other engines |
| **MAY** | Receive data from other modules via input parameters (service layer) |
| **MAY** | Return outputs consumed by engines in other modules (service layer) |

### Cross-Module Data Flow

Data flows between modules through the **service layer**, not direct engine imports:

```python
# CORRECT - Service layer orchestrates
class ConsolidationService:
    def consolidate_budget(self, version_id: UUID) -> ConsolidationResult:
        # 1. Get enrollment data from Students module
        enrollment = self.enrollment_service.get_projections(version_id)

        # 2. Get DHG data from Teachers module
        dhg = self.dhg_service.get_requirements(version_id)

        # 3. Calculate revenue (Finance module engine)
        revenue = calculate_revenue(enrollment)

        # 4. Calculate costs (Finance module engine)
        costs = calculate_personnel_costs(dhg)

        # 5. Return consolidated result
        return ConsolidationResult(revenue=revenue, costs=costs)

# WRONG - Direct cross-module engine import
from engine.students.enrollment import calculate_projections  # ❌ Cross-module
from engine.finance.revenue import calculate_revenue
```

### Enforcement

- **Import linter**: CI check to verify no cross-module engine imports
- **Directory structure**: Physical separation by module
- **Code review**: Flag any engine importing from another module's engine folder

---

## Appendix: Compliance Checklist

When reviewing or creating an engine, verify:

- [ ] Pure functions - no DB/API imports
- [ ] Pydantic v2 models with `ConfigDict`
- [ ] All `Decimal`, no `float` for money
- [ ] Standard quantization helpers used
- [ ] Validators in separate file
- [ ] All public functions exported in `__all__`
- [ ] Docstrings with formula and example
- [ ] `calculation_breakdown` for major outputs
- [ ] Unit tests with invariants
- [ ] No reverse dependencies (DAG structure)

---

## Appendix B: Enrollment Engine Cleanup (Required)

### Background

The enrollment engine (`backend/app/engine/enrollment/`) currently contains a **dual system**:

1. **Legacy System** (TO BE REMOVED):
   - `models.py` - Simple compound growth models with Pydantic v1 style
   - `calculator.py` - Basic compound growth projection

2. **New Cohort-Based System** (TO KEEP):
   - `projection_models.py` - 4-layer override system with retention + lateral entry
   - `projection_engine.py` - Cohort progression engine with capacity constraints
   - `calibration_engine.py` - Weighted historical analysis (70/30)
   - `lateral_optimizer.py` - Capacity-aware lateral entry optimization
   - `optimizer_models.py` - Optimization decision models

**Decision**: Remove the legacy system, keep only the new cohort-based system.

### B.1 Files to Remove (Legacy System)

| File | Lines | Reason |
|------|-------|--------|
| `models.py` | 202 | Legacy compound growth models using Pydantic v1 (`class Config:`) |
| `calculator.py` | 225 | Simple `(1 + rate)^years` growth - superseded by cohort progression |

**Total**: ~427 lines of legacy code to remove.

### B.2 Files to Keep and Fix

| File | Lines | Status | Required Fixes |
|------|-------|--------|----------------|
| `projection_models.py` | 260 | ✅ Keep | Remove deprecated fields (lines 98-108) |
| `projection_engine.py` | 521 | ✅ Keep | Fix float precision (lines 213-214, 356) |
| `calibration_engine.py` | 374 | ✅ Keep | Clean - no issues |
| `lateral_optimizer.py` | 540 | ✅ Keep | Fix float precision (lines 189-190) |
| `optimizer_models.py` | 316 | ✅ Keep | Remove dead code (OptimizationMode enum, lines 57-72) |
| `validators.py` | 227 | ✅ Keep | Clean - but references legacy models (update imports) |
| `fiscal_year_proration.py` | 82 | ✅ Keep | Clean - no issues |
| `__init__.py` | 143 | ✅ Keep | Update exports after cleanup |

### B.3 Float Precision Fixes (Rule 2 Violations)

**Critical**: These lines use `float()` cast on `Decimal` values, violating Rule 2.

#### File: `projection_engine.py`

**Line 213-214** (in `_calculate_grade_with_lateral`):
```python
# BEFORE (WRONG):
lateral = int(prev_enrollment * float(lateral_rate))

# AFTER (CORRECT):
lateral = int(prev_enrollment * lateral_rate)  # Decimal arithmetic
```

**Line 356** (in `_project_grade_cohort_progression`):
```python
# BEFORE (WRONG):
retained = int(prev_enrollment * float(retention))

# AFTER (CORRECT):
retained = int(prev_enrollment * retention)  # Decimal arithmetic
```

#### File: `lateral_optimizer.py`

**Line 189-190** (in `_apply_multiplier`):
```python
# BEFORE (WRONG):
return int(base * float(lateral_multiplier))

# AFTER (CORRECT):
return int(base * lateral_multiplier)  # Decimal arithmetic
```

### B.4 Deprecated Fields to Remove

#### File: `projection_models.py` (lines 98-108)

```python
# REMOVE these deprecated fields from EngineEffectiveRates:
lateral_entry_fixed: int | None = Field(
    default=None,
    ge=0,
    le=100,
    description="DEPRECATED: Fixed lateral entry count. Use lateral_entry_rate instead.",
)
is_percentage_based: bool = Field(
    default=True,
    description="DEPRECATED: Always True. All grades now use percentage-based lateral.",
)
```

**Reason**: All grades now use percentage-based lateral entry (unified model). These fields are remnants of the old mixed model.

### B.5 Dead Code to Remove

#### File: `optimizer_models.py` (lines 57-72)

```python
# REMOVE this unused enum:
class OptimizationMode(str, Enum):
    """
    Optimization strategy mode.
    Future enhancement: Allow users to choose between different strategies.
    """
    BALANCED = "balanced"
    MINIMIZE_REJECTIONS = "minimize_rejections"
    MAXIMIZE_EFFICIENCY = "maximize_efficiency"
```

**Reason**: This enum is defined but **never used** anywhere in the codebase. It was planned for future enhancement but never implemented.

### B.6 DB Golden Rules Alignment

Per **DB_golden_rules.md Section 8.6**, the enrollment module has specific requirements:

#### Input/Output Table Classification

| Table Type | Tables | Engine Responsibility |
|------------|--------|----------------------|
| **INPUT** | `enrollment_configs`, `enrollment_data`, `enrollment_overrides`, `enrollment_calibration` | Read-only (services fetch, engines use) |
| **OUTPUT** | `enrollment_projections`, `class_structures` | Engine produces (services persist) |

#### Required Lineage Columns for Engine Outputs

All engine output models should include lineage fields that map to DB columns:

```python
class ProjectionResult(BaseModel):
    # ... calculation results ...

    # Lineage (NEW - align with DB OUTPUT table requirements)
    version_id: UUID | None = None       # FK to versions table
    fiscal_year: int                      # Year this data represents
    computed_at: datetime | None = None   # When calculation ran
    computed_by: UUID | None = None       # User/job that triggered
    run_id: UUID | None = None            # To group related computations
    inputs_hash: str | None = None        # SHA256 of inputs for reproducibility
```

**Current Gap**: `ProjectionResult` in `projection_models.py` is missing these lineage fields.

#### Version ID Alignment

Per Rule 3 update, use `version_id` instead of `budget_version_id`:

| Location | Current | Required |
|----------|---------|----------|
| `ProjectionInput` | Missing | Add `version_id: UUID \| None` |
| `GradeProjection` | Missing | Add `version_id: UUID \| None` in result |
| `ProjectionResult` | Missing | Add lineage columns |

### B.7 Update `__init__.py` After Cleanup

After removing legacy files, update `backend/app/engine/enrollment/__init__.py`:

```python
# REMOVE these legacy exports:
from app.engine.enrollment.models import (
    EnrollmentGrowthScenario,  # REMOVE
    EnrollmentInput,           # REMOVE
    EnrollmentProjection,      # REMOVE
    EnrollmentProjectionResult,# REMOVE
    RetentionModel,            # REMOVE
)
from app.engine.enrollment.calculator import (
    calculate_enrollment_projection,  # REMOVE
    apply_retention_model,            # REMOVE
    calculate_attrition,              # REMOVE
)

# Update validators.py to remove legacy model imports
```

### B.8 Migration Checklist

| Priority | Task | File | Status |
|----------|------|------|--------|
| P0 | Delete `models.py` | models.py | ⏳ Pending |
| P0 | Delete `calculator.py` | calculator.py | ⏳ Pending |
| P1 | Fix float precision (3 locations) | projection_engine.py, lateral_optimizer.py | ⏳ Pending |
| P1 | Remove deprecated fields | projection_models.py:98-108 | ⏳ Pending |
| P1 | Remove dead OptimizationMode enum | optimizer_models.py:57-72 | ⏳ Pending |
| P2 | Add lineage fields to ProjectionResult | projection_models.py | ⏳ Pending |
| P2 | Add version_id to ProjectionInput | projection_models.py | ⏳ Pending |
| P2 | Update __init__.py exports | __init__.py | ⏳ Pending |
| P3 | Update validators.py imports | validators.py | ⏳ Pending |
| P3 | Update tests to remove legacy model tests | tests/engine/test_enrollment_projection.py | ⏳ Pending |

### B.9 Test Impact

After cleanup, the following test changes are required:

| Test File | Action |
|-----------|--------|
| `tests/engine/test_enrollment_projection.py` | Remove tests for legacy `calculate_enrollment_projection` |
| `tests/engine/test_calibration_engine.py` | No changes needed |
| `tests/engine/test_lateral_optimizer.py` | No changes needed |

---

## Appendix C: Golden Rules Compliance Matrix (Enrollment Engine)

| Rule | Status | Notes |
|------|--------|-------|
| **1. Deterministic Core** | ✅ Compliant | All projection functions are pure |
| **2. Numeric Policy** | ⚠️ 3 Violations | Float casts in 3 locations (see B.3) |
| **3. Version Awareness** | ⚠️ Missing | version_id not in input/output models |
| **4. Time Axis Consistency** | ✅ Compliant | Uses fiscal_year throughout |
| **5. Dependency Graph** | ✅ Compliant | No circular dependencies |
| **6. Pydantic I/O** | ⚠️ Mixed | New models use v2, legacy uses v1 |
| **7. Validation Layer** | ✅ Compliant | Validators in separate file |
| **8. Auditability** | ⚠️ Missing | calculation_breakdown not in outputs |
| **9. Testing Invariants** | ✅ Compliant | Has property-based tests |
| **10. Module Structure** | ✅ Compliant | Standard structure |
| **11. No Circular Deps** | ✅ Compliant | Linear flow |
| **12. Performance** | ✅ Compliant | <50ms typical |
| **13. Multi-Currency** | N/A | Enrollment is currency-free |

---

## Appendix D: DHG Engine Cleanup (Required)

### Overview

The DHG (Dotation Horaire Globale) engine calculates teaching hours allocation and teacher FTE requirements for the French education system.

**Files**: `backend/app/engine/dhg/`
- `models.py` (282 lines)
- `calculator.py` (415 lines)
- `validators.py` (424 lines)

### D.1 Pydantic v1 to v2 Migration

**File: `models.py`**

| Model | Line | Issue | Fix |
|-------|------|-------|-----|
| `FTECalculationResult` | ~189 | Uses `class Config:` | Migrate to `model_config = ConfigDict(...)` |
| `TeacherRequirement` | ~164 | Uses `class Config:` | Migrate to `model_config = ConfigDict(...)` |
| `HSAAllocation` | ~220 | Uses `class Config:` | Migrate to `model_config = ConfigDict(...)` |

**Critical Issue**: `TRMDGapResult` at line ~158 uses `@dataclass` instead of Pydantic:
```python
# BEFORE (WRONG):
@dataclass
class TRMDGapResult:
    subject_code: str
    ...

# AFTER (CORRECT):
class TRMDGapResult(BaseModel):
    subject_code: str
    ...
    model_config = ConfigDict(frozen=True)
```

### D.2 Version ID Alignment

Per Rule 3, add `version_id` to input/output models:

| Model | Current | Required |
|-------|---------|----------|
| `DHGInput` | Missing | Add `version_id: UUID \| None = None` |
| `DHGHoursResult` | Missing | Add `version_id: UUID \| None = None` |
| `FTECalculationResult` | Missing | Add lineage columns |

### D.3 Auditability Enhancement

DHG outputs should include `calculation_breakdown` for audit purposes:
```python
class FTECalculationResult(BaseModel):
    # ... existing fields ...

    # ADD for auditability:
    calculation_breakdown: str | None = Field(
        None,
        description="Human-readable breakdown of FTE calculation"
    )
```

### D.4 Compliance Status

| Rule | Status | Notes |
|------|--------|-------|
| 1. Deterministic Core | ✅ Compliant | Pure functions |
| 2. Numeric Policy | ✅ Compliant | Uses Decimal throughout |
| 3. Version Awareness | ⚠️ Missing | No version_id |
| 6. Pydantic I/O | ⚠️ Mixed | `class Config:` + `@dataclass` |
| 8. Auditability | ⚠️ Missing | No calculation_breakdown |

### D.5 Migration Checklist

| Priority | Task | Status |
|----------|------|--------|
| P1 | Convert `@dataclass TRMDGapResult` to Pydantic | ⏳ Pending |
| P1 | Migrate 3 models from `class Config:` to `ConfigDict` | ⏳ Pending |
| P2 | Add `version_id` to input/output models | ⏳ Pending |
| P2 | Add `calculation_breakdown` to FTECalculationResult | ⏳ Pending |

---

## Appendix E: EOS Engine Status (Mostly Compliant)

### Overview

The EOS (End of Service) engine implements KSA Labor Law Article 84-85 for gratuity calculations. This engine is **mostly compliant** with the Golden Rules.

**Files**: `backend/app/engine/eos/`
- `models.py` (161 lines)
- `calculator.py` (305 lines)
- `validators.py` (84 lines)

### E.1 Strengths (Exemplary)

1. **Auditability** ✅: `EOSResult` includes `calculation_breakdown` (line 100):
   ```python
   calculation_breakdown: str = Field(
       ...,
       description="Human-readable calculation explanation",
   )
   ```

2. **Pydantic v2 Compatible**: Uses `model_config = {...}` dict style (compatible with both v1 and v2)

3. **Decimal Precision** ✅: Uses `ROUND_HALF_UP` consistently

4. **Human-Readable Output**: Produces detailed breakdown:
   ```
   Service: 5y 11m = 5.92 years
   Years 1-5: 0.5 × SAR 10,000 × 5.00 = SAR 25,000.00
   Years 6+: 1.0 × SAR 10,000 × 0.92 = SAR 9,166.67
   Gross EOS: SAR 34,166.67
   Resignation factor (5-10yr): 67%
   Final EOS: SAR 22,891.67
   ```

### E.2 Required Fixes

**Version ID Alignment**:
| Model | Current | Required |
|-------|---------|----------|
| `EOSInput` | Missing | Add `version_id: UUID \| None = None` |
| `EOSResult` | Missing | Add `version_id: UUID \| None = None` |
| `EOSProvisionInput` | Missing | Add `version_id: UUID \| None = None` |

### E.3 Compliance Status

| Rule | Status | Notes |
|------|--------|-------|
| 1. Deterministic Core | ✅ Compliant | Pure functions |
| 2. Numeric Policy | ✅ Compliant | Decimal + ROUND_HALF_UP |
| 3. Version Awareness | ⚠️ Missing | No version_id |
| 6. Pydantic I/O | ✅ Compliant | v2-compatible dict style |
| 8. Auditability | ✅ Exemplary | Detailed calculation_breakdown |

### E.4 Migration Checklist

| Priority | Task | Status |
|----------|------|--------|
| P2 | Add `version_id` to input/output models | ⏳ Pending |

**Note**: EOS engine should be used as a **reference implementation** for other engines, especially for auditability patterns.

---

## Appendix F: GOSI Engine Cleanup (Required)

### Overview

The GOSI (General Organization for Social Insurance) engine calculates Saudi social insurance contributions (21.5% Saudi, 2% expatriate).

**Files**: `backend/app/engine/gosi/`
- `models.py` (166 lines)
- `calculator.py` (113 lines)
- `validators.py` (45 lines)

### F.1 Pydantic Status

Uses `model_config = {...}` dict style - **compatible with Pydantic v2**.

### F.2 Required Fixes

**Version ID Alignment**:
| Model | Current | Required |
|-------|---------|----------|
| `GOSIInput` | Missing | Add `version_id: UUID \| None = None` |
| `GOSIResult` | Missing | Add `version_id: UUID \| None = None` |

**Auditability Enhancement**:
```python
class GOSIResult(BaseModel):
    # ... existing fields ...

    # ADD for auditability:
    calculation_breakdown: str | None = Field(
        None,
        description="Human-readable breakdown of GOSI calculation"
    )
```

### F.3 Compliance Status

| Rule | Status | Notes |
|------|--------|-------|
| 1. Deterministic Core | ✅ Compliant | Pure functions |
| 2. Numeric Policy | ✅ Compliant | Uses Decimal with quantize |
| 3. Version Awareness | ⚠️ Missing | No version_id |
| 6. Pydantic I/O | ✅ Compliant | v2-compatible dict style |
| 8. Auditability | ⚠️ Missing | No calculation_breakdown |

### F.4 Migration Checklist

| Priority | Task | Status |
|----------|------|--------|
| P2 | Add `version_id` to input/output models | ⏳ Pending |
| P2 | Add `calculation_breakdown` to GOSIResult | ⏳ Pending |

---

## Appendix G: Revenue Engine Cleanup (Required)

### Overview

The Revenue engine calculates tuition revenue with fee structures, sibling discounts, and nationality-based pricing.

**Files**: `backend/app/engine/revenue/`
- `models.py` (258 lines)
- `calculator.py` (416 lines)
- `validators.py` (355 lines)

### G.1 Pydantic v1 to v2 Migration

**File: `models.py`**

| Model | Line | Issue | Fix |
|-------|------|-------|-----|
| `StudentRevenueResult` | ~229 | Uses `class Config:` | Migrate to `model_config = ConfigDict(...)` |

```python
# BEFORE (WRONG):
class StudentRevenueResult(BaseModel):
    ...
    class Config:
        frozen = True

# AFTER (CORRECT):
class StudentRevenueResult(BaseModel):
    ...
    model_config = ConfigDict(frozen=True)
```

### G.2 Version ID Alignment

| Model | Current | Required |
|-------|---------|----------|
| `RevenueInput` | Missing | Add `version_id: UUID \| None = None` |
| `StudentRevenueResult` | Missing | Add `version_id: UUID \| None = None` |
| `RevenueProjectionResult` | Missing | Add lineage columns |

### G.3 Auditability Enhancement

Revenue calculations should include breakdown showing fee components:
```python
class StudentRevenueResult(BaseModel):
    # ... existing fields ...

    # ADD for auditability:
    calculation_breakdown: str | None = Field(
        None,
        description="Breakdown showing base tuition, discounts, net amount"
    )
```

### G.4 Compliance Status

| Rule | Status | Notes |
|------|--------|-------|
| 1. Deterministic Core | ✅ Compliant | Pure functions |
| 2. Numeric Policy | ✅ Compliant | Uses Decimal throughout |
| 3. Version Awareness | ⚠️ Missing | No version_id |
| 6. Pydantic I/O | ⚠️ Mixed | `class Config:` in StudentRevenueResult |
| 8. Auditability | ⚠️ Missing | No calculation_breakdown |
| 13. Multi-Currency | ✅ Compliant | SAR-only, appropriate for revenue |

### G.5 Migration Checklist

| Priority | Task | Status |
|----------|------|--------|
| P1 | Migrate `StudentRevenueResult` to `ConfigDict` | ⏳ Pending |
| P2 | Add `version_id` to input/output models | ⏳ Pending |
| P2 | Add `calculation_breakdown` to StudentRevenueResult | ⏳ Pending |

---

## Appendix H: KPI Engine Cleanup (Required)

### Overview

The KPI engine calculates key performance indicators (H/E, E/D, cost ratios, etc.) for budget analysis.

**Files**: `backend/app/engine/kpi/`
- `models.py` (220 lines)
- `calculator.py` (526 lines)
- `validators.py` (332 lines)

### H.1 Pydantic v1 to v2 Migration

**File: `models.py`**

Multiple models use `class Config:` pattern:

| Model | Issue | Fix |
|-------|-------|-----|
| Various KPI output models | Uses `class Config:` | Migrate to `model_config = ConfigDict(...)` |

### H.2 Version ID Alignment (Critical)

**Current Issue**: Uses `budget_id` instead of `version_id`:
```python
# BEFORE (WRONG):
class KPIInput(BaseModel):
    budget_id: UUID  # ❌ Wrong field name

# AFTER (CORRECT):
class KPIInput(BaseModel):
    version_id: UUID  # ✅ Aligned with DB Golden Rules
```

### H.3 Compliance Status

| Rule | Status | Notes |
|------|--------|-------|
| 1. Deterministic Core | ✅ Compliant | Pure functions |
| 2. Numeric Policy | ✅ Compliant | Uses Decimal throughout |
| 3. Version Awareness | ⚠️ Wrong Name | Has `budget_id` instead of `version_id` |
| 6. Pydantic I/O | ⚠️ Mixed | `class Config:` in some models |
| 8. Auditability | ⚠️ Partial | Some KPIs have formula, not all |

### H.4 Migration Checklist

| Priority | Task | Status |
|----------|------|--------|
| P0 | Rename `budget_id` to `version_id` | ⏳ Pending |
| P1 | Migrate models from `class Config:` to `ConfigDict` | ⏳ Pending |
| P2 | Add `calculation_breakdown` to all KPI outputs | ⏳ Pending |

---

## Appendix I: Financial Statements Engine Cleanup (Required)

### Overview

The Financial Statements engine generates PCG (Plan Comptable Général) and IFRS-format financial statements.

**Files**: `backend/app/engine/financial_statements/`
- `models.py` (279 lines)
- `calculator.py` (789 lines)
- `validators.py` (384 lines)

### I.1 Pydantic v1 to v2 Migration (Critical)

**File: `models.py`** - Uses `class Config:` extensively (9 models):

| Model | Line | Issue |
|-------|------|-------|
| `AccountMapping` | ~45 | `class Config:` |
| `StatementLine` | ~72 | `class Config:` |
| `BalanceSheet` | ~98 | `class Config:` |
| `IncomeStatement` | ~125 | `class Config:` |
| `CashFlowStatement` | ~152 | `class Config:` |
| `FinancialStatementSet` | ~180 | `class Config:` |
| `StatementInput` | ~210 | `class Config:` |
| `StatementOutput` | ~238 | `class Config:` |
| `ConsolidatedStatements` | ~265 | `class Config:` |

All need migration to `model_config = ConfigDict(...)`.

### I.2 Version ID Alignment (Critical)

**Current Issue**: Uses `budget_version_id` instead of `version_id`:
```python
# BEFORE (WRONG):
class StatementInput(BaseModel):
    budget_version_id: UUID  # ❌ Old naming convention

# AFTER (CORRECT):
class StatementInput(BaseModel):
    version_id: UUID  # ✅ Aligned with DB Golden Rules
```

### I.3 Auditability

Financial statements should include account code references and calculation trails for audit compliance.

### I.4 Compliance Status

| Rule | Status | Notes |
|------|--------|-------|
| 1. Deterministic Core | ✅ Compliant | Pure functions |
| 2. Numeric Policy | ✅ Compliant | Uses Decimal throughout |
| 3. Version Awareness | ⚠️ Wrong Name | Has `budget_version_id` instead of `version_id` |
| 6. Pydantic I/O | ❌ Non-compliant | 9 models use `class Config:` |
| 8. Auditability | ⚠️ Partial | Has account codes but limited breakdown |
| 9. Testing Invariants | ✅ Compliant | Balance sheet balancing tests |

### I.5 Migration Checklist

| Priority | Task | Status |
|----------|------|--------|
| P0 | Rename `budget_version_id` to `version_id` | ⏳ Pending |
| P0 | Migrate 9 models from `class Config:` to `ConfigDict` | ⏳ Pending |
| P2 | Add lineage columns to StatementOutput | ⏳ Pending |

---

## Appendix J: All Engines Compliance Matrix

### Summary by Engine

| Engine | Rule 2 (Decimal) | Rule 3 (version_id) | Rule 6 (Pydantic v2) | Rule 8 (Audit) | Priority |
|--------|------------------|---------------------|----------------------|----------------|----------|
| **Enrollment** | ⚠️ 3 float casts | ⚠️ Missing | ⚠️ Mixed | ⚠️ Missing | HIGH |
| **DHG** | ✅ OK | ⚠️ Missing | ⚠️ 3 models + dataclass | ⚠️ Missing | HIGH |
| **EOS** | ✅ OK | ⚠️ Missing | ✅ OK | ✅ Exemplary | LOW |
| **GOSI** | ✅ OK | ⚠️ Missing | ✅ OK | ⚠️ Missing | MEDIUM |
| **Revenue** | ✅ OK | ⚠️ Missing | ⚠️ 1 model | ⚠️ Missing | MEDIUM |
| **KPI** | ✅ OK | ⚠️ Wrong (`budget_id`) | ⚠️ Multiple | ⚠️ Partial | HIGH |
| **Financial Statements** | ✅ OK | ⚠️ Wrong (`budget_version_id`) | ❌ 9 models | ⚠️ Partial | HIGH |

### Detailed Issue Counts

| Issue Type | Enrollment | DHG | EOS | GOSI | Revenue | KPI | Fin. Stmt. | **Total** |
|------------|------------|-----|-----|------|---------|-----|------------|-----------|
| Float precision | 3 | 0 | 0 | 0 | 0 | 0 | 0 | **3** |
| `class Config:` | 2* | 3 | 0 | 0 | 1 | 3+ | 9 | **18+** |
| `@dataclass` | 0 | 1 | 0 | 0 | 0 | 0 | 0 | **1** |
| Missing `version_id` | 2 | 2 | 3 | 2 | 3 | 0** | 0** | **12** |
| Wrong `version_id` name | 0 | 0 | 0 | 0 | 0 | 1 | 1 | **2** |
| Missing `calculation_breakdown` | 1 | 1 | 0 | 1 | 1 | 0.5 | 0.5 | **5** |

*Enrollment legacy models marked for deletion
**Has wrong field name (budget_id, budget_version_id)

### Priority Order for Cleanup

Based on impact and effort, recommended cleanup order:

1. **P0 - Breaking Changes**:
   - Rename `budget_id` → `version_id` in KPI engine
   - Rename `budget_version_id` → `version_id` in Financial Statements engine
   - Fix 3 float precision issues in Enrollment engine

2. **P1 - Pydantic v2 Migration**:
   - Financial Statements: 9 models (highest count)
   - DHG: 3 models + 1 dataclass conversion
   - KPI: 3+ models
   - Revenue: 1 model
   - Enrollment: Remove legacy files (2 files)

3. **P2 - Version ID Addition**:
   - Add `version_id` field to all input/output models across all engines

4. **P3 - Auditability**:
   - Add `calculation_breakdown` to engines missing it (DHG, GOSI, Revenue)
   - Follow EOS engine as reference implementation

---

## Appendix K: Recommended Migration Order

### Phase 1: Critical Fixes (Blocking)

| Task | Engine | Effort | Impact |
|------|--------|--------|--------|
| Rename `budget_version_id` → `version_id` | Financial Statements | Low | High (DB alignment) |
| Rename `budget_id` → `version_id` | KPI | Low | High (DB alignment) |
| Fix 3 float precision issues | Enrollment | Low | High (data integrity) |
| Delete legacy `models.py` + `calculator.py` | Enrollment | Low | Medium (cleanup) |

### Phase 2: Pydantic v2 Migration

| Task | Engine | Files/Models | Effort |
|------|--------|--------------|--------|
| Migrate 9 models | Financial Statements | models.py | Medium |
| Convert dataclass + 3 models | DHG | models.py | Medium |
| Migrate 3+ models | KPI | models.py | Low |
| Migrate 1 model | Revenue | models.py | Low |

### Phase 3: Version Awareness

Add `version_id: UUID | None = None` to all input/output models:
- Enrollment: ProjectionInput, ProjectionResult
- DHG: DHGInput, DHGHoursResult, FTECalculationResult
- EOS: EOSInput, EOSResult, EOSProvisionInput
- GOSI: GOSIInput, GOSIResult
- Revenue: RevenueInput, StudentRevenueResult
- KPI: Already has (needs rename only)
- Financial Statements: Already has (needs rename only)

### Phase 4: Auditability Enhancement

Add `calculation_breakdown: str | None` following EOS pattern:
- DHG: FTECalculationResult
- GOSI: GOSIResult
- Revenue: StudentRevenueResult

---

## Appendix L: Module-Engine Dependency Graph

### Calculation Flow Diagram

> **Note**: All tables are in `efir_budget` schema with module prefixes. No separate PostgreSQL schemas.

```
┌────────────────────────────────────────────────────────────────────────────┐
│                            SETTINGS MODULE                                  │
│  (versions, parameters, reference data)                                    │
│  Tables: settings_*, ref_*  │  Engines: (none)                             │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │ version_id
                                   │ (all modules reference)
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           STUDENTS MODULE                                   │
│  Enrollment projections, class structure, lateral movements                │
│  Tables: students_*  │  Engines: enrollment/, calibration/                 │
│                                                                            │
│  enrollment/projection_engine.py → Cohort progression                      │
│  enrollment/calibration_engine.py → YoY calibration                        │
│  enrollment/lateral_optimizer.py → Capacity optimization                   │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │ student_counts, class_counts
                                   │ (passed via service layer)
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           TEACHERS MODULE                                   │
│  DHG requirements, employees, positions, EOS/GOSI                          │
│  Tables: teachers_*  │  Engines: dhg/, eos/, gosi/                         │
│                                                                            │
│  dhg/calculator.py → DHG hours = classes × curriculum_hours                │
│  dhg/calculator.py → FTE = total_hours ÷ standard_hours                    │
│  eos/calculator.py → EOS liability (KSA labor law)                         │
│  gosi/calculator.py → GOSI contributions (12% employer)                    │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │ fte_needs, personnel_costs
                                   │ (passed via service layer)
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           FINANCE MODULE                                    │
│  Revenue, costs, CapEx, financial statements                               │
│  Tables: finance_*  │  Engines: revenue/, costs/, financial_statements/   │
│                                                                            │
│  revenue/calculator.py → Revenue = students × fees                         │
│  costs/calculator.py → Total costs (personnel + operating + CapEx)         │
│  financial_statements/calculator.py → PCG/IFRS statements                  │
└──────────────────────────────────┬─────────────────────────────────────────┘
                                   │ all_financial_data
                                   │ (passed via service layer)
                                   ▼
┌────────────────────────────────────────────────────────────────────────────┐
│                           INSIGHTS MODULE                                   │
│  KPIs, dashboards, variance analysis, reports                              │
│  Tables: insights_*  │  Engines: kpi/, variance/                           │
│                                                                            │
│  kpi/calculator.py → H/E, E/D, Cost/Student, Revenue/Student               │
│  variance/calculator.py → Budget vs Actual analysis (future)               │
└────────────────────────────────────────────────────────────────────────────┘

ADMIN MODULE (spans all modules)
Tables: admin_*  │  Engines: (none)
Responsibilities: Users, audit logs, data imports
```

### Calculation Dependencies by Engine

| Engine | Depends On | Produces | Consumed By |
|--------|------------|----------|-------------|
| `enrollment/` | Settings (version, params) | student_counts, class_counts | dhg/, revenue/, kpi/ |
| `dhg/` | enrollment/ outputs, Settings | dhg_hours, fte_requirements | costs/, kpi/ |
| `eos/` | employees (via service) | eos_liability | costs/ |
| `gosi/` | employees (via service) | gosi_contributions | costs/ |
| `revenue/` | enrollment/ outputs, Settings (fees) | total_revenue | financial_statements/, kpi/ |
| `costs/` | dhg/, eos/, gosi/ outputs | total_costs | financial_statements/, kpi/ |
| `financial_statements/` | revenue/, costs/ outputs | PCG/IFRS statements | kpi/ |
| `kpi/` | All above | KPI values | (terminal - dashboards) |
| `variance/` | kpi/, financial_data (ACTUAL vs BUDGET) | variance_reports | (terminal - reports) |

### Cache Invalidation Graph

When input data changes, dependent calculations must be invalidated:

```
Settings Change (fees, params)
    └─→ Invalidate: enrollment, revenue, costs, financial_statements, kpi

Enrollment Change (projections, class structure)
    └─→ Invalidate: dhg, revenue, costs, financial_statements, kpi

Teacher Change (employees, allocations)
    └─→ Invalidate: dhg, eos, gosi, costs, financial_statements, kpi

Fee Structure Change
    └─→ Invalidate: revenue, financial_statements, kpi

Cost Parameters Change
    └─→ Invalidate: costs, financial_statements, kpi
```

### API Route Alignment

API routes should align with module ownership:

```
/api/v1/students/enrollment/...      → enrollment/ engine
/api/v1/students/class-structure/... → (service uses enrollment/)

/api/v1/teachers/dhg/...             → dhg/ engine
/api/v1/teachers/eos/...             → eos/ engine
/api/v1/teachers/gosi/...            → gosi/ engine

/api/v1/finance/revenue/...          → revenue/ engine
/api/v1/finance/costs/...            → costs/ engine
/api/v1/finance/statements/...       → financial_statements/ engine

/api/v1/insights/kpis/...            → kpi/ engine
/api/v1/insights/variance/...        → variance/ engine
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.4 | 2025-12-15 | Updated Rule 14 and Appendix L: Changed from multi-schema to table prefix convention (`students_*`, `teachers_*`, `finance_*`, etc. in single `efir_budget` schema) - aligns with updated DB_golden_rules.md |
| 1.3 | 2025-12-14 | Added Rule 14 (Module-Engine Ownership) and Appendix L (Module-Engine Dependency Graph) - aligns with DB_golden_rules.md Section 9 unified 6-module architecture |
| 1.2 | 2025-12-14 | Added Appendix D-K: All engines review (DHG, EOS, GOSI, Revenue, KPI, Financial Statements), comprehensive compliance matrix, migration roadmap |
| 1.1 | 2025-12-14 | Added Appendix B (Enrollment Engine Cleanup), Appendix C (Compliance Matrix), updated Rule 3 for DB alignment (version_id) |
| 1.0 | 2025-12-14 | Initial version |
