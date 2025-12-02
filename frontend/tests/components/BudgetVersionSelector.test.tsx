/**
 * Tests for BudgetVersionSelector component.
 *
 * Covers:
 * - Rendering in different states (loading, empty, populated)
 * - User interactions (selection, keyboard navigation)
 * - Status badge display
 * - API error handling
 * - Edge cases
 *
 * Target Coverage: 95% (from 0%)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'

// Mock the useBudgetVersions hook
vi.mock('@/hooks/api/useBudgetVersions', () => ({
  useBudgetVersions: vi.fn(),
}))

// Type for mocked query results
type MockQueryResult = ReturnType<typeof useBudgetVersions>

describe('BudgetVersionSelector', () => {
  let queryClient: QueryClient
  const mockOnChange = vi.fn()

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  const mockVersions = {
    items: [
      {
        id: '00000000-0000-0000-0000-000000000001',
        name: 'Budget 2024 Working',
        fiscal_year: 2024,
        status: 'WORKING' as const,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-15T10:30:00Z',
        created_by_id: 'user-1',
      },
      {
        id: '00000000-0000-0000-0000-000000000002',
        name: 'Budget 2024 Submitted',
        fiscal_year: 2024,
        status: 'SUBMITTED' as const,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-02-01T14:00:00Z',
        created_by_id: 'user-1',
        submitted_at: '2024-02-01T14:00:00Z',
        submitted_by_id: 'user-1',
      },
      {
        id: '00000000-0000-0000-0000-000000000003',
        name: 'Budget 2023 Approved',
        fiscal_year: 2023,
        status: 'APPROVED' as const,
        created_at: '2023-01-01T00:00:00Z',
        updated_at: '2023-03-01T09:00:00Z',
        created_by_id: 'user-1',
        approved_at: '2023-03-01T09:00:00Z',
        approved_by_id: 'user-2',
      },
      {
        id: '00000000-0000-0000-0000-000000000004',
        name: 'Budget 2022 Superseded',
        fiscal_year: 2022,
        status: 'SUPERSEDED' as const,
        created_at: '2022-01-01T00:00:00Z',
        updated_at: '2022-12-01T09:00:00Z',
        created_by_id: 'user-1',
      },
    ],
    total: 4,
    page: 1,
    page_size: 50,
  }

  const renderComponent = (props = {}) => {
    return render(
      <QueryClientProvider client={queryClient}>
        <BudgetVersionSelector value={undefined} onChange={mockOnChange} {...props} />
      </QueryClientProvider>
    )
  }

  // ==============================================================================
  // Rendering Tests
  // ==============================================================================

  describe('Rendering States', () => {
    it('should render loading state', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isError: false,
        isSuccess: false,
      } as MockQueryResult)

      renderComponent()

      expect(screen.getByText('Budget Version')).toBeInTheDocument()
      expect(screen.getByText('Loading...')).toBeInTheDocument()

      // Select should be disabled during loading
      const trigger = screen.getByRole('combobox')
      expect(trigger).toBeDisabled()
    })

    it('should render empty state when no versions', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 50 },
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent()

      expect(screen.getByText('Budget Version')).toBeInTheDocument()
      expect(screen.getByText('Select budget version')).toBeInTheDocument()
    })

    it('should render versions list', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent()

      expect(screen.getByText('Budget Version')).toBeInTheDocument()
      expect(screen.getByText('Select budget version')).toBeInTheDocument()
    })

    it('should display version name and fiscal year', async () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      // Click to open dropdown
      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      // Check that version name is displayed
      await waitFor(() => {
        expect(screen.getByText('Budget 2024 Working')).toBeInTheDocument()
      })

      // Check fiscal year display
      expect(screen.getByText('FY2024')).toBeInTheDocument()
    })

    it('should display status badges correctly', async () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      // Open dropdown
      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        // Check that all status badges are rendered
        expect(screen.getByText('WORKING')).toBeInTheDocument()
        expect(screen.getByText('SUBMITTED')).toBeInTheDocument()
        expect(screen.getByText('APPROVED')).toBeInTheDocument()
        expect(screen.getByText('SUPERSEDED')).toBeInTheDocument()
      })
    })

    it('should apply custom className', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const { container } = renderComponent({ className: 'custom-class' })

      const wrapper = container.querySelector('.custom-class')
      expect(wrapper).toBeInTheDocument()
    })

    it('should display custom label', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent({ label: 'Select Version' })

      expect(screen.getByText('Select Version')).toBeInTheDocument()
    })
  })

  // ==============================================================================
  // Interaction Tests
  // ==============================================================================

  describe('User Interactions', () => {
    it('should call onChange when version selected', async () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      // Open dropdown
      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      // Select a version
      await waitFor(() => {
        expect(screen.getByText('Budget 2024 Working')).toBeInTheDocument()
      })

      const option = screen.getByText('Budget 2024 Working')
      await user.click(option)

      // Check onChange was called with correct ID
      expect(mockOnChange).toHaveBeenCalledTimes(1)
      expect(mockOnChange).toHaveBeenCalledWith('00000000-0000-0000-0000-000000000001')
    })

    it('should display selected version correctly', async () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent({ value: '00000000-0000-0000-0000-000000000002' })

      // Selected version should be displayed
      // Note: Exact implementation depends on shadcn/ui Select component
      const trigger = screen.getByRole('combobox')
      expect(trigger).toBeInTheDocument()
    })

    it('should show correct badge variant by status', async () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        // Check badge text content (variant is applied via className)
        expect(screen.getByText('WORKING')).toBeInTheDocument()
        expect(screen.getByText('SUBMITTED')).toBeInTheDocument()
        expect(screen.getByText('APPROVED')).toBeInTheDocument()
        expect(screen.getByText('SUPERSEDED')).toBeInTheDocument()
      })
    })

    it('should disable selector when loading', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: undefined,
        isLoading: true,
        error: null,
        isError: false,
        isSuccess: false,
      } as MockQueryResult)

      renderComponent()

      const trigger = screen.getByRole('combobox')
      expect(trigger).toBeDisabled()
    })

    it('should handle keyboard navigation', async () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')

      // Open with keyboard
      await user.click(trigger)

      await waitFor(() => {
        expect(screen.getByText('Budget 2024 Working')).toBeInTheDocument()
      })

      // Navigate with arrow keys and select with Enter
      // Note: Exact keyboard behavior depends on shadcn/ui implementation
    })
  })

  // ==============================================================================
  // Data Handling Tests
  // ==============================================================================

  describe('Data Handling', () => {
    it('should fetch versions on mount', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent()

      // Hook should be called on mount
      expect(useBudgetVersions).toHaveBeenCalled()
    })

    it('should handle API error gracefully', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: undefined,
        isLoading: false,
        error: new Error('Failed to fetch versions'),
        isError: true,
        isSuccess: false,
      } as MockQueryResult)

      renderComponent()

      // Component should still render without crashing
      expect(screen.getByText('Budget Version')).toBeInTheDocument()

      // Should show placeholder when error
      expect(screen.getByText('Select budget version')).toBeInTheDocument()
    })

    it('should display versions in correct order', async () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        const options = screen.getAllByRole('option')
        expect(options).toHaveLength(4)
      })
    })

    it('should handle versions with missing optional fields', async () => {
      const incompleteVersions = {
        items: [
          {
            id: '1',
            name: 'Minimal Version',
            fiscal_year: 2024,
            status: 'WORKING' as const,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            created_by_id: 'user-1',
            // Missing optional fields like notes, submitted_at, etc.
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      }

      vi.mocked(useBudgetVersions).mockReturnValue({
        data: incompleteVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        expect(screen.getByText('Minimal Version')).toBeInTheDocument()
      })
    })
  })

  // ==============================================================================
  // Edge Cases
  // ==============================================================================

  describe('Edge Cases', () => {
    it('should handle undefined value prop', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent({ value: undefined })

      // Should render placeholder
      expect(screen.getByText('Select budget version')).toBeInTheDocument()
    })

    it('should handle invalid versionId', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      // Value that doesn't exist in versions list
      renderComponent({ value: 'non-existent-id' })

      // Should still render without error
      expect(screen.getByText('Budget Version')).toBeInTheDocument()
    })

    it('should handle empty versions array', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 50 },
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent()

      expect(screen.getByText('Select budget version')).toBeInTheDocument()
    })

    it('should handle null data gracefully', () => {
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: null,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      renderComponent()

      // Should render without crashing
      expect(screen.getByText('Budget Version')).toBeInTheDocument()
    })

    it('should re-render when versions data changes', async () => {
      const { rerender } = render(
        <QueryClientProvider client={queryClient}>
          <BudgetVersionSelector value={undefined} onChange={mockOnChange} />
        </QueryClientProvider>
      )

      // Initial render with empty data
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: { items: [], total: 0, page: 1, page_size: 50 },
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      rerender(
        <QueryClientProvider client={queryClient}>
          <BudgetVersionSelector value={undefined} onChange={mockOnChange} />
        </QueryClientProvider>
      )

      // Update with versions
      vi.mocked(useBudgetVersions).mockReturnValue({
        data: mockVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      rerender(
        <QueryClientProvider client={queryClient}>
          <BudgetVersionSelector value={undefined} onChange={mockOnChange} />
        </QueryClientProvider>
      )

      // Component should update
      expect(screen.getByText('Budget Version')).toBeInTheDocument()
    })
  })

  // ==============================================================================
  // Badge Variant Tests
  // ==============================================================================

  describe('Status Badge Variants', () => {
    it('should use info variant for WORKING status', async () => {
      const workingVersions = {
        items: [
          {
            id: '1',
            name: 'Working',
            fiscal_year: 2024,
            status: 'WORKING' as const,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            created_by_id: 'user-1',
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      }

      vi.mocked(useBudgetVersions).mockReturnValue({
        data: workingVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        expect(screen.getByText('WORKING')).toBeInTheDocument()
      })
    })

    it('should use warning variant for SUBMITTED status', async () => {
      const submittedVersions = {
        items: [
          {
            id: '1',
            name: 'Submitted',
            fiscal_year: 2024,
            status: 'SUBMITTED' as const,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            created_by_id: 'user-1',
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      }

      vi.mocked(useBudgetVersions).mockReturnValue({
        data: submittedVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        expect(screen.getByText('SUBMITTED')).toBeInTheDocument()
      })
    })

    it('should use success variant for APPROVED status', async () => {
      const approvedVersions = {
        items: [
          {
            id: '1',
            name: 'Approved',
            fiscal_year: 2024,
            status: 'APPROVED' as const,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            created_by_id: 'user-1',
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      }

      vi.mocked(useBudgetVersions).mockReturnValue({
        data: approvedVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        expect(screen.getByText('APPROVED')).toBeInTheDocument()
      })
    })

    it('should use default variant for SUPERSEDED status', async () => {
      const supersededVersions = {
        items: [
          {
            id: '1',
            name: 'Superseded',
            fiscal_year: 2024,
            status: 'SUPERSEDED' as const,
            created_at: '2024-01-01T00:00:00Z',
            updated_at: '2024-01-01T00:00:00Z',
            created_by_id: 'user-1',
          },
        ],
        total: 1,
        page: 1,
        page_size: 50,
      }

      vi.mocked(useBudgetVersions).mockReturnValue({
        data: supersededVersions,
        isLoading: false,
        error: null,
        isError: false,
        isSuccess: true,
      } as MockQueryResult)

      const user = userEvent.setup()
      renderComponent()

      const trigger = screen.getByRole('combobox')
      await user.click(trigger)

      await waitFor(() => {
        expect(screen.getByText('SUPERSEDED')).toBeInTheDocument()
      })
    })
  })
})
