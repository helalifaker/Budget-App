import { useMemo, useCallback, useRef, useEffect } from 'react'
import {
  ColDef,
  CellValueChangedEvent,
  GridApi,
  ICellRendererParams,
  CellClassParams,
} from 'ag-grid-community'
import { DataTableLazy } from '@/components/DataTableLazy'
import { useCustomClipboard } from '@/hooks/useCustomClipboard'
import { LevelInfo } from '@/types/api'
import { SubjectHoursMatrixRow, validateHoursValue } from './subjectHoursUtils'

// Type re-export only (safe for fast-refresh)
export type { SubjectHoursMatrixRow }

export interface SubjectHoursMatrixProps {
  levels: LevelInfo[]
  isLoading?: boolean
  error?: Error | null
  onDataChange: (rows: SubjectHoursMatrixRow[]) => void
  rowData: SubjectHoursMatrixRow[]
}

// ============================================================================
// Cell Renderers
// ============================================================================

// Checkbox renderer for split class
function SplitCheckboxRenderer(params: ICellRendererParams<SubjectHoursMatrixRow>) {
  const levelId = params.colDef?.field?.replace('split_', '') ?? ''
  const data = params.data

  if (!data || !data.isApplicable) {
    return <span className="text-text-disabled">-</span>
  }

  const isChecked = data.splitFlags[levelId] ?? false

  return (
    <input
      type="checkbox"
      checked={isChecked}
      onChange={(e) => {
        if (params.api && data) {
          const updatedSplitFlags = { ...data.splitFlags, [levelId]: e.target.checked }
          const updatedRow: SubjectHoursMatrixRow = {
            ...data,
            splitFlags: updatedSplitFlags,
            isDirty: true,
          }
          params.api.applyTransaction({ update: [updatedRow] })
          // Trigger parent update through context or event
          const event = new CustomEvent('subjectHoursChange', { detail: { row: updatedRow } })
          window.dispatchEvent(event)
        }
      }}
      className="h-4 w-4 rounded border-border-light text-text-secondary focus:ring-gold/50"
      disabled={!data.isApplicable}
    />
  )
}

// ============================================================================
// Cell Style Helper
// ============================================================================

function getCellStyle(
  params: CellClassParams<SubjectHoursMatrixRow>,
  isHoursColumn: boolean
): Record<string, string> | null {
  const data = params.data
  if (!data) return null

  // Non-applicable subjects: subtle background with muted text
  if (!data.isApplicable) {
    return { backgroundColor: 'var(--color-subtle)', color: 'var(--color-text-disabled)' }
  }

  // For hours columns, check validity
  if (isHoursColumn) {
    const levelId = params.colDef?.field?.replace('hours_', '') ?? ''
    const value = data.hours[levelId]
    if (!validateHoursValue(value)) {
      return { backgroundColor: 'var(--color-terracotta-100)' } // Terracotta for invalid
    }
  }

  // Dirty rows: warning background
  if (data.isDirty) {
    return { backgroundColor: 'var(--color-warning-100)' }
  }

  return null
}

// ============================================================================
// Main Component
// ============================================================================

