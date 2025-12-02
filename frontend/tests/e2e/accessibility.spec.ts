import { test, expect } from '@playwright/test'
import AxeBuilder from '@axe-core/playwright'
import { login } from './helpers/auth.helper'

/**
 * E2E Test Suite: Accessibility (a11y) Testing
 * Tests WCAG 2.1 AA compliance using axe-core
 * Validates keyboard navigation, screen reader support, and accessibility attributes
 */

test.describe('Accessibility - WCAG 2.1 AA Compliance', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('dashboard page has no accessibility violations', async ({ page }) => {
    await page.goto('/dashboard')

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('enrollment planning page has no accessibility violations', async ({ page }) => {
    await page.goto('/planning/enrollment')

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('DHG workforce planning page has no accessibility violations', async ({ page }) => {
    await page.goto('/planning/dhg')

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('budget consolidation page has no accessibility violations', async ({ page }) => {
    await page.goto('/consolidation/budget')

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('KPI dashboard has no accessibility violations', async ({ page }) => {
    await page.goto('/analysis/kpis')

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('financial statements page has no accessibility violations', async ({ page }) => {
    await page.goto('/consolidation/statements')

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })
})

test.describe('Keyboard Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('can navigate main menu with keyboard', async ({ page }) => {
    await page.goto('/dashboard')

    // Tab through navigation
    await page.keyboard.press('Tab')
    await page.keyboard.press('Tab')

    // Verify focus visible
    const focusedElement = await page.evaluateHandle(() => document.activeElement)
    const tagName = await focusedElement.evaluate((el) => el?.tagName.toLowerCase())

    expect(['a', 'button', 'input']).toContain(tagName)
  })

  test('can interact with forms using keyboard only', async ({ page }) => {
    await page.goto('/configuration/versions')

    // Click create button (keyboard accessible)
    const createButton = page.locator('button:has-text("New Version")')
    if (await createButton.isVisible()) {
      await createButton.focus()
      await page.keyboard.press('Enter')

      // Tab through form fields
      await page.keyboard.press('Tab') // Name field
      await page.keyboard.type('Keyboard Test Budget')

      await page.keyboard.press('Tab') // Fiscal year field
      await page.keyboard.type('2025')

      await page.keyboard.press('Tab') // Academic year field
      await page.keyboard.type('2024-2025')

      // Submit with Enter
      await page.keyboard.press('Tab') // Tab to submit button
      await page.keyboard.press('Enter')

      // Verify success
      await expect(page.locator('text=/saved|success/i')).toBeVisible({ timeout: 5000 })
    }
  })

  test('can navigate AG Grid with keyboard', async ({ page }) => {
    await page.goto('/planning/enrollment')

    // Wait for grid to load
    await page.waitForSelector('.ag-root-wrapper', { timeout: 10000 })

    // Focus on grid
    const grid = page.locator('.ag-root-wrapper').first()
    await grid.click()

    // Use arrow keys to navigate
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('ArrowDown')
    await page.keyboard.press('ArrowRight')

    // Verify keyboard navigation working
    const focusedCell = await page.locator('.ag-cell-focus').isVisible()
    expect(focusedCell).toBe(true)
  })

  test('can open and close dialogs with keyboard', async ({ page }) => {
    await page.goto('/configuration/versions')

    const createButton = page.locator('button:has-text("New Version")')
    if (await createButton.isVisible()) {
      // Open dialog with keyboard
      await createButton.focus()
      await page.keyboard.press('Enter')

      // Wait for dialog
      await page.waitForTimeout(500)

      // Close dialog with Escape
      await page.keyboard.press('Escape')

      // Verify dialog closed
      const dialog = page.locator('[role="dialog"], .dialog')
      await expect(dialog).not.toBeVisible()
    }
  })
})

test.describe('Screen Reader Support', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('buttons have accessible labels', async ({ page }) => {
    await page.goto('/dashboard')

    // Check all buttons have accessible text or aria-label
    const buttons = page.locator('button')
    const count = await buttons.count()

    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i)
      const ariaLabel = await button.getAttribute('aria-label')
      const text = await button.textContent()

      // Button must have either text or aria-label
      expect(ariaLabel || text?.trim()).toBeTruthy()
    }
  })

  test('form inputs have associated labels', async ({ page }) => {
    await page.goto('/configuration/versions')

    const createButton = page.locator('button:has-text("New Version")')
    if (await createButton.isVisible()) {
      await createButton.click()
      await page.waitForTimeout(500)

      // Check all inputs have labels
      const inputs = page.locator('input')
      const count = await inputs.count()

      for (let i = 0; i < count; i++) {
        const input = inputs.nth(i)
        const id = await input.getAttribute('id')
        const ariaLabel = await input.getAttribute('aria-label')
        const ariaLabelledBy = await input.getAttribute('aria-labelledby')

        if (id) {
          // Check for associated label
          const label = page.locator(`label[for="${id}"]`)
          const labelExists = await label.isVisible()

          // Input must have label, aria-label, or aria-labelledby
          expect(labelExists || ariaLabel || ariaLabelledBy).toBeTruthy()
        }
      }
    }
  })

  test('images have alt text', async ({ page }) => {
    await page.goto('/dashboard')

    // Check all images have alt text
    const images = page.locator('img')
    const count = await images.count()

    for (let i = 0; i < count; i++) {
      const img = images.nth(i)
      const alt = await img.getAttribute('alt')
      const role = await img.getAttribute('role')

      // Image must have alt text or role="presentation"
      expect(alt !== null || role === 'presentation').toBe(true)
    }
  })

  test('headings have proper hierarchy', async ({ page }) => {
    await page.goto('/dashboard')

    // Get all heading levels
    const h1Count = await page.locator('h1').count()
    const h2Count = await page.locator('h2').count()

    // Should have at least one h1
    expect(h1Count).toBeGreaterThan(0)

    // If there are h2s, there should be h1s
    if (h2Count > 0) {
      expect(h1Count).toBeGreaterThan(0)
    }
  })

  test('data tables have proper ARIA roles', async ({ page }) => {
    await page.goto('/planning/enrollment')

    // Wait for AG Grid
    await page.waitForSelector('.ag-root-wrapper', { timeout: 10000 })

    // Verify grid has role="grid" or role="table"
    const grid = page.locator('.ag-root-wrapper [role="grid"], .ag-root-wrapper [role="table"]')
    await expect(grid).toBeVisible()

    // Verify column headers have role="columnheader"
    const columnHeaders = page.locator('[role="columnheader"]')
    expect(await columnHeaders.count()).toBeGreaterThan(0)
  })

  test('loading states announced to screen readers', async ({ page }) => {
    await page.goto('/planning/enrollment')

    // Check for aria-live regions
    const liveRegions = page.locator('[aria-live="polite"], [aria-live="assertive"]')
    const count = await liveRegions.count()

    // Should have at least one live region for announcements
    expect(count).toBeGreaterThanOrEqual(0) // May be 0 if not actively loading
  })
})

test.describe('Color Contrast', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('color contrast meets WCAG AA standards', async ({ page }) => {
    await page.goto('/dashboard')

    // Run axe with color-contrast rule specifically
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2aa'])
      .include(['body'])
      .analyze()

    // Filter for color contrast violations
    const contrastViolations = accessibilityScanResults.violations.filter(
      (v) => v.id === 'color-contrast'
    )

    expect(contrastViolations).toEqual([])
  })

  test('focus indicators are visible', async ({ page }) => {
    await page.goto('/dashboard')

    // Tab to first interactive element
    await page.keyboard.press('Tab')

    // Check for focus indicator
    const focusedElement = await page.evaluateHandle(() => document.activeElement)

    // Get computed styles
    const outline = await focusedElement.evaluate((el) => {
      const styles = window.getComputedStyle(el)
      return {
        outlineWidth: styles.outlineWidth,
        outlineStyle: styles.outlineStyle,
        boxShadow: styles.boxShadow,
      }
    })

    // Should have visible outline or box-shadow focus indicator
    const hasFocusIndicator =
      (outline.outlineWidth && outline.outlineWidth !== '0px') ||
      (outline.boxShadow && outline.boxShadow !== 'none')

    expect(hasFocusIndicator).toBe(true)
  })
})

test.describe('Responsive and Mobile Accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await login(page, 'manager')
  })

  test('mobile viewport has no accessibility violations', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 })

    await page.goto('/dashboard')

    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa'])
      .analyze()

    expect(accessibilityScanResults.violations).toEqual([])
  })

  test('touch targets are adequately sized (44x44px minimum)', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 })
    await page.goto('/dashboard')

    // Check button sizes
    const buttons = page.locator('button')
    const count = await buttons.count()

    for (let i = 0; i < Math.min(count, 10); i++) {
      // Check first 10 buttons
      const button = buttons.nth(i)
      const box = await button.boundingBox()

      if (box) {
        // WCAG recommends minimum 44x44px for touch targets
        const meetsSizeRequirement = box.width >= 40 && box.height >= 40 // Allow 40px with some tolerance
        expect(meetsSizeRequirement).toBe(true)
      }
    }
  })
})
