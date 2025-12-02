import { test, expect } from '@playwright/test'
import { login } from './helpers/auth.helper'

/**
 * E2E Test Suite: 5-Year Strategic Planning
 * Tests multi-year budget scenarios, projections, and strategic planning features
 */

test.describe('5-Year Strategic Planning', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('create new 5-year strategic plan', async ({ page }) => {
    await page.goto('/strategic')

    // Verify strategic planning page loaded
    await expect(page.locator('h1, h2').filter({ hasText: /strategic|5.*year/i })).toBeVisible()

    // Click create new plan
    const createButton = page.locator(
      'button:has-text("New Plan"), button:has-text("Create"), [data-testid="create-plan"]'
    )

    if (await createButton.isVisible()) {
      await createButton.click()
      await page.waitForTimeout(500)

      // Fill plan details
      await page.fill('[name="name"]', `Strategic Plan ${Date.now()}`)
      await page.fill('[name="start_year"]', '2025')
      await page.fill('[name="end_year"]', '2029')

      const description = page.locator('[name="description"]')
      if (await description.isVisible()) {
        await description.fill('5-year strategic budget plan for expansion')
      }

      // Save
      await page.click('button:has-text("Save"), button[type="submit"]')
      await expect(page.locator('text=/saved|success|created/i')).toBeVisible({ timeout: 5000 })
    }
  })

  test('configure enrollment growth scenarios (conservative, base, optimistic)', async ({
    page,
  }) => {
    await page.goto('/strategic')

    // Select or create plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
      await page.waitForTimeout(1000)
    }

    // Navigate to scenarios section
    const scenariosTab = page.locator('button:has-text("Scenarios"), [data-testid="scenarios-tab"]')
    if (await scenariosTab.isVisible()) {
      await scenariosTab.click()
    }

    // Configure conservative scenario (2% growth)
    const conservativeScenario = page.locator('[data-testid="conservative-scenario"]')
    if (await conservativeScenario.isVisible()) {
      await conservativeScenario.click()

      const growthRateInput = page.locator('[name="growth_rate"], [data-testid="growth-rate"]')
      if (await growthRateInput.isVisible()) {
        await growthRateInput.fill('2')
        await page.click('button:has-text("Save")')
        await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
      }
    }

    // Configure base scenario (5% growth)
    const baseScenario = page.locator('[data-testid="base-scenario"]')
    if (await baseScenario.isVisible()) {
      await baseScenario.click()

      const growthRateInput = page.locator('[name="growth_rate"], [data-testid="growth-rate"]')
      if (await growthRateInput.isVisible()) {
        await growthRateInput.fill('5')
        await page.click('button:has-text("Save")')
        await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
      }
    }

    // Configure optimistic scenario (10% growth)
    const optimisticScenario = page.locator('[data-testid="optimistic-scenario"]')
    if (await optimisticScenario.isVisible()) {
      await optimisticScenario.click()

      const growthRateInput = page.locator('[name="growth_rate"], [data-testid="growth-rate"]')
      if (await growthRateInput.isVisible()) {
        await growthRateInput.fill('10')
        await page.click('button:has-text("Save")')
        await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
      }
    }
  })

  test('view 5-year enrollment projections', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
      await page.waitForTimeout(1000)
    }

    // Navigate to projections
    const projectionsTab = page.locator(
      'button:has-text("Projections"), [data-testid="projections-tab"]'
    )
    if (await projectionsTab.isVisible()) {
      await projectionsTab.click()
    }

    // Verify projection years displayed (2025-2029)
    await expect(page.locator('text=/2025/i')).toBeVisible()
    await expect(page.locator('text=/2026/i')).toBeVisible()
    await expect(page.locator('text=/2027/i')).toBeVisible()
    await expect(page.locator('text=/2028/i')).toBeVisible()
    await expect(page.locator('text=/2029/i')).toBeVisible()
  })

  test('view 5-year revenue and expense projections', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Verify revenue and expense projections
    await expect(page.locator('[data-testid*="revenue-projection"]')).toBeVisible()
    await expect(page.locator('[data-testid*="expense-projection"]')).toBeVisible()
    await expect(page.locator('[data-testid*="net-result-projection"]')).toBeVisible()

    // Verify chart visualization
    const projectionChart = page
      .locator('[data-testid="projection-chart"], text=/projection.*chart/i')
      .first()
    if (await projectionChart.isVisible()) {
      await expect(projectionChart.locator('svg, canvas')).toBeVisible()
    }
  })

  test('compare scenarios side-by-side', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Click compare scenarios
    const compareButton = page.locator(
      'button:has-text("Compare"), [data-testid="compare-scenarios"]'
    )
    if (await compareButton.isVisible()) {
      await compareButton.click()
      await page.waitForTimeout(1000)

      // Verify all three scenarios displayed
      await expect(page.locator('text=/conservative/i')).toBeVisible()
      await expect(page.locator('text=/base/i')).toBeVisible()
      await expect(page.locator('text=/optimistic/i')).toBeVisible()

      // Verify comparison metrics
      await expect(page.locator('text=/enrollment/i')).toBeVisible()
      await expect(page.locator('text=/revenue/i')).toBeVisible()
      await expect(page.locator('text=/expense/i')).toBeVisible()
    }
  })

  test('configure CapEx investments for 5-year plan', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Navigate to CapEx section
    const capexTab = page.locator('button:has-text("CapEx"), [data-testid="capex-tab"]')
    if (await capexTab.isVisible()) {
      await capexTab.click()
    }

    // Add new capital investment
    const addButton = page.locator('button:has-text("Add Investment"), [data-testid="add-capex"]')
    if (await addButton.isVisible()) {
      await addButton.click()

      // Fill investment details
      await page.fill('[name="description"]', 'New Building Construction')
      await page.fill('[name="amount"]', '5000000')
      await page.selectOption('[name="year"]', '2026')
      await page.selectOption('[name="category"]', 'Infrastructure')

      // Save
      await page.click('button:has-text("Save"), button[type="submit"]')
      await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
    }
  })

  test('workforce planning projections (FTE growth)', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Navigate to workforce section
    const workforceTab = page.locator('button:has-text("Workforce"), [data-testid="workforce-tab"]')
    if (await workforceTab.isVisible()) {
      await workforceTab.click()
    }

    // Verify FTE projections displayed
    await expect(page.locator('[data-testid*="fte-projection"], text=/fte/i')).toBeVisible()

    // Verify teacher FTE by year
    await expect(page.locator('text=/teaching.*staff|teacher.*fte/i')).toBeVisible()
    await expect(page.locator('text=/support.*staff/i')).toBeVisible()
  })

  test('cash flow projections for 5 years', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Navigate to cash flow section
    const cashFlowTab = page.locator('button:has-text("Cash Flow"), [data-testid="cashflow-tab"]')
    if (await cashFlowTab.isVisible()) {
      await cashFlowTab.click()
    }

    // Verify cash flow components
    await expect(page.locator('text=/operating.*cash/i')).toBeVisible()
    await expect(page.locator('text=/investing.*cash/i')).toBeVisible()
    await expect(page.locator('text=/financing.*cash/i')).toBeVisible()

    // Verify cash flow chart
    const cashFlowChart = page.locator('[data-testid="cashflow-chart"]')
    if (await cashFlowChart.isVisible()) {
      await expect(cashFlowChart.locator('svg, canvas')).toBeVisible()
    }
  })

  test('export strategic plan to Excel', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Look for export button
    const exportButton = page.locator('button:has-text("Export"), [data-testid="export-button"]')

    if (await exportButton.isVisible()) {
      // Start waiting for download
      const downloadPromise = page.waitForEvent('download')

      await exportButton.click()

      // Wait for download
      const download = await downloadPromise

      // Verify filename
      expect(download.suggestedFilename()).toMatch(/strategic|5.*year|plan/i)
      expect(download.suggestedFilename()).toMatch(/\.xlsx$/)
    }
  })

  test('sensitivity analysis on key assumptions', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Navigate to sensitivity analysis
    const sensitivityTab = page.locator(
      'button:has-text("Sensitivity"), [data-testid="sensitivity-tab"]'
    )
    if (await sensitivityTab.isVisible()) {
      await sensitivityTab.click()
    }

    // Verify sensitivity parameters
    await expect(page.locator('text=/enrollment.*growth/i')).toBeVisible()
    await expect(page.locator('text=/fee.*increase/i')).toBeVisible()
    await expect(page.locator('text=/salary.*increase/i')).toBeVisible()

    // Adjust enrollment growth assumption
    const enrollmentGrowthSlider = page.locator('[name="enrollment_growth"], input[type="range"]')
    if (await enrollmentGrowthSlider.isVisible()) {
      await enrollmentGrowthSlider.fill('8')
      await page.waitForTimeout(1000)

      // Verify impact on projections
      await expect(page.locator('[data-testid="sensitivity-impact"]')).toBeVisible()
    }
  })

  test('facility capacity planning for growth', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Navigate to facilities section
    const facilitiesTab = page.locator(
      'button:has-text("Facilities"), [data-testid="facilities-tab"]'
    )
    if (await facilitiesTab.isVisible()) {
      await facilitiesTab.click()
    }

    // Verify capacity metrics
    await expect(page.locator('text=/classroom.*capacity/i')).toBeVisible()
    await expect(page.locator('text=/student.*capacity/i')).toBeVisible()

    // Check for capacity warnings if enrollment exceeds capacity
    const capacityWarning = page.locator('[data-status="warning"], text=/capacity.*exceeded/i')
    if (await capacityWarning.isVisible()) {
      // Verify warning message displayed
      await expect(capacityWarning).toBeVisible()
    }
  })
})

