/**
 * UnifiedLateralTable - Lateral Entry Configuration for School Directors
 *
 * A clear, simple table showing lateral entry rates for all 14 grades.
 * Designed to be understandable by school administrators (not engineers).
 *
 * Key concepts:
 * - Calibrated Rate: Calculated from historical data (70% last year + 30% previous year)
 * - Override: Enable to set your own custom rate
 * - Growth Rate: How enrollment grows grade-to-grade = Retention × (1 + Lateral)
 *
 * Example: If 100 students in CP and growth rate is 104.5%:
 *   → Expect ~105 students in CE1 next year
 */

import { memo, useState, useCallback, useMemo } from 'react'
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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import { Edit2, X, Check, DoorOpen, HelpCircle, TrendingUp, TrendingDown } from 'lucide-react'
import { cn } from '@/lib/utils'
import { CYCLE_RETENTION_RATES, UNIFIED_LATERAL_DEFAULTS } from '@/types/enrollment-projection'
import type {
  EntryPointRate,
  IncidentalLateral,
  ParameterOverrideUpdate,
} from '@/types/enrollment-settings'

// =============================================================================
// Types
// =============================================================================

interface UnifiedLateralTableProps {
  entryPointRates: EntryPointRate[]
  incidentalLateral: IncidentalLateral[]
  onUpdate: (update: ParameterOverrideUpdate) => void
  disabled?: boolean
}

interface GradeRow {
  grade_code: string
  grade_name: string
  cycle_code: string
  cycle_name: string
  is_entry_point: boolean

  // Calibrated values (from historical analysis)
  calibrated_lateral: number
  base_retention: number

  // Override state
  has_override: boolean
  override_lateral: number | null

  // Effective values (what will be used)
  effective_lateral: number
  effective_retention: number
  growth_rate: number

  // Metadata
  confidence: 'high' | 'medium' | 'low'
}

// =============================================================================
// Grade Configuration - French School System
// =============================================================================

const GRADE_CONFIG: Record<
  string,
  { name: string; cycle: string; cycleName: string; order: number }
> = {
  MS: { name: 'Moyenne Section', cycle: 'MAT', cycleName: 'Maternelle', order: 1 },
  GS: { name: 'Grande Section', cycle: 'MAT', cycleName: 'Maternelle', order: 2 },
  CP: { name: 'Cours Préparatoire', cycle: 'ELEM', cycleName: 'Élémentaire', order: 3 },
  CE1: { name: 'Cours Élémentaire 1', cycle: 'ELEM', cycleName: 'Élémentaire', order: 4 },
  CE2: { name: 'Cours Élémentaire 2', cycle: 'ELEM', cycleName: 'Élémentaire', order: 5 },
  CM1: { name: 'Cours Moyen 1', cycle: 'ELEM', cycleName: 'Élémentaire', order: 6 },
  CM2: { name: 'Cours Moyen 2', cycle: 'ELEM', cycleName: 'Élémentaire', order: 7 },
  '6EME': { name: 'Sixième', cycle: 'COLL', cycleName: 'Collège', order: 8 },
  '5EME': { name: 'Cinquième', cycle: 'COLL', cycleName: 'Collège', order: 9 },
  '4EME': { name: 'Quatrième', cycle: 'COLL', cycleName: 'Collège', order: 10 },
  '3EME': { name: 'Troisième', cycle: 'COLL', cycleName: 'Collège', order: 11 },
  '2NDE': { name: 'Seconde', cycle: 'LYC', cycleName: 'Lycée', order: 12 },
  '1ERE': { name: 'Première', cycle: 'LYC', cycleName: 'Lycée', order: 13 },
  TLE: { name: 'Terminale', cycle: 'LYC', cycleName: 'Lycée', order: 14 },
}

const ENTRY_POINTS = new Set(['MS', 'GS', 'CP', '6EME', '2NDE'])

const CYCLE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  MAT: { bg: 'bg-purple-50', text: 'text-purple-700', border: 'border-purple-200' },
  ELEM: { bg: 'bg-green-50', text: 'text-green-700', border: 'border-green-200' },
  COLL: { bg: 'bg-blue-50', text: 'text-blue-700', border: 'border-blue-200' },
  LYC: { bg: 'bg-amber-50', text: 'text-amber-700', border: 'border-amber-200' },
}

