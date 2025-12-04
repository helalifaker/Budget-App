import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { KPICard } from '@/components/KPICard'

describe('KPICard', () => {
  it('renders basic KPI with title, value, and unit', () => {
    render(<KPICard title="Student Count" value={1250} unit="students" />)

    expect(screen.getByText('Student Count')).toBeInTheDocument()
    expect(screen.getByText('1250.00')).toBeInTheDocument()
    expect(screen.getByText('students')).toBeInTheDocument()
  })

  it('renders string value without decimal formatting', () => {
    render(<KPICard title="Budget Status" value="Approved" unit="" />)

    expect(screen.getByText('Budget Status')).toBeInTheDocument()
    expect(screen.getByText('Approved')).toBeInTheDocument()
  })

  it('displays status badge with correct status', () => {
    const { rerender } = render(<KPICard title="Test KPI" value={100} unit="%" status="good" />)
    expect(screen.getByText('GOOD')).toBeInTheDocument()

    rerender(<KPICard title="Test KPI" value={100} unit="%" status="warning" />)
    expect(screen.getByText('WARNING')).toBeInTheDocument()

    rerender(<KPICard title="Test KPI" value={100} unit="%" status="alert" />)
    expect(screen.getByText('ALERT')).toBeInTheDocument()
  })

  it('applies correct CSS classes for status colors', () => {
    const { container, rerender } = render(
      <KPICard title="Test KPI" value={100} unit="%" status="good" />
    )

    let card = container.querySelector('.bg-green-100')
    expect(card).toBeInTheDocument()

    rerender(<KPICard title="Test KPI" value={100} unit="%" status="warning" />)
    card = container.querySelector('.bg-yellow-100')
    expect(card).toBeInTheDocument()

    rerender(<KPICard title="Test KPI" value={100} unit="%" status="alert" />)
    card = container.querySelector('.bg-red-100')
    expect(card).toBeInTheDocument()
  })

  it('displays benchmark range when provided', () => {
    render(
      <KPICard title="H/E Ratio" value={1.25} unit="h/student" benchmark={{ min: 1.1, max: 1.4 }} />
    )

    expect(screen.getByText(/Benchmark: 1\.10 - 1\.40 h\/student/)).toBeInTheDocument()
  })

  it('displays upward trend indicator correctly', () => {
    render(
      <KPICard title="Enrollment" value={1300} unit="students" trend="up" previousValue={1250} />
    )

    // Should show "+50.00 vs previous"
    expect(screen.getByText(/\+50\.00 vs previous/)).toBeInTheDocument()
  })

  it('displays downward trend indicator correctly', () => {
    render(
      <KPICard
        title="Cost per Student"
        value={45000}
        unit="SAR"
        trend="down"
        previousValue={47000}
      />
    )

    // Should show "-2000.00 vs previous" (absolute value)
    expect(screen.getByText(/-2000\.00 vs previous/)).toBeInTheDocument()
  })

  it('displays stable trend indicator correctly', () => {
    render(<KPICard title="Teacher FTE" value={85} unit="FTE" trend="stable" previousValue={85} />)

    // Should show "0.00 vs previous" with no +/- sign
    expect(screen.getByText(/0\.00 vs previous/)).toBeInTheDocument()
    expect(screen.queryByText(/\+/)).not.toBeInTheDocument()
    expect(screen.queryByText(/-/)).not.toBeInTheDocument()
  })

  it('does not display trend when previousValue is not provided', () => {
    render(<KPICard title="Test KPI" value={100} unit="%" trend="up" />)

    expect(screen.queryByText(/vs previous/)).not.toBeInTheDocument()
  })

  it('does not display trend when trend is not provided', () => {
    render(<KPICard title="Test KPI" value={100} unit="%" previousValue={90} />)

    expect(screen.queryByText(/vs previous/)).not.toBeInTheDocument()
  })

  it('displays all features combined', () => {
    render(
      <KPICard
        title="Operating Margin"
        value={12.5}
        unit="%"
        status="good"
        benchmark={{ min: 10, max: 15 }}
        trend="up"
        previousValue={11.2}
      />
    )

    expect(screen.getByText('Operating Margin')).toBeInTheDocument()
    expect(screen.getByText('12.50')).toBeInTheDocument()
    expect(screen.getByText('%')).toBeInTheDocument()
    expect(screen.getByText('GOOD')).toBeInTheDocument()
    expect(screen.getByText(/Benchmark: 10\.00 - 15\.00 %/)).toBeInTheDocument()
    expect(screen.getByText(/\+1\.30 vs previous/)).toBeInTheDocument()
  })

  it('formats decimal values to 2 decimal places', () => {
    render(<KPICard title="Ratio" value={1.2567} unit="ratio" />)

    expect(screen.getByText('1.26')).toBeInTheDocument()
  })

  it('handles zero values correctly', () => {
    render(<KPICard title="Deficit" value={0} unit="SAR" />)

    expect(screen.getByText('0.00')).toBeInTheDocument()
  })

  it('handles negative values correctly', () => {
    render(<KPICard title="Net Income" value={-50000} unit="SAR" status="alert" />)

    expect(screen.getByText('-50000.00')).toBeInTheDocument()
    expect(screen.getByText('ALERT')).toBeInTheDocument()
  })

  it('calculates trend difference correctly for string values', () => {
    // When value is string, trend calculation returns 0 (design limitation)
    render(<KPICard title="Status" value="Active" unit="" trend="up" previousValue={100} />)

    // Should show "0.00 vs previous" since string values don't support trend calculation
    expect(screen.getByText(/\+0\.00 vs previous/)).toBeInTheDocument()
  })
})
