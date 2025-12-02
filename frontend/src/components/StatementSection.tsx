import { cn } from '@/lib/utils'
import type { StatementLine } from '@/types/api'

interface StatementSectionProps {
  lines: StatementLine[]
  className?: string
}

export function StatementSection({ lines, className }: StatementSectionProps) {
  const formatAmount = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className={cn('space-y-1', className)}>
      {lines.map((line, index) => (
        <div
          key={`${line.account_code}-${index}`}
          className={cn(
            'grid grid-cols-[1fr,auto] gap-4 py-1.5 px-3 hover:bg-gray-50',
            line.is_bold && 'font-bold',
            line.is_underlined && 'border-t-2 border-gray-300',
            line.indent === 0 && 'bg-gray-100'
          )}
          style={{ paddingLeft: `${line.indent * 24 + 12}px` }}
        >
          <div className="flex items-center gap-2">
            {line.account_code && (
              <span className="text-xs text-gray-500 font-mono w-16">{line.account_code}</span>
            )}
            <span className={cn(line.is_bold ? 'font-bold' : '')}>{line.label}</span>
          </div>
          <div
            className={cn(
              'text-right font-mono',
              line.is_bold && 'font-bold',
              line.amount < 0 && 'text-red-600'
            )}
          >
            {formatAmount(line.amount)}
          </div>
        </div>
      ))}
    </div>
  )
}
