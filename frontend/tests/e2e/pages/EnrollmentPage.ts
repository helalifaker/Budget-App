/**
 * Enrollment Planning Page Object
 * Encapsulates interactions with the enrollment planning module
 */

import { Page, Locator } from '@playwright/test'
import { BasePage } from './BasePage'

export class EnrollmentPage extends BasePage {
  readonly path = '/planning/enrollment'

  constructor(page: Page) {
    super(page)
  }

  /**
   * Navigate to enrollment planning page
   */
  async navigate(): Promise<void> {
    await this.goto(this.path)
  }

  /**
   * Get add enrollment button
   */
  getAddButton(): Locator {
    return this.page.locator(
      'button:has-text("Add Enrollment"), button:has-text("New"), [data-testid="add-enrollment"]'
    )
  }

  /**
   * Get level selector
   */
  getLevelSelector(): Locator {
    return this.page.locator('[name="level_id"], [data-testid="level-select"]')
  }

  /**
   * Get nationality selector
   */
  getNationalitySelector(): Locator {
    return this.page.locator('[name="nationality"], [data-testid="nationality-select"]')
  }

  /**
   * Get student count input
   */
  getStudentCountInput(): Locator {
    return this.page.locator('[name="student_count"], [data-testid="student-count"]')
  }

  /**
   * Add enrollment entry
   */
  async addEnrollment(level: string, nationality: string, count: number): Promise<void> {
    await this.getAddButton().click()
    await this.page.waitForTimeout(500)

    await this.getLevelSelector().selectOption(level)
    await this.getNationalitySelector().selectOption(nationality)
    await this.getStudentCountInput().fill(count.toString())

    await this.getSaveButton().click()
    await this.waitForSuccess()
  }

  /**
   * Get total enrollment display
   */
  getTotalEnrollment(): Locator {
    return this.page.locator('[data-testid="total-enrollment"], text=/total.*students?/i')
  }

  /**
   * Get enrollment by level
   */
  getEnrollmentByLevel(level: string): Locator {
    return this.page.locator(`[data-testid="enrollment-${level}"], tr:has-text("${level}")`)
  }

  /**
   * Calculate from previous year
   */
  async calculateFromPreviousYear(growthRate: number): Promise<void> {
    const calculateButton = this.page.locator(
      'button:has-text("Calculate"), [data-testid="calculate-from-previous"]'
    )
    await calculateButton.click()

    const growthRateInput = this.page.locator('[name="growth_rate"], [data-testid="growth-rate"]')
    if (await growthRateInput.isVisible()) {
      await growthRateInput.fill(growthRate.toString())
    }

    await this.getSaveButton().click()
    await this.waitForSuccess()
  }

  /**
   * Export enrollment data
   */
  async exportData(): Promise<void> {
    const downloadPromise = this.page.waitForEvent('download')
    await this.getExportButton().click()
    await downloadPromise
  }
}
