# EFIR Budget Planning Application
## Technical Solution Design (TSD)

**Version:** 1.2  
**Date:** November 2025  
**Status:** Draft – Ready for architecture + sprint planning  
**Prepared For:** École Française Internationale de Riyad (EFIR)

---

## 1. Purpose & References
- Capture the end-to-end solution design for the EFIR Budget Planning Application using the updated v1.2 stack.  
- Align engineering, product, and data teams on implementation scope, responsibilities, and technical constraints.  
- Provide a single reference for onboarding, estimation, and future audits.

**Reference Documents**  
- Product Requirements: `EFIR_Budget_App_PRD_v1_2.md`  
- Functional Requirements: `EFIR_Budget_Planning_Requirements_v1.2.md`  
- Module Specs: `EFIR_Module_Technical_Specification.md`

---

## 2. Business & Functional Scope Snapshot
| Domain | Scope Summary | Key Outputs |
|--------|---------------|-------------|
| Configuration | Academic calendars, class size policies, subject hours, fee matrix, teacher cost parameters | Shared master data APIs |
| Planning | Enrollment, workforce (DHG), facility, revenue, cost, CapEx | Driver-based planning views & calculations |
| Consolidation | Budget assembly, approvals, forecasting | Multi-version budgets, PCG + IFRS statements |
| Analysis | KPIs, dashboards, variance vs actuals | Executive dashboards, exports |
| Strategic | 5-year planning scenarios | Scenario planner, sensitivity analysis |

---

## 3. Solution Overview
```
┌──────────────┐        HTTPS + JWT/RLS        ┌────────────────┐
│ React 19.2   │◄──────────────────────────────►│ FastAPI 0.123  │
│ + Vite 7.2   │  Supabase JS client (auth)    │  Service Layer │
└──────┬───────┘                                 └─────┬────────┘
       │                                             │
       ▼                                             ▼
┌──────────────┐                           ┌───────────────────────┐
│ Supabase Auth│                           │PostgreSQL 17 (RLS +   │
│ + Realtime   │◄─────Edge Functions──────►│Row Level Policies)    │
└──────────────┘                           └───────────────────────┘
                                                 │
                                                 ▼
                                      Odoo / AEFE data imports
```

Key integration principles:
1. **Frontend-first UX:** Spreadsheet-like experiences via AG Grid, shadcn/ui, Tailwind 4.1.
2. **API-first backend:** FastAPI exposes modular services aligned with planning modules; heavy calculations run server-side with async tasks.
3. **Supabase-native platform:** PostgreSQL storage, Auth, Realtime collaborations, Edge Functions for scheduled jobs & imports.
4. **Observability baked-in:** Structured logging, tracing, and health probes for both frontend build (Vite + Sentry optional) and FastAPI (OpenTelemetry).

---

## 4. Technology Stack Alignment (v1.2)
| Layer | Technology | Notes |
|-------|------------|-------|
| UI Framework | React 19.2, TypeScript 5.9 | React Server Components + Actions for data mutations; Activity API for collaboration cues |
| Build Tooling | Vite 7.2, Vitest 3 | Baseline browser targeting, environment API, HMR test harness |
| UI System | Tailwind CSS 4.1, shadcn/ui (TW v4), AG Grid 34.3, Recharts 2.15 | AG Grid themeQuartz + custom cell renderers; OKLCH palette |
| Backend | FastAPI 0.123, Python 3.12, Uvicorn 0.34, Pydantic 2.12 | Modular routers, pydantic settings, async SQLAlchemy |
| Data | Supabase (PostgreSQL 17) | Row Level Security, database functions, edge functions |
| Auth & Collaboration | Supabase Auth, Supabase Realtime | Role-based policies, live cursor + auto-save |
| Dev Quality | ESLint 9 (flat), Prettier 3.4, Husky 9, lint-staged 15, Ruff 0.8, mypy 1.14, pytest 8, Playwright 1.49 | Mandatory pre-commit and CI gates |

---

## 5. Application Architecture Detail
### 5.1 Frontend (React 19 + Vite)
- **Application shell:** React Router app with layout-level suspense boundaries, streaming SSR via Vite for fast first paint.  
- **State layers:**  
  - Local UI state via React hooks/useEffectEvent.  
  - Server mutations handled through React Actions calling FastAPI endpoints via typed client.  
  - Cached queries managed with TanStack Query (React Query) to coordinate Supabase and REST data (real-time invalidation via Supabase channel events).  
- **Feature surfaces:**  
  - Parameter configurators use shadcn/ui forms + Zod validation.  
  - Planning grids (modules 7–12) rely on AG Grid with custom editors, column virtualization, undo/redo.  
  - Dashboards use Recharts, responsive layout, and persistent filter panels.  
- **Internationalization:** Minimal i18n via Lingui or react-intl (FR/EN) for AEFE stakeholders.  
- **Theming:** Tailwind 4 design tokens layered above shadcn defaults; AG Grid theme extended with EFIR palette.  
- **Security UX:** JWT stored in memory using Supabase client; silent refresh flows; route guards for role-based modules.

