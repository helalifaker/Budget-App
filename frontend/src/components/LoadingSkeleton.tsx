/**
 * Loading Skeleton Components
 *
 * Provides various skeleton loading states for lazy-loaded components:
 * - GridSkeleton: For AG Grid data tables
 * - ChartSkeleton: For Recharts visualizations
 * - DashboardSkeleton: For KPI cards and dashboards
 * - FormSkeleton: For form sections
 *
 * These skeletons improve perceived performance by showing a loading state
 * while heavy components (AG Grid, Recharts) are being lazy loaded.
 */

/**
 * Skeleton for AG Grid data tables
 * Used when lazy loading planning/consolidation grids
 */
export function GridSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {/* Grid header */}
      <div className="h-12 bg-gray-200 dark:bg-gray-700 rounded" />

      {/* Grid rows */}
      <div className="space-y-2">
        {[...Array(8)].map((_, i) => (
          <div key={i} className="h-16 bg-gray-100 dark:bg-gray-800 rounded" />
        ))}
      </div>

      {/* Grid footer (pagination) */}
      <div className="flex justify-between items-center">
        <div className="h-8 w-32 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="h-8 w-48 bg-gray-200 dark:bg-gray-700 rounded" />
      </div>
    </div>
  )
}

/**
 * Skeleton for Recharts visualizations
 * Used when lazy loading analysis/dashboard charts
 */
export function ChartSkeleton() {
  return (
    <div className="animate-pulse">
      <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded flex items-center justify-center">
        <span className="text-gray-400 dark:text-gray-500">Chargement du graphique...</span>
      </div>
    </div>
  )
}

/**
 * Skeleton for dashboard KPI cards
 * Used on main dashboard and analysis pages
 */
export function DashboardSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {[...Array(4)].map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="h-32 bg-gray-200 dark:bg-gray-700 rounded p-4 space-y-3">
            {/* KPI title */}
            <div className="h-4 w-24 bg-gray-300 dark:bg-gray-600 rounded" />

            {/* KPI value */}
            <div className="h-8 w-32 bg-gray-300 dark:bg-gray-600 rounded" />

            {/* KPI change indicator */}
            <div className="h-3 w-16 bg-gray-300 dark:bg-gray-600 rounded" />
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * Skeleton for form sections
 * Used when lazy loading configuration forms
 */
export function FormSkeleton() {
  return (
    <div className="animate-pulse space-y-6">
      {/* Form fields */}
      {[...Array(4)].map((_, i) => (
        <div key={i} className="space-y-2">
          {/* Label */}
          <div className="h-4 w-32 bg-gray-200 dark:bg-gray-700 rounded" />

          {/* Input */}
          <div className="h-10 bg-gray-100 dark:bg-gray-800 rounded" />
        </div>
      ))}

      {/* Form actions */}
      <div className="flex gap-3 justify-end">
        <div className="h-10 w-24 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="h-10 w-24 bg-gray-300 dark:bg-gray-600 rounded" />
      </div>
    </div>
  )
}

/**
 * Skeleton for page header
 * Used across all lazy-loaded pages
 */
export function PageHeaderSkeleton() {
  return (
    <div className="animate-pulse space-y-4 mb-6">
      {/* Page title */}
      <div className="h-8 w-64 bg-gray-200 dark:bg-gray-700 rounded" />

      {/* Page description */}
      <div className="h-4 w-96 bg-gray-100 dark:bg-gray-800 rounded" />

      {/* Action buttons */}
      <div className="flex gap-3">
        <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded" />
        <div className="h-10 w-32 bg-gray-200 dark:bg-gray-700 rounded" />
      </div>
    </div>
  )
}

/**
 * Skeleton for table with filters
 * Combines filter bar and data grid
 */
export function TableWithFiltersSkeleton() {
  return (
    <div className="animate-pulse space-y-4">
      {/* Filter bar */}
      <div className="flex gap-3">
        {[...Array(3)].map((_, i) => (
          <div key={i} className="h-10 w-48 bg-gray-200 dark:bg-gray-700 rounded" />
        ))}
      </div>

      {/* Grid */}
      <GridSkeleton />
    </div>
  )
}

/**
 * Skeleton for cards grid layout
 * Used on strategic planning and consolidation pages
 */
export function CardsGridSkeleton() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {[...Array(6)].map((_, i) => (
        <div key={i} className="animate-pulse">
          <div className="h-48 bg-gray-200 dark:bg-gray-700 rounded p-6 space-y-4">
            {/* Card title */}
            <div className="h-6 w-48 bg-gray-300 dark:bg-gray-600 rounded" />

            {/* Card content lines */}
            <div className="space-y-3">
              <div className="h-4 w-full bg-gray-100 dark:bg-gray-800 rounded" />
              <div className="h-4 w-5/6 bg-gray-100 dark:bg-gray-800 rounded" />
              <div className="h-4 w-4/6 bg-gray-100 dark:bg-gray-800 rounded" />
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}

/**
 * Generic loading spinner
 * For small components or inline loading states
 */
export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return (
    <div className="flex items-center justify-center">
      <div
        className={`animate-spin rounded-full border-b-2 border-primary ${sizeClasses[size]}`}
        role="status"
        aria-label="Chargement..."
      >
        <span className="sr-only">Chargement...</span>
      </div>
    </div>
  )
}

/**
 * Full page loading state
 * Used for route-level lazy loading
 */
export function PageLoadingSkeleton() {
  return (
    <div className="container mx-auto p-6 space-y-6">
      <PageHeaderSkeleton />
      <DashboardSkeleton />
      <GridSkeleton />
    </div>
  )
}
