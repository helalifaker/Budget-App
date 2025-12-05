# Test Coverage Improvement Roadmap - EFIR Budget App

**Target:** 90% test coverage
**Current:** ~30-35% coverage
**Estimated Effort:** 142-189 hours
**Timeline:** 4-6 weeks (1 full-time developer)

---

## Executive Summary

This document provides a **complete, step-by-step action plan** for improving test coverage from 30% to 90%. The plan is organized by phases based on effort vs. impact, with specific file paths, test counts, and estimated hours for each component.

### Key Numbers

| Metric | Current | Target |
|--------|---------|--------|
| **Backend Services** | 4 tested, 17 untested | All 21 tested |
| **Frontend Services** | 0 tested, 11 untested | All 11 tested |
| **Components** | 5 tested, 40 untested | 30+ tested |
| **Routes/Pages** | 0 tested, 16 untested | 10+ tested |
| **Coverage %** | ~30% | 90% |

---

## Phase 1: Quick Wins (Week 1) - 7-9 hours, +3.5% coverage

### The Strategy
Start with the smallest, easiest-to-test files that have the lowest dependencies. Frontend services are **API wrapper functions** - they're pure functions that can be tested with simple mocking.

### 1.1 Frontend Services (70-90 tests, 7-9 hours)

All frontend services follow the same pattern:
```typescript
export const serviceApi = {
  getResource: async (id: string) => apiRequest<Response>({ ... }),
  createResource: async (data: RequestData) => apiRequest<Response>({ ... }),
  updateResource: async (id: string, data: RequestData) => apiRequest<Response>({ ... }),
  deleteResource: async (id: string) => apiRequest<Response>({ ... }),
}
```

**Test Template for All Services:**

```typescript
// /home/user/Budget-App/frontend/tests/services/configuration.test.ts
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { apiRequest } from '@/lib/api-client'
import { configurationApi } from '@/services/configuration'

vi.mock('@/lib/api-client', () => ({
  apiRequest: vi.fn(),
}))

describe('Configuration Service', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Fetch Operations', () => {
    it('should get academic cycles', async () => {
      const mockData = {
        items: [
          { id: '1', name_fr: 'Maternelle', code: 'MATERNELLE' },
          { id: '2', name_fr: 'Élémentaire', code: 'ELEMENTAIRE' },
        ],
        total: 2,
      }

      vi.mocked(apiRequest).mockResolvedValueOnce(mockData)

      const result = await configurationApi.getAcademicCycles('version-1')

      expect(result).toEqual(mockData)
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'GET',
        url: '/configuration/academic-cycles/version-1',
      })
    })

    it('should handle network errors', async () => {
      vi.mocked(apiRequest).mockRejectedValueOnce(new Error('Network error'))

      await expect(configurationApi.getAcademicCycles('version-1')).rejects.toThrow(
        'Network error'
      )
    })

    it('should handle 404 errors', async () => {
      const error = new Error('Not found')
      vi.mocked(apiRequest).mockRejectedValueOnce(error)

      await expect(configurationApi.getAcademicCycles('invalid-id')).rejects.toThrow()
    })
  })

  describe('Create Operations', () => {
    it('should create academic cycle', async () => {
      const mockResponse = { id: '123', name_fr: 'Test Cycle', code: 'TEST' }
      vi.mocked(apiRequest).mockResolvedValueOnce(mockResponse)

      const result = await configurationApi.createAcademicCycle('version-1', {
        name_fr: 'Test Cycle',
        code: 'TEST',
      })

      expect(result).toEqual(mockResponse)
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'POST',
        url: '/configuration/academic-cycles',
        data: { version_id: 'version-1', name_fr: 'Test Cycle', code: 'TEST' },
      })
    })

    it('should handle validation errors on create', async () => {
      vi.mocked(apiRequest).mockRejectedValueOnce(new Error('Invalid data'))

      await expect(configurationApi.createAcademicCycle('version-1', {})).rejects.toThrow()
    })
  })

  describe('Update Operations', () => {
    it('should update academic cycle', async () => {
      const mockResponse = { id: '123', name_fr: 'Updated', code: 'UPDATED' }
      vi.mocked(apiRequest).mockResolvedValueOnce(mockResponse)

      const result = await configurationApi.updateAcademicCycle('123', {
        name_fr: 'Updated',
      })

      expect(result).toEqual(mockResponse)
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'PUT',
        url: '/configuration/academic-cycles/123',
        data: { name_fr: 'Updated' },
      })
    })
  })

  describe('Delete Operations', () => {
    it('should delete academic cycle', async () => {
      vi.mocked(apiRequest).mockResolvedValueOnce({ success: true })

      await configurationApi.deleteAcademicCycle('123')

      expect(apiRequest).toHaveBeenCalledWith({
        method: 'DELETE',
        url: '/configuration/academic-cycles/123',
      })
    })

    it('should handle delete not found', async () => {
      vi.mocked(apiRequest).mockRejectedValueOnce(new Error('Not found'))

      await expect(configurationApi.deleteAcademicCycle('invalid')).rejects.toThrow()
    })
  })
})
```

