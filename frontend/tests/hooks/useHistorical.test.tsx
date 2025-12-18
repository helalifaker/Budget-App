/**
 * Tests for useHistorical Hooks
 *
 * Tests cover:
 * - All 6 historical data hooks (enrollment, classes, dhg, revenue, costs, capex)
 * - Query key generation
 * - Enabled/disabled behavior
 * - Custom history years parameter
 * - Error handling
 * - Loading states
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, waitFor } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import {
  historicalKeys,
  useEnrollmentWithHistory,
  useClassesWithHistory,
  useDHGWithHistory,
  useRevenueWithHistory,
  useCostsWithHistory,
  useCapExWithHistory,
} from '@/hooks/api/useHistorical'
import { historicalService } from '@/services/historical'
import type {
  EnrollmentWithHistoryResponse,
  ClassStructureWithHistoryResponse,
  DHGWithHistoryResponse,
  RevenueWithHistoryResponse,
  CostsWithHistoryResponse,
  CapExWithHistoryResponse,
} from '@/types/historical'

// Mock the historical service
vi.mock('@/services/historical', () => ({
  historicalService: {
    getEnrollmentWithHistory: vi.fn(),
    getClassesWithHistory: vi.fn(),
    getDHGWithHistory: vi.fn(),
    getRevenueWithHistory: vi.fn(),
    getCostsWithHistory: vi.fn(),
    getCapExWithHistory: vi.fn(),
  },
}))

describe('useHistorical Hooks', () => {
  let queryClient: QueryClient
  const testVersionId = 'version-123'

  // Mock data factory functions
  const createMockHistoricalComparison = () => ({
    n_minus_2: { fiscal_year: 2022, value: 100, is_actual: true },
    n_minus_1: { fiscal_year: 2023, value: 110, is_actual: true },
    current: 120,
    vs_n_minus_1_abs: 10,
    vs_n_minus_1_pct: 9.09,
    vs_n_minus_2_abs: 20,
    vs_n_minus_2_pct: 20.0,
  })

  const mockEnrollmentResponse: EnrollmentWithHistoryResponse = {
    version_id: testVersionId,
    fiscal_year: 2024,
    current_fiscal_year: 2024,
    rows: [
      {
        level_id: 'level-1',
        level_code: '6EME',
        level_name: 'Sixième',
        student_count: 120,
        history: createMockHistoricalComparison(),
      },
    ],
    totals: createMockHistoricalComparison(),
  }

  const mockClassesResponse: ClassStructureWithHistoryResponse = {
    version_id: testVersionId,
    fiscal_year: 2024,
    current_fiscal_year: 2024,
    rows: [
      {
        level_id: 'level-1',
        level_code: '6EME',
        level_name: 'Sixième',
        class_count: 5,
        average_class_size: 24,
        history: createMockHistoricalComparison(),
      },
    ],
    totals: createMockHistoricalComparison(),
  }

  const mockDHGResponse: DHGWithHistoryResponse = {
    version_id: testVersionId,
    fiscal_year: 2024,
    current_fiscal_year: 2024,
    rows: [
      {
        subject_id: 'subject-1',
        subject_code: 'MATH',
        subject_name: 'Mathématiques',
        total_hours: 150,
        fte: 8.33,
        hours_history: createMockHistoricalComparison(),
        fte_history: createMockHistoricalComparison(),
      },
    ],
    totals_hours: createMockHistoricalComparison(),
    totals_fte: createMockHistoricalComparison(),
  }

  const mockRevenueResponse: RevenueWithHistoryResponse = {
    version_id: testVersionId,
    fiscal_year: 2024,
    current_fiscal_year: 2024,
    rows: [
      {
        account_code: '70100',
        account_name: 'Tuition Revenue',
        fee_type: 'tuition',
        amount_sar: 45000000,
        history: createMockHistoricalComparison(),
      },
    ],
    totals: createMockHistoricalComparison(),
  }

  const mockCostsResponse: CostsWithHistoryResponse = {
    version_id: testVersionId,
    fiscal_year: 2024,
    current_fiscal_year: 2024,
    rows: [
      {
        account_code: '64100',
        account_name: 'Teacher Salaries',
        cost_category: 'personnel',
        amount_sar: 28000000,
        history: createMockHistoricalComparison(),
      },
    ],
    totals: createMockHistoricalComparison(),
    personnel_totals: createMockHistoricalComparison(),
    operating_totals: createMockHistoricalComparison(),
  }

  const mockCapExResponse: CapExWithHistoryResponse = {
    version_id: testVersionId,
    fiscal_year: 2024,
    current_fiscal_year: 2024,
    rows: [
      {
        account_code: '21500',
        account_name: 'Equipment',
        category: 'equipment',
        amount_sar: 2000000,
        history: createMockHistoricalComparison(),
      },
    ],
    totals: createMockHistoricalComparison(),
  }

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  afterEach(() => {
    queryClient.clear()
  })

  const wrapper = ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )

  describe('historicalKeys', () => {
    it('should generate correct base key', () => {
      expect(historicalKeys.all).toEqual(['historical'])
    })

    it('should generate enrollment key', () => {
      expect(historicalKeys.enrollment(testVersionId)).toEqual([
        'historical',
        'enrollment',
        testVersionId,
      ])
    })

    it('should generate classes key', () => {
      expect(historicalKeys.classes(testVersionId)).toEqual([
        'historical',
        'classes',
        testVersionId,
      ])
    })

    it('should generate dhg key', () => {
      expect(historicalKeys.dhg(testVersionId)).toEqual(['historical', 'dhg', testVersionId])
    })

    it('should generate revenue key', () => {
      expect(historicalKeys.revenue(testVersionId)).toEqual([
        'historical',
        'revenue',
        testVersionId,
      ])
    })

    it('should generate costs key', () => {
      expect(historicalKeys.costs(testVersionId)).toEqual(['historical', 'costs', testVersionId])
    })

    it('should generate capex key', () => {
      expect(historicalKeys.capex(testVersionId)).toEqual(['historical', 'capex', testVersionId])
    })
  })

  describe('useEnrollmentWithHistory', () => {
    it('should fetch enrollment data with history', async () => {
      vi.mocked(historicalService.getEnrollmentWithHistory).mockResolvedValue(
        mockEnrollmentResponse
      )

      const { result } = renderHook(() => useEnrollmentWithHistory(testVersionId), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalService.getEnrollmentWithHistory).toHaveBeenCalledWith(testVersionId, {
        history_years: 2,
      })
      expect(result.current.data).toEqual(mockEnrollmentResponse)
    })

    it('should respect custom history years', async () => {
      vi.mocked(historicalService.getEnrollmentWithHistory).mockResolvedValue(
        mockEnrollmentResponse
      )

      const { result } = renderHook(
        () => useEnrollmentWithHistory(testVersionId, { historyYears: 3 }),
        { wrapper }
      )

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalService.getEnrollmentWithHistory).toHaveBeenCalledWith(testVersionId, {
        history_years: 3,
      })
    })

    it('should be disabled when versionId is undefined', () => {
      const { result } = renderHook(() => useEnrollmentWithHistory(undefined), { wrapper })

      expect(result.current.fetchStatus).toBe('idle')
      expect(historicalService.getEnrollmentWithHistory).not.toHaveBeenCalled()
    })

    it('should be disabled when enabled option is false', () => {
      const { result } = renderHook(
        () => useEnrollmentWithHistory(testVersionId, { enabled: false }),
        { wrapper }
      )

      expect(result.current.fetchStatus).toBe('idle')
      expect(historicalService.getEnrollmentWithHistory).not.toHaveBeenCalled()
    })

    it('should handle fetch error', async () => {
      const error = new Error('Failed to fetch enrollment history')
      vi.mocked(historicalService.getEnrollmentWithHistory).mockRejectedValue(error)

      const { result } = renderHook(() => useEnrollmentWithHistory(testVersionId), { wrapper })

      await waitFor(() => {
        expect(result.current.isError).toBe(true)
      })

      expect(result.current.error).toEqual(error)
    })
  })

  describe('useClassesWithHistory', () => {
    it('should fetch class structure data with history', async () => {
      vi.mocked(historicalService.getClassesWithHistory).mockResolvedValue(mockClassesResponse)

      const { result } = renderHook(() => useClassesWithHistory(testVersionId), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalService.getClassesWithHistory).toHaveBeenCalledWith(testVersionId, {
        history_years: 2,
      })
      expect(result.current.data).toEqual(mockClassesResponse)
    })

    it('should be disabled when versionId is undefined', () => {
      const { result } = renderHook(() => useClassesWithHistory(undefined), { wrapper })

      expect(result.current.fetchStatus).toBe('idle')
    })
  })

  describe('useDHGWithHistory', () => {
    it('should fetch DHG data with history', async () => {
      vi.mocked(historicalService.getDHGWithHistory).mockResolvedValue(mockDHGResponse)

      const { result } = renderHook(() => useDHGWithHistory(testVersionId), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalService.getDHGWithHistory).toHaveBeenCalledWith(testVersionId, {
        history_years: 2,
      })
      expect(result.current.data).toEqual(mockDHGResponse)
    })

    it('should be disabled when versionId is undefined', () => {
      const { result } = renderHook(() => useDHGWithHistory(undefined), { wrapper })

      expect(result.current.fetchStatus).toBe('idle')
    })
  })

  describe('useRevenueWithHistory', () => {
    it('should fetch revenue data with history', async () => {
      vi.mocked(historicalService.getRevenueWithHistory).mockResolvedValue(mockRevenueResponse)

      const { result } = renderHook(() => useRevenueWithHistory(testVersionId), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalService.getRevenueWithHistory).toHaveBeenCalledWith(testVersionId, {
        history_years: 2,
      })
      expect(result.current.data).toEqual(mockRevenueResponse)
    })

    it('should be disabled when versionId is undefined', () => {
      const { result } = renderHook(() => useRevenueWithHistory(undefined), { wrapper })

      expect(result.current.fetchStatus).toBe('idle')
    })
  })

  describe('useCostsWithHistory', () => {
    it('should fetch costs data with history', async () => {
      vi.mocked(historicalService.getCostsWithHistory).mockResolvedValue(mockCostsResponse)

      const { result } = renderHook(() => useCostsWithHistory(testVersionId), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalService.getCostsWithHistory).toHaveBeenCalledWith(testVersionId, {
        history_years: 2,
      })
      expect(result.current.data).toEqual(mockCostsResponse)
    })

    it('should be disabled when versionId is undefined', () => {
      const { result } = renderHook(() => useCostsWithHistory(undefined), { wrapper })

      expect(result.current.fetchStatus).toBe('idle')
    })
  })

  describe('useCapExWithHistory', () => {
    it('should fetch CapEx data with history', async () => {
      vi.mocked(historicalService.getCapExWithHistory).mockResolvedValue(mockCapExResponse)

      const { result } = renderHook(() => useCapExWithHistory(testVersionId), { wrapper })

      await waitFor(() => {
        expect(result.current.isSuccess).toBe(true)
      })

      expect(historicalService.getCapExWithHistory).toHaveBeenCalledWith(testVersionId, {
        history_years: 2,
      })
      expect(result.current.data).toEqual(mockCapExResponse)
    })

    it('should be disabled when versionId is undefined', () => {
      const { result } = renderHook(() => useCapExWithHistory(undefined), { wrapper })

      expect(result.current.fetchStatus).toBe('idle')
    })
  })

  describe('loading states', () => {
    it('should show loading state while fetching', async () => {
      vi.mocked(historicalService.getEnrollmentWithHistory).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve(mockEnrollmentResponse), 100))
      )

      const { result } = renderHook(() => useEnrollmentWithHistory(testVersionId), { wrapper })

      // Should be loading initially
      expect(result.current.isLoading).toBe(true)
      expect(result.current.data).toBeUndefined()

      // Wait for data to load
      await waitFor(() => {
        expect(result.current.isLoading).toBe(false)
      })

      expect(result.current.data).toEqual(mockEnrollmentResponse)
    })
  })

  describe('stale time', () => {
    it('should use cached data within stale time', async () => {
      vi.mocked(historicalService.getEnrollmentWithHistory).mockResolvedValue(
        mockEnrollmentResponse
      )

      // First render
      const { result: result1 } = renderHook(() => useEnrollmentWithHistory(testVersionId), {
        wrapper,
      })

      await waitFor(() => {
        expect(result1.current.isSuccess).toBe(true)
      })

      expect(historicalService.getEnrollmentWithHistory).toHaveBeenCalledTimes(1)

      // Second render - should use cache
      const { result: result2 } = renderHook(() => useEnrollmentWithHistory(testVersionId), {
        wrapper,
      })

      // Should immediately have data (from cache)
      expect(result2.current.data).toEqual(mockEnrollmentResponse)
      // Should not call service again
      expect(historicalService.getEnrollmentWithHistory).toHaveBeenCalledTimes(1)
    })
  })
})
