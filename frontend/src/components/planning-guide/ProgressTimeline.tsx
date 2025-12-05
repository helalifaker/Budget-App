import { StepProgress, STEP_METADATA } from '@/types/planning-progress'
import { CheckCircle2, Circle, AlertCircle, Lock, AlertTriangle } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ProgressTimelineProps {
  steps: StepProgress[]
}

export function ProgressTimeline({ steps }: ProgressTimelineProps) {
  const getStepIcon = (step: StepProgress) => {
    const iconClass = 'h-6 w-6'

    switch (step.status) {
      case 'completed':
        return <CheckCircle2 className={`${iconClass} text-success-600`} />
      case 'in_progress':
        return <AlertTriangle className={`${iconClass} text-warning-600`} />
      case 'error':
        return <AlertCircle className={`${iconClass} text-error-600`} />
      case 'blocked':
        return <Lock className={`${iconClass} text-twilight-400`} />
      default:
        return <Circle className={`${iconClass} text-sand-400`} />
    }
  }

  const getConnectorColor = (currentStep: StepProgress) => {
    if (currentStep.status === 'completed') {
      return 'bg-success-400'
    }
    if (currentStep.status === 'in_progress') {
      return 'bg-gradient-to-r from-warning-400 to-sand-300'
    }
    return 'bg-sand-300'
  }

  const getStepBgColor = (step: StepProgress) => {
    switch (step.status) {
      case 'completed':
        return 'bg-success-100 border-success-300'
      case 'in_progress':
        return 'bg-warning-100 border-warning-300'
      case 'error':
        return 'bg-error-100 border-error-300'
      case 'blocked':
        return 'bg-twilight-100 border-twilight-300'
      default:
        return 'bg-sand-100 border-sand-300'
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-sand-200 p-6">
      <h3 className="text-lg font-semibold text-brown-800 mb-6 font-serif">Planning Steps</h3>

      {/* Desktop: Horizontal Timeline */}
      <div className="hidden lg:block">
        <div className="relative">
          {/* Connector Line */}
          <div className="absolute top-5 left-0 right-0 h-0.5 bg-sand-300" />

          {/* Steps */}
          <div className="relative flex justify-between">
            {steps.map((step, index) => {
              const metadata = STEP_METADATA[step.step_id]
              const isLast = index === steps.length - 1

              return (
                <div key={step.step_id} className="flex flex-col items-center flex-1">
                  {/* Step Circle */}
                  <div
                    className={cn(
                      'relative z-10 w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-300',
                      getStepBgColor(step),
                      'hover:scale-110 cursor-pointer'
                    )}
                  >
                    {getStepIcon(step)}
                  </div>

                  {/* Step Number & Title */}
                  <div className="mt-3 text-center">
                    <div className="text-xs font-medium text-twilight-600">
                      Step {step.step_number}
                    </div>
                    <div className="text-sm font-medium text-brown-800 mt-1 max-w-[120px]">
                      {metadata?.title}
                    </div>
                  </div>

                  {/* Progress Percentage */}
                  {step.status !== 'not_started' && (
                    <div className="mt-1 text-xs text-twilight-600">
                      {Math.round(step.progress_percentage)}%
                    </div>
                  )}

                  {/* Connector (not for last item) */}
                  {!isLast && (
                    <div
                      className={cn(
                        'absolute top-5 h-0.5 transition-all duration-500',
                        getConnectorColor(step)
                      )}
                      style={{
                        left: `${((index + 1) / steps.length) * 100 - 100 / steps.length / 2}%`,
                        width: `${100 / steps.length}%`,
                      }}
                    />
                  )}
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Mobile: Vertical Timeline */}
      <div className="lg:hidden space-y-4">
        {steps.map((step, index) => {
          const metadata = STEP_METADATA[step.step_id]
          const isLast = index === steps.length - 1

          return (
            <div key={step.step_id} className="relative flex items-start gap-4">
              {/* Vertical Connector */}
              {!isLast && <div className="absolute left-5 top-12 bottom-0 w-0.5 bg-sand-300" />}

              {/* Step Circle */}
              <div
                className={cn(
                  'relative z-10 w-10 h-10 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                  getStepBgColor(step)
                )}
              >
                {getStepIcon(step)}
              </div>

              {/* Step Content */}
              <div className="flex-1 pt-1">
                <div className="flex items-center justify-between">
                  <div>
                    <div className="text-xs font-medium text-twilight-600">
                      Step {step.step_number}
                    </div>
                    <div className="text-sm font-medium text-brown-800">{metadata?.title}</div>
                  </div>
                  {step.status !== 'not_started' && (
                    <div className="text-sm font-medium text-twilight-700">
                      {Math.round(step.progress_percentage)}%
                    </div>
                  )}
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
