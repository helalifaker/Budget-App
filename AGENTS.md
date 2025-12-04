# Repository Guidelines

## Project Structure & Module Organization
- Monorepo root scripts orchestrate both stacks; see `package.json` for shared tasks.
- `frontend/` — React 19 + Vite + TypeScript; UI components, hooks, and routing live under `src/`; Playwright setup in `tests/` or `src/__tests__/`.
- `backend/` — FastAPI app in `app/` (api/, engine/, models/, schemas/, services/); Alembic migrations in `alembic/versions/`; pytest suites in `tests/`.
- `docs/` holds module specs and database guides; `.claude/` and `CLAUDE.md` define agent boundaries and should be consulted before changing cross-domain logic.

## Build, Test, and Development Commands
- `pnpm dev` — run frontend dev server and backend Uvicorn hot-reload together.
- `pnpm build` — build the frontend bundle; backend is compiled/type-checked during lint/typecheck steps.
- `pnpm lint` — ESLint+Prettier for frontend and Ruff for backend.
- `pnpm typecheck` — TS `tsc --noEmit` plus backend `mypy`.
- `pnpm test` — Vitest + backend pytest. For focused work: `pnpm --filter efir-budget-frontend test`, `cd backend && .venv/bin/pytest`.
- E2E/UI: `cd frontend && pnpm test:e2e` (Playwright); bundle analysis: `cd frontend && pnpm build:analyze`.

## Coding Style & Naming Conventions
- Frontend: Prettier formatting (2-space indent), ESLint rules enforced; React components PascalCase; hooks/components in `src/` co-locate tests as `*.test.tsx`.
- Backend: Ruff line length 100; Pydantic/SQLAlchemy models PascalCase; functions/vars snake_case; keep calculation engines pure (no I/O) and call them from services/APIs only.
- Type safety is mandatory: TypeScript strictness on, Python type hints plus mypy; avoid TODO stubs—implement complete logic per `CLAUDE.md`.

## Testing Guidelines
- Frameworks: Vitest (unit), Playwright (E2E), pytest (backend). Target ≥80% coverage (see `TEST_COVERAGE_*` docs); prefer `pytest -q` for fast runs.
- Naming: frontend tests `*.test.ts(x)`; backend tests `tests/test_*.py`. Mock external services; keep engine tests side-effect free.
- Before PR: run `pnpm lint`, `pnpm typecheck`, `pnpm test`; attach Playwright report when modifying flows.

## Commit & Pull Request Guidelines
- History follows Conventional Commit style (`feat:`, `fix:`, `chore:`, `test:`). Use imperative mood and concise scope (e.g., `feat: add DHG allocation grid`).
- PRs should include: summary, scope of modules touched, test command results, and screenshots/GIFs for UI changes. Link related issues/docs (e.g., module spec in `docs/`).
- Respect agent boundaries: route business rules to `product-architect-agent`, API changes to `backend-api-specialist`, DB changes to `database-supabase-agent`; note the responsible agent in PR descriptions.

## Security & Configuration Tips
- Do not commit secrets; keep `.env.local` in `frontend/` and `backend/` with Supabase URLs/keys and database URLs.
- Enable MFA with Supabase accounts; when touching auth/RLS, consult `SETUP_JWT_AUTH.md` and `security-rls-agent` guidance.