const CONFIDENCE_COLORS: Record<string, string> = {
  high: 'bg-green-100 text-green-700',
  medium: 'bg-amber-100 text-amber-700',
  low: 'bg-red-100 text-red-700',
}

// =============================================================================
// Helper Functions
// =============================================================================

/**
 * Build unified grade rows from API data + defaults.
 * Uses UNIFIED_LATERAL_DEFAULTS as the source of truth for calibrated values.
 */
function buildGradeRows(
  entryPointRates: EntryPointRate[],
  incidentalLateral: IncidentalLateral[]
): GradeRow[] {
  const rows: GradeRow[] = []

  // Create a map of API data for quick lookup
  const entryPointMap = new Map(entryPointRates.map((r) => [r.grade_code, r]))
  const incidentalMap = new Map(incidentalLateral.map((r) => [r.grade_code, r]))

  // Process all 14 grades in order
  for (const [gradeCode, config] of Object.entries(GRADE_CONFIG)) {
    const defaults = UNIFIED_LATERAL_DEFAULTS[gradeCode]
    const cycleRetention =
      CYCLE_RETENTION_RATES[config.cycle as keyof typeof CYCLE_RETENTION_RATES] ?? 0.96

    // Get calibrated values from defaults (source of truth)
    const calibratedLateral = defaults?.lateral_rate ?? 0
    const baseRetention = defaults?.retention_rate ?? cycleRetention

    // Check for override in API data
    let hasOverride = false
    let overrideLateral: number | null = null
    let confidence: 'high' | 'medium' | 'low' = 'high'

    const entryPointData = entryPointMap.get(gradeCode)
    const incidentalData = incidentalMap.get(gradeCode)

    if (entryPointData) {
      hasOverride = entryPointData.override_enabled
      // Convert API percentage (if stored as 0.20 for 20%) to our format
      overrideLateral = entryPointData.manual_rate
      confidence = entryPointData.confidence
    } else if (incidentalData) {
      hasOverride = incidentalData.override_enabled
      // For incidental, manual_value might be a fixed count - convert to percentage
      // Using derived_retention as a proxy for the lateral rate in the unified model
      overrideLateral = incidentalData.manual_retention
      confidence = incidentalData.confidence
    }

    // Calculate effective values
    const effectiveLateral =
      hasOverride && overrideLateral !== null ? overrideLateral : calibratedLateral
    const effectiveRetention = baseRetention // Retention is always from cycle defaults

    // Growth rate = Retention × (1 + Lateral Rate)
    const growthRate = effectiveRetention * (1 + effectiveLateral)

    rows.push({
      grade_code: gradeCode,
      grade_name: config.name,
      cycle_code: config.cycle,
      cycle_name: config.cycleName,
      is_entry_point: ENTRY_POINTS.has(gradeCode),
      calibrated_lateral: calibratedLateral,
      base_retention: baseRetention,
      has_override: hasOverride,
      override_lateral: overrideLateral,
      effective_lateral: effectiveLateral,
      effective_retention: effectiveRetention,
      growth_rate: growthRate,
      confidence,
    })
  }

  // Sort by order
  rows.sort((a, b) => GRADE_CONFIG[a.grade_code].order - GRADE_CONFIG[b.grade_code].order)

  return rows
}

// =============================================================================
// Component
// =============================================================================

