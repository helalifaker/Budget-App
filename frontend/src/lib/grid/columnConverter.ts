/**
 * Column Definition Converter
 *
 * Converts AG Grid ColDef to TanStack Table ColumnDef.
 * This enables gradual migration by allowing the same column definitions
 * to be used with both grid libraries.
 *
 * @example
 * ```tsx
 * const agGridColumns: ColDef[] = [
 *   { field: 'name', headerName: 'Name', width: 200 },
 *   { field: 'amount', headerName: 'Amount', valueFormatter: currencyFormatter },
 * ]
 *
 * const tanstackColumns = convertColumns(agGridColumns, {
 *   cellRenderers: { currencyRenderer: CurrencyCell },
 * })
 * ```
 */

import type { ColumnDef, CellContext, HeaderContext } from '@tanstack/react-table'

// ============================================================================
// AG Grid Types (subset needed for conversion)
// ============================================================================

/**
 * AG Grid ColDef properties we support converting.
 * This is a subset of the full AG Grid ColDef interface.
 */
export interface AGGridColDef<TData = unknown> {
  /** Field name to access data */
  field?: string
  /** Column header text */
  headerName?: string
  /** Column unique ID (defaults to field) */
  colId?: string
  /** Fixed width in pixels */
  width?: number
  /** Minimum width in pixels */
  minWidth?: number
  /** Maximum width in pixels */
  maxWidth?: number
  /** Flex grow factor */
  flex?: number
  /** Pin column to left or right */
  pinned?: 'left' | 'right' | boolean
  /** Enable sorting */
  sortable?: boolean
  /** Enable filtering */
  filter?: boolean | string
  /** Enable resizing */
  resizable?: boolean
  /** Hide column */
  hide?: boolean
  /** Cell renderer component name or function */
  cellRenderer?: string | ((params: AGGridCellRendererParams<TData>) => React.ReactNode)
  /** Value formatter function */
  valueFormatter?: (params: AGGridValueFormatterParams<TData>) => string
  /** Value getter function */
  valueGetter?: (params: AGGridValueGetterParams<TData>) => unknown
  /** Cell class or class function */
  cellClass?: string | string[] | ((params: AGGridCellClassParams<TData>) => string | string[])
  /** Header class */
  headerClass?: string | string[]
  /** Editable flag or function */
  editable?: boolean | ((params: AGGridEditableParams<TData>) => boolean)
  /** Cell editor component name */
  cellEditor?: string
  /** Cell editor params */
  cellEditorParams?: Record<string, unknown>
  /** Header tooltip */
  headerTooltip?: string
  /** Cell style object or function */
  cellStyle?:
    | React.CSSProperties
    | ((params: AGGridCellStyleParams<TData>) => React.CSSProperties | undefined)
  /** Suppress movable */
  suppressMovable?: boolean
  /** Lock position */
  lockPosition?: boolean | 'left' | 'right'
  /** Type hint for cell formatting */
  type?: string | string[]
  /** Custom comparator for sorting */
  comparator?: (valueA: unknown, valueB: unknown, nodeA: unknown, nodeB: unknown) => number
  /** Children columns for grouping */
  children?: AGGridColDef<TData>[]
  /** Header group component */
  headerGroupComponent?: string
}

/**
 * AG Grid cell renderer params (simplified)
 */
export interface AGGridCellRendererParams<TData = unknown> {
  value: unknown
  data: TData
  node: { data: TData; id: string; rowIndex: number }
  column: { colId: string; colDef: AGGridColDef<TData> }
  rowIndex: number
  colDef: AGGridColDef<TData>
  api: unknown
  context: unknown
}

/**
 * AG Grid value formatter params
 */
export interface AGGridValueFormatterParams<TData = unknown> {
  value: unknown
  data: TData
  node: { data: TData; id: string }
  column: { colId: string }
  colDef: AGGridColDef<TData>
}

/**
 * AG Grid value getter params
 */
