import { useCallback, useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { ColDef, CellValueChangedEvent, ValueGetterParams } from 'ag-grid-community'
import { requireAuth } from '@/lib/auth-guard'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { AlertCircle } from 'lucide-react'
import {
  useTimetableConstraints,
  useUpdateTimetableConstraint,
  useLevels,
} from '@/hooks/api/useConfiguration'
import { TimetableConstraint } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'

export const Route = createFileRoute('/configuration/timetable')({
  beforeLoad: requireAuth,
  component: TimetablePage,
})

function TimetablePage() {
  const { selectedVersionId } = useBudgetVersion()
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

  const handleCellValueChanged = useCallback(
    (event: CellValueChangedEvent<TimetableConstraint>) => {
      const { data: row, oldValue, newValue, colDef } = event

      // Validate cross-field constraint: max_hours_per_day <= total_hours_per_week
      if (colDef.field === 'max_hours_per_day' || colDef.field === 'total_hours_per_week') {
        const maxHours =
          colDef.field === 'max_hours_per_day' ? Number(newValue) : Number(row.max_hours_per_day)
        const totalHours =
          colDef.field === 'total_hours_per_week'
            ? Number(newValue)
            : Number(row.total_hours_per_week)

        if (maxHours > totalHours) {
          toastMessages.error.custom(
            'Les heures max par jour ne peuvent pas dépasser le total hebdomadaire'
          )
          // Revert to old value
          if (colDef.field) {
            event.node.setDataValue(colDef.field, oldValue)
          }
          return
        }
      }

      if (!selectedVersionId || !row.level_id) return

      updateMutation.mutate(
        {
          budget_version_id: selectedVersionId,
          level_id: row.level_id,
          total_hours_per_week:
            colDef.field === 'total_hours_per_week'
              ? Number(newValue)
              : Number(row.total_hours_per_week),
          max_hours_per_day:
            colDef.field === 'max_hours_per_day' ? Number(newValue) : Number(row.max_hours_per_day),
          days_per_week:
            colDef.field === 'days_per_week' ? Number(newValue) : Number(row.days_per_week),
          requires_lunch_break:
            colDef.field === 'requires_lunch_break' ? newValue : row.requires_lunch_break,
          min_break_duration_minutes:
            colDef.field === 'min_break_duration_minutes'
              ? Number(newValue)
              : Number(row.min_break_duration_minutes),
          notes: colDef.field === 'notes' ? newValue : row.notes,
        },
        {
          onError: () => {
            // Revert on error
            if (colDef.field) {
              event.node.setDataValue(colDef.field, oldValue)
            }
          },
        }
      )
    },
    [selectedVersionId, updateMutation]
  )

  const columnDefs: ColDef<TimetableConstraint>[] = useMemo(
    () => [
      {
        field: 'level_id',
        headerName: 'Niveau',
        valueFormatter: (params) => getLevelName(params.value),
        flex: 1.2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'total_hours_per_week',
        headerName: 'Heures/Semaine',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 60, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 2 }),
        flex: 1,
      },
      {
        field: 'max_hours_per_day',
        headerName: 'Heures Max/Jour',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 12, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 2 }),
        flex: 1,
      },
      {
        field: 'days_per_week',
        headerName: 'Jours/Semaine',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 4, max: 6, precision: 0 },
        flex: 0.9,
      },
      {
        headerName: 'Capacité Totale',
        valueGetter: (params: ValueGetterParams<TimetableConstraint>) => {
          const days = params.data?.days_per_week ?? 0
          const maxHours = params.data?.max_hours_per_day ?? 0
          return days * maxHours
        },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : `${Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 2 })}h`,
        flex: 1,
        cellStyle: { backgroundColor: '#f0f9ff', fontWeight: 'bold' },
      },
      {
        field: 'requires_lunch_break',
        headerName: 'Pause Déjeuner',
        editable: true,
        cellRenderer: 'agCheckboxCellRenderer',
        cellEditor: 'agCheckboxCellEditor',
        flex: 1,
      },
      {
        field: 'min_break_duration_minutes',
        headerName: 'Pause Min (min)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 30, max: 120, precision: 0 },
        flex: 1,
      },
      {
        field: 'notes',
        headerName: 'Notes',
        editable: true,
        flex: 1.5,
        filter: 'agTextColumnFilter',
      },
    ],
    [getLevelName]
  )

  return (
    <MainLayout>
      <PageContainer
        title="Contraintes Horaires"
        description="Définir les limites hebdomadaires (heures/jour, heures/semaine, pauses) pour valider les emplois du temps DHG"
      >
        <div className="space-y-4">
          {!selectedVersionId ? (
            <div className="rounded-md border border-amber-200 bg-amber-50 p-4 text-amber-900">
              <AlertCircle className="mb-2 h-5 w-5" />
              Veuillez sélectionner une version budgétaire pour afficher les contraintes horaires.
            </div>
          ) : (
            <>
              {/* Info Box */}
              <div className="flex items-start gap-2 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm">
                <AlertCircle className="mt-0.5 h-4 w-4 text-blue-600" />
                <div>
                  <p className="font-medium text-blue-900">Règles de validation</p>
                  <ul className="list-inside list-disc text-blue-700">
                    <li>Heures max/jour ≤ Total heures/semaine</li>
                    <li>Capacité totale = Jours/semaine × Heures max/jour</li>
                    <li>Pause minimale: 30-120 minutes</li>
                  </ul>
                </div>
              </div>

              {/* Data Grid */}
              {error ? (
                <div className="rounded-md border border-red-200 bg-red-50 p-4 text-red-900">
                  Erreur de chargement: {error.message}
                </div>
              ) : (
                <DataTableLazy
                  rowData={rowData}
                  columnDefs={columnDefs}
                  loading={isLoading}
                  onCellValueChanged={handleCellValueChanged}
                  pagination
                  paginationPageSize={50}
                  domLayout="autoHeight"
                />
              )}
            </>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
