/**
 * Base Page Object - Parent class for all page objects
 * Provides common functionality shared across all pages
 */

import { Page, Locator, expect } from '@playwright/test'

export class BasePage {
  protected page: Page

  constructor(page: Page) {
    this.page = page
  }

  /**
   * Navigate to a specific route
   */
  async goto(path: string): Promise<void> {
    await this.page.goto(path)
    await this.page.waitForLoadState('networkidle')
  }

  /**
   * Get page title
   */
  getTitle(): Locator {
    return this.page.locator('h1, h2').first()
  }

  /**
   * Verify page title
   */
  async verifyTitle(expectedText: string | RegExp): Promise<void> {
    await expect(this.getTitle()).toContainText(expectedText)
  }

  /**
   * Get version selector
   */
  getVersionSelector(): Locator {
    return this.page.locator(
      '[data-testid="version-selector"], select[name="version"], select[name="budget_version_id"]'
    )
  }

  /**
   * Select budget version
   */
  async selectVersion(versionName: string | RegExp): Promise<void> {
    const selector = this.getVersionSelector()
    if (await selector.isVisible()) {
      if (typeof versionName === 'string') {
        await selector.selectOption({ label: versionName })
      } else {
        await selector.selectOption({ label: versionName })
      }
      await this.page.waitForTimeout(1000)
    }
  }

  /**
   * Get export button
   */
  getExportButton(): Locator {
    return this.page.locator('button:has-text("Export"), [data-testid="export-button"]')
  }

  /**
   * Get save button
   */
  getSaveButton(): Locator {
    return this.page.locator('button:has-text("Save"), button[type="submit"]')
  }

  /**
   * Get cancel button
   */
  getCancelButton(): Locator {
    return this.page.locator('button:has-text("Cancel"), [data-testid="cancel-button"]')
  }

  /**
   * Wait for success message
   */
  async waitForSuccess(): Promise<void> {
    await expect(this.page.locator('text=/saved|success|complete/i')).toBeVisible({ timeout: 5000 })
  }

  /**
   * Wait for error message
   */
  async waitForError(): Promise<void> {
    await expect(this.page.locator('text=/error|failed|invalid/i')).toBeVisible({ timeout: 5000 })
  }

  /**
   * Check if element exists
   */
  async elementExists(selector: string): Promise<boolean> {
    return await this.page.locator(selector).isVisible()
  }

  /**
   * Wait for loading to complete
   */
  async waitForLoading(): Promise<void> {
    await this.page.waitForLoadState('networkidle')
  }
}
