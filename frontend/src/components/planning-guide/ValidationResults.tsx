import { StepValidation, VALIDATION_STATUS_COLORS } from '@/types/planning-progress'
import { CheckCircle, XCircle, AlertTriangle, Info } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ValidationResultsProps {
  validation: StepValidation[]
}

export function ValidationResults({ validation }: ValidationResultsProps) {
  if (validation.length === 0) return null

  const getValidationIcon = (status: StepValidation['status']) => {
    const iconClass = 'h-4 w-4 flex-shrink-0'

    switch (status) {
      case 'passed':
        return <CheckCircle className={`${iconClass} text-success-600`} />
      case 'failed':
        return <XCircle className={`${iconClass} text-error-600`} />
      case 'warning':
        return <AlertTriangle className={`${iconClass} text-warning-600`} />
      case 'info':
        return <Info className={`${iconClass} text-info-600`} />
    }
  }

  const getValidationBgColor = (status: StepValidation['status']) => {
    switch (status) {
      case 'passed':
        return 'bg-success-50 border-success-200'
      case 'failed':
        return 'bg-error-50 border-error-200'
      case 'warning':
        return 'bg-warning-50 border-warning-200'
      case 'info':
        return 'bg-info-50 border-info-200'
    }
  }

  return (
    <div className="space-y-2">
      <h4 className="text-sm font-semibold text-text-primary">Validation Checks</h4>
      <div className="space-y-2">
        {validation.map((check) => (
          <div
            key={check.check_id}
            className={cn(
              'flex items-start gap-3 p-3 rounded-lg border',
              getValidationBgColor(check.status)
            )}
          >
            {getValidationIcon(check.status)}
            <div className="flex-1 min-w-0">
              <p className={cn('text-sm font-medium', VALIDATION_STATUS_COLORS[check.status])}>
                {check.message}
              </p>
              {check.details && Object.keys(check.details).length > 0 && (
                <div className="mt-2 text-xs text-text-secondary bg-white bg-opacity-50 rounded px-2 py-1">
                  {Object.entries(check.details).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="font-medium">
                        {key.replace(/_/g, ' ').replace(/\b\w/g, (l) => l.toUpperCase())}:
                      </span>
                      <span>
                        {typeof value === 'number' ? value.toLocaleString() : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
