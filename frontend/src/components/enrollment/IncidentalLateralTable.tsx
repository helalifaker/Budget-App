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
import type { IncidentalLateral, ParameterOverrideUpdate } from '@/types/enrollmentSettings'

interface IncidentalLateralTableProps {
  entries: IncidentalLateral[]
  onUpdate: (update: ParameterOverrideUpdate) => void
  disabled?: boolean
}

const GRADE_INFO: Record<string, { cycle: string; order: number }> = {
  CE1: { cycle: 'ELEM', order: 1 },
  CE2: { cycle: 'ELEM', order: 2 },
  CM1: { cycle: 'ELEM', order: 3 },
  CM2: { cycle: 'ELEM', order: 4 },
  '5EME': { cycle: 'COLL', order: 5 },
  '4EME': { cycle: 'COLL', order: 6 },
  '3EME': { cycle: 'COLL', order: 7 },
  '1ERE': { cycle: 'LYC', order: 8 },
  TLE: { cycle: 'LYC', order: 9 },
}

const CYCLE_COLORS: Record<string, string> = {
  ELEM: 'bg-green-500',
  COLL: 'bg-blue-500',
  LYC: 'bg-purple-500',
}

const CONFIDENCE_BADGE: Record<string, { className: string }> = {
  high: { className: 'bg-green-100 text-green-700 border-green-200' },
  medium: { className: 'bg-amber-100 text-amber-700 border-amber-200' },
  low: { className: 'bg-red-50 text-red-600 border-red-200' },
}

/**
 * IncidentalLateralTable - Configure fixed lateral entry values for non-entry-point grades.
 *
 * Incidental lateral grades (CE1-CM2, 5EME-3EME, 1ERE, TLE) use fixed values
 * rather than percentage-based calculations. These are typically smaller,
 * less predictable movements.
 *
 * Displays:
 * - Derived values from historical calibration
 * - Override toggle to enable manual values
 * - Effective value used in projections
 */
export const IncidentalLateralTable = memo(function IncidentalLateralTable({
  entries,
  onUpdate,
  disabled = false,
}: IncidentalLateralTableProps) {
  const [editingGrade, setEditingGrade] = useState<string | null>(null)
  const [editValue, setEditValue] = useState<string>('')

  const startEditing = useCallback((entry: IncidentalLateral) => {
    setEditingGrade(entry.grade_code)
    setEditValue(String(entry.manual_value ?? entry.derived_value ?? entry.effective_value))
  }, [])

  const cancelEditing = useCallback(() => {
    setEditingGrade(null)
    setEditValue('')
  }, [])

  const saveEditing = useCallback(
    (gradeCode: string) => {
      const value = parseInt(editValue, 10)

      if (!isNaN(value) && value >= 0) {
        onUpdate({
          grade_code: gradeCode,
          override_fixed_lateral: true,
          manual_fixed_lateral: value,
        })
      }
      setEditingGrade(null)
    },
    [editValue, onUpdate]
  )

  const toggleOverride = useCallback(
    (entry: IncidentalLateral, enabled: boolean) => {
      onUpdate({
        grade_code: entry.grade_code,
        override_fixed_lateral: enabled,
        manual_fixed_lateral: enabled ? entry.effective_value : null,
      })
    },
    [onUpdate]
  )

  // Group by cycle
  const groupedEntries = entries.reduce(
    (acc, entry) => {
      const cycle = GRADE_INFO[entry.grade_code]?.cycle || 'OTHER'
      if (!acc[cycle]) acc[cycle] = []
      acc[cycle].push(entry)
      return acc
    },
    {} as Record<string, IncidentalLateral[]>
  )

  // Sort within each group
  Object.values(groupedEntries).forEach((group) => {
    group.sort(
      (a, b) => (GRADE_INFO[a.grade_code]?.order || 0) - (GRADE_INFO[b.grade_code]?.order || 0)
    )
  })

  const renderRow = (entry: IncidentalLateral) => {
    const isEditing = editingGrade === entry.grade_code
    const confidenceBadge = CONFIDENCE_BADGE[entry.confidence]

    return (
      <TableRow key={entry.grade_code}>
        <TableCell className="font-medium">{entry.grade_code}</TableCell>
        <TableCell>
          {entry.derived_value !== null ? (
            <div className="flex items-center gap-2">
              <span>{entry.derived_value}</span>
              <Badge variant="outline" className={cn('text-xs', confidenceBadge.className)}>
                {entry.confidence}
              </Badge>
            </div>
          ) : (
            <span className="text-muted-foreground italic">Default</span>
          )}
        </TableCell>
        <TableCell>
          <Switch
            checked={entry.override_enabled}
            onCheckedChange={(checked) => toggleOverride(entry, checked)}
            disabled={disabled}
          />
        </TableCell>
        <TableCell>
          {isEditing ? (
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-20 h-8"
                min="0"
                max="100"
              />
            </div>
          ) : entry.override_enabled ? (
            <span className="font-medium">{entry.manual_value}</span>
          ) : (
            <span className="text-muted-foreground">-</span>
          )}
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <span
              className={cn(
                'font-semibold',
                entry.override_enabled ? 'text-blue-600' : 'text-foreground'
              )}
            >
              {entry.effective_value}
            </span>
            {entry.override_enabled && (
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
              <Button size="sm" variant="ghost" onClick={() => saveEditing(entry.grade_code)}>
                <Check className="h-4 w-4 text-green-600" />
              </Button>
            </div>
          ) : (
            <Button
              size="sm"
              variant="ghost"
              onClick={() => startEditing(entry)}
              disabled={disabled || !entry.override_enabled}
            >
              <Edit2 className="h-4 w-4" />
            </Button>
          )}
        </TableCell>
      </TableRow>
    )
  }

  const renderCycleTable = (cycle: string, cycleEntries: IncidentalLateral[]) => (
    <div key={cycle}>
      <h4 className="text-sm font-semibold text-muted-foreground mb-2 flex items-center gap-2">
        <div className={cn('w-2 h-2 rounded-full', CYCLE_COLORS[cycle] || 'bg-gray-500')} />
        {cycle === 'ELEM'
          ? 'Elementary (CE1-CM2)'
          : cycle === 'COLL'
            ? 'Collège (5ème-3ème)'
            : cycle === 'LYC'
              ? 'Lycée (1ère, Terminale)'
              : cycle}
      </h4>
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="w-[100px]">Grade</TableHead>
              <TableHead>Derived Value</TableHead>
              <TableHead className="w-[80px]">Override</TableHead>
              <TableHead>Manual Value</TableHead>
              <TableHead>Effective Value</TableHead>
              <TableHead className="w-[80px]">Actions</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>{cycleEntries.map(renderRow)}</TableBody>
        </Table>
      </div>
    </div>
  )

  return (
    <div className="space-y-6">
      {Object.entries(groupedEntries)
        .sort(([a], [b]) => {
          const order = { ELEM: 1, COLL: 2, LYC: 3 }
          return (order[a as keyof typeof order] || 99) - (order[b as keyof typeof order] || 99)
        })
        .map(([cycle, cycleEntries]) => renderCycleTable(cycle, cycleEntries))}
    </div>
  )
})