**Apply Template to Each Service:**

| Service | Size | Tests | Hours |
|---------|------|-------|-------|
| configuration.ts | 1.2K | 6 | 0.75 |
| class-structure.ts | 1.4K | 6 | 0.75 |
| enrollment.ts | 1.7K | 7 | 1.00 |
| budget-versions.ts | 1.7K | 7 | 1.00 |
| capex.ts | 1.8K | 7 | 1.00 |
| costs.ts | 1.9K | 7 | 1.00 |
| consolidation.ts | 1.9K | 7 | 1.00 |
| revenue.ts | 1.9K | 7 | 1.00 |
| strategic.ts | 2.0K | 8 | 1.00 |
| analysis.ts | 2.2K | 8 | 1.00 |
| dhg.ts | 2.7K | 10 | 1.25 |
| **TOTAL** | 20.3K | **81** | **10.75** |

### 1.2 Toast Messages & Error Utilities (30 minutes, +0.5% coverage)

**File:** `/home/user/Budget-App/frontend/src/lib/toast-messages.ts` (176 LOC)
**Current Status:** Partially tested in `/__tests__/toast-messages.test.ts`

**Additional Tests Needed:**
- handleAPIErrorToast() with all error types (8 tests)
- Edge cases (3 tests)
- Batch operation messages (3 tests)

**File:** `/home/user/Budget-App/frontend/src/lib/errors.ts`
**Current Status:** Untested

**Tests Needed:** 8-10

---

## Phase 2: Mid-Sized Backend Services (Weeks 2-3) - 35-45 hours, +19% coverage

### Strategy
Focus on services with moderate complexity that have clear dependencies on fixtures already in `conftest.py`. These services have business logic that needs multiple test scenarios.

### 2.1 Configuration Service (25,596 LOC) - 8-10 hours, +6% coverage

**File to Create:** `/home/user/Budget-App/backend/tests/services/test_configuration_service.py`

**Key Methods to Test:**

```python
# Pattern 1: Create operations with validation
async def test_create_class_size_params_valid():
    """Test creating valid class size parameters."""
    # Setup
    academic_cycle = await create_test_cycle(db_session, "COLLEGE")

    # Execute
    params = ClassSizeParam(
        id=uuid4(),
        cycle_id=academic_cycle.id,
        min_size=20,
        target_size=25,
        max_size=30,
    )
    db_session.add(params)
    await db_session.flush()

    # Assert
    assert params.min_size < params.target_size < params.max_size

async def test_create_class_size_params_invalid_order():
    """Test validation: min < target < max."""
    with pytest.raises(ValueError):
        # Invalid: target > max
        ClassSizeParam(min_size=20, target_size=35, max_size=30)

# Pattern 2: Update with state checks
async def test_update_subject_hours_by_level():
    """Test updating subject hours for specific level."""
    level = await create_test_level(db_session, "6ème")
    subject = await create_test_subject(db_session, "Mathématiques")

    # Create initial
    matrix = SubjectHoursMatrix(
        id=uuid4(),
        level_id=level.id,
        subject_id=subject.id,
        hours_per_week=4.5,
    )
    db_session.add(matrix)
    await db_session.flush()

    # Update
    matrix.hours_per_week = 5.0
    await db_session.flush()

    # Verify
    updated = await db_session.get(SubjectHoursMatrix, matrix.id)
    assert updated.hours_per_week == 5.0

# Pattern 3: Business rule validation
async def test_fee_structure_sibling_discount():
    """Test sibling discount rules: 25% on tuition, not on DAI."""
    fee_structure = await create_test_fee_structure(db_session)

    # Sibling discount applies to tuition
    tuition = fee_structure.fees.get("tuition")
    assert tuition.sibling_discount == Decimal("0.25")

    # Sibling discount does NOT apply to DAI
    dai = fee_structure.fees.get("dai")
    assert dai.sibling_discount == Decimal("0.0")
```

