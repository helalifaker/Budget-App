/**
 * CheckboxEditor
 *
 * Inline checkbox editor for TanStack Table cells.
 * Toggles boolean values with keyboard support.
 *
 * Features:
 * - Space to toggle
 * - Enter to confirm (and optionally navigate)
 * - Escape to cancel
 * - Tab/Shift+Tab for cell navigation
 */

import { useRef, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'
import { Checkbox } from '@/components/ui/checkbox'

export interface CheckboxEditorProps {
  /** Current cell value */
  value: boolean | null | undefined
  /** Callback when value changes and editing should stop */
  onCommit: (value: boolean) => void
  /** Callback to cancel editing */
  onCancel: () => void
  /** Navigate to next/previous cell on Tab */
  onNavigate?: (direction: 'next' | 'prev') => void
  /** Navigate up/down on Enter/Shift+Enter */
  onNavigateRow?: (direction: 'up' | 'down') => void
  /** Additional class names */
  className?: string
  /** Label for accessibility */
  ariaLabel?: string
}

export function CheckboxEditor({
  value,
  onCommit,
  onCancel,
  onNavigate,
  onNavigateRow,
  className,
  ariaLabel = 'Toggle value',
}: CheckboxEditorProps) {
  const containerRef = useRef<HTMLDivElement>(null)

  // Current checked state
  const isChecked = value ?? false

  // Focus container on mount for keyboard handling
  useEffect(() => {
    containerRef.current?.focus()
  }, [])

  // Handle toggle
  const handleToggle = useCallback(() => {
    onCommit(!isChecked)
  }, [isChecked, onCommit])

  // Handle checkbox change
  const handleCheckedChange = useCallback(
    (checked: boolean | 'indeterminate') => {
      if (checked === 'indeterminate') return
      onCommit(checked)
    },
    [onCommit]
  )

  // Handle keyboard events on container
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>) => {
      switch (e.key) {
        case ' ':
        case 'Space':
          e.preventDefault()
          handleToggle()
          break

        case 'Enter':
          e.preventDefault()
          // Commit current value and navigate
          onCommit(isChecked)
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
          onCommit(isChecked)
          onNavigate?.(e.shiftKey ? 'prev' : 'next')
          break
      }
    },
    [handleToggle, isChecked, onCommit, onCancel, onNavigate, onNavigateRow]
  )

  return (
    <div
      ref={containerRef}
      tabIndex={0}
      onKeyDown={handleKeyDown}
      className={cn(
        // Centering
        'flex items-center justify-center',
        'w-full h-full',
        // Focus styles
        'outline-none',
        'focus:ring-2 focus:ring-gold-500 focus:ring-offset-1',
        className
      )}
      aria-label={ariaLabel}
    >
      <Checkbox
        checked={isChecked}
        onCheckedChange={handleCheckedChange}
        className={cn(
          'h-4 w-4',
          'border-border-medium',
          'data-[state=checked]:bg-gold-500',
          'data-[state=checked]:border-gold-500'
        )}
      />
    </div>
  )
}
