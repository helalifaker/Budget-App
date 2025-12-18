/**
 * Enrollment Validation Page - /students/validation
 *
 * Validates enrollment data before it's used in class structure and subsequent calculations.
 * Shows validation status, warnings, and errors that need to be addressed.
 *
 * Features:
 * - Data completeness check
 * - Capacity warnings
 * - Distribution validation
 * - Cross-module dependency check
 */

import { createFileRoute } from '@tanstack/react-router'
import { requireAuth } from '@/lib/auth-guard'
import { useMemo } from 'react'
import { PageContainer } from '@/components/layout/PageContainer'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Progress } from '@/components/ui/progress'
import {
  CheckCircle2,
  AlertTriangle,
  AlertCircle,
  ArrowRight,
  RefreshCw,
  FileCheck,
  Users,
  BarChart3,
  ClipboardCheck,
} from 'lucide-react'
import { useEnrollmentWithDistribution } from '@/hooks/api/useEnrollment'
import { useClassSizeParams, useLevels } from '@/hooks/api/useConfiguration'
import { useEnrollmentProjectionConfig } from '@/hooks/api/useEnrollmentProjection'
import { useVersion } from '@/contexts/VersionContext'
import { Link } from '@tanstack/react-router'
import { cn } from '@/lib/utils'

export const Route = createFileRoute('/_authenticated/enrollment/validation')({
  beforeLoad: requireAuth,
  component: EnrollmentValidationPage,
})

// Validation status types
type ValidationStatus = 'success' | 'warning' | 'error' | 'pending'

interface ValidationCheck {
  id: string
  title: string
  description: string
  status: ValidationStatus
  details?: string
  action?: {
    label: string
    href: string
  }
}

