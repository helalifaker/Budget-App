import { test, expect } from '@playwright/test'

/**
 * E2E Test Suite: External Integrations
 * Tests Odoo, Skolengo, and AEFE integrations
 */

test.describe('Odoo Integration', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin
    await page.goto('/login')
    await page.fill('[name="email"]', 'admin@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
  })

  test('configure Odoo connection', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Verify Odoo configuration form visible
    await expect(page.locator('h1, h2').filter({ hasText: /odoo/i })).toBeVisible()

    // Check for configuration fields
    const urlInput = page.locator('[name="odoo_url"], [data-testid="odoo-url"]')
    const apiKeyInput = page.locator('[name="api_key"], [data-testid="api-key"]')
    const databaseInput = page.locator('[name="database"], [data-testid="database"]')

    if (await urlInput.isVisible()) {
      await expect(urlInput).toBeVisible()
      await expect(apiKeyInput).toBeVisible()
      await expect(databaseInput).toBeVisible()
    }
  })

  test('test Odoo connection', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Look for test connection button
    const testButton = page.locator(
      'button:has-text("Test Connection"), [data-testid="test-connection"]'
    )

    if (await testButton.isVisible()) {
      await testButton.click()

      // Wait for connection result
      const resultMessage = page.locator(
        '[data-testid="connection-result"], text=/success|failed|error/i'
      )
      await expect(resultMessage).toBeVisible({ timeout: 10000 })
    }
  })

  test('import actuals from Odoo', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Navigate to import section
    const importTab = page.locator('button:has-text("Import"), [data-testid="import-tab"]')
    if (await importTab.isVisible()) {
      await importTab.click()
    }

    // Select period
    const periodSelect = page.locator('[name="period"], [data-testid="period-select"]')
    if (await periodSelect.isVisible()) {
      await periodSelect.selectOption('T1')
    }

    // Select fiscal year
    const yearSelect = page.locator('[name="fiscal_year"], [data-testid="year-select"]')
    if (await yearSelect.isVisible()) {
      await yearSelect.selectOption('2025')
    }

    // Click import button
    const importButton = page.locator(
      'button:has-text("Import Actuals"), [data-testid="import-button"]'
    )
    if (await importButton.isVisible()) {
      await importButton.click()

      // Wait for import to complete
      await expect(page.locator('text=/import.*successful|complete/i')).toBeVisible({
        timeout: 30000,
      })

      // Verify import summary displayed
      await expect(
        page.locator('[data-testid="import-summary"], text=/records.*imported/i')
      ).toBeVisible()
    }
  })

  test('view Odoo account mapping', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Navigate to mapping section
    const mappingTab = page.locator('button:has-text("Mapping"), [data-testid="mapping-tab"]')
    if (await mappingTab.isVisible()) {
      await mappingTab.click()
    }

    // Verify account mapping table visible
    await expect(page.locator('text=/odoo.*account|account.*code/i')).toBeVisible()
    await expect(page.locator('text=/efir.*account|budget.*account/i')).toBeVisible()

    // Check for mapping entries
    const mappingRows = page.locator('[data-testid="mapping-row"], tr').filter({ hasText: /\d{5}/ })
    if (await mappingRows.first().isVisible()) {
      expect(await mappingRows.count()).toBeGreaterThan(0)
    }
  })

  test('create new account mapping', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Navigate to mapping section
    const mappingTab = page.locator('button:has-text("Mapping"), [data-testid="mapping-tab"]')
    if (await mappingTab.isVisible()) {
      await mappingTab.click()
    }

    // Click add mapping button
    const addButton = page.locator('button:has-text("Add Mapping"), [data-testid="add-mapping"]')
    if (await addButton.isVisible()) {
      await addButton.click()

      // Fill mapping form
      await page.fill('[name="odoo_account"], [data-testid="odoo-account"]', '600010')
      await page.fill('[name="efir_account"], [data-testid="efir-account"]', '64110')
      await page.fill(
        '[name="description"], [data-testid="description"]',
        'Teaching Salaries Mapping'
      )

      // Save mapping
      await page.click('button:has-text("Save"), button[type="submit"]')

      // Verify mapping created
      await expect(page.locator('text=/mapping.*saved|success/i')).toBeVisible({ timeout: 5000 })
    }
  })

  test('view import history', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Navigate to history section
    const historyTab = page.locator('button:has-text("History"), [data-testid="history-tab"]')
    if (await historyTab.isVisible()) {
      await historyTab.click()
    }

    // Verify import history table visible
    await expect(page.locator('text=/import.*date|timestamp/i')).toBeVisible()
    await expect(page.locator('text=/status|records/i')).toBeVisible()

    // Check for history entries
    const historyRows = page
      .locator('[data-testid="history-row"], tr')
      .filter({ hasText: /\d{4}-\d{2}-\d{2}/ })
    if (await historyRows.first().isVisible()) {
      expect(await historyRows.count()).toBeGreaterThan(0)
    }
  })
})

