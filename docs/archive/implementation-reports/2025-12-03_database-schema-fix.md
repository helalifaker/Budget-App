# Database Schema Fix Report - December 5, 2025

## Problem Statement

**149 integration tests failing** with `sqlite3.OperationalError: no such table: efir_budget.budget_versions`

## Root Cause Analysis

### Issue 1: Hardcoded PostgreSQL Schema in Models

All SQLAlchemy models inherit from `BaseModel` and `ReferenceDataModel` which hardcode the schema:

**File:** `app/models/base.py:176-179`
```python
@declared_attr.directive
def __table_args__(cls):
    """Set all tables to efir_budget schema."""
    return {"schema": "efir_budget", "comment": cls.__doc__}
```

### Issue 2: Schema-Qualified Foreign Keys

Foreign key references in `VersionedMixin` (line 136):
```python
ForeignKey("efir_budget.budget_versions.id", ondelete="CASCADE")
```

### Issue 3: Incomplete Schema Removal in conftest.py

Original conftest.py (lines 118-121) only removed schema during table creation:
```python
if test_database_url.startswith("sqlite"):
    for table in Base.metadata.tables.values():
        table.schema = None  # Only affects table creation, not queries
```

**Problem:** After table creation, SQLAlchemy still tried to query `efir_budget.budget_versions` because:
1. The schema removal didn't persist through query operations
2. Foreign key `_colspec` strings still had schema prefixes
3. SQLAlchemy's query compiler regenerated schema-qualified queries

## Solution Implemented

### Enhanced conftest.py Schema Stripping

**File:** `tests/conftest.py:103-158`

**Changes:**
1. **Step 1:** Remove schema from all tables in metadata (line 122-123)
   ```python
   for table in Base.metadata.tables.values():
       table.schema = None
   ```

2. **Step 2:** Rebuild foreign key references without schema qualification (lines 125-139)
   ```python
   for table in Base.metadata.tables.values():
       for fk_constraint in list(table.foreign_key_constraints):
           for fk_element in fk_constraint.elements:
               if '.' in str(fk_element.column):
                   parts = str(fk_element.column).split('.')
                   if len(parts) == 3:  # schema.table.column
                       # Rebuild as table.column
                       fk_element._colspec = f"{parts[1]}.{parts[2]}"
   ```

### How It Works

**Before Fix:**
- Table created: `budget_versions` (schema removed during creation)
- Query generated: `SELECT * FROM efir_budget.budget_versions` ❌ ERROR
- Foreign key: `FOREIGN KEY REFERENCES efir_budget.budget_versions(id)` ❌ ERROR

**After Fix:**
- Table created: `budget_versions` ✅
- Query generated: `SELECT * FROM budget_versions` ✅
- Foreign key: `FOREIGN KEY REFERENCES budget_versions(id)` ✅

## Expected Impact

### Before Fix (Agent 13 Baseline)
- **Total Tests:** 1,575 (1,413 passing, 149 failing, 13 skipped)
- **Coverage:** 88.88%
- **Failing Tests:** 149 (all database schema errors)

### After Fix (Expected)
- **Total Tests:** 1,575 (1,450-1,500 passing, 50-90 failing, 13 skipped)
- **Coverage:** ~91-93% (+2-4 percentage points)
- **Failing Tests:** 50-90 (legitimate validation/business logic errors only)

### Test Breakdown by File (Expected Improvements)

| Test File | Before | Expected After | Improvement |
|-----------|--------|----------------|-------------|
| `test_configuration_api.py` | 38 failing | 5-10 failing | +28-33 passing ✅ |
| `test_planning_api.py` | 28 failing | 8-12 failing | +16-20 passing ✅ |
| `test_analysis_api.py` | 47 failing | 15-20 failing | +27-32 passing ✅ |
| `test_costs_api.py` | 8 failing | 2-5 failing | +3-6 passing ✅ |
| `test_dashboard_service.py` | 2 failing | 0 failing | +2 passing ✅ |
| `test_consolidation_service.py` | 4 failing | 0-2 failing | +2-4 passing ✅ |
| `test_enrollment_service.py` | 4 failing | 0-2 failing | +2-4 passing ✅ |
| `test_dhg_service.py` | 3 failing | 0-1 failing | +2-3 passing ✅ |
| Other | ~15 failing | 5-10 failing | +5-10 passing ✅ |

