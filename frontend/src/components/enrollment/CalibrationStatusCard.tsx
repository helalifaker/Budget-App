import { memo } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { RefreshCw, CheckCircle2, AlertTriangle, XCircle, Star, Calendar } from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CalibrationStatus } from '@/types/enrollment-settings'

interface CalibrationStatusCardProps {
  status: CalibrationStatus
  onRecalibrate: () => void
  isRecalibrating?: boolean
}

const CONFIDENCE_CONFIG: Record<
  CalibrationStatus['overall_confidence'],
  { icon: typeof CheckCircle2; color: string; bgColor: string; label: string }
> = {
  high: {
    icon: CheckCircle2,
    color: 'text-sage-600',
    bgColor: 'bg-sage-50',
    label: 'High Confidence',
  },
  medium: {
    icon: AlertTriangle,
    color: 'text-terracotta-600',
    bgColor: 'bg-terracotta-50',
    label: 'Medium Confidence',
  },
  low: {
    icon: XCircle,
    color: 'text-terracotta-700',
    bgColor: 'bg-terracotta-100',
    label: 'Low Confidence',
  },
}

/**
 * CalibrationStatusCard - Shows the status of auto-calibration from historical data.
 *
 * Displays:
 * - When parameters were last calibrated
 * - Which historical years were used
 * - Overall confidence level
 * - Data quality score (1-5 stars)
 * - Button to trigger recalibration
 */
export const CalibrationStatusCard = memo(function CalibrationStatusCard({
  status,
  onRecalibrate,
  isRecalibrating = false,
}: CalibrationStatusCardProps) {
  const confidence = CONFIDENCE_CONFIG[status.overall_confidence]
  const ConfidenceIcon = confidence.icon

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'Never'
    const date = new Date(dateStr)
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  }

  return (
    <Card className={cn('border-l-4', confidence.color.replace('text-', 'border-'))}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-lg', confidence.bgColor)}>
              <ConfidenceIcon className={cn('h-5 w-5', confidence.color)} />
            </div>
            <div>
              <CardTitle className="text-lg">Auto-Calibration Status</CardTitle>
              <CardDescription>Derived parameters from historical enrollment data</CardDescription>
            </div>
          </div>
          <Badge variant="outline" className={cn(confidence.bgColor, confidence.color)}>
            {confidence.label}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Data Quality Score */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Data Quality</span>
          <div className="flex items-center gap-1">
            {Array.from({ length: 5 }).map((_, i) => (
              <Star
                key={i}
                className={cn(
                  'h-4 w-4',
                  i < status.data_quality_score ? 'fill-gold text-gold' : 'text-border-light'
                )}
              />
            ))}
          </div>
        </div>

        {/* Source Years */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Historical Window</span>
          <div className="flex items-center gap-1">
            {status.source_years.length > 0 ? (
              <span className="text-sm font-medium">
                {status.source_years[0]} - {status.source_years[status.source_years.length - 1]}
              </span>
            ) : (
              <span className="text-sm text-muted-foreground italic">No data</span>
            )}
          </div>
        </div>

        {/* Years Available */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Years of Data</span>
          <Badge variant="secondary">{status.total_years_available} years</Badge>
        </div>

        {/* Last Calibrated */}
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">Last Calibrated</span>
          <div className="flex items-center gap-1.5 text-sm">
            <Calendar className="h-3.5 w-3.5 text-muted-foreground" />
            <span>{formatDate(status.last_calibrated)}</span>
          </div>
        </div>

        {/* Data Sufficiency Warning */}
        {!status.has_sufficient_data && (
          <div className="flex items-start gap-2 p-3 bg-terracotta-50 border border-terracotta-200 rounded-lg">
            <AlertTriangle className="h-4 w-4 text-terracotta-600 mt-0.5" />
            <div className="text-sm text-terracotta-800">
              <p className="font-medium">Insufficient Historical Data</p>
              <p className="text-terracotta-700">
                At least 2 years of enrollment data are needed for reliable calibration. Using
                document defaults instead.
              </p>
            </div>
          </div>
        )}

        {/* Recalibrate Button */}
        <Button
          onClick={onRecalibrate}
          disabled={isRecalibrating}
          variant="outline"
          className="w-full"
        >
          <RefreshCw className={cn('h-4 w-4 mr-2', isRecalibrating && 'animate-spin')} />
          {isRecalibrating ? 'Recalibrating...' : 'Recalibrate from History'}
        </Button>
      </CardContent>
    </Card>
  )
})
