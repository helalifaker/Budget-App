import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Debounce a value - returns the value after it stops changing for the specified delay.
 *
 * @param value - The value to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns The debounced value
 *
 * @example
 * ```tsx
 * const [searchTerm, setSearchTerm] = useState('')
 * const debouncedSearch = useDebounce(searchTerm, 500)
 *
 * useEffect(() => {
 *   // This only fires 500ms after user stops typing
 *   searchApi(debouncedSearch)
 * }, [debouncedSearch])
 * ```
 */
export function useDebounce<T>(value: T, delay = 300): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value)
    }, delay)

    return () => {
      clearTimeout(timer)
    }
  }, [value, delay])

  return debouncedValue
}

/**
 * Debounce a callback function - the callback is only executed after it stops
 * being called for the specified delay.
 *
 * @param callback - The function to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns A debounced version of the callback
 *
 * @example
 * ```tsx
 * const debouncedSave = useDebouncedCallback((value: string) => {
 *   api.save(value)
 * }, 500)
 *
 * // This only calls api.save 500ms after last change
 * <input onChange={(e) => debouncedSave(e.target.value)} />
 * ```
 */
export function useDebouncedCallback<Args extends unknown[], R>(
  callback: (...args: Args) => R,
  delay = 300
): (...args: Args) => void {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const callbackRef = useRef(callback)

  // Update the callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const debouncedCallback = useCallback(
    (...args: Args) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args)
      }, delay)
    },
    [delay]
  )

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return debouncedCallback
}

/**
 * Debounce a callback function with the ability to cancel or flush immediately.
 * Useful when you need more control over the debounced behavior.
 *
 * @param callback - The function to debounce
 * @param delay - Delay in milliseconds (default: 300ms)
 * @returns Object with debounced callback, cancel, and flush functions
 *
 * @example
 * ```tsx
 * const { debouncedCallback, cancel, flush } = useDebouncedCallbackWithControls(
 *   (value: string) => api.save(value),
 *   500
 * )
 *
 * // Cancel pending save (e.g., on navigation)
 * useEffect(() => () => cancel(), [])
 *
 * // Force immediate save (e.g., on form submit)
 * const handleSubmit = () => {
 *   flush()
 *   // ...
 * }
 * ```
 */
export function useDebouncedCallbackWithControls<Args extends unknown[], R>(
  callback: (...args: Args) => R,
  delay = 300
): {
  debouncedCallback: (...args: Args) => void
  cancel: () => void
  flush: () => void
  isPending: boolean
} {
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const callbackRef = useRef(callback)
  const argsRef = useRef<Args | null>(null)
  const [isPending, setIsPending] = useState(false)

  // Update the callback ref when callback changes
  useEffect(() => {
    callbackRef.current = callback
  }, [callback])

  const cancel = useCallback(() => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
    }
    argsRef.current = null
    setIsPending(false)
  }, [])

  const flush = useCallback(() => {
    if (timeoutRef.current && argsRef.current) {
      clearTimeout(timeoutRef.current)
      timeoutRef.current = null
      callbackRef.current(...argsRef.current)
      argsRef.current = null
      setIsPending(false)
    }
  }, [])

  const debouncedCallback = useCallback(
    (...args: Args) => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }

      argsRef.current = args
      setIsPending(true)

      timeoutRef.current = setTimeout(() => {
        callbackRef.current(...args)
        argsRef.current = null
        timeoutRef.current = null
        setIsPending(false)
      }, delay)
    },
    [delay]
  )

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  return { debouncedCallback, cancel, flush, isPending }
}
