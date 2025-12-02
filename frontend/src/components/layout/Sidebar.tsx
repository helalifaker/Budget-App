import { Link } from '@tanstack/react-router'
import { usePrefetchRoute } from '@/hooks/usePrefetchRoute'
import { useBudgetVersions } from '@/hooks/api/useBudgetVersions'

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: '📊' },
  {
    name: 'Configuration',
    icon: '⚙️',
    children: [
      { name: 'Budget Versions', href: '/configuration/versions' },
      { name: 'Class Sizes', href: '/configuration/class-sizes' },
      { name: 'Subject Hours', href: '/configuration/subject-hours' },
      { name: 'Teacher Costs', href: '/configuration/teacher-costs' },
      { name: 'Fee Structure', href: '/configuration/fees' },
    ],
  },
  {
    name: 'Planning',
    icon: '📝',
    children: [
      { name: 'Enrollment', href: '/planning/enrollment' },
      { name: 'Class Structure', href: '/planning/classes' },
      { name: 'DHG Workforce', href: '/planning/dhg' },
      { name: 'Revenue', href: '/planning/revenue' },
      { name: 'Costs', href: '/planning/costs' },
      { name: 'CapEx', href: '/planning/capex' },
    ],
  },
  {
    name: 'Consolidation',
    icon: '💰',
    children: [
      { name: 'Budget Review', href: '/consolidation/budget' },
      { name: 'Financial Statements', href: '/consolidation/statements' },
    ],
  },
  {
    name: 'Analysis',
    icon: '📈',
    children: [
      { name: 'KPIs', href: '/analysis/kpis' },
      { name: 'Dashboards', href: '/analysis/dashboards' },
      { name: 'Budget vs Actual', href: '/analysis/variance' },
    ],
  },
  {
    name: 'Strategic Planning',
    icon: '🎯',
    href: '/strategic',
  },
]

export function Sidebar() {
  const { prefetchRoute } = usePrefetchRoute()
  const { data: budgetVersionsData } = useBudgetVersions()

  // Get the currently active budget version ID (first working or submitted version)
  const activeBudgetVersionId = budgetVersionsData?.items?.find(
    (v) => v.status === 'WORKING' || v.status === 'SUBMITTED'
  )?.id

  return (
    <div className="w-64 bg-white border-r border-gray-200">
      <div className="flex flex-col h-full">
        <div className="flex items-center h-16 px-6 border-b border-gray-200">
          <h1 className="text-xl font-bold text-gray-900">EFIR Budget</h1>
        </div>

        <nav className="flex-1 px-4 py-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => (
            <div key={item.name}>
              {item.href ? (
                <Link
                  to={item.href}
                  className="flex items-center px-4 py-2 text-sm font-medium text-gray-700 rounded-md hover:bg-gray-100"
                  activeProps={{
                    className: 'bg-gray-100 text-primary',
                  }}
                  onMouseEnter={() => prefetchRoute(item.href, activeBudgetVersionId)}
                >
                  <span className="mr-3">{item.icon}</span>
                  {item.name}
                </Link>
              ) : (
                <>
                  <div className="flex items-center px-4 py-2 text-sm font-medium text-gray-500">
                    <span className="mr-3">{item.icon}</span>
                    {item.name}
                  </div>
                  {item.children && (
                    <div className="ml-8 space-y-1">
                      {item.children.map((child) => (
                        <Link
                          key={child.name}
                          to={child.href}
                          className="block px-4 py-2 text-sm text-gray-600 rounded-md hover:bg-gray-100"
                          activeProps={{
                            className: 'bg-gray-100 text-primary font-medium',
                          }}
                          onMouseEnter={() => prefetchRoute(child.href, activeBudgetVersionId)}
                        >
                          {child.name}
                        </Link>
                      ))}
                    </div>
                  )}
                </>
              )}
            </div>
          ))}
        </nav>
      </div>
    </div>
  )
}
