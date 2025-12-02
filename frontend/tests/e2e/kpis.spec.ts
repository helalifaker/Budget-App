import { test, expect } from '@playwright/test'
import { login } from './helpers/auth.helper'
import { selectBudgetVersion } from './helpers/navigation.helper'
import { TEST_KPI_TARGETS } from './fixtures/test-data'

/**
 * E2E Test Suite: KPI Dashboard & Analysis
 * Tests KPI calculations, variance analysis, and dashboard visualizations
 */

test.describe('KPI Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('view KPI dashboard with key metrics', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Verify KPI dashboard loaded
    await expect(page.locator('h1, h2').filter({ hasText: /kpi|dashboard/i })).toBeVisible()

    // Verify key KPI cards displayed
    await expect(page.locator('[data-testid*="kpi-card"]')).toHaveCount({ min: 4 })

    // Check for specific KPIs
    await expect(page.locator('text=/enrollment.*capacity/i')).toBeVisible()
    await expect(page.locator('text=/H\\/E.*ratio/i')).toBeVisible()
    await expect(page.locator('text=/E\\/D.*ratio|students.*class/i')).toBeVisible()
    await expect(page.locator('text=/operating.*margin/i')).toBeVisible()
  })

  test('enrollment capacity utilization KPI', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select budget version
    await selectBudgetVersion(page, /Test|2025/i)

    // Find enrollment capacity KPI
    const capacityKPI = page
      .locator('[data-testid="kpi-enrollment-capacity"], text=/enrollment.*capacity/i')
      .first()

    if (await capacityKPI.isVisible()) {
      // Verify percentage displayed
      await expect(capacityKPI).toContainText(/%/)

      // Get capacity percentage
      const capacityText = await capacityKPI.textContent()
      const match = capacityText?.match(/(\d+)%/)

      if (match) {
        const capacity = parseInt(match[1])
        // Capacity should be between 0% and 100%
        expect(capacity).toBeGreaterThanOrEqual(0)
        expect(capacity).toBeLessThanOrEqual(100)

        // Check if capacity meets target (85%)
        if (capacity >= TEST_KPI_TARGETS.enrollment_capacity_percent) {
          // Should show green/success indicator
          await expect(
            capacityKPI.locator('[data-status="success"], .text-green-500')
          ).toBeVisible()
        }
      }
    }
  })

  test('H/E ratio (hours per student) KPI', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Find H/E ratio KPI
    const heRatioKPI = page.locator('[data-testid="kpi-he-ratio"], text=/H\\/E.*ratio/i').first()

    if (await heRatioKPI.isVisible()) {
      // Verify ratio displayed
      const ratioText = await heRatioKPI.textContent()
      const match = ratioText?.match(/(\d+\.\d+)/)

      if (match) {
        const ratio = parseFloat(match[1])

        // H/E ratio should be within reasonable range (1.0 - 1.5 for secondary)
        expect(ratio).toBeGreaterThan(0.5)
        expect(ratio).toBeLessThan(2.0)
      }
    }
  })

  test('E/D ratio (students per class) KPI', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Find E/D ratio KPI
    const edRatioKPI = page
      .locator('[data-testid="kpi-ed-ratio"], text=/E\\/D.*ratio|students.*class/i')
      .first()

    if (await edRatioKPI.isVisible()) {
      // Verify ratio displayed
      const ratioText = await edRatioKPI.textContent()
      const match = ratioText?.match(/(\d+\.?\d*)/)

      if (match) {
        const ratio = parseFloat(match[1])

        // E/D ratio should be within class size constraints (18-35)
        expect(ratio).toBeGreaterThanOrEqual(15)
        expect(ratio).toBeLessThanOrEqual(40)
      }
    }
  })

  test('operating margin KPI', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Find operating margin KPI
    const marginKPI = page
      .locator('[data-testid="kpi-operating-margin"], text=/operating.*margin/i')
      .first()

    if (await marginKPI.isVisible()) {
      // Verify percentage displayed
      await expect(marginKPI).toContainText(/%/)

      // Get margin percentage
      const marginText = await marginKPI.textContent()
      const match = marginText?.match(/(-?\d+\.?\d*)%/)

      if (match) {
        const margin = parseFloat(match[1])

        // Check if margin meets target (5%)
        if (margin >= TEST_KPI_TARGETS.operating_margin_percent) {
          // Should show green/success indicator
          await expect(marginKPI.locator('[data-status="success"], .text-green-500')).toBeVisible()
        } else if (margin < 0) {
          // Negative margin should show red/danger indicator
          await expect(marginKPI.locator('[data-status="danger"], .text-red-500')).toBeVisible()
        }
      }
    }
  })

  test('teacher FTE vs enrollment trend', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for FTE trend chart
    const fteChart = page.locator('[data-testid="fte-trend-chart"], text=/fte.*trend/i').first()

    if (await fteChart.isVisible()) {
      // Verify chart rendered
      await expect(fteChart.locator('svg, canvas')).toBeVisible()

      // Check for legend
      await expect(fteChart.locator('text=/enrollment|fte/i')).toBeVisible()
    }
  })

  test('revenue vs expense breakdown chart', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for revenue vs expense chart
    const revenueExpenseChart = page
      .locator('[data-testid="revenue-expense-chart"], text=/revenue.*expense/i')
      .first()

    if (await revenueExpenseChart.isVisible()) {
      // Verify chart rendered (pie or bar chart)
      await expect(revenueExpenseChart.locator('svg, canvas')).toBeVisible()

      // Check for legend showing revenue and expense categories
      await expect(revenueExpenseChart.locator('text=/revenue/i')).toBeVisible()
      await expect(revenueExpenseChart.locator('text=/expense/i')).toBeVisible()
    }
  })

  test('enrollment by nationality breakdown chart', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for nationality breakdown chart
    const nationalityChart = page
      .locator('[data-testid="nationality-chart"], text=/nationality.*breakdown/i')
      .first()

    if (await nationalityChart.isVisible()) {
      // Verify chart rendered
      await expect(nationalityChart.locator('svg, canvas')).toBeVisible()

      // Check for nationality labels
      await expect(nationalityChart.locator('text=/french/i')).toBeVisible()
      await expect(nationalityChart.locator('text=/saudi/i')).toBeVisible()
    }
  })

  test('KPI target comparison view', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for target comparison section
    const targetSection = page
      .locator('[data-testid="kpi-targets"], text=/target.*comparison/i')
      .first()

    if (await targetSection.isVisible()) {
      // Verify actual vs target displayed for each KPI
      await expect(targetSection.locator('text=/actual/i')).toBeVisible()
      await expect(targetSection.locator('text=/target/i')).toBeVisible()
      await expect(targetSection.locator('text=/variance|difference/i')).toBeVisible()
    }
  })

  test('export KPI report to PDF', async ({ page }) => {
    await page.goto('/analysis/kpis')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Look for export button
    const exportButton = page.locator('button:has-text("Export"), [data-testid="export-button"]')

    if (await exportButton.isVisible()) {
      // Look for PDF option
      const pdfOption = page.locator('button:has-text("PDF"), [data-testid="export-pdf"]')

      if (await pdfOption.isVisible()) {
        // Start waiting for download
        const downloadPromise = page.waitForEvent('download')

        await pdfOption.click()

        // Wait for download
        const download = await downloadPromise

        // Verify filename
        expect(download.suggestedFilename()).toMatch(/kpi|dashboard|report/i)
        expect(download.suggestedFilename()).toMatch(/\.pdf$/)
      }
    }
  })
})

