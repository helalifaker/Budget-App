# Consolidation & Financial Statements API Reference

Quick reference guide for Phase 6.4 API endpoints.

## Base URL
```
/api/v1/consolidation
```

## Authentication
All endpoints require authentication via Bearer token.
Approval endpoint requires `manager` role.

---

## Budget Consolidation Endpoints

### 1. Get Consolidated Budget
```http
GET /api/v1/consolidation/{version_id}
```

**Description:** Retrieve consolidated budget with all line items grouped by type.

**Response:** `BudgetConsolidationResponse`

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.efir.edu.sa/api/v1/consolidation/550e8400-e29b-41d4-a716-446655440000
```

---

### 2. Run Consolidation
```http
POST /api/v1/consolidation/{version_id}/consolidate
```

**Description:** Calculate consolidated budget by aggregating all planning modules.

**Request Body:** `ConsolidationRequest` (optional)
```json
{
  "recalculate": true
}
```

**Response:** `BudgetConsolidationResponse`

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"recalculate": true}' \
  https://api.efir.edu.sa/api/v1/consolidation/550e8400-e29b-41d4-a716-446655440000/consolidate
```

---

### 3. Submit for Approval
```http
POST /api/v1/consolidation/{version_id}/submit
```

**Description:** Submit budget version for approval (WORKING → SUBMITTED).

**Request Body:** `SubmitForApprovalRequest` (optional)
```json
{
  "notes": "Budget ready for review"
}
```

**Response:** `WorkflowActionResponse`

**Business Rules:**
- Can only submit if status is WORKING
- Must pass completeness validation

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Budget ready for review"}' \
  https://api.efir.edu.sa/api/v1/consolidation/550e8400-e29b-41d4-a716-446655440000/submit
```

---

### 4. Approve Budget
```http
POST /api/v1/consolidation/{version_id}/approve
```

**Description:** Approve budget version (SUBMITTED → APPROVED). **Manager role required.**

**Request Body:** `ApprovebudgetRequest` (optional)
```json
{
  "notes": "Approved by Finance Director"
}
```

**Response:** `WorkflowActionResponse`

**Business Rules:**
- Can only approve if status is SUBMITTED
- Requires manager role
- Previous approved versions marked as SUPERSEDED
- Approved version becomes BASELINE

**Example:**
```bash
curl -X POST \
  -H "Authorization: Bearer <manager-token>" \
  -H "Content-Type: application/json" \
  -d '{"notes": "Approved by Finance Director"}' \
  https://api.efir.edu.sa/api/v1/consolidation/550e8400-e29b-41d4-a716-446655440000/approve
```

---

### 5. Validate Completeness
```http
GET /api/v1/consolidation/{version_id}/validation
```

**Description:** Check if all required modules are complete.

**Response:** `ConsolidationValidationResponse`

**Checks:**
- Enrollment planning exists
- Class structure exists
- Revenue planning exists
- Personnel costs exist
- Operating costs exist

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.efir.edu.sa/api/v1/consolidation/550e8400-e29b-41d4-a716-446655440000/validation
```

**Response Example:**
```json
{
  "is_complete": true,
  "missing_modules": [],
  "warnings": [],
  "module_counts": {
    "enrollment": 42,
    "class_structure": 14,
    "revenue": 15,
    "personnel_costs": 35,
    "operating_costs": 25,
    "capex": 10
  }
}
```

---

### 6. Get Consolidation Summary
```http
GET /api/v1/consolidation/{version_id}/summary
```

**Description:** Get high-level consolidation summary without detailed line items.

**Response:** `ConsolidationSummary`

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.efir.edu.sa/api/v1/consolidation/550e8400-e29b-41d4-a716-446655440000/summary
```

---

## Financial Statements Endpoints

### 7. Get Income Statement
```http
GET /api/v1/consolidation/statements/income/{version_id}?format=pcg
```

**Description:** Generate or retrieve income statement.

**Query Parameters:**
- `format` (optional): `pcg` (French PCG) or `ifrs` (IFRS). Default: `pcg`

**Response:** `IncomeStatementResponse`

**Formats:**
- **PCG:** Compte de résultat (French Plan Comptable Général)
- **IFRS:** Income Statement (International Financial Reporting Standards)

**Example:**
```bash
# French PCG format
curl -H "Authorization: Bearer <token>" \
  "https://api.efir.edu.sa/api/v1/consolidation/statements/income/550e8400-e29b-41d4-a716-446655440000?format=pcg"

# IFRS format
curl -H "Authorization: Bearer <token>" \
  "https://api.efir.edu.sa/api/v1/consolidation/statements/income/550e8400-e29b-41d4-a716-446655440000?format=ifrs"
```

---

### 8. Get Balance Sheet
```http
GET /api/v1/consolidation/statements/balance/{version_id}
```

**Description:** Generate or retrieve balance sheet (assets + liabilities).

**Response:** `BalanceSheetResponse`

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.efir.edu.sa/api/v1/consolidation/statements/balance/550e8400-e29b-41d4-a716-446655440000
```

