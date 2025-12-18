import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  usePlanningWriteback,
  VersionConflictError,
  CellLockedError,
  BatchConflictError,
} from '@/hooks/api/usePlanningWriteback'
import { apiRequest } from '@/lib/api-client'
import { toast } from 'sonner'
import type { CellData } from '@/types/writeback'

// Mock dependencies
vi.mock('@/lib/api-client', () => ({
  apiRequest: vi.fn(),
}))

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    warning: vi.fn(),
  },
}))

describe('usePlanningWriteback', () => {
  let queryClient: QueryClient
  const versionId = 'budget-version-123'
  const mockCellData: CellData[] = [
    {
      id: 'cell-1',
      version_id: versionId,
      module_code: 'enrollment',
      entity_id: 'entity-1',
      field_name: 'student_count',
      period_code: 'T1',
      value_numeric: 100,
      version: 1,
      is_locked: false,
      modified_by: 'user-1',
      modified_at: '2025-01-01T10:00:00Z',
      created_at: '2025-01-01T09:00:00Z',
    },
    {
      id: 'cell-2',
      version_id: versionId,
      module_code: 'enrollment',
      entity_id: 'entity-1',
      field_name: 'student_count',
      period_code: 'T2',
      value_numeric: 150,
      version: 1,
      is_locked: false,
      modified_by: 'user-1',
      modified_at: '2025-01-01T10:00:00Z',
      created_at: '2025-01-01T09:00:00Z',
    },
  ]

  beforeEach(() => {
    // Create fresh query client for each test
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })

    // Reset all mocks
    vi.clearAllMocks()

    // Pre-populate cache with cell data
    queryClient.setQueryData(['cells', versionId], mockCellData)
  })

  afterEach(() => {
    queryClient.clear()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('updateCell', () => {
    it('should optimistically update cell value before server response', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock successful API response with delay to ensure optimistic update happens first
      vi.mocked(apiRequest).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  id: 'cell-1',
                  value_numeric: 200,
                  version: 2,
                  modified_by: 'user-1',
                  modified_at: '2025-01-01T11:00:00Z',
                }),
              10
            )
          )
      )

      // Start update
      const updatePromise = result.current.updateCell({
        cellId: 'cell-1',
        value: 200,
        version: 1,
      })

      // Wait for optimistic update to be applied (onMutate is async due to cancelQueries)
      await waitFor(() => {
        const cacheData = queryClient.getQueryData<CellData[]>(['cells', versionId])
        expect(cacheData?.[0].value_numeric).toBe(200)
        expect(cacheData?.[0].version).toBe(2) // Version incremented optimistically
      })

      // Wait for server response
      await updatePromise

      // Verify API was called
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'PUT',
        url: '/writeback/cells/cell-1',
        data: {
          value_numeric: 200,
          version: 1,
        },
      })

      // Verify success toast
      expect(toast.success).toHaveBeenCalledWith('Cellule sauvegardée', { duration: 1000 })
    })

    it('should rollback optimistic update on version conflict', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock version conflict error
      const conflictError = {
        response: {
          status: 409,
          data: {
            detail: {
              message: 'Version conflict',
              cell_id: 'cell-1',
              expected_version: 1,
              actual_version: 2,
            },
          },
        },
      }
      vi.mocked(apiRequest).mockRejectedValue(conflictError)

      // Attempt update
      await expect(
        result.current.updateCell({
          cellId: 'cell-1',
          value: 200,
          version: 1,
        })
      ).rejects.toThrow(VersionConflictError)

      // Wait for rollback
      await waitFor(() => {
        const cacheData = queryClient.getQueryData<CellData[]>(['cells', versionId])
        expect(cacheData?.[0].value_numeric).toBe(100) // Rolled back to original
        expect(cacheData?.[0].version).toBe(1) // Version rolled back
      })

      // Verify error toast
      expect(toast.error).toHaveBeenCalledWith('Cellule modifiée par un autre utilisateur', {
        description: 'Les données ont été rechargées automatiquement.',
        duration: 4000,
      })
    })

    it('should handle locked cell error', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock locked cell error
      const lockedError = {
        response: {
          status: 423,
          data: {
            detail: {
              message: 'Cell is locked',
              cell_id: 'cell-1',
            },
          },
        },
      }
      vi.mocked(apiRequest).mockRejectedValue(lockedError)

      // Attempt update
      await expect(
        result.current.updateCell({
          cellId: 'cell-1',
          value: 200,
          version: 1,
        })
      ).rejects.toThrow(CellLockedError)

      // Wait for rollback
      await waitFor(() => {
        const cacheData = queryClient.getQueryData<CellData[]>(['cells', versionId])
        expect(cacheData?.[0].value_numeric).toBe(100) // Rolled back
      })

      // Verify error toast
      expect(toast.error).toHaveBeenCalledWith('Cellule verrouillée', {
        description: 'Cette cellule ne peut pas être modifiée.',
        duration: 3000,
      })
    })

    it('should update isUpdating flag during mutation', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock slow API response
      vi.mocked(apiRequest).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  id: 'cell-1',
                  value_numeric: 200,
                  version: 2,
                  modified_by: 'user-1',
                  modified_at: '2025-01-01T11:00:00Z',
                }),
              100
            )
          )
      )

      // isUpdating should be false initially
      expect(result.current.isUpdating).toBe(false)

      // Start update
      const updatePromise = result.current.updateCell({
        cellId: 'cell-1',
        value: 200,
        version: 1,
      })

      // isUpdating should be true during mutation
      await waitFor(() => {
        expect(result.current.isUpdating).toBe(true)
      })

      // Wait for completion
      await updatePromise

      // isUpdating should be false after completion
      await waitFor(() => {
        expect(result.current.isUpdating).toBe(false)
      })
    })
  })

  describe('batchUpdate', () => {
    it('should optimistically update multiple cells', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock successful batch response with delay
      vi.mocked(apiRequest).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  session_id: 'session-123',
                  updated_count: 2,
                  conflicts: [],
                }),
              10
            )
          )
      )

      // Start batch update
      const updatePromise = result.current.batchUpdate({
        sessionId: 'session-123',
        updates: [
          { cellId: 'cell-1', value: 200, version: 1 },
          { cellId: 'cell-2', value: 250, version: 1 },
        ],
      })

      // Wait for optimistic updates to be applied (onMutate is async)
      await waitFor(() => {
        const cacheData = queryClient.getQueryData<CellData[]>(['cells', versionId])
        expect(cacheData?.[0].value_numeric).toBe(200)
        expect(cacheData?.[1].value_numeric).toBe(250)
      })

      // Wait for server response
      await updatePromise

      // Verify API was called
      expect(apiRequest).toHaveBeenCalledWith({
        method: 'POST',
        url: '/writeback/cells/batch',
        data: {
          session_id: 'session-123',
          updates: [
            { cell_id: 'cell-1', value_numeric: 200, version: 1 },
            { cell_id: 'cell-2', value_numeric: 250, version: 1 },
          ],
        },
      })

      // Verify success toast
      expect(toast.success).toHaveBeenCalledWith('2 cellules sauvegardées', { duration: 2000 })
    })

    it('should show warning when conflicts are detected', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock batch response with conflicts
      vi.mocked(apiRequest).mockResolvedValue({
        session_id: 'session-123',
        updated_count: 1,
        conflicts: [
          {
            cell_id: 'cell-2',
            expected_version: 1,
            actual_version: 2,
            message: 'Version mismatch',
          },
        ],
      })

      // Start batch update
      await result.current.batchUpdate({
        sessionId: 'session-123',
        updates: [
          { cellId: 'cell-1', value: 200, version: 1 },
          { cellId: 'cell-2', value: 250, version: 1 },
        ],
      })

      // Verify warning toast
      expect(toast.warning).toHaveBeenCalledWith('1 cellules sauvegardées', {
        description: '1 conflit(s) détecté(s). Les données ont été rechargées.',
        duration: 5000,
      })
    })

    it('should rollback all updates on batch conflict error', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock batch conflict error
      const batchConflictError = {
        response: {
          status: 409,
          data: {
            detail: {
              message: 'Batch update conflicts detected',
              conflicts: [
                {
                  cell_id: 'cell-1',
                  expected_version: 1,
                  actual_version: 2,
                  message: 'Version conflict',
                },
              ],
            },
          },
        },
      }
      vi.mocked(apiRequest).mockRejectedValue(batchConflictError)

      // Attempt batch update
      await expect(
        result.current.batchUpdate({
          sessionId: 'session-123',
          updates: [
            { cellId: 'cell-1', value: 200, version: 1 },
            { cellId: 'cell-2', value: 250, version: 1 },
          ],
        })
      ).rejects.toThrow(BatchConflictError)

      // Wait for rollback
      await waitFor(() => {
        const cacheData = queryClient.getQueryData<CellData[]>(['cells', versionId])
        expect(cacheData?.[0].value_numeric).toBe(100) // Rolled back
        expect(cacheData?.[1].value_numeric).toBe(150) // Rolled back
      })

      // Verify error toast
      expect(toast.error).toHaveBeenCalledWith('Conflits détectés lors de la sauvegarde groupée', {
        description: '1 cellule(s) ont été modifiées par un autre utilisateur.',
        duration: 5000,
      })
    })
  })

  describe('cache invalidation', () => {
    it('should invalidate change history after successful update', async () => {
      const { result } = renderHook(() => usePlanningWriteback(versionId), { wrapper })

      // Mock successful API response
      vi.mocked(apiRequest).mockResolvedValue({
        id: 'cell-1',
        value_numeric: 200,
        version: 2,
        modified_by: 'user-1',
        modified_at: '2025-01-01T11:00:00Z',
      })

      // Spy on invalidateQueries
      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      // Update cell
      await result.current.updateCell({
        cellId: 'cell-1',
        value: 200,
        version: 1,
      })

      // Verify change history was invalidated
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['cell-changes', versionId] })
    })
  })
})
