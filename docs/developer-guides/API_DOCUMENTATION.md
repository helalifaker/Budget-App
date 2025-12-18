# EFIR Budget Planning Application - API Documentation

**Version**: 1.0
**Base URL**: `http://localhost:8000/api/v1` (development) or `https://api.efir-budget.com/api/v1` (production)
**Authentication**: JWT Bearer token

## Table of Contents

1. [Authentication](#authentication)
2. [Configuration Endpoints](#configuration-endpoints)
3. [Planning Endpoints](#planning-endpoints)
4. [Consolidation Endpoints](#consolidation-endpoints)
5. [Analysis Endpoints](#analysis-endpoints)
6. [Integration Endpoints](#integration-endpoints)
7. [Error Responses](#error-responses)

---

## Authentication

All API endpoints require authentication using JWT Bearer tokens.

### Login

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@efir.local",
  "password": "password123"
}
```

**Response** (200 OK):
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "user-uuid",
    "email": "user@efir.local",
    "role": "manager"
  }
}
```

### Using the Token

Include the token in the `Authorization` header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## Configuration Endpoints

### Versions (formerly Budget Versions)

#### List Versions
```http
GET /configuration/versions
```

**Response** (200 OK):
```json
[
  {
    "id": "version-uuid",
    "name": "Budget 2025-2026",
    "fiscal_year": 2025,
    "academic_year": "2024-2025",
    "status": "WORKING",
    "start_date": "2025-01-01",
    "end_date": "2025-12-31",
    "description": "Annual budget for fiscal year 2025",
    "created_by": "user-uuid",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
  }
]
```

#### Create Version
```http
POST /configuration/versions
Content-Type: application/json

{
  "name": "Budget 2025-2026",
  "fiscal_year": 2025,
  "academic_year": "2024-2025",
  "start_date": "2025-01-01",
  "end_date": "2025-12-31",
  "description": "Annual budget"
}
```

**Response** (201 Created):
```json
{
  "id": "version-uuid",
  "name": "Budget 2025-2026",
  "fiscal_year": 2025,
  "status": "WORKING",
  ...
}
```

#### Submit Version for Approval
```http
PATCH /configuration/versions/{version_id}/submit
```

**Response** (200 OK):
```json
{
  "id": "version-uuid",
  "status": "SUBMITTED",
  "submitted_at": "2024-12-15T14:30:00Z"
}
```

#### Approve Version
```http
PATCH /configuration/versions/{version_id}/approve
```

**Response** (200 OK):
```json
{
  "id": "version-uuid",
  "status": "APPROVED",
  "approved_at": "2024-12-16T09:00:00Z",
  "approved_by": "manager-uuid"
}
```

### Class Size Parameters

#### Get Class Size Parameters
```http
GET /configuration/class-size/{version_id}
```

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "parameters": [
    {
      "level_id": "6eme",
      "level_name": "6ème",
      "min_class_size": 20,
      "target_class_size": 25,
      "max_class_size": 28
    }
  ]
}
```

#### Update Class Size Parameters
```http
PUT /configuration/class-size/{version_id}/{level_id}
Content-Type: application/json

{
  "min_class_size": 20,
  "target_class_size": 25,
  "max_class_size": 28
}
```

**Response** (200 OK): Returns updated parameters

### Subject Hours Matrix

#### Get Subject Hours
```http
GET /configuration/subject-hours/{version_id}
```

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "subject_hours": [
    {
      "subject_id": "math",
      "subject_name": "Mathématiques",
      "level_id": "6eme",
      "level_name": "6ème",
      "hours_per_week": 4.5
    }
  ]
}
```

---

## Planning Endpoints

### Enrollment Planning

#### Get Enrollment Plans
```http
GET /planning/enrollment/{version_id}
```

**Query Parameters**:
- `level_id` (optional): Filter by level
- `nationality` (optional): Filter by nationality (French, Saudi, Other)
- `period` (optional): Filter by period (P1, P2)

**Response** (200 OK):
```json
  [
	  {
	    "id": "enrollment-uuid",
	    "version_id": "version-uuid",
	    "level_id": "6eme",
	    "level_name": "6ème",
	    "nationality": "French",
    "student_count": 120,
    "period": "P2",
    "created_at": "2024-12-01T10:00:00Z",
    "updated_at": "2024-12-01T10:00:00Z"
  }
]
```

#### Create Enrollment Plan
```http
 POST /planning/enrollment
 Content-Type: application/json

 {
	  "version_id": "version-uuid",
	  "level_id": "6eme",
	  "nationality": "French",
	  "student_count": 120,
	  "period": "P2"
 }
```

**Response** (201 Created): Returns created enrollment plan

#### Update Enrollment Plan
```http
PUT /planning/enrollment/{plan_id}
Content-Type: application/json

{
  "student_count": 125
}
```

**Response** (200 OK): Returns updated enrollment plan

#### Delete Enrollment Plan
```http
DELETE /planning/enrollment/{plan_id}
```

**Response** (204 No Content)

### Class Structure

#### Get Class Structure
```http
GET /planning/classes/{version_id}
```

**Response** (200 OK):
```json
[
  {
    "level_id": "6eme",
    "level_name": "6ème",
    "enrollment": 120,
    "class_count": 5,
    "average_class_size": 24.0,
    "min_size": 20,
    "max_size": 28,
    "requires_atsem": false
  }
]
```

#### Calculate Class Structure from Enrollment
```http
POST /planning/classes/{version_id}/calculate
```

**Response** (200 OK):
```json
{
  "message": "Class structure calculated successfully",
  "classes_calculated": 18,
  "total_students": 1245
}
```

### DHG Workforce Planning

#### Get DHG Calculation
```http
GET /planning/dhg/{version_id}
```

**Query Parameters**:
- `cycle` (optional): Filter by cycle (primary, secondary)
- `subject_id` (optional): Filter by subject

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "secondary": {
    "subjects": [
      {
        "subject_id": "math",
        "subject_name": "Mathématiques",
        "total_hours": 68.0,
        "simple_fte": 3.78,
        "recommended_teachers": 4,
        "hsa_hours": 14.0,
        "teacher_breakdown": [
          {
            "teacher_type": "AEFE_DETACHED",
            "fte": 2,
            "cost_eur": 83726.0,
            "cost_sar": 351651.0
          },
          {
            "teacher_type": "LOCAL",
            "fte": 2,
            "cost_sar": 480000.0
          }
        ]
      }
    ],
    "totals": {
      "total_hours": 840.0,
      "total_fte": 46.67,
      "total_cost_sar": 15420000.0,
      "h_e_ratio": 1.40
    }
  }
}
```

#### Update Teacher Assignment
```http
PUT /planning/dhg/{version_id}/assignment
Content-Type: application/json

{
  "subject_id": "math",
  "level_id": "6eme",
  "teacher_type": "AEFE_DETACHED",
  "fte": 2
}
```

**Response** (200 OK): Returns updated DHG calculation

### Revenue Planning

#### Get Revenue Plans
```http
GET /planning/revenue/{version_id}
```

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "revenue_streams": [
    {
      "category": "TUITION",
      "account_code": "70110",
      "description": "Tuition T1",
      "period": "T1",
      "amount_sar": 15000000.0
    },
    {
      "category": "REGISTRATION",
      "account_code": "70210",
      "description": "Registration Fees",
      "period": "P1",
      "amount_sar": 500000.0
    }
  ],
  "totals": {
    "total_revenue": 45000000.0,
    "by_period": {
      "P1": 22500000.0,
      "P2": 22500000.0
    }
  }
}
```

### Cost Planning

#### Get Cost Plans
```http
GET /planning/costs/{version_id}
```

**Query Parameters**:
- `account_category` (optional): Filter by category (61, 62, 63, 64, 65, 66, 67)

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "cost_items": [
    {
      "account_code": "64110",
      "description": "Teaching Salaries",
      "amount_p1": 7500000.0,
      "amount_p2": 7500000.0,
      "amount_total": 15000000.0,
      "is_auto_calculated": true
    }
  ],
  "totals": {
    "total_costs": 38000000.0,
    "by_period": {
      "P1": 19000000.0,
      "P2": 19000000.0
    }
  }
}
```

#### Create Cost Item
```http
POST /planning/costs
Content-Type: application/json

{
  "version_id": "version-uuid",
  "account_code": "61110",
  "description": "Educational Supplies",
  "amount_p1": 150000.0,
  "amount_p2": 150000.0
}
```

**Response** (201 Created): Returns created cost item

---

## Consolidation Endpoints

### Budget Consolidation

#### Consolidate Budget
```http
POST /consolidation/budget/{version_id}/consolidate
```

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "consolidation_status": "SUCCESS",
  "summary": {
    "total_revenue": 45000000.0,
    "total_costs": 38000000.0,
    "ebitda": 7000000.0,
    "net_result": 7000000.0
  },
  "validation_errors": []
}
```

#### Get Consolidated Budget
```http
GET /consolidation/budget/{version_id}
```

**Response** (200 OK): Returns full consolidated budget with all line items

### Financial Statements

#### Get Income Statement
```http
GET /consolidation/statements/{version_id}/income-statement
```

**Query Parameters**:
- `format` (optional): `pcg` or `ifrs` (default: pcg)

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "format": "pcg",
  "revenue": [
    {
      "account_code": "70xxx",
      "category": "Operating Revenue",
      "amount": 45000000.0,
      "details": [...]
    }
  ],
  "expenses": [
    {
      "account_code": "64xxx",
      "category": "Personnel Costs",
      "amount": 25000000.0,
      "details": [...]
    }
  ],
  "net_result": 7000000.0
}
```

#### Get Balance Sheet
```http
GET /consolidation/statements/{version_id}/balance-sheet
```

**Response** (200 OK):
```json
{
  "assets": {
    "fixed_assets": 5000000.0,
    "current_assets": 3000000.0,
    "total_assets": 8000000.0
  },
  "liabilities_equity": {
    "equity": 5000000.0,
    "long_term_liabilities": 2000000.0,
    "current_liabilities": 1000000.0,
    "total_liabilities_equity": 8000000.0
  }
}
```

---

## Analysis Endpoints

### Statistical Analysis & KPIs

#### Get KPIs
```http
GET /analysis/kpis/{version_id}
```

**Response** (200 OK):
```json
{
  "enrollment_kpis": {
    "total_enrollment": 1500,
    "growth_rate": 5.5,
    "capacity_utilization": 80.0,
    "average_class_size": 24.5,
    "nationality_mix": {
      "French": 60.0,
      "Saudi": 30.0,
      "Other": 10.0
    }
  },
  "financial_kpis": {
    "revenue_per_student": 30000.0,
    "cost_per_student": 25333.0,
    "operating_margin": 15.6,
    "ebitda_margin": 15.6,
    "net_profit_margin": 15.6
  },
  "workforce_kpis": {
    "student_teacher_ratio": 15.5,
    "h_e_ratio": 1.40,
    "aefe_percentage": 45.0,
    "average_teacher_cost_sar": 330000.0,
    "hsa_percentage": 8.5
  }
}
```

### Budget vs Actual

#### Import Actuals
```http
POST /analysis/actuals/import
Content-Type: application/json

{
  "version_id": "version-uuid",
  "period": "T1",
  "source": "ODOO",
  "data": [...]
}
```

**Response** (201 Created):
```json
{
  "import_id": "import-uuid",
  "records_imported": 150,
  "status": "SUCCESS"
}
```

#### Get Budget vs Actual Variance
```http
GET /analysis/budget-vs-actual/{version_id}
```

**Query Parameters**:
- `period` (optional): T1, T2, T3
- `account_category` (optional): Filter by account category

**Response** (200 OK):
```json
{
  "version_id": "version-uuid",
  "period": "T1",
  "variances": [
    {
      "account_code": "70110",
      "description": "Tuition T1",
      "budget": 15000000.0,
      "actual": 14250000.0,
      "variance": -750000.0,
      "variance_percent": -5.0,
      "favorable": false
    }
  ],
  "summary": {
    "total_budget": 45000000.0,
    "total_actual": 43500000.0,
    "total_variance": -1500000.0,
    "variance_percent": -3.3
  }
}
```

---

## Integration Endpoints

### Odoo Integration

#### Test Odoo Connection
```http
POST /integrations/odoo/test-connection
Content-Type: application/json

{
  "odoo_url": "https://company.odoo.com",
  "database": "company_db",
  "api_key": "your-api-key"
}
```

**Response** (200 OK):
```json
{
  "status": "SUCCESS",
  "message": "Connection successful",
  "version": "Odoo 17.0"
}
```

#### Import Actuals from Odoo
```http
POST /integrations/odoo/import-actuals
Content-Type: application/json

{
  "version_id": "version-uuid",
  "period": "T1",
  "fiscal_year": 2025
}
```

**Response** (200 OK):
```json
{
  "import_id": "import-uuid",
  "records_imported": 150,
  "status": "SUCCESS",
  "summary": {
    "revenue_records": 75,
    "expense_records": 75
  }
}
```

### Skolengo Integration

#### Import Enrollment from Skolengo
```http
POST /integrations/skolengo/import-enrollment
Content-Type: application/json

{
  "version_id": "version-uuid",
  "academic_year": "2024-2025"
}
```

**Response** (200 OK):
```json
{
  "import_id": "import-uuid",
  "students_imported": 1450,
  "status": "SUCCESS"
}
```

### AEFE Integration

#### Import Position File
```http
POST /integrations/aefe/import-positions
Content-Type: multipart/form-data

file: [aefe_positions.xlsx]
version_id: version-uuid
```

**Response** (200 OK):
```json
{
  "import_id": "import-uuid",
  "positions_imported": 45,
  "funded_positions": 20,
  "detached_positions": 25,
  "total_prrd_cost_eur": 1046575.0,
  "total_prrd_cost_sar": 4395615.0
}
```

---

## Error Responses

### Standard Error Format

All errors return JSON in this format:

```json
{
  "detail": "Error message",
  "error_code": "ERROR_CODE",
  "timestamp": "2024-12-02T10:00:00Z"
}
```

### HTTP Status Codes

- **200 OK**: Success
- **201 Created**: Resource created successfully
- **204 No Content**: Success with no response body (e.g., DELETE)
- **400 Bad Request**: Invalid input or validation error
- **401 Unauthorized**: Authentication required or invalid token
- **403 Forbidden**: Authenticated but not authorized for this action
- **404 Not Found**: Resource not found
- **409 Conflict**: Resource conflict (e.g., duplicate)
- **422 Unprocessable Entity**: Validation error with details
- **500 Internal Server Error**: Server error

### Example Error Responses

**Validation Error** (422):
```json
{
  "detail": [
    {
      "loc": ["body", "student_count"],
      "msg": "ensure this value is greater than 0",
      "type": "value_error.number.not_gt"
    }
  ]
}
```

**Authentication Error** (401):
```json
{
  "detail": "Invalid authentication credentials",
  "error_code": "INVALID_TOKEN"
}
```

**Not Found** (404):
```json
{
  "detail": "Budget version not found",
  "error_code": "RESOURCE_NOT_FOUND"
}
```

---

## Rate Limiting

API endpoints are rate-limited to:
- **Public endpoints**: 60 requests per minute per IP
- **Authenticated endpoints**: 300 requests per minute per user

Rate limit headers are included in responses:
```
X-RateLimit-Limit: 300
X-RateLimit-Remaining: 295
X-RateLimit-Reset: 1638360000
```

---

## Pagination

List endpoints support pagination via query parameters:

```http
GET /planning/enrollment/{version_id}?page=1&page_size=50
```

**Parameters**:
- `page` (default: 1): Page number
- `page_size` (default: 20, max: 100): Items per page

**Response includes pagination metadata**:
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total_items": 150,
    "total_pages": 8
  }
}
```

---

## WebSocket Events (Realtime)

For real-time updates, subscribe to Supabase Realtime channels:

```javascript
const channel = supabase.channel('budget-updates')
  .on('postgres_changes', {
    event: '*',
    schema: 'public',
    table: 'settings_versions',
    filter: `id=eq.${versionId}`
  }, (payload) => {
    console.log('Budget updated:', payload);
  })
  .subscribe();
```

---

**End of API Documentation**
