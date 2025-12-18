# E2E Test Failure Analysis - 67/185 Tests Failing (36%)

**Date**: 2025-12-17
**Status**: Critical - Requires immediate attention
**Impact**: High - Blocking CI/CD and deployment confidence

---

## Executive Summary

The E2E test suite is experiencing a **36% failure rate** (67 out of 185 tests failing). The root cause is a **UI architecture refactoring** that changed the application from a 6-module flat structure to a **10-module Executive Cockpit** architecture, but the tests were not updated to match the new routes and component structure.

### Key Issues Identified

1. **Route Mismatches** - Tests reference old routes that no longer exist
2. **Sidebar Collapse State** - Elements have `opacity-0 w-0` classes when sidebar is collapsed
3. **Module Name Changes** - Old module names don't match new architecture
4. **Missing Wait States** - Tests don't account for sidebar hover animations

---

## Root Cause Analysis

### 1. Architecture Migration (Primary Cause)

**Old Architecture (6 modules)**:
- `/configuration/*` - Global settings
- `/planning/*` - All planning tasks
- `/analysis/*` - KPIs and dashboards
- `/finance/*` - Mixed financial operations
- `/enrollment/*` - Enrollment only
- `/workforce/*` - Workforce only

**New Architecture (10 modules)**:
```typescript
// From ModuleContext.tsx (lines 199-349)
export const MODULES = {
  'command-center': '/command-center',
  'enrollment': '/enrollment',      // Student projections
  'workforce': '/workforce',        // Teachers/HR
  'revenue': '/revenue',            // NEW - was /finance/revenue
  'costs': '/costs',                // NEW - was /finance/costs
  'investments': '/investments',    // NEW - was /finance/capex
  'consolidation': '/consolidation',// Budget rollup
  'insights': '/insights',          // NEW - was /analysis
  'strategic': '/strategic',        // Long-term planning
  'settings': '/settings',          // NEW - was /configuration
  'admin': '/admin'                 // System admin
}
```

### 2. Broken Route Mappings in Tests

| Old Route (in tests) | New Route (actual) | Test Files Affected |
|---------------------|-------------------|---------------------|
| `/analysis/kpis` | `/insights/kpis` | kpis.spec.ts (8 tests) |
| `/analysis/variance` | `/insights/variance` | kpis.spec.ts (7 tests) |
| `/configuration/subject-hours` | `/workforce/settings/subject-hours` | subject-hours.spec.ts (6 tests), dhg.spec.ts (1 test) |
| `/configuration/versions` | `/settings/versions` | budget-workflow.spec.ts (8 tests), accessibility.spec.ts (3 tests) |
| `/configuration/fees` | `/revenue/settings` | revenue.spec.ts (3 tests) |
| `/planning/enrollment` | `/enrollment/projections` | Multiple (12 tests) |
| `/planning/dhg` | `/workforce/dhg` | dhg.spec.ts (9 tests) |
| `/planning/revenue` | `/revenue/tuition` | revenue.spec.ts (11 tests) |
| `/planning/classes` | `/enrollment/class-structure` | dhg.spec.ts (1 test) |
| `/finance/statements` | `/consolidation/statements` | consolidation.spec.ts (7 tests) |

**Total affected**: ~67 tests

### 3. Sidebar Collapse State Issues

**Problem**: The `AppSidebar` component (lines 82-296) uses hover-to-expand behavior:

```tsx
// AppSidebar.tsx lines 97-98, 150-152
isExpanded ? 'w-[var(--sidebar-width-expanded)]' : 'w-[var(--sidebar-width-collapsed)]'

// Label visibility
isExpanded ? 'opacity-100' : 'opacity-0 w-0'
```

**Impact**: When tests try to find elements like "Configuration Overview" or "Settings", they exist in the DOM but have:
- `opacity-0` - invisible
- `w-0` - zero width
- Parent sidebar is only 64px collapsed vs 240px expanded

**Error Pattern**:
```
Error: expect(locator).toBeVisible() failed
Locator: locator('text=/Configuration Overview|Settings/i').first()
Expected: visible
Received: hidden
- unexpected value "hidden"
```

### 4. Missing Animation Waits