function EnrollmentValidationPage() {
  const { selectedVersionId } = useVersion()

  // Data queries
  const {
    data: enrollmentData,
    isLoading: enrollmentLoading,
    error: enrollmentError,
    refetch: refetchEnrollment,
  } = useEnrollmentWithDistribution(selectedVersionId)
  const { data: classSizeParams, isLoading: paramsLoading } = useClassSizeParams(selectedVersionId)
  const { data: levels } = useLevels()
  const { data: projectionConfig } = useEnrollmentProjectionConfig(selectedVersionId)

  // Calculate validation checks
  const validationChecks = useMemo((): ValidationCheck[] => {
    if (!selectedVersionId) {
      return []
    }

    const checks: ValidationCheck[] = []

    // Extract the breakdown array from enrollment data
    const breakdown = enrollmentData?.breakdown ?? []

    // 1. Enrollment Data Completeness
    const totalLevels = levels?.length ?? 0
    const enrolledLevels = breakdown.filter((e) => e.total_students > 0).length
    const completenessPercent = totalLevels > 0 ? (enrolledLevels / totalLevels) * 100 : 0

    checks.push({
      id: 'enrollment-completeness',
      title: 'Enrollment Data Completeness',
      description: `${enrolledLevels} of ${totalLevels} levels have enrollment data`,
      status:
        completenessPercent === 100 ? 'success' : completenessPercent > 50 ? 'warning' : 'error',
      details:
        completenessPercent < 100
          ? `Missing data for ${totalLevels - enrolledLevels} levels`
          : 'All levels have enrollment data',
      action:
        completenessPercent < 100
          ? { label: 'Complete Enrollment', href: '/students/planning' }
          : undefined,
    })

    // 2. Class Size Parameters Configuration
    const configuredParams = classSizeParams?.length ?? 0
    const paramsPercent = totalLevels > 0 ? (configuredParams / totalLevels) * 100 : 0

    checks.push({
      id: 'class-size-params',
      title: 'Class Size Parameters',
      description: `${configuredParams} of ${totalLevels} levels have size parameters`,
      status: paramsPercent === 100 ? 'success' : paramsPercent > 50 ? 'warning' : 'error',
      details:
        paramsPercent < 100
          ? `Configure class sizes for ${totalLevels - configuredParams} more levels`
          : 'All levels have class size parameters',
      action:
        paramsPercent < 100 ? { label: 'Configure Sizes', href: '/students/settings' } : undefined,
    })

    // 3. Capacity Check
    const SCHOOL_CAPACITY = projectionConfig?.school_max_capacity ?? 1850
    const totalStudents = enrollmentData?.summary?.total_students ?? 0
    const capacityPercent = (totalStudents / SCHOOL_CAPACITY) * 100
    const isOverCapacity = capacityPercent > 100

    checks.push({
      id: 'capacity-check',
      title: 'School Capacity',
      description: `${totalStudents} of ${SCHOOL_CAPACITY} students (${Math.round(capacityPercent)}%)`,
      status: isOverCapacity ? 'error' : capacityPercent > 90 ? 'warning' : 'success',
      details: isOverCapacity
        ? `Over capacity by ${totalStudents - SCHOOL_CAPACITY} students`
        : capacityPercent > 90
          ? 'Approaching maximum capacity'
          : 'Within normal capacity',
    })

    // 4. Nationality Distribution Validation
    // Check if french + saudi + other counts sum to total_students for each level
    const levelsWithDistribution = breakdown.filter((e) => {
      const distTotal = (e.french_count ?? 0) + (e.saudi_count ?? 0) + (e.other_count ?? 0)
      return e.total_students > 0 && distTotal === e.total_students
    }).length
    const levelsWithEnrollment = breakdown.filter((e) => e.total_students > 0).length
    const distPercent =
      levelsWithEnrollment > 0 ? (levelsWithDistribution / levelsWithEnrollment) * 100 : 100

    checks.push({
      id: 'distribution-validation',
      title: 'Nationality Distribution',
      description: `${levelsWithDistribution} of ${levelsWithEnrollment} levels have complete distribution`,
      status: distPercent === 100 ? 'success' : distPercent > 50 ? 'warning' : 'error',
      details:
        distPercent < 100
          ? `${levelsWithEnrollment - levelsWithDistribution} levels have mismatched distribution totals`
          : 'All distributions match enrollment totals',
      action:
        distPercent < 100 ? { label: 'Fix Distribution', href: '/students/planning' } : undefined,
    })

    // 5. Ready for Class Structure
    const isReadyForClassStructure =
      completenessPercent > 50 && paramsPercent === 100 && !isOverCapacity

    checks.push({
      id: 'class-structure-ready',
      title: 'Class Structure Ready',
      description: isReadyForClassStructure
        ? 'Enrollment data is ready for class structure calculation'
        : 'Complete prerequisites before generating class structure',
      status: isReadyForClassStructure ? 'success' : 'pending',
      details: isReadyForClassStructure
        ? 'You can proceed to Class Structure'
        : 'Complete enrollment and configure class sizes first',
      action: isReadyForClassStructure
        ? { label: 'Go to Class Structure', href: '/students/class-structure' }
        : undefined,
    })

    return checks
  }, [selectedVersionId, enrollmentData, classSizeParams, levels, projectionConfig])

  // Calculate overall status
  const overallStatus = useMemo(() => {
    if (validationChecks.length === 0) return 'pending'
    if (validationChecks.some((c) => c.status === 'error')) return 'error'
    if (validationChecks.some((c) => c.status === 'warning')) return 'warning'
    if (validationChecks.every((c) => c.status === 'success')) return 'success'
    return 'pending'
  }, [validationChecks])

  const successCount = validationChecks.filter((c) => c.status === 'success').length
  const progressPercent = (successCount / Math.max(validationChecks.length, 1)) * 100

  const isLoading = enrollmentLoading || paramsLoading

  const statusConfig = {
    success: {
      icon: CheckCircle2,
      color: 'text-success-600',
      bg: 'bg-success-50',
      border: 'border-success-200',
      label: 'All Checks Passed',
    },
    warning: {
      icon: AlertTriangle,
      color: 'text-warning-600',
      bg: 'bg-warning-50',
      border: 'border-warning-200',
      label: 'Warnings Found',
    },
    error: {
      icon: AlertCircle,
      color: 'text-error-600',
      bg: 'bg-error-50',
      border: 'border-error-200',
      label: 'Errors Found',
    },
    pending: {
      icon: ClipboardCheck,
      color: 'text-text-muted',
      bg: 'bg-subtle',
      border: 'border-border-light',
      label: 'Pending',
    },
  }

  return (
    <PageContainer
      title="Enrollment Validation"
      description="Review enrollment data quality and completeness before proceeding to class structure"
    >
      <div className="space-y-6">
        {/* Version Selection Warning */}
        {!selectedVersionId && (
          <div className="flex items-center gap-2 p-4 bg-subtle border border-border-light rounded-lg">
            <AlertCircle className="h-4 w-4 text-sand-600" />
            <p className="text-sm text-sand-800">
              Please select a budget version to validate enrollment data.
            </p>
          </div>
        )}

        {selectedVersionId && (
          <>
            {/* Overall Status Card */}
            <Card
              className={cn(statusConfig[overallStatus].bg, statusConfig[overallStatus].border)}
            >
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {(() => {
                      const StatusIcon = statusConfig[overallStatus].icon
                      return (
                        <div
                          className={cn(
                            'w-12 h-12 rounded-full flex items-center justify-center',
                            statusConfig[overallStatus].bg
                          )}
                        >
                          <StatusIcon
                            className={cn('h-6 w-6', statusConfig[overallStatus].color)}
                          />
                        </div>
                      )
                    })()}
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        Validation Status
                        <Badge
                          variant={
                            overallStatus === 'success'
                              ? 'success'
                              : overallStatus === 'error'
                                ? 'destructive'
                                : 'secondary'
                          }
                        >
                          {statusConfig[overallStatus].label}
                        </Badge>
                      </CardTitle>
                      <CardDescription>
                        {successCount} of {validationChecks.length} checks passed
                      </CardDescription>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => refetchEnrollment()}
                    disabled={isLoading}
                  >
                    <RefreshCw className={cn('h-4 w-4 mr-2', isLoading && 'animate-spin')} />
                    Refresh
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <Progress value={progressPercent} className="h-2" />
              </CardContent>
            </Card>

            {/* Error State */}
            {enrollmentError && (
              <div className="flex items-center gap-2 p-4 bg-error-50 border border-error-200 rounded-lg">
                <AlertCircle className="h-4 w-4 text-error-600" />
                <p className="text-sm text-error-800">
                  Failed to load enrollment data. Please try again.
                </p>
              </div>
            )}

            {/* Validation Checks Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {validationChecks.map((check) => {
                const config = statusConfig[check.status]
                const CheckIcon = config.icon

                return (
                  <Card
                    key={check.id}
                    className={cn('transition-all duration-200', config.border, 'hover:shadow-sm')}
                  >
                    <CardHeader className="pb-2">
                      <div className="flex items-start justify-between">
                        <div
                          className={cn(
                            'w-10 h-10 rounded-lg flex items-center justify-center',
                            config.bg
                          )}
                        >
                          <CheckIcon className={cn('h-5 w-5', config.color)} />
                        </div>
                        <Badge
                          variant={
                            check.status === 'success'
                              ? 'success'
                              : check.status === 'error'
                                ? 'destructive'
                                : check.status === 'warning'
                                  ? 'warning'
                                  : 'secondary'
                          }
                        >
                          {check.status}
                        </Badge>
                      </div>
                      <CardTitle className="text-base mt-2">{check.title}</CardTitle>
                      <CardDescription>{check.description}</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {check.details && (
                        <p className="text-sm text-text-secondary mb-3">{check.details}</p>
                      )}
                      {check.action && (
                        <Button asChild variant="outline" size="sm" className="w-full gap-2">
                          <Link to={check.action.href}>
                            {check.action.label}
                            <ArrowRight className="h-4 w-4" />
                          </Link>
                        </Button>
                      )}
                    </CardContent>
                  </Card>
                )
              })}
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-text-secondary flex items-center gap-2">
                    <Users className="h-4 w-4" />
                    Total Students
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {enrollmentData?.summary?.total_students ?? 0}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-text-secondary flex items-center gap-2">
                    <BarChart3 className="h-4 w-4" />
                    Levels Configured
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {enrollmentData?.breakdown?.filter((e) => e.total_students > 0).length ?? 0} /{' '}
                    {levels?.length ?? 0}
                  </p>
                </CardContent>
              </Card>

              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="text-sm font-medium text-text-secondary flex items-center gap-2">
                    <FileCheck className="h-4 w-4" />
                    Parameters Set
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-2xl font-bold">
                    {classSizeParams?.length ?? 0} / {levels?.length ?? 0}
                  </p>
                </CardContent>
              </Card>
            </div>
          </>
        )}
      </div>
    </PageContainer>
  )
}
