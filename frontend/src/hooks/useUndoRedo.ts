import { useState, useCallback } from 'react'

interface UseUndoRedoOptions<T> {
  initialState: T
  maxHistorySize?: number
}

export function useUndoRedo<T>({ initialState, maxHistorySize = 10 }: UseUndoRedoOptions<T>) {
  const [history, setHistory] = useState<T[]>([initialState])
  const [currentIndex, setCurrentIndex] = useState(0)

  const currentState = history[currentIndex]

  const canUndo = currentIndex > 0
  const canRedo = currentIndex < history.length - 1

  const setState = useCallback(
    (newState: T | ((prev: T) => T)) => {
      const resolvedState =
        typeof newState === 'function' ? (newState as (prev: T) => T)(currentState) : newState

      const isSame = JSON.stringify(resolvedState) === JSON.stringify(currentState)
      if (isSame) return

      const newHistory = [...history.slice(0, currentIndex + 1), resolvedState]

      const trimmedHistory =
        newHistory.length > maxHistorySize
          ? newHistory.slice(newHistory.length - maxHistorySize)
          : newHistory

      setHistory(trimmedHistory)
      setCurrentIndex(trimmedHistory.length - 1)
    },
    [currentState, currentIndex, history, maxHistorySize]
  )

  const undo = useCallback(() => {
    if (canUndo) {
      setCurrentIndex(currentIndex - 1)
    }
  }, [canUndo, currentIndex])

  const redo = useCallback(() => {
    if (canRedo) {
      setCurrentIndex(currentIndex + 1)
    }
  }, [canRedo, currentIndex])

  const reset = useCallback(() => {
    setHistory([initialState])
    setCurrentIndex(0)
  }, [initialState])

  const getChangeLog = useCallback(() => {
    return history.map((state, index) => ({
      index,
      state,
      isCurrent: index === currentIndex,
    }))
  }, [history, currentIndex])

  return {
    state: currentState,
    setState,
    undo,
    redo,
    canUndo,
    canRedo,
    reset,
    getChangeLog,
  }
}
