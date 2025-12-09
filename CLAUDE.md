# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference Commands

### Monorepo (from project root)
```bash
pnpm dev        # Run both frontend + backend concurrently
pnpm build      # Build frontend
pnpm lint       # Lint both frontend + backend
pnpm typecheck  # Type check both frontend + backend
pnpm test       # Test both frontend + backend
```

### Frontend (from `frontend/`)
```bash
pnpm install              # Install dependencies
pnpm dev                  # Start dev server (http://localhost:5173)
pnpm build                # Production build
pnpm build:analyze        # Bundle size analysis
pnpm build:stats          # Build + show JS bundle sizes
pnpm test                 # Run Vitest (watch mode)
pnpm test -- --run        # Run tests once (CI mode)
pnpm test:ui              # Vitest UI (interactive test runner)
pnpm test:all             # Run Vitest + Playwright together
pnpm test:e2e             # Playwright E2E tests
pnpm test:e2e:ui          # Playwright UI (visual debugging)
pnpm test:e2e:debug       # Playwright debugger
pnpm test:e2e:report      # Show Playwright HTML report
pnpm lint:fix             # ESLint with auto-fix
pnpm format               # Prettier formatting
pnpm typecheck            # TypeScript check (tsc --noEmit)
pnpm generate:types       # Generate TS types from OpenAPI (backend must be running)
```

### Backend (from `backend/`)

**Prerequisites**: Python 3.11+ (3.14 recommended for latest features)

```bash
# Setup
python3 -m venv .venv                        # Create virtual environment
source .venv/bin/activate                    # Activate venv (required first)
pip install -e .[dev]                        # Install with dev dependencies (ruff, mypy, pytest)

# Development
uvicorn app.main:app --reload                # Start API (http://localhost:8000)
alembic upgrade head                         # Apply migrations
alembic revision --autogenerate -m "desc"    # Create migration

# Testing
.venv/bin/pytest tests/ -v --tb=short        # Run tests verbose
.venv/bin/pytest tests/engine/ -v            # Test specific directory
.venv/bin/pytest -k test_dhg                 # Tests matching pattern
.venv/bin/pytest tests/ --cov=app --cov-report=term-missing -v  # With coverage

# Code Quality
.venv/bin/ruff check . --fix                 # Lint with auto-fix
.venv/bin/mypy app                           # Type check
```

### Running Single Tests
```bash
# Frontend - single test file
pnpm test -- tests/components/ui/Button.test.tsx --run

# Backend - single test file or function
.venv/bin/pytest tests/engine/test_dhg.py -v
.venv/bin/pytest tests/api/test_planning_api.py::test_specific_function -v
```

---

## Environment Setup

### First-Time Setup

1. **Copy environment templates** (both frontend and backend):
   ```bash
   cp .env.example .env.local
   cp frontend/.env.example frontend/.env.local
   cp backend/.env.example backend/.env.local
   ```

2. **Configure Supabase** in `.env.local` files:
   - `VITE_SUPABASE_URL` - Your Supabase project URL
   - `VITE_SUPABASE_ANON_KEY` - Anon key (safe for frontend)
   - `DATABASE_URL` - PostgreSQL connection via pgBouncer (for app)
   - `DIRECT_URL` - Direct PostgreSQL connection (for migrations)

3. **Critical**: Use `DIRECT_URL` for Alembic migrations (bypasses connection pooler), `DATABASE_URL` for application runtime.

### Pre-commit Hooks

Pre-commit hooks (Husky + lint-staged) are already configured and will auto-run on commit:
- ESLint + Prettier (frontend)
- Ruff + mypy (backend)
- TypeScript type checking
- No additional setup required

---

## Architecture Overview

### Module-Based Architecture (18 Modules, 5 Layers)

