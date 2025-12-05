import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useMemo, useCallback, useEffect } from 'react'
import { ColDef, CellValueChangedEvent, ValueFormatterParams } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { Button } from '@/components/ui/button'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Save, Users, TrendingUp, Globe, AlertCircle, CheckCircle } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  useEnrollmentWithDistribution,
  useBulkUpsertEnrollmentTotals,
  useBulkUpsertDistributions,
} from '@/hooks/api/useEnrollment'
import { useLevels } from '@/hooks/api/useConfiguration'
import { EnrollmentBreakdown } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'
import { Badge } from '@/components/ui/badge'

export const Route = createFileRoute('/planning/enrollment')({
  beforeLoad: requireAuth,
  component: EnrollmentPlanningPage,
})

// School capacity constant
const SCHOOL_CAPACITY = 1875
const LEVEL_CAPACITY = 125

// ============================================================================
// Types for local state
// ============================================================================

interface LocalTotal {
  level_id: string
  level_code: string
  level_name: string
  cycle_code: string
  total_students: number
  capacity: number
}

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

// ============================================================================
// Main Page Component
// ============================================================================

function EnrollmentPlanningPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [activeTab, setActiveTab] = useState('totals')

  // Local state for editing
  const [localTotals, setLocalTotals] = useState<LocalTotal[]>([])
  const [localDistributions, setLocalDistributions] = useState<LocalDistribution[]>([])
  const [hasUnsavedTotals, setHasUnsavedTotals] = useState(false)
  const [hasUnsavedDistributions, setHasUnsavedDistributions] = useState(false)

  // Queries
  const {
    data: enrollmentData,
    isLoading,
    error,
  } = useEnrollmentWithDistribution(selectedVersionId)
  const { data: levelsData } = useLevels()

  // Mutations
  const saveTotalsMutation = useBulkUpsertEnrollmentTotals()
  const saveDistributionsMutation = useBulkUpsertDistributions()

  // Get cycle code from level's cycle_id
  const getCycleCode = useCallback((cycleId: string) => {
    // Map cycle_id to code based on known cycles
    const cycleMap: Record<string, string> = {
      MAT: 'MAT',
      ELEM: 'ELEM',
      COLL: 'COLL',
      LYC: 'LYC',
    }
    // For now, derive from level code patterns
    return cycleMap[cycleId] ?? ''
  }, [])

  // Initialize local state from API data
  useEffect(() => {
    if (enrollmentData && levelsData) {
      // Build totals with level info
      const totals = levelsData.map((level) => {
        const existingTotal = enrollmentData.totals.find((t) => t.level_id === level.id)
        return {
          level_id: level.id,
          level_code: level.code,
          level_name: level.name_fr || level.name_en,
          cycle_code: level.cycle_id ? getCycleCode(level.cycle_id) : '',
          total_students: existingTotal?.total_students ?? 0,
          capacity: LEVEL_CAPACITY,
        }
      })
      setLocalTotals(totals)

      // Build distributions with level info
      const distributions = levelsData.map((level) => {
        const existingDist = enrollmentData.distributions.find((d) => d.level_id === level.id)
        const french = existingDist?.french_pct ?? 0
        const saudi = existingDist?.saudi_pct ?? 0
        const other = existingDist?.other_pct ?? 0
        const sum = french + saudi + other
        return {
          level_id: level.id,
          level_code: level.code,
          level_name: level.name_fr || level.name_en,
          cycle_code: level.cycle_id ? getCycleCode(level.cycle_id) : '',
          french_pct: french,
          saudi_pct: saudi,
          other_pct: other,
          sum,
          isValid: Math.abs(sum - 100) < 0.01 || sum === 0,
        }
      })
      setLocalDistributions(distributions)

      setHasUnsavedTotals(false)
      setHasUnsavedDistributions(false)
    }
  }, [enrollmentData, levelsData, getCycleCode])

  // Calculate summary statistics
  const statistics = useMemo(() => {
    if (!enrollmentData?.summary) {
      return {
        totalStudents: localTotals.reduce((sum, t) => sum + t.total_students, 0),
        capacityUtilization: 0,
        byNationality: {} as Record<string, number>,
        byCycle: {} as Record<string, number>,
      }
    }

    const total = localTotals.reduce((sum, t) => sum + t.total_students, 0)
    return {
      totalStudents: total,
      capacityUtilization: Math.round((total / SCHOOL_CAPACITY) * 1000) / 10,
      byNationality: enrollmentData.summary.by_nationality,
      byCycle: enrollmentData.summary.by_cycle,
    }
  }, [enrollmentData?.summary, localTotals])

  // Check if all distributions are valid
  const allDistributionsValid = useMemo(() => {
    return localDistributions.every((d) => d.isValid || d.sum === 0)
  }, [localDistributions])

  // Save totals handler
  const handleSaveTotals = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }

    try {
      await saveTotalsMutation.mutateAsync({
        versionId: selectedVersionId,
        totals: localTotals.map((t) => ({
          level_id: t.level_id,
          total_students: t.total_students,
        })),
      })
      setHasUnsavedTotals(false)
    } catch {
      // Error handled by mutation
    }
  }

  // Save distributions handler
  const handleSaveDistributions = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }

    if (!allDistributionsValid) {
      toastMessages.error.validation('All percentages must sum to 100%')
      return
    }

    try {
      // Filter out empty distributions (sum = 0)
      const nonEmptyDistributions = localDistributions.filter((d) => d.sum > 0)

      await saveDistributionsMutation.mutateAsync({
        versionId: selectedVersionId,
        distributions: nonEmptyDistributions.map((d) => ({
          level_id: d.level_id,
          french_pct: d.french_pct,
          saudi_pct: d.saudi_pct,
          other_pct: d.other_pct,
        })),
      })
      setHasUnsavedDistributions(false)
    } catch {
      // Error handled by mutation
    }
  }

  // ============================================================================
  // Column Definitions for Totals Grid
  // ============================================================================

  const totalsColumnDefs: ColDef<LocalTotal>[] = useMemo(
    () => [
      {
        field: 'cycle_code',
        headerName: 'Cycle',
        width: 100,
        rowGroup: true,
        hide: true,
      },
      {
        field: 'level_code',
        headerName: 'Level',
        width: 100,
      },
      {
        field: 'level_name',
        headerName: 'Name',
        flex: 1,
      },
      {
        field: 'total_students',
        headerName: 'Total Students',
        width: 150,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 500,
        },
        cellClass: (params) => {
          const capacity = params.data?.capacity ?? LEVEL_CAPACITY
          if (params.value > capacity) {
            return 'bg-red-100 text-red-800'
          }
          if (params.value > capacity * 0.8) {
            return 'bg-yellow-100 text-yellow-800'
          }
          return ''
        },
      },
      {
        field: 'capacity',
        headerName: 'Capacity',
        width: 100,
        valueFormatter: (params: ValueFormatterParams) => `${params.value}`,
      },
      {
        headerName: 'Utilization',
        width: 120,
        valueGetter: (params) => {
          const total = params.data?.total_students ?? 0
          const capacity = params.data?.capacity ?? 1
          return Math.round((total / capacity) * 100)
        },
        cellRenderer: (params: { value: number }) => {
          const pct = params.value
          let color = 'bg-green-500'
          if (pct > 100) color = 'bg-red-500'
          else if (pct > 80) color = 'bg-yellow-500'

          return (
            <div className="flex items-center gap-2">
              <div className="flex-1 h-2 bg-gray-200 rounded">
                <div
                  className={`h-2 rounded ${color}`}
                  style={{ width: `${Math.min(pct, 100)}%` }}
                />
              </div>
              <span className="text-xs w-10">{pct}%</span>
            </div>
          )
        },
      },
    ],
    []
  )

  // ============================================================================
  // Column Definitions for Distribution Grid
  // ============================================================================

  const distributionColumnDefs: ColDef<LocalDistribution>[] = useMemo(
    () => [
      {
        field: 'cycle_code',
        headerName: 'Cycle',
        width: 100,
        rowGroup: true,
        hide: true,
      },
      {
        field: 'level_code',
        headerName: 'Level',
        width: 100,
      },
      {
        field: 'level_name',
        headerName: 'Name',
        flex: 1,
      },
      {
        field: 'french_pct',
        headerName: 'French %',
        width: 120,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 100,
          precision: 2,
        },
      },
      {
        field: 'saudi_pct',
        headerName: 'Saudi %',
        width: 120,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 100,
          precision: 2,
        },
      },
      {
        field: 'other_pct',
        headerName: 'Other %',
        width: 120,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 100,
          precision: 2,
        },
      },
      {
        field: 'sum',
        headerName: 'Total',
        width: 100,
        cellRenderer: (params: { data: LocalDistribution }) => {
          const sum = params.data?.sum ?? 0
          const isValid = params.data?.isValid
          if (sum === 0) return <span className="text-gray-400">-</span>
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
      },
    ],
    []
  )

  // ============================================================================
  // Column Definitions for Breakdown Grid (Read-only)
  // ============================================================================

  const breakdownColumnDefs: ColDef<EnrollmentBreakdown>[] = useMemo(
    () => [
      {
        field: 'cycle_code',
        headerName: 'Cycle',
        width: 100,
        rowGroup: true,
        hide: true,
      },
      {
        field: 'level_code',
        headerName: 'Level',
        width: 100,
      },
      {
        field: 'level_name',
        headerName: 'Name',
        flex: 1,
      },
      {
        field: 'french_count',
        headerName: 'French',
        width: 100,
        type: 'numericColumn',
      },
      {
        field: 'saudi_count',
        headerName: 'Saudi',
        width: 100,
        type: 'numericColumn',
      },
      {
        field: 'other_count',
        headerName: 'Other',
        width: 100,
        type: 'numericColumn',
      },
      {
        field: 'total_students',
        headerName: 'Total',
        width: 100,
        type: 'numericColumn',
        cellClass: 'font-bold',
      },
    ],
    []
  )

  // ============================================================================
  // Cell Value Changed Handlers
  // ============================================================================

  const onTotalsCellValueChanged = useCallback((event: CellValueChangedEvent<LocalTotal>) => {
    const { data, newValue, colDef } = event
    if (!data || colDef.field !== 'total_students') return

    setLocalTotals((prev) =>
      prev.map((t) =>
        t.level_id === data.level_id ? { ...t, total_students: Number(newValue) || 0 } : t
      )
    )
    setHasUnsavedTotals(true)
  }, [])

  const onDistributionCellValueChanged = useCallback(
    (event: CellValueChangedEvent<LocalDistribution>) => {
      const { data, newValue, colDef } = event
      if (!data) return

      const field = colDef.field as 'french_pct' | 'saudi_pct' | 'other_pct'
      if (!['french_pct', 'saudi_pct', 'other_pct'].includes(field)) return

      setLocalDistributions((prev) =>
        prev.map((d) => {
          if (d.level_id !== data.level_id) return d

          const updated = { ...d, [field]: Number(newValue) || 0 }
          const sum = updated.french_pct + updated.saudi_pct + updated.other_pct
          return {
            ...updated,
            sum,
            isValid: Math.abs(sum - 100) < 0.01 || sum === 0,
          }
        })
      )
      setHasUnsavedDistributions(true)
    },
    []
  )

  // ============================================================================
  // Render
  // ============================================================================

  return (
    <MainLayout>
      <PageContainer
        title="Enrollment Planning"
        description="Plan student enrollment by level with nationality distribution"
      >
        {/* Summary Cards */}
        {selectedVersionId && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {/* Total Students */}
            <Card data-testid="total-students-card">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Students</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div data-testid="total-students" className="text-2xl font-bold">
                  {statistics.totalStudents.toLocaleString()}
                </div>
                <p className="text-xs text-muted-foreground mt-1">Across all 15 levels</p>
              </CardContent>
            </Card>

            {/* Capacity Utilization */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">School Capacity</CardTitle>
                <TrendingUp className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.capacityUtilization}%</div>
                <p className="text-xs text-muted-foreground mt-1">
                  {statistics.totalStudents.toLocaleString()} / {SCHOOL_CAPACITY.toLocaleString()}{' '}
                  max
                </p>
                <div className="w-full bg-gray-200 rounded-full h-2 mt-2">
                  <div
                    className={`h-2 rounded-full ${
                      statistics.capacityUtilization > 90
                        ? 'bg-red-500'
                        : statistics.capacityUtilization > 75
                          ? 'bg-yellow-500'
                          : 'bg-green-500'
                    }`}
                    style={{ width: `${Math.min(statistics.capacityUtilization, 100)}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            {/* By Nationality */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">By Nationality</CardTitle>
                <Globe className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {Object.entries(statistics.byNationality).map(([nationality, count]) => (
                    <div key={nationality} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{nationality}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                  {Object.keys(statistics.byNationality).length === 0 && (
                    <p className="text-xs text-muted-foreground">No data yet</p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* By Cycle */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">By Cycle</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {Object.entries(statistics.byCycle).map(([cycle, count]) => (
                    <div key={cycle} className="flex justify-between text-sm">
                      <span className="text-muted-foreground">{cycle}</span>
                      <span className="font-medium">{count}</span>
                    </div>
                  ))}
                  {Object.keys(statistics.byCycle).length === 0 && (
                    <p className="text-xs text-muted-foreground">No data yet</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Tabbed Interface */}
        {selectedVersionId ? (
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
            <div className="flex items-center justify-between">
              <TabsList>
                <TabsTrigger value="totals">
                  Enrollment by Level
                  {hasUnsavedTotals && (
                    <Badge variant="secondary" className="ml-2 bg-yellow-100">
                      Unsaved
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="distribution">
                  Nationality Distribution
                  {hasUnsavedDistributions && (
                    <Badge variant="secondary" className="ml-2 bg-yellow-100">
                      Unsaved
                    </Badge>
                  )}
                </TabsTrigger>
                <TabsTrigger value="breakdown">Calculated Breakdown</TabsTrigger>
              </TabsList>

              {/* Save Button based on active tab */}
              {activeTab === 'totals' && (
                <Button
                  onClick={handleSaveTotals}
                  disabled={!hasUnsavedTotals || saveTotalsMutation.isPending}
                >
                  <Save className="h-4 w-4 mr-2" />
                  {saveTotalsMutation.isPending ? 'Saving...' : 'Save Totals'}
                </Button>
              )}
              {activeTab === 'distribution' && (
                <Button
                  onClick={handleSaveDistributions}
                  disabled={
                    !hasUnsavedDistributions ||
                    saveDistributionsMutation.isPending ||
                    !allDistributionsValid
                  }
                >
                  <Save className="h-4 w-4 mr-2" />
                  {saveDistributionsMutation.isPending ? 'Saving...' : 'Save Distribution'}
                </Button>
              )}
            </div>

            {/* Tab 1: Enrollment Totals by Level */}
            <TabsContent value="totals" className="space-y-4">
              <div className="text-sm text-muted-foreground mb-2">
                Enter total student count per level. Changes are saved when you click "Save Totals".
              </div>
              <DataTableLazy
                rowData={localTotals}
                columnDefs={totalsColumnDefs}
                loading={isLoading}
                error={error}
                pagination={false}
                onCellValueChanged={onTotalsCellValueChanged}
                groupDisplayType="groupRows"
                suppressMovableColumns
              />
            </TabsContent>

            {/* Tab 2: Nationality Distribution */}
            <TabsContent value="distribution" className="space-y-4">
              <div className="text-sm text-muted-foreground mb-2">
                Set nationality percentages per level (must sum to 100%). These percentages are
                applied to calculate the breakdown.
              </div>
              {!allDistributionsValid && (
                <div className="bg-red-50 border border-red-200 rounded p-3 text-sm text-red-700">
                  <AlertCircle className="inline h-4 w-4 mr-2" />
                  Some rows have percentages that don't sum to 100%. Please correct them before
                  saving.
                </div>
              )}
              <DataTableLazy
                rowData={localDistributions}
                columnDefs={distributionColumnDefs}
                loading={isLoading}
                error={error}
                pagination={false}
                onCellValueChanged={onDistributionCellValueChanged}
                groupDisplayType="groupRows"
                suppressMovableColumns
              />
            </TabsContent>

            {/* Tab 3: Calculated Breakdown (Read-only) */}
            <TabsContent value="breakdown" className="space-y-4">
              <div className="text-sm text-muted-foreground mb-2">
                This view shows the calculated student counts by level and nationality based on your
                totals and distribution percentages.
              </div>
              <DataTableLazy
                rowData={enrollmentData?.breakdown ?? []}
                columnDefs={breakdownColumnDefs}
                loading={isLoading}
                error={error}
                pagination={false}
                groupDisplayType="groupRows"
                suppressMovableColumns
              />
            </TabsContent>
          </Tabs>
        ) : (
          <div className="text-center py-12 text-muted-foreground">
            Please select a budget version to view enrollment data
          </div>
        )}
      </PageContainer>
    </MainLayout>
  )
}
