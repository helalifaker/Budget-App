import { memo, useCallback, useMemo, useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { FieldLabel, FieldHint } from '@/components/ui/HelpTooltip'
import { ENROLLMENT_FIELDS } from '@/constants/enrollment-field-definitions'
import type { GlobalOverrides, EnrollmentScenario } from '@/types/enrollment-projection'
import { SLIDER_CONFIGS } from '@/types/enrollment-projection'

interface BasicOverridesPanelProps {
  overrides: GlobalOverrides | null
  onChange: (updates: Partial<GlobalOverrides>) => void
  disabled?: boolean
  /** Selected scenario to show base values as reference */
  selectedScenario?: EnrollmentScenario | null
}

/**
 * PS Entry Slider Field with local state for smooth UI during drag
 */
interface PsEntrySliderFieldProps {
  basePsEntry: number
  psEntryAdjustment: number
  onChange: (updates: Partial<GlobalOverrides>) => void
  disabled?: boolean
}

function PsEntrySliderField({
  basePsEntry,
  psEntryAdjustment,
  onChange,
  disabled,
}: PsEntrySliderFieldProps) {
  // Local state for immediate display feedback during dragging
  const [localAdjustment, setLocalAdjustment] = useState(psEntryAdjustment)

  // Sync local state when external value changes (e.g., reset button)
  useEffect(() => {
    setLocalAdjustment(psEntryAdjustment)
  }, [psEntryAdjustment])

  const localFinalValue = basePsEntry + localAdjustment

  return (
    <div className="space-y-2">
      <FieldLabel field={ENROLLMENT_FIELDS.ps_entry_adjustment} />

      {/* Base reference */}
      <div className="text-xs text-text-secondary">
        Scenario base: <span className="font-medium text-text-primary">{basePsEntry} students</span>
      </div>

      {/* Slider */}
      <div className="flex items-center gap-4">
        <Slider
          min={SLIDER_CONFIGS.psEntryAdjustment.min}
          max={SLIDER_CONFIGS.psEntryAdjustment.max}
          step={SLIDER_CONFIGS.psEntryAdjustment.step}
          value={[localAdjustment]}
          // Update local state immediately for smooth UI
          onValueChange={([v]) => setLocalAdjustment(v)}
          // Only trigger API call when user releases the slider
          onValueCommit={([v]) =>
            onChange({
              ps_entry_adjustment: v === 0 ? null : v,
            })
          }
          disabled={disabled}
          className="flex-1"
        />
        <span className="w-16 text-right font-medium tabular-nums">
          {localAdjustment > 0 ? '+' : ''}
          {localAdjustment}
        </span>
      </div>

      {/* Final value */}
      <div className="text-xs">
        <span className="text-text-secondary">Result: </span>
        <span className="font-semibold text-sage">{localFinalValue} students</span>
      </div>

      <FieldHint field={ENROLLMENT_FIELDS.ps_entry_adjustment} />
    </div>
  )
}

/**
 * Retention Slider Field with local state for smooth UI during drag
 */
interface RetentionSliderFieldProps {
  baseRetention: number
  retentionAdjustment: number
  onChange: (updates: Partial<GlobalOverrides>) => void
  disabled?: boolean
}

function RetentionSliderField({
  baseRetention,
  retentionAdjustment,
  onChange,
  disabled,
}: RetentionSliderFieldProps) {
  // Local state for immediate display feedback during dragging (in percentage)
  const [localAdjustmentPct, setLocalAdjustmentPct] = useState(
    Math.round(retentionAdjustment * 100)
  )

  // Sync local state when external value changes (e.g., reset button)
  useEffect(() => {
    setLocalAdjustmentPct(Math.round(retentionAdjustment * 100))
  }, [retentionAdjustment])

  const localFinalRetentionPct = Math.round(baseRetention * 100) + localAdjustmentPct

  return (
    <div className="space-y-2">
      <FieldLabel field={ENROLLMENT_FIELDS.retention_adjustment} />

      {/* Base reference */}
      <div className="text-xs text-text-secondary">
        Scenario base:{' '}
        <span className="font-medium text-text-primary">
          {Math.round(baseRetention * 100)}% retention
        </span>
      </div>

      {/* Slider */}
      <div className="flex items-center gap-4">
        <Slider
          min={Math.round(SLIDER_CONFIGS.retentionAdjustment.min * 100)}
          max={Math.round(SLIDER_CONFIGS.retentionAdjustment.max * 100)}
          step={Math.round(SLIDER_CONFIGS.retentionAdjustment.step * 100)}
          value={[localAdjustmentPct]}
          // Update local state immediately for smooth UI
          onValueChange={([v]) => setLocalAdjustmentPct(v)}
          // Only trigger API call when user releases the slider
          onValueCommit={([v]) =>
            onChange({
              retention_adjustment: v === 0 ? null : v / 100,
            })
          }
          disabled={disabled}
          className="flex-1"
        />
        <span className="w-16 text-right font-medium tabular-nums">
          {localAdjustmentPct > 0 ? '+' : ''}
          {localAdjustmentPct}%
        </span>
      </div>

      {/* Final value */}
      <div className="text-xs">
        <span className="text-text-secondary">Result: </span>
        <span className="font-semibold text-sage">{localFinalRetentionPct}%</span>
      </div>

      <FieldHint field={ENROLLMENT_FIELDS.retention_adjustment} />
    </div>
  )
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
  selectedScenario,
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

  // Base values from selected scenario (ensure numeric conversion - API may return strings)
  const basePsEntry = Number(selectedScenario?.ps_entry) || 0
  const baseRetention = Number(selectedScenario?.default_retention) || 0.96

  // Get adjustment values (actual final values computed in child components for smooth drag UX)
  const psEntryAdjustment = current.ps_entry_adjustment ?? 0
  const retentionAdjustment = current.retention_adjustment ?? 0

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
        {/* PS Entry Adjustment - Slider showing variation from base */}
        <PsEntrySliderField
          basePsEntry={basePsEntry}
          psEntryAdjustment={psEntryAdjustment}
          onChange={onChange}
          disabled={disabled}
        />

        {/* Retention Adjustment - Slider showing variation from base */}
        <RetentionSliderField
          baseRetention={baseRetention}
          retentionAdjustment={retentionAdjustment}
          onChange={onChange}
          disabled={disabled}
        />
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
