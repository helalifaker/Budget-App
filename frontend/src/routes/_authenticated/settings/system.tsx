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

export const Route = createFileRoute('/_authenticated/settings/system')({
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

  // Column definitions
  const columnDefs: ColumnDef<SystemConfig, unknown>[] = useMemo(
    () => [
      {
        accessorKey: 'key',
        header: 'Clé',
        size: 180,
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'category',
        header: 'Catégorie',
        size: 100,
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'value',
        header: 'Valeur (JSON)',
        size: 300,
        cell: ({ getValue }) => {
          const value = getValue()
          if (!value) return '—'
          try {
            const formatted = JSON.stringify(value, null, 2)
            // Truncate for display (full value shown in editor)
            return (
              <span className="font-mono text-xs whitespace-pre-wrap line-clamp-3">
                {formatted}
              </span>
            )
          } catch {
            return String(value)
          }
        },
        meta: {
          editable: true,
          editorType: 'largeText',
          maxLength: 5000,
          rows: 10,
          validateJson: true,
          placeholder: 'Enter JSON value',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'description',
        header: 'Description',
        size: 240,
        meta: {
          editable: true,
          editorType: 'text',
          placeholder: 'Description',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'is_active',
        header: 'Actif',
        size: 80,
        cell: ({ getValue }) => (getValue() ? '✓' : '✗'),
        meta: {
          editable: true,
          editorType: 'checkbox',
          align: 'center',
        } satisfies EditableColumnMeta,
      },
    ],
    []
  )

  // Cell value changed handler
  const handleCellValueChanged = useCallback(
    (event: CellValueChangedEvent<SystemConfig>) => {
      const { data: row, field, newValue } = event

      // Validate JSON if editing the value field
      if (field === 'value') {
        try {
          // Try to parse the JSON to validate it
          JSON.parse(typeof newValue === 'string' ? newValue : JSON.stringify(newValue))
        } catch {
          toastMessages.error.custom('JSON invalide. Vérifiez la syntaxe.')
          return
        }
      }

      if (!row.key) return

      // Prepare update data
      const updateData: Partial<SystemConfig> = {}
      if (field === 'value') {
        updateData.value = typeof newValue === 'string' ? JSON.parse(newValue) : newValue
      } else if (field === 'description') {
        updateData.description = newValue as string
      } else if (field === 'is_active') {
        updateData.is_active = newValue as boolean
      }

      updateMutation.mutate(
        { key: row.key, data: updateData },
        {
          onError: () => {
            toastMessages.error.custom('Erreur lors de la mise à jour')
          },
        }
      )
    },
    [updateMutation]
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
          <EditableTable
            rowData={rowData}
            columnDefs={columnDefs}
            getRowId={(row) => row.key}
            onCellValueChanged={handleCellValueChanged}
            loading={isLoading}
            height={600}
          />
        )}
      </div>
    </PageContainer>
  )
}
