# Database Schema Fix Status Report - December 5, 2025

## Executive Summary

**Status:** Partial Success - Schema stripping working, but integration test architecture needs revision

**Achievement:**
- ✅ Fixed 16 tests (from 149 failures → 133 failures)
- ✅ Schema stripping successfully implemented in conftest.py
- ✅ SQL queries no longer use `efir_budget.` prefix
- ⚠️  But tests still fail due to missing table creation

**Root Cause Identified:**
Integration tests use `TestClient(app)` which creates its own database engine, bypassing conftest.py fixtures.

---

## What We Accomplished

### 1. Schema Stripping Implementation ✅

**Location:** `tests/conftest.py:56-107`

**Two-Phase Approach:**
```python
# Phase 1: Strip schema from tables (before User class)
for table in Base.metadata.tables.values():
    table.schema = None

# Phase 2: Strip schema from foreign keys (after User class)
for table in Base.metadata.tables.values():
    for fk_constraint in table.foreign_key_constraints:
        for fk_element in fk_constraint.elements:
            colspec = str(fk_element._colspec)
            if '.' in colspec:
                parts = colspec.split('.')
                if len(parts) == 3:  # schema.table.column
                    fk_element._colspec = f"{parts[1]}.{parts[2]}"
```

**Result:** SQL queries changed from:
```sql
-- Before:
SELECT efir_budget.budget_versions.name FROM efir_budget.budget_versions

-- After:
SELECT budget_versions.name FROM budget_versions
```

✅ **Schema stripping WORKS!**

### 2. Test Results Improvement

**Before Fix:**
- Tests passing: 1,413
- Tests failing: 149
- Coverage: 88.88%

**After Fix:**
- Tests passing: 1,429 (+16 tests) ✅
- Tests failing: 133 (-16 tests) ✅
- Coverage: 88.64% (slight drop, within noise)

**Improvement:** 10.7% reduction in failing tests

---

## The Fundamental Architecture Issue

### Problem: TestClient Bypasses Fixtures

**Integration Test Pattern (from test_configuration_api.py:20-22):**
```python
@pytest.fixture
def client():
    return TestClient(app)  # Uses production app!
```

**What Happens:**
1. `TestClient(app)` instantiates `app` from `app.main:create_app()`
2. `create_app()` uses `app.database:get_db_session()` for database
3. `app.database` creates its OWN async engine using environment variables
4. This engine doesn't go through conftest.py's schema stripping
5. Tables created with schema="efir_budget" (from `BaseModel.__table_args__`)
6. But schema stripping in conftest only affects conftest's engine, not app's engine

**Architectural Diagram:**
```
┌─────────────────────────────────────────────────────┐
│ Integration Test                                    │
├─────────────────────────────────────────────────────┤
│ test_get_budget_versions_integration(client)        │
│   ├─ Uses TestClient(app) fixture                   │
│   └─ app = FastAPI from app.main                    │
│       └─ Database: app.database.get_db_session()    │
│           └─ Engine: create_async_engine()          │
│               ├─ Metadata: Base.metadata (schema="efir_budget") ❌
│               └─ NOT using conftest engine ❌       │
└─────────────────────────────────────────────────────┘

vs

┌─────────────────────────────────────────────────────┐
│ Service Test (Working)                              │
├─────────────────────────────────────────────────────┤
│ test_service_method(db_session)                     │
│   └─ db_session from conftest engine fixture ✅     │
│       └─ Engine: conftest.engine                    │
│           └─ Metadata: Base.metadata (schema=None) ✅│
└─────────────────────────────────────────────────────┘
```

### Why Service Tests Work But API Tests Don't

**Service Tests (99% coverage for some services):**
```python
@pytest.mark.asyncio
async def test_service_method(db_session):
    service = Service(db_session)  # Uses conftest's db_session
    result = await service.method()
```
✅ **Works** because `db_session` comes from conftest's schema-stripped engine

