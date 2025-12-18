/**
 * Strategic Module Page - 5-Year Planning
 *
 * Navigation (SmartHeader + ModuleDock) is provided by _authenticated.tsx layout.
 * NO MainLayout/CockpitLayout wrapper here to avoid double navigation.
 */

import { createFileRoute } from '@tanstack/react-router'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Badge } from '@/components/ui/badge'
import { ScenarioChart } from '@/components/charts/ScenarioChart'
import { useVersions } from '@/hooks/api/useVersions'
import {
  useStrategicPlans,
  useStrategicPlan,
  useCreateStrategicPlan,
  useUpdateScenarioAssumptions,
  useStrategicProjections,
  useDeleteStrategicPlan,
} from '@/hooks/api/useStrategic'
import { Plus, Edit, Trash2 } from 'lucide-react'
import { toastMessages } from '@/lib/toast-messages'

const createPlanSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  base_version_id: z.string().uuid('Select a version'),
  years_count: z.number().min(1).max(5),
})

type CreatePlanForm = z.infer<typeof createPlanSchema>

const assumptionsSchema = z.object({
  scenario_id: z.string().uuid(),
  enrollment_growth_rate: z.number(),
  fee_increase_rate: z.number(),
  salary_inflation_rate: z.number(),
  operating_growth_rate: z.number(),
})

type AssumptionsForm = z.infer<typeof assumptionsSchema>

export const Route = createFileRoute('/_authenticated/strategic/')({
  component: StrategicPlanningPage,
})

