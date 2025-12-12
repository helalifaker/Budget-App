import { useState, useCallback, useRef, useEffect } from 'react'
import { useDebouncedCallback } from './useDebounce'

/**
 * Options for configuring the useDraft hook
 */
export interface UseDraftOptions<T> {
  /**
   * Unique identifier for this draft (e.g., budget version ID)
   */
  draftKey: string

  /**
   * Initial data to populate the draft from (server data)
   */
  initialData: T | undefined

  /**
   * Function to save draft to server (background auto-save)
   * Should NOT trigger expensive calculations
   */
  saveDraftFn: (data: T) => Promise<void>

  /**
   * Function to apply the draft (commit + run calculations)
   * This is the "Apply & Calculate" action
   */
  applyFn: (data: T) => Promise<T>

  /**
   * Debounce delay for auto-save in milliseconds
   * @default 500
   */
  debounceMs?: number

  /**
   * Compare function to determine if draft differs from initial
   * @default JSON.stringify comparison
   */
  compareFn?: (draft: T, initial: T) => boolean

  /**
   * Callback when draft is successfully applied
   */
  onApplySuccess?: (result: T) => void

  /**
   * Callback when draft save or apply fails
   */
  onError?: (error: Error) => void
}

/**
 * Status of the draft system
 */
export type DraftStatus = 'idle' | 'saving' | 'saved' | 'applying' | 'applied' | 'error'

/**
 * Return type for the useDraft hook
 */
export interface UseDraftReturn<T> {
  /**
   * Current draft data (local state)
   */
  draft: T | undefined

  /**
   * Update the draft (triggers debounced auto-save)
   */
  setDraft: (update: T | ((prev: T) => T)) => void

  /**
   * Update a single field in the draft
   */
  updateDraftField: <K extends keyof T>(field: K, value: T[K]) => void

  /**
   * Whether there are changes that haven't been applied
   */
  hasUnappliedChanges: boolean

  /**
   * Whether the draft is currently being saved to server
   */
  isSaving: boolean

  /**
   * Whether the apply action is in progress
   */
  isApplying: boolean

  /**
   * Current status of the draft system
   */
  status: DraftStatus

  /**
   * Timestamp of last successful apply
   */
  lastAppliedAt: Date | null

  /**
   * Apply the current draft (commit + calculate)
   */
  apply: () => Promise<void>

  /**
   * Discard draft changes and revert to initial data
   */
  discard: () => void

  /**
   * Force save the current draft immediately (bypasses debounce)
   */
  forceSave: () => Promise<void>

  /**
   * Whether the draft system is ready (has initial data)
   */
  isReady: boolean

  /**
   * Error from last failed operation
   */
  error: Error | null
}

/**
 * Default comparison function using JSON.stringify
 */
function defaultCompareFn<T>(draft: T, initial: T): boolean {
  return JSON.stringify(draft) === JSON.stringify(initial)
}

/**
 * Hook for managing draft state with auto-save and manual apply pattern.
 *
 * This hook provides the "Auto-Draft + Manual Apply" UX pattern:
 * - Edits are saved as drafts automatically (debounced)
 * - User explicitly applies changes to trigger expensive calculations
 * - Clear visual feedback on draft vs applied state
 * - Navigation blocking when there are unapplied changes
 *
 * @example
 * ```tsx
 * const { draft, setDraft, hasUnappliedChanges, apply, discard } = useDraft({
 *   draftKey: budgetVersionId,
 *   initialData: config?.global_overrides,
 *   saveDraftFn: (data) => api.saveDraft(versionId, data),
 *   applyFn: (data) => api.applyAndCalculate(versionId, data),
 * })
 *
 * // Update draft (instant local update + debounced save)
 * const handleChange = (field, value) => {
 *   updateDraftField(field, value)
 * }
 *
 * // Apply changes (explicit user action)
 * const handleApply = async () => {
 *   await apply()
 * }
 * ```
 */
