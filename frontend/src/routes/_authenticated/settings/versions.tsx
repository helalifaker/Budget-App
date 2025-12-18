import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { PageContainer } from '@/components/layout/PageContainer'
import { FormDialog } from '@/components/FormDialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Skeleton } from '@/components/ui/skeleton'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Checkbox } from '@/components/ui/checkbox'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  Plus,
  Edit,
  Trash2,
  Copy,
  Send,
  CheckCircle,
  Unlock,
  Wrench,
  FileCheck,
  FileUp,
  Archive,
  FolderOpen,
  TrendingUp,
  Target,
  FlaskConical,
  BarChart3,
} from 'lucide-react'
import {
  useVersions,
  useCreateVersion,
  useUpdateVersion,
  useDeleteVersion,
  useSubmitVersion,
  useApproveVersion,
  useCloneVersion,
  useRejectVersion,
  useSupersedeVersion,
} from '@/hooks/api/useVersions'
import {
  budgetVersionSchema,
  cloneBudgetVersionSchema,
  type BudgetVersionFormData,
  type CloneBudgetVersionFormData,
} from '@/schemas/configuration'
import { BudgetVersion, ScenarioType } from '@/types/api'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { z } from 'zod'
import { cn } from '@/lib/utils'

export const Route = createFileRoute('/_authenticated/settings/versions')({
  beforeLoad: requireAuth,
  component: BudgetVersionsPage,
})

// Schema for unlock form
const unlockVersionSchema = z.object({
  reason: z.string().min(5, 'Reason must be at least 5 characters'),
})
type UnlockVersionFormData = z.infer<typeof unlockVersionSchema>

// Workflow rules by scenario type
const CAN_SUBMIT: Set<ScenarioType> = new Set(['BUDGET', 'FORECAST', 'STRATEGIC'])
const CAN_APPROVE: Set<ScenarioType> = new Set(['ACTUAL', 'BUDGET', 'FORECAST', 'STRATEGIC'])
const CAN_REJECT: Set<ScenarioType> = CAN_SUBMIT

// Status configuration with icons and colors
const statusConfig: Record<string, { icon: React.ElementType; label: string; className: string }> =
  {
    working: {
      icon: Wrench,
      label: 'Working',
      className: 'bg-amber-100 text-amber-800 border-amber-200',
    },
    submitted: {
      icon: FileUp,
      label: 'Submitted',
      className: 'bg-blue-100 text-blue-800 border-blue-200',
    },
    approved: {
      icon: FileCheck,
      label: 'Approved',
      className: 'bg-green-100 text-green-800 border-green-200',
    },
    forecast: {
      icon: FileCheck,
      label: 'Forecast',
      className: 'bg-indigo-100 text-indigo-800 border-indigo-200',
    },
    superseded: {
      icon: Archive,
      label: 'Superseded',
      className: 'bg-slate-100 text-slate-600 border-slate-200',
    },
  }

// Scenario type configuration with icons and colors
const scenarioTypeConfig: Record<
  ScenarioType,
  { icon: React.ElementType; label: string; className: string; description: string }
> = {
  ACTUAL: {
    icon: BarChart3,
    label: 'Actual',
    className: 'bg-blue-100 text-blue-800 border-blue-200',
    description: 'Imported actual data (validated after import)',
  },
  BUDGET: {
    icon: Target,
    label: 'Budget',
    className: 'bg-amber-100 text-amber-800 border-amber-200',
    description: 'Standard budget with full workflow',
  },
  FORECAST: {
    icon: TrendingUp,
    label: 'Forecast',
    className: 'bg-purple-100 text-purple-800 border-purple-200',
    description: 'Mid-year forecast revisions',
  },
  STRATEGIC: {
    icon: Target,
    label: 'Strategic',
    className: 'bg-emerald-100 text-emerald-800 border-emerald-200',
    description: '5-year strategic plans',
  },
  WHAT_IF: {
    icon: FlaskConical,
    label: 'What-If',
    className: 'bg-slate-100 text-slate-600 border-slate-200',
    description: 'Sandbox scenarios (no workflow)',
  },
}

