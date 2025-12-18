/**
 * Cell Editors
 *
 * Inline cell editors for TanStack Table.
 * Each editor handles a specific data type with full keyboard support.
 *
 * Common keyboard shortcuts across all editors:
 * - Enter: Commit value and navigate down
 * - Shift+Enter: Commit value and navigate up
 * - Tab: Commit value and navigate to next cell
 * - Shift+Tab: Commit value and navigate to previous cell
 * - Escape: Cancel editing, restore original value
 *
 * @example
 * ```tsx
 * import { TextEditor, NumberEditor, CheckboxEditor } from './editors'
 *
 * // Usage in EditableCell
 * switch (editorType) {
 *   case 'text':
 *     return <TextEditor value={value} onCommit={onCommit} onCancel={onCancel} />
 *   case 'number':
 *     return <NumberEditor value={value} onCommit={onCommit} onCancel={onCancel} min={0} max={100} />
 *   case 'checkbox':
 *     return <CheckboxEditor value={value} onCommit={onCommit} onCancel={onCancel} />
 * }
 * ```
 */

export { TextEditor, type TextEditorProps } from './TextEditor'
export { NumberEditor, type NumberEditorProps } from './NumberEditor'
export { CheckboxEditor, type CheckboxEditorProps } from './CheckboxEditor'
export { LargeTextEditor, type LargeTextEditorProps } from './LargeTextEditor'

/**
 * Editor type for column configuration
 */
export type EditorType = 'text' | 'number' | 'checkbox' | 'select' | 'date' | 'largeText'

/**
 * Common editor props shared by all editors
 */
export interface BaseEditorProps<T> {
  /** Current cell value */
  value: T
  /** Callback when value changes and editing should stop */
  onCommit: (value: T) => void
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
}
