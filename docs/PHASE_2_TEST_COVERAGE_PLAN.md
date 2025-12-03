# Phase 2: Test Coverage Implementation Plan

**EFIR Budget Planning Application - QA & Validation Agent**

**Document Version:** 1.0
**Date:** 2025-12-02
**Target Coverage:** 95% (lines, branches, functions, statements)
**Current Coverage:** Backend 50%, Frontend <5%

---

## Executive Summary

This document provides a comprehensive, prioritized test implementation plan to achieve 95% code coverage across the EFIR Budget Planning Application. The plan follows EFIR Development Standards and includes detailed test scenarios, mock requirements, and time estimates.

### Current State Analysis

**Backend Coverage (50% overall):**
- **Critical Services (P0 - Need immediate attention):**
  - `dhg_service.py`: 15.6% → Target 95%
  - `consolidation_service.py`: 16.6% → Target 95%
  - `revenue_service.py`: 14.8% → Target 95%
  - `cost_service.py`: 12.6% → Target 95%

- **Well-Covered (Maintain):**
  - Calculation engines: 100% (dhg, enrollment, kpi, revenue calculators)
  - Models: 93-100% (configuration, planning, consolidation)
  - Schemas: 89-100% (all Pydantic models)

**Frontend Coverage (<5% overall):**
- **Critical Components (P0):**
  - `BudgetVersionSelector.tsx`: 0% → Target 95%
  - `DataTable.tsx`: 0% → Target 95%
  - Hook: `useBudgetVersions`: 0% → Target 95%
  - Hook: `useDHG`: 0% → Target 95%

### Test Execution Summary

**Current Test Results (Backend):**
- Total Tests: 293
- Passed: 244
- Failed: 7
- Errors: 39 (database setup issues)
- Skipped: 3

**Issues Identified:**
1. Database foreign key errors (auth.users table missing in test setup)
2. Missing test coverage for service layer methods
3. E2E tests failing due to Playwright configuration
4. Frontend tests have act() warnings

---

## Priority Matrix

### P0 (Critical - Week 1-2)
**Business Impact:** High - Core calculation and consolidation logic
**Coverage Gap:** 80%+
**Time Estimate:** 80 hours

| Module | Current | Target | Gap | Hours |
|--------|---------|--------|-----|-------|
| DHG Service | 15.6% | 95% | 79.4% | 24h |
| Consolidation Service | 16.6% | 95% | 78.4% | 20h |
| Revenue Service | 14.8% | 95% | 80.2% | 16h |
| Cost Service | 12.6% | 95% | 82.4% | 20h |

### P1 (High - Week 3)
**Business Impact:** High - Supporting services
**Coverage Gap:** 70%+
**Time Estimate:** 48 hours

| Module | Current | Target | Gap | Hours |
|--------|---------|--------|-----|-------|
| Integration Services | 18-23% | 95% | 72-77% | 24h |
| KPI Service | 14.2% | 95% | 80.8% | 12h |
| Dashboard Service | 15.7% | 95% | 79.3% | 12h |

### P2 (Medium - Week 4)
**Business Impact:** Medium - Supporting infrastructure
**Coverage Gap:** 50%+
**Time Estimate:** 40 hours

| Module | Current | Target | Gap | Hours |
|--------|---------|--------|-----|-------|
| API Endpoints | 20-38% | 95% | 57-75% | 20h |
| Middleware/Auth | 40-73% | 95% | 22-55% | 12h |
| Base Service | 16.2% | 95% | 78.8% | 8h |

### P3 (Low - Week 5)
**Business Impact:** Low - Already well-covered
**Coverage Gap:** <20%
**Time Estimate:** 16 hours

| Module | Current | Target | Gap | Hours |
|--------|---------|--------|-----|-------|
| Validators | 40-95% | 95% | 0-55% | 8h |
| Models/Schemas (gaps) | 81-93% | 95% | 2-14% | 8h |

---

## Backend Test Implementation Plan

### P0.1: DHG Service Tests (24 hours)

**File:** `backend/tests/services/test_dhg_service.py`
**Current Coverage:** 15.6% (27 of 173 lines)
**Target Coverage:** 95% (164+ lines)

#### Test Scenarios

**1. DHG Subject Hours Calculation (6 hours)**
```python
# Test: calculate_dhg_subject_hours - standard case
# Test: calculate_dhg_subject_hours - missing class structure
# Test: calculate_dhg_subject_hours - missing subject hours matrix
# Test: calculate_dhg_subject_hours - partial recalculation
# Test: calculate_dhg_subject_hours - zero classes
# Test: calculate_dhg_subject_hours - bilingual adjustments
```

**2. Teacher Requirement Calculation (6 hours)**
```python
# Test: calculate_teacher_requirements - secondary levels
# Test: calculate_teacher_requirements - primary levels
# Test: calculate_teacher_requirements - mixed levels
# Test: calculate_teacher_requirements - HSA allocation
# Test: calculate_teacher_requirements - exceeds HSA limit
# Test: calculate_teacher_requirements - zero DHG hours
```

**3. Teacher Allocation Management (6 hours)**
```python
# Test: create_teacher_allocation - AEFE detached
# Test: create_teacher_allocation - AEFE funded
# Test: create_teacher_allocation - local teacher
# Test: update_teacher_allocation - FTE change
# Test: delete_teacher_allocation - soft delete
# Test: get_teacher_allocations - with filters
```

**4. Gap Analysis (TRMD) (6 hours)**
```python
# Test: calculate_gap_analysis - deficit scenario
# Test: calculate_gap_analysis - surplus scenario
# Test: calculate_gap_analysis - exact match
# Test: calculate_gap_analysis - by subject
# Test: calculate_gap_analysis - HSA coverage
# Test: calculate_gap_analysis - validation errors
```

