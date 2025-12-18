/**
 * VersionProvider
 *
 * Provides global version selection state to the entire application.
 * Persists selection to localStorage and auto-selects a sensible default.
 *
 * Features:
 * - Persists selection to localStorage (survives page refresh)
 * - Auto-selects first "working" or "submitted" version if none persisted
 * - Validates persisted ID against available versions
 * - Provides both ID and full version object
 */

import React, { useEffect, useState, useCallback, useMemo } from 'react'
import { useVersions } from '@/hooks/api/useVersions'
import { VersionContext, type VersionContextType } from './VersionContext'
import type { BudgetVersion } from '@/types/api'

/** LocalStorage key for persisting selected version */
const STORAGE_KEY = 'efir-selected-version'

/**
 * Get the persisted version ID from localStorage.
 * Returns undefined if not found or invalid.
 */
function getPersistedVersionId(): string | undefined {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    return stored ?? undefined
  } catch {
    // localStorage may be unavailable (e.g., private browsing)
    return undefined
  }
}

/**
 * Persist the selected version ID to localStorage.
 */
function persistVersionId(id: string | undefined): void {
  try {
    if (id) {
      localStorage.setItem(STORAGE_KEY, id)
    } else {
      localStorage.removeItem(STORAGE_KEY)
    }
  } catch {
    // localStorage may be unavailable
    console.warn('[VersionProvider] Failed to persist version ID')
  }
}

/**
 * Find the best default version to auto-select.
 * Priority: working > submitted > approved > any
 */
function findDefaultVersion(versions: BudgetVersion[]): BudgetVersion | undefined {
  // First, try to find a "working" version (most common use case)
  const working = versions.find((v) => v.status === 'working')
  if (working) return working

  // Next, try a "submitted" version
  const submitted = versions.find((v) => v.status === 'submitted')
  if (submitted) return submitted

  // Then, try an "approved" version
  const approved = versions.find((v) => v.status === 'approved')
  if (approved) return approved

  // Finally, return the first version if any exist
  return versions[0]
}

export function VersionProvider({ children }: { children: React.ReactNode }) {
  // Fetch all versions - query is enabled based on session existence
  const {
    data: versionsData,
    isLoading: versionsLoading,
    isFetching: versionsFetching,
    error: versionsError,
  } = useVersions({ page: 1, pageSize: 100 }) // Fetch up to 100 versions

  // Extract versions array
  const versions = useMemo(() => {
    return versionsData?.items ?? []
  }, [versionsData])

  // Track the selected version ID
  const [selectedVersionId, setSelectedVersionIdState] = useState<string | undefined>(() => {
    // Initialize from localStorage
    return getPersistedVersionId()
  })

  // Track if we've auto-selected (to avoid re-selecting on every render)
  const [hasAutoSelected, setHasAutoSelected] = useState(false)

  // Auto-select a default version when versions load (if none selected)
  useEffect(() => {
    // Don't auto-select if:
    // - Versions are still loading
    // - We've already auto-selected
    if (versionsLoading || hasAutoSelected) {
      return
    }

    // If we have a persisted ID, validate it still exists
    if (selectedVersionId) {
      const exists = versions.some((v) => v.id === selectedVersionId)
      if (exists) {
        // Persisted version is valid, keep it
        setHasAutoSelected(true)
        return
      }
      // Persisted version no longer exists (or no versions at all), clear it
      console.log('[VersionProvider] Persisted version no longer exists, clearing')
      setSelectedVersionIdState(undefined)
      persistVersionId(undefined)
      // Mark as auto-selected to prevent re-running this block
      setHasAutoSelected(true)
      return
    }

    // If no versions exist, just mark as auto-selected and return
    if (versions.length === 0) {
      setHasAutoSelected(true)
      return
    }

    // Auto-select a default version
    const defaultVersion = findDefaultVersion(versions)
    if (defaultVersion) {
      console.log(
        '[VersionProvider] Auto-selecting version:',
        defaultVersion.name,
        `(${defaultVersion.status})`
      )
      setSelectedVersionIdState(defaultVersion.id)
      persistVersionId(defaultVersion.id)
    }

    setHasAutoSelected(true)
    // eslint-disable-next-line react-hooks/exhaustive-deps -- Only run once when conditions are met, selectedVersionId changes are handled internally
  }, [versionsLoading, versions, hasAutoSelected])

  // Handler to update selected version
  const setSelectedVersionId = useCallback((id: string | undefined) => {
    setSelectedVersionIdState(id)
    persistVersionId(id)
  }, [])

  // Handler to clear selection
  const clearSelection = useCallback(() => {
    setSelectedVersionIdState(undefined)
    persistVersionId(undefined)
  }, [])

  // Find the full version object for the selected ID
  const selectedVersion = useMemo(() => {
    if (!selectedVersionId) return null
    return versions.find((v) => v.id === selectedVersionId) ?? null
  }, [selectedVersionId, versions])

  // Compute loading state - use versionsLoading for initial load, isFetching for refetch
  const isLoading = versionsLoading || versionsFetching

  // Only expose the selectedVersionId after validation is complete
  // This prevents stale localStorage IDs from triggering API calls before validation
  const validatedVersionId = hasAutoSelected ? selectedVersionId : undefined
  const validatedVersion = hasAutoSelected ? selectedVersion : null

  // Build context value
  const value: VersionContextType = useMemo(
    () => ({
      selectedVersionId: validatedVersionId,
      selectedVersion: validatedVersion,
      setSelectedVersionId,
      versions,
      isLoading: isLoading || !hasAutoSelected, // Include validation in loading state
      error: versionsError as Error | null,
      clearSelection,
    }),
    [
      validatedVersionId,
      validatedVersion,
      setSelectedVersionId,
      versions,
      isLoading,
      hasAutoSelected,
      versionsError,
      clearSelection,
    ]
  )

  return <VersionContext.Provider value={value}>{children}</VersionContext.Provider>
}

// Backward compatibility alias
export const BudgetVersionProvider = VersionProvider
