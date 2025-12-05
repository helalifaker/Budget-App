/**
 * GlobalVersionSelector
 *
 * A prominent, luxuriously styled budget version selector for the header.
 * Uses the global BudgetVersionContext to persist selection across the app.
 *
 * Features:
 * - Gold accent styling for premium feel
 * - Groups versions by status
 * - Shows fiscal year and status badge inline
 * - Keyboard accessible
 */

import { ChevronDown, Calendar, FileCheck } from 'lucide-react'
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import type { BudgetVersion } from '@/types/api'
import { cn } from '@/lib/utils'

interface GlobalVersionSelectorProps {
  className?: string
}

/**
 * Get status badge styling with luxury gold accent
 */
function getStatusBadge(status: BudgetVersion['status']) {
  const config: Record<
    BudgetVersion['status'],
    { variant: 'default' | 'info' | 'success' | 'warning'; label: string }
  > = {
    working: { variant: 'info', label: 'Working' },
    submitted: { variant: 'warning', label: 'Submitted' },
    approved: { variant: 'success', label: 'Approved' },
    forecast: { variant: 'info', label: 'Forecast' },
    superseded: { variant: 'default', label: 'Superseded' },
  }
  const { variant, label } = config[status]
  return (
    <Badge variant={variant} className="text-[10px] px-1.5 py-0">
      {label}
    </Badge>
  )
}

/**
 * Group versions by status for better organization
 */
function groupVersionsByStatus(versions: BudgetVersion[]) {
  const groups: Record<string, BudgetVersion[]> = {
    working: [],
    submitted: [],
    approved: [],
    other: [],
  }

  versions.forEach((v) => {
    if (v.status === 'working') groups.working.push(v)
    else if (v.status === 'submitted') groups.submitted.push(v)
    else if (v.status === 'approved') groups.approved.push(v)
    else groups.other.push(v)
  })

  return groups
}

export function GlobalVersionSelector({ className }: GlobalVersionSelectorProps) {
  const { selectedVersionId, selectedVersion, setSelectedVersionId, versions, isLoading } =
    useBudgetVersion()

  // Group versions for organized display
  const groupedVersions = groupVersionsByStatus(versions)

  // Loading state
  if (isLoading) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg',
          'bg-sand-100 border border-sand-200',
          'animate-pulse',
          className
        )}
      >
        <FileCheck className="w-4 h-4 text-twilight-400" />
        <span className="text-sm text-twilight-500">Loading...</span>
      </div>
    )
  }

  // No versions available
  if (versions.length === 0) {
    return (
      <div
        className={cn(
          'flex items-center gap-2 px-3 py-2 rounded-lg',
          'bg-sand-50 border border-sand-200',
          className
        )}
      >
        <FileCheck className="w-4 h-4 text-twilight-400" />
        <span className="text-sm text-twilight-500">No budget versions</span>
      </div>
    )
  }

  return (
    <Select
      value={selectedVersionId ?? ''}
      onValueChange={(value) => setSelectedVersionId(value || undefined)}
    >
      <SelectTrigger
        data-testid="version-selector"
        className={cn(
          // Base styling
          'w-auto min-w-[280px] max-w-[360px]',
          'h-10 px-3',
          // Luxury styling
          'bg-white border-sand-200',
          'hover:border-gold-400 hover:bg-sand-50',
          'focus:ring-2 focus:ring-gold-400/30 focus:border-gold-500',
          // Typography
          'text-sm font-medium text-brown-800',
          // Transition
          'transition-all duration-200',
          className
        )}
      >
        <div className="flex items-center gap-2 w-full">
          <FileCheck className="w-4 h-4 text-gold-600 shrink-0" />
          <SelectValue placeholder="Select budget version">
            {selectedVersion && (
              <div className="flex items-center gap-2 truncate">
                <span className="truncate">{selectedVersion.name}</span>
                <span className="text-xs text-twilight-500 shrink-0">
                  FY{selectedVersion.fiscal_year}
                </span>
                {getStatusBadge(selectedVersion.status)}
              </div>
            )}
          </SelectValue>
          <ChevronDown className="w-4 h-4 text-twilight-400 shrink-0 ml-auto" />
        </div>
      </SelectTrigger>

      <SelectContent
        className={cn(
          // Luxury dropdown styling
          'bg-white border border-sand-200',
          'shadow-luxe-lg rounded-xl',
          'overflow-hidden'
        )}
      >
        {/* Working Versions */}
        {groupedVersions.working.length > 0 && (
          <SelectGroup>
            <SelectLabel className="text-xs font-semibold text-twilight-500 uppercase tracking-wide px-3 py-2 bg-sand-50">
              Working Drafts
            </SelectLabel>
            {groupedVersions.working.map((version) => (
              <VersionItem key={version.id} version={version} />
            ))}
          </SelectGroup>
        )}

        {/* Submitted Versions */}
        {groupedVersions.submitted.length > 0 && (
          <SelectGroup>
            <SelectLabel className="text-xs font-semibold text-twilight-500 uppercase tracking-wide px-3 py-2 bg-sand-50 border-t border-sand-100">
              Under Review
            </SelectLabel>
            {groupedVersions.submitted.map((version) => (
              <VersionItem key={version.id} version={version} />
            ))}
          </SelectGroup>
        )}

        {/* Approved Versions */}
        {groupedVersions.approved.length > 0 && (
          <SelectGroup>
            <SelectLabel className="text-xs font-semibold text-twilight-500 uppercase tracking-wide px-3 py-2 bg-sand-50 border-t border-sand-100">
              Approved
            </SelectLabel>
            {groupedVersions.approved.map((version) => (
              <VersionItem key={version.id} version={version} />
            ))}
          </SelectGroup>
        )}

        {/* Other Versions (forecast, superseded) */}
        {groupedVersions.other.length > 0 && (
          <SelectGroup>
            <SelectLabel className="text-xs font-semibold text-twilight-500 uppercase tracking-wide px-3 py-2 bg-sand-50 border-t border-sand-100">
              Other
            </SelectLabel>
            {groupedVersions.other.map((version) => (
              <VersionItem key={version.id} version={version} />
            ))}
          </SelectGroup>
        )}
      </SelectContent>
    </Select>
  )
}

/**
 * Individual version item in the dropdown
 */
function VersionItem({ version }: { version: BudgetVersion }) {
  return (
    <SelectItem
      value={version.id}
      className={cn(
        'px-3 py-2.5',
        'cursor-pointer',
        'hover:bg-sand-50',
        'focus:bg-gold-50 focus:text-brown-900',
        'transition-colors duration-150'
      )}
    >
      <div className="flex items-center justify-between gap-4 min-w-[260px]">
        <div className="flex items-center gap-2">
          <Calendar className="w-3.5 h-3.5 text-twilight-400" />
          <span className="font-medium text-brown-800">{version.name}</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-twilight-500">FY{version.fiscal_year}</span>
          {getStatusBadge(version.status)}
        </div>
      </div>
    </SelectItem>
  )
}
