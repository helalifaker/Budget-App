import { memo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  RefreshCw,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  Star,
  Calendar,
  Database,
  Activity,
} from 'lucide-react'
import { cn } from '@/lib/utils'
import type { CalibrationStatus } from '@/types/enrollmentSettings'

interface CalibrationStatusBarProps {
  status: CalibrationStatus
  onRecalibrate: () => void
  isRecalibrating?: boolean
}

/**
 * Confidence configuration using theme colors:
 * - High: sage (enrollment/success)
 * - Medium: gold (finance/primary)
 * - Low: terracotta (warnings/error)
 */
const CONFIDENCE_CONFIG = {
  high: {
    icon: CheckCircle2,
    textClass: 'text-sage',
    bgClass: 'bg-sage-100',
    borderClass: 'border-l-sage',
    badgeClass: 'bg-sage-100 text-sage border-0',
    label: 'High',
  },
  medium: {
    icon: AlertTriangle,
    textClass: 'text-gold',
    bgClass: 'bg-gold-100',
    borderClass: 'border-l-gold',
    badgeClass: 'bg-gold-100 text-gold border-0',
    label: 'Medium',
  },
  low: {
    icon: XCircle,
    textClass: 'text-terracotta',
    bgClass: 'bg-terracotta-100',
    borderClass: 'border-l-terracotta',
    badgeClass: 'bg-terracotta-100 text-terracotta border-0',
    label: 'Low',
  },
} as const

/**
 * CalibrationStatusBar - Unified card displaying calibration metadata.
 *
 * Single card design with:
 * - Header: Title + Confidence Badge + Recalibrate Button
 * - Content: 3 aligned stat items (Quality, Years, Window)
 *
 * Uses theme colors (sage, gold, terracotta) instead of hardcoded Tailwind colors.
 */
export const CalibrationStatusBar = memo(function CalibrationStatusBar({
  status,
  onRecalibrate,
  isRecalibrating = false,
}: CalibrationStatusBarProps) {
  const conf = CONFIDENCE_CONFIG[status.overall_confidence]
  const ConfIcon = conf.icon

  const getHistoricalWindow = () => {
    if (status.source_years.length === 0) return 'No data'
    if (status.source_years.length === 1) return status.source_years[0]
    return `${status.source_years[0]} - ${status.source_years[status.source_years.length - 1]}`
  }

  return (
    <Card className={cn('border-l-4', conf.borderClass)}>
      <CardHeader className="pb-3">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          {/* Title + Confidence Badge */}
          <div className="flex items-center gap-3">
            <div className={cn('p-2 rounded-lg', conf.bgClass)}>
              <Activity className={cn('h-5 w-5', conf.textClass)} />
            </div>
            <div>
              <CardTitle className="text-base font-semibold text-text-primary">
                Auto-Calibration Status
              </CardTitle>
              <p className="text-xs text-text-muted">Derived from historical enrollment data</p>
            </div>
            <Badge variant="outline" className={cn('ml-2', conf.badgeClass)}>
              <ConfIcon className="h-3 w-3 mr-1" />
              {conf.label} Confidence
            </Badge>
          </div>

          {/* Recalibrate Button */}
          <Button
            onClick={onRecalibrate}
            disabled={isRecalibrating}
            variant="outline"
            size="sm"
            className="shrink-0"
          >
            <RefreshCw className={cn('h-4 w-4 mr-2', isRecalibrating && 'animate-spin')} />
            {isRecalibrating ? 'Calibrating...' : 'Recalibrate from History'}
          </Button>
        </div>
      </CardHeader>

      <CardContent>
        {/* Stats Row - 3 items with consistent alignment */}
        <div className="grid grid-cols-3 gap-6 pt-2 border-t border-border-light">
          {/* Data Quality */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-0.5 mb-1">
              {Array.from({ length: 5 }).map((_, i) => (
                <Star
                  key={i}
                  className={cn(
                    'h-4 w-4',
                    i < status.data_quality_score ? 'fill-gold text-gold' : 'text-border-medium'
                  )}
                />
              ))}
            </div>
            <p className="text-xs text-text-muted font-medium">Data Quality</p>
          </div>

          {/* Years of Data */}
          <div className="text-center border-x border-border-light">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Database className="h-4 w-4 text-text-tertiary" />
              <span className="text-lg font-semibold tabular-nums text-text-primary">
                {status.total_years_available}
              </span>
              <span className="text-sm text-text-muted">years</span>
            </div>
            <p className="text-xs text-text-muted font-medium">Years of Data</p>
          </div>

          {/* Historical Window */}
          <div className="text-center">
            <div className="flex items-center justify-center gap-1.5 mb-1">
              <Calendar className="h-4 w-4 text-text-tertiary" />
              <span className="text-sm font-medium text-text-primary">{getHistoricalWindow()}</span>
            </div>
            <p className="text-xs text-text-muted font-medium">Historical Window</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
})
