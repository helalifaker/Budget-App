/**
 * TextEditor
 *
 * Inline text editor for TanStack Table cells.
 * Handles single-line text input with keyboard navigation.
 *
 * Features:
 * - Auto-focus on mount
 * - Enter to confirm, Escape to cancel
 * - Tab/Shift+Tab for cell navigation
 * - Initial key support (type-to-edit)
 */

import { useRef, useEffect, useCallback, useState } from 'react'
import { cn } from '@/lib/utils'

export interface TextEditorProps {
  /** Current cell value */
  value: string | null | undefined
  /** Callback when value changes and editing should stop */
  onCommit: (value: string) => void
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
  /** Placeholder text */
  placeholder?: string
  /** Maximum length */
  maxLength?: number
  /** Whether the field is required */
  required?: boolean
}

export function TextEditor({
  value,
  onCommit,
  onCancel,
  onNavigate,
  onNavigateRow,
  initialKey,
  className,
  placeholder,
  maxLength,
  required,
}: TextEditorProps) {
  const inputRef = useRef<HTMLInputElement>(null)

  // Local value state - start with initialKey if provided (type-to-edit)
  const [localValue, setLocalValue] = useState<string>(() => {
    // Empty string initial key means clear (from Delete/Backspace)
    if (initialKey === '') {
      return ''
    }
    if (initialKey && initialKey.length === 1 && /^[\w\s]$/.test(initialKey)) {
      // Single printable character - replace value
      return initialKey
    }
    // No initial key or special key - use existing value
    return value ?? ''
  })

  // Auto-focus and select on mount
  useEffect(() => {
    const input = inputRef.current
    if (!input) return

    input.focus()

    // If type-to-edit with a character or empty string (delete), place cursor at end
    if (initialKey !== undefined && initialKey !== null) {
      input.setSelectionRange(input.value.length, input.value.length)
    } else {
      // Select all for editing existing value
      input.select()
    }
  }, [initialKey])

  // Handle commit
  const handleCommit = useCallback(() => {
    const trimmedValue = localValue.trim()
    if (required && !trimmedValue) {
      // Don't commit empty required field - could show validation error
      onCancel()
      return
    }
    onCommit(trimmedValue)
  }, [localValue, onCommit, onCancel, required])

  // Handle keyboard events
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      switch (e.key) {
        case 'Enter':
          e.preventDefault()
          handleCommit()
          // Navigate down after commit
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
      }
    },
    [handleCommit, onCancel, onNavigate, onNavigateRow]
  )

  // Handle blur - commit on blur
  const handleBlur = useCallback(() => {
    handleCommit()
  }, [handleCommit])

  return (
    <input
      ref={inputRef}
      type="text"
      value={localValue}
      onChange={(e) => setLocalValue(e.target.value)}
      onKeyDown={handleKeyDown}
      onBlur={handleBlur}
      placeholder={placeholder}
      maxLength={maxLength}
      className={cn(
        // Base styles
        'w-full h-full px-2 py-1',
        'text-sm font-normal',
        'bg-white',
        'border-0 outline-none',
        // Focus ring using EFIR design system
        'ring-2 ring-gold-500 ring-offset-1',
        'focus:ring-gold-600',
        // Shadow for depth
        'shadow-sm',
        className
      )}
    />
  )
}