**Test Categories:**

1. **Configuration CRUD** (15 tests)
   - Create with validation
   - Update with constraints
   - Delete with referential checks
   - Get/List with filtering

2. **Business Rules** (25 tests)
   - Class size constraints (min < target < max)
   - Fee structure rules (sibling discount logic)
   - Teacher cost allocation (AEFE vs Local)
   - Subject hours by level/cycle

3. **Integration** (15 tests)
   - Bulk operations (atomicity)
   - Cross-module dependencies
   - Error recovery

4. **Edge Cases** (10 tests)
   - Boundary values
   - Empty datasets
   - Duplicate handling

**Tests Needed:** 60-80
**Effort Breakdown:**
- Understand service structure: 1 hour
- Write fixtures/helpers: 1 hour
- CRUD tests: 3 hours
- Business rule tests: 2-3 hours
- Integration tests: 1.5 hours
- Review & fixes: 1-1.5 hours

### 2.2 Enrollment Service (13,513 LOC) - 3-4 hours, +4% coverage

**File to Create:** `/home/user/Budget-App/backend/tests/services/test_enrollment_service.py`

**Key Test Scenarios:**

```python
# Real EFIR Scenario: Complete school enrollment
async def test_enrollment_complete_school():
    """Test enrollment projections for all levels."""
    # Setup: EFIR school with 1,800 students
    fixture = await setup_efir_test_school(db_session)
    service = EnrollmentService(db_session)

    # Create enrollment for full school
    enrollment = EnrollmentPlan(
        version_id=fixture.budget_version.id,
        maternelle_students=300,  # PS, MS, GS
        elementaire_students=450,  # CP-CM2
        college_students=600,      # 6ème-3ème
        lycee_students=450,        # 2nde-Terminale
        total=1800,
    )

    # Verify calculations
    assert enrollment.total == 1800
    assert enrollment.maternelle_percent == 300 / 1800

async def test_enrollment_by_nationality():
    """Test enrollment breakdown by nationality."""
    enrollment = EnrollmentPlan(
        french_students=800,
        saudi_students=700,
        other_students=300,
        total=1800,
    )

    # Verify percentages
    assert enrollment.french_percent == pytest.approx(44.4, abs=0.1)

async def test_enrollment_growth_projection():
    """Test multi-year enrollment projections."""
    service = EnrollmentService(db_session)

    # Year 1: 1,800 students
    # Year 2: 5% growth → 1,890
    # Year 3: 5% growth → 1,984
    projections = await service.project_enrollment(
        start_enrollment=1800,
        growth_rate=0.05,
        years=3,
    )

    assert projections[0] == 1800
    assert projections[1] == 1890
    assert projections[2] == pytest.approx(1984, abs=1)
```

**Tests Needed:** 35-45

### 2.3 Revenue Service (15,247 LOC) - 4-5 hours, +5% coverage

**File to Create:** `/home/user/Budget-App/backend/tests/services/test_revenue_service.py`

**Key Test Scenarios:**

```python
# Real EFIR Scenario: Tuition revenue with trimesters and nationalities
async def test_revenue_calculation_complete():
    """
    Test revenue calculation with real EFIR structure:
    - 1,800 students
    - 3 trimesters (T1: 40%, T2: 30%, T3: 30%)
    - 3 nationality categories
    """
    fixture = await setup_efir_test_school(db_session)
    service = RevenueService(db_session)

    # Calculate revenue
    revenue = await service.calculate_tuition_revenue(
        version_id=fixture.budget_version.id,
        french_students=800,
        saudi_students=700,
        other_students=300,
        annual_tuition=35000,  # SAR
    )

    # Verify
    assert revenue.total > 0
    assert revenue.t1_revenue == revenue.total * Decimal("0.4")
    assert revenue.t2_revenue == revenue.total * Decimal("0.3")
    assert revenue.t3_revenue == revenue.total * Decimal("0.3")

async def test_sibling_discount_tuition_only():
    """
    Test sibling discount:
    - Applies: Tuition
    - Does NOT apply: DAI, registration fees
    """
    service = RevenueService(db_session)

    # Family with 3 children
    # Child 1: Pay 100% tuition
    # Child 2: Pay 100% tuition
    # Child 3: Pay 75% tuition (25% discount)

    tuition_child1 = Decimal("35000")
    tuition_child2 = Decimal("35000")
    tuition_child3 = tuition_child1 * Decimal("0.75")  # 25% discount

    total = tuition_child1 + tuition_child2 + tuition_child3
    assert total == Decimal("96250")

    # DAI (registration fee) has NO discount
    dai = Decimal("1000")
    dai_total = dai * 3  # 3 children, full price
    assert dai_total == Decimal("3000")

async def test_revenue_by_nationality():
    """
    Test revenue calculation by nationality:
    - French: TTC (includes taxes)
    - Saudi: HT (excluding taxes)
    - Other: TTC
    """
    french_revenue = await service.calculate_french_revenue(
        students=800,
        annual_tuition=35000,
        rate_ttc=True,
    )

    saudi_revenue = await service.calculate_saudi_revenue(
        students=700,
        annual_tuition=35000,
        rate_ht=True,
    )

    # French TTC > Saudi HT
    assert french_revenue > saudi_revenue
```

