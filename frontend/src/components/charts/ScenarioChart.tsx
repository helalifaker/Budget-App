import { useState } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { chartColors } from '@/lib/theme.constants'

interface ScenarioData {
  year: number
  conservative: number
  base: number
  optimistic: number
}

interface ScenarioChartProps {
  data: ScenarioData[]
  title?: string
  className?: string
  metrics?: string[]
}

interface TooltipPayload {
  value?: number
  name?: string
  color?: string
  payload?: ScenarioData
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayload[]
}

const SCENARIO_COLORS = {
  conservative: chartColors.conservative,
  base: chartColors.base,
  optimistic: chartColors.optimistic,
}

export function ScenarioChart({
  data,
  title = 'Strategic Scenarios',
  className,
  metrics = ['Revenue', 'Costs', 'Net Income', 'Students'],
}: ScenarioChartProps) {
  const [selectedMetric, setSelectedMetric] = useState('Revenue')

  const formatValue = (value: number | undefined, metric: string) => {
    if (value === undefined) return '—'
    if (metric === 'Students' || metric === 'Classes' || metric === 'Teachers') {
      return value.toLocaleString('en-US')
    }
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
      notation: 'compact',
    }).format(value)
  }

  const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-paper border border-border-light rounded-lg shadow-lg p-3">
          <p className="font-medium text-text-primary mb-2">Year {payload[0].payload?.year}</p>
          {payload.map((entry: TooltipPayload, idx: number) => {
            const value = entry.value
            if (value !== undefined) {
              return (
                <div key={`${entry.name}-${idx}`} className="flex items-center gap-2 text-sm">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: entry.color }} />
                  <span className="capitalize">{entry.name}:</span>
                  <span className="font-semibold">{formatValue(value, selectedMetric)}</span>
                </div>
              )
            }
            return null
          })}
        </div>
      )
    }
    return null
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>{title}</CardTitle>
          <Select value={selectedMetric} onValueChange={setSelectedMetric}>
            <SelectTrigger className="w-40">
              <SelectValue placeholder="Select metric" />
            </SelectTrigger>
            <SelectContent>
              {metrics.map((metric) => (
                <SelectItem key={metric} value={metric}>
                  {metric}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="year" label={{ value: 'Year', position: 'insideBottom', offset: -5 }} />
            <YAxis tickFormatter={(value) => formatValue(value, selectedMetric)} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Line
              type="monotone"
              dataKey="conservative"
              stroke={SCENARIO_COLORS.conservative}
              strokeWidth={2}
              name="Conservative"
              dot={{ r: 4 }}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="base"
              stroke={SCENARIO_COLORS.base}
              strokeWidth={2}
              name="Base Case"
              dot={{ r: 4 }}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="optimistic"
              stroke={SCENARIO_COLORS.optimistic}
              strokeWidth={2}
              name="Optimistic"
              dot={{ r: 4 }}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
