import { PlanningProgressResponse } from '@/types/planning-progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { CheckCircle2, AlertCircle, AlertTriangle, Lock } from 'lucide-react'
import { useMemo } from 'react'

interface ProgressOverviewProps {
  progress: PlanningProgressResponse
}

export function ProgressOverview({ progress }: ProgressOverviewProps) {
  // Calculate status counts
  const statusCounts = useMemo(() => {
    const counts = {
      completed: 0,
      in_progress: 0,
      error: 0,
      blocked: 0,
      warnings: 0,
    }

    progress.steps.forEach((step) => {
      if (step.status === 'completed') counts.completed++
      else if (step.status === 'in_progress') counts.in_progress++
      else if (step.status === 'error') counts.error++
      else if (step.status === 'blocked') counts.blocked++

      // Count warnings across all validations
      step.validation.forEach((v) => {
        if (v.status === 'warning') counts.warnings++
      })
    })

    return counts
  }, [progress.steps])

  // Determine overall status color
  const getProgressColor = (percentage: number, hasErrors: boolean, hasBlockers: boolean) => {
    if (hasBlockers) return 'text-twilight-600'
    if (hasErrors) return 'text-error-600'
    if (percentage === 100) return 'text-success-600'
    if (percentage >= 67) return 'text-success-500'
    if (percentage >= 34) return 'text-info-600'
    return 'text-warning-600'
  }

  const progressColor = getProgressColor(
    progress.overall_progress,
    statusCounts.error > 0,
    statusCounts.blocked > 0
  )

  const getProgressBarColor = () => {
    if (statusCounts.blocked > 0) return 'bg-twilight-400'
    if (statusCounts.error > 0) return 'bg-error-500'
    if (progress.overall_progress === 100) return 'bg-success-500'
    if (progress.overall_progress >= 67) return 'bg-success-400'
    if (progress.overall_progress >= 34) return 'bg-info-500'
    return 'bg-warning-500'
  }

  return (
    <Card className="border-l-4 border-l-gold-500 shadow-lg">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-2xl font-serif text-brown-800">
              Overall Planning Progress
            </CardTitle>
            <p className="text-sm text-twilight-600 mt-1">
              Track your progress across all 6 planning steps
            </p>
          </div>
          <div className="text-right">
            <div className={`text-5xl font-bold ${progressColor}`}>
              {Math.round(progress.overall_progress)}%
            </div>
            <p className="text-sm text-twilight-600 mt-1">
              {progress.completed_steps} of {progress.total_steps} completed
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Progress Bar */}
        <div className="mb-6">
          <div className="w-full bg-sand-200 rounded-full h-4 overflow-hidden">
            <div
              className={`h-4 rounded-full transition-all duration-500 ease-out ${getProgressBarColor()}`}
              style={{ width: `${progress.overall_progress}%` }}
            />
          </div>
        </div>

        {/* Status Badges */}
        <div className="flex flex-wrap gap-3">
          {progress.completed_steps > 0 && (
            <Badge variant="success" className="flex items-center gap-1.5 px-3 py-1">
              <CheckCircle2 className="h-4 w-4" />
              {progress.completed_steps} Completed
            </Badge>
          )}

          {statusCounts.in_progress > 0 && (
            <Badge variant="warning" className="flex items-center gap-1.5 px-3 py-1">
              <AlertCircle className="h-4 w-4" />
              {statusCounts.in_progress} In Progress
            </Badge>
          )}

          {statusCounts.warnings > 0 && (
            <Badge variant="warning" className="flex items-center gap-1.5 px-3 py-1">
              <AlertTriangle className="h-4 w-4" />
              {statusCounts.warnings} Warnings
            </Badge>
          )}

          {statusCounts.error > 0 && (
            <Badge variant="destructive" className="flex items-center gap-1.5 px-3 py-1">
              <AlertCircle className="h-4 w-4" />
              {statusCounts.error} Errors
            </Badge>
          )}

          {statusCounts.blocked > 0 && (
            <Badge variant="secondary" className="flex items-center gap-1.5 px-3 py-1">
              <Lock className="h-4 w-4" />
              {statusCounts.blocked} Blocked
            </Badge>
          )}
        </div>

        {/* Next Action Suggestion */}
        {progress.overall_progress < 100 && (
          <div className="mt-6 p-4 bg-info-50 border border-info-200 rounded-lg">
            <p className="text-sm text-info-800">
              <strong>Next Step:</strong>{' '}
              {(() => {
                const nextStep = progress.steps.find(
                  (s) => s.status === 'not_started' || s.status === 'in_progress'
                )
                if (nextStep) {
                  const metadata = progress.steps.find((s) => s.step_id === nextStep.step_id)
                  return `Complete ${metadata?.step_id.replace('_', ' ')} (Step ${nextStep.step_number})`
                }
                return 'Review and resolve any errors or warnings'
              })()}
            </p>
          </div>
        )}

        {progress.overall_progress === 100 && (
          <div className="mt-6 p-4 bg-success-50 border border-success-200 rounded-lg">
            <p className="text-sm text-success-800 font-medium">
              🎉 Congratulations! All planning steps are completed. You can now proceed to budget
              consolidation.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
