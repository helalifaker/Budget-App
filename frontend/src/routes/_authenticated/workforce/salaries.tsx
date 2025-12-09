/**
 * Workforce - Salaries & End of Service
 *
 * KSA labor law compliant salary management with:
 * - Salary breakdown (Basic + Housing + Transport + Other)
 * - GOSI calculations (employer + employee)
 * - End of Service provision tracking
 * - Yearly EOS impact calculation
 *
 * @module /workforce/salaries
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useState, useMemo } from 'react'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import {
  Banknote,
  Calculator,
  TrendingUp,
  Wallet,
  AlertCircle,
  User,
  RefreshCw,
  Building,
  BadgePercent,
  Calendar,
} from 'lucide-react'
import { useBudgetVersion } from '@/contexts/BudgetVersionContext'
import {
  useEmployees,
  useCurrentSalary,
  useEOSProvision,
  useCalculateEOS,
  useWorkforceSummary,
  useEOSSummary,
} from '@/hooks/api/useWorkforce'
import type { Employee, EOSCalculation, TerminationType } from '@/types/workforce'
import {
  EMPLOYEE_CATEGORY_LABELS,
  NATIONALITY_LABELS,
  GOSI_RATES,
  EOS_RATES,
  RESIGNATION_FACTORS,
  TERMINATION_TYPE_LABELS,
} from '@/types/workforce'
import { format } from 'date-fns'

export const Route = createFileRoute('/_authenticated/workforce/salaries')({
  beforeLoad: requireAuth,
  component: SalariesPage,
})

// ============================================================================
// Salary Breakdown Card Component
// ============================================================================

interface SalaryBreakdownCardProps {
  employee: Employee | null
  salary: {
    basic_salary_sar: number
    housing_allowance_sar: number
    transport_allowance_sar: number
    other_allowances_sar: number
    gross_salary_sar: number
    gosi_employer_sar: number
    gosi_employee_sar: number
  } | null
}

function SalaryBreakdownCard({ employee, salary }: SalaryBreakdownCardProps) {
  if (!employee) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Salary Breakdown</CardTitle>
          <CardDescription>Select an employee to view salary details</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
          <User className="h-12 w-12 opacity-50" />
        </CardContent>
      </Card>
    )
  }

  if (!salary) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Salary Breakdown</CardTitle>
          <CardDescription>{employee.full_name} - No salary record</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
          <p>No salary configured for this employee</p>
        </CardContent>
      </Card>
    )
  }

  const netSalary = salary.gross_salary_sar - salary.gosi_employee_sar
  const totalEmployerCost = salary.gross_salary_sar + salary.gosi_employer_sar

  const gosiRate = employee.nationality === 'SAUDI' ? GOSI_RATES.SAUDI : GOSI_RATES.EXPATRIATE

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Banknote className="h-5 w-5 text-gold-600" />
          Salary Breakdown
        </CardTitle>
        <CardDescription>
          {employee.full_name} ({EMPLOYEE_CATEGORY_LABELS[employee.category]})
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Components */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span>Basic Salary</span>
            <span className="font-medium">{salary.basic_salary_sar.toLocaleString()} SAR</span>
          </div>
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Housing Allowance</span>
            <span>{salary.housing_allowance_sar.toLocaleString()} SAR</span>
          </div>
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Transport Allowance</span>
            <span>{salary.transport_allowance_sar.toLocaleString()} SAR</span>
          </div>
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>Other Allowances</span>
            <span>{salary.other_allowances_sar.toLocaleString()} SAR</span>
          </div>
        </div>

        <Separator />

        {/* Gross */}
        <div className="flex justify-between font-medium">
          <span>Gross Salary</span>
          <span className="text-green-600">{salary.gross_salary_sar.toLocaleString()} SAR</span>
        </div>

        {/* GOSI */}
        <div className="space-y-2 rounded-lg bg-slate-50 p-3">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Building className="h-4 w-4" />
            GOSI Contributions ({NATIONALITY_LABELS[employee.nationality]})
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              Employer ({(gosiRate.employer * 100).toFixed(2)}%)
            </span>
            <span className="text-amber-600">-{salary.gosi_employer_sar.toLocaleString()} SAR</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">
              Employee ({(gosiRate.employee * 100).toFixed(2)}%)
            </span>
            <span className="text-red-600">-{salary.gosi_employee_sar.toLocaleString()} SAR</span>
          </div>
        </div>

        <Separator />

        {/* Net & Total Cost */}
        <div className="space-y-2">
          <div className="flex justify-between">
            <span className="text-sm">Net Salary (Employee)</span>
            <span className="font-semibold text-blue-600">{netSalary.toLocaleString()} SAR</span>
          </div>
          <div className="flex justify-between">
            <span className="text-sm">Total Employer Cost</span>
            <span className="font-semibold text-purple-600">
              {totalEmployerCost.toLocaleString()} SAR
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// EOS Calculator Card Component
// ============================================================================

