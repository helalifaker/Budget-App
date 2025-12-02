# E2E Testing Guide - EFIR Budget Planning Application

## Overview

This document provides comprehensive guidance on End-to-End (E2E) testing for the EFIR Budget Planning Application using **Playwright 1.49.x**.

## Table of Contents

1. [Test Infrastructure](#test-infrastructure)
2. [Test Organization](#test-organization)
3. [Running Tests](#running-tests)
4. [Writing Tests](#writing-tests)
5. [Test Coverage](#test-coverage)
6. [Best Practices](#best-practices)
7. [Troubleshooting](#troubleshooting)
8. [CI/CD Integration](#cicd-integration)

---

## Test Infrastructure

### Technology Stack

- **Playwright 1.49.x**: Modern E2E testing framework
- **TypeScript 5.9.x**: Type-safe test code
- **@axe-core/playwright 4.11.x**: Accessibility testing
- **Test Runner**: Playwright Test (built-in)

### Project Structure

```
frontend/tests/e2e/
├── fixtures/
│   └── test-data.ts           # Reusable test data
├── helpers/
│   ├── auth.helper.ts          # Authentication helpers
│   ├── navigation.helper.ts    # Navigation utilities
│   └── grid.helper.ts          # AG Grid interactions
├── pages/
│   ├── BasePage.ts             # Base Page Object Model
│   ├── EnrollmentPage.ts       # Enrollment page POM
│   └── BudgetVersionPage.ts    # Budget version POM
├── auth.spec.ts                # Authentication tests
├── budget-workflow.spec.ts     # Budget workflow tests
├── dhg.spec.ts                 # DHG workforce planning tests
├── consolidation.spec.ts       # Budget consolidation tests
├── revenue.spec.ts             # Revenue calculation tests
├── kpis.spec.ts                # KPI dashboard tests
├── strategic.spec.ts           # 5-year strategic planning tests
├── integrations.spec.ts        # External integrations tests
└── accessibility.spec.ts       # WCAG 2.1 AA compliance tests
```

---

## Test Organization

### Test Suites

#### 1. Authentication Tests (`auth.spec.ts`)
- Login with valid/invalid credentials
- Logout functionality
- Session persistence
- Protected route guards
- Role-based access control (RBAC)

#### 2. Budget Workflow Tests (`budget-workflow.spec.ts`)
- Create budget version
- Plan enrollment and classes
- Submit for approval
- Approve budget
- Budget version state transitions
- Copy and compare versions

#### 3. DHG Workforce Planning Tests (`dhg.spec.ts`)
- Subject hours → FTE calculation
- Primary (24h) vs Secondary (18h) teaching hours
- HSA (overtime) calculation and limits
- AEFE vs Local teacher costs
- TRMD gap analysis
- H/E ratio validation
- Export DHG to Excel

#### 4. Budget Consolidation Tests (`consolidation.spec.ts`)
- Consolidate budget totals
- Revenue consolidation from all sources
- Expense consolidation by account code
- Period-based consolidation (T1, T2, T3)
- Financial statement generation (PCG & IFRS)
- Balance sheet equation validation
- Export to Excel/PDF

#### 5. Revenue Planning Tests (`revenue.spec.ts`)
- Configure fee structure by nationality and level
- Calculate revenue from enrollment
- Trimester distribution (40%, 30%, 30%)
- Sibling discount application
- Revenue breakdown by nationality and level
- Account code mapping (PCG 70xxx)
- Other revenue sources (cafeteria, transport)

#### 6. KPI Dashboard Tests (`kpis.spec.ts`)
- Enrollment capacity utilization
- H/E ratio (hours per student)
- E/D ratio (students per class)
- Operating margin
- FTE vs enrollment trends
- Revenue vs expense charts
- KPI target comparison
- Variance analysis

#### 7. Strategic Planning Tests (`strategic.spec.ts`)
- Create 5-year strategic plan
- Configure growth scenarios (conservative, base, optimistic)
- 5-year enrollment projections
- Revenue and expense projections
- CapEx investment planning
- Workforce FTE growth
- Cash flow projections
- Sensitivity analysis

#### 8. Integration Tests (`integrations.spec.ts`)
- Odoo connection and import
- Skolengo enrollment sync
- AEFE position file import
- PRRD rate configuration
- Account mapping
- Import history and retries

#### 9. Accessibility Tests (`accessibility.spec.ts`)
- WCAG 2.1 AA compliance (axe-core)
- Keyboard navigation
- Screen reader support
- Color contrast validation
- Focus indicators
- Mobile accessibility

---

## Running Tests

### Quick Start

```bash
cd frontend

# Run all E2E tests
pnpm test:e2e

# Run in headed mode (see browser)
pnpm test:e2e:headed

# Run in UI mode (interactive)
pnpm test:e2e:ui

# Run in debug mode
pnpm test:e2e:debug

# View test report
pnpm test:e2e:report
```

### Running Specific Test Suites

```bash
# Run only authentication tests
pnpm playwright test auth.spec.ts

# Run only accessibility tests
pnpm playwright test accessibility.spec.ts

# Run tests matching a pattern
pnpm playwright test --grep "DHG"

# Run tests excluding a pattern
pnpm playwright test --grep-invert "accessibility"
```

### Running Individual Tests

```bash
# Run specific test by name
pnpm playwright test -g "login with valid credentials"

# Run specific file and test
pnpm playwright test auth.spec.ts -g "logout successfully"
```

### Configuration Options

```bash
# Run tests in parallel (default)
pnpm playwright test --workers=4

# Run tests in serial
pnpm playwright test --workers=1

# Run with different browser
pnpm playwright test --project=firefox
pnpm playwright test --project=webkit

# Generate trace files
pnpm playwright test --trace on

# Update snapshots
pnpm playwright test --update-snapshots
```

---

## Writing Tests

### Basic Test Structure

```typescript
import { test, expect } from '@playwright/test';
import { login } from './helpers/auth.helper';

test.describe('Feature Name', () => {
  test.beforeEach(async ({ page }) => {
    // Setup (e.g., login)
    await login(page, 'manager');
  });

  test('should do something', async ({ page }) => {
    // Arrange
    await page.goto('/some-route');

    // Act
    await page.click('button:has-text("Submit")');

    // Assert
    await expect(page.locator('text=/success/i')).toBeVisible();
  });
});
```

### Using Test Fixtures

```typescript
import { TEST_USERS, TEST_BUDGET_VERSION } from './fixtures/test-data';

test('use test data', async ({ page }) => {
  const user = TEST_USERS.manager;
  await page.fill('[name="email"]', user.email);

  const budgetName = TEST_BUDGET_VERSION.name;
  await page.fill('[name="name"]', budgetName);
});
```

### Using Helpers

```typescript
import { login, logout } from './helpers/auth.helper';
import { selectBudgetVersion, navigateTo } from './helpers/navigation.helper';
import { getGridRow, editGridCell } from './helpers/grid.helper';

test('use helpers', async ({ page }) => {
  // Authentication
  await login(page, 'manager');

  // Navigation
  await navigateTo(page, '/planning/enrollment');
  await selectBudgetVersion(page, /2025/);

  // AG Grid interaction
  await editGridCell(page, 0, 'student_count', '30');

  // Cleanup
  await logout(page);
});
```

### Using Page Object Model

```typescript
import { EnrollmentPage } from './pages/EnrollmentPage';
import { BudgetVersionPage } from './pages/BudgetVersionPage';

test('use page objects', async ({ page }) => {
  const enrollmentPage = new EnrollmentPage(page);

  await enrollmentPage.navigate();
  await enrollmentPage.selectVersion('Test Budget 2025');
  await enrollmentPage.addEnrollment('6ème', 'French', 25);
  await enrollmentPage.waitForSuccess();
});
```

### Accessibility Testing

```typescript
import AxeBuilder from '@axe-core/playwright';

test('accessibility', async ({ page }) => {
  await page.goto('/dashboard');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();

  expect(results.violations).toEqual([]);
});
```

---

## Test Coverage

### Critical User Flows (Must Have 100% Coverage)

1. **Budget Lifecycle**:
   - Create budget version
   - Add enrollment → Calculate classes → Calculate DHG → Submit → Approve

2. **Financial Calculations**:
   - Enrollment projections
   - Class formation with constraints
   - DHG hours and FTE calculation
   - Revenue calculation with fees and discounts
   - Budget consolidation

3. **Data Integrity**:
   - Revenue = Sum of all revenue streams
   - Expenses = Sum of all expense accounts
   - Balance Sheet: Assets = Liabilities + Equity

4. **Integrations**:
   - Odoo actuals import
   - Skolengo enrollment sync
   - AEFE position data

5. **Accessibility**:
   - WCAG 2.1 AA compliance
   - Keyboard navigation
   - Screen reader support

### Coverage Goals

- **End-to-End Tests**: All 18 modules covered
- **Critical Paths**: 100% coverage
- **User Workflows**: All user roles tested (Admin, Manager, User, HR, Academic)
- **WCAG Compliance**: All pages tested with axe-core

### Running Coverage Report

```bash
# Generate coverage report
pnpm test:e2e --coverage

# View HTML coverage report
open playwright-report/index.html
```

---

## Best Practices

### 1. Test Independence

✅ **DO**:
```typescript
test.beforeEach(async ({ page }) => {
  // Each test starts fresh
  await login(page, 'manager');
  const uniqueName = `Test ${Date.now()}`;
});
```

❌ **DON'T**:
```typescript
// Don't rely on previous test state
let sharedBudgetName; // Bad - tests depend on each other
```

### 2. Explicit Waits

✅ **DO**:
```typescript
await expect(page.locator('text=/success/i')).toBeVisible({ timeout: 5000 });
await page.waitForLoadState('networkidle');
```

❌ **DON'T**:
```typescript
await page.waitForTimeout(5000); // Bad - arbitrary wait
```

### 3. Resilient Selectors

✅ **DO**:
```typescript
// Use data-testid for test-specific selectors
await page.click('[data-testid="submit-button"]');

// Use semantic selectors
await page.click('button:has-text("Submit")');

// Use ARIA roles
await page.click('button[role="button"]');
```

❌ **DON'T**:
```typescript
// Avoid fragile CSS selectors
await page.click('.btn.btn-primary.mt-4'); // Bad - breaks with style changes
```

### 4. Test Data Management

✅ **DO**:
```typescript
// Use fixtures for reusable data
import { TEST_ENROLLMENT_DATA } from './fixtures/test-data';

// Generate unique names
const uniqueName = generateTestBudgetName();
```

❌ **DON'T**:
```typescript
// Don't hardcode test data
await page.fill('[name="name"]', 'Test Budget'); // Bad - may conflict
```

### 5. Error Handling

✅ **DO**:
```typescript
const button = page.locator('button:has-text("Submit")');
if (await button.isVisible()) {
  await button.click();
} else {
  console.log('Submit button not found, skipping...');
}
```

❌ **DON'T**:
```typescript
// Don't assume elements exist
await page.click('button:has-text("Submit")'); // May fail if not present
```

### 6. Cleanup

✅ **DO**:
```typescript
test.afterEach(async ({ page }) => {
  // Clean up test data
  await deleteTestBudget(page, testBudgetName);
});
```

---

## Troubleshooting

### Common Issues

#### 1. Test Timeout

**Problem**: Test times out waiting for element

**Solution**:
```typescript
// Increase timeout for slow operations
await expect(page.locator('text=/success/i')).toBeVisible({ timeout: 30000 });

// Wait for network to settle
await page.waitForLoadState('networkidle');
```

#### 2. Element Not Found

**Problem**: Cannot find element

**Solution**:
```typescript
// Check element existence before interacting
const element = page.locator('button:has-text("Submit")');
if (await element.isVisible()) {
  await element.click();
}

// Use flexible selectors
const button = page.locator('button').filter({ hasText: /submit|save/i });
```

#### 3. Flaky Tests

**Problem**: Test passes sometimes, fails other times

**Solution**:
```typescript
// Use auto-waiting built into Playwright
await page.click('button'); // Automatically waits for element

// Retry failed tests (in playwright.config.ts)
retries: process.env.CI ? 2 : 0
```

#### 4. Authentication Issues

**Problem**: Tests fail due to authentication

**Solution**:
```typescript
// Use authentication helpers
await login(page, 'manager');

// Check authentication status
const isAuth = await isAuthenticated(page);
if (!isAuth) {
  await login(page, 'manager');
}
```

### Debugging Tests

```bash
# Run test in debug mode
pnpm test:e2e:debug

# Generate trace
pnpm playwright test --trace on

# View trace
pnpm playwright show-trace trace.zip

# Run with console logs
DEBUG=pw:api pnpm test:e2e

# Take screenshot on failure (automatic in playwright.config.ts)
screenshot: 'only-on-failure'
```

---

## CI/CD Integration

### GitHub Actions Example

```yaml
name: E2E Tests

on: [push, pull_request]

jobs:
  e2e-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '20'

      - name: Install pnpm
        run: npm install -g pnpm

      - name: Install dependencies
        run: pnpm install

      - name: Install Playwright browsers
        run: pnpm playwright install --with-deps

      - name: Run E2E tests
        run: pnpm test:e2e

      - name: Upload test report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
```

### Pre-commit Hook (with Husky)

Already configured in `package.json`:

```json
"lint-staged": {
  "*.{ts,tsx}": [
    "eslint --fix",
    "prettier --write"
  ]
}
```

To add E2E smoke tests to pre-push:

```bash
# .husky/pre-push
#!/bin/sh
pnpm playwright test --grep "@smoke"
```

---

## Metrics & Reporting

### Test Execution Time

Monitor test execution time to identify slow tests:

```bash
# Run with reporter that shows timing
pnpm playwright test --reporter=html
```

### Test Results

View comprehensive test results:

```bash
# Generate HTML report
pnpm test:e2e --reporter=html

# View report
pnpm test:e2e:report
```

### Coverage Tracking

Track E2E test coverage over time:

- Monitor number of tests per module
- Track critical path coverage
- Measure WCAG compliance coverage
- Review test execution trends

---

## Checklist for New E2E Tests

Before submitting new E2E tests, ensure:

- [ ] Test uses helpers and fixtures (no hardcoded data)
- [ ] Test is independent (can run in isolation)
- [ ] Test uses explicit waits (no arbitrary timeouts)
- [ ] Test uses resilient selectors (data-testid or semantic)
- [ ] Test has proper assertions (not just navigation checks)
- [ ] Test cleans up after itself (if creating data)
- [ ] Test follows AAA pattern (Arrange, Act, Assert)
- [ ] Test name clearly describes what is being tested
- [ ] Test is grouped in appropriate describe block
- [ ] Test passes locally 3 times in a row
- [ ] Test has been reviewed for best practices

---

## Resources

- [Playwright Documentation](https://playwright.dev/docs/intro)
- [Playwright Best Practices](https://playwright.dev/docs/best-practices)
- [Axe Accessibility Testing](https://www.deque.com/axe/core-documentation/api-documentation/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [AG Grid Testing Guide](https://www.ag-grid.com/react-data-grid/testing/)

---

## Support

For questions or issues with E2E tests:

1. Check this documentation first
2. Review existing test examples
3. Check Playwright documentation
4. Create an issue in the repository

---

**Last Updated**: December 2025
**Version**: 1.0
**Maintainer**: QA Validation Agent
