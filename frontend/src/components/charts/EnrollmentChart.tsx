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
import { chartColors } from '@/lib/theme.constants'

interface EnrollmentData {
  level: string
  students: number
  capacity?: number
}

interface EnrollmentChartProps {
  data: EnrollmentData[]
  title?: string
  showCapacity?: boolean
  className?: string
}

interface TooltipPayload {
  value?: number
  payload?: EnrollmentData
}

interface CustomTooltipProps {
  active?: boolean
  payload?: TooltipPayload[]
}

export function EnrollmentChart({
  data,
  title = 'Enrollment by Level',
  showCapacity = false,
  className,
}: EnrollmentChartProps) {
  const CustomTooltip = ({ active, payload }: CustomTooltipProps) => {
    if (active && payload && payload.length && payload[0].value !== undefined) {
      const value = payload[0].value
      const capacity = payload[0].payload?.capacity
      const level = payload[0].payload?.level
      return (
        <div className="bg-paper border border-border-light rounded-lg shadow-lg p-3">
          <p className="font-medium text-text-primary mb-1">{level}</p>
          <p className="text-sm">
            <span className="text-text-secondary">Students:</span>{' '}
            <span className="font-semibold text-efir-gold">{value}</span>
          </p>
          {showCapacity && capacity && (
            <>
              <p className="text-sm">
                <span className="text-text-secondary">Capacity:</span>{' '}
                <span className="font-semibold text-sage">{capacity}</span>
              </p>
              <p className="text-xs text-text-tertiary mt-1">
                Utilization: {((value / capacity) * 100).toFixed(1)}%
              </p>
            </>
          )}
        </div>
      )
    }
    return null
  }

  const total = data.reduce((sum, item) => sum + item.students, 0)

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <div className="text-2xl font-bold text-text-primary">
          {total.toLocaleString()} students
        </div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="level" angle={-45} textAnchor="end" height={80} />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="students" fill={chartColors.primary} name="Students" />
            {showCapacity && (
              <Bar dataKey="capacity" fill={chartColors.secondary} name="Capacity" />
            )}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
