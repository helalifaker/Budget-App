# Budget → Version Terminology Cleanup

**Generated**: 2025-12-16
**Status**: Pending Implementation
**Scope**: Comprehensive rename of "budget" terminology to "version" across entire codebase

---

## Executive Summary

| Category | Files | Changes | Priority |
|----------|-------|---------|----------|
| F821 Error Fix | 1 | 1 | P0 - Critical |
| Backend Services | 8 | ~45 | P1 - High |
| Backend API | 3 | ~25 | P1 - High |
| Backend Schemas | 1 | 2 | P1 - High |
| Backend Models | 1 | 4 | P2 - Medium |
| Frontend Services | 3 | ~15 | P1 - High |
| Frontend Components | 4 | ~20 | P2 - Medium |
| Frontend Routes | 20+ | ~50 | P2 - Medium |
| Frontend Hooks | 5 | ~15 | P2 - Medium |
| Backend Tests | 25+ | ~200 | P3 - Low |
| Frontend Tests | 10+ | ~50 | P3 - Low |
| Documentation | 15+ | ~100 | P4 - Lowest |

**Total Estimated Changes**: ~530+ occurrences

---

## P0 - CRITICAL: F821 Error Fix

### File: `backend/app/services/students/enrollment_projection_service.py`

**Issue**: Missing import causes F821 "undefined name" error

**Fix**: Add `calculate_proration_by_grade` to imports (lines 25-39):

```python
from app.engine.enrollment import (
    ClassSizeConfig,
    EngineEffectiveRates,
    GradeOptimizationInput,
    GradeOptimizationResult,
    NewStudentsSummary,
    ProjectionInput,
    ScenarioParams,
    build_new_students_summary,
    calculate_proration_by_grade,  # ADD THIS LINE
    is_entry_point_grade,
    optimize_grade_lateral_entry,
    optimize_ps_entry,
    project_multi_year,
    validate_projection_input,
)
```

---

## P1 - HIGH PRIORITY: Backend Changes

### 1. Schema Field Renames

#### File: `backend/app/schemas/consolidation.py`

| Line | Current | Change To |
|------|---------|-----------|
| 53 | `budget_version_name: str` | `version_name: str` |
| 310 | `budget_version_name: str` | `version_name: str` |

---

### 2. Service Instance Variables

#### File: `backend/app/services/finance/consolidation_service.py`

| Line | Current | Change To |
|------|---------|-----------|
| 59 | `self.budget_version_service = BaseService(BudgetVersion, session)` | `self.version_service = BaseService(Version, session)` |
| 79 | Comment: "Eager loads budget_version" | "Eager loads version" |
| 83 | `await self.budget_version_service.get_by_id(version_id)` | `await self.version_service.get_by_id(version_id)` |
| 137 | `await self.budget_version_service.get_by_id(version_id)` | `await self.version_service.get_by_id(version_id)` |
| 201 | `budget_version = await self.budget_version_service.get_by_id(version_id)` | `version = await self.version_service.get_by_id(version_id)` |
| 204 | `if budget_version.status != BudgetVersionStatus.WORKING:` | `if version.status != VersionStatus.WORKING:` |
| 207-209 | `budget_version.status` references | `version.status` |
| 223 | `updated = await self.budget_version_service.update(` | `updated = await self.version_service.update(` |
| 260 | `budget_version = await self.budget_version_service.get_by_id(version_id)` | `version = await self.version_service.get_by_id(version_id)` |
| 263-268 | `budget_version.status` references | `version.status` |
| 273 | `budget_version.fiscal_year` | `version.fiscal_year` |
| 278 | `updated = await self.budget_version_service.update(` | `updated = await self.version_service.update(` |
| 437 | `await self.budget_version_service.update(` | `await self.version_service.update(` |

#### File: `backend/app/services/finance/financial_statements_service.py`

| Line | Current | Change To |
|------|---------|-----------|
| 56 | `self.budget_version_service = BaseService(BudgetVersion, session)` | `self.version_service = BaseService(Version, session)` |
| 286 | `budget_version = await self.budget_version_service.get_by_id(version_id)` | `version = await self.version_service.get_by_id(version_id)` |
| 302-304 | `budget_version.academic_year` | `version.academic_year` |
| 312 | `budget_version.fiscal_year` | `version.fiscal_year` |
| 333 | `budget_version = await self.budget_version_service.get_by_id(version_id)` | `version = await self.version_service.get_by_id(version_id)` |
| 346-370 | `budget_version.academic_year`, `budget_version.fiscal_year` | `version.academic_year`, `version.fiscal_year` |