#### Mock Requirements
```python
# Fixtures needed
@pytest.fixture
def mock_budget_version():
    """Budget version with valid configuration"""

@pytest.fixture
def mock_class_structure():
    """Class structure: 6ème(6), 5ème(6), 4ème(5), 3ème(4)"""

@pytest.fixture
def mock_subject_hours_matrix():
    """Subject hours for Collège (Math, French, History, etc.)"""

@pytest.fixture
def mock_teacher_cost_params():
    """AEFE and local teacher cost parameters"""

@pytest.fixture
def mock_teacher_allocations():
    """AEFE detached (5), AEFE funded (3), Local (8)"""
```

#### Expected Coverage Gains
- **Lines:** 27 → 164 (137 new lines, +79.4%)
- **Branches:** 5 → 48 (43 new branches)
- **Functions:** 3 → 18 (15 new functions)

---

### P0.2: Consolidation Service Tests (20 hours)

**File:** `backend/tests/services/test_consolidation_service.py`
**Current Coverage:** 16.6% (Need to create comprehensive tests)
**Target Coverage:** 95%

#### Test Scenarios

**1. Budget Consolidation (8 hours)**
```python
# Test: consolidate_budget - complete budget
# Test: consolidate_budget - revenue aggregation
# Test: consolidate_budget - personnel cost aggregation
# Test: consolidate_budget - operating cost aggregation
# Test: consolidate_budget - CapEx aggregation
# Test: consolidate_budget - empty version
# Test: consolidate_budget - partial data
# Test: consolidate_budget - recalculation
```

**2. Approval Workflow (6 hours)**
```python
# Test: submit_budget - WORKING → SUBMITTED
# Test: submit_budget - already submitted error
# Test: approve_budget - SUBMITTED → APPROVED
# Test: approve_budget - not submitted error
# Test: reject_budget - SUBMITTED → WORKING
# Test: supersede_budget - APPROVED → SUPERSEDED
# Test: workflow_validation - status transitions
```

**3. Version Validation (4 hours)**
```python
# Test: validate_version_completeness - all modules present
# Test: validate_version_completeness - missing enrollment
# Test: validate_version_completeness - missing DHG
# Test: validate_version_balance - revenue = costs + surplus
# Test: validate_version_balance - budget deficit
# Test: validate_account_codes - PCG compliance
```

**4. Line Item Rollup (2 hours)**
```python
# Test: rollup_by_category - revenue categories
# Test: rollup_by_category - cost categories
# Test: rollup_by_account_code - PCG grouping
# Test: rollup_by_trimester - period distribution
```

#### Mock Requirements
```python
@pytest.fixture
def mock_complete_budget():
    """Budget with revenue, personnel, operating, CapEx"""

@pytest.fixture
def mock_revenue_plan():
    """Tuition (70110-70130), DAI (70500), Registration (70600)"""

@pytest.fixture
def mock_personnel_costs():
    """Teaching (64110), ATSEM (64210), Admin (64310)"""

@pytest.fixture
def mock_operating_costs():
    """Utilities (60610), Supplies (60620), Maintenance (61520)"""

@pytest.fixture
def mock_capex_plan():
    """Equipment (21310), Renovations (21320)"""
```

#### Expected Coverage Gains
- **Lines:** ~30 → 180 (150 new lines, +78.4%)
- **Branches:** ~8 → 60 (52 new branches)
- **Functions:** ~4 → 20 (16 new functions)

---

### P0.3: Revenue Service Tests (16 hours)

**File:** `backend/tests/services/test_revenue_service.py`
**Current Coverage:** 14.8%
**Target Coverage:** 95%

#### Test Scenarios

**1. Revenue Calculation (8 hours)**
```python
# Test: calculate_tuition_revenue - French nationality
# Test: calculate_tuition_revenue - Saudi nationality (HT)
# Test: calculate_tuition_revenue - Other nationality
# Test: calculate_tuition_revenue - sibling discount (3rd+ child)
# Test: calculate_tuition_revenue - no discount on DAI
# Test: calculate_tuition_revenue - trimester distribution (40/30/30)
# Test: calculate_total_revenue - all fee categories
# Test: calculate_revenue_by_level - enrollment-driven
```

**2. Fee Structure Application (4 hours)**
```python
# Test: apply_fee_structure - standard fees
# Test: apply_fee_structure - bilingual premium
# Test: apply_fee_structure - baccalauréat premium
# Test: apply_fee_structure - fiscal year transition
# Test: apply_fee_structure - missing fee structure error
```

**3. Revenue Plan Management (4 hours)**
```python
# Test: create_revenue_entry - manual entry
# Test: create_revenue_entry - calculated entry
# Test: update_revenue_entry - amount override
# Test: delete_revenue_entry - soft delete
# Test: get_revenue_by_account - PCG account code
# Test: get_revenue_by_trimester - period filtering
```

#### Mock Requirements
```python
@pytest.fixture
def mock_enrollment_plan():
    """Enrollment: Maternelle(120), Élémentaire(320), Collège(260), Lycée(180)"""

@pytest.fixture
def mock_fee_structure():
    """Fees by level, nationality, category (tuition, DAI, registration)"""

@pytest.fixture
def mock_sibling_data():
    """Students with sibling relationships for discount calculation"""

@pytest.fixture
def mock_trimester_distribution():
    """T1: 40%, T2: 30%, T3: 30% revenue distribution"""
```

