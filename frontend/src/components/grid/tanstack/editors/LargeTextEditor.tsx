/**
 * LargeTextEditor
 *
 * Inline multi-line text editor for TanStack Table cells.
 * Ideal for JSON editing, long text, or any multi-line content.
 *
 * Features:
 * - Multi-line textarea input
 * - JSON syntax validation (optional)
 * - Monospace font for code-like content
 * - Auto-resize based on content
 * - Ctrl+Enter to confirm (Enter creates newlines)
 * - Escape to cancel
 */

import { useRef, useEffect, useCallback, useState } from 'react'
import { cn } from '@/lib/utils'

export interface LargeTextEditorProps {
  /** Current cell value */
  value: string | null | undefined
  /** Callback when value changes and editing should stop */
  onCommit: (value: string) => void
  /** Callback to cancel editing */
  onCancel: () => void
  /** Navigate to next/previous cell on Tab */
  onNavigate?: (direction: 'next' | 'prev') => void
  /** Navigate up/down on Ctrl+Enter/Ctrl+Shift+Enter */
  onNavigateRow?: (direction: 'up' | 'down') => void
  /** Initial key that triggered editing (for type-to-edit) */
  initialKey?: string | null
  /** Additional class names */
  className?: string
  /** Placeholder text */
  placeholder?: string
  /** Maximum length */
  maxLength?: number
  /** Number of rows to display */
  rows?: number
  /** Enable JSON validation */
  validateJson?: boolean
  /** Whether the field is required */
  required?: boolean
}

export function LargeTextEditor({
  value,
  onCommit,
  onCancel,
  onNavigate,
  onNavigateRow,
  initialKey,
  className,
  placeholder = 'Enter text...',
  maxLength = 5000,
  rows = 6,
  validateJson = false,
  required,
}: LargeTextEditorProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null)

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

  // Validation error state
  const [jsonError, setJsonError] = useState<string | null>(null)

  // Auto-focus and select on mount
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return

    textarea.focus()

    // If type-to-edit with a character or empty string (delete), place cursor at end
    if (initialKey !== undefined && initialKey !== null) {
      textarea.setSelectionRange(textarea.value.length, textarea.value.length)
    } else {
      // Select all for editing existing value
      textarea.select()
    }
  }, [initialKey])

  // Validate JSON when validateJson is enabled
  useEffect(() => {
    if (!validateJson || !localValue.trim()) {
      setJsonError(null)
      return
    }

    try {
      JSON.parse(localValue)
      setJsonError(null)
    } catch (e) {
      setJsonError(e instanceof Error ? e.message : 'Invalid JSON')
    }
  }, [localValue, validateJson])

  // Handle commit
  const handleCommit = useCallback(() => {
    const trimmedValue = localValue.trim()

    if (required && !trimmedValue) {
      onCancel()
      return
    }

    // Block commit if JSON validation fails
    if (validateJson && trimmedValue && jsonError) {
      // Don't commit, keep editing
      return
    }

    onCommit(trimmedValue)
  }, [localValue, onCommit, onCancel, required, validateJson, jsonError])

  // Handle keyboard events
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      switch (e.key) {
        case 'Enter':
          // Ctrl/Cmd + Enter commits
          if (e.ctrlKey || e.metaKey) {
            e.preventDefault()
            handleCommit()
            // Navigate after commit
            if (e.shiftKey) {
              onNavigateRow?.('up')
            } else {
              onNavigateRow?.('down')
            }
          }
          // Plain Enter creates a newline (default behavior)
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
    <div className="relative">
      <textarea
        ref={textareaRef}
        value={localValue}
        onChange={(e) => setLocalValue(e.target.value)}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        placeholder={placeholder}
        maxLength={maxLength}
        rows={rows}
        className={cn(
          // Base styles
          'w-full min-w-[300px] px-3 py-2',
          'text-sm font-mono',
          'bg-white',
          'border-0 outline-none',
          'resize-none',
          // Focus ring using EFIR design system
          'ring-2 ring-gold-500 ring-offset-1',
          'focus:ring-gold-600',
          // Shadow for depth
          'shadow-md',
          // Rounded corners
          'rounded-md',
          // Error state
          jsonError && 'ring-terracotta-500 focus:ring-terracotta-600',
          className
        )}
      />

      {/* JSON validation error */}
      {validateJson && jsonError && (
        <div className="absolute left-0 right-0 -bottom-6 text-xs text-terracotta-600 truncate">
          {jsonError}
        </div>
      )}

      {/* Keyboard hint */}
      <div className="absolute right-2 bottom-2 text-xs text-text-tertiary pointer-events-none">
        Ctrl+Enter to save
      </div>
    </div>
  )
}
