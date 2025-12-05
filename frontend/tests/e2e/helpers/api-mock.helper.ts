/**
 * API Mock Helper for E2E Tests
 *
 * Provides Playwright route interception to mock backend API responses.
 * This makes tests independent of backend availability.
 */

import { Page, Route } from '@playwright/test'

// Store for created budget versions during tests
let mockBudgetVersions: BudgetVersion[] = [
  {
    id: 'existing-version-1',
    name: 'Budget 2024-2025',
    fiscal_year: 2025,
    academic_year: '2024-2025',
    status: 'working',
    notes: 'Existing working budget',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 'existing-version-2',
    name: 'Budget 2023-2024 Approved',
    fiscal_year: 2024,
    academic_year: '2023-2024',
    status: 'approved',
    notes: 'Last year approved budget',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
]

interface BudgetVersion {
  id: string
  name: string
  fiscal_year: number
  academic_year: string
  status: string
  notes?: string
  created_at: string
  updated_at: string
}

/**
 * Setup API mocking for budget version endpoints
 */
export async function setupBudgetVersionMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /budget-versions - list all versions
  await page.route(`${apiBaseUrl}/budget-versions*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: mockBudgetVersions,
          total: mockBudgetVersions.length,
          page: 1,
          page_size: 50,
          pages: 1,
        }),
      })
    } else {
      await route.continue()
    }
  })

  // Mock POST /budget-versions - create new version
  await page.route(`${apiBaseUrl}/budget-versions`, async (route: Route) => {
    if (route.request().method() === 'POST') {
      const requestBody = route.request().postDataJSON()
      const newVersion: BudgetVersion = {
        id: `new-version-${Date.now()}`,
        name: requestBody.name,
        fiscal_year: requestBody.fiscal_year,
        academic_year: requestBody.academic_year,
        status: 'working',
        notes: requestBody.notes || '',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      mockBudgetVersions.push(newVersion)
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(newVersion),
      })
    } else {
      await route.continue()
    }
  })

  // Mock PUT /budget-versions/:id - update version
  await page.route(`${apiBaseUrl}/budget-versions/*`, async (route: Route) => {
    const url = route.request().url()
    const method = route.request().method()

    if (method === 'PUT' || method === 'PATCH') {
      const id = url.split('/').pop()?.split('?')[0]
      const requestBody = route.request().postDataJSON()
      const versionIndex = mockBudgetVersions.findIndex((v) => v.id === id)

      if (versionIndex >= 0) {
        mockBudgetVersions[versionIndex] = {
          ...mockBudgetVersions[versionIndex],
          ...requestBody,
          updated_at: new Date().toISOString(),
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockBudgetVersions[versionIndex]),
        })
      } else {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Version not found' }),
        })
      }
    } else if (method === 'DELETE') {
      const id = url.split('/').pop()?.split('?')[0]
      mockBudgetVersions = mockBudgetVersions.filter((v) => v.id !== id)
      await route.fulfill({
        status: 204,
      })
    } else if (method === 'GET') {
      // Single version fetch
      const id = url.split('/').pop()?.split('?')[0]
      const version = mockBudgetVersions.find((v) => v.id === id)
      if (version) {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(version),
        })
      } else {
        await route.fulfill({
          status: 404,
          contentType: 'application/json',
          body: JSON.stringify({ detail: 'Version not found' }),
        })
      }
    } else {
      await route.continue()
    }
  })

  // Mock POST /budget-versions/:id/submit - submit version
  await page.route(`${apiBaseUrl}/budget-versions/*/submit`, async (route: Route) => {
    const url = route.request().url()
    const id = url.split('/').slice(-2)[0]
    const versionIndex = mockBudgetVersions.findIndex((v) => v.id === id)

    if (versionIndex >= 0) {
      mockBudgetVersions[versionIndex].status = 'submitted'
      mockBudgetVersions[versionIndex].updated_at = new Date().toISOString()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBudgetVersions[versionIndex]),
      })
    } else {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Version not found' }),
      })
    }
  })

  // Mock POST /budget-versions/:id/approve - approve version
  await page.route(`${apiBaseUrl}/budget-versions/*/approve`, async (route: Route) => {
    const url = route.request().url()
    const id = url.split('/').slice(-2)[0]
    const versionIndex = mockBudgetVersions.findIndex((v) => v.id === id)

    if (versionIndex >= 0) {
      mockBudgetVersions[versionIndex].status = 'approved'
      mockBudgetVersions[versionIndex].updated_at = new Date().toISOString()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockBudgetVersions[versionIndex]),
      })
    } else {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Version not found' }),
      })
    }
  })

  // Mock POST /budget-versions/:id/clone - clone version
  await page.route(`${apiBaseUrl}/budget-versions/*/clone`, async (route: Route) => {
    const url = route.request().url()
    const id = url.split('/').slice(-2)[0]
    const requestBody = route.request().postDataJSON()
    const sourceVersion = mockBudgetVersions.find((v) => v.id === id)

    if (sourceVersion) {
      const clonedVersion: BudgetVersion = {
        id: `cloned-version-${Date.now()}`,
        name: requestBody.name,
        fiscal_year: sourceVersion.fiscal_year,
        academic_year: sourceVersion.academic_year,
        status: 'working',
        notes: `Cloned from ${sourceVersion.name}`,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      mockBudgetVersions.push(clonedVersion)
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify(clonedVersion),
      })
    } else {
      await route.fulfill({
        status: 404,
        contentType: 'application/json',
        body: JSON.stringify({ detail: 'Source version not found' }),
      })
    }
  })
}

/**
 * Reset mock data between tests
 */
export function resetMockData(): void {
  mockBudgetVersions = [
    {
      id: 'existing-version-1',
      name: 'Budget 2024-2025',
      fiscal_year: 2025,
      academic_year: '2024-2025',
      status: 'working',
      notes: 'Existing working budget',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
    {
      id: 'existing-version-2',
      name: 'Budget 2023-2024 Approved',
      fiscal_year: 2024,
      academic_year: '2023-2024',
      status: 'approved',
      notes: 'Last year approved budget',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    },
  ]
}

/**
 * Get current mock budget versions (for assertions)
 */
export function getMockBudgetVersions(): BudgetVersion[] {
  return [...mockBudgetVersions]
}