#### File: `backend/app/services/settings/configuration_service.py`

| Line | Current | Change To |
|------|---------|-----------|
| 84 | `self.budget_version_base_service = BaseService(BudgetVersion, session)` | `self.version_service = BaseService(Version, session)` |

---

### 3. API Route Handlers

#### File: `backend/app/api/v1/consolidation.py`

| Line | Current | Change To |
|------|---------|-----------|
| 234 | `budget_version = await consolidation_service.budget_version_service.get_by_id(` | `version = await consolidation_service.version_service.get_by_id(` |
| 238 | `if not budget_version:` | `if not version:` |
| 294 | `budget_version = await consolidation_service.budget_version_service.get_by_id(` | `version = await consolidation_service.version_service.get_by_id(` |
| 298 | `if not budget_version:` | `if not version:` |
| 337 | `budget_version_name=budget_version.name,` | `version_name=version.name,` |
| 338-340 | `budget_version.fiscal_year`, `budget_version.academic_year`, `budget_version.status` | `version.fiscal_year`, etc. |
| 436 | `budget_version = await consolidation_service.budget_version_service.get_by_id(` | `version = await consolidation_service.version_service.get_by_id(` |
| 440-446 | `budget_version` references | `version` |
| 505-515 | `budget_version` references | `version` |
| 609-634 | `budget_version` references | `version` |
| 621 | `budget_version_name=budget_version.name,` | `version_name=version.name,` |
| 733-756 | `budget_version` references | `version` |
| 948-971 | `budget_version` references | `version` |

#### File: `backend/app/api/v1/configuration.py`

| Line | Current | Change To |
|------|---------|-----------|
| 352 | `version = await config_service.budget_version_base_service.update(` | `version = await config_service.version_service.update(` |

#### File: `backend/app/api/v1/export.py`

| Line | Current | Change To |
|------|---------|-----------|
| 116 | `consolidation.budget_version.name` | `consolidation.version.name` |
| 349 | `consolidation.budget_version.name` | `consolidation.version.name` |
| 385 | `consolidation.budget_version.status` | `consolidation.version.status` |

---

### 4. Model Relationship Rename

#### File: `backend/app/models/base.py`

| Line | Current | Change To |
|------|---------|-----------|
| 262 | Comment: "Mixin for tables that belong to a specific budget version" | "Mixin for tables that belong to a specific version" |
| 272 | Comment: "Foreign key to budget version." | "Foreign key to version." |
| 278 | Comment: "Budget version this record belongs to" | "Version this record belongs to" |
| 282-283 | `def budget_version(cls):` | `def version(cls):` |

**Impact of relationship rename** - Update all `selectinload` calls:

| File | Line | Current | Change To |
|------|------|---------|-----------|
| `backend/app/services/students/class_structure_service.py` | 83 | `selectinload(ClassStructure.budget_version)` | `selectinload(ClassStructure.version)` |
| `backend/app/services/students/enrollment_service.py` | 94 | `selectinload(EnrollmentPlan.budget_version)` | `selectinload(EnrollmentPlan.version)` |
| `backend/app/services/teachers/dhg_service.py` | 99 | `selectinload(DHGSubjectHours.budget_version)` | `selectinload(DHGSubjectHours.version)` |
| `backend/app/services/teachers/dhg_service.py` | 248 | `selectinload(DHGTeacherRequirement.budget_version)` | `selectinload(DHGTeacherRequirement.version)` |
| `backend/app/services/teachers/dhg_service.py` | 385 | `selectinload(TeacherAllocation.budget_version)` | `selectinload(TeacherAllocation.version)` |
| `backend/app/services/insights/kpi_service.py` | 282 | `selectinload(KPIValue.budget_version)` | `selectinload(KPIValue.version)` |
| `backend/app/services/insights/kpi_service.py` | 322 | `selectinload(KPIValue.budget_version)` | `selectinload(KPIValue.version)` |
| `backend/app/services/finance/consolidation_service.py` | 95 | `selectinload(BudgetConsolidation.budget_version)` | `selectinload(BudgetConsolidation.version)` |

---

## P1 - HIGH PRIORITY: Frontend Changes

### 1. Type/Interface Field Names

#### File: `frontend/src/services/consolidation.ts`

