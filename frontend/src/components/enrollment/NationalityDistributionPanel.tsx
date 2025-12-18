import { memo, useEffect, useMemo, useState, useCallback } from 'react'
import type { ColumnDef } from '@tanstack/react-table'
import {
  EditableTable,
  type CellValueChangedEvent,
  type EditableColumnMeta,
} from '@/components/grid/tanstack'
import { Button } from '@/components/ui/button'
import { AlertCircle, CheckCircle, Save } from 'lucide-react'
import {
  useEnrollmentWithDistribution,
  useBulkUpsertDistributions,
} from '@/hooks/api/useEnrollment'
import { useLevels } from '@/hooks/api/useConfiguration'
import { toastMessages } from '@/lib/toast-messages'

interface LocalDistribution {
  level_id: string
  level_code: string
  level_name: string
  cycle_code: string
  french_pct: number
  saudi_pct: number
  other_pct: number
  sum: number
  isValid: boolean
}

interface LevelLike {
  id: string
  code: string
  name_fr?: string | null
  name_en?: string | null
  cycle_id?: string | null
}

interface NationalityDistributionPanelProps {
  versionId: string | undefined
  disabled?: boolean
}

// PERFORMANCE FIX: React.memo prevents re-renders when props haven't changed
export const NationalityDistributionPanel = memo(function NationalityDistributionPanel({
  versionId,
  disabled,
}: NationalityDistributionPanelProps) {
  const { data: enrollmentData, isLoading } = useEnrollmentWithDistribution(versionId)
  const { data: levelsData } = useLevels()
  const saveMutation = useBulkUpsertDistributions()

  const [rows, setRows] = useState<LocalDistribution[]>([])
  const [dirty, setDirty] = useState(false)

  const getCycleCode = useCallback((cycleId: string) => {
    const cycleMap: Record<string, string> = {
      MAT: 'MAT',
      ELEM: 'ELEM',
      COLL: 'COLL',
      LYC: 'LYC',
    }
    return cycleMap[cycleId] ?? ''
  }, [])

  useEffect(() => {
    if (!levelsData) return
    const dists = enrollmentData?.distributions ?? []
    const next = (levelsData as unknown as LevelLike[]).map((level) => {
      const existing = dists.find((d) => d.level_id === level.id)
      const french = existing?.french_pct ?? 30
      const saudi = existing?.saudi_pct ?? 2
      const other = existing?.other_pct ?? 68
      const sum = french + saudi + other
      return {
        level_id: level.id,
        level_code: level.code,
        level_name: level.name_fr || level.name_en || level.code,
        cycle_code: level.cycle_id ? getCycleCode(level.cycle_id) : '',
        french_pct: french,
        saudi_pct: saudi,
        other_pct: other,
        sum,
        isValid: Math.abs(sum - 100) < 0.01,
      }
    })
    setRows(next)
    setDirty(false)
  }, [levelsData, enrollmentData?.distributions, getCycleCode])

  const allValid = useMemo(() => rows.every((r) => r.isValid), [rows])

  const columnDefs: ColumnDef<LocalDistribution, unknown>[] = useMemo(
    () => [
      {
        accessorKey: 'cycle_code',
        header: 'Cycle',
        size: 100,
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'level_code',
        header: 'Level',
        size: 100,
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'level_name',
        header: 'Name',
        size: 200,
        meta: {
          editable: false,
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'french_pct',
        header: 'French %',
        size: 120,
        cell: ({ getValue }) => {
          const value = getValue() as number
          return value?.toFixed(2) ?? '0.00'
        },
        meta: {
          editable: !disabled,
          editorType: 'number',
          min: 0,
          max: 100,
          precision: 2,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'saudi_pct',
        header: 'Saudi %',
        size: 120,
        cell: ({ getValue }) => {
          const value = getValue() as number
          return value?.toFixed(2) ?? '0.00'
        },
        meta: {
          editable: !disabled,
          editorType: 'number',
          min: 0,
          max: 100,
          precision: 2,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'other_pct',
        header: 'Other %',
        size: 120,
        cell: ({ getValue }) => {
          const value = getValue() as number
          return value?.toFixed(2) ?? '0.00'
        },
        meta: {
          editable: !disabled,
          editorType: 'number',
          min: 0,
          max: 100,
          precision: 2,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
      {
        accessorKey: 'sum',
        header: 'Total',
        size: 100,
        cell: ({ row }) => {
          const sum = row.original.sum ?? 0
          const isValid = row.original.isValid
          return (
            <span className={isValid ? 'text-green-600' : 'text-red-600'}>
              {sum.toFixed(1)}%
              {isValid ? (
                <CheckCircle className="inline h-3 w-3 ml-1" />
              ) : (
                <AlertCircle className="inline h-3 w-3 ml-1" />
              )}
            </span>
          )
        },
        meta: {
          editable: false,
          align: 'right',
        } satisfies EditableColumnMeta,
      },
    ],
    [disabled]
  )

  const onCellValueChanged = useCallback((event: CellValueChangedEvent<LocalDistribution>) => {
    const { data, field, newValue } = event
    if (!data || !field) return
    if (!['french_pct', 'saudi_pct', 'other_pct'].includes(field)) return

    setRows((prev) =>
      prev.map((r) => {
        if (r.level_id !== data.level_id) return r
        const updated = { ...r, [field]: Number(newValue) || 0 }
        const sum = updated.french_pct + updated.saudi_pct + updated.other_pct
        return {
          ...updated,
          sum,
          isValid: Math.abs(sum - 100) < 0.01,
        }
      })
    )
    setDirty(true)
  }, [])

  const save = async () => {
    if (!versionId) {
      toastMessages.warning.selectVersion()
      return
    }
    if (!allValid) {
      toastMessages.error.validation('All percentages must sum to 100%')
      return
    }
    await saveMutation.mutateAsync({
      versionId,
      distributions: rows.map((r) => ({
        level_id: r.level_id,
        french_pct: r.french_pct,
        saudi_pct: r.saudi_pct,
        other_pct: r.other_pct,
      })),
    })
    setDirty(false)
  }

  return (
    <div className="space-y-3">
      <div className="flex justify-end">
        <Button type="button" onClick={save} disabled={!dirty || !allValid || disabled}>
          <Save className="h-4 w-4 mr-2" />
          Save Distributions
        </Button>
      </div>
      <EditableTable<LocalDistribution>
        rowData={rows}
        columnDefs={columnDefs}
        loading={isLoading}
        onCellValueChanged={onCellValueChanged}
        getRowId={(row) => row.level_id}
        height={400}
      />
    </div>
  )
})
