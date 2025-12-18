import { useCallback, useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { ColumnDef } from '@tanstack/react-table'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import {
  EditableTable,
  type CellValueChangedEvent,
  type EditableColumnMeta,
} from '@/components/grid/tanstack'
import { AlertCircle } from 'lucide-react'
import {
  useTimetableConstraints,
  useUpdateTimetableConstraint,
  useLevels,
} from '@/hooks/api/useConfiguration'
import { TimetableConstraint } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useVersion } from '@/contexts/VersionContext'

export const Route = createFileRoute('/_authenticated/workforce/settings/timetable')({
  beforeLoad: requireAuth,
  component: TimetablePage,
})

function TimetablePage() {
  const { selectedVersionId } = useVersion()
  const [rowData, setRowData] = useState<TimetableConstraint[]>([])

  const { data: constraints, isLoading, error } = useTimetableConstraints(selectedVersionId!)
  const { data: levels } = useLevels()
  const updateMutation = useUpdateTimetableConstraint()

  useEffect(() => {
    if (constraints) {
      setRowData(constraints)
    }
  }, [constraints])

  const getLevelName = useCallback(
    (id: string) => levels?.find((l) => l.id === id)?.name_en || id,
    [levels]
  )

  // Column definitions
  const columnDefs: ColumnDef<TimetableConstraint, unknown>[] = useMemo(
    () => [
      {
        accessorKey: 'level_id',
        header: 'Niveau',
        size: 140,
        cell: ({ getValue }) => getLevelName(getValue() as string),
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'total_hours_per_week',
        header: 'Heures/Semaine',
        size: 120,
        cell: ({ getValue }) => {
          const value = getValue()
          return value == null
            ? '—'
            : Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 2 })
        },
        meta: {
          editable: true,
          editorType: 'number',
          min: 0,
          max: 60,
          precision: 2,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'max_hours_per_day',
        header: 'Heures Max/Jour',
        size: 130,
        cell: ({ getValue }) => {
          const value = getValue()
          return value == null
            ? '—'
            : Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 2 })
        },
        meta: {
          editable: true,
          editorType: 'number',
          min: 0,
          max: 12,
          precision: 2,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'days_per_week',
        header: 'Jours/Semaine',
        size: 110,
        cell: ({ getValue }) => String(getValue() ?? '—'),
        meta: {
          editable: true,
          editorType: 'number',
          min: 4,
          max: 6,
          precision: 0,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        id: 'total_capacity',
        header: 'Capacité Totale',
        size: 120,
        accessorFn: (row) => {
          const days = row.days_per_week ?? 0
          const maxHours = row.max_hours_per_day ?? 0
          return days * maxHours
        },
        cell: ({ getValue }) => {
          const value = getValue()
          return (
            <span className="font-semibold text-slate-700">
              {value == null
                ? '—'
                : `${Number(value).toLocaleString('fr-FR', { maximumFractionDigits: 2 })}h`}
            </span>
          )
        },
        meta: {
          editable: false,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'requires_lunch_break',
        header: 'Pause Déjeuner',
        size: 120,
        cell: ({ getValue }) => (getValue() ? '✓' : '✗'),
        meta: {
          editable: true,
          editorType: 'checkbox',
          align: 'center',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'min_break_duration_minutes',
        header: 'Pause Min (min)',
        size: 120,
        cell: ({ getValue }) => String(getValue() ?? '—'),
        meta: {
          editable: true,
          editorType: 'number',
          min: 30,
          max: 120,
          precision: 0,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'notes',
        header: 'Notes',
        size: 180,
        cell: ({ getValue }) => String(getValue() ?? '—'),
        meta: {
          editable: true,
          editorType: 'text',
          placeholder: 'Add notes...',
        } satisfies EditableColumnMeta,
      },
    ],
    [getLevelName]
  )

  // Cell value changed handler
  const handleCellValueChanged = useCallback(
    (event: CellValueChangedEvent<TimetableConstraint>) => {
      const { data: row, field, newValue } = event

      // Validate cross-field constraint: max_hours_per_day <= total_hours_per_week
      if (field === 'max_hours_per_day' || field === 'total_hours_per_week') {
        const maxHours =
          field === 'max_hours_per_day' ? Number(newValue) : Number(row.max_hours_per_day)
        const totalHours =
          field === 'total_hours_per_week' ? Number(newValue) : Number(row.total_hours_per_week)

        if (maxHours > totalHours) {
          toastMessages.error.custom('Max hours per day cannot exceed total weekly hours')
          return
        }
      }

      if (!selectedVersionId || !row.level_id) return

      updateMutation.mutate(
        {
          version_id: selectedVersionId,
          level_id: row.level_id,
          total_hours_per_week:
            field === 'total_hours_per_week' ? Number(newValue) : Number(row.total_hours_per_week),
          max_hours_per_day:
            field === 'max_hours_per_day' ? Number(newValue) : Number(row.max_hours_per_day),
          days_per_week: field === 'days_per_week' ? Number(newValue) : Number(row.days_per_week),
          requires_lunch_break:
            field === 'requires_lunch_break' ? (newValue as boolean) : row.requires_lunch_break,
          min_break_duration_minutes:
            field === 'min_break_duration_minutes'
              ? Number(newValue)
              : Number(row.min_break_duration_minutes),
          notes: field === 'notes' ? (newValue as string) : row.notes,
        },
        {
          onError: () => {
            toastMessages.error.custom('Failed to update timetable constraint')
          },
        }
      )
    },
    [selectedVersionId, updateMutation]
  )

  return (
    <PageContainer
      title="Timetable Constraints"
      description="Define weekly limits (hours/day, hours/week, breaks) to validate DHG schedules"
    >
      <div className="space-y-4">
        {!selectedVersionId ? (
          <div className="rounded-md border border-terracotta-200 bg-terracotta-50 p-4 text-terracotta-900">
            <AlertCircle className="mb-2 h-5 w-5" />
            Please select a version to view timetable constraints.
          </div>
        ) : (
          <>
            {/* Info Box */}
            <div className="flex items-start gap-2 rounded-md border border-slate-200 bg-slate-50 p-3 text-sm">
              <AlertCircle className="mt-0.5 h-4 w-4 text-slate-600" />
              <div>
                <p className="font-medium text-slate-900">Validation Rules</p>
                <ul className="list-inside list-disc text-slate-700">
                  <li>Max hours/day ≤ Total hours/week</li>
                  <li>Total capacity = Days/week × Max hours/day</li>
                  <li>Minimum break: 30-120 minutes</li>
                </ul>
              </div>
            </div>

            {/* Data Grid */}
            {error ? (
              <div className="rounded-md border border-terracotta-200 bg-terracotta-50 p-4 text-terracotta-900">
                Loading error: {error.message}
              </div>
            ) : (
              <EditableTable
                rowData={rowData}
                columnDefs={columnDefs}
                getRowId={(row) => row.level_id}
                onCellValueChanged={handleCellValueChanged}
                loading={isLoading}
                height={500}
              />
            )}
          </>
        )}
      </div>
    </PageContainer>
  )
}
