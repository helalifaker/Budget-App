import { CustomCellRendererProps } from 'ag-grid-react'
import { cn } from '@/lib/utils'

interface CurrencyRendererProps extends CustomCellRendererProps {
  value: number
}

export function CurrencyRenderer({ value }: CurrencyRendererProps) {
  if (value === null || value === undefined) return null

  const formatted = new Intl.NumberFormat('en-SA', {
    style: 'currency',
    currency: 'SAR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)

  return (
    <div
      className={cn(
        'flex items-center justify-end h-full font-medium',
        value < 0 ? 'text-red-600' : 'text-gray-900'
      )}
    >
      {formatted}
    </div>
  )
}
