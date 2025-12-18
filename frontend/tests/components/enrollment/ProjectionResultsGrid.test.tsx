/**
 * Tests for ProjectionResultsGrid component.
 *
 * This component displays enrollment projections with multi-level headers:
 * - Historical years (gray background)
 * - Base year (neutral)
 * - Projected years with R|L|T sub-columns (Retain | Lateral | Total)
 *
 * The R|L|T breakdown helps school directors understand:
 * - R (Retained): Students progressing from the previous grade
 * - L (Lateral): New lateral entries from outside
 * - T (Total): R + L combined
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ProjectionResultsGrid } from '@/components/enrollment/ProjectionResultsGrid'
import type { YearProjection, HistoricalYearData } from '@/types/enrollmentProjection'

// Helper to create mock projections (future years only, base year is separate)
const createMockProjections = (overrides: Partial<YearProjection>[] = []): YearProjection[] => {
  const baseProjections: YearProjection[] = [
    // Year +1 (first projection year)
    {
      school_year: '2026/2027',
      fiscal_year: 2027,
      grades: [
        {
          grade_code: 'PS',
          cycle_code: 'MAT',
          projected_students: 68,
          retained_students: 0,
          lateral_students: 68,
          divisions: 3,
          avg_class_size: 22.67,
        },
        {
          grade_code: 'MS',
          cycle_code: 'MAT',
          projected_students: 90,
          retained_students: 62,
          lateral_students: 28,
          divisions: 4,
          avg_class_size: 22.5,
        },
        {
          grade_code: 'GS',
          cycle_code: 'MAT',
          projected_students: 87,
          retained_students: 68,
          lateral_students: 19,
          divisions: 4,
          avg_class_size: 21.75,
        },
      ],
      total_students: 245,
      utilization_rate: 0.13,
      was_capacity_constrained: false,
    },
    // Year +2
    {
      school_year: '2027/2028',
      fiscal_year: 2028,
      grades: [
        {
          grade_code: 'PS',
          cycle_code: 'MAT',
          projected_students: 70,
          retained_students: 0,
          lateral_students: 70,
          divisions: 3,
          avg_class_size: 23.33,
        },
        {
          grade_code: 'MS',
          cycle_code: 'MAT',
          projected_students: 95,
          retained_students: 65,
          lateral_students: 30,
          divisions: 4,
          avg_class_size: 23.75,
        },
        {
          grade_code: 'GS',
          cycle_code: 'MAT',
          projected_students: 106,
          retained_students: 86,
          lateral_students: 20,
          divisions: 5,
          avg_class_size: 21.2,
        },
      ],
      total_students: 271,
      utilization_rate: 0.15,
      was_capacity_constrained: false,
    },
  ]

  return baseProjections.map((proj, index) => ({
    ...proj,
    ...(overrides[index] || {}),
  }))
}

// Helper to create mock historical data
const createMockHistoricalYears = (): HistoricalYearData[] => [
  {
    fiscal_year: 2024,
    school_year: '2023/2024',
    grades: { PS: 68, MS: 86, GS: 95 },
    total_students: 249,
  },
  {
    fiscal_year: 2025,
    school_year: '2024/2025',
    grades: { PS: 59, MS: 109, GS: 123 },
    total_students: 291,
  },
]

// Helper to create mock base year data (actual enrollment for base year)
const createMockBaseYearData = (): HistoricalYearData => ({
  fiscal_year: 2025,
  school_year: '2025/2026',
  grades: { PS: 65, MS: 71, GS: 68 },
  total_students: 204,
})

describe('ProjectionResultsGrid', () => {
  describe('rendering', () => {
    it('renders section header', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      expect(screen.getByText('Projection Results')).toBeInTheDocument()
    })

    it('renders empty state when no projections', () => {
      render(<ProjectionResultsGrid projections={[]} />)

      expect(screen.getByText('No projections yet.')).toBeInTheDocument()
    })

    it('renders grade column header', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      expect(screen.getByText('Grade')).toBeInTheDocument()
    })

    it('renders all grade rows', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      expect(screen.getByText('PS')).toBeInTheDocument()
      expect(screen.getByText('MS')).toBeInTheDocument()
      expect(screen.getByText('GS')).toBeInTheDocument()
    })

    it('renders total row', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      expect(screen.getByText('TOTAL')).toBeInTheDocument()
    })
  })

  describe('historical columns', () => {
    it('renders historical year columns when provided', () => {
      const projections = createMockProjections()
      const historical = createMockHistoricalYears()
      render(<ProjectionResultsGrid projections={projections} historical_years={historical} />)

      // Should show "Historical" section header
      expect(screen.getByText('Historical')).toBeInTheDocument()

      // Should show year format YY-YY (e.g., "23-24" for 2023/2024)
      expect(screen.getByText('23-24')).toBeInTheDocument()
      expect(screen.getByText('24-25')).toBeInTheDocument()
    })

    it('renders historical values for each grade', () => {
      const projections = createMockProjections()
      const historical = createMockHistoricalYears()
      render(<ProjectionResultsGrid projections={projections} historical_years={historical} />)

      // Historical values from 2023/2024 (first historical year)
      // Use getAllByText since values may appear multiple times
      const ps2023 = screen.getAllByText('86') // MS 2023 (unique value)
      expect(ps2023.length).toBeGreaterThan(0)

      const ms2023 = screen.getAllByText('95') // GS 2023 (unique value)
      expect(ms2023.length).toBeGreaterThan(0)
    })

    it('renders historical totals', () => {
      const projections = createMockProjections()
      const historical = createMockHistoricalYears()
      render(<ProjectionResultsGrid projections={projections} historical_years={historical} />)

      // Total for 2023/2024 historical year
      expect(screen.getByText('249')).toBeInTheDocument()
      // Total for 2024/2025 historical year
      expect(screen.getByText('291')).toBeInTheDocument()
    })

    it('sorts historical years oldest to newest', () => {
      const projections = createMockProjections()
      // Create historical data in reverse order
      const historical: HistoricalYearData[] = [
        {
          fiscal_year: 2025,
          school_year: '2024/2025',
          grades: { PS: 59, MS: 109, GS: 123 },
          total_students: 291,
        },
        {
          fiscal_year: 2024,
          school_year: '2023/2024',
          grades: { PS: 68, MS: 86, GS: 95 },
          total_students: 249,
        },
      ]
      render(<ProjectionResultsGrid projections={projections} historical_years={historical} />)

      // Get all table headers to verify order
      const headers = screen.getAllByRole('columnheader')
      // First historical column should be 23-24 (older), second should be 24-25 (newer)
      const histCols = headers.filter(
        (h) => h.textContent?.includes('23-24') || h.textContent?.includes('24-25')
      )
      expect(histCols[0].textContent).toContain('23-24')
    })
  })

  describe('base year column', () => {
    it('renders base year column when base_year_data is provided', () => {
      const projections = createMockProjections()
      const baseYearData = createMockBaseYearData()
      render(<ProjectionResultsGrid projections={projections} base_year_data={baseYearData} />)

      // Base year label
      expect(screen.getByText('Base')).toBeInTheDocument()
      // Base year format YY-YY (from school_year 2025/2026 -> "25-26")
      expect(screen.getByText('25-26')).toBeInTheDocument()
    })

    it('renders base year total from base_year_data', () => {
      const projections = createMockProjections()
      const baseYearData = createMockBaseYearData()
      render(<ProjectionResultsGrid projections={projections} base_year_data={baseYearData} />)

      // Base year total (204 students from base_year_data)
      expect(screen.getByText('204')).toBeInTheDocument()
    })

    it('does not render base year column when base_year_data is not provided', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // Base year label should NOT be present
      expect(screen.queryByText('Base')).not.toBeInTheDocument()
    })
  })

  describe('R|L|T sub-columns', () => {
    it('renders R, L, T sub-headers for projected years', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // Should have R and L headers for each projected year (2 projected years)
      // Note: There are 2 projected years (2026/2027 and 2027/2028), base year is separate
      const rHeaders = screen.getAllByText('R')
      const lHeaders = screen.getAllByText('L')
      const tHeaders = screen.getAllByText('T')

      expect(rHeaders.length).toBeGreaterThanOrEqual(2)
      expect(lHeaders.length).toBeGreaterThanOrEqual(2)
      expect(tHeaders.length).toBeGreaterThanOrEqual(2)
    })

    it('renders retain (R) values for non-PS grades', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // MS retained for year +1: 62 students
      // (Note: multiple "62" values may exist in the table)
      const cells = screen.getAllByText('62')
      expect(cells.length).toBeGreaterThan(0)
    })

    it('renders lateral (L) values', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // MS lateral for year +1: 28 students
      expect(screen.getByText('28')).toBeInTheDocument()
    })

    it('renders total (T) values', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // MS total for year +1: 90 students
      expect(screen.getByText('90')).toBeInTheDocument()
    })
  })

  describe('PS grade special case', () => {
    it('shows dash for PS grade retain column', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // PS has no retention (entry grade), should show '—' (em-dash) in R column
      // Find all em-dash cells - they represent PS retain values
      const dashes = screen.getAllByText('—')
      // Should have at least 2 dashes (one for each projected year)
      expect(dashes.length).toBeGreaterThanOrEqual(2)
    })

    it('shows PS lateral values', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // PS lateral for year +1: 68 students (all PS students are lateral)
      // Use getAllByText since this value may appear multiple times
      const psLateralCells = screen.getAllByText('68')
      expect(psLateralCells.length).toBeGreaterThan(0)
    })
  })

  describe('totals row calculation', () => {
    it('calculates correct total retained for projected year', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // Year +1 total retained:
      // PS: 0 + MS: 62 + GS: 68 = 130
      expect(screen.getByText('130')).toBeInTheDocument()
    })

    it('calculates correct total lateral for projected year', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // Year +1 total lateral:
      // PS: 68 + MS: 28 + GS: 19 = 115
      expect(screen.getByText('115')).toBeInTheDocument()
    })

    it('displays total students for projected year', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // Year +1 total: 245 students
      expect(screen.getByText('245')).toBeInTheDocument()
      // Year +2 total: 271 students
      expect(screen.getByText('271')).toBeInTheDocument()
    })
  })

  describe('capacity constraint indicator', () => {
    it('shows asterisk when year is capacity constrained', () => {
      const projections = createMockProjections([
        {}, // Base year - no override
        { was_capacity_constrained: true }, // Year +1 - constrained
      ])
      render(<ProjectionResultsGrid projections={projections} />)

      // Should show asterisk in the year header (use getAllByText in case multiple exist)
      const asterisks = screen.getAllByText('*')
      expect(asterisks.length).toBeGreaterThanOrEqual(1)
    })

    it('shows capacity legend when any year is constrained', () => {
      const projections = createMockProjections([
        {}, // Base year
        { was_capacity_constrained: true }, // Year +1 - constrained
      ])
      render(<ProjectionResultsGrid projections={projections} />)

      // Should show capacity constraint explanation in legend
      expect(screen.getByText(/Constrained by school max capacity/)).toBeInTheDocument()
    })

    it('hides capacity legend when no years are constrained', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      // Should not show capacity constraint explanation
      expect(screen.queryByText(/Constrained by school max capacity/)).not.toBeInTheDocument()
    })
  })

  describe('legend', () => {
    it('renders R legend explanation', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      expect(screen.getByText(/Retained \(from previous grade\)/)).toBeInTheDocument()
    })

    it('renders L legend explanation', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      expect(screen.getByText(/Lateral Entry \(new students\)/)).toBeInTheDocument()
    })

    it('renders T legend explanation', () => {
      const projections = createMockProjections()
      render(<ProjectionResultsGrid projections={projections} />)

      expect(screen.getByText(/Total \(R \+ L\)/)).toBeInTheDocument()
    })
  })
})
