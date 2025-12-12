/**
 * Enrollment Planning Page - /enrollment/planning
 *
 * Projection-driven enrollment planner (Retention + Lateral Entry).
 * Features:
 * - Step-by-step workflow with numbered tabs
 * - Contextual explanations via StepIntroCard
 * - Help tooltips on all fields
 * - Clear navigation between steps
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useCallback, useMemo, useRef, useState } from 'react'
import { ArrowRight } from 'lucide-react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Button } from '@/components/ui/button'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useCycles, useLevels } from '@/hooks/api/useConfiguration'
import {
  useCalculateProjections,
  useEnrollmentProjectionConfig,
  useEnrollmentProjectionResults,
  useEnrollmentScenarios,
  useUnvalidateProjections,
  useUpdateGlobalOverrides,
  useUpdateGradeOverrides,
  useUpdateLevelOverrides,
  useUpdateProjectionConfig,
  useValidateProjections,
} from '@/hooks/api/useEnrollmentProjection'
import { toastMessages } from '@/lib/toast-messages'
import { ScenarioSelector } from '@/components/enrollment/ScenarioSelector'
import {
  BasicOverridesPanel,
  AdvancedOverridesPanel,
} from '@/components/enrollment/GlobalOverridesPanel'
import { LevelOverridesPanel } from '@/components/enrollment/LevelOverridesPanel'
import { GradeOverridesGrid } from '@/components/enrollment/GradeOverridesGrid'
import { ProjectionResultsGrid } from '@/components/enrollment/ProjectionResultsGrid'
import { NationalityDistributionPanel } from '@/components/enrollment/NationalityDistributionPanel'
import { CapacityWarningBanner } from '@/components/enrollment/CapacityWarningBanner'
import { ValidationConfirmDialog } from '@/components/enrollment/ValidationConfirmDialog'
import { StepIntroCard } from '@/components/enrollment/StepIntroCard'
import { AdvancedFeaturesSection } from '@/components/enrollment/AdvancedFeaturesSection'
import { WelcomeDialog } from '@/components/enrollment/WelcomeDialog'
import { WhatsNextCard } from '@/components/enrollment/WhatsNextCard'
import { ProjectionSummaryCard } from '@/components/enrollment/ProjectionSummaryCard'
import { ContextualTip } from '@/components/ui/ContextualTip'
import { STEP_INTRO_CONTENT } from '@/constants/enrollment-field-definitions'
import type { GlobalOverrides, GradeOverride, LevelOverride } from '@/types/enrollmentProjection'

interface LevelLike {
  id: string
  code: string
  name_fr?: string | null
  name_en?: string | null
  sort_order?: number | null
  cycle_id?: string | null
  cycle?: { code: string } | null
}

interface CycleLike {
  id: string
  code: string
  name_fr?: string | null
  name_en?: string | null
}

export const Route = createFileRoute('/_authenticated/enrollment/planning')({
  beforeLoad: requireAuth,
  component: EnrollmentPlanningPage,
})

function EnrollmentPlanningPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [activeTab, setActiveTab] = useState<'projections' | 'distribution' | 'validation'>(
    'projections'
  )
  const resultsRef = useRef<HTMLDivElement>(null)

  const { data: scenarios = [] } = useEnrollmentScenarios()
  const { data: config, isLoading: configLoading } =
    useEnrollmentProjectionConfig(selectedVersionId)
  const { data: results, isLoading: resultsLoading } =
    useEnrollmentProjectionResults(selectedVersionId)

  const { data: levels = [] } = useLevels()
  const { data: cycles = [] } = useCycles()

  const updateConfig = useUpdateProjectionConfig()
  const updateGlobal = useUpdateGlobalOverrides()
  const updateLevel = useUpdateLevelOverrides()
  const updateGrade = useUpdateGradeOverrides()
  const calculate = useCalculateProjections()
  const validate = useValidateProjections()
  const unvalidate = useUnvalidateProjections()

  const disabled = config?.status === 'validated'

  const selectedScenarioId = config?.scenario_id ?? null

  // PERFORMANCE FIX: Memoize handlers with useCallback to prevent child re-renders
  const onSelectScenario = useCallback(
    (scenarioId: string) => {
      if (!selectedVersionId) {
        toastMessages.warning.selectVersion()
        return
      }
      updateConfig.mutate({
        versionId: selectedVersionId,
        updates: { scenario_id: scenarioId },
      })
    },
    [selectedVersionId, updateConfig]
  )

  const onGlobalChange = useCallback(
    (patch: Partial<GlobalOverrides>) => {
      if (!selectedVersionId) return
      const current = config?.global_overrides ?? {
        ps_entry_adjustment: null,
        retention_adjustment: null,
        lateral_multiplier_override: null,
        class_size_override: null,
      }
      updateGlobal.mutate({
        versionId: selectedVersionId,
        overrides: { ...current, ...patch },
      })
    },
    [selectedVersionId, config?.global_overrides, updateGlobal]
  )

  const onLevelChange = useCallback(
    (rows: LevelOverride[]) => {
      if (!selectedVersionId) return
      updateLevel.mutate({
        versionId: selectedVersionId,
        overrides: rows.map((r) => ({
          cycle_id: r.cycle_id,
          class_size_ceiling: r.class_size_ceiling,
          max_divisions: r.max_divisions,
        })),
      })
    },
    [selectedVersionId, updateLevel]
  )

  const onGradeChange = useCallback(
    (rows: GradeOverride[]) => {
      if (!selectedVersionId) return
      updateGrade.mutate({
        versionId: selectedVersionId,
        overrides: rows.map((r) => ({
          level_id: r.level_id,
          retention_rate: r.retention_rate,
          lateral_entry: r.lateral_entry,
          max_divisions: r.max_divisions,
          class_size_ceiling: r.class_size_ceiling,
        })),
      })
    },
    [selectedVersionId, updateGrade]
  )

  const isLoading = configLoading || resultsLoading

  const projections = results?.projections ?? []
  const maxCapacity = results?.config.school_max_capacity ?? config?.school_max_capacity ?? 1850

  const levelsSorted = useMemo(() => {
    const copy = [...(levels as unknown as LevelLike[])]
    copy.sort((a, b) => (a.sort_order ?? 0) - (b.sort_order ?? 0))
    return copy
  }, [levels])

  const onTabChange = (value: string) => {
    if (value === 'projections' || value === 'distribution' || value === 'validation') {
      setActiveTab(value)
    }
  }

  // Navigate to next tab
  const goToNextTab = () => {
    if (activeTab === 'projections') setActiveTab('distribution')
    else if (activeTab === 'distribution') setActiveTab('validation')
  }

  // Navigate to previous tab
  const goToPreviousTab = () => {
    if (activeTab === 'validation') setActiveTab('distribution')
    else if (activeTab === 'distribution') setActiveTab('projections')
  }

  // Scroll to results section
  const scrollToResults = () => {
    resultsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  // Handle unlocking projections for editing
  const handleUnlockForEdit = () => {
    if (selectedVersionId) {
      unvalidate.mutate(selectedVersionId)
      setActiveTab('projections')
    }
  }

  return (
    <div className="space-y-6">
      {/* Welcome Dialog for first-time users */}
      <WelcomeDialog />

      <Tabs value={activeTab} onValueChange={onTabChange}>
        {/* Numbered Tab List */}
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="projections" className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sage/20 text-xs font-bold text-sage">
              1
            </span>
            Projections
          </TabsTrigger>
          <TabsTrigger value="distribution" className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sage/20 text-xs font-bold text-sage">
              2
            </span>
            Distribution
          </TabsTrigger>
          <TabsTrigger value="validation" className="flex items-center gap-2">
            <span className="flex h-5 w-5 items-center justify-center rounded-full bg-sage/20 text-xs font-bold text-sage">
              3
            </span>
            Validation
          </TabsTrigger>
        </TabsList>

        {/* Tab 1: Projections */}
        <TabsContent value="projections" className="space-y-6">
          {/* Step Introduction Card */}
          <StepIntroCard
            stepNumber={STEP_INTRO_CONTENT.projections.stepNumber}
            title={STEP_INTRO_CONTENT.projections.title}
            why={STEP_INTRO_CONTENT.projections.why}
            whatToDo={STEP_INTRO_CONTENT.projections.whatToDo}
            tip={STEP_INTRO_CONTENT.projections.tip}
          />

          {/* Action bar */}
          <div className="flex justify-end">
            <Button
              type="button"
              variant="default"
              onClick={() => selectedVersionId && calculate.mutate(selectedVersionId)}
              disabled={!selectedVersionId || calculate.isPending}
            >
              {calculate.isPending ? 'Calculating...' : 'Calculate Projections'}
            </Button>
          </div>

          {/* Contextual Tip for Scenario Selection */}
          <ContextualTip tipId="scenario-selection-hint" variant="compact">
            Most schools start with the "Base Case" scenario. Only adjust parameters if you have
            specific information about changes expected next year.
          </ContextualTip>

          {/* Scenario Selection */}
          <ScenarioSelector
            scenarios={scenarios}
            selectedScenarioId={selectedScenarioId}
            onSelect={onSelectScenario}
            disabled={disabled}
          />

          {/* Basic Adjustments (always visible) */}
          {config && (
            <BasicOverridesPanel
              overrides={config.global_overrides}
              onChange={onGlobalChange}
              disabled={disabled}
            />
          )}

          {/* Advanced Features Section (checkbox-gated) */}
          {config && (
            <AdvancedFeaturesSection disabled={disabled}>
              {/* Advanced Global Overrides */}
              <AdvancedOverridesPanel
                overrides={config.global_overrides}
                onChange={onGlobalChange}
                disabled={disabled}
              />

              {/* Cycle-Level Overrides */}
              <LevelOverridesPanel
                cycles={cycles as unknown as CycleLike[]}
                overrides={config.level_overrides}
                onChange={onLevelChange}
                disabled={disabled}
              />

              {/* Grade-Level Overrides */}
              <GradeOverridesGrid
                levels={levelsSorted}
                overrides={config.grade_overrides}
                onChange={onGradeChange}
                disabled={disabled}
              />
            </AdvancedFeaturesSection>
          )}

          {/* Projection Summary Card */}
          {projections.length > 0 && (
            <ProjectionSummaryCard
              projections={projections}
              maxCapacity={maxCapacity}
              onViewDetails={scrollToResults}
            />
          )}

          {/* Capacity Warning */}
          {projections.length > 0 && (
            <CapacityWarningBanner projections={projections} maxCapacity={maxCapacity} />
          )}

          {/* Results Grid */}
          <div ref={resultsRef}>
            {projections.length > 0 && <ProjectionResultsGrid projections={projections} />}
          </div>

          {/* Loading State */}
          {isLoading && (
            <div className="flex items-center justify-center p-8">
              <div className="text-sm text-text-secondary">Loading projection data...</div>
            </div>
          )}

          {/* Continue Button */}
          <div className="flex justify-end pt-4 border-t border-border-light">
            <Button type="button" onClick={goToNextTab} className="gap-2">
              Continue to Step 2: Distribution
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </TabsContent>

        {/* Tab 2: Distribution */}
        <TabsContent value="distribution" className="space-y-6">
          {/* Step Introduction Card */}
          <StepIntroCard
            stepNumber={STEP_INTRO_CONTENT.distribution.stepNumber}
            title={STEP_INTRO_CONTENT.distribution.title}
            why={STEP_INTRO_CONTENT.distribution.why}
            whatToDo={STEP_INTRO_CONTENT.distribution.whatToDo}
            tip={STEP_INTRO_CONTENT.distribution.tip}
          />

          {/* Distribution Panel */}
          <NationalityDistributionPanel versionId={selectedVersionId} disabled={disabled} />

          {/* Navigation Buttons */}
          <div className="flex justify-between pt-4 border-t border-border-light">
            <Button type="button" variant="outline" onClick={goToPreviousTab}>
              Back to Projections
            </Button>
            <Button type="button" onClick={goToNextTab} className="gap-2">
              Continue to Step 3: Validation
              <ArrowRight className="h-4 w-4" />
            </Button>
          </div>
        </TabsContent>

        {/* Tab 3: Validation */}
        <TabsContent value="validation" className="space-y-6">
          {/* Step Introduction Card */}
          <StepIntroCard
            stepNumber={STEP_INTRO_CONTENT.validation.stepNumber}
            title={STEP_INTRO_CONTENT.validation.title}
            why={STEP_INTRO_CONTENT.validation.why}
            whatToDo={STEP_INTRO_CONTENT.validation.whatToDo}
            tip={STEP_INTRO_CONTENT.validation.tip}
          />

          {/* Validation Dialog or WhatsNextCard based on status */}
          {config && config.status === 'validated' ? (
            <WhatsNextCard onEdit={handleUnlockForEdit} />
          ) : (
            config && (
              <ValidationConfirmDialog
                status={config.status}
                onValidate={(confirmation) =>
                  selectedVersionId &&
                  validate.mutate({ versionId: selectedVersionId, confirmation })
                }
                onUnvalidate={() => selectedVersionId && unvalidate.mutate(selectedVersionId)}
                disabled={!selectedVersionId}
              />
            )
          )}

          {/* Results Preview */}
          {projections.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium text-text-secondary">Projection Summary</h4>
              <ProjectionSummaryCard projections={projections} maxCapacity={maxCapacity} />
              <ProjectionResultsGrid projections={projections} />
            </div>
          )}

          {/* Navigation Button */}
          <div className="flex justify-start pt-4 border-t border-border-light">
            <Button type="button" variant="outline" onClick={goToPreviousTab}>
              Back to Distribution
            </Button>
          </div>
        </TabsContent>
      </Tabs>
    </div>
  )
}
