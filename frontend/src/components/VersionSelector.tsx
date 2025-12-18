import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { useVersions } from '@/hooks/api/useVersions'
import { BudgetVersion } from '@/types/api'

interface VersionSelectorProps {
  value: string | undefined
  onChange: (versionId: string) => void
  label?: string
  className?: string
  showCreateButton?: boolean
}

// Backward compatibility alias
export type BudgetVersionSelectorProps = VersionSelectorProps

export function VersionSelector({
  value,
  onChange,
  label = 'Version',
  className,
}: VersionSelectorProps) {
  const { data: versions, isLoading } = useVersions()

  // Use empty string when value is undefined to keep Select controlled
  // This prevents React's "changing from uncontrolled to controlled" warning
  const controlledValue = value ?? ''

  const getStatusBadge = (status: BudgetVersion['status']) => {
    const variants: Record<BudgetVersion['status'], 'default' | 'info' | 'success' | 'warning'> = {
      working: 'info',
      submitted: 'warning',
      approved: 'success',
      forecast: 'info',
      superseded: 'default',
    }
    return <Badge variant={variants[status]}>{status.toUpperCase()}</Badge>
  }

  if (isLoading) {
    return (
      <div className={className}>
        <Label>{label}</Label>
        <Select value={controlledValue} disabled>
          <SelectTrigger className="w-[300px]">
            <SelectValue placeholder="Loading..." />
          </SelectTrigger>
        </Select>
      </div>
    )
  }

  // Handle empty state - no versions exist
  const hasVersions = versions?.items && versions.items.length > 0

  return (
    <div className={className}>
      <Label>{label}</Label>
      <Select value={controlledValue} onValueChange={onChange} disabled={!hasVersions}>
        <SelectTrigger className="w-[300px]">
          <SelectValue placeholder={hasVersions ? 'Select version' : 'No versions available'} />
        </SelectTrigger>
        {hasVersions && (
          <SelectContent>
            {versions.items.map((version) => (
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
        )}
      </Select>
    </div>
  )
}

// Backward compatibility alias
export const BudgetVersionSelector = VersionSelector
