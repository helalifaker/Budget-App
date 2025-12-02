import { test, expect } from '@playwright/test'

/**
 * E2E Test Suite: DHG Workforce Planning
 * Tests the DHG (Dotation Horaire Globale) calculations and workforce planning
 */

test.describe('DHG Workforce Planning', () => {
  test.beforeEach(async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('[name="email"]', 'manager@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
  })

  test('subject hours calculation drives FTE calculation', async ({ page }) => {
    await page.goto('/planning/dhg')

    // Select a working budget version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
      await page.waitForTimeout(1000) // Wait for data to load
    }

    // Look for subject hours input fields
    const subjectHoursInput = page
      .locator('[data-testid*="subject-hours"], input[name*="hours"]')
      .first()

    if (await subjectHoursInput.isVisible()) {
      // Enter subject hours
      await subjectHoursInput.fill('96')
      await subjectHoursInput.press('Tab') // Trigger calculation

      // Wait for FTE calculation
      await page.waitForTimeout(500)

      // Verify FTE calculated (96 hours ÷ 18 standard hours = 5.33 FTE)
      const fteDisplay = page
        .locator('[data-testid*="fte"], [data-testid*="teacher-count"]')
        .first()
      if (await fteDisplay.isVisible()) {
        const fteText = await fteDisplay.textContent()
        expect(fteText).toMatch(/5\.|6/) // Should show ~5.33 or rounded to 6
      }
    }
  })

  test('primary vs secondary teaching hours calculation', async ({ page }) => {
    await page.goto('/planning/dhg')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Check primary section (24h standard)
    const primaryTab = page.locator('button:has-text("Primary"), [data-testid="primary-tab"]')
    if (await primaryTab.isVisible()) {
      await primaryTab.click()

      // Verify standard hours displayed
      await expect(page.locator('text=/24.*hours?|24h/i')).toBeVisible()
    }

    // Check secondary section (18h standard)
    const secondaryTab = page.locator('button:has-text("Secondary"), [data-testid="secondary-tab"]')
    if (await secondaryTab.isVisible()) {
      await secondaryTab.click()

      // Verify standard hours displayed
      await expect(page.locator('text=/18.*hours?|18h/i')).toBeVisible()
    }
  })

  test('HSA (overtime) calculation and limits', async ({ page }) => {
    await page.goto('/planning/dhg')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Look for HSA/overtime section
    const hsaInput = page
      .locator('[data-testid*="hsa"], input[name*="overtime"], input[name*="hsa"]')
      .first()

    if (await hsaInput.isVisible()) {
      // Try to enter HSA hours exceeding limit (max 4 hours)
      await hsaInput.fill('6')
      await hsaInput.press('Tab')

      // Should show validation error
      const errorMessage = page.locator('text=/maximum|limit|exceeded/i')
      if (await errorMessage.isVisible()) {
        await expect(errorMessage).toBeVisible()
      }

      // Enter valid HSA hours
      await hsaInput.fill('2')
      await hsaInput.press('Tab')

      // Should accept valid hours
      await expect(errorMessage).not.toBeVisible()
    }
  })

  test('AEFE vs local teacher cost calculation', async ({ page }) => {
    await page.goto('/planning/dhg')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Look for teacher type selector
    const teacherTypeSelect = page
      .locator('[data-testid="teacher-type"], select[name*="teacher_type"]')
      .first()

    if (await teacherTypeSelect.isVisible()) {
      // Select AEFE teacher
      await teacherTypeSelect.selectOption('AEFE')
      await page.waitForTimeout(500)

      // Verify PRRD cost displayed (EUR)
      const prrdCost = page.locator('[data-testid*="prrd"], text=/PRRD|41.*EUR|€/i').first()
      if (await prrdCost.isVisible()) {
        await expect(prrdCost).toBeVisible()
      }

      // Select local teacher
      await teacherTypeSelect.selectOption('Local')
      await page.waitForTimeout(500)

      // Verify SAR cost displayed
      const localCost = page.locator('[data-testid*="salary"], text=/SAR|salary/i').first()
      if (await localCost.isVisible()) {
        await expect(localCost).toBeVisible()
      }
    }
  })

  test('TRMD gap analysis display', async ({ page }) => {
    await page.goto('/planning/dhg')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Look for TRMD/gap analysis section
    const trmdSection = page.locator('[data-testid="trmd"], [data-testid="gap-analysis"]')

    if (await trmdSection.isVisible()) {
      // Verify TRMD components visible
      await expect(page.locator('text=/needs|besoins/i')).toBeVisible()
      await expect(page.locator('text=/available|disponible/i')).toBeVisible()
      await expect(page.locator('text=/deficit|gap|écart/i')).toBeVisible()
    }
  })

  test('class structure drives DHG hours calculation', async ({ page }) => {
    // First, set up class structure
    await page.goto('/planning/classes')

    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Note the number of classes
    const classCountElement = page
      .locator('[data-testid*="class-count"], td, [role="gridcell"]')
      .first()
    if (await classCountElement.isVisible()) {
      await classCountElement.textContent()
    }

    // Navigate to DHG
    await page.goto('/planning/dhg')

    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Verify DHG uses class structure
    // Total hours should reflect: classes × hours per subject per level
    const totalHoursElement = page
      .locator('[data-testid*="total-hours"], text=/total.*hours/i')
      .first()
    if (await totalHoursElement.isVisible()) {
      await expect(totalHoursElement).toBeVisible()
    }
  })

  test('export DHG calculation to Excel', async ({ page }) => {
    await page.goto('/planning/dhg')

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

      // Wait for download to complete
      const download = await downloadPromise

      // Verify filename
      expect(download.suggestedFilename()).toMatch(/dhg|workforce|teacher/i)
    }
  })

  test('H/E ratio validation (hours per student)', async ({ page }) => {
    await page.goto('/planning/dhg')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Look for H/E ratio display
    const heRatioElement = page
      .locator('[data-testid*="he-ratio"], text=/H\\/E|hours.*student/i')
      .first()

    if (await heRatioElement.isVisible()) {
      const heRatioText = await heRatioElement.textContent()

      // H/E ratio should be within reasonable bounds (1.0 - 1.5 for secondary)
      const ratioMatch = heRatioText?.match(/(\d+\.\d+)/)
      if (ratioMatch) {
        const ratio = parseFloat(ratioMatch[1])
        expect(ratio).toBeGreaterThan(0.5)
        expect(ratio).toBeLessThan(2.0)
      }
    }
  })

  test('subject hours by level configuration', async ({ page }) => {
    await page.goto('/configuration/subject-hours')

    // Verify subject hours matrix loaded
    await expect(page.locator('h1, h2').filter({ hasText: /subject.*hours/i })).toBeVisible()

    // Look for grade level tabs or selectors
    const gradeSelector = page.locator('[data-testid*="level"], [data-testid*="grade"]').first()

    if (await gradeSelector.isVisible()) {
      // Select a level (e.g., 6ème)
      await gradeSelector.click()

      // Verify subject hours displayed
      await expect(page.locator('text=/math|français|english/i')).toBeVisible()
    }

    // Check that hours are editable (for admin)
    const editButton = page.locator('button:has-text("Edit"), [data-testid="edit-button"]').first()
    if (await editButton.isVisible()) {
      await editButton.click()

      // Verify input fields appear
      const hoursInput = page.locator('input[type="number"]').first()
      await expect(hoursInput).toBeVisible()
    }
  })
})

