# API Test Coverage Expansion Report
**Date**: December 4, 2025
**Agent**: QA & Validation Agent (Agent 6)
**Mission**: Expand Planning, Analysis, Costs, and Configuration API tests to 95% coverage

---

## Executive Summary

### Current State
| API Module | Current Coverage | Current Tests | Target Coverage | Tests Needed |
|------------|------------------|---------------|-----------------|--------------|
| Planning API | 27% | 19 tests | 95% | ~45 tests |
| Analysis API | 30% | 23 tests | 95% | ~50 tests |
| Costs API | 30% | 18 tests | 95% | ~40 tests |
| Configuration API | 38% | 27 tests | 95% | ~35 tests |

### Reference Benchmark
- **Consolidation API**: 93% coverage with 45 comprehensive tests
- This proves the test pattern works and is achievable

### Gap Analysis
**Total Missing Lines**:
- Planning: 141/193 lines missing (73% gap)
- Analysis: 159/226 lines missing (70% gap)
- Costs: 124/176 lines missing (70% gap)
- Configuration: 95/154 lines missing (62% gap)

**Total Tests Needed**: ~170 new tests (120-135 core + 35 configuration bonus)

---

## Root Cause Analysis

### Why Current Tests Have Low Coverage

1. **Authentication Pattern Issue** ✅ IDENTIFIED
   - Current tests use nested `patch("app.dependencies.auth.get_current_user")`
   - **Solution**: Use `app.dependency_overrides` in fixture (proven in consolidation tests)

2. **Incomplete CRUD Coverage**
   - Many endpoints lack DELETE, PUT tests
   - Error paths (404, 400, 422, 500) not fully tested

3. **Missing Edge Cases**
   - Validation errors not covered
   - Business rule violations not tested
   - Empty result sets not handled

---

## Proven Test Pattern (from Consolidation API - 93% Coverage)

### ✅ Correct Authentication Pattern

```python
@pytest.fixture
def client():
    """Create test client with auth override."""
    from app.dependencies.auth import get_current_user, require_manager

    def mock_get_current_user():
        user = MagicMock()
        user.id = uuid.uuid4()
        user.email = "test@efir.local"
        user.role = "admin"
        return user

    def mock_require_manager():
        manager = MagicMock()
        manager.id = uuid.uuid4()
        manager.email = "manager@efir.local"
        manager.role = "finance_director"
        return manager

    app.dependency_overrides[get_current_user] = mock_get_current_user
    app.dependency_overrides[require_manager] = mock_require_manager

    yield TestClient(app)

    # Clean up
    app.dependency_overrides.clear()
```

### ✅ Correct Test Structure

```python
def test_get_endpoint_success(self, client):
    """Test successful retrieval."""
    version_id = uuid.uuid4()

    # Mock service layer
    with patch("app.api.v1.module.get_service") as mock_svc:
        mock_service = AsyncMock()
        mock_service.method.return_value = [mock_data]
        mock_svc.return_value = mock_service

        # Make request (NO nested auth patch needed - handled by fixture)
        response = client.get(f"/api/v1/module/{version_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
```

---

## Detailed Test Expansion Plan

### PART 1: Planning API (45 tests needed)

**Current**: 19 tests, 27% coverage
**Target**: ~45 tests, 95% coverage

#### Enrollment Planning (15 tests)
1. ✅ `test_get_enrollment_plan_success()` - GET 200
2. ✅ `test_get_enrollment_plan_not_found()` - GET 404
3. ⭐ `test_get_enrollment_plan_empty()` - GET 200 with []
4. ⭐ `test_create_enrollment_entry_success()` - POST 201
5. ⭐ `test_create_enrollment_validation_error()` - POST 400 (negative count)
6. ⭐ `test_create_enrollment_capacity_exceeded()` - POST 422 (>1875)
7. ⭐ `test_create_enrollment_duplicate()` - POST 400 (duplicate level+nationality)
8. ⭐ `test_update_enrollment_entry_success()` - PUT 200
9. ⭐ `test_update_enrollment_not_found()` - PUT 404
10. ⭐ `test_update_enrollment_validation()` - PUT 400
11. ⭐ `test_delete_enrollment_entry_success()` - DELETE 204
12. ⭐ `test_delete_enrollment_not_found()` - DELETE 404
13. ⭐ `test_get_enrollment_summary_success()` - GET /summary 200
14. ⭐ `test_project_enrollment_success()` - POST /project 200
15. ⭐ `test_project_enrollment_invalid_scenario()` - POST /project 400

