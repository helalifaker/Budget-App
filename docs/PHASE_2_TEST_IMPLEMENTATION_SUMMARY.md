# Phase 2: Test Coverage Implementation Summary

**Date:** 2025-12-02
**Status:** Planning Complete - Ready for Implementation
**Target:** 95% Coverage (Backend + Frontend)

---

## Executive Summary

Comprehensive test coverage implementation plan created for EFIR Budget Planning Application. Current coverage is 50% backend and <5% frontend. Plan targets 95% coverage across all critical modules with a 5-week timeline.

### Current State

**Backend Coverage: 49.84%**
- Total Lines: 5,973
- Covered: 2,996
- Test Files: 15
- Tests Passing: 244/293
- Tests Failing: 7
- Tests Errored: 39 (database setup issues)

**Critical Service Coverage Gaps:**
- `dhg_service.py`: **15.6%** (Need +79.4%)
- `consolidation_service.py`: **16.6%** (Need +78.4%)
- `revenue_service.py`: **14.8%** (Need +80.2%)
- `cost_service.py`: **12.6%** (Need +82.4%)

**Frontend Coverage: <5%**
- Test Files: 1 (App.test.tsx)
- Component Coverage: 0%
- Hook Coverage: 0%
- E2E Tests: 5 (failing - config issues)

### Deliverables Created

1. **Comprehensive Test Plan** (`PHASE_2_TEST_COVERAGE_PLAN.md`)
   - 18,000+ word detailed implementation guide
   - Priority matrix (P0-P3)
   - Test scenarios for all critical modules
   - Mock/fixture requirements
   - 5-week timeline with daily milestones

2. **Backend Test Templates**
   - `test_dhg_service.py` (500+ lines)
     - 8 test classes
     - 20+ test scenarios
     - Complete fixtures for DHG testing
     - Ready for implementation

3. **Frontend Test Templates**
   - `BudgetVersionSelector.test.tsx` (650+ lines)
     - 7 test suites
     - 30+ test scenarios
     - Complete mock data
     - Ready for implementation

---

## Implementation Roadmap

### Week 1: P0 Backend Services (40 hours)

**Target:** Critical service layer at 95%

| Day | Focus | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1-2 | DHG Service + DB Fixes | 16h | 95% coverage on DHG |
| 3-4 | Consolidation + Revenue | 16h | 95% coverage on both |
| 5 | Cost Service | 8h | 95% coverage |

**Milestone 1:** Backend P0 services at 95% coverage

### Week 2: P0 Frontend Components (36 hours)

**Target:** Critical UI components at 95%

| Day | Focus | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1 | Test Infrastructure Fixes | 8h | Playwright + act() fixed |
| 2-3 | Component Tests | 16h | BudgetVersionSelector + DataTable |
| 4-5 | Hook Tests | 12h | useBudgetVersions + useDHG |

**Milestone 2:** Frontend P0 at 95% coverage

### Week 3: P1 Backend Services (48 hours)

**Target:** Integration services at 95%

| Day | Focus | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1-3 | Integration Services | 24h | Odoo + Skolengo + AEFE |
| 4-5 | Supporting Services | 16h | KPI + Dashboard |
| 6 | Review & Fixes | 8h | Address gaps |

**Milestone 3:** P1 services at 95% coverage

### Week 4: P2 API & Infrastructure (40 hours)

**Target:** API layer at 95%

| Day | Focus | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1-3 | API Endpoints | 24h | Planning + Consolidation + Analysis |
| 4-5 | Middleware & Auth | 16h | Auth + RBAC + Base Service |

**Milestone 4:** Backend API layer at 95% coverage

### Week 5: P3 Final Coverage (24 hours)

**Target:** Overall 95% achieved

| Day | Focus | Hours | Deliverable |
|-----|-------|-------|-------------|
| 1-2 | Fill Gaps | 16h | Validators + Models |
| 3 | Documentation & CI/CD | 8h | Final report + Coverage gates |

**Milestone 5:** 95% coverage achieved

---

## Priority Breakdown

### P0 (Critical - 80 hours)

**Backend (40h):**
1. DHG Service - 24h
   - Subject hours calculation
   - Teacher requirements
   - Gap analysis (TRMD)
   - HSA allocation

2. Consolidation Service - 20h
   - Budget consolidation
   - Approval workflow
   - Version validation
   - Line item rollup

3. Revenue Service - 16h
   - Tuition calculation
   - Fee structure application
   - Sibling discounts
   - Trimester distribution

4. Cost Service - 20h
   - Personnel costs (AEFE + Local)
   - Operating costs
   - Driver-based calculation
   - Cost allocation

**Frontend (40h):**
1. BudgetVersionSelector - 8h
   - Rendering states
   - User interactions
   - Status badges
   - Edge cases

2. DataTable (AG Grid) - 10h
   - Grid rendering
   - Cell editing
   - Sorting/filtering
   - Custom renderers