**API Integration Tests (failing):**
```python
def test_api_endpoint(client):
    response = client.get("/api/v1/endpoint")  # Uses app's own engine
```
❌ **Fails** because `client` uses app's production engine (not conftest's)

---

## Solutions Evaluated

### Option A: Monkeypatch app.database (Recommended) ⭐

**Approach:** Override `app.database.get_db_session` to use conftest's test engine

**Implementation:**
```python
# In conftest.py or test_*.py fixture
@pytest.fixture
def client(engine):
    """Create test client with monkeypatched database."""
    from app import database
    from app.main import create_app

    # Override get_db_session to use test engine
    async def test_get_db_session():
        async with AsyncSession(engine) as session:
            yield session

    with patch.object(database, "get_db_session", test_get_db_session):
        app = create_app()
        yield TestClient(app)
```

**Pros:**
- ✅ Minimal code changes
- ✅ Preserves existing test structure
- ✅ Works with all integration tests
- ✅ Ensures schema stripping applies to API tests

**Cons:**
- ⚠️ Requires careful monkeypatch implementation
- ⚠️ May need to handle async context properly

**Estimated Effort:** 2-4 hours

**Expected Impact:**
- Fix 100-120 of the 133 remaining failures
- Coverage increase: +4-6% → 92-95%

---

### Option B: Rewrite Integration Tests to Use db_session

**Approach:** Change integration tests to inject db_session instead of using TestClient

**Implementation:**
```python
# Current (fails):
def test_endpoint(client):
    response = client.get("/api/v1/endpoint")

# New (works):
async def test_endpoint(db_session):
    from app.api.v1 import configuration
    result = await configuration.get_budget_versions(db=db_session)
```

**Pros:**
- ✅ Guaranteed to work with conftest fixtures
- ✅ More control over test data

**Cons:**
- ❌ Major rewrite of ~100 integration tests
- ❌ Loses benefits of end-to-end API testing
- ❌ No longer tests FastAPI routing, middleware, serialization

**Estimated Effort:** 20-30 hours

**Not Recommended** - Defeats purpose of integration tests

---

### Option C: Use PostgreSQL Test Database

**Approach:** Run tests against real PostgreSQL with schemas

**Implementation:**
```python
@pytest.fixture(scope="session")
def test_database_url():
    return "postgresql+asyncpg://test:test@localhost:5432/test_db"
```

**Pros:**
- ✅ No schema compatibility issues
- ✅ Closer to production environment

**Cons:**
- ❌ Requires external PostgreSQL server
- ❌ Slower tests (network overhead)
- ❌ CI/CD complexity (need database service)
- ❌ Doesn't solve the root issue (still need fixtures)

**Estimated Effort:** 4-8 hours

**Not Recommended** - Adds infrastructure dependency

---

### Option D: Custom TestClient with Database Dependency Override

**Approach:** Use FastAPI's dependency override mechanism

**Implementation:**
```python
@pytest.fixture
def client(engine):
    """Create test client with overridden database dependency."""
    from app.main import create_app
    from app.dependencies.database import get_db_session

    app = create_app()

    async def override_get_db_session():
        async with AsyncSession(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = override_get_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
```

**Pros:**
- ✅ Clean FastAPI-native approach
- ✅ Preserves full API testing
- ✅ Easy to understand and maintain
- ✅ Recommended by FastAPI documentation

**Cons:**
- ⚠️ Requires refactoring how database is injected in endpoints

**Estimated Effort:** 3-5 hours

**Highly Recommended** ⭐⭐ - Best long-term solution

---

## Recommended Path Forward

### Phase 1: Implement Option D (Dependency Override) - Highest ROI

**Step 1:** Ensure all API endpoints use `get_db_session` dependency
```python
# app/api/v1/configuration.py
from app.dependencies.database import get_db_session

@router.get("/budget-versions")
async def get_budget_versions(db: AsyncSession = Depends(get_db_session)):
    # ...
```