**Tests Needed:** 40-50

### 2.4 Class Structure Service (14,987 LOC) - 3-4 hours, +4% coverage

**File to Create:** `/home/user/Budget-App/backend/tests/services/test_class_structure_service.py`

**Key Test Scenarios:**

```python
# Real EFIR Scenario: Form classes from enrollment
async def test_class_formation_college():
    """
    Test class formation for Collège (600 students):
    - 6ème: 150 students → 6 classes (25 per class)
    - 5ème: 150 students → 6 classes (25 per class)
    - 4ème: 150 students → 6 classes (25 per class)
    - 3ème: 150 students → 6 classes (25 per class)
    Total: 24 classes
    """
    service = ClassStructureService(db_session)
    fixture = await setup_efir_test_school(db_session)

    # Get class size params
    college_params = await fixture.get_class_size_params("COLLEGE")
    # min=20, target=25, max=30

    # Calculate required classes
    required_classes = await service.calculate_required_classes(
        level="6ème",
        enrollment=150,
        min_size=20,
        target_size=25,
        max_size=30,
    )

    # 150 ÷ 25 = 6 classes exactly
    assert required_classes == 6

async def test_atsem_requirement_maternelle():
    """
    Test ATSEM requirement: 1 ATSEM per Maternelle class
    - PS (Petite Section): 90 students
    - MS (Moyenne Section): 105 students
    - GS (Grande Section): 105 students
    Total: 300 students, 12 classes, 12 ATSEM required
    """
    service = ClassStructureService(db_session)

    maternelle_params = await get_class_size_params("MATERNELLE")
    # min=18, target=25, max=28

    # PS: 90 ÷ 25 = 3.6 → 4 classes
    ps_classes = await service.calculate_required_classes(
        enrollment=90,
        min_size=18,
        target_size=25,
        max_size=28,
    )
    assert ps_classes == 4

    # Each class needs 1 ATSEM
    atsem_required = ps_classes
    assert atsem_required == 4

async def test_class_optimization():
    """
    Test class size optimization:
    Given 150 students, find distribution that fits constraints.
    Constraint: min=20, target=25, max=30

    Solution: 6 classes × 25 = 150 (perfect)
    """
    service = ClassStructureService(db_session)

    classes = await service.optimize_class_distribution(
        enrollment=150,
        min_size=20,
        target_size=25,
        max_size=30,
    )

    # Verify constraints
    assert len(classes) == 6
    assert all(20 <= size <= 30 for size in classes)
    assert sum(classes) == 150
```

**Tests Needed:** 35-45

**Phase 2 Summary:**
- 4 services
- 170-220 tests
- 35-45 hours
- +19% coverage gain

---

## Phase 3: Large Complex Services (Weeks 3-4) - 45-60 hours, +25% coverage

### Strategy
These are the critical services with complex business logic, state management, and multi-step workflows. They require:
1. Understanding the full business process
2. Creating comprehensive fixtures
3. Testing normal path + error paths + edge cases

### 3.1 Writeback Service (36,049 LOC) - 12-15 hours, +10% coverage

**File to Create:** `/home/user/Budget-App/backend/tests/services/test_writeback_service.py`

This is the MOST CRITICAL service - handles all real-time cell editing with optimistic locking and conflict detection.

