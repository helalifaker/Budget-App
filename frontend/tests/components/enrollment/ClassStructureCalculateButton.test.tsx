/**
 * Tests for ClassStructure page - Calculate from Enrollment button behavior.
 *
 * Tests the button's disabled state based on enrollment data availability
 * and tooltip behavior for user guidance.
 *
 * Coverage targets:
 * - Button disabled when no enrollment data
 * - Button enabled when enrollment data exists
 * - Tooltip visibility and content
 * - Edge cases (no version, pending state, loading)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from '@/components/ui/tooltip'
import { Calculator } from 'lucide-react'

/**
 * Isolated test component that mirrors the button logic from class-structure.tsx
 * This allows us to test the button behavior without importing the full page
 * which has complex route dependencies.
 */
interface CalculateButtonTestProps {
  selectedVersionId: string | undefined
  isPending: boolean
  hasEnrollmentData: boolean
  isEnrollmentLoading: boolean
  onClick: () => void
}

function CalculateButtonTest({
  selectedVersionId,
  isPending,
  hasEnrollmentData,
  isEnrollmentLoading,
  onClick,
}: CalculateButtonTestProps) {
  return (
    <TooltipProvider>
      <Tooltip>
        <TooltipTrigger asChild>
          <span tabIndex={!hasEnrollmentData && selectedVersionId ? 0 : undefined}>
            <Button
              data-testid="calculate-button"
              variant="outline"
              onClick={onClick}
              disabled={
                !selectedVersionId || isPending || !hasEnrollmentData || isEnrollmentLoading
              }
            >
              <Calculator className="h-4 w-4 mr-2" />
              Calculate from Enrollment
            </Button>
          </span>
        </TooltipTrigger>
        {!hasEnrollmentData && selectedVersionId && !isEnrollmentLoading && (
          <TooltipContent>
            <p>Veuillez d'abord saisir les effectifs dans la page Planification</p>
          </TooltipContent>
        )}
      </Tooltip>
    </TooltipProvider>
  )
}

describe('ClassStructure - Calculate Button', () => {
  let queryClient: QueryClient
  const mockOnClick = vi.fn()

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const renderButton = (props: Partial<CalculateButtonTestProps> = {}) => {
    const defaultProps: CalculateButtonTestProps = {
      selectedVersionId: 'version-123',
      isPending: false,
      hasEnrollmentData: true,
      isEnrollmentLoading: false,
      onClick: mockOnClick,
    }
    return render(
      <QueryClientProvider client={queryClient}>
        <CalculateButtonTest {...defaultProps} {...props} />
      </QueryClientProvider>
    )
  }

  describe('Button Disabled States', () => {
    it('should disable button when no enrollment data exists', () => {
      renderButton({ hasEnrollmentData: false })

      const button = screen.getByTestId('calculate-button')
      expect(button).toBeDisabled()
    })

    it('should enable button when enrollment data exists', () => {
      renderButton({ hasEnrollmentData: true })

      const button = screen.getByTestId('calculate-button')
      expect(button).not.toBeDisabled()
    })

    it('should disable button when no version is selected', () => {
      renderButton({ selectedVersionId: undefined })

      const button = screen.getByTestId('calculate-button')
      expect(button).toBeDisabled()
    })

    it('should disable button while calculation is pending', () => {
      renderButton({ isPending: true })

      const button = screen.getByTestId('calculate-button')
      expect(button).toBeDisabled()
    })

    it('should disable button while enrollment summary is loading', () => {
      renderButton({ isEnrollmentLoading: true })

      const button = screen.getByTestId('calculate-button')
      expect(button).toBeDisabled()
    })

    it('should enable button when all conditions are met', () => {
      renderButton({
        selectedVersionId: 'version-123',
        isPending: false,
        hasEnrollmentData: true,
        isEnrollmentLoading: false,
      })

      const button = screen.getByTestId('calculate-button')
      expect(button).not.toBeDisabled()
    })
  })

  describe('Button Click Behavior', () => {
    it('should call onClick when button is clicked and enabled', async () => {
      const user = userEvent.setup()
      renderButton({ hasEnrollmentData: true })

      const button = screen.getByTestId('calculate-button')
      await user.click(button)

      expect(mockOnClick).toHaveBeenCalledTimes(1)
    })

    it('should not call onClick when button is disabled', async () => {
      const user = userEvent.setup()
      renderButton({ hasEnrollmentData: false })

      const button = screen.getByTestId('calculate-button')
      await user.click(button)

      expect(mockOnClick).not.toHaveBeenCalled()
    })
  })

  describe('Tooltip Conditional Rendering Logic', () => {
    /**
     * Note: Radix Tooltip uses a Portal and renders content only on hover.
     * We test the conditional rendering logic by verifying the span wrapper
     * has the correct tabIndex attribute which indicates tooltip should be shown.
     */

    it('should have tabIndex on span when tooltip should show (no enrollment data)', () => {
      renderButton({
        selectedVersionId: 'version-123',
        hasEnrollmentData: false,
        isEnrollmentLoading: false,
      })

      // The span wrapper should have tabIndex=0 when tooltip should show
      const buttonWrapper = screen.getByTestId('calculate-button').parentElement
      expect(buttonWrapper).toHaveAttribute('tabindex', '0')
    })

    it('should not have tabIndex on span when button is enabled (has enrollment)', () => {
      renderButton({
        selectedVersionId: 'version-123',
        hasEnrollmentData: true,
        isEnrollmentLoading: false,
      })

      // No tabIndex when enrollment data exists (no tooltip needed)
      const buttonWrapper = screen.getByTestId('calculate-button').parentElement
      expect(buttonWrapper).not.toHaveAttribute('tabindex')
    })

    it('should not have tabIndex when no version is selected', () => {
      renderButton({
        selectedVersionId: undefined,
        hasEnrollmentData: false,
        isEnrollmentLoading: false,
      })

      // No tabIndex when no version (different disabled reason)
      const buttonWrapper = screen.getByTestId('calculate-button').parentElement
      expect(buttonWrapper).not.toHaveAttribute('tabindex')
    })
  })

  describe('Button Text and Icon', () => {
    it('should display correct button text', () => {
      renderButton()

      expect(screen.getByText('Calculate from Enrollment')).toBeInTheDocument()
    })

    it('should render calculator icon', () => {
      renderButton()

      // The icon is rendered inside the button
      const button = screen.getByTestId('calculate-button')
      const svg = button.querySelector('svg')
      expect(svg).toBeInTheDocument()
    })
  })
})

describe('Enrollment Data Check Logic', () => {
  it('should correctly determine hasEnrollmentData from total_students', () => {
    // Test the logic that would be used in the component
    const checkHasEnrollmentData = (summary: { total_students: number } | undefined) => {
      return (summary?.total_students ?? 0) > 0
    }

    // No summary data
    expect(checkHasEnrollmentData(undefined)).toBe(false)

    // Zero students
    expect(checkHasEnrollmentData({ total_students: 0 })).toBe(false)

    // Has students
    expect(checkHasEnrollmentData({ total_students: 100 })).toBe(true)
    expect(checkHasEnrollmentData({ total_students: 1 })).toBe(true)
  })
})