**Response Example:**
```json
{
  "budget_version_id": "550e8400-e29b-41d4-a716-446655440000",
  "fiscal_year": 2025,
  "assets": { ... },
  "liabilities": { ... },
  "is_balanced": true
}
```

---

### 9. Get All Period Totals
```http
GET /api/v1/consolidation/statements/{version_id}/periods
```

**Description:** Get financial totals for all periods.

**Periods:**
- **P1:** Period 1 (January - June)
- **Summer:** Summer period (July - August)
- **P2:** Period 2 (September - December)
- **Annual:** Full year

**Response:** `list[FinancialPeriodTotals]`

**Example:**
```bash
curl -H "Authorization: Bearer <token>" \
  https://api.efir.edu.sa/api/v1/consolidation/statements/550e8400-e29b-41d4-a716-446655440000/periods
```

---

### 10. Get Single Period Total
```http
GET /api/v1/consolidation/statements/{version_id}/periods/{period}
```

**Description:** Get financial totals for a specific period.

**Path Parameters:**
- `period`: `p1`, `summer`, `p2`, or `annual`

**Response:** `FinancialPeriodTotals`

**Example:**
```bash
# Period 1 totals
curl -H "Authorization: Bearer <token>" \
  https://api.efir.edu.sa/api/v1/consolidation/statements/550e8400-e29b-41d4-a716-446655440000/periods/p1

# Annual totals
curl -H "Authorization: Bearer <token>" \
  https://api.efir.edu.sa/api/v1/consolidation/statements/550e8400-e29b-41d4-a716-446655440000/periods/annual
```

**Response Example:**
```json
{
  "budget_version_id": "550e8400-e29b-41d4-a716-446655440000",
  "period": "p1",
  "total_revenue": "19551200.00",
  "total_expenses": "16892500.00",
  "operating_result": "2658700.00",
  "net_result": "2658700.00"
}
```

---

## Common Response Codes

| Code | Description |
|------|-------------|
| 200  | Success |
| 201  | Created |
| 400  | Bad Request (invalid data) |
| 401  | Unauthorized (missing/invalid token) |
| 403  | Forbidden (insufficient permissions) |
| 404  | Not Found (budget version not found) |
| 422  | Unprocessable Entity (business rule violation) |
| 500  | Internal Server Error |

---

## Error Response Format

```json
{
  "detail": "Error message",
  "rule": "BUSINESS_RULE_CODE",
  "details": {
    "field": "field_name",
    "current_status": "working"
  }
}
```

---

## Workflow State Machine

```
WORKING → SUBMITTED → APPROVED
                   ↓
              SUPERSEDED
```

**Transitions:**
- `WORKING → SUBMITTED`: Via `/submit` endpoint (any authenticated user)
- `SUBMITTED → APPROVED`: Via `/approve` endpoint (manager only)
- `APPROVED → SUPERSEDED`: Automatic when new version approved for same fiscal year

---

## Common Use Cases

### Use Case 1: Complete Budget Cycle
```bash
# 1. Run consolidation
POST /api/v1/consolidation/{version_id}/consolidate

# 2. Validate completeness
GET /api/v1/consolidation/{version_id}/validation

# 3. Submit for approval
POST /api/v1/consolidation/{version_id}/submit

# 4. Approve (manager)
POST /api/v1/consolidation/{version_id}/approve

# 5. Generate income statement
GET /api/v1/consolidation/statements/income/{version_id}?format=pcg
```

### Use Case 2: Review Budget Before Submission
```bash
# 1. Get consolidated budget
GET /api/v1/consolidation/{version_id}

# 2. Get summary
GET /api/v1/consolidation/{version_id}/summary

# 3. Validate completeness
GET /api/v1/consolidation/{version_id}/validation

# 4. Get period totals
GET /api/v1/consolidation/statements/{version_id}/periods
```

### Use Case 3: Generate Financial Reports
```bash
# 1. Income statement (French PCG)
GET /api/v1/consolidation/statements/income/{version_id}?format=pcg

# 2. Income statement (IFRS)
GET /api/v1/consolidation/statements/income/{version_id}?format=ifrs

# 3. Balance sheet
GET /api/v1/consolidation/statements/balance/{version_id}

# 4. Period analysis
GET /api/v1/consolidation/statements/{version_id}/periods
```

---

## Notes

- All monetary amounts are in SAR (Saudi Riyal) with 2 decimal precision
- UUIDs must be in standard format: `550e8400-e29b-41d4-a716-446655440000`
- Dates/times are in ISO 8601 format with UTC timezone
- All endpoints support CORS for frontend integration
- Rate limiting may apply based on server configuration

---

**API Version:** 1.0
**Last Updated:** December 2, 2025
**Module:** Phase 6.4 - Consolidation & Financial Statements
