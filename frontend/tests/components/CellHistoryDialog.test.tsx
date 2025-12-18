/**
 * CellHistoryDialog Component Tests
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { CellHistoryDialog } from '@/components/CellHistoryDialog'
import { useCellHistory } from '@/hooks/api/useChangeHistory'

// Mock hooks
vi.mock('@/hooks/api/useChangeHistory', () => ({
  useCellHistory: vi.fn(() => ({
    changes: [
      {
        id: '1',
        version_id: 'budget-1',
        entity_type: 'enrollment',
        entity_id: 'cell-1',
        field_name: 'student_count',
        old_value: '100',
        new_value: '150',
        change_type: 'UPDATE',
        changed_by: 'user1@efir.sa',
        changed_at: '2025-01-01T10:00:00Z',
        user_email: 'user1@efir.sa',
      },
      {
        id: '2',
        version_id: 'budget-1',
        entity_type: 'enrollment',
        entity_id: 'cell-1',
        field_name: 'student_count',
        old_value: null,
        new_value: '100',
        change_type: 'INSERT',
        changed_by: 'user2@efir.sa',
        changed_at: '2025-01-01T09:00:00Z',
        user_email: 'user2@efir.sa',
      },
    ],
    isLoading: false,
    isError: false,
    error: null,
    refetch: vi.fn(),
  })),
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

describe('CellHistoryDialog', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = createTestQueryClient()
  })

  it('renders dialog when open', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CellHistoryDialog
          cellId="cell-1"
          versionId="budget-1"
          open={true}
          onOpenChange={() => {}}
        />
      </QueryClientProvider>
    )

    expect(screen.getByText('Historique des modifications')).toBeInTheDocument()
  })

  it.skip('displays change history correctly', () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <CellHistoryDialog
          cellId="cell-1"
          versionId="budget-1"
          open={true}
          onOpenChange={() => {}}
        />
      </QueryClientProvider>
    )

    expect(container.textContent).toContain('student_count')
    expect(container.textContent).toContain('100')
    expect(container.textContent).toContain('150')
  })

  it('shows change type badges', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CellHistoryDialog
          cellId="cell-1"
          versionId="budget-1"
          open={true}
          onOpenChange={() => {}}
        />
      </QueryClientProvider>
    )

    expect(screen.getByText('Modified')).toBeInTheDocument()
    expect(screen.getByText('Created')).toBeInTheDocument()
  })

  it('displays user and timestamp', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <CellHistoryDialog
          cellId="cell-1"
          versionId="budget-1"
          open={true}
          onOpenChange={() => {}}
        />
      </QueryClientProvider>
    )

    expect(screen.getByText(/user1@efir.sa/)).toBeInTheDocument()
    expect(screen.getByText(/user2@efir.sa/)).toBeInTheDocument()
  })

  it('shows empty state when no changes', () => {
    vi.mocked(useCellHistory).mockReturnValue({
      changes: [],
      isLoading: false,
      isError: false,
      error: null,
      refetch: vi.fn(),
    })

    render(
      <QueryClientProvider client={queryClient}>
        <CellHistoryDialog
          cellId="cell-1"
          versionId="budget-1"
          open={true}
          onOpenChange={() => {}}
        />
      </QueryClientProvider>
    )

    expect(screen.getByText('No changes recorded')).toBeInTheDocument()
  })
})
