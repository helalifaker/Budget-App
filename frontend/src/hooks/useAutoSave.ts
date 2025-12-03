import { useEffect, useRef, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

interface UseAutoSaveOptions<T> {
  data: T
  onSave: (data: T) => Promise<void>
  delay?: number
  enabled?: boolean
}

export function useAutoSave<T>({
  data,
  onSave,
  delay = 1000,
  enabled = true,
}: UseAutoSaveOptions<T>) {
  const [isSaving, setIsSaving] = useState(false)
  const [lastSaved, setLastSaved] = useState<Date | null>(null)
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const dataRef = useRef<T>(data)

  const saveMutation = useMutation({
    mutationFn: onSave,
    onMutate: () => {
      setIsSaving(true)
    },
    onSuccess: () => {
      setIsSaving(false)
      setLastSaved(new Date())
    },
    onError: (error) => {
      setIsSaving(false)
      console.error('Auto-save failed:', error)
    },
  })

  useEffect(() => {
    if (!enabled) return

    const hasChanged = JSON.stringify(dataRef.current) !== JSON.stringify(data)
    if (!hasChanged) return

    dataRef.current = data

    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }

    timeoutRef.current = setTimeout(() => {
      saveMutation.mutate(data)
    }, delay)

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [data, delay, enabled, saveMutation])

  return {
    isSaving,
    lastSaved,
    error: saveMutation.error,
  }
}
