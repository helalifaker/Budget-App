# Phase 6.4 Quick Reference

## Services

### ConsolidationService
**Location:** `app/services/consolidation_service.py`

**Public Methods:**
```python
async def get_consolidation(budget_version_id: uuid.UUID) -> list[BudgetConsolidation]
async def consolidate_budget(budget_version_id: uuid.UUID, user_id: uuid.UUID | None = None) -> list[BudgetConsolidation]
async def submit_for_approval(budget_version_id: uuid.UUID, user_id: uuid.UUID) -> BudgetVersion
async def approve_budget(budget_version_id: uuid.UUID, user_id: uuid.UUID) -> BudgetVersion
async def calculate_line_items(budget_version_id: uuid.UUID) -> list[dict]
async def validate_completeness(budget_version_id: uuid.UUID) -> dict[str, any]
```

### FinancialStatementsService
**Location:** `app/services/financial_statements_service.py`

**Public Methods:**
```python
async def get_income_statement(budget_version_id: uuid.UUID, format: str = 'pcg') -> FinancialStatement
async def get_balance_sheet(budget_version_id: uuid.UUID) -> dict[str, FinancialStatement]
async def calculate_statement_lines(budget_version_id: uuid.UUID, statement_type: StatementType, statement_format: StatementFormat) -> list[dict]
async def get_period_totals(budget_version_id: uuid.UUID, period: str) -> dict[str, Decimal]
```

## Schemas

### Request Schemas
- `ConsolidationRequest`
- `SubmitForApprovalRequest`
- `ApprovebudgetRequest`
- `GenerateStatementRequest`

### Response Schemas
- `ConsolidationLineItemResponse`
- `BudgetConsolidationResponse`
- `ConsolidationValidationResponse`
- `ConsolidationSummary`
- `FinancialStatementLineResponse`
- `IncomeStatementResponse`
- `BalanceSheetResponse`
- `FinancialPeriodTotals`
- `WorkflowActionResponse`
- `ConsolidationVarianceItem`
- `ConsolidationVarianceResponse`

## API Endpoints

### Budget Consolidation
```
GET    /api/v1/consolidation/{version_id}
POST   /api/v1/consolidation/{version_id}/consolidate
POST   /api/v1/consolidation/{version_id}/submit
POST   /api/v1/consolidation/{version_id}/approve          [Manager Only]
GET    /api/v1/consolidation/{version_id}/validation
GET    /api/v1/consolidation/{version_id}/summary
```

### Financial Statements
```
GET    /api/v1/consolidation/statements/income/{version_id}?format=pcg|ifrs
GET    /api/v1/consolidation/statements/balance/{version_id}
GET    /api/v1/consolidation/statements/{version_id}/periods
GET    /api/v1/consolidation/statements/{version_id}/periods/{period}
```

## Consolidation Categories

### Revenue Categories
- `REVENUE_TUITION` - 701xx (Tuition by trimester)
- `REVENUE_FEES` - 702xx-709xx (DAI, registration, etc.)
- `REVENUE_OTHER` - 75xxx-77xxx (Other revenue)

### Personnel Categories
- `PERSONNEL_TEACHING` - 64110-64119 (Teaching staff)
- `PERSONNEL_ADMIN` - 64120-64129 (Admin staff)
- `PERSONNEL_SUPPORT` - 64130-64139 (Support staff)
- `PERSONNEL_SOCIAL` - 645xx (Social charges)

### Operating Categories
- `OPERATING_SUPPLIES` - 606xx (Supplies)
- `OPERATING_UTILITIES` - 6061x (Utilities)
- `OPERATING_MAINTENANCE` - 615xx (Maintenance)
- `OPERATING_INSURANCE` - 616xx (Insurance)
- `OPERATING_OTHER` - 60xxx-68xxx (Other operating)

### CapEx Categories
- `CAPEX_EQUIPMENT` - 2154x (Equipment)
- `CAPEX_IT` - 2183x (IT)
- `CAPEX_FURNITURE` - 2184x (Furniture)
- `CAPEX_BUILDING` - 213xx (Building improvements)
- `CAPEX_SOFTWARE` - 205xx (Software)

## Workflow States

```
WORKING → SUBMITTED → APPROVED
                   ↓
              SUPERSEDED
```

**Transitions:**
- `submit_for_approval()` - WORKING → SUBMITTED
- `approve_budget()` - SUBMITTED → APPROVED (also marks previous as SUPERSEDED)

## Business Rules

### Submission Rules
1. Can only submit if status is WORKING
2. Must pass completeness validation:
   - Enrollment planning exists
   - Class structure exists
   - At least one revenue entry
   - At least one personnel cost entry
   - At least one operating cost entry

