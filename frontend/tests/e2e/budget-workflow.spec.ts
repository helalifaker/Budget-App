import { test, expect } from '@playwright/test'

/**
 * E2E Test Suite: Budget Version Workflow
 * Tests the complete budget lifecycle: Create → Plan → Submit → Approve
 */

test.describe('Budget Version Workflow', () => {
  test.beforeEach(async ({ page }) => {
    // Login as manager to have full permissions
    await page.goto('/login')
    await page.fill('[name="email"]', 'manager@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
  })

  test('complete budget workflow: create, plan, submit, approve', async ({ page }) => {
    const testName = `Budget 2025 E2E Test ${Date.now()}`

    // Step 1: Create new budget version
    await page.goto('/configuration/versions')
    await expect(page.locator('h1, h2').filter({ hasText: /version/i })).toBeVisible()

    // Click create button
    await page.click(
      'button:has-text("New Version"), button:has-text("Create"), [data-testid="create-version-button"]'
    )

    // Fill form
    await page.fill('[name="name"]', testName)
    await page.fill('[name="fiscal_year"]', '2025')
    await page.fill('[name="academic_year"]', '2024-2025')

    // Optional fields
    const descriptionField = page.locator('[name="description"]')
    if (await descriptionField.isVisible()) {
      await descriptionField.fill('E2E test budget version for automated testing')
    }

    // Submit form
    await page.click('button[type="submit"]:has-text("Create"), button:has-text("Save")')

    // Verify version created
    await expect(page.locator(`text="${testName}"`)).toBeVisible({ timeout: 10000 })
    await expect(page.locator('text=/WORKING|Draft/i')).toBeVisible()

    // Step 2: Add enrollment data
    await page.goto('/planning/enrollment')

    // Select the version we just created
    const versionSelector = page.locator(
      '[data-testid="version-selector"], select[name="version"], select[name="budget_version_id"]'
    )
    if (await versionSelector.isVisible()) {
      await versionSelector.selectOption({ label: new RegExp(testName) })
    }

    // Add enrollment for a level
    const addButton = page
      .locator(
        'button:has-text("Add Enrollment"), button:has-text("New"), [data-testid="add-enrollment"]'
      )
      .first()
    if (await addButton.isVisible()) {
      await addButton.click()

      // Fill enrollment form
      await page.selectOption('[name="level_id"], [data-testid="level-select"]', { index: 1 })
      await page.selectOption('[name="nationality"], [data-testid="nationality-select"]', 'French')
      await page.fill('[name="student_count"], [data-testid="student-count"]', '25')

      // Save
      await page.click('button:has-text("Save"), button[type="submit"]')
      await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
    }

    // Step 3: Calculate class structure
    await page.goto('/planning/classes')

    // Select version
    const classVersionSelector = page.locator(
      '[data-testid="version-selector"], select[name="version"]'
    )
    if (await classVersionSelector.isVisible()) {
      await classVersionSelector.selectOption({ label: new RegExp(testName) })
    }

    // Calculate from enrollment
    const calculateButton = page.locator(
      'button:has-text("Calculate"), [data-testid="calculate-button"]'
    )
    if (await calculateButton.isVisible()) {
      await calculateButton.click()
      await expect(page.locator('text=/calculation|complete|success/i')).toBeVisible({
        timeout: 10000,
      })
    }

    // Step 4: Submit for approval
    await page.goto('/configuration/versions')

    // Find the version row and click submit
    const versionRow = page.locator(`tr:has-text("${testName}")`)
    await versionRow.locator('button:has-text("Submit"), [data-testid="submit-button"]').click()

    // Confirm if modal appears
    const confirmButton = page.locator('button:has-text("Confirm"), button:has-text("Yes")')
    if (await confirmButton.isVisible()) {
      await confirmButton.click()
    }

    // Verify status changed to SUBMITTED
    await expect(versionRow.locator('text=/SUBMITTED|Pending/i')).toBeVisible({ timeout: 5000 })

    // Step 5: Approve budget
    await versionRow.locator('button:has-text("Approve"), [data-testid="approve-button"]').click()

    // Confirm if modal appears
    const approveConfirm = page.locator('button:has-text("Confirm"), button:has-text("Yes")')
    if (await approveConfirm.isVisible()) {
      await approveConfirm.click()
    }

    // Verify status changed to APPROVED
    await expect(versionRow.locator('text=/APPROVED/i')).toBeVisible({ timeout: 5000 })
  })

  test('cannot submit incomplete budget version', async ({ page }) => {
    const testName = `Incomplete Budget ${Date.now()}`

    // Create version without any planning data
    await page.goto('/configuration/versions')
    await page.click('button:has-text("New Version"), button:has-text("Create")')

    await page.fill('[name="name"]', testName)
    await page.fill('[name="fiscal_year"]', '2025')
    await page.fill('[name="academic_year"]', '2024-2025')
    await page.click('button[type="submit"]:has-text("Create")')

    // Try to submit immediately
    const versionRow = page.locator(`tr:has-text("${testName}")`)
    const submitButton = versionRow.locator(
      'button:has-text("Submit"), [data-testid="submit-button"]'
    )

    if (await submitButton.isVisible()) {
      await submitButton.click()

      // Should show validation error
      await expect(page.locator('text=/validation|error|incomplete|required/i')).toBeVisible({
        timeout: 5000,
      })
    }
  })

  test('version workflow state transitions', async ({ page }) => {
    await page.goto('/configuration/versions')

    // Check that working version shows edit options
    const workingVersion = page.locator('tr:has-text(/WORKING|Draft/i)').first()
    if (await workingVersion.isVisible()) {
      await expect(
        workingVersion.locator('button:has-text("Edit"), [data-testid="edit-button"]')
      ).toBeVisible()
    }

    // Check that approved version has limited actions
    const approvedVersion = page.locator('tr:has-text(/APPROVED/i)').first()
    if (await approvedVersion.isVisible()) {
      const editButton = approvedVersion.locator('button:has-text("Edit")')
      // Edit should not be available for approved versions
      await expect(editButton).not.toBeVisible()
    }
  })

  test('copy existing version to create new one', async ({ page }) => {
    await page.goto('/configuration/versions')

    // Find an existing version to copy
    const existingVersion = page.locator('tr').first()
    const copyButton = existingVersion.locator(
      'button:has-text("Copy"), [data-testid="copy-button"]'
    )

    if (await copyButton.isVisible()) {
      await copyButton.click()

      // Fill new version details
      await page.fill('[name="name"]', `Copied Budget ${Date.now()}`)
      await page.fill('[name="fiscal_year"]', '2026')
      await page.click('button:has-text("Create"), button[type="submit"]')

      // Verify new version created with copied data
      await expect(page.locator('text=/copied|success/i')).toBeVisible({ timeout: 5000 })
    }
  })

  test('compare two budget versions', async ({ page }) => {
    await page.goto('/configuration/versions')

    // Select compare mode if available
    const compareButton = page.locator('button:has-text("Compare"), [data-testid="compare-button"]')
    if (await compareButton.isVisible()) {
      await compareButton.click()

      // Select two versions
      await page.selectOption('[data-testid="version-1-select"]', { index: 0 })
      await page.selectOption('[data-testid="version-2-select"]', { index: 1 })

      // View comparison
      await page.click('button:has-text("View Comparison"), button:has-text("Compare")')

      // Verify comparison view loaded
      await expect(page.locator('text=/comparison|variance|difference/i')).toBeVisible()
    }
  })
})

test.describe('Budget Version Permissions', () => {
  test('regular user cannot approve budgets', async ({ page }) => {
    // Login as regular user
    await page.goto('/login')
    await page.fill('[name="email"]', 'user@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    await page.goto('/configuration/versions')

    // Approve button should not exist or be disabled
    const approveButtons = page.locator(
      'button:has-text("Approve"), [data-testid="approve-button"]'
    )
    const count = await approveButtons.count()

    if (count > 0) {
      // If visible, should be disabled
      await expect(approveButtons.first()).toBeDisabled()
    }
  })

  test('user can view but not delete approved budgets', async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('[name="email"]', 'user@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    await page.goto('/configuration/versions')

    // Find approved version
    const approvedRow = page.locator('tr:has-text(/APPROVED/i)').first()

    if (await approvedRow.isVisible()) {
      // Delete button should not exist or be disabled
      const deleteButton = approvedRow.locator(
        'button:has-text("Delete"), [data-testid="delete-button"]'
      )
      if (await deleteButton.isVisible()) {
        await expect(deleteButton).toBeDisabled()
      }

      // View button should be enabled
      const viewButton = approvedRow.locator('button:has-text("View"), a:has-text("View")')
      if (await viewButton.isVisible()) {
        await expect(viewButton).toBeEnabled()
      }
    }
  })
})
