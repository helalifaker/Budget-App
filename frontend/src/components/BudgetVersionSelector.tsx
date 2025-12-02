import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'

interface BudgetVersionSelectorProps {
  value?: string
  onChange: (versionId: string) => void
  label?: string
  className?: string
}

export function BudgetVersionSelector({
  value,
  onChange,
  label = 'Budget Version',
  className,
}: BudgetVersionSelectorProps) {
  const { data, isLoading, error } = useBudgetVersions()

  if (error) {
    return <div className="text-sm text-error-600">Error loading budget versions</div>
  }

  return (
    <div className={className}>
      <Label htmlFor="budget-version-select">{label}</Label>
      <Select value={value} onValueChange={onChange} disabled={isLoading}>
        <SelectTrigger id="budget-version-select" className="mt-1">
          <SelectValue placeholder={isLoading ? 'Loading...' : 'Select a budget version'} />
        </SelectTrigger>
        <SelectContent>
          {data?.items.map((version) => (
            <SelectItem key={version.id} value={version.id}>
              {version.name} ({version.fiscal_year}) - {version.status}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  )
}