### Approval Rules
1. Can only approve if status is SUBMITTED
2. Requires manager role
3. Previous approved versions for same fiscal year marked as SUPERSEDED
4. Approved version becomes BASELINE

### Consolidation Rules
1. Aggregates by account_code from all source tables
2. Maps to consolidation categories based on account code ranges
3. Calculates totals:
   - `Operating Result = Total Revenue - Total Personnel - Total Operating`
   - `Net Result = Operating Result` (CapEx not expensed directly)

## Period Identifiers

- `p1` - Period 1 (January - June)
- `summer` - Summer period (July - August)
- `p2` - Period 2 (September - December)
- `annual` - Full year

## Statement Formats

- `pcg` - French Plan Comptable Général (Compte de résultat)
- `ifrs` - International Financial Reporting Standards (Income Statement)

## Import Statements

### Service Usage
```python
from app.services.consolidation_service import ConsolidationService
from app.services.financial_statements_service import FinancialStatementsService

# In FastAPI endpoint or service
consolidation_service = ConsolidationService(session)
statements_service = FinancialStatementsService(session)
```

### Schema Usage
```python
from app.schemas.consolidation import (
    BudgetConsolidationResponse,
    ConsolidationLineItemResponse,
    IncomeStatementResponse,
    FinancialPeriodTotals,
    WorkflowActionResponse,
)
```

### Router Registration
```python
from app.api.v1.consolidation import router as consolidation_router

app.include_router(consolidation_router)
```

## Error Handling

### Exception Types
- `NotFoundError` - 404 (Budget version not found)
- `ValidationError` - 400 (Invalid data)
- `BusinessRuleError` - 422 (Workflow violation)
- `ForbiddenError` - 403 (Insufficient permissions)

### Example
```python
try:
    await consolidation_service.submit_for_approval(version_id, user_id)
except BusinessRuleError as e:
    # Handle workflow violation
    print(f"Rule: {e.details['rule']}, Message: {e.message}")
except NotFoundError as e:
    # Handle not found
    print(f"Not found: {e.message}")
```

## Common Patterns

### Get and Consolidate
```python
# Get existing consolidation
consolidations = await service.get_consolidation(version_id)

# Recalculate if needed
if not consolidations:
    consolidations = await service.consolidate_budget(version_id, user_id)
```

### Full Workflow
```python
# 1. Validate
validation = await service.validate_completeness(version_id)
if not validation['is_complete']:
    raise ValidationError("Budget incomplete")

# 2. Consolidate
await service.consolidate_budget(version_id, user_id)

# 3. Submit
await service.submit_for_approval(version_id, user_id)

# 4. Approve (as manager)
await service.approve_budget(version_id, manager_id)

# 5. Generate statements
income_stmt = await statements_service.get_income_statement(version_id, 'pcg')
balance_sheet = await statements_service.get_balance_sheet(version_id)
```

### Get Totals by Period
```python
periods = ['p1', 'summer', 'p2', 'annual']
for period in periods:
    totals = await statements_service.get_period_totals(version_id, period)
    print(f"{period}: Revenue={totals['total_revenue']}, "
          f"Expenses={totals['total_expenses']}, "
          f"Net={totals['net_result']}")
```

## Testing Patterns

### Service Testing
```python
import pytest
from app.services.consolidation_service import ConsolidationService

@pytest.mark.asyncio
async def test_consolidate_budget(async_session, sample_budget_version):
    service = ConsolidationService(async_session)
    result = await service.consolidate_budget(
        sample_budget_version.id,
        user_id=sample_user.id
    )
    assert len(result) > 0
    assert all(item.is_calculated for item in result)
```

### API Testing
```python
from fastapi.testclient import TestClient

def test_get_consolidated_budget(client: TestClient, auth_headers):
    response = client.get(
        f"/api/v1/consolidation/{version_id}",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "total_expenses" in data
```

## Performance Considerations

- Consolidation aggregates from potentially thousands of records
- Use database-level aggregation (SQL GROUP BY) for performance
- Statement generation caches results (doesn't regenerate if exists)
- Consider adding caching layer for frequently accessed consolidations
- Period totals currently return same data (needs period-specific implementation)

## Future Enhancements

- [ ] Full cash flow statement implementation
- [ ] Complete balance sheet with all asset/liability categories
- [ ] Period-specific data aggregation
- [ ] Variance analysis service and endpoints
- [ ] Statement comparison between versions
- [ ] Excel/PDF export for statements
- [ ] Statement templates for different formats
- [ ] Drill-down from statement lines to source records
- [ ] Consolidation history and audit trail
- [ ] Real-time consolidation updates via WebSocket

---

**Quick Reference Version:** 1.0
**Last Updated:** December 2, 2025