| Line | Current | Change To |
|------|---------|-----------|
| 48 | `budget_version_name: string` | `version_name: string` |
| 79 | `budget_version_name: string` | `version_name: string` |

---

### 2. Query Invalidation Keys

#### File: `frontend/src/hooks/api/useConsolidation.ts`

| Line | Current | Change To |
|------|---------|-----------|
| 90 | `queryKey: ['budget-versions']` | `queryKey: ['versions']` |
| 109 | `queryKey: ['budget-versions']` | `queryKey: ['versions']` |

#### File: `frontend/src/hooks/api/useAnalysis.ts`

| Line | Current | Change To |
|------|---------|-----------|
| 72 | `queryKey: ['budget-versions']` | `queryKey: ['versions']` |

---

### 3. Storage Key

#### File: `frontend/src/contexts/VersionProvider.tsx`

| Line | Current | Change To |
|------|---------|-----------|
| 20 | `const STORAGE_KEY = 'efir-selected-budget-version'` | `const STORAGE_KEY = 'efir-selected-version'` |

---

### 4. UI Labels & Placeholders

#### File: `frontend/src/components/VersionSelector.tsx`

| Line | Current | Change To |
|------|---------|-----------|
| 27 | `label = 'Budget Version'` | `label = 'Version'` |
| 69 | `'Select budget version'` / `'No budget versions available'` | `'Select version'` / `'No versions available'` |

#### File: `frontend/src/components/GlobalVersionSelector.tsx`

| Line | Current | Change To |
|------|---------|-----------|
| 111 | `No budget versions` | `No versions` |
| 140 | `placeholder="Select budget version"` | `placeholder="Select version"` |

---

## P2 - MEDIUM PRIORITY: Frontend Routes (User-Facing Messages)

All routes with "Please select a budget version" messages:

| File | Line | Change |
|------|------|--------|
| `frontend/src/routes/_authenticated/investments/capex.tsx` | 423 | `Please select a version to view capital expenditure planning` |
| `frontend/src/routes/_authenticated/investments/cashflow.tsx` | 139 | `Please select a version to view cash flow analysis` |
| `frontend/src/routes/_authenticated/investments/index.tsx` | 173 | `Please select a version to view investment planning` |
| `frontend/src/routes/_authenticated/investments/projects.tsx` | 137 | `Please select a version to view project planning` |
| `frontend/src/routes/_authenticated/investments/settings.tsx` | 123 | `Please select a version to configure investment settings` |
| `frontend/src/routes/_authenticated/costs/personnel.tsx` | 388 | `Please select a version to view personnel cost planning` |
| `frontend/src/routes/_authenticated/costs/index.tsx` | 166 | `Please select a version to view cost planning` |
| `frontend/src/routes/_authenticated/costs/settings.tsx` | 120 | `Please select a version to configure cost settings` |
| `frontend/src/routes/_authenticated/strategic/long-term.tsx` | 138 | `Please select a version to view long-term planning` |
| `frontend/src/routes/_authenticated/strategic/scenarios.tsx` | 138 | `Please select a version to view scenario modeling` |
| `frontend/src/routes/_authenticated/strategic/targets.tsx` | 151 | `Please select a version to view strategic targets` |
| `frontend/src/routes/_authenticated/strategic/index.tsx` | 47 | `'Select a version'` |
| `frontend/src/routes/_authenticated/workforce/aefe-positions.tsx` | 109, 629, 731 | Multiple messages |
| `frontend/src/routes/_authenticated/workforce/gap-analysis.tsx` | 498 | `Please select a version from the header to view gap analysis.` |
| `frontend/src/routes/_authenticated/workforce/salaries.tsx` | 409 | `Please select a version from the header to view salaries.` |
| `frontend/src/routes/_authenticated/workforce/settings/timetable.tsx` | 229 | `Please select a version to view timetable constraints.` |
| `frontend/src/routes/_authenticated/consolidation/checklist.tsx` | 489 | `Please select a version to view the consolidation checklist` |
| `frontend/src/routes/_authenticated/settings/versions.tsx` | 335, 570, 616, 785, 908 | Multiple messages |

---

## P2 - MEDIUM PRIORITY: Comments & Docstrings

### Backend Comments to Update