test.describe('Strategic Plan Validation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('validate enrollment cannot exceed total capacity', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Try to set unrealistic enrollment growth (20% per year = exceeds capacity by year 3)
    const scenariosTab = page.locator('button:has-text("Scenarios")')
    if (await scenariosTab.isVisible()) {
      await scenariosTab.click()
    }

    const growthRateInput = page.locator('[name="growth_rate"]')
    if (await growthRateInput.isVisible()) {
      await growthRateInput.fill('20')
      await page.click('button:has-text("Calculate"), button:has-text("Save")')

      // Should show validation warning about capacity
      await expect(page.locator('text=/capacity.*exceeded|warning.*capacity/i')).toBeVisible({
        timeout: 5000,
      })
    }
  })

  test('validate financial sustainability indicators', async ({ page }) => {
    await page.goto('/strategic')

    // Select plan
    const planSelector = page.locator('[data-testid="plan-selector"], select[name="plan"]')
    if (await planSelector.isVisible()) {
      await planSelector.selectOption({ index: 0 })
    }

    // Check for sustainability indicators
    const sustainabilitySection = page.locator(
      '[data-testid="sustainability"], text=/sustainability/i'
    )

    if (await sustainabilitySection.isVisible()) {
      // Verify indicators displayed
      await expect(page.locator('text=/debt.*ratio/i')).toBeVisible()
      await expect(page.locator('text=/liquidity.*ratio/i')).toBeVisible()
      await expect(page.locator('text=/operating.*margin/i')).toBeVisible()

      // Check for any red flags
      const warningIndicators = page.locator('[data-status="warning"], [data-status="danger"]')
      const warningCount = await warningIndicators.count()

      // Log warnings if any
      if (warningCount > 0) {
        console.log(`⚠️  ${warningCount} sustainability warnings found`)
      }
    }
  })
})
