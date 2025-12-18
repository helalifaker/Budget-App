# CLAUDE.md

Guidance for Claude Code in this repository. **Keep this file minimal** - detailed docs are linked below.

## Quick Commands

```bash
# Monorepo (root)
pnpm dev          # Run frontend + backend
pnpm lint         # Lint both
pnpm typecheck    # Type check both
pnpm test         # Test both

# Frontend (frontend/)
pnpm dev          # Dev server :5173
pnpm test -- --run # Tests once
pnpm lint:fix     # ESLint fix

# Backend (backend/)
uv run uvicorn app.main:app --reload  # API :8000
uv run pytest tests/ -v --tb=short    # Tests
uv run ruff check . --fix             # Lint
uv run mypy app                       # Types
uv run alembic upgrade head           # Migrations
```

---

## Critical Constraints (NON-NEGOTIABLE)

### Schema Safety
| Schema | Rule |
|--------|------|
| `public` | **NEVER TOUCH** - belongs to another project |
| `efir_budget` | **OUR ONLY SCHEMA** - all tables here |

### Table Prefixes (in `efir_budget`)
- `ref_*` - Reference data (subjects, levels)
- `students_*` - Enrollment, class structure
- `teachers_*` - Employees, DHG, positions
- `finance_*` - Revenue, costs, statements
- `insights_*` - KPIs, dashboards
- `settings_*` - Versions, parameters
- `admin_*` - Audit, imports

---

## Architecture (10 Modules)

| Module | Route | Color | Primary Role | Purpose |
|--------|-------|-------|--------------|---------|
| **Enrollment** | `/enrollment/*` | sage | Academic Director | Projections, class structure, validation |
| **Workforce** | `/workforce/*` | wine | HR Manager | Employees, DHG, requirements, gap analysis |
| **Revenue** | `/revenue/*` | gold | Finance Director | Tuition, subsidies, other revenue |
| **Costs** | `/costs/*` | orange | Finance Director | Personnel, operating, overhead costs |
| **Investments** | `/investments/*` | teal | CFO | CapEx, projects, cash flow |
| **Consolidation** | `/consolidation/*` | blue | Finance Director | Checklist, rollup, statements, exports |
| **Insights** | `/insights/*` | slate | All (read) | KPIs, variance, trends, reports |
| **Strategic** | `/strategic/*` | purple | CFO/Executive | Long-term planning, scenarios, targets |
| **Settings** | `/settings/*` | neutral | All (limited) | Versions, system config |
| **Admin** | `/admin/*` | neutral | Admin only | Data uploads, historical imports |

**Module-specific settings**: Each module has its own `/settings` subpage (e.g., `/enrollment/settings`, `/workforce/settings`).

**Data Flow**: Enrollment → Class Structure → DHG → FTE → Personnel Costs → Budget → Statements

---

## Development Standards (4 Non-Negotiables)

1. **Complete** - No TODO/FIXME in production, all edge cases handled
2. **Type-safe** - TypeScript strict, Python type hints, Pydantic models
3. **Tested** - 80%+ coverage, comprehensive tests
4. **Quality gates** - Must pass: `pnpm lint && pnpm typecheck` + `ruff check . && mypy app`

---

## Key Acronyms

| Term | Meaning |
|------|---------|
| DHG | Dotation Horaire Globale (hours allocation) |
| TRMD | Gap analysis (needs vs available) |
| PRRD | AEFE teacher contribution (~41,863 EUR) |
| GOSI | Saudi social insurance (12%+10%) |
| EOS | End of service gratuity |
| H/E | Hours per student ratio |
| E/D | Students per class ratio |

---

## Calculation Engines

Pure functions in `backend/app/engine/`. Pattern:
```python
class DHGInput(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")
    version_id: UUID  # NOT budget_version_id

def calculate_dhg(inputs: DHGInput) -> DHGOutput:
    """Pure function - no DB, no side effects"""
```

---

## Agent System

14 specialized agents - see `.claude/AGENT_ORCHESTRATION.md`

| Model | Use For |
|-------|---------|
| **Opus** | Architecture, complex reasoning |
| **Sonnet** | Standard development (default) |
| **Haiku** | Tests, simple tasks |

**Key rule**: Consult `product-architect-agent` for business rules (SOURCE OF TRUTH)

---

## Detailed Documentation

**Read these only when working on related tasks** (keeps context small):

| Topic | Document |
|-------|----------|
| Full setup & env | [docs/CLAUDE_DETAILED.md](docs/CLAUDE_DETAILED.md) |
| Database rules | [docs/planning/DB_golden_rules.md](docs/planning/DB_golden_rules.md) |
| Engine rules | [backend/app/engine/engine_golden_rules.md](backend/app/engine/engine_golden_rules.md) |
| Refactoring plan | [docs/planning/REFACTORING_MASTER_PLAN.md](docs/planning/REFACTORING_MASTER_PLAN.md) |
| Schema changes | [docs/planning/DATABASE_REFACTORING_PLAN.md](docs/planning/DATABASE_REFACTORING_PLAN.md) |
| Agent orchestration | [.claude/AGENT_ORCHESTRATION.md](.claude/AGENT_ORCHESTRATION.md) |
| Module specs | [docs/modules/](docs/modules/) |
| API docs | [docs/developer-guides/API_DOCUMENTATION.md](docs/developer-guides/API_DOCUMENTATION.md) |

---

## Migration Naming Standard (NON-NEGOTIABLE)

**All Alembic migrations MUST follow this convention:**

| Element | Format | Example |
|---------|--------|---------|
| **File name** | `YYYYMMDD_HHMM_descriptive_name.py` | `20251215_0800_add_school_period.py` |
| **Revision ID** | `NNN_descriptive_name` (3-digit, sequential) | `029_add_school_period` |
| **Down revision** | Previous revision in chain | `028_phase_4c_financial_consolidation` |

**Rules:**
1. **Sequential numbering**: Each new migration gets the next number (no gaps, no branches)
2. **Single chain**: All migrations form ONE linear chain (no forks)
3. **Descriptive names**: Use `snake_case`, describe what the migration does
4. **Check before creating**: Run `alembic heads` to verify only ONE head exists
5. **Verify after creating**: Run `alembic history` to confirm linear chain

**Before creating a migration:**
```bash
cd backend
uv run alembic heads           # Must show exactly ONE head
uv run alembic history --verbose | head -20  # Check current chain
```

---

## Environment Quick Reference

```bash
# Required env vars (see backend/.env.example)
SUPABASE_JWT_SECRET    # Required for API auth
DATABASE_URL           # For app (via pgBouncer)
DIRECT_URL             # For migrations (direct connection)
```

JWT Secret: Supabase Dashboard → Settings → API → JWT Settings
