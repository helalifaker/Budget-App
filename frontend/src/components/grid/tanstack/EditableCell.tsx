/**
 * EditableCell
 *
 * Wrapper component that renders either a display value or an inline editor.
 * Handles edit triggers (click, F2, type-to-edit) and editor selection.
 *
 * This is the core component for inline editing in TanStack Table.
 * It integrates with useTableState for state management.
 *
 * Edit Triggers:
 * - Double-click: Start editing with existing value
 * - F2: Start editing with existing value (when focused)
 * - Type any character: Start editing with that character (type-to-edit)
 * - Enter: Start editing (when focused)
 *
 * @example
 * ```tsx
 * <EditableCell
 *   rowId={row.id}
 *   columnId="name"
 *   value={row.original.name}
 *   editorType="text"
 *   isEditing={editingCell?.rowId === row.id && editingCell?.columnId === 'name'}
 *   isFocused={focusedCell?.rowId === row.id && focusedCell?.columnId === 'name'}
 *   onStartEdit={(initialKey) => startEditing({ rowId: row.id, columnId: 'name' }, initialKey)}
 *   onCommit={(value) => updateCell(row.id, 'name', value)}
 *   onCancel={stopEditing}
 * />
 * ```
 */

import { useCallback, useRef, memo } from 'react'
import { cn } from '@/lib/utils'
import { TextEditor } from './editors/TextEditor'
import { NumberEditor } from './editors/NumberEditor'
import { CheckboxEditor } from './editors/CheckboxEditor'
import { LargeTextEditor } from './editors/LargeTextEditor'
import type { EditorType } from './editors'

// ============================================================================
// Types
// ============================================================================

export interface EditableCellProps<T = unknown> {
  /** Row ID for this cell */
  rowId: string
  /** Column ID for this cell */
  columnId: string
  /** Current cell value */
  value: T
  /** Type of editor to use */
  editorType: EditorType
  /** Whether this cell is currently being edited */
  isEditing: boolean
  /** Whether this cell is currently focused */
  isFocused: boolean
  /** Callback to start editing */
  onStartEdit: (initialKey?: string) => void
  /** Callback when editing completes with new value */
  onCommit: (value: T) => void
  /** Callback to cancel editing */
  onCancel: () => void
  /** Navigate to adjacent cell */
  onNavigate?: (direction: 'next' | 'prev') => void
  /** Navigate to cell in adjacent row */
  onNavigateRow?: (direction: 'up' | 'down') => void
  /** Custom display renderer (when not editing) */
  displayRenderer?: (value: T) => React.ReactNode
  /** Whether the cell is editable */
  editable?: boolean
  /** Additional class names */
  className?: string
  /** Initial key that triggered editing */
  initialKey?: string | null

  // Editor-specific props
  /** NumberEditor: minimum value */
  min?: number
  /** NumberEditor: maximum value */
  max?: number
  /** NumberEditor: step increment */
  step?: number
  /** NumberEditor: decimal precision */
  precision?: number
  /** TextEditor: placeholder */
  placeholder?: string
  /** TextEditor: max length */
  maxLength?: number
  /** LargeTextEditor: number of rows */
  rows?: number
  /** LargeTextEditor: enable JSON validation */
  validateJson?: boolean
}

// ============================================================================
// Component
// ============================================================================

