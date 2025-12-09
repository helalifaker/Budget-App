/**
 * React Query hooks for workforce/personnel management.
 *
 * Provides data fetching and mutation hooks for:
 * - Employee management (CRUD, placeholders)
 * - Salary management with GOSI calculations
 * - EOS (End of Service) provisions
 * - AEFE position management
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workforceApi } from '@/services/workforce'
import { toastMessages } from '@/lib/toast-messages'
import { useAuth } from '@/contexts/AuthContext'
import type {
  EmployeeCreate,
  EmployeeUpdate,
  EmployeeSalaryCreate,
  EmployeeSalaryUpdate,
  EOSCalculationRequest,
  AEFEPositionUpdate,
  InitializeAEFEPositionsRequest,
  PlaceholderEmployeeCreate,
  EmployeeFilters,
} from '@/types/workforce'

// ==============================================================================
// Query Keys Factory
// ==============================================================================

export const workforceKeys = {
  all: ['workforce'] as const,

  // Employees
  employees: (budgetVersionId: string) =>
    [...workforceKeys.all, 'employees', budgetVersionId] as const,
  employeesFiltered: (budgetVersionId: string, filters?: EmployeeFilters) =>
    [...workforceKeys.employees(budgetVersionId), filters] as const,
  employee: (employeeId: string) => [...workforceKeys.all, 'employee', employeeId] as const,

  // Salaries
  salaries: (employeeId: string) => [...workforceKeys.all, 'salaries', employeeId] as const,
  currentSalary: (employeeId: string) =>
    [...workforceKeys.salaries(employeeId), 'current'] as const,
  salaryBreakdown: (employeeId: string) =>
    [...workforceKeys.salaries(employeeId), 'breakdown'] as const,

  // EOS
  eos: (employeeId: string) => [...workforceKeys.all, 'eos', employeeId] as const,
  eosSummary: (budgetVersionId: string) =>
    [...workforceKeys.all, 'eos-summary', budgetVersionId] as const,

  // AEFE Positions
  aefePositions: (budgetVersionId: string) =>
    [...workforceKeys.all, 'aefe-positions', budgetVersionId] as const,
  aefeSummary: (budgetVersionId: string) =>
    [...workforceKeys.all, 'aefe-summary', budgetVersionId] as const,

  // Workforce Summary
  summary: (budgetVersionId: string) => [...workforceKeys.all, 'summary', budgetVersionId] as const,
}

// ==============================================================================
// Employee Hooks
// ==============================================================================

/**
 * Fetch all employees for a budget version.
 * Includes both Base 100 and Planned (placeholder) employees.
 */
export function useEmployees(budgetVersionId: string | undefined, filters?: EmployeeFilters) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.employeesFiltered(budgetVersionId ?? '', filters),
    queryFn: () => workforceApi.employees.getAll(budgetVersionId!, filters),
    enabled: !!budgetVersionId && !!session && !loading,
    staleTime: 5 * 60 * 1000, // 5 minutes - employees may be edited
  })
}

/**
 * Fetch a single employee by ID.
 */
export function useEmployee(employeeId: string | undefined) {
  return useQuery({
    queryKey: workforceKeys.employee(employeeId ?? ''),
    queryFn: () => workforceApi.employees.getById(employeeId!),
    enabled: !!employeeId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Create a new employee.
 * Employee code is auto-generated (EMP001, EMP002, etc.).
 */
export function useCreateEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EmployeeCreate) => workforceApi.employees.create(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employees(variables.budget_version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budget_version_id),
      })
      toastMessages.success.created('Employee')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Update an existing employee.
 */
export function useUpdateEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      employeeId,
      data,
    }: {
      employeeId: string
      data: EmployeeUpdate
      budgetVersionId: string
    }) => workforceApi.employees.update(employeeId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employee(variables.employeeId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employees(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budgetVersionId),
      })
      toastMessages.success.updated('Employee')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Soft-delete an employee.
 */
