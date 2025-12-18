import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { useUndoRedo } from '@/hooks/state/useUndoRedo'
import { apiRequest } from '@/lib/api-client'
import { CellChange } from '@/types/writeback'

// Mock dependencies
vi.mock('@/lib/api-client')
vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
  },
}))

const mockApiRequest = vi.mocked(apiRequest)

// Test wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe('useUndoRedo', () => {
  const versionId = 'test-budget-version-id'
  const moduleCode = 'enrollment'

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe('Stack Management', () => {
    it('should initialize with empty stacks', async () => {
      mockApiRequest.mockResolvedValue([])

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canUndo).toBe(false)
        expect(result.current.canRedo).toBe(false)
        expect(result.current.undoCount).toBe(0)
        expect(result.current.redoCount).toBe(0)
      })
    })

    it('should build undo stack from change history', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 100,
          new_value: 150,
          change_type: 'manual',
          changed_by: 'user-1',
          changed_at: '2025-01-01T10:00:00Z',
        },
        {
          id: '2',
          cell_id: 'cell-2',
          session_id: 'session-2',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-2',
          field_name: 'student_count',
          old_value: 200,
          new_value: 250,
          change_type: 'manual',
          changed_by: 'user-1',
          changed_at: '2025-01-01T11:00:00Z',
        },
      ]

      mockApiRequest.mockResolvedValue(mockChanges)

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canUndo).toBe(true)
        expect(result.current.undoCount).toBe(2)
        expect(result.current.undoStack).toEqual(['session-2', 'session-1']) // Most recent first
      })
    })

    it('should separate undo and redo stacks based on change_type', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 100,
          new_value: 150,
          change_type: 'manual',
          changed_by: 'user-1',
          changed_at: '2025-01-01T10:00:00Z',
        },
        {
          id: '2',
          cell_id: 'cell-1',
          session_id: 'session-2',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 150,
          new_value: 100,
          change_type: 'undo',
          changed_by: 'user-1',
          changed_at: '2025-01-01T11:00:00Z',
        },
      ]

      mockApiRequest.mockResolvedValue(mockChanges)

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.undoCount).toBe(1) // session-1 in undo stack
        expect(result.current.redoCount).toBe(1) // session-2 in redo stack
        expect(result.current.canUndo).toBe(true)
        expect(result.current.canRedo).toBe(true)
      })
    })

    it('should limit stacks to 100 sessions', async () => {
      // Create 150 mock changes (should be limited to 100)
      const mockChanges: CellChange[] = Array.from({ length: 150 }, (_, i) => ({
        id: `${i}`,
        cell_id: `cell-${i}`,
        session_id: `session-${i}`,
        sequence_number: 0,
        module_code: 'enrollment',
        entity_id: `entity-${i}`,
        field_name: 'student_count',
        old_value: 100,
        new_value: 150,
        change_type: 'manual' as const,
        changed_by: 'user-1',
        changed_at: new Date(Date.now() + i * 1000).toISOString(),
      }))

      mockApiRequest.mockResolvedValue(mockChanges)

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.undoCount).toBe(100)
        expect(result.current.undoStack.length).toBe(100)
      })
    })
  })

  describe('Undo Functionality', () => {
    it('should call undo API endpoint with correct session_id', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 100,
          new_value: 150,
          change_type: 'manual',
          changed_by: 'user-1',
          changed_at: '2025-01-01T10:00:00Z',
        },
      ]

      mockApiRequest
        .mockResolvedValueOnce(mockChanges) // Initial fetch
        .mockResolvedValueOnce({
          reverted_count: 1,
          new_session_id: 'undo-session-1',
        }) // Undo response

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canUndo).toBe(true)
      })

      await act(async () => {
        await result.current.undo()
      })

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith({
          method: 'POST',
          url: '/writeback/cells/undo',
          data: { session_id: 'session-1' },
        })
      })
    })

    it('should not call undo when stack is empty', async () => {
      mockApiRequest.mockResolvedValue([])

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canUndo).toBe(false)
      })

      await act(async () => {
        await result.current.undo()
      })

      // Should not have made undo API call
      expect(mockApiRequest).toHaveBeenCalledTimes(1) // Only initial fetch
    })

    it('should set loading state during undo', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 100,
          new_value: 150,
          change_type: 'manual',
          changed_by: 'user-1',
          changed_at: '2025-01-01T10:00:00Z',
        },
      ]

      mockApiRequest.mockResolvedValueOnce(mockChanges).mockImplementationOnce(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  reverted_count: 1,
                  new_session_id: 'undo-session-1',
                }),
              100
            )
          )
      )

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canUndo).toBe(true)
      })

      let undoPromise: Promise<void> | undefined
      await act(async () => {
        undoPromise = result.current.undo()
      })

      await waitFor(() => {
        expect(result.current.isLoading).toBe(true)
      })

      await act(async () => {
        await undoPromise
      })

      expect(result.current.isLoading).toBe(false)
    })
  })

  describe('Redo Functionality', () => {
    it('should call undo API endpoint with undo session_id', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'undo-session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 150,
          new_value: 100,
          change_type: 'undo',
          changed_by: 'user-1',
          changed_at: '2025-01-01T11:00:00Z',
        },
      ]

      mockApiRequest
        .mockResolvedValueOnce(mockChanges) // Initial fetch
        .mockResolvedValueOnce({
          reverted_count: 1,
          new_session_id: 'redo-session-1',
        }) // Redo response

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canRedo).toBe(true)
      })

      await act(async () => {
        await result.current.redo()
      })

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith({
          method: 'POST',
          url: '/writeback/cells/undo',
          data: { session_id: 'undo-session-1' },
        })
      })
    })

    it('should not call redo when stack is empty', async () => {
      mockApiRequest.mockResolvedValue([])

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canRedo).toBe(false)
      })

      await act(async () => {
        await result.current.redo()
      })

      // Should not have made redo API call
      expect(mockApiRequest).toHaveBeenCalledTimes(1) // Only initial fetch
    })
  })

  describe('Keyboard Shortcuts', () => {
    it('should trigger undo on Ctrl+Z', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 100,
          new_value: 150,
          change_type: 'manual',
          changed_by: 'user-1',
          changed_at: '2025-01-01T10:00:00Z',
        },
      ]

      mockApiRequest.mockResolvedValueOnce(mockChanges).mockResolvedValueOnce({
        reverted_count: 1,
        new_session_id: 'undo-session-1',
      })

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canUndo).toBe(true)
      })

      // Simulate Ctrl+Z keyboard event
      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        bubbles: true,
      })

      await act(async () => {
        window.dispatchEvent(event)
      })

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith({
          method: 'POST',
          url: '/writeback/cells/undo',
          data: { session_id: 'session-1' },
        })
      })
    })

    it('should trigger redo on Ctrl+Y', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'undo-session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 150,
          new_value: 100,
          change_type: 'undo',
          changed_by: 'user-1',
          changed_at: '2025-01-01T11:00:00Z',
        },
      ]

      mockApiRequest.mockResolvedValueOnce(mockChanges).mockResolvedValueOnce({
        reverted_count: 1,
        new_session_id: 'redo-session-1',
      })

      const { result } = renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      await waitFor(() => {
        expect(result.current.canRedo).toBe(true)
      })

      // Simulate Ctrl+Y keyboard event
      const event = new KeyboardEvent('keydown', {
        key: 'y',
        ctrlKey: true,
        bubbles: true,
      })

      await act(async () => {
        window.dispatchEvent(event)
      })

      await waitFor(() => {
        expect(mockApiRequest).toHaveBeenCalledWith({
          method: 'POST',
          url: '/writeback/cells/undo',
          data: { session_id: 'undo-session-1' },
        })
      })
    })

    it('should not trigger shortcuts when typing in input', async () => {
      const mockChanges: CellChange[] = [
        {
          id: '1',
          cell_id: 'cell-1',
          session_id: 'session-1',
          sequence_number: 0,
          module_code: 'enrollment',
          entity_id: 'entity-1',
          field_name: 'student_count',
          old_value: 100,
          new_value: 150,
          change_type: 'manual',
          changed_by: 'user-1',
          changed_at: '2025-01-01T10:00:00Z',
        },
      ]

      mockApiRequest.mockResolvedValue(mockChanges)

      renderHook(() => useUndoRedo(versionId, moduleCode), {
        wrapper: createWrapper(),
      })

      // Create input element and focus it
      const input = document.createElement('input')
      document.body.appendChild(input)
      input.focus()

      // Simulate Ctrl+Z while input is focused
      const event = new KeyboardEvent('keydown', {
        key: 'z',
        ctrlKey: true,
        bubbles: true,
      })

      await act(async () => {
        input.dispatchEvent(event)
      })

      // Should not have called undo API
      expect(mockApiRequest).toHaveBeenCalledTimes(1) // Only initial fetch

      document.body.removeChild(input)
    })
  })
})
