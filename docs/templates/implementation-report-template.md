# {Implementation Name} - Implementation Report

**Date**: YYYY-MM-DD
**Agent**: {agent-name}
**Scope**: {Brief scope statement - one sentence}
**Status**: {✅ Complete | 🚧 In Progress | ⚠️ Complete with Issues | ❌ Failed}

---

## Overview

**Objective**: {What was implemented - clear, specific objective}

**Approach**: {High-level approach taken}

**Duration**: {X} hours/days

**Complexity**: {Low | Medium | High}

---

## Implementation Details

### Changes Made

**Backend** ({N} files, {X} lines):
```
app/api/v1/{endpoint}.py           - {Purpose}
app/engine/{module}/calculator.py   - {Purpose}
app/models/{module}/{model}.py      - {Purpose}
app/schemas/{module}/{schema}.py    - {Purpose}
```

**Frontend** ({N} files, {X} lines):
```
src/routes/{module}/{page}.tsx      - {Purpose}
src/components/{component}.tsx      - {Purpose}
src/hooks/{hook}.ts                 - {Purpose}
```

**Database**:
- Migration: `alembic/versions/{migration}.py` - {Purpose}
- Schema Changes: {Description of schema changes}
- RLS Policies: {Description of RLS policy changes}

**Tests** ({N} tests, coverage: {X}%):
- Unit tests: `tests/{module}/test_{file}.py` - {N} tests
- Integration tests: `tests/api/test_{module}_api.py` - {N} tests
- E2E tests: `frontend/tests/e2e/{scenario}.spec.ts` - {N} tests

### Code Samples

**Key Implementation Pattern**:
```python
# Example of main implementation pattern
def key_function(input: InputModel) -> OutputModel:
    """Brief description of what this does."""
    # Implementation
    return result
```

**API Endpoint**:
```python
@router.post("/endpoint", response_model=ResponseSchema)
async def create_endpoint(data: RequestSchema) -> ResponseSchema:
    """Brief description."""
    # Implementation
    return response
```

---

## Integration Points

### APIs Changed
- `POST /api/v1/{endpoint}` - {Description of change}
- `GET /api/v1/{endpoint}/{id}` - {Description of change}
- `PUT /api/v1/{endpoint}/{id}` - {Description of change}

### Dependencies
- **{Module A}** → **{Module B}**: {Reason for dependency}
- **{Module C}** → **{Module D}**: {Reason for dependency}

### Breaking Changes
{List any breaking changes, or "None"}

- **{Change description}**
  - Impact: {What breaks}
  - Migration Path: {How to migrate}
  - Affected Code: {What needs updating}

---

## Testing

### Test Coverage

| Category | Coverage | Tests | Status |
|----------|----------|-------|--------|
| Unit | {X}% | {N} tests | {✅/⚠️/❌} |
| Integration | {X}% | {N} tests | {✅/⚠️/❌} |
| E2E | {N} scenarios | {N} tests | {✅/⚠️/❌} |

### Test Results

```
======================== Test Summary ========================
{N} passed, {N} failed, {N} skipped

Key Test Files:
  tests/{module}/test_{file}.py ........... {status}
  tests/api/test_{module}_api.py .......... {status}

{Include any notable test output or errors}
```

### Edge Cases Covered
1. {Edge case} - {How it's handled}
2. {Edge case} - {How it's handled}
3. {Edge case} - {How it's handled}

---

## Performance Impact

### Metrics

**Before Implementation**:
- Response Time: {X}ms
- Database Queries: {N}
- Memory Usage: {X}MB
- Bundle Size: {X}KB (if frontend)

**After Implementation**:
- Response Time: {Y}ms ({+/- Z}ms, {+/- W}%)
- Database Queries: {M} ({+/- N}%)
- Memory Usage: {Y}MB ({+/- Z}MB, {+/- W}%)
- Bundle Size: {Y}KB ({+/- Z}KB, {+/- W}%) (if frontend)

### Optimization Notes
{Any performance optimizations made or considerations}

---

## Deployment Notes

### Prerequisites
- {Requirement 1}
- {Requirement 2}
- {Requirement 3}

### Migration Steps
1. {Step 1 with specific commands if applicable}
2. {Step 2}
3. {Step 3}

### Environment Variables
{List any new env vars, or "None"}

```bash
{ENV_VAR_NAME}={description}
{ENV_VAR_NAME_2}={description}
```

### Rollback Plan
{Detailed steps to rollback if issues arise}

1. {Rollback step 1}
2. {Rollback step 2}
3. {Verify rollback: command or check}

---

## Known Issues

### Current Limitations
{List any known limitations, or "None"}

- {Limitation description}
  - Impact: {Who/what is affected}
  - Workaround: {Temporary solution if any}
  - Plan: {When/how this will be addressed}

### Deferred Work
{Features or improvements deferred to future}

- {Deferred item}
  - Reason deferred: {Why not included now}
  - Priority: {High | Medium | Low}
  - Estimated effort: {X} hours/days

---

## Future Enhancements

### Out of Scope for This Implementation
- {Enhancement} - {Why it was out of scope}
- {Enhancement} - {Why it was out of scope}

### Follow-up Work Needed
- [ ] {Task} - {Priority} - {Estimated effort} - {Owner}
- [ ] {Task} - {Priority} - {Estimated effort} - {Owner}
- [ ] {Task} - {Priority} - {Estimated effort} - {Owner}

### Suggested Improvements
1. {Improvement} - {Expected benefit}
2. {Improvement} - {Expected benefit}

---

## References

**Related Documents**:
- [Related ADR](link-to-adr.md)
- [Module Specification](link-to-module-spec.md)
- [API Documentation](link-to-api-docs.md)

**Code References**:
- Main implementation: `{file-path}:{line-range}`
- Tests: `{test-file-path}`
- Migration: `{migration-file-path}`

**External Resources**:
- {Link to external docs if any}

---

**Agent Handoff** (if applicable):
- **Next Agent**: {agent-name}
- **Context**: {What the next agent needs to know}
- **Open Items**: {Anything requiring follow-up}

---

**Archived**: {YYYY-MM-DD when archived}
**Archive Location**: `docs/archive/implementation-reports/{filename}.md`