```
Configuration Layer (1-6)     Planning Layer (7-12)        Consolidation (13-14)
├─ System Config              ├─ Enrollment Planning       ├─ Budget Consolidation
├─ Class Size Parameters      ├─ Class Structure           └─ Financial Statements
├─ Subject Hours              ├─ DHG Workforce Planning
├─ Teacher Costs              ├─ Revenue Planning          Analysis Layer (15-17)
├─ Fee Structure              ├─ Cost Planning             ├─ KPIs
└─ Timetable Constraints      └─ CapEx Planning            ├─ Dashboards
                                                           └─ Budget vs Actual
Strategic Layer (18)
└─ 5-Year Planning

Workforce Module (integrated across Planning):
├─ Employee Management (salaries, contracts)
├─ DHG Requirements & Gap Analysis (TRMD)
├─ AEFE Positions Management
├─ GOSI/EOS Cost Calculations
└─ HSA (Overtime) Configuration
```

### Critical Data Flow
```
Enrollment → Class Structure → DHG Hours → Teacher FTE → Personnel Costs
                                                              ↓
Revenue ←──────────────────────────────────────── Budget Consolidation
                                                              ↓
                                                    Financial Statements
```
**Key Principle**: Enrollment is the primary driver. Changes cascade through all dependent calculations.

### Backend Structure
```
backend/app/
├── api/v1/          # FastAPI routes (configuration, planning, consolidation, analysis, etc.)
├── engine/          # Pure calculation engines:
│   ├── dhg/             # DHG hours & FTE calculations
│   ├── enrollment/      # Enrollment projections
│   ├── eos/             # End of Service calculations
│   ├── financial_statements/  # PCG/IFRS statements
│   ├── gosi/            # GOSI (social insurance) calculations
│   ├── kpi/             # Key performance indicators
│   └── revenue/         # Revenue projections
├── models/          # SQLAlchemy ORM (configuration, planning, consolidation, analysis, strategic)
├── schemas/         # Pydantic request/response models
├── services/        # Business logic layer
└── core/            # Infrastructure (logging, pagination, security, cache)
```

### Frontend Structure
```
frontend/src/
├── routes/                  # TanStack Router pages
│   ├── _authenticated/      # Auth-protected routes wrapper
│   │   ├── admin/               # Historical data import
│   │   ├── analysis/            # kpis, dashboards, variance
│   │   ├── configuration/       # class-sizes, fees, subject-hours, etc.
│   │   ├── consolidation/       # budget, checklist, statements
│   │   ├── enrollment/          # class-structure, planning
│   │   ├── finance/             # capex, costs, revenue, statements
│   │   ├── planning/            # dhg, guide, classes, costs, revenue
│   │   ├── strategic/           # 5-year planning
│   │   └── workforce/           # employees, salaries, dhg/, settings/
│   ├── _authenticated.command-center.tsx  # Ctrl+K command palette
│   └── _authenticated.tsx   # Auth layout wrapper
├── components/              # Reusable components (ui/, charts/, layout/, grid/)
├── contexts/                # React contexts (AuthContext, BudgetVersionProvider)
├── hooks/                   # Custom hooks (api/, useExcelKeyboard, useImpactCalculation)
├── services/                # API client functions
└── types/                   # TypeScript types and API contracts
```

---

## Agent System (14 Specialized Agents)

This codebase uses a 14-agent orchestration system. See `.claude/AGENT_ORCHESTRATION.md` for full details.

### Key Agent Boundaries

| Task Type | Agent | Cannot Do |
|-----------|-------|-----------|
| Business rules, formulas | `product-architect-agent` | Write code |
| Architecture, API contracts | `system-architect-agent` | Business logic |
| PostgreSQL, migrations, RLS | `database-supabase-agent` | Calculations, APIs |
| Calculation engines | `backend-engine-agent` | Database, APIs, UI |
| FastAPI endpoints | `backend-api-specialist` | Calculation logic |
| React components | `frontend-ui-agent` | Backend, database |
| Tests only | `qa-validation-agent` | Production code |

