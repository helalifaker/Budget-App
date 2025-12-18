import { memo, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { FieldLabel, FieldHint } from '@/components/ui/HelpTooltip'
import { ENROLLMENT_FIELDS } from '@/constants/enrollment-field-definitions'
import type { LevelOverride } from '@/types/enrollment-projection'
import { SLIDER_CONFIGS } from '@/types/enrollment-projection'

interface CycleLike {
  id: string
  code: string
  name_fr?: string | null
  name_en?: string | null
}

interface LevelOverridesPanelProps {
  cycles: CycleLike[]
  overrides: LevelOverride[]
  onChange: (overrides: LevelOverride[]) => void
  disabled?: boolean
}

/**
 * LevelOverridesPanel - Cycle-level (school level) adjustment fields
 *
 * Allows setting class size ceiling and max divisions per cycle:
 * - Maternelle (Preschool)
 * - Élémentaire (Elementary)
 * - Collège (Middle School)
 * - Lycée (High School)
 *
 * This panel should be placed inside AdvancedFeaturesSection
 * as it's an advanced configuration option.
 */
export const LevelOverridesPanel = memo(function LevelOverridesPanel({
  cycles,
  overrides,
  onChange,
  disabled,
}: LevelOverridesPanelProps) {
  // PERFORMANCE FIX: Memoize rows computation
  const rows: LevelOverride[] = useMemo(
    () =>
      cycles.map((c) => {
        const existing = overrides.find((o) => o.cycle_id === c.id)
        return (
          existing ?? {
            cycle_id: c.id,
            cycle_code: c.code,
            cycle_name: c.name_fr || c.name_en || c.code,
            class_size_ceiling: null,
            max_divisions: null,
          }
        )
      }),
    [cycles, overrides]
  )

  // PERFORMANCE FIX: Memoize updateRow to prevent child re-renders
  const updateRow = useCallback(
    (cycleId: string, patch: Partial<LevelOverride>) => {
      const next = rows.map((r) => (r.cycle_id === cycleId ? { ...r, ...patch } : r))
      onChange(next)
    },
    [rows, onChange]
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle>Cycle-Level Overrides</CardTitle>
        <p className="text-sm text-text-secondary mt-1">
          Set limits per school level (cycle). These apply to all grades within each cycle.
        </p>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Column headers with tooltips */}
        <div className="hidden md:grid md:grid-cols-3 gap-3 pb-2 border-b border-border-light">
          <div className="text-xs font-medium text-text-secondary uppercase tracking-wider">
            Cycle
          </div>
          <FieldLabel field={ENROLLMENT_FIELDS.cycle_class_size_ceiling} short />
          <FieldLabel field={ENROLLMENT_FIELDS.cycle_max_divisions} short />
        </div>

        {rows.map((row) => (
          <div key={row.cycle_id} className="grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
            <div className="text-sm font-medium text-text-primary">{row.cycle_name}</div>
            <div className="space-y-1">
              <div className="text-xs text-text-secondary md:hidden">Class Size Ceiling</div>
              <Input
                type="number"
                min={SLIDER_CONFIGS.classSize.min}
                max={SLIDER_CONFIGS.classSize.max}
                step={1}
                value={row.class_size_ceiling ?? ''}
                onChange={(e) =>
                  updateRow(row.cycle_id, {
                    class_size_ceiling: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
                disabled={disabled}
                placeholder="28"
              />
              <FieldHint field={ENROLLMENT_FIELDS.cycle_class_size_ceiling} className="md:hidden" />
            </div>
            <div className="space-y-1">
              <div className="text-xs text-text-secondary md:hidden">Max Divisions</div>
              <Input
                type="number"
                min={2}
                max={10}
                step={1}
                value={row.max_divisions ?? ''}
                onChange={(e) =>
                  updateRow(row.cycle_id, {
                    max_divisions: e.target.value === '' ? null : Number(e.target.value),
                  })
                }
                disabled={disabled}
                placeholder="6"
              />
              <FieldHint field={ENROLLMENT_FIELDS.cycle_max_divisions} className="md:hidden" />
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
})
