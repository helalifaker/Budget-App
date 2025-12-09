/**
 * Historical Import API Service
 *
 * Frontend service for importing historical actuals data via Excel/CSV files.
 */

import { apiRequest } from '@/lib/api-client'

/**
 * Supported import modules
 */
export type ImportModule = 'enrollment' | 'dhg' | 'revenue' | 'costs' | 'capex'

/**
 * Import status
 */
export type ImportStatus = 'success' | 'partial' | 'error'

/**
 * Import preview response from backend
 */
export interface ImportPreviewResponse {
  fiscal_year: number
  detected_module: ImportModule | null
  total_rows: number
  valid_rows: number
  invalid_rows: number
  warnings: string[]
  errors: string[]
  sample_data: Record<string, string | number | null>[]
  can_import: boolean
}

/**
 * Import result response from backend
 */
export interface ImportResultResponse {
  fiscal_year: number
  module: ImportModule
  status: ImportStatus
  imported_count: number
  updated_count: number
  skipped_count: number
  error_count: number
  message: string
  errors: string[]
}

/**
 * Import history entry
 */
export interface ImportHistoryEntry {
  id: string
  fiscal_year: number
  module: ImportModule
  imported_at: string
  imported_by: string | null
  record_count: number
  status: ImportStatus
}

/**
 * Historical import API service
 */
export const historicalImportService = {
  /**
   * Preview an import file without executing
   */
  previewImport: async (
    file: File,
    fiscalYear: number,
    module?: ImportModule
  ): Promise<ImportPreviewResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('fiscal_year', String(fiscalYear))
    if (module) {
      formData.append('module', module)
    }

    // Use fetch directly for multipart/form-data
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    const response = await fetch(`${baseUrl}/admin/historical/preview`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Upload failed' }))
      throw new Error(error.detail || 'Failed to preview import')
    }

    return response.json()
  },

  /**
   * Execute an import
   */
  executeImport: async (
    file: File,
    fiscalYear: number,
    module?: ImportModule,
    overwrite: boolean = false
  ): Promise<ImportResultResponse> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('fiscal_year', String(fiscalYear))
    if (module) {
      formData.append('module', module)
    }
    formData.append('overwrite', String(overwrite))

    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    const response = await fetch(`${baseUrl}/admin/historical/import`, {
      method: 'POST',
      body: formData,
      credentials: 'include',
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Import failed' }))
      throw new Error(error.detail || 'Failed to execute import')
    }

    return response.json()
  },

  /**
   * Get import history
   */
  getImportHistory: async (
    fiscalYear?: number,
    module?: ImportModule,
    limit: number = 50
  ): Promise<ImportHistoryEntry[]> => {
    const params = new URLSearchParams()
    if (fiscalYear) params.append('fiscal_year', String(fiscalYear))
    if (module) params.append('module', module)
    params.append('limit', String(limit))

    return apiRequest<ImportHistoryEntry[]>({
      method: 'GET',
      url: `/admin/historical/history?${params.toString()}`,
    })
  },

  /**
   * Download template for a module
   */
  downloadTemplate: async (module: ImportModule): Promise<Blob> => {
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
    const response = await fetch(`${baseUrl}/admin/historical/template/${module}`, {
      method: 'GET',
      credentials: 'include',
    })

    if (!response.ok) {
      throw new Error('Failed to download template')
    }

    return response.blob()
  },

  /**
   * Delete historical data for a fiscal year
   */
  deleteHistoricalData: async (fiscalYear: number, module?: ImportModule): Promise<void> => {
    const params = module ? `?module=${module}` : ''
    return apiRequest<void>({
      method: 'DELETE',
      url: `/admin/historical/${fiscalYear}${params}`,
    })
  },
}
