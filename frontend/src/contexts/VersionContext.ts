/**
 * VersionContext
 *
 * Global context for managing version selection across the application.
 * Solves the problem of users having to re-select their version on every page.
 *
 * Features:
 * - Persists selection to localStorage
 * - Auto-selects first "working" or "submitted" version if none persisted
 * - Provides both the version ID and full version object
 * - Syncs with TanStack Query cache
 */

import { createContext, useContext } from 'react'
import type { BudgetVersion } from '@/types/api'

export interface VersionContextType {
  /** Currently selected version ID */
  selectedVersionId: string | undefined

  /** Full version object for selected version */
  selectedVersion: BudgetVersion | null

  /** Update the selected version ID */
  setSelectedVersionId: (id: string | undefined) => void

  /** List of all available versions */
  versions: BudgetVersion[]

  /** Whether versions are still loading */
  isLoading: boolean

  /** Error state if version fetch failed */
  error: Error | null

  /** Clear the selected version */
  clearSelection: () => void
}

// Backward compatibility alias
export type BudgetVersionContextType = VersionContextType

export const VersionContext = createContext<VersionContextType | undefined>(undefined)

// Backward compatibility alias
export const BudgetVersionContext = VersionContext

/**
 * Hook to access the version context.
 * Must be used within a VersionProvider.
 *
 * @example
 * ```tsx
 * const { selectedVersionId, selectedVersion, setSelectedVersionId } = useVersion()
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
export function useVersion(): VersionContextType {
  const context = useContext(VersionContext)
  if (context === undefined) {
    throw new Error('useVersion must be used within a VersionProvider')
  }
  return context
}

// Backward compatibility alias
export const useBudgetVersion = useVersion
