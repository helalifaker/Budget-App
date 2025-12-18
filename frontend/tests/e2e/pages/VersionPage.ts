/**
 * Version Management Page Object
 * Encapsulates interactions with version configuration
 */

import { Page, Locator, expect } from '@playwright/test'
import { BasePage } from './BasePage'

export class VersionPage extends BasePage {
  readonly path = '/configuration/versions'

  constructor(page: Page) {
    super(page)
  }

  /**
   * Navigate to budget versions page
   */
  async navigate(): Promise<void> {
    await this.goto(this.path)
  }

  /**
   * Get create version button
   */
  getCreateButton(): Locator {
    return this.page.locator(
      'button:has-text("New Version"), button:has-text("Create"), [data-testid="create-version-button"]'
    )
  }

  /**
   * Get version name input
   */
  getNameInput(): Locator {
    return this.page.locator('[name="name"]')
  }

  /**
   * Get fiscal year input
   */
  getFiscalYearInput(): Locator {
    return this.page.locator('[name="fiscal_year"]')
  }

  /**
   * Get academic year input
   */
  getAcademicYearInput(): Locator {
    return this.page.locator('[name="academic_year"]')
  }

  /**
   * Get description input
   */
  getDescriptionInput(): Locator {
    return this.page.locator('[name="description"]')
  }

  /**
   * Create new budget version
   */
  async createVersion(
    name: string,
    fiscalYear: string,
    academicYear: string,
    description?: string
  ): Promise<void> {
    await this.getCreateButton().click()
    await this.page.waitForTimeout(500)

    await this.getNameInput().fill(name)
    await this.getFiscalYearInput().fill(fiscalYear)
    await this.getAcademicYearInput().fill(academicYear)

    if (description) {
      const descInput = this.getDescriptionInput()
      if (await descInput.isVisible()) {
        await descInput.fill(description)
      }
    }

    await this.getSaveButton().click()
    await this.waitForSuccess()
  }

  /**
   * Get version row by name
   */
  getVersionRow(versionName: string): Locator {
    return this.page.locator(`tr:has-text("${versionName}")`)
  }

  /**
   * Submit version for approval
   */
  async submitVersion(versionName: string): Promise<void> {
    const row = this.getVersionRow(versionName)
    const submitButton = row.locator('button:has-text("Submit"), [data-testid="submit-button"]')
    await submitButton.click()

    // Confirm if modal appears
    const confirmButton = this.page.locator('button:has-text("Confirm"), button:has-text("Yes")')
    if (await confirmButton.isVisible()) {
      await confirmButton.click()
    }

    await this.page.waitForTimeout(2000)
  }

  /**
   * Approve version
   */
  async approveVersion(versionName: string): Promise<void> {
    const row = this.getVersionRow(versionName)
    const approveButton = row.locator('button:has-text("Approve"), [data-testid="approve-button"]')
    await approveButton.click()

    // Confirm if modal appears
    const confirmButton = this.page.locator('button:has-text("Confirm"), button:has-text("Yes")')
    if (await confirmButton.isVisible()) {
      await confirmButton.click()
    }

    await this.page.waitForTimeout(2000)
  }

  /**
   * Verify version status
   */
  async verifyVersionStatus(versionName: string, expectedStatus: string): Promise<void> {
    const row = this.getVersionRow(versionName)
    await expect(row.locator(`text=/\\b${expectedStatus}\\b/i`)).toBeVisible({ timeout: 5000 })
  }

  /**
   * Copy version
   */
  async copyVersion(versionName: string, newName: string): Promise<void> {
    const row = this.getVersionRow(versionName)
    const copyButton = row.locator('button:has-text("Copy"), [data-testid="copy-button"]')

    if (await copyButton.isVisible()) {
      await copyButton.click()
      await this.page.waitForTimeout(500)

      await this.getNameInput().fill(newName)
      await this.getSaveButton().click()
      await this.waitForSuccess()
    }
  }

  /**
   * Delete version
   */
  async deleteVersion(versionName: string): Promise<void> {
    const row = this.getVersionRow(versionName)
    const deleteButton = row.locator('button:has-text("Delete"), [data-testid="delete-button"]')

    if (await deleteButton.isVisible()) {
      await deleteButton.click()

      // Confirm deletion
      const confirmButton = this.page.locator(
        'button:has-text("Confirm"), button:has-text("Delete")'
      )
      if (await confirmButton.isVisible()) {
        await confirmButton.click()
      }

      await this.page.waitForTimeout(2000)
    }
  }
}
