/**
 * PlanningWorkflowProgress - Minimal Stepper Design
 *
 * Clean horizontal stepper for module planning workflow:
 * - Completed: Sage filled circle with white checkmark
 * - Current: Gold filled circle (solid, no spinner)
 * - Pending: Light gray border circle
 * - Thin 2px connector lines between circles
 *
 * UI Redesign: Simplified from card-based to minimal stepper
 */

import { cn } from '@/lib/utils'
import { Check, type LucideIcon } from 'lucide-react'
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
 * Get status styling for a workflow step
 */
function getStepStyles(status: WorkflowStepStatus) {
  switch (status) {
    case 'complete':
      return {
        circle: 'bg-sage-500 border-sage-500',
        icon: 'text-white',
        label: 'text-sage-700',
        metric: 'text-sage-600',
        line: 'bg-sage-500',
      }
    case 'in-progress':
      return {
        circle: 'bg-gold border-gold',
        icon: 'text-white',
        label: 'text-gold-700 font-semibold',
        metric: 'text-gold-600 font-semibold',
        line: 'bg-border-medium',
      }
    case 'warning':
      return {
        circle: 'bg-terracotta-500 border-terracotta-500',
        icon: 'text-white',
        label: 'text-terracotta-700',
        metric: 'text-terracotta-600',
        line: 'bg-terracotta-200',
      }
    case 'error':
      return {
        circle: 'bg-wine-500 border-wine-500',
        icon: 'text-white',
        label: 'text-wine-700',
        metric: 'text-wine-600',
        line: 'bg-wine-200',
      }
    default: // pending
      return {
        circle: 'bg-transparent border-border-medium',
        icon: 'text-text-muted',
        label: 'text-text-tertiary',
        metric: 'text-text-muted',
        line: 'bg-border-light',
      }
  }
}

/**
 * Individual step indicator
 */
function StepIndicator({ step, isLast }: { step: WorkflowStep; isLast: boolean }) {
  const styles = getStepStyles(step.status)
  const isComplete = step.status === 'complete'
  const isCurrent = step.status === 'in-progress'

  return (
    <div className="flex items-center flex-1 last:flex-none">
      {/* Step content */}
      <div className="flex flex-col items-center min-w-[80px]">
        {/* Circle indicator */}
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.2 }}
          className={cn(
            'w-8 h-8 rounded-full border-2 flex items-center justify-center',
            'transition-all duration-200',
            styles.circle,
            isCurrent && 'ring-4 ring-gold/20'
          )}
        >
          {isComplete ? (
            <Check className={cn('w-4 h-4', styles.icon)} strokeWidth={3} />
          ) : isCurrent ? (
            <div className="w-2.5 h-2.5 bg-white rounded-full" />
          ) : (
            <div className="w-2 h-2 bg-border-medium rounded-full" />
          )}
        </motion.div>

        {/* Label */}
        <span className={cn('text-xs mt-2 text-center', styles.label)}>{step.title}</span>

        {/* Metric (if provided) */}
        {step.metric && (
          <span className={cn('text-sm font-mono', styles.metric)}>{step.metric}</span>
        )}
      </div>

      {/* Connector line */}
      {!isLast && (
        <div className="flex-1 h-0.5 mx-2 mt-[-24px]">
          <motion.div
            initial={{ scaleX: 0 }}
            animate={{ scaleX: 1 }}
            transition={{ duration: 0.3, delay: 0.1 }}
            className={cn(
              'h-full origin-left',
              step.status === 'complete' ? styles.line : 'bg-border-light'
            )}
          />
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
    <div className={cn('bg-paper rounded-xl border border-border-light p-5', className)}>
      {/* Header with title and progress percentage */}
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-sm font-semibold text-text-primary">{title}</h3>
        <div className="flex items-center gap-3">
          {/* Progress bar */}
          <div className="h-1.5 w-20 bg-subtle rounded-full overflow-hidden">
            <motion.div
              className={cn(
                'h-full rounded-full',
                calculatedProgress >= 100
                  ? 'bg-sage-500'
                  : calculatedProgress >= 50
                    ? 'bg-gold'
                    : 'bg-slate-400'
              )}
              initial={{ width: 0 }}
              animate={{ width: `${calculatedProgress}%` }}
              transition={{ duration: 0.5, ease: 'easeOut' }}
            />
          </div>
          <span className="text-sm font-semibold text-text-primary tabular-nums">
            {calculatedProgress}%
          </span>
        </div>
      </div>

      {/* Steps - horizontal layout */}
      <div className="flex items-start justify-between">
        {steps.map((step, index) => (
          <StepIndicator key={step.id} step={step} isLast={index === steps.length - 1} />
        ))}
      </div>
    </div>
  )
}
