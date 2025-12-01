# Quick Start Guide - Configuration API

## Installation

```bash
cd backend
pip install -e .
```

## Environment Setup

Create `.env` file in backend directory:

```env
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/efir_budget
SUPABASE_JWT_SECRET=your-supabase-jwt-secret-from-dashboard
JWT_SECRET_KEY=generate-a-secure-random-key
SQL_ECHO=False
```

## Start Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at:
- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Quick Test (No Auth Required)

```bash
# Health check
curl http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/
```

## Testing with Authentication

### Get JWT Token from Supabase

1. Sign in to your Supabase dashboard
2. Go to Authentication → Users
3. Copy the JWT access token for a test user

### Export Token

```bash
export JWT_TOKEN="your-jwt-token-here"
```

### Test Configuration Endpoints

```bash
# Get all system configurations
curl -X GET "http://localhost:8000/api/v1/config/system" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get academic cycles
curl -X GET "http://localhost:8000/api/v1/academic-cycles" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Get academic levels
curl -X GET "http://localhost:8000/api/v1/academic-levels" \
  -H "Authorization: Bearer $JWT_TOKEN"

# Create budget version
curl -X POST "http://localhost:8000/api/v1/budget-versions" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Budget 2025-2026",
    "fiscal_year": 2026,
    "academic_year": "2025-2026",
    "notes": "Test budget"
  }'

# Get all budget versions
curl -X GET "http://localhost:8000/api/v1/budget-versions" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Complete Endpoint List

### System Configuration
- `GET /api/v1/config/system` - List configurations
- `GET /api/v1/config/system/{key}` - Get by key
- `PUT /api/v1/config/system/{key}` - Create/update

### Budget Versions
- `GET /api/v1/budget-versions` - List versions
- `GET /api/v1/budget-versions/{id}` - Get by ID
- `POST /api/v1/budget-versions` - Create
- `PUT /api/v1/budget-versions/{id}` - Update
- `PUT /api/v1/budget-versions/{id}/submit` - Submit
- `PUT /api/v1/budget-versions/{id}/approve` - Approve (manager/admin)
- `PUT /api/v1/budget-versions/{id}/supersede` - Supersede

### Reference Data
- `GET /api/v1/academic-cycles` - List cycles
- `GET /api/v1/academic-levels` - List levels
- `GET /api/v1/subjects` - List subjects
- `GET /api/v1/teacher-categories` - List categories
- `GET /api/v1/fee-categories` - List fee categories
- `GET /api/v1/nationality-types` - List nationality types

### Parameters (require version_id)
- `GET /api/v1/class-size-params?version_id={id}` - Get class size params
- `PUT /api/v1/class-size-params` - Create/update
- `GET /api/v1/subject-hours?version_id={id}` - Get subject hours
- `PUT /api/v1/subject-hours` - Create/update
- `GET /api/v1/teacher-costs?version_id={id}` - Get teacher costs
- `PUT /api/v1/teacher-costs` - Create/update
- `GET /api/v1/fee-structure?version_id={id}` - Get fee structure
- `PUT /api/v1/fee-structure` - Create/update

## User Roles

| Role | Access Level |
|------|-------------|
| **admin** | Full access to all endpoints |
| **manager** | Can approve budgets, manage configurations |
| **planner** | Can create/edit budgets (default) |
| **viewer** | Read-only access |

## Common Issues

### 401 Unauthorized
- Check JWT token is valid
- Ensure Authorization header format: `Bearer YOUR_TOKEN`
- Verify token hasn't expired

### 403 Forbidden
- Check user has required role for endpoint
- Manager/admin required for approval endpoints

### 409 Conflict
- Cannot create multiple working versions for same fiscal year
- Submit or supersede existing working version first

### 422 Unprocessable Entity
- Business rule violation
- Check version status before submitting/approving

## Next Steps

1. Install dependencies: `pip install -e .`
2. Set up environment variables in `.env`
3. Run migrations: `alembic upgrade head`
4. Start server: `uvicorn app.main:app --reload`
5. Test endpoints using Swagger UI: http://localhost:8000/docs
6. Create your first budget version
7. Configure class sizes, subject hours, teacher costs, and fees

---

**For detailed documentation, see**: `IMPLEMENTATION_SUMMARY.md`
