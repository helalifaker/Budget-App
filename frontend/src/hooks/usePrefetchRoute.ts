import { useQueryClient } from '@tanstack/react-query'
import { useRouter } from '@tanstack/react-router'
import { useCallback } from 'react'
import { enrollmentKeys } from './api/useEnrollment'
import { dhgKeys } from './api/useDHG'
import { analysisKeys } from './api/useAnalysis'
import { budgetVersionKeys } from './api/useBudgetVersions'
import { consolidationKeys } from './api/useConsolidation'

/**
 * Hook for prefetching route data on navigation hover
 *
 * Prefetches both route data (via TanStack Router) and query data (via React Query)
 * to provide instant navigation experience
 *
 * @example
 * const { prefetchRoute } = usePrefetchRoute()
 *
 * <Link
 *   to="/planning/enrollment"
 *   onMouseEnter={() => prefetchRoute('/planning/enrollment')}
 * >
 *   Enrollment
 * </Link>
 */
export function usePrefetchRoute() {
  const queryClient = useQueryClient()
  const router = useRouter()

  const prefetchRoute = useCallback(
    (to: string, budgetVersionId?: string) => {
      // Prefetch route component and loader data
      router.preloadRoute({ to })

      // Prefetch specific queries based on route
      // Only prefetch if we have the required context (budget version ID)
      if (!budgetVersionId) {
        return
      }

      // Planning routes
      if (to.includes('/planning/enrollment')) {
        queryClient.prefetchQuery({
          queryKey: enrollmentKeys.byVersion(budgetVersionId),
        })
      } else if (to.includes('/planning/dhg')) {
        queryClient.prefetchQuery({
          queryKey: dhgKeys.subjectHours(budgetVersionId),
        })
        queryClient.prefetchQuery({
          queryKey: dhgKeys.teacherFTE(budgetVersionId),
        })
      } else if (to.includes('/planning/classes')) {
        // Class structure would use class structure keys if available
        // For now, we'll skip prefetching
      } else if (to.includes('/planning/revenue')) {
        // Revenue planning - would prefetch revenue data
      } else if (to.includes('/planning/costs')) {
        // Cost planning - would prefetch cost data
      } else if (to.includes('/planning/capex')) {
        // CapEx planning - would prefetch capex data
      }

      // Consolidation routes
      else if (to.includes('/consolidation/budget')) {
        queryClient.prefetchQuery({
          queryKey: consolidationKeys.summary(budgetVersionId),
        })
      } else if (to.includes('/consolidation/statements')) {
        queryClient.prefetchQuery({
          queryKey: consolidationKeys.statements(budgetVersionId, 'PCG'),
        })
      }

      // Analysis routes
      else if (to.includes('/analysis/kpis')) {
        queryClient.prefetchQuery({
          queryKey: analysisKeys.kpis(budgetVersionId),
        })
      } else if (to.includes('/analysis/dashboards')) {
        queryClient.prefetchQuery({
          queryKey: analysisKeys.dashboard(budgetVersionId),
        })
      } else if (to.includes('/analysis/variance')) {
        // Variance analysis - would prefetch variance data
      }

      // Configuration routes
      else if (to.includes('/configuration/versions')) {
        queryClient.prefetchQuery({
          queryKey: budgetVersionKeys.lists(),
        })
      }

      // Dashboard
      else if (to === '/dashboard' || to.includes('/dashboard')) {
        queryClient.prefetchQuery({
          queryKey: analysisKeys.dashboard(budgetVersionId),
        })
        queryClient.prefetchQuery({
          queryKey: analysisKeys.activity(),
        })
      }
    },
    [queryClient, router]
  )

  return { prefetchRoute }
}