#### Class Structure (10 tests)
16. ⭐ `test_get_class_structure_success()`
17. ⭐ `test_get_class_structure_not_found()`
18. ⭐ `test_calculate_class_structure_success()` - POST /calculate
19. ⭐ `test_calculate_class_structure_missing_enrollment()` - 400
20. ⭐ `test_calculate_class_structure_atsem()` - Maternelle ATSEM assignment
21. ⭐ `test_update_class_structure_success()`
22. ⭐ `test_update_class_structure_not_found()`
23. ⭐ `test_update_class_structure_validation()` - Min/max validation
24. ⭐ `test_class_structure_manual_override()`
25. ⭐ `test_class_structure_target_vs_max()`

#### DHG Workforce Planning (12 tests)
26. ⭐ `test_get_dhg_subject_hours_success()`
27. ⭐ `test_calculate_dhg_hours_success()` - POST /calculate
28. ⭐ `test_calculate_dhg_hours_missing_class_structure()` - 400
29. ⭐ `test_get_teacher_requirements_success()`
30. ⭐ `test_calculate_fte_success()` - POST /calculate-fte
31. ⭐ `test_calculate_fte_hsa_limits()` - Max 4 hours HSA
32. ⭐ `test_get_trmd_gap_analysis_success()` - TRMD endpoint
33. ⭐ `test_get_teacher_allocations_success()`
34. ⭐ `test_create_teacher_allocation_success()` - POST 201
35. ⭐ `test_update_teacher_allocation()` - PUT
36. ⭐ `test_delete_teacher_allocation()` - DELETE 204
37. ⭐ `test_bulk_update_allocations_success()` - POST /bulk-update

#### Error Handling (8 tests)
38. ⭐ `test_internal_server_error()` - 500
39. ⭐ `test_unauthorized_access()` - 401
40. ⭐ `test_invalid_uuid_format()` - 422
41. ⭐ `test_missing_required_fields()` - 422
42. ⭐ `test_invalid_json_body()` - 422
43. ⭐ `test_concurrent_update_conflict()` - 409
44. ⭐ `test_rate_limit_exceeded()` - 429
45. ⭐ `test_service_unavailable()` - 503

---

### PART 2: Analysis API (50 tests needed)

**Current**: 23 tests, 30% coverage
**Target**: ~50 tests, 95% coverage

#### KPI Endpoints (18 tests)
1. ⭐ `test_calculate_kpis_success()` - POST /calculate 200
2. ⭐ `test_calculate_kpis_not_found()` - 404
3. ⭐ `test_calculate_kpis_missing_data()` - 400
4. ⭐ `test_get_all_kpis_success()` - GET 200
5. ⭐ `test_get_all_kpis_empty()` - GET 200 with []
6. ⭐ `test_get_all_kpis_by_category()` - Filter: educational, financial, operational
7. ⭐ `test_get_specific_kpi_success()` - GET /{kpi_code}
8. ⭐ `test_get_specific_kpi_not_found()` - 404
9. ⭐ `test_get_kpi_trends_success()` - GET /trends
10. ⭐ `test_get_kpi_trends_single_version()` - Edge case
11. ⭐ `test_get_kpi_trends_no_history()` - Empty
12. ⭐ `test_get_benchmark_comparison_success()` - GET /benchmarks
13. ⭐ `test_benchmark_within_range()` - Status: within_range
14. ⭐ `test_benchmark_above_range()` - Status: above_range
15. ⭐ `test_benchmark_below_range()` - Status: below_range
16. ⭐ `test_kpi_h_e_primary_calculation()` - Hours/Student
17. ⭐ `test_kpi_e_d_primary_calculation()` - Students/Class
18. ⭐ `test_kpi_operating_margin_calculation()` - Financial KPI

