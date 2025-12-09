/**
 * Workforce - Employee Registry
 *
 * Central employee management page with:
 * - AG Grid listing all employees (Base 100 + Planned)
 * - Filterable by category, cycle, status
 * - Add/Edit employee functionality
 * - "Base 100" vs "Planned" badges
 *
 * @module /workforce/employees
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useMemo, useCallback } from 'react'
import { ColDef, ValueFormatterParams, ICellRendererParams } from 'ag-grid-community'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  UserPlus,
  Users,
  Filter,
  RefreshCw,
  GraduationCap,
  Briefcase,
  AlertCircle,
  BadgeEuro,
} from 'lucide-react'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import { useEmployees, useCreateEmployee, useWorkforceSummary } from '@/hooks/api/useWorkforce'
import type {
  Employee,
  EmployeeCategory,
  EmployeeNationality,
  ContractType,
  EmployeeFilters,
} from '@/types/workforce'
import {
  EMPLOYEE_CATEGORY_LABELS,
  NATIONALITY_LABELS,
  CONTRACT_TYPE_LABELS,
} from '@/types/workforce'
import { format } from 'date-fns'
import { toastMessages } from '@/lib/toast-messages'

export const Route = createFileRoute('/_authenticated/workforce/employees')({
  beforeLoad: requireAuth,
  component: EmployeesPage,
})

// ============================================================================
// Employee Badge Component
// ============================================================================

function EmployeeBadge({ isPlaceholder }: { isPlaceholder: boolean }) {
  if (isPlaceholder) {
    return (
      <Badge variant="outline" className="bg-amber-50 text-amber-700 border-amber-300">
        Planned
      </Badge>
    )
  }
  return (
    <Badge variant="outline" className="bg-emerald-50 text-emerald-700 border-emerald-300">
      Base 100
    </Badge>
  )
}

// ============================================================================
// Add Employee Dialog
// ============================================================================

interface AddEmployeeDialogProps {
  budgetVersionId: string
  open: boolean
  onOpenChange: (open: boolean) => void
}

function AddEmployeeDialog({ budgetVersionId, open, onOpenChange }: AddEmployeeDialogProps) {
  const [formData, setFormData] = useState({
    full_name: '',
    nationality: 'EXPATRIATE' as EmployeeNationality,
    category: 'LOCAL_TEACHER' as EmployeeCategory,
    hire_date: format(new Date(), 'yyyy-MM-dd'),
    contract_type: 'PERMANENT' as ContractType,
    fte: 1.0,
    job_title: '',
  })

  const createMutation = useCreateEmployee()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!formData.full_name.trim()) {
      toastMessages.error.custom('Employee name is required')
      return
    }

    try {
      await createMutation.mutateAsync({
        ...formData,
        budget_version_id: budgetVersionId,
        basic_salary_percentage: 0.5,
        is_active: true,
        is_placeholder: false,
      })
      onOpenChange(false)
      setFormData({
        full_name: '',
        nationality: 'EXPATRIATE',
        category: 'LOCAL_TEACHER',
        hire_date: format(new Date(), 'yyyy-MM-dd'),
        contract_type: 'PERMANENT',
        fte: 1.0,
        job_title: '',
      })
    } catch {
      // Error is handled by the mutation
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[500px]">
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>Add New Employee</DialogTitle>
            <DialogDescription>
              Create a new employee record. Employee code will be auto-generated.
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 py-4">
            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="full_name" className="text-right">
                Name
              </Label>
              <Input
                id="full_name"
                value={formData.full_name}
                onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                className="col-span-3"
                placeholder="Full name"
              />
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="category" className="text-right">
                Category
              </Label>
              <Select
                value={formData.category}
                onValueChange={(v) => setFormData({ ...formData, category: v as EmployeeCategory })}
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(EMPLOYEE_CATEGORY_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="nationality" className="text-right">
                Nationality
              </Label>
              <Select
                value={formData.nationality}
                onValueChange={(v) =>
                  setFormData({ ...formData, nationality: v as EmployeeNationality })
                }
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(NATIONALITY_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="hire_date" className="text-right">
                Hire Date
              </Label>
              <Input
                id="hire_date"
                type="date"
                value={formData.hire_date}
                onChange={(e) => setFormData({ ...formData, hire_date: e.target.value })}
                className="col-span-3"
              />
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="contract_type" className="text-right">
                Contract
              </Label>
              <Select
                value={formData.contract_type}
                onValueChange={(v) =>
                  setFormData({ ...formData, contract_type: v as ContractType })
                }
              >
                <SelectTrigger className="col-span-3">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {Object.entries(CONTRACT_TYPE_LABELS).map(([value, label]) => (
                    <SelectItem key={value} value={value}>
                      {label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="fte" className="text-right">
                FTE
              </Label>
              <Input
                id="fte"
                type="number"
                min="0"
                max="1"
                step="0.1"
                value={formData.fte}
                onChange={(e) => setFormData({ ...formData, fte: parseFloat(e.target.value) || 1 })}
                className="col-span-3"
              />
            </div>

            <div className="grid grid-cols-4 items-center gap-4">
              <Label htmlFor="job_title" className="text-right">
                Job Title
              </Label>
              <Input
                id="job_title"
                value={formData.job_title}
                onChange={(e) => setFormData({ ...formData, job_title: e.target.value })}
                className="col-span-3"
                placeholder="e.g., Mathematics Teacher"
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
              Cancel
            </Button>
            <Button type="submit" disabled={createMutation.isPending}>
              {createMutation.isPending ? 'Creating...' : 'Create Employee'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ============================================================================
// Main Page Component
// ============================================================================

function EmployeesPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [addDialogOpen, setAddDialogOpen] = useState(false)
  const [filters, setFilters] = useState<EmployeeFilters>({})

  // Queries
  const {
    data: employeesData,
    isLoading,
    error,
    refetch,
  } = useEmployees(selectedVersionId, filters)

  const { data: summaryData } = useWorkforceSummary(selectedVersionId)

  // Column definitions for AG Grid
  const columnDefs = useMemo<ColDef<Employee>[]>(
    () => [
      {
        field: 'employee_code',
        headerName: 'Code',
        width: 100,
        pinned: 'left',
        sortable: true,
      },
      {
        field: 'full_name',
        headerName: 'Name',
        flex: 2,
        minWidth: 200,
        sortable: true,
        filter: true,
      },
      {
        field: 'is_placeholder',
        headerName: 'Status',
        width: 120,
        cellRenderer: (params: ICellRendererParams<Employee>) => {
          if (params.value === undefined) return null
          return <EmployeeBadge isPlaceholder={params.value} />
        },
      },
      {
        field: 'category',
        headerName: 'Category',
        width: 150,
        valueFormatter: (params: ValueFormatterParams<Employee>) =>
          EMPLOYEE_CATEGORY_LABELS[params.value as EmployeeCategory] || params.value,
        sortable: true,
        filter: true,
      },
      {
        field: 'nationality',
        headerName: 'Nationality',
        width: 120,
        valueFormatter: (params: ValueFormatterParams<Employee>) =>
          NATIONALITY_LABELS[params.value as EmployeeNationality] || params.value,
        sortable: true,
      },
      {
        field: 'hire_date',
        headerName: 'Hire Date',
        width: 120,
        valueFormatter: (params: ValueFormatterParams<Employee>) =>
          params.value ? format(new Date(params.value), 'dd/MM/yyyy') : '-',
        sortable: true,
      },
      {
        field: 'contract_type',
        headerName: 'Contract',
        width: 120,
        valueFormatter: (params: ValueFormatterParams<Employee>) =>
          CONTRACT_TYPE_LABELS[params.value as ContractType] || params.value,
      },
      {
        field: 'fte',
        headerName: 'FTE',
        width: 80,
        type: 'numericColumn',
        valueFormatter: (params: ValueFormatterParams<Employee>) =>
          params.value?.toFixed(2) || '1.00',
      },
      {
        field: 'job_title',
        headerName: 'Position',
        flex: 1,
        minWidth: 150,
      },
      {
        field: 'is_active',
        headerName: 'Active',
        width: 90,
        cellRenderer: (params: ICellRendererParams<Employee>) => {
          if (params.value === undefined) return null
          return params.value ? (
            <Badge className="bg-green-100 text-green-700">Active</Badge>
          ) : (
            <Badge className="bg-gray-100 text-gray-700">Inactive</Badge>
          )
        },
      },
    ],
    []
  )

  // Handle filter changes
  const handleCategoryFilter = useCallback((value: string) => {
    setFilters((prev) => ({
      ...prev,
      category: value === 'all' ? undefined : (value as EmployeeCategory),
    }))
  }, [])

  const handleStatusFilter = useCallback((value: string) => {
    setFilters((prev) => ({
      ...prev,
      is_placeholder: value === 'all' ? undefined : value === 'planned',
    }))
  }, [])

  const handleActiveFilter = useCallback((value: string) => {
    setFilters((prev) => ({
      ...prev,
      is_active: value === 'all' ? undefined : value === 'active',
    }))
  }, [])

  const clearFilters = useCallback(() => {
    setFilters({})
  }, [])

  // Summary stats
  const stats = useMemo(() => {
    if (!summaryData) {
      return {
        total: 0,
        teachers: 0,
        adminSupport: 0,
        aefeFilled: 0,
        base100: 0,
        planned: 0,
        totalFTE: 0,
      }
    }

    const byCategory = summaryData.by_category
    const teacherCount =
      (byCategory['AEFE_DETACHED'] || 0) +
      (byCategory['AEFE_FUNDED'] || 0) +
      (byCategory['LOCAL_TEACHER'] || 0)

    const adminSupportCount = (byCategory['ADMINISTRATIVE'] || 0) + (byCategory['SUPPORT'] || 0)

    return {
      total: summaryData.total_employees,
      teachers: teacherCount,
      adminSupport: adminSupportCount,
      aefeFilled: summaryData.aefe_positions_filled,
      base100: summaryData.base_100_count,
      planned: summaryData.planned_count,
      totalFTE: summaryData.total_fte,
    }
  }, [summaryData])

  // Check if no version selected
  if (!selectedVersionId) {
    return (
      <PageContainer
        title="Employee Registry"
        description="Manage all staff - teachers, administrative, and support personnel"
      >
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-center gap-4 py-6">
            <AlertCircle className="h-8 w-8 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800">No Budget Version Selected</p>
              <p className="text-sm text-amber-700">
                Please select a budget version from the header to view employees.
              </p>
            </div>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title="Employee Registry"
      description="Manage all staff - teachers, administrative, and support personnel"
      actions={
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()}>
            <RefreshCw className="h-4 w-4 mr-2" />
            Refresh
          </Button>
          <Button size="sm" onClick={() => setAddDialogOpen(true)}>
            <UserPlus className="h-4 w-4 mr-2" />
            Add Employee
          </Button>
        </div>
      }
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Employees</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Users className="h-5 w-5 text-gold-600" />
                <span>{stats.total}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2 text-xs">
                <span className="text-emerald-600">{stats.base100} Base 100</span>
                <span className="text-muted-foreground">•</span>
                <span className="text-amber-600">{stats.planned} Planned</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Teachers</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <GraduationCap className="h-5 w-5 text-sage-600" />
                <span>{stats.teachers}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">
                Local + AEFE ({stats.totalFTE.toFixed(1)} FTE)
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Admin & Support</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Briefcase className="h-5 w-5 text-text-secondary" />
                <span>{stats.adminSupport}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Administrative + Support Staff</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>AEFE Positions</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <BadgeEuro className="h-5 w-5 text-terracotta-600" />
                <span>{stats.aefeFilled} / 28</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">Filled / Total Positions</p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardHeader className="py-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Filter className="h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">Filters</span>
              </div>
              {(filters.category ||
                filters.is_placeholder !== undefined ||
                filters.is_active !== undefined) && (
                <Button variant="ghost" size="sm" onClick={clearFilters}>
                  Clear All
                </Button>
              )}
            </div>
          </CardHeader>
          <CardContent className="py-3 pt-0">
            <div className="flex flex-wrap gap-4">
              <div className="w-48">
                <Label className="text-xs text-muted-foreground">Category</Label>
                <Select value={filters.category || 'all'} onValueChange={handleCategoryFilter}>
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="All Categories" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Categories</SelectItem>
                    {Object.entries(EMPLOYEE_CATEGORY_LABELS).map(([value, label]) => (
                      <SelectItem key={value} value={value}>
                        {label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>

              <div className="w-40">
                <Label className="text-xs text-muted-foreground">Status</Label>
                <Select
                  value={
                    filters.is_placeholder === undefined
                      ? 'all'
                      : filters.is_placeholder
                        ? 'planned'
                        : 'base100'
                  }
                  onValueChange={handleStatusFilter}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="All Status" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Status</SelectItem>
                    <SelectItem value="base100">Base 100</SelectItem>
                    <SelectItem value="planned">Planned</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="w-36">
                <Label className="text-xs text-muted-foreground">Active</Label>
                <Select
                  value={
                    filters.is_active === undefined
                      ? 'all'
                      : filters.is_active
                        ? 'active'
                        : 'inactive'
                  }
                  onValueChange={handleActiveFilter}
                >
                  <SelectTrigger className="h-9">
                    <SelectValue placeholder="All" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All</SelectItem>
                    <SelectItem value="active">Active</SelectItem>
                    <SelectItem value="inactive">Inactive</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Employee Grid */}
        <Card>
          <CardHeader className="py-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                Employee List
                {employeesData && (
                  <span className="ml-2 text-sm font-normal text-muted-foreground">
                    ({employeesData.total} employees)
                  </span>
                )}
              </CardTitle>
            </div>
          </CardHeader>
          <CardContent className="p-0">
            <div className="h-[500px] w-full">
              <DataTableLazy<Employee>
                rowData={employeesData?.employees || []}
                columnDefs={columnDefs}
                loading={isLoading}
                error={error}
                defaultColDef={{
                  resizable: true,
                  sortable: true,
                }}
                getRowId={(params) => params.data.id}
                rowSelection="single"
                animateRows={true}
                pagination={true}
                paginationPageSize={20}
              />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Add Employee Dialog */}
      <AddEmployeeDialog
        budgetVersionId={selectedVersionId}
        open={addDialogOpen}
        onOpenChange={setAddDialogOpen}
      />
    </PageContainer>
  )
}