export interface AGGridValueGetterParams<TData = unknown> {
  data: TData
  node: { data: TData; id: string }
  column: { colId: string }
  colDef: AGGridColDef<TData>
}

/**
 * AG Grid cell class params
 */
export interface AGGridCellClassParams<TData = unknown> {
  value: unknown
  data: TData
  node: { data: TData; id: string }
  column: { colId: string }
  colDef: AGGridColDef<TData>
  rowIndex: number
}

/**
 * AG Grid editable params
 */
export interface AGGridEditableParams<TData = unknown> {
  data: TData
  node: { data: TData; id: string }
  column: { colId: string }
  colDef: AGGridColDef<TData>
}

/**
 * AG Grid cell style params
 */
export interface AGGridCellStyleParams<TData = unknown> {
  value: unknown
  data: TData
  node: { data: TData; id: string }
  column: { colId: string }
  colDef: AGGridColDef<TData>
}

// ============================================================================
// Converter Options
// ============================================================================

/**
 * Options for column conversion.
 */
export interface ConvertColumnsOptions<TData> {
  /**
   * Map of cell renderer names to React components.
   * Used when AG Grid colDef has cellRenderer as a string.
   */
  cellRenderers?: Record<
    string,
    (props: { value: unknown; data: TData; rowIndex: number }) => React.ReactNode
  >

  /**
   * Map of cell editor names to React components.
   * Used when converting editable columns.
   */
  cellEditors?: Record<string, React.ComponentType<unknown>>

  /**
   * Default column width if not specified.
   */
  defaultWidth?: number

  /**
   * Default minimum width.
   */
  defaultMinWidth?: number

  /**
   * Whether to enable sorting by default.
   */
  defaultSortable?: boolean

  /**
   * Whether to enable filtering by default.
   */
  defaultFilterable?: boolean

  /**
   * Function to get row ID from data.
   * Required for proper cell identification.
   */
  getRowId?: (data: TData) => string
}

// ============================================================================
// TanStack Column Meta Extension
// ============================================================================

/**
 * Extended meta type for TanStack columns.
 * Stores AG Grid-specific settings that don't have direct TanStack equivalents.
 */
export interface TanStackColumnMeta<TData = unknown> {
  /** Column is editable */
  editable?: boolean | ((data: TData) => boolean)
  /** Pin position */
  pinned?: 'left' | 'right'
  /** Original AG Grid colDef for reference */
  agGridColDef?: AGGridColDef<TData>
  /** Cell class or class function */
  cellClass?: string | string[] | ((data: TData, value: unknown) => string | string[])
  /** Cell style function */
  cellStyle?: (data: TData, value: unknown) => React.CSSProperties | undefined
  /** Cell editor component name */
  cellEditor?: string
  /** Cell editor params */
  cellEditorParams?: Record<string, unknown>
  /** Column type hints */
  type?: string | string[]
}

// ============================================================================
// Converter Implementation
// ============================================================================

/**
 * Convert a single AG Grid ColDef to TanStack ColumnDef.
 */
