/**
 * Step Progress Component - EFIR Luxury Warm Theme
 *
 * Horizontal step indicator for planning workflow:
 * - Completed: Sage (#7D9082) with checkmark
 * - Current: Gold (#A68B5B) with pulse animation
 * - Pending: Light border, muted text
 * - Blocked: Terracotta (#C4785D) with alert icon
 *
 * Uses Lucide icons only (no emoji)
 */

import * as React from 'react'
import { Check, Circle, AlertCircle, Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

/** Step status type */
export type StepStatus = 'completed' | 'current' | 'pending' | 'blocked'

/** Individual step configuration */
export interface Step {
  id: string
  label: string
  status: StepStatus
  /** Optional description for the step */
  description?: string
}

interface StepProgressProps {
  /** Array of steps to display */
  steps: Step[]
  /** Currently active step index (0-based) */
  currentStep: number
  /** Size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Additional CSS classes */
  className?: string
  /** Callback when a step is clicked */
  onStepClick?: (stepIndex: number, step: Step) => void
}

const statusConfig: Record<
  StepStatus,
  {
    iconBg: string
    iconColor: string
    textColor: string
    lineColor: string
    icon: React.ElementType
  }
> = {
  completed: {
    iconBg: 'bg-sage-500',
    iconColor: 'text-white',
    textColor: 'text-sage-700',
    lineColor: 'bg-sage-500',
    icon: Check,
  },
  current: {
    iconBg: 'bg-efir-gold-500',
    iconColor: 'text-white',
    textColor: 'text-efir-gold-700',
    lineColor: 'bg-border-light',
    icon: Loader2,
  },
  pending: {
    iconBg: 'bg-subtle',
    iconColor: 'text-text-muted',
    textColor: 'text-text-tertiary',
    lineColor: 'bg-border-light',
    icon: Circle,
  },
  blocked: {
    iconBg: 'bg-terracotta-500',
    iconColor: 'text-white',
    textColor: 'text-terracotta-700',
    lineColor: 'bg-terracotta-200',
    icon: AlertCircle,
  },
}

const sizeStyles = {
  sm: {
    icon: 'w-6 h-6',
    iconInner: 'w-3 h-3',
    text: 'text-xs',
    description: 'text-xs',
    gap: 'gap-1',
  },
  md: {
    icon: 'w-8 h-8',
    iconInner: 'w-4 h-4',
    text: 'text-sm',
    description: 'text-xs',
    gap: 'gap-1.5',
  },
  lg: {
    icon: 'w-10 h-10',
    iconInner: 'w-5 h-5',
    text: 'text-base',
    description: 'text-sm',
    gap: 'gap-2',
  },
}

export function StepProgress({
  steps,
  currentStep,
  size = 'md',
  className,
  onStepClick,
}: StepProgressProps) {
  const sizeStyle = sizeStyles[size]

  return (
    <div
      className={cn('flex items-start justify-between w-full', className)}
      role="navigation"
      aria-label="Progress steps"
    >
      {steps.map((step, index) => {
        const config = statusConfig[step.status]
        const Icon = config.icon
        const isLast = index === steps.length - 1
        const isClickable = onStepClick && (step.status === 'completed' || index <= currentStep)

        return (
          <React.Fragment key={step.id}>
            {/* Step item */}
            <div
              className={cn(
                'flex flex-col items-center',
                sizeStyle.gap,
                isClickable && 'cursor-pointer group'
              )}
              onClick={() => isClickable && onStepClick(index, step)}
              role={isClickable ? 'button' : undefined}
              tabIndex={isClickable ? 0 : undefined}
              aria-current={index === currentStep ? 'step' : undefined}
              onKeyDown={(e) => {
                if (isClickable && (e.key === 'Enter' || e.key === ' ')) {
                  e.preventDefault()
                  onStepClick(index, step)
                }
              }}
            >
              {/* Step icon */}
              <div
                className={cn(
                  'flex items-center justify-center rounded-full',
                  'border-2 border-transparent',
                  'transition-all duration-200',
                  config.iconBg,
                  config.iconColor,
                  sizeStyle.icon,
                  step.status === 'current' && 'ring-4 ring-efir-gold-100',
                  isClickable && 'group-hover:ring-2 group-hover:ring-efir-gold-200'
                )}
              >
                <Icon
                  className={cn(sizeStyle.iconInner, step.status === 'current' && 'animate-spin')}
                />
              </div>

              {/* Step label */}
              <span
                className={cn(
                  'font-body font-medium text-center max-w-[100px]',
                  sizeStyle.text,
                  config.textColor,
                  isClickable && 'group-hover:text-efir-gold-600'
                )}
              >
                {step.label}
              </span>

              {/* Optional description */}
              {step.description && (
                <span
                  className={cn(
                    'font-body text-center max-w-[120px] text-text-muted',
                    sizeStyle.description
                  )}
                >
                  {step.description}
                </span>
              )}
            </div>

            {/* Connector line */}
            {!isLast && (
              <div
                className={cn(
                  'flex-1 h-[2px] mt-3 sm:mt-4 mx-2',
                  'transition-colors duration-300',
                  step.status === 'completed' ? config.lineColor : 'bg-border-light'
                )}
                aria-hidden="true"
              />
            )}
          </React.Fragment>
        )
      })}
    </div>
  )
}

export type { StepProgressProps }
