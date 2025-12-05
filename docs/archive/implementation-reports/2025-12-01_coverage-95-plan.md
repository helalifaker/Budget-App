# Test Coverage Improvement Plan: 73.62% → 95%

**Current Status**: 73.62% coverage  
**Target**: 95% coverage  
**Gap**: 21.38 percentage points  
**Priority**: **IMMEDIATE**

---

## Executive Summary

To reach 95% coverage, we need to add comprehensive tests across **13 critical modules** that currently have low coverage. The strategy is:

1. **Week 1**: Fix failing tests + Create missing test files + Cover critical APIs (export, integrations, consolidation)
2. **Week 2**: Expand service layer tests (writeback, configuration, cost, capex)
3. **Week 3**: Complete remaining API endpoints (planning, analysis, costs)
4. **Week 4**: Finalize integration services and edge cases

**Estimated Effort**: 4 weeks (1 developer full-time)  
**Estimated Tests**: 500-600 new tests

---

## Current Coverage Analysis

### Critical Gaps (>50% missing lines)

| Module | Current | Missing Lines | Priority | Tests Needed |
|--------|---------|---------------|----------|--------------|
| **app/api/v1/export.py** | 13% | 123/142 | P0 | 35-40 tests |
| **app/api/v1/integrations.py** | 21% | 177/224 | P0 | 45-50 tests |
| **app/api/v1/consolidation.py** | 21% | 133/168 | P0 | 35-40 tests |
| **app/services/materialized_view_service.py** | 28% | 34/47 | P0 | ✅ **CREATED** (18 tests) |
| **app/api/v1/configuration.py** | 38% | 95/154 | P1 | 30-35 tests |
| **app/api/v1/costs.py** | 30% | 124/176 | P1 | 35-40 tests |
| **app/api/v1/planning.py** | 27% | 141/193 | P1 | 40-45 tests |
| **app/api/v1/analysis.py** | 30% | 159/226 | P1 | 45-50 tests |
| **app/services/configuration_service.py** | 30% | 98/140 | P1 | 30-35 tests |
| **app/services/writeback_service.py** | 42% | 125/216 | P1 | 50-60 tests |
| **app/services/capex_service.py** | 44% | 62/111 | P2 | 20-25 tests |
| **app/services/cost_service.py** | 57% | 75/175 | P2 | 30-35 tests |
| **app/services/odoo_integration.py** | 49% | 78/154 | P2 | 25-30 tests |
| **app/services/skolengo_integration.py** | 59% | 54/131 | P2 | 20-25 tests |

**Total Estimated Tests**: 500-600 tests

---

## Phase 1: Critical APIs (Week 1) - Target: +8-10% Coverage

### 1.1 Export API (`app/api/v1/export.py`) - 13% → 95%
**Status**: ⚠️ Tests exist but failing

**Actions**:
- [x] Create `test_materialized_view_service.py` (DONE - 18 tests)
- [ ] Fix `test_export_api.py` async mocking issues
- [ ] Add tests for all export endpoints (Excel, PDF, CSV)
- [ ] Test error handling (missing dependencies, invalid IDs)
- [ ] Test file generation and streaming
- [ ] Test edge cases (None values, empty data, large files)

**Tests Needed**: 35-40 tests  
**Estimated Hours**: 10-12 hours

### 1.2 Integrations API (`app/api/v1/integrations.py`) - 21% → 95%
**Status**: ⚠️ Tests exist but failing

**Actions**:
- [ ] Fix `test_integrations_api.py` async mocking
- [ ] Test Odoo connection endpoints
- [ ] Test Skolengo import/export endpoints
- [ ] Test AEFE position import endpoints
- [ ] Test error handling (connection failures, invalid data)

**Tests Needed**: 45-50 tests  
**Estimated Hours**: 12-15 hours

### 1.3 Consolidation API (`app/api/v1/consolidation.py`) - 21% → 95%
**Status**: ⚠️ Tests exist but need expansion

**Actions**:
- [ ] Expand `test_consolidation_api.py`
- [ ] Test version creation and management
- [ ] Test submit/approve workflow
- [ ] Test version comparison
- [ ] Test consolidation calculation
- [ ] Test error handling (invalid status transitions)

**Tests Needed**: 35-40 tests  
**Estimated Hours**: 10-12 hours

---

## Phase 2: Service Layer - Critical Services (Week 2) - Target: +6-8% Coverage

