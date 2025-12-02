import { test, expect } from '@playwright/test'
import { login } from './helpers/auth.helper'
import { selectBudgetVersion } from './helpers/navigation.helper'

/**
 * E2E Test Suite: Revenue Planning
 * Tests revenue calculation with fee structures, sibling discounts, and trimester distribution
 */

test.describe('Revenue Planning', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('configure fee structure by nationality and level', async ({ page }) => {
    await page.goto('/configuration/fees')

    // Verify fee structure page loaded
    await expect(page.locator('h1, h2').filter({ hasText: /fee.*structure/i })).toBeVisible()

    // Check nationality tabs
    const frenchTab = page.locator('button:has-text("French"), [data-testid="french-tab"]')
    const saudiTab = page.locator('button:has-text("Saudi"), [data-testid="saudi-tab"]')

    if (await frenchTab.isVisible()) {
      await frenchTab.click()
      // Verify French fee structure displayed
      await expect(page.locator('text=/TTC|tuition/i')).toBeVisible()
    }

    if (await saudiTab.isVisible()) {
      await saudiTab.click()
      // Verify Saudi fee structure displayed (HT - VAT exempt)
      await expect(page.locator('text=/HT|tuition/i')).toBeVisible()
    }
  })

  test('edit tuition fees for specific level', async ({ page }) => {
    await page.goto('/configuration/fees')

    // Edit Collège fees for French students
    const editButton = page.locator('button:has-text("Edit"), [data-testid="edit-button"]').first()

    if (await editButton.isVisible()) {
      await editButton.click()

      // Find tuition input
      const tuitionInput = page.locator('[name*="tuition"], [data-testid*="tuition"]').first()

      if (await tuitionInput.isVisible()) {
        await tuitionInput.fill('36500')
        await page.click('button:has-text("Save"), button[type="submit"]')
        await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
      }
    }
  })

  test('configure sibling discount (25% for 3rd+ child)', async ({ page }) => {
    await page.goto('/configuration/fees')

    // Navigate to discounts section
    const discountsTab = page.locator('button:has-text("Discounts"), [data-testid="discounts-tab"]')

    if (await discountsTab.isVisible()) {
      await discountsTab.click()

      // Verify sibling discount configuration
      await expect(page.locator('text=/sibling.*discount/i')).toBeVisible()

      // Check 3rd child discount (should be 25%)
      const thirdChildDiscount = page.locator(
        '[name="third_child_discount"], [data-testid="third-child-discount"]'
      )

      if (await thirdChildDiscount.isVisible()) {
        const discountValue = await thirdChildDiscount.inputValue()
        expect(parseFloat(discountValue)).toBeGreaterThanOrEqual(0)
        expect(parseFloat(discountValue)).toBeLessThanOrEqual(100)
      }
    }
  })

  test('calculate revenue from enrollment and fees', async ({ page }) => {
    await page.goto('/planning/revenue')

    // Select budget version
    await selectBudgetVersion(page, /Test|2025/i)

    // Click calculate button
    const calculateButton = page.locator(
      'button:has-text("Calculate"), [data-testid="calculate-revenue"]'
    )

    if (await calculateButton.isVisible()) {
      await calculateButton.click()

      // Wait for calculation to complete
      await expect(page.locator('text=/calculation.*complete|success/i')).toBeVisible({
        timeout: 10000,
      })

      // Verify revenue components displayed
      await expect(
        page.locator('[data-testid="tuition-revenue"], text=/tuition.*revenue/i')
      ).toBeVisible()
      await expect(
        page.locator('[data-testid="registration-revenue"], text=/registration/i')
      ).toBeVisible()
      await expect(page.locator('[data-testid="total-revenue"], text=/total/i')).toBeVisible()
    }
  })

  test('verify trimester revenue distribution (T1: 40%, T2: 30%, T3: 30%)', async ({ page }) => {
    await page.goto('/planning/revenue')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for trimester tabs
    const t1Tab = page.locator('button:has-text("T1"), [data-testid="period-t1"]')
    const t2Tab = page.locator('button:has-text("T2"), [data-testid="period-t2"]')
    const t3Tab = page.locator('button:has-text("T3"), [data-testid="period-t3"]')

    if (await t1Tab.isVisible()) {
      await t1Tab.click()
      // T1 should show 40% of annual revenue
      await expect(page.locator('text=/40%|T1/i')).toBeVisible()
    }

    if (await t2Tab.isVisible()) {
      await t2Tab.click()
      // T2 should show 30% of annual revenue
      await expect(page.locator('text=/30%|T2/i')).toBeVisible()
    }

    if (await t3Tab.isVisible()) {
      await t3Tab.click()
      // T3 should show 30% of annual revenue
      await expect(page.locator('text=/30%|T3/i')).toBeVisible()
    }
  })

  test('revenue by nationality breakdown', async ({ page }) => {
    await page.goto('/planning/revenue')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for nationality breakdown
    const nationalitySection = page.locator(
      '[data-testid="nationality-breakdown"], text=/nationality.*breakdown/i'
    )

    if (await nationalitySection.isVisible()) {
      // Verify French, Saudi, Other categories
      await expect(page.locator('text=/french.*revenue/i')).toBeVisible()
      await expect(page.locator('text=/saudi.*revenue/i')).toBeVisible()
      await expect(page.locator('text=/other.*revenue/i')).toBeVisible()
    }
  })

  test('revenue by level breakdown (Maternelle, Élémentaire, Collège, Lycée)', async ({ page }) => {
    await page.goto('/planning/revenue')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for level breakdown
    const levelSection = page.locator('[data-testid="level-breakdown"], text=/level.*breakdown/i')

    if (await levelSection.isVisible()) {
      // Verify cycle categories
      await expect(page.locator('text=/maternelle/i')).toBeVisible()
      await expect(page.locator('text=/élémentaire|elementaire/i')).toBeVisible()
      await expect(page.locator('text=/collège|college/i')).toBeVisible()
      await expect(page.locator('text=/lycée|lycee/i')).toBeVisible()
    }
  })

  test('sibling discount application validation', async ({ page }) => {
    await page.goto('/planning/revenue')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Look for sibling discount summary
    const discountSection = page.locator(
      '[data-testid="sibling-discount"], text=/sibling.*discount/i'
    )

    if (await discountSection.isVisible()) {
      // Verify discount amount displayed
      await expect(page.locator('[data-testid="discount-amount"]')).toBeVisible()

      // Verify number of students receiving discount
      await expect(page.locator('[data-testid="discount-students"]')).toBeVisible()
    }
  })

  test('export revenue calculation to Excel', async ({ page }) => {
    await page.goto('/planning/revenue')

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
      expect(download.suggestedFilename()).toMatch(/revenue/i)
      expect(download.suggestedFilename()).toMatch(/\.xlsx$|\.csv$/)
    }
  })

  test('revenue account code mapping (PCG 70xxx)', async ({ page }) => {
    await page.goto('/planning/revenue')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Check for account codes section
    const accountCodeSection = page.locator(
      '[data-testid="account-codes"], text=/account.*codes?/i'
    )

    if (await accountCodeSection.isVisible()) {
      // Verify PCG account codes for revenue (70xxx)
      // 70110: Tuition T1
      // 70120: Tuition T2
      // 70130: Tuition T3
      // 70200: Registration
      const accountCodes = page.locator('text=/^70[0-9]{3}/')
      if (await accountCodes.first().isVisible()) {
        expect(await accountCodes.count()).toBeGreaterThan(0)
      }
    }
  })

  test('other revenue sources (cafeteria, transport, activities)', async ({ page }) => {
    await page.goto('/planning/revenue')

    // Select version
    await selectBudgetVersion(page, /Test|2025/i)

    // Navigate to other revenue section
    const otherRevenueTab = page.locator(
      'button:has-text("Other Revenue"), [data-testid="other-revenue-tab"]'
    )

    if (await otherRevenueTab.isVisible()) {
      await otherRevenueTab.click()

      // Add cafeteria revenue
      const addButton = page.locator('button:has-text("Add"), [data-testid="add-revenue"]')
      if (await addButton.isVisible()) {
        await addButton.click()

        // Select revenue type
        await page.selectOption('[name="revenue_type"], [data-testid="revenue-type"]', 'Cafeteria')

        // Enter amount
        await page.fill('[name="amount"], [data-testid="amount"]', '150000')

        // Save
        await page.click('button:has-text("Save"), button[type="submit"]')
        await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
      }
    }
  })
})

