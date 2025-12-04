# Writeback Service Test Helpers

## Overview

This document provides a quick reference for the test helper functions and patterns used in `test_writeback_service_extended.py`.

---

## Helper Functions

### `create_mock_cell()`

Creates a mock cell dictionary with sensible defaults for testing.

**Signature:**
```python
def create_mock_cell(
    cell_id: UUID | None = None,
    budget_version_id: UUID | None = None,
    module_code: str = "enrollment",
    is_locked: bool = False,
    version: int = 1,
    value_numeric: Decimal | None = Decimal("100"),
    value_text: str | None = None,
) -> dict
```

**Usage Examples:**

```python
# Basic cell
cell = create_mock_cell()

# Locked cell
locked_cell = create_mock_cell(is_locked=True)

# DHG calculation cell
dhg_cell = create_mock_cell(
    module_code="dhg",
    value_numeric=Decimal("5.33")  # 5.33 FTE
)

# Text note cell
note_cell = create_mock_cell(
    module_code="consolidation",
    value_numeric=None,
    value_text="Budget approved"
)
```

**Returns:**
```python
{
    "id": UUID,
    "budget_version_id": UUID,
    "module_code": str,
    "entity_id": UUID,
    "field_name": "student_count",
    "period_code": "2025",
    "value_numeric": Decimal | None,
    "value_text": str | None,
    "value_type": "numeric" | "text",
    "is_locked": bool,
    "lock_reason": str | None,
    "locked_by": UUID | None,
    "locked_at": datetime | None,
    "version": int,
    "modified_by": UUID,
    "modified_at": datetime,
    "created_by_id": UUID,
    "created_at": datetime,
}
```

---

### `create_mock_change()`

Creates a mock change record for testing undo/history functionality.

**Signature:**
```python
def create_mock_change(
    cell_id: UUID,
    budget_version_id: UUID,
    module_code: str = "enrollment",
    session_id: UUID | None = None,
    sequence_number: int = 1,
    old_value_numeric: Decimal | None = Decimal("100"),
    new_value_numeric: Decimal | None = Decimal("150"),
) -> dict
```

**Usage Examples:**

```python
# Single change
change = create_mock_change(cell_id, budget_version_id)

# Sequence of changes
session_id = uuid4()
changes = [
    create_mock_change(
        cell_id,
        budget_version_id,
        session_id=session_id,
        sequence_number=1,
        old_value_numeric=Decimal("100"),
        new_value_numeric=Decimal("150")
    ),
    create_mock_change(
        cell_id,
        budget_version_id,
        session_id=session_id,
        sequence_number=2,
        old_value_numeric=Decimal("150"),
        new_value_numeric=Decimal("200")
    ),
]
```

**Returns:**
```python
{
    "id": UUID,
    "cell_id": UUID,
    "budget_version_id": UUID,
    "module_code": str,
    "entity_id": UUID,
    "field_name": "student_count",
    "period_code": "2025",
    "old_value_numeric": Decimal | None,
    "old_value_text": str | None,
    "new_value_numeric": Decimal | None,
    "new_value_text": str | None,
    "change_type": "update",
    "session_id": UUID,
    "sequence_number": int,
    "changed_by": UUID,
    "changed_at": datetime,
}
```

---

## Common Mock Patterns

### Pattern 1: Mock AsyncSession with Single Result

```python
mock_session = AsyncMock(spec=AsyncSession)
mock_result = MagicMock()
mock_row = MagicMock()

# Set up row data
mock_row._mapping = create_mock_cell(cell_id, budget_version_id)

# Chain the mocks
mock_result.fetchone.return_value = mock_row
mock_session.execute.return_value = mock_result
mock_session.commit = AsyncMock()
```

### Pattern 2: Mock AsyncSession with Multiple Results

```python
mock_session = AsyncMock(spec=AsyncSession)
mock_result = MagicMock()

# Multiple rows
cells = [create_mock_cell(uuid4(), budget_version_id) for _ in range(3)]
mock_result.fetchall.return_value = [
    MagicMock(_mapping=cell) for cell in cells
]

mock_session.execute.return_value = mock_result
```

### Pattern 3: Conditional Mock Execute

```python
def mock_execute(query, params):
    if "FROM efir_budget.cell_changes" in str(query):
        return mock_result_changes
    elif "INSERT INTO efir_budget.cell_changes" in str(query):
        return mock_result_insert
    else:  # UPDATE
        return mock_result_update

mock_session.execute.side_effect = mock_execute
```

### Pattern 4: Mock Service Method

```python
service = WritebackService(mock_session)

# Replace a method with async mock
async def mock_get_cell(cell_id, raise_if_not_found=True):
    return cell if cell_id == target_cell_id else None

service.get_cell_by_id = mock_get_cell
```

---

## Test Structure Template

