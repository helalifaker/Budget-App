import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  Cell,
  Legend,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface WaterfallData {
  name: string
  value: number
  type: 'budget' | 'favorable' | 'unfavorable' | 'actual'
}

interface WaterfallChartProps {
  data: WaterfallData[]
  title?: string
  className?: string
}

interface TooltipPayload {
  value?: number
  payload?: WaterfallData
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayload[]
}

const COLORS = {
  budget: '#3B82F6',
  favorable: '#10B981',
  unfavorable: '#EF4444',
  actual: '#8B5CF6',
}

export function WaterfallChart({
  data,
  title = 'Variance Waterfall',
  className,
}: WaterfallChartProps) {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
    if (active && payload && payload.length && payload[0].value !== undefined) {
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-medium text-gray-900">{payload[0].payload?.name}</p>
          <p className="text-lg font-bold">{formatCurrency(Math.abs(payload[0].value))}</p>
          <p className="text-xs text-gray-500 capitalize">{payload[0].payload?.type}</p>
        </div>
      )
    }
    return null
  }

  // Transform data for stacked bar chart to create waterfall effect
  const chartData = data.map((item, index) => {
    let cumulative = 0
    for (let i = 0; i < index; i++) {
      cumulative += data[i].value
    }
    return {
      ...item,
      start: cumulative,
      value: Math.abs(item.value),
      actualValue: item.value,
    }
  })

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={400}>
          <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
            <YAxis tickFormatter={(value) => formatCurrency(value)} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="value" stackId="a" fill="#8884d8">
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[entry.type]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
