import { memo, useState, useCallback } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Edit2, X, Check } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { EntryPointRate, ParameterOverrideUpdate } from '@/types/enrollment-settings'

interface EntryPointRatesTableProps {
  rates: EntryPointRate[]
  onUpdate: (update: ParameterOverrideUpdate) => void
  disabled?: boolean
}

const GRADE_LABELS: Record<string, { name: string; description: string }> = {
  MS: { name: 'Moyenne Section', description: 'Maternelle entry (+42% lateral)' },
  GS: { name: 'Grande Section', description: 'Maternelle transition (+27%)' },
  CP: { name: 'CP', description: 'Elementary entry (+14%)' },
  '6EME': { name: '6ème', description: 'Collège entry (+9%)' },
  '2NDE': { name: '2nde', description: 'Lycée entry (+10%)' },
}

const CONFIDENCE_BADGE: Record<
  string,
  { variant: 'default' | 'secondary' | 'outline'; className: string }
> = {
  high: { variant: 'default', className: 'bg-green-100 text-green-700 border-green-200' },
  medium: { variant: 'secondary', className: 'bg-amber-100 text-amber-700 border-amber-200' },
  low: { variant: 'outline', className: 'bg-red-50 text-red-600 border-red-200' },
}

/**
 * EntryPointRatesTable - Configure lateral entry rates for entry point grades.
 *
 * Entry point grades (MS, GS, CP, 6EME, 2NDE) use percentage-based lateral entry,
 * meaning lateral entry is calculated as a percentage of the previous grade's enrollment.
 *
 * Displays:
 * - Derived rates from historical calibration
 * - Override toggle to enable manual rates
 * - Effective rate used in projections
 * - Confidence level for derived values
 */
