import { CustomCellRendererProps } from 'ag-grid-react'
import { Badge } from '@/components/ui/badge'
import { BudgetVersion } from '@/types/api'

interface StatusBadgeRendererProps extends CustomCellRendererProps {
  value: BudgetVersion['status'] | string
}

export function StatusBadgeRenderer({ value }: StatusBadgeRendererProps) {
  if (!value) return null

  const getVariant = (status: string) => {
    const statusMap: Record<string, 'info' | 'warning' | 'success' | 'default'> = {
      WORKING: 'info',
      SUBMITTED: 'warning',
      APPROVED: 'success',
      SUPERSEDED: 'default',
      DRAFT: 'default',
      ACTIVE: 'success',
      INACTIVE: 'default',
    }
    return statusMap[status] || 'default'
  }

  return (
    <div className="flex items-center h-full">
      <Badge variant={getVariant(value)}>{value}</Badge>
    </div>
  )
}
