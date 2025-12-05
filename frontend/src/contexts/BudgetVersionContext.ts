/**
 * BudgetVersionContext
 *
 * Global context for managing budget version selection across the application.
 * Solves the problem of users having to re-select their budget version on every page.
 *
 * Features:
 * - Persists selection to localStorage
 * - Auto-selects first "working" or "submitted" version if none persisted
 * - Provides both the version ID and full version object
 * - Syncs with TanStack Query cache
 */

import { createContext, useContext } from 'react'
import type { BudgetVersion } from '@/types/api'

export interface BudgetVersionContextType {
  /** Currently selected budget version ID */
  selectedVersionId: string | undefined

  /** Full budget version object for selected version */
  selectedVersion: BudgetVersion | null

  /** Update the selected version ID */
  setSelectedVersionId: (id: string | undefined) => void

  /** List of all available budget versions */
  versions: BudgetVersion[]

  /** Whether versions are still loading */
  isLoading: boolean

  /** Error state if version fetch failed */
  error: Error | null

  /** Clear the selected version */
  clearSelection: () => void
}

export const BudgetVersionContext = createContext<BudgetVersionContextType | undefined>(undefined)

/**
 * Hook to access the budget version context.
 * Must be used within a BudgetVersionProvider.
 *
 * @example
 * ```tsx
 * const { selectedVersionId, selectedVersion, setSelectedVersionId } = useBudgetVersion()
 *
 * // Use in data fetching
 * const { data } = useEnrollments(selectedVersionId)
 *
 * // Or access the full version object
 * if (selectedVersion?.status === 'approved') {
 *   // Show read-only mode
 * }
 * ```
 */
export function useBudgetVersion(): BudgetVersionContextType {
  const context = useContext(BudgetVersionContext)
  if (context === undefined) {
    throw new Error('useBudgetVersion must be used within a BudgetVersionProvider')
  }
  return context
}