#### Dashboard Endpoints (12 tests)
19. ⭐ `test_get_dashboard_summary_success()`
20. ⭐ `test_get_enrollment_chart_success()` - Bar chart
21. ⭐ `test_get_cost_breakdown_chart_success()` - Pie chart
22. ⭐ `test_get_revenue_breakdown_chart_success()` - Bar chart
23. ⭐ `test_get_alerts_success()` - Alerts list
24. ⭐ `test_get_alerts_empty()` - No alerts
25. ⭐ `test_get_recent_activity_success()`
26. ⭐ `test_get_comparison_data_success()` - Multi-version
27. ⭐ `test_get_comparison_invalid_versions()` - 404
28. ⭐ `test_dashboard_cache_refresh()` - Materialized view
29. ⭐ `test_dashboard_performance()` - Query optimization
30. ⭐ `test_dashboard_real_time_updates()` - WebSocket

#### Budget vs Actual (10 tests)
31. ⭐ `test_import_actuals_success()` - POST /import
32. ⭐ `test_import_actuals_invalid_format()` - 400
33. ⭐ `test_import_actuals_odoo_integration()` - External API
34. ⭐ `test_calculate_variance_success()` - POST /calculate-variance
35. ⭐ `test_calculate_variance_missing_actuals()` - 400
36. ⭐ `test_get_variance_report_success()` - GET /variance
37. ⭐ `test_variance_favorable_unfavorable()` - Revenue +, Expense -
38. ⭐ `test_create_forecast_revision_success()` - POST /forecast
39. ⭐ `test_forecast_from_ytd_actuals()` - Projection
40. ⭐ `test_forecast_approval_workflow()` - Requires manager

#### Strategic Planning (10 tests)
41. ⭐ `test_create_strategic_plan_success()` - 5-year plan
42. ⭐ `test_get_strategic_plan_success()`
43. ⭐ `test_get_strategic_plan_not_found()` - 404
44. ⭐ `test_get_year_projection_success()` - Year 1-5
45. ⭐ `test_update_scenario_assumptions()` - Conservative/Base/Optimistic
46. ⭐ `test_compare_scenarios_success()` - Side-by-side
47. ⭐ `test_add_initiative_success()` - CapEx initiative
48. ⭐ `test_initiative_impact_on_costs()` - Financial impact
49. ⭐ `test_strategic_plan_enrollment_growth()` - 3% annual
50. ⭐ `test_strategic_plan_facility_expansion()` - Capacity increase

---

### PART 3: Costs API (40 tests needed)

**Current**: 18 tests, 30% coverage
**Target**: ~40 tests, 95% coverage

#### Revenue Planning (10 tests)
1. ⭐ `test_get_revenue_plan_success()`
2. ⭐ `test_get_revenue_plan_empty()`
3. ⭐ `test_calculate_revenue_success()` - POST /calculate
4. ⭐ `test_calculate_revenue_missing_enrollment()` - 400
5. ⭐ `test_calculate_revenue_sibling_discount()` - 25% for 3rd child
6. ⭐ `test_calculate_revenue_trimester_distribution()` - 40%, 30%, 30%
7. ⭐ `test_create_revenue_entry_success()` - Manual entry
8. ⭐ `test_create_revenue_invalid_account()` - Account must be 70xxx
9. ⭐ `test_update_revenue_entry()`
10. ⭐ `test_get_revenue_summary_success()`

#### Personnel Cost Planning (10 tests)
11. ⭐ `test_get_personnel_costs_success()`
12. ⭐ `test_calculate_personnel_costs_success()` - From DHG
13. ⭐ `test_calculate_personnel_costs_missing_dhg()` - 400
14. ⭐ `test_calculate_aefe_costs()` - PRRD 41,863 EUR
15. ⭐ `test_calculate_local_costs()` - SAR salaries
16. ⭐ `test_calculate_atsem_costs()` - Maternelle assistants
17. ⭐ `test_create_personnel_cost_entry()`
18. ⭐ `test_personnel_cost_invalid_account()` - Must be 64xxx
19. ⭐ `test_personnel_cost_benefits()` - Social charges
20. ⭐ `test_personnel_cost_by_category()` - AEFE vs Local

