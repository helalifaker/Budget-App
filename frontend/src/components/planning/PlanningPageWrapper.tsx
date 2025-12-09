/**
 * PlanningPageWrapper - Step navigation wrapper for all planning pages
 *
 * Provides consistent navigation experience across all 6 planning steps:
 * - Step indicator header (e.g., "Step 1 of 6: Enrollment Planning")
 * - Breadcrumb navigation
 * - Previous/Next step buttons
 * - Link to planning guide
 * - Status-aware navigation (blocks access to unavailable steps)
 */

import { ReactNode, useMemo } from 'react'
import { Link, useNavigate } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  ChevronLeft,
  ChevronRight,
  BookOpen,
  CheckCircle2,
  AlertTriangle,
  Lock,
  Circle,
  AlertCircle,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { usePlanningProgress } from '@/hooks/api/usePlanningProgress'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { STEP_METADATA, StepProgress } from '@/types/planning-progress'

// Step order for navigation
const STEP_ORDER = ['enrollment', 'class_structure', 'dhg', 'revenue', 'costs', 'capex'] as const
type StepId = (typeof STEP_ORDER)[number]

interface PlanningPageWrapperProps {
  /** Current step ID */
  stepId: StepId
  /** Optional subtitle for breadcrumb (e.g., "By Level", "Subject Hours") */
  subtitle?: string
  /** Optional action buttons to display in the header */
  actions?: ReactNode
  /** Child content (the actual planning page) */
  children: ReactNode
}

/**
 * Get status icon for a step
 */
function getStatusIcon(status: StepProgress['status'] | undefined, className = 'h-4 w-4') {
  switch (status) {
    case 'completed':
      return <CheckCircle2 className={cn(className, 'text-success-600')} />
    case 'in_progress':
      return <AlertTriangle className={cn(className, 'text-warning-600')} />
    case 'error':
      return <AlertCircle className={cn(className, 'text-error-600')} />
    case 'blocked':
      return <Lock className={cn(className, 'text-text-secondary')} />
    default:
      return <Circle className={cn(className, 'text-sand-400')} />
  }
}

/**
 * Get status badge variant
 */
function getStatusVariant(
  status: StepProgress['status'] | undefined
): 'default' | 'success' | 'warning' | 'destructive' | 'secondary' {
  switch (status) {
    case 'completed':
      return 'success'
    case 'in_progress':
      return 'warning'
    case 'error':
      return 'destructive'
    case 'blocked':
      return 'secondary'
    default:
      return 'default'
  }
}

/**
 * Get status label
 */
function getStatusLabel(status: StepProgress['status'] | undefined): string {
  switch (status) {
    case 'completed':
      return 'Completed'
    case 'in_progress':
      return 'In Progress'
    case 'error':
      return 'Has Errors'
    case 'blocked':
      return 'Blocked'
    default:
      return 'Not Started'
  }
}

