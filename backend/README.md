# EFIR Budget Planning Backend

FastAPI 0.123 + Python 3.14.0 backend for the EFIR Budget Planning Application, implementing the DHG (Dotation Horaire Globale) workforce planning methodology.

---

## 🤖 For AI Agents

**⚠️ CRITICAL: If you are an AI agent working on backend code, read this section FIRST.**

### Agent System (9 Agents)

This codebase uses a 9-agent orchestration system. For backend work:

| Agent | Use For | Key Rules |
|-------|---------|-----------|
| `product-architect-agent` | Business rules, formulas (SOURCE OF TRUTH) | Consult before implementing any calculation |
| `Plan` | Architecture decisions, implementation planning | Use for schema design, major features |
| `Explore` | Fast codebase exploration | Find files, patterns, existing implementations |
| `performance-agent` | Profiling, optimization | Query tuning, caching strategies |
| `qa-validation-agent` | Tests (unit, integration) | 80%+ coverage requirement |
| `general-purpose` | Complex multi-step research | Code search, dependency analysis |

### Agent Boundary Rules

**CRITICAL ENFORCEMENT:**

1. **Calculation Engines** (`app/engine/`):
   - Implement pure functions (no side effects, no database access)
   - Use Pydantic models for input/output validation
   - Follow formulas exactly as specified by `product-architect-agent`
   - Be fully testable (no API calls, no external dependencies)

2. **API Endpoints** (`app/api/v1/`):
   - Call engine functions via service layer for all calculations
   - Use FastAPI dependency injection for services
   - Validate requests with Pydantic schemas
   - Return proper HTTP status codes and error messages

3. **Database Changes**:
   - Create Alembic migrations for all schema changes
   - Use `Plan` agent for schema design decisions
   - Follow naming conventions in `AGENTS.md`

### Backend Code Organization

**Calculation Engines** (`backend/app/engine/`):

- **Pattern**: Pure functions with Pydantic input/output models
- **Example**: `app/engine/dhg/calculate_dhg_hours()` - no database, no API, pure calculation

**API Endpoints** (`backend/app/api/v1/`):

- **Pattern**: FastAPI routes that call engine functions via services
- **Example**: `app/api/v1/calculations/dhg.py` - calls engine via service layer

**Database Models** (`backend/app/models/`):

- **Pattern**: SQLAlchemy ORM models with proper relationships
- **Migrations**: `backend/alembic/versions/` (25+ migrations as of December 2025)

**Services** (`backend/app/services/`):

- **Pattern**: Business logic layer between API and engines
- **Example**: `EnrollmentService.calculate()` orchestrates engine function calls

### Agent Workflow Examples

**Example 1: Implementing DHG Calculation**
```
1. product-architect-agent → Provides DHG formula and business rules
2. Implement pure calculation function in engine/
3. Create FastAPI endpoint that calls engine via service
4. qa-validation-agent → Writes tests for engine and API
```

**Example 2: Adding Database Table**
```
1. Plan agent → Design schema, approve architecture
2. Create SQLAlchemy model and Alembic migration
3. Create CRUD endpoints (if needed)
4. Add RLS policies in migration
```

**See [Agent Orchestration Guide](../.claude/AGENT_ORCHESTRATION.md) for complete workflow patterns.**

### Backend Development Standards

All backend agents MUST follow:
- **Type Safety**: Python 3.14.0 type hints, Pydantic validation
- **Test Coverage**: 80%+ minimum (enforced by pytest.ini)
- **Code Quality**: Ruff linting, mypy type checking
- **Documentation**: Docstrings for all functions, module .md files

**See [CLAUDE.md](../CLAUDE.md) "EFIR Development Standards System" section for complete requirements.**

---

## Technology Stack

- **Framework**: FastAPI 0.123.4 (async, high-performance)
- **Language**: Python 3.14.0 (Free-threaded Python, Template String Literals)
- **Validation**: Pydantic 2.12.5
- **Server**: Uvicorn 0.38.0 (ASGI server)
- **ORM**: SQLAlchemy 2.0.44 (async with `asyncpg`)
- **Migrations**: Alembic 1.17.2
- **Database**: PostgreSQL 17.x (via Supabase)
- **Cache**: Redis 8.4+ (TTL-based caching with `cashews`, graceful degradation)
- **Security**: Supabase Auth + Row Level Security (RLS)

