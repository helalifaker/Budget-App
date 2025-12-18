/**
 * API Mock Helper for E2E Tests
 *
 * Provides Playwright route interception to mock backend API responses.
 * This makes tests independent of backend availability.
 */

import { Page, Route } from '@playwright/test'

// Store for created versions during tests
let mockVersions: BudgetVersion[] = [
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
 * Setup API mocking for version endpoints
 */
export async function setupVersionMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /budget-versions - list all versions
  await page.route(`${apiBaseUrl}/budget-versions*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: mockVersions,
          total: mockVersions.length,
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
      mockVersions.push(newVersion)
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
      const versionIndex = mockVersions.findIndex((v) => v.id === id)

      if (versionIndex >= 0) {
        mockVersions[versionIndex] = {
          ...mockVersions[versionIndex],
          ...requestBody,
          updated_at: new Date().toISOString(),
        }
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockVersions[versionIndex]),
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
      mockVersions = mockVersions.filter((v) => v.id !== id)
      await route.fulfill({
        status: 204,
      })
    } else if (method === 'GET') {
      // Single version fetch
      const id = url.split('/').pop()?.split('?')[0]
      const version = mockVersions.find((v) => v.id === id)
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
    const versionIndex = mockVersions.findIndex((v) => v.id === id)

    if (versionIndex >= 0) {
      mockVersions[versionIndex].status = 'submitted'
      mockVersions[versionIndex].updated_at = new Date().toISOString()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockVersions[versionIndex]),
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
    const versionIndex = mockVersions.findIndex((v) => v.id === id)

    if (versionIndex >= 0) {
      mockVersions[versionIndex].status = 'approved'
      mockVersions[versionIndex].updated_at = new Date().toISOString()
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockVersions[versionIndex]),
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
    const sourceVersion = mockVersions.find((v) => v.id === id)

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
      mockVersions.push(clonedVersion)
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
  mockVersions = [
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
 * Get current mock versions (for assertions)
 */
export function getMockVersions(): BudgetVersion[] {
  return [...mockVersions]
}

/**
 * Setup API mocking for DHG workforce planning endpoints
 */
export async function setupDHGMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /planning/dhg/subject-hours - subject hours matrix
  await page.route(`${apiBaseUrl}/planning/dhg/subject-hours*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'sh-1',
          subject_name: 'Mathematics',
          level_name: '6ème',
          hours_per_week: 4.5,
          is_split: false,
          number_of_classes: 3,
        },
        {
          id: 'sh-2',
          subject_name: 'French',
          level_name: '6ème',
          hours_per_week: 5,
          is_split: false,
          number_of_classes: 3,
        },
        {
          id: 'sh-3',
          subject_name: 'English',
          level_name: '6ème',
          hours_per_week: 3,
          is_split: true,
          number_of_classes: 3,
        },
      ]),
    })
  })

  // Mock GET /planning/dhg/teacher-requirements - FTE requirements
  await page.route(`${apiBaseUrl}/planning/dhg/teacher-requirements*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'tr-1',
          cycle_id: 'secondary',
          subject_id: 'math',
          required_hours: 54,
          standard_hours: 18,
          fte_required: 3.0,
          notes: null,
        },
        {
          id: 'tr-2',
          cycle_id: 'secondary',
          subject_id: 'french',
          required_hours: 60,
          standard_hours: 18,
          fte_required: 3.33,
          notes: null,
        },
        {
          id: 'tr-3',
          cycle_id: 'primary',
          subject_id: 'general',
          required_hours: 72,
          standard_hours: 24,
          fte_required: 3.0,
          notes: null,
        },
      ]),
    })
  })

  // Mock GET /planning/dhg/trmd-gap-analysis - TRMD gap analysis
  await page.route(`${apiBaseUrl}/planning/dhg/trmd-gap-analysis*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_deficit: 1.5,
        total_hsa_needed: 27,
        gaps: [
          {
            subject_id: 'math',
            cycle_id: 'secondary',
            required_fte: 3.0,
            aefe_allocated: 2.0,
            local_allocated: 0.5,
            total_allocated: 2.5,
            deficit: 0.5,
            hsa_needed: 9,
          },
          {
            subject_id: 'french',
            cycle_id: 'secondary',
            required_fte: 3.33,
            aefe_allocated: 2.0,
            local_allocated: 0.33,
            total_allocated: 2.33,
            deficit: 1.0,
            hsa_needed: 18,
          },
        ],
      }),
    })
  })

  // Mock POST /planning/dhg/calculate - trigger FTE calculation
  await page.route(`${apiBaseUrl}/planning/dhg/calculate*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        message: 'FTE calculation complete',
        total_fte: 9.33,
      }),
    })
  })

  // Mock class structure endpoint for integration tests
  await page.route(`${apiBaseUrl}/planning/classes*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            { id: 'cs-1', level: '6ème', number_of_classes: 3, students_per_class: 25 },
            { id: 'cs-2', level: '5ème', number_of_classes: 3, students_per_class: 25 },
            { id: 'cs-3', level: 'CP', number_of_classes: 2, students_per_class: 24 },
          ],
          total: 3,
        }),
      })
    } else {
      await route.continue()
    }
  })

  // Mock enrollment endpoint for integration tests
  await page.route(`${apiBaseUrl}/planning/enrollment*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'e-1',
              level: '6ème',
              total_students: 75,
              french_students: 40,
              foreign_students: 35,
            },
            {
              id: 'e-2',
              level: '5ème',
              total_students: 75,
              french_students: 38,
              foreign_students: 37,
            },
          ],
          total: 2,
        }),
      })
    } else {
      await route.continue()
    }
  })
}

/**
 * Setup API mocking for subject hours configuration
 */
export async function setupSubjectHoursMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  await page.route(`${apiBaseUrl}/configuration/subject-hours*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        items: [
          { id: 'cfg-1', subject: 'Mathematics', level: '6ème', hours: 4.5 },
          { id: 'cfg-2', subject: 'French', level: '6ème', hours: 5 },
          { id: 'cfg-3', subject: 'English', level: '6ème', hours: 3 },
        ],
        total: 3,
      }),
    })
  })
}

