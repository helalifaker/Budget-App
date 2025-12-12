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
pnpm generate:types:file  # Generate TS types from local openapi.json file
```

### Backend (from `backend/`)

**Prerequisites**: Python 3.11+, [uv](https://docs.astral.sh/uv/) (recommended) or pip

```bash
# Setup with uv (recommended - 10-100x faster)
uv sync --all-extras                         # Install all deps (creates .venv automatically)

# Setup with pip (alternative)
python3 -m venv .venv && source .venv/bin/activate
pip install -e .[dev]

# Development
uv run uvicorn app.main:app --reload         # Start API (http://localhost:8000)
uv run alembic upgrade head                  # Apply migrations
uv run alembic revision --autogenerate -m "desc"  # Create migration

# Testing
uv run pytest tests/ -v --tb=short           # Run tests verbose
uv run pytest tests/engine/ -v               # Test specific directory
uv run pytest -k test_dhg                    # Tests matching pattern
uv run pytest tests/ --cov=app --cov-report=term-missing -v  # With coverage

# Code Quality
uv run ruff check . --fix                    # Lint with auto-fix
uv run ruff format app                       # Format code (used by pre-commit)
uv run mypy app                              # Type check
```

### Running Single Tests
```bash
# Frontend - single test file
pnpm test -- tests/components/ui/Button.test.tsx --run

# Backend - single test file or function
uv run pytest tests/engine/test_dhg.py -v
uv run pytest tests/api/test_planning_api.py::test_specific_function -v
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

### ⚠️ JWT Authentication (Required for API)

The `SUPABASE_JWT_SECRET` is **required** for the backend to verify JWT tokens. Without it, all API calls return `401 Unauthorized` even after successful login.

**How to get your JWT Secret:**
1. Supabase Dashboard → Your Project → Settings → API
2. Scroll to **JWT Settings** section
3. Copy the **JWT Secret** (not the anon key or service role key)
4. Add to `backend/.env.local`: `SUPABASE_JWT_SECRET=your-secret-here`

See `backend/SETUP_JWT_AUTH.md` for detailed setup and troubleshooting.

### Redis Caching (Optional, Recommended for Production)

Redis 8.4+ provides TTL-based caching for expensive calculations:

```bash
# macOS installation
brew install redis && brew services start redis

# Verify Redis is running
redis-cli ping  # Expected: PONG
```

**Configuration** in `backend/.env.local`:
```env
REDIS_ENABLED="true"           # Enable caching
REDIS_REQUIRED="false"         # Graceful degradation if unavailable
REDIS_URL="redis://localhost:6379/0"
```

**Cache follows the calculation dependency graph**: Enrollment → Class Structure → DHG → Personnel Costs. Changing enrollment data automatically invalidates all dependent caches.

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

### UI Layout System (ModuleLayout Pattern)

The application uses a modern, responsive layout with fixed chrome height (120px):

```
┌────────┬────────────────────────────────────────────────────────────────────┐
│        │ ModuleHeader (48px) - Title + Search + Version + User              │
│ App    ├────────────────────────────────────────────────────────────────────┤
│ Side   │ WorkflowTabs (40px) - Horizontal tab navigation                    │
│ bar    ├────────────────────────────────────────────────────────────────────┤
│ (64px) │ TaskDescription (32px) - Contextual help text                      │
│        ├────────────────────────────────────────────────────────────────────┤
│        │ Content Area (flexible) - AG Grid / Forms / Tables                 │
└────────┴────────────────────────────────────────────────────────────────────┘
Mobile: MobileBottomNav (fixed) + MobileDrawer (slide-out)
```

**Key Layout Components** (`frontend/src/components/layout/`):
| Component | Purpose |
|-----------|---------|
| `ModuleLayout` | Main wrapper with all providers and responsive handling |
| `AppSidebar` | Collapsible sidebar (64px collapsed → 240px on hover) |
| `ModuleHeader` | Module title, global search, budget version selector |
| `WorkflowTabs` | Horizontal workflow step navigation |
| `TaskDescription` | Contextual help text based on current route |
| `MobileDrawer` | Slide-out navigation for mobile |
| `MobileBottomNav` | Bottom tab navigation for mobile |

**CSS Variables** (defined in `frontend/src/index.css`):
```css
--sidebar-width-collapsed: 64px;
--sidebar-width-expanded: 240px;
--layout-chrome-height: 120px;  /* 48 + 40 + 32 */
--redesign-content-height: calc(100vh - var(--layout-chrome-height));
```

---

## Agent System (14 Specialized Agents)

This codebase uses a 14-agent orchestration system. See `.claude/AGENT_ORCHESTRATION.md` for full details.

### Model Selection for Agents

⚠️ **Important**: Model selection is guidance, not automatic enforcement. For critical tasks, explicitly request the model: "Use Opus for this architecture design"

| Model | Use For | Agents |
|-------|---------|--------|
| ⚡ **Opus** | Complex reasoning & architecture | product-architect, system-architect, efir-master, performance-agent |
| 🎯 **Sonnet** | Standard development (default) | backend-engine, frontend-ui, database-supabase, backend-api-specialist, security-rls, governance-versioning, reporting-statements |
| 💨 **Haiku** | Simple tasks (tests, formatting) | qa-validation (running tests), documentation-training (simple formatting), data-migration (simple ETL) |

