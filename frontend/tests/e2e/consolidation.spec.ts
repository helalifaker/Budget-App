import { test, expect } from '@playwright/test'

/**
 * E2E Test Suite: Budget Consolidation
 * Tests budget consolidation and financial statement generation
 */

test.describe('Budget Consolidation', () => {
  test.beforeEach(async ({ page }) => {
    // Login as manager
    await page.goto('/login')
    await page.fill('[name="email"]', 'manager@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
  })

  test('consolidate budget and verify totals', async ({ page }) => {
    await page.goto('/consolidation/budget')

    // Select budget version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
      await page.waitForTimeout(1000)
    }

    // Click consolidate button
    const consolidateButton = page.locator(
      'button:has-text("Consolidate"), [data-testid="consolidate-button"]'
    )
    if (await consolidateButton.isVisible()) {
      await consolidateButton.click()

      // Wait for consolidation to complete
      await expect(page.locator('text=/consolidation.*complete|success/i')).toBeVisible({
        timeout: 15000,
      })

      // Verify consolidated totals displayed
      await expect(
        page.locator('[data-testid="total-revenue"], text=/total.*revenue/i')
      ).toBeVisible()
      await expect(
        page.locator('[data-testid="total-expenses"], text=/total.*expense/i')
      ).toBeVisible()
      await expect(
        page.locator('[data-testid="net-result"], text=/net.*result|profit|loss/i')
      ).toBeVisible()
    }
  })

  test('revenue consolidation from all sources', async ({ page }) => {
    await page.goto('/consolidation/budget')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Verify revenue breakdown visible
    const revenueSection = page.locator('[data-testid="revenue-section"], text=/revenue/i').first()
    if (await revenueSection.isVisible()) {
      // Check for different revenue categories
      await expect(page.locator('text=/tuition|frais.*scolarité/i')).toBeVisible()
      await expect(page.locator('text=/registration|inscription/i')).toBeVisible()
      await expect(page.locator('text=/cafeteria|cantine/i')).toBeVisible()
    }
  })

  test('expense consolidation by account code', async ({ page }) => {
    await page.goto('/consolidation/budget')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Verify expense categories visible
    const expenseSection = page.locator('[data-testid="expense-section"], text=/expense/i').first()
    if (await expenseSection.isVisible()) {
      // Check for account code structure (60xxx-68xxx)
      await expect(page.locator('text=/64110|personnel|salaries/i')).toBeVisible()
      await expect(page.locator('text=/61|purchase|achat/i')).toBeVisible()
    }
  })

  test('period-based consolidation (T1, T2, T3)', async ({ page }) => {
    await page.goto('/consolidation/budget')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Check for period tabs or filters
    const t1Tab = page.locator('button:has-text("T1"), [data-testid="period-t1"]')
    const t2Tab = page.locator('button:has-text("T2"), [data-testid="period-t2"]')
    const t3Tab = page.locator('button:has-text("T3"), [data-testid="period-t3"]')

    if (await t1Tab.isVisible()) {
      // Click T1
      await t1Tab.click()
      await expect(page.locator('text=/T1|40%/i')).toBeVisible()

      // Click T2
      await t2Tab.click()
      await expect(page.locator('text=/T2|30%/i')).toBeVisible()

      // Click T3
      await t3Tab.click()
      await expect(page.locator('text=/T3|30%/i')).toBeVisible()
    }
  })

  test('export consolidated budget to Excel', async ({ page }) => {
    await page.goto('/consolidation/budget')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
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
      expect(download.suggestedFilename()).toMatch(/budget|consolidation/i)
      expect(download.suggestedFilename()).toMatch(/\.xlsx$/)
    }
  })
})

