# EFIR Budget Planning Application - Tests

## Overview

This directory contains the test suite for the EFIR Budget Planning Application backend.

## Test Structure

```
tests/
├── conftest.py              # Pytest configuration and fixtures
├── test_health.py           # API health check tests
├── test_models.py           # Model import and relationship tests
├── test_validators.py       # Business logic validation tests
└── README.md               # This file
```

## Running Tests

### Run all tests:
```bash
cd backend
pytest
```

### Run with coverage:
```bash
pytest --cov=app --cov-report=html
```

### Run specific test file:
```bash
pytest tests/test_validators.py
```

### Run specific test class:
```bash
pytest tests/test_validators.py::TestClassStructureValidationSync
```

### Run specific test:
```bash
pytest tests/test_validators.py::TestClassStructureValidationSync::test_valid_class_size_within_bounds
```

### Run with verbose output:
```bash
pytest -v
```

### Run with output from print statements:
```bash
pytest -s
```

## Test Coverage

Current test coverage areas:

### ✅ Implemented
1. **Model Imports** (`test_models.py`)
   - Verifies all models can be imported without mapper errors
   - Tests CRITICAL-1, CRITICAL-2 fixes

2. **Soft Delete** (`test_models.py`)
   - Verifies BaseModel inherits SoftDeleteMixin
   - Tests HIGH-1 fix

3. **Audit Trail** (`test_models.py`)
   - Verifies audit fields exist and are nullable
   - Tests CRITICAL-3 fix

4. **Class Structure Validation** (`test_validators.py`)
   - Comprehensive validation logic tests
   - Tests HIGH-4 implementation
   - 14 test cases covering edge cases and realistic scenarios

### 📋 Pending (Phase 4+)
5. **Budget Version Business Rules**
   - Unique working per fiscal year
   - Forecast parent requirement
   - Approved version lock

6. **Planning Table Uniqueness**
   - Test unique constraints prevent duplicates

7. **DHG Calculations**
   - Test DHG hours calculation formulas
   - Test teacher FTE calculations
   - Test TRMD gap analysis

8. **Revenue Calculations**
   - Test trimester splits (40/30/30)
   - Test sibling discounts
   - Test fee structure application

9. **Cost Calculations**
   - Test AEFE cost calculations (EUR → SAR)
   - Test local teacher costs
   - Test operating cost driver-based calculations

10. **RLS Policies**
    - Test access control by role
    - Test soft-delete filtering
    - Test version-based access

## Test Development Guidelines

### Writing New Tests

1. **Follow EFIR Development Standards**:
   - ✅ Complete implementation (no TODO comments)
   - ✅ Type hints on all functions
   - ✅ Comprehensive docstrings
   - ✅ 80%+ coverage for tested modules

2. **Test Structure**:
   ```python
   class TestFeatureName:
       """Test feature description."""

       def test_specific_behavior(self):
           """Test that specific behavior works correctly."""
           # Arrange
           input_data = ...

           # Act
           result = function_under_test(input_data)

           # Assert
           assert result == expected_value
   ```

3. **Use Fixtures**:
   - Use `db_session` for database tests
   - Define new fixtures in `conftest.py` for reusable test data
   - Use `@pytest.fixture` for test setup

4. **Test Coverage Goals**:
   - Aim for 80%+ coverage minimum
   - Test happy paths (valid inputs)
   - Test edge cases (boundary values)
   - Test error cases (invalid inputs)
   - Test realistic scenarios (real EFIR data)

### Example Test

```python
import pytest
from decimal import Decimal
from app.validators.class_structure import (
    ClassStructureValidationError,
    validate_class_structure_sync,
)

class TestClassStructureValidation:
    """Test class structure validation logic."""

    def test_valid_class_size(self):
        """Test that valid class size passes validation."""
        # Arrange
        min_size, max_size = 18, 30
        avg_size = Decimal("25.5")

        # Act & Assert (should not raise)
        validate_class_structure_sync(
            min_class_size=min_size,
            max_class_size=max_size,
            avg_class_size=avg_size,
            level_name="6ème",
            number_of_classes=6,
            total_students=153,
        )

    def test_invalid_class_size_above_max(self):
        """Test that oversized class raises error."""
        # Arrange
        min_size, max_size = 18, 30
        avg_size = Decimal("35.0")  # > max

        # Act & Assert
        with pytest.raises(ClassStructureValidationError):
            validate_class_structure_sync(
                min_class_size=min_size,
                max_class_size=max_size,
                avg_class_size=avg_size,
                level_name="6ème",
                number_of_classes=4,
                total_students=140,
            )
```

## Integration Tests

Integration tests require a PostgreSQL test database.

### Setup Test Database

```bash
# Create test database
createdb efir_budget_test

# Run migrations
DATABASE_URL=postgresql://user:pass@localhost/efir_budget_test alembic upgrade head
```

### Run Integration Tests

```bash
# Set test database URL
export TEST_DATABASE_URL=postgresql://user:pass@localhost/efir_budget_test

# Run integration tests
pytest tests/test_integration.py
```

## Continuous Integration

Tests run automatically on:
- Pre-commit hooks (via Husky + lint-staged)
- Pull requests (via GitHub Actions)
- Main branch merges

## Test Dependencies

All test dependencies are in `requirements.txt`:

```
pytest==8.x
pytest-asyncio==0.x
pytest-cov==5.x
```

## Coverage Reports

Coverage reports are generated in `htmlcov/` directory:

```bash
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Contributing

When adding new features:
1. Write tests FIRST (TDD approach)
2. Ensure tests pass before committing
3. Maintain or improve coverage percentage
4. Update this README if adding new test categories

## Questions?

See:
- `docs/PHASE_0-3_CRITICAL_REVIEW.md` for testing requirements
- `CLAUDE.md` for EFIR Development Standards
- Pytest documentation: https://docs.pytest.org/