### 2.1 Writeback Service (`app/services/writeback_service.py`) - 42% → 95%
**Status**: ⚠️ Tests exist but need major expansion

**Actions**:
- [ ] Expand `test_writeback_service.py`
- [ ] Test single cell updates with optimistic locking
- [ ] Test batch updates with rollback
- [ ] Test version conflict detection
- [ ] Test cell history and comments
- [ ] Test undo/redo functionality
- [ ] Test cell locking for approved budgets
- [ ] Test real-time sync scenarios

**Tests Needed**: 50-60 tests  
**Estimated Hours**: 15-18 hours

### 2.2 Configuration Service (`app/services/configuration_service.py`) - 30% → 95%
**Status**: ⚠️ Tests exist but need expansion

**Actions**:
- [ ] Expand `test_configuration_service.py`
- [ ] Test CRUD operations for all config types
- [ ] Test business rule validation
- [ ] Test constraint enforcement
- [ ] Test bulk operations
- [ ] Test cross-module dependencies

**Tests Needed**: 30-35 tests  
**Estimated Hours**: 10-12 hours

### 2.3 Cost Service (`app/services/cost_service.py`) - 57% → 95%
**Status**: ⚠️ Tests exist but need expansion

**Actions**:
- [ ] Expand `test_cost_service.py`
- [ ] Test cost calculation by category
- [ ] Test personnel cost aggregation
- [ ] Test operational cost planning
- [ ] Test cost allocation logic
- [ ] Test error handling

**Tests Needed**: 30-35 tests  
**Estimated Hours**: 8-10 hours

### 2.4 Capex Service (`app/services/capex_service.py`) - 44% → 95%
**Status**: ⚠️ Tests exist but need expansion

**Actions**:
- [ ] Expand `test_capex_service.py`
- [ ] Test capital expenditure planning
- [ ] Test depreciation calculations
- [ ] Test multi-year CapEx projections
- [ ] Test validation and error handling

**Tests Needed**: 20-25 tests  
**Estimated Hours**: 6-8 hours

---

## Phase 3: Remaining APIs (Week 3) - Target: +4-5% Coverage

### 3.1 Configuration API (`app/api/v1/configuration.py`) - 38% → 95%
**Actions**:
- [ ] Expand `test_configuration_api.py`
- [ ] Test all CRUD endpoints
- [ ] Test validation endpoints
- [ ] Test bulk operations
- [ ] Test error handling

**Tests Needed**: 30-35 tests  
**Estimated Hours**: 8-10 hours

### 3.2 Planning API (`app/api/v1/planning.py`) - 27% → 95%
**Actions**:
- [ ] Expand `test_planning_api.py`
- [ ] Test enrollment endpoints
- [ ] Test class structure endpoints
- [ ] Test DHG endpoints
- [ ] Test revenue/cost endpoints
- [ ] Test error handling

**Tests Needed**: 40-45 tests  
**Estimated Hours**: 12-15 hours

### 3.3 Analysis API (`app/api/v1/analysis.py`) - 30% → 95%
**Actions**:
- [ ] Expand `test_analysis_api.py`
- [ ] Test KPI calculation endpoints
- [ ] Test dashboard endpoints
- [ ] Test variance analysis endpoints
- [ ] Test error handling

**Tests Needed**: 45-50 tests  
**Estimated Hours**: 12-15 hours

### 3.4 Costs API (`app/api/v1/costs.py`) - 30% → 95%
**Actions**:
- [ ] Expand `test_costs_api.py`
- [ ] Test cost calculation endpoints
- [ ] Test cost category endpoints
- [ ] Test error handling

**Tests Needed**: 35-40 tests  
**Estimated Hours**: 10-12 hours

---

## Phase 4: Integration Services (Week 4) - Target: +2-3% Coverage

### 4.1 Odoo Integration (`app/services/odoo_integration.py`) - 49% → 95%
**Actions**:
- [ ] Expand `test_odoo_integration.py`
- [ ] Test connection handling
- [ ] Test actuals import
- [ ] Test error handling and retries

**Tests Needed**: 25-30 tests  
**Estimated Hours**: 8-10 hours

### 4.2 Skolengo Integration (`app/services/skolengo_integration.py`) - 59% → 95%
**Actions**:
- [ ] Expand `test_skolengo_integration.py`
- [ ] Test enrollment import/export
- [ ] Test data comparison
- [ ] Test error handling

**Tests Needed**: 20-25 tests  
**Estimated Hours**: 6-8 hours

