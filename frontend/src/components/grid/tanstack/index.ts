/**
 * TanStack Table Components
 *
 * Premium table components built on TanStack Table with EFIR design system.
 *
 * Components:
 * - TanStackDataTable: Drop-in replacement for AG Grid DataTable (recommended)
 * - BaseTable: Read-only table (small datasets < 100 rows)
 * - VirtualizedTable: Virtualized table (large datasets 100+ rows)
 * - EditableCell: Inline editing wrapper with edit triggers
 *
 * Cell Editors:
 * - TextEditor: Text input editor
 * - NumberEditor: Numeric input with validation
 * - CheckboxEditor: Boolean toggle
 *
 * Future additions (Phase 5+):
 * - ExcelTable: Full Excel-like features (keyboard nav, clipboard)
 *
 * @example
 * ```tsx
 * import { TanStackDataTable } from '@/components/grid/tanstack'
 *
 * // Automatic virtualization based on data size
 * <TanStackDataTable
 *   rowData={data}
 *   columnDefs={columns}
 *   getRowId={(row) => row.id}
 *   loading={isLoading}
 * />
 * ```
 *
 * @example
 * ```tsx
 * import { BaseTable, VirtualizedTable } from '@/components/grid/tanstack'
 *
 * // Small dataset
 * <BaseTable data={items} columns={columns} getRowId={(row) => row.id} />
 *
 * // Large dataset with virtualization
 * <VirtualizedTable
 *   data={largeItems}
 *   columns={columns}
 *   getRowId={(row) => row.id}
 *   height={600}
 * />
 * ```
 */

// Main component (recommended for migration)
export {
  TanStackDataTable,
  type TanStackDataTableProps,
  type CellRendererProps,
} from './TanStackDataTable'

// Lower-level components
export { BaseTable, type BaseTableProps } from './BaseTable'
export { VirtualizedTable, type VirtualizedTableProps } from './VirtualizedTable'

// Hooks
export { useTableState } from './hooks'
export type {
  TableState,
  TableStateActions,
  UseTableStateOptions,
  UseTableStateReturn,
} from './hooks'

// Editing components (Phase 3-4)
export { EditableCell, type EditableCellProps } from './EditableCell'
export {
  EditableTable,
  type EditableTableProps,
  type EditableTableApi,
  type CellValueChangedEvent,
  type EditableColumnMeta,
} from './EditableTable'

// Excel-like table (prefer lazy-loaded wrapper for bundle size)
export { ExcelEditableTableLazy, type ExcelEditableTableProps } from './ExcelEditableTableLazy'

// Cell editors
export {
  TextEditor,
  NumberEditor,
  CheckboxEditor,
  LargeTextEditor,
  type TextEditorProps,
  type NumberEditorProps,
  type CheckboxEditorProps,
  type LargeTextEditorProps,
  type EditorType,
} from './editors'

// Import styles (can be imported separately if needed)
import './styles/table.css'