export function PlanningPageWrapper({
  stepId,
  subtitle,
  actions,
  children,
}: PlanningPageWrapperProps) {
  const navigate = useNavigate()
  const { selectedVersionId } = useBudgetVersion()
  const { data: progressData } = usePlanningProgress(selectedVersionId)

  // Get current step metadata
  const currentMetadata = STEP_METADATA[stepId]
  const currentStepNumber = STEP_ORDER.indexOf(stepId) + 1
  const totalSteps = STEP_ORDER.length

  // Find previous and next steps
  const previousStepId = currentStepNumber > 1 ? STEP_ORDER[currentStepNumber - 2] : null
  const nextStepId = currentStepNumber < totalSteps ? STEP_ORDER[currentStepNumber] : null

  const previousMetadata = previousStepId ? STEP_METADATA[previousStepId] : null
  const nextMetadata = nextStepId ? STEP_METADATA[nextStepId] : null

  // Get step progress statuses
  const stepStatuses = useMemo(() => {
    if (!progressData?.steps) return {}
    return progressData.steps.reduce(
      (acc, step) => {
        acc[step.step_id] = step
        return acc
      },
      {} as Record<string, StepProgress>
    )
  }, [progressData?.steps])

  const currentStepProgress = stepStatuses[stepId]
  const nextStepProgress = nextStepId ? stepStatuses[nextStepId] : null

  // Check if next step is accessible (not blocked)
  const isNextAccessible = nextStepProgress?.status !== 'blocked'

  // Navigation handlers
  const handlePrevious = () => {
    if (previousMetadata) {
      navigate({ to: previousMetadata.route })
    }
  }

  const handleNext = () => {
    if (nextMetadata && isNextAccessible) {
      navigate({ to: nextMetadata.route })
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Step Header */}
      <div className="bg-white border-b border-border-light px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Left: Step indicator and title */}
          <div className="flex items-center gap-4">
            {/* Step number badge */}
            <Badge
              variant="outline"
              className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold border-2 border-gold-500 bg-gold-50 text-gold-700"
            >
              {currentStepNumber}
            </Badge>

            <div>
              <div className="flex items-center gap-2">
                <span className="text-sm text-text-secondary">
                  Step {currentStepNumber} of {totalSteps}
                </span>
                {currentStepProgress && (
                  <Badge
                    variant={getStatusVariant(currentStepProgress.status)}
                    className="flex items-center gap-1"
                  >
                    {getStatusIcon(currentStepProgress.status, 'h-3 w-3')}
                    {getStatusLabel(currentStepProgress.status)}
                  </Badge>
                )}
              </div>
              <h1 className="text-xl font-semibold text-text-primary font-serif">
                {currentMetadata?.title}
              </h1>
            </div>
          </div>

          {/* Right: Actions and Guide link */}
          <div className="flex items-center gap-3">
            {actions}
            <Button variant="outline" size="sm" asChild className="gap-2">
              <Link to="/planning/guide">
                <BookOpen className="h-4 w-4" />
                Planning Guide
              </Link>
            </Button>
          </div>
        </div>

        {/* Breadcrumb */}
        <nav className="mt-3 flex items-center text-sm text-text-secondary">
          <Link to="/planning/guide" className="hover:text-text-primary transition-colors">
            Planning
          </Link>
          <ChevronRight className="h-4 w-4 mx-1" />
          <Link
            to={currentMetadata?.route || '#'}
            className="hover:text-text-primary transition-colors"
          >
            {currentMetadata?.title.replace(' Planning', '')}
          </Link>
          {subtitle && (
            <>
              <ChevronRight className="h-4 w-4 mx-1" />
              <span className="text-text-primary">{subtitle}</span>
            </>
          )}
        </nav>
      </div>

      {/* Main Content */}
      <div className="flex-1 overflow-auto">{children}</div>

      {/* Step Navigation Footer */}
      <div className="bg-white border-t border-border-light px-6 py-4">
        <div className="flex items-center justify-between">
          {/* Previous Button */}
          <div>
            {previousMetadata ? (
              <Button variant="outline" onClick={handlePrevious} className="gap-2">
                <ChevronLeft className="h-4 w-4" />
                <span className="hidden sm:inline">Previous:</span>{' '}
                {previousMetadata.title.replace(' Planning', '')}
              </Button>
            ) : (
              <div /> // Empty placeholder for flex alignment
            )}
          </div>

          {/* Progress indicator */}
          <div className="hidden md:flex items-center gap-2">
            {STEP_ORDER.map((stepOrderId, index) => {
              const status = stepStatuses[stepOrderId]?.status
              const isCurrent = stepOrderId === stepId
              return (
                <div
                  key={stepOrderId}
                  className={cn(
                    'w-3 h-3 rounded-full transition-all',
                    isCurrent && 'ring-2 ring-gold-500 ring-offset-2',
                    status === 'completed' && 'bg-success-500',
                    status === 'in_progress' && 'bg-warning-500',
                    status === 'error' && 'bg-error-500',
                    status === 'blocked' && 'bg-twilight-400',
                    (!status || status === 'not_started') && 'bg-subtle'
                  )}
                  title={`Step ${index + 1}: ${STEP_METADATA[stepOrderId]?.title}`}
                />
              )
            })}
          </div>

          {/* Next Button */}
          <div>
            {nextMetadata ? (
              <Button
                variant={isNextAccessible ? 'default' : 'outline'}
                onClick={handleNext}
                disabled={!isNextAccessible}
                className={cn('gap-2', !isNextAccessible && 'opacity-50 cursor-not-allowed')}
              >
                <span className="hidden sm:inline">Next:</span>{' '}
                {nextMetadata.title.replace(' Planning', '')}
                {!isNextAccessible ? (
                  <Lock className="h-4 w-4" />
                ) : (
                  <ChevronRight className="h-4 w-4" />
                )}
              </Button>
            ) : (
              <Button variant="default" asChild className="gap-2">
                <Link to="/finance/consolidation">
                  Review & Consolidate
                  <ChevronRight className="h-4 w-4" />
                </Link>
              </Button>
            )}
          </div>
        </div>

        {/* Blocked message */}
        {nextStepProgress?.status === 'blocked' && nextStepProgress.blockers.length > 0 && (
          <div className="mt-3 bg-twilight-50 border border-twilight-200 rounded-lg p-3 text-sm">
            <div className="flex items-center gap-2 text-text-secondary">
              <Lock className="h-4 w-4" />
              <span className="font-medium">Next step is blocked:</span>
              <span>{nextStepProgress.blockers[0]?.message}</span>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