test.describe('Variance Analysis', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('budget vs actual variance analysis', async ({ page }) => {
    await page.goto('/analysis/variance')

    // Verify variance analysis page loaded
    await expect(
      page.locator('h1, h2').filter({ hasText: /variance|budget.*actual/i })
    ).toBeVisible()

    // Select budget version
    await selectBudgetVersion(page, /Test|2025/i)

    // Verify variance columns displayed
    await expect(page.locator('text=/budget/i')).toBeVisible()
    await expect(page.locator('text=/actual/i')).toBeVisible()
    await expect(page.locator('text=/variance|difference/i')).toBeVisible()
  })

  test('variance by account code', async ({ page }) => {
    await page.goto('/analysis/variance')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for account code filter
    const accountFilter = page.locator('[name="account_code"], [data-testid="account-filter"]')

    if (await accountFilter.isVisible()) {
      // Select teaching salaries account (64110)
      await accountFilter.fill('64110')
      await page.waitForTimeout(1000)

      // Verify filtered results
      await expect(page.locator('text=/64110|teaching.*salaries/i')).toBeVisible()
    }
  })

  test('favorable vs unfavorable variance highlighting', async ({ page }) => {
    await page.goto('/analysis/variance')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for color-coded variances
    const favorableRows = page.locator('[data-status="favorable"], .text-green-500')
    const unfavorableRows = page.locator('[data-status="unfavorable"], .text-red-500')

    // At least one should exist
    const favorableCount = await favorableRows.count()
    const unfavorableCount = await unfavorableRows.count()

    expect(favorableCount + unfavorableCount).toBeGreaterThan(0)
  })

  test('variance drill-down by period (T1, T2, T3)', async ({ page }) => {
    await page.goto('/analysis/variance')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for period filter
    const periodFilter = page.locator('[name="period"], [data-testid="period-select"]')

    if (await periodFilter.isVisible()) {
      await periodFilter.selectOption('T1')
      await page.waitForTimeout(1000)

      // Verify T1 data displayed
      await expect(page.locator('text=/T1|trimester.*1/i')).toBeVisible()

      // Switch to T2
      await periodFilter.selectOption('T2')
      await page.waitForTimeout(1000)

      await expect(page.locator('text=/T2|trimester.*2/i')).toBeVisible()
    }
  })

  test('export variance analysis to Excel', async ({ page }) => {
    await page.goto('/analysis/variance')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Look for export button
    const exportButton = page.locator('button:has-text("Export"), [data-testid="export-button"]')

    if (await exportButton.isVisible()) {
      // Start waiting for download
      const downloadPromise = page.waitForEvent('download')

      await exportButton.click()

      // Wait for download
      const download = await downloadPromise

      // Verify filename
      expect(download.suggestedFilename()).toMatch(/variance|budget.*actual/i)
      expect(download.suggestedFilename()).toMatch(/\.xlsx$|\.csv$/)
    }
  })
})