#### Expected Coverage Gains
- **Lines:** ~25 → 160 (135 new lines, +80.2%)
- **Branches:** ~6 → 55 (49 new branches)
- **Functions:** ~3 → 16 (13 new functions)

---

### P0.4: Cost Service Tests (20 hours)

**File:** `backend/tests/services/test_cost_service.py`
**Current Coverage:** 12.6%
**Target Coverage:** 95%

#### Test Scenarios

**1. Personnel Cost Calculation (10 hours)**
```python
# Test: calculate_teaching_costs - AEFE detached (PRRD)
# Test: calculate_teaching_costs - AEFE funded (zero cost)
# Test: calculate_teaching_costs - local teachers (SAR)
# Test: calculate_teaching_costs - HSA overtime costs
# Test: calculate_teaching_costs - ATSEM costs (Maternelle)
# Test: calculate_administrative_costs - admin staff
# Test: calculate_administrative_costs - support staff
# Test: calculate_personnel_costs_total - all categories
```

**2. Operating Cost Calculation (6 hours)**
```python
# Test: calculate_facility_costs - enrollment-driven
# Test: calculate_facility_costs - per-student costs
# Test: calculate_utility_costs - square meter driver
# Test: calculate_supply_costs - student count driver
# Test: calculate_maintenance_costs - fixed + variable
# Test: calculate_operating_costs_total - all accounts
```

**3. Cost Driver Management (4 hours)**
```python
# Test: create_cost_entry - driver-based calculation
# Test: create_cost_entry - manual override
# Test: update_cost_driver - enrollment change cascade
# Test: update_cost_driver - FTE change cascade
# Test: delete_cost_entry - soft delete
# Test: recalculate_costs - version-wide update
```

#### Mock Requirements
```python
@pytest.fixture
def mock_teacher_allocations():
    """AEFE detached (15 FTE), Local (25 FTE), ATSEM (8 FTE)"""

@pytest.fixture
def mock_teacher_cost_params():
    """PRRD: 41,863 EUR/teacher, Local: 12,500 SAR/month"""

@pytest.fixture
def mock_enrollment_drivers():
    """Total students: 880, Square meters: 12,000"""

@pytest.fixture
def mock_cost_drivers():
    """Utilities: 50 SAR/sqm, Supplies: 500 SAR/student"""
```

#### Expected Coverage Gains
- **Lines:** ~22 → 175 (153 new lines, +82.4%)
- **Branches:** ~5 → 58 (53 new branches)
- **Functions:** ~3 → 18 (15 new functions)

---

## Frontend Test Implementation Plan

### P0.5: BudgetVersionSelector Component Tests (8 hours)

**File:** `frontend/tests/components/BudgetVersionSelector.test.tsx`
**Current Coverage:** 0%
**Target Coverage:** 95%

#### Test Scenarios

```typescript
describe('BudgetVersionSelector', () => {
  // 1. Rendering tests (2 hours)
  it('should render loading state')
  it('should render empty state when no versions')
  it('should render versions list')
  it('should display version name and fiscal year')
  it('should display status badges correctly')
  it('should apply custom className')

  // 2. Interaction tests (3 hours)
  it('should call onChange when version selected')
  it('should display selected version correctly')
  it('should show correct badge variant by status')
  it('should disable selector when loading')
  it('should handle keyboard navigation')

  // 3. Data tests (2 hours)
  it('should fetch versions on mount')
  it('should handle API error gracefully')
  it('should sort versions by fiscal year')
  it('should filter out deleted versions')

  // 4. Edge cases (1 hour)
  it('should handle undefined value prop')
  it('should handle invalid versionId')
  it('should handle empty versions array')
})
```

#### Mock Requirements
```typescript
// Mock API responses
const mockVersions = {
  items: [
    { id: '1', name: 'Budget 2024', fiscal_year: 2024, status: 'WORKING' },
    { id: '2', name: 'Budget 2024 V2', fiscal_year: 2024, status: 'SUBMITTED' },
    { id: '3', name: 'Budget 2023', fiscal_year: 2023, status: 'APPROVED' },
  ],
  total: 3,
  page: 1,
  page_size: 50,
}

// Mock TanStack Query
vi.mock('@/hooks/api/useBudgetVersions', () => ({
  useBudgetVersions: vi.fn(() => ({
    data: mockVersions,
    isLoading: false,
    error: null,
  })),
}))
```

---

### P0.6: useBudgetVersions Hook Tests (6 hours)

**File:** `frontend/tests/hooks/useBudgetVersions.test.ts`
**Current Coverage:** 0%
**Target Coverage:** 95%

#### Test Scenarios

```typescript
describe('useBudgetVersions', () => {
  // 1. Query tests (2 hours)
  it('should fetch versions on mount')
  it('should use correct query key')
  it('should handle pagination parameters')
  it('should cache results correctly')

  // 2. Mutation tests (3 hours)
  it('should create budget version and invalidate cache')
  it('should update budget version and invalidate detail')
  it('should delete budget version and invalidate list')
  it('should submit budget version and show toast')
  it('should approve budget version and update status')
  it('should clone budget version with new name')

  // 3. Error handling (1 hour)
  it('should handle create error with toast')
  it('should handle network error gracefully')
  it('should retry failed requests')
})
```

#### Mock Requirements
```typescript
// Mock API service
vi.mock('@/services/budget-versions', () => ({
  budgetVersionsApi: {
    getAll: vi.fn(),
    getById: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    delete: vi.fn(),
    submit: vi.fn(),
    approve: vi.fn(),
    clone: vi.fn(),
  },
}))

// Mock toast notifications
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

// QueryClient wrapper for tests
const queryClient = new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
})
```

---

