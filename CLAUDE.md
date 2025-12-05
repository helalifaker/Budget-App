# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Reference Commands

### Frontend (from `frontend/`)
```bash
pnpm install              # Install dependencies
pnpm dev                  # Start dev server (http://localhost:5173)
pnpm build                # Production build
pnpm test                 # Run Vitest (watch mode)
pnpm test -- --run        # Run tests once (CI mode)
pnpm lint:fix             # ESLint with auto-fix
pnpm format               # Prettier formatting
pnpm typecheck            # TypeScript check (tsc --noEmit)
pnpm test:e2e             # Playwright E2E tests
```

### Backend (from `backend/`)
```bash
source .venv/bin/activate                    # Activate venv (required first)
uvicorn app.main:app --reload                # Start API (http://localhost:8000)
.venv/bin/pytest tests/ -v --tb=short        # Run tests verbose
.venv/bin/pytest tests/engine/ -v            # Test specific directory
.venv/bin/pytest -k test_dhg                 # Tests matching pattern
.venv/bin/ruff check . --fix                 # Lint with auto-fix
.venv/bin/mypy app                           # Type check
alembic upgrade head                         # Apply migrations
alembic revision --autogenerate -m "desc"    # Create migration
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
├── engine/          # Pure calculation engines (dhg/, enrollment/, kpi/, revenue/, financial_statements/)
├── models/          # SQLAlchemy ORM (configuration, planning, consolidation, analysis, strategic)
├── schemas/         # Pydantic request/response models
├── services/        # Business logic layer
└── core/            # Infrastructure (logging, pagination, security, cache)
```

### Frontend Structure
```
frontend/src/
├── routes/          # TanStack Router pages (mirrors module structure)
│   ├── configuration/   # class-sizes, fees, subject-hours, teacher-costs, etc.
│   ├── planning/        # enrollment, classes, dhg, revenue, costs, capex
│   ├── consolidation/   # budget, statements
│   ├── analysis/        # kpis, dashboards, variance
│   └── strategic/       # 5-year planning
├── components/      # Reusable components (ui/, charts/, layout/)
├── contexts/        # React contexts (AuthContext)
└── schemas/         # Zod validation schemas
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

- **DHG**: Dotation Horaire Globale (Global Hours Allocation)
- **TRMD**: Tableau de Répartition des Moyens par Discipline (Gap Analysis)
- **HSA**: Heures Supplémentaires Annuelles (Annual Overtime)
- **PRRD**: Participation à la Rémunération des Résidents Détachés
- **H/E**: Heures/Élève (Hours per Student ratio)
- **E/D**: Élèves/Division (Students per Class)

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

Linear migration chain in `backend/alembic/versions/`:
```
001_initial_config → 002_planning_layer → 003_consolidation_layer →
004_fix_critical_issues → 005_analysis_layer → 006_class_structure_validation →
007_strategic_layer → 008_performance_indexes → 009_materialized_views_kpi →
010_planning_cells_writeback
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