#### Operating Cost Planning (10 tests)
21. ⭐ `test_get_operating_costs_success()`
22. ⭐ `test_calculate_operating_costs_success()`
23. ⭐ `test_operating_costs_driver_based()` - Per student, per sqm
24. ⭐ `test_operating_costs_fixed()` - Rent, insurance
25. ⭐ `test_create_operating_cost_entry()`
26. ⭐ `test_operating_cost_categories()` - Supplies, utilities, maintenance
27. ⭐ `test_operating_cost_account_mapping()` - 60xxx-68xxx
28. ⭐ `test_operating_cost_validation()`
29. ⭐ `test_update_operating_cost()`
30. ⭐ `test_get_cost_summary_success()` - Combined personnel + operating

#### CapEx Planning (10 tests)
31. ⭐ `test_get_capex_plan_success()`
32. ⭐ `test_create_capex_entry_success()`
33. ⭐ `test_update_capex_entry_success()`
34. ⭐ `test_update_capex_not_found()` - 404
35. ⭐ `test_delete_capex_entry_success()` - DELETE 204
36. ⭐ `test_calculate_depreciation_success()` - Straight-line
37. ⭐ `test_depreciation_5_year_schedule()` - Computers
38. ⭐ `test_depreciation_net_book_value()`
39. ⭐ `test_get_capex_summary_success()`
40. ⭐ `test_get_annual_depreciation_by_year()`

---

### PART 4: Configuration API (35 tests - BONUS)

**Current**: 27 tests, 38% coverage
**Target**: ~35 tests, 95% coverage

#### System Configuration (8 tests)
1. ⭐ `test_get_system_configs_success()`
2. ⭐ `test_get_system_configs_by_category()`
3. ⭐ `test_get_system_config_by_key()`
4. ⭐ `test_get_system_config_not_found()` - 404
5. ⭐ `test_upsert_system_config_create()` - Create new
6. ⭐ `test_upsert_system_config_update()` - Update existing
7. ⭐ `test_upsert_eur_sar_rate()` - Exchange rate
8. ⭐ `test_upsert_max_capacity()` - 1,875 students

#### Budget Version Workflow (12 tests)
9. ⭐ `test_get_budget_versions_success()`
10. ⭐ `test_get_budget_versions_by_fiscal_year()`
11. ⭐ `test_get_budget_versions_by_status()`
12. ⭐ `test_get_budget_version_by_id()`
13. ⭐ `test_create_budget_version_success()`
14. ⭐ `test_create_budget_version_conflict()` - Duplicate WORKING
15. ⭐ `test_update_budget_version()`
16. ⭐ `test_submit_budget_version_success()` - WORKING → SUBMITTED
17. ⭐ `test_submit_budget_version_wrong_status()` - 422
18. ⭐ `test_approve_budget_version_success()` - Requires manager
19. ⭐ `test_approve_budget_unauthorized()` - 403
20. ⭐ `test_supersede_budget_version()` - APPROVED → SUPERSEDED

#### Academic Data (6 tests)
21. ⭐ `test_get_academic_cycles_success()`
22. ⭐ `test_get_academic_levels_success()`
23. ⭐ `test_get_levels_by_cycle()` - Filter Maternelle, Élémentaire, Collège, Lycée
24. ⭐ `test_academic_level_hierarchy()`
25. ⭐ `test_academic_cycle_aggregation()`
26. ⭐ `test_level_code_uniqueness()`

#### Class Size Parameters (3 tests)
27. ⭐ `test_get_class_size_params_success()`
28. ⭐ `test_upsert_class_size_param()`
29. ⭐ `test_class_size_validation()` - min < target ≤ max

#### Subject Hours Matrix (2 tests)
30. ⭐ `test_get_subject_hours_matrix()`
31. ⭐ `test_upsert_subject_hours()`

#### Fee Structure (4 tests)
32. ⭐ `test_get_fee_structure_success()`
33. ⭐ `test_upsert_fee_structure()`
34. ⭐ `test_fee_structure_nationality_types()` - French TTC, Saudi HT, Other TTC
35. ⭐ `test_fee_structure_validation()` - Positive amounts

---

## Implementation Strategy

### Phase 1: Fix Authentication Pattern (1 hour)
1. Update all 4 API test files with correct `app.dependency_overrides` fixture
2. Remove nested auth patches from all test methods
3. Verify existing tests pass

### Phase 2: Expand Planning API (3 hours)
1. Add missing CRUD operations (UPDATE, DELETE)
2. Add error path tests (404, 400, 422)
3. Add edge case tests (empty results, validation)
4. Run coverage check → Target 95%

