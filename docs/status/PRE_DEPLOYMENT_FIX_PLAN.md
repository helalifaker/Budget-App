# EFIR Budget App - Pre-Deployment Fix Plan

**Date:** 2025-12-02
**Target:** Production Deployment Readiness
**Coverage Goal:** 95% (Production-Grade)
**Strategy:** Comprehensive Quality (P0-P3)
**Timeline:** 7-10 days with parallel execution

---

## Executive Summary

This plan addresses all **7 critical blockers** identified in the pre-deployment analysis through **5 parallel workstreams** with zero file conflicts. The comprehensive approach prioritizes **DHG Workforce Planning**, **Budget Consolidation**, and **Revenue/Cost Planning** test coverage while fixing all code quality issues.

**Current State:**
- ❌ ESLint broken (missing dependency)
- ❌ 16 Ruff linting errors
- ❌ 19 mypy type errors
- ❌ 32% test coverage (need 95%)
- ❌ 3 API routers not registered
- ❌ Missing test dependencies
- ❌ Dockerfile health check issue

**Target State:**
- ✅ All linting/type errors resolved
- ✅ 95% test coverage achieved
- ✅ All API routers registered
- ✅ CI/CD pipeline passing
- ✅ Production-ready deployment

---

## Parallel Workstream Architecture

### Zero-Conflict Design

| Workstream | Domain | Files Modified | Conflicts |
|------------|--------|----------------|-----------|
| **WS1** | Frontend Quick Fixes | `frontend/package.json`, `frontend/vitest.config.ts` | None |
| **WS2** | Backend Quick Fixes | `backend/app/main.py`, `backend/Dockerfile`, `backend/pyproject.toml`, `backend/app/api/v1/integrations.py` | None |
| **WS3** | Backend Type Errors | `backend/tests/conftest.py`, `backend/tests/engine/test_revenue.py`, `backend/tests/engine/test_kpi.py` | None |
| **WS4** | Backend Test Coverage | **NEW files only** in `backend/tests/` | None |
| **WS5** | Frontend Test Coverage | **NEW files only** in `frontend/src/` | None |

**Execution Strategy:**
- **Phase 1 (Parallel):** WS1 + WS2 + WS3 → 3-4 hours (P0 fixes)
- **Phase 2 (Parallel):** WS4 + WS5 → 7-10 days (P2-P3 coverage to 95%)

---

## Workstream 1: Frontend Quick Fixes (P0)

**Owner:** Frontend Developer
**Timeline:** 1-2 hours
**Depends On:** None
**Blocks:** WS5 (coverage config needed)

### Tasks

#### 1.1 Fix ESLint Dependency (15 min)

**File:** `frontend/package.json`

```bash
cd frontend
pnpm add -D @eslint/js
```

**Verification:**
```bash
pnpm lint  # Should now run without errors
```

**Success Criteria:** ESLint runs without "Cannot find package '@eslint/js'" error

---

#### 1.2 Add Coverage Configuration (30 min)

**File:** `frontend/vitest.config.ts`

Add coverage thresholds:

```typescript
export default defineConfig({
  test: {
    // ... existing config
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/**',
        'dist/**',
        '**/*.test.{ts,tsx}',
        '**/*.spec.{ts,tsx}',
        '**/routeTree.gen.ts',
        'src/setupTests.ts',
      ],
      thresholds: {
        lines: 95,
        functions: 95,
        branches: 95,
        statements: 95,
      },
    },
  },
});
```

**Verification:**
```bash
pnpm test -- --coverage
# Should show coverage report with thresholds
```

**Success Criteria:** Coverage report generates with 95% thresholds configured

---

#### 1.3 Add Code Splitting Configuration (30 min)

**File:** `frontend/vite.config.ts`

Add manual chunk splitting to reduce bundle size:

```typescript
export default defineConfig({
  // ... existing config
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor-react': ['react', 'react-dom', '@tanstack/react-router', '@tanstack/react-query'],
          'vendor-ui': ['@radix-ui/react-dialog', '@radix-ui/react-select', '@radix-ui/react-tabs', 'lucide-react'],
          'vendor-grid': ['ag-grid-community', 'ag-grid-react'],
          'vendor-charts': ['recharts', 'framer-motion'],
          'vendor-forms': ['react-hook-form', 'zod', '@hookform/resolvers'],
          'vendor-supabase': ['@supabase/supabase-js'],
        },
      },
    },
    chunkSizeWarningLimit: 600, // Increase from 500 to suppress warnings
  },
});
```

