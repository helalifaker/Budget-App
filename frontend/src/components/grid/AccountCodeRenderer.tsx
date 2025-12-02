import { CustomCellRendererProps } from 'ag-grid-react'
import { cn } from '@/lib/utils'

interface AccountCodeRendererProps extends CustomCellRendererProps {
  value: string
}

// Account code categories with colors
const getAccountCategory = (code: string): { label: string; color: string } => {
  const codeNum = parseInt(code)

  if (codeNum >= 70000 && codeNum < 71000) {
    return { label: 'Tuition', color: 'bg-green-100 text-green-800' }
  }
  if (codeNum >= 70100 && codeNum < 70300) {
    return { label: 'Enrollment Fees', color: 'bg-blue-100 text-blue-800' }
  }
  if (codeNum >= 75000 && codeNum < 78000) {
    return { label: 'Other Revenue', color: 'bg-purple-100 text-purple-800' }
  }
  if (codeNum >= 64000 && codeNum < 65000) {
    return { label: 'Salaries', color: 'bg-orange-100 text-orange-800' }
  }
  if (codeNum >= 60000 && codeNum < 63000) {
    return { label: 'Supplies', color: 'bg-yellow-100 text-yellow-800' }
  }
  if (codeNum >= 20000 && codeNum < 30000) {
    return { label: 'CapEx', color: 'bg-indigo-100 text-indigo-800' }
  }

  return { label: 'Other', color: 'bg-gray-100 text-gray-800' }
}

export function AccountCodeRenderer({ value }: AccountCodeRendererProps) {
  if (!value) return null

  const category = getAccountCategory(value)

  return (
    <div className="flex items-center gap-2 h-full py-1">
      <span className="font-mono font-medium">{value}</span>
      <span className={cn('text-xs px-2 py-0.5 rounded-full', category.color)}>
        {category.label}
      </span>
    </div>
  )
}