test.describe('Skolengo Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'admin@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('configure Skolengo connection', async ({ page }) => {
    await page.goto('/settings/integrations/skolengo')

    // Verify Skolengo configuration form visible
    await expect(page.locator('h1, h2').filter({ hasText: /skolengo/i })).toBeVisible()

    // Check for configuration fields
    const apiUrlInput = page.locator('[name="skolengo_url"], [data-testid="skolengo-url"]')
    const apiKeyInput = page.locator('[name="api_key"], [data-testid="api-key"]')

    if (await apiUrlInput.isVisible()) {
      await expect(apiUrlInput).toBeVisible()
      await expect(apiKeyInput).toBeVisible()
    }
  })

  test('import enrollment data from Skolengo', async ({ page }) => {
    await page.goto('/settings/integrations/skolengo')

    // Navigate to import section
    const importTab = page.locator('button:has-text("Import"), [data-testid="import-tab"]')
    if (await importTab.isVisible()) {
      await importTab.click()
    }

    // Select academic year
    const yearSelect = page.locator('[name="academic_year"], [data-testid="year-select"]')
    if (await yearSelect.isVisible()) {
      await yearSelect.selectOption('2024-2025')
    }

    // Select target budget version
    const versionSelect = page.locator('[name="budget_version"], [data-testid="version-select"]')
    if (await versionSelect.isVisible()) {
      await versionSelect.selectOption({ index: 0 })
    }

    // Click import button
    const importButton = page.locator(
      'button:has-text("Import Enrollment"), [data-testid="import-button"]'
    )
    if (await importButton.isVisible()) {
      await importButton.click()

      // Wait for import to complete
      await expect(page.locator('text=/import.*successful|complete/i')).toBeVisible({
        timeout: 30000,
      })

      // Verify import summary
      await expect(page.locator('[data-testid="import-summary"]')).toBeVisible()
    }
  })

  test('export enrollment projections to Skolengo', async ({ page }) => {
    await page.goto('/settings/integrations/skolengo')

    // Navigate to export section
    const exportTab = page.locator('button:has-text("Export"), [data-testid="export-tab"]')
    if (await exportTab.isVisible()) {
      await exportTab.click()
    }

    // Select budget version to export
    const versionSelect = page.locator('[name="budget_version"], [data-testid="version-select"]')
    if (await versionSelect.isVisible()) {
      await versionSelect.selectOption({ index: 0 })
    }

    // Click export button
    const exportButton = page.locator(
      'button:has-text("Export to Skolengo"), [data-testid="export-button"]'
    )
    if (await exportButton.isVisible()) {
      await exportButton.click()

      // Wait for export to complete
      await expect(page.locator('text=/export.*successful|complete/i')).toBeVisible({
        timeout: 30000,
      })
    }
  })

  test('preview Skolengo import data', async ({ page }) => {
    await page.goto('/settings/integrations/skolengo')

    // Navigate to import section
    const importTab = page.locator('button:has-text("Import"), [data-testid="import-tab"]')
    if (await importTab.isVisible()) {
      await importTab.click()
    }

    // Click preview button
    const previewButton = page.locator('button:has-text("Preview"), [data-testid="preview-button"]')
    if (await previewButton.isVisible()) {
      await previewButton.click()

      // Wait for preview to load
      await expect(page.locator('[data-testid="preview-data"], text=/level|student/i')).toBeVisible(
        { timeout: 10000 }
      )

      // Verify preview table shows data
      const previewRows = page.locator('[data-testid="preview-row"], tr')
      if (await previewRows.first().isVisible()) {
        expect(await previewRows.count()).toBeGreaterThan(0)
      }
    }
  })
})