/**
 * Setup API mocking for KPI analysis endpoints
 */
export async function setupKPIMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /analysis/kpis - list all KPIs
  await page.route(`${apiBaseUrl}/analysis/kpis*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'kpi-1',
          title: 'Enrollment Capacity',
          value: 87.5,
          unit: '%',
          benchmark_min: 80,
          benchmark_max: 95,
          trend: 'UP',
          status: 'GOOD',
          previous_value: 85.0,
        },
        {
          id: 'kpi-2',
          title: 'H/E Ratio',
          value: 1.28,
          unit: 'hours/student',
          benchmark_min: 1.1,
          benchmark_max: 1.5,
          trend: 'STABLE',
          status: 'GOOD',
          previous_value: 1.25,
        },
        {
          id: 'kpi-3',
          title: 'E/D Ratio',
          value: 24.5,
          unit: 'students/class',
          benchmark_min: 20,
          benchmark_max: 30,
          trend: 'DOWN',
          status: 'GOOD',
          previous_value: 26.0,
        },
        {
          id: 'kpi-4',
          title: 'Operating Margin',
          value: 6.2,
          unit: '%',
          benchmark_min: 5,
          benchmark_max: 15,
          trend: 'UP',
          status: 'GOOD',
          previous_value: 4.5,
        },
        {
          id: 'kpi-5',
          title: 'Cost per Student',
          value: 42500,
          unit: 'SAR',
          benchmark_min: 35000,
          benchmark_max: 50000,
          trend: 'STABLE',
          status: 'WARNING',
          previous_value: 41000,
        },
        {
          id: 'kpi-6',
          title: 'Teacher Retention',
          value: 92,
          unit: '%',
          benchmark_min: 85,
          benchmark_max: 98,
          trend: 'UP',
          status: 'GOOD',
          previous_value: 88,
        },
      ]),
    })
  })
}

/**
 * Setup API mocking for Variance Analysis endpoints
 */
export async function setupVarianceMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /analysis/variance - variance report
  await page.route(`${apiBaseUrl}/analysis/variance*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_variance: 125000,
        favorable_count: 8,
        unfavorable_count: 4,
        generated_at: new Date().toISOString(),
        lines: [
          {
            account_code: '70110',
            description: 'Tuition Revenue T1',
            category: 'REVENUE',
            budget: 5000000,
            actual: 5150000,
            variance: 150000,
            variance_percent: 3.0,
            is_favorable: true,
            is_material: true,
          },
          {
            account_code: '70120',
            description: 'Tuition Revenue T2',
            category: 'REVENUE',
            budget: 3750000,
            actual: 3800000,
            variance: 50000,
            variance_percent: 1.33,
            is_favorable: true,
            is_material: false,
          },
          {
            account_code: '64110',
            description: 'Teaching Salaries',
            category: 'PERSONNEL',
            budget: 4200000,
            actual: 4350000,
            variance: -150000,
            variance_percent: -3.57,
            is_favorable: false,
            is_material: true,
          },
          {
            account_code: '64500',
            description: 'Social Charges',
            category: 'PERSONNEL',
            budget: 882000,
            actual: 913500,
            variance: -31500,
            variance_percent: -3.57,
            is_favorable: false,
            is_material: false,
          },
          {
            account_code: '61300',
            description: 'Rent',
            category: 'OPERATING',
            budget: 600000,
            actual: 580000,
            variance: 20000,
            variance_percent: 3.33,
            is_favorable: true,
            is_material: false,
          },
          {
            account_code: '61400',
            description: 'Utilities',
            category: 'OPERATING',
            budget: 120000,
            actual: 135000,
            variance: -15000,
            variance_percent: -12.5,
            is_favorable: false,
            is_material: true,
          },
        ],
      }),
    })
  })

  // Mock POST /analysis/import-actuals - import actuals
  await page.route(`${apiBaseUrl}/analysis/import-actuals*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        message: 'Actuals imported successfully',
        imported_count: 42,
      }),
    })
  })

  // Mock POST /analysis/forecast-revision - create forecast
  await page.route(`${apiBaseUrl}/analysis/forecast-revision*`, async (route: Route) => {
    await route.fulfill({
      status: 201,
      contentType: 'application/json',
      body: JSON.stringify({
        id: `forecast-${Date.now()}`,
        name: 'Forecast Revision',
        status: 'working',
        created_at: new Date().toISOString(),
      }),
    })
  })
}

/**
 * Setup API mocking for consolidation endpoints
 */
export async function setupConsolidationMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /consolidation/summary - budget summary
  await page.route(`${apiBaseUrl}/consolidation/summary*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        total_revenue: 12500000,
        total_expenses: 11750000,
        net_result: 750000,
        revenue_breakdown: {
          tuition: 10000000,
          registration: 1500000,
          other: 1000000,
        },
        expense_breakdown: {
          personnel: 8500000,
          operating: 2500000,
          capex: 750000,
        },
        generated_at: new Date().toISOString(),
      }),
    })
  })

  // Mock GET /consolidation/statements - financial statements
  await page.route(`${apiBaseUrl}/consolidation/statements*`, async (route: Route) => {
    const url = route.request().url()
    const params = new URL(url).searchParams
    const statementType = params.get('statement_type') || 'INCOME'

    let lines: Array<{
      code: string
      description: string
      level: number
      amount: number
      is_total: boolean
    }> = []

    if (statementType === 'INCOME') {
      lines = [
        { code: '70', description: 'Revenue', level: 0, amount: 12500000, is_total: true },
        { code: '701', description: 'Tuition Fees', level: 1, amount: 10000000, is_total: false },
        {
          code: '702',
          description: 'Registration Fees',
          level: 1,
          amount: 1500000,
          is_total: false,
        },
        { code: '708', description: 'Other Revenue', level: 1, amount: 1000000, is_total: false },
        { code: '60-68', description: 'Expenses', level: 0, amount: -11750000, is_total: true },
        { code: '64', description: 'Personnel Costs', level: 1, amount: -8500000, is_total: false },
        { code: '61', description: 'Operating Costs', level: 1, amount: -2500000, is_total: false },
        { code: '68', description: 'Depreciation', level: 1, amount: -750000, is_total: false },
        { code: 'NET', description: 'Net Result', level: 0, amount: 750000, is_total: true },
      ]
    } else if (statementType === 'BALANCE') {
      lines = [
        { code: '1-5', description: 'Assets', level: 0, amount: 25000000, is_total: true },
        { code: '2', description: 'Fixed Assets', level: 1, amount: 15000000, is_total: false },
        { code: '4', description: 'Receivables', level: 1, amount: 5000000, is_total: false },
        { code: '5', description: 'Cash', level: 1, amount: 5000000, is_total: false },
        {
          code: '1+4',
          description: 'Equity & Liabilities',
          level: 0,
          amount: 25000000,
          is_total: true,
        },
        { code: '1', description: 'Equity', level: 1, amount: 20000000, is_total: false },
        { code: '4', description: 'Payables', level: 1, amount: 5000000, is_total: false },
      ]
    } else {
      lines = [
        {
          code: 'OP',
          description: 'Operating Cash Flow',
          level: 0,
          amount: 1500000,
          is_total: true,
        },
        {
          code: 'INV',
          description: 'Investing Cash Flow',
          level: 0,
          amount: -750000,
          is_total: true,
        },
        { code: 'FIN', description: 'Financing Cash Flow', level: 0, amount: 0, is_total: true },
        { code: 'NET', description: 'Net Cash Flow', level: 0, amount: 750000, is_total: true },
      ]
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        statement_type: statementType,
        format: params.get('format') || 'PCG',
        period: params.get('period') || 'ANNUAL',
        generated_at: new Date().toISOString(),
        lines,
      }),
    })
  })
}

