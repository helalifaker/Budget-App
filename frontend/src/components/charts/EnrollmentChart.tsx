import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  TooltipProps,
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

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

export function EnrollmentChart({
  data,
  title = 'Enrollment by Level',
  showCapacity = false,
  className,
}: EnrollmentChartProps) {
  const CustomTooltip = ({ active, payload }: TooltipProps<number, string>) => {
    if (active && payload && payload.length && payload[0].value !== undefined) {
      const value = payload[0].value
      const capacity = payload[0].payload.capacity
      return (
        <div className="bg-white border border-gray-200 rounded-lg shadow-lg p-3">
          <p className="font-medium text-gray-900 mb-1">{payload[0].payload.level}</p>
          <p className="text-sm">
            <span className="text-gray-600">Students:</span>{' '}
            <span className="font-semibold text-blue-600">{value}</span>
          </p>
          {showCapacity && capacity && (
            <>
              <p className="text-sm">
                <span className="text-gray-600">Capacity:</span>{' '}
                <span className="font-semibold text-green-600">{capacity}</span>
              </p>
              <p className="text-xs text-gray-500 mt-1">
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
        <div className="text-2xl font-bold text-gray-900">{total.toLocaleString()} students</div>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="level" angle={-45} textAnchor="end" height={80} />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Bar dataKey="students" fill="#3B82F6" name="Students" />
            {showCapacity && <Bar dataKey="capacity" fill="#10B981" name="Capacity" />}
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  )
}
