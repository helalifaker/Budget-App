/**
 * NumberEditor
 *
 * Inline number editor for TanStack Table cells.
 * Handles numeric input with validation, min/max, step, and precision.
 *
 * Features:
 * - Auto-focus on mount
 * - Enter to confirm, Escape to cancel
 * - Tab/Shift+Tab for cell navigation
 * - Initial key support (type-to-edit)
 * - Min/max validation
 * - Step increment with Arrow keys
 * - Configurable decimal precision
 */

import { useRef, useEffect, useCallback, useState } from 'react'
import { cn } from '@/lib/utils'

export interface NumberEditorProps {
  /** Current cell value */
  value: number | null | undefined
  /** Callback when value changes and editing should stop */
  onCommit: (value: number | null) => void
  /** Callback to cancel editing */
  onCancel: () => void
  /** Navigate to next/previous cell on Tab */
  onNavigate?: (direction: 'next' | 'prev') => void
  /** Navigate up/down on Enter/Shift+Enter */
  onNavigateRow?: (direction: 'up' | 'down') => void
  /** Initial key that triggered editing (for type-to-edit) */
  initialKey?: string | null
  /** Additional class names */
  className?: string
  /** Minimum value */
  min?: number
  /** Maximum value */
  max?: number
  /** Step increment for Arrow key changes */
  step?: number
  /** Number of decimal places */
  precision?: number
  /** Placeholder text */
  placeholder?: string
  /** Allow null/empty values */
  allowNull?: boolean
}

export function NumberEditor({
  value,
  onCommit,
  onCancel,
  onNavigate,
  onNavigateRow,
  initialKey,
  className,
  min,
  max,
  step = 1,
  precision = 2,
  placeholder,
  allowNull = false,
}: NumberEditorProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  // Local string state for editing
  const [localValue, setLocalValue] = useState<string>(() => {
    // If type-to-edit with a digit or minus sign
    if (initialKey && /^[-\d.]$/.test(initialKey)) {
      return initialKey
    }
    // Format existing value
    if (value === null || value === undefined) {
      return ''
    }
    return value.toFixed(precision)
  })

  // Validation error state
  const [hasError, setHasError] = useState(false)

  // Auto-focus and select on mount
  useEffect(() => {
    const input = inputRef.current
    if (!input) return

    input.focus()

    // If type-to-edit with a digit, place cursor at end
    if (initialKey && /^[-\d.]$/.test(initialKey)) {
      input.setSelectionRange(input.value.length, input.value.length)
    } else {
      // Select all for editing existing value
      input.select()
    }
  }, [initialKey])

  // Parse and validate the current value
  const parseValue = useCallback(
    (str: string): number | null => {
      const trimmed = str.trim()
      if (trimmed === '') {
        return allowNull ? null : (min ?? 0)
      }

      const num = parseFloat(trimmed)
      if (isNaN(num)) {
        return null
      }

      // Apply min/max constraints
      let constrained = num
      if (min !== undefined) constrained = Math.max(min, constrained)
      if (max !== undefined) constrained = Math.min(max, constrained)

      // Round to precision
      const factor = Math.pow(10, precision)
      return Math.round(constrained * factor) / factor
    },
    [min, max, precision, allowNull]
  )

  // Validate on change
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value
      setLocalValue(newValue)

      // Quick validation
      const trimmed = newValue.trim()
      if (trimmed === '' && !allowNull) {
        setHasError(true)
      } else if (trimmed !== '' && isNaN(parseFloat(trimmed))) {
        setHasError(true)
      } else {
        setHasError(false)
      }
    },
    [allowNull]
  )

  // Handle commit
  const handleCommit = useCallback(() => {
    const parsed = parseValue(localValue)
    if (parsed === null && !allowNull) {
      // Invalid - cancel instead
      onCancel()
      return
    }
    onCommit(parsed)
  }, [localValue, parseValue, onCommit, onCancel, allowNull])

  // Handle keyboard events
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      switch (e.key) {
        case 'Enter':
          e.preventDefault()
          handleCommit()
          if (e.shiftKey) {
            onNavigateRow?.('up')
          } else {
            onNavigateRow?.('down')
          }
          break

        case 'Escape':
          e.preventDefault()
          onCancel()
          break

        case 'Tab':
          e.preventDefault()
          handleCommit()
          onNavigate?.(e.shiftKey ? 'prev' : 'next')
          break

        case 'ArrowUp':
          if (e.altKey || e.metaKey) {
            e.preventDefault()
            // Increment by step
            const currentValue = parseValue(localValue) ?? min ?? 0
            const newValue = currentValue + step
            const constrained = max !== undefined ? Math.min(max, newValue) : newValue
            setLocalValue(constrained.toFixed(precision))
            setHasError(false)
          }
          break

        case 'ArrowDown':
          if (e.altKey || e.metaKey) {
            e.preventDefault()
            // Decrement by step
            const currentValue = parseValue(localValue) ?? min ?? 0
            const newValue = currentValue - step
            const constrained = min !== undefined ? Math.max(min, newValue) : newValue
            setLocalValue(constrained.toFixed(precision))
            setHasError(false)
          }
          break
      }
    },
    [
      handleCommit,
      onCancel,
      onNavigate,
      onNavigateRow,
      parseValue,
      localValue,
      step,
      min,
      max,
      precision,
    ]
  )

  // Handle blur - commit on blur
  const handleBlur = useCallback(() => {
    handleCommit()
  }, [handleCommit])

  return (
    <input
      ref={inputRef}
      type="text"
      inputMode="decimal"
      value={localValue}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      onBlur={handleBlur}
      placeholder={placeholder}
      className={cn(
        // Base styles
        'w-full h-full px-2 py-1',
        'text-sm font-normal tabular-nums text-right',
        'bg-white',
        'border-0 outline-none',
        // Focus ring using EFIR design system
        hasError
          ? 'ring-2 ring-terracotta-500 ring-offset-1'
          : 'ring-2 ring-gold-500 ring-offset-1 focus:ring-gold-600',
        // Shadow for depth
        'shadow-sm',
        className
      )}
    />
  )
}