/**
 * Setup API mocking for Revenue Planning endpoints
 */
export async function setupRevenueMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /planning/revenue - revenue line items
  await page.route(`${apiBaseUrl}/planning/revenue*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'r-1',
              account_code: '70110',
              description: 'Tuition Revenue - Trimester 1',
              category: 'Tuition',
              t1_amount: 4000000,
              t2_amount: 0,
              t3_amount: 0,
              annual_amount: 4000000,
              is_auto_calculated: true,
              notes: null,
            },
            {
              id: 'r-2',
              account_code: '70120',
              description: 'Tuition Revenue - Trimester 2',
              category: 'Tuition',
              t1_amount: 0,
              t2_amount: 3000000,
              t3_amount: 0,
              annual_amount: 3000000,
              is_auto_calculated: true,
              notes: null,
            },
            {
              id: 'r-3',
              account_code: '70130',
              description: 'Tuition Revenue - Trimester 3',
              category: 'Tuition',
              t1_amount: 0,
              t2_amount: 0,
              t3_amount: 3000000,
              annual_amount: 3000000,
              is_auto_calculated: true,
              notes: null,
            },
            {
              id: 'r-4',
              account_code: '70200',
              description: 'Registration Fees',
              category: 'Enrollment Fees',
              t1_amount: 1500000,
              t2_amount: 0,
              t3_amount: 0,
              annual_amount: 1500000,
              is_auto_calculated: true,
              notes: null,
            },
            {
              id: 'r-5',
              account_code: '75100',
              description: 'Transportation',
              category: 'Other Revenue',
              t1_amount: 200000,
              t2_amount: 200000,
              t3_amount: 200000,
              annual_amount: 600000,
              is_auto_calculated: false,
              notes: 'School bus service',
            },
            {
              id: 'r-6',
              account_code: '75200',
              description: 'Cafeteria',
              category: 'Other Revenue',
              t1_amount: 150000,
              t2_amount: 150000,
              t3_amount: 150000,
              annual_amount: 450000,
              is_auto_calculated: false,
              notes: 'Meal service',
            },
          ],
          total: 6,
        }),
      })
    } else {
      await route.continue()
    }
  })

  // Mock POST /planning/revenue/calculate - calculate revenue
  await page.route(`${apiBaseUrl}/planning/revenue/calculate*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        status: 'success',
        message: 'Revenue calculation complete',
        total_revenue: 12550000,
      }),
    })
  })

  // Mock fee configuration endpoints
  await page.route(`${apiBaseUrl}/configuration/fees*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'f-1',
              nationality: 'French',
              level: 'Collège',
              tuition: 36000,
              registration: 2500,
              dai: 1500,
            },
            {
              id: 'f-2',
              nationality: 'Saudi',
              level: 'Collège',
              tuition: 30000,
              registration: 2500,
              dai: 1500,
            },
            {
              id: 'f-3',
              nationality: 'Other',
              level: 'Collège',
              tuition: 36000,
              registration: 2500,
              dai: 1500,
            },
          ],
          total: 3,
        }),
      })
    } else {
      await route.continue()
    }
  })
}

/**
 * Setup API mocking for Strategic Planning endpoints
 */
export async function setupStrategicMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /strategic - strategic plan data
  await page.route(`${apiBaseUrl}/strategic*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'sp-1',
              name: '5-Year Strategic Plan 2025-2030',
              base_year: 2025,
              years: 5,
              status: 'active',
              created_at: new Date().toISOString(),
            },
          ],
          total: 1,
        }),
      })
    } else {
      await route.continue()
    }
  })

  // Mock strategic projections
  await page.route(`${apiBaseUrl}/strategic/projections*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        enrollment: [
          { year: 2025, students: 1200 },
          { year: 2026, students: 1250 },
          { year: 2027, students: 1300 },
          { year: 2028, students: 1350 },
          { year: 2029, students: 1400 },
        ],
        revenue: [
          { year: 2025, amount: 45000000 },
          { year: 2026, amount: 48000000 },
          { year: 2027, amount: 51000000 },
          { year: 2028, amount: 54000000 },
          { year: 2029, amount: 58000000 },
        ],
        expenses: [
          { year: 2025, amount: 42000000 },
          { year: 2026, amount: 44000000 },
          { year: 2027, amount: 46000000 },
          { year: 2028, amount: 48000000 },
          { year: 2029, amount: 51000000 },
        ],
      }),
    })
  })
}

/**
 * Setup API mocking for Enrollment endpoints
 */
export async function setupEnrollmentMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock enrollment data
  await page.route(`${apiBaseUrl}/enrollment*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'enr-ps',
              level: 'PS',
              cycle: 'Maternelle',
              current_students: 48,
              new_students: 12,
              departures: 5,
              projected_total: 55,
            },
            {
              id: 'enr-ms',
              level: 'MS',
              cycle: 'Maternelle',
              current_students: 52,
              new_students: 8,
              departures: 4,
              projected_total: 56,
            },
            {
              id: 'enr-gs',
              level: 'GS',
              cycle: 'Maternelle',
              current_students: 55,
              new_students: 3,
              departures: 2,
              projected_total: 56,
            },
            {
              id: 'enr-cp',
              level: 'CP',
              cycle: 'Élémentaire',
              current_students: 54,
              new_students: 2,
              departures: 1,
              projected_total: 55,
            },
            {
              id: 'enr-6e',
              level: '6ème',
              cycle: 'Collège',
              current_students: 62,
              new_students: 5,
              departures: 3,
              projected_total: 64,
            },
          ],
          total: 5,
        }),
      })
    } else {
      await route.continue()
    }
  })

  // Mock planning enrollment endpoint
  await page.route(`${apiBaseUrl}/planning/enrollment*`, async (route: Route) => {
    if (route.request().method() === 'GET') {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          items: [
            {
              id: 'plan-enr-1',
              level: 'PS',
              cycle: 'Maternelle',
              current_students: 48,
              projected_total: 55,
            },
          ],
          total: 1,
        }),
      })
    } else {
      await route.continue()
    }
  })
}

