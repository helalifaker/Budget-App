import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import { AlertCircleIcon } from 'lucide-react'

interface VarianceRowProps {
  account: string
  description: string
  budget: number
  actual: number
  variance: number
  variancePercent: number
  isFavorable: boolean
  isMaterial: boolean
  className?: string
}

export function VarianceRow({
  account,
  description,
  budget,
  actual,
  variance,
  variancePercent,
  isFavorable,
  isMaterial,
  className,
}: VarianceRowProps) {
  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  const formatPercent = (percent: number) => {
    return `${percent > 0 ? '+' : ''}${percent.toFixed(1)}%`
  }

  return (
    <div
      className={cn(
        'grid grid-cols-[100px,1fr,120px,120px,120px,100px,120px] gap-4 py-2 px-3 hover:bg-gray-50 border-b border-gray-100',
        className
      )}
    >
      <div className="text-sm font-mono text-gray-600">{account}</div>
      <div className="text-sm">{description}</div>
      <div className="text-sm text-right font-mono">{formatAmount(budget)}</div>
      <div className="text-sm text-right font-mono">{formatAmount(actual)}</div>
      <div
        className={cn(
          'text-sm text-right font-mono font-semibold',
          isFavorable ? 'text-green-600' : 'text-red-600'
        )}
      >
        {formatAmount(variance)}
      </div>
      <div
        className={cn(
          'text-sm text-right font-mono font-semibold',
          isFavorable ? 'text-green-600' : 'text-red-600'
        )}
      >
        {formatPercent(variancePercent)}
      </div>
      <div className="flex items-center justify-end gap-2">
        <Badge variant={isFavorable ? 'default' : 'destructive'} className="text-xs">
          {isFavorable ? 'Favorable' : 'Unfavorable'}
        </Badge>
        {isMaterial && <AlertCircleIcon className="w-4 h-4 text-orange-500" />}
      </div>
    </div>
  )
}
