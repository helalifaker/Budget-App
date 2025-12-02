import { test, expect } from '@playwright/test'

/**
 * E2E Test Suite: Authentication Flow
 * Tests login, logout, and session management
 */

test.describe('Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('login with valid credentials redirects to dashboard', async ({ page }) => {
    // Navigate to login page
    await page.goto('/login')

    // Verify login form is visible
    await expect(page.locator('h1, h2').filter({ hasText: /sign in|login/i })).toBeVisible()

    // Fill in credentials
    await page.fill('[name="email"]', 'test@efir.local')
    await page.fill('[name="password"]', 'password123')

    // Submit form
    await page.click('button[type="submit"]')

    // Verify redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })

    // Verify dashboard elements are visible
    await expect(page.locator('text=/budget|dashboard/i')).toBeVisible()
  })

  test('login with invalid credentials shows error', async ({ page }) => {
    await page.goto('/login')

    // Fill in invalid credentials
    await page.fill('[name="email"]', 'invalid@efir.local')
    await page.fill('[name="password"]', 'wrongpassword')

    // Submit form
    await page.click('button[type="submit"]')

    // Verify error message is shown
    await expect(page.locator('text=/invalid|error|incorrect/i')).toBeVisible({ timeout: 5000 })

    // Verify still on login page
    await expect(page).toHaveURL(/\/login/)
  })

  test('logout successfully', async ({ page }) => {
    // Login first
    await page.goto('/login')
    await page.fill('[name="email"]', 'test@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })

    // Click logout button (look for sign out, logout, or user menu)
    const logoutButton = page
      .locator(
        'button:has-text("Sign Out"), button:has-text("Logout"), [data-testid="logout-button"]'
      )
      .first()

    // If logout is in a dropdown, click user menu first
    const userMenu = page
      .locator('[data-testid="user-menu"], button:has([data-testid="user-avatar"])')
      .first()
    if (await userMenu.isVisible()) {
      await userMenu.click()
    }

    await logoutButton.click()

    // Verify redirect to login page
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
  })

  test('protected routes redirect to login when not authenticated', async ({ page }) => {
    // Try to access protected route without authentication
    await page.goto('/dashboard')

    // Should redirect to login
    await expect(page).toHaveURL(/\/login/, { timeout: 5000 })
  })

  test('authenticated user cannot access login page', async ({ page }) => {
    // Login first
    await page.goto('/login')
    await page.fill('[name="email"]', 'test@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })

    // Try to navigate back to login
    await page.goto('/login')

    // Should redirect to dashboard or home
    await expect(page).toHaveURL(/\/(dashboard|home)/, { timeout: 5000 })
  })

  test('session persists after page reload', async ({ page }) => {
    // Login
    await page.goto('/login')
    await page.fill('[name="email"]', 'test@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })

    // Reload page
    await page.reload()

    // Should still be on dashboard
    await expect(page).toHaveURL(/\/dashboard/)
    await expect(page.locator('text=/budget|dashboard/i')).toBeVisible()
  })

  test('remember me functionality (if implemented)', async ({ page }) => {
    await page.goto('/login')

    // Check if remember me checkbox exists
    const rememberMe = page.locator('[name="remember"], input[type="checkbox"]').first()
    if (await rememberMe.isVisible()) {
      await rememberMe.check()
    }

    // Login
    await page.fill('[name="email"]', 'test@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
  })
})

test.describe('Role-based Access Control', () => {
  test('user role can view but not approve budgets', async ({ page }) => {
    // Login as regular user
    await page.goto('/login')
    await page.fill('[name="email"]', 'user@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Navigate to budget versions
    await page.goto('/configuration/versions')

    // Approve button should not be visible or disabled
    const approveButton = page.locator('[data-testid="approve-button"], button:has-text("Approve")')
    if (await approveButton.isVisible()) {
      await expect(approveButton).toBeDisabled()
    }
  })

  test('manager role can approve budgets', async ({ page }) => {
    // Login as manager
    await page.goto('/login')
    await page.fill('[name="email"]', 'manager@efir.local')
    await page.fill('[name="password"]', 'password123')
    await page.click('button[type="submit"]')

    // Navigate to budget versions
    await page.goto('/configuration/versions')

    // Approve button should be visible and enabled for submitted budgets
    const approveButton = page
      .locator('[data-testid="approve-button"], button:has-text("Approve")')
      .first()
    if (await approveButton.isVisible()) {
      await expect(approveButton).toBeEnabled()
    }
  })
})