The sidebar has a 200ms expand animation (line 110):
```tsx
style={{
  transitionDuration: LAYOUT.sidebarAnimationDuration, // 200ms
}}
```

Tests that hover over the sidebar don't wait for this animation:
```tsx
// navigation.spec.ts lines 68-70 - GOOD example
await sidebar.hover()
await page.waitForTimeout(300) // Wait for expand animation

// But many tests don't have this wait
```

---

## Failure Categories

### Category A: Route Mismatches (HIGH PRIORITY)
**Count**: 50+ tests
**Severity**: Critical - Tests navigate to non-existent routes

**Examples**:
- `kpis.spec.ts`: All tests use `/analysis/*` instead of `/insights/*`
- `dhg.spec.ts`: Uses `/planning/dhg` instead of `/workforce/dhg`
- `revenue.spec.ts`: Uses `/planning/revenue` instead of `/revenue/tuition`

**Fix**: Update all route references in test files

### Category B: Sidebar Visibility Issues (MEDIUM PRIORITY)
**Count**: 12+ tests
**Severity**: High - Tests fail on element visibility checks

**Examples**:
- `navigation.spec.ts`: "sidebar displays all modules" - tries to read module labels without hovering
- `subject-hours.spec.ts`: Looks for "Configuration Overview" text that's hidden

**Fix**: Add hover waits and update selectors to use `aria-label` instead of text content

### Category C: Module Name Mismatches (LOW PRIORITY)
**Count**: 5+ tests
**Severity**: Medium - Tests look for old module names

**Examples**:
- Looking for "Finance" module button when it's now split into "Revenue", "Costs", "Investments"
- Looking for "Analysis" module when it's now "Insights"
- Looking for "Configuration" module when it's now "Settings"

**Fix**: Update test assertions to use new module names

### Category D: Mobile Navigation Tests (LOW PRIORITY)
**Count**: 3+ tests
**Severity**: Low - Mobile drawer tests may need updates

**Fix**: Verify mobile drawer still works with new architecture

---

## Proposed Fix Strategy

### Phase 1: Route Migration (IMMEDIATE - Day 1)

**Effort**: 4 hours
**Impact**: Fixes ~50 tests (75% of failures)

Create a route migration helper:

```typescript
// tests/e2e/helpers/route-migration.helper.ts
export const ROUTE_MIGRATIONS: Record<string, string> = {
  '/analysis/kpis': '/insights/kpis',
  '/analysis/variance': '/insights/variance',
  '/configuration/subject-hours': '/workforce/settings/subject-hours',
  '/configuration/versions': '/settings/versions',
  '/configuration/fees': '/revenue/settings',
  '/planning/enrollment': '/enrollment/projections',
  '/planning/dhg': '/workforce/dhg',
  '/planning/revenue': '/revenue/tuition',
  '/planning/classes': '/enrollment/class-structure',
  '/finance/statements': '/consolidation/statements',
}

export function migrateRoute(oldRoute: string): string {
  return ROUTE_MIGRATIONS[oldRoute] || oldRoute
}
```

Then use find-and-replace:
```bash
# Example for kpis.spec.ts
sed -i '' "s|'/analysis/kpis'|'/insights/kpis'|g" tests/e2e/kpis.spec.ts
sed -i '' "s|'/analysis/variance'|'/insights/variance'|g" tests/e2e/kpis.spec.ts
```

### Phase 2: Sidebar Interaction Fixes (Day 2)

**Effort**: 3 hours
**Impact**: Fixes ~12 tests

Update `navigation.spec.ts` and other sidebar tests:

```typescript
// Before
await expect(sidebar.locator('[aria-label="Enrollment"]')).toBeVisible()

// After
async function expandSidebar(page: Page, sidebar: Locator) {
  await sidebar.hover()
  await page.waitForTimeout(300) // Wait for expand animation
}

// Usage
await expandSidebar(page, sidebar)
await expect(sidebar.locator('[aria-label="Enrollment"]')).toBeVisible()
```

Use `aria-label` selectors instead of text content:
```typescript
// Before - FAILS when sidebar collapsed
const enrollmentButton = sidebar.locator('text=Enrollment')

// After - WORKS even when collapsed
const enrollmentButton = sidebar.locator('[aria-label="Enrollment"]')
```

### Phase 3: Module Name Updates (Day 3)

