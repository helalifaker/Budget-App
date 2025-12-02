import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import * as Sentry from '@sentry/react'
import { ErrorBoundary } from '@/components/ErrorBoundary'

// Mock Sentry
vi.mock('@sentry/react', () => ({
  captureException: vi.fn(),
}))

// Mock lucide-react
vi.mock('lucide-react', () => ({
  AlertTriangle: () => <div data-testid="alert-triangle-icon">AlertTriangle</div>,
}))

// Component that throws an error for testing
function ThrowError({ shouldThrow = false }: { shouldThrow?: boolean }) {
  if (shouldThrow) {
    throw new Error('Test error message')
  }
  return <div>Child component</div>
}

describe('ErrorBoundary', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Suppress console.error in tests (ErrorBoundary logs errors)
    vi.spyOn(console, 'error').mockImplementation(() => {})
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Normal Rendering', () => {
    it('should render children when no error occurs', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Child component')).toBeInTheDocument()
      expect(Sentry.captureException).not.toHaveBeenCalled()
    })

    it('should render multiple children without errors', () => {
      render(
        <ErrorBoundary>
          <div>First child</div>
          <div>Second child</div>
          <div>Third child</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('First child')).toBeInTheDocument()
      expect(screen.getByText('Second child')).toBeInTheDocument()
      expect(screen.getByText('Third child')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('should catch and display error when child component throws', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Should display error UI
      expect(screen.getByText('Une erreur est survenue')).toBeInTheDocument()
      expect(
        screen.getByText(/Nous sommes désolés, mais quelque chose s'est mal passé/)
      ).toBeInTheDocument()

      // Should not display child component
      expect(screen.queryByText('Child component')).not.toBeInTheDocument()
    })

    it('should capture error with Sentry', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Sentry should be called with error and componentStack
      expect(Sentry.captureException).toHaveBeenCalledTimes(1)
      expect(Sentry.captureException).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          contexts: expect.objectContaining({
            react: expect.objectContaining({
              componentStack: expect.any(String),
            }),
          }),
        })
      )
    })

    it('should log error to console', () => {
      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(consoleSpy).toHaveBeenCalledWith(
        'ErrorBoundary caught error:',
        expect.any(Error),
        expect.any(Object)
      )
    })
  })

  describe('Error UI Components', () => {
    it('should display error icon', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByTestId('alert-triangle-icon')).toBeInTheDocument()
    })

    it('should display action buttons', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Retour au tableau de bord')).toBeInTheDocument()
      expect(screen.getByText('Rafraîchir la page')).toBeInTheDocument()
    })

    it('should display technical details in collapsed state', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const details = screen.getByText('Détails techniques')
      expect(details).toBeInTheDocument()

      // Technical details should be in a <details> element
      const detailsElement = details.closest('details')
      expect(detailsElement).toBeInTheDocument()
    })

    it('should show error message in technical details', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Expand technical details
      const summary = screen.getByText('Détails techniques')
      fireEvent.click(summary)

      // Should show error message
      expect(screen.getByText(/Test error message/)).toBeInTheDocument()
    })
  })

  describe('Error Recovery', () => {
    it('should reload page when "Rafraîchir la page" is clicked', () => {
      // Mock window.location.reload
      const reloadMock = vi.fn()
      Object.defineProperty(window, 'location', {
        value: { reload: reloadMock },
        writable: true,
      })

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const refreshButton = screen.getByText('Rafraîchir la page')
      fireEvent.click(refreshButton)

      expect(reloadMock).toHaveBeenCalledTimes(1)
    })

    it('should navigate to dashboard when "Retour au tableau de bord" is clicked', () => {
      // Mock window.location.href
      const mockLocation = { href: '' }
      Object.defineProperty(window, 'location', {
        value: mockLocation,
        writable: true,
      })

      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const dashboardButton = screen.getByText('Retour au tableau de bord')
      fireEvent.click(dashboardButton)

      expect(mockLocation.href).toBe('/dashboard')
    })
  })

  describe('Custom Fallback', () => {
    it('should render custom fallback when provided', () => {
      const customFallback = <div>Custom error message</div>

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom error message')).toBeInTheDocument()
      expect(screen.queryByText('Une erreur est survenue')).not.toBeInTheDocument()
    })

    it('should not render custom fallback when no error', () => {
      const customFallback = <div>Custom error message</div>

      render(
        <ErrorBoundary fallback={customFallback}>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Child component')).toBeInTheDocument()
      expect(screen.queryByText('Custom error message')).not.toBeInTheDocument()
    })
  })

  describe('Error State Management', () => {
    it('should maintain error state after error occurs', () => {
      const { rerender } = render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Error UI should be visible
      expect(screen.getByText('Une erreur est survenue')).toBeInTheDocument()

      // Rerender with non-throwing component
      rerender(
        <ErrorBoundary>
          <ThrowError shouldThrow={false} />
        </ErrorBoundary>
      )

      // Error UI should still be visible (error state persists)
      expect(screen.getByText('Une erreur est survenue')).toBeInTheDocument()
      expect(screen.queryByText('Child component')).not.toBeInTheDocument()
    })
  })

  describe('Edge Cases', () => {
    it('should handle errors with no stack trace', () => {
      // Create error without stack
      function ThrowErrorNoStack() {
        const error = new Error('Error without stack')
        error.stack = undefined
        throw error
      }

      render(
        <ErrorBoundary>
          <ThrowErrorNoStack />
        </ErrorBoundary>
      )

      expect(screen.getByText('Une erreur est survenue')).toBeInTheDocument()
      expect(Sentry.captureException).toHaveBeenCalled()
    })

    it('should handle errors with very long messages', () => {
      function ThrowLongError() {
        throw new Error('A'.repeat(1000))
      }

      render(
        <ErrorBoundary>
          <ThrowLongError />
        </ErrorBoundary>
      )

      expect(screen.getByText('Une erreur est survenue')).toBeInTheDocument()
    })

    it('should handle null children', () => {
      render(<ErrorBoundary>{null}</ErrorBoundary>)

      // Should render nothing but not crash
      expect(screen.queryByText('Une erreur est survenue')).not.toBeInTheDocument()
    })

    it('should handle undefined children', () => {
      render(<ErrorBoundary>{undefined}</ErrorBoundary>)

      // Should render nothing but not crash
      expect(screen.queryByText('Une erreur est survenue')).not.toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('should have proper ARIA roles and labels', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      // Buttons should be accessible
      const dashboardButton = screen.getByText('Retour au tableau de bord')
      const refreshButton = screen.getByText('Rafraîchir la page')

      expect(dashboardButton.tagName).toBe('BUTTON')
      expect(refreshButton.tagName).toBe('BUTTON')
    })

    it('should have keyboard-accessible details toggle', () => {
      render(
        <ErrorBoundary>
          <ThrowError shouldThrow={true} />
        </ErrorBoundary>
      )

      const summary = screen.getByText('Détails techniques')
      expect(summary.closest('details')).toBeInTheDocument()

      // Details/summary is natively keyboard accessible
      expect(summary.tagName).toBe('SUMMARY')
    })
  })
})