export function useDeleteEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ employeeId }: { employeeId: string; budgetVersionId: string }) =>
      workforceApi.employees.delete(employeeId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employees(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budgetVersionId),
      })
      toastMessages.success.deleted('Employee')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Create a placeholder employee from DHG gap analysis.
 */
export function useCreatePlaceholderEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: PlaceholderEmployeeCreate) => workforceApi.employees.createPlaceholder(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employees(variables.budget_version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budget_version_id),
      })
      toastMessages.success.custom('Placeholder position created from DHG gap')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

// ==============================================================================
// Salary Hooks
// ==============================================================================

/**
 * Get current salary for an employee.
 */
export function useCurrentSalary(employeeId: string | undefined) {
  return useQuery({
    queryKey: workforceKeys.currentSalary(employeeId ?? ''),
    queryFn: () => workforceApi.salaries.getCurrent(employeeId!),
    enabled: !!employeeId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get salary history for an employee.
 */
export function useSalaryHistory(employeeId: string | undefined) {
  return useQuery({
    queryKey: workforceKeys.salaries(employeeId ?? ''),
    queryFn: () => workforceApi.salaries.getHistory(employeeId!),
    enabled: !!employeeId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get salary breakdown with GOSI calculations.
 */
export function useSalaryBreakdown(employeeId: string | undefined) {
  return useQuery({
    queryKey: workforceKeys.salaryBreakdown(employeeId ?? ''),
    queryFn: () => workforceApi.salaries.getBreakdown(employeeId!),
    enabled: !!employeeId,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Create/update salary for an employee.
 */
export function useCreateSalary() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: EmployeeSalaryCreate) => workforceApi.salaries.create(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.salaries(variables.employee_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budget_version_id),
      })
      toastMessages.success.created('Salary')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Update an existing salary record.
 */
export function useUpdateSalary() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      salaryId,
      data,
    }: {
      salaryId: string
      data: EmployeeSalaryUpdate
      employeeId: string
      budgetVersionId: string
    }) => workforceApi.salaries.update(salaryId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.salaries(variables.employeeId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budgetVersionId),
      })
      toastMessages.success.updated('Salary')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

// ==============================================================================
// EOS (End of Service) Hooks
// ==============================================================================

/**
 * Calculate EOS without saving.
 * Use this for the EOS calculator UI.
 */
export function useCalculateEOS() {
  return useMutation({
    mutationFn: (data: EOSCalculationRequest) => workforceApi.eos.calculate(data),
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Get EOS provision for an employee.
 */
export function useEOSProvision(employeeId: string | undefined) {
  return useQuery({
    queryKey: workforceKeys.eos(employeeId ?? ''),
    queryFn: () => workforceApi.eos.getProvision(employeeId!),
    enabled: !!employeeId,
    staleTime: 10 * 60 * 1000, // 10 minutes - EOS changes less frequently
  })
}

/**
 * Calculate and save EOS provision for an employee.
 */
export function useCalculateAndSaveEOS() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      employeeId,
      budgetVersionId,
      asOfDate,
    }: {
      employeeId: string
      budgetVersionId: string
      asOfDate: string
    }) => workforceApi.eos.calculateAndSave(employeeId, budgetVersionId, asOfDate),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.eos(variables.employeeId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.eosSummary(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budgetVersionId),
      })
      toastMessages.success.custom('EOS provision calculated')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Calculate EOS for all employees in a budget version.
 */
export function useCalculateAllEOS() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ budgetVersionId, asOfDate }: { budgetVersionId: string; asOfDate: string }) =>
      workforceApi.eos.calculateAll(budgetVersionId, asOfDate),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.eosSummary(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budgetVersionId),
      })
      // Invalidate all individual EOS provisions
      queryClient.invalidateQueries({
        predicate: (query) => query.queryKey[0] === 'workforce' && query.queryKey[1] === 'eos',
      })
      toastMessages.success.custom(
        `Calculated EOS for ${data.calculated_count} employees (Total: ${data.total_provision_sar.toLocaleString()} SAR)`
      )
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Get EOS summary for a budget version.
 */
