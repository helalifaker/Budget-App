# Test Coverage Improvement Plan: 73.62% → 80%

**Current Status**: 73.62% coverage  
**Target**: 80% coverage  
**Gap**: 6.38 percentage points  
**Priority**: High (Required for production readiness)

---

## Executive Summary

Analysis of the current test coverage reveals **13 critical gaps** that need to be addressed to reach 80%. The plan prioritizes:
1. **API endpoints** (lowest coverage, highest user impact)
2. **Service layer** (business logic critical paths)
3. **Missing test files** (no tests exist)

**Estimated Effort**: 2-3 weeks (1 developer)  
**Strategy**: Focus on highest-impact, lowest-coverage areas first

---

## Coverage Analysis by Module

### Critical Gaps (Highest Priority)

| Module | Current Coverage | Missing Lines | Priority | Estimated Tests Needed |
|--------|------------------|---------------|----------|------------------------|
| **app/api/v1/export.py** | 13% | 123/142 | P0 - Critical | 25-30 tests |
| **app/api/v1/integrations.py** | 21% | 177/224 | P0 - Critical | 35-40 tests |
| **app/api/v1/consolidation.py** | 21% | 133/168 | P0 - Critical | 30-35 tests |
| **app/services/materialized_view_service.py** | 28% | 34/47 | P0 - Critical | 10-12 tests (NEW FILE) |
| **app/services/writeback_service.py** | 42% | 125/216 | P0 - Critical | 30-35 tests |
| **app/api/v1/configuration.py** | 38% | 95/154 | P1 - High | 20-25 tests |
| **app/api/v1/costs.py** | 30% | 124/176 | P1 - High | 25-30 tests |
| **app/api/v1/planning.py** | 27% | 141/193 | P1 - High | 30-35 tests |
| **app/api/v1/analysis.py** | 30% | 159/226 | P1 - High | 35-40 tests |
| **app/services/configuration_service.py** | 30% | 98/140 | P1 - High | 25-30 tests |
| **app/services/capex_service.py** | 44% | 62/111 | P2 - Medium | 15-20 tests |
| **app/services/cost_service.py** | 57% | 75/175 | P2 - Medium | 20-25 tests |
| **app/services/odoo_integration.py** | 49% | 78/154 | P2 - Medium | 20-25 tests |
| **app/services/skolengo_integration.py** | 59% | 54/131 | P2 - Medium | 15-20 tests |

**Total Estimated Tests**: 340-407 tests  
**Coverage Gain Estimate**: +8-10 percentage points (will exceed 80% target)

---

## Phase 1: Critical API Endpoints (Week 1) - +3-4% Coverage

