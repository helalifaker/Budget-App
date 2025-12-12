import { useMemo, useState } from 'react'
import type { YearProjection } from '@/types/enrollmentProjection'
import { Button } from '@/components/ui/button'
import { ReductionBreakdownModal } from './ReductionBreakdownModal'

interface CapacityWarningBannerProps {
  projections: YearProjection[]
  maxCapacity: number
}

export function CapacityWarningBanner({ projections, maxCapacity }: CapacityWarningBannerProps) {
  const [open, setOpen] = useState(false)

  const constrainedYear = useMemo(() => {
    const constrained = projections.filter((p) => p.was_capacity_constrained)
    return constrained[constrained.length - 1] ?? null
  }, [projections])

  if (!constrainedYear) return null

  return (
    <>
      <div className="flex items-center justify-between gap-3 p-3 border border-red-200 bg-red-50 rounded-lg">
        <div>
          <div className="font-semibold text-red-800">Over Capacity</div>
          <div className="text-sm text-red-700">
            {constrainedYear.school_year} projections exceeded max capacity ({maxCapacity}). A
            proportional reduction was applied.
          </div>
        </div>
        <Button type="button" variant="outline" onClick={() => setOpen(true)}>
          View breakdown
        </Button>
      </div>

      <ReductionBreakdownModal
        open={open}
        onOpenChange={setOpen}
        yearProjection={constrainedYear}
      />
    </>
  )
}
