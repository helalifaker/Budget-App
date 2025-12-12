/**
 * Tests for SettingsReminderCard component.
 *
 * This component reminds users to configure lateral entry settings before planning.
 * It shows different states based on whether calibration is complete and
 * supports both full and compact display modes.
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { SettingsReminderCard } from '@/components/enrollment/SettingsReminderCard'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

// Wrapper for TanStack Router
const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  })

  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

import { vi } from 'vitest'

// Mock TanStack Router's Link component
vi.mock('@tanstack/react-router', async () => {
  const actual = await vi.importActual('@tanstack/react-router')
  return {
    ...actual,
    Link: ({
      children,
      to,
      ...props
    }: {
      children: React.ReactNode
      to: string
      [key: string]: unknown
    }) => (
      <a href={to} {...props}>
        {children}
      </a>
    ),
  }
})

describe('SettingsReminderCard', () => {
  describe('uncalibrated state (default)', () => {
    it('renders prompt to configure settings', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard />
        </TestWrapper>
      )

      expect(screen.getByText('Step 0: Configure Lateral Entry Settings')).toBeInTheDocument()
    })

    it('renders explanation text for unconfigured state', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard />
        </TestWrapper>
      )

      expect(
        screen.getByText(/Before running projections, configure your lateral entry rates/)
      ).toBeInTheDocument()
    })

    it('renders "Configure Settings" button', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard />
        </TestWrapper>
      )

      expect(screen.getByRole('link', { name: /Configure Settings/i })).toBeInTheDocument()
    })

    it('links to enrollment settings page', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard />
        </TestWrapper>
      )

      const link = screen.getByRole('link', { name: /Configure Settings/i })
      expect(link).toHaveAttribute('href', '/enrollment/settings')
    })

    it('has amber styling for unconfigured state', () => {
      const { container } = render(
        <TestWrapper>
          <SettingsReminderCard />
        </TestWrapper>
      )

      // Card should have amber border
      const card = container.querySelector('.border-l-amber-500')
      expect(card).toBeInTheDocument()
    })
  })

  describe('calibrated state', () => {
    it('renders configured title when calibrated', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} />
        </TestWrapper>
      )

      expect(screen.getByText('Step 0: Settings Configured')).toBeInTheDocument()
    })

    it('renders confirmation text when calibrated', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} />
        </TestWrapper>
      )

      expect(
        screen.getByText(/Your lateral entry rates and scenario multipliers are configured/)
      ).toBeInTheDocument()
    })

    it('renders "Review Settings" button when calibrated', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} />
        </TestWrapper>
      )

      expect(screen.getByRole('link', { name: /Review Settings/i })).toBeInTheDocument()
    })

    it('has green styling for configured state', () => {
      const { container } = render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} />
        </TestWrapper>
      )

      // Card should have green border
      const card = container.querySelector('.border-l-green-500')
      expect(card).toBeInTheDocument()
    })
  })

  describe('confidence level badge', () => {
    it('displays high confidence badge in green', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} confidenceLevel="high" />
        </TestWrapper>
      )

      expect(screen.getByText('high confidence')).toBeInTheDocument()
    })

    it('displays medium confidence badge in amber', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} confidenceLevel="medium" />
        </TestWrapper>
      )

      expect(screen.getByText('medium confidence')).toBeInTheDocument()
    })

    it('displays low confidence badge in red', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} confidenceLevel="low" />
        </TestWrapper>
      )

      expect(screen.getByText('low confidence')).toBeInTheDocument()
    })

    it('does not display badge when confidenceLevel is null', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} confidenceLevel={null} />
        </TestWrapper>
      )

      expect(screen.queryByText(/confidence/)).not.toBeInTheDocument()
    })
  })

  describe('compact mode', () => {
    it('renders minimal indicator when compact and calibrated', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} compact={true} />
        </TestWrapper>
      )

      expect(screen.getByText('Settings configured')).toBeInTheDocument()
      expect(screen.getByText('Review →')).toBeInTheDocument()
    })

    it('links to settings page in compact mode', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} compact={true} />
        </TestWrapper>
      )

      const link = screen.getByRole('link', { name: /Review →/i })
      expect(link).toHaveAttribute('href', '/enrollment/settings')
    })

    it('shows full card when compact but not calibrated', () => {
      render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={false} compact={true} />
        </TestWrapper>
      )

      // Should show full card, not compact view
      expect(screen.getByText('Step 0: Configure Lateral Entry Settings')).toBeInTheDocument()
    })
  })

  describe('custom className', () => {
    it('applies custom className', () => {
      const { container } = render(
        <TestWrapper>
          <SettingsReminderCard className="my-custom-class" />
        </TestWrapper>
      )

      expect(container.querySelector('.my-custom-class')).toBeInTheDocument()
    })

    it('applies custom className in compact mode', () => {
      const { container } = render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} compact={true} className="compact-custom" />
        </TestWrapper>
      )

      expect(container.querySelector('.compact-custom')).toBeInTheDocument()
    })
  })

  describe('icon rendering', () => {
    it('shows checkmark icon when calibrated', () => {
      const { container } = render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={true} />
        </TestWrapper>
      )

      // CheckCircle2 icon should be present
      const greenIcon = container.querySelector('.text-green-600')
      expect(greenIcon).toBeInTheDocument()
    })

    it('shows settings icon when not calibrated', () => {
      const { container } = render(
        <TestWrapper>
          <SettingsReminderCard isCalibrated={false} />
        </TestWrapper>
      )

      // Settings2 icon should be present
      const amberIcon = container.querySelector('.text-amber-600')
      expect(amberIcon).toBeInTheDocument()
    })
  })
})
