import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ArrowUpIcon, ArrowDownIcon, MinusIcon } from 'lucide-react'
import { cn } from '@/lib/utils'

interface KPICardProps {
  title: string
  value: number | string
  unit: string
  benchmark?: { min: number; max: number }
  trend?: 'up' | 'down' | 'stable'
  status?: 'good' | 'warning' | 'alert'
  previousValue?: number
}

export function KPICard({
  title,
  value,
  unit,
  benchmark,
  trend,
  status = 'good',
  previousValue,
}: KPICardProps) {
  const statusColors = {
    good: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200',
    alert: 'bg-red-100 text-red-800 border-red-200',
  }

  const trendIcon = {
    up: <ArrowUpIcon className="w-4 h-4" />,
    down: <ArrowDownIcon className="w-4 h-4" />,
    stable: <MinusIcon className="w-4 h-4" />,
  }

  const trendColor = {
    up: 'text-green-600',
    down: 'text-red-600',
    stable: 'text-gray-600',
  }

  return (
    <Card className={cn('hover:shadow-md transition-shadow', statusColors[status])}>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">{title}</CardTitle>
          {status && (
            <Badge variant="outline" className="text-xs">
              {status.toUpperCase()}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold">
              {typeof value === 'number' ? value.toFixed(2) : value}
            </span>
            <span className="text-sm text-gray-600">{unit}</span>
          </div>

          {benchmark && (
            <div className="text-xs text-gray-600">
              Benchmark: {benchmark.min.toFixed(2)} - {benchmark.max.toFixed(2)} {unit}
            </div>
          )}

          {trend && previousValue !== undefined && (
            <div className={cn('flex items-center gap-1 text-sm', trendColor[trend])}>
              {trendIcon[trend]}
              <span>
                {trend === 'up' ? '+' : trend === 'down' ? '-' : ''}
                {Math.abs(typeof value === 'number' ? value - previousValue : 0).toFixed(2)} vs
                previous
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
