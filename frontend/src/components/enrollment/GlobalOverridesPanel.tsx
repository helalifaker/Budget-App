import { memo, useCallback, useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { FieldLabel, FieldHint } from '@/components/ui/HelpTooltip'
import { ENROLLMENT_FIELDS } from '@/constants/enrollment-field-definitions'
import type { GlobalOverrides } from '@/types/enrollmentProjection'
import { SLIDER_CONFIGS } from '@/types/enrollmentProjection'

interface BasicOverridesPanelProps {
  overrides: GlobalOverrides | null
  onChange: (updates: Partial<GlobalOverrides>) => void
  disabled?: boolean
}

/**
 * BasicOverridesPanel - Essential adjustment fields for enrollment projections
 *
 * Shows only the basic fields that most users need:
 * - PS Entry Adjustment (new preschool students)
 * - Retention Adjustment (student retention rate)
 *
 * Advanced fields (lateral multiplier, class size override) are in
 * AdvancedOverridesPanel, shown behind the acknowledgment toggle.
 */
export const BasicOverridesPanel = memo(function BasicOverridesPanel({
  overrides,
  onChange,
  disabled,
}: BasicOverridesPanelProps) {
  const current = useMemo(
    () =>
      overrides ?? {
        ps_entry_adjustment: null,
        retention_adjustment: null,
        lateral_multiplier_override: null,
        class_size_override: null,
      },
    [overrides]
  )

  const resetBasic = useCallback(
    () =>
      onChange({
        ps_entry_adjustment: null,
        retention_adjustment: null,
      }),
    [onChange]
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Basic Adjustments</span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={resetBasic}
            disabled={disabled}
          >
            Reset
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* PS Entry Adjustment - Basic Field */}
        <div className="space-y-1.5">
          <FieldLabel field={ENROLLMENT_FIELDS.ps_entry_adjustment} />
          <Input
            type="number"
            min={SLIDER_CONFIGS.psEntryAdjustment.min}
            max={SLIDER_CONFIGS.psEntryAdjustment.max}
            step={SLIDER_CONFIGS.psEntryAdjustment.step}
            value={current.ps_entry_adjustment ?? ''}
            onChange={(e) =>
              onChange({
                ps_entry_adjustment: e.target.value === '' ? null : Number(e.target.value),
              })
            }
            disabled={disabled}
            placeholder="0"
            className="w-full"
          />
          <FieldHint field={ENROLLMENT_FIELDS.ps_entry_adjustment} />
        </div>

        {/* Retention Adjustment - Basic Field */}
        <div className="space-y-1.5">
          <FieldLabel field={ENROLLMENT_FIELDS.retention_adjustment} />
          <Input
            type="number"
            min={SLIDER_CONFIGS.retentionAdjustment.min}
            max={SLIDER_CONFIGS.retentionAdjustment.max}
            step={SLIDER_CONFIGS.retentionAdjustment.step}
            value={current.retention_adjustment ?? ''}
            onChange={(e) =>
              onChange({
                retention_adjustment: e.target.value === '' ? null : Number(e.target.value),
              })
            }
            disabled={disabled}
            placeholder="0.00"
            className="w-full"
          />
          <FieldHint field={ENROLLMENT_FIELDS.retention_adjustment} />
        </div>
      </CardContent>
    </Card>
  )
})

interface AdvancedOverridesPanelProps {
  overrides: GlobalOverrides | null
  onChange: (updates: Partial<GlobalOverrides>) => void
  disabled?: boolean
}

/**
 * AdvancedOverridesPanel - Power-user adjustment fields
 *
 * Shows advanced global fields for fine-tuning projections:
 * - Transfer Students Factor (lateral multiplier)
 * - Default Class Size override
 *
 * This panel should be placed inside AdvancedFeaturesSection
 * to require user acknowledgment before editing.
 */
export const AdvancedOverridesPanel = memo(function AdvancedOverridesPanel({
  overrides,
  onChange,
  disabled,
}: AdvancedOverridesPanelProps) {
  const current = useMemo(
    () =>
      overrides ?? {
        ps_entry_adjustment: null,
        retention_adjustment: null,
        lateral_multiplier_override: null,
        class_size_override: null,
      },
    [overrides]
  )

  const resetAdvanced = useCallback(
    () =>
      onChange({
        lateral_multiplier_override: null,
        class_size_override: null,
      }),
    [onChange]
  )

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Global Advanced Overrides</span>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={resetAdvanced}
            disabled={disabled}
          >
            Reset
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Lateral Multiplier Override - Advanced Field */}
        <div className="space-y-1.5">
          <FieldLabel field={ENROLLMENT_FIELDS.lateral_multiplier} />
          <Input
            type="number"
            min={SLIDER_CONFIGS.lateralMultiplier.min}
            max={SLIDER_CONFIGS.lateralMultiplier.max}
            step={SLIDER_CONFIGS.lateralMultiplier.step}
            value={current.lateral_multiplier_override ?? ''}
            onChange={(e) =>
              onChange({
                lateral_multiplier_override: e.target.value === '' ? null : Number(e.target.value),
              })
            }
            disabled={disabled}
            placeholder="1.0"
            className="w-full"
          />
          <FieldHint field={ENROLLMENT_FIELDS.lateral_multiplier} />
        </div>

        {/* Class Size Override - Advanced Field */}
        <div className="space-y-1.5">
          <FieldLabel field={ENROLLMENT_FIELDS.class_size_override} />
          <Input
            type="number"
            min={SLIDER_CONFIGS.classSize.min}
            max={SLIDER_CONFIGS.classSize.max}
            step={SLIDER_CONFIGS.classSize.step}
            value={current.class_size_override ?? ''}
            onChange={(e) =>
              onChange({
                class_size_override: e.target.value === '' ? null : Number(e.target.value),
              })
            }
            disabled={disabled}
            placeholder="25"
            className="w-full"
          />
          <FieldHint field={ENROLLMENT_FIELDS.class_size_override} />
        </div>
      </CardContent>
    </Card>
  )
})

// Re-export for backwards compatibility during migration
export const GlobalOverridesPanel = BasicOverridesPanel
