# EFIR Budget App — Performance Refactoring Plan

Date: 2025-12-12  
Scope: Monorepo (frontend + backend + database + infra)  
Goal: “No lag” UX via measurable performance SLOs, reduced request round-trips, resilient infra, and async-heavy workflows.

---

## 0) Principles (non-negotiable for a finance app)

- **Performance budgets**: define p50/p95 targets per critical user interaction and enforce them in CI/load tests.
- **Resilience over “slow success”**: timeouts must fail fast; degraded modes must not add multi-second latency.
- **Minimize chatty dependencies**: avoid request paths that require many DB/Redis round-trips.
- **Async by default for heavy work**: calculations/cascades must not block UI interactions.
- **Observability-first**: every latency regression must be explainable within minutes (trace → DB queries → dependency timing).

---

## 1) Target SLOs / Performance Budgets

### UX budgets (end-to-end in browser)
- **Scenario selection**: UI feedback < 100ms; “saved” confirmation < 500ms p95.
- **Configuration changes (forms/overrides)**: typing stays 60fps; no network writes per keystroke; save < 500ms p95.
- **Planning page initial load**: first meaningful content < 1.5s p75; < 2.5s p95.
- **Grid interactions (AG Grid)**: scroll/resize/filter stays responsive (no long tasks > 50ms).
- **Heavy calculations (e.g., enrollment projections)**: async job dispatch < 250ms; job completion time is tracked separately.

### Backend budgets
- **CRUD endpoints**: p95 < 250ms (excluding auth/gateway); p99 < 500ms.
- **Read endpoints with joins**: p95 < 400ms; must be query-count bounded.
- **Async job enqueue endpoints**: p95 < 200ms.
- **Database query count**: hard cap per endpoint category (e.g., config update ≤ 2 queries; config read ≤ 3).

---

## 2) Phase 0 (Week 0–1): Measurement & Guardrails

### 2.1 Backend observability (must land first)
- Add **request duration** logging (start → end) with correlation id and route name.
- Add **DB query count + total DB time per request** (include query count in logs).
- Turn slow query logs into **actionable dashboards** (p95/p99, top N endpoints, top N queries).
- Add tracing (Sentry performance or OpenTelemetry) across:
  - HTTP request span
  - DB spans (SQLAlchemy)
  - Redis spans (if in request path)
- Add “dependency health budget” alerts:
  - Redis connect timeouts > 50ms
  - DB connection time > 100ms

### 2.2 Frontend observability
- Enable **React Profiler** and track:
  - long tasks
  - rerender frequency for planning pages
  - time-to-interactive on navigation
- Add lightweight instrumentation around:
  - scenario selection
  - save/validate actions
  - heavy grid renders

### 2.3 CI guardrails
- Add performance “smoke” load tests for top endpoints (k6/locust) with budgets and regression checks.
- Establish a baseline report stored in `docs/agent-work/` (or a dedicated perf folder) and updated on demand.

Deliverable: “Performance Baseline Report” + dashboards + regression thresholds.

---

## 3) Phase 1 (Week 1–2): Remove Known Latency Multipliers

### 3.1 Dependency timeouts and failure modes
- Ensure Redis is **not allowed to add seconds** to requests:
  - Redis timeouts set to sub-second (prod)
  - If Redis is required, fail startup (prod) and alert
  - If Redis is optional, skip rate limiting/caching immediately when unavailable
- Ensure rate limiting strategy is intentional:
  - Prefer gateway/WAF rate limiting for production when possible
  - If app-level rate limiting remains, it must not be on the critical path without healthy Redis

### 3.2 DB connectivity and pooling
- Align runtime DB URLs and pooling strategy with the environment:
  - Prefer **direct DB host** when reachable (esp. in-prod same-region)
  - Use **connection pooling** for API runtime (avoid per-request connection creation)
  - Keep pooler usage to cases that need it; avoid “double pooling” pitfalls
- Validate region locality:
  - API region must match DB region; cross-region RTT compounds query fan-out

### 3.3 Auth/middleware overhead audit
- Measure time spent in auth middleware and remove high-volume debug logging in production.
- Confirm middleware ordering and ensure no duplicated work per request.

Deliverable: p95 < 400ms for basic CRUD endpoints under light load.

---

## 4) Phase 2 (Week 2–4): “Less SQL per click” (API + DB Query Shape)

This is the biggest UX win for the planning experience.

### 4.1 Create “thin” endpoints for interactive actions
- Split “config update” from “full config fetch”:
  - **PATCH config** returns a minimal payload (only updated fields + version id + status)
  - Full config detail is fetched separately (and cached) when needed
