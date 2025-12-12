/**
 * DHG Workforce Planning Page - /planning/dhg
 *
 * Manages DHG (Dotation Horaire Globale) workforce planning.
 * Navigation handled by ModuleLayout (WorkflowTabs + ModuleHeader).
 *
 * Phase 6 Migration: Removed PlanningPageWrapper, uses ModuleLayout
 * Phase 12: Added draft pattern for performance optimization
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState, useMemo, useCallback } from 'react'
import { AgGridReact } from 'ag-grid-react'
import type { CellValueChangedEvent } from 'ag-grid-community'
import { ColDef, themeQuartz } from 'ag-grid-community'
import { SummaryCard } from '@/components/SummaryCard'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import {
  useSubjectHours,
  useTeacherRequirements,
  useTRMDGapAnalysis,
  useApplyAndCalculateDHG,
} from '@/hooks/api/useDHG'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'
import { Users, Clock, AlertTriangle, TrendingUp, Calculator, Save } from 'lucide-react'
import { HistoricalToggle, HistoricalSummary } from '@/components/planning/HistoricalToggle'
import { useDHGWithHistory } from '@/hooks/api/useHistorical'
import { DraftStatusIndicator } from '@/components/ui/DraftStatusIndicator'
import { UnappliedChangesBanner } from '@/components/ui/UnappliedChangesBanner'
import type { DraftStatus } from '@/hooks/useDraft'

export const Route = createFileRoute('/_authenticated/planning/dhg')({
  component: DHGPage,
})

function DHGPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [activeTab, setActiveTab] = useState<'hours' | 'fte' | 'trmd' | 'hsa'>('hours')
  const [showHistorical, setShowHistorical] = useState(false)

  // Draft status tracking (Phase 12 Performance)
  const [hasUnappliedChanges, setHasUnappliedChanges] = useState(false)
  const [lastAppliedAt, setLastAppliedAt] = useState<Date | null>(null)
  const [draftStatus, setDraftStatus] = useState<DraftStatus>('idle')

  const { data: subjectHours, isLoading: loadingHours } = useSubjectHours(selectedVersionId!)
  const { data: teacherFTE, isLoading: loadingFTE } = useTeacherRequirements(selectedVersionId!)
  const { data: trmdGaps, isLoading: loadingTRMD } = useTRMDGapAnalysis(selectedVersionId!)
  const { data: budgetVersions } = useBudgetVersions()
  const applyAndCalculate = useApplyAndCalculateDHG()

  // Historical data query - only enabled when toggle is ON
  const { data: historicalData, isLoading: historicalLoading } = useDHGWithHistory(
    selectedVersionId,
    {
      enabled: showHistorical,
    }
  )

  // Get current fiscal year from selected budget version
  const currentFiscalYear = useMemo(() => {
    if (!selectedVersionId || !budgetVersions?.items) return new Date().getFullYear()
    const version = budgetVersions.items.find((v) => v.id === selectedVersionId)
    return version?.fiscal_year ?? new Date().getFullYear()
  }, [selectedVersionId, budgetVersions])

  // Check if TRMD data is null (prerequisites missing)
  const trmdMissingPrerequisites = !loadingTRMD && !trmdGaps

  // PERFORMANCE: Apply & Calculate handler (BFF pattern)
  const handleApplyAndCalculate = useCallback(async () => {
    if (!selectedVersionId) return
    setDraftStatus('applying')
    try {
      await applyAndCalculate.mutateAsync({ versionId: selectedVersionId })
      setHasUnappliedChanges(false)
      setLastAppliedAt(new Date())
      setDraftStatus('applied')
    } catch {
      setDraftStatus('error')
    }
  }, [selectedVersionId, applyAndCalculate])

  // Discard changes handler - refetch data to reset to last saved state
  const handleDiscardChanges = useCallback(() => {
    setHasUnappliedChanges(false)
    setDraftStatus('idle')
    // Note: Data will be refetched from cache/server
  }, [])

  // Handler for tracking cell edits as draft changes
  const handleCellValueChanged = useCallback(() => {
    setHasUnappliedChanges(true)
    setDraftStatus('saved') // Mark as having changes
  }, [])

  // Summary metrics - API returns arrays directly
  const fteItems = teacherFTE || []
  const trmdGapItems = trmdGaps?.gaps || []
  const totalFTE = fteItems.reduce(
    (sum: number, item: { fte_required?: number }) => sum + (item.fte_required || 0),
    0
  )
  const totalHSAHours = trmdGaps?.total_hsa_needed || 0
  const totalDeficit = trmdGaps?.total_deficit || 0
  const totalSubjects = trmdGapItems.length

  return (
    <div className="p-6 space-y-5">
      {/* Page Actions with Draft Status */}
      <div className="flex items-center justify-between gap-3">
        <DraftStatusIndicator
          status={draftStatus}
          lastAppliedAt={lastAppliedAt}
          hasUnappliedChanges={hasUnappliedChanges}
        />
        <div className="flex items-center gap-3">
          <HistoricalToggle
            showHistorical={showHistorical}
            onToggle={setShowHistorical}
            disabled={!selectedVersionId}
            isLoading={historicalLoading}
            currentFiscalYear={currentFiscalYear}
          />
          <Button
            data-testid="calculate-button"
            onClick={handleApplyAndCalculate}
            disabled={!selectedVersionId || applyAndCalculate.isPending}
            variant="premium"
          >
            <Calculator className="w-4 h-4" />
            {applyAndCalculate.isPending ? 'Calculating...' : 'Apply & Calculate'}
          </Button>
        </div>
      </div>

      {/* Unapplied Changes Banner */}
      {selectedVersionId && (
        <UnappliedChangesBanner
          hasChanges={hasUnappliedChanges}
          impactSummary={`${totalSubjects} subjects, ${totalFTE.toFixed(1)} FTE`}
          onDiscard={handleDiscardChanges}
          onApply={handleApplyAndCalculate}
          isApplying={applyAndCalculate.isPending}
        />
      )}

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Historical Summary for FTE */}
          {showHistorical && historicalData?.totals_fte && (
            <div className="flex gap-4 mb-4">
              <HistoricalSummary
                currentValue={totalFTE}
                priorYearValue={historicalData.totals_fte.n_minus_1?.value ?? null}
                changePercent={historicalData.totals_fte.vs_n_minus_1_pct ?? null}
                label="Total FTE vs Prior Year"
                isCurrency={false}
              />
              {historicalData.totals_hours && (
                <HistoricalSummary
                  currentValue={fteItems.reduce((sum, item) => sum + (item.required_hours || 0), 0)}
                  priorYearValue={historicalData.totals_hours.n_minus_1?.value ?? null}
                  changePercent={historicalData.totals_hours.vs_n_minus_1_pct ?? null}
                  label="Total Hours vs Prior Year"
                  isCurrency={false}
                />
              )}
            </div>
          )}

          {/* Summary Cards - Premium Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              title="Total FTE Required"
              value={totalFTE.toFixed(2)}
              subtitle="Full-time equivalents"
              icon={<Users className="w-4 h-4" />}
              compact
            />
            <SummaryCard
              title="HSA Hours"
              value={totalHSAHours.toFixed(1)}
              subtitle="Overtime hours"
              icon={<Clock className="w-4 h-4" />}
              compact
            />
            <SummaryCard
              title="Deficit Hours"
              value={totalDeficit.toFixed(1)}
              subtitle="Hours to fill"
              icon={<AlertTriangle className="w-4 h-4" />}
              valueClassName={totalDeficit > 0 ? 'text-error-600' : 'text-success-600'}
              trend={totalDeficit > 0 ? 'down' : 'up'}
              compact
            />
            <SummaryCard
              title="Subjects Analyzed"
              value={totalSubjects}
              subtitle="In TRMD gap analysis"
              icon={<TrendingUp className="w-4 h-4" />}
              compact
            />
          </div>

          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger data-testid="subject-hours-tab" value="hours">
                Subject Hours
              </TabsTrigger>
              <TabsTrigger data-testid="fte-tab" value="fte">
                Teacher FTE
              </TabsTrigger>
              <TabsTrigger data-testid="trmd-tab" value="trmd">
                TRMD Gap Analysis
              </TabsTrigger>
              <TabsTrigger data-testid="hsa-tab" value="hsa">
                HSA Planning
              </TabsTrigger>
            </TabsList>

            <TabsContent value="hours" className="mt-6">
              <SubjectHoursTab
                data={subjectHours || []}
                isLoading={loadingHours}
                onCellValueChanged={handleCellValueChanged}
              />
            </TabsContent>

            <TabsContent value="fte" className="mt-6">
              <TeacherFTETab
                data={fteItems}
                isLoading={loadingFTE}
                onCellValueChanged={handleCellValueChanged}
              />
            </TabsContent>

            <TabsContent value="trmd" className="mt-6">
              {trmdMissingPrerequisites ? (
                <Card>
                  <CardContent className="py-12">
                    <div className="text-center text-gray-500">
                      <AlertTriangle className="w-12 h-12 mx-auto mb-4 text-amber-500" />
                      <p className="text-lg font-medium mb-2">
                        Teacher requirements not calculated
                      </p>
                      <p className="text-sm">
                        Please calculate teacher FTE requirements first before viewing the TRMD
                        analysis.
                      </p>
                      <Button
                        onClick={handleApplyAndCalculate}
                        className="mt-4"
                        disabled={applyAndCalculate.isPending}
                      >
                        <Calculator className="w-4 h-4 mr-2" />
                        {applyAndCalculate.isPending
                          ? 'Calculating...'
                          : 'Calculate Teacher Requirements'}
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : (
                <TRMDTab
                  data={trmdGapItems}
                  isLoading={loadingTRMD}
                  onCellValueChanged={handleCellValueChanged}
                />
              )}
            </TabsContent>

            <TabsContent value="hsa" className="mt-6">
              <HSATab data={[]} isLoading={false} onCellValueChanged={handleCellValueChanged} />
            </TabsContent>
          </Tabs>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view DHG workforce planning
        </div>
      )}
    </div>
  )
}

interface SubjectHoursItem {
  id?: string
  budget_version_id?: string
  level_id?: string
  subject_id?: string
  created_at?: string
  updated_at?: string
  subject_name?: string
  level_name?: string
  hours_per_week: number
  is_split: boolean
  number_of_classes?: number
}

interface TabProps {
  onCellValueChanged?: (event: CellValueChangedEvent) => void
}

function SubjectHoursTab({
  data,
  isLoading,
  onCellValueChanged,
}: { data: SubjectHoursItem[]; isLoading: boolean } & TabProps) {
  const columnDefs: ColDef[] = [
    { headerName: 'Subject', field: 'subject_name', pinned: 'left', width: 200 },
    { headerName: 'Level', field: 'level_name', width: 120 },
    {
      headerName: 'Hours/Week',
      field: 'hours_per_week',
      width: 120,
      editable: true,
      cellDataType: 'number',
    },
    {
      headerName: 'Split Class',
      field: 'is_split',
      width: 120,
      cellRenderer: (params: { value: boolean; setValue: (value: boolean) => void }) => (
        <input
          type="checkbox"
          checked={params.value}
          onChange={(e) => {
            params.setValue(e.target.checked)
          }}
          className="w-4 h-4"
        />
      ),
    },
    {
      headerName: 'Total Hours',
      valueGetter: (params: { data: SubjectHoursItem }) => {
        const hours = params.data.hours_per_week
        const classes = params.data.number_of_classes || 1
        return hours * classes
      },
      width: 130,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Subject Hours Matrix</CardTitle>
        <p className="text-sm text-gray-600">
          Edit weekly hours. Click &quot;Apply &amp; Calculate&quot; to recalculate FTE
          requirements.
        </p>
      </CardHeader>
      <CardContent>
        <div style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
            theme={themeQuartz}
            onCellValueChanged={onCellValueChanged}
          />
        </div>
      </CardContent>
    </Card>
  )
}

// Matches DHGTeacherRequirement from backend API
interface TeacherFTEItem {
  id: string
  budget_version_id: string
  subject_id: string
  cycle_id: string
  required_hours: number
  standard_hours: number
  fte_required: number
  notes?: string | null
  created_at: string
  updated_at: string
  // Display fields (may be added by frontend)
  cycle_name?: string
  subject_name?: string
}

function TeacherFTETab({
  data,
  isLoading,
  onCellValueChanged,
}: { data: TeacherFTEItem[]; isLoading: boolean } & TabProps) {
  const columnDefs: ColDef[] = [
    { headerName: 'Cycle', field: 'cycle_id', width: 150 },
    { headerName: 'Subject', field: 'subject_id', width: 200 },
    {
      headerName: 'Required Hours',
      field: 'required_hours',
      width: 140,
      valueFormatter: (params) => params.value?.toFixed(1) ?? '0.0',
    },
    {
      headerName: 'Standard Hours',
      field: 'standard_hours',
      width: 140,
      valueFormatter: (params) => params.value?.toFixed(1) ?? '0.0',
    },
    {
      headerName: 'FTE Required',
      field: 'fte_required',
      width: 140,
      valueFormatter: (params) => params.value?.toFixed(2) ?? '0.00',
      cellStyle: { fontWeight: 'bold' },
    },
    {
      headerName: 'Notes',
      field: 'notes',
      width: 200,
      editable: true,
    },
  ]

  const totalFTERequired = data.reduce((sum, item) => sum + (item.fte_required || 0), 0)
  const totalRequiredHours = data.reduce((sum, item) => sum + (item.required_hours || 0), 0)

  return (
    <Card>
      <CardHeader>
        <CardTitle>Teacher FTE Requirements</CardTitle>
        <p className="text-sm text-gray-600">
          Requirements calculated from subject hours. Primary: 24h/week, Secondary: 18h/week.
        </p>
        <div className="flex gap-4 mt-2">
          <Badge variant="info">Total Hours: {totalRequiredHours.toFixed(1)}</Badge>
          <Badge variant="success">Total FTE: {totalFTERequired.toFixed(2)}</Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
            theme={themeQuartz}
            onCellValueChanged={onCellValueChanged}
          />
        </div>
      </CardContent>
    </Card>
  )
}

// Matches TRMDGapAnalysis.gaps from backend API
interface TRMDItem {
  subject_id: string
  cycle_id: string
  required_fte: number
  aefe_allocated: number
  local_allocated: number
  total_allocated: number
  deficit: number
  hsa_needed: number
  // Display fields (may be added by frontend)
  subject_name?: string
}

function TRMDTab({
  data,
  isLoading,
  onCellValueChanged,
}: { data: TRMDItem[]; isLoading: boolean } & TabProps) {
  const columnDefs: ColDef[] = [
    { headerName: 'Subject', field: 'subject_id', pinned: 'left', width: 150 },
    { headerName: 'Cycle', field: 'cycle_id', width: 120 },
    {
      headerName: 'Required FTE',
      field: 'required_fte',
      width: 140,
      valueFormatter: (params) => params.value?.toFixed(2) ?? '0.00',
    },
    {
      headerName: 'AEFE Allocated',
      field: 'aefe_allocated',
      width: 150,
      editable: true,
      cellDataType: 'number',
      valueFormatter: (params) => params.value?.toFixed(2) ?? '0.00',
    },
    {
      headerName: 'Local Allocated',
      field: 'local_allocated',
      width: 150,
      editable: true,
      cellDataType: 'number',
      valueFormatter: (params) => params.value?.toFixed(2) ?? '0.00',
    },
    {
      headerName: 'Total Allocated',
      field: 'total_allocated',
      width: 140,
      valueFormatter: (params) => params.value?.toFixed(2) ?? '0.00',
    },
    {
      headerName: 'Deficit/Surplus',
      field: 'deficit',
      width: 150,
      valueFormatter: (params) => params.value?.toFixed(2) ?? '0.00',
      cellStyle: (params) => ({
        color: (params.value || 0) > 0 ? 'var(--color-terracotta)' : 'var(--color-sage)',
        fontWeight: 'bold',
      }),
      cellRenderer: (params: { value: number }) => {
        const value = params.value || 0
        const icon = value > 0 ? '▼' : '▲'
        return `${icon} ${Math.abs(value).toFixed(2)} FTE`
      },
    },
    {
      headerName: 'HSA Needed',
      field: 'hsa_needed',
      width: 140,
      valueFormatter: (params) => params.value?.toFixed(1) ?? '0.0',
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>TRMD Analysis (Requirements vs Resources)</CardTitle>
        <p className="text-sm text-gray-600">
          Compare requirements to available positions. Red = deficit (recruitment or HSA needed),
          Green = surplus.
        </p>
      </CardHeader>
      <CardContent>
        <div style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
            theme={themeQuartz}
            onCellValueChanged={onCellValueChanged}
          />
        </div>
      </CardContent>
    </Card>
  )
}

interface HSAItem {
  teacher_name?: string
  subject_name?: string
  hsa_hours: number
  notes?: string | null
}

function HSATab({
  data,
  isLoading,
  onCellValueChanged,
}: { data: HSAItem[]; isLoading: boolean } & TabProps) {
  const columnDefs: ColDef[] = [
    { headerName: 'Teacher', field: 'teacher_name', width: 200 },
    { headerName: 'Subject', field: 'subject_name', width: 200 },
    {
      headerName: 'HSA Hours',
      field: 'hsa_hours',
      width: 140,
      editable: true,
      cellDataType: 'number',
      cellEditor: 'agNumberCellEditor',
      cellEditorParams: {
        min: 0,
        max: 4,
      },
    },
    {
      headerName: 'Status',
      valueGetter: (params: { data: HSAItem }) => {
        const hours = params.data.hsa_hours
        if (hours > 4) return 'Exceeds Max'
        if (hours >= 2) return 'Within Limit'
        return 'Below Target'
      },
      width: 140,
      cellRenderer: (params: { value: string }) => {
        const status = params.value
        const variant =
          status === 'Exceeds Max'
            ? 'destructive'
            : status === 'Within Limit'
              ? 'success'
              : 'warning'
        return <Badge variant={variant}>{status}</Badge>
      },
    },
    { headerName: 'Notes', field: 'notes', width: 300, editable: true },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>HSA Planning (Overtime Hours)</CardTitle>
        <p className="text-sm text-gray-600">
          Assign overtime hours to teachers. Maximum: 2-4 hours per teacher per week.
        </p>
        <div className="mt-2">
          <Button size="sm">
            <Save className="w-4 h-4 mr-2" />
            Add HSA Assignment
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        <div style={{ height: 600 }}>
          <AgGridReact
            rowData={data}
            columnDefs={columnDefs}
            defaultColDef={{
              sortable: true,
              filter: true,
              resizable: true,
            }}
            loading={isLoading}
            theme={themeQuartz}
            onCellValueChanged={(event) => {
              // Track as draft change
              onCellValueChanged?.(event)
              // Validation warning
              const hours = event.data.hsa_hours
              if (hours > 4) {
                console.warn('HSA hours exceed maximum of 4 hours per teacher')
              }
            }}
          />
        </div>
      </CardContent>
    </Card>
  )
}