// Academic year helpers
function getCurrentAcademicYear(fiscalYear: number): string {
  // P1 (Jan-Aug) academic year - ending year
  return `${fiscalYear - 1}-${fiscalYear}`
}

function getPlannedAcademicYear(fiscalYear: number): string {
  // P2 (Sep-Dec) academic year - starting year
  return `${fiscalYear}-${fiscalYear + 1}`
}

// Generate fiscal year options (current year -2 to +5)
function getFiscalYearOptions(): number[] {
  const currentYear = new Date().getFullYear()
  const years: number[] = []
  for (let i = currentYear - 2; i <= currentYear + 5; i++) {
    years.push(i)
  }
  return years
}

// Relative time formatter
function formatRelativeTime(dateString: string | null | undefined): string {
  if (!dateString) return '-'

  const date = new Date(dateString)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffMinutes = Math.floor(diffMs / (1000 * 60))

  if (diffMinutes < 1) return 'Just now'
  if (diffMinutes < 60) return `${diffMinutes}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays === 1) return 'Yesterday'
  if (diffDays < 7) return `${diffDays} days ago`
  if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`
  return date.toLocaleDateString('fr-FR')
}

// Status Badge Component
function StatusBadge({ status }: { status: string }) {
  const config = statusConfig[status] || statusConfig.working
  const Icon = config.icon

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
        config.className
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {config.label}
    </span>
  )
}

// Scenario Type Badge Component
function ScenarioTypeBadge({ scenarioType }: { scenarioType: ScenarioType }) {
  const config = scenarioTypeConfig[scenarioType] || scenarioTypeConfig.BUDGET
  const Icon = config.icon

  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border',
        config.className
      )}
    >
      <Icon className="h-3.5 w-3.5" />
      {config.label}
    </span>
  )
}

// Filter Tabs Component
function FilterTabs({
  activeFilter,
  onFilterChange,
}: {
  activeFilter: ScenarioType | 'ALL'
  onFilterChange: (filter: ScenarioType | 'ALL') => void
}) {
  const filters: Array<{ value: ScenarioType | 'ALL'; label: string }> = [
    { value: 'ALL', label: 'All' },
    { value: 'BUDGET', label: 'Budget' },
    { value: 'ACTUAL', label: 'Actual' },
    { value: 'FORECAST', label: 'Forecast' },
    { value: 'STRATEGIC', label: 'Strategic' },
    { value: 'WHAT_IF', label: 'What-If' },
  ]

  return (
    <div className="flex gap-1 p-1 bg-subtle rounded-lg">
      {filters.map((filter) => (
        <button
          key={filter.value}
          onClick={() => onFilterChange(filter.value)}
          className={cn(
            'px-3 py-1.5 text-sm font-medium rounded-md transition-colors',
            activeFilter === filter.value
              ? 'bg-paper text-text-primary shadow-sm'
              : 'text-text-secondary hover:text-text-primary'
          )}
        >
          {filter.label}
        </button>
      ))}
    </div>
  )
}

