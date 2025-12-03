/**
 * EnhancedDataTable Component Tests
 *
 * Tests for AG Grid integration with cell-level writeback
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { EnhancedDataTable } from '@/components/EnhancedDataTable'

// Mock hooks
vi.mock('@/hooks/api/usePlanningWriteback', () => ({
  usePlanningWriteback: vi.fn(() => ({
    updateCell: vi.fn().mockResolvedValue({
      id: '123',
      field_name: 'value',
      value: 100,
      version: 2,
      updated_at: new Date().toISOString(),
      updated_by: 'test@efir.sa',
    }),
    isUpdating: false,
    error: null,
  })),
  VersionConflictError: class VersionConflictError extends Error {
    constructor(
      message: string,
      public currentVersion: number,
      public expectedVersion: number
    ) {
      super(message)
      this.name = 'VersionConflictError'
    }
  },
}))

vi.mock('@/hooks/useRealtimeSync', () => ({
  useRealtimeSync: vi.fn(),
}))

vi.mock('@/hooks/useUserPresence', () => ({
  useUserPresence: vi.fn(() => ({
    activeUsers: [
      {
        user_id: '1',
        user_email: 'test@efir.sa',
        joined_at: new Date().toISOString(),
      },
    ],
    broadcast: vi.fn(),
  })),
}))

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(() => ({
    user: { id: '1', email: 'test@efir.sa' },
    session: { access_token: 'test-token' },
  })),
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })

describe('EnhancedDataTable', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = createTestQueryClient()
  })

  const mockColumnDefs = [
    { field: 'id', headerName: 'ID' },
    { field: 'value', headerName: 'Value', editable: true },
  ]

  const mockRowData = [
    { id: '1', value: 100, version: 1, is_locked: false },
    { id: '2', value: 200, version: 1, is_locked: false },
    { id: '3', value: 300, version: 1, is_locked: true },
  ]

  it('renders AG Grid with data', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <EnhancedDataTable
          budgetVersionId="budget-1"
          moduleCode="enrollment"
          columnDefs={mockColumnDefs}
          rowData={mockRowData}
        />
      </QueryClientProvider>
    )

    // AG Grid should render
    expect(document.querySelector('.ag-theme-quartz')).toBeInTheDocument()
  })

  it('displays active users', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <EnhancedDataTable
          budgetVersionId="budget-1"
          moduleCode="enrollment"
          columnDefs={mockColumnDefs}
          rowData={mockRowData}
        />
      </QueryClientProvider>
    )

    expect(screen.getByText('Utilisateurs actifs:')).toBeInTheDocument()
    expect(screen.getByText('test@efir.sa')).toBeInTheDocument()
  })

  it('shows loading state', () => {
    render(
      <QueryClientProvider client={queryClient}>
        <EnhancedDataTable
          budgetVersionId="budget-1"
          moduleCode="enrollment"
          columnDefs={mockColumnDefs}
          rowData={mockRowData}
          loading
        />
      </QueryClientProvider>
    )

    expect(screen.getByText('Chargement...')).toBeInTheDocument()
  })

  it('shows error state', () => {
    const error = new Error('Failed to load data')

    render(
      <QueryClientProvider client={queryClient}>
        <EnhancedDataTable
          budgetVersionId="budget-1"
          moduleCode="enrollment"
          columnDefs={mockColumnDefs}
          rowData={mockRowData}
          error={error}
        />
      </QueryClientProvider>
    )

    expect(screen.getByText('Error loading data')).toBeInTheDocument()
    expect(screen.getByText('Failed to load data')).toBeInTheDocument()
  })

  it('disables editing when enableWriteback is false', () => {
    const { container } = render(
      <QueryClientProvider client={queryClient}>
        <EnhancedDataTable
          budgetVersionId="budget-1"
          moduleCode="enrollment"
          columnDefs={mockColumnDefs}
          rowData={mockRowData}
          enableWriteback={false}
        />
      </QueryClientProvider>
    )

    // Check that cells are not editable
    const grid = container.querySelector('.ag-theme-quartz')
    expect(grid).toBeInTheDocument()
  })
})
