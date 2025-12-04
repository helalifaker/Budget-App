import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SummaryCard } from '@/components/SummaryCard'
import { DollarSign } from 'lucide-react'

describe('SummaryCard', () => {
  it('renders basic card with title and value', () => {
    render(<SummaryCard title="Total Students" value={1250} />)

    expect(screen.getByText('Total Students')).toBeInTheDocument()
    expect(screen.getByText('1250')).toBeInTheDocument()
  })

  it('renders string value', () => {
    render(<SummaryCard title="Status" value="Approved" />)

    expect(screen.getByText('Status')).toBeInTheDocument()
    expect(screen.getByText('Approved')).toBeInTheDocument()
  })

  it('renders number value', () => {
    render(<SummaryCard title="Count" value={42} />)

    expect(screen.getByText('Count')).toBeInTheDocument()
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('renders subtitle when provided', () => {
    render(<SummaryCard title="Revenue" value="1.2M SAR" subtitle="vs last year" />)

    expect(screen.getByText('Revenue')).toBeInTheDocument()
    expect(screen.getByText('1.2M SAR')).toBeInTheDocument()
    expect(screen.getByText('vs last year')).toBeInTheDocument()
  })

  it('renders icon when provided', () => {
    render(<SummaryCard title="Revenue" value="1.2M" icon={<DollarSign data-testid="icon" />} />)

    expect(screen.getByTestId('icon')).toBeInTheDocument()
  })

  it('renders upward trend indicator', () => {
    const { container } = render(
      <SummaryCard title="Enrollment" value={1300} trend="up" trendValue="+5.2%" />
    )

    expect(screen.getByText('+5.2%')).toBeInTheDocument()
    const trendElement = container.querySelector('.text-green-600')
    expect(trendElement).toBeInTheDocument()
  })

  it('renders downward trend indicator', () => {
    const { container } = render(
      <SummaryCard title="Costs" value="2.5M" trend="down" trendValue="-3.1%" />
    )

    expect(screen.getByText('-3.1%')).toBeInTheDocument()
    const trendElement = container.querySelector('.text-red-600')
    expect(trendElement).toBeInTheDocument()
  })

  it('does not render trend without trendValue', () => {
    render(<SummaryCard title="Test" value={100} trend="up" />)

    // Trend section should not be visible if trendValue is not provided
    expect(screen.queryByText(/text-green-600/)).not.toBeInTheDocument()
  })

  it('renders both trend and subtitle together', () => {
    render(
      <SummaryCard
        title="Operating Margin"
        value="12.5%"
        subtitle="Target: 10-15%"
        trend="up"
        trendValue="+2.3%"
      />
    )

    expect(screen.getByText('Operating Margin')).toBeInTheDocument()
    expect(screen.getByText('12.5%')).toBeInTheDocument()
    expect(screen.getByText('+2.3%')).toBeInTheDocument()
    expect(screen.getByText('Target: 10-15%')).toBeInTheDocument()
  })

  it('applies custom className to container', () => {
    const { container } = render(<SummaryCard title="Test" value={100} className="custom-class" />)

    const card = container.querySelector('.custom-class')
    expect(card).toBeInTheDocument()
  })

  it('applies custom valueClassName to value', () => {
    render(<SummaryCard title="Net Income" value="-50,000" valueClassName="text-red-600" />)

    const valueElement = screen.getByText('-50,000')
    expect(valueElement.className).toMatch(/text-red-600/)
  })

  it('renders without optional props', () => {
    render(<SummaryCard title="Simple Card" value="Value" />)

    expect(screen.getByText('Simple Card')).toBeInTheDocument()
    expect(screen.getByText('Value')).toBeInTheDocument()
    // Subtitle and trend should not be present
    expect(screen.queryByText(/text-gray-500/)).not.toBeInTheDocument()
  })

  it('formats large numbers correctly when passed as string', () => {
    render(<SummaryCard title="Budget" value="1,234,567 SAR" />)

    expect(screen.getByText('1,234,567 SAR')).toBeInTheDocument()
  })

  it('handles zero value', () => {
    render(<SummaryCard title="Deficit" value={0} />)

    expect(screen.getByText('Deficit')).toBeInTheDocument()
    expect(screen.getByText('0')).toBeInTheDocument()
  })

  it('handles negative value', () => {
    render(<SummaryCard title="Net Loss" value={-50000} />)

    expect(screen.getByText('Net Loss')).toBeInTheDocument()
    expect(screen.getByText('-50000')).toBeInTheDocument()
  })

  it('renders all features combined', () => {
    const { container } = render(
      <SummaryCard
        title="Total Revenue"
        value="2.5M SAR"
        subtitle="Annual"
        trend="up"
        trendValue="+12.5%"
        icon={<DollarSign data-testid="revenue-icon" />}
        className="revenue-card"
        valueClassName="text-green-700"
      />
    )

    expect(screen.getByText('Total Revenue')).toBeInTheDocument()
    expect(screen.getByText('2.5M SAR')).toBeInTheDocument()
    expect(screen.getByText('Annual')).toBeInTheDocument()
    expect(screen.getByText('+12.5%')).toBeInTheDocument()
    expect(screen.getByTestId('revenue-icon')).toBeInTheDocument()

    const card = container.querySelector('.revenue-card')
    expect(card).toBeInTheDocument()

    const valueElement = screen.getByText('2.5M SAR')
    expect(valueElement.className).toMatch(/text-green-700/)
  })

  it('applies hover effect class', () => {
    const { container } = render(<SummaryCard title="Test" value={100} />)

    const card = container.firstChild
    expect(card).toHaveClass('hover:shadow-md')
    expect(card).toHaveClass('transition-shadow')
  })
})
