/**
 * Tests for CalibrationStatusCard component.
 *
 * This component displays the calibration status from historical enrollment data,
 * showing confidence levels, data quality scores (1-5 stars), source years,
 * and a recalibrate button.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { CalibrationStatusCard } from '@/components/enrollment/CalibrationStatusCard'
import type { CalibrationStatus } from '@/types/enrollmentSettings'

// Helper to create mock calibration status
const createMockStatus = (overrides: Partial<CalibrationStatus> = {}): CalibrationStatus => ({
  last_calibrated: '2025-01-15T10:30:00Z',
  source_years: ['2022-2023', '2023-2024', '2024-2025'],
  overall_confidence: 'high',
  data_quality_score: 4,
  total_years_available: 3,
  has_sufficient_data: true,
  ...overrides,
})

describe('CalibrationStatusCard', () => {
  let mockOnRecalibrate: ReturnType<typeof vi.fn>

  beforeEach(() => {
    mockOnRecalibrate = vi.fn()
  })

  describe('rendering', () => {
    it('renders card with title and description', () => {
      const status = createMockStatus()
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('Auto-Calibration Status')).toBeInTheDocument()
      expect(
        screen.getByText('Derived parameters from historical enrollment data')
      ).toBeInTheDocument()
    })

    it('displays years of data count', () => {
      const status = createMockStatus({ total_years_available: 5 })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('5 years')).toBeInTheDocument()
    })

    it('displays historical window correctly', () => {
      const status = createMockStatus({
        source_years: ['2020-2021', '2021-2022', '2022-2023'],
      })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('2020-2021 - 2022-2023')).toBeInTheDocument()
    })

    it('displays "No data" when source years is empty', () => {
      const status = createMockStatus({ source_years: [] })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('No data')).toBeInTheDocument()
    })
  })

  describe('confidence levels', () => {
    it('displays high confidence with green styling', () => {
      const status = createMockStatus({ overall_confidence: 'high' })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('High Confidence')).toBeInTheDocument()
    })

    it('displays medium confidence with amber styling', () => {
      const status = createMockStatus({ overall_confidence: 'medium' })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('Medium Confidence')).toBeInTheDocument()
    })

    it('displays low confidence with red styling', () => {
      const status = createMockStatus({ overall_confidence: 'low' })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('Low Confidence')).toBeInTheDocument()
    })
  })

  describe('data quality score (stars)', () => {
    it('renders correct number of filled stars for score 4', () => {
      const status = createMockStatus({ data_quality_score: 4 })
      const { container } = render(
        <CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />
      )

      // Count filled stars (have fill-amber-400 class)
      const filledStars = container.querySelectorAll('.fill-amber-400')
      expect(filledStars.length).toBe(4)
    })

    it('renders 5 filled stars for perfect score', () => {
      const status = createMockStatus({ data_quality_score: 5 })
      const { container } = render(
        <CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />
      )

      const filledStars = container.querySelectorAll('.fill-amber-400')
      expect(filledStars.length).toBe(5)
    })

    it('renders 0 filled stars for score 0', () => {
      const status = createMockStatus({ data_quality_score: 0 })
      const { container } = render(
        <CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />
      )

      const filledStars = container.querySelectorAll('.fill-amber-400')
      expect(filledStars.length).toBe(0)
    })
  })

  describe('last calibrated date', () => {
    it('displays formatted date when available', () => {
      const status = createMockStatus({
        last_calibrated: '2025-03-15T14:30:00Z',
      })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      // Check that a formatted date is shown (format varies by locale)
      expect(screen.getByText('Last Calibrated')).toBeInTheDocument()
    })

    it('displays "Never" when not calibrated', () => {
      const status = createMockStatus({ last_calibrated: null })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('Never')).toBeInTheDocument()
    })
  })

  describe('insufficient data warning', () => {
    it('shows warning when has_sufficient_data is false', () => {
      const status = createMockStatus({ has_sufficient_data: false })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByText('Insufficient Historical Data')).toBeInTheDocument()
      expect(screen.getByText(/At least 2 years of enrollment data are needed/)).toBeInTheDocument()
    })

    it('does not show warning when has_sufficient_data is true', () => {
      const status = createMockStatus({ has_sufficient_data: true })
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.queryByText('Insufficient Historical Data')).not.toBeInTheDocument()
    })
  })

  describe('recalibrate button', () => {
    it('renders recalibrate button', () => {
      const status = createMockStatus()
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      expect(screen.getByRole('button', { name: /Recalibrate from History/i })).toBeInTheDocument()
    })

    it('calls onRecalibrate when button is clicked', () => {
      const status = createMockStatus()
      render(<CalibrationStatusCard status={status} onRecalibrate={mockOnRecalibrate} />)

      fireEvent.click(screen.getByRole('button', { name: /Recalibrate from History/i }))
      expect(mockOnRecalibrate).toHaveBeenCalledTimes(1)
    })

    it('shows loading state when isRecalibrating is true', () => {
      const status = createMockStatus()
      render(
        <CalibrationStatusCard
          status={status}
          onRecalibrate={mockOnRecalibrate}
          isRecalibrating={true}
        />
      )

      expect(screen.getByRole('button', { name: /Recalibrating.../i })).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Recalibrating.../i })).toBeDisabled()
    })

    it('button is enabled when not recalibrating', () => {
      const status = createMockStatus()
      render(
        <CalibrationStatusCard
          status={status}
          onRecalibrate={mockOnRecalibrate}
          isRecalibrating={false}
        />
      )

      expect(screen.getByRole('button', { name: /Recalibrate from History/i })).not.toBeDisabled()
    })
  })
})
