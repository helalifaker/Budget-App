/**
 * Consolidation Module Dashboard - /consolidation
 *
 * Overview of budget consolidation and financial output activities.
 */

import { createFileRoute, Link } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { SummaryCard } from '@/components/SummaryCard'
import { useVersion } from '@/contexts/VersionContext'
import { useConsolidationValidation } from '@/hooks/api/useConsolidation'
import { FileText, CheckCircle, AlertCircle, Download, ArrowRight, Layers } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/consolidation/')({
  component: ConsolidationIndexPage,
})

function ConsolidationIndexPage() {
  const { selectedVersionId } = useVersion()
  const { data: validation } = useConsolidationValidation(selectedVersionId!)

  // Calculate validation status based on missing modules and warnings
  const missingModules = validation?.missing_modules?.length || 0
  const warnings = validation?.warnings?.length || 0
  const totalIssues = missingModules + warnings
  const isComplete = validation?.is_complete ?? false
  const readinessPercent = isComplete ? 100 : Math.max(0, 100 - totalIssues * 20)

  // For summary cards - estimate based on module_counts
  const moduleCount = validation?.module_counts ? Object.keys(validation.module_counts).length : 0
  const completedModules = moduleCount - missingModules
  const totalChecks = moduleCount || 5 // Default to 5 modules
  const completedChecks = isComplete ? totalChecks : Math.max(0, completedModules)

  const workflowItems = [
    {
      title: 'Pre-Close Checklist',
      description: 'Validate data completeness before consolidation',
      href: '/consolidation/checklist',
      icon: <CheckCircle className="w-5 h-5" />,
      status:
        readinessPercent === 100 ? 'complete' : readinessPercent > 0 ? 'in_progress' : 'pending',
    },
    {
      title: 'Budget Rollup',
      description: 'Consolidate all budget inputs',
      href: '/consolidation/rollup',
      icon: <Layers className="w-5 h-5" />,
      status: 'pending',
    },
    {
      title: 'Financial Statements',
      description: 'P&L, Balance Sheet, Cash Flow',
      href: '/consolidation/statements',
      icon: <FileText className="w-5 h-5" />,
      status: 'pending',
    },
    {
      title: 'Reports & Exports',
      description: 'Generate and download reports',
      href: '/consolidation/exports',
      icon: <Download className="w-5 h-5" />,
      status: 'pending',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {selectedVersionId ? (
        <>
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <SummaryCard
              title="Readiness"
              value={`${readinessPercent}%`}
              subtitle="Checklist complete"
              icon={<CheckCircle className="w-5 h-5" />}
              valueClassName={readinessPercent === 100 ? 'text-green-600' : 'text-amber-600'}
            />
            <SummaryCard
              title="Checks Passed"
              value={`${completedChecks}/${totalChecks}`}
              subtitle="Pre-close validations"
              icon={<CheckCircle className="w-5 h-5" />}
            />
            <SummaryCard
              title="Issues"
              value={`${totalChecks - completedChecks}`}
              subtitle="Items requiring attention"
              icon={<AlertCircle className="w-5 h-5" />}
              valueClassName={totalChecks - completedChecks > 0 ? 'text-red-600' : 'text-green-600'}
            />
            <SummaryCard
              title="Reports"
              value="3"
              subtitle="Available formats"
              icon={<FileText className="w-5 h-5" />}
            />
          </div>

          {/* Workflow Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {workflowItems.map((item) => (
              <Link key={item.href} to={item.href}>
                <Card className="hover:shadow-md transition-shadow cursor-pointer h-full">
                  <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-blue-lighter rounded-lg text-blue">{item.icon}</div>
                      <CardTitle className="text-lg">{item.title}</CardTitle>
                    </div>
                    <ArrowRight className="w-5 h-5 text-gray-400" />
                  </CardHeader>
                  <CardContent>
                    <p className="text-sm text-gray-600">{item.description}</p>
                    <div className="mt-3">
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${
                          item.status === 'complete'
                            ? 'bg-green-100 text-green-800'
                            : item.status === 'in_progress'
                              ? 'bg-amber-100 text-amber-800'
                              : 'bg-gray-100 text-gray-600'
                        }`}
                      >
                        {item.status === 'complete'
                          ? 'Complete'
                          : item.status === 'in_progress'
                            ? 'In Progress'
                            : 'Not Started'}
                      </span>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>

          {/* Quick Info */}
          <Card>
            <CardHeader>
              <CardTitle>Consolidation Overview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Process Flow</h4>
                  <p className="text-gray-600">
                    1. Complete all planning modules (Enrollment → Workforce → Revenue → Costs →
                    Investments)
                    <br />
                    2. Run pre-close checklist to validate data completeness
                    <br />
                    3. Execute budget rollup to consolidate all inputs
                    <br />
                    4. Generate financial statements and reports
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Statement Formats</h4>
                  <p className="text-gray-600">
                    Financial statements are available in PCG (French accounting standards) and IFRS
                    formats. Both can be generated for the same budget version.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a budget version to view consolidation
        </div>
      )}
    </div>
  )
}
