# EFIR Budget App - Testing Guide

## Overview

This document describes the testing strategy, commands, and organization for the EFIR Budget Planning Application backend.

## Test Structure

```
tests/
├── conftest.py                    # Pytest fixtures and configuration
├── test_health.py                 # Health check tests
├── test_models.py                 # Model validation tests
├── test_validators.py             # Business rule validators
├── test_migrations.py             # Database migration tests
├── test_integration.py            # Basic integration tests
├── test_rls_policies.py           # Row Level Security tests
├── engine/                        # Calculation engine tests
│   ├── test_dhg.py               # DHG calculation tests
│   ├── test_enrollment.py         # Enrollment projection tests
│   ├── test_kpi.py               # KPI calculation tests
│   └── test_revenue.py           # Revenue calculation tests
├── services/                      # Service layer tests
│   ├── test_configuration_service.py
│   ├── test_enrollment_service.py
│   ├── test_class_structure_service.py
│   ├── test_dhg_service.py
│   ├── test_revenue_service.py
│   └── test_cost_service.py
├── api/                          # API endpoint tests
│   ├── test_configuration_api.py
│   ├── test_planning_api.py
│   ├── test_costs_api.py
│   └── test_calculations_api.py
└── integration/                   # End-to-end workflow tests
    └── test_budget_workflow.py
```

## Running Tests

### All Tests
```bash
pytest
```

### With Verbose Output
```bash
pytest -v
```

### With Coverage Report
```bash
pytest --cov=app --cov-report=html --cov-report=term
```

### Specific Test Files
```bash
# Run engine tests only
pytest tests/engine/

# Run service tests only
pytest tests/services/

# Run API tests only
pytest tests/api/

# Run integration tests only
pytest tests/integration/
```

### Specific Test Patterns
```bash
# Run all DHG-related tests
pytest -k test_dhg

# Run all enrollment tests
pytest -k enrollment

# Run all configuration tests
pytest -k configuration
```

### With Coverage Threshold
```bash
pytest --cov=app --cov-report=term --cov-fail-under=80
```

## Test Categories

### 1. Unit Tests (80%+ Coverage)

**Engine Tests** (`tests/engine/`):
- ✅ `test_dhg.py` - DHG calculation logic
- ✅ `test_enrollment.py` - Enrollment projections
- ✅ `test_kpi.py` - KPI calculations
- ✅ `test_revenue.py` - Revenue calculations

**Service Tests** (`tests/services/`):
- Configuration service CRUD operations
- Budget version workflow (create, submit, approve)
- Class size parameter validation
- Subject hours matrix operations
- Teacher cost parameters
- Fee structure operations
- Enrollment planning and projections
- Class structure calculation
- DHG hours calculation
- Teacher FTE calculation
- TRMD gap analysis
- Revenue calculation with sibling discounts
- Personnel cost calculation
- Operating cost management
- CapEx depreciation

**Model Tests** (`tests/test_models.py`):
- Model validation
- Relationship integrity
- Soft delete behavior
- Audit trail fields

### 2. Integration Tests

**API Endpoint Tests** (`tests/api/`):
- GET endpoints (200 responses, data structure)
- POST endpoints (201 created, validation errors)
- PUT endpoints (200 updated, 404 not found)
- DELETE endpoints (204 no content)
- Authentication/authorization
- Error handling (400, 401, 403, 404, 422)

**Workflow Tests** (`tests/integration/test_budget_workflow.py`):
Complete budget creation workflow:
1. Create budget version
2. Configure class sizes, subject hours, teacher costs
3. Enter enrollment data
4. Calculate class structure
5. Calculate DHG and teacher FTE
6. Calculate revenue and costs
7. Consolidate budget
8. Generate financial statements
9. Submit for approval
10. Approve budget

### 3. Performance Tests

**Load Testing**:
- Test with realistic EFIR data volumes (~1,875 students)
- Test DHG calculation performance (multiple levels/subjects)
- Test enrollment projection performance (5-year projections)

## Test Data

### Fixtures in `conftest.py`

**Academic Structure**:
- `academic_cycles` - Maternelle, Élémentaire, Collège, Lycée
- `academic_levels` - PS, MS, GS, CP, 6ème, 5ème, etc.
- `nationality_types` - French, Saudi, Other
- `subjects` - French, Math, History, English
- `teacher_categories` - AEFE Detached, AEFE Funded, Local
- `fee_categories` - Tuition, DAI, Registration

**Budget Data**:
- `test_budget_version` - Working budget version
- `test_class_size_params` - Min/target/max class sizes
- `test_enrollment_data` - Sample enrollment by level/nationality
- `test_class_structure` - Calculated class formations
- `test_subject_hours_matrix` - Hours per subject/level
- `test_teacher_cost_params` - AEFE and local teacher costs
- `test_fee_structure` - Tuition and fees by level/nationality
- `test_dhg_data` - DHG hours and teacher requirements

### Realistic EFIR Data