```python
# Test Pattern 1: Simple cell update with version tracking
async def test_update_cell_success():
    """Test updating a single cell value."""
    service = WritebackService(db_session)
    fixture = await setup_efir_test_school(db_session)

    # Create a cell to update
    cell = BudgetCell(
        id=uuid4(),
        version_id=fixture.budget_version.id,
        module="planning",
        row="6ème",
        column="enrollment",
        value=Decimal("150"),
        version_tag=1,
    )
    db_session.add(cell)
    await db_session.flush()

    # Update cell
    request = CellUpdateRequest(
        id=str(cell.id),
        value=Decimal("160"),
        version_tag=1,  # Current version
    )

    result = await service.update_cell(fixture.budget_version.id, request)

    assert result.value == Decimal("160")
    assert result.version_tag == 2  # Incremented

# Test Pattern 2: Optimistic locking - concurrent updates
async def test_concurrent_update_conflict():
    """
    Test optimistic locking conflict detection.

    Scenario:
    - User A reads cell version=5, value=150
    - User B reads cell version=5, value=150
    - User A updates to 160 (version becomes 6)
    - User B tries to update to 170 with version=5 → CONFLICT
    """
    service = WritebackService(db_session)
    fixture = await setup_efir_test_school(db_session)

    # Create initial cell
    cell = BudgetCell(
        id=uuid4(),
        version_id=fixture.budget_version.id,
        value=Decimal("150"),
        version_tag=5,
    )
    db_session.add(cell)
    await db_session.flush()

    # User A updates (succeeds)
    request_a = CellUpdateRequest(
        id=str(cell.id),
        value=Decimal("160"),
        version_tag=5,
    )
    result_a = await service.update_cell(fixture.budget_version.id, request_a)
    assert result_a.version_tag == 6

    # User B tries to update with old version (fails)
    request_b = CellUpdateRequest(
        id=str(cell.id),
        value=Decimal("170"),
        version_tag=5,  # Old version!
    )

    with pytest.raises(VersionConflictError):
        await service.update_cell(fixture.budget_version.id, request_b)

# Test Pattern 3: Batch updates with rollback
async def test_batch_update_rollback():
    """
    Test batch update atomicity.
    If one cell fails validation, entire batch rolls back.
    """
    service = WritebackService(db_session)
    fixture = await setup_efir_test_school(db_session)

    # Create 3 cells
    cells = []
    for i in range(3):
        cell = BudgetCell(
            id=uuid4(),
            version_id=fixture.budget_version.id,
            value=Decimal(str(100 + i * 10)),
            version_tag=1,
        )
        db_session.add(cell)
        cells.append(cell)
    await db_session.flush()

    # Batch update: 2 valid, 1 invalid
    updates = [
        CellUpdateRequest(id=str(cells[0].id), value=Decimal("200"), version_tag=1),
        CellUpdateRequest(id=str(cells[1].id), value=Decimal("210"), version_tag=1),
        CellUpdateRequest(id=str(cells[2].id), value=Decimal("-999"), version_tag=1),  # Invalid!
    ]

    # Should raise error
    with pytest.raises(ValidationError):
        await service.batch_update(fixture.budget_version.id, updates)

    # Verify all cells unchanged (rollback)
    for i, cell in enumerate(cells):
        refreshed = await db_session.get(BudgetCell, cell.id)
        assert refreshed.value == Decimal(str(100 + i * 10))

# Test Pattern 4: Cell comments and history
async def test_add_cell_comment():
    """Test adding comments to cells."""
    service = WritebackService(db_session)
    fixture = await setup_efir_test_school(db_session)

    cell = BudgetCell(id=uuid4(), version_id=fixture.budget_version.id)
    db_session.add(cell)
    await db_session.flush()

    # Add comment
    comment = CellComment(
        cell_id=cell.id,
        user_id=fixture.test_user_id,
        text="This enrollment increased due to new marketing campaign",
        created_at=datetime.utcnow(),
    )
    db_session.add(comment)
    await db_session.flush()

    # Retrieve
    history = await service.get_cell_comments(str(cell.id))
    assert len(history) == 1
    assert history[0].text == "This enrollment increased due to new marketing campaign"

# Test Pattern 5: Undo/Redo functionality
async def test_undo_cell_update():
    """Test undoing a cell update."""
    service = WritebackService(db_session)
    fixture = await setup_efir_test_school(db_session)

    cell = BudgetCell(
        id=uuid4(),
        version_id=fixture.budget_version.id,
        value=Decimal("100"),
        version_tag=1,
    )
    db_session.add(cell)
    await db_session.flush()

    # Update cell
    await service.update_cell(
        fixture.budget_version.id,
        CellUpdateRequest(id=str(cell.id), value=Decimal("200"), version_tag=1),
    )

    # Verify update
    updated = await db_session.get(BudgetCell, cell.id)
    assert updated.value == Decimal("200")

    # Undo
    await service.undo(fixture.budget_version.id, cell.id)

    # Verify reverted
    reverted = await db_session.get(BudgetCell, cell.id)
    assert reverted.value == Decimal("100")

# Test Pattern 6: Cell locking for approved budgets
async def test_cell_locking_approved_budget():
    """
    Test cells cannot be edited in Approved/Superseded budgets.
    """
    service = WritebackService(db_session)
    fixture = await setup_efir_test_school(db_session)

    # Change budget status to APPROVED
    fixture.budget_version.status = BudgetVersionStatus.APPROVED
    await db_session.flush()

    cell = BudgetCell(id=uuid4(), version_id=fixture.budget_version.id)
    db_session.add(cell)
    await db_session.flush()

    # Try to update (should fail)
    with pytest.raises(CellLockedError):
        await service.update_cell(
            fixture.budget_version.id,
            CellUpdateRequest(id=str(cell.id), value=Decimal("999"), version_tag=1),
        )
```

**Tests Needed:** 80-100

**Specific Test Categories:**
1. **Basic CRUD** (15 tests)
2. **Optimistic Locking** (20 tests)
3. **Batch Operations** (15 tests)
4. **Comments & Annotations** (10 tests)
5. **Undo/Redo** (10 tests)
6. **Cell Locking** (10 tests)
7. **Real-time Sync** (5 tests)
8. **Error Cases** (15 tests)

### 3.2 Consolidation Service (25,596 LOC) - 10-12 hours, +8% coverage

**File to Create:** `/home/user/Budget-App/backend/tests/services/test_consolidation_service.py`

```python
# Real EFIR Scenario: Full budget consolidation
async def test_consolidate_full_budget():
    """
    Test consolidating a complete budget with all modules:
    - Configuration (system setup)
    - Planning (enrollment → classes → DHG → revenue)
    - Consolidation (aggregate all costs)
    - Analysis (KPIs)
    """
    service = ConsolidationService(db_session)
    fixture = await setup_efir_complete_budget(db_session)

    # Consolidate
    result = await service.consolidate_budget(fixture.budget_version.id)

    # Verify all modules aggregated
    assert result.total_revenue > 0
    assert result.total_cost > 0
    assert result.balance == result.total_revenue - result.total_cost

async def test_budget_version_workflow():
    """
    Test budget version status transitions:
    WORKING → SUBMITTED → APPROVED → SUPERSEDED
    """
    service = ConsolidationService(db_session)
    fixture = await setup_efir_test_school(db_session)

    version = fixture.budget_version

    # Initial: WORKING
    assert version.status == BudgetVersionStatus.WORKING

    # Submit
    await service.submit_version(version.id)
    assert version.status == BudgetVersionStatus.SUBMITTED

    # Approve
    await service.approve_version(version.id)
    assert version.status == BudgetVersionStatus.APPROVED

    # Create new version (supersedes old)
    new_version = await service.create_budget_version(
        name="Budget 2025 v2",
        fiscal_year=2025,
    )
    assert new_version.status == BudgetVersionStatus.WORKING

async def test_validate_consolidation():
    """
    Test budget validation:
    - Revenue > 0
    - Costs > 0
    - Balance calculable
    - All modules complete
    """
    service = ConsolidationService(db_session)
    fixture = await setup_efir_test_school(db_session)

    # Validate
    issues = await service.validate_consolidation(fixture.budget_version.id)

    # Should have no critical errors
    assert not any(issue.severity == "ERROR" for issue in issues)
```

**Tests Needed:** 70-90

### 3.3 Financial Statements Service (22,008 LOC) - 8-10 hours, +7% coverage

**File to Create:** `/home/user/Budget-App/backend/tests/services/test_financial_statements_service.py`