export const EntryPointRatesTable = memo(function EntryPointRatesTable({
  rates,
  onUpdate,
  disabled = false,
}: EntryPointRatesTableProps) {
  const [editingGrade, setEditingGrade] = useState<string | null>(null)
  const [editValues, setEditValues] = useState<{ rate: string; retention: string }>({
    rate: '',
    retention: '',
  })

  const startEditing = useCallback((rate: EntryPointRate) => {
    setEditingGrade(rate.grade_code)
    // Get rate value with fallback chain, ensuring we have a valid number
    const rateValue = rate.manual_rate ?? rate.derived_rate ?? rate.effective_rate ?? 0
    const retentionValue =
      rate.manual_retention ?? rate.derived_retention ?? rate.effective_retention ?? 0
    setEditValues({
      // Multiply by 100 AFTER the nullish coalescing to convert decimal to percentage
      rate: (Number(rateValue) * 100).toFixed(1),
      retention: (Number(retentionValue) * 100).toFixed(1),
    })
  }, [])

  const cancelEditing = useCallback(() => {
    setEditingGrade(null)
    setEditValues({ rate: '', retention: '' })
  }, [])

  const saveEditing = useCallback(
    (gradeCode: string) => {
      const rateValue = parseFloat(editValues.rate)
      const retentionValue = parseFloat(editValues.retention)

      if (!isNaN(rateValue) && !isNaN(retentionValue)) {
        onUpdate({
          grade_code: gradeCode,
          override_lateral_rate: true,
          override_retention_rate: true,
          manual_lateral_rate: rateValue / 100, // Convert percentage to decimal
          manual_retention_rate: retentionValue / 100,
        })
      }
      setEditingGrade(null)
    },
    [editValues, onUpdate]
  )

  const toggleOverride = useCallback(
    (rate: EntryPointRate, enabled: boolean) => {
      onUpdate({
        grade_code: rate.grade_code,
        override_lateral_rate: enabled,
        override_retention_rate: enabled,
        manual_lateral_rate: enabled ? rate.effective_rate : null,
        manual_retention_rate: enabled ? rate.effective_retention : null,
      })
    },
    [onUpdate]
  )

  const formatPercent = (value: number | null) => {
    if (value === null) return '-'
    return `${(value * 100).toFixed(1)}%`
  }

  // Group by category
  const maternelleFunnel = rates.filter((r) => r.category === 'maternelle_funnel')
  const cycleTransitions = rates.filter((r) => r.category === 'cycle_transition')

  const renderRow = (rate: EntryPointRate) => {
    const isEditing = editingGrade === rate.grade_code
    const label = GRADE_LABELS[rate.grade_code] || { name: rate.grade_code, description: '' }
    const confidenceBadge = CONFIDENCE_BADGE[rate.confidence]

    return (
      <TableRow key={rate.grade_code}>
        <TableCell>
          <div>
            <div className="font-medium">{label.name}</div>
            <div className="text-xs text-muted-foreground">{label.description}</div>
          </div>
        </TableCell>
        <TableCell>
          {rate.derived_rate !== null ? (
            <div className="flex items-center gap-2">
              <span>{formatPercent(rate.derived_rate)}</span>
              <Badge variant="outline" className={cn('text-xs', confidenceBadge.className)}>
                {rate.confidence}
              </Badge>
            </div>
          ) : (
            <span className="text-muted-foreground italic">No data</span>
          )}
        </TableCell>
        <TableCell>
          <Switch
            checked={rate.override_enabled}
            onCheckedChange={(checked) => toggleOverride(rate, checked)}
            disabled={disabled}
          />
        </TableCell>
        <TableCell>
          {isEditing ? (
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={editValues.rate}
                onChange={(e) => setEditValues((prev) => ({ ...prev, rate: e.target.value }))}
                className="w-20 h-8"
                step="0.1"
                min="0"
                max="100"
              />
              <span className="text-sm text-muted-foreground">%</span>
            </div>
          ) : rate.override_enabled ? (
            <span className="font-medium">{formatPercent(rate.manual_rate)}</span>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'font-semibold',
                rate.override_enabled ? 'text-blue-600' : 'text-foreground'
              )}
            >
              {formatPercent(rate.effective_rate)}
            </span>
            {rate.override_enabled && (
              <Badge variant="outline" className="text-xs bg-blue-50 text-blue-600 border-blue-200">
                Override
              </Badge>
            )}
          </div>
        </TableCell>
        <TableCell>
          {isEditing ? (
            <div className="flex items-center gap-1">
              <Button size="sm" variant="ghost" onClick={cancelEditing}>
                <X className="h-4 w-4" />
              </Button>
              <Button size="sm" variant="ghost" onClick={() => saveEditing(rate.grade_code)}>
                <Check className="h-4 w-4 text-green-600" />
              </Button>
            </div>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => startEditing(rate)}
              disabled={disabled || !rate.override_enabled}
            >
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
        </TableCell>
      </TableRow>
    )
  }

  return (
    <div className="space-y-6">
      {/* Maternelle Funnel */}
      {maternelleFunnel.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-purple-500" />
            Maternelle Funnel
          </h4>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-[180px]">Grade</TableHead>
                  <TableHead>Derived Rate</TableHead>
                  <TableHead className="w-[80px]">Override</TableHead>
                  <TableHead>Manual Rate</TableHead>
                  <TableHead>Effective Rate</TableHead>
                  <TableHead className="w-[80px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>{maternelleFunnel.map(renderRow)}</TableBody>
            </Table>
          </div>
        </div>
      )}

      {/* Cycle Transitions */}
      {cycleTransitions.length > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
            <div className="w-2 h-2 rounded-full bg-blue-500" />
            Cycle Entry Points
          </h4>
          <div className="border rounded-lg overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50">
                  <TableHead className="w-[180px]">Grade</TableHead>
                  <TableHead>Derived Rate</TableHead>
                  <TableHead className="w-[80px]">Override</TableHead>
                  <TableHead>Manual Rate</TableHead>
                  <TableHead>Effective Rate</TableHead>
                  <TableHead className="w-[80px]">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>{cycleTransitions.map(renderRow)}</TableBody>
            </Table>
          </div>
        </div>
      )}
    </div>
  )
})