Tests use realistic values based on EFIR operational data:
- Class sizes: 15-24 (Maternelle), 20-32 (Secondary)
- Student counts: ~1,800 total enrollment
- Teacher FTE: ~120 teachers
- Tuition: 25,000-35,000 SAR/year
- PRRD contribution: 41,863 EUR/teacher
- Standard hours: 24h (Primary), 18h (Secondary)

## Testing Best Practices

### 1. Test Naming Convention
```python
async def test_<service>_<operation>_<scenario>():
    """Test that <service> <operation> <expected outcome> when <scenario>."""
    pass
```

Examples:
- `test_enrollment_service_create_success`
- `test_enrollment_service_create_validation_error`
- `test_dhg_service_calculate_hours_with_split_classes`

### 2. Arrange-Act-Assert Pattern
```python
@pytest.mark.asyncio
async def test_create_enrollment(db_session, test_budget_version):
    # Arrange
    service = EnrollmentService(db_session)
    data = {
        "budget_version_id": test_budget_version.id,
        "level_id": test_level_id,
        "nationality_type_id": test_nat_id,
        "student_count": 25
    }

    # Act
    enrollment = await service.create(data)

    # Assert
    assert enrollment.id is not None
    assert enrollment.student_count == 25
```

### 3. Test Edge Cases
Always test:
- Empty input
- Maximum values
- Invalid input
- Null/None values
- Boundary conditions
- Error conditions

### 4. Use Fixtures for Setup
Reuse fixtures instead of duplicating setup code:
```python
@pytest.mark.asyncio
async def test_with_fixtures(
    db_session,
    test_budget_version,
    test_enrollment_data,
    test_class_structure
):
    # Test logic here
    pass
```

### 5. Test Database Isolation
Each test gets a fresh database session that's rolled back after the test, ensuring isolation.

## Coverage Requirements

**Minimum Coverage**: 80%

**Coverage by Module**:
- Engine calculations: 90%+
- Services: 85%+
- API endpoints: 80%+
- Models: 80%+

**Coverage Report**:
```bash
pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser
```

## Continuous Integration

### Pre-commit Checks
```bash
# Run before committing
pytest --cov=app --cov-fail-under=80
ruff check .
mypy app/
```

### CI/CD Pipeline
1. Lint check (Ruff)
2. Type check (mypy)
3. Unit tests (pytest)
4. Integration tests
5. Coverage check (>80%)
6. Build verification

## Common Issues & Solutions

### Issue: Import errors
**Solution**: Ensure `PYTHONPATH` includes project root
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Issue: Database migration errors in tests
**Solution**: Ensure migrations are up to date
```bash
alembic upgrade head
```

### Issue: Fixture dependency errors
**Solution**: Check fixture dependency order in `conftest.py`

### Issue: Async tests not running
**Solution**: Ensure `pytest-asyncio` is installed and tests use `@pytest.mark.asyncio`

## Test Data Management

### Creating Test Data
Use fixtures in `conftest.py` for reusable test data. Each fixture should:
1. Create necessary prerequisite data
2. Be independently usable
3. Clean up after itself (via session rollback)

### Realistic Test Values
Based on EFIR operational data:
- Total enrollment: ~1,800 students
- Maternelle: ~450 students (3 levels × 50 students/level × 3 classes)
- Élémentaire: ~600 students
- Collège: ~450 students
- Lycée: ~300 students
- Teacher FTE: ~120 total
- H/E ratio: ~0.067 (target benchmark)

## API Testing

### Authentication
Tests mock authentication via dependency override:
```python
def override_get_current_user():
    return User(id=uuid4(), email="test@efir.edu.sa")

app.dependency_overrides[get_current_user] = override_get_current_user
```

### Testing Endpoints
```python
from fastapi.testclient import TestClient

client = TestClient(app)

def test_get_budget_versions():
    response = client.get("/api/v1/budget-versions")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

## Performance Benchmarks

### Expected Performance
- Enrollment projection (5 years): <100ms
- DHG calculation (all levels): <500ms
- Class structure calculation: <200ms
- Revenue calculation (1,800 students): <1s
- Budget consolidation: <2s

### Load Testing
```bash
# Install locust
pip install locust

# Run load test
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Debugging Tests

### Run Single Test with Output
```bash
pytest tests/services/test_enrollment_service.py::test_create_enrollment -v -s
```

### Debug with Breakpoint
```python
import pdb; pdb.set_trace()
```

### Enable SQL Logging
In `conftest.py`:
```python
engine = create_async_engine(
    test_database_url,
    echo=True,  # Enable SQL logging
)
```

## Documentation

- API Documentation: `/docs/API.md`
- Module Specifications: `/docs/modules/`
- Testing Guide: `/docs/TESTING.md` (this file)

## References

- pytest: https://docs.pytest.org/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/
- FastAPI Testing: https://fastapi.tiangolo.com/tutorial/testing/
- SQLAlchemy Testing: https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites
