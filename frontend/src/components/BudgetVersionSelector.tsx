import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'
import { BudgetVersion } from '@/types/api'

interface BudgetVersionSelectorProps {
  value: string | undefined
  onChange: (versionId: string) => void
  label?: string
  className?: string
  showCreateButton?: boolean
}

export function BudgetVersionSelector({
  value,
  onChange,
  label = 'Budget Version',
  className,
}: BudgetVersionSelectorProps) {
  const { data: versions, isLoading } = useBudgetVersions()

  const getStatusBadge = (status: BudgetVersion['status']) => {
    const variants: Record<BudgetVersion['status'], 'default' | 'info' | 'success' | 'warning'> = {
      WORKING: 'info',
      SUBMITTED: 'warning',
      APPROVED: 'success',
      SUPERSEDED: 'default',
    }
    return <Badge variant={variants[status]}>{status}</Badge>
  }

  if (isLoading) {
    return (
      <div className={className}>
        <Label>{label}</Label>
        <Select disabled>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Loading..." />
          </SelectTrigger>
        </Select>
      </div>
    )
  }

  return (
    <div className={className}>
      <Label>{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-[300px]">
          <SelectValue placeholder="Select budget version" />
        </SelectTrigger>
        <SelectContent>
          {versions?.items.map((version) => (
            <SelectItem key={version.id} value={version.id}>
              <div className="flex items-center justify-between gap-4 min-w-[250px]">
                <span className="font-medium">{version.name}</span>
                <div className="flex items-center gap-2">
                  <span className="text-xs text-gray-500">FY{version.fiscal_year}</span>
                  {getStatusBadge(version.status)}
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