export const UnifiedLateralTable = memo(function UnifiedLateralTable({
  entryPointRates,
  incidentalLateral,
  onUpdate,
  disabled = false,
}: UnifiedLateralTableProps) {
  const [editingGrade, setEditingGrade] = useState<string | null>(null)
  const [editValue, setEditValue] = useState('')

  // Build grade rows
  const gradeRows = useMemo(
    () => buildGradeRows(entryPointRates, incidentalLateral),
    [entryPointRates, incidentalLateral]
  )

  // Group by cycle
  const groupedRows = useMemo(() => {
    const groups: Record<string, GradeRow[]> = { MAT: [], ELEM: [], COLL: [], LYC: [] }
    for (const row of gradeRows) {
      groups[row.cycle_code]?.push(row)
    }
    return groups
  }, [gradeRows])

  // Summary stats
  const stats = useMemo(() => {
    const overrideCount = gradeRows.filter((r) => r.has_override).length
    const avgGrowth = gradeRows.reduce((sum, r) => sum + r.growth_rate, 0) / gradeRows.length
    return { overrideCount, avgGrowth }
  }, [gradeRows])

  // Format percentage for display
  const formatPct = (value: number, decimals = 1) => `${(value * 100).toFixed(decimals)}%`

  // Toggle override for a grade
  const handleToggleOverride = useCallback(
    (row: GradeRow, enabled: boolean) => {
      onUpdate({
        grade_code: row.grade_code,
        override_lateral_rate: enabled,
        override_retention_rate: enabled,
        manual_lateral_rate: enabled ? row.effective_lateral : null,
        manual_retention_rate: enabled ? row.effective_retention : null,
      })
    },
    [onUpdate]
  )

  // Start editing
  const startEdit = useCallback((row: GradeRow) => {
    setEditingGrade(row.grade_code)
    setEditValue((row.effective_lateral * 100).toFixed(1))
  }, [])

  // Cancel editing
  const cancelEdit = useCallback(() => {
    setEditingGrade(null)
    setEditValue('')
  }, [])

  // Save edit
  const saveEdit = useCallback(
    (row: GradeRow) => {
      const value = parseFloat(editValue)
      if (!isNaN(value) && value >= 0 && value <= 100) {
        onUpdate({
          grade_code: row.grade_code,
          override_lateral_rate: true,
          override_retention_rate: true,
          manual_lateral_rate: value / 100, // Convert percentage to decimal
          manual_retention_rate: row.effective_retention,
        })
      }
      setEditingGrade(null)
    },
    [editValue, onUpdate]
  )

  // Render cycle header
  const renderCycleHeader = (cycleCode: string, cycleName: string) => {
    const color = CYCLE_COLORS[cycleCode]
    const retention = CYCLE_RETENTION_RATES[cycleCode as keyof typeof CYCLE_RETENTION_RATES]

    return (
      <TableRow key={`cycle-${cycleCode}`} className={cn('border-t-2', color.border)}>
        <TableCell colSpan={7} className={cn('py-2', color.bg)}>
          <div className="flex items-center gap-3">
            <span className={cn('font-semibold', color.text)}>{cycleName}</span>
            <span className="text-xs text-muted-foreground">
              Base retention: {formatPct(retention ?? 0.96, 0)}
            </span>
          </div>
        </TableCell>
      </TableRow>
    )
  }

  // Render grade row
  const renderGradeRow = (row: GradeRow) => {
    const isEditing = editingGrade === row.grade_code

    return (
      <TableRow key={row.grade_code} className={row.is_entry_point ? 'bg-muted/20' : ''}>
        {/* Grade */}
        <TableCell>
          <div className="flex items-center gap-2">
            <span className="font-medium">{row.grade_code}</span>
            {row.is_entry_point && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Badge
                      variant="outline"
                      className="gap-1 px-1.5 py-0 text-xs bg-purple-50 text-purple-700 border-purple-200"
                    >
                      <DoorOpen className="h-3 w-3" />
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="font-medium">Entry Point Grade</p>
                    <p className="text-xs">Major intake level with higher new student rates</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
          <div className="text-xs text-muted-foreground">{row.grade_name}</div>
        </TableCell>

        {/* Calibrated Rate */}
        <TableCell>
          <div className="flex items-center gap-2">
            <span>{formatPct(row.calibrated_lateral)}</span>
            <Badge variant="outline" className={cn('text-xs', CONFIDENCE_COLORS[row.confidence])}>
              {row.confidence}
            </Badge>
          </div>
        </TableCell>

        {/* Override Toggle */}
        <TableCell>
          <Switch
            checked={row.has_override}
            onCheckedChange={(checked) => handleToggleOverride(row, checked)}
            disabled={disabled}
          />
        </TableCell>

        {/* Custom Rate (editable when override enabled) */}
        <TableCell>
          {isEditing ? (
            <div className="flex items-center gap-1">
              <Input
                type="number"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-20 h-8"
                step="0.1"
                min="0"
                max="100"
                autoFocus
              />
              <span className="text-xs text-muted-foreground">%</span>
              <Button size="sm" variant="ghost" onClick={cancelEdit} className="h-7 w-7 p-0 ml-1">
                <X className="h-4 w-4" />
              </Button>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => saveEdit(row)}
                className="h-7 w-7 p-0"
              >
                <Check className="h-4 w-4 text-green-600" />
              </Button>
            </div>
          ) : row.has_override ? (
            <div className="flex items-center gap-2">
              <span className="font-medium text-blue-600">
                {formatPct(row.override_lateral ?? 0)}
              </span>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => startEdit(row)}
                disabled={disabled}
                className="h-7 w-7 p-0"
              >
                <Edit2 className="h-3 w-3" />
              </Button>
            </div>
          ) : (
            <span className="text-muted-foreground">—</span>
          )}
        </TableCell>

        {/* Final Rate (what will be used) */}
        <TableCell>
          <span className={cn('font-semibold', row.has_override && 'text-blue-600')}>
            {formatPct(row.effective_lateral)}
          </span>
          {row.has_override && (
            <Badge
              variant="outline"
              className="ml-2 text-xs bg-blue-50 text-blue-600 border-blue-200"
            >
              custom
            </Badge>
          )}
        </TableCell>

        {/* Growth Rate */}
        <TableCell>
          <div className="flex items-center gap-1">
            {row.growth_rate >= 1 ? (
              <TrendingUp className="h-4 w-4 text-green-600" />
            ) : (
              <TrendingDown className="h-4 w-4 text-amber-600" />
            )}
            <span
              className={cn(
                'font-semibold',
                row.growth_rate >= 1 ? 'text-green-600' : 'text-amber-600'
              )}
            >
              {formatPct(row.growth_rate)}
            </span>
          </div>
        </TableCell>
      </TableRow>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <div className="flex items-center gap-6 text-sm">
        <div>
          <span className="text-muted-foreground">Total Grades: </span>
          <span className="font-medium">{gradeRows.length}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Custom Rates: </span>
          <span className="font-medium text-blue-600">{stats.overrideCount}</span>
        </div>
        <div>
          <span className="text-muted-foreground">Avg Growth: </span>
          <span
            className={cn(
              'font-medium',
              stats.avgGrowth >= 1 ? 'text-green-600' : 'text-amber-600'
            )}
          >
            {formatPct(stats.avgGrowth)}
          </span>
        </div>
      </div>

      {/* Help Box */}
      <div className="flex items-start gap-2 p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm">
        <HelpCircle className="h-4 w-4 text-slate-500 mt-0.5 flex-shrink-0" />
        <div className="text-slate-700">
          <p className="font-medium">How to read this table</p>
          <ul className="mt-1 space-y-1 text-slate-600">
            <li>
              <strong>Calibrated Rate:</strong> New students expected as % of previous grade (from
              historical data)
            </li>
            <li>
              <strong>Override:</strong> Enable to set your own custom rate instead of the
              calibrated value
            </li>
            <li>
              <strong>Growth Rate:</strong> Total enrollment change = Retention × (1 + Lateral).
              Above 100% = growth
            </li>
          </ul>
        </div>
      </div>

      {/* Table */}
      <div className="border rounded-lg overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="w-[160px]">Grade</TableHead>
              <TableHead className="w-[140px]">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger className="flex items-center gap-1">
                      Calibrated Rate
                      <HelpCircle className="h-3 w-3 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>New students as % of previous grade</p>
                      <p className="text-xs text-muted-foreground">
                        From 70% last year + 30% previous year
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </TableHead>
              <TableHead className="w-[80px]">Override</TableHead>
              <TableHead className="w-[160px]">Custom Rate</TableHead>
              <TableHead className="w-[120px]">Final Rate</TableHead>
              <TableHead className="w-[120px]">
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger className="flex items-center gap-1">
                      Growth Rate
                      <HelpCircle className="h-3 w-3 text-muted-foreground" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Expected enrollment change year-over-year</p>
                      <p className="text-xs text-muted-foreground">
                        = Retention × (1 + Lateral Rate)
                      </p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {['MAT', 'ELEM', 'COLL', 'LYC'].map((cycleCode) => {
              const cycleRows = groupedRows[cycleCode]
              if (!cycleRows?.length) return null

              const cycleName = cycleRows[0].cycle_name
              return [renderCycleHeader(cycleCode, cycleName), ...cycleRows.map(renderGradeRow)]
            })}
          </TableBody>
        </Table>
      </div>
    </div>
  )
})
