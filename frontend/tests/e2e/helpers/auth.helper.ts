/**
 * E2E Test Helper: Authentication
 * Reusable authentication helpers for E2E tests
 */

import { Page, expect } from '@playwright/test'
import { TEST_USERS } from '../fixtures/test-data'

export type UserRole = keyof typeof TEST_USERS

/**
 * Login helper - Performs login and verifies successful authentication
 */
export async function login(page: Page, role: UserRole = 'manager'): Promise<void> {
  const user = TEST_USERS[role]

  await page.goto('/login')
  await page.fill('[name="email"]', user.email)
  await page.fill('[name="password"]', user.password)
  await page.click('button[type="submit"]')

  // Verify successful login by checking dashboard redirect
  await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
}

/**
 * Logout helper - Performs logout and verifies successful sign out
 */
export async function logout(page: Page): Promise<void> {
  // Look for logout button (may be in dropdown)
  const userMenu = page
    .locator('[data-testid="user-menu"], button:has([data-testid="user-avatar"])')
    .first()

  if (await userMenu.isVisible()) {
    await userMenu.click()
  }

  const logoutButton = page
    .locator(
      'button:has-text("Sign Out"), button:has-text("Logout"), [data-testid="logout-button"]'
    )
    .first()

  await logoutButton.click()

  // Verify redirect to login
  await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
}

/**
 * Check if user is authenticated
 */
export async function isAuthenticated(page: Page): Promise<boolean> {
  const currentUrl = page.url()
  return !currentUrl.includes('/login')
}

/**
 * Setup authenticated session - Use in beforeEach hooks
 */
export async function setupAuthenticatedSession(
  page: Page,
  role: UserRole = 'manager'
): Promise<void> {
  await login(page, role)

  // Wait for dashboard to fully load
  await page.waitForLoadState('networkidle')
}
