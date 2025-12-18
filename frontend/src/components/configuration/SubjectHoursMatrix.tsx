import { useMemo, useCallback, useEffect } from 'react'
import type { ColumnDef, CellContext } from '@tanstack/react-table'
import {
  EditableTable,
  type CellValueChangedEvent,
  type EditableColumnMeta,
} from '@/components/grid/tanstack'
import { LevelInfo } from '@/types/api'
import { SubjectHoursMatrixRow, validateHoursValue } from './subjectHoursUtils'
import { cn } from '@/lib/utils'

// Type re-export only (safe for fast-refresh)
export type { SubjectHoursMatrixRow }

export interface SubjectHoursMatrixProps {
  levels: LevelInfo[]
  isLoading?: boolean
  error?: Error | null
  onDataChange: (rows: SubjectHoursMatrixRow[]) => void
  rowData: SubjectHoursMatrixRow[]
}

// Category label mapping
const CATEGORY_LABELS: Record<string, string> = {
  core: 'Core',
  elective: 'Elective',
  specialty: 'Specialty',
  local: 'Local',
}

// ============================================================================
// Cell Style Helper (for className)
// ============================================================================

function getCellClass(data: SubjectHoursMatrixRow | undefined, levelId?: string): string {
  if (!data) return ''

  // Non-applicable subjects: subtle background with muted text
  if (!data.isApplicable) {
    return 'bg-subtle text-text-disabled'
  }

  // For hours columns, check validity
  if (levelId) {
    const value = data.hours[levelId]
    if (!validateHoursValue(value)) {
      return 'bg-terracotta-100' // Invalid value
    }
  }

  // Dirty rows: warning background
  if (data.isDirty) {
    return 'bg-warning-100'
  }

  return ''
}

// ============================================================================
// Main Component
// ============================================================================

export function SubjectHoursMatrix({
  levels,
  isLoading = false,
  onDataChange,
  rowData,
}: SubjectHoursMatrixProps) {
  // Listen for custom change events (from checkbox changes)
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

  // Handle cell value changes
  const onCellValueChanged = useCallback(
    (event: CellValueChangedEvent<SubjectHoursMatrixRow>) => {
      const { data, field, newValue } = event
      if (!data || !field) return

      // Skip non-applicable rows
      if (!data.isApplicable) return

      // Handle hours columns
      if (field.startsWith('hours_')) {
        const levelId = field.replace('hours_', '')
        const numValue = typeof newValue === 'number' ? newValue : parseFloat(String(newValue))

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

      // Handle split columns (checkboxes)
      if (field.startsWith('split_')) {
        const levelId = field.replace('split_', '')
        const updatedSplitFlags = { ...data.splitFlags, [levelId]: Boolean(newValue) }

        const updatedRow: SubjectHoursMatrixRow = {
          ...data,
          splitFlags: updatedSplitFlags,
          isDirty: true,
        }

        onDataChange(rowData.map((r) => (r.id === updatedRow.id ? updatedRow : r)))
      }

      // Handle notes column
      if (field === 'notes') {
        const updatedRow: SubjectHoursMatrixRow = {
          ...data,
          notes: String(newValue ?? ''),
          isDirty: true,
        }
        onDataChange(rowData.map((r) => (r.id === updatedRow.id ? updatedRow : r)))
      }
    },
    [rowData, onDataChange]
  )

  // Build column definitions dynamically based on levels
  const columnDefs: ColumnDef<SubjectHoursMatrixRow, unknown>[] = useMemo(() => {
    const cols: ColumnDef<SubjectHoursMatrixRow, unknown>[] = [
      // Subject info columns (fixed)
      {
        accessorKey: 'subjectCode',
        header: 'Code',
        size: 80,
        cell: ({ getValue, row }) => (
          <span className={cn('font-mono font-medium', getCellClass(row.original))}>
            {String(getValue() ?? '')}
          </span>
        ),
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'subjectName',
        header: 'Subject',
        size: 180,
        cell: ({ getValue, row }) => (
          <span className={getCellClass(row.original)}>{String(getValue() ?? '')}</span>
        ),
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'category',
        header: 'Category',
        size: 100,
        cell: ({ getValue, row }) => {
          const value = getValue() as string
          return (
            <span className={getCellClass(row.original)}>{CATEGORY_LABELS[value] ?? value}</span>
          )
        },
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
    ]

    // Add a column for each level (hours)
    for (const level of levels) {
      const levelId = level.id
      cols.push({
        id: `hours_${levelId}`,
        accessorFn: (row) => row.hours[levelId] ?? null,
        header: level.code,
        size: 75,
        cell: (info: CellContext<SubjectHoursMatrixRow, unknown>) => {
          const value = info.getValue() as number | null
          const data = info.row.original
          const cellClass = getCellClass(data, levelId)

          if (!data?.isApplicable) {
            return <span className={cellClass}>N/A</span>
          }
          if (value === null || value === undefined) {
            return <span className={cellClass}>-</span>
          }
          return <span className={cellClass}>{value}</span>
        },
        meta: {
          editable: true, // Editability check handled in onCellValueChanged
          editorType: 'number',
          min: 0,
          max: 12,
          precision: 1,
          align: 'right',
        } satisfies EditableColumnMeta,
      } as ColumnDef<SubjectHoursMatrixRow, unknown>)
    }

    // Add split checkbox column (combined for primary level)
    // Using first level for simplicity - in practice, this may need multiple columns
    if (levels.length > 0) {
      const firstLevel = levels[0]
      cols.push({
        id: `split_${firstLevel.id}`,
        accessorFn: (row) => row.splitFlags[firstLevel.id] ?? false,
        header: 'Split',
        size: 70,
        cell: (info: CellContext<SubjectHoursMatrixRow, unknown>) => {
          const data = info.row.original
          if (!data?.isApplicable) {
            return <span className="text-text-disabled">-</span>
          }
          const isChecked = Boolean(info.getValue())
          return isChecked ? '✓' : '✗'
        },
        meta: {
          editable: true, // Editability check handled in onCellValueChanged
          editorType: 'checkbox',
          align: 'center',
        } satisfies EditableColumnMeta,
      } as ColumnDef<SubjectHoursMatrixRow, unknown>)
    }

    // Notes column
    cols.push({
      accessorKey: 'notes',
      header: 'Notes',
      size: 200,
      cell: ({ getValue, row }) => (
        <span className={getCellClass(row.original)}>{String(getValue() ?? '—')}</span>
      ),
      meta: {
        editable: true, // Editability check handled in onCellValueChanged
        editorType: 'text',
        placeholder: 'Add notes...',
      } satisfies EditableColumnMeta,
    })

    return cols
  }, [levels])

  return (
    <div className="w-full">
      <EditableTable<SubjectHoursMatrixRow>
        rowData={rowData}
        columnDefs={columnDefs}
        loading={isLoading}
        onCellValueChanged={onCellValueChanged}
        getRowId={(row) => row.id}
        height={500}
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
        <div className="ml-auto text-text-tertiary">Tip: Edit cells inline by clicking on them</div>
      </div>
    </div>
  )
}
