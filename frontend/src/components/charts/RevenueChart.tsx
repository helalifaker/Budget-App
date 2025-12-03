import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface RevenueData {
  category: string
  amount: number
  color: string
}

interface RevenueChartProps {
  data: RevenueData[]
  title?: string
  className?: string
}

interface TooltipPayload {
  value?: number
  name?: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayload[]
}

interface PieLabelProps {
  name?: string
  percent?: number
}

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#F59E0B', '#EF4444']

export function RevenueChart({ data, title = 'Revenue Breakdown', className }: RevenueChartProps) {
  const formatCurrency = (value: number | undefined) => {
    if (value === undefined) return '—'
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value)
  }

  const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
    if (active && payload && payload.length && payload[0].value !== undefined) {
      const value = payload[0].value
      const total = data.reduce((sum, d) => sum + d.amount, 0)
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-medium text-gray-900">{payload[0].name}</p>
          <p className="text-lg font-bold text-green-600">{formatCurrency(value)}</p>
          <p className="text-xs text-gray-500">{((value / total) * 100).toFixed(1)}%</p>
        </div>
      )
    }
    return null
  }

  const chartData = data.map((item, index) => ({
    name: item.category,
    value: item.amount,
    color: item.color || COLORS[index % COLORS.length],
  }))

  const total = data.reduce((sum, item) => sum + item.amount, 0)

  const renderLabel = ({ name, percent }: PieLabelProps) => {
    const percentValue = percent ?? 0
    return `${name} (${(percentValue * 100).toFixed(0)}%)`
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <div className="text-2xl font-bold text-gray-900">{formatCurrency(total)}</div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={chartData}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={renderLabel}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {chartData.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip content={<CustomTooltip />} />
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
