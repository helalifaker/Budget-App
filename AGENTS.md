# Agent & Repository Guide

## Primary References
- `CLAUDE.md` — primary source of truth for standards, formulas, and architecture; read before any change.
- `.claude/AGENT_ORCHESTRATION.md` + `.claude/agents/*` — 14-agent boundaries and routing rules (product-architect is business-rule source).
- `README.md`, `backend/README.md`, `frontend/README.md` — current stack/version details and workflow notes.
- `DOCUMENTATION_INDEX.md` — master navigation for all docs.

## Documentation Map
- Root specs in `foundation/`: `EFIR_Budget_App_PRD_v1.2.md`, `EFIR_Budget_App_TSD_v1.2.md`, `EFIR_Budget_Planning_Requirements_v1.2.md`, `EFIR_Module_Technical_Specification.md`, `EFIR_Workforce_Planning_Logic.md`, `EFIR_Data_Summary_v2.md`; stack/security/coverage notes in `docs/technical-decisions/STACK_VERSION_REVIEW.md` and `docs/technical-decisions/2025-11-18_security-cache-fixes.md`; testing/phase summaries in `docs/testing/TEST_COVERAGE_STRATEGY.md` and `docs/PHASE_2_*`.
- `docs/README.md`, `DOCUMENTATION_GUIDE.md`, `AGENT_DOCUMENTATION_STANDARDS.md` — how to write/consume docs.
- `docs/MODULES/` — 18 module specifications; `docs/DATABASE/` — `schema_design.md`, `setup_guide.md`, `sql/rls_policies.sql`.
- `docs/developer-guides/` (API_DOCUMENTATION, INTEGRATION_GUIDE, E2E_TESTING_GUIDE, PERFORMANCE_OPTIMIZATIONS, SUPABASE_AUTH_SETUP) and `docs/user-guides/` (USER_GUIDE, DEPLOYMENT_GUIDE, SUPABASE_SETUP_GUIDE).
- `docs/testing/` (calculation validation, E2E summary, coverage strategy); `docs/technical-decisions/` (TDRs, error boundary, stack upgrades).
- `docs/roadmaps/` (DETAILED_IMPLEMENTATION_PLAN, FOCUSED_ENHANCEMENT_ROADMAP, TECH_ENHANCEMENT_ROADMAP) and `docs/status/` (CURRENT_STATUS, PRODUCTION_READINESS, REMAINING_WORK, CODEBASE_REVIEW).
- `docs/templates/` (reports/TDR templates), `docs/agent-work/` (latest coverage updates), and `docs/archive/` (implementation reports, phase docs, status reports) for historical references.
- Enrollment projection implementation: `ENROLLMENT_PROJECTION_IMPLEMENTATION_PLAN.md` — phased plan for the retention + lateral-entry model, 4-layer overrides, capacity clamp, proration, and related DB/API/UI work.

## Stack Snapshot
- Frontend: React 19.2 + Vite 7 + TypeScript 5.9; Tailwind 4/shadcn-ui; AG Grid 34.3; TanStack Router/Query; React Hook Form + Zod; Supabase JS.
- Backend: FastAPI 0.123.4 on Python 3.14 (pyproject `>=3.11,<3.15`); Pydantic 2.12; SQLAlchemy 2.0; Alembic migrations; async stack (`asyncpg`).
- Tooling: pnpm workspaces; Husky + lint-staged; ESLint 9/Prettier for frontend; Ruff (line length 100) + mypy (py 3.12 target) + pytest for backend; Playwright + Vitest for E2E/unit.

## Project Layout
- Monorepo root orchestrates both stacks (`package.json` scripts). Key dirs: `frontend/` (React app under `src/`), `backend/` (FastAPI in `app/` with api/ engine/ models/ schemas/ services/), `docs/` (module specs/database guides), `.claude/` (agent configs).
- Alembic migrations live in `backend/alembic/versions/`; frontend Playwright setup under `frontend/tests/` and `src/__tests__/`.

## Commands (root unless noted)
- `pnpm dev` — runs frontend dev server + backend Uvicorn reload via concurrently.
- `pnpm build` — frontend build (tsc + Vite).
- `pnpm lint` — frontend ESLint/Prettier + backend Ruff.
- `pnpm typecheck` — frontend `tsc --noEmit` + backend mypy.
- `pnpm test` — Vitest then backend pytest. Focus: `pnpm --filter efir-budget-frontend test`; `cd backend && .venv/bin/pytest`.
- E2E/bundle: `cd frontend && pnpm test:e2e`; `cd frontend && pnpm build:analyze`.

## Coding Standards & Boundaries
- Frontend: TypeScript strict, 2-space Prettier; React components PascalCase; co-locate tests as `*.test.tsx`; server state via TanStack Query; forms via React Hook Form + Zod; no business/calculation logic in UI.
- Backend: Functions/vars snake_case; models/schemas PascalCase; engines in `app/engine` stay pure/no I/O; FastAPI routes/services call engines; schema changes only through Alembic migrations; follow DI patterns and Pydantic validation.
- Agent routing: business rules → `product-architect-agent`; DB/migrations → `database-supabase-agent`; APIs → `backend-api-specialist`; calculations → `backend-engine-agent`; UI → `frontend-ui-agent`; multi-domain → `efir-master-agent`.
- Supabase MCP tooling: Supabase MCP (`mcp__supabase__*`) is available in Codex. Use it for Supabase-related work (schema/RLS inspection, branches, Edge Functions, executing SQL) instead of manual dashboard steps, while keeping schema changes authored via Alembic migrations.

## Testing Expectations
- Frameworks: Vitest (frontend), Playwright (E2E), pytest (backend). Target ≥80% coverage (see `TEST_COVERAGE_*` docs).
- Naming: frontend `*.test.ts(x)`; backend `tests/test_*.py`. Mock external services; keep engine tests side-effect free. Prefer `pytest -q` for speed.
- Before PR: run `pnpm lint`, `pnpm typecheck`, `pnpm test`; attach Playwright report when flows change.

## Current Status (2025-12-09)
- Overall: 90% production-ready; all 18 modules implemented; database schema and 16 Alembic migrations complete/stable.
- Testing: Backend coverage 88.88% (1,575 tests: 1,413 passing, 149 failing due to test DB schema init); frontend has 145+ component tests; E2E 143/148 passing.
- Priority work: Fix Alembic migration setup in `conftest.py` for tests, add coverage for `cost_service.py`, `dashboard_service.py`, middleware (`auth.py`, `rate_limit.py`), and resolve remaining E2E timing/config issues.
- Recommendation: Proceed to staging/production once test DB initialization is fixed and coverage pushes toward 95%; see `docs/status/CURRENT_STATUS.md` and `docs/status/REMAINING_WORK.md` for live details.

## Git & PR Hygiene
- Conventional Commits (`feat:`, `fix:`, `chore:`, `test:` …), imperative scope (e.g., `feat: add DHG allocation grid`).
- PRs include summary, modules touched, test commands/results, screenshots/GIFs for UI, and link to relevant docs/specs; note responsible agent when crossing domains.

## Security & Config
- Never commit secrets. Use `.env.local` in both `frontend/` and `backend/` for Supabase/database URLs/keys (see `SETUP_JWT_AUTH.md` for auth/RLS). Keep MFA enabled on Supabase.