## Project Structure

```
backend/
├── app/
│   ├── api/v1/           # FastAPI routes
│   │   ├── calculations.py   # DHG, KPI, Revenue calculation endpoints
│   │   ├── configuration.py  # System config endpoints
│   │   ├── planning.py       # Enrollment/planning endpoints
│   │   └── costs.py          # Cost planning endpoints
│   ├── core/             # Security, pagination utilities
│   ├── dependencies/     # Auth dependencies
│   ├── engine/           # Pure calculation engines
│   │   ├── dhg/          # DHG hours, FTE, teacher requirements
│   │   ├── enrollment/   # Enrollment projections
│   │   ├── kpi/          # KPI calculations
│   │   └── revenue/      # Revenue planning
│   ├── middleware/       # Auth, RBAC middleware
│   ├── models/           # SQLAlchemy models (18 modules)
│   │   ├── configuration.py  # Modules 1-6
│   │   ├── planning.py       # Modules 7-12
│   │   ├── consolidation.py  # Modules 13-14
│   │   ├── analysis.py       # Modules 15-17
│   │   └── strategic.py      # Module 18
│   ├── schemas/          # Pydantic schemas for API
│   ├── services/         # Business logic services
│   └── validators/       # Business rule validation
├── alembic/              # Database migrations
│   └── versions/         # 7 migration files
└── tests/                # Pytest tests
```

## Setup

### Prerequisites

- Python 3.11+ (3.12 recommended)
- PostgreSQL 17.x or Supabase account
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

### Installation

```bash
# With uv (recommended - 10-100x faster)
uv sync --all-extras                  # Creates .venv and installs all deps

# With pip (alternative)
python3 -m venv .venv
source .venv/bin/activate             # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your database credentials
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db?sslmode=require
DIRECT_URL=postgresql://user:pass@host:5432/db?sslmode=require

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret-from-supabase-dashboard

# Optional
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]
```

#### Supabase JWT Authentication

**⚠️ Required for API Authentication**

The `SUPABASE_JWT_SECRET` is required for the backend to verify Supabase JWT tokens from authenticated users. Without it, all API calls will return `401 Unauthorized` even after successful login.

**How to get your JWT Secret:**
1. Go to Supabase Dashboard → Your Project → Settings → API
2. Scroll to **JWT Settings** section
3. Copy the **JWT Secret** (not the anon key or service role key)
4. Add to `backend/.env.local` as: `SUPABASE_JWT_SECRET=your-secret-here`

**See [SETUP_JWT_AUTH.md](./SETUP_JWT_AUTH.md) for detailed setup instructions and troubleshooting.**

#### Redis Caching Configuration

**Redis 8.4+ is required for caching functionality** (optional but recommended for production).

The backend uses Redis for:
- **TTL-based caching** of expensive calculations (DHG, enrollment projections, KPIs)
- **Cascading cache invalidation** following the calculation dependency graph
- **Rate limiting** for API endpoints (when enabled)

**Installation (Development)**
```bash
# macOS (Homebrew)
brew install redis
brew services start redis

# Verify Redis is running
redis-cli ping
# Expected output: PONG
```

**Configuration Variables** (see [.env.example](.env.example) for details):
- `REDIS_ENABLED` - Enable/disable caching (`"true"` or `"false"`)
- `REDIS_REQUIRED` - Fail startup if Redis unavailable (`"false"` for graceful degradation)
- `REDIS_URL` - Connection string (default: `redis://localhost:6379/0`)
- `REDIS_CONNECT_TIMEOUT` - Connection timeout in seconds (default: `5`)
- `REDIS_SOCKET_TIMEOUT` - Operation timeout in seconds (default: `5`)
- `REDIS_MAX_RETRIES` - Maximum retry attempts (default: `3`)