**Critical Rules**:
1. Consult `product-architect-agent` for business rules (SOURCE OF TRUTH)
2. Never cross agent boundaries
3. Route multi-domain tasks through `efir-master-agent`

---

## Domain-Specific Knowledge

### DHG (Dotation Horaire Globale) - Core Calculation

The French education system's workforce planning methodology:

```
Total Subject Hours = Σ(Number of Classes × Hours per Subject per Level)
Teacher FTE Required = Total Subject Hours ÷ Standard Hours (18h/week secondary, 24h/week primary)
```

**Gap Analysis (TRMD)**:
- Besoins (Needs): Hours required from DHG
- Available: AEFE positions + Local staff
- Deficit: Filled by recruitment or HSA (overtime, max 2-4 hours/teacher)

### French Education System Levels

| Cycle | Levels | Notes |
|-------|--------|-------|
| Maternelle (Preschool) | PS, MS, GS | Requires ATSEM (1 per class) |
| Élémentaire (Elementary) | CP, CE1, CE2, CM1, CM2 | 24h/week teaching |
| Collège (Middle School) | 6ème, 5ème, 4ème, 3ème | 18h/week teaching |
| Lycée (High School) | 2nde, 1ère, Terminale | 18h/week teaching |

### Staff Categories

- **AEFE Detached**: French nationals, school pays PRRD (~41,863 EUR/teacher)
- **AEFE Funded**: Fully funded by AEFE (no school cost)
- **Local Teachers**: Recruited locally, paid in SAR

### Key Acronyms

**French Education System:**
- **DHG**: Dotation Horaire Globale (Global Hours Allocation)
- **TRMD**: Tableau de Répartition des Moyens par Discipline (Gap Analysis)
- **HSA**: Heures Supplémentaires Annuelles (Annual Overtime)
- **PRRD**: Participation à la Rémunération des Résidents Détachés
- **H/E**: Heures/Élève (Hours per Student ratio)
- **E/D**: Élèves/Division (Students per Class)

**Saudi-Specific:**
- **GOSI**: General Organization for Social Insurance (employer 12% + employee 10%)
- **EOS**: End of Service (gratuity calculation per Saudi Labor Law)

### Financial Rules

- **Currency**: SAR (Saudi Riyal), with EUR for AEFE costs
- **Accounting**: French PCG (Plan Comptable Général) + IFRS mapping
- **Revenue Recognition**: Trimester-based (T1: 40%, T2: 30%, T3: 30%)
- **Account Codes**: 60xxx-68xxx (Expenses), 70xxx-77xxx (Revenue)
- **Sibling Discount**: 25% on tuition for 3rd+ child (not on DAI/registration)

---

## Development Standards (4 Non-Negotiables)

### 1. Complete Implementation
- No TODO/FIXME comments in production code
- All edge cases handled
- No placeholders

### 2. Type Safety
- TypeScript strict mode (no `any` types)
- Python type hints on all functions
- Pydantic models for all API contracts

### 3. Testing (80%+ Coverage)
- Backend: `pytest --cov=app --cov-fail-under=80`
- Frontend: `vitest --coverage`
- E2E: Playwright for critical flows

### 4. Quality Gates
All must pass before commit:
- `pnpm lint && pnpm typecheck` (frontend)
- `.venv/bin/ruff check . && .venv/bin/mypy app` (backend)

---

## Database Migrations

Linear migration chain in `backend/alembic/versions/` (15 migrations):
```
001_initial_configuration → 002_planning_layer → 003_consolidation_layer →
004_fix_critical_issues → 005_analysis_layer → 006_class_structure_validation →
007_strategic_layer → 008_performance_indexes → 009_materialized_views_kpi →
010_planning_cells_writeback → 011_audit_columns_nationality →
012_seed_subjects → 013_historical_comparison → 014_workforce_personnel →
015_seed_reference_data_distributions
```

---

## Calculation Engine Pattern

All engines in `backend/app/engine/` follow this pattern:

```python
from pydantic import BaseModel

class DHGInput(BaseModel):
    class_structure: dict[str, int]
    subject_hours: dict[str, float]

class DHGOutput(BaseModel):
    total_fte: float
    gap_analysis: dict[str, float]

def calculate_dhg(inputs: DHGInput) -> DHGOutput:
    """Pure function - no side effects, fully testable"""
    # Implementation
    return DHGOutput(...)
```

**Key Principles**:
- Pure functions (no database access)
- Pydantic for input validation
- Business logic exactly matches `product-architect-agent` specifications

---

## Key Documentation

| Document | Purpose |
|----------|---------|
| `docs/MODULES/MODULE_08_*.md` | DHG workforce planning specification |
| `docs/MODULES/MODULE_07_*.md` | Enrollment planning rules |
| `docs/MODULES/MODULE_14_*.md` | Financial statements (PCG/IFRS) |
| `.claude/AGENT_ORCHESTRATION.md` | Complete agent system guide |
| `backend/README.md` | Backend setup and API documentation |
| `frontend/README.md` | Frontend architecture and patterns |
| `foundation/EFIR_Module_Technical_Specification.md` | Complete 18-module specification |
| `docs/developer-guides/DEVELOPER_GUIDE.md` | Developer setup and guidelines |
| `docs/user-guides/USER_GUIDE.md` | End-user documentation |
| `docs/DOCUMENTATION_GUIDE.md` | Documentation standards and governance |
| `docs/AGENT_DOCUMENTATION_STANDARDS.md` | Agent documentation rules |

---

## Documentation System

### Overview

All 146 documentation files are organized in a clean, discoverable structure with clear governance standards.

**Master Navigation**: See [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) for complete documentation navigation.

### Directory Structure

```
/
├── foundation/              # Core specifications (PRD, TSD, requirements)
├── docs/
│   ├── MODULES/             # 18 module specifications (SOURCE OF TRUTH for business rules)
│   ├── user-guides/         # User documentation
│   ├── developer-guides/    # Developer documentation (API, integration, E2E testing)
│   ├── status/              # Living status docs (updated frequently)
│   ├── testing/             # Test coverage strategy and E2E guides
│   ├── agent-work/          # Recent agent reports (<30 days)
│   ├── technical-decisions/ # Architecture Decision Records (ADRs)
│   ├── roadmaps/            # Future planning documents
│   ├── database/            # Database schema and setup
│   ├── archive/             # Historical documents (phases, implementations, status)
│   └── templates/           # Document templates for agents
├── backend/docs/            # Backend-specific technical docs
└── frontend/                # Frontend-specific docs (bundle analysis, etc.)
```

### Where to Find Documentation

**For Business Rules & Formulas**:
- [docs/MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md](docs/MODULES/MODULE_08_TEACHER_WORKFORCE_PLANNING_DHG.md) - DHG calculations ⭐
- [docs/MODULES/MODULE_07_ENROLLMENT_PLANNING.md](docs/MODULES/MODULE_07_ENROLLMENT_PLANNING.md) - Enrollment rules
- [docs/MODULES/MODULE_10_REVENUE_PLANNING.md](docs/MODULES/MODULE_10_REVENUE_PLANNING.md) - Revenue calculations
- [foundation/EFIR_Workforce_Planning_Logic.md](foundation/EFIR_Workforce_Planning_Logic.md) - DHG methodology

**For Development**:
- [docs/developer-guides/DEVELOPER_GUIDE.md](docs/developer-guides/DEVELOPER_GUIDE.md) - Developer setup
- [docs/developer-guides/API_DOCUMENTATION.md](docs/developer-guides/API_DOCUMENTATION.md) - API reference
- [backend/README.md](backend/README.md) - Backend architecture
- [frontend/README.md](frontend/README.md) - Frontend architecture

