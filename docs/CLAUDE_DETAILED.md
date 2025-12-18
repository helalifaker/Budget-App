# CLAUDE_DETAILED.md

**Full reference documentation for Claude Code.** Only read this when you need detailed information - the summary is in [CLAUDE.md](../CLAUDE.md).

---

## Table of Contents
1. [Environment Setup](#environment-setup)
2. [Architecture Details](#architecture-details)
3. [Agent System](#agent-system)
4. [Domain Knowledge](#domain-knowledge)
5. [Database Schema](#database-schema)
6. [Frontend-Backend Schema Alignment](#frontend-backend-schema-alignment)
7. [Documentation System](#documentation-system)
8. [MCP Setup](#mcp-setup)

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

### JWT Authentication (Required for API)

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

## Architecture Details

### Backend Structure
```
backend/app/
├── api/v1/          # FastAPI routes (organized by module)
│   ├── students/        # Enrollment, class structure, projections
│   ├── teachers/        # Employees, DHG, AEFE positions
│   ├── finance/         # Revenue, costs, CapEx, statements
│   ├── insights/        # KPIs, dashboards, variance
│   ├── settings/        # Versions, parameters, strategic
│   └── admin/           # Users, imports, audit
├── engine/          # Pure calculation engines (by module ownership):
│   ├── students/        # enrollment/, calibration/, lateral_optimizer
│   ├── teachers/        # dhg/, eos/, gosi/
│   ├── finance/         # revenue/, financial_statements/
│   └── insights/        # kpi/
├── models/          # SQLAlchemy ORM (by prefix: students_*, teachers_*, finance_*, etc.)
├── schemas/         # Pydantic v2 request/response models
├── services/        # Business logic layer (coordinates engine + database)
└── core/            # Infrastructure (logging, pagination, security, cache)
```

**Engine-Module Ownership** (see `engine_golden_rules.md` Rule 14):
| Engine | Module Owner | Inputs From |
|--------|--------------|-------------|
| `enrollment/` | Students | Configuration (class sizes, parameters) |
| `calibration/` | Students | Enrollment, historical actuals |
| `dhg/` | Teachers | Class structure (from Students) |
| `eos/`, `gosi/` | Teachers | Employee data |
| `revenue/` | Finance | Enrollment counts, fee structure |
| `financial_statements/` | Finance | All planning outputs |
| `kpi/` | Insights | All module outputs |

### Frontend Structure
```
frontend/src/
├── routes/                  # TanStack Router pages (6-module structure)
│   ├── _authenticated/      # Auth-protected routes wrapper
│   │   ├── students/            # planning, class-structure, validation, settings
│   │   ├── teachers/            # employees, dhg/, aefe-positions, settings
│   │   ├── finance/             # revenue, costs, capex, statements, settings
│   │   ├── insights/            # kpis, dashboards, variance
│   │   ├── settings/            # versions, parameters, strategic
│   │   └── admin/               # users, imports, audit
│   ├── _authenticated.command-center.tsx  # Ctrl+K command palette
│   └── _authenticated.tsx   # Auth layout wrapper
├── components/
│   ├── ui/                  # shadcn/ui components
│   ├── charts/              # Recharts visualizations
│   ├── layout/              # ModuleLayout, AppSidebar, WorkflowTabs
│   └── grid/
│       └── tanstack/        # TanStack Table components (replaced AG Grid)
├── contexts/                # React contexts (AuthContext, ModuleContext)
├── hooks/                   # Custom hooks (api/, useGridExcelKeyboard)
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
│        │ Content Area (flexible) - TanStack Table / Forms / Charts          │
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

## Agent System

This codebase uses a 9-agent orchestration system. See `.claude/AGENT_ORCHESTRATION.md` for full details.

### Model Selection for Agents

| Model | Use For | Agents |
|-------|---------|--------|
| **Opus** | Complex reasoning & architecture | product-architect-agent, Plan |
| **Sonnet** | Standard development (default) | Explore, frontend-ui-agent, performance-agent, qa-validation-agent, general-purpose |
| **Haiku** | Simple tasks (docs, guidance) | documentation-training-agent, claude-code-guide |

**Example invocation**:
```javascript
Task({
  subagent_type: "qa-validation-agent",
  model: "haiku",  // Cost-effective for running existing tests
  prompt: "Run the existing DHG calculation tests"
})
```

### Key Agent Boundaries

| Task Type | Agent | Cannot Do |
|-----------|-------|-----------|
| Business rules, formulas | `product-architect-agent` | Write code |
| Architecture, implementation plans | `Plan` | Implement features |
| Fast codebase exploration | `Explore` | Write code |
| React components, UI | `frontend-ui-agent` | Backend logic, DB changes |
| Performance optimization | `performance-agent` | Change business logic |
| Tests only | `qa-validation-agent` | Production code |
| Documentation | `documentation-training-agent` | Write code |

**Critical Rules**:
1. Consult `product-architect-agent` for business rules (SOURCE OF TRUTH)
2. Never cross agent boundaries
3. Use `Plan` agent for architecture decisions before major feature work
4. Use appropriate models: Opus for architecture/complex reasoning, Haiku for simple tasks, Sonnet for standard development

---

## Domain Knowledge

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

### Financial Rules

- **Currency**: SAR (Saudi Riyal), with EUR for AEFE costs
- **Accounting**: French PCG (Plan Comptable Général) + IFRS mapping
- **Revenue Recognition**: Trimester-based (T1: 40%, T2: 30%, T3: 30%)
- **Account Codes**: 60xxx-68xxx (Expenses), 70xxx-77xxx (Revenue)
- **Sibling Discount**: 25% on tuition for 3rd+ child (not on DAI/registration)

---

## Database Schema

### Database Migrations

Linear migration chain in `backend/alembic/versions/` (16 migrations):
```
001_initial_configuration → 002_planning_layer → 003_consolidation_layer →
004_fix_critical_issues → 005_analysis_layer → 006_class_structure_validation →
007_strategic_layer → 008_performance_indexes → 009_materialized_views_kpi →
010_planning_cells_writeback → 011_audit_columns_nationality →
012_seed_subjects → 013_historical_comparison → 014_workforce_personnel →
015_seed_reference_data_distributions → 016_fix_function_security_rls_performance
```

### Unified Versioning System

The `budget_versions` table is renamed to `settings_versions` (with module prefix) and `budget_version_id` becomes `version_id`:

```sql
-- OLD: budget_version_id (FK to budget_versions)
-- NEW: version_id (FK to settings_versions)

CREATE TYPE scenario_type AS ENUM (
  'ACTUAL',      -- Historical actuals (locked, immutable)
  'BUDGET',      -- Official approved budget
  'FORECAST',    -- Mid-year forecast revisions
  'STRATEGIC',   -- 5-year strategic planning
  'WHAT_IF'      -- Scenario analysis (sandboxed)
);
```

### Table Classification System

All tables follow one of 6 classifications (see `planning/DB_golden_rules.md` Section 3):

| Classification | Has version_id? | Has org_id? | Example Tables |
|----------------|-----------------|-------------|----------------|
| **STATIC** | ❌ | ❌ | `subjects`, `education_levels`, `nationalities` |
| **VERSION-LINKED** | ✅ | ✅ | `enrollment_projections`, `class_structure`, `dhg_results` |
| **ORG-SCOPED** | ❌ | ✅ | `employees`, `aefe_positions`, `cost_centers` |
| **OUTPUT** | ✅ | ✅ | `financial_statements`, `kpi_results` |
| **UI-LAYER** | ✅ | ✅ | `planning_cells`, `cell_comments` |
| **AUDIT** | ❌ | ✅ | `audit_logs`, `change_history` |

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
| **Version FK** | `version_id: UUID` | Use `version_id` (not `budget_version_id`) |
| **Scenario type** | `scenario_type: ScenarioType` | Enum: `'ACTUAL' \| 'BUDGET' \| 'FORECAST' \| ...` |
| **Bilingual names** | `name_fr`, `name_en` | Use `entity.name_en` (not `entity.name`) |
| **Status enums** | lowercase: `working`, `approved` | Use lowercase: `'working'` (not `'WORKING'`) |
| **Sort order field** | `sort_order` | Use `sort_order` (not `display_order`) |
| **Boolean flags** | `is_secondary`, `requires_atsem` | Must include all required booleans |

---

## Documentation System

**Master Navigation**: [DOCUMENTATION_INDEX.md](../DOCUMENTATION_INDEX.md) - Complete navigation for all documentation files.

### Key Documentation by Purpose

| Need | Document |
|------|----------|
| Business rules & formulas | `docs/modules/MODULE_08_*.md` (DHG), `docs/modules/MODULE_07_*.md` (Enrollment) |
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
| Product architect | `docs/modules/` | `MODULE_{NN}_{NAME}.md` |

See [docs/DOCUMENTATION_GUIDE.md](DOCUMENTATION_GUIDE.md) for complete governance and naming conventions.

---

## MCP Setup

This repo uses MCP servers for agent tooling.

### Supabase MCP

1. Ensure your Supabase access token is available as an environment variable:
   - Add `SUPABASE_ACCESS_TOKEN=...` to `.env.local` (root), or export it in your shell.
2. Add the Supabase MCP server:
   ```bash
   claude mcp add supabase --url "https://mcp.supabase.com/mcp?project_ref=<your_project_ref>"
   ```

### Recommended MCP Configuration

For optimal context usage, only enable MCP servers you actively need:

```bash
# Essential (always enabled)
claude mcp enable supabase
claude mcp enable filesystem

# Enable as needed
claude mcp enable github      # When working with PRs/issues
claude mcp enable playwright  # When doing E2E testing
claude mcp enable sentry      # When debugging production errors

# Disable rarely-used
claude mcp disable memory
claude mcp disable sequential-thinking
```