export function useDraft<T extends object>(options: UseDraftOptions<T>): UseDraftReturn<T> {
  const {
    draftKey,
    initialData,
    saveDraftFn,
    applyFn,
    debounceMs = 500,
    compareFn = defaultCompareFn,
    onApplySuccess,
    onError,
  } = options

  // Local draft state
  const [draft, setDraftState] = useState<T | undefined>(initialData)
  const [status, setStatus] = useState<DraftStatus>('idle')
  const [lastAppliedAt, setLastAppliedAt] = useState<Date | null>(null)
  const [error, setError] = useState<Error | null>(null)

  // Track the "applied" version (what's on the server after last apply)
  const appliedDataRef = useRef<T | undefined>(initialData)

  // Track if we've received initial data
  const hasInitializedRef = useRef(false)

  // Update draft and applied ref when initial data changes
  useEffect(() => {
    if (initialData !== undefined) {
      // Only update if this is the first initialization or if the key changed
      if (!hasInitializedRef.current) {
        setDraftState(initialData)
        appliedDataRef.current = initialData
        hasInitializedRef.current = true
        setStatus('idle')
      }
    }
  }, [initialData])

  // Reset when draft key changes (e.g., different budget version)
  useEffect(() => {
    hasInitializedRef.current = false
    setDraftState(initialData)
    appliedDataRef.current = initialData
    setStatus('idle')
    setLastAppliedAt(null)
    setError(null)
  }, [draftKey, initialData])

  // Debounced save function
  const debouncedSave = useDebouncedCallback(async (data: T) => {
    try {
      setStatus('saving')
      await saveDraftFn(data)
      setStatus('saved')
      setError(null)
    } catch (err) {
      setStatus('error')
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      onError?.(error)
    }
  }, debounceMs)

  // Update draft (triggers debounced save)
  const setDraft = useCallback(
    (update: T | ((prev: T) => T)) => {
      setDraftState((prev) => {
        const newValue = typeof update === 'function' ? (update as (prev: T) => T)(prev!) : update
        // Trigger debounced save
        debouncedSave(newValue)
        return newValue
      })
    },
    [debouncedSave]
  )

  // Update a single field
  const updateDraftField = useCallback(
    <K extends keyof T>(field: K, value: T[K]) => {
      setDraft((prev) => ({ ...prev, [field]: value }))
    },
    [setDraft]
  )

  // Check if there are unapplied changes
  const hasUnappliedChanges =
    draft !== undefined &&
    appliedDataRef.current !== undefined &&
    !compareFn(draft, appliedDataRef.current)

  // Apply the draft
  const apply = useCallback(async () => {
    if (!draft) return

    try {
      setStatus('applying')
      setError(null)
      const result = await applyFn(draft)

      // Update the applied reference
      appliedDataRef.current = result
      setDraftState(result)
      setLastAppliedAt(new Date())
      setStatus('applied')

      onApplySuccess?.(result)
    } catch (err) {
      setStatus('error')
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      onError?.(error)
      throw error
    }
  }, [draft, applyFn, onApplySuccess, onError])

  // Discard changes
  const discard = useCallback(() => {
    setDraftState(appliedDataRef.current)
    setStatus('idle')
    setError(null)
  }, [])

  // Force save immediately (bypass debounce)
  const forceSave = useCallback(async () => {
    if (!draft) return

    try {
      setStatus('saving')
      await saveDraftFn(draft)
      setStatus('saved')
      setError(null)
    } catch (err) {
      setStatus('error')
      const error = err instanceof Error ? err : new Error(String(err))
      setError(error)
      onError?.(error)
      throw error
    }
  }, [draft, saveDraftFn, onError])

  return {
    draft,
    setDraft,
    updateDraftField,
    hasUnappliedChanges,
    isSaving: status === 'saving',
    isApplying: status === 'applying',
    status,
    lastAppliedAt,
    apply,
    discard,
    forceSave,
    isReady: draft !== undefined,
    error,
  }
}

/**
 * Hook for blocking navigation when there are unsaved changes.
 * Works with both browser navigation and React Router.
 *
 * @example
 * ```tsx
 * const { hasUnappliedChanges } = useDraft({ ... })
 * useNavigationBlock(hasUnappliedChanges, "You have unapplied changes. Discard them?")
 * ```
 */
export function useNavigationBlock(shouldBlock: boolean, message?: string) {
  const defaultMessage =
    'Vous avez des modifications non appliquées. Voulez-vous vraiment quitter cette page?'

  useEffect(() => {
    if (!shouldBlock) return

    const handleBeforeUnload = (e: BeforeUnloadEvent) => {
      e.preventDefault()
      e.returnValue = message ?? defaultMessage
      return message ?? defaultMessage
    }

    window.addEventListener('beforeunload', handleBeforeUnload)

    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload)
    }
  }, [shouldBlock, message])
}