### P0.7: DataTable Component Tests (10 hours)

**File:** `frontend/tests/components/DataTable.test.tsx`
**Current Coverage:** 0% (needs to be created)
**Target Coverage:** 95%

#### Test Scenarios

```typescript
describe('DataTable', () => {
  // 1. Grid rendering tests (3 hours)
  it('should render AG Grid with column definitions')
  it('should display row data correctly')
  it('should apply default column definitions')
  it('should handle empty data gracefully')
  it('should show loading state')

  // 2. Editing tests (4 hours)
  it('should enable cell editing when editable')
  it('should call onCellValueChanged with updated data')
  it('should validate cell input')
  it('should revert on invalid input')
  it('should handle row-level editing')

  // 3. Sorting and filtering tests (2 hours)
  it('should sort columns on header click')
  it('should filter data with column filters')
  it('should clear filters')
  it('should maintain sort state')

  // 4. Custom renderers tests (1 hour)
  it('should render currency cells with formatter')
  it('should render date cells correctly')
  it('should render status badges')
  it('should render action buttons')
})
```

---

### P0.8: useDHG Hook Tests (6 hours)

**File:** `frontend/tests/hooks/useDHG.test.ts`
**Current Coverage:** 0% (needs to be created)
**Target Coverage:** 95%

#### Test Scenarios

```typescript
describe('useDHG', () => {
  // 1. Calculation trigger tests (2 hours)
  it('should fetch DHG subject hours')
  it('should trigger DHG calculation')
  it('should fetch teacher requirements')
  it('should handle calculation errors')

  // 2. Teacher allocation tests (2 hours)
  it('should create teacher allocation')
  it('should update teacher allocation FTE')
  it('should delete teacher allocation')
  it('should fetch gap analysis (TRMD)')

  // 3. Integration tests (2 hours)
  it('should invalidate cache after calculation')
  it('should refetch on version change')
  it('should handle optimistic updates')
  it('should show toast on success/error')
})
```

---

## Test Infrastructure Setup

### Backend Test Setup Fixes (4 hours)

**Issue:** Database foreign key errors (auth.users table)

**Fix 1: Create test database schema**
```python
# backend/tests/conftest.py

@pytest.fixture(scope="session")
async def setup_test_db():
    """Create test database with auth schema"""
    async with engine.begin() as conn:
        # Create auth schema for Supabase compatibility
        await conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))

        # Create auth.users table
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS auth.users (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                email VARCHAR(255) UNIQUE NOT NULL,
                encrypted_password VARCHAR(255),
                email_confirmed_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            )
        """))

        # Create test user
        await conn.execute(text("""
            INSERT INTO auth.users (id, email, email_confirmed_at)
            VALUES (
                '00000000-0000-0000-0000-000000000001',
                'test@efir.sa',
                NOW()
            )
            ON CONFLICT DO NOTHING
        """))

        # Create public schema tables
        await conn.run_sync(Base.metadata.create_all)
```

**Fix 2: Update pytest.ini for async support**
```ini
[pytest]
asyncio_default_fixture_loop_scope = function
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    -v
    --strict-markers
    --cov=app
    --cov-report=term
    --cov-report=html
    --cov-report=json
    --cov-fail-under=80
markers =
    asyncio: mark test as async
    integration: mark test as integration test
    slow: mark test as slow running
```

### Frontend Test Setup Fixes (2 hours)

**Issue:** Playwright configuration errors, act() warnings

**Fix 1: Separate Vitest and Playwright configs**
```typescript
// vitest.config.ts - Unit tests only
export default defineConfig({
  test: {
    environment: 'jsdom',
    setupFiles: ['src/setupTests.ts'],
    globals: true,
    include: ['src/**/*.test.{ts,tsx}'],
    exclude: ['tests/e2e/**'],
  },
})
```

```typescript
// playwright.config.ts - E2E tests only
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
})
```

**Fix 2: Wrap TanStack Router tests in act()**
```typescript
// src/setupTests.ts
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(() => {
  cleanup()
})

// Helper for async act
export const waitFor = async (callback: () => void, timeout = 1000) => {
  await act(async () => {
    await new Promise((resolve) => setTimeout(resolve, timeout))
    callback()
  })
}
```

---

## Test Templates

### Backend Service Test Template