**Effort**: 2 hours
**Impact**: Fixes ~5 tests

Update module name assertions:

```typescript
// Before
const modules = ['Enrollment', 'Workforce', 'Finance', 'Analysis', 'Strategic', 'Configuration']

// After
const modules = [
  'Enrollment',
  'Workforce',
  'Revenue',     // was part of Finance
  'Costs',       // was part of Finance
  'Investments', // was part of Finance
  'Consolidation',
  'Insights',    // was Analysis
  'Strategic',
  'Settings',    // was Configuration
]
```

### Phase 4: Test Infrastructure Improvements (Day 4)

**Effort**: 3 hours
**Impact**: Prevents future regressions

1. **Create shared navigation helpers**:
```typescript
// tests/e2e/helpers/navigation.helper.ts
export async function navigateToModule(page: Page, moduleId: ModuleId) {
  const module = MODULES[moduleId]
  await page.goto(module.basePath)
  await page.waitForLoadState('networkidle')
}

export async function expandSidebarAndClick(
  page: Page,
  moduleLabel: string
) {
  const sidebar = page.locator('aside[role="navigation"]')
  await sidebar.hover()
  await page.waitForTimeout(300)
  await sidebar.locator(`[aria-label="${moduleLabel}"]`).click()
}
```

2. **Add route validation test**:
```typescript
test('all module routes are accessible', async ({ page }) => {
  for (const [moduleId, module] of Object.entries(MODULES)) {
    if (moduleId === 'admin') continue // Skip admin for non-admin user

    await page.goto(module.basePath)
    await expect(page).toHaveURL(new RegExp(module.basePath))
  }
})
```

---

## Quick Wins (Can be done in parallel)

### Fix 1: Update kpis.spec.ts (15 minutes)
```bash
cd tests/e2e
sed -i '' "s|'/analysis/kpis'|'/insights/kpis'|g" kpis.spec.ts
sed -i '' "s|'/analysis/variance'|'/insights/variance'|g" kpis.spec.ts
```
**Impact**: Fixes 15 tests immediately

### Fix 2: Update dhg.spec.ts (15 minutes)
```bash
sed -i '' "s|'/planning/dhg'|'/workforce/dhg'|g" dhg.spec.ts
sed -i '' "s|'/planning/classes'|'/enrollment/class-structure'|g" dhg.spec.ts
sed -i '' "s|'/configuration/subject-hours'|'/workforce/settings/subject-hours'|g" dhg.spec.ts
```
**Impact**: Fixes 11 tests

### Fix 3: Update revenue.spec.ts (15 minutes)
```bash
sed -i '' "s|'/planning/revenue'|'/revenue/tuition'|g" revenue.spec.ts
sed -i '' "s|'/configuration/fees'|'/revenue/settings'|g" revenue.spec.ts
```
**Impact**: Fixes 14 tests

### Fix 4: Update budget-workflow.spec.ts (10 minutes)
```bash
sed -i '' "s|'/configuration/versions'|'/settings/versions'|g" budget-workflow.spec.ts
```
**Impact**: Fixes 8 tests

### Fix 5: Update consolidation.spec.ts (10 minutes)
```bash
sed -i '' "s|'/finance/statements'|'/consolidation/statements'|g" consolidation.spec.ts
```
**Impact**: Fixes 7 tests

**Total Quick Win Impact**: 55 tests fixed in 65 minutes

---

## Recommended Execution Plan

### Sprint 1 (Day 1-2): Emergency Fixes
**Goal**: Get to 90% pass rate

1. Run all Quick Wins (1 hour)
2. Update navigation.spec.ts sidebar tests (2 hours)
3. Update accessibility.spec.ts routes (1 hour)
4. Run full test suite and verify fixes

**Expected outcome**: 60+ tests fixed, <10 failures remaining

### Sprint 2 (Day 3-4): Test Infrastructure
**Goal**: Prevent future regressions

1. Create navigation helper utilities
2. Add route validation tests
3. Document test patterns in TESTING.md
4. Add pre-commit hook to run E2E smoke tests

### Sprint 3 (Week 2): Continuous Improvement
**Goal**: Maintain test health

1. Add test coverage for new modules
2. Create visual regression tests for sidebar animations
3. Add performance benchmarks
4. Document testing best practices