**Verification:**
```bash
pnpm build
# Check dist/assets/ for multiple chunk files (vendor-react-*.js, vendor-ui-*.js, etc.)
```

**Success Criteria:** Build produces 6+ vendor chunks, main bundle < 500KB

---

## Workstream 2: Backend Quick Fixes (P0 + P1)

**Owner:** Backend Developer
**Timeline:** 2-3 hours
**Depends On:** None
**Blocks:** None

### Tasks

#### 2.1 Fix Ruff Linting Errors (15 min)

**Files:** `backend/app/api/v1/integrations.py`, `backend/app/models/integrations.py`, `backend/app/schemas/integrations.py`

**Auto-fix all 16 errors:**
```bash
cd backend
.venv/bin/ruff check . --fix
```

**Manual fixes needed (if auto-fix doesn't work):**

**integrations.py - Remove unused imports:**
```python
# Line 36 - Remove or use:
# from app.schemas.integrations import SkolengoExportRequest

# Line 38 - Remove or use:
# from app.schemas.integrations import SkolengoSyncRequest
```

**integrations.py - Fix conversion flags (14 locations):**
```python
# Before: f"Unexpected error: {str(e)}"
# After:  f"Unexpected error: {e!s}"
```

**schemas/integrations.py - Sort imports:**
```python
# Move datetime import to correct position
```

**models/integrations.py - Remove unused Column import:**
```python
# Remove: from sqlalchemy import Column
```

**Verification:**
```bash
.venv/bin/ruff check .
# Should output: All checks passed!
```

**Success Criteria:** Zero ruff errors

---

#### 2.2 Add Pandas to Test Dependencies (5 min)

**File:** `backend/pyproject.toml`

Add to `[project.optional-dependencies]` dev section:

```toml
[project.optional-dependencies]
dev = [
    # ... existing deps
    "pandas==2.2.3",
]
```

**Install:**
```bash
.venv/bin/pip install -e ".[dev]"
```

**Verification:**
```bash
.venv/bin/python -c "import pandas; print(pandas.__version__)"
# Should output: 2.2.3
```

**Success Criteria:** pandas imports without ModuleNotFoundError

---

#### 2.3 Register Missing API Routers (30 min)

**File:** `backend/app/main.py`

Add imports at top:
```python
from app.api.v1.consolidation import router as consolidation_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.integrations import router as integrations_router
```

Add router registrations after existing routers:
```python
# Existing routers
app.include_router(health.router)
app.include_router(calculations_router)
app.include_router(configuration.router)
app.include_router(planning.router)
app.include_router(costs_router)

# NEW: Add missing routers
app.include_router(consolidation_router)
app.include_router(analysis_router)
app.include_router(integrations_router)
```

**Update:** `backend/app/api/v1/__init__.py`

```python
from app.api.v1.calculations import router as calculations_router
from app.api.v1.configuration import router as configuration_router
from app.api.v1.costs import router as costs_router
from app.api.v1.planning import router as planning_router
# NEW:
from app.api.v1.consolidation import router as consolidation_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.integrations import router as integrations_router

__all__ = [
    "calculations_router",
    "configuration_router",
    "costs_router",
    "planning_router",
    # NEW:
    "consolidation_router",
    "analysis_router",
    "integrations_router",
]
```

**Verification:**
```bash
# Start server
uvicorn app.main:app --reload

# Check OpenAPI docs
curl http://localhost:8000/docs
# Should show all router endpoints including /v1/consolidation, /v1/analysis, /v1/integrations
```

**Success Criteria:** All 3 routers accessible at their endpoint paths

---

#### 2.4 Fix Docker Health Check (30 min)

**File:** `backend/Dockerfile`

**Replace:** Lines 45-47

```dockerfile
# Before:
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')" || exit 1

# After (Option 1 - using curl):
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# After (Option 2 - using httpx in dependencies):
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health', timeout=5).raise_for_status()" || exit 1
```

**Recommended:** Option 1 (curl) - simpler, no Python dependencies

**If using Option 2, add httpx to pyproject.toml:**
```toml
dependencies = [
    # ... existing
    "httpx>=0.27.0",
]
```

**Verification:**
```bash
# Build image
docker build -t efir-backend:test .

# Run with health check
docker run -d --name efir-test -p 8000:8000 efir-backend:test

# Wait 30 seconds, then check health
docker inspect --format='{{.State.Health.Status}}' efir-test
# Should output: healthy

# Cleanup
docker stop efir-test && docker rm efir-test
```

**Success Criteria:** Docker container reports "healthy" status after startup period

---

## Workstream 3: Backend Type Error Fixes (P0)

**Owner:** Backend Developer
**Timeline:** 3-4 hours
**Depends On:** None
**Blocks:** WS4 (tests must pass before adding more)

### Tasks

#### 3.1 Fix Type Errors in integrations.py (1 hour)

**File:** `backend/app/api/v1/integrations.py`

**Problem:** Lines 141-147 - Variables have type `Any | None` but functions expect `str`

**Fix:** Add null checks and type assertions

```python
# Around line 135-150 in import_odoo_actuals endpoint:

# BEFORE:
url = config.get("url")
database = config.get("database")
username = config.get("username")
encrypted_password = config.get("password")

password = service._decrypt_password(encrypted_password)

actuals = await service.fetch_actuals(
    url=url,
    database=database,
    username=username,
    password=password,
    ...
)

# AFTER:
url = config.get("url")
database = config.get("database")
username = config.get("username")
encrypted_password = config.get("password")

# Add null checks
if not all([url, database, username, encrypted_password]):
    raise HTTPException(
        status_code=400,
        detail="Missing required Odoo configuration: url, database, username, or password"
    )

# Type narrowing - mypy now knows these are str, not Any | None
assert isinstance(url, str)
assert isinstance(database, str)
assert isinstance(username, str)
assert isinstance(encrypted_password, str)

password = service._decrypt_password(encrypted_password)

actuals = await service.fetch_actuals(
    url=url,
    database=database,
    username=username,
    password=password,
    ...
)
```

**Verification:**
```bash
.venv/bin/mypy app/api/v1/integrations.py
# Should show 0 errors (was 4)
```

**Success Criteria:** Zero mypy errors in integrations.py

---

#### 3.2 Fix Type Errors in consolidation.py (2-3 hours)

**File:** `backend/app/api/v1/consolidation.py`

**Problem:** 15 errors across 3 categories:
1. Null checks (8 errors) - `BudgetVersion | None` accessed without checking
2. Missing arguments (2 errors) - Request schemas require `notes` parameter
3. Type mismatches (5 errors) - `datetime | None` but expects `datetime`

**Fix 1: Add null checks (lines 142-145, 241, 303, 403-405, 416, 517)**

```python
# Pattern occurs multiple times - BEFORE:
budget_version = await consolidation_service.budget_version_service.get_by_id(version_id)

result = SomeResponse(
    budget_version_name=budget_version.name,  # ERROR
    fiscal_year=budget_version.fiscal_year,    # ERROR
    academic_year=budget_version.academic_year, # ERROR
    status=budget_version.status,              # ERROR
)

# AFTER:
budget_version = await consolidation_service.budget_version_service.get_by_id(version_id)

if not budget_version:
    raise HTTPException(
        status_code=404,
        detail=f"Budget version {version_id} not found"
    )

# Type narrowing - mypy now knows budget_version is BudgetVersion, not None
result = SomeResponse(
    budget_version_name=budget_version.name,
    fiscal_year=budget_version.fiscal_year,
    academic_year=budget_version.academic_year,
    status=budget_version.status,
)
```

**Apply this pattern at all 8 error locations:**
- Line 142-145: get_budget_summary endpoint
- Line 241: submit_for_approval endpoint
- Line 303: approve_budget endpoint
- Line 403-405: get_consolidation_details endpoint
- Line 416: Another null check
- Line 517: Another null check

**Fix 2: Add missing `notes` argument (lines 214, 274)**

```python
# Line 214 - BEFORE:
request: SubmitForApprovalRequest = SubmitForApprovalRequest()

# Line 214 - AFTER:
request: SubmitForApprovalRequest = SubmitForApprovalRequest(
    notes="Submitted for approval"  # or get from request body
)

# Line 274 - BEFORE:
request: ApprovebudgetRequest = ApprovebudgetRequest()

# Line 274 - AFTER:
request: ApprovebudgetRequest = ApprovebudgetRequest(
    notes="Approved"  # or get from request body
)
```

**Fix 3: Handle nullable datetime (lines 253, 315)**

```python
# Line 253 - BEFORE:
action_at=updated.submitted_at  # submitted_at can be None

# Line 253 - AFTER:
action_at=updated.submitted_at or datetime.utcnow()

# Line 315 - BEFORE:
action_at=updated.approved_at  # approved_at can be None

# Line 315 - AFTER:
action_at=updated.approved_at or datetime.utcnow()
```

**Verification:**
```bash
.venv/bin/mypy app/api/v1/consolidation.py
# Should show 0 errors (was 15)
```

**Success Criteria:** Zero mypy errors in consolidation.py

---

#### 3.3 Run Full Type Check (15 min)

**Verify all type errors resolved:**

```bash
cd backend
.venv/bin/mypy .
# Should show 0 errors (was 19)
```

**Success Criteria:** Zero mypy errors across entire backend codebase

---

## Workstream 4: Backend Test Coverage (P2-P3)

**Owner:** Backend Developer(s)
**Timeline:** 7-10 days
**Depends On:** WS3 (type errors must be fixed)
**Blocks:** None
**Target Coverage:** 95%

### Test Priority Matrix

Based on user requirements (DHG, Consolidation, Revenue/Cost):

| Priority | Module | Current Coverage | Target | Files to Create |
|----------|--------|------------------|--------|-----------------|
| **P0** | DHG Service | 16% | 95% | `tests/services/test_dhg_service.py` |
| **P0** | Consolidation Service | 0% | 95% | `tests/services/test_consolidation_service.py` |
| **P0** | Revenue Service | 15% | 95% | `tests/services/test_revenue_service.py` |
| **P0** | Cost Service | 13% | 95% | `tests/services/test_cost_service.py` |
| **P1** | KPI Service | 0% | 95% | `tests/services/test_kpi_service.py` |
| **P1** | Consolidation API | 0% | 95% | `tests/api/test_consolidation.py` |
| **P1** | Analysis API | 0% | 95% | `tests/api/test_analysis.py` |
| **P2** | Strategic Service | 0% | 90% | `tests/services/test_strategic_service.py` |
| **P2** | Dashboard Service | 0% | 90% | `tests/services/test_dashboard_service.py` |
| **P2** | Integrations API | 0% | 90% | `tests/api/test_integrations.py` |

### Backend Coverage Verification

**After each service/API test file:**
```bash
PYTHONPATH=. .venv/bin/pytest tests/services/test_X_service.py -v --cov=app/services/X_service --cov-report=term-missing
# Verify 95%+ coverage for that module
```

**Final verification:**
```bash
PYTHONPATH=. .venv/bin/pytest tests/ -v --cov=app --cov-report=term --cov-report=html

# Open htmlcov/index.html to see detailed coverage report
# Verify overall coverage >= 95%
```

---

## Workstream 5: Frontend Test Coverage (P2-P3)

**Owner:** Frontend Developer(s)
**Timeline:** 7-10 days
**Depends On:** WS1 (coverage config needed)
**Blocks:** None
**Target Coverage:** 95%

### Test Priority Matrix

Based on complexity and business criticality:

| Priority | Component/Route | Type | Complexity | Files to Create |
|----------|----------------|------|------------|-----------------|
| **P0** | BudgetVersionSelector | Component | Medium | `tests/components/BudgetVersionSelector.test.tsx` |
| **P0** | DataTable | Component | High | `tests/components/DataTable.test.tsx` |
| **P0** | useBudgetVersions | Hook | Medium | `tests/hooks/api/useBudgetVersions.test.ts` |
| **P0** | useDHG | Hook | High | `tests/hooks/api/useDHG.test.ts` |
| **P1** | Dashboard route | Route | High | `tests/routes/dashboard.test.tsx` |
| **P1** | DHG route | Route | High | `tests/routes/planning/dhg.test.tsx` |
| **P1** | Budget route | Route | High | `tests/routes/consolidation/budget.test.tsx` |
| **P1** | FormDialog | Component | Medium | `tests/components/FormDialog.test.tsx` |
| **P2** | Charts | Components | Medium | `tests/components/charts/*.test.tsx` |
| **P2** | Grid renderers | Components | Low | `tests/components/grid/*.test.tsx` |
| **P3** | UI primitives | Components | Low | `tests/components/ui/*.test.tsx` |

### Frontend Coverage Verification

**After each component/hook test:**
```bash
cd frontend
pnpm test -- --coverage --run tests/components/ComponentName.test.tsx
# Verify 95%+ coverage for that component
```

**Final verification:**
```bash
pnpm test -- --coverage --run

# Check coverage summary in terminal
# Open coverage/index.html for detailed report
# Verify overall coverage >= 95%
```

---

## Execution Timeline

### Phase 1: Quick Fixes (Parallel) - Days 1-2

**Day 1 (4 hours):**
- **AM:** WS1 (Frontend quick fixes) + WS2 (Backend quick fixes) - 2 hours each
- **PM:** WS3 (Backend type errors) - 4 hours

**Checkpoint 1 (End of Day 1):**
```bash
# Frontend
cd frontend && pnpm lint && pnpm typecheck

# Backend
cd backend && .venv/bin/ruff check . && .venv/bin/mypy .

# Expected: 0 errors
```

---

### Phase 2: Test Coverage (Parallel) - Days 2-10

**Days 2-5 (Backend P0 - DHG, Consolidation, Revenue, Cost):**
- Day 2: DHG Service tests (95% coverage)
- Day 3: Consolidation Service tests (95% coverage)
- Day 4: Revenue Service tests (95% coverage)
- Day 5: Cost Service tests (95% coverage)

**Days 2-5 (Frontend P0 - Critical components/hooks):**
- Day 2: BudgetVersionSelector + DataTable tests
- Day 3: useBudgetVersions + useDHG hooks
- Day 4: useConsolidation + useRevenue hooks
- Day 5: Dashboard route tests

**Checkpoint 2 (End of Day 5):**
```bash
# Backend
PYTHONPATH=. .venv/bin/pytest tests/ --cov=app/services --cov-report=term
# Expected: DHG, Consolidation, Revenue, Cost services >= 95%

# Frontend
pnpm test -- --coverage --run
# Expected: Critical components/hooks >= 95%
```

---

**Days 6-8 (Backend P1 - KPI, APIs):**
- Day 6: KPI Service tests (95% coverage)
- Day 7: Consolidation API tests (95% coverage)
- Day 8: Analysis API tests (95% coverage)

**Days 6-8 (Frontend P1 - Routes):**
- Day 6: DHG route tests
- Day 7: Budget route tests
- Day 8: FormDialog tests

**Checkpoint 3 (End of Day 8):**
```bash
# Backend
PYTHONPATH=. .venv/bin/pytest tests/ --cov=app --cov-report=term
# Expected: Overall backend >= 85%

# Frontend
pnpm test -- --coverage --run
# Expected: Overall frontend >= 85%
```

---

**Days 9-10 (Final Push to 95%):**
- Day 9: Backend P2 (Strategic, Dashboard, Integrations) - 90% coverage
- Day 10: Frontend P2-P3 (Charts, Grid, UI) - 90% coverage

**Final Checkpoint (End of Day 10):**
```bash
# Backend
PYTHONPATH=. .venv/bin/pytest tests/ -v --cov=app --cov-report=term --cov-report=html
# Expected: Overall >= 95%

# Frontend
pnpm test -- --coverage --run
# Expected: Overall >= 95%

# CI/CD simulation
cd frontend && pnpm lint && pnpm typecheck && pnpm test -- --run --coverage
cd backend && .venv/bin/ruff check . && .venv/bin/mypy . && PYTHONPATH=. .venv/bin/pytest tests/ --cov=app

# Expected: ALL PASS
```

---

## Success Criteria

### P0 Blockers (Must Pass)
- [ ] ESLint runs without errors
- [ ] Ruff linting: 0 errors
- [ ] mypy type checking: 0 errors
- [ ] All 3 API routers registered and accessible
- [ ] Docker health check uses curl (no requests dependency)
- [ ] pandas installed in test dependencies

### P1 Infrastructure (Must Pass)
- [ ] Frontend coverage configuration active
- [ ] Code splitting reduces bundle to <500KB per chunk
- [ ] All routes lazy-loaded via TanStack Router

### P2-P3 Coverage (Must Pass for 95% Target)
- [ ] Backend overall coverage: >= 95%
- [ ] Frontend overall coverage: >= 95%
- [ ] DHG Service: >= 95% coverage
- [ ] Consolidation Service: >= 95% coverage
- [ ] Revenue Service: >= 95% coverage
- [ ] Cost Service: >= 95% coverage
- [ ] KPI Service: >= 95% coverage
- [ ] All API endpoints: >= 95% coverage
- [ ] Critical frontend components: >= 95% coverage
- [ ] API hooks: >= 95% coverage
- [ ] Critical routes: >= 90% coverage

### CI/CD Pipeline (Must Pass)
- [ ] GitHub Actions workflow passes all checks
- [ ] No linting warnings
- [ ] No type errors
- [ ] All tests pass (unit + E2E)
- [ ] Coverage thresholds met

---

## Post-Completion Verification

**Final Checklist:**

```bash
# 1. Clean install
cd frontend && rm -rf node_modules pnpm-lock.yaml && pnpm install
cd backend && rm -rf .venv && python3 -m venv .venv && .venv/bin/pip install -e ".[dev]"

# 2. Lint & Type Check
cd frontend && pnpm lint && pnpm typecheck
cd backend && .venv/bin/ruff check . && .venv/bin/mypy .

# 3. Test Coverage
cd frontend && pnpm test -- --coverage --run
cd backend && PYTHONPATH=. .venv/bin/pytest tests/ --cov=app --cov-report=term

# 4. E2E Tests
cd frontend && pnpm test:e2e

# 5. Build
cd frontend && pnpm build
cd backend && docker build -t efir-backend:latest .

# 6. Docker Health Check
docker run -d --name efir-backend-test -p 8000:8000 efir-backend:latest
sleep 30
docker inspect --format='{{.State.Health.Status}}' efir-backend-test
# Expected: healthy

docker stop efir-backend-test && docker rm efir-backend-test
```

**All checks must pass before deployment.**

---

## Critical Files Reference

**Phase 1 (P0) Files:**
1. `frontend/package.json` - Add @eslint/js
2. `frontend/vitest.config.ts` - Add coverage config
3. `frontend/vite.config.ts` - Add code splitting
4. `backend/app/api/v1/integrations.py` - Fix Ruff errors
5. `backend/app/main.py` - Register routers
6. `backend/app/api/v1/__init__.py` - Export routers
7. `backend/Dockerfile` - Fix health check
8. `backend/pyproject.toml` - Add pandas
9. `backend/app/api/v1/consolidation.py` - Fix type errors

**Phase 2 (P2-P3) New Files:**
- **Backend:** 9+ new test files in `tests/services/` and `tests/api/`
- **Frontend:** 30+ new test files in `tests/components/`, `tests/hooks/`, `tests/routes/`

---

## Notes

- **User Priorities:** DHG Workforce Planning, Budget Consolidation, Revenue/Cost Planning
- **Coverage Strategy:** Prioritize business-critical modules (DHG, Consolidation) for 95%, accept 90% for less critical (Strategic, Dashboard)
- **Parallel Execution:** All 5 workstreams can run simultaneously with zero file conflicts
- **EFIR Standards:** 80% minimum required, 95% is production-grade target
- **Timeline Flexibility:** 7-10 days realistic for comprehensive 95% coverage; can compress to 5-7 days for 90%

---

**Plan Status:** Ready for execution
**Next Step:** Begin Phase 1 (WS1 + WS2 + WS3 in parallel)
