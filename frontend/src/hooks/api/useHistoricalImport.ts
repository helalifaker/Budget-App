/**
 * useHistoricalImport Hooks
 *
 * React Query hooks for historical data import operations.
 */

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  historicalImportService,
  ImportModule,
  ImportPreviewResponse,
  ImportResultResponse,
  ImportHistoryEntry,
} from '@/services/historicalImport'

/**
 * Query keys for historical import
 */
export const historicalImportKeys = {
  all: ['historicalImport'] as const,
  history: (fiscalYear?: number, module?: ImportModule) =>
    [...historicalImportKeys.all, 'history', fiscalYear, module] as const,
}

/**
 * Hook for previewing an import file
 */
export function usePreviewImport() {
  const mutation = useMutation<
    ImportPreviewResponse,
    Error,
    { file: File; fiscalYear: number; module?: ImportModule }
  >({
    mutationFn: ({ file, fiscalYear, module }) =>
      historicalImportService.previewImport(file, fiscalYear, module),
  })

  return {
    preview: mutation.mutate,
    previewAsync: mutation.mutateAsync,
    previewData: mutation.data,
    isPreviewLoading: mutation.isPending,
    previewError: mutation.error,
    resetPreview: mutation.reset,
  }
}

/**
 * Hook for executing an import
 */
export function useExecuteImport() {
  const queryClient = useQueryClient()

  const mutation = useMutation<
    ImportResultResponse,
    Error,
    { file: File; fiscalYear: number; module?: ImportModule; overwrite?: boolean }
  >({
    mutationFn: ({ file, fiscalYear, module, overwrite }) =>
      historicalImportService.executeImport(file, fiscalYear, module, overwrite),
    onSuccess: () => {
      // Invalidate import history
      queryClient.invalidateQueries({ queryKey: historicalImportKeys.all })
      // Invalidate historical data queries so the grids refresh
      queryClient.invalidateQueries({ queryKey: ['historical'] })
    },
  })

  return {
    execute: mutation.mutate,
    executeAsync: mutation.mutateAsync,
    importResult: mutation.data,
    isImporting: mutation.isPending,
    importError: mutation.error,
    resetImport: mutation.reset,
  }
}

/**
 * Hook for fetching import history
 */
export function useImportHistory(fiscalYear?: number, module?: ImportModule) {
  return useQuery<ImportHistoryEntry[], Error>({
    queryKey: historicalImportKeys.history(fiscalYear, module),
    queryFn: () => historicalImportService.getImportHistory(fiscalYear, module),
  })
}

/**
 * Hook for downloading a template
 */
export function useDownloadTemplate() {
  const mutation = useMutation<Blob, Error, ImportModule>({
    mutationFn: (module) => historicalImportService.downloadTemplate(module),
    onSuccess: (blob, module) => {
      // Trigger download
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `historical_${module}_template.xlsx`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    },
  })

  return {
    downloadTemplate: mutation.mutate,
    isDownloading: mutation.isPending,
    downloadError: mutation.error,
  }
}

/**
 * Hook for deleting historical data
 */
export function useDeleteHistoricalData() {
  const queryClient = useQueryClient()

  const mutation = useMutation<void, Error, { fiscalYear: number; module?: ImportModule }>({
    mutationFn: ({ fiscalYear, module }) =>
      historicalImportService.deleteHistoricalData(fiscalYear, module),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: historicalImportKeys.all })
      queryClient.invalidateQueries({ queryKey: ['historical'] })
    },
  })

  return {
    deleteData: mutation.mutate,
    deleteDataAsync: mutation.mutateAsync,
    isDeleting: mutation.isPending,
    deleteError: mutation.error,
  }
}
