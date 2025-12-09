/**
 * Workforce API service.
 *
 * Service layer for workforce/personnel management endpoints.
 * Handles employee management, salaries, EOS provisions, and AEFE positions.
 */

import { apiRequest } from '@/lib/api-client'
import type {
  Employee,
  EmployeeBulkResponse,
  EmployeeCreate,
  EmployeeUpdate,
  EmployeeSalary,
  EmployeeSalaryCreate,
  EmployeeSalaryUpdate,
  SalaryBreakdown,
  EOSProvision,
  EOSCalculation,
  EOSCalculationRequest,
  EOSSummary,
  AEFEPosition,
  AEFEPositionSummary,
  AEFEPositionUpdate,
  InitializeAEFEPositionsRequest,
  PlaceholderEmployeeCreate,
  WorkforceSummary,
  EmployeeFilters,
} from '@/types/workforce'
import { withServiceErrorHandling } from './utils'

/**
 * Workforce API - Employee-based personnel management
 */
export const workforceApi = {
  // ==============================================================================
  // Employee Management
  // ==============================================================================
  employees: {
    /**
     * List all employees for a budget version.
     * Includes both Base 100 (existing) and Planned (placeholder) employees.
     */
    getAll: async (budgetVersionId: string, filters?: EmployeeFilters) => {
      const params = new URLSearchParams({ version_id: budgetVersionId })

      if (filters?.category) params.append('category', filters.category)
      if (filters?.nationality) params.append('nationality', filters.nationality)
      if (filters?.cycle_id) params.append('cycle_id', filters.cycle_id)
      if (filters?.subject_id) params.append('subject_id', filters.subject_id)
      if (filters?.is_active !== undefined) params.append('is_active', String(filters.is_active))
      if (filters?.is_placeholder !== undefined)
        params.append('is_placeholder', String(filters.is_placeholder))
      if (filters?.search) params.append('search', filters.search)

      return withServiceErrorHandling(
        apiRequest<EmployeeBulkResponse>({
          method: 'GET',
          url: `/workforce/employees?${params.toString()}`,
        }),
        'workforce: get employees'
      )
    },

    /**
     * Get a single employee by ID.
     */
    getById: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<Employee>({
          method: 'GET',
          url: `/workforce/employees/${employeeId}`,
        }),
        'workforce: get employee'
      )
    },

    /**
     * Create a new employee.
     * Employee code is auto-generated (EMP001, EMP002, etc.).
     */
    create: async (data: EmployeeCreate) => {
      return withServiceErrorHandling(
        apiRequest<Employee>({
          method: 'POST',
          url: '/workforce/employees',
          data,
        }),
        'workforce: create employee'
      )
    },

    /**
     * Update an existing employee.
     */
    update: async (employeeId: string, data: EmployeeUpdate) => {
      return withServiceErrorHandling(
        apiRequest<Employee>({
          method: 'PUT',
          url: `/workforce/employees/${employeeId}`,
          data,
        }),
        'workforce: update employee'
      )
    },

    /**
     * Soft-delete an employee.
     * Employee is marked as inactive, not permanently deleted.
     */
    delete: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<void>({
          method: 'DELETE',
          url: `/workforce/employees/${employeeId}`,
        }),
        'workforce: delete employee'
      )
    },

    /**
     * Create a placeholder employee from DHG gap analysis.
     * Placeholder employees are marked with is_placeholder=true.
     */
    createPlaceholder: async (data: PlaceholderEmployeeCreate) => {
      return withServiceErrorHandling(
        apiRequest<Employee>({
          method: 'POST',
          url: '/workforce/employees/placeholder',
          data,
        }),
        'workforce: create placeholder employee'
      )
    },
  },

  // ==============================================================================
  // Salary Management
  // ==============================================================================
  salaries: {
    /**
     * Get current salary for an employee.
     * Returns the salary record with effective_to = NULL or future date.
     */
    getCurrent: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<EmployeeSalary | null>({
          method: 'GET',
          url: `/workforce/employees/${employeeId}/salaries/current`,
        }),
        'workforce: get current salary'
      )
    },

    /**
     * Get salary history for an employee.
     */
    getHistory: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<EmployeeSalary[]>({
          method: 'GET',
          url: `/workforce/employees/${employeeId}/salaries`,
        }),
        'workforce: get salary history'
      )
    },

    /**
     * Create/update salary for an employee.
     * Automatically closes previous salary record.
     */
    create: async (data: EmployeeSalaryCreate) => {
      return withServiceErrorHandling(
        apiRequest<EmployeeSalary>({
          method: 'POST',
          url: `/workforce/employees/${data.employee_id}/salaries`,
          data,
        }),
        'workforce: create salary'
      )
    },

    /**
     * Update an existing salary record.
     */
    update: async (salaryId: string, data: EmployeeSalaryUpdate) => {
      return withServiceErrorHandling(
        apiRequest<EmployeeSalary>({
          method: 'PUT',
          url: `/workforce/salaries/${salaryId}`,
          data,
        }),
        'workforce: update salary'
      )
    },

    /**
     * Get salary breakdown with GOSI calculations.
     */
    getBreakdown: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<SalaryBreakdown>({
          method: 'GET',
          url: `/workforce/employees/${employeeId}/salary-breakdown`,
        }),
        'workforce: get salary breakdown'
      )
    },
  },

  // ==============================================================================
  // EOS (End of Service) Management
  // ==============================================================================
  eos: {
    /**
     * Calculate EOS without saving.
     * Use this for the EOS calculator UI.
     */
    calculate: async (data: EOSCalculationRequest) => {
      return withServiceErrorHandling(
        apiRequest<EOSCalculation>({
          method: 'POST',
          url: '/workforce/eos/calculate',
          data,
        }),
        'workforce: calculate EOS'
      )
    },

    /**
     * Get EOS provision for an employee.
     */
    getProvision: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<EOSProvision | null>({
          method: 'GET',
          url: `/workforce/employees/${employeeId}/eos`,
        }),
        'workforce: get EOS provision'
      )
    },

    /**
     * Calculate and save EOS provision for an employee.
     */
    calculateAndSave: async (employeeId: string, budgetVersionId: string, asOfDate: string) => {
      return withServiceErrorHandling(
        apiRequest<EOSProvision>({
          method: 'POST',
          url: `/workforce/employees/${employeeId}/eos`,
          data: {
            budget_version_id: budgetVersionId,
            employee_id: employeeId,
            as_of_date: asOfDate,
          },
        }),
        'workforce: calculate and save EOS provision'
      )
    },

    /**
     * Calculate EOS for all employees in a budget version.
     */
    calculateAll: async (budgetVersionId: string, asOfDate: string) => {
      return withServiceErrorHandling(
        apiRequest<{ calculated_count: number; total_provision_sar: number }>({
          method: 'POST',
          url: '/workforce/eos/calculate-all',
          data: {
            budget_version_id: budgetVersionId,
            as_of_date: asOfDate,
          },
        }),
        'workforce: calculate all EOS'
      )
    },

    /**
     * Get EOS summary for a budget version.
     */
    getSummary: async (budgetVersionId: string, asOfDate?: string) => {
      const params = new URLSearchParams({ version_id: budgetVersionId })
      if (asOfDate) params.append('as_of_date', asOfDate)

      return withServiceErrorHandling(
        apiRequest<EOSSummary>({
          method: 'GET',
          url: `/workforce/eos/summary?${params.toString()}`,
        }),
        'workforce: get EOS summary'
      )
    },
  },

  // ==============================================================================
  // AEFE Position Management
  // ==============================================================================
  aefe: {
    /**
     * Get all AEFE positions for a budget version.
     */
    getAll: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPosition[]>({
          method: 'GET',
          url: `/workforce/aefe-positions?version_id=${budgetVersionId}`,
        }),
        'workforce: get AEFE positions'
      )
    },

    /**
     * Get AEFE positions summary (filled/vacant counts, costs).
     */
    getSummary: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPositionSummary>({
          method: 'GET',
          url: `/workforce/aefe-positions/summary?version_id=${budgetVersionId}`,
        }),
        'workforce: get AEFE summary'
      )
    },

    /**
     * Update an AEFE position (assign employee, update PRRD, etc.).
     */
    update: async (positionId: string, data: AEFEPositionUpdate) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPosition>({
          method: 'PUT',
          url: `/workforce/aefe-positions/${positionId}`,
          data,
        }),
        'workforce: update AEFE position'
      )
    },

    /**
     * Assign an employee to an AEFE position.
     */
    assignEmployee: async (positionId: string, employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPosition>({
          method: 'POST',
          url: `/workforce/aefe-positions/${positionId}/assign`,
          data: { employee_id: employeeId },
        }),
        'workforce: assign employee to AEFE position'
      )
    },

    /**
     * Unassign employee from an AEFE position.
     */
    unassignEmployee: async (positionId: string) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPosition>({
          method: 'POST',
          url: `/workforce/aefe-positions/${positionId}/unassign`,
        }),
        'workforce: unassign employee from AEFE position'
      )
    },

    /**
     * Initialize 28 AEFE positions (24 Detached + 4 Funded).
     * Call this when creating a new budget version.
     */
    initialize: async (data: InitializeAEFEPositionsRequest) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPosition[]>({
          method: 'POST',
          url: '/workforce/aefe-positions/initialize',
          data,
        }),
        'workforce: initialize AEFE positions'
      )
    },

    /**
     * Update PRRD rate for all detached positions.
     */
    updatePRRDRate: async (
      budgetVersionId: string,
      prrdAmountEur: number,
      exchangeRate: number
    ) => {
      return withServiceErrorHandling(
        apiRequest<{ updated_count: number; total_prrd_sar: number }>({
          method: 'POST',
          url: '/workforce/aefe-positions/update-prrd',
          data: {
            budget_version_id: budgetVersionId,
            prrd_amount_eur: prrdAmountEur,
            exchange_rate_eur_sar: exchangeRate,
          },
        }),
        'workforce: update PRRD rate'
      )
    },
  },

  // ==============================================================================
  // Workforce Summary
  // ==============================================================================
  summary: {
    /**
     * Get workforce summary for dashboard.
     * Includes employee counts, FTE totals, payroll, EOS provisions.
     */
    get: async (budgetVersionId: string) => {
      return withServiceErrorHandling(
        apiRequest<WorkforceSummary>({
          method: 'GET',
          url: `/workforce/summary?version_id=${budgetVersionId}`,
        }),
        'workforce: get summary'
      )
    },
  },
}

// ==============================================================================
// Convenience Exports
// ==============================================================================

export const {
  employees: employeesApi,
  salaries: salariesApi,
  eos: eosApi,
  aefe: aefeApi,
  summary: workforceSummaryApi,
} = workforceApi
