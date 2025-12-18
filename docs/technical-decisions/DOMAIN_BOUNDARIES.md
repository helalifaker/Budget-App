# Domain Boundaries

> Technical decision document defining the canonical 10 modules and their naming conventions across all layers.

**Date**: 2025-12-16
**Status**: Approved
**Authors**: Development Team

---

## Canonical Module List

The EFIR Budget App is organized into **10 canonical modules**. These module names MUST be used consistently across all layers of the application.

| Module | Description | Route Prefix | DB Table Prefix |
|--------|-------------|--------------|-----------------|
| **Enrollment** | Student projections, class structure, validation | `/enrollment/*` | `students_*` |
| **Workforce** | Employees, DHG, requirements, gap analysis | `/workforce/*` | `teachers_*` |
| **Revenue** | Tuition, subsidies, other revenue | `/revenue/*` | `finance_*` |
| **Costs** | Personnel costs, operating expenses | `/costs/*` | `finance_*` |
| **Investments** | CapEx, projects, cash flow | `/investments/*` | `finance_*` |
| **Consolidation** | Budget rollup, financial statements, exports | `/consolidation/*` | `finance_*` |
| **Insights** | KPIs, variance analysis, dashboards, reports | `/insights/*` | `insights_*` |
| **Strategic** | Long-term planning, scenarios, targets | `/strategic/*` | `admin_*` |
| **Settings** | Versions, system configuration, parameters | `/settings/*` | `settings_*` |
| **Admin** | Data uploads, historical imports, audit | `/admin/*` | `admin_*` |

---

## Layer Mapping

Each module should have consistent naming across all application layers:

### Backend Layers

| Module | API Route File | Services Folder | Engine Folder |
|--------|----------------|-----------------|---------------|
| Enrollment | `api/v1/enrollment.py` | `services/enrollment/` | `engine/enrollment/` |
| Workforce | `api/v1/workforce.py` | `services/workforce/` | `engine/workforce/` |
| Revenue | `api/v1/revenue.py` | `services/revenue/` | `engine/revenue/` |
| Costs | `api/v1/costs.py` | `services/costs/` | `engine/costs/` |
| Investments | `api/v1/investments.py` | `services/investments/` | `engine/investments/` |
| Consolidation | `api/v1/consolidation.py` | `services/consolidation/` | `engine/consolidation/` |
| Insights | `api/v1/insights.py` | `services/insights/` | `engine/insights/` |
| Strategic | `api/v1/strategic.py` | `services/strategic/` | `engine/strategic/` |
| Settings | `api/v1/settings.py` | `services/settings/` | `engine/settings/` |
| Admin | `api/v1/admin.py` | `services/admin/` | `engine/admin/` |

### Frontend Layers

| Module | Route Folder | Services File | Hooks File | Types File |
|--------|--------------|---------------|------------|------------|
| Enrollment | `routes/_authenticated/enrollment/` | `services/enrollment.ts` | `hooks/api/useEnrollment.ts` | `types/enrollment.ts` |
| Workforce | `routes/_authenticated/workforce/` | `services/workforce.ts` | `hooks/api/useWorkforce.ts` | `types/workforce.ts` |
| Revenue | `routes/_authenticated/revenue/` | `services/revenue.ts` | `hooks/api/useRevenue.ts` | `types/revenue.ts` |
| Costs | `routes/_authenticated/costs/` | `services/costs.ts` | `hooks/api/useCosts.ts` | `types/costs.ts` |
| Investments | `routes/_authenticated/investments/` | `services/investments.ts` | `hooks/api/useInvestments.ts` | `types/investments.ts` |
| Consolidation | `routes/_authenticated/consolidation/` | `services/consolidation.ts` | `hooks/api/useConsolidation.ts` | `types/consolidation.ts` |
| Insights | `routes/_authenticated/insights/` | `services/insights.ts` | `hooks/api/useInsights.ts` | `types/insights.ts` |
| Strategic | `routes/_authenticated/strategic/` | `services/strategic.ts` | `hooks/api/useStrategic.ts` | `types/strategic.ts` |
| Settings | `routes/_authenticated/settings/` | `services/settings.ts` | `hooks/api/useSettings.ts` | `types/settings.ts` |
| Admin | `routes/_authenticated/admin/` | `services/admin.ts` | `hooks/api/useAdmin.ts` | `types/admin.ts` |

---

## Naming Conventions

### General Rules

1. **Module names are lowercase** in code, paths, and folder names
2. **Use singular form** (enrollment, not enrollments)
3. **Consistency is mandatory** - same name across all layers
4. **No abbreviations** in module names (except established acronyms like DHG, KPI)

### File Naming

| Layer | Convention | Example |
|-------|------------|---------|
| Backend Python | `snake_case` | `enrollment_service.py` |
| Frontend TypeScript | `kebab-case` | `enrollment-projection.ts` |
| React Hooks | `camelCase` with `use` prefix | `useEnrollment.ts` |
| React Components | `PascalCase` | `EnrollmentGrid.tsx` |

### Export Naming

| Layer | Convention | Example |
|-------|------------|---------|
| Backend services | `PascalCase` class | `EnrollmentService` |
| Frontend services | `camelCase` with `Api` suffix | `enrollmentApi` |
| Frontend hooks | `camelCase` with `use` prefix | `useEnrollment` |

---

## Data Flow

The modules follow a specific data dependency chain:

```
Enrollment → Class Structure → DHG Requirements → Personnel Costs → Budget → Statements
    ↓              ↓                  ↓                  ↓            ↓
Students    Workforce Need      FTE Calculation      Costs      Consolidation
```

### Module Dependencies

| Module | Depends On | Provides Data To |
|--------|------------|------------------|
| Enrollment | Settings | Workforce, Revenue |
| Workforce | Enrollment, Settings | Costs |
| Revenue | Enrollment, Settings | Consolidation |
| Costs | Workforce, Settings | Consolidation |
| Investments | Settings | Consolidation |
| Consolidation | Revenue, Costs, Investments | Insights |
| Insights | All modules | - |
| Strategic | Insights | - |
| Settings | - | All modules |
| Admin | - | - |

---

## Module-Specific Settings

Each module may have its own settings subpage:

- `/enrollment/settings` - Entry point rates, nationality distribution
- `/workforce/settings` - Subject hours, cost parameters, HSA rates
- `/revenue/settings` - Fee structure, discount rules
- `/costs/settings` - Cost categories, allocation rules
- etc.

These are distinct from the global `/settings/*` module which handles:
- Version management
- System configuration
- Reference data

---

## Future Cleanup Items

The following inconsistencies should be addressed:

1. **Folder naming case**: `docs/modules/` and `docs/database/` should be lowercase (`docs/modules/`, `docs/database/`)
2. **Legacy naming**: Some backend code may still use `students`, `teachers`, `finance` instead of canonical module names

---

## References

- [CLAUDE.md](../../CLAUDE.md) - Main project guidelines
- [Module Specifications](../MODULES/) - Detailed module documentation
- [TYPE_CONTRACT.md](./TYPE_CONTRACT.md) - OpenAPI type generation workflow