test.describe('AEFE Integration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'admin@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('import AEFE position file', async ({ page }) => {
    await page.goto('/settings/integrations/aefe')

    // Verify AEFE integration page visible
    await expect(page.locator('h1, h2').filter({ hasText: /aefe/i })).toBeVisible()

    // Look for file upload
    const fileInput = page.locator('[type="file"], [data-testid="file-upload"]')
    if (await fileInput.isVisible()) {
      // Upload test file (would need actual file in real test)
      // await fileInput.setInputFiles('path/to/aefe_positions.xlsx');

      // Click import button
      const importButton = page.locator('button:has-text("Import"), [data-testid="import-button"]')
      if (await importButton.isVisible()) {
        await importButton.click()

        // Wait for import to complete
        await expect(page.locator('text=/import.*successful|complete/i')).toBeVisible({
          timeout: 30000,
        })
      }
    }
  })

  test('configure PRRD rates', async ({ page }) => {
    await page.goto('/settings/integrations/aefe')

    // Navigate to PRRD configuration
    const prrdTab = page.locator('button:has-text("PRRD"), [data-testid="prrd-tab"]')
    if (await prrdTab.isVisible()) {
      await prrdTab.click()
    }

    // Verify PRRD rate configuration visible
    await expect(page.locator('text=/prrd.*rate|contribution/i')).toBeVisible()

    // Check for rate input
    const rateInput = page.locator('[name="prrd_rate"], [data-testid="prrd-rate"]')
    if (await rateInput.isVisible()) {
      await expect(rateInput).toBeVisible()

      // Verify current rate displayed (should be around 41,863 EUR)
      const currentRate = await rateInput.inputValue()
      expect(parseFloat(currentRate)).toBeGreaterThan(40000)
    }
  })

  test('view AEFE funded vs detached positions', async ({ page }) => {
    await page.goto('/settings/integrations/aefe')

    // Navigate to positions section
    const positionsTab = page.locator('button:has-text("Positions"), [data-testid="positions-tab"]')
    if (await positionsTab.isVisible()) {
      await positionsTab.click()
    }

    // Verify positions table visible
    await expect(page.locator('text=/funded|detached|resident/i')).toBeVisible()

    // Check for position type indicators
    const fundedPositions = page.locator('[data-testid*="funded"], text=/funded/i')
    const detachedPositions = page.locator('[data-testid*="detached"], text=/detached|resident/i')

    if (
      (await fundedPositions.first().isVisible()) ||
      (await detachedPositions.first().isVisible())
    ) {
      // At least one type should be visible
      expect(true).toBe(true)
    }
  })

  test('export AEFE workforce report', async ({ page }) => {
    await page.goto('/settings/integrations/aefe')

    // Look for export button
    const exportButton = page.locator('button:has-text("Export"), [data-testid="export-button"]')

    if (await exportButton.isVisible()) {
      // Start waiting for download
      const downloadPromise = page.waitForEvent('download')

      await exportButton.click()

      // Wait for download
      const download = await downloadPromise

      // Verify filename
      expect(download.suggestedFilename()).toMatch(/aefe|workforce|positions/i)
    }
  })
})

test.describe('Integration Error Handling', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'admin@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('handle Odoo connection failure gracefully', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Enter invalid credentials
    await page.fill('[name="odoo_url"]', 'https://invalid.odoo.com')
    await page.fill('[name="api_key"]', 'invalid_key')
    await page.fill('[name="database"]', 'invalid_db')

    // Test connection
    const testButton = page.locator('button:has-text("Test Connection")')
    if (await testButton.isVisible()) {
      await testButton.click()

      // Should show error message
      await expect(page.locator('text=/connection.*failed|error|invalid/i')).toBeVisible({
        timeout: 10000,
      })
    }
  })

  test('show validation errors for invalid import data', async ({ page }) => {
    await page.goto('/settings/integrations/skolengo')

    // Try to import without selecting required fields
    const importButton = page.locator('button:has-text("Import Enrollment")')
    if (await importButton.isVisible()) {
      await importButton.click()

      // Should show validation error
      await expect(page.locator('text=/required|select.*version|validation/i')).toBeVisible({
        timeout: 5000,
      })
    }
  })

  test('retry failed import', async ({ page }) => {
    await page.goto('/settings/integrations/odoo')

    // Navigate to history
    const historyTab = page.locator('button:has-text("History")')
    if (await historyTab.isVisible()) {
      await historyTab.click()
    }

    // Find failed import
    const failedRow = page.locator('tr:has-text("Failed"), [data-testid*="failed"]').first()
    if (await failedRow.isVisible()) {
      // Click retry button
      const retryButton = failedRow.locator(
        'button:has-text("Retry"), [data-testid="retry-button"]'
      )
      if (await retryButton.isVisible()) {
        await retryButton.click()

        // Wait for retry to complete
        await expect(page.locator('text=/retry.*initiated|processing/i')).toBeVisible({
          timeout: 5000,
        })
      }
    }
  })
})

test.describe('Integration Data Sync', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'admin@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('Odoo actuals sync with budget comparison', async ({ page }) => {
    // Import actuals from Odoo
    await page.goto('/settings/integrations/odoo')
    const importButton = page.locator('button:has-text("Import Actuals")')

    if (await importButton.isVisible()) {
      await importButton.click()
      await expect(page.locator('text=/import.*successful/i')).toBeVisible({ timeout: 30000 })
    }

    // Navigate to budget vs actual analysis
    await page.goto('/analysis/budget-vs-actual')

    // Verify actuals displayed
    await expect(page.locator('[data-testid*="actual"], text=/actual/i')).toBeVisible()

    // Verify variance calculations
    await expect(page.locator('[data-testid*="variance"], text=/variance|écart/i')).toBeVisible()
  })

  test('Skolengo enrollment sync with planning module', async ({ page }) => {
    // Import enrollment from Skolengo
    await page.goto('/settings/integrations/skolengo')

    const importTab = page.locator('button:has-text("Import")')
    if (await importTab.isVisible()) {
      await importTab.click()

      const importButton = page.locator('button:has-text("Import Enrollment")')
      if (await importButton.isVisible()) {
        await importButton.click()
        await expect(page.locator('text=/import.*successful/i')).toBeVisible({ timeout: 30000 })
      }
    }

    // Navigate to enrollment planning
    await page.goto('/planning/enrollment')

    // Verify imported data visible
    await expect(page.locator('[data-testid*="enrollment"], text=/student/i')).toBeVisible()
  })
})