### 1.1 Export API (`app/api/v1/export.py`) - 13% → 80%
**Priority**: P0 - Critical  
**Current**: 13% coverage (123/142 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/api/test_export_api.py` (exists but tests failing)

**Key Endpoints to Test**:
- `POST /api/v1/export/budget/excel` - Excel export with budget data
- `POST /api/v1/export/budget/pdf` - PDF export with financial statements
- `POST /api/v1/export/budget/csv` - CSV export
- `POST /api/v1/export/kpi/excel` - KPI dashboard export
- Error handling: missing dependencies, invalid versions, empty data

**Tests Needed**: 25-30 tests  
**Estimated Hours**: 6-8 hours

**Implementation Pattern**:
```python
@pytest.mark.asyncio
async def test_export_budget_excel_success(
    client: AsyncClient,
    test_budget_version: BudgetVersion,
    authenticated_user: dict,
):
    """Test successful Excel export of budget consolidation."""
    response = await client.post(
        "/api/v1/export/budget/excel",
        json={"version_id": str(test_budget_version.id), "include_details": True},
        headers=authenticated_user,
    )
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(response.content) > 0

@pytest.mark.asyncio
async def test_export_budget_excel_version_not_found(
    client: AsyncClient,
    authenticated_user: dict,
):
    """Test Excel export with invalid version ID."""
    response = await client.post(
        "/api/v1/export/budget/excel",
        json={"version_id": str(uuid4()), "include_details": True},
        headers=authenticated_user,
    )
    assert response.status_code == 404
```

### 1.2 Integrations API (`app/api/v1/integrations.py`) - 21% → 80%
**Priority**: P0 - Critical  
**Current**: 21% coverage (177/224 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/api/test_integrations_api.py` (exists but tests failing)

**Key Endpoints to Test**:
- `POST /api/v1/integrations/odoo/test-connection` - Test Odoo connection
- `POST /api/v1/integrations/odoo/import-actuals` - Import actuals from Odoo
- `POST /api/v1/integrations/skolengo/import-enrollment` - Import enrollment data
- `POST /api/v1/integrations/aefe/import-positions` - Import AEFE positions
- Error handling: connection failures, invalid data, missing credentials

**Tests Needed**: 35-40 tests  
**Estimated Hours**: 8-10 hours

### 1.3 Consolidation API (`app/api/v1/consolidation.py`) - 21% → 80%
**Priority**: P0 - Critical  
**Current**: 21% coverage (133/168 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/api/test_consolidation_api.py` (exists)

**Key Endpoints to Test**:
- `POST /api/v1/consolidation/versions` - Create budget version
- `GET /api/v1/consolidation/versions/{version_id}` - Get version details
- `POST /api/v1/consolidation/versions/{version_id}/submit` - Submit for approval
- `POST /api/v1/consolidation/versions/{version_id}/approve` - Approve version
- `GET /api/v1/consolidation/versions/{version_id}/compare` - Compare versions
- Error handling: invalid status transitions, missing data

**Tests Needed**: 30-35 tests  
**Estimated Hours**: 6-8 hours

---

## Phase 2: Missing Service Tests (Week 1-2) - +2-3% Coverage

### 2.1 Materialized View Service (`app/services/materialized_view_service.py`) - 28% → 80%
**Priority**: P0 - Critical  
**Current**: 28% coverage (34/47 lines missing)  
**Target**: 80% coverage  
**Status**: **NO TEST FILE EXISTS**

**Test File to Create**: `backend/tests/services/test_materialized_view_service.py`

**Key Methods to Test**:
- `refresh_all()` - Refresh all materialized views
- `refresh_view()` - Refresh individual view
- `get_refresh_status()` - Check refresh status
- Error handling: database errors, concurrent refresh conflicts

**Tests Needed**: 10-12 tests  
**Estimated Hours**: 3-4 hours

**Implementation Pattern**:
```python
@pytest.mark.asyncio
async def test_refresh_all_views_success(
    db_session: AsyncSession,
):
    """Test refreshing all materialized views."""
    service = MaterializedViewService()
    result = await service.refresh_all(db_session)
    
    assert "mv_kpi_dashboard" in result
    assert "mv_budget_consolidation" in result
    assert result["mv_kpi_dashboard"]["status"] == "success"

@pytest.mark.asyncio
async def test_refresh_view_concurrent_conflict(
    db_session: AsyncSession,
):
    """Test handling concurrent refresh conflicts."""
    service = MaterializedViewService()
    
    # Start two concurrent refreshes
    task1 = service.refresh_view(db_session, "mv_kpi_dashboard")
    task2 = service.refresh_view(db_session, "mv_kpi_dashboard")
    
    results = await asyncio.gather(task1, task2, return_exceptions=True)
    
    # One should succeed, one should handle conflict gracefully
    assert any(isinstance(r, dict) and r.get("status") == "success" for r in results)
```

### 2.2 Writeback Service (`app/services/writeback_service.py`) - 42% → 80%
**Priority**: P0 - Critical  
**Current**: 42% coverage (125/216 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/services/test_writeback_service.py` (exists)

**Key Methods to Test**:
- `update_cell()` - Single cell update with optimistic locking
- `batch_update()` - Batch updates with rollback
- `get_cell_history()` - Cell change history
- `add_cell_comment()` - Add comments to cells
- `undo_cell_update()` - Undo functionality
- Error handling: version conflicts, locked cells, validation errors

**Tests Needed**: 30-35 tests  
**Estimated Hours**: 8-10 hours

---

## Phase 3: Configuration & Planning APIs (Week 2) - +1-2% Coverage

### 3.1 Configuration API (`app/api/v1/configuration.py`) - 38% → 80%
**Priority**: P1 - High  
**Current**: 38% coverage (95/154 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/api/test_configuration_api.py` (exists)

**Key Endpoints to Test**:
- CRUD operations for academic cycles, levels, subjects
- Fee structure management
- Teacher cost configuration
- Class size parameters
- Error handling: validation, constraints, duplicates

**Tests Needed**: 20-25 tests  
**Estimated Hours**: 5-6 hours

### 3.2 Planning API (`app/api/v1/planning.py`) - 27% → 80%
**Priority**: P1 - High  
**Current**: 27% coverage (141/193 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/api/test_planning_api.py` (exists)

**Key Endpoints to Test**:
- Enrollment planning CRUD
- Class structure calculation
- DHG workforce planning
- Revenue calculation
- Cost planning
- Error handling: invalid inputs, missing dependencies

**Tests Needed**: 30-35 tests  
**Estimated Hours**: 6-8 hours

### 3.3 Analysis API (`app/api/v1/analysis.py`) - 30% → 80%
**Priority**: P1 - High  
**Current**: 30% coverage (159/226 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/api/test_analysis_api.py` (exists)

**Key Endpoints to Test**:
- KPI calculation and retrieval
- Dashboard data aggregation
- Budget vs actual comparison
- Variance analysis
- Error handling: missing data, calculation errors

**Tests Needed**: 35-40 tests  
**Estimated Hours**: 6-8 hours

---

## Phase 4: Service Layer Improvements (Week 2-3) - +1-2% Coverage

### 4.1 Configuration Service (`app/services/configuration_service.py`) - 30% → 80%
**Priority**: P1 - High  
**Current**: 30% coverage (98/140 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/services/test_configuration_service.py` (exists)

**Key Methods to Test**:
- Complex validation logic
- Business rule enforcement
- Bulk operations
- Cross-module dependencies
- Error handling: constraint violations, business rule errors

**Tests Needed**: 25-30 tests  
**Estimated Hours**: 6-8 hours

### 4.2 Cost Service (`app/services/cost_service.py`) - 57% → 80%
**Priority**: P2 - Medium  
**Current**: 57% coverage (75/175 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/services/test_cost_service.py` (exists)

**Key Methods to Test**:
- Cost calculation by category
- Personnel cost aggregation
- Operational cost planning
- Error handling: missing parameters, invalid calculations

**Tests Needed**: 20-25 tests  
**Estimated Hours**: 5-6 hours

### 4.3 Capex Service (`app/services/capex_service.py`) - 44% → 80%
**Priority**: P2 - Medium  
**Current**: 44% coverage (62/111 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/services/test_capex_service.py` (exists)

**Key Methods to Test**:
- Capital expenditure planning
- Depreciation calculations
- Multi-year CapEx projections
- Error handling: invalid dates, negative amounts

**Tests Needed**: 15-20 tests  
**Estimated Hours**: 4-5 hours

---

## Phase 5: Integration Services (Week 3) - +0.5-1% Coverage

### 5.1 Odoo Integration (`app/services/odoo_integration.py`) - 49% → 80%
**Priority**: P2 - Medium  
**Current**: 49% coverage (78/154 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/services/test_odoo_integration.py` (exists)

**Tests Needed**: 20-25 tests  
**Estimated Hours**: 5-6 hours

### 5.2 Skolengo Integration (`app/services/skolengo_integration.py`) - 59% → 80%
**Priority**: P2 - Medium  
**Current**: 59% coverage (54/131 lines missing)  
**Target**: 80% coverage

**Test File**: `backend/tests/services/test_skolengo_integration.py` (exists)

**Tests Needed**: 15-20 tests  
**Estimated Hours**: 4-5 hours

---

## Implementation Checklist

### Week 1: Critical APIs
- [ ] Fix failing tests in `test_export_api.py` (25-30 tests)
- [ ] Fix failing tests in `test_integrations_api.py` (35-40 tests)
- [ ] Add missing tests in `test_consolidation_api.py` (30-35 tests)
- [ ] Create `test_materialized_view_service.py` (10-12 tests)
- [ ] Verify coverage improvement (+3-4%)

### Week 2: Service Layer & APIs
- [ ] Add missing tests in `test_writeback_service.py` (30-35 tests)
- [ ] Add missing tests in `test_configuration_api.py` (20-25 tests)
- [ ] Add missing tests in `test_planning_api.py` (30-35 tests)
- [ ] Add missing tests in `test_analysis_api.py` (35-40 tests)
- [ ] Verify coverage improvement (+2-3%)

### Week 3: Remaining Services
- [ ] Add missing tests in `test_configuration_service.py` (25-30 tests)
- [ ] Add missing tests in `test_cost_service.py` (20-25 tests)
- [ ] Add missing tests in `test_capex_service.py` (15-20 tests)
- [ ] Add missing tests in `test_odoo_integration.py` (20-25 tests)
- [ ] Add missing tests in `test_skolengo_integration.py` (15-20 tests)
- [ ] Verify coverage improvement (+1-2%)

### Final Verification
- [ ] Run full test suite: `pytest --cov=app --cov-report=term-missing`
- [ ] Verify coverage ≥ 80%
- [ ] Fix any failing tests
- [ ] Update PRODUCTION_READINESS_ASSESSMENT.md with new coverage percentage

---

## Success Metrics

**Target Coverage by Module**:
- All API endpoints: ≥ 80%
- All service methods: ≥ 80%
- Engine/calculator modules: ≥ 90% (already good, maintain)
- Models/schemas: ≥ 95% (already good, maintain)

**Overall Target**: **≥ 80% total coverage**

**Quality Metrics**:
- All new tests pass
- No test warnings or errors
- Tests follow EFIR Development Standards
- Real EFIR data scenarios included where applicable
- Error cases properly tested

---

## Quick Reference Commands

```bash
# Run tests with coverage
cd backend
source .venv/bin/activate
pytest --cov=app --cov-report=term-missing --cov-report=html

# Check specific module coverage
pytest --cov=app.api.v1.export --cov-report=term-missing tests/api/test_export_api.py

# Run only new tests
pytest tests/services/test_materialized_view_service.py -v

# Check coverage progress
pytest --cov=app --cov-report=term-missing | grep "TOTAL"
```

---

## Notes

1. **Existing Test Files**: Many test files exist but have failing tests. Priority is to fix existing tests before adding new ones.

2. **Test Fixtures**: Leverage existing fixtures in `conftest.py` for consistency.

3. **EFIR Data**: Use real EFIR scenarios (1,800 students, French education structure) in complex tests.

4. **Error Handling**: Ensure all error paths are tested (404s, validation errors, business rule violations).

5. **Integration Tests**: Some tests require database setup. Use `@pytest.mark.asyncio` and proper fixtures.

---

**Last Updated**: December 3, 2025  
**Next Review**: After Week 1 completion
