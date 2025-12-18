/**
 * Projects Page - /investments/projects
 *
 * Manages major project budgeting and tracking.
 */

import { createFileRoute } from '@tanstack/react-router'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { useVersion } from '@/contexts/VersionContext'
import { Plus, Download, FolderKanban, Calendar, DollarSign, CheckCircle } from 'lucide-react'

export const Route = createFileRoute('/_authenticated/investments/projects')({
  component: ProjectsPage,
})

function ProjectsPage() {
  const { selectedVersionId } = useVersion()

  const projectTypes = [
    {
      title: 'Construction',
      icon: <FolderKanban className="w-5 h-5" />,
      description: 'Building and facility projects',
    },
    {
      title: 'Renovation',
      icon: <Calendar className="w-5 h-5" />,
      description: 'Improvement and upgrade projects',
    },
    {
      title: 'Technology',
      icon: <DollarSign className="w-5 h-5" />,
      description: 'IT infrastructure projects',
    },
    {
      title: 'Equipment',
      icon: <CheckCircle className="w-5 h-5" />,
      description: 'Major equipment purchases',
    },
  ]

  return (
    <div className="p-6 space-y-6">
      {/* Page Actions */}
      <div className="flex items-center justify-end gap-3">
        <Button disabled={!selectedVersionId}>
          <Plus className="w-4 h-4 mr-2" />
          New Project
        </Button>
        <Button variant="outline">
          <Download className="w-4 h-4 mr-2" />
          Export
        </Button>
      </div>

      {/* Content */}
      {selectedVersionId ? (
        <>
          {/* Project Types */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {projectTypes.map((project) => (
              <Card key={project.title}>
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium">{project.title}</CardTitle>
                  <div className="p-2 bg-teal-lighter rounded-lg text-teal">{project.icon}</div>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-gray-600">{project.description}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Placeholder Content */}
          <Card>
            <CardHeader>
              <CardTitle>Project Budgets</CardTitle>
              <p className="text-sm text-gray-600">
                Plan and track major capital projects with multi-year budgets.
              </p>
            </CardHeader>
            <CardContent>
              <div className="text-center py-12 text-gray-500">
                <FolderKanban className="w-12 h-12 mx-auto mb-4 text-gray-300" />
                <p className="text-lg font-medium mb-2">Project Planning</p>
                <p className="text-sm">This page will display project budgets once created.</p>
              </div>
            </CardContent>
          </Card>

          {/* Info Card */}
          <Card>
            <CardHeader>
              <CardTitle>Project Budget Guide</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                <div>
                  <h4 className="font-medium mb-2">Multi-Year Projects</h4>
                  <p className="text-gray-600">
                    For projects spanning multiple fiscal years, create separate budget allocations
                    for each year with clear milestones.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Contingency</h4>
                  <p className="text-gray-600">
                    Include 10-15% contingency for construction projects. Technology projects may
                    need higher contingency (15-20%).
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Approval Workflow</h4>
                  <p className="text-gray-600">
                    Large projects require board approval. Document business case, ROI analysis, and
                    funding sources.
                  </p>
                </div>
                <div>
                  <h4 className="font-medium mb-2">Tracking</h4>
                  <p className="text-gray-600">
                    Track actual vs budgeted spending monthly. Flag variances over 10% for
                    management review.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <div className="text-center py-12 text-text-secondary">
          Please select a version to view project planning
        </div>
      )}
    </div>
  )
}