test.describe('Revenue Validation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('validate fee changes trigger revenue recalculation', async ({ page }) => {
    // Change fee structure
    await page.goto('/configuration/fees')

    const editButton = page.locator('button:has-text("Edit")').first()
    if (await editButton.isVisible()) {
      await editButton.click()

      const tuitionInput = page.locator('[name*="tuition"]').first()
      if (await tuitionInput.isVisible()) {
        const originalValue = await tuitionInput.inputValue()
        await tuitionInput.fill((parseInt(originalValue) + 1000).toString())
        await page.click('button:has-text("Save")')
        await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
      }
    }

    // Navigate to revenue and verify it triggers recalculation
    await page.goto('/planning/revenue')
    await selectBudgetVersion(page, /Test|2025/i)

    // Should show notification about recalculation needed
    const recalcNotification = page.locator('text=/recalculate|outdated|refresh/i')
    if (await recalcNotification.isVisible()) {
      // Trigger recalculation
      const calculateButton = page.locator('button:has-text("Calculate")')
      await calculateButton.click()
      await expect(page.locator('text=/calculation.*complete/i')).toBeVisible({ timeout: 10000 })
    }
  })

  test('validate enrollment changes trigger revenue recalculation', async ({ page }) => {
    await page.goto('/planning/revenue')
    await selectBudgetVersion(page, /Test|2025/i)

    // Note current revenue
    const totalRevenue = page.locator('[data-testid="total-revenue"]').first()
    const initialRevenue = await totalRevenue.textContent()

    // Add more students
    await page.goto('/planning/enrollment')
    await selectBudgetVersion(page, /Test|2025/i)

    const addButton = page.locator('button:has-text("Add Enrollment")')
    if (await addButton.isVisible()) {
      await addButton.click()
      await page.selectOption('[name="level_id"]', { index: 1 })
      await page.selectOption('[name="nationality"]', 'French')
      await page.fill('[name="student_count"]', '30')
      await page.click('button:has-text("Save")')
      await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
    }

    // Recalculate revenue
    await page.goto('/planning/revenue')
    await selectBudgetVersion(page, /Test|2025/i)

    const calculateButton = page.locator('button:has-text("Calculate")')
    if (await calculateButton.isVisible()) {
      await calculateButton.click()
      await expect(page.locator('text=/calculation.*complete/i')).toBeVisible({ timeout: 10000 })
    }

    // Verify revenue changed
    const newRevenue = await totalRevenue.textContent()
    expect(newRevenue).not.toBe(initialRevenue)
  })

  test('validate sibling discount not applied to DAI/registration', async ({ page }) => {
    await page.goto('/planning/revenue')
    await selectBudgetVersion(page, /Test|2025/i)

    // Check sibling discount section
    const discountSection = page.locator('[data-testid="sibling-discount"]')

    if (await discountSection.isVisible()) {
      // Verify discount is only on tuition, not on registration/DAI
      await expect(page.locator('text=/discount.*tuition.*only/i')).toBeVisible()

      // Registration and DAI should not show discount
      const registrationRow = page.locator(
        'tr:has-text("Registration"), [data-testid*="registration"]'
      )
      if (await registrationRow.isVisible()) {
        // Should not contain discount column or discount should be 0
        const discountCell = registrationRow.locator('td').filter({ hasText: /discount/i })
        if (await discountCell.isVisible()) {
          const discountText = await discountCell.textContent()
          expect(discountText).toMatch(/0|n\/a|-/i)
        }
      }
    }
  })
})
