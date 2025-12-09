/**
 * PlanningWorkflowProgress - Step progress indicators for module planning workflow
 *
 * Displays the planning workflow as connected step cards with status indicators.
 * Each step shows: icon, title, metric value, and status (complete/in-progress/pending/warning)
 *
 * Used in module dashboards to visualize planning progress.
 */

import { cn } from '@/lib/utils'
import { CheckCircle2, Circle, AlertTriangle, Clock, type LucideIcon } from 'lucide-react'
import { motion } from 'framer-motion'

export type WorkflowStepStatus = 'complete' | 'in-progress' | 'pending' | 'warning' | 'error'

export interface WorkflowStep {
  id: string
  title: string
  metric?: string
  status: WorkflowStepStatus
  icon?: LucideIcon
}

interface PlanningWorkflowProgressProps {
  steps: WorkflowStep[]
  title?: string
  progress?: number // 0-100
  className?: string
}

/**
 * Get status styling and icon for a workflow step
 */
function getStepStatusInfo(status: WorkflowStepStatus) {
  switch (status) {
    case 'complete':
      return {
        icon: CheckCircle2,
        bgColor: 'bg-success-100',
        borderColor: 'border-success-300',
        iconColor: 'text-success-600',
        textColor: 'text-success-700',
      }
    case 'in-progress':
      return {
        icon: Clock,
        bgColor: 'bg-gold-100',
        borderColor: 'border-gold-300',
        iconColor: 'text-gold-600',
        textColor: 'text-gold-700',
      }
    case 'warning':
      return {
        icon: AlertTriangle,
        bgColor: 'bg-warning-100',
        borderColor: 'border-warning-300',
        iconColor: 'text-warning-600',
        textColor: 'text-warning-700',
      }
    case 'error':
      return {
        icon: AlertTriangle,
        bgColor: 'bg-error-100',
        borderColor: 'border-error-300',
        iconColor: 'text-error-600',
        textColor: 'text-error-700',
      }
    default:
      return {
        icon: Circle,
        bgColor: 'bg-subtle',
        borderColor: 'border-border-light',
        iconColor: 'text-text-muted',
        textColor: 'text-text-tertiary',
      }
  }
}

/**
 * Individual workflow step card
 */
function WorkflowStepCard({ step, isLast }: { step: WorkflowStep; isLast: boolean }) {
  const statusInfo = getStepStatusInfo(step.status)
  const StatusIcon = statusInfo.icon
  const StepIcon = step.icon

  return (
    <div className="flex items-center">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.2 }}
        className={cn(
          'relative flex flex-col items-center justify-center',
          'min-w-[100px] p-3 rounded-xl',
          'border-2 transition-all duration-200',
          statusInfo.bgColor,
          statusInfo.borderColor
        )}
      >
        {/* Status icon in top-right corner */}
        <div className="absolute -top-2 -right-2">
          <StatusIcon className={cn('w-5 h-5', statusInfo.iconColor)} />
        </div>

        {/* Step icon */}
        {StepIcon && <StepIcon className={cn('w-6 h-6 mb-1.5', statusInfo.iconColor)} />}

        {/* Title */}
        <span className={cn('text-xs font-medium text-center', statusInfo.textColor)}>
          {step.title}
        </span>

        {/* Metric value */}
        {step.metric && (
          <span className={cn('text-sm font-bold font-mono mt-0.5', statusInfo.textColor)}>
            {step.metric}
          </span>
        )}
      </motion.div>

      {/* Connector arrow */}
      {!isLast && (
        <div className="flex items-center px-2">
          <div className="w-4 h-0.5 bg-subtle" />
          <div className="w-0 h-0 border-t-4 border-b-4 border-l-4 border-t-transparent border-b-transparent border-l-border-medium" />
        </div>
      )}
    </div>
  )
}

export function PlanningWorkflowProgress({
  steps,
  title = 'Planning Workflow',
  progress,
  className,
}: PlanningWorkflowProgressProps) {
  // Calculate progress if not provided
  const calculatedProgress =
    progress ??
    Math.round((steps.filter((s) => s.status === 'complete').length / steps.length) * 100)

  return (
    <div className={cn('bg-white rounded-xl border border-border-light p-4', className)}>
      {/* Header with title and progress */}
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
        <div className="flex items-center gap-2">
          <div className="h-2 w-24 bg-subtle rounded-full overflow-hidden">
            <motion.div
              className={cn(
                'h-full rounded-full',
                calculatedProgress >= 100
                  ? 'bg-success-500'
                  : calculatedProgress >= 50
                    ? 'bg-gold-500'
                    : 'bg-slate-400'
              )}
              initial={{ width: 0 }}
              animate={{ width: `${calculatedProgress}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </div>
          <span className="text-sm font-bold text-text-primary font-mono">
            {calculatedProgress}%
          </span>
        </div>
      </div>

      {/* Workflow steps */}
      <div className="flex items-center justify-center flex-wrap gap-y-3">
        {steps.map((step, index) => (
          <WorkflowStepCard key={step.id} step={step} isLast={index === steps.length - 1} />
        ))}
      </div>
    </div>
  )
}
