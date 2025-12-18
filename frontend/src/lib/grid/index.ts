/**
 * Grid Abstraction Layer
 *
 * This module provides a grid-agnostic interface for building Excel-like
 * features (keyboard navigation, clipboard, selection) using TanStack Table.
 *
 * Migrated from AG Grid to TanStack Table (December 2024)
 */

// Types and interfaces
export type {
  GridAdapter,
  CellId,
  RowNode,
  ColumnAdapter,
  FocusedCell,
  EditingCellInfo,
  SelectionChangeCallback,
  FocusChangeCallback,
  CellValueChangeCallback,
  Unsubscribe,
  GridAdapterOptions,
  NavigationDirection,
} from './GridAdapter'

// TanStack implementation
export {
  TanStackAdapter,
  createTanStackAdapter,
  type TanStackTableState,
  type TanStackTableActions,
  type TanStackAdapterOptions,
} from './TanStackAdapter'

// Column definition converter utilities
export {
  convertColumn,
  convertColumns,
  getPinnedColumns,
  isColumnEditable,
  getCellClassName,
  getCellStyle,
  type AGGridColDef,
  type AGGridCellRendererParams,
  type AGGridValueFormatterParams,
  type AGGridValueGetterParams,
  type ConvertColumnsOptions,
  type TanStackColumnMeta,
} from './columnConverter'
