import { useCallback, useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { requireAuth } from '@/lib/auth-guard'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { AlertCircle } from 'lucide-react'
import {
  useFeeStructure,
  useFeeCategories,
  useNationalityTypes,
  useLevels,
  useUpdateFeeStructure,
} from '@/hooks/api/useConfiguration'
import { FeeStructure } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'

export const Route = createFileRoute('/configuration/fees')({
  beforeLoad: requireAuth,
  component: FeesPage,
})

function FeesPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [rowData, setRowData] = useState<FeeStructure[]>([])

  const { data: feeRows, isLoading, error } = useFeeStructure(selectedVersionId!)
  const { data: feeCategories } = useFeeCategories()
  const { data: nationalityTypes } = useNationalityTypes()
  const { data: levels } = useLevels()
  const updateMutation = useUpdateFeeStructure()

  useEffect(() => {
    if (feeRows) {
      setRowData(feeRows)
    }
  }, [feeRows])

  const getFeeCategoryName = useCallback(
    (id: string) =>
      feeCategories?.find((c) => c.id === id)?.name_en ||
      feeCategories?.find((c) => c.id === id)?.name_fr ||
      id,
    [feeCategories]
  )

  const getNationalityName = useCallback(
    (id: string) => nationalityTypes?.find((n) => n.id === id)?.name_en || id,
    [nationalityTypes]
  )

  const getLevelName = useCallback(
    (id: string) => levels?.find((l) => l.id === id)?.name_en || id,
    [levels]
  )

  const columnDefs: ColDef<FeeStructure>[] = useMemo(
    () => [
      {
        field: 'level_id',
        headerName: 'Niveau',
        valueFormatter: (params) => getLevelName(params.value),
        flex: 1.2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'nationality_type_id',
        headerName: 'Nationalité',
        valueFormatter: (params) => getNationalityName(params.value),
        flex: 1.1,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'fee_category_id',
        headerName: 'Catégorie',
        valueFormatter: (params) => getFeeCategoryName(params.value),
        flex: 1.2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'trimester',
        headerName: 'Trimestre',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 1, max: 3, precision: 0 },
        valueFormatter: (params) => params.value ?? 'Annuel',
        flex: 0.8,
      },
      {
        field: 'amount_sar',
        headerName: 'Montant (SAR)',
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 500000, precision: 2 },
        valueFormatter: (params) =>
          params.value == null
            ? ''
            : Number(params.value).toLocaleString('fr-FR', { maximumFractionDigits: 2 }),
        flex: 1,
      },
      {
        field: 'notes',
        headerName: 'Notes',
        editable: true,
        flex: 1.2,
      },
    ],
    [getFeeCategoryName, getNationalityName, getLevelName]
  )

  const handleCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<FeeStructure>) => {
      const updatedRow = event.data
      const field = event.column.getColId()
      const newValue = event.newValue
      const oldValue = event.oldValue

      if (!updatedRow || newValue === oldValue) return

      if (field === 'amount_sar' && (newValue == null || Number(newValue) < 0)) {
        toastMessages.error.validation('Le montant doit être positif')
        event.node.setDataValue(field, oldValue)
        return
      }

      if (field === 'trimester' && newValue != null) {
        const parsed = Number(newValue)
        if (parsed < 1 || parsed > 3) {
          toastMessages.error.validation('Le trimestre doit être 1, 2 ou 3 (ou vide pour annuel)')
          event.node.setDataValue(field, oldValue)
          return
        }
      }

      const payload = {
        budget_version_id: updatedRow.budget_version_id,
        level_id: updatedRow.level_id,
        nationality_type_id: updatedRow.nationality_type_id,
        fee_category_id: updatedRow.fee_category_id,
        amount_sar: field === 'amount_sar' ? Number(newValue) : updatedRow.amount_sar,
        trimester:
          field === 'trimester'
            ? newValue == null
              ? null
              : Number(newValue)
            : updatedRow.trimester,
        notes: field === 'notes' ? newValue : updatedRow.notes,
      }

      try {
        await updateMutation.mutateAsync(payload)
      } catch {
        event.node.setDataValue(field, oldValue)
      }
    },
    [updateMutation]
  )

  return (
    <MainLayout>
      <PageContainer
        title="Fee Structure"
        description="Configure tuition and other fee amounts by level, nationality and category"
      >
        <div className="space-y-4">
          {!selectedVersionId && (
            <div className="flex items-center gap-2 p-4 bg-sand-50 border border-sand-200 rounded-lg">
              <AlertCircle className="h-4 w-4 text-sand-600" />
              <p className="text-sm text-sand-800">
                Veuillez sélectionner une version budgétaire pour voir la structure tarifaire.
              </p>
            </div>
          )}

          {selectedVersionId && (
            <>
              <div className="flex items-center gap-2 p-4 bg-info-50 border border-info-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-info-600" />
                <p className="text-sm text-info-800">
                  Les montants sont en SAR. Laissez le trimestre vide pour les frais annuels, sinon
                  1-3 pour la scolarité trimestrielle.
                </p>
              </div>

              <DataTableLazy
                rowData={rowData}
                columnDefs={columnDefs}
                loading={isLoading}
                error={error}
                pagination
                paginationPageSize={50}
                onCellValueChanged={handleCellValueChanged}
                defaultColDef={{
                  sortable: true,
                  filter: true,
                  resizable: true,
                }}
              />
            </>
          )}
        </div>
      </PageContainer>
    </MainLayout>
  )
}