3. useBudgetVersions Hook - 6h
   - Query tests
   - Mutation tests
   - Error handling
   - Cache invalidation

4. useDHG Hook - 6h
   - Calculation triggers
   - Teacher allocations
   - Integration tests

5. Test Infrastructure - 10h
   - Database setup fixes
   - Playwright configuration
   - act() warning fixes
   - Fixture library setup

### P1 (High - 48 hours)

**Backend Only:**
1. Odoo Integration - 8h
2. Skolengo Integration - 8h
3. AEFE Integration - 8h
4. KPI Service - 12h
5. Dashboard Service - 12h

### P2 (Medium - 40 hours)

**Backend Only:**
1. Planning API - 8h
2. Consolidation API - 8h
3. Analysis API - 8h
4. Auth Middleware - 8h
5. RBAC Middleware - 4h
6. Base Service - 4h

### P3 (Low - 24 hours)

**Backend Only:**
1. Validators - 8h
2. Model/Schema gaps - 8h
3. Documentation - 8h

---

## Critical Issues to Fix

### Backend Issues

**1. Database Foreign Key Errors (Priority: HIGH)**

**Issue:** 39 tests failing with:
```
Foreign key associated with column 'kpi_definitions.updated_by_id'
could not find table 'auth.users'
```

**Root Cause:** Test database missing auth schema for Supabase compatibility

**Solution:** Create auth schema and users table in test setup
```python
# backend/tests/conftest.py

@pytest.fixture(scope="session")
async def setup_test_db():
    async with engine.begin() as conn:
        # Create auth schema
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))

        # Create auth.users table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS auth.users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Create test user
        await conn.execute(text("""
            INSERT INTO auth.users (id, email)
            VALUES (
                '00000000-0000-0000-0000-000000000001',
                'test@efir.sa'
            )
            ON CONFLICT DO NOTHING
        """))
```

**Time to Fix:** 2-4 hours
**Impact:** Fixes 39 failing tests

**2. Pytest Asyncio Configuration Warning**

**Issue:**
```
PytestDeprecationWarning: The configuration option
"asyncio_default_fixture_loop_scope" is unset.
```

**Solution:** Update pytest.ini
```ini
[pytest]
asyncio_default_fixture_loop_scope = function
```

**Time to Fix:** 5 minutes

### Frontend Issues

**1. Playwright Configuration Conflict (Priority: HIGH)**

**Issue:** E2E tests failing with:
```
Error: Playwright Test did not expect test.describe() to be called here.
```

**Root Cause:** Vitest and Playwright both trying to run E2E tests

**Solution:** Separate configurations
```typescript
// vitest.config.ts - Unit tests only
export default defineConfig({
  test: {
    include: ['src/**/*.test.{ts,tsx}'],
    exclude: ['tests/e2e/**'],
  },
})

// playwright.config.ts - E2E tests only
export default defineConfig({
  testDir: './tests/e2e',
})
```

**Time to Fix:** 1-2 hours

**2. React act() Warnings (Priority: MEDIUM)**

**Issue:**
```
An update to Transitioner inside a test was not wrapped in act(...)
```

**Root Cause:** TanStack Router state updates not wrapped

**Solution:** Use waitFor() for async operations
```typescript
import { waitFor } from '@testing-library/react'

it('should update on navigation', async () => {
  render(<Component />)

  await waitFor(() => {
    expect(screen.getByText('Loaded')).toBeInTheDocument()
  })
})
```

**Time to Fix:** 2-4 hours (update all affected tests)

---

## Test Infrastructure

### Backend Test Setup

**Required Fixtures:**
- Database session with rollback
- Auth schema and test user
- Budget version factory
- Academic levels/cycles/subjects
- Subject hours matrix
- Class structure
- Teacher allocations
- Fee structure
- Cost parameters

**Files Created:**
- `backend/tests/fixtures/__init__.py` (centralized fixtures)
- `backend/tests/services/test_dhg_service.py` (template)
- Updated `backend/tests/conftest.py` (database setup)

### Frontend Test Setup

**Required Mocks:**
- TanStack Query QueryClient
- API service mocks
- Router context
- Toast notifications
- Supabase client

**Files Created:**
- `frontend/tests/fixtures/index.ts` (centralized mocks)
- `frontend/tests/components/BudgetVersionSelector.test.tsx` (template)
- Updated `frontend/src/setupTests.ts` (test utilities)

---

## Coverage Verification

### Daily Coverage Commands

**Backend:**
```bash
cd backend
pytest --cov=app --cov-report=term --cov-report=html
open htmlcov/index.html
```

**Frontend:**
```bash
cd frontend
pnpm test -- --coverage
open coverage/index.html
```

### CI/CD Coverage Gates

**GitHub Actions Workflow:**
```yaml
name: Test Coverage

on: [push, pull_request]

jobs:
  backend-coverage:
    steps:
      - run: pytest --cov=app --cov-fail-under=95

  frontend-coverage:
    steps:
      - run: pnpm test -- --coverage
      - run: |
          # Check coverage thresholds
          # Lines: 95%, Functions: 95%, Branches: 95%
```