### 5.2 Backend (FastAPI Services)
- **Service layout:**
  - `app/main.py` bootstraps API, lifespan hooks, and OpenAPI docs.  
  - Routers aligned to module categories: `config`, `planning`, `financials`, `analytics`, `integrations`.  
  - Background tasks (Celery alternative) executed via FastAPI `BackgroundTasks` for short jobs; Supabase Edge Functions or Temporal-like orchestrator for long-running calculations (e.g., scenario rebuild).  
- **Data access:** SQLAlchemy 2.0 ORM + asyncpg for high-throughput operations.  
- **Validation:** Pydantic v2 models for request/response; schema generation feeds AG Grid column typing.  
- **Calculation services:**  
  - DHG engine (Python) receives normalized inputs (class counts, subject hours) and returns FTE, gaps, overtime suggestions.  
  - Revenue engine multiplies enrollment × fee matrix while applying rules (discounts, payment schedules).  
  - Consolidation service aggregates budgets, enforces PCG hierarchy, and stores snapshots with metadata.  
- **Integrations:**
  - Scheduled import endpoints for Odoo actuals (REST JSON).  
  - Upload endpoints for AEFE workforce files (CSV/Excel) parsed via pandas & stored in staging tables.

### 5.3 Supabase / PostgreSQL Data Layer
| Schema Group | Representative Tables | Notes |
|--------------|----------------------|-------|
| `config` | `schools`, `academic_cycles`, `class_size_rules`, `subjects`, `fee_matrix`, `teacher_costs` | Versioned via `effective_from`/`effective_to` |
| `planning` | `enrollment_plans`, `class_structures`, `dgh_runs`, `workforce_positions`, `facility_requirements` | Each row tagged by scenario + version |
| `financials` | `revenue_lines`, `personnel_costs`, `operating_costs`, `capex_items`, `budget_versions`, `financial_statements` | Snapshot + line-level audit columns |
| `analytics` | `kpi_cache`, `variance_reports`, `scenario_runs` | refreshed via scheduled jobs |
| `integration` | `odoo_actuals`, `aefe_staff_uploads`, `import_logs` | Staging + error handling |

**Row Level Security Strategy**  
- Roles: `admin`, `finance_manager`, `department_head`, `viewer`.  
- Policies enforced per table using Supabase Auth UID + `user_roles` join.  
- Example: department heads can read/write cost center rows where `cost_center_id` ∈ assigned list; revenue modules restricted to finance roles.  

**Realtime Channels**  
- Auto-save events publish to `planning_updates` channel; clients subscribe to show collaborator presence and highlight cells updated in last 30 seconds.  

### 5.4 Edge Functions & Automation
| Function | Trigger | Purpose |
|----------|--------|---------|
| `sync_odoo_actuals` | Scheduled (nightly) | Calls Odoo API, stores GL lines, pushes notifications if variances exceed thresholds |
| `refresh_kpi_cache` | Scheduled (hourly) | Aggregates planning + actuals for dashboards |
| `run_scenario` | HTTP (from UI) | Kicks off long-running scenario recalculation, stores results, emits status events |
| `notify_approvals` | Database trigger (budget version status change) | Sends email/Slack notifications via Supabase hooks |

---

## 6. Module-to-Service Mapping
| Module | Frontend Surface | API / Service | Key Data Assets |
|--------|-----------------|---------------|-----------------|
| 1. System Configuration | Settings console with stepper forms | `config/system` router | `schools`, `calendar_config`, `chart_of_accounts` |
| 2. Class Size Parameters | Grid + scenario comparators | `config/class-size` | `class_size_rules`, `class_structure_overrides` |
| 3. Subject Hours | Curriculum matrix editor | `config/subjects` | `subject_hours` |
| 4. Teacher Cost Parameters | Salary scale designer | `config/teacher-costs` | `teacher_costs`, `allowance_rates` |
| 5. Fee Structure | Fee cards + rule builder | `config/fees` | `fee_matrix`, `discount_rules` |
| 6. Timetable Constraints | Visual constraint builder | `planning/timetable` | `timetable_rules` |
| 7. Enrollment Planning | Scenario-driven data grid | `planning/enrollment` | `enrollment_plans` |
| 8. Workforce Planning (DHG) | DHG cockpit with charts | `planning/workforce` + DHG engine | `dgh_runs`, `fte_positions` |
| 9. Facility Planning | Room capacity board | `planning/facility` | `facility_requirements` |
| 10. Revenue Planning | Tuition waterfall view | `financials/revenue` | `revenue_lines` |
| 11. Cost Planning | Driver-based expense planners | `financials/costs` | `personnel_costs`, `operating_costs` |
| 12. CapEx Planning | CapEx backlog + depreciation | `financials/capex` | `capex_items`, `depreciation_schedules` |
| 13. Budget Consolidation | Approval workflow UI | `financials/budgets` | `budget_versions`, `approvals` |
| 14. Financial Statements | PCG/IFRS views exporter | `financials/statements` | `financial_statements` |
| 15. Statistical Analysis | KPI dashboards | `analytics/kpis` | `kpi_cache` |
| 16. Dashboards & Reporting | Role-specific dashboards | `analytics/dashboards` | Materialized views |
| 17. Budget vs Actual | Variance explorer | `analytics/variance` | `variance_reports`, `odoo_actuals` |
| 18. 5-Year Strategic Plan | Scenario sandbox | `strategy/scenarios` | `scenario_runs`, `multi_year_plans` |

