/**
 * Sidebar Helper - Utilities for E2E tests with collapsible sidebar
 *
 * The AppSidebar uses hover-to-expand behavior:
 * - Collapsed: 64px width, icons only, text is opacity-0 w-0
 * - Expanded: 240px width, icons + labels visible
 * - Animation: 200ms transition
 *
 * These helpers ensure tests properly interact with the sidebar state.
 */

import { Page, Locator } from '@playwright/test'

/**
 * Wait for sidebar to fully expand after hover
 * @param page - Playwright page
 * @param sidebar - Sidebar locator
 * @param timeout - Wait duration in ms (default: 300ms to account for 200ms animation + buffer)
 */
export async function expandSidebar(
  page: Page,
  sidebar: Locator,
  timeout: number = 300
): Promise<void> {
  await sidebar.hover()
  await page.waitForTimeout(timeout)
}

/**
 * Get the desktop sidebar element
 * Uses the specific aside[role="navigation"] selector to avoid mobile nav
 */
export function getDesktopSidebar(page: Page): Locator {
  return page.locator('aside[role="navigation"][aria-label="Module navigation"]')
}

/**
 * Click a module in the sidebar
 * Automatically handles hover-to-expand and waits for animation
 *
 * @param page - Playwright page
 * @param moduleLabel - Module aria-label (e.g., "Enrollment", "Workforce")
 */
export async function clickSidebarModule(page: Page, moduleLabel: string): Promise<void> {
  const sidebar = getDesktopSidebar(page)
  await expandSidebar(page, sidebar)

  // Use aria-label instead of text content to avoid opacity-0 issues
  const moduleButton = sidebar.locator(`[aria-label="${moduleLabel}"]`)
  await moduleButton.click()
}

/**
 * Verify module is active in sidebar
 * Active modules have aria-current="page"
 */
export async function isModuleActive(page: Page, moduleLabel: string): Promise<boolean> {
  const sidebar = getDesktopSidebar(page)
  const moduleButton = sidebar.locator(`[aria-label="${moduleLabel}"]`)
  const ariaCurrent = await moduleButton.getAttribute('aria-current')
  return ariaCurrent === 'page'
}

/**
 * Get all visible module labels in the sidebar
 * Requires sidebar to be expanded first
 */
export async function getVisibleModules(page: Page): Promise<string[]> {
  const sidebar = getDesktopSidebar(page)
  await expandSidebar(page, sidebar)

  // Get all module buttons with aria-label
  const moduleButtons = sidebar.locator('button[aria-label]')
  const count = await moduleButtons.count()

  const labels: string[] = []
  for (let i = 0; i < count; i++) {
    const label = await moduleButtons.nth(i).getAttribute('aria-label')
    if (label && !label.includes('Command Center')) {
      labels.push(label)
    }
  }

  return labels
}

/**
 * Wait for sidebar to be visible and interactive
 * Useful for tests that navigate to a page and need to interact with sidebar
 */
export async function waitForSidebar(page: Page, timeout: number = 5000): Promise<Locator> {
  const sidebar = getDesktopSidebar(page)
  await sidebar.waitFor({ state: 'visible', timeout })
  return sidebar
}

/**
 * Verify all expected modules are present in sidebar
 * Does NOT require hover (uses aria-label which is always present)
 *
 * @param page - Playwright page
 * @param expectedModules - Array of module labels to check
 * @returns Object with missing and found modules
 */
export async function verifyModulesExist(
  page: Page,
  expectedModules: string[]
): Promise<{ found: string[]; missing: string[] }> {
  const sidebar = getDesktopSidebar(page)

  const found: string[] = []
  const missing: string[] = []

  for (const moduleLabel of expectedModules) {
    const moduleButton = sidebar.locator(`[aria-label="${moduleLabel}"]`)
    const exists = (await moduleButton.count()) > 0

    if (exists) {
      found.push(moduleLabel)
    } else {
      missing.push(moduleLabel)
    }
  }

  return { found, missing }
}

/**
 * Standard wait for page stabilization after navigation
 * Combines network idle wait with overlay dismissal
 */
export async function waitForPageStable(page: Page): Promise<void> {
  await page.waitForLoadState('networkidle')
  await page.waitForTimeout(500) // Allow for any animations to settle
  await dismissOverlays(page)
}

/**
 * Dismiss any open overlays/toasts/modals
 * (Copied from navigation.spec.ts for reuse)
 */
export async function dismissOverlays(page: Page): Promise<void> {
  // Try multiple approaches to close overlays
  for (let attempt = 0; attempt < 3; attempt++) {
    const overlay = page
      .locator('[data-state="open"][aria-hidden="true"].fixed.inset-0, [data-sonner-toast]')
      .first()

    if (await overlay.isVisible({ timeout: 500 }).catch(() => false)) {
      // Try pressing Escape first
      await page.keyboard.press('Escape')
      await page.waitForTimeout(300)

      // If still visible, try clicking the overlay backdrop to close
      if (await overlay.isVisible({ timeout: 300 }).catch(() => false)) {
        await overlay.click({ force: true }).catch(() => {})
        await page.waitForTimeout(300)
      }
    } else {
      break // No overlay visible, exit loop
    }
  }

  // Final wait for any overlays to be gone
  await page
    .locator('[data-state="open"].fixed.inset-0')
    .waitFor({ state: 'hidden', timeout: 2000 })
    .catch(() => {})
}

/**
 * Navigate to logo (Command Center)
 * Handles hover and click on the logo button
 */
export async function clickLogo(page: Page): Promise<void> {
  const sidebar = getDesktopSidebar(page)
  await expandSidebar(page, sidebar)

  const logoButton = sidebar.locator('[aria-label="Go to Command Center"]')
  await logoButton.click()
}