```python
class TestFeatureName:
    """Tests for feature description."""

    @pytest.mark.asyncio
    async def test_operation_scenario(self):
        """Test description."""
        # Arrange
        mock_session = AsyncMock(spec=AsyncSession)
        cell_id = uuid4()
        user_id = uuid4()

        # Create test data
        cell = create_mock_cell(cell_id)

        # Set up mocks
        # ... mock setup ...

        service = WritebackService(mock_session)

        # Act
        result = await service.method_name(...)

        # Assert
        assert result.field == expected_value
        mock_session.commit.assert_called_once()
```

---

## Assertion Patterns

### Assert Success
```python
assert result.updated_count == 3
assert result.failed_count == 0
assert len(result.updated_cells) == 3
mock_session.commit.assert_called_once()
```

### Assert Error Handling
```python
with pytest.raises(NotFoundError) as exc_info:
    await service.method_name(...)

assert "Cell" in str(exc_info.value)
assert str(cell_id) in str(exc_info.value)
```

### Assert Conflict Details
```python
assert result.failed_count == 1
assert result.conflicts[0].error_type == "version_conflict"
assert result.conflicts[0].current_version == 5
assert result.conflicts[0].provided_version == 3
```

### Assert Cache Invalidation
```python
with patch("app.services.writeback_service.CacheInvalidator.invalidate") as mock_invalidate:
    mock_invalidate.return_value = AsyncMock()

    await service.method_name(...)

    assert mock_invalidate.call_count >= 1
    # Verify called with correct params
    mock_invalidate.assert_called_with(
        str(budget_version_id),
        "enrollment"
    )
```

---

## EFIR-Specific Test Data

### Enrollment Planning
```python
cell = create_mock_cell(
    module_code="enrollment",
    field_name="student_count",
    period_code="2025",
    value_numeric=Decimal("100")  # 100 students
)
```

### Class Structure
```python
cell = create_mock_cell(
    module_code="class_structure",
    field_name="class_count",
    value_numeric=Decimal("4")  # 4 classes
)
```

### DHG Workforce
```python
cell = create_mock_cell(
    module_code="dhg",
    field_name="teacher_fte",
    value_numeric=Decimal("5.33")  # 5.33 FTE teachers
)
```

### Revenue
```python
cell = create_mock_cell(
    module_code="revenue",
    field_name="tuition_revenue",
    value_numeric=Decimal("2500000.00")  # 2.5M SAR
)
```

### Personnel Costs
```python
cell = create_mock_cell(
    module_code="personnel_costs",
    field_name="teacher_salary",
    value_numeric=Decimal("15000.00")  # 15K SAR/month
)
```

### Consolidation Notes
```python
cell = create_mock_cell(
    module_code="consolidation",
    field_name="notes",
    value_numeric=None,
    value_text="Budget approved by Finance Director"
)
```

---

## Mock Side Effects

### Sequential Results
```python
# First call returns None, second call returns cell
call_count = 0

async def mock_get_cell(cell_id, raise_if_not_found=True):
    nonlocal call_count
    call_count += 1
    if call_count == 1:
        return None
    else:
        return cell

service.get_cell_by_id = mock_get_cell
```

### Multiple Cells
```python
cells = [
    create_mock_cell(uuid4(), budget_version_id) for _ in range(3)
]

async def mock_get_cell(cell_id, raise_if_not_found=True):
    for cell in cells:
        if cell["id"] == cell_id:
            return cell
    return None

service.get_cell_by_id = mock_get_cell
```

---

## Error Testing Patterns

### NotFoundError
```python
async def mock_get_cell(cell_id, raise_if_not_found=True):
    if raise_if_not_found:
        raise NotFoundError("PlanningCell", str(cell_id))
    return None

service.get_cell_by_id = mock_get_cell

with pytest.raises(NotFoundError):
    await service.method_name(...)
```

### VersionConflictError
```python
cell = create_mock_cell(cell_id, version=5)  # Server has v5

update_req = CellUpdateRequest(
    value_numeric=Decimal("200"),
    version=3  # Client expects v3
)

with pytest.raises(VersionConflictError) as exc_info:
    await service.update_cell(cell_id, update_req, user_id)

assert exc_info.value.details["current_version"] == 5
assert exc_info.value.details["provided_version"] == 3
```

### CellLockedError
```python
locked_cell = create_mock_cell(
    cell_id,
    is_locked=True
)
locked_cell["lock_reason"] = "Budget approved"

async def mock_get_cell(cell_id_arg, raise_if_not_found=True):
    return locked_cell

service.get_cell_by_id = mock_get_cell

with pytest.raises(CellLockedError) as exc_info:
    await service.update_cell(...)

assert "Budget approved" in str(exc_info.value)
```

---

## Batch Operations

### Create Batch Request
```python
batch = BatchUpdateRequest(
    session_id=uuid4(),
    updates=[
        CellUpdate(
            cell_id=cell_id_1,
            value_numeric=Decimal("200"),
            version=1
        ),
        CellUpdate(
            cell_id=cell_id_2,
            value_text="Updated note",
            version=1
        ),
    ],
    allow_partial_success=True  # or False
)
```

