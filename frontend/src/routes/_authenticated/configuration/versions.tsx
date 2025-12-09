import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ColDef } from 'ag-grid-community'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { FormDialog } from '@/components/FormDialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Plus, Edit, Trash2, Copy, Send, CheckCircle } from 'lucide-react'
import {
  useBudgetVersions,
  useCreateBudgetVersion,
  useUpdateBudgetVersion,
  useDeleteBudgetVersion,
  useSubmitBudgetVersion,
  useApproveBudgetVersion,
  useCloneBudgetVersion,
} from '@/hooks/api/useBudgetVersions'
import {
  budgetVersionSchema,
  cloneBudgetVersionSchema,
  type BudgetVersionFormData,
  type CloneBudgetVersionFormData,
} from '@/schemas/configuration'
import { BudgetVersion } from '@/types/api'

export const Route = createFileRoute('/_authenticated/configuration/versions')({
  beforeLoad: requireAuth,
  component: BudgetVersionsPage,
})

function BudgetVersionsPage() {
  const { data, isLoading, error } = useBudgetVersions()
  const [rowData, setRowData] = useState<BudgetVersion[]>([])
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false)
  const [selectedVersion, setSelectedVersion] = useState<BudgetVersion | null>(null)

  const createMutation = useCreateBudgetVersion()
  const updateMutation = useUpdateBudgetVersion()
  const deleteMutation = useDeleteBudgetVersion()
  const submitMutation = useSubmitBudgetVersion()
  const approveMutation = useApproveBudgetVersion()
  const cloneMutation = useCloneBudgetVersion()

  const createForm = useForm<BudgetVersionFormData>({
    resolver: zodResolver(budgetVersionSchema),
    defaultValues: {
      name: '',
      fiscal_year: new Date().getFullYear(),
      academic_year: `${new Date().getFullYear()}-${new Date().getFullYear() + 1}`,
      notes: '',
    },
  })

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
    // eslint-disable-next-line react-hooks/exhaustive-deps -- editForm.reset is stable from react-hook-form
  }, [selectedVersion, editDialogOpen])

  const handleCreate = async (formData: BudgetVersionFormData) => {
    try {
      await createMutation.mutateAsync(formData)
      setCreateDialogOpen(false)
      createForm.reset()
    } catch {
      // Error toast is handled by the mutation
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
      // Error toast is handled by the mutation
    }
  }

  const handleClone = async (formData: CloneBudgetVersionFormData) => {
    if (!selectedVersion) return
    try {
      await cloneMutation.mutateAsync({
        id: selectedVersion.id,
        name: formData.name,
      })
      setCloneDialogOpen(false)
      setSelectedVersion(null)
      cloneForm.reset()
    } catch {
      // Error toast is handled by the mutation
    }
  }

  const handleDelete = useCallback(
    async (id: string, name: string) => {
      if (window.confirm(`Are you sure you want to delete "${name}"?`)) {
        try {
          await deleteMutation.mutateAsync(id)
        } catch {
          // Error toast is handled by the mutation
        }
      }
    },
    [deleteMutation]
  )

  const handleSubmit = useCallback(
    async (id: string) => {
      try {
        await submitMutation.mutateAsync(id)
      } catch {
        // Error toast is handled by the mutation
      }
    },
    [submitMutation]
  )

  const handleApprove = useCallback(
    async (id: string) => {
      if (window.confirm('Are you sure you want to approve this budget version?')) {
        try {
          await approveMutation.mutateAsync(id)
        } catch {
          // Error toast is handled by the mutation
        }
      }
    },
    [approveMutation]
  )

  const columnDefs: ColDef<BudgetVersion>[] = useMemo(
    () => [
      {
        field: 'name',
        headerName: 'Name',
        flex: 2,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'fiscal_year',
        headerName: 'Fiscal Year',
        flex: 1,
        filter: 'agNumberColumnFilter',
      },
      {
        field: 'academic_year',
        headerName: 'Academic Year',
        flex: 1,
        filter: 'agTextColumnFilter',
      },
      {
        field: 'status',
        headerName: 'Status',
        flex: 1,
        cellRenderer: (params: { value: string }) => {
          const statusColors: Record<string, string> = {
            working: 'bg-subtle text-text-primary',
            submitted: 'bg-info-100 text-info-700',
            approved: 'bg-success-100 text-success-700',
            forecast: 'bg-info-100 text-info-700',
            superseded: 'bg-twilight-100 text-text-secondary',
          }
          return (
            <span
              className={`px-2 py-1 rounded text-xs font-medium ${statusColors[params.value] || ''}`}
            >
              {params.value.toUpperCase()}
            </span>
          )
        },
      },
      {
        headerName: 'Actions',
        flex: 2,
        cellRenderer: (params: { data: BudgetVersion }) => {
          const version = params.data
          return (
            <div className="flex gap-2 py-2">
              <Button
                data-testid="edit-button"
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedVersion(version)
                  setEditDialogOpen(true)
                }}
                disabled={version.status !== 'working'}
              >
                <Edit className="h-3 w-3" />
              </Button>
              <Button
                data-testid="copy-button"
                size="sm"
                variant="outline"
                onClick={() => {
                  setSelectedVersion(version)
                  setCloneDialogOpen(true)
                }}
              >
                <Copy className="h-3 w-3" />
              </Button>
              {version.status === 'working' && (
                <Button
                  data-testid="submit-button"
                  size="sm"
                  variant="default"
                  onClick={() => handleSubmit(version.id)}
                  disabled={submitMutation.isPending}
                >
                  <Send className="h-3 w-3" />
                </Button>
              )}
              {version.status === 'submitted' && (
                <Button
                  data-testid="approve-button"
                  size="sm"
                  variant="default"
                  onClick={() => handleApprove(version.id)}
                  disabled={approveMutation.isPending}
                >
                  <CheckCircle className="h-3 w-3" />
                </Button>
              )}
              <Button
                data-testid="delete-button"
                size="sm"
                variant="destructive"
                onClick={() => handleDelete(version.id, version.name)}
                disabled={version.status !== 'working' || deleteMutation.isPending}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          )
        },
      },
    ],
    [
      deleteMutation.isPending,
      submitMutation.isPending,
      approveMutation.isPending,
      handleApprove,
      handleDelete,
      handleSubmit,
    ]
  )

  return (
    <>
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
        <DataTableLazy
          rowData={rowData}
          columnDefs={columnDefs}
          loading={isLoading}
          error={error}
          pagination={true}
          paginationPageSize={50}
        />
      </PageContainer>

      {/* Create Dialog */}
      <FormDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        title="Create Budget Version"
        description="Create a new budget version"
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
            <Label htmlFor="fiscal_year">Fiscal Year</Label>
            <Input
              id="fiscal_year"
              type="number"
              {...createForm.register('fiscal_year', { valueAsNumber: true })}
            />
            {createForm.formState.errors.fiscal_year && (
              <p className="text-sm text-error-600 mt-1">
                {createForm.formState.errors.fiscal_year.message}
              </p>
            )}
          </div>
          <div>
            <Label htmlFor="academic_year">Academic Year</Label>
            <Input
              id="academic_year"
              {...createForm.register('academic_year')}
              placeholder="2024-2025"
            />
            {createForm.formState.errors.academic_year && (
              <p className="text-sm text-error-600 mt-1">
                {createForm.formState.errors.academic_year.message}
              </p>
            )}
          </div>
          <div>
            <Label htmlFor="notes">Notes (Optional)</Label>
            <Input id="notes" {...createForm.register('notes')} />
          </div>
        </div>
      </FormDialog>

      {/* Edit Dialog */}
      <FormDialog
        open={editDialogOpen}
        onOpenChange={setEditDialogOpen}
        title="Edit Budget Version"
        description="Update budget version details"
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
            <Input id="edit-notes" {...editForm.register('notes')} />
          </div>
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
        </div>
      </FormDialog>
    </>
  )
}