/**
 * Setup API mocking for Subject Hours Matrix endpoints
 */
export async function setupSubjectHoursMatrixMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /configuration/subject-hours/matrix - subject hours matrix
  await page.route(`${apiBaseUrl}/configuration/subject-hours/matrix*`, async (route: Route) => {
    const url = route.request().url()
    const params = new URL(url).searchParams
    const cycleCode = params.get('cycle_code') || 'COLL'

    let levels: {
      id: string
      code: string
      name_en: string
      name_fr: string
      sort_order: number
    }[] = []

    if (cycleCode === 'COLL') {
      levels = [
        { id: '6eme', code: '6ème', name_en: '6th Grade', name_fr: 'Sixième', sort_order: 1 },
        { id: '5eme', code: '5ème', name_en: '5th Grade', name_fr: 'Cinquième', sort_order: 2 },
        { id: '4eme', code: '4ème', name_en: '4th Grade', name_fr: 'Quatrième', sort_order: 3 },
        { id: '3eme', code: '3ème', name_en: '3rd Grade', name_fr: 'Troisième', sort_order: 4 },
      ]
    } else if (cycleCode === 'LYC') {
      levels = [
        { id: '2nde', code: '2nde', name_en: '10th Grade', name_fr: 'Seconde', sort_order: 5 },
        { id: '1ere', code: '1ère', name_en: '11th Grade', name_fr: 'Première', sort_order: 6 },
        { id: 'term', code: 'Term', name_en: '12th Grade', name_fr: 'Terminale', sort_order: 7 },
      ]
    }

    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        cycle_code: cycleCode,
        levels,
        subjects: [
          {
            id: 'math',
            code: 'MATH',
            name_fr: 'Mathématiques',
            name_en: 'Mathematics',
            category: 'core',
            is_applicable: true,
            hours: Object.fromEntries(
              levels.map((l) => [l.id, { hours_per_week: 4.5, is_split: false, notes: null }])
            ),
          },
          {
            id: 'fran',
            code: 'FRAN',
            name_fr: 'Français',
            name_en: 'French',
            category: 'core',
            is_applicable: true,
            hours: Object.fromEntries(
              levels.map((l) => [l.id, { hours_per_week: 4.5, is_split: false, notes: null }])
            ),
          },
          {
            id: 'angl',
            code: 'ANGL',
            name_fr: 'Anglais',
            name_en: 'English',
            category: 'core',
            is_applicable: true,
            hours: Object.fromEntries(
              levels.map((l) => [l.id, { hours_per_week: 3.0, is_split: true, notes: 'LV1' }])
            ),
          },
          {
            id: 'hgeo',
            code: 'HGEO',
            name_fr: 'Histoire-Géographie',
            name_en: 'History-Geography',
            category: 'core',
            is_applicable: true,
            hours: Object.fromEntries(
              levels.map((l) => [l.id, { hours_per_week: 3.0, is_split: false, notes: null }])
            ),
          },
        ],
      }),
    })
  })

  // Mock POST /configuration/subject-hours/batch - batch save subject hours
  await page.route(`${apiBaseUrl}/configuration/subject-hours/batch*`, async (route: Route) => {
    if (route.request().method() === 'POST') {
      const requestBody = route.request().postDataJSON()
      const entriesCount = requestBody?.entries?.length || 0

      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          created_count: Math.floor(entriesCount / 2),
          updated_count: Math.ceil(entriesCount / 2),
          deleted_count: 0,
          errors: [],
        }),
      })
    } else {
      await route.continue()
    }
  })

  // Mock POST /configuration/subject-hours/apply-template - apply curriculum template
  await page.route(
    `${apiBaseUrl}/configuration/subject-hours/apply-template*`,
    async (route: Route) => {
      if (route.request().method() === 'POST') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            status: 'success',
            message: 'Template applied successfully',
            applied_count: 15,
            skipped_count: 0,
          }),
        })
      } else {
        await route.continue()
      }
    }
  )

  // Mock GET /configuration/templates - curriculum templates
  await page.route(`${apiBaseUrl}/configuration/templates*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          code: 'AEFE_STANDARD_COLL',
          name: 'AEFE Standard - Collège',
          description: 'Standard AEFE curriculum for middle school',
          cycle_codes: ['COLL'],
        },
        {
          code: 'AEFE_STANDARD_LYC',
          name: 'AEFE Standard - Lycée',
          description: 'Standard AEFE curriculum for high school',
          cycle_codes: ['LYC'],
        },
        {
          code: 'AEFE_STANDARD_ALL',
          name: 'AEFE Standard - Complete',
          description: 'Complete AEFE curriculum for all cycles',
          cycle_codes: ['MAT', 'ELEM', 'COLL', 'LYC'],
        },
      ]),
    })
  })

  // Mock POST /configuration/subjects - create new subject
  await page.route(`${apiBaseUrl}/configuration/subjects`, async (route: Route) => {
    if (route.request().method() === 'POST') {
      const requestBody = route.request().postDataJSON()
      await route.fulfill({
        status: 201,
        contentType: 'application/json',
        body: JSON.stringify({
          id: `new-subject-${Date.now()}`,
          code: requestBody.code,
          name_fr: requestBody.name_fr,
          name_en: requestBody.name_en,
          category: requestBody.category,
          applicable_cycles: requestBody.applicable_cycles,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }),
      })
    } else {
      await route.continue()
    }
  })
}

/**
 * Setup API mocking for Historical Import Admin endpoints
 *
 * IMPORTANT: Route registration order matters in Playwright!
 * Routes are matched in REVERSE order (LIFO - last registered is checked first).
 * The broad DELETE route pattern must be registered FIRST so it's checked LAST,
 * allowing more specific routes (preview, import, history, template) to match first.
 */
export async function setupHistoricalImportMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'
  console.log('[MOCK] Setting up historical import mocks...')

  // IMPORTANT: Register the broad DELETE route FIRST so it's checked LAST
  // This prevents it from intercepting preview/import/history/template requests
  // DELETE is for /admin/historical/:fiscalYear (numeric paths like /admin/historical/2024)
  console.log(`[MOCK] Registering DELETE route (first, checked last)`)
  await page.route(`${apiBaseUrl}/admin/historical/*`, async (route: Route) => {
    const method = route.request().method()
    const url = route.request().url()
    console.log(`[MOCK] DELETE route handler checking: ${method} ${url}`)

    // Only handle DELETE requests to fiscal year paths (numeric)
    // Let other requests pass through to more specific handlers
    if (method === 'DELETE') {
      console.log(`[MOCK] Handling DELETE request`)
      await route.fulfill({
        status: 204,
      })
    } else {
      // CRITICAL: Use route.fallback() instead of route.continue()
      // route.fallback() allows other matching routes to handle the request
      // route.continue() sends the request to the actual server
      console.log(`[MOCK] DELETE route falling back for ${method} request`)
      await route.fallback()
    }
  })

  // Mock GET /admin/historical/template/:module - download template
  console.log(`[MOCK] Registering template route`)
  await page.route(`${apiBaseUrl}/admin/historical/template/*`, async (route: Route) => {
    const url = route.request().url()
    const module = url.split('/').pop()
    console.log(`[MOCK] Intercepted template request: ${url}`)

    // Return a mock Excel blob
    await route.fulfill({
      status: 200,
      contentType: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      headers: {
        'Content-Disposition': `attachment; filename="historical_${module}_template.xlsx"`,
      },
      body: Buffer.from('mock excel content'),
    })
  })

  // Mock GET /admin/historical/history - import history
  const historyUrl = `${apiBaseUrl}/admin/historical/history*`
  console.log(`[MOCK] Registering history route: ${historyUrl}`)
  await page.route(historyUrl, async (route: Route) => {
    const method = route.request().method()
    console.log(`[MOCK] Intercepted history request: ${method} ${route.request().url()}`)
    if (method === 'GET') {
      console.log('[MOCK] Returning mock history response')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify([
          {
            id: 'import-1',
            fiscal_year: 2024,
            module: 'enrollment',
            imported_at: '2025-01-15T10:30:00Z',
            imported_by: 'admin@efir.local',
            record_count: 15,
            status: 'success',
          },
          {
            id: 'import-2',
            fiscal_year: 2024,
            module: 'revenue',
            imported_at: '2025-01-14T14:20:00Z',
            imported_by: 'admin@efir.local',
            record_count: 42,
            status: 'success',
          },
          {
            id: 'import-3',
            fiscal_year: 2023,
            module: 'costs',
            imported_at: '2025-01-12T09:15:00Z',
            imported_by: 'admin@efir.local',
            record_count: 58,
            status: 'partial',
          },
        ]),
      })
    } else {
      await route.fallback()
    }
  })

  // Mock POST /admin/historical/import - execute import
  const importUrl = `${apiBaseUrl}/admin/historical/import*`
  console.log(`[MOCK] Registering import route: ${importUrl}`)
  await page.route(importUrl, async (route: Route) => {
    const method = route.request().method()
    console.log(`[MOCK] Intercepted import request: ${method} ${route.request().url()}`)
    if (method === 'POST') {
      console.log('[MOCK] Returning mock import response')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          fiscal_year: 2024,
          module: 'enrollment',
          status: 'success',
          imported_count: 14,
          updated_count: 0,
          skipped_count: 1,
          error_count: 0,
          message: 'Import completed successfully',
          errors: [],
        }),
      })
    } else if (method === 'OPTIONS') {
      await route.fulfill({
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Credentials': 'true',
        },
        body: '',
      })
    } else {
      await route.fallback()
    }
  })

  // Mock POST /admin/historical/preview - preview import
  const previewUrl = `${apiBaseUrl}/admin/historical/preview*`
  console.log(`[MOCK] Registering preview route: ${previewUrl}`)
  await page.route(previewUrl, async (route: Route) => {
    const method = route.request().method()
    console.log(`[MOCK] Intercepted preview request: ${method} ${route.request().url()}`)
    if (method === 'POST') {
      console.log('[MOCK] Returning mock preview response')
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          fiscal_year: 2024,
          detected_module: 'enrollment',
          total_rows: 15,
          valid_rows: 14,
          invalid_rows: 1,
          warnings: ['Row 8: Student count seems unusually high (>500)'],
          errors: ['Row 12: Missing level_code'],
          sample_data: [
            { level_code: '6EME', level_name: 'Sixième', student_count: 120 },
            { level_code: '5EME', level_name: 'Cinquième', student_count: 118 },
            { level_code: 'CP', level_name: 'Cours Préparatoire', student_count: 95 },
            { level_code: 'CE1', level_name: 'Cours Élémentaire 1', student_count: 102 },
            { level_code: 'CM2', level_name: 'Cours Moyen 2', student_count: 88 },
          ],
          can_import: true,
        }),
      })
    } else if (method === 'OPTIONS') {
      await route.fulfill({
        status: 200,
        headers: {
          'Access-Control-Allow-Origin': '*',
          'Access-Control-Allow-Methods': 'POST, OPTIONS',
          'Access-Control-Allow-Headers': 'Content-Type',
          'Access-Control-Allow-Credentials': 'true',
        },
        body: '',
      })
    } else {
      await route.fallback()
    }
  })

  console.log('[MOCK] Historical import mocks setup complete')
}

/**
 * Setup API mocking for Historical Comparison endpoints (with-history)
 */
export async function setupHistoricalComparisonMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  const createHistoricalComparison = () => ({
    n_minus_2: { fiscal_year: 2022, value: 100, is_actual: true },
    n_minus_1: { fiscal_year: 2023, value: 110, is_actual: true },
    current: 120,
    vs_n_minus_1_abs: 10,
    vs_n_minus_1_pct: 9.09,
    vs_n_minus_2_abs: 20,
    vs_n_minus_2_pct: 20.0,
  })

  // Mock GET /planning/enrollment/:versionId/with-history
  await page.route(`${apiBaseUrl}/planning/enrollment/*/with-history*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        version_id: 'test-version',
        fiscal_year: 2024,
        current_fiscal_year: 2024,
        rows: [
          {
            level_id: 'level-1',
            level_code: '6EME',
            level_name: 'Sixième',
            student_count: 120,
            history: createHistoricalComparison(),
          },
          {
            level_id: 'level-2',
            level_code: '5EME',
            level_name: 'Cinquième',
            student_count: 118,
            history: createHistoricalComparison(),
          },
        ],
        totals: createHistoricalComparison(),
      }),
    })
  })

  // Mock GET /planning/dhg/:versionId/with-history
  await page.route(`${apiBaseUrl}/planning/dhg/*/with-history*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        version_id: 'test-version',
        fiscal_year: 2024,
        current_fiscal_year: 2024,
        rows: [
          {
            subject_id: 'subject-1',
            subject_code: 'MATH',
            subject_name: 'Mathématiques',
            total_hours: 150,
            fte: 8.33,
            hours_history: createHistoricalComparison(),
            fte_history: createHistoricalComparison(),
          },
        ],
        totals_hours: createHistoricalComparison(),
        totals_fte: createHistoricalComparison(),
      }),
    })
  })

  // Mock GET /planning/revenue/:versionId/with-history
  await page.route(`${apiBaseUrl}/planning/revenue/*/with-history*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({
        version_id: 'test-version',
        fiscal_year: 2024,
        current_fiscal_year: 2024,
        rows: [
          {
            account_code: '70100',
            account_name: 'Tuition Revenue',
            fee_type: 'tuition',
            amount_sar: 45000000,
            history: createHistoricalComparison(),
          },
        ],
        totals: createHistoricalComparison(),
      }),
    })
  })
}

