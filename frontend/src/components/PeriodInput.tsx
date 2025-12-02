import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { cn } from '@/lib/utils'

interface PeriodValue {
  p1: number
  summer: number
  p2: number
}

interface PeriodInputProps {
  value: PeriodValue
  onChange: (value: PeriodValue) => void
  label?: string
  className?: string
  disabled?: boolean
  currency?: boolean
}

export function PeriodInput({
  value,
  onChange,
  label,
  className,
  disabled = false,
  currency = true,
}: PeriodInputProps) {
  const handleChange = (period: keyof PeriodValue, newValue: string) => {
    const numValue = parseFloat(newValue) || 0
    onChange({
      ...value,
      [period]: numValue,
    })
  }

  const total = value.p1 + value.summer + value.p2

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount)
  }

  return (
    <div className={cn('space-y-3', className)}>
      {label && <Label className="text-sm font-medium">{label}</Label>}
      <div className="grid grid-cols-4 gap-3">
        <div className="space-y-1">
          <Label htmlFor="p1" className="text-xs text-gray-600">
            Period 1 (Jan-Jun)
          </Label>
          <Input
            id="p1"
            type="number"
            value={value.p1}
            onChange={(e) => handleChange('p1', e.target.value)}
            disabled={disabled}
            className="h-9"
            step="0.01"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="summer" className="text-xs text-gray-600">
            Summer (Jul-Aug)
          </Label>
          <Input
            id="summer"
            type="number"
            value={value.summer}
            onChange={(e) => handleChange('summer', e.target.value)}
            disabled={disabled}
            className="h-9"
            step="0.01"
          />
        </div>
        <div className="space-y-1">
          <Label htmlFor="p2" className="text-xs text-gray-600">
            Period 2 (Sep-Dec)
          </Label>
          <Input
            id="p2"
            type="number"
            value={value.p2}
            onChange={(e) => handleChange('p2', e.target.value)}
            disabled={disabled}
            className="h-9"
            step="0.01"
          />
        </div>
        <div className="space-y-1">
          <Label className="text-xs text-gray-600">Annual Total</Label>
          <div className="h-9 px-3 rounded-md border bg-gray-50 flex items-center justify-end font-medium text-sm">
            {currency ? formatCurrency(total) : total.toFixed(2)}
          </div>
        </div>
      </div>
    </div>
  )
}
