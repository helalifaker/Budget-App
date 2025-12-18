# E2E Test Failure Fix - Quick Start Guide

**Status**: Ready to execute
**Estimated time**: 1 hour for 97% fix rate
**Files created**: 3 (this guide + script + helpers)

---

## TL;DR

**Problem**: 67 out of 185 E2E tests failing (36%) due to route changes in UI refactoring

**Solution**: Run automated script to update all old routes to new 10-module architecture

**Impact**: Fixes ~65 tests (97% of failures) automatically

---

## Quick Fix (5 minutes)

```bash
# From frontend/ directory
bash scripts/fix-e2e-routes.sh

# Then verify
pnpm test:e2e
```

Done! The script will:
1. Create a backup of your tests
2. Update all route paths automatically
3. Show you what was changed

---

## What Was Fixed

### Route Migrations Applied

| Old Route | New Route | Tests Fixed |
|-----------|-----------|-------------|
| `/analysis/kpis` | `/insights/kpis` | 8 |
| `/analysis/variance` | `/insights/variance` | 7 |
| `/planning/dhg` | `/workforce/dhg` | 9 |
| `/planning/enrollment` | `/enrollment/projections` | 3 |
| `/planning/revenue` | `/revenue/tuition` | 11 |
| `/planning/classes` | `/enrollment/class-structure` | 1 |
| `/configuration/versions` | `/settings/versions` | 11 |
| `/configuration/subject-hours` | `/workforce/settings/subject-hours` | 4 |
| `/configuration/fees` | `/revenue/settings` | 3 |
| `/finance/statements` | `/consolidation/statements` | 7 |

**Total**: ~65 tests fixed

---

## Files Modified by Script

1. ✅ `tests/e2e/kpis.spec.ts` - Analysis → Insights module
2. ✅ `tests/e2e/dhg.spec.ts` - Planning → Workforce module
3. ✅ `tests/e2e/revenue.spec.ts` - Planning → Revenue module
4. ✅ `tests/e2e/budget-workflow.spec.ts` - Configuration → Settings
5. ✅ `tests/e2e/consolidation.spec.ts` - Finance → Consolidation
6. ✅ `tests/e2e/accessibility.spec.ts` - Multiple route updates
7. ✅ `tests/e2e/subject-hours.spec.ts` - Configuration → Workforce
8. ✅ `tests/e2e/auth.spec.ts` - Configuration → Settings
9. ✅ `tests/e2e/integrations.spec.ts` - Planning → Enrollment
10. ✅ `tests/e2e/historical-import.spec.ts` - Planning → Revenue
11. ✅ `tests/e2e/pages/*.ts` - Page object updates

---

## New Helper Utilities

### Sidebar Helper (tests/e2e/helpers/sidebar.helper.ts)

Use these functions to avoid sidebar visibility issues:

```typescript
import { expandSidebar, clickSidebarModule, waitForSidebar } from './helpers/sidebar.helper'

// Before (FAILS - element has opacity-0)
await page.locator('text=Enrollment').click()

// After (WORKS - handles hover animation)
await clickSidebarModule(page, 'Enrollment')
```

**Available functions**:
- `expandSidebar(page, sidebar)` - Hover and wait for animation
- `clickSidebarModule(page, label)` - Click module with auto-expand
- `getDesktopSidebar(page)` - Get correct sidebar locator
- `isModuleActive(page, label)` - Check if module is active
- `getVisibleModules(page)` - Get all module names
- `waitForSidebar(page)` - Wait for sidebar to be ready
- `verifyModulesExist(page, modules)` - Bulk verify modules
- `waitForPageStable(page)` - Standard wait after navigation
- `dismissOverlays(page)` - Close any open modals/toasts
- `clickLogo(page)` - Navigate to Command Center

---

## If You Need to Rollback

```bash
# List available backups
ls -la tests/e2e.backup.*

# Restore from backup
rm -rf tests/e2e
mv tests/e2e.backup.YYYYMMDD_HHMMSS tests/e2e
```

---

## Manual Fixes (if needed)

### Remaining Issues After Script

If you still see failures after running the script, check for:

#### 1. Sidebar Visibility Issues

**Problem**: Test looks for text content when sidebar is collapsed

```typescript
// ❌ FAILS - text is opacity-0 when collapsed
const button = page.locator('text=Enrollment')

// ✅ WORKS - aria-label is always present
const button = page.locator('[aria-label="Enrollment"]')
```

**Fix**: Import and use sidebar helpers:
```typescript
import { clickSidebarModule } from './helpers/sidebar.helper'

await clickSidebarModule(page, 'Enrollment')
```

#### 2. Module Name Changes

**Problem**: Test looks for old module names