export function convertColumn<TData extends object>(
  agColDef: AGGridColDef<TData>,
  options: ConvertColumnsOptions<TData> = {}
): ColumnDef<TData, unknown> {
  const {
    cellRenderers = {},
    defaultWidth = 150,
    defaultMinWidth = 50,
    defaultSortable = true,
  } = options

  const columnId = agColDef.colId ?? agColDef.field ?? `col_${Math.random().toString(36).slice(2)}`
  const field = agColDef.field

  // Build the TanStack column definition
  const columnDef: ColumnDef<TData, unknown> = {
    id: columnId,

    // Header
    header: ({ column }: HeaderContext<TData, unknown>) => {
      // Return the header name or fall back to field name
      return agColDef.headerName ?? agColDef.field ?? column.id
    },

    // Enable/disable features
    enableSorting: agColDef.sortable ?? defaultSortable,
    enableColumnFilter: agColDef.filter === true || typeof agColDef.filter === 'string',
    enableResizing: agColDef.resizable !== false,
    enableHiding: true,

    // Size configuration
    size: agColDef.width ?? (agColDef.flex ? undefined : defaultWidth),
    minSize: agColDef.minWidth ?? defaultMinWidth,
    maxSize: agColDef.maxWidth,

    // Meta for AG Grid-specific settings
    meta: {
      pinned: typeof agColDef.pinned === 'string' ? agColDef.pinned : undefined,
      editable: agColDef.editable,
      cellEditor: agColDef.cellEditor,
      cellEditorParams: agColDef.cellEditorParams,
      type: agColDef.type,
      agGridColDef: agColDef,
      cellClass:
        typeof agColDef.cellClass === 'function'
          ? (data: TData, value: unknown) => {
              const params = createCellClassParams(data, value, columnId, agColDef)
              return (
                agColDef.cellClass as (params: AGGridCellClassParams<TData>) => string | string[]
              )(params)
            }
          : agColDef.cellClass,
      cellStyle:
        typeof agColDef.cellStyle === 'function'
          ? (data: TData, value: unknown) => {
              const params = createCellStyleParams(data, value, columnId, agColDef)
              return (
                agColDef.cellStyle as (
                  params: AGGridCellStyleParams<TData>
                ) => React.CSSProperties | undefined
              )(params)
            }
          : undefined,
    } as TanStackColumnMeta<TData>,
  }

  // Accessor - how to get the value from data
  if (field) {
    // Use accessorKey for simple field access
    ;(columnDef as ColumnDef<TData, unknown> & { accessorKey: string }).accessorKey = field
  } else if (agColDef.valueGetter) {
    // Use accessorFn for computed values
    ;(columnDef as ColumnDef<TData, unknown> & { accessorFn: (row: TData) => unknown }).accessorFn =
      (row: TData) => {
        const params = createValueGetterParams(row, columnId, agColDef)
        return agColDef.valueGetter!(params)
      }
  }

  // Cell renderer
  columnDef.cell = createCellRenderer(agColDef, cellRenderers, columnId)

  return columnDef
}

/**
 * Convert multiple AG Grid ColDefs to TanStack ColumnDefs.
 */
export function convertColumns<TData extends object>(
  agColDefs: AGGridColDef<TData>[],
  options: ConvertColumnsOptions<TData> = {}
): ColumnDef<TData, unknown>[] {
  return agColDefs
    .filter((colDef) => !colDef.hide) // Filter out hidden columns
    .map((colDef) => convertColumn(colDef, options))
}

// ============================================================================
// Cell Renderer Factory
// ============================================================================

/**
 * Create a TanStack cell renderer from AG Grid configuration.
 */
function createCellRenderer<TData extends object>(
  agColDef: AGGridColDef<TData>,
  cellRenderers: Record<
    string,
    (props: { value: unknown; data: TData; rowIndex: number }) => React.ReactNode
  >,
  columnId: string
): (info: CellContext<TData, unknown>) => React.ReactNode {
  return (info: CellContext<TData, unknown>) => {
    const { getValue, row } = info
    let value = getValue()

    // Apply value formatter if present
    if (agColDef.valueFormatter) {
      const params = createValueFormatterParams(value, row.original, columnId, agColDef)
      value = agColDef.valueFormatter(params)
    }

    // Apply cell renderer if present
    if (agColDef.cellRenderer) {
      if (typeof agColDef.cellRenderer === 'string') {
        // Look up renderer by name
        const Renderer = cellRenderers[agColDef.cellRenderer]
        if (Renderer) {
          return Renderer({ value, data: row.original, rowIndex: row.index })
        }
        // Fall through to default if renderer not found
        console.warn(`Cell renderer "${agColDef.cellRenderer}" not found in cellRenderers map`)
      } else if (typeof agColDef.cellRenderer === 'function') {
        // Call the renderer function directly
        const params = createCellRendererParams(
          value,
          row.original,
          row.id,
          row.index,
          columnId,
          agColDef
        )
        return agColDef.cellRenderer(params)
      }
    }

    // Default: return the value as-is
    // Handle null/undefined gracefully
    if (value === null || value === undefined) {
      return '—'
    }

    // For objects/arrays, stringify for display
    if (typeof value === 'object') {
      return JSON.stringify(value)
    }

    return String(value)
  }
}