**For Testing**:
- [docs/testing/TEST_COVERAGE_STRATEGY.md](docs/testing/TEST_COVERAGE_STRATEGY.md) - Coverage goals & plan
- [docs/developer-guides/E2E_TESTING_GUIDE.md](docs/developer-guides/E2E_TESTING_GUIDE.md) - E2E testing
- [backend/docs/TESTING.md](backend/docs/TESTING.md) - Backend testing

**For Current Status**:
- [docs/status/CURRENT_STATUS.md](docs/status/CURRENT_STATUS.md) - Current work (living doc, updated hourly)
- [docs/status/REMAINING_WORK.md](docs/status/REMAINING_WORK.md) - Outstanding tasks
- [docs/status/PRODUCTION_READINESS.md](docs/status/PRODUCTION_READINESS.md) - Production checklist

### Where Agents Create Documentation

**CRITICAL**: All agents MUST follow [docs/AGENT_DOCUMENTATION_STANDARDS.md](docs/AGENT_DOCUMENTATION_STANDARDS.md).

**Quick Reference**:

| Agent | Document Type | Location | Naming |
|-------|---------------|----------|--------|
| `qa-validation-agent` | Coverage reports | `docs/agent-work/` | `YYYY-MM-DD_agent-{N}_coverage-{scope}.md` |
| `efir-master-agent` | Coordination reports | `docs/agent-work/` | `YYYY-MM-DD_master-agent_{purpose}.md` |
| `backend-*-agent` | Implementation reports | `docs/agent-work/` | `YYYY-MM-DD_{agent}_{implementation}.md` |
| `system-architect-agent` | ADRs | `docs/technical-decisions/` | `{DECISION}_ADR.md` |
| `documentation-training-agent` | User/Dev guides | `docs/user-guides/` or `docs/developer-guides/` | `{NAME}_GUIDE.md` |
| `product-architect-agent` | Module specs | `docs/MODULES/` | `MODULE_{NN}_{NAME}.md` |

**Living Documents** (update in place with timestamp headers):
- `docs/status/CURRENT_STATUS.md`
- `docs/status/REMAINING_WORK.md`
- `docs/status/CODEBASE_REVIEW.md`
- `docs/status/PRODUCTION_READINESS.md`

### Document Naming Conventions

| Type | Format | Example |
|------|--------|---------|
| Living docs | `{NAME}.md` | `CURRENT_STATUS.md` |
| Agent reports | `YYYY-MM-DD_agent-{N}_{purpose}.md` | `2025-12-05_agent-13_coverage.md` |
| Phase summaries | `YYYY-MM-DD_phase-{N}-{desc}.md` | `2025-12-05_phase-1-completion.md` |
| Implementation | `YYYY-MM-DD_{name}.md` | `2025-12-03_database-schema-fix.md` |
| Guides | `{NAME}_GUIDE.md` | `USER_GUIDE.md` |
| Versioned | `{NAME}_v{major}_{minor}.md` | `EFIR_Budget_App_PRD_v1.2.md` |

### Document Lifecycle

**Living Documents** (no dates in filenames):
- Updated frequently with timestamp headers
- Never archived
- Examples: `CURRENT_STATUS.md`, `REMAINING_WORK.md`

**Snapshot Documents** (dated with YYYY-MM-DD prefix):
- Created once, never modified
- Archived after 30-90 days depending on type
- Examples: Agent reports, phase summaries, implementation reports

**Reference Documents** (versioned or unversioned):
- Updated when business rules change
- Versioned using semantic versioning (v1.2 → v1.3)
- Examples: Module specs, PRD, TSD

### Maintenance Schedule

- **Daily**: Update living status docs in `docs/status/`
- **Weekly**: Review agent reports, archive old work (>30 days)
- **Monthly**: Archive completed work, update cross-references
- **Quarterly**: Full documentation audit, consolidation review

See [docs/DOCUMENTATION_GUIDE.md](docs/DOCUMENTATION_GUIDE.md) for complete governance and maintenance processes.