interface EOSCalculatorCardProps {
  employee: Employee | null
}

function EOSCalculatorCard({ employee }: EOSCalculatorCardProps) {
  const [hireDate, setHireDate] = useState(employee?.hire_date || '')
  const [terminationDate, setTerminationDate] = useState(format(new Date(), 'yyyy-MM-dd'))
  const [basicSalary, setBasicSalary] = useState<number>(15000)
  const [terminationType, setTerminationType] = useState<TerminationType | ''>('')
  const [result, setResult] = useState<EOSCalculation | null>(null)

  const calculateMutation = useCalculateEOS()

  const handleCalculate = async () => {
    if (!hireDate) return

    try {
      const calculation = await calculateMutation.mutateAsync({
        hire_date: hireDate,
        termination_date: terminationDate || undefined,
        basic_salary_sar: basicSalary,
        termination_type: terminationType || undefined,
      })
      setResult(calculation)
    } catch {
      // Error handled by mutation
    }
  }

  // Update form when employee changes
  useState(() => {
    if (employee) {
      setHireDate(employee.hire_date)
    }
  })

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Calculator className="h-5 w-5 text-sage-600" />
          EOS Calculator
        </CardTitle>
        <CardDescription>
          Calculate End of Service benefits according to KSA labor law
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Inputs */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="hire_date">Hire Date</Label>
            <Input
              id="hire_date"
              type="date"
              value={hireDate}
              onChange={(e) => setHireDate(e.target.value)}
            />
          </div>
          <div>
            <Label htmlFor="termination_date">Termination Date</Label>
            <Input
              id="termination_date"
              type="date"
              value={terminationDate}
              onChange={(e) => setTerminationDate(e.target.value)}
            />
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div>
            <Label htmlFor="basic_salary">Basic Salary (SAR)</Label>
            <Input
              id="basic_salary"
              type="number"
              min={0}
              value={basicSalary}
              onChange={(e) => setBasicSalary(parseFloat(e.target.value) || 0)}
            />
          </div>
          <div>
            <Label htmlFor="termination_type">Termination Type</Label>
            <Select
              value={terminationType}
              onValueChange={(v) => setTerminationType(v as TerminationType)}
            >
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                {Object.entries(TERMINATION_TYPE_LABELS).map(([value, label]) => (
                  <SelectItem key={value} value={value}>
                    {label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <Button onClick={handleCalculate} disabled={calculateMutation.isPending || !hireDate}>
          {calculateMutation.isPending ? 'Calculating...' : 'Calculate EOS'}
        </Button>

        {/* Results */}
        {result && (
          <div className="space-y-3 rounded-lg bg-slate-50 p-4">
            <div className="flex items-center gap-2 text-sm font-medium">
              <BadgePercent className="h-4 w-4" />
              Calculation Results
            </div>

            <div className="grid grid-cols-2 gap-2 text-sm">
              <span className="text-muted-foreground">Years of Service:</span>
              <span className="font-medium">
                {result.years_of_service} years, {result.months_of_service} months
              </span>

              <span className="text-muted-foreground">Years 1-5 (0.5 mo/yr):</span>
              <span>{result.years_1_to_5_amount_sar.toLocaleString()} SAR</span>

              <span className="text-muted-foreground">Years 6+ (1.0 mo/yr):</span>
              <span>{result.years_6_plus_amount_sar.toLocaleString()} SAR</span>
            </div>

            <Separator />

            <div className="flex justify-between">
              <span>Gross EOS</span>
              <span className="font-medium">{result.gross_eos_sar.toLocaleString()} SAR</span>
            </div>

            {result.resignation_factor !== null && result.resignation_factor !== undefined && (
              <div className="flex justify-between text-sm">
                <span className="text-muted-foreground">
                  Resignation Factor ({(result.resignation_factor * 100).toFixed(0)}%)
                </span>
                <span className="text-amber-600">Applied</span>
              </div>
            )}

            <div className="flex justify-between text-lg font-semibold">
              <span>Final EOS</span>
              <span className="text-green-600">{result.final_eos_sar.toLocaleString()} SAR</span>
            </div>

            <p className="text-xs text-muted-foreground mt-2">{result.calculation_breakdown}</p>
          </div>
        )}

        {/* Formula Reference */}
        <div className="text-xs text-muted-foreground space-y-1 pt-2">
          <p className="font-medium">KSA Labor Law EOS Formula:</p>
          <p>• Years 1-5: {EOS_RATES.YEARS_1_TO_5} month per year of service</p>
          <p>• Years 6+: {EOS_RATES.YEARS_6_PLUS} month per year of service</p>
          <p className="font-medium mt-2">Resignation Factors:</p>
          <p>• &lt;2 years: {RESIGNATION_FACTORS.LESS_THAN_2_YEARS * 100}%</p>
          <p>• 2-5 years: {RESIGNATION_FACTORS.BETWEEN_2_AND_5_YEARS * 100}%</p>
          <p>• 5-10 years: {RESIGNATION_FACTORS.BETWEEN_5_AND_10_YEARS * 100}%</p>
          <p>• &gt;10 years: {RESIGNATION_FACTORS.MORE_THAN_10_YEARS * 100}%</p>
        </div>
      </CardContent>
    </Card>
  )
}

// ============================================================================
// Main Page Component
// ============================================================================

function SalariesPage() {
  const { selectedVersionId } = useBudgetVersion()
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null)

  // Queries
  const { data: employeesData } = useEmployees(selectedVersionId)
  const { data: summaryData } = useWorkforceSummary(selectedVersionId)
  const { data: eosSummaryData } = useEOSSummary(selectedVersionId)
  const { data: currentSalaryData } = useCurrentSalary(selectedEmployeeId || undefined)
  const { data: eosProvisionData } = useEOSProvision(selectedEmployeeId || undefined)

  // Find selected employee
  const selectedEmployee = useMemo(() => {
    if (!selectedEmployeeId || !employeesData) return null
    return employeesData.employees.find((e) => e.id === selectedEmployeeId) || null
  }, [selectedEmployeeId, employeesData])

  // Summary stats
  const stats = useMemo(() => {
    return {
      monthlyPayroll: summaryData?.total_monthly_payroll_sar || 0,
      gosiEmployer: summaryData?.total_gosi_employer_sar || 0,
      eosProvision: summaryData?.total_eos_provision_sar || 0,
      yearlyImpact: eosSummaryData?.year_over_year_change_sar || 0,
    }
  }, [summaryData, eosSummaryData])

  // Check if no version selected
  if (!selectedVersionId) {
    return (
      <PageContainer
        title="Salaries & End of Service"
        description="KSA labor law compliant salary management with EOS provisions"
      >
        <Card className="border-amber-200 bg-amber-50">
          <CardContent className="flex items-center gap-4 py-6">
            <AlertCircle className="h-8 w-8 text-amber-600" />
            <div>
              <p className="font-medium text-amber-800">No Budget Version Selected</p>
              <p className="text-sm text-amber-700">
                Please select a budget version from the header to view salaries.
              </p>
            </div>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  return (
    <PageContainer
      title="Salaries & End of Service"
      description="KSA labor law compliant salary management with EOS provisions"
      actions={
        <Button variant="outline" size="sm">
          <RefreshCw className="h-4 w-4 mr-2" />
          Calculate All EOS
        </Button>
      }
    >
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <Card>
            <CardHeader className="pb-2">
              <CardDescription>Total Payroll (Monthly)</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Banknote className="h-5 w-5 text-gold-600" />
                <span>{stats.monthlyPayroll.toLocaleString()}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">SAR/month • All local employees</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>GOSI (Employer)</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Calculator className="h-5 w-5 text-sage-600" />
                <span>{stats.gosiEmployer.toLocaleString()}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">SAR/month • 11.75% Saudi, 2% Expat</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>EOS Provision</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <Wallet className="h-5 w-5 text-text-secondary" />
                <span>{stats.eosProvision.toLocaleString()}</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">SAR • Total accrued liability</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardDescription>EOS Yearly Impact</CardDescription>
              <CardTitle className="text-2xl flex items-center gap-2">
                <TrendingUp className="h-5 w-5 text-terracotta-600" />
                <span
                  className={
                    stats.yearlyImpact > 0
                      ? 'text-red-600'
                      : stats.yearlyImpact < 0
                        ? 'text-green-600'
                        : ''
                  }
                >
                  {stats.yearlyImpact > 0 ? '+' : ''}
                  {stats.yearlyImpact.toLocaleString()}
                </span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-xs text-muted-foreground">SAR • Provision change YoY</p>
            </CardContent>
          </Card>
        </div>

        {/* Employee Selector */}
        <Card>
          <CardHeader className="py-3">
            <div className="flex items-center gap-2">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium">Select Employee</span>
            </div>
          </CardHeader>
          <CardContent className="py-3 pt-0">
            <div className="flex items-center gap-4">
              <div className="w-96">
                <Select
                  value={selectedEmployeeId || ''}
                  onValueChange={(v) => setSelectedEmployeeId(v || null)}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select an employee..." />
                  </SelectTrigger>
                  <SelectContent>
                    {employeesData?.employees.map((employee) => (
                      <SelectItem key={employee.id} value={employee.id}>
                        {employee.employee_code} - {employee.full_name} (
                        {EMPLOYEE_CATEGORY_LABELS[employee.category]})
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              {selectedEmployee && (
                <div className="flex items-center gap-2">
                  <Badge variant="outline">
                    {NATIONALITY_LABELS[selectedEmployee.nationality]}
                  </Badge>
                  <Badge variant="outline" className="flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    Hired: {format(new Date(selectedEmployee.hire_date), 'MMM yyyy')}
                  </Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Salary Breakdown */}
          <SalaryBreakdownCard employee={selectedEmployee} salary={currentSalaryData || null} />

          {/* EOS Calculator */}
          <EOSCalculatorCard employee={selectedEmployee} />
        </div>

        {/* Current EOS Provision */}
        {selectedEmployee && eosProvisionData && (
          <Card>
            <CardHeader>
              <CardTitle className="text-lg flex items-center gap-2">
                <Wallet className="h-5 w-5 text-text-secondary" />
                Current EOS Provision
              </CardTitle>
              <CardDescription>
                As of {format(new Date(eosProvisionData.as_of_date), 'MMMM d, yyyy')}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Years of Service</p>
                  <p className="text-lg font-semibold">
                    {eosProvisionData.years_of_service} years, {eosProvisionData.months_of_service}{' '}
                    months
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Base Salary</p>
                  <p className="text-lg font-semibold">
                    {eosProvisionData.base_salary_sar.toLocaleString()} SAR
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Years 1-5</p>
                  <p className="text-lg font-semibold">
                    {eosProvisionData.years_1_to_5_amount_sar.toLocaleString()} SAR
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Years 6+</p>
                  <p className="text-lg font-semibold">
                    {eosProvisionData.years_6_plus_amount_sar.toLocaleString()} SAR
                  </p>
                </div>
              </div>
              <Separator className="my-4" />
              <div className="flex justify-between items-center">
                <span className="text-lg">Total Provision</span>
                <span className="text-2xl font-bold text-green-600">
                  {eosProvisionData.provision_amount_sar.toLocaleString()} SAR
                </span>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </PageContainer>
  )
}