### Phase 3: Expand Analysis API (4 hours)
1. Complete KPI endpoint tests (18 tests)
2. Complete Dashboard endpoint tests (12 tests)
3. Add Budget vs Actual tests (10 tests)
4. Add Strategic Planning tests (10 tests)
5. Run coverage check → Target 95%

### Phase 4: Expand Costs API (3 hours)
1. Complete Revenue planning tests (10 tests)
2. Complete Personnel cost tests (10 tests)
3. Complete Operating cost tests (10 tests)
4. Complete CapEx planning tests (10 tests)
5. Run coverage check → Target 95%

### Phase 5: Expand Configuration API (2 hours - BONUS)
1. Complete System config tests (8 tests)
2. Complete Budget version workflow tests (12 tests)
3. Complete Academic data tests (6 tests)
4. Complete Parameter tests (9 tests)
5. Run coverage check → Target 95%

### Phase 6: Final Validation (1 hour)
1. Run full test suite with `pytest -n auto`
2. Verify all tests pass in parallel
3. Generate coverage report
4. Document any remaining gaps

**Total Estimated Time**: 14 hours

---

## Success Criteria

### Coverage Targets
- ✅ Planning API: 27% → **95%** (+68%)
- ✅ Analysis API: 30% → **95%** (+65%)
- ✅ Costs API: 30% → **95%** (+65%)
- ✅ Configuration API: 38% → **95%** (+57%)

### Test Count Targets
- ✅ Planning API: 19 → **45 tests** (+26)
- ✅ Analysis API: 23 → **50 tests** (+27)
- ✅ Costs API: 18 → **40 tests** (+22)
- ✅ Configuration API: 27 → **35 tests** (+8)

**Total New Tests**: ~83 tests (from 87 to ~170)

### Quality Gates
1. ✅ All tests pass with `pytest -n auto` (parallel execution)
2. ✅ No flaky tests (consistent pass rate)
3. ✅ Test isolation (no interdependencies)
4. ✅ Proper mock usage (service layer mocked, not database)
5. ✅ Coverage reports generated
6. ✅ No regressions in existing tests

---

## Next Steps

1. **Immediate**: Apply the correct authentication pattern to all test files
2. **Priority 1**: Expand Planning API tests (highest ROI)
3. **Priority 2**: Expand Analysis API tests (most complex)
4. **Priority 3**: Expand Costs API tests
5. **Priority 4**: Expand Configuration API tests (bonus)

---

## Appendix: Test Template

### Standard Test Template

```python
def test_endpoint_name_scenario(self, client):
    """Test description explaining what is being tested."""
    # Arrange
    resource_id = uuid.uuid4()
    request_data = {
        "field": "value",
    }

    # Mock service layer
    with patch("app.api.v1.module.get_service") as mock_svc:
        mock_service = AsyncMock()
        mock_service.method.return_value = expected_response
        mock_svc.return_value = mock_service

        # Act
        response = client.post(
            f"/api/v1/module/endpoint/{resource_id}",
            json=request_data
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["field"] == "expected_value"

        # Verify service called correctly
        mock_service.method.assert_called_once()
```

### Error Test Template

```python
def test_endpoint_name_error_case(self, client):
    """Test error scenario."""
    resource_id = uuid.uuid4()

    with patch("app.api.v1.module.get_service") as mock_svc:
        from app.services.exceptions import NotFoundError

        mock_service = AsyncMock()
        mock_service.method.side_effect = NotFoundError("Resource", resource_id)
        mock_svc.return_value = mock_service

        response = client.get(f"/api/v1/module/endpoint/{resource_id}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
```

---

## Conclusion

This comprehensive expansion plan will increase API test coverage from **31% to 95%** across all 4 critical API modules, adding ~83 high-quality tests following the proven consolidation API pattern. The authentication fix alone will resolve most existing test failures, and the systematic CRUD + error path approach ensures complete coverage of all endpoints.

**Estimated ROI**:
- **Time Investment**: 14 hours
- **Coverage Gain**: +64% average
- **Tests Added**: 83 tests
- **Risk Reduction**: High (catches regressions, validates business logic)
- **Maintenance**: Low (using proven patterns)
