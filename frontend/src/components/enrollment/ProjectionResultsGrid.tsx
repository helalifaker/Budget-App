import { memo, useMemo, useCallback } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { YearProjection } from '@/types/enrollmentProjection'

interface ProjectionResultsGridProps {
  projections: YearProjection[]
}

// PERFORMANCE FIX: React.memo prevents re-renders when props haven't changed
export const ProjectionResultsGrid = memo(function ProjectionResultsGrid({
  projections,
}: ProjectionResultsGridProps) {
  // PERFORMANCE FIX: Memoize computed values to prevent recalculation on every render
  const years = useMemo(() => projections.map((p) => p.school_year), [projections])

  const gradeRows = useMemo(
    () => (projections.length > 0 ? projections[0].grades.map((g) => g.grade_code) : []),
    [projections]
  )

  const getValue = useCallback(
    (gradeCode: string, yearIndex: number) => {
      const year = projections[yearIndex]
      return year?.grades.find((g) => g.grade_code === gradeCode)?.projected_students ?? 0
    },
    [projections]
  )

  if (!projections.length) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Projection Results</CardTitle>
        </CardHeader>
        <CardContent>No projections yet.</CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Projection Results</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Grade</th>
                {years.map((y, i) => (
                  <th key={y} className="text-right p-2">
                    {y}
                    {projections[i].was_capacity_constrained && (
                      <span className="ml-1 text-red-600">*</span>
                    )}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {gradeRows.map((grade) => (
                <tr key={grade} className="border-b last:border-b-0">
                  <td className="p-2 font-medium">{grade}</td>
                  {years.map((_, i) => (
                    <td key={`${grade}-${i}`} className="p-2 text-right tabular-nums">
                      {getValue(grade, i)}
                    </td>
                  ))}
                </tr>
              ))}
              <tr className="border-t font-semibold">
                <td className="p-2">TOTAL</td>
                {years.map((_, i) => (
                  <td key={`total-${i}`} className="p-2 text-right tabular-nums">
                    {projections[i].total_students}
                  </td>
                ))}
              </tr>
            </tbody>
          </table>
          <p className="text-xs text-text-secondary mt-2">
            * Year constrained to school max capacity.
          </p>
        </div>
      </CardContent>
    </Card>
  )
})
