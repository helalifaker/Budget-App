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
  employees: (versionId: string) => [...workforceKeys.all, 'employees', versionId] as const,
  employeesFiltered: (versionId: string, filters?: EmployeeFilters) =>
    [...workforceKeys.employees(versionId), filters] as const,
  employee: (versionId: string, employeeId: string) =>
    [...workforceKeys.all, 'employee', versionId, employeeId] as const,

  // Salaries
  salaries: (employeeId: string) => [...workforceKeys.all, 'salaries', employeeId] as const,
  currentSalary: (employeeId: string) =>
    [...workforceKeys.salaries(employeeId), 'current'] as const,
  salaryBreakdown: (employeeId: string) =>
    [...workforceKeys.salaries(employeeId), 'breakdown'] as const,

  // EOS
  eos: (employeeId: string) => [...workforceKeys.all, 'eos', employeeId] as const,
  eosSummary: (versionId: string) => [...workforceKeys.all, 'eos-summary', versionId] as const,

  // AEFE Positions
  aefePositions: (versionId: string) =>
    [...workforceKeys.all, 'aefe-positions', versionId] as const,
  aefeSummary: (versionId: string) => [...workforceKeys.all, 'aefe-summary', versionId] as const,

  // Workforce Summary
  summary: (versionId: string) => [...workforceKeys.all, 'summary', versionId] as const,
}

// ==============================================================================
// Employee Hooks
// ==============================================================================

/**
 * Fetch all employees for a budget version.
 * Includes both Base 100 and Planned (placeholder) employees.
 */
export function useEmployees(versionId: string | undefined, filters?: EmployeeFilters) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.employeesFiltered(versionId ?? '', filters),
    queryFn: () => workforceApi.employees.getAll(versionId!, filters),
    enabled: !!versionId && !!session && !loading,
    staleTime: 5 * 60 * 1000, // 5 minutes - employees may be edited
  })
}

/**
 * Fetch a single employee by ID.
 */
export function useEmployee(versionId: string | undefined, employeeId: string | undefined) {
  return useQuery({
    queryKey: workforceKeys.employee(versionId ?? '', employeeId ?? ''),
    queryFn: () => workforceApi.employees.getById(versionId!, employeeId!),
    enabled: !!versionId && !!employeeId,
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
        queryKey: workforceKeys.employees(variables.version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.version_id),
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
      versionId: string
    }) => workforceApi.employees.update(employeeId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employee(variables.versionId, variables.employeeId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employees(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.versionId),
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
    mutationFn: ({ employeeId }: { employeeId: string; versionId: string }) =>
      workforceApi.employees.delete(employeeId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.employees(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.versionId),
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
        queryKey: workforceKeys.employees(variables.version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.version_id),
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
        queryKey: workforceKeys.summary(variables.version_id),
      })
      toastMessages.success.created('Salary')
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
 * Calculate and save EOS provision for an employee.
 */
export function useCalculateAndSaveEOS() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      employeeId,
      versionId,
      asOfDate,
    }: {
      employeeId: string
      versionId: string
      asOfDate: string
    }) => workforceApi.eos.calculateAndSave(employeeId, versionId, asOfDate),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.eos(variables.employeeId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.eosSummary(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.versionId),
      })
      toastMessages.success.custom('EOS provision calculated')
    },
    onError: (error: Error) => {
      toastMessages.error.custom(error.message)
    },
  })
}

// ==============================================================================
// AEFE Position Hooks
// ==============================================================================

/**
 * Get all AEFE positions for a budget version.
 */
export function useAEFEPositions(versionId: string | undefined) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.aefePositions(versionId ?? ''),
    queryFn: () => workforceApi.aefe.getAll(versionId!),
    enabled: !!versionId && !!session && !loading,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Get AEFE positions summary (filled/vacant counts, costs).
 */
export function useAEFESummary(versionId: string | undefined) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.aefeSummary(versionId ?? ''),
    queryFn: () => workforceApi.aefe.getSummary(versionId!),
    enabled: !!versionId && !!session && !loading,
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
      versionId: string
    }) => workforceApi.aefe.update(positionId, data),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.versionId),
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
      versionId: string
    }) => workforceApi.aefe.assignEmployee(positionId, employeeId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.versionId),
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
    mutationFn: ({ positionId }: { positionId: string; versionId: string }) =>
      workforceApi.aefe.unassignEmployee(positionId),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefePositions(variables.versionId),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.versionId),
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
        queryKey: workforceKeys.aefePositions(variables.version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.aefeSummary(variables.version_id),
      })
      queryClient.invalidateQueries({
        queryKey: workforceKeys.summary(variables.version_id),
      })
      toastMessages.success.custom('Initialized 28 AEFE positions (24 Detached + 4 Funded)')
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
export function useWorkforceSummary(versionId: string | undefined) {
  const { session, loading } = useAuth()

  return useQuery({
    queryKey: workforceKeys.summary(versionId ?? ''),
    queryFn: () => workforceApi.summary.get(versionId!),
    enabled: !!versionId && !!session && !loading,
    staleTime: 5 * 60 * 1000,
  })
}