**Coverage Thresholds:**
- Lines: 95%
- Functions: 95%
- Branches: 95%
- Statements: 95%

---

## Success Criteria

### Phase 2 Complete When:

✅ **Backend Coverage ≥ 95%**
- All P0 services (DHG, Consolidation, Revenue, Cost) at 95%+
- All calculation engines maintained at 100%
- All API endpoints at 95%+
- All tests passing (0 failures)

✅ **Frontend Coverage ≥ 95%**
- All P0 components at 95%+
- All critical hooks at 95%+
- E2E tests passing for critical paths

✅ **Test Quality**
- All tests follow EFIR Development Standards
- No skipped tests without justification
- No flaky tests
- All mocks/fixtures documented

✅ **CI/CD Integration**
- Coverage gates enforced (95% minimum)
- Pre-commit hooks enabled
- Automated coverage reporting
- Coverage badges in README

✅ **Documentation**
- All test scenarios documented
- Fixture library complete
- Test templates available
- Weekly progress reports

---

## Resources

### Documentation

**Created:**
- `docs/PHASE_2_TEST_COVERAGE_PLAN.md` (18,000+ words)
- `backend/tests/services/test_dhg_service.py` (500+ lines)
- `frontend/tests/components/BudgetVersionSelector.test.tsx` (650+ lines)

**Reference:**
- CLAUDE.md - Development standards
- EFIR_Module_Technical_Specification.md - Business logic
- EFIR_Workforce_Planning_Logic.md - DHG methodology

### Testing Frameworks

**Backend:**
- pytest 8.x
- pytest-asyncio 0.24
- pytest-cov 6.0
- SQLAlchemy async testing

**Frontend:**
- Vitest 3.x
- Testing Library (React)
- Playwright 1.49
- userEvent (user interactions)

### Coverage Tools

**Backend:**
- pytest-cov (HTML, JSON, LCOV reports)
- Coverage.py

**Frontend:**
- Vitest Coverage (v8 provider)
- Istanbul reports

---

## Next Steps

### Immediate Actions (Day 1)

1. **Fix Database Setup** (2-4h)
   - Create auth schema in test DB
   - Add auth.users table
   - Insert test user
   - Run tests to verify

2. **Fix Pytest Config** (5min)
   - Update pytest.ini with asyncio scope

3. **Start DHG Service Tests** (4h)
   - Implement first test class
   - Create fixtures
   - Verify coverage increase

### Week 1 Goals

- Backend P0 services at 95%
- All database setup issues resolved
- All tests passing
- Coverage report showing progress

### Daily Workflow

1. **Morning:** Check coverage report
2. **Implement:** Write tests for assigned module
3. **Run:** Execute tests and verify coverage
4. **Fix:** Address any failures immediately
5. **Commit:** Push passing tests with coverage report
6. **Report:** Update weekly progress doc

---

## Risk Assessment

### High Risk

**Database Setup Issues**
- Impact: Blocks all service tests
- Mitigation: Fix first (Day 1)
- Time: 2-4 hours

**Tight Timeline**
- Impact: May not hit 95% in 5 weeks
- Mitigation: Focus on P0 first, extend to P1/P2 as needed
- Contingency: 6th week buffer

### Medium Risk

**Test Maintenance Overhead**
- Impact: Tests may break with refactoring
- Mitigation: Follow best practices, avoid implementation details
- Strategy: Test behavior, not implementation

**Frontend Testing Complexity**
- Impact: TanStack Router/Query mocking can be tricky
- Mitigation: Use established patterns, comprehensive fixtures
- Support: Reference Testing Library docs

### Low Risk

**Coverage Tool Accuracy**
- Impact: Coverage metrics may not reflect true quality
- Mitigation: Manual code review + automated coverage
- Process: Review coverage reports weekly

---

## Appendix: Quick Reference

### Test File Naming

**Backend:**
- `tests/services/test_{service_name}_service.py`
- `tests/engine/test_{engine_name}.py`
- `tests/api/test_{endpoint_name}.py`

**Frontend:**
- `tests/components/{ComponentName}.test.tsx`
- `tests/hooks/{hookName}.test.ts`
- `tests/e2e/{feature}.spec.ts`

### Test Naming Convention

**Backend:**
```python
async def test_{method}_{scenario}_{expected_result}()
```

**Frontend:**
```typescript
it('should {action} when {condition}')
```

### Coverage Report Locations

**Backend:**
- Terminal: `pytest --cov=app --cov-report=term`
- HTML: `backend/htmlcov/index.html`
- JSON: `backend/coverage.json`

**Frontend:**
- Terminal: `pnpm test -- --coverage`
- HTML: `frontend/coverage/index.html`
- LCOV: `frontend/coverage/lcov.info`

---

**Document Status:** COMPLETE
**Ready for Implementation:** YES
**Owner:** QA & Validation Agent
**Approved By:** [Pending]