**Step 2:** Update client fixture to override dependency
```python
# tests/conftest.py (add)
@pytest.fixture
def client(engine):
    from app.main import create_app
    from app.dependencies.database import get_db_session

    app = create_app()

    async def test_db_session():
        async with AsyncSession(engine) as session:
            yield session

    app.dependency_overrides[get_db_session] = test_db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
```

**Step 3:** Remove local client fixtures from test files
- Delete client fixtures from tests/api/test_*.py files
- Use centralized conftest.client fixture

**Expected Results:**
- 100-120 tests will start passing
- Coverage: 88.64% → 92-95% (+4-6 points)
- Remaining failures will be legitimate (missing data, validation errors)

---

### Phase 2: Add Test Fixtures for Integration Tests

After dependency override works, remaining failures will be due to missing test data.

**Example Failures:**
```python
# Test expects budget versions to exist
response = client.get("/api/v1/budget-versions")
# Returns: [] (empty list) instead of test data
```

**Solution:** Add autouse fixtures that populate test data
```python
@pytest.fixture(autouse=True)
async def setup_test_data(db_session, test_user_id):
    """Automatically populate test database for integration tests."""
    # Create budget version
    version = BudgetVersion(
        id=uuid4(),
        name="FY2025 Test Budget",
        fiscal_year=2025,
        created_by_id=test_user_id
    )
    db_session.add(version)
    await db_session.commit()
```

**Expected Impact:**
- Additional 10-20 tests passing
- Coverage: 92-95% → 95%+ (final push)

---

## Current Status Summary

**✅ Accomplishments:**
1. Schema stripping working correctly in conftest.py
2. SQL queries no longer use schema prefixes
3. 16 tests fixed (149 → 133 failures)
4. Root cause identified and documented
5. Clear path forward established

**🔧 Work Remaining:**
1. Implement dependency override in client fixture (3-5 hours)
2. Verify all endpoints use get_db_session dependency (1-2 hours)
3. Add autouse test data fixtures (2-3 hours)
4. Fix remaining validation/business logic errors (2-4 hours)

**Total Effort to 95% Coverage:** 8-14 hours

---

## Technical Details for Implementation

### Code Locations

**1. Schema Stripping (WORKING):**
- File: `tests/conftest.py:56-107`
- Lines 65-66: Remove schema from tables
- Lines 94-106: Strip schema from foreign keys

**2. Client Fixture (NEEDS UPDATE):**
- Current: Individual test files define own client
- Target: Centralized in `tests/conftest.py`

**3. Database Dependency:**
- Check: `app/dependencies/database.py:get_db_session()`
- Verify all endpoints use this dependency

### Verification Commands

**Test schema stripping works:**
```bash
cd backend
python3 -c "
from tests.conftest import Base
for table in Base.metadata.tables.values():
    assert table.schema is None, f'{table.name} has schema {table.schema}'
print('✅ All tables have schema=None')
"
```

**Test dependency override pattern:**
```bash
cd backend && source .venv/bin/activate
pytest tests/api/test_configuration_api.py::TestBudgetVersionEndpointsIntegration::test_get_budget_versions_integration -xvs
# After fix, should see table creation messages and test should pass or return empty list
```

---

## Conclusion

We've successfully implemented schema stripping for SQLite compatibility, which fixed 16 tests and proves the approach works. However, the integration test architecture needs one more fix: **dependency override** to ensure TestClient uses the schema-stripped test database.

**Recommended Next Step:**
Implement Option D (Dependency Override) - estimated 3-5 hours, expected to fix 100-120 additional tests and bring coverage to 92-95%.

**Final Push to 95%:**
Add autouse test data fixtures (2-3 hours) to populate test database with realistic EFIR scenarios.

**Total Time to 95% Coverage:** 8-14 hours from current state.

---

**Agent 13 Status:** Analysis complete. Recommending dependency override implementation.
**Coverage Goal:** 95% achievable with proposed approach.
**Success Probability:** 90%+ (dependency override is well-documented FastAPI pattern)