export function useEOSSummary(budgetVersionId: string | undefined, asOfDate?: string) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: [...workforceKeys.eosSummary(budgetVersionId ?? ''), asOfDate] as const,
    queryFn: () => workforceApi.eos.getSummary(budgetVersionId!, asOfDate),
    enabled: !!budgetVersionId && !!session && !loading,
    staleTime: 10 * 60 * 1000,
  })
}

// ==============================================================================
// AEFE Position Hooks
// ==============================================================================

/**
 * Get all AEFE positions for a budget version.
 */
export function useAEFEPositions(budgetVersionId: string | undefined) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.aefePositions(budgetVersionId ?? ''),
    queryFn: () => workforceApi.aefe.getAll(budgetVersionId!),
    enabled: !!budgetVersionId && !!session && !loading,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get AEFE positions summary (filled/vacant counts, costs).
 */
export function useAEFESummary(budgetVersionId: string | undefined) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.aefeSummary(budgetVersionId ?? ''),
    queryFn: () => workforceApi.aefe.getSummary(budgetVersionId!),
    enabled: !!budgetVersionId && !!session && !loading,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Update an AEFE position.
 */
export function useUpdateAEFEPosition() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      positionId,
      data,
    }: {
      positionId: string
      data: AEFEPositionUpdate
      budgetVersionId: string
    }) => workforceApi.aefe.update(positionId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budgetVersionId),
      })
      toastMessages.success.updated('AEFE position')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Assign an employee to an AEFE position.
 */
export function useAssignEmployeeToAEFE() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      positionId,
      employeeId,
    }: {
      positionId: string
      employeeId: string
      budgetVersionId: string
    }) => workforceApi.aefe.assignEmployee(positionId, employeeId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.budgetVersionId),
      })
      toastMessages.success.custom('Employee assigned to AEFE position')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Unassign employee from an AEFE position.
 */
export function useUnassignEmployeeFromAEFE() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ positionId }: { positionId: string; budgetVersionId: string }) =>
      workforceApi.aefe.unassignEmployee(positionId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.budgetVersionId),
      })
      toastMessages.success.custom('Employee unassigned from AEFE position')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Initialize 28 AEFE positions (24 Detached + 4 Funded).
 */
export function useInitializeAEFEPositions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (data: InitializeAEFEPositionsRequest) => workforceApi.aefe.initialize(data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.budget_version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.budget_version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budget_version_id),
      })
      toastMessages.success.custom('Initialized 28 AEFE positions (24 Detached + 4 Funded)')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

/**
 * Update PRRD rate for all detached positions.
 */
export function useUpdatePRRDRate() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      budgetVersionId,
      prrdAmountEur,
      exchangeRate,
    }: {
      budgetVersionId: string
      prrdAmountEur: number
      exchangeRate: number
    }) => workforceApi.aefe.updatePRRDRate(budgetVersionId, prrdAmountEur, exchangeRate),
    onSuccess: (data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.budgetVersionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.budgetVersionId),
      })
      toastMessages.success.custom(
        `Updated PRRD rate for ${data.updated_count} positions (Total: ${data.total_prrd_sar.toLocaleString()} SAR)`
      )
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

// ==============================================================================
// Workforce Summary Hook
// ==============================================================================

/**
 * Get workforce summary for dashboard.
 * Includes employee counts, FTE totals, payroll, EOS provisions.
 */
export function useWorkforceSummary(budgetVersionId: string | undefined) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.summary(budgetVersionId ?? ''),
    queryFn: () => workforceApi.summary.get(budgetVersionId!),
    enabled: !!budgetVersionId && !!session && !loading,
    staleTime: 5 * 60 * 1000,
  })
}
