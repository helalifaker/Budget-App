import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

interface CostData {
  period: string
  personnel: number
  operating: number
}

interface CostChartProps {
  data: CostData[]
  title?: string
  className?: string
}

interface TooltipPayload {
  value?: number
  name?: string
  color?: string
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayload[]
  label?: string
}

export function CostChart({ data, title = 'Cost Breakdown by Period', className }: CostChartProps) {
  const formatCurrency = (value: number | undefined) => {
    if (value === undefined) return '—'
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      notation: 'compact',
      minimumFractionDigits: 0,
      maximumFractionDigits: 1,
    }).format(value)
  }

  const CustomTooltip = ({ active, payload, label }: CustomTooltipProps) => {
    if (active && payload && payload.length) {
      const totalCost = payload.reduce((sum: number, p: TooltipPayload) => sum + (p.value || 0), 0)
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-medium text-gray-900 mb-2">{label}</p>
          {payload.map((p: TooltipPayload, index: number) => (
            <div key={index} className="flex justify-between gap-4 text-sm">
              <span style={{ color: p.color }}>{p.name}:</span>
              <span className="font-medium">{formatCurrency(p.value)}</span>
            </div>
          ))}
          <div className="border-t mt-2 pt-2 flex justify-between gap-4 text-sm font-bold">
            <span>Total:</span>
            <span>{formatCurrency(totalCost)}</span>
          </div>
        </div>
      )
    }
    return null
  }

  const totalPersonnel = data.reduce((sum, d) => sum + d.personnel, 0)
  const totalOperating = data.reduce((sum, d) => sum + d.operating, 0)
  const grandTotal = totalPersonnel + totalOperating

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <div className="flex gap-6 mt-2">
          <div>
            <div className="text-xs text-gray-500">Personnel</div>
            <div className="text-lg font-bold text-orange-600">
              {formatCurrency(totalPersonnel)}
            </div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Operating</div>
            <div className="text-lg font-bold text-blue-600">{formatCurrency(totalOperating)}</div>
          </div>
          <div>
            <div className="text-xs text-gray-500">Total</div>
            <div className="text-lg font-bold text-gray-900">{formatCurrency(grandTotal)}</div>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="period" />
            <YAxis tickFormatter={(value) => formatCurrency(value)} />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="personnel" name="Personnel Costs" fill="#F97316" />
            <Bar dataKey="operating" name="Operating Costs" fill="#3B82F6" />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
