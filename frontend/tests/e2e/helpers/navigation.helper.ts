/**
 * E2E Test Helper: Navigation
 * Reusable navigation helpers for E2E tests
 */

import { Page, expect } from '@playwright/test'

/**
 * Navigate to a route and wait for it to load
 */
export async function navigateTo(page: Page, path: string): Promise<void> {
  await page.goto(path)
  await page.waitForLoadState('networkidle')
}

/**
 * Select budget version from selector
 */
export async function selectBudgetVersion(page: Page, versionName: string | RegExp): Promise<void> {
  const versionSelector = page.locator(
    '[data-testid="version-selector"], select[name="version"], select[name="budget_version_id"]'
  )

  if (await versionSelector.isVisible()) {
    if (typeof versionName === 'string') {
      await versionSelector.selectOption({ label: versionName })
    } else {
      await versionSelector.selectOption({ label: versionName })
    }
    await page.waitForTimeout(1000) // Wait for data to load
  }
}

/**
 * Wait for AG Grid to load
 */
export async function waitForGridLoad(page: Page): Promise<void> {
  // Wait for AG Grid to render
  await page.waitForSelector('.ag-root-wrapper', { timeout: 10000 })

  // Wait for loading overlay to disappear
  await page.waitForSelector('.ag-overlay-loading-center', {
    state: 'hidden',
    timeout: 10000,
  })
}

/**
 * Navigate through module tabs
 */
export async function clickTab(page: Page, tabName: string): Promise<void> {
  const tab = page.locator(
    `button:has-text("${tabName}"), [data-testid="${tabName.toLowerCase()}-tab"]`
  )
  await tab.click()
  await page.waitForTimeout(500)
}

/**
 * Open dialog/modal by button text
 */
export async function openDialog(page: Page, buttonText: string): Promise<void> {
  const button = page.locator(
    `button:has-text("${buttonText}"), [data-testid*="${buttonText.toLowerCase()}"]`
  )
  await button.click()
  await page.waitForTimeout(500)
}

/**
 * Close dialog/modal
 */
export async function closeDialog(page: Page): Promise<void> {
  const closeButton = page
    .locator('button:has-text("Close"), button:has-text("Cancel"), [data-testid="close-button"]')
    .first()
  await closeButton.click()
  await page.waitForTimeout(300)
}

/**
 * Verify page title contains expected text
 */
export async function verifyPageTitle(page: Page, expectedText: string | RegExp): Promise<void> {
  const heading = page.locator('h1, h2').first()
  await expect(heading).toContainText(expectedText)
}
