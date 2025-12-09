/**
 * useImpactCalculation Hook
 *
 * Debounced hook for calculating real-time impact of budget changes.
 * Waits 300ms after the last change before making an API call to avoid
 * flooding the server during rapid edits.
 */

import { useState, useCallback, useRef, useEffect } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import {
  impactService,
  ImpactCalculationRequest,
  ImpactCalculationResponse,
} from '@/services/impact'

const DEBOUNCE_DELAY = 300 // milliseconds

interface UseImpactCalculationOptions {
  /** Budget version ID */
  versionId: string | null
  /** Enable/disable the hook */
  enabled?: boolean
  /** Debounce delay in milliseconds (default: 300) */
  debounceMs?: number
}

interface UseImpactCalculationReturn {
  /** Current impact metrics */
  impact: ImpactCalculationResponse | null
  /** Whether calculation is in progress */
  isLoading: boolean
  /** Any error from the calculation */
  error: Error | null
  /** Function to trigger impact calculation */
  calculateImpact: (request: ImpactCalculationRequest) => void
  /** Function to clear current impact */
  clearImpact: () => void
  /** Whether there is a pending calculation */
  isPending: boolean
}

/**
 * Hook for calculating real-time budget impact with debouncing.
 *
 * @example
 * ```tsx
 * const { impact, isLoading, calculateImpact } = useImpactCalculation({
 *   versionId: selectedVersionId,
 * })
 *
 * // Call when user edits a cell
 * const handleCellChange = (event) => {
 *   calculateImpact({
 *     step_id: 'enrollment',
 *     dimension_type: 'level',
 *     dimension_id: event.data.level_id,
 *     field_name: 'student_count',
 *     new_value: event.newValue,
 *   })
 * }
 * ```
 */
export function useImpactCalculation({
  versionId,
  enabled = true,
  debounceMs = DEBOUNCE_DELAY,
}: UseImpactCalculationOptions): UseImpactCalculationReturn {
  const [pendingRequest, setPendingRequest] = useState<ImpactCalculationRequest | null>(null)
  const [isPending, setIsPending] = useState(false)
  const debounceTimerRef = useRef<number | null>(null)
  const queryClient = useQueryClient()

  // Query for impact calculation
  const {
    data: impact,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['impact', versionId, pendingRequest],
    queryFn: async () => {
      if (!versionId || !pendingRequest) {
        return null
      }
      return impactService.calculateImpact(versionId, pendingRequest)
    },
    enabled: enabled && !!versionId && !!pendingRequest,
    staleTime: 0, // Always refetch when request changes
    gcTime: 1000 * 60, // Cache for 1 minute
  })

  // Debounced calculation trigger
  const calculateImpact = useCallback(
    (request: ImpactCalculationRequest) => {
      // Clear any pending timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }

      // Show pending state immediately
      setIsPending(true)

      // Set up debounced update
      debounceTimerRef.current = setTimeout(() => {
        setPendingRequest(request)
        setIsPending(false)
      }, debounceMs)
    },
    [debounceMs]
  )

  // Clear impact
  const clearImpact = useCallback(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    setPendingRequest(null)
    setIsPending(false)
    // Invalidate the query cache
    queryClient.removeQueries({ queryKey: ['impact', versionId] })
  }, [versionId, queryClient])

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [])

  return {
    impact: impact ?? null,
    isLoading,
    error: error as Error | null,
    calculateImpact,
    clearImpact,
    isPending,
  }
}

/**
 * Helper function to format currency for impact display
 */
export function formatImpactCurrency(value: number): string {
  const absValue = Math.abs(value)
  const sign = value >= 0 ? '+' : '-'

  if (absValue >= 1_000_000) {
    return `${sign}${(absValue / 1_000_000).toFixed(1)}M SAR`
  }
  if (absValue >= 1_000) {
    return `${sign}${(absValue / 1_000).toFixed(0)}K SAR`
  }
  return `${sign}${absValue.toFixed(0)} SAR`
}

/**
 * Helper function to format FTE for impact display
 */
export function formatImpactFTE(value: number): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(1)} FTE`
}

/**
 * Helper function to format percentage for impact display
 */
export function formatImpactPercent(value: number): string {
  const sign = value >= 0 ? '+' : ''
  return `${sign}${value.toFixed(2)}%`
}