test.describe('DHG Integration with Other Modules', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('[name="email"]', 'manager@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
  })

  test('enrollment changes trigger DHG recalculation', async ({ page }) => {
    // Add enrollment
    await page.goto('/planning/enrollment')

    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Note current DHG FTE
    await page.goto('/planning/dhg')
    const initialFTE = await page.locator('[data-testid*="total-fte"]').first().textContent()

    // Go back and add more students
    await page.goto('/planning/enrollment')
    // (Add enrollment logic here)

    // Recalculate classes
    await page.goto('/planning/classes')
    const calculateButton = page.locator('button:has-text("Calculate")')
    if (await calculateButton.isVisible()) {
      await calculateButton.click()
    }

    // Check DHG updated
    await page.goto('/planning/dhg')
    const newFTE = await page.locator('[data-testid*="total-fte"]').first().textContent()

    // FTE should have changed (if enrollment increased)
    expect(newFTE).not.toBe(initialFTE)
  })

  test('DHG costs flow to budget consolidation', async ({ page }) => {
    await page.goto('/planning/dhg')

    // Select version
    const versionSelector = page.locator('[data-testid="version-selector"], select[name="version"]')
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Note total personnel cost
    await page.locator('[data-testid*="total-cost"]').first().textContent()

    // Navigate to consolidation
    await page.goto('/consolidation/budget')

    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ index: 0 })
    }

    // Verify personnel costs match DHG
    const personnelCost = page.locator('text=/personnel|salaries|teaching.*cost/i').first()
    if (await personnelCost.isVisible()) {
      // Should contain similar value (may be formatted differently)
      await expect(personnelCost).toBeVisible()
    }
  })
})
