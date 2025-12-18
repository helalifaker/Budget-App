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
  EOSProvision,
  EOSCalculation,
  EOSCalculationRequest,
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
     * List all employees for a version.
     * Includes both Base 100 (existing) and Planned (placeholder) employees.
     */
    getAll: async (versionId: string, filters?: EmployeeFilters) => {
      // Build query params for filters (not version_id - that goes in path)
      const params = new URLSearchParams()

      if (filters?.category) params.append('category', filters.category)
      if (filters?.nationality) params.append('nationality', filters.nationality)
      if (filters?.cycle_id) params.append('cycle_id', filters.cycle_id)
      if (filters?.subject_id) params.append('subject_id', filters.subject_id)
      if (filters?.is_active !== undefined)
        params.append('include_inactive', String(!filters.is_active))
      if (filters?.is_placeholder !== undefined)
        params.append('is_placeholder', String(filters.is_placeholder))
      if (filters?.search) params.append('search', filters.search)

      const queryString = params.toString()
      return withServiceErrorHandling(
        apiRequest<EmployeeBulkResponse>({
          method: 'GET',
          url: `/workforce/employees/${versionId}${queryString ? `?${queryString}` : ''}`,
        }),
        'workforce: get employees'
      )
    },

    /**
     * Get a single employee by ID.
     */
    getById: async (versionId: string, employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<Employee>({
          method: 'GET',
          url: `/workforce/employees/${versionId}/${employeeId}`,
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
          url: `/workforce/employees/${employeeId}/salary`,
        }),
        'workforce: get current salary'
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
          url: `/workforce/employees/${data.employee_id}/salary`,
          data,
        }),
        'workforce: create salary'
      )
    },

    /**
     * Get salary history for an employee.
     * Returns all salary records ordered by effective date (most recent first).
     */
    getHistory: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<EmployeeSalary[]>({
          method: 'GET',
          url: `/workforce/employees/${employeeId}/salary/history`,
        }),
        'workforce: get salary history'
      )
    },

    /**
     * Get salary breakdown for an employee (alias for getCurrent).
     * The current salary includes GOSI breakdown already.
     */
    getBreakdown: async (employeeId: string) => {
      return withServiceErrorHandling(
        apiRequest<EmployeeSalary | null>({
          method: 'GET',
          url: `/workforce/employees/${employeeId}/salary`,
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
     * Calculate and save EOS provision for an employee.
     */
    calculateAndSave: async (employeeId: string, versionId: string, asOfDate: string) => {
      return withServiceErrorHandling(
        apiRequest<EOSProvision>({
          method: 'POST',
          url: `/workforce/employees/${employeeId}/eos`,
          data: {
            version_id: versionId,
            employee_id: employeeId,
            as_of_date: asOfDate,
          },
        }),
        'workforce: calculate and save EOS provision'
      )
    },

    /**
     * Get current EOS provision for an employee.
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
     * Calculate EOS for all eligible employees in a version.
     * Excludes AEFE employees (Detached and Funded).
     */
    calculateAll: async (versionId: string, asOfDate: string) => {
      return withServiceErrorHandling(
        apiRequest<{ calculated_count: number; total_provision_sar: number }>({
          method: 'POST',
          url: `/workforce/eos/calculate-all/${versionId}?as_of_date=${asOfDate}`,
        }),
        'workforce: calculate all EOS'
      )
    },

    /**
     * Get EOS provision summary for a version.
     */
    getSummary: async (versionId: string, asOfDate?: string) => {
      const params = asOfDate ? `?as_of_date=${asOfDate}` : ''
      return withServiceErrorHandling(
        apiRequest<{
          version_id: string
          employee_count: number
          total_provision_sar: number
          as_of_date: string | null
        }>({
          method: 'GET',
          url: `/workforce/eos/summary/${versionId}${params}`,
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
     * Get all AEFE positions for a version.
     */
    getAll: async (versionId: string) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPosition[]>({
          method: 'GET',
          url: `/workforce/aefe-positions/${versionId}`,
        }),
        'workforce: get AEFE positions'
      )
    },

    /**
     * Get AEFE positions summary (filled/vacant counts, costs).
     */
    getSummary: async (versionId: string) => {
      return withServiceErrorHandling(
        apiRequest<AEFEPositionSummary>({
          method: 'GET',
          url: `/workforce/aefe-positions/${versionId}/summary`,
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
     * Backend expects query params: ?employee_id=...&cycle_id=...&subject_id=...
     */
    assignEmployee: async (
      positionId: string,
      employeeId: string,
      cycleId?: string,
      subjectId?: string
    ) => {
      const params = new URLSearchParams({ employee_id: employeeId })
      if (cycleId) params.append('cycle_id', cycleId)
      if (subjectId) params.append('subject_id', subjectId)

      return withServiceErrorHandling(
        apiRequest<AEFEPosition>({
          method: 'POST',
          url: `/workforce/aefe-positions/${positionId}/assign?${params.toString()}`,
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
     * Call this when creating a new version.
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
     * Update PRRD rate for all detached positions in a version.
     * Funded positions are not affected.
     */
    updatePRRDRate: async (versionId: string, prrdAmountEur: number, exchangeRate: number) => {
      return withServiceErrorHandling(
        apiRequest<{ updated_count: number; total_prrd_sar: number }>({
          method: 'PUT',
          url: `/workforce/aefe-positions/${versionId}/prrd-rate?prrd_amount_eur=${prrdAmountEur}&exchange_rate_eur_sar=${exchangeRate}`,
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
    get: async (versionId: string) => {
      return withServiceErrorHandling(
        apiRequest<WorkforceSummary>({
          method: 'GET',
          url: `/workforce/summary/${versionId}`,
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
