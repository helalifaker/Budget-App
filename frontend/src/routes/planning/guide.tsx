import { createFileRoute, Link } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { Button } from '@/components/ui/button'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'
import { usePlanningProgress } from '@/hooks/api/usePlanningProgress'
import { ProgressOverview } from '@/components/planning-guide/ProgressOverview'
import { ProgressTimeline } from '@/components/planning-guide/ProgressTimeline'
import { StepCard } from '@/components/planning-guide/StepCard'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { BookOpen, Plus } from 'lucide-react'

export const Route = createFileRoute('/planning/guide')({
  beforeLoad: requireAuth,
  component: PlanningGuidePage,
})

function PlanningGuidePage() {
  const { selectedVersionId } = useBudgetVersion()

  const { data: versions, isLoading: versionsLoading } = useBudgetVersions()
  const { data: progressData, isLoading: progressLoading } = usePlanningProgress(selectedVersionId)

  const hasVersions = versions?.items && versions.items.length > 0

  return (
    <MainLayout>
      <PageContainer
        title="Planning Guide & Progress Tracker"
        description="Step-by-step guide through the budget planning process with real-time validation"
      >
        {/* Empty State - No Budget Versions */}
        {!versionsLoading && !hasVersions && (
          <div className="text-center py-16 bg-gradient-to-br from-sand-50 to-gold-50 rounded-lg border-2 border-dashed border-gold-300">
            <div className="max-w-md mx-auto space-y-6">
              <div className="w-16 h-16 bg-gold-100 rounded-full flex items-center justify-center mx-auto">
                <BookOpen className="h-8 w-8 text-gold-600" />
              </div>
              <div>
                <h3 className="text-xl font-semibold text-brown-800 mb-2">
                  Welcome to the Planning Guide
                </h3>
                <p className="text-twilight-700 mb-4">
                  To begin planning your budget, you need to create a budget version first.
                </p>
                <p className="text-sm text-twilight-600 mb-6">
                  A budget version represents a specific fiscal year and scenario (e.g., "2025-2026
                  Budget", "Conservative Forecast", etc.)
                </p>
              </div>
              <Button asChild size="lg" className="gap-2">
                <Link to="/configuration/versions">
                  <Plus className="h-5 w-5" />
                  Create Your First Budget Version
                </Link>
              </Button>
            </div>
          </div>
        )}

        {/* Select Version Prompt */}
        {!versionsLoading && hasVersions && !selectedVersionId && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <BookOpen className="h-16 w-16 text-sand-400 mb-4" />
            <h3 className="text-xl font-semibold text-brown-800 mb-2">Select a Budget Version</h3>
            <p className="text-twilight-600 max-w-md">
              Choose a budget version above to view your planning progress and get step-by-step
              guidance through the budget planning process.
            </p>
          </div>
        )}

        {/* Loading State */}
        {selectedVersionId && progressLoading && (
          <div className="flex items-center justify-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-gold-500" />
          </div>
        )}

        {/* Planning Progress Display */}
        {selectedVersionId && progressData && (
          <div className="space-y-8 animate-fadeIn">
            {/* Overall Progress Overview */}
            <ProgressOverview progress={progressData} />

            {/* Timeline Visual */}
            <ProgressTimeline steps={progressData.steps} />

            {/* Step Cards */}
            <div className="space-y-6">
              {progressData.steps.map((step, index) => (
                <StepCard key={step.step_id} step={step} stepNumber={index + 1} />
              ))}
            </div>
          </div>
        )}
      </PageContainer>
    </MainLayout>
  )
}
