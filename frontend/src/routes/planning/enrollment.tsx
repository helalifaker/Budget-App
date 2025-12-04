import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useEffect, useMemo, useCallback } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { ColDef, CellValueChangedEvent } from 'ag-grid-community'
import { MainLayout } from '@/components/layout/MainLayout'
import { PageContainer } from '@/components/layout/PageContainer'
import { DataTableLazy } from '@/components/DataTableLazy'
import { FormDialog } from '@/components/FormDialog'
import { BudgetVersionSelector } from '@/components/BudgetVersionSelector'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Plus, Trash2, Calculator, Users, TrendingUp, Globe } from 'lucide-react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  useEnrollments,
  useCreateEnrollment,
  useUpdateEnrollment,
  useDeleteEnrollment,
  useCalculateProjections,
} from '@/hooks/api/useEnrollment'
import { useLevels, useNationalityTypes } from '@/hooks/api/useConfiguration'
import { enrollmentSchema, type EnrollmentFormData } from '@/schemas/planning'
import { Enrollment } from '@/types/api'
import { toastMessages } from '@/lib/toast-messages'

export const Route = createFileRoute('/planning/enrollment')({
  beforeLoad: requireAuth,
  component: EnrollmentPlanningPage,
})

function EnrollmentPlanningPage() {
  const [selectedVersionId, setSelectedVersionId] = useState<string>('')
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [rowData, setRowData] = useState<Enrollment[]>([])

  const {
    data: enrollmentsData,
    isLoading: enrollmentsLoading,
    error: enrollmentsError,
  } = useEnrollments(selectedVersionId)
  const { data: levelsData } = useLevels()
  const { data: nationalityTypesData } = useNationalityTypes()

  const createMutation = useCreateEnrollment()
  const updateMutation = useUpdateEnrollment()
  const deleteMutation = useDeleteEnrollment()
  const calculateMutation = useCalculateProjections()

  const createForm = useForm<EnrollmentFormData>({
    resolver: zodResolver(enrollmentSchema),
    defaultValues: {
      level_id: '',
      nationality_type_id: '',
      student_count: 0,
    },
  })

  useEffect(() => {
    if (enrollmentsData?.items) {
      setRowData(enrollmentsData.items)
    }
  }, [enrollmentsData])

  const getLevelName = useCallback(
    (levelId: string) => {
      return levelsData?.find((l) => l.id === levelId)?.name || levelId
    },
    [levelsData]
  )

  const getNationalityTypeName = useCallback(
    (nationalityTypeId: string) => {
      return (
        nationalityTypesData?.find((n) => n.id === nationalityTypeId)?.name || nationalityTypeId
      )
    },
    [nationalityTypesData]
  )

  // Calculate summary statistics
  const statistics = useMemo(() => {
    const totalStudents = rowData.reduce((sum, enrollment) => sum + enrollment.student_count, 0)

    // Calculate by nationality
    const byNationality = rowData.reduce(
      (acc, enrollment) => {
        const nationalityName = getNationalityTypeName(enrollment.nationality_type_id)
        acc[nationalityName] = (acc[nationalityName] || 0) + enrollment.student_count
        return acc
      },
      {} as Record<string, number>
    )

    // Calculate by level (group by cycle)
    const byLevel = rowData.reduce(
      (acc, enrollment) => {
        const levelName = getLevelName(enrollment.level_id)
        acc[levelName] = (acc[levelName] || 0) + enrollment.student_count
        return acc
      },
      {} as Record<string, number>
    )

    // Capacity utilization (EFIR total capacity ~1,875 students)
    const totalCapacity = 1875
    const capacityUtilization = totalCapacity > 0 ? (totalStudents / totalCapacity) * 100 : 0

    return {
      totalStudents,
      byNationality,
      byLevel,
      capacityUtilization: Math.round(capacityUtilization * 10) / 10,
      totalCapacity,
    }
  }, [rowData, getLevelName, getNationalityTypeName])

  const handleCreate = async (formData: EnrollmentFormData) => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }
    try {
      await createMutation.mutateAsync({
        budget_version_id: selectedVersionId,
        ...formData,
      })
      setCreateDialogOpen(false)
      createForm.reset()
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const handleDelete = useCallback(
    async (id: string) => {
      if (window.confirm('Êtes-vous sûr de vouloir supprimer cet effectif ?')) {
        try {
          await deleteMutation.mutateAsync(id)
        } catch {
          // Error toast is handled by the mutation's onError
        }
      }
    },
    [deleteMutation]
  )

  const handleCalculateProjections = async () => {
    if (!selectedVersionId) {
      toastMessages.warning.selectVersion()
      return
    }
    try {
      await calculateMutation.mutateAsync(selectedVersionId)
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const columnDefs: ColDef<Enrollment>[] = useMemo(
    () => [
      {
        field: 'level_id',
        headerName: 'Level',
        flex: 1,
        valueFormatter: (params) => getLevelName(params.value),
      },
      {
        field: 'nationality_type_id',
        headerName: 'Nationality',
        flex: 1,
        valueFormatter: (params) => getNationalityTypeName(params.value),
      },
      {
        field: 'student_count',
        headerName: 'Student Count',
        flex: 1,
        editable: true,
        cellEditor: 'agNumberCellEditor',
        cellEditorParams: {
          min: 0,
          max: 1000,
        },
      },
      {
        headerName: 'Actions',
        flex: 1,
        cellRenderer: (params: { data: Enrollment }) => {
          const enrollment = params.data
          return (
            <div className="flex gap-2 py-2">
              <Button
                size="sm"
                variant="destructive"
                onClick={() => handleDelete(enrollment.id)}
                disabled={deleteMutation.isPending}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          )
        },
      },
    ],
    [deleteMutation.isPending, getLevelName, getNationalityTypeName, handleDelete]
  )

  const onCellValueChanged = async (params: CellValueChangedEvent<Enrollment>) => {
    const enrollment = params.data
    try {
      await updateMutation.mutateAsync({
        id: enrollment.id,
        data: {
          student_count: params.newValue,
        },
      })
    } catch {
      // Error toast is handled by the mutation's onError
      // Revert the change on error
      params.node.setDataValue(params.column, params.oldValue)
    }
  }

  return (
    <MainLayout>
      <PageContainer
        title="Enrollment Planning"
        description="Plan student enrollment by level and nationality"
        actions={
          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={handleCalculateProjections}
              disabled={!selectedVersionId || calculateMutation.isPending}
            >
              <Calculator className="h-4 w-4 mr-2" />
              Calculate Projections
            </Button>
            <Button onClick={() => setCreateDialogOpen(true)} disabled={!selectedVersionId}>
              <Plus className="h-4 w-4 mr-2" />
              Add Enrollment
            </Button>
          </div>
        }
      >
        <div className="mb-6">
          <BudgetVersionSelector
            value={selectedVersionId}
            onChange={setSelectedVersionId}
            className="max-w-md"
          />
        </div>

        {selectedVersionId && rowData.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            {/* Total Students */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Students</CardTitle>
                <Users className="h-4 w-4 text-twilight-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.totalStudents}</div>
                <p className="text-xs text-twilight-600 mt-1">
                  Across all levels and nationalities
                </p>
              </CardContent>
            </Card>

            {/* Capacity Utilization */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Capacity</CardTitle>
                <TrendingUp className="h-4 w-4 text-twilight-600" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statistics.capacityUtilization}%</div>
                <p className="text-xs text-twilight-600 mt-1">
                  {statistics.totalStudents} / {statistics.totalCapacity} max
                </p>
                <div className="w-full bg-twilight-200 rounded-full h-2 mt-2">
                  <div
                    className={`h-2 rounded-full ${
                      statistics.capacityUtilization > 90
                        ? 'bg-error-600'
                        : statistics.capacityUtilization > 75
                          ? 'bg-warning-600'
                          : 'bg-success-600'
                    }`}
                    style={{ width: `${Math.min(statistics.capacityUtilization, 100)}%` }}
                  />
                </div>
              </CardContent>
            </Card>

            {/* By Nationality */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">By Nationality</CardTitle>
                <Globe className="h-4 w-4 text-twilight-600" />
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {Object.entries(statistics.byNationality)
                    .slice(0, 3)
                    .map(([nationality, count]) => (
                      <div key={nationality} className="flex justify-between text-sm">
                        <span className="text-twilight-700">{nationality}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  {Object.keys(statistics.byNationality).length > 3 && (
                    <p className="text-xs text-twilight-600 mt-2">
                      +{Object.keys(statistics.byNationality).length - 3} more
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* By Level Summary */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">By Level</CardTitle>
                <Users className="h-4 w-4 text-twilight-600" />
              </CardHeader>
              <CardContent>
                <div className="space-y-1">
                  {Object.entries(statistics.byLevel)
                    .slice(0, 3)
                    .map(([level, count]) => (
                      <div key={level} className="flex justify-between text-sm">
                        <span className="text-twilight-700">{level}</span>
                        <span className="font-medium">{count}</span>
                      </div>
                    ))}
                  {Object.keys(statistics.byLevel).length > 3 && (
                    <p className="text-xs text-twilight-600 mt-2">
                      +{Object.keys(statistics.byLevel).length - 3} more
                    </p>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {selectedVersionId ? (
          <DataTableLazy
            rowData={rowData}
            columnDefs={columnDefs}
            loading={enrollmentsLoading}
            error={enrollmentsError}
            pagination={true}
            paginationPageSize={50}
            onCellValueChanged={onCellValueChanged}
          />
        ) : (
          <div className="text-center py-12 text-twilight-600">
            Please select a budget version to view enrollment data
          </div>
        )}
      </PageContainer>

      {/* Create Dialog */}
      <FormDialog
        open={createDialogOpen}
        onOpenChange={setCreateDialogOpen}
        title="Add Enrollment Entry"
        description="Add a new enrollment entry for this budget version"
        onSubmit={createForm.handleSubmit(handleCreate)}
        isSubmitting={createMutation.isPending}
      >
        <div className="space-y-4">
          <div>
            <Label htmlFor="level_id">Level</Label>
            <Select
              onValueChange={(value) => createForm.setValue('level_id', value)}
              value={createForm.watch('level_id')}
            >
              <SelectTrigger id="level_id" className="mt-1">
                <SelectValue placeholder="Select a level" />
              </SelectTrigger>
              <SelectContent>
                {levelsData?.map((level) => (
                  <SelectItem key={level.id} value={level.id}>
                    {level.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {createForm.formState.errors.level_id && (
              <p className="text-sm text-error-600 mt-1">
                {createForm.formState.errors.level_id.message}
              </p>
            )}
          </div>
          <div>
            <Label htmlFor="nationality_type_id">Nationality Type</Label>
            <Select
              onValueChange={(value) => createForm.setValue('nationality_type_id', value)}
              value={createForm.watch('nationality_type_id')}
            >
              <SelectTrigger id="nationality_type_id" className="mt-1">
                <SelectValue placeholder="Select a nationality type" />
              </SelectTrigger>
              <SelectContent>
                {nationalityTypesData?.map((type) => (
                  <SelectItem key={type.id} value={type.id}>
                    {type.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {createForm.formState.errors.nationality_type_id && (
              <p className="text-sm text-error-600 mt-1">
                {createForm.formState.errors.nationality_type_id.message}
              </p>
            )}
          </div>
          <div>
            <Label htmlFor="student_count">Student Count</Label>
            <Input
              id="student_count"
              type="number"
              {...createForm.register('student_count', { valueAsNumber: true })}
            />
            {createForm.formState.errors.student_count && (
              <p className="text-sm text-error-600 mt-1">
                {createForm.formState.errors.student_count.message}
              </p>
            )}
          </div>
        </div>
      </FormDialog>
    </MainLayout>
  )
}
