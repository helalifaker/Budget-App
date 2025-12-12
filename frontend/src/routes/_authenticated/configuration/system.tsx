import { useCallback, useEffect, useMemo, useState } from 'react'
import { createFileRoute } from '@tanstack/react-router'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { requireAuth } from '@/lib/auth-guard'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { AlertCircle } from 'lucide-react'
import { useSystemConfigs, useUpdateSystemConfig } from '@/hooks/api/useConfiguration'
import { SystemConfig } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'

export const Route = createFileRoute('/_authenticated/configuration/system')({
  beforeLoad: requireAuth,
  component: SystemConfigPage,
})

const CATEGORIES = [
  { value: 'all', label: 'Toutes' },
  { value: 'currency', label: 'Devise' },
  { value: 'locale', label: 'Locale' },
  { value: 'academic', label: 'Académique' },
  { value: 'system', label: 'Système' },
]

function SystemConfigPage() {
  const [selectedCategory, setSelectedCategory] = useState('all')
  const [rowData, setRowData] = useState<SystemConfig[]>([])

  const {
    data: configs,
    isLoading,
    error,
  } = useSystemConfigs(selectedCategory === 'all' ? undefined : selectedCategory)
  const updateMutation = useUpdateSystemConfig()

  useEffect(() => {
    if (configs) {
      setRowData(configs)
    }
  }, [configs])

  const handleCellValueChanged = useCallback(
    (event: CellValueChangedEvent<SystemConfig>) => {
      const { data: row, oldValue, newValue, colDef } = event

      // Validate JSON if editing the value field
      if (colDef.field === 'value') {
        try {
          // Try to parse the JSON to validate it
          JSON.parse(typeof newValue === 'string' ? newValue : JSON.stringify(newValue))
        } catch {
          toastMessages.error.custom('JSON invalide. Vérifiez la syntaxe.')
          // Revert to old value
          event.node.setDataValue(colDef.field, oldValue)
          return
        }
      }

      if (!row.key) return

      // Prepare update data
      const updateData: Partial<SystemConfig> = {}
      if (colDef.field === 'value') {
        updateData.value = typeof newValue === 'string' ? JSON.parse(newValue) : newValue
      } else if (colDef.field === 'description') {
        updateData.description = newValue
      } else if (colDef.field === 'is_active') {
        updateData.is_active = newValue
      }

      updateMutation.mutate(
        { key: row.key, data: updateData },
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
    [updateMutation]
  )

  const columnDefs: ColDef<SystemConfig>[] = useMemo(
    () => [
      {
        field: 'key',
        headerName: 'Clé',
        flex: 1.5,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'category',
        headerName: 'Catégorie',
        flex: 0.8,
        filter: 'agSetColumnFilter',
      },
      {
        field: 'value',
        headerName: 'Valeur (JSON)',
        editable: true,
        cellEditor: 'agLargeTextCellEditor',
        cellEditorParams: {
          maxLength: 5000,
          rows: 10,
          cols: 50,
        },
        valueFormatter: (params) => {
          if (!params.value) return ''
          try {
            return JSON.stringify(params.value, null, 2)
          } catch {
            return String(params.value)
          }
        },
        cellStyle: { fontFamily: 'monospace', fontSize: '12px' },
        flex: 2.5,
        wrapText: true,
        autoHeight: true,
      },
      {
        field: 'description',
        headerName: 'Description',
        editable: true,
        flex: 2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'is_active',
        headerName: 'Actif',
        editable: true,
        cellRenderer: 'agCheckboxCellRenderer',
        cellEditor: 'agCheckboxCellEditor',
        flex: 0.6,
        filter: 'agSetColumnFilter',
      },
    ],
    []
  )

  return (
    <PageContainer
      title="Configuration Système"
      description="Gérer les paramètres de configuration système (devise, locale, paramètres académiques)"
    >
      <div className="space-y-4">
        {/* Category Filter */}
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Label htmlFor="category-filter">Category:</Label>
            <Select value={selectedCategory} onValueChange={setSelectedCategory}>
              <SelectTrigger id="category-filter" className="w-[200px]">
                <SelectValue placeholder="Select a category" />
              </SelectTrigger>
              <SelectContent>
                {CATEGORIES.map((cat) => (
                  <SelectItem key={cat.value} value={cat.value}>
                    {cat.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Info Box */}
        <div className="flex items-start gap-2 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm">
          <AlertCircle className="mt-0.5 h-4 w-4 text-blue-600" />
          <div>
            <p className="font-medium text-blue-900">Configuration Editing</p>
            <p className="text-blue-700">
              Click a cell to edit. JSON values must be valid. Format: {'{'}&#34;key&#34;:
              &#34;value&#34;{'}'}, [1, 2, 3], or &#34;string&#34;
            </p>
          </div>
        </div>

        {/* Data Grid */}
        {error ? (
          <div className="rounded-md border border-red-200 bg-red-50 p-4 text-red-900">
            Loading error: {error.message}
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
      </div>
    </PageContainer>
  )
}