**Graceful Degradation**
```bash
# Option 1: Disable Redis entirely (testing/development)
REDIS_ENABLED="false" uvicorn app.main:app --reload

# Option 2: Enable with graceful fallback (recommended for development)
REDIS_ENABLED="true" REDIS_REQUIRED="false" uvicorn app.main:app --reload
# Server starts even if Redis is unavailable - caching gracefully disabled

# Option 3: Fail fast if Redis unavailable (production mode)
REDIS_ENABLED="true" REDIS_REQUIRED="true" uvicorn app.main:app
# Server fails to start with clear error message if Redis down
```

**Health Check**
```bash
curl http://localhost:8000/health/ready | jq '.checks.cache'
# Returns cache initialization status and configuration
```

**Cache Architecture**
- **Dependency tracking**: Enrollment → Class Structure → DHG → Personnel Costs
- **Automatic invalidation**: Changing enrollment data clears all dependent caches
- **TTL defaults**: Configuration (1 hour), Calculations (5 minutes), KPIs (1 minute)

**See [app/core/cache.py](app/core/cache.py) for implementation details.**

## Running the Application

```bash
# Development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

API documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## API Endpoints

### Health
- `GET /health/live` - Liveness probe
- `GET /health/ready` - Readiness check (with DB)

### Calculations
- `POST /api/v1/calculations/enrollment` - Enrollment projections
- `POST /api/v1/calculations/dhg` - DHG hours and FTE
- `POST /api/v1/calculations/kpi` - KPI calculations
- `POST /api/v1/calculations/revenue` - Revenue planning

### Configuration (CRUD)
- `GET/POST /api/v1/config/system` - System configuration
- `GET/POST /api/v1/config/budget-versions` - Budget version management

## Database Migrations

```bash
# View migration history
alembic history --verbose

# Apply all migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Rollback one migration
alembic downgrade -1
```

### Current Migrations (10)

1. `initial_configuration_layer` - Modules 1-6 tables
2. `planning_layer` - Modules 7-12 tables
3. `consolidation_layer` - Modules 13-14 tables
4. `fix_critical_issues` - Constraint fixes
5. `analysis_layer` - Modules 15-17 tables
6. `class_structure_validation` - Validation triggers
7. `strategic_layer` - Module 18 tables
8. `performance_indexes` - Query optimization indexes
9. `materialized_views_kpi` - KPI dashboard caching
10. `planning_cells_writeback` - Real-time data entry support

## Testing

```bash
# Run all tests
PYTHONPATH=. pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/engine/test_dhg.py -v

# Run only unit tests
pytest tests/ -m unit -v
```

### Test Coverage Target: 80%+

## Code Quality

```bash
# Linting (ruff)
ruff check .
ruff check . --fix  # Auto-fix

# Type checking (mypy)
mypy app

# Formatting
ruff format .
```

### Pre-configured Rules

- **Ruff**: E, F, B, I, UP, RUF, ASYNC
- **mypy**: Strict optional, check untyped defs
- **Ignored**: FastAPI Depends patterns, SQLAlchemy dynamic types

## Calculation Engines

### DHG (Dotation Horaire Globale)

The core workforce planning engine:

```python
from app.engine.dhg import calculate_dhg_hours, calculate_fte_from_hours

# Calculate total DHG hours per level
result = calculate_dhg_hours(dhg_input)
# result.total_hours = Σ(classes x hours_per_subject)

# Calculate FTE requirements
fte_result = calculate_fte_from_hours(result)
# fte_result.simple_fte = total_hours / 18  (secondary standard)
# fte_result.rounded_fte = ceil(simple_fte)
```

### Revenue

```python
from app.engine.revenue import calculate_tuition_revenue

# Calculate with sibling discounts
result = calculate_tuition_revenue(tuition_input)
# Applies 25% discount for 3rd+ child
```

## Module Architecture

| Layer | Modules | Description |
|-------|---------|-------------|
| Configuration | 1-6 | Master data, parameters |
| Planning | 7-12 | Enrollment, DHG, Revenue, Costs |
| Consolidation | 13-14 | Budget consolidation, statements |
| Analysis | 15-17 | KPIs, dashboards, actuals |
| Strategic | 18 | 5-year planning |

## License

Internal use only - EFIR School Budget Planning Application