**Example invocation**:
```javascript
Task({
  subagent_type: "qa-validation-agent",
  model: "haiku",  // Cost-effective for running existing tests
  prompt: "Run the existing DHG calculation tests"
})
```

**Cost impact**: Proper model selection can save 30-40% while maintaining/improving quality on critical decisions.

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
4. Use appropriate models: Opus for architecture/complex reasoning, Haiku for simple tasks, Sonnet for standard development

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
- `uv run ruff check . && uv run mypy app` (backend)

---

## Database Migrations

Linear migration chain in `backend/alembic/versions/` (16 migrations):
```
001_initial_configuration → 002_planning_layer → 003_consolidation_layer →
004_fix_critical_issues → 005_analysis_layer → 006_class_structure_validation →
007_strategic_layer → 008_performance_indexes → 009_materialized_views_kpi →
010_planning_cells_writeback → 011_audit_columns_nationality →
012_seed_subjects → 013_historical_comparison → 014_workforce_personnel →
015_seed_reference_data_distributions → 016_fix_function_security_rls_performance
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

## Frontend-Backend Schema Alignment

Frontend Zod schemas (`frontend/src/types/api.ts`) must match backend Pydantic schemas. Drift causes runtime validation errors.

### OpenAPI Type Generation

```bash
# Start backend server first
cd backend && uv run uvicorn app.main:app --reload

# Generate TypeScript types (from another terminal)
cd frontend
pnpm generate:types       # From running server at localhost:8000
pnpm generate:types:file  # From saved openapi.json file
```

Generated types saved to `frontend/src/types/generated-api.ts`. Compare with hand-written Zod schemas to detect drift.

### Critical Schema Patterns

| Pattern | Backend (Pydantic) | Frontend (Zod/TypeScript) |
|---------|-------------------|---------------------------|
| **Bilingual names** | `name_fr`, `name_en` | Use `entity.name_en` (not `entity.name`) |
| **Status enums** | lowercase: `working`, `approved` | Use lowercase: `'working'` (not `'WORKING'`) |
| **Sort order field** | `sort_order` | Use `sort_order` (not `display_order`) |
| **Boolean flags** | `is_secondary`, `requires_atsem` | Must include all required booleans |

### Schema Validation Tests

```bash
# Run schema validation tests
cd frontend && pnpm test -- tests/schemas/api-schemas.test.ts --run
```

These tests catch drift early by validating enum values, field names, and required fields.

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

**Master Navigation**: [DOCUMENTATION_INDEX.md](DOCUMENTATION_INDEX.md) - Complete navigation for all documentation files.

### Key Documentation by Purpose

| Need | Document |
|------|----------|
| Business rules & formulas | `docs/MODULES/MODULE_08_*.md` (DHG), `docs/MODULES/MODULE_07_*.md` (Enrollment) |
| Development setup | `docs/developer-guides/DEVELOPER_GUIDE.md`, `backend/README.md`, `frontend/README.md` |
| API reference | `docs/developer-guides/API_DOCUMENTATION.md` |
| Testing | `docs/testing/TEST_COVERAGE_STRATEGY.md`, `docs/developer-guides/E2E_TESTING_GUIDE.md` |
| Current status | `docs/status/CURRENT_STATUS.md`, `docs/status/REMAINING_WORK.md` |
| Agent documentation rules | `docs/AGENT_DOCUMENTATION_STANDARDS.md` |

### Living Documents (Update in Place)

These files are updated frequently with timestamp headers:
- `docs/status/CURRENT_STATUS.md` - Current work
- `docs/status/REMAINING_WORK.md` - Outstanding tasks
- `docs/status/CODEBASE_REVIEW.md` - Code quality tracking
- `docs/status/PRODUCTION_READINESS.md` - Production checklist

### Agent Documentation Locations

| Agent | Location | Naming |
|-------|----------|--------|
| All agents (reports) | `docs/agent-work/` | `YYYY-MM-DD_{agent}_{purpose}.md` |
| System architect (ADRs) | `docs/technical-decisions/` | `{DECISION}_ADR.md` |
| Product architect | `docs/MODULES/` | `MODULE_{NN}_{NAME}.md` |

See [docs/DOCUMENTATION_GUIDE.md](docs/DOCUMENTATION_GUIDE.md) for complete governance and naming conventions.

---

## MCP Setup (Codex CLI)

This repo uses MCP servers via Codex CLI for agent tooling. MCP servers are configured globally in `~/.codex/config.toml`.

### Supabase MCP

1. Ensure your Supabase access token is available as an environment variable:
   - Add `SUPABASE_ACCESS_TOKEN=...` to `.env.local` (root), or export it in your shell before launching Codex.
2. Add the Supabase MCP server:
   ```bash
   codex mcp add supabase --url "https://mcp.supabase.com/mcp?project_ref=<your_project_ref>"
   ```
3. Verify it was added (if `codex mcp list` errors on macOS, inspect `~/.codex/config.toml` instead):
   - Look for `mcp_servers.supabase.url` pointing to your project.