// Loading Skeleton
function TableSkeleton() {
  return (
    <div className="rounded-xl border border-border-light shadow-efir-sm overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow className="bg-subtle/30">
            <TableHead className="w-[180px]">Name</TableHead>
            <TableHead className="w-[100px]">Type</TableHead>
            <TableHead className="w-[80px]">FY</TableHead>
            <TableHead className="w-[140px]">Period</TableHead>
            <TableHead className="w-[120px]">Status</TableHead>
            <TableHead className="w-[100px]">Created</TableHead>
            <TableHead className="w-[180px] text-right">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {[1, 2, 3].map((i) => (
            <TableRow key={i}>
              <TableCell>
                <Skeleton className="h-4 w-32" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-6 w-20 rounded-full" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-4 w-12" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-4 w-28" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-6 w-24 rounded-full" />
              </TableCell>
              <TableCell>
                <Skeleton className="h-4 w-16" />
              </TableCell>
              <TableCell>
                <div className="flex justify-end gap-1">
                  <Skeleton className="h-8 w-8 rounded" />
                  <Skeleton className="h-8 w-8 rounded" />
                  <Skeleton className="h-8 w-8 rounded" />
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

// Empty State Component
function EmptyState({ onCreateClick }: { onCreateClick: () => void }) {
  return (
    <div className="rounded-xl border border-border-light shadow-efir-sm bg-paper p-12 text-center">
      <div className="mx-auto w-16 h-16 bg-subtle rounded-full flex items-center justify-center mb-4">
        <FolderOpen className="h-8 w-8 text-text-tertiary" />
      </div>
      <h3 className="text-lg font-semibold text-text-primary mb-2">No Versions</h3>
      <p className="text-text-secondary mb-6 max-w-sm mx-auto">
        Get started by creating your first version to begin planning.
      </p>
      <Button onClick={onCreateClick}>
        <Plus className="h-4 w-4 mr-2" />
        Create First Version
      </Button>
    </div>
  )
}

// Action Button with Tooltip
function ActionButton({
  tooltip,
  icon: Icon,
  onClick,
  disabled,
  variant = 'outline',
  testId,
}: {
  tooltip: string
  icon: React.ElementType
  onClick: () => void
  disabled?: boolean
  variant?: 'outline' | 'default' | 'destructive'
  testId?: string
}) {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button
          size="icon"
          variant={variant}
          onClick={onClick}
          disabled={disabled}
          className="h-8 w-8"
          data-testid={testId}
        >
          <Icon className="h-4 w-4" />
        </Button>
      </TooltipTrigger>
      <TooltipContent>
        <p>{tooltip}</p>
      </TooltipContent>
    </Tooltip>
  )
}

function BudgetVersionsPage() {
  // Filter state
  const [scenarioFilter, setScenarioFilter] = useState<ScenarioType | 'ALL'>('ALL')

  // Fetch versions with optional filter
  const { data, isLoading, error } = useVersions({
    scenarioType: scenarioFilter === 'ALL' ? undefined : scenarioFilter,
  })

  const [rowData, setRowData] = useState<BudgetVersion[]>([])
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false)
  const [unlockDialogOpen, setUnlockDialogOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<BudgetVersion | null>(null)

  const createMutation = useCreateVersion()
  const updateMutation = useUpdateVersion()
  const deleteMutation = useDeleteVersion()
  const submitMutation = useSubmitVersion()
  const approveMutation = useApproveVersion()
  const cloneMutation = useCloneVersion()
  const rejectMutation = useRejectVersion()
  const supersedeMutation = useSupersedeVersion()

  const createForm = useForm<BudgetVersionFormData>({
    resolver: zodResolver(budgetVersionSchema),
    defaultValues: {
      name: '',
      fiscal_year: new Date().getFullYear(),
      academic_year: getPlannedAcademicYear(new Date().getFullYear()),
      scenario_type: 'BUDGET',
      notes: '',
    },
  })

  // Watch fiscal_year to auto-compute academic_year (use planned AY = P2)
  const watchedFiscalYear = createForm.watch('fiscal_year')

  useEffect(() => {
    if (watchedFiscalYear && !isNaN(watchedFiscalYear)) {
      createForm.setValue('academic_year', getPlannedAcademicYear(watchedFiscalYear))
    }
  }, [watchedFiscalYear, createForm])

  const editForm = useForm<Partial<BudgetVersionFormData>>({
    defaultValues: {
      name: '',
      notes: '',
    },
  })

  const cloneForm = useForm<CloneBudgetVersionFormData>({
    resolver: zodResolver(cloneBudgetVersionSchema),
    defaultValues: {
      name: '',
      fiscal_year: new Date().getFullYear(),
      academic_year: getPlannedAcademicYear(new Date().getFullYear()),
      scenario_type: 'BUDGET',
      clone_configuration: true,
    },
  })

  // Watch clone form fiscal_year to auto-compute academic_year
  const cloneWatchedFiscalYear = cloneForm.watch('fiscal_year')

  useEffect(() => {
    if (cloneWatchedFiscalYear && !isNaN(cloneWatchedFiscalYear)) {
      cloneForm.setValue('academic_year', getPlannedAcademicYear(cloneWatchedFiscalYear))
    }
  }, [cloneWatchedFiscalYear, cloneForm])

  const unlockForm = useForm<UnlockVersionFormData>({
    resolver: zodResolver(unlockVersionSchema),
    defaultValues: {
      reason: '',
    },
  })

  useEffect(() => {
    if (data?.items) {
      setRowData(data.items)
    }
  }, [data])

  useEffect(() => {
    if (selectedVersion && editDialogOpen) {
      editForm.reset({
        name: selectedVersion.name,
        notes: selectedVersion.notes || '',
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVersion, editDialogOpen])

  // Reset clone form when opening clone dialog
  useEffect(() => {
    if (selectedVersion && cloneDialogOpen) {
      cloneForm.reset({
        name: `${selectedVersion.name} (Copy)`,
        fiscal_year: selectedVersion.fiscal_year,
        academic_year: selectedVersion.academic_year,
        scenario_type: selectedVersion.scenario_type || 'BUDGET',
        clone_configuration: true,
      })
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedVersion, cloneDialogOpen])

  const handleCreate = async (formData: BudgetVersionFormData) => {
    try {
      await createMutation.mutateAsync(formData)
      setCreateDialogOpen(false)
      createForm.reset()
    } catch {
      // Error toast handled by mutation
    }
  }

  const handleEdit = async (formData: Partial<BudgetVersionFormData>) => {
    if (!selectedVersion) return
    try {
      await updateMutation.mutateAsync({
        id: selectedVersion.id,
        data: {
          name: formData.name,
          notes: formData.notes,
        },
      })
      setEditDialogOpen(false)
      setSelectedVersion(null)
    } catch {
      // Error toast handled by mutation
    }
  }

  const handleClone = async (formData: CloneBudgetVersionFormData) => {
    if (!selectedVersion) return
    try {
      await cloneMutation.mutateAsync({
        id: selectedVersion.id,
        data: formData,
      })
      setCloneDialogOpen(false)
      setSelectedVersion(null)
      cloneForm.reset()
    } catch {
      // Error toast handled by mutation
    }
  }

  const handleUnlock = async (formData: UnlockVersionFormData) => {
    if (!selectedVersion) return
    try {
      await rejectMutation.mutateAsync({
        id: selectedVersion.id,
        reason: formData.reason,
      })
      setUnlockDialogOpen(false)
      setSelectedVersion(null)
      unlockForm.reset()
    } catch {
      // Error toast handled by mutation
    }
  }

  const handleDelete = async (version: BudgetVersion) => {
    if (window.confirm(`Are you sure you want to delete "${version.name}"?`)) {
      try {
        await deleteMutation.mutateAsync(version.id)
      } catch {
        // Error toast handled by mutation
      }
    }
  }

  const handleSubmit = async (id: string) => {
    try {
      await submitMutation.mutateAsync(id)
    } catch {
      // Error toast handled by mutation
    }
  }

  const handleApprove = async (id: string, scenarioType: ScenarioType) => {
    const confirmMessage =
      scenarioType === 'ACTUAL'
        ? 'Are you sure you want to validate and approve this actual data?'
        : 'Are you sure you want to approve this version?'
    if (window.confirm(confirmMessage)) {
      try {
        await approveMutation.mutateAsync(id)
      } catch {
        // Error toast handled by mutation
      }
    }
  }

  const handleSupersede = async (version: BudgetVersion) => {
    if (
      window.confirm(
        `Archive "${version.name}"? This will mark it as superseded and it will no longer be editable.`
      )
    ) {
      try {
        await supersedeMutation.mutateAsync(version.id)
      } catch {
        // Error toast handled by mutation
      }
    }
  }

  // Check if actions are allowed based on scenario type
  const canSubmit = (version: BudgetVersion) =>
    version.status === 'working' && CAN_SUBMIT.has(version.scenario_type || 'BUDGET')

  const canApprove = (version: BudgetVersion) => {
    const scenarioType = version.scenario_type || 'BUDGET'
    // ACTUAL can be approved directly from working (skip submit)
    if (scenarioType === 'ACTUAL') {
      return version.status === 'working' && CAN_APPROVE.has(scenarioType)
    }
    // Others need to be submitted first
    return version.status === 'submitted' && CAN_APPROVE.has(scenarioType)
  }

  const canReject = (version: BudgetVersion) =>
    version.status === 'submitted' && CAN_REJECT.has(version.scenario_type || 'BUDGET')

  // Error state
  if (error) {
    return (
      <PageContainer title="Budget Versions" description="Manage budget scenarios and versions">
        <div className="rounded-xl border border-terracotta-200 bg-terracotta-50 p-6 text-center">
          <p className="text-terracotta-800 font-medium">Error loading versions</p>
          <p className="text-terracotta-600 text-sm mt-1">{error.message}</p>
        </div>
      </PageContainer>
    )
  }

  return (
    <TooltipProvider>
      <PageContainer
        title="Budget Versions"
        description="Manage budget scenarios and versions"
        actions={
          <Button data-testid="create-version-button" onClick={() => setCreateDialogOpen(true)}>
            <Plus className="h-4 w-4 mr-2" />
            New Version
          </Button>
        }
      >
        {/* Filter Tabs */}
        <div className="mb-4">
          <FilterTabs activeFilter={scenarioFilter} onFilterChange={setScenarioFilter} />
        </div>

        {isLoading ? (
          <TableSkeleton />
        ) : rowData.length === 0 ? (
          <EmptyState onCreateClick={() => setCreateDialogOpen(true)} />
        ) : (
          <div className="rounded-xl border border-border-light shadow-efir-sm overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow className="bg-subtle/30 hover:bg-subtle/30">
                  <TableHead className="w-[200px] font-semibold">Name</TableHead>
                  <TableHead className="w-[100px] font-semibold">Type</TableHead>
                  <TableHead className="w-[80px] font-semibold">FY</TableHead>
                  <TableHead className="w-[140px] font-semibold">Academic Year</TableHead>
                  <TableHead className="w-[120px] font-semibold">Status</TableHead>
                  <TableHead className="w-[100px] font-semibold">Created</TableHead>
                  <TableHead className="w-[180px] text-right font-semibold">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rowData.map((version) => (
                  <TableRow key={version.id} className="group">
                    <TableCell className="font-medium text-text-primary">{version.name}</TableCell>
                    <TableCell>
                      <ScenarioTypeBadge scenarioType={version.scenario_type || 'BUDGET'} />
                    </TableCell>
                    <TableCell>{version.fiscal_year}</TableCell>
                    <TableCell className="text-text-secondary">{version.academic_year}</TableCell>
                    <TableCell>
                      <StatusBadge status={version.status} />
                    </TableCell>
                    <TableCell className="text-text-secondary text-sm">
                      {formatRelativeTime(version.created_at)}
                    </TableCell>
                    <TableCell>
                      <div className="flex justify-end gap-1">
                        {/* Edit - only for working status */}
                        {version.status === 'working' && (
                          <ActionButton
                            tooltip="Edit"
                            icon={Edit}
                            onClick={() => {
                              setSelectedVersion(version)
                              setEditDialogOpen(true)
                            }}
                            testId="edit-button"
                          />
                        )}

                        {/* Clone - always available */}
                        <ActionButton
                          tooltip="Clone"
                          icon={Copy}
                          onClick={() => {
                            setSelectedVersion(version)
                            setCloneDialogOpen(true)
                          }}
                          testId="copy-button"
                        />

                        {/* Submit - only for working status and submittable types */}
                        {canSubmit(version) && (
                          <ActionButton
                            tooltip="Submit for Approval"
                            icon={Send}
                            onClick={() => handleSubmit(version.id)}
                            disabled={submitMutation.isPending}
                            variant="default"
                            testId="submit-button"
                          />
                        )}

                        {/* Unlock - only for submitted status and rejectable types */}
                        {canReject(version) && (
                          <ActionButton
                            tooltip="Unlock (Return to Working)"
                            icon={Unlock}
                            onClick={() => {
                              setSelectedVersion(version)
                              setUnlockDialogOpen(true)
                            }}
                            testId="unlock-button"
                          />
                        )}

                        {/* Approve - context-dependent (ACTUAL: from working, others: from submitted) */}
                        {canApprove(version) && (
                          <ActionButton
                            tooltip={
                              version.scenario_type === 'ACTUAL' ? 'Validate & Approve' : 'Approve'
                            }
                            icon={CheckCircle}
                            onClick={() =>
                              handleApprove(version.id, version.scenario_type || 'BUDGET')
                            }
                            disabled={approveMutation.isPending}
                            variant="default"
                            testId="approve-button"
                          />
                        )}

                        {/* Delete - only for working/submitted status */}
                        {(version.status === 'working' || version.status === 'submitted') && (
                          <ActionButton
                            tooltip={
                              version.status === 'submitted'
                                ? 'Delete (Remove from approval flow)'
                                : 'Delete'
                            }
                            icon={Trash2}
                            onClick={() => handleDelete(version)}
                            disabled={deleteMutation.isPending}
                            variant="destructive"
                            testId="delete-button"
                          />
                        )}

                        {/* Supersede - only for working status */}
                        {version.status === 'working' && (
                          <ActionButton
                            tooltip="Archive (Supersede)"
                            icon={Archive}
                            onClick={() => handleSupersede(version)}
                            disabled={supersedeMutation.isPending}
                            testId="supersede-button"
                          />
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </PageContainer>

      {/* Create Dialog */}
      <FormDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        title="Create Budget Version"
        description="Create a new version"
        onSubmit={createForm.handleSubmit(handleCreate)}
        isSubmitting={createMutation.isPending}
        submitLabel="Create"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="name">Name</Label>
            <Input
              id="name"
              {...createForm.register('name')}
              placeholder="e.g., 2024-2025 Budget"
            />
            {createForm.formState.errors.name && (
              <p className="text-sm text-error-600 mt-1">
                {createForm.formState.errors.name.message}
              </p>
            )}
          </div>

          <div>
            <Label>Version Type</Label>
            <RadioGroup
              value={createForm.watch('scenario_type')}
              onValueChange={(value: string) =>
                createForm.setValue('scenario_type', value as ScenarioType)
              }
              className="grid grid-cols-2 gap-2 mt-2"
            >
              {(
                Object.entries(scenarioTypeConfig) as [
                  ScenarioType,
                  typeof scenarioTypeConfig.BUDGET,
                ][]
              ).map(([type, config]) => (
                <div
                  key={type}
                  className={cn(
                    'flex items-center space-x-2 rounded-lg border p-3 cursor-pointer hover:bg-subtle/50 transition-colors',
                    createForm.watch('scenario_type') === type
                      ? 'border-primary bg-primary/5'
                      : 'border-border-light'
                  )}
                  onClick={() => createForm.setValue('scenario_type', type)}
                >
                  <RadioGroupItem value={type} id={`type-${type}`} />
                  <div className="flex-1">
                    <Label htmlFor={`type-${type}`} className="cursor-pointer font-medium">
                      <config.icon className="h-4 w-4 inline-block mr-1.5" />
                      {config.label}
                    </Label>
                    <p className="text-xs text-text-tertiary mt-0.5">{config.description}</p>
                  </div>
                </div>
              ))}
            </RadioGroup>
          </div>

          <div>
            <Label htmlFor="fiscal_year">Fiscal Year</Label>
            <Select
              value={String(watchedFiscalYear)}
              onValueChange={(value) => createForm.setValue('fiscal_year', parseInt(value))}
            >
              <SelectTrigger className="mt-1.5">
                <SelectValue placeholder="Select fiscal year" />
              </SelectTrigger>
              <SelectContent>
                {getFiscalYearOptions().map((year) => (
                  <SelectItem key={year} value={String(year)}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {createForm.formState.errors.fiscal_year && (
              <p className="text-sm text-error-600 mt-1">
                {createForm.formState.errors.fiscal_year.message}
              </p>
            )}
          </div>

          {/* Academic Years Display */}
          <div className="grid grid-cols-2 gap-4">
            {/* Current Academic Year (P1) */}
            <div className="rounded-lg border border-border-light bg-subtle/50 p-4">
              <div className="text-xs text-text-tertiary font-medium uppercase tracking-wide">
                Current Academic Year
              </div>
              <div className="text-lg font-semibold text-text-primary mt-1">
                {getCurrentAcademicYear(watchedFiscalYear)}
              </div>
              <div className="text-xs text-text-secondary mt-1">
                P1: Jan-Aug {watchedFiscalYear}
              </div>
            </div>

            {/* Planned Academic Year (P2) */}
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
              <div className="text-xs text-text-tertiary font-medium uppercase tracking-wide">
                Planned Academic Year
              </div>
              <div className="text-lg font-semibold text-primary mt-1">
                {getPlannedAcademicYear(watchedFiscalYear)}
              </div>
              <div className="text-xs text-text-secondary mt-1">
                P2: Sep-Dec {watchedFiscalYear}
              </div>
            </div>
          </div>

          {/* Hidden academic_year field for form submission */}
          <input type="hidden" {...createForm.register('academic_year')} />

          <div>
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Textarea id="notes" {...createForm.register('notes')} rows={2} />
          </div>
        </div>
      </FormDialog>

      {/* Edit Dialog */}
      <FormDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        title="Edit Budget Version"
        description="Update version details"
        onSubmit={editForm.handleSubmit(handleEdit)}
        isSubmitting={updateMutation.isPending}
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="edit-name">Name</Label>
            <Input id="edit-name" {...editForm.register('name')} />
            {editForm.formState.errors.name && (
              <p className="text-sm text-error-600 mt-1">
                {editForm.formState.errors.name.message}
              </p>
            )}
          </div>
          <div>
            <Label htmlFor="edit-notes">Notes</Label>
            <Textarea id="edit-notes" {...editForm.register('notes')} rows={2} />
          </div>
          {selectedVersion && (
            <div className="rounded-lg bg-subtle p-3 text-sm text-text-secondary">
              <p>
                <strong>Type:</strong>{' '}
                <ScenarioTypeBadge scenarioType={selectedVersion.scenario_type || 'BUDGET'} />
              </p>
              <p className="mt-1 text-xs text-text-tertiary">
                Note: Version type cannot be changed after creation.
              </p>
            </div>
          )}
        </div>
      </FormDialog>

      {/* Clone Dialog */}
      <FormDialog
        open={cloneDialogOpen}
        onOpenChange={setCloneDialogOpen}
        title="Clone Budget Version"
        description={`Clone "${selectedVersion?.name}"`}
        onSubmit={cloneForm.handleSubmit(handleClone)}
        isSubmitting={cloneMutation.isPending}
        submitLabel="Clone"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="clone-name">New Version Name</Label>
            <Input
              id="clone-name"
              {...cloneForm.register('name')}
              placeholder="e.g., 2024-2025 Budget (Copy)"
            />
            {cloneForm.formState.errors.name && (
              <p className="text-sm text-error-600 mt-1">
                {cloneForm.formState.errors.name.message}
              </p>
            )}
          </div>

          <div>
            <Label>Version Type</Label>
            <RadioGroup
              value={cloneForm.watch('scenario_type')}
              onValueChange={(value: string) =>
                cloneForm.setValue('scenario_type', value as ScenarioType)
              }
              className="grid grid-cols-2 gap-2 mt-2"
            >
              {(
                Object.entries(scenarioTypeConfig) as [
                  ScenarioType,
                  typeof scenarioTypeConfig.BUDGET,
                ][]
              ).map(([type, config]) => (
                <div
                  key={type}
                  className={cn(
                    'flex items-center space-x-2 rounded-lg border p-3 cursor-pointer hover:bg-subtle/50 transition-colors',
                    cloneForm.watch('scenario_type') === type
                      ? 'border-primary bg-primary/5'
                      : 'border-border-light'
                  )}
                  onClick={() => cloneForm.setValue('scenario_type', type)}
                >
                  <RadioGroupItem value={type} id={`clone-type-${type}`} />
                  <div className="flex-1">
                    <Label htmlFor={`clone-type-${type}`} className="cursor-pointer font-medium">
                      <config.icon className="h-4 w-4 inline-block mr-1.5" />
                      {config.label}
                    </Label>
                  </div>
                </div>
              ))}
            </RadioGroup>
          </div>

          <div>
            <Label htmlFor="clone-fiscal_year">Fiscal Year</Label>
            <Select
              value={String(cloneWatchedFiscalYear)}
              onValueChange={(value) => cloneForm.setValue('fiscal_year', parseInt(value))}
            >
              <SelectTrigger className="mt-1.5">
                <SelectValue placeholder="Select fiscal year" />
              </SelectTrigger>
              <SelectContent>
                {getFiscalYearOptions().map((year) => (
                  <SelectItem key={year} value={String(year)}>
                    {year}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {cloneForm.formState.errors.fiscal_year && (
              <p className="text-sm text-error-600 mt-1">
                {cloneForm.formState.errors.fiscal_year.message}
              </p>
            )}
          </div>

          {/* Academic Years Display */}
          <div className="grid grid-cols-2 gap-4">
            {/* Current Academic Year (P1) */}
            <div className="rounded-lg border border-border-light bg-subtle/50 p-4">
              <div className="text-xs text-text-tertiary font-medium uppercase tracking-wide">
                Current Academic Year
              </div>
              <div className="text-lg font-semibold text-text-primary mt-1">
                {getCurrentAcademicYear(cloneWatchedFiscalYear)}
              </div>
              <div className="text-xs text-text-secondary mt-1">
                P1: Jan-Aug {cloneWatchedFiscalYear}
              </div>
            </div>

            {/* Planned Academic Year (P2) */}
            <div className="rounded-lg border border-primary/30 bg-primary/5 p-4">
              <div className="text-xs text-text-tertiary font-medium uppercase tracking-wide">
                Planned Academic Year
              </div>
              <div className="text-lg font-semibold text-primary mt-1">
                {getPlannedAcademicYear(cloneWatchedFiscalYear)}
              </div>
              <div className="text-xs text-text-secondary mt-1">
                P2: Sep-Dec {cloneWatchedFiscalYear}
              </div>
            </div>
          </div>

          {/* Hidden academic_year field for form submission */}
          <input type="hidden" {...cloneForm.register('academic_year')} />

          <div className="flex items-center space-x-2">
            <Checkbox
              id="clone-config"
              checked={cloneForm.watch('clone_configuration')}
              onCheckedChange={(checked) =>
                cloneForm.setValue('clone_configuration', checked === true)
              }
            />
            <Label htmlFor="clone-config" className="cursor-pointer">
              Clone configuration parameters
            </Label>
          </div>
        </div>
      </FormDialog>

      {/* Unlock Dialog */}
      <FormDialog
        open={unlockDialogOpen}
        onOpenChange={(open) => {
          setUnlockDialogOpen(open)
          if (!open) {
            unlockForm.reset()
          }
        }}
        title="Unlock Budget Version"
        description={`Return "${selectedVersion?.name}" to Working status. This will allow further editing.`}
        onSubmit={unlockForm.handleSubmit(handleUnlock)}
        isSubmitting={rejectMutation.isPending}
        submitLabel="Unlock"
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="unlock-reason">Reason for Unlocking</Label>
            <Textarea
              id="unlock-reason"
              {...unlockForm.register('reason')}
              placeholder="Please explain why this version needs to be unlocked..."
              rows={4}
            />
            {unlockForm.formState.errors.reason && (
              <p className="text-sm text-error-600 mt-1">
                {unlockForm.formState.errors.reason.message}
              </p>
            )}
            <p className="text-xs text-text-tertiary mt-2">
              This reason will be recorded in the version&apos;s audit log.
            </p>
          </div>
        </div>
      </FormDialog>
    </TooltipProvider>
  )
}