export function SubjectHoursMatrix({
  levels,
  isLoading = false,
  error = null,
  onDataChange,
  rowData,
}: SubjectHoursMatrixProps) {
  const gridApiRef = useRef<GridApi | null>(null)

  // Handle grid ready
  const onGridReady = useCallback((params: { api: GridApi }) => {
    gridApiRef.current = params.api
  }, [])

  // Listen for custom change events
  useEffect(() => {
    const handleChange = (event: CustomEvent<{ row: SubjectHoursMatrixRow }>) => {
      const updatedRow = event.detail.row
      onDataChange(rowData.map((r) => (r.id === updatedRow.id ? updatedRow : r)))
    }

    window.addEventListener('subjectHoursChange', handleChange as EventListener)
    return () => {
      window.removeEventListener('subjectHoursChange', handleChange as EventListener)
    }
  }, [onDataChange, rowData])

  // Handle paste from clipboard
  const handlePasteCells = useCallback(
    async (
      updates: Array<{
        rowId: string
        field: string
        newValue: string
        originalData: SubjectHoursMatrixRow
      }>
    ) => {
      const updatedRows = new Map<string, SubjectHoursMatrixRow>()

      for (const update of updates) {
        const existing = updatedRows.get(update.rowId) ?? update.originalData

        // Skip non-applicable rows
        if (!existing.isApplicable) continue

        // Parse field to determine if it's an hours column
        if (update.field.startsWith('hours_')) {
          const levelId = update.field.replace('hours_', '')
          const numValue = parseFloat(update.newValue)
          const newHours = {
            ...existing.hours,
            [levelId]: isNaN(numValue) ? null : numValue,
          }

          const updatedRow: SubjectHoursMatrixRow = {
            ...existing,
            hours: newHours,
            isDirty: true,
            isValid: Object.values(newHours).every(validateHoursValue),
          }
          updatedRows.set(update.rowId, updatedRow)
        }
      }

      // Apply updates to parent state
      const newRowData = rowData.map((row) =>
        updatedRows.has(row.id) ? updatedRows.get(row.id)! : row
      )
      onDataChange(newRowData)
    },
    [rowData, onDataChange]
  )

  const { handlePaste } = useCustomClipboard<SubjectHoursMatrixRow>({
    gridApi: gridApiRef.current,
    onPasteCells: handlePasteCells,
  })

  // Handle cell value changes
  const onCellValueChanged = useCallback(
    (event: CellValueChangedEvent<SubjectHoursMatrixRow>) => {
      const { data, colDef, newValue } = event
      if (!data || !colDef.field) return

      // Skip non-applicable rows
      if (!data.isApplicable) return

      // Handle hours columns
      if (colDef.field.startsWith('hours_')) {
        const levelId = colDef.field.replace('hours_', '')
        const numValue = typeof newValue === 'number' ? newValue : parseFloat(newValue)

        const newHours = {
          ...data.hours,
          [levelId]: isNaN(numValue) ? null : numValue,
        }

        const updatedRow: SubjectHoursMatrixRow = {
          ...data,
          hours: newHours,
          isDirty: true,
          isValid: Object.values(newHours).every(validateHoursValue),
        }

        onDataChange(rowData.map((r) => (r.id === updatedRow.id ? updatedRow : r)))
      }

      // Handle notes column
      if (colDef.field === 'notes') {
        const updatedRow: SubjectHoursMatrixRow = {
          ...data,
          notes: newValue?.toString() ?? '',
          isDirty: true,
        }
        onDataChange(rowData.map((r) => (r.id === updatedRow.id ? updatedRow : r)))
      }
    },
    [rowData, onDataChange]
  )

  // Build column definitions dynamically based on levels
  const columnDefs: ColDef<SubjectHoursMatrixRow>[] = useMemo(() => {
    const cols: ColDef<SubjectHoursMatrixRow>[] = [
      // Subject info columns (fixed)
      {
        field: 'subjectCode',
        headerName: 'Code',
        width: 80,
        pinned: 'left',
        editable: false,
        cellClass: 'font-mono font-medium',
        cellStyle: (params) => getCellStyle(params, false),
      },
      {
        field: 'subjectName',
        headerName: 'Subject',
        width: 180,
        pinned: 'left',
        editable: false,
        cellStyle: (params) => getCellStyle(params, false),
      },
      {
        field: 'category',
        headerName: 'Category',
        width: 100,
        editable: false,
        cellStyle: (params) => getCellStyle(params, false),
        valueFormatter: (params) => {
          const categoryLabels: Record<string, string> = {
            core: 'Core',
            elective: 'Elective',
            specialty: 'Specialty',
            local: 'Local',
          }
          return categoryLabels[params.value] ?? params.value
        },
      },
    ]

    // Add a column for each level (hours)
    for (const level of levels) {
      cols.push({
        field: `hours_${level.id}` as keyof SubjectHoursMatrixRow,
        headerName: level.code,
        headerTooltip: `${level.name_en} - Hours per week`,
        width: 75,
        editable: (params) => params.data?.isApplicable ?? false,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 12,
          precision: 1,
        },
        cellStyle: (params) => getCellStyle(params, true),
        valueGetter: (params) => {
          if (!params.data) return null
          return params.data.hours[level.id] ?? null
        },
        valueSetter: (params) => {
          if (!params.data) return false
          const numValue =
            typeof params.newValue === 'number' ? params.newValue : parseFloat(params.newValue)
          params.data.hours[level.id] = isNaN(numValue) ? null : numValue
          return true
        },
        valueFormatter: (params) => {
          if (params.value === null || params.value === undefined) return '-'
          if (!params.data?.isApplicable) return 'N/A'
          return params.value.toString()
        },
      } as ColDef<SubjectHoursMatrixRow>)
    }

    // Add split checkbox column (combined for all levels)
    cols.push({
      headerName: 'Split',
      headerTooltip: 'Split class (smaller groups)',
      width: 70,
      editable: false,
      cellRenderer: SplitCheckboxRenderer,
      cellStyle: (params) => getCellStyle(params, false),
    })

    // Notes column
    cols.push({
      field: 'notes',
      headerName: 'Notes',
      flex: 1,
      minWidth: 150,
      editable: (params) => params.data?.isApplicable ?? false,
      cellStyle: (params) => getCellStyle(params, false),
    })

    return cols
  }, [levels])

  // Get row ID
  const getRowId = useCallback((params: { data: SubjectHoursMatrixRow }) => {
    return params.data.id
  }, [])

  return (
    <div onPaste={handlePaste} className="w-full">
      <DataTableLazy
        rowData={rowData}
        columnDefs={columnDefs}
        loading={isLoading}
        error={error}
        pagination={false}
        onCellValueChanged={onCellValueChanged}
        onGridReady={onGridReady}
        domLayout="autoHeight"
        defaultColDef={{
          sortable: true,
          resizable: true,
        }}
        getRowId={getRowId}
        suppressMovableColumns
        rowSelection={undefined}
      />

      {/* Legend */}
      <div className="mt-3 flex items-center gap-4 text-xs text-text-tertiary">
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-warning-100 rounded border border-border-light" />
          <span>Unsaved changes</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-terracotta-100 rounded border border-border-light" />
          <span>Invalid value (0-12 range)</span>
        </div>
        <div className="flex items-center gap-1">
          <div className="w-4 h-4 bg-subtle rounded border border-border-light" />
          <span>Not applicable</span>
        </div>
        <div className="ml-auto text-text-tertiary">
          Tip: Paste from Excel (Ctrl+V / Cmd+V) to bulk-fill hours
        </div>
      </div>
    </div>
  )
}