// ============================================================================
// Param Factories (create AG Grid-compatible params for callbacks)
// ============================================================================

function createValueFormatterParams<TData>(
  value: unknown,
  data: TData,
  columnId: string,
  colDef: AGGridColDef<TData>
): AGGridValueFormatterParams<TData> {
  return {
    value,
    data,
    node: { data, id: '' },
    column: { colId: columnId },
    colDef,
  }
}

function createValueGetterParams<TData>(
  data: TData,
  columnId: string,
  colDef: AGGridColDef<TData>
): AGGridValueGetterParams<TData> {
  return {
    data,
    node: { data, id: '' },
    column: { colId: columnId },
    colDef,
  }
}

function createCellRendererParams<TData>(
  value: unknown,
  data: TData,
  rowId: string,
  rowIndex: number,
  columnId: string,
  colDef: AGGridColDef<TData>
): AGGridCellRendererParams<TData> {
  return {
    value,
    data,
    node: { data, id: rowId, rowIndex },
    column: { colId: columnId, colDef },
    rowIndex,
    colDef,
    api: null,
    context: null,
  }
}

function createCellClassParams<TData>(
  data: TData,
  value: unknown,
  columnId: string,
  colDef: AGGridColDef<TData>
): AGGridCellClassParams<TData> {
  return {
    value,
    data,
    node: { data, id: '' },
    column: { colId: columnId },
    colDef,
    rowIndex: 0,
  }
}

function createCellStyleParams<TData>(
  data: TData,
  value: unknown,
  columnId: string,
  colDef: AGGridColDef<TData>
): AGGridCellStyleParams<TData> {
  return {
    value,
    data,
    node: { data, id: '' },
    column: { colId: columnId },
    colDef,
  }
}

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get pinned columns from converted column definitions.
 */
export function getPinnedColumns<TData>(columns: ColumnDef<TData, unknown>[]): {
  left: string[]
  right: string[]
} {
  const left: string[] = []
  const right: string[] = []

  columns.forEach((col) => {
    const meta = col.meta as TanStackColumnMeta<TData> | undefined
    if (meta?.pinned === 'left' && col.id) {
      left.push(col.id)
    } else if (meta?.pinned === 'right' && col.id) {
      right.push(col.id)
    }
  })

  return { left, right }
}

/**
 * Get editable status for a column.
 */
export function isColumnEditable<TData>(column: ColumnDef<TData, unknown>, data?: TData): boolean {
  const meta = column.meta as TanStackColumnMeta<TData> | undefined
  if (!meta?.editable) return false

  if (typeof meta.editable === 'function') {
    return data ? meta.editable(data) : false
  }

  return meta.editable
}

/**
 * Get cell class names for a cell.
 */
export function getCellClassName<TData>(
  column: ColumnDef<TData, unknown>,
  data: TData,
  value: unknown
): string {
  const meta = column.meta as TanStackColumnMeta<TData> | undefined
  if (!meta?.cellClass) return ''

  if (typeof meta.cellClass === 'function') {
    const result = meta.cellClass(data, value)
    return Array.isArray(result) ? result.join(' ') : result
  }

  return Array.isArray(meta.cellClass) ? meta.cellClass.join(' ') : meta.cellClass
}

/**
 * Get cell style for a cell.
 */
export function getCellStyle<TData>(
  column: ColumnDef<TData, unknown>,
  data: TData,
  value: unknown
): React.CSSProperties | undefined {
  const meta = column.meta as TanStackColumnMeta<TData> | undefined
  if (!meta?.cellStyle) return undefined

  return meta.cellStyle(data, value)
}