```python
# Real EFIR Scenario: Generate PCG and IFRS statements
async def test_generate_pcg_statement():
    """
    Generate French accounting statement (PCG - Plan Comptable Général)
    Account codes:
    - 60xxx-68xxx: Expenses
    - 70xxx-77xxx: Revenue
    """
    service = FinancialStatementsService(db_session)
    fixture = await setup_efir_complete_budget(db_session)

    # Generate PCG statement
    statement = await service.generate_pcg_statement(fixture.budget_version.id)

    # Verify structure
    assert statement.fiscal_year == 2024
    assert len(statement.revenue_accounts) > 0
    assert len(statement.expense_accounts) > 0

    # Verify balance
    total_revenue = sum(a.amount for a in statement.revenue_accounts)
    total_expense = sum(a.amount for a in statement.expense_accounts)
    assert statement.net_income == total_revenue - total_expense

async def test_account_code_validation():
    """
    Test account code validation:
    - 60110: Teaching salaries (payroll)
    - 61xxx: Social contributions
    - 70110: Tuition T1
    - 70210: Tuition T2
    """
    service = FinancialStatementsService(db_session)

    # Valid codes
    assert service.is_valid_account_code("60110")  # Salaries
    assert service.is_valid_account_code("70110")  # Revenue T1

    # Invalid codes
    assert not service.is_valid_account_code("99999")
    assert not service.is_valid_account_code("invalid")
```

**Tests Needed:** 50-65

**Phase 3 Summary:**
- 3 services
- 200-255 tests
- 45-60 hours
- +25% coverage gain

---

## Phase 4: Integration Services (Weeks 4-5) - 25-35 hours, +26% coverage

### 4.1 Strategic Service - 50-65 tests, 6-8 hours
### 4.2 KPI Service - 50-65 tests, 6-8 hours
### 4.3 Cost Service - 50-65 tests, 6-8 hours
### 4.4 Dashboard Service - 30-40 tests, 4-5 hours
### 4.5 Budget Actual Service - 30-40 tests, 4-5 hours

---

## Phase 5: Components & Routes (Weeks 5-6) - 30-40 hours, +10-12% coverage

### 5.1 Frontend Components - 40-50 tests, 4-5 hours
### 5.2 Frontend Routes - 20-30 tests, 3-4 hours
### 5.3 API Hooks - 40-50 tests, 4-5 hours

---

## Complete Implementation Checklist

### Week 1
- [ ] Create `/frontend/tests/services/` directory
- [ ] Create service test template
- [ ] Write tests for all 11 frontend services (70-90 tests)
- [ ] Write toast messages tests (15-20 tests)
- [ ] Run all tests: `pnpm test`
- [ ] Verify no broken tests

### Week 2-3
- [ ] Create `/backend/tests/services/test_configuration_service.py`
- [ ] Create `/backend/tests/services/test_enrollment_service.py`
- [ ] Create `/backend/tests/services/test_revenue_service.py`
- [ ] Create `/backend/tests/services/test_class_structure_service.py`
- [ ] Run all tests: `pytest`
- [ ] Coverage check

### Week 3-4
- [ ] Create `/backend/tests/services/test_writeback_service.py` (CRITICAL)
- [ ] Create `/backend/tests/services/test_consolidation_service.py`
- [ ] Create `/backend/tests/services/test_financial_statements_service.py`
- [ ] Run all tests

### Week 4-5
- [ ] Create remaining service tests (Strategic, KPI, Cost, Dashboard, Budget Actual)
- [ ] Run all tests
- [ ] Coverage check

### Week 5-6
- [ ] Create component tests for data grids and dialogs
- [ ] Create route tests
- [ ] Create API hook tests
- [ ] Run all tests
- [ ] Final coverage check

---

## Success Metrics

By end of Phase 5, you should have:
- ✅ 750-950 new tests
- ✅ 90% code coverage
- ✅ All test suites passing
- ✅ No console.log/print in production code
- ✅ Meaningful assertions with messages
- ✅ Real EFIR scenarios in complex tests
- ✅ All linting and type checks passing

---

## Commands to Track Progress

```bash
# Backend tests
cd /home/user/Budget-App/backend
pytest --cov=app --cov-report=term-missing | tail -20

# Frontend tests
cd /home/user/Budget-App/frontend
pnpm test -- --coverage

# Lint
pnpm lint
.venv/bin/ruff check .

# Type check
pnpm typecheck
.venv/bin/mypy .
```

---

For detailed step-by-step instructions for each phase, see the companion document `TEST_COVERAGE_IMPLEMENTATION_DETAILS.md`.