```python
"""
Tests for {ServiceName} service.

Covers:
- CRUD operations
- Business logic validation
- Error handling
- Edge cases
"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.{service_module} import {ServiceName}
from app.services.exceptions import ValidationError, BusinessRuleError, NotFoundError


@pytest.fixture
async def service(db_session: AsyncSession) -> {ServiceName}:
    """Create service instance with test database session."""
    return {ServiceName}(db_session)


@pytest.fixture
async def mock_{entity}(db_session: AsyncSession):
    """Create mock {entity} for testing."""
    # Create and return mock entity
    pass


class Test{ServiceName}CRUD:
    """Test CRUD operations."""

    async def test_create_{entity}_success(
        self, service: {ServiceName}, mock_data: dict
    ):
        """Test successful {entity} creation."""
        result = await service.create_{entity}(**mock_data)

        assert result.id is not None
        assert result.{field} == mock_data["{field}"]

    async def test_create_{entity}_validation_error(
        self, service: {ServiceName}
    ):
        """Test {entity} creation with invalid data."""
        with pytest.raises(ValidationError) as exc_info:
            await service.create_{entity}(
                {invalid_field}="invalid"
            )

        assert "{field}" in str(exc_info.value)

    async def test_get_{entity}_by_id(
        self, service: {ServiceName}, mock_{entity}
    ):
        """Test retrieve {entity} by ID."""
        result = await service.get_{entity}_by_id(mock_{entity}.id)

        assert result.id == mock_{entity}.id

    async def test_get_{entity}_not_found(
        self, service: {ServiceName}
    ):
        """Test retrieve non-existent {entity}."""
        with pytest.raises(NotFoundError):
            await service.get_{entity}_by_id(uuid.uuid4())

    async def test_update_{entity}_success(
        self, service: {ServiceName}, mock_{entity}
    ):
        """Test successful {entity} update."""
        updated = await service.update_{entity}(
            mock_{entity}.id,
            {field}="new_value"
        )

        assert updated.{field} == "new_value"

    async def test_delete_{entity}_success(
        self, service: {ServiceName}, mock_{entity}
    ):
        """Test soft delete {entity}."""
        await service.delete_{entity}(mock_{entity}.id)

        # Verify soft delete
        result = await service.get_{entity}_by_id(mock_{entity}.id)
        assert result.deleted_at is not None


class Test{ServiceName}BusinessLogic:
    """Test business logic and calculations."""

    async def test_calculate_{operation}_standard_case(
        self, service: {ServiceName}, mock_data
    ):
        """Test {operation} calculation with standard inputs."""
        result = await service.calculate_{operation}(**mock_data)

        assert result.{calculated_field} == expected_value

    async def test_calculate_{operation}_edge_case(
        self, service: {ServiceName}
    ):
        """Test {operation} calculation with edge case."""
        result = await service.calculate_{operation}(
            {edge_case_params}
        )

        assert result.{field} == expected_edge_value

    async def test_calculate_{operation}_business_rule_error(
        self, service: {ServiceName}
    ):
        """Test {operation} violates business rule."""
        with pytest.raises(BusinessRuleError) as exc_info:
            await service.calculate_{operation}(
                {invalid_business_rule_params}
            )

        assert "business rule violation" in str(exc_info.value).lower()
```

### Frontend Component Test Template

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { {ComponentName} } from '@/components/{ComponentName}'

// Mock dependencies
vi.mock('@/hooks/api/{hookName}', () => ({
  {hookName}: vi.fn(),
}))

