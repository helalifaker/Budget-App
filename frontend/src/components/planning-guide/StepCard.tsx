import { StepProgress, STEP_METADATA, STEP_STATUS_COLORS } from '@/types/planning-progress'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ValidationResults } from './ValidationResults'
import { HelpContent } from './HelpContent'
import { Link } from '@tanstack/react-router'
import {
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Lock,
  Circle,
  ChevronRight,
  BookOpen,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import { useState } from 'react'

interface StepCardProps {
  step: StepProgress
  stepNumber: number
}

export function StepCard({ step, stepNumber }: StepCardProps) {
  const [helpExpanded, setHelpExpanded] = useState(false)
  const metadata = STEP_METADATA[step.step_id]
  const statusColors = STEP_STATUS_COLORS[step.status]

  // Get status icon
  const getStatusIcon = () => {
    const iconClass = 'h-5 w-5'
    switch (step.status) {
      case 'completed':
        return <CheckCircle2 className={`${iconClass} text-success-600`} />
      case 'in_progress':
        return <AlertTriangle className={`${iconClass} text-warning-600`} />
      case 'error':
        return <AlertCircle className={`${iconClass} text-error-600`} />
      case 'blocked':
        return <Lock className={`${iconClass} text-twilight-600`} />
      default:
        return <Circle className={`${iconClass} text-sand-400`} />
    }
  }

  // Get status label
  const getStatusLabel = () => {
    switch (step.status) {
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

  // Get status badge variant
  const getStatusVariant = (): 'default' | 'success' | 'warning' | 'destructive' | 'secondary' => {
    switch (step.status) {
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

  // Get progress bar color
  const getProgressBarColor = () => {
    switch (step.status) {
      case 'completed':
        return 'bg-success-500'
      case 'in_progress':
        return 'bg-warning-500'
      case 'error':
        return 'bg-error-500'
      case 'blocked':
        return 'bg-twilight-400'
      default:
        return 'bg-sand-400'
    }
  }

  // Format metrics for display
  const formatMetrics = () => {
    const entries = Object.entries(step.metrics)
    if (entries.length === 0) return null

    return entries.map(([key, value]) => {
      // Format key (e.g., total_students -> Total Students)
      const formattedKey = key
        .split('_')
        .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ')

      // Format value (handle numbers and strings)
      const formattedValue = typeof value === 'number' ? value.toLocaleString() : String(value)

      return { key: formattedKey, value: formattedValue }
    })
  }

  const metrics = formatMetrics()

  return (
    <Card
      className={cn(
        'transition-all duration-300 hover:shadow-lg',
        'border-l-4',
        statusColors.border,
        statusColors.bg
      )}
    >
      <CardHeader>
        {/* Header: Step Number, Title, Status */}
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-center gap-4 flex-1">
            {/* Step Number Badge */}
            <Badge
              variant="outline"
              className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg font-bold border-2"
            >
              {stepNumber}
            </Badge>

            {/* Title & Description */}
            <div className="flex-1">
              <h3 className="text-xl font-semibold text-brown-800 font-serif">{metadata?.title}</h3>
              <p className="text-sm text-twilight-600 mt-1">{metadata?.description}</p>
            </div>
          </div>

          {/* Status Badge */}
          <div className="flex flex-col items-end gap-2">
            <Badge variant={getStatusVariant()} className="flex items-center gap-1.5">
              {getStatusIcon()}
              {getStatusLabel()}
            </Badge>
            {step.status !== 'not_started' && (
              <span className="text-sm font-medium text-twilight-700">
                {Math.round(step.progress_percentage)}%
              </span>
            )}
          </div>
        </div>

        {/* Progress Bar */}
        {step.status !== 'not_started' && (
          <div className="mt-4">
            <div className="w-full bg-sand-200 rounded-full h-2 overflow-hidden">
              <div
                className={cn(
                  'h-2 rounded-full transition-all duration-500 ease-out',
                  getProgressBarColor()
                )}
                style={{ width: `${step.progress_percentage}%` }}
              />
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Metrics Section */}
        {metrics && metrics.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {metrics.map((metric) => (
              <div key={metric.key} className="bg-white rounded-lg border border-sand-200 p-3">
                <div className="text-xs text-twilight-600">{metric.key}</div>
                <div className="text-lg font-semibold text-brown-800 mt-1">{metric.value}</div>
              </div>
            ))}
          </div>
        )}

        {/* Validation Results */}
        {step.validation.length > 0 && <ValidationResults validation={step.validation} />}

        {/* Blockers */}
        {step.blockers.length > 0 && (
          <div className="space-y-2">
            <h4 className="text-sm font-semibold text-brown-800 flex items-center gap-2">
              <Lock className="h-4 w-4 text-twilight-600" />
              Blockers
            </h4>
            {step.blockers.map((blocker, index) => (
              <div key={index} className="bg-twilight-50 border border-twilight-300 rounded-lg p-4">
                <p className="text-sm text-twilight-800 font-medium mb-2">{blocker.message}</p>
                <p className="text-sm text-twilight-600">
                  <strong>Resolution:</strong> {blocker.resolution}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Help Section (Expandable) */}
        <div className="border border-sand-300 rounded-lg">
          <button
            onClick={() => setHelpExpanded(!helpExpanded)}
            className="w-full flex items-center justify-between p-4 hover:bg-sand-50 transition-colors rounded-lg"
          >
            <div className="flex items-center gap-2 text-brown-800 font-medium">
              <BookOpen className="h-5 w-5 text-gold-600" />
              <span>How to complete this step</span>
            </div>
            {helpExpanded ? (
              <ChevronUp className="h-5 w-5 text-twilight-600" />
            ) : (
              <ChevronDown className="h-5 w-5 text-twilight-600" />
            )}
          </button>

          {helpExpanded && (
            <div className="border-t border-sand-300 p-4 animate-slideIn">
              <HelpContent stepId={step.step_id} />
            </div>
          )}
        </div>

        {/* Action Button */}
        <div className="flex justify-end">
          <Button
            asChild
            variant={step.status === 'completed' ? 'outline' : 'default'}
            className={cn('gap-2', step.status === 'blocked' && 'opacity-50 cursor-not-allowed')}
            disabled={step.status === 'blocked'}
          >
            <Link to={metadata?.route || '#'}>
              {step.status === 'completed' ? 'Review Step' : 'Start Working'}
              <ChevronRight className="h-4 w-4" />
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
