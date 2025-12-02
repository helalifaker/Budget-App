/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable @typescript-eslint/no-unused-vars */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useRealtimeSync } from '@/hooks/useRealtimeSync'
import { supabase } from '@/lib/supabase'
import { useAuth } from '@/contexts/AuthContext'
import { toast } from 'sonner'
import type { CellData } from '@/types/writeback'

// Mock dependencies
vi.mock('@/lib/supabase', () => ({
  supabase: {
    channel: vi.fn(),
    removeChannel: vi.fn(),
  },
}))

vi.mock('@/contexts/AuthContext', () => ({
  useAuth: vi.fn(),
}))

vi.mock('sonner', () => ({
  toast: {
    info: vi.fn(),
    error: vi.fn(),
    success: vi.fn(),
  },
}))

describe('useRealtimeSync', () => {
  let queryClient: QueryClient
  let mockChannel: any
  let mockUser: any
  let subscribeCallback: any

  beforeEach(() => {
    // Create fresh query client for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    // Mock user
    mockUser = {
      id: 'user-123',
      email: 'test@efir.com',
    }

    vi.mocked(useAuth).mockReturnValue({
      user: mockUser,
      session: null,
      loading: false,
      signIn: vi.fn(),
      signUp: vi.fn(),
      signOut: vi.fn(),
      resetPassword: vi.fn(),
    })

    // Mock channel
    mockChannel = {
      on: vi.fn().mockReturnThis(),
      subscribe: vi.fn((callback) => {
        subscribeCallback = callback
        // Simulate successful subscription
        setTimeout(() => callback('SUBSCRIBED'), 0)
        return mockChannel
      }),
      unsubscribe: vi.fn(),
    }

    vi.mocked(supabase.channel).mockReturnValue(mockChannel)
    vi.mocked(supabase.removeChannel).mockResolvedValue({ status: 'ok', error: null })
  })

  afterEach(() => {
    vi.clearAllMocks()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  it('should initialize with IDLE status', () => {
    const { result } = renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId: 'budget-123',
        }),
      { wrapper }
    )

    // Initially IDLE, then CONNECTING
    expect(['IDLE', 'CONNECTING']).toContain(result.current.status)
  })

  it('should connect to realtime channel on mount', async () => {
    const budgetVersionId = 'budget-123'

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(supabase.channel).toHaveBeenCalledWith(
        `budget:${budgetVersionId}`,
        expect.objectContaining({
          config: expect.objectContaining({
            broadcast: { self: false },
            presence: { key: mockUser.id },
          }),
        })
      )
    })
  })

  it('should subscribe to postgres changes', async () => {
    const budgetVersionId = 'budget-123'

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(mockChannel.on).toHaveBeenCalledWith(
        'postgres_changes',
        expect.objectContaining({
          event: '*',
          schema: 'public',
          table: 'planning_cells',
          filter: `budget_version_id=eq.${budgetVersionId}`,
        }),
        expect.any(Function)
      )
    })
  })

  it('should update status to SUBSCRIBED after successful connection', async () => {
    const { result } = renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId: 'budget-123',
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(result.current.status).toBe('SUBSCRIBED')
      expect(result.current.isConnected).toBe(true)
    })
  })

  it('should handle UPDATE event and update cache', async () => {
    const budgetVersionId = 'budget-123'
    let changeHandler: any

    // Capture the change handler
    mockChannel.on.mockImplementation((event: string, config: any, handler: any) => {
      if (event === 'postgres_changes') {
        changeHandler = handler
      }
      return mockChannel
    })

    // Set initial cache data
    const initialCells: CellData[] = [
      {
        id: 'cell-1',
        budget_version_id: budgetVersionId,
        module_code: 'enrollment',
        entity_id: 'level-1',
        field_name: 'student_count',
        value_numeric: 100,
        version: 1,
        is_locked: false,
        modified_by: 'other-user',
        modified_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      },
    ]

    queryClient.setQueryData(['cells', budgetVersionId], initialCells)

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(changeHandler).toBeDefined()
    })

    // Simulate UPDATE event from another user
    const updatedCell = {
      ...initialCells[0],
      value_numeric: 150,
      version: 2,
      modified_by: 'other-user',
    }

    changeHandler({
      eventType: 'UPDATE',
      new: updatedCell,
      old: initialCells[0],
    })

    // Check cache was updated
    await waitFor(() => {
      const cachedData = queryClient.getQueryData<CellData[]>(['cells', budgetVersionId])
      expect(cachedData).toBeDefined()
      expect(cachedData![0].value_numeric).toBe(150)
      expect(cachedData![0].version).toBe(2)
    })

    // Check toast notification was shown
    expect(toast.info).toHaveBeenCalledWith(
      'Cellule mise à jour par un autre utilisateur',
      expect.objectContaining({
        description: expect.stringContaining('student_count'),
      })
    )
  })

  it('should ignore changes from current user', async () => {
    const budgetVersionId = 'budget-123'
    let changeHandler: any

    mockChannel.on.mockImplementation((event: string, config: any, handler: any) => {
      if (event === 'postgres_changes') {
        changeHandler = handler
      }
      return mockChannel
    })

    queryClient.setQueryData(['cells', budgetVersionId], [])

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(changeHandler).toBeDefined()
    })

    // Simulate UPDATE event from current user
    changeHandler({
      eventType: 'UPDATE',
      new: {
        id: 'cell-1',
        modified_by: mockUser.id, // Same as current user
        field_name: 'test',
      },
      old: {},
    })

    // Cache should not be updated
    const cachedData = queryClient.getQueryData(['cells', budgetVersionId])
    expect(cachedData).toEqual([])

    // Toast should not be shown
    expect(toast.info).not.toHaveBeenCalled()
  })

  it('should handle INSERT event', async () => {
    const budgetVersionId = 'budget-123'
    let changeHandler: any

    mockChannel.on.mockImplementation((event: string, config: any, handler: any) => {
      if (event === 'postgres_changes') {
        changeHandler = handler
      }
      return mockChannel
    })

    queryClient.setQueryData(['cells', budgetVersionId], [])

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(changeHandler).toBeDefined()
    })

    // Simulate INSERT event
    const newCell: CellData = {
      id: 'cell-2',
      budget_version_id: budgetVersionId,
      module_code: 'enrollment',
      entity_id: 'level-2',
      field_name: 'new_field',
      value_numeric: 200,
      version: 1,
      is_locked: false,
      modified_by: 'other-user',
      modified_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    }

    changeHandler({
      eventType: 'INSERT',
      new: newCell,
      old: null,
    })

    // Check cache was updated
    await waitFor(() => {
      const cachedData = queryClient.getQueryData<CellData[]>(['cells', budgetVersionId])
      expect(cachedData).toBeDefined()
      expect(cachedData).toHaveLength(1)
      expect(cachedData![0].id).toBe('cell-2')
    })
  })

  it('should handle DELETE event', async () => {
    const budgetVersionId = 'budget-123'
    let changeHandler: any

    mockChannel.on.mockImplementation((event: string, config: any, handler: any) => {
      if (event === 'postgres_changes') {
        changeHandler = handler
      }
      return mockChannel
    })

    const initialCells: CellData[] = [
      {
        id: 'cell-1',
        budget_version_id: budgetVersionId,
        module_code: 'enrollment',
        entity_id: 'level-1',
        field_name: 'student_count',
        value_numeric: 100,
        version: 1,
        is_locked: false,
        modified_by: 'other-user',
        modified_at: new Date().toISOString(),
        created_at: new Date().toISOString(),
      },
    ]

    queryClient.setQueryData(['cells', budgetVersionId], initialCells)

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(changeHandler).toBeDefined()
    })

    // Simulate DELETE event
    changeHandler({
      eventType: 'DELETE',
      new: null,
      old: initialCells[0],
    })

    // Check cache was updated
    await waitFor(() => {
      const cachedData = queryClient.getQueryData<CellData[]>(['cells', budgetVersionId])
      expect(cachedData).toBeDefined()
      expect(cachedData).toHaveLength(0)
    })
  })

  it('should call onCellChanged callback', async () => {
    const budgetVersionId = 'budget-123'
    const onCellChanged = vi.fn()
    let changeHandler: any

    mockChannel.on.mockImplementation((event: string, config: any, handler: any) => {
      if (event === 'postgres_changes') {
        changeHandler = handler
      }
      return mockChannel
    })

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId,
          onCellChanged,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(changeHandler).toBeDefined()
    })

    const cellData: CellData = {
      id: 'cell-1',
      budget_version_id: budgetVersionId,
      module_code: 'enrollment',
      entity_id: 'level-1',
      field_name: 'test',
      value_numeric: 100,
      version: 1,
      is_locked: false,
      modified_by: 'other-user',
      modified_at: new Date().toISOString(),
      created_at: new Date().toISOString(),
    }

    changeHandler({
      eventType: 'UPDATE',
      new: cellData,
      old: null,
    })

    await waitFor(() => {
      expect(onCellChanged).toHaveBeenCalledWith({
        eventType: 'UPDATE',
        cell: cellData,
        userId: 'other-user',
      })
    })
  })

  it('should cleanup subscription on unmount', async () => {
    const { unmount } = renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId: 'budget-123',
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(supabase.channel).toHaveBeenCalled()
    })

    unmount()

    await waitFor(() => {
      expect(supabase.removeChannel).toHaveBeenCalledWith(mockChannel)
    })
  })

  it('should handle connection errors', async () => {
    // Mock error status
    mockChannel.subscribe.mockImplementation((callback) => {
      setTimeout(() => callback('CHANNEL_ERROR'), 0)
      return mockChannel
    })

    const { result } = renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId: 'budget-123',
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(result.current.status).toBe('CHANNEL_ERROR')
      expect(result.current.isError).toBe(true)
    })

    expect(toast.error).toHaveBeenCalledWith(
      'Erreur de synchronisation temps réel',
      expect.objectContaining({
        description: 'Reconnexion en cours...',
      })
    )
  })

  it('should not show notifications when disabled', async () => {
    let changeHandler: any

    mockChannel.on.mockImplementation((event: string, config: any, handler: any) => {
      if (event === 'postgres_changes') {
        changeHandler = handler
      }
      return mockChannel
    })

    renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId: 'budget-123',
          showNotifications: false,
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(changeHandler).toBeDefined()
    })

    changeHandler({
      eventType: 'UPDATE',
      new: {
        id: 'cell-1',
        modified_by: 'other-user',
        field_name: 'test',
      },
      old: null,
    })

    expect(toast.info).not.toHaveBeenCalled()
  })

  it('should provide manual reconnect function', async () => {
    const { result } = renderHook(
      () =>
        useRealtimeSync({
          budgetVersionId: 'budget-123',
        }),
      { wrapper }
    )

    await waitFor(() => {
      expect(result.current.status).toBe('SUBSCRIBED')
    })

    // Call reconnect
    result.current.reconnect()

    await waitFor(() => {
      expect(supabase.removeChannel).toHaveBeenCalled()
    })
  })
})