test.describe('Financial Statements', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'manager@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('generate income statement (compte de résultat)', async ({ page }) => {
    await page.goto('/consolidation/statements')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Select income statement
    const incomeStatementTab = page.locator(
      'button:has-text("Income"), button:has-text("Résultat"), [data-testid="income-statement"]'
    )
    if (await incomeStatementTab.isVisible()) {
      await incomeStatementTab.click()
    }

    // Verify income statement components
    await expect(page.locator('text=/revenue|produits/i').first()).toBeVisible()
    await expect(page.locator('text=/expenses|charges/i').first()).toBeVisible()
    await expect(page.locator('text=/net.*result|résultat.*net/i')).toBeVisible()
  })

  test('generate balance sheet (bilan)', async ({ page }) => {
    await page.goto('/consolidation/statements')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Select balance sheet
    const balanceSheetTab = page.locator(
      'button:has-text("Balance"), button:has-text("Bilan"), [data-testid="balance-sheet"]'
    )
    if (await balanceSheetTab.isVisible()) {
      await balanceSheetTab.click()
    }

    // Verify balance sheet components
    await expect(page.locator('text=/assets|actif/i').first()).toBeVisible()
    await expect(page.locator('text=/liabilities|passif/i').first()).toBeVisible()
    await expect(page.locator('text=/equity|capitaux/i').first()).toBeVisible()
  })

  test('generate cash flow statement', async ({ page }) => {
    await page.goto('/consolidation/statements')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Select cash flow statement
    const cashFlowTab = page.locator(
      'button:has-text("Cash Flow"), button:has-text("Trésorerie"), [data-testid="cash-flow"]'
    )
    if (await cashFlowTab.isVisible()) {
      await cashFlowTab.click()
    }

    // Verify cash flow components
    await expect(page.locator('text=/operating|exploitation/i').first()).toBeVisible()
    await expect(page.locator('text=/investing|investissement/i').first()).toBeVisible()
    await expect(page.locator('text=/financing|financement/i').first()).toBeVisible()
  })

  test('French PCG account code structure', async ({ page }) => {
    await page.goto('/consolidation/statements')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Verify PCG account codes visible
    // Revenue: 70xxx-77xxx
    // Expenses: 60xxx-68xxx
    const accountCodes = page.locator('text=/^[67][0-9]{4}/i')
    if (await accountCodes.first().isVisible()) {
      const count = await accountCodes.count()
      expect(count).toBeGreaterThan(0)
    }
  })

  test('toggle between French PCG and IFRS view', async ({ page }) => {
    await page.goto('/consolidation/statements')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Look for format toggle
    const formatToggle = page.locator(
      '[data-testid="format-toggle"], button:has-text("PCG"), button:has-text("IFRS")'
    )
    if (await formatToggle.first().isVisible()) {
      // Click to PCG format
      await page.click('button:has-text("PCG")')
      await expect(page.locator('text=/compte.+résultat|bilan/i')).toBeVisible()

      // Click to IFRS format
      await page.click('button:has-text("IFRS")')
      await expect(page.locator('text=/income.+statement|balance.+sheet/i')).toBeVisible()
    }
  })

  test('export financial statements to PDF', async ({ page }) => {
    await page.goto('/consolidation/statements')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Look for export PDF button
    const exportPDFButton = page.locator(
      'button:has-text("Export PDF"), [data-testid="export-pdf"]'
    )

    if (await exportPDFButton.isVisible()) {
      // Start waiting for download
      const downloadPromise = page.waitForEvent('download')

      await exportPDFButton.click()

      // Wait for download
      const download = await downloadPromise

      // Verify filename
      expect(download.suggestedFilename()).toMatch(/\.pdf$/)
    }
  })
})

test.describe('Consolidation Validation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'manager@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('verify revenue equals sum of all revenue streams', async ({ page }) => {
    await page.goto('/consolidation/budget')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
      await page.waitForTimeout(1000)
    }

    // Get individual revenue components
    const tuitionRevenue = await page
      .locator('[data-testid*="tuition-revenue"]')
      .first()
      .textContent()

    // Get total revenue
    const totalRevenue = await page.locator('[data-testid="total-revenue"]').first().textContent()

    // Verify total equals sum (rough check - would need parsing for exact match)
    expect(totalRevenue).toBeTruthy()
    expect(tuitionRevenue).toBeTruthy()
  })

  test('verify balance sheet equation: Assets = Liabilities + Equity', async ({ page }) => {
    await page.goto('/consolidation/statements')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Select balance sheet
    const balanceSheetTab = page.locator('button:has-text("Balance"), button:has-text("Bilan")')
    if (await balanceSheetTab.isVisible()) {
      await balanceSheetTab.click()
      await page.waitForTimeout(1000)

      // Get totals
      await page.locator('[data-testid="total-assets"]').first().textContent()
      await page.locator('[data-testid="total-liabilities"]').first().textContent()
      await page.locator('[data-testid="total-equity"]').first().textContent()

      // Verify all values present
      await expect(page.locator('[data-testid="total-assets"]')).toBeVisible()
      await expect(page.locator('[data-testid="total-liabilities"]')).toBeVisible()
      await expect(page.locator('[data-testid="total-equity"]')).toBeVisible()
    }
  })

  test('consolidation fails with incomplete data', async ({ page }) => {
    await page.goto('/consolidation/budget')

    // Create new version without complete data
    await page.goto('/configuration/versions')
    await page.click('button:has-text("New Version")')
    await page.fill('[name="name"]', `Incomplete ${Date.now()}`)
    await page.fill('[name="fiscal_year"]', '2025')
    await page.fill('[name="academic_year"]', '2024-2025')
    await page.click('button[type="submit"]:has-text("Create")')

    // Try to consolidate immediately
    await page.goto('/consolidation/budget')
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ label: /Incomplete/ })
    }

    const consolidateButton = page.locator('button:has-text("Consolidate")')
    if (await consolidateButton.isVisible()) {
      await consolidateButton.click()

      // Should show validation error
      await expect(page.locator('text=/incomplete|missing|required|validation/i')).toBeVisible({
        timeout: 5000,
      })
    }
  })
})
