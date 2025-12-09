/**
 * Workforce - AEFE Position Management
 *
 * Manage AEFE positions allocation:
 * - 24 Detached positions (school pays PRRD ~41,863 EUR)
 * - 4 Funded positions (zero cost to school)
 * - Position-to-employee assignment
 * - PRRD rate and EUR/SAR exchange rate configuration
 *
 * @module /workforce/aefe-positions
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
  BadgeEuro,
  UserCheck,
  UserX,
  Euro,
  AlertCircle,
  Settings2,
  UserPlus,
  Sparkles,
} from 'lucide-react'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import {
  useAEFEPositions,
  useAEFESummary,
  useEmployees,
  useUpdateAEFEPosition,
  useAssignEmployeeToAEFE,
  useInitializeAEFEPositions,
} from '@/hooks/api/useWorkforce'
import type { AEFEPosition, AEFEPositionUpdate } from '@/types/workforce'
import { AEFE_POSITION_TYPE_LABELS, EMPLOYEE_CATEGORY_LABELS } from '@/types/workforce'
import type { ColDef, ICellRendererParams, ValueFormatterParams } from 'ag-grid-community'
import { DataTableLazy as DataTable } from '@/components/DataTableLazy'

export const Route = createFileRoute('/_authenticated/workforce/aefe-positions')({
  beforeLoad: requireAuth,
  component: AEFEPositionsPage,
})

// ============================================================================
// Initialize AEFE Positions Dialog
// ============================================================================

interface InitializeDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  budgetVersionId: string
}

function InitializeDialog({ open, onOpenChange, budgetVersionId }: InitializeDialogProps) {
  const [academicYear, setAcademicYear] = useState('2025-2026')
  const [prrdAmountEur, setPrrdAmountEur] = useState(41863)
  const [exchangeRate, setExchangeRate] = useState(4.05)

  const initializeMutation = useInitializeAEFEPositions()

  const handleInitialize = async () => {
    try {
      await initializeMutation.mutateAsync({
        budget_version_id: budgetVersionId,
        academic_year: academicYear,
        prrd_amount_eur: prrdAmountEur,
        exchange_rate_eur_sar: exchangeRate,
      })
      onOpenChange(false)
    } catch {
      // Error handled by mutation
    }
  }

  const totalPrrdEur = prrdAmountEur * 24
  const totalPrrdSar = totalPrrdEur * exchangeRate

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-gold-600" />
            Initialize AEFE Positions
          </DialogTitle>
          <DialogDescription>
            Create 28 AEFE positions (24 Detached + 4 Funded) for this budget version.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div>
            <Label htmlFor="academic_year">Academic Year</Label>
            <Input
              id="academic_year"
              value={academicYear}
              onChange={(e) => setAcademicYear(e.target.value)}
              placeholder="2025-2026"
            />
          </div>

          <div>
            <Label htmlFor="prrd_amount">PRRD Amount (EUR per position)</Label>
            <Input
              id="prrd_amount"
              type="number"
              value={prrdAmountEur}
              onChange={(e) => setPrrdAmountEur(parseFloat(e.target.value) || 0)}
            />
            <p className="text-xs text-muted-foreground mt-1">
              Standard AEFE rate: ~41,863 EUR/year
            </p>
          </div>

          <div>
            <Label htmlFor="exchange_rate">EUR/SAR Exchange Rate</Label>
            <Input
              id="exchange_rate"
              type="number"
              step="0.01"
              value={exchangeRate}
              onChange={(e) => setExchangeRate(parseFloat(e.target.value) || 0)}
            />
          </div>

          <div className="rounded-lg bg-slate-50 p-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total PRRD (24 positions)</span>
              <span className="font-medium">{totalPrrdEur.toLocaleString()} EUR</span>
            </div>
            <div className="flex justify-between mt-1">
              <span className="text-muted-foreground">In SAR</span>
              <span className="font-medium">{totalPrrdSar.toLocaleString()} SAR</span>
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              * 4 Funded positions have zero cost to school
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleInitialize} disabled={initializeMutation.isPending}>
            {initializeMutation.isPending ? 'Creating...' : 'Create 28 Positions'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Assign Employee Dialog
// ============================================================================

interface AssignDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  position: AEFEPosition | null
  budgetVersionId: string
}

function AssignDialog({ open, onOpenChange, position, budgetVersionId }: AssignDialogProps) {
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string>('')

  const { data: employeesData } = useEmployees(budgetVersionId)
  const assignMutation = useAssignEmployeeToAEFE()

  // Filter to AEFE employees only
  const aefeEmployees = useMemo(() => {
    if (!employeesData) return []
    return employeesData.employees.filter(
      (e) => e.category === 'AEFE_DETACHED' || e.category === 'AEFE_FUNDED'
    )
  }, [employeesData])

  const handleAssign = async () => {
    if (!position || !selectedEmployeeId) return

    try {
      await assignMutation.mutateAsync({
        positionId: position.id,
        employeeId: selectedEmployeeId,
        budgetVersionId,
      })
      onOpenChange(false)
      setSelectedEmployeeId('')
    } catch {
      // Error handled by mutation
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <UserPlus className="h-5 w-5 text-sage-600" />
            Assign Employee to Position
          </DialogTitle>
          <DialogDescription>
            {position && (
              <>
                Position #{position.position_number} (
                {AEFE_POSITION_TYPE_LABELS[position.position_type]})
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          <Label htmlFor="employee">Select Employee</Label>
          <Select value={selectedEmployeeId} onValueChange={setSelectedEmployeeId}>
            <SelectTrigger className="mt-2">
              <SelectValue placeholder="Choose an AEFE employee..." />
            </SelectTrigger>
            <SelectContent>
              {aefeEmployees.length === 0 ? (
                <div className="p-2 text-sm text-muted-foreground text-center">
                  No AEFE employees found
                </div>
              ) : (
                aefeEmployees.map((employee) => (
                  <SelectItem key={employee.id} value={employee.id}>
                    {employee.employee_code} - {employee.full_name} (
                    {EMPLOYEE_CATEGORY_LABELS[employee.category]})
                  </SelectItem>
                ))
              )}
            </SelectContent>
          </Select>

          {aefeEmployees.length === 0 && (
            <p className="text-xs text-amber-600 mt-2">
              Create AEFE employees first in the Employees page before assigning to positions.
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleAssign} disabled={assignMutation.isPending || !selectedEmployeeId}>
            {assignMutation.isPending ? 'Assigning...' : 'Assign'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Edit Position Dialog
// ============================================================================

interface EditPositionDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  position: AEFEPosition | null
  budgetVersionId: string
}

function EditPositionDialog({
  open,
  onOpenChange,
  position,
  budgetVersionId,
}: EditPositionDialogProps) {
  const [prrdAmountEur, setPrrdAmountEur] = useState(position?.prrd_amount_eur || 41863)
  const [exchangeRate, setExchangeRate] = useState(position?.exchange_rate_eur_sar || 4.05)
  const [notes, setNotes] = useState(position?.notes || '')

  const updateMutation = useUpdateAEFEPosition()

  // Update state when position changes
  useMemo(() => {
    if (position) {
      setPrrdAmountEur(position.prrd_amount_eur)
      setExchangeRate(position.exchange_rate_eur_sar)
      setNotes(position.notes || '')
    }
  }, [position])

  const handleSave = async () => {
    if (!position) return

    const data: AEFEPositionUpdate = {
      prrd_amount_eur: prrdAmountEur,
      exchange_rate_eur_sar: exchangeRate,
      notes: notes || null,
    }

    try {
      await updateMutation.mutateAsync({
        positionId: position.id,
        data,
        budgetVersionId,
      })
      onOpenChange(false)
    } catch {
      // Error handled by mutation
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Settings2 className="h-5 w-5 text-text-secondary" />
            Edit Position Settings
          </DialogTitle>
          <DialogDescription>
            {position && (
              <>
                Position #{position.position_number} -{' '}
                {AEFE_POSITION_TYPE_LABELS[position.position_type]}
              </>
            )}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {position?.position_type === 'DETACHED' ? (
            <>
              <div>
                <Label htmlFor="edit_prrd">PRRD Amount (EUR)</Label>
                <Input
                  id="edit_prrd"
                  type="number"
                  value={prrdAmountEur}
                  onChange={(e) => setPrrdAmountEur(parseFloat(e.target.value) || 0)}
                />
              </div>

              <div>
                <Label htmlFor="edit_rate">EUR/SAR Exchange Rate</Label>
                <Input
                  id="edit_rate"
                  type="number"
                  step="0.01"
                  value={exchangeRate}
                  onChange={(e) => setExchangeRate(parseFloat(e.target.value) || 0)}
                />
              </div>

              <div className="rounded-lg bg-slate-50 p-3 text-sm">
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Cost in SAR</span>
                  <span className="font-medium">
                    {(prrdAmountEur * exchangeRate).toLocaleString()} SAR
                  </span>
                </div>
              </div>
            </>
          ) : (
            <div className="rounded-lg bg-green-50 p-3 text-sm text-green-800">
              <p className="font-medium">Funded Position</p>
              <p className="text-xs mt-1">
                This position is fully funded by AEFE with zero cost to the school.
              </p>
            </div>
          )}

          <div>
            <Label htmlFor="edit_notes">Notes</Label>
            <Input
              id="edit_notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes..."
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSave} disabled={updateMutation.isPending}>
            {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Main Page Component
// ============================================================================

function AEFEPositionsPage() {
  const { selectedVersionId } = useBudgetVersion()

  // Dialog states
  const [initDialogOpen, setInitDialogOpen] = useState(false)
  const [assignDialogOpen, setAssignDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedPosition, setSelectedPosition] = useState<AEFEPosition | null>(null)

  // Queries
  const { data: summaryData, isLoading } = useAEFESummary(selectedVersionId)
  const { data: positionsData } = useAEFEPositions(selectedVersionId)

  // Summary stats
  const stats = useMemo(() => {
    if (!summaryData) {
      return {
        total: 0,
        filled: 0,
        vacant: 0,
        detached: 0,
        funded: 0,
        totalPrrdEur: 0,
        totalPrrdSar: 0,
      }
    }
    return {
      total: summaryData.total_positions,
      filled: summaryData.filled_positions,
      vacant: summaryData.vacant_positions,
      detached: summaryData.detached_positions,
      funded: summaryData.funded_positions,
      totalPrrdEur: summaryData.total_prrd_eur,
      totalPrrdSar: summaryData.total_prrd_sar,
    }
  }, [summaryData])

  // Check if positions need to be initialized
  const needsInitialization = !isLoading && stats.total === 0

  // Handle assign button click
  const handleAssignClick = useCallback((position: AEFEPosition) => {
    setSelectedPosition(position)
    setAssignDialogOpen(true)
  }, [])

  // Handle edit button click
  const handleEditClick = useCallback((position: AEFEPosition) => {
    setSelectedPosition(position)
    setEditDialogOpen(true)
  }, [])

  // AG Grid Column Definitions
  const columnDefs = useMemo<ColDef<AEFEPosition>[]>(
    () => [
      {
        headerName: '#',
        field: 'position_number',
        width: 70,
        pinned: 'left',
        cellRenderer: (params: ICellRendererParams<AEFEPosition>) => (
          <span className="font-mono font-medium">{params.value}</span>
        ),
      },
      {
        headerName: 'Type',
        field: 'position_type',
        width: 150,
        cellRenderer: (params: ICellRendererParams<AEFEPosition>) => {
          const type = params.value as 'DETACHED' | 'FUNDED'
          return (
            <Badge variant={type === 'DETACHED' ? 'default' : 'secondary'}>
              {AEFE_POSITION_TYPE_LABELS[type]}
            </Badge>
          )
        },
      },
      {
        headerName: 'Status',
        field: 'is_filled',
        width: 110,
        cellRenderer: (params: ICellRendererParams<AEFEPosition>) => {
          const isFilled = params.value as boolean
          return (
            <Badge variant={isFilled ? 'outline' : 'destructive'} className="gap-1">
              {isFilled ? (
                <>
                  <UserCheck className="h-3 w-3" /> Filled
                </>
              ) : (
                <>
                  <UserX className="h-3 w-3" /> Vacant
                </>
              )}
            </Badge>
          )
        },
      },
      {
        headerName: 'Assigned Employee',
        field: 'employee_name',
        flex: 1,
        minWidth: 200,
        cellRenderer: (params: ICellRendererParams<AEFEPosition>) => {
          const name = params.value as string | null
          if (!name) {
            return <span className="text-muted-foreground italic">Not assigned</span>
          }
          return <span className="font-medium">{name}</span>
        },
      },
      {
        headerName: 'PRRD (EUR)',
        field: 'prrd_amount_eur',
        width: 130,
        type: 'numericColumn',
        valueFormatter: (params: ValueFormatterParams) => {
          const pos = params.data as AEFEPosition
          if (pos.position_type === 'FUNDED') return '-'
          return params.value ? params.value.toLocaleString() : '0'
        },
        cellStyle: { textAlign: 'right' },
      },
      {
        headerName: 'PRRD (SAR)',
        field: 'prrd_amount_sar',
        width: 140,
        type: 'numericColumn',
        valueFormatter: (params: ValueFormatterParams) => {
          const pos = params.data as AEFEPosition
          if (pos.position_type === 'FUNDED') return '-'
          return params.value ? params.value.toLocaleString() : '0'
        },
        cellStyle: { textAlign: 'right' },
      },
      {
        headerName: 'Rate',
        field: 'exchange_rate_eur_sar',
        width: 80,
        type: 'numericColumn',
        valueFormatter: (params: ValueFormatterParams) => {
          const pos = params.data as AEFEPosition
          if (pos.position_type === 'FUNDED') return '-'
          return params.value?.toFixed(2) || '-'
        },
        cellStyle: { textAlign: 'right' },
      },
      {
        headerName: 'Actions',
        width: 160,
        pinned: 'right',
        cellRenderer: (params: ICellRendererParams<AEFEPosition>) => {
          const position = params.data
          if (!position) return null
          return (
            <div className="flex items-center gap-1">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleAssignClick(position)}
                className="h-7 px-2"
              >
                <UserPlus className="h-3.5 w-3.5 mr-1" />
                Assign
              </Button>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleEditClick(position)}
                className="h-7 px-2"
              >
                <Settings2 className="h-3.5 w-3.5" />
              </Button>
            </div>
          )
        },
      },
    ],
    [handleAssignClick, handleEditClick]
  )

  // Row data (useAEFEPositions returns AEFEPosition[] directly)
  const rowData = useMemo(() => {
    if (!positionsData) return []
    return positionsData
  }, [positionsData])

  // Check if no version selected
  if (!selectedVersionId) {
    return (
      <PageContainer
        title="AEFE Position Management"
        description="Manage 28 AEFE positions (24 Detached + 4 Funded)"
      >
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-center gap-4 py-6">
            <AlertCircle className="h-8 w-8 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800">No Budget Version Selected</p>
              <p className="text-sm text-amber-700">
                Please select a budget version from the header to manage AEFE positions.
              </p>
            </div>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title="AEFE Position Management"
      description="Manage 28 AEFE positions (24 Detached + 4 Funded)"
      actions={
        needsInitialization ? (
          <Button onClick={() => setInitDialogOpen(true)}>
            <Sparkles className="h-4 w-4 mr-2" />
            Initialize Positions
          </Button>
        ) : undefined
      }
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Positions</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <BadgeEuro className="h-5 w-5 text-gold-600" />
                <span>{stats.total}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {stats.detached} Detached + {stats.funded} Funded
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Filled Positions</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <UserCheck className="h-5 w-5 text-sage-600" />
                <span>
                  {stats.filled} / {stats.total}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="w-full bg-slate-100 rounded-full h-2">
                <div
                  className="bg-sage-500 h-2 rounded-full transition-all"
                  style={{
                    width: stats.total > 0 ? `${(stats.filled / stats.total) * 100}%` : '0%',
                  }}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Vacant Positions</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <UserX className="h-5 w-5 text-terracotta-600" />
                <span>{stats.vacant}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Available for assignment</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total PRRD Cost</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Euro className="h-5 w-5 text-text-secondary" />
                <span>{stats.totalPrrdEur.toLocaleString()}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                {stats.totalPrrdSar.toLocaleString()} SAR • Detached only
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Initialization Prompt */}
        {needsInitialization && (
          <Card className="border-dashed border-2 border-gold-300 bg-gold-50/50">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <div className="w-16 h-16 rounded-full bg-gold-100 flex items-center justify-center mb-4">
                <Sparkles className="h-8 w-8 text-gold-600" />
              </div>
              <h3 className="text-lg font-semibold text-text-primary mb-2">
                Initialize AEFE Positions
              </h3>
              <p className="text-sm text-text-secondary text-center max-w-md mb-4">
                Create the 28 AEFE positions for this budget version:
              </p>
              <ul className="text-sm text-text-secondary space-y-1 mb-6">
                <li>• 24 Detached positions - School pays PRRD (~41,863 EUR/year)</li>
                <li>• 4 Funded positions - Fully funded by AEFE (zero cost)</li>
              </ul>
              <Button onClick={() => setInitDialogOpen(true)} size="lg">
                <Sparkles className="h-4 w-4 mr-2" />
                Initialize 28 Positions
              </Button>
            </CardContent>
          </Card>
        )}

        {/* Positions Grid */}
        {!needsInitialization && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-lg">Position Assignments</CardTitle>
              <CardDescription>
                Assign AEFE employees to positions and configure PRRD rates
              </CardDescription>
            </CardHeader>
            <CardContent>
              <DataTable
                columnDefs={columnDefs}
                rowData={rowData}
                rowHeight={40}
                headerHeight={44}
                domLayout="autoHeight"
                defaultColDef={{
                  sortable: true,
                  resizable: true,
                }}
                getRowId={(params) => params.data.id}
              />
            </CardContent>
          </Card>
        )}
      </div>

      {/* Dialogs */}
      <InitializeDialog
        open={initDialogOpen}
        onOpenChange={setInitDialogOpen}
        budgetVersionId={selectedVersionId}
      />
      <AssignDialog
        open={assignDialogOpen}
        onOpenChange={setAssignDialogOpen}
        position={selectedPosition}
        budgetVersionId={selectedVersionId}
      />
      <EditPositionDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        position={selectedPosition}
        budgetVersionId={selectedVersionId}
      />
    </PageContainer>
  )
}