function StrategicPlanningPage() {
  const [createDialogOpen, setCreateDialogOpen] = useState(false)
  const [editDialogOpen, setEditDialogOpen] = useState(false)
  const [selectedPlanId, setSelectedPlanId] = useState<string | undefined>(undefined)
  const [selectedScenarioId, setSelectedScenarioId] = useState<string | undefined>(undefined)

  const { data: plans, isLoading: plansLoading } = useStrategicPlans()
  const { data: selectedPlan } = useStrategicPlan(selectedPlanId)
  const { data: budgetVersions } = useVersions()
  const { data: projections } = useStrategicProjections(selectedPlanId, selectedScenarioId)

  const createMutation = useCreateStrategicPlan()
  const updateAssumptionsMutation = useUpdateScenarioAssumptions()
  const deleteMutation = useDeleteStrategicPlan()

  const createForm = useForm<CreatePlanForm>({
    resolver: zodResolver(createPlanSchema),
    defaultValues: {
      name: '',
      base_version_id: '',
      years_count: 5,
    },
  })

  const assumptionsForm = useForm<AssumptionsForm>({
    resolver: zodResolver(assumptionsSchema),
  })

  const handleCreate = async (data: CreatePlanForm) => {
    try {
      const result = await createMutation.mutateAsync(data)
      setCreateDialogOpen(false)
      setSelectedPlanId(result.id)
      createForm.reset()
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const handleUpdateAssumptions = async (data: AssumptionsForm) => {
    if (!selectedPlanId) {
      toastMessages.warning.selectVersion()
      return
    }
    try {
      await updateAssumptionsMutation.mutateAsync({
        planId: selectedPlanId,
        ...data,
      })
      setEditDialogOpen(false)
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const handleDelete = async (planId: string) => {
    if (!confirm('Êtes-vous sûr de vouloir supprimer ce plan stratégique ?')) return
    try {
      await deleteMutation.mutateAsync(planId)
      if (selectedPlanId === planId) {
        setSelectedPlanId('')
      }
    } catch {
      // Error toast is handled by the mutation's onError
    }
  }

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-SA', {
      style: 'currency',
      currency: 'SAR',
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value)
  }

  // Prepare chart data
  const chartData =
    projections?.map((p) => ({
      year: p.year,
      conservative: selectedPlan?.scenarios.find((s) => s.name === 'Conservative') ? p.revenue : 0,
      base: selectedPlan?.scenarios.find((s) => s.name === 'Base Case') ? p.revenue : 0,
      optimistic: selectedPlan?.scenarios.find((s) => s.name === 'Optimistic') ? p.revenue : 0,
    })) || []

  return (
    <div className="p-6" style={{ background: 'var(--efir-bg-canvas)' }}>
      <div className="space-y-6">
        {/* Create Plan Button */}
        <div className="flex justify-end">
          <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Plus className="w-4 h-4 mr-2" />
                Create Plan
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Strategic Plan</DialogTitle>
              </DialogHeader>
              <form onSubmit={createForm.handleSubmit(handleCreate)} className="space-y-4">
                <div>
                  <Label>Plan Name</Label>
                  <Input {...createForm.register('name')} placeholder="5-Year Plan 2026-2030" />
                  {createForm.formState.errors.name && (
                    <p className="text-sm text-red-600 mt-1">
                      {createForm.formState.errors.name.message}
                    </p>
                  )}
                </div>
                <div>
                  <Label>Base Budget Version</Label>
                  <Select
                    value={createForm.watch('base_version_id')}
                    onValueChange={(v) => createForm.setValue('base_version_id', v)}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select version" />
                    </SelectTrigger>
                    <SelectContent>
                      {budgetVersions?.items
                        .filter((v) => v.status === 'approved')
                        .map((v) => (
                          <SelectItem key={v.id} value={v.id}>
                            {v.name} - {v.fiscal_year}
                          </SelectItem>
                        ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Number of Years</Label>
                  <Input
                    type="number"
                    min={1}
                    max={5}
                    {...createForm.register('years_count', { valueAsNumber: true })}
                  />
                </div>
                <Button type="submit" disabled={createMutation.isPending}>
                  {createMutation.isPending ? 'Creating...' : 'Create Plan'}
                </Button>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Plans List */}
        <Card>
          <CardHeader>
            <CardTitle>Strategic Plans</CardTitle>
          </CardHeader>
          <CardContent>
            {plansLoading ? (
              <div className="text-center py-8">Loading plans...</div>
            ) : plans && plans.length > 0 ? (
              <div className="space-y-3">
                {plans.map((plan) => (
                  <div
                    key={plan.id}
                    className={`p-4 border rounded-lg hover:border-blue-500 cursor-pointer transition-colors ${
                      selectedPlanId === plan.id ? 'border-blue-500 bg-blue-50' : ''
                    }`}
                    onClick={() => setSelectedPlanId(plan.id)}
                  >
                    <div className="flex items-center justify-between">
                      <div>
                        <h3 className="font-semibold text-lg">{plan.name}</h3>
                        <p className="text-sm text-gray-600">
                          Base Year: {plan.base_year} | {plan.years_count} years
                        </p>
                        <p className="text-xs text-gray-500 mt-1">
                          Created: {new Date(plan.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(plan.id)
                          }}
                        >
                          <Trash2 className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No strategic plans. Create one to get started.
              </div>
            )}
          </CardContent>
        </Card>

        {/* Plan Details */}
        {selectedPlan && (
          <>
            {/* Scenarios */}
            <Card>
              <CardHeader>
                <CardTitle>Scenarios & Assumptions</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {selectedPlan.scenarios.map((scenario) => (
                    <div key={scenario.id} className="p-4 border rounded-lg">
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold">{scenario.name}</h4>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            assumptionsForm.setValue('scenario_id', scenario.id)
                            assumptionsForm.setValue(
                              'enrollment_growth_rate',
                              scenario.enrollment_growth_rate
                            )
                            assumptionsForm.setValue(
                              'fee_increase_rate',
                              scenario.fee_increase_rate
                            )
                            assumptionsForm.setValue(
                              'salary_inflation_rate',
                              scenario.salary_inflation_rate
                            )
                            assumptionsForm.setValue(
                              'operating_growth_rate',
                              scenario.operating_growth_rate
                            )
                            setSelectedScenarioId(scenario.id)
                            setEditDialogOpen(true)
                          }}
                        >
                          <Edit className="w-4 h-4" />
                        </Button>
                      </div>
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Enrollment Growth:</span>
                          <Badge variant="outline">
                            {(scenario.enrollment_growth_rate * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Fee Increase:</span>
                          <Badge variant="outline">
                            {(scenario.fee_increase_rate * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Salary Inflation:</span>
                          <Badge variant="outline">
                            {(scenario.salary_inflation_rate * 100).toFixed(1)}%
                          </Badge>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Operating Growth:</span>
                          <Badge variant="outline">
                            {(scenario.operating_growth_rate * 100).toFixed(1)}%
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Edit Assumptions Dialog */}
            <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
              <DialogContent>
                <DialogHeader>
                  <DialogTitle>Edit Scenario Assumptions</DialogTitle>
                </DialogHeader>
                <form
                  onSubmit={assumptionsForm.handleSubmit(handleUpdateAssumptions)}
                  className="space-y-4"
                >
                  <div>
                    <Label>Enrollment Growth Rate (%)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      {...assumptionsForm.register('enrollment_growth_rate', {
                        valueAsNumber: true,
                      })}
                    />
                  </div>
                  <div>
                    <Label>Fee Increase Rate (%)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      {...assumptionsForm.register('fee_increase_rate', { valueAsNumber: true })}
                    />
                  </div>
                  <div>
                    <Label>Salary Inflation Rate (%)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      {...assumptionsForm.register('salary_inflation_rate', {
                        valueAsNumber: true,
                      })}
                    />
                  </div>
                  <div>
                    <Label>Operating Growth Rate (%)</Label>
                    <Input
                      type="number"
                      step="0.1"
                      {...assumptionsForm.register('operating_growth_rate', {
                        valueAsNumber: true,
                      })}
                    />
                  </div>
                  <Button type="submit" disabled={updateAssumptionsMutation.isPending}>
                    {updateAssumptionsMutation.isPending ? 'Updating...' : 'Update'}
                  </Button>
                </form>
              </DialogContent>
            </Dialog>

            {/* Projections Table */}
            {selectedScenarioId && projections && projections.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>Multi-Year Projections</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-3">Year</th>
                          <th className="text-right py-2 px-3">Students</th>
                          <th className="text-right py-2 px-3">Classes</th>
                          <th className="text-right py-2 px-3">Teachers</th>
                          <th className="text-right py-2 px-3">Revenue</th>
                          <th className="text-right py-2 px-3">Personnel</th>
                          <th className="text-right py-2 px-3">Operating</th>
                          <th className="text-right py-2 px-3">Net Income</th>
                          <th className="text-right py-2 px-3">Margin %</th>
                        </tr>
                      </thead>
                      <tbody>
                        {projections.map((p) => (
                          <tr key={p.year} className="border-b hover:bg-gray-50">
                            <td className="py-2 px-3 font-medium">{p.year}</td>
                            <td className="text-right py-2 px-3">{p.students.toLocaleString()}</td>
                            <td className="text-right py-2 px-3">{p.classes.toLocaleString()}</td>
                            <td className="text-right py-2 px-3">{p.teachers.toLocaleString()}</td>
                            <td className="text-right py-2 px-3">{formatCurrency(p.revenue)}</td>
                            <td className="text-right py-2 px-3">
                              {formatCurrency(p.personnel_costs)}
                            </td>
                            <td className="text-right py-2 px-3">
                              {formatCurrency(p.operating_costs)}
                            </td>
                            <td
                              className={`text-right py-2 px-3 font-semibold ${p.net_income >= 0 ? 'text-green-600' : 'text-red-600'}`}
                            >
                              {formatCurrency(p.net_income)}
                            </td>
                            <td className="text-right py-2 px-3">
                              {p.operating_margin.toFixed(1)}%
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Scenario Comparison Chart */}
            {chartData.length > 0 && (
              <ScenarioChart
                data={chartData}
                title="Scenario Comparison"
                metrics={['Revenue', 'Costs', 'Net Income', 'Students']}
              />
            )}
          </>
        )}
      </div>
    </div>
  )
}