### Test Partial Success
```python
# Cell 1: Success
# Cell 2: Version conflict
# Cell 3: Locked

cells = [
    create_mock_cell(cell_id_1, version=1),
    create_mock_cell(cell_id_2, version=5),  # Conflict
    create_mock_cell(cell_id_3, is_locked=True),  # Locked
]

result = await service.batch_update_cells(batch, user_id)

assert result.updated_count == 1
assert result.failed_count == 2
assert len(result.conflicts) == 2

error_types = [c.error_type for c in result.conflicts]
assert "version_conflict" in error_types
assert "cell_locked" in error_types
```

---

## Undo Operations

### Create Undo Request
```python
session_id = uuid4()
request = UndoRequest(session_id=session_id)

result = await service.undo_session(request, user_id)

assert result.reverted_count == expected_count
assert len(result.reverted_cells) == expected_count
```

### Test Undo with Failures
```python
# Change 1: Success
# Change 2: Cell locked
# Change 3: Cell deleted

result = await service.undo_session(request, user_id)

assert result.reverted_count == 1
assert len(result.failed_cells) == 2

error_types = [c.error_type for c in result.failed_cells]
assert "cell_locked" in error_types
assert "not_found" in error_types
```

---

## Comments

### Add Comment
```python
comment_request = CommentRequest(
    comment_text="Please review this value"
)

result = await service.add_comment(cell_id, comment_request, user_id)

assert result.comment_text == "Please review this value"
assert result.is_resolved is False
```

### Resolve Comment
```python
result = await service.resolve_comment(comment_id, user_id)

assert result.is_resolved is True
assert result.resolved_by == user_id
assert result.resolved_at is not None
```

---

## Lock Operations

### Lock Cell
```python
lock_request = LockRequest(lock_reason="Budget approved")

result = await service.lock_cell(cell_id, lock_request, user_id)

assert result.is_locked is True
assert result.lock_reason == "Budget approved"
assert result.locked_by == user_id
```

### Unlock Cell
```python
unlock_request = UnlockRequest(unlock_reason="Budget reopened")

result = await service.unlock_cell(cell_id, unlock_request, user_id)

assert result.is_locked is False
assert result.lock_reason is None
```

---

## Performance Testing Notes

### Parallel Execution
All tests must pass with `pytest -n auto`:
```bash
pytest tests/services/test_writeback_service_extended.py -n auto
```

### Isolation Requirements
- No shared state between tests
- Each test creates its own mocks
- UUID generation prevents ID collisions

---

## Quick Reference: Module Codes

| Module Code | Description | Typical Fields |
|------------|-------------|----------------|
| `enrollment` | Student enrollment planning | `student_count` |
| `class_structure` | Class formation | `class_count` |
| `dhg` | Teacher workforce planning | `teacher_fte`, `hours_per_week` |
| `revenue` | Revenue projections | `tuition_revenue`, `fees` |
| `personnel_costs` | Staff costs | `teacher_salary`, `atsem_salary` |
| `operating_costs` | Operating expenses | `supplies`, `utilities` |
| `capex` | Capital expenditures | `equipment`, `renovation` |
| `consolidation` | Budget consolidation | `notes`, `assumptions` |

---

## Best Practices

### ✅ DO
- Use `create_mock_cell()` for all cell mocks
- Use `@pytest.mark.asyncio` for all async tests
- Use `AsyncMock(spec=AsyncSession)` for database sessions
- Test both success and failure paths
- Assert transaction commits
- Verify cache invalidation when relevant

### ❌ DON'T
- Share mocks between tests
- Forget `await` on async calls
- Use `MagicMock` for async methods (use `AsyncMock`)
- Skip error case testing
- Forget to assert side effects (commits, invalidations)

---

## Debugging Tips

### Print Mock Calls
```python
# See all calls to execute
print(mock_session.execute.call_args_list)

# See specific call
print(mock_session.execute.call_args)
```

### Inspect Exception Details
```python
with pytest.raises(VersionConflictError) as exc_info:
    await service.method_name(...)

print(f"Message: {exc_info.value.message}")
print(f"Details: {exc_info.value.details}")
print(f"Status: {exc_info.value.status_code}")
```

### Verify Change Logging
```python
# Check if change was logged
log_queries = [
    call for call in mock_session.execute.call_args_list
    if "INSERT INTO efir_budget.cell_changes" in str(call)
]
assert len(log_queries) == expected_count
```

---

## Summary

These helper functions and patterns enable:
- ✅ Consistent test data creation
- ✅ Proper async mocking
- ✅ Realistic EFIR scenarios
- ✅ Comprehensive error testing
- ✅ Easy test maintenance

**Use these patterns to maintain 95%+ coverage with clean, maintainable tests!**