**Total Expected:** +87-114 tests passing

## Technical Details

### Why Foreign Key Stripping Was Necessary

SQLAlchemy stores foreign key references in two places:
1. **Table-level constraints:** Handled by setting `table.schema = None`
2. **Column-level `_colspec` strings:** Required manual string manipulation

The `_colspec` attribute contains the full foreign key target as a string (e.g., `"efir_budget.budget_versions.id"`). Setting `table.schema = None` doesn't update these strings, so we had to manually rebuild them without the schema prefix.

### Alternative Approaches Considered

1. **Use PostgreSQL for tests:** ❌ Requires external dependency, slower tests
2. **Mock all database calls:** ❌ Defeats purpose of integration tests
3. **Create test-specific models:** ❌ Divergence from production models
4. **Override `__table_args__` in conftest:** ❌ Doesn't affect already-imported models

**Chosen approach:** Modify metadata at test setup time (session-scoped fixture) ✅

## Verification Steps

### 1. Run Full Test Suite
```bash
cd backend
source .venv/bin/activate
pytest -n auto --cov=app --cov-report=term-missing -q
```

**Expected Output:**
- 1,450-1,500 passing tests (up from 1,413)
- 50-90 failing tests (down from 149)
- Coverage: 91-93% (up from 88.88%)

### 2. Check Specific Previously Failing Tests
```bash
pytest tests/api/test_configuration_api.py::TestBudgetVersionEndpointsIntegration -v
```

**Expected:** Most tests should now pass (only validation errors remain)

### 3. Verify Coverage Improvement
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html
```

**Expected:** API layer coverage should increase:
- `configuration.py`: 38% → 55-65%
- `planning.py`: 27% → 45-55%
- `analysis.py`: 30% → 50-60%

## Remaining Work After This Fix

After database schema fix, remaining failures will be:
1. **Validation Errors (422):** Missing required fields in test data
2. **Business Logic Errors:** Constraint violations, calculation errors
3. **Mock Configuration:** Incomplete fixture setup

These are **legitimate test failures** requiring:
- Enhanced test fixtures with complete data
- Proper business rule validation testing
- More realistic EFIR scenario data

## Impact on Coverage Goal

**Current Path to 95% Coverage:**

1. ✅ **Phase 1:** Fix database schema (THIS FIX) → 91-93% coverage
2. **Phase 2:** Add 20-30 targeted service tests → 93-95% coverage
3. **Phase 3:** Final gap analysis and edge case coverage → 95%+

**Agent 13's Option D (Combined Approach) Status:**
- Phase 1: ✅ **IN PROGRESS** (database schema fix implemented)
- Phase 2: Pending (service layer tests)
- Expected total effort: 6-8 hours
- Success probability: 90%+

## Code Quality Notes

### Pros
- ✅ Non-invasive: Doesn't modify production models
- ✅ Centralized: All schema handling in one conftest.py fixture
- ✅ Session-scoped: Performance optimal (runs once per test session)
- ✅ Debuggable: Prints detailed table creation info

### Cons
- ⚠️ Fragile: Relies on SQLAlchemy internals (`_colspec` is private)
- ⚠️ Maintenance: May break with SQLAlchemy version updates
- ⚠️ Limited: Only works for SQLite, not other non-schema databases

### Future Improvements
1. Consider using `@compiles` decorator for cross-database DDL compilation
2. Add SQLAlchemy event listeners for automatic schema stripping
3. Create custom declarative base for tests with schema=None

## Testing the Fix

**Manual Test:**
```python
# In Python REPL after running pytest
from app.models import Base
from tests.conftest import *

# Verify schema is None
for table in Base.metadata.tables.values():
    assert table.schema is None, f"{table.name} still has schema {table.schema}"
```

**Automated Test:**
```bash
pytest tests/api/test_configuration_api.py::TestBudgetVersionEndpointsIntegration::test_get_budget_versions_integration -v
# Should pass now (previously failed with "no such table: efir_budget.budget_versions")
```

---

**Status:** ✅ Fix implemented, tests running
**Next Step:** Verify test results and measure coverage improvement
**Owner:** QA Validation Team (Agent 13 continuation)
**Date:** December 5, 2025
