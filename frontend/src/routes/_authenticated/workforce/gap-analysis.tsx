/**
 * Workforce - Gap Analysis (TRMD)
 *
 * TRMD (Tableau de Répartition des Moyens par Discipline) gap analysis:
 * - Besoins (Requirements) from DHG calculations
 * - Moyens (Available) from employee registry
 * - Déficit/Surplus calculation
 * - "Create Placeholder" functionality with validation button
 *
 * @module /teachers/dhg/gap-analysis
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useMemo, useCallback } from 'react'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Scale,
  TrendingUp,
  TrendingDown,
  CheckCircle2,
  UserPlus,
  AlertCircle,
  RefreshCw,
  MinusCircle,
} from 'lucide-react'
import { useVersion } from '@/contexts/VersionContext'
import { useTRMDGapAnalysis } from '@/hooks/api/useDHG'
import { useSubjects, useCycles } from '@/hooks/api/useConfiguration'
import { useCreatePlaceholderEmployee } from '@/hooks/api/useWorkforce'
import type { PlaceholderEmployeeCreate, EmployeeCategory } from '@/types/workforce'
import { EMPLOYEE_CATEGORY_LABELS } from '@/types/workforce'
import type { ColumnDef, CellContext } from '@tanstack/react-table'
import { TanStackDataTable } from '@/components/grid/tanstack'

export const Route = createFileRoute('/_authenticated/workforce/gap-analysis')({
  beforeLoad: requireAuth,
  component: GapAnalysisPage,
})

// ============================================================================
// Types
// ============================================================================

interface TRMDGapItem extends Record<string, unknown> {
  subject_id: string
  cycle_id: string
  required_fte: number
  aefe_allocated: number
  local_allocated: number
  total_allocated: number
  deficit: number
  hsa_needed: number
  // Added for display
  subject_name?: string
  cycle_name?: string
}

// ============================================================================
// Create Placeholder Dialog
// ============================================================================

interface CreatePlaceholderDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  gapItem: TRMDGapItem | null
  versionId: string
}

function CreatePlaceholderDialog({
  open,
  onOpenChange,
  gapItem,
  versionId,
}: CreatePlaceholderDialogProps) {
  const [category, setCategory] = useState<EmployeeCategory>('LOCAL_TEACHER')
  const [fte, setFte] = useState(1.0)
  const [estimatedSalary, setEstimatedSalary] = useState<number | null>(null)
  const [notes, setNotes] = useState('')
  const [validationStep, setValidationStep] = useState<'input' | 'confirm'>('input')

  const createPlaceholderMutation = useCreatePlaceholderEmployee()

  // Reset form when dialog opens with a new gap item
  useMemo(() => {
    if (gapItem) {
      setFte(Math.min(gapItem.deficit, 1.0))
      setNotes(`From DHG gap: ${gapItem.subject_name || 'Subject'}`)
      setValidationStep('input')
    }
  }, [gapItem])

  const handleValidate = () => {
    setValidationStep('confirm')
  }

  const handleCreate = async () => {
    if (!gapItem) return

    const data: PlaceholderEmployeeCreate = {
      version_id: versionId,
      category,
      cycle_id: gapItem.cycle_id || undefined,
      subject_id: gapItem.subject_id || undefined,
      fte,
      estimated_salary_sar: estimatedSalary || undefined,
      notes: notes || undefined,
    }

    try {
      await createPlaceholderMutation.mutateAsync(data)
      onOpenChange(false)
      setValidationStep('input')
    } catch {
      // Error handled by mutation
    }
  }

  const handleBack = () => {
    setValidationStep('input')
  }

  const categoryOptions: EmployeeCategory[] = ['LOCAL_TEACHER', 'AEFE_DETACHED', 'ADMINISTRATIVE']

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-gold-600" />
            {validationStep === 'input' ? 'Create Placeholder Position' : 'Confirm & Add'}
          </DialogTitle>
          <DialogDescription>
            {gapItem && (
              <>
                Fill deficit: {gapItem.subject_name || 'Subject'} ({gapItem.deficit.toFixed(2)} FTE
                needed)
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        {validationStep === 'input' ? (
          <>
            <div className="space-y-4 py-4">
              <div>
                <Label htmlFor="category">Employee Category</Label>
                <Select value={category} onValueChange={(v) => setCategory(v as EmployeeCategory)}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {categoryOptions.map((cat) => (
                      <SelectItem key={cat} value={cat}>
                        {EMPLOYEE_CATEGORY_LABELS[cat]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="fte">FTE (Full Time Equivalent)</Label>
                <Input
                  id="fte"
                  type="number"
                  min={0.1}
                  max={1}
                  step={0.1}
                  value={fte}
                  onChange={(e) => setFte(parseFloat(e.target.value) || 0)}
                  className="mt-1"
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Gap deficit: {gapItem?.deficit.toFixed(2)} FTE
                </p>
              </div>

              <div>
                <Label htmlFor="estimated_salary">Estimated Salary (SAR/month)</Label>
                <Input
                  id="estimated_salary"
                  type="number"
                  min={0}
                  value={estimatedSalary || ''}
                  onChange={(e) =>
                    setEstimatedSalary(e.target.value ? parseFloat(e.target.value) : null)
                  }
                  placeholder="Leave empty for category average"
                  className="mt-1"
                />
              </div>

              <div>
                <Label htmlFor="notes">Notes</Label>
                <Input
                  id="notes"
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Optional notes..."
                  className="mt-1"
                />
              </div>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button onClick={handleValidate} className="gap-2">
                <CheckCircle2 className="h-4 w-4" />
                Validate
              </Button>
            </DialogFooter>
          </>
        ) : (
          <>
            <div className="space-y-4 py-4">
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
                <p className="font-medium text-amber-800 mb-2">Confirm Placeholder Creation</p>
                <div className="space-y-1 text-sm text-amber-700">
                  <p>
                    <strong>Category:</strong> {EMPLOYEE_CATEGORY_LABELS[category]}
                  </p>
                  <p>
                    <strong>FTE:</strong> {fte}
                  </p>
                  <p>
                    <strong>Subject:</strong> {gapItem?.subject_name || 'N/A'}
                  </p>
                  {estimatedSalary && (
                    <p>
                      <strong>Est. Salary:</strong> {estimatedSalary.toLocaleString()} SAR/month
                    </p>
                  )}
                </div>
              </div>

              <p className="text-sm text-muted-foreground">
                This will create a placeholder position marked as &quot;Planned&quot; in the
                Employee Registry. It will be included in budget calculations.
              </p>
            </div>

            <DialogFooter>
              <Button variant="outline" onClick={handleBack}>
                Back
              </Button>
              <Button
                onClick={handleCreate}
                disabled={createPlaceholderMutation.isPending}
                className="gap-2 bg-gold-600 hover:bg-gold-700"
              >
                <CheckCircle2 className="h-4 w-4" />
                {createPlaceholderMutation.isPending ? 'Creating...' : 'Confirm & Add'}
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Main Page Component
// ============================================================================

function GapAnalysisPage() {
  const { selectedVersionId } = useVersion()

  // Dialog state
  const [placeholderDialogOpen, setPlaceholderDialogOpen] = useState(false)
  const [selectedGapItem, setSelectedGapItem] = useState<TRMDGapItem | null>(null)

  // Queries
  const { data: trmdData, isLoading, refetch } = useTRMDGapAnalysis(selectedVersionId!)
  const { data: subjectsData } = useSubjects()
  const { data: cyclesData } = useCycles()

  // Create lookup maps for display names
  const subjectMap = useMemo(() => {
    if (!subjectsData) return new Map<string, string>()
    const map = new Map<string, string>()
    subjectsData.forEach((s) => map.set(s.id, s.name_fr || s.name_en))
    return map
  }, [subjectsData])

  const cycleMap = useMemo(() => {
    if (!cyclesData) return new Map<string, string>()
    const map = new Map<string, string>()
    cyclesData.forEach((c) => map.set(c.id, c.name_fr || c.name_en))
    return map
  }, [cyclesData])

  // Enrich gap data with display names
  const enrichedGaps = useMemo<TRMDGapItem[]>(() => {
    if (!trmdData?.gaps) return []
    return trmdData.gaps.map((gap) => ({
      ...gap,
      subject_name: subjectMap.get(gap.subject_id) || 'Unknown Subject',
      cycle_name: cycleMap.get(gap.cycle_id) || 'Unknown Cycle',
    }))
  }, [trmdData, subjectMap, cycleMap])

  // Summary calculations
  const summary = useMemo(() => {
    const totalRequired = enrichedGaps.reduce((sum, g) => sum + g.required_fte, 0)
    const totalAllocated = enrichedGaps.reduce((sum, g) => sum + g.total_allocated, 0)
    const totalDeficit = enrichedGaps.reduce((sum, g) => sum + Math.max(0, g.deficit), 0)
    const totalSurplus = enrichedGaps.reduce((sum, g) => sum + Math.abs(Math.min(0, g.deficit)), 0)
    const totalHsa = enrichedGaps.reduce((sum, g) => sum + g.hsa_needed, 0)

    let status: 'deficit' | 'balanced' | 'surplus' = 'balanced'
    if (totalDeficit > 0.1) status = 'deficit'
    else if (totalSurplus > 0.1) status = 'surplus'

    return {
      totalRequired,
      totalAllocated,
      totalDeficit,
      totalSurplus,
      totalHsa,
      status,
    }
  }, [enrichedGaps])

  // Handle create placeholder click
  const handleCreatePlaceholder = useCallback((gapItem: TRMDGapItem) => {
    setSelectedGapItem(gapItem)
    setPlaceholderDialogOpen(true)
  }, [])

  // Column definitions
  const columnDefs = useMemo<ColumnDef<TRMDGapItem, unknown>[]>(
    () => [
      {
        id: 'subject_name',
        accessorKey: 'subject_name',
        header: 'Subject',
        size: 150,
        minSize: 150,
        meta: { pinned: 'left' as const },
      },
      {
        id: 'cycle_name',
        accessorKey: 'cycle_name',
        header: 'Cycle',
        size: 120,
      },
      {
        id: 'required_fte',
        accessorKey: 'required_fte',
        header: 'Besoins (FTE)',
        size: 120,
        cell: ({ getValue }: CellContext<TRMDGapItem, unknown>) => {
          const value = getValue() as number | undefined
          return (
            <span className="block text-right tabular-nums">{value?.toFixed(2) || '0.00'}</span>
          )
        },
      },
      {
        id: 'aefe_allocated',
        accessorKey: 'aefe_allocated',
        header: 'AEFE',
        size: 90,
        cell: ({ getValue }: CellContext<TRMDGapItem, unknown>) => {
          const value = getValue() as number | undefined
          return (
            <span className="block text-right tabular-nums">{value?.toFixed(2) || '0.00'}</span>
          )
        },
      },
      {
        id: 'local_allocated',
        accessorKey: 'local_allocated',
        header: 'Local',
        size: 90,
        cell: ({ getValue }: CellContext<TRMDGapItem, unknown>) => {
          const value = getValue() as number | undefined
          return (
            <span className="block text-right tabular-nums">{value?.toFixed(2) || '0.00'}</span>
          )
        },
      },
      {
        id: 'total_allocated',
        accessorKey: 'total_allocated',
        header: 'Moyens (FTE)',
        size: 120,
        cell: ({ getValue }: CellContext<TRMDGapItem, unknown>) => {
          const value = getValue() as number | undefined
          return (
            <span className="block text-right tabular-nums font-medium">
              {value?.toFixed(2) || '0.00'}
            </span>
          )
        },
      },
      {
        id: 'deficit',
        accessorKey: 'deficit',
        header: 'Gap',
        size: 100,
        cell: ({ getValue }: CellContext<TRMDGapItem, unknown>) => {
          const deficit = getValue() as number
          if (deficit > 0) {
            return (
              <span className="block text-right tabular-nums text-red-600 font-medium">
                -{deficit.toFixed(2)}
              </span>
            )
          } else if (deficit < 0) {
            return (
              <span className="block text-right tabular-nums text-green-600 font-medium">
                +{Math.abs(deficit).toFixed(2)}
              </span>
            )
          }
          return <span className="block text-right tabular-nums text-muted-foreground">0.00</span>
        },
      },
      {
        id: 'hsa_needed',
        accessorKey: 'hsa_needed',
        header: 'HSA Needed',
        size: 110,
        cell: ({ getValue }: CellContext<TRMDGapItem, unknown>) => {
          const val = getValue() as number
          return (
            <span className="block text-right tabular-nums">
              {val > 0 ? val.toFixed(1) + 'h' : '-'}
            </span>
          )
        },
      },
      {
        id: 'action',
        header: 'Action',
        size: 150,
        meta: { pinned: 'right' as const },
        cell: ({ row }: CellContext<TRMDGapItem, unknown>) => {
          const gapItem = row.original
          if (!gapItem || gapItem.deficit <= 0) {
            return null
          }
          return (
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleCreatePlaceholder(gapItem)}
              className="h-7 px-2 gap-1"
            >
              <UserPlus className="h-3.5 w-3.5" />
              Fill Deficit
            </Button>
          )
        },
      },
    ],
    [handleCreatePlaceholder]
  )

  // Check if no version selected
  if (!selectedVersionId) {
    return (
      <PageContainer
        title="Gap Analysis (TRMD)"
        description="Compare teacher requirements (Besoins) vs available staff (Moyens)"
      >
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-center gap-4 py-6">
            <AlertCircle className="h-8 w-8 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800">No Version Selected</p>
              <p className="text-sm text-amber-700">
                Please select a version from the header to view gap analysis.
              </p>
            </div>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  // Loading or no data state
  if (isLoading) {
    return (
      <PageContainer
        title="Gap Analysis (TRMD)"
        description="Compare teacher requirements (Besoins) vs available staff (Moyens)"
      >
        <Card>
          <CardContent className="flex items-center justify-center py-12">
            <RefreshCw className="h-8 w-8 animate-spin text-muted-foreground" />
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  // No data available
  if (!trmdData || enrichedGaps.length === 0) {
    return (
      <PageContainer
        title="Gap Analysis (TRMD)"
        description="Compare teacher requirements (Besoins) vs available staff (Moyens)"
      >
        <Card className="border-dashed border-2 border-border-medium bg-subtle/50">
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="w-16 h-16 rounded-full bg-gold-100 flex items-center justify-center mb-4">
              <Scale className="h-8 w-8 text-gold-600" />
            </div>
            <h3 className="text-lg font-semibold text-text-primary mb-2">No Gap Analysis Data</h3>
            <p className="text-sm text-text-secondary text-center max-w-md mb-4">
              The TRMD gap analysis requires DHG calculations to be completed first. Please ensure
              subject hours and class structure are configured.
            </p>
            <Button variant="outline" onClick={() => refetch()}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title="Gap Analysis (TRMD)"
      description="Compare teacher requirements (Besoins) vs available staff (Moyens)"
      actions={
        <Button variant="outline" size="sm" onClick={() => refetch()}>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Besoins (Required)</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-gold-600" />
                <span>{summary.totalRequired.toFixed(1)} FTE</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">From DHG calculation</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Moyens (Available)</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-sage-600" />
                <span>{summary.totalAllocated.toFixed(1)} FTE</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">AEFE + Local teachers</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Déficit / Surplus</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                {summary.status === 'deficit' ? (
                  <>
                    <TrendingDown className="h-5 w-5 text-terracotta-600" />
                    <span className="text-terracotta-600">
                      -{summary.totalDeficit.toFixed(1)} FTE
                    </span>
                  </>
                ) : summary.status === 'surplus' ? (
                  <>
                    <TrendingUp className="h-5 w-5 text-green-600" />
                    <span className="text-green-600">+{summary.totalSurplus.toFixed(1)} FTE</span>
                  </>
                ) : (
                  <>
                    <MinusCircle className="h-5 w-5 text-blue-600" />
                    <span className="text-blue-600">Balanced</span>
                  </>
                )}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {summary.status === 'deficit'
                  ? 'Positions to fill'
                  : summary.status === 'surplus'
                    ? 'Extra capacity'
                    : 'Staff matches needs'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Status</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Scale className="h-5 w-5 text-text-secondary" />
                <Badge
                  variant={
                    summary.status === 'deficit'
                      ? 'destructive'
                      : summary.status === 'surplus'
                        ? 'default'
                        : 'secondary'
                  }
                  className="text-sm"
                >
                  {summary.status === 'deficit'
                    ? 'DEFICIT'
                    : summary.status === 'surplus'
                      ? 'SURPLUS'
                      : 'BALANCED'}
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {summary.totalHsa > 0 && (
                <p className="text-xs text-amber-600">HSA needed: {summary.totalHsa.toFixed(0)}h</p>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Gap Analysis Grid */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-lg">TRMD by Subject</CardTitle>
            <CardDescription>
              Gap analysis per subject. Click &quot;Fill Deficit&quot; to create placeholder
              positions.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <TanStackDataTable<TRMDGapItem>
              columnDefs={columnDefs}
              rowData={enrichedGaps}
              getRowId={(data) => `${data.subject_id}-${data.cycle_id}`}
              tableLabel="TRMD Gap Analysis Grid"
              enableSorting={true}
              compact={true}
              height={400}
              moduleColor="wine"
              nativeColumns={true}
            />
          </CardContent>
        </Card>

        {/* Formula Reference */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">TRMD Calculation Reference</CardTitle>
            <CardDescription>
              Tableau de Répartition des Moyens par Discipline (Gap Analysis)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
              <div className="p-4 bg-sage-50 rounded-lg">
                <p className="font-semibold text-sage-800 mb-1">Besoins (Requirements)</p>
                <p className="text-sage-600">
                  Calculated from DHG: Total Hours ÷ Standard Teaching Hours (18h secondary, 24h
                  primary)
                </p>
              </div>
              <div className="p-4 bg-twilight-50 rounded-lg">
                <p className="font-semibold text-text-secondary mb-1">Moyens (Available)</p>
                <p className="text-text-secondary">
                  Sum of employee FTE by subject (AEFE Detached + AEFE Funded + Local teachers)
                </p>
              </div>
              <div className="p-4 bg-terracotta-50 rounded-lg">
                <p className="font-semibold text-terracotta-800 mb-1">Déficit / Surplus</p>
                <p className="text-terracotta-600">
                  Besoins - Moyens = Gap (positive = deficit, negative = surplus)
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Create Placeholder Dialog */}
      <CreatePlaceholderDialog
        open={placeholderDialogOpen}
        onOpenChange={setPlaceholderDialogOpen}
        gapItem={selectedGapItem}
        versionId={selectedVersionId}
      />
    </PageContainer>
  )
}
