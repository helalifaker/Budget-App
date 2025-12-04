import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { AlertCircle } from 'lucide-react'
import {
  useFeeStructure,
  useUpdateFeeStructure,
  useFeeCategories,
  useNationalityTypes,
  useLevels,
} from '@/hooks/api/useConfiguration'
import { FeeStructure } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'

export const Route = createFileRoute('/configuration/fees')({
  beforeLoad: requireAuth,
  component: FeesPage,
})

function FeesPage() {
  const [selectedVersionId, setSelectedVersionId] = useState<string>('')
  const [rowData, setRowData] = useState<FeeStructure[]>([])

  const {
    data: feeStructureData,
    isLoading: feesLoading,
    error: feesError,
  } = useFeeStructure(selectedVersionId)
  const { data: feeCategoriesData, isLoading: categoriesLoading } = useFeeCategories()
  const { data: nationalityTypesData, isLoading: nationalitiesLoading } = useNationalityTypes()
  const { data: levelsData, isLoading: levelsLoading } = useLevels()

  const updateMutation = useUpdateFeeStructure()

  const isLoading = feesLoading || categoriesLoading || nationalitiesLoading || levelsLoading

  useEffect(() => {
    if (feeStructureData) {
      setRowData(feeStructureData)
    }
  }, [feeStructureData])

  const getLevelName = useCallback(
    (levelId: string) => {
      return levelsData?.find((l) => l.id === levelId)?.name || levelId
    },
    [levelsData]
  )

  const getNationalityName = useCallback(
    (nationalityTypeId: string) => {
      return (
        nationalityTypesData?.find((n) => n.id === nationalityTypeId)?.name || nationalityTypeId
      )
    },
    [nationalityTypesData]
  )

  const getFeeCategoryName = useCallback(
    (feeCategoryId: string) => {
      return feeCategoriesData?.find((c) => c.id === feeCategoryId)?.name_fr || feeCategoryId
    },
    [feeCategoriesData]
  )

  const getSiblingDiscountApplicable = useCallback(
    (feeCategoryId: string) => {
      const category = feeCategoriesData?.find((c) => c.id === feeCategoryId)
      return category?.allows_sibling_discount ? 'Oui' : 'Non'
    },
    [feeCategoriesData]
  )

  const formatCurrency = useCallback((value: number | null | undefined): string => {
    if (value == null) return ''
    return new Intl.NumberFormat('fr-FR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value)
  }, [])

  const handleCellValueChanged = useCallback(
    async (event: CellValueChangedEvent<FeeStructure>) => {
      const updatedRow = event.data
      if (!updatedRow) return

      const field = event.column.getColId()
      const newValue = event.newValue
      const oldValue = event.oldValue

      if (newValue === oldValue) return

      if (field === 'amount_sar' && newValue < 0) {
        toastMessages.error.validation('Le montant doit être positif ou nul')
        event.node.setDataValue(field, oldValue)
        return
      }

      const updatedData = {
        [field]: newValue,
      }

      try {
        await updateMutation.mutateAsync({
          id: updatedRow.id,
          ...updatedData,
        })
      } catch {
        event.node.setDataValue(field, oldValue)
      }
    },
    [updateMutation]
  )

  const columnDefs: ColDef<FeeStructure>[] = useMemo(
    () => [
      {
        field: 'level_id',
        headerName: 'Niveau',
        flex: 2,
        editable: false,
        valueGetter: (params) => {
          const levelId = params.data?.level_id
          return levelId ? getLevelName(levelId) : ''
        },
        filter: 'agTextColumnFilter',
      },
      {
        field: 'nationality_type_id',
        headerName: 'Nationalité',
        flex: 2,
        editable: false,
        valueGetter: (params) => {
          const nationalityId = params.data?.nationality_type_id
          return nationalityId ? getNationalityName(nationalityId) : ''
        },
        filter: 'agTextColumnFilter',
      },
      {
        field: 'fee_category_id',
        headerName: 'Catégorie',
        flex: 2,
        editable: false,
        valueGetter: (params) => {
          const categoryId = params.data?.fee_category_id
          return categoryId ? getFeeCategoryName(categoryId) : ''
        },
        filter: 'agTextColumnFilter',
      },
      {
        field: 'trimester',
        headerName: 'Trimestre',
        flex: 1,
        editable: false,
        valueGetter: (params) => {
          const trimester = params.data?.trimester
          return trimester ? `T${trimester}` : 'Annuel'
        },
        filter: 'agTextColumnFilter',
      },
      {
        field: 'amount_sar',
        headerName: 'Montant (SAR)',
        flex: 1.5,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          precision: 2,
        },
        filter: 'agNumberColumnFilter',
        valueFormatter: (params) => formatCurrency(params.value),
      },
      {
        headerName: 'Réduction Fratrie',
        flex: 1.5,
        editable: false,
        valueGetter: (params) => {
          const categoryId = params.data?.fee_category_id
          return categoryId ? getSiblingDiscountApplicable(categoryId) : 'Non'
        },
        filter: 'agTextColumnFilter',
      },
      {
        field: 'notes',
        headerName: 'Notes',
        flex: 2,
        editable: true,
        cellEditor: 'agLargeTextCellEditor',
        filter: 'agTextColumnFilter',
      },
    ],
    [
      getLevelName,
      getNationalityName,
      getFeeCategoryName,
      getSiblingDiscountApplicable,
      formatCurrency,
    ]
  )

  return (
    <MainLayout>
      <PageContainer
        title="Structure Tarifaire"
        description="Configuration des frais de scolarité par niveau, nationalité et catégorie"
      >
        <div className="space-y-4">
          <BudgetVersionSelector value={selectedVersionId} onChange={setSelectedVersionId} />

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
                  Les cellules Montant et Notes sont modifiables. Cliquez pour éditer les valeurs.
                  Les changements sont automatiquement sauvegardés.
                </p>
              </div>

              <DataTableLazy
                rowData={rowData}
                columnDefs={columnDefs}
                loading={isLoading}
                error={feesError}
                pagination={true}
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