function EditableCellInner<T>({
  rowId,
  columnId,
  value,
  editorType,
  isEditing,
  isFocused,
  onStartEdit,
  onCommit,
  onCancel,
  onNavigate,
  onNavigateRow,
  displayRenderer,
  editable = true,
  className,
  initialKey,
  // Editor props
  min,
  max,
  step,
  precision,
  placeholder,
  maxLength,
  rows,
  validateJson,
}: EditableCellProps<T>) {
  const cellRef = useRef<HTMLDivElement>(null)

  // ========== Event Handlers ==========

  // Handle double-click to edit
  const handleDoubleClick = useCallback(() => {
    if (editable && !isEditing) {
      onStartEdit()
    }
  }, [editable, isEditing, onStartEdit])

  // Handle keyboard events when focused (not editing)
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (isEditing || !editable) return

      // F2 to start editing
      if (e.key === 'F2') {
        e.preventDefault()
        onStartEdit()
        return
      }

      // Enter to start editing
      if (e.key === 'Enter' && !e.ctrlKey && !e.metaKey) {
        e.preventDefault()
        onStartEdit()
        return
      }

      // Type-to-edit: printable characters start editing with that character
      if (e.key.length === 1 && !e.ctrlKey && !e.metaKey && !e.altKey) {
        // Check if it's a printable character
        if (/^[\w\d\s\-_.,!@#$%^&*()+=]$/.test(e.key)) {
          e.preventDefault()
          onStartEdit(e.key)
          return
        }
      }

      // Backspace/Delete to clear and edit
      if (e.key === 'Backspace' || e.key === 'Delete') {
        e.preventDefault()
        onStartEdit('')
        return
      }
    },
    [isEditing, editable, onStartEdit]
  )

  // ========== Render Editor ==========

  const renderEditor = () => {
    switch (editorType) {
      case 'text':
        return (
          <TextEditor
            value={value as string | null | undefined}
            onCommit={onCommit as (v: string) => void}
            onCancel={onCancel}
            onNavigate={onNavigate}
            onNavigateRow={onNavigateRow}
            initialKey={initialKey}
            placeholder={placeholder}
            maxLength={maxLength}
          />
        )

      case 'number':
        return (
          <NumberEditor
            value={value as number | null | undefined}
            onCommit={onCommit as (v: number | null) => void}
            onCancel={onCancel}
            onNavigate={onNavigate}
            onNavigateRow={onNavigateRow}
            initialKey={initialKey}
            min={min}
            max={max}
            step={step}
            precision={precision}
            placeholder={placeholder}
          />
        )

      case 'checkbox':
        return (
          <CheckboxEditor
            value={value as boolean | null | undefined}
            onCommit={onCommit as (v: boolean) => void}
            onCancel={onCancel}
            onNavigate={onNavigate}
            onNavigateRow={onNavigateRow}
          />
        )

      case 'largeText':
        return (
          <LargeTextEditor
            value={value as string | null | undefined}
            onCommit={onCommit as (v: string) => void}
            onCancel={onCancel}
            onNavigate={onNavigate}
            onNavigateRow={onNavigateRow}
            initialKey={initialKey}
            placeholder={placeholder}
            maxLength={maxLength}
            rows={rows}
            validateJson={validateJson}
          />
        )

      default:
        // Fall back to text editor
        return (
          <TextEditor
            value={String(value ?? '')}
            onCommit={(v) => onCommit(v as T)}
            onCancel={onCancel}
            onNavigate={onNavigate}
            onNavigateRow={onNavigateRow}
            initialKey={initialKey}
          />
        )
    }
  }

  // ========== Render Display Value ==========

  const renderDisplay = () => {
    if (displayRenderer) {
      return displayRenderer(value)
    }

    // Default display based on type
    if (value === null || value === undefined) {
      return <span className="text-muted-foreground">—</span>
    }

    if (typeof value === 'boolean') {
      return value ? '✓' : '✗'
    }

    if (typeof value === 'number') {
      return <span className="tabular-nums">{value}</span>
    }

    return String(value)
  }

  // ========== Main Render ==========

  return (
    <div
      ref={cellRef}
      data-row-id={rowId}
      data-column-id={columnId}
      data-editable={editable}
      tabIndex={isFocused ? 0 : -1}
      onDoubleClick={handleDoubleClick}
      onKeyDown={handleKeyDown}
      className={cn(
        'relative w-full h-full',
        'flex items-center',
        // Focused state (when not editing)
        isFocused &&
          !isEditing && ['outline-none', 'ring-2 ring-inset ring-gold-500/50', 'bg-gold-50/30'],
        // Non-editable cells have different cursor
        !editable && 'cursor-default',
        className
      )}
    >
      {isEditing ? (
        <div className="absolute inset-0 z-10">{renderEditor()}</div>
      ) : (
        <div className="w-full truncate">{renderDisplay()}</div>
      )}
    </div>
  )
}

// Memoize for performance
export const EditableCell = memo(EditableCellInner) as typeof EditableCellInner