| File | Line | Current | Change To |
|------|------|---------|-----------|
| `backend/app/services/students/class_structure_service.py` | 65 | "Eager loads level, cycle, budget_version" | "Eager loads level, cycle, version" |
| `backend/app/services/students/enrollment_service.py` | ~94 | "budget_version" | "version" |
| `backend/app/services/teachers/dhg_service.py` | 82, 234, 368 | Multiple "budget_version" comments | "version" |
| `backend/app/services/insights/kpi_service.py` | 265, 306 | "budget_version" comments | "version" |
| `backend/app/services/finance/consolidation_service.py` | 66-79 | Multiple docstrings | Update to "version" |

### Frontend Comments to Update

| File | Lines | Description |
|------|-------|-------------|
| `frontend/src/components/ChangeLogDialog.tsx` | 21 | JSDoc param description |
| `frontend/src/components/GlobalVersionSelector.tsx` | 4 | Component description |
| `frontend/src/components/UndoRedoToolbar.tsx` | 23 | JSDoc param |
| `frontend/src/components/ChangeLogViewer.tsx` | 28 | JSDoc param |
| `frontend/src/components/CommandPalette.tsx` | 302 | Command description |
| `frontend/src/components/layout/TaskDescription.tsx` | 71 | Route description |
| `frontend/src/services/*.ts` | Multiple | JSDoc comments |
| `frontend/src/hooks/api/*.ts` | Multiple | JSDoc comments |

---

## P3 - LOW PRIORITY: Test Files

### Backend Test Fixtures to Rename

#### File: `backend/tests/conftest.py`

| Line | Current | Change To |
|------|---------|-----------|
| 854 | `async def test_budget_version(` | `async def test_version(` |

#### File: `backend/tests/fixtures/__init__.py`

| Line | Current | Change To |
|------|---------|-----------|
| 483 | `async def mock_budget_version(db_session):` | `async def mock_version(db_session):` |
| 500 | `async def mock_budget_version_submitted(db_session):` | `async def mock_version_submitted(db_session):` |

### Backend Test Files Using `test_budget_version` Fixture

All these files need parameter renames from `test_budget_version` to `test_version`:

- `backend/tests/services/test_teacher_cost_service.py` (~38 occurrences)
- `backend/tests/services/test_dashboard_service.py` (~50 occurrences)
- `backend/tests/services/test_fee_structure_service.py` (~30 occurrences)
- `backend/tests/services/test_capex_service.py` (~35 occurrences)
- `backend/tests/services/test_consolidation_service.py`
- `backend/tests/services/test_configuration_service.py`
- `backend/tests/services/test_cost_service.py`
- `backend/tests/services/test_enrollment_calibration_service.py`
- `backend/tests/services/test_enrollment_projection_service.py`
- `backend/tests/services/test_class_size_service.py`
- `backend/tests/services/test_class_structure_service.py`
- `backend/tests/services/test_dhg_service.py`
- `backend/tests/services/test_enrollment_service.py`
- `backend/tests/services/test_historical_import_service.py`
- `backend/tests/services/test_impact_calculator_service.py`
- `backend/tests/services/test_kpi_service.py`
- `backend/tests/services/test_materialized_view_service.py`
- `backend/tests/services/test_reference_data_service.py`
- `backend/tests/services/test_revenue_service.py`
- `backend/tests/services/test_strategic_service.py`
- `backend/tests/services/test_subject_hours_service.py`
- `backend/tests/services/test_timetable_constraints_service.py`
- `backend/tests/services/test_writeback_service.py`
- `backend/tests/services/test_writeback_service_extended.py`

### Backend API Test Files

| File | Changes Needed |
|------|----------------|
| `backend/tests/api/test_consolidation_api.py` | `mock_budget_version` → `mock_version` |
| `backend/tests/api/test_planning_api.py` | `test_budget_version` references |
| `backend/tests/api/test_analysis_api.py` | Multiple references |
| `backend/tests/api/test_export_api.py` | Test function names like `test_export_budget_excel_success` |

### Frontend Test Files

#### File: `frontend/tests/e2e/helpers/api-mock.helper.ts`

| Line | Current | Change To |
|------|---------|-----------|
| 11 | `let mockBudgetVersions: BudgetVersion[]` | `let mockVersions: Version[]` |
| 34 | `interface BudgetVersion` | Use imported `Version` type |
| 48 | `export async function setupBudgetVersionMocks(page)` | `export async function setupVersionMocks(page)` |
| 262 | `export function getMockBudgetVersions()` | `export function getMockVersions()` |

#### File: `frontend/tests/e2e/helpers/navigation.helper.ts`

