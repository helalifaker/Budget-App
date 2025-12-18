/**
 * Tests for useHistoricalImport Hooks
 *
 * Tests cover:
 * - Preview import mutation
 * - Execute import mutation
 * - Import history query
 * - Download template mutation
 * - Delete historical data mutation
 * - Query key invalidation
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor, act } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  usePreviewImport,
  useExecuteImport,
  useImportHistory,
  useDownloadTemplate,
  useDeleteHistoricalData,
  historicalImportKeys,
} from '@/hooks/api/useHistoricalImport'
import { historicalImportService } from '@/services/historical-import'
import type {
  ImportPreviewResponse,
  ImportResultResponse,
  ImportHistoryEntry,
} from '@/services/historical-import'

// Mock the historical import service
vi.mock('@/services/historical-import', () => ({
  historicalImportService: {
    previewImport: vi.fn(),
    executeImport: vi.fn(),
    getImportHistory: vi.fn(),
    downloadTemplate: vi.fn(),
    deleteHistoricalData: vi.fn(),
  },
}))

// Mock window methods for download test
const mockCreateObjectURL = vi.fn(() => 'blob:mock-url')
const mockRevokeObjectURL = vi.fn()
const mockClick = vi.fn()

describe('useHistoricalImport Hooks', () => {
  let queryClient: QueryClient

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

    // Setup window mocks
    global.URL.createObjectURL = mockCreateObjectURL
    global.URL.revokeObjectURL = mockRevokeObjectURL
  })

  afterEach(() => {
    queryClient.clear()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('historicalImportKeys', () => {
    it('should generate correct base key', () => {
      expect(historicalImportKeys.all).toEqual(['historicalImport'])
    })

    it('should generate history key without filters', () => {
      expect(historicalImportKeys.history()).toEqual([
        'historicalImport',
        'history',
        undefined,
        undefined,
      ])
    })

    it('should generate history key with fiscal year filter', () => {
      expect(historicalImportKeys.history(2024)).toEqual([
        'historicalImport',
        'history',
        2024,
        undefined,
      ])
    })

    it('should generate history key with both filters', () => {
      expect(historicalImportKeys.history(2024, 'enrollment')).toEqual([
        'historicalImport',
        'history',
        2024,
        'enrollment',
      ])
    })
  })

  describe('usePreviewImport', () => {
    const mockFile = new File(['test data'], 'test.csv', { type: 'text/csv' })
    const mockPreviewResponse: ImportPreviewResponse = {
      fiscal_year: 2024,
      detected_module: 'enrollment',
      total_rows: 10,
      valid_rows: 8,
      invalid_rows: 2,
      warnings: ['Row 5: Missing optional field'],
      errors: ['Row 9: Invalid value'],
      sample_data: [{ level_code: '6EME', student_count: 120 }],
      can_import: true,
    }

    it('should preview import file successfully', async () => {
      vi.mocked(historicalImportService.previewImport).mockResolvedValue(mockPreviewResponse)

      const { result } = renderHook(() => usePreviewImport(), { wrapper })

      // Initially should have empty state
      expect(result.current.previewData).toBeUndefined()
      expect(result.current.isPreviewLoading).toBe(false)
      expect(result.current.previewError).toBeNull()

      // Execute preview
      act(() => {
        result.current.preview({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Wait for mutation to complete
      await waitFor(() => {
        expect(result.current.isPreviewLoading).toBe(false)
        expect(result.current.previewData).toBeDefined()
      })

      // Verify service was called correctly
      expect(historicalImportService.previewImport).toHaveBeenCalledWith(mockFile, 2024, undefined)

      // Verify result
      expect(result.current.previewData).toEqual(mockPreviewResponse)
    })

    it('should preview with module override', async () => {
      vi.mocked(historicalImportService.previewImport).mockResolvedValue(mockPreviewResponse)

      const { result } = renderHook(() => usePreviewImport(), { wrapper })

      await act(async () => {
        await result.current.previewAsync({
          file: mockFile,
          fiscalYear: 2024,
          module: 'enrollment',
        })
      })

      expect(historicalImportService.previewImport).toHaveBeenCalledWith(
        mockFile,
        2024,
        'enrollment'
      )
    })

    it('should handle preview error', async () => {
      const error = new Error('Failed to parse file')
      vi.mocked(historicalImportService.previewImport).mockRejectedValue(error)

      const { result } = renderHook(() => usePreviewImport(), { wrapper })

      // Use mutate and wait for error state
      act(() => {
        result.current.preview({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Wait for error state to be set
      await waitFor(() => {
        expect(result.current.previewError).not.toBeNull()
      })

      expect(result.current.previewError?.message).toBe('Failed to parse file')
    })

    it('should update isPreviewLoading during mutation', async () => {
      vi.mocked(historicalImportService.previewImport).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(
              () =>
                resolve({
                  ...mockPreviewResponse,
                }),
              100
            )
          )
      )

      const { result } = renderHook(() => usePreviewImport(), { wrapper })

      expect(result.current.isPreviewLoading).toBe(false)

      // Start preview
      const previewPromise = result.current.previewAsync({
        file: mockFile,
        fiscalYear: 2024,
      })

      // Should be loading
      await waitFor(() => {
        expect(result.current.isPreviewLoading).toBe(true)
      })

      await previewPromise

      // Should be done loading
      await waitFor(() => {
        expect(result.current.isPreviewLoading).toBe(false)
      })
    })

    it('should reset preview state', async () => {
      vi.mocked(historicalImportService.previewImport).mockResolvedValue(mockPreviewResponse)

      const { result } = renderHook(() => usePreviewImport(), { wrapper })

      // Execute preview
      act(() => {
        result.current.preview({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Wait for mutation to complete
      await waitFor(() => {
        expect(result.current.previewData).toBeDefined()
      })

      // Reset
      act(() => {
        result.current.resetPreview()
      })

      // Verify reset
      await waitFor(() => {
        expect(result.current.previewData).toBeUndefined()
      })
      expect(result.current.previewError).toBeNull()
    })
  })

  describe('useExecuteImport', () => {
    const mockFile = new File(['test data'], 'test.csv', { type: 'text/csv' })
    const mockImportResult: ImportResultResponse = {
      fiscal_year: 2024,
      module: 'enrollment',
      status: 'success',
      imported_count: 10,
      updated_count: 0,
      skipped_count: 0,
      error_count: 0,
      message: 'Import successful',
      errors: [],
    }

    it('should execute import successfully', async () => {
      vi.mocked(historicalImportService.executeImport).mockResolvedValue(mockImportResult)

      const { result } = renderHook(() => useExecuteImport(), { wrapper })

      expect(result.current.importResult).toBeUndefined()
      expect(result.current.isImporting).toBe(false)

      // Execute import
      act(() => {
        result.current.execute({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Wait for mutation to complete
      await waitFor(() => {
        expect(result.current.isImporting).toBe(false)
        expect(result.current.importResult).toBeDefined()
      })

      expect(historicalImportService.executeImport).toHaveBeenCalledWith(
        mockFile,
        2024,
        undefined,
        undefined
      )
      expect(result.current.importResult).toEqual(mockImportResult)
    })

    it('should execute import with module and overwrite', async () => {
      vi.mocked(historicalImportService.executeImport).mockResolvedValue(mockImportResult)

      const { result } = renderHook(() => useExecuteImport(), { wrapper })

      await act(async () => {
        await result.current.executeAsync({
          file: mockFile,
          fiscalYear: 2024,
          module: 'enrollment',
          overwrite: true,
        })
      })

      expect(historicalImportService.executeImport).toHaveBeenCalledWith(
        mockFile,
        2024,
        'enrollment',
        true
      )
    })

    it('should invalidate queries on success', async () => {
      vi.mocked(historicalImportService.executeImport).mockResolvedValue(mockImportResult)

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const { result } = renderHook(() => useExecuteImport(), { wrapper })

      await act(async () => {
        await result.current.executeAsync({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Should invalidate import history
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: historicalImportKeys.all })
      // Should invalidate historical data queries
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['historical'] })
    })

    it('should handle import error', async () => {
      const error = new Error('Import failed')
      vi.mocked(historicalImportService.executeImport).mockRejectedValue(error)

      const { result } = renderHook(() => useExecuteImport(), { wrapper })

      // Use mutate and wait for error state
      act(() => {
        result.current.execute({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Wait for error state
      await waitFor(() => {
        expect(result.current.importError).not.toBeNull()
      })

      expect(result.current.importError?.message).toBe('Import failed')
    })

    it('should handle partial success', async () => {
      const partialResult: ImportResultResponse = {
        ...mockImportResult,
        status: 'partial',
        imported_count: 8,
        error_count: 2,
        errors: ['Row 5: Invalid data', 'Row 9: Missing required field'],
      }
      vi.mocked(historicalImportService.executeImport).mockResolvedValue(partialResult)

      const { result } = renderHook(() => useExecuteImport(), { wrapper })

      // Execute import
      act(() => {
        result.current.execute({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Wait for mutation to complete
      await waitFor(() => {
        expect(result.current.importResult).toBeDefined()
      })

      expect(result.current.importResult?.status).toBe('partial')
      expect(result.current.importResult?.error_count).toBe(2)
    })

    it('should reset import state', async () => {
      vi.mocked(historicalImportService.executeImport).mockResolvedValue(mockImportResult)

      const { result } = renderHook(() => useExecuteImport(), { wrapper })

      // Execute import
      act(() => {
        result.current.execute({
          file: mockFile,
          fiscalYear: 2024,
        })
      })

      // Wait for mutation to complete
      await waitFor(() => {
        expect(result.current.importResult).toBeDefined()
      })

      // Reset
      act(() => {
        result.current.resetImport()
      })

      // Verify reset
      await waitFor(() => {
        expect(result.current.importResult).toBeUndefined()
      })
      expect(result.current.importError).toBeNull()
    })
  })

  describe('useImportHistory', () => {
    const mockHistory: ImportHistoryEntry[] = [
      {
        id: 'history-1',
        fiscal_year: 2024,
        module: 'enrollment',
        imported_at: '2024-01-15T10:30:00Z',
        imported_by: 'user@example.com',
        record_count: 15,
        status: 'success',
      },
      {
        id: 'history-2',
        fiscal_year: 2023,
        module: 'revenue',
        imported_at: '2024-01-10T14:20:00Z',
        imported_by: 'admin@example.com',
        record_count: 42,
        status: 'success',
      },
    ]

    it('should fetch import history without filters', async () => {
      vi.mocked(historicalImportService.getImportHistory).mockResolvedValue(mockHistory)

      const { result } = renderHook(() => useImportHistory(), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalImportService.getImportHistory).toHaveBeenCalledWith(undefined, undefined)
      expect(result.current.data).toEqual(mockHistory)
    })

    it('should fetch import history with fiscal year filter', async () => {
      const filteredHistory = mockHistory.filter((h) => h.fiscal_year === 2024)
      vi.mocked(historicalImportService.getImportHistory).mockResolvedValue(filteredHistory)

      const { result } = renderHook(() => useImportHistory(2024), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalImportService.getImportHistory).toHaveBeenCalledWith(2024, undefined)
      expect(result.current.data).toHaveLength(1)
    })

    it('should fetch import history with both filters', async () => {
      const filteredHistory = mockHistory.filter(
        (h) => h.fiscal_year === 2024 && h.module === 'enrollment'
      )
      vi.mocked(historicalImportService.getImportHistory).mockResolvedValue(filteredHistory)

      const { result } = renderHook(() => useImportHistory(2024, 'enrollment'), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalImportService.getImportHistory).toHaveBeenCalledWith(2024, 'enrollment')
    })

    it('should handle fetch error', async () => {
      const error = new Error('Failed to fetch history')
      vi.mocked(historicalImportService.getImportHistory).mockRejectedValue(error)

      const { result } = renderHook(() => useImportHistory(), { wrapper })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })

    it('should update loading state', async () => {
      vi.mocked(historicalImportService.getImportHistory).mockImplementation(
        () =>
          new Promise((resolve) =>
            setTimeout(() => {
              resolve(mockHistory)
            }, 100)
          )
      )

      const { result } = renderHook(() => useImportHistory(), { wrapper })

      // Initially loading
      expect(result.current.isLoading).toBe(true)

      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })
    })
  })

  describe('useDownloadTemplate', () => {
    const mockBlob = new Blob(['test content'], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    })

    beforeEach(() => {
      // Mock createElement and appendChild
      const mockAnchor = {
        href: '',
        download: '',
        click: mockClick,
      } as unknown as HTMLAnchorElement

      vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor)
      vi.spyOn(document.body, 'appendChild').mockImplementation(
        () => document.body as unknown as HTMLAnchorElement
      )
      vi.spyOn(document.body, 'removeChild').mockImplementation(
        () => document.body as unknown as HTMLAnchorElement
      )
    })

    it('should download template successfully', async () => {
      vi.mocked(historicalImportService.downloadTemplate).mockResolvedValue(mockBlob)

      const { result } = renderHook(() => useDownloadTemplate(), { wrapper })

      expect(result.current.isDownloading).toBe(false)

      await act(async () => {
        result.current.downloadTemplate('enrollment')
      })

      // Wait for mutation to complete
      await waitFor(() => {
        expect(result.current.isDownloading).toBe(false)
      })

      expect(historicalImportService.downloadTemplate).toHaveBeenCalledWith('enrollment')
      expect(mockCreateObjectURL).toHaveBeenCalledWith(mockBlob)
      expect(mockClick).toHaveBeenCalled()
      expect(mockRevokeObjectURL).toHaveBeenCalledWith('blob:mock-url')
    })

    it('should set correct download filename', async () => {
      vi.mocked(historicalImportService.downloadTemplate).mockResolvedValue(mockBlob)

      const mockAnchor = {
        href: '',
        download: '',
        click: mockClick,
      } as unknown as HTMLAnchorElement
      vi.spyOn(document, 'createElement').mockReturnValue(mockAnchor)

      const { result } = renderHook(() => useDownloadTemplate(), { wrapper })

      await act(async () => {
        result.current.downloadTemplate('dhg')
      })

      await waitFor(() => {
        expect(result.current.isDownloading).toBe(false)
      })

      expect(mockAnchor.download).toBe('historical_dhg_template.xlsx')
    })

    it('should handle download error', async () => {
      const error = new Error('Download failed')
      vi.mocked(historicalImportService.downloadTemplate).mockRejectedValue(error)

      const { result } = renderHook(() => useDownloadTemplate(), { wrapper })

      await act(async () => {
        result.current.downloadTemplate('enrollment')
      })

      await waitFor(() => {
        expect(result.current.downloadError).toEqual(error)
      })
    })
  })

  describe('useDeleteHistoricalData', () => {
    it('should delete historical data successfully', async () => {
      vi.mocked(historicalImportService.deleteHistoricalData).mockResolvedValue()

      const { result } = renderHook(() => useDeleteHistoricalData(), { wrapper })

      expect(result.current.isDeleting).toBe(false)

      await act(async () => {
        await result.current.deleteDataAsync({ fiscalYear: 2024 })
      })

      expect(historicalImportService.deleteHistoricalData).toHaveBeenCalledWith(2024, undefined)
    })

    it('should delete with module filter', async () => {
      vi.mocked(historicalImportService.deleteHistoricalData).mockResolvedValue()

      const { result } = renderHook(() => useDeleteHistoricalData(), { wrapper })

      await act(async () => {
        await result.current.deleteDataAsync({ fiscalYear: 2024, module: 'enrollment' })
      })

      expect(historicalImportService.deleteHistoricalData).toHaveBeenCalledWith(2024, 'enrollment')
    })

    it('should invalidate queries on success', async () => {
      vi.mocked(historicalImportService.deleteHistoricalData).mockResolvedValue()

      const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries')

      const { result } = renderHook(() => useDeleteHistoricalData(), { wrapper })

      await act(async () => {
        await result.current.deleteDataAsync({ fiscalYear: 2024 })
      })

      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: historicalImportKeys.all })
      expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['historical'] })
    })

    it('should handle delete error', async () => {
      const error = new Error('Delete failed')
      vi.mocked(historicalImportService.deleteHistoricalData).mockRejectedValue(error)

      const { result } = renderHook(() => useDeleteHistoricalData(), { wrapper })

      // Use mutate and wait for error state
      act(() => {
        result.current.deleteData({ fiscalYear: 2024 })
      })

      // Wait for error state
      await waitFor(() => {
        expect(result.current.deleteError).not.toBeNull()
      })

      expect(result.current.deleteError?.message).toBe('Delete failed')
    })

    it('should update isDeleting during mutation', async () => {
      vi.mocked(historicalImportService.deleteHistoricalData).mockImplementation(
        () => new Promise((resolve) => setTimeout(resolve, 100))
      )

      const { result } = renderHook(() => useDeleteHistoricalData(), { wrapper })

      expect(result.current.isDeleting).toBe(false)

      const deletePromise = result.current.deleteDataAsync({ fiscalYear: 2024 })

      await waitFor(() => {
        expect(result.current.isDeleting).toBe(true)
      })

      await deletePromise

      await waitFor(() => {
        expect(result.current.isDeleting).toBe(false)
      })
    })
  })
})
