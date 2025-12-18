import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog'
import type { YearProjection } from '@/types/enrollment-projection'

interface ReductionBreakdownModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  yearProjection: YearProjection | null
}

export function ReductionBreakdownModal({
  open,
  onOpenChange,
  yearProjection,
}: ReductionBreakdownModalProps) {
  if (!yearProjection) return null

  const reduced = yearProjection.grades.filter((g) => (g.reduction_applied ?? 0) > 0)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>Capacity Reduction Breakdown ({yearProjection.school_year})</DialogTitle>
        </DialogHeader>
        {reduced.length === 0 ? (
          <p className="text-sm text-text-secondary">No reductions applied.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b">
                  <th className="text-left p-2">Grade</th>
                  <th className="text-right p-2">Original</th>
                  <th className="text-right p-2">Adjusted</th>
                  <th className="text-right p-2">Reduction</th>
                </tr>
              </thead>
              <tbody>
                {reduced.map((g) => (
                  <tr key={g.grade_code} className="border-b last:border-b-0">
                    <td className="p-2 font-medium">{g.grade_code}</td>
                    <td className="p-2 text-right tabular-nums">
                      {g.original_projection ?? g.projected_students}
                    </td>
                    <td className="p-2 text-right tabular-nums">{g.projected_students}</td>
                    <td className="p-2 text-right tabular-nums text-red-700">
                      {g.reduction_applied}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  )
}
