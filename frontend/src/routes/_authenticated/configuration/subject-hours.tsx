import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { PageContainer } from '@/components/layout/PageContainer'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { AlertCircle, Save, CheckCircle } from 'lucide-react'
import { SummaryCard } from '@/components/SummaryCard'
import {
  useLevels,
  useCycles,
  useSubjectHoursMatrix,
  useBatchSaveSubjectHours,
  useCurriculumTemplates,
  useApplyTemplate,
  useCreateSubject,
} from '@/hooks/api/useConfiguration'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { toastMessages } from '@/lib/toast-messages'
import { SubjectHoursMatrix } from '@/components/configuration/SubjectHoursMatrix'
import type { SubjectHoursMatrixRow } from '@/components/configuration/subjectHoursUtils'
import {
  transformToMatrixRows,
  transformToEntries,
} from '@/components/configuration/subjectHoursUtils'
import { TemplateSelector } from '@/components/configuration/TemplateSelector'
import { AddSubjectDialog } from '@/components/configuration/AddSubjectDialog'

export const Route = createFileRoute('/_authenticated/configuration/subject-hours')({
  beforeLoad: requireAuth,
  component: SubjectHoursPage,
})

// Available cycle tabs
const CYCLE_TABS = [
  { code: 'MAT', name: 'Maternelle', disabled: true, hint: 'Primary school curriculum' },
  { code: 'ELEM', name: 'Élémentaire', disabled: true, hint: 'Primary school curriculum' },
  { code: 'COLL', name: 'Collège', disabled: false, hint: '6ème - 3ème' },
  { code: 'LYC', name: 'Lycée', disabled: false, hint: '2nde - Terminale' },
]

function SubjectHoursPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [activeCycle, setActiveCycle] = useState<string>('COLL')
  const [matrixData, setMatrixData] = useState<Map<string, SubjectHoursMatrixRow[]>>(new Map())
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)

  // API Queries
  const { data: levelsData } = useLevels()
  const { data: cyclesData } = useCycles()
  const { data: templatesData } = useCurriculumTemplates()

  // Matrix data query for current cycle
  const {
    data: matrixResponse,
    isLoading: matrixLoading,
    error: matrixError,
  } = useSubjectHoursMatrix(selectedVersionId ?? null, activeCycle)

  // Mutations
  const batchSaveMutation = useBatchSaveSubjectHours()
  const applyTemplateMutation = useApplyTemplate()
  const createSubjectMutation = useCreateSubject()

  // Get levels for current cycle
  const levelsForCycle = useMemo(() => {
    if (!levelsData || !cyclesData) return []
    const cycleId = cyclesData.find((c) => c.code === activeCycle)?.id
    if (!cycleId) return []
    return levelsData
      .filter((l) => l.cycle_id === cycleId)
      .sort((a, b) => a.sort_order - b.sort_order)
  }, [levelsData, cyclesData, activeCycle])

  // Transform API data to matrix rows when data loads
  useEffect(() => {
    if (matrixResponse && levelsForCycle.length > 0) {
      const rows = transformToMatrixRows(
        matrixResponse.subjects,
        levelsForCycle.map((l) => ({
          id: l.id,
          code: l.code,
          name_en: l.name_en,
          name_fr: l.name_fr,
          sort_order: l.sort_order,
        }))
      )
      setMatrixData((prev) => new Map(prev).set(activeCycle, rows))
      setHasUnsavedChanges(false)
    }
  }, [matrixResponse, levelsForCycle, activeCycle])

  // Get current cycle's matrix data
  const currentMatrixData = useMemo(() => {
    return matrixData.get(activeCycle) ?? []
  }, [matrixData, activeCycle])

  // Handle data changes from matrix
  const handleDataChange = useCallback(
    (newRows: SubjectHoursMatrixRow[]) => {
      setMatrixData((prev) => new Map(prev).set(activeCycle, newRows))
      setHasUnsavedChanges(true)
    },
    [activeCycle]
  )

  // Calculate statistics
  const statistics = useMemo(() => {
    const rows = currentMatrixData
    const dirtyRows = rows.filter((r) => r.isDirty)
    const totalSubjects = rows.filter((r) => r.isApplicable).length
    const configuredSubjects = rows.filter(
      (r) => r.isApplicable && Object.values(r.hours).some((h) => h !== null && h > 0)
    ).length

    // Calculate total hours for this cycle
    let totalHours = 0
    for (const row of rows) {
      if (row.isApplicable) {
        for (const hours of Object.values(row.hours)) {
          if (hours !== null && hours > 0) {
            totalHours += hours
          }
        }
      }
    }

    // Check if all rows are valid
    const allValid = rows.every((r) => r.isValid)

    return {
      totalSubjects,
      configuredSubjects,
      totalHours,
      dirtyCount: dirtyRows.length,
      allValid,
      isComplete: configuredSubjects === totalSubjects,
    }
  }, [currentMatrixData])

  // Handle save
  const handleSave = async () => {
    if (!selectedVersionId || !statistics.allValid) return

    const dirtyRows = currentMatrixData.filter((r) => r.isDirty)
    if (dirtyRows.length === 0) {
      toastMessages.warning.unsavedChanges()
      return
    }

    const entries = transformToEntries(
      dirtyRows,
      levelsForCycle.map((l) => ({
        id: l.id,
        code: l.code,
        name_en: l.name_en,
        name_fr: l.name_fr,
        sort_order: l.sort_order,
      })),
      true
    )

    try {
      await batchSaveMutation.mutateAsync({
        budget_version_id: selectedVersionId,
        entries: entries.map((e) => ({
          subject_id: e.subject_id,
          level_id: e.level_id,
          hours_per_week: e.hours_per_week,
          is_split: e.is_split,
          notes: e.notes,
        })),
      })

      // Mark all rows as not dirty
      const updatedRows = currentMatrixData.map((r) => ({ ...r, isDirty: false }))
      setMatrixData((prev) => new Map(prev).set(activeCycle, updatedRows))
      setHasUnsavedChanges(false)
    } catch {
      // Error handled by mutation
    }
  }

  // Handle template application
  const handleApplyTemplate = async (templateCode: string, overwriteExisting: boolean) => {
    if (!selectedVersionId) return

    try {
      await applyTemplateMutation.mutateAsync({
        budget_version_id: selectedVersionId,
        template_code: templateCode,
        cycle_codes: [activeCycle],
        overwrite_existing: overwriteExisting,
      })
      // Data will be refreshed via query invalidation
    } catch {
      // Error handled by mutation
    }
  }

  // Handle adding new subject
  const handleAddSubject = async (data: {
    code: string
    name_fr: string
    name_en: string
    category: string
    applicable_cycles: string[]
  }) => {
    try {
      await createSubjectMutation.mutateAsync({
        code: data.code,
        name_fr: data.name_fr,
        name_en: data.name_en,
        category: data.category as 'core' | 'elective' | 'specialty' | 'local',
        applicable_cycles: data.applicable_cycles,
      })
      toastMessages.success.created('Subject')
    } catch {
      // Error handled by mutation
    }
  }

  // Get existing subject codes for validation
  const existingSubjectCodes = useMemo(() => {
    return currentMatrixData.map((r) => r.subjectCode)
  }, [currentMatrixData])

  return (
    <PageContainer
      title="Subject Hours Configuration"
      description="Configure weekly teaching hours for each subject by academic level"
    >
      <div className="space-y-6">
        {/* Version Selection Warning */}
        {!selectedVersionId && (
          <div className="flex items-center gap-2 p-4 bg-subtle border border-border-light rounded-lg">
            <AlertCircle className="h-4 w-4 text-sand-600" />
            <p className="text-sm text-sand-800">
              Please select a budget version to configure subject hours.
            </p>
          </div>
        )}

        {selectedVersionId && (
          <>
            {/* Cycle Tabs with Actions */}
            <Tabs value={activeCycle} onValueChange={setActiveCycle}>
              <div className="flex items-center justify-between mb-4">
                <TabsList>
                  {CYCLE_TABS.map((tab) => (
                    <TabsTrigger
                      key={tab.code}
                      value={tab.code}
                      disabled={tab.disabled}
                      title={tab.hint}
                    >
                      {tab.name}
                      {tab.disabled && (
                        <span className="ml-1 text-xs text-muted-foreground">(N/A)</span>
                      )}
                    </TabsTrigger>
                  ))}
                </TabsList>

                {/* Action Buttons */}
                <div className="flex items-center gap-2">
                  <TemplateSelector
                    templates={templatesData ?? []}
                    currentCycleCode={activeCycle}
                    onApplyTemplate={handleApplyTemplate}
                    isApplying={applyTemplateMutation.isPending}
                    disabled={!selectedVersionId}
                  />
                  <AddSubjectDialog
                    onAddSubject={handleAddSubject}
                    isAdding={createSubjectMutation.isPending}
                    existingCodes={existingSubjectCodes}
                  />
                </div>
              </div>

              {/* Tab Content - Matrix Grid */}
              {CYCLE_TABS.filter((t) => !t.disabled).map((tab) => (
                <TabsContent key={tab.code} value={tab.code} className="space-y-4">
                  {/* Summary Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <SummaryCard
                      title="Subjects"
                      value={`${statistics.configuredSubjects} / ${statistics.totalSubjects}`}
                      subtitle={
                        statistics.isComplete ? 'All configured' : 'Some need configuration'
                      }
                      icon={
                        statistics.isComplete ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-amber-500" />
                        )
                      }
                    />
                    <SummaryCard
                      title="Total Hours"
                      value={`${statistics.totalHours.toFixed(1)}h`}
                      subtitle={`Weekly for ${tab.name}`}
                    />
                    <SummaryCard
                      title="Unsaved Changes"
                      value={statistics.dirtyCount}
                      subtitle={hasUnsavedChanges ? 'Click Save to persist' : 'All saved'}
                      trend={statistics.dirtyCount > 0 ? 'stable' : 'up'}
                    />
                    <SummaryCard
                      title="Validation"
                      value={statistics.allValid ? 'Valid' : 'Has Errors'}
                      subtitle={
                        statistics.allValid ? 'All values in range (0-12h)' : 'Fix invalid values'
                      }
                      trend={statistics.allValid ? 'up' : 'down'}
                      icon={
                        statistics.allValid ? (
                          <CheckCircle className="h-4 w-4 text-green-500" />
                        ) : (
                          <AlertCircle className="h-4 w-4 text-red-500" />
                        )
                      }
                    />
                  </div>

                  {/* Matrix Grid */}
                  <SubjectHoursMatrix
                    levels={levelsForCycle.map((l) => ({
                      id: l.id,
                      code: l.code,
                      name_en: l.name_en,
                      name_fr: l.name_fr,
                      sort_order: l.sort_order,
                    }))}
                    rowData={currentMatrixData}
                    onDataChange={handleDataChange}
                    isLoading={matrixLoading}
                    error={matrixError}
                  />
                </TabsContent>
              ))}
            </Tabs>

            {/* Save Button Bar */}
            <div className="flex items-center justify-between pt-4 border-t">
              <p className="text-sm text-muted-foreground">
                Edit cells directly. Hours must be between 0 and 12 per week.
                {hasUnsavedChanges && (
                  <span className="ml-2 text-amber-600">
                    You have unsaved changes ({statistics.dirtyCount} rows modified).
                  </span>
                )}
              </p>
              <Button
                onClick={handleSave}
                disabled={!hasUnsavedChanges || !statistics.allValid || batchSaveMutation.isPending}
              >
                <Save className="h-4 w-4 mr-2" />
                {batchSaveMutation.isPending ? 'Saving...' : 'Save Changes'}
                {hasUnsavedChanges && (
                  <Badge variant="secondary" className="ml-2 bg-amber-100 text-amber-800">
                    {statistics.dirtyCount}
                  </Badge>
                )}
              </Button>
            </div>
          </>
        )}
      </div>
    </PageContainer>
  )
}