---

## 7. Data Flow & Calculation Pipelines
```
Enrollment Input → Class Size Rules → Class Count
      │                    │             │
      └────────┬───────────┴─────────────┘
               ▼
        Subject Hours Matrix → DHG Engine → Workforce Costs
               │                                 │
               ▼                                 ▼
          Facility Needs                   Personnel Costing
               │                                 │
               ├───────────────┐               ├───────────────┐
               ▼               ▼               ▼               ▼
        Revenue Planner   Operating Costs   CapEx Planner   Scenario Engine
               │               │               │               │
               └───────────────┴─────┬─────────┴──────────────┘
                                     ▼
                           Budget Consolidation
                                     │
                      Financial Statements & KPIs
                                     │
                         Dashboards & Variance
```

Key processing notes:
1. **Deterministic runs:** Every DHG / budget run is stored with hash of inputs for reproducibility.  
2. **Scenario layering:** Users clone baseline scenarios; overrides stored as diff patches (JSONB) to minimize storage and enable quick comparisons.  
3. **Auto-save cadence:** Planning grids auto-save every 5 seconds of inactivity; conflicting edits resolved via operational transforms provided by AG Grid transaction API + Supabase realtime events.  
4. **Auditability:** Each write includes `created_by`, `updated_by`, `source` (UI/API/import) for traceability.

---

## 8. Security, Compliance & Access Control
- **Authentication:** Supabase Auth (email/password + SSO-ready). JWTs validated on FastAPI via `X-Supabase-Auth`.  
- **Authorization:** Dual enforcement—FastAPI dependency checks for coarse role gates; PostgreSQL RLS for row/column restrictions.  
- **Data residency:** Hosted in Supabase region `eu-central-1` to ensure compliance with French AEFE data requirements.  
- **PII handling:** Enrollment data limited to aggregated counts; individual student records stay in SIS.  
- **Secrets:** Managed via Supabase config + GitHub Actions secrets; local dev uses `.env` with `doppler` or `direnv`.  
- **Logging & Monitoring:**  
  - FastAPI logs shipped to Grafana Loki or Logtail.  
  - Metrics via Prometheus/OpenTelemetry collectors.  
  - Frontend errors captured via Sentry (optional) with PII scrubbing.

---

## 9. Non-Functional Requirements
| Category | Target |
|----------|--------|
| Performance | Sub-200ms API latency for standard queries; DHG recalculation < 8s for 5 scenarios |
| Availability | 99.5% uptime SLA during budgeting season (Aug-Feb) |
| Scalability | Support 50 concurrent planners with realtime collaboration |
| Data Integrity | Transactional consistency for budget approvals; referential constraints enforced |
| Observability | 100% API coverage with structured logs + request IDs |
| Accessibility | WCAG 2.1 AA compliance for key workflows |
| Localization | EN + FR UI toggle, SAR/EUR currency formatting |

---

## 10. DevOps, CI/CD & Environments
| Environment | Purpose | Deployment Notes |
|-------------|---------|------------------|
| `dev` | Individual developer sandboxes | Supabase project per developer; Vite dev server; FastAPI via Uvicorn reload |
| `staging` | Integrated QA & UAT | Auto-deployed on `main` merges via GitHub Actions; seeded with anonymized data |
| `prod` | Live EFIR environment | Blue/green deploy via Supabase + Fly.io/Render for FastAPI services |

**CI/CD Pipeline Steps**  
1. Install dependencies (pnpm + uv/pip).  
2. Lint & format: ESLint, Prettier, Ruff.  
3. Type check: `tsc --noEmit`, `mypy`.  
4. Tests: Vitest (unit), pytest (API), Playwright (critical flows).  
5. Build artifacts: Vite preview build, Docker image for FastAPI.  
6. Deploy to staging/prod with database migrations (`alembic`) gated via manual approval.

**Release Management**  
- Semantic versioning (e.g., `v1.2.0-beta`).  
- Feature flags for high-risk modules (DHG engine rewrite, Realtime collaboration).  
- Canary releases in staging with finance users before prod promotion.

---

## 11. Open Questions & Future Enhancements
1. Confirm final hosting target for FastAPI (Supabase Edge Functions vs Fly.io) to finalize observability stack.  
2. Determine whether SIS (Skolengo) integration is inbound only (CSV) or requires API-based sync.  
3. Evaluate adoption of React Server Components for heavy dashboards vs staying CSR for simplicity.  
4. Decide on analytics warehouse (e.g., Supabase + DuckDB) for historical KPI retention beyond transactional DB.  
5. Explore offline-first support (Service Workers) for unstable connectivity periods.

---

*Prepared by Codex (GPT-5) for EFIR Budget Planning Application – aligns with PRD/FRS v1.2 stack updates.*
