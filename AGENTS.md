# Agent & Repository Guide

## Primary References
- `CLAUDE.md` — primary source of truth for standards, formulas, and architecture; read before any change.
- `.claude/AGENT_ORCHESTRATION.md` + `.claude/agents/*` — 14-agent boundaries and routing rules (product-architect is business-rule source).
- `README.md`, `backend/README.md`, `frontend/README.md` — current stack/version details and workflow notes.

## Stack Snapshot
- Frontend: React 19.2 + Vite 7 + TypeScript 5.9; Tailwind 4/shadcn-ui; AG Grid 34.3; TanStack Router/Query; React Hook Form + Zod; Supabase JS.
- Backend: FastAPI 0.123.4 on Python >=3.11 (<3.15); Pydantic 2.12; SQLAlchemy 2.0; Alembic migrations; async stack (`asyncpg`).
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

## Testing Expectations
- Frameworks: Vitest (frontend), Playwright (E2E), pytest (backend). Target ≥80% coverage (see `TEST_COVERAGE_*` docs).
- Naming: frontend `*.test.ts(x)`; backend `tests/test_*.py`. Mock external services; keep engine tests side-effect free. Prefer `pytest -q` for speed.
- Before PR: run `pnpm lint`, `pnpm typecheck`, `pnpm test`; attach Playwright report when flows change.

## Git & PR Hygiene
- Conventional Commits (`feat:`, `fix:`, `chore:`, `test:` …), imperative scope (e.g., `feat: add DHG allocation grid`).
- PRs include summary, modules touched, test commands/results, screenshots/GIFs for UI, and link to relevant docs/specs; note responsible agent when crossing domains.

## Security & Config
- Never commit secrets. Use `.env.local` in both `frontend/` and `backend/` for Supabase/database URLs/keys (see `SETUP_JWT_AUTH.md` for auth/RLS). Keep MFA enabled on Supabase.
