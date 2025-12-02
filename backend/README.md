# EFIR Budget Planning Backend

FastAPI 0.123 + Python 3.12 backend for the EFIR Budget Planning Application, implementing the DHG (Dotation Horaire Globale) workforce planning methodology.

## Technology Stack

- **Framework**: FastAPI 0.123.0 (async, high-performance)
- **Language**: Python 3.12+ (required for union types)
- **Validation**: Pydantic 2.12.0
- **ORM**: SQLAlchemy 2.0.44 (async with `asyncpg`)
- **Migrations**: Alembic
- **Database**: PostgreSQL 17.x (via Supabase)
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

- Python 3.12+ (required for type syntax)
- PostgreSQL 17.x or Supabase account
- Poetry or pip

### Installation

```bash
# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
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
JWT_SECRET=your-jwt-secret

# Optional
DEBUG=true
CORS_ORIGINS=["http://localhost:5173"]
```

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

### Current Migrations (7)

1. `initial_configuration_layer` - Modules 1-6 tables
2. `planning_layer` - Modules 7-12 tables
3. `consolidation_layer` - Modules 13-14 tables
4. `fix_critical_issues` - Constraint fixes
5. `analysis_layer` - Modules 15-17 tables
6. `class_structure_validation` - Validation triggers
7. `strategic_layer` - Module 18 tables

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