---

## Implementation Strategy

### Test Patterns to Use

**API Endpoint Tests**:
```python
@pytest.mark.asyncio
async def test_endpoint_success(client, authenticated_user, mock_service):
    """Test successful endpoint call."""
    with patch("app.api.v1.module.Service") as mock_service_class:
        mock_service_class.return_value = mock_service
        response = client.get("/api/v1/endpoint", headers=authenticated_user)
        assert response.status_code == 200
        assert response.json()["key"] == "expected_value"
```

**Service Method Tests**:
```python
@pytest.mark.asyncio
async def test_service_method_success(db_session, test_fixtures):
    """Test successful service method."""
    service = ServiceClass(db_session)
    result = await service.method(param1, param2)
    assert result.field == expected_value
```

**Error Handling Tests**:
```python
@pytest.mark.asyncio
async def test_service_method_validation_error(db_session):
    """Test service method with invalid input."""
    service = ServiceClass(db_session)
    with pytest.raises(ValidationError, match="error message"):
        await service.method(invalid_param)
```

---

## Daily Progress Tracking

### Week 1 Checklist
- [ ] Day 1: Fix export API tests (35-40 tests)
- [ ] Day 2: Fix integrations API tests (45-50 tests)
- [ ] Day 3: Expand consolidation API tests (35-40 tests)
- [ ] Day 4: Verify Phase 1 coverage improvement
- [ ] Day 5: Code review and fixes

### Week 2 Checklist
- [ ] Day 1: Expand writeback service tests (50-60 tests)
- [ ] Day 2: Expand configuration service tests (30-35 tests)
- [ ] Day 3: Expand cost service tests (30-35 tests)
- [ ] Day 4: Expand capex service tests (20-25 tests)
- [ ] Day 5: Verify Phase 2 coverage improvement

### Week 3 Checklist
- [ ] Day 1: Expand configuration API tests (30-35 tests)
- [ ] Day 2: Expand planning API tests (40-45 tests)
- [ ] Day 3: Expand analysis API tests (45-50 tests)
- [ ] Day 4: Expand costs API tests (35-40 tests)
- [ ] Day 5: Verify Phase 3 coverage improvement

### Week 4 Checklist
- [ ] Day 1: Expand Odoo integration tests (25-30 tests)
- [ ] Day 2: Expand Skolengo integration tests (20-25 tests)
- [ ] Day 3: Final coverage check and gap analysis
- [ ] Day 4: Fix any remaining failing tests
- [ ] Day 5: Final verification - confirm 95% coverage achieved

---

## Success Metrics

**Coverage Targets by Module**:
- All API endpoints: ≥ 95%
- All service methods: ≥ 95%
- Engine/calculator modules: ≥ 95% (maintain current high coverage)
- Models/schemas: ≥ 95% (maintain current high coverage)

**Overall Target**: **≥ 95% total coverage**

**Quality Metrics**:
- All new tests pass
- No test warnings or errors
- Tests follow EFIR Development Standards
- Real EFIR data scenarios included
- Error cases properly tested
- Edge cases covered

---

## Quick Reference Commands

```bash
# Run all tests with coverage
cd backend
source .venv/bin/activate
pytest --cov=app --cov-report=term-missing --cov-report=html

# Check specific module coverage
pytest --cov=app.api.v1.export --cov-report=term-missing tests/api/test_export_api.py

# Run only new tests
pytest tests/services/test_materialized_view_service.py -v

# Check coverage progress
pytest --cov=app --cov-report=term-missing | grep "TOTAL"

# Run tests in watch mode (for development)
pytest-watch --cov=app tests/
```

---

## Notes

1. **Test Client**: Use `TestClient` from FastAPI for sync endpoint tests, but ensure async dependencies are properly mocked.

2. **Async Mocking**: Use `AsyncMock` from `unittest.mock` for async service methods.

3. **Database Fixtures**: Leverage existing fixtures in `conftest.py` for consistent test data.

4. **EFIR Data**: Use real EFIR scenarios (1,800 students, French education structure) in complex tests.

5. **Error Handling**: Ensure all error paths are tested (404s, validation errors, business rule violations).

6. **Integration Tests**: Some tests require database setup. Use `@pytest.mark.asyncio` and proper fixtures.

---

**Last Updated**: December 3, 2025  
**Current Progress**: Materialized View Service tests created (18 tests)  
**Next Milestone**: Fix and expand export API tests