| Line | Current | Change To |
|------|---------|-----------|
| 19 | `export async function selectBudgetVersion(page, versionName)` | `export async function selectVersion(page, versionName)` |

#### All E2E spec files using `setupBudgetVersionMocks`:

- `frontend/tests/e2e/integrations.spec.ts`
- `frontend/tests/e2e/consolidation.spec.ts`
- `frontend/tests/e2e/budget-workflow.spec.ts`
- `frontend/tests/e2e/dhg.spec.ts`
- `frontend/tests/e2e/historical-import.spec.ts`
- `frontend/tests/e2e/kpis.spec.ts`
- `frontend/tests/e2e/accessibility.spec.ts`
- `frontend/tests/e2e/strategic.spec.ts`
- `frontend/tests/e2e/subject-hours.spec.ts`
- `frontend/tests/e2e/revenue.spec.ts`

---

## P4 - LOWEST PRIORITY: Documentation

### Files to Update

- `docs/planning/DB_golden_rules.md`
- `docs/database/schema_design.md`
- `docs/database_SCHEMA.md`
- `docs/modules/MODULE_02_FUTURE_ENHANCEMENTS.md`
- `docs/modules/MODULE_13_BUDGET_CONSOLIDATION.md`
- `docs/PHASE_2_TEST_COVERAGE_PLAN.md`
- `docs/PHASE_2_QUICK_START_GUIDE.md`
- `docs/roadmaps/DETAILED_IMPLEMENTATION_PLAN.md`

---

## ITEMS TO KEEP (Backward Compatibility Aliases)

These alias definitions should be **KEPT** for backward compatibility:

### Backend Aliases (Keep)

| File | Line | Alias |
|------|------|-------|
| `backend/app/models/settings.py` | 86 | `BudgetVersionStatus = VersionStatus` |
| `backend/app/models/settings.py` | 400 | `BudgetVersion = Version` |
| `backend/app/models/__init__.py` | 196-197 | `BudgetVersion`, `BudgetVersionStatus` |
| `backend/app/schemas/configuration.py` | 17, 113, 127, 138, 189, 266 | Schema aliases |
| `backend/app/schemas/consolidation.py` | 21 | `BudgetVersionStatus = VersionStatus` |
| `backend/app/services/settings/version_service.py` | 33-34, 707 | Service aliases |
| All service files | Various | Local `BudgetVersion = Version` aliases |

### Frontend Aliases (Keep)

| File | Line | Alias |
|------|------|-------|
| `frontend/src/types/api.ts` | 49-50 | `BudgetVersionSchema`, `BudgetVersion` |
| `frontend/src/hooks/api/useVersions.ts` | Various | All `useBudgetVersion*` exports |
| `frontend/src/contexts/VersionContext.ts` | 41, 46, 74 | Context aliases |
| `frontend/src/contexts/VersionProvider.tsx` | 197 | `BudgetVersionProvider` |
| `frontend/src/components/VersionSelector.tsx` | 22, 93 | Component aliases |

### API Routes (Keep - External Contract)

| File | Route |
|------|-------|
| `backend/app/api/v1/configuration.py` | `/budget-versions`, `/budget-versions/{version_id}/*` |
| `backend/app/api/v1/export.py` | `/budget/{version_id}/excel`, `/budget/{version_id}/pdf`, `/budget/{version_id}/csv` |

---

## Execution Order

1. **Phase 1**: Fix F821 error (1 file, 1 change)
2. **Phase 2**: Backend schema + service changes (5 files, ~50 changes)
3. **Phase 3**: Backend API changes (3 files, ~30 changes)
4. **Phase 4**: Backend model relationship + selectinload updates (9 files, ~15 changes)
5. **Phase 5**: Frontend type/service changes (3 files, ~10 changes)
6. **Phase 6**: Frontend component/route UI messages (25+ files, ~70 changes)
7. **Phase 7**: Backend tests (25+ files, ~200 changes)
8. **Phase 8**: Frontend tests (12+ files, ~50 changes)
9. **Phase 9**: Documentation updates (8+ files, ~100 changes)
10. **Phase 10**: Run full test suite and fix any issues

---

## Verification Commands

After each phase:

```bash
# Backend
cd backend
uv run ruff check . --fix
uv run mypy app
PYTEST_RUNNING=1 uv run pytest tests/ -v --tb=short -x

# Frontend
cd frontend
pnpm lint:fix
pnpm typecheck
pnpm test -- --run
```