- Avoid returning heavy relationship graphs on every write response.

### 4.2 Bound query counts per endpoint
- Replace relationship fan-out patterns with:
  - targeted selects (DTO queries)
  - single-join queries where appropriate
  - precomputed reference lookups (levels/cycles/scenarios)
- Add a hard query-count cap per endpoint in tests (e.g., “update_config ≤ 2 queries”).

### 4.3 DB indexing and execution plans
- Add/verify indexes for:
  - per-version config lookup (unique already exists; verify usage)
  - override tables filtered by config id
  - frequently queried “active row” filters (deleted_at patterns)
- Collect and review EXPLAIN plans for the top 10 slow queries.

Deliverable: scenario select “saved” < 500ms p95 even with remote DB, and < 250ms p95 in-region.

---

## 5) Phase 3 (Week 4–6): Async Calculations + Cascades (No Blocking UX)

### 5.1 Job system for heavy work
- Introduce a background job runner (Celery/RQ/Arq) with:
  - idempotent tasks
  - retry policy
  - dead-letter queue
  - status tracking table
- Convert expensive operations into jobs:
  - projection calculations
  - validation cascades
  - consolidation, exports, imports

### 5.2 Event-driven cascade (outbox pattern)
- When enrollment/config changes, write an event to an outbox table.
- Background workers consume events and update dependent modules/caches.
- UI shows “pending updates” state without blocking interaction.

Deliverable: UI stays responsive; expensive work does not run on request threads.

---

## 6) Phase 4 (Week 6–10): CQRS / Read Models for “Massive Finance App” Scale

### 6.1 Separate read vs write concerns
- Write model: normalized, auditable, transactional.
- Read model: denormalized “screen-shaped” views/tables for:
  - dashboards
  - consolidated reports
  - cross-module summaries

### 6.2 Materialized views / snapshotting
- Use materialized views or snapshot tables for:
  - budget version summaries
  - KPI aggregates
  - variance reporting
- Refresh strategy:
  - incremental updates when possible
  - scheduled refresh for big aggregates

### 6.3 Caching strategy (safe and observable)
- Cache only where:
  - data is read-heavy
  - invalidation is deterministic
  - stale reads are acceptable within a defined TTL
- Add cache hit-rate metrics and “cache bypass” switches.

Deliverable: dashboards and reports load fast without stressing OLTP tables.

---

## 7) Frontend Responsiveness Track (runs in parallel to Phases 1–4)

### 7.1 Interaction design to minimize writes
- Debounce + batch edits; commit on:
  - “Save” button
  - blur
  - step completion
- Keep “selected scenario” as immediate UI state; show “Saved” separately.

### 7.2 Rendering performance
- Avoid rerenders of the whole planning page on small state changes:
  - isolate state per section
  - memoize grids and heavy panels
  - avoid transforming large datasets in render
- Ensure AG Grid is configured for large datasets (virtualization, stable row IDs).

### 7.3 Data fetching strategy
- Prefetch reference data (scenarios, levels, cycles) early and cache with long stale time.
- Use `keepPreviousData` patterns so UI doesn’t “blink” on refetches.

Deliverable: no long tasks; UI remains smooth even when backend is slower.

---

## 8) Production Hardening Checklist (before go-live)

- Run load tests for expected concurrency and data size:
  - p95 and p99 SLO adherence
  - endpoint query count caps
  - DB CPU/IO saturation behavior
- Verify region locality (API + DB + Redis).
- Confirm Redis strategy:
  - required + monitored, or removed from request path
- Ensure all timeouts are sane (sub-second for internal deps where possible).
- Add autoscaling signals (CPU, latency, queue depth).

---

## 9) Suggested Work Breakdown (who does what)

- **performance-agent**: tracing, budgets, load tests, dashboards
- **system-architect-agent**: CQRS/read-model design, job architecture
- **backend-api-specialist**: thin endpoints + response shaping + query caps
- **database-supabase-agent**: indexes, materialized views, schema support for outbox/jobs
- **backend-engine-agent**: job-safe calculation engines (pure, idempotent)
- **frontend-ui-agent**: UX batching/debounce, render optimizations, perceived performance
- **security-rls-agent**: ensure RLS/auth doesn’t regress latency

---

## 10) Success Criteria

- Scenario selection “saved” < 500ms p95 (in-region), < 800ms p95 (remote).
- Update-config endpoints: query count ≤ 2 and stable under load.
- No dependency (Redis/DB) can add multi-second latency silently.
- Dashboards/reports use read models; OLTP remains healthy.
- Clear tracing for every slow request: “where time went” is always visible.

