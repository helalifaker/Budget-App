/**
 * Grid Components - TanStack Table
 *
 * This module provides premium TanStack Table components with Excel-like functionality:
 * - TanStackDataTable: Main data grid (auto-virtualizes for large datasets)
 * - EditableTable: Inline editing support
 * - ExcelEditableTable: Full Excel-like keyboard navigation and clipboard support
 *
 * All components use the EFIR design system for consistent styling.
 */

// Re-export all TanStack components from the tanstack subfolder
export {
  // Main tables
  TanStackDataTable,
  BaseTable,
  VirtualizedTable,
  EditableTable,
  ExcelEditableTableLazy,

  // Types
  type TanStackDataTableProps,
  type BaseTableProps,
  type VirtualizedTableProps,
  type EditableTableProps,
  type ExcelEditableTableProps,
  type CellRendererProps,
  type EditableTableApi,
  type CellValueChangedEvent,
  type EditableColumnMeta,

  // Hooks
  useTableState,
  type TableState,
  type TableStateActions,
  type UseTableStateOptions,
  type UseTableStateReturn,

  // Editing components
  EditableCell,
  type EditableCellProps,

  // Cell editors
  TextEditor,
  NumberEditor,
  CheckboxEditor,
  LargeTextEditor,
  type TextEditorProps,
  type NumberEditorProps,
  type CheckboxEditorProps,
  type LargeTextEditorProps,
  type EditorType,
} from './tanstack'