/**
 * Setup API mocking for Configuration endpoints (levels, cycles)
 */
export async function setupConfigurationMocks(page: Page): Promise<void> {
  const apiBaseUrl = 'http://localhost:8000/api/v1'

  // Mock GET /configuration/levels - academic levels
  await page.route(`${apiBaseUrl}/configuration/levels*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'ps',
          code: 'PS',
          name_fr: 'Petite Section',
          name_en: 'Petite Section',
          cycle_id: 'mat',
          sort_order: 1,
        },
        {
          id: 'ms',
          code: 'MS',
          name_fr: 'Moyenne Section',
          name_en: 'Moyenne Section',
          cycle_id: 'mat',
          sort_order: 2,
        },
        {
          id: 'gs',
          code: 'GS',
          name_fr: 'Grande Section',
          name_en: 'Grande Section',
          cycle_id: 'mat',
          sort_order: 3,
        },
        {
          id: 'cp',
          code: 'CP',
          name_fr: 'Cours Préparatoire',
          name_en: 'CP',
          cycle_id: 'elem',
          sort_order: 4,
        },
        {
          id: 'ce1',
          code: 'CE1',
          name_fr: 'Cours Élémentaire 1',
          name_en: 'CE1',
          cycle_id: 'elem',
          sort_order: 5,
        },
        {
          id: 'ce2',
          code: 'CE2',
          name_fr: 'Cours Élémentaire 2',
          name_en: 'CE2',
          cycle_id: 'elem',
          sort_order: 6,
        },
        {
          id: 'cm1',
          code: 'CM1',
          name_fr: 'Cours Moyen 1',
          name_en: 'CM1',
          cycle_id: 'elem',
          sort_order: 7,
        },
        {
          id: 'cm2',
          code: 'CM2',
          name_fr: 'Cours Moyen 2',
          name_en: 'CM2',
          cycle_id: 'elem',
          sort_order: 8,
        },
        {
          id: '6eme',
          code: '6ème',
          name_fr: 'Sixième',
          name_en: '6th Grade',
          cycle_id: 'coll',
          sort_order: 9,
        },
        {
          id: '5eme',
          code: '5ème',
          name_fr: 'Cinquième',
          name_en: '5th Grade',
          cycle_id: 'coll',
          sort_order: 10,
        },
        {
          id: '4eme',
          code: '4ème',
          name_fr: 'Quatrième',
          name_en: '4th Grade',
          cycle_id: 'coll',
          sort_order: 11,
        },
        {
          id: '3eme',
          code: '3ème',
          name_fr: 'Troisième',
          name_en: '3rd Grade',
          cycle_id: 'coll',
          sort_order: 12,
        },
        {
          id: '2nde',
          code: '2nde',
          name_fr: 'Seconde',
          name_en: '10th Grade',
          cycle_id: 'lyc',
          sort_order: 13,
        },
        {
          id: '1ere',
          code: '1ère',
          name_fr: 'Première',
          name_en: '11th Grade',
          cycle_id: 'lyc',
          sort_order: 14,
        },
        {
          id: 'term',
          code: 'Term',
          name_fr: 'Terminale',
          name_en: '12th Grade',
          cycle_id: 'lyc',
          sort_order: 15,
        },
      ]),
    })
  })

  // Mock GET /configuration/cycles - academic cycles
  await page.route(`${apiBaseUrl}/configuration/cycles*`, async (route: Route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'mat',
          code: 'MAT',
          name_fr: 'Maternelle',
          name_en: 'Preschool',
          sort_order: 1,
          requires_atsem: true,
        },
        {
          id: 'elem',
          code: 'ELEM',
          name_fr: 'Élémentaire',
          name_en: 'Elementary',
          sort_order: 2,
          requires_atsem: false,
        },
        {
          id: 'coll',
          code: 'COLL',
          name_fr: 'Collège',
          name_en: 'Middle School',
          sort_order: 3,
          requires_atsem: false,
        },
        {
          id: 'lyc',
          code: 'LYC',
          name_fr: 'Lycée',
          name_en: 'High School',
          sort_order: 4,
          requires_atsem: false,
        },
      ]),
    })
  })
}
