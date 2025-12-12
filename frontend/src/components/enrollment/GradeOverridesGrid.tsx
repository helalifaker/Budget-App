import { memo, useMemo, useCallback } from 'react'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { DataTableLazy } from '@/components/DataTableLazy'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { HelpTooltip } from '@/components/ui/HelpTooltip'
import { ENROLLMENT_FIELDS } from '@/constants/enrollment-field-definitions'
import type { GradeOverride } from '@/types/enrollmentProjection'

interface LevelLike {
  id: string
  code: string
  name_fr?: string | null
  name_en?: string | null
  cycle?: { code: string } | null
  cycle_id?: string | null
}

interface GradeOverridesGridProps {
  levels: LevelLike[]
  overrides: GradeOverride[]
  onChange: (overrides: GradeOverride[]) => void
  disabled?: boolean
}

/**
 * GradeOverridesGrid - Grade-specific enrollment adjustments
 *
 * AG Grid for editing per-grade overrides:
 * - Retention Rate: % of students progressing to next grade
 * - Lateral Entry: Expected transfer students
 * - Max Divisions: Maximum class sections (A, B, C...)
 * - Class Size Ceiling: Maximum students per class
 *
 * This grid should be placed inside AdvancedFeaturesSection
 * as it's an advanced configuration option.
 */
export const GradeOverridesGrid = memo(function GradeOverridesGrid({
  levels,
  overrides,
  onChange,
  disabled,
}: GradeOverridesGridProps) {
  const rows: GradeOverride[] = useMemo(
    () =>
      levels.map((l) => {
        const existing = overrides.find((o) => o.level_id === l.id)
        return (
          existing ?? {
            level_id: l.id,
            level_code: l.code,
            level_name: l.name_fr || l.name_en || l.code,
            retention_rate: null,
            lateral_entry: null,
            max_divisions: null,
            class_size_ceiling: null,
          }
        )
      }),
    [levels, overrides]
  )

  const columnDefs: ColDef<GradeOverride>[] = useMemo(
    () => [
      {
        field: 'level_code',
        headerName: 'Grade',
        width: 110,
        headerTooltip: 'Grade level code (e.g., PS, CP, 6ème)',
      },
      {
        field: 'level_name',
        headerName: 'Name',
        flex: 1,
        headerTooltip: 'Full name of the grade level',
      },
      {
        field: 'retention_rate',
        headerName: 'Retention',
        width: 120,
        editable: !disabled,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0.85, max: 1.0, step: 0.01, precision: 2 },
        valueFormatter: (p) => (p.value == null ? '-' : `${(p.value * 100).toFixed(1)}%`),
        headerTooltip: 'Percentage of students who continue to the next grade (85% - 100%)',
      },
      {
        field: 'lateral_entry',
        headerName: 'Transfers',
        width: 120,
        editable: !disabled,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 0, max: 50, step: 1 },
        headerTooltip: 'Expected number of transfer students joining this grade mid-year',
      },
      {
        field: 'max_divisions',
        headerName: 'Max Classes',
        width: 120,
        editable: !disabled,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 2, max: 8, step: 1 },
        headerTooltip: 'Maximum number of class sections allowed (e.g., A, B, C, D)',
      },
      {
        field: 'class_size_ceiling',
        headerName: 'Max Size',
        width: 110,
        editable: !disabled,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: { min: 20, max: 30, step: 1 },
        headerTooltip: 'Maximum number of students allowed per class section',
      },
    ],
    [disabled]
  )

  const onCellValueChanged = useCallback(
    (event: CellValueChangedEvent<GradeOverride>) => {
      const { data, colDef, newValue } = event
      if (!data || !colDef.field) return
      const field = colDef.field
      const parsed = newValue === '' || newValue == null ? null : Number(newValue)

      const updated = rows.map((r) => {
        if (r.level_id !== data.level_id) return r
        if (field === 'retention_rate') return { ...r, retention_rate: parsed }
        if (field === 'lateral_entry') return { ...r, lateral_entry: parsed }
        if (field === 'max_divisions') return { ...r, max_divisions: parsed }
        if (field === 'class_size_ceiling') return { ...r, class_size_ceiling: parsed }
        return r
      })
      onChange(updated)
    },
    [rows, onChange]
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span>Grade-Level Overrides</span>
          <HelpTooltip
            field={{
              label: 'Grade Overrides',
              description: 'Fine-tune enrollment parameters for each individual grade level.',
              why: 'Different grades may have different retention patterns, transfer rates, or capacity constraints.',
              example:
                'PS (Petite Section) might have higher lateral entry due to new families joining.',
            }}
          />
        </CardTitle>
        <p className="text-sm text-text-secondary mt-1">
          Click on a cell to edit. Leave empty to use cycle-level or scenario defaults.
        </p>
      </CardHeader>
      <CardContent>
        {/* Legend for field meanings */}
        <div className="flex flex-wrap gap-4 mb-4 text-xs text-text-secondary">
          <span className="flex items-center gap-1">
            <HelpTooltip field={ENROLLMENT_FIELDS.grade_retention_rate} size="sm" />
            <span>Retention = % students staying</span>
          </span>
          <span className="flex items-center gap-1">
            <HelpTooltip field={ENROLLMENT_FIELDS.grade_lateral_entry} size="sm" />
            <span>Transfers = new students mid-year</span>
          </span>
          <span className="flex items-center gap-1">
            <HelpTooltip field={ENROLLMENT_FIELDS.max_divisions} size="sm" />
            <span>Max Classes = class sections limit</span>
          </span>
          <span className="flex items-center gap-1">
            <HelpTooltip field={ENROLLMENT_FIELDS.class_size_ceiling} size="sm" />
            <span>Max Size = students per class limit</span>
          </span>
        </div>

        <div className="w-full">
          <DataTableLazy
            rowData={rows}
            columnDefs={columnDefs}
            onCellValueChanged={onCellValueChanged}
            domLayout="autoHeight"
            pagination={false}
            defaultColDef={{
              resizable: true,
              sortable: false,
            }}
            getRowId={(p) => p.data.level_id}
            tooltipShowDelay={200}
          />
        </div>
      </CardContent>
    </Card>
  )
})