---

## Files That Need Changes

### High Priority (Route Updates)
- `tests/e2e/kpis.spec.ts` - 15 route updates
- `tests/e2e/dhg.spec.ts` - 11 route updates
- `tests/e2e/revenue.spec.ts` - 14 route updates
- `tests/e2e/budget-workflow.spec.ts` - 8 route updates
- `tests/e2e/consolidation.spec.ts` - 7 route updates
- `tests/e2e/accessibility.spec.ts` - 4 route updates
- `tests/e2e/subject-hours.spec.ts` - 3 route updates

### Medium Priority (Sidebar Interactions)
- `tests/e2e/navigation.spec.ts` - Add hover waits, update module names
- `tests/e2e/helpers/api-mock.helper.ts` - Update API route mocks

### Low Priority (Infrastructure)
- `tests/e2e/helpers/navigation.helper.ts` - CREATE NEW
- `tests/e2e/helpers/route-migration.helper.ts` - CREATE NEW
- `docs/TESTING.md` - UPDATE with new patterns

---

## Risk Assessment

### Risks if Not Fixed
- **High Risk**: False confidence in UI functionality
- **Medium Risk**: Delayed feature releases due to test failures
- **Low Risk**: Developer friction ("tests are flaky, ignore them")

### Risks During Fix
- **Low Risk**: Breaking working tests during refactor
  - *Mitigation*: Test changes in isolation, run after each file update
- **Medium Risk**: Missing edge cases in new architecture
  - *Mitigation*: Manual smoke testing alongside automated fixes

---

## Success Metrics

- [ ] Pass rate > 95% (< 10 failures out of 185 tests)
- [ ] All Quick Wins completed and verified
- [ ] Navigation helper utilities created and documented
- [ ] No flaky tests (3 consecutive successful runs)
- [ ] Test execution time < 5 minutes (currently ~7 minutes)

---

## Next Steps

1. **IMMEDIATE**: Execute Quick Wins (65 minutes)
2. **Day 1**: Verify fixes with full test run
3. **Day 2**: Fix remaining navigation/sidebar tests
4. **Day 3**: Create infrastructure improvements
5. **Week 2**: Add comprehensive documentation

---

## Appendix: Detailed Route Mapping

### Complete Old → New Route Map

```typescript
// Enrollment Module
'/planning/enrollment' → '/enrollment/projections'
'/planning/classes' → '/enrollment/class-structure'

// Workforce Module
'/planning/dhg' → '/workforce/dhg'
'/configuration/subject-hours' → '/workforce/settings/subject-hours'

// Revenue Module (NEW)
'/planning/revenue' → '/revenue/tuition'
'/configuration/fees' → '/revenue/settings'

// Costs Module (NEW)
// No old routes (new module)

// Investments Module (NEW)
'/finance/capex' → '/investments/capex'

// Consolidation Module
'/finance/statements' → '/consolidation/statements'
'/consolidation/budget' → '/consolidation/rollup'

// Insights Module
'/analysis/kpis' → '/insights/kpis'
'/analysis/variance' → '/insights/variance'
'/analysis/dashboards' → '/insights/reports'

// Settings Module
'/configuration/versions' → '/settings/versions'
'/configuration/system' → '/settings/system'

// Admin Module
'/admin/historical-import' → '/admin/uploads' (unchanged)
```

### API Route Changes

The API routes in `helpers/api-mock.helper.ts` also need updates:

```typescript
// Old API routes (in mocks)
'/planning/enrollment' → Still valid (backend not refactored yet)
'/planning/dhg' → Still valid
'/configuration/*' → Still valid
'/analysis/*' → Still valid

// Note: Backend API routes haven't changed yet
// This is a frontend-only refactoring
// API mocks are still correct
```

---

## Conclusion

The E2E test failures are **entirely fixable** with systematic route updates and minor test pattern improvements. The root cause is well-understood (architecture refactoring), and the fixes are straightforward (find-and-replace + helper utilities).

**Estimated total effort**: 12 hours over 2-3 days
**Expected outcome**: 95%+ pass rate, robust test infrastructure

**Recommendation**: Execute Quick Wins immediately to unblock CI/CD, then complete infrastructure improvements over the next week.