describe('{ComponentName}', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const renderComponent = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <{ComponentName} {...props} />
      </QueryClientProvider>
    )
  }

  describe('Rendering', () => {
    it('should render without crashing', () => {
      renderComponent()
      expect(screen.getByRole('{role}')).toBeInTheDocument()
    })

    it('should display loading state', () => {
      vi.mocked({hookName}).mockReturnValue({
        data: null,
        isLoading: true,
        error: null,
      })

      renderComponent()
      expect(screen.getByText(/loading/i)).toBeInTheDocument()
    })

    it('should display error state', () => {
      vi.mocked({hookName}).mockReturnValue({
        data: null,
        isLoading: false,
        error: new Error('Test error'),
      })

      renderComponent()
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  describe('Interactions', () => {
    it('should call handler on user action', async () => {
      const user = userEvent.setup()
      const onAction = vi.fn()

      renderComponent({ onAction })

      const button = screen.getByRole('button', { name: /action/i })
      await user.click(button)

      expect(onAction).toHaveBeenCalledTimes(1)
    })
  })

  describe('Data Display', () => {
    it('should display data correctly', () => {
      const mockData = { /* ... */ }
      vi.mocked({hookName}).mockReturnValue({
        data: mockData,
        isLoading: false,
        error: null,
      })

      renderComponent()

      expect(screen.getByText(mockData.field)).toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle empty data', () => {
      vi.mocked({hookName}).mockReturnValue({
        data: [],
        isLoading: false,
        error: null,
      })

      renderComponent()
      expect(screen.getByText(/no data/i)).toBeInTheDocument()
    })
  })
})
```

### Frontend Hook Test Template

```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { toast } from 'sonner'

import { {hookName} } from '@/hooks/api/{hookName}'

// Mock API service
vi.mock('@/services/{serviceName}', () => ({
  {apiName}: {
    {method}: vi.fn(),
  },
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

describe('{hookName}', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )

  describe('Query', () => {
    it('should fetch data on mount', async () => {
      const mockData = { /* ... */ }
      vi.mocked({apiName}.{method}).mockResolvedValue(mockData)

      const { result } = renderHook(() => {hookName}(), { wrapper })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockData)
      expect({apiName}.{method}).toHaveBeenCalledTimes(1)
    })

    it('should handle fetch error', async () => {
      vi.mocked({apiName}.{method}).mockRejectedValue(
        new Error('Fetch failed')
      )

      const { result } = renderHook(() => {hookName}(), { wrapper })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(result.current.error).toBeInstanceOf(Error)
    })
  })

  describe('Mutation', () => {
    it('should mutate data successfully', async () => {
      const mockResult = { /* ... */ }
      vi.mocked({apiName}.{mutationMethod}).mockResolvedValue(mockResult)

      const { result } = renderHook(() => {useMutationHook}(), { wrapper })

      result.current.mutate({ /* data */ })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(result.current.data).toEqual(mockResult)
      expect(toast.success).toHaveBeenCalled()
    })

    it('should invalidate queries on success', async () => {
      const spy = vi.spyOn(queryClient, 'invalidateQueries')

      const { result } = renderHook(() => {useMutationHook}(), { wrapper })

      result.current.mutate({ /* data */ })

      await waitFor(() => expect(result.current.isSuccess).toBe(true))

      expect(spy).toHaveBeenCalled()
    })

    it('should show error toast on failure', async () => {
      vi.mocked({apiName}.{mutationMethod}).mockRejectedValue(
        new Error('Mutation failed')
      )

      const { result } = renderHook(() => {useMutationHook}(), { wrapper })

      result.current.mutate({ /* data */ })

      await waitFor(() => expect(result.current.isError).toBe(true))

      expect(toast.error).toHaveBeenCalledWith(
        expect.stringContaining('failed')
      )
    })
  })
})
```

---

## Fixture & Mock Data Library

### Backend Fixtures

**File:** `backend/tests/fixtures/__init__.py`

```python
"""
Centralized test fixtures and mock data for EFIR Budget Planning tests.

Organized by domain:
- Configuration fixtures
- Planning fixtures
- Consolidation fixtures
- Analysis fixtures
"""

import uuid
from datetime import datetime
from decimal import Decimal

import pytest


# ==============================================================================
# Configuration Fixtures
# ==============================================================================

@pytest.fixture
def mock_academic_levels():
    """Mock academic levels: PS → Terminale."""
    return [
        {
            "id": uuid.uuid4(),
            "code": "PS",
            "name": "Petite Section",
            "cycle_id": "maternelle_cycle_id",
            "sort_order": 1,
        },
        {
            "id": uuid.uuid4(),
            "code": "MS",
            "name": "Moyenne Section",
            "cycle_id": "maternelle_cycle_id",
            "sort_order": 2,
        },
        # ... (all levels)
    ]


@pytest.fixture
def mock_subject_hours_matrix():
    """Mock subject hours matrix for Collège."""
    return [
        {
            "subject_code": "MATH",
            "level_code": "6EME",
            "hours_per_week": Decimal("4.5"),
        },
        {
            "subject_code": "FR",
            "level_code": "6EME",
            "hours_per_week": Decimal("4.5"),
        },
        # ... (all subjects × levels)
    ]


@pytest.fixture
def mock_fee_structure():
    """Mock fee structure for FY2024."""
    return [
        {
            "level_code": "6EME",
            "fee_category": "TUITION",
            "nationality": "FRENCH",
            "amount_sar": Decimal("28500.00"),
            "fiscal_year": 2024,
        },
        # ... (all levels × categories × nationalities)
    ]


@pytest.fixture
def mock_teacher_cost_params():
    """Mock teacher cost parameters."""
    return {
        "aefe_detached": {
            "prrd_eur": Decimal("41863.00"),
            "social_charges_pct": Decimal("0.42"),
            "eur_to_sar": Decimal("4.25"),
        },
        "local": {
            "monthly_salary_sar": Decimal("12500.00"),
            "months": 12,
            "social_charges_pct": Decimal("0.11"),
        },
    }


# ==============================================================================
# Planning Fixtures
# ==============================================================================

@pytest.fixture
def mock_enrollment_plan():
    """Mock enrollment plan (880 students)."""
    return [
        {"level_code": "PS", "students": 24, "nationality": "FRENCH"},
        {"level_code": "PS", "students": 6, "nationality": "SAUDI"},
        # ... (all levels × nationalities)
    ]


@pytest.fixture
def mock_class_structure():
    """Mock class structure based on enrollment."""
    return [
        {"level_code": "PS", "num_classes": 2, "avg_class_size": 15},
        {"level_code": "MS", "num_classes": 2, "avg_class_size": 16},
        # ... (all levels)
    ]


@pytest.fixture
def mock_dhg_subject_hours():
    """Mock DHG subject hours calculation result."""
    return [
        {
            "subject_code": "MATH",
            "level_code": "6EME",
            "num_classes": 6,
            "hours_per_class": Decimal("4.5"),
            "total_hours": Decimal("27.0"),
        },
        # ... (all subjects)
    ]


@pytest.fixture
def mock_teacher_allocations():
    """Mock teacher allocations (TRMD)."""
    return [
        {
            "subject_code": "MATH",
            "category": "AEFE_DETACHED",
            "fte": Decimal("5.33"),
            "standard_hours": Decimal("18.0"),
            "hsa_hours": Decimal("0.94"),
        },
        # ... (all subjects × categories)
    ]


# ==============================================================================
# Consolidation Fixtures
# ==============================================================================

@pytest.fixture
def mock_revenue_plan():
    """Mock revenue plan entries."""
    return [
        {
            "account_code": "70110",
            "description": "Tuition T1",
            "amount_sar": Decimal("10200000.00"),
            "trimester": 1,
        },
        {
            "account_code": "70120",
            "description": "Tuition T2",
            "amount_sar": Decimal("7650000.00"),
            "trimester": 2,
        },
        # ... (all revenue accounts)
    ]


@pytest.fixture
def mock_personnel_cost_plan():
    """Mock personnel cost plan entries."""
    return [
        {
            "account_code": "64110",
            "description": "Teaching Salaries",
            "amount_sar": Decimal("8500000.00"),
        },
        {
            "account_code": "64210",
            "description": "ATSEM Salaries",
            "amount_sar": Decimal("960000.00"),
        },
        # ... (all personnel accounts)
    ]


@pytest.fixture
def mock_operating_cost_plan():
    """Mock operating cost plan entries."""
    return [
        {
            "account_code": "60610",
            "description": "Utilities",
            "amount_sar": Decimal("600000.00"),
        },
        # ... (all operating accounts)
    ]


@pytest.fixture
def mock_capex_plan():
    """Mock CapEx plan entries."""
    return [
        {
            "account_code": "21310",
            "description": "IT Equipment",
            "amount_sar": Decimal("500000.00"),
        },
        # ... (all CapEx accounts)
    ]


# ==============================================================================
# Budget Version Fixtures
# ==============================================================================

@pytest.fixture
async def mock_budget_version(db_session):
    """Create complete budget version for testing."""
    from app.models.configuration import BudgetVersion, BudgetVersionStatus

    version = BudgetVersion(
        id=uuid.uuid4(),
        name="Budget 2024 Test",
        fiscal_year=2024,
        status=BudgetVersionStatus.WORKING,
        created_by_id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
    )

    db_session.add(version)
    await db_session.commit()
    await db_session.refresh(version)

    return version


@pytest.fixture
async def mock_complete_budget(db_session, mock_budget_version):
    """Create complete budget with all modules populated."""
    # Create enrollment
    # Create class structure
    # Create DHG
    # Create revenue
    # Create costs
    # Create CapEx

    return mock_budget_version
```

### Frontend Fixtures

**File:** `frontend/tests/fixtures/index.ts`

```typescript
/**
 * Centralized test fixtures and mock data for EFIR Budget Planning frontend tests.
 */

import { BudgetVersion, EnrollmentData, DHGCalculation } from '@/types/api'

// ==============================================================================
// Budget Version Fixtures
// ==============================================================================

export const mockBudgetVersions: BudgetVersion[] = [
  {
    id: '00000000-0000-0000-0000-000000000001',
    name: 'Budget 2024 Working',
    fiscal_year: 2024,
    status: 'WORKING',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-15T10:30:00Z',
    created_by_id: 'user-1',
    notes: 'Initial budget draft',
  },
  {
    id: '00000000-0000-0000-0000-000000000002',
    name: 'Budget 2024 Submitted',
    fiscal_year: 2024,
    status: 'SUBMITTED',
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-02-01T14:00:00Z',
    created_by_id: 'user-1',
    notes: 'Submitted for approval',
    submitted_at: '2024-02-01T14:00:00Z',
    submitted_by_id: 'user-1',
  },
  {
    id: '00000000-0000-0000-0000-000000000003',
    name: 'Budget 2023 Approved',
    fiscal_year: 2023,
    status: 'APPROVED',
    created_at: '2023-01-01T00:00:00Z',
    updated_at: '2023-03-01T09:00:00Z',
    created_by_id: 'user-1',
    notes: 'Approved budget',
    approved_at: '2023-03-01T09:00:00Z',
    approved_by_id: 'user-2',
  },
]

export const mockBudgetVersionPaginated = {
  items: mockBudgetVersions,
  total: 3,
  page: 1,
  page_size: 50,
  has_next: false,
  has_prev: false,
}

// ==============================================================================
// Enrollment Fixtures
// ==============================================================================

export const mockEnrollmentData: EnrollmentData[] = [
  {
    level_code: '6EME',
    level_name: '6ème',
    french: 60,
    saudi: 20,
    other: 10,
    total: 90,
  },
  {
    level_code: '5EME',
    level_name: '5ème',
    french: 55,
    saudi: 18,
    other: 12,
    total: 85,
  },
  // ... (all levels)
]

// ==============================================================================
// DHG Calculation Fixtures
// ==============================================================================

export const mockDHGCalculation: DHGCalculation = {
  version_id: '00000000-0000-0000-0000-000000000001',
  subject_hours: [
    {
      subject_code: 'MATH',
      subject_name: 'Mathématiques',
      level_code: '6EME',
      num_classes: 6,
      hours_per_class: 4.5,
      total_hours: 27.0,
    },
    // ... (all subjects)
  ],
  teacher_requirements: [
    {
      subject_code: 'MATH',
      total_hours: 96.0,
      standard_hours: 18.0,
      simple_fte: 5.33,
      available_fte: 5.0,
      hsa_hours: 5.94,
      hsa_fte: 0.33,
    },
    // ... (all subjects)
  ],
  gap_analysis: {
    total_besoins: 120.5,
    total_moyens: 115.0,
    deficit: 5.5,
    hsa_coverage: 4.5,
    remaining_deficit: 1.0,
  },
}

// ==============================================================================
// Mock API Responses
// ==============================================================================

export const createMockApiResponse = <T>(data: T, delay = 0) => {
  return new Promise<T>((resolve) => {
    setTimeout(() => resolve(data), delay)
  })
}

export const createMockApiError = (message: string, delay = 0) => {
  return new Promise<never>((_, reject) => {
    setTimeout(() => reject(new Error(message)), delay)
  })
}
```

---

## Timeline & Milestones

### Week 1: P0 Backend Services (40 hours)

**Day 1-2 (16h):** DHG Service
- Fix database setup issues (4h)
- Write DHG service tests (12h)
- Target: 95% coverage on DHG service

**Day 3-4 (16h):** Consolidation & Revenue Services
- Consolidation service tests (10h)
- Revenue service tests (6h)
- Target: 95% coverage on both

**Day 5 (8h):** Cost Service
- Cost service tests (8h)
- Target: 95% coverage

**Milestone 1:** Backend P0 services at 95% coverage

### Week 2: P0 Frontend Components (36 hours)

**Day 1 (8h):** Test infrastructure
- Fix Playwright config (2h)
- Fix act() warnings (2h)
- Set up test fixtures (4h)

**Day 2-3 (16h):** Component tests
- BudgetVersionSelector tests (8h)
- DataTable tests (8h)
- Target: 95% coverage on components

**Day 4-5 (12h):** Hook tests
- useBudgetVersions tests (6h)
- useDHG tests (6h)
- Target: 95% coverage on hooks

**Milestone 2:** Frontend P0 at 95% coverage

### Week 3: P1 Backend Services (48 hours)

**Day 1-3 (24h):** Integration Services
- Odoo integration tests (8h)
- Skolengo integration tests (8h)
- AEFE integration tests (8h)

**Day 4-5 (16h):** Supporting Services
- KPI service tests (8h)
- Dashboard service tests (8h)

**Day 6 (8h):** Review & fixes
- Address coverage gaps
- Fix failing tests

**Milestone 3:** P1 services at 95% coverage

### Week 4: P2 API & Infrastructure (40 hours)

**Day 1-3 (24h):** API Endpoints
- Planning API tests (8h)
- Consolidation API tests (8h)
- Analysis API tests (8h)

**Day 4-5 (16h):** Middleware & Auth
- Auth middleware tests (8h)
- RBAC middleware tests (4h)
- Base service tests (4h)

**Milestone 4:** Backend API layer at 95% coverage

### Week 5: P3 Final Coverage & Docs (24 hours)

**Day 1-2 (16h):** Fill remaining gaps
- Validators (8h)
- Model/Schema gaps (8h)

**Day 3 (8h):** Documentation & CI/CD
- Update test documentation
- Configure CI/CD coverage gates
- Generate final coverage report

**Milestone 5:** Overall 95% coverage achieved

---

## Coverage Verification & Reporting

### Daily Coverage Checks

```bash
# Backend coverage check
cd backend
pytest --cov=app --cov-report=term --cov-report=html

# Frontend coverage check
cd frontend
pnpm test -- --coverage

# View HTML reports
# Backend: backend/htmlcov/index.html
# Frontend: frontend/coverage/index.html
```

### Coverage Gates (CI/CD)

```yaml
# .github/workflows/test-coverage.yml
name: Test Coverage

on: [push, pull_request]

jobs:
  backend-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.14'
      - name: Run tests with coverage
        run: |
          cd backend
          pip install -e .[dev]
          pytest --cov=app --cov-fail-under=95
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4

  frontend-coverage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - name: Run tests with coverage
        run: |
          cd frontend
          pnpm install
          pnpm test -- --coverage
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
```

### Weekly Progress Report Template

```markdown
# Test Coverage Progress - Week {X}

## Summary
- **Overall Coverage:** {X}%
- **Backend Coverage:** {X}%
- **Frontend Coverage:** {X}%
- **Tests Written:** {X}
- **Tests Passing:** {X}

## Completed This Week
- [ ] {Module/Component} - {Coverage}%
- [ ] {Module/Component} - {Coverage}%

## Blockers/Issues
- {Issue description}

## Next Week Plan
- {Priority 1}
- {Priority 2}

## Coverage by Module

### Backend
| Module | Previous | Current | Target | Status |
|--------|----------|---------|--------|--------|
| DHG Service | 15.6% | {X}% | 95% | {✅/🟡/❌} |

### Frontend
| Component | Previous | Current | Target | Status |
|-----------|----------|---------|--------|--------|
| BudgetVersionSelector | 0% | {X}% | 95% | {✅/🟡/❌} |
```

---

## Success Criteria

### Phase 2 Complete When:

1. **Backend Coverage ≥ 95%**
   - All P0-P2 services at 95%+
   - All calculation engines maintained at 100%
   - All API endpoints at 95%+

2. **Frontend Coverage ≥ 95%**
   - All P0 components at 95%+
   - All critical hooks at 95%+
   - All E2E critical paths covered

3. **Test Quality**
   - All tests follow EFIR standards
   - No skipped tests without justification
   - No flaky tests
   - All mocks/fixtures documented

4. **CI/CD Integration**
   - Coverage gates enforced
   - Pre-commit hooks enabled
   - Automated coverage reporting

5. **Documentation**
   - All test scenarios documented
   - Fixture library complete
   - Test templates available

---

## Appendix A: Common Test Patterns

### Testing Async Functions

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### Testing Database Operations

```python
@pytest.fixture
async def db_session():
    async with async_session_maker() as session:
        yield session
        await session.rollback()
```

### Testing API Endpoints

```python
async def test_api_endpoint(client: AsyncClient):
    response = await client.post(
        "/api/v1/endpoint",
        json={"key": "value"}
    )
    assert response.status_code == 200
```

### Testing React Components

```typescript
it('should render', () => {
  render(<Component />)
  expect(screen.getByRole('button')).toBeInTheDocument()
})
```

### Testing TanStack Query Hooks

```typescript
const { result } = renderHook(() => useQuery(), { wrapper })

await waitFor(() => expect(result.current.isSuccess).toBe(true))
```

---

## Appendix B: Troubleshooting Guide

### Backend Issues

**Issue:** Foreign key constraint errors
**Solution:** Ensure auth.users table exists in test DB

**Issue:** Async tests failing
**Solution:** Add `@pytest.mark.asyncio` decorator

**Issue:** Database state persisting between tests
**Solution:** Use transaction rollback in fixtures

### Frontend Issues

**Issue:** act() warnings
**Solution:** Wrap async operations in `waitFor()`

**Issue:** Playwright tests failing
**Solution:** Separate Vitest and Playwright configs

**Issue:** Mock not working
**Solution:** Ensure vi.mock() is at top of file

---

## Appendix C: Resources

**EFIR Development Standards:**
- CLAUDE.md
- EFIR_Module_Technical_Specification.md
- EFIR_Workforce_Planning_Logic.md

**Testing Frameworks:**
- pytest: https://docs.pytest.org
- Vitest: https://vitest.dev
- Playwright: https://playwright.dev
- Testing Library: https://testing-library.com

**Coverage Tools:**
- pytest-cov: https://pytest-cov.readthedocs.io
- Vitest Coverage: https://vitest.dev/guide/coverage.html

---

**Document Status:** DRAFT v1.0
**Next Review:** After Week 1 completion
**Owner:** QA & Validation Agent
