/**
 * SettingsReminderCard - Reminds users to configure lateral entry settings before planning.
 *
 * This card appears at the top of the planning page and links to the Settings tab
 * where users can configure calibration parameters, lateral entry rates, and
 * scenario multipliers.
 */

import { memo } from 'react'
import { Link } from '@tanstack/react-router'
import { Settings2, ArrowRight, CheckCircle2 } from 'lucide-react'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { cn } from '@/lib/utils'

interface SettingsReminderCardProps {
  /**
   * Whether calibration has been completed (affects messaging).
   * When true, shows a "ready" state; when false, prompts configuration.
   */
  isCalibrated?: boolean
  /**
   * Overall confidence level from calibration status.
   */
  confidenceLevel?: 'high' | 'medium' | 'low' | null
  /**
   * Whether to show the card in compact mode.
   */
  compact?: boolean
  className?: string
}

/**
 * Card that reminds users about the Settings configuration step.
 *
 * This is displayed before the projection workflow to ensure users
 * have configured their lateral entry rates and scenario multipliers.
 */
export const SettingsReminderCard = memo(function SettingsReminderCard({
  isCalibrated = false,
  confidenceLevel,
  compact = false,
  className,
}: SettingsReminderCardProps) {
  if (compact && isCalibrated) {
    // In compact mode with calibration done, show minimal indicator
    return (
      <div className={cn('flex items-center gap-2 text-sm text-muted-foreground', className)}>
        <CheckCircle2 className="h-4 w-4 text-sage" />
        <span>Settings configured</span>
        <Link to="/enrollment/settings" className="text-primary hover:underline">
          Review →
        </Link>
      </div>
    )
  }

  const getConfidenceBadge = () => {
    if (!confidenceLevel) return null
    const colors = {
      high: 'bg-sage-100 text-sage-700',
      medium: 'bg-warning-100 text-warning-700',
      low: 'bg-error-100 text-error-700',
    }
    return (
      <span
        className={cn(
          'inline-flex items-center px-2 py-0.5 rounded text-xs font-medium',
          colors[confidenceLevel]
        )}
      >
        {confidenceLevel} confidence
      </span>
    )
  }

  return (
    <Card
      className={cn(
        'border-l-4',
        isCalibrated ? 'border-l-sage bg-sage-50' : 'border-l-warning-500 bg-warning-50',
        className
      )}
    >
      <CardContent className="py-4">
        <div className="flex items-start justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className={cn('p-2 rounded-lg', isCalibrated ? 'bg-sage-100' : 'bg-warning-100')}>
              {isCalibrated ? (
                <CheckCircle2 className="h-5 w-5 text-sage" />
              ) : (
                <Settings2 className="h-5 w-5 text-warning-600" />
              )}
            </div>
            <div>
              <h3 className="font-medium text-sm">
                {isCalibrated
                  ? 'Step 0: Settings Configured'
                  : 'Step 0: Configure Lateral Entry Settings'}
              </h3>
              <p className="text-sm text-muted-foreground mt-1">
                {isCalibrated ? (
                  <>
                    Your lateral entry rates and scenario multipliers are configured.{' '}
                    {getConfidenceBadge()}
                  </>
                ) : (
                  <>
                    Before running projections, configure your lateral entry rates and scenario
                    multipliers in the Settings tab. This ensures accurate enrollment forecasts.
                  </>
                )}
              </p>
            </div>
          </div>
          <Button asChild variant={isCalibrated ? 'outline' : 'default'} size="sm">
            <Link to="/enrollment/settings">
              {isCalibrated ? 'Review Settings' : 'Configure Settings'}
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </CardContent>
    </Card>
  )
})