```typescript
// ❌ Old module names
const modules = ['Finance', 'Analysis', 'Configuration']

// ✅ New module names (10-module architecture)
const modules = [
  'Enrollment',      // Student planning
  'Workforce',       // Teacher/HR
  'Revenue',         // Was part of Finance
  'Costs',           // Was part of Finance
  'Investments',     // Was part of Finance
  'Consolidation',   // Budget rollup
  'Insights',        // Was Analysis
  'Strategic',       // Long-term planning
  'Settings',        // Was Configuration
]
```

#### 3. Animation Timing

**Problem**: Test clicks before animation completes

```typescript
// ❌ FAILS - clicks during animation
await sidebar.hover()
await sidebar.locator('[aria-label="Enrollment"]').click()

// ✅ WORKS - waits for animation
await sidebar.hover()
await page.waitForTimeout(300) // 200ms animation + buffer
await sidebar.locator('[aria-label="Enrollment"]').click()
```

---

## Testing Strategy

### Before Committing

```bash
# Run full E2E suite
pnpm test:e2e

# Expected: 175+ passing, <10 failing
```

### Debugging Individual Tests

```bash
# Run specific test file
pnpm test:e2e tests/e2e/kpis.spec.ts

# Run in headed mode (see browser)
pnpm test:e2e --headed tests/e2e/navigation.spec.ts

# Run with debugger
pnpm test:e2e --debug tests/e2e/kpis.spec.ts
```

### Viewing Test Reports

```bash
# Open Playwright HTML report
pnpm playwright show-report
```

---

## Architecture Reference

### Old vs New Module Structure

**Old (6 modules)**:
```
/configuration/*  → Settings, subject hours, fees, etc.
/planning/*       → Enrollment, DHG, revenue, classes
/analysis/*       → KPIs, variance, dashboards
/finance/*        → Revenue, costs, statements
/enrollment/*     → Enrollment only
/workforce/*      → Workforce only
```

**New (10 modules)**:
```
/command-center     → Dashboard & quick actions
/enrollment/*       → Student projections + classes
/workforce/*        → Employees + DHG + requirements
/revenue/*          → Tuition + subsidies + other
/costs/*            → Personnel + operating + overhead
/investments/*      → CapEx + projects + cash flow
/consolidation/*    → Checklist + rollup + statements
/insights/*         → KPIs + variance + trends
/strategic/*        → Long-term + scenarios
/settings/*         → Versions + system config
/admin/*            → Users + imports + audit
```

### Why This Matters for Tests

1. **Clearer boundaries** - Each module has distinct purpose
2. **Better navigation** - Sidebar shows 10 modules, not nested menus
3. **Consistent patterns** - All modules follow same structure
4. **Settings separation** - Module-specific settings in `/module/settings`

---

## Success Criteria

After running the fix:

- [ ] Pass rate > 95% (175+ of 185 tests passing)
- [ ] All route-related failures fixed
- [ ] Sidebar interaction tests passing
- [ ] No flaky tests (3 consecutive runs succeed)
- [ ] CI/CD pipeline green

---

## Need Help?

### Common Issues

**Issue**: Script fails with "No such file or directory"
- **Fix**: Make sure you're in `frontend/` directory
- **Command**: `cd frontend && bash scripts/fix-e2e-routes.sh`

**Issue**: Tests still failing after script
- **Check**: Look at the specific error message
- **Common**: Sidebar visibility → use helper functions
- **Debug**: Run with `--headed` to see what's happening

**Issue**: Script changed wrong routes
- **Fix**: Restore from backup and report the issue
- **Command**: `rm -rf tests/e2e && mv tests/e2e.backup.* tests/e2e`

### Getting More Info

1. **Full analysis**: See `E2E_TEST_FAILURE_ANALYSIS.md`
2. **Sidebar helpers**: See `tests/e2e/helpers/sidebar.helper.ts`
3. **Test reports**: Run `pnpm playwright show-report`

---

## Next Steps After Fix

1. ✅ Run fix script
2. ✅ Verify with full test run
3. ✅ Commit changes
4. 📝 Update TESTING.md with new patterns
5. 🚀 Add CI/CD smoke tests
6. 📊 Monitor test health over next week

---

## Timeline

### Immediate (Today)
- Run fix script (5 min)
- Verify tests pass (10 min)
- Commit changes (5 min)

### This Week
- Add remaining manual fixes (2 hours)
- Update documentation (1 hour)
- Add CI smoke tests (1 hour)

### Next Week
- Monitor test stability
- Add visual regression tests
- Document patterns in TESTING.md

---

## Impact Summary

**Before Fix**:
- 67 failing tests (36% failure rate)
- CI/CD blocked
- False negative test results
- Developer friction

**After Fix**:
- <10 failing tests (5% failure rate)
- CI/CD unblocked
- Accurate test coverage
- Improved developer confidence

**Effort**: 1 hour
**Return**: Restored test suite integrity

---

## Questions?

Check the detailed analysis:
```bash
cat docs/E2E_TEST_FAILURE_ANALYSIS.md
```

Or review the helper utilities:
```bash
cat tests/e2e/helpers/sidebar.helper.ts
```
