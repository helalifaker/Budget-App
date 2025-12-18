import { useQueryClient } from '@tanstack/react-query'
import { useRouter } from '@tanstack/react-router'
import { useCallback } from 'react'
import { enrollmentKeys } from '@/hooks/api/useEnrollment'
import { dhgKeys } from '@/hooks/api/useDHG'
import { analysisKeys } from '@/hooks/api/useAnalysis'
import { versionKeys } from '@/hooks/api/useVersions'
import { consolidationKeys } from '@/hooks/api/useConsolidation'
import { analysisApi } from '@/services/analysis'
import { enrollmentApi } from '@/services/enrollment'
import { dhgApi } from '@/services/dhg'
import { consolidationService } from '@/services/consolidation'
import { versionsApi } from '@/services/versions'

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
    (to: string, versionId?: string) => {
      // Prefetch route component and loader data
      router.preloadRoute({ to })

      // Prefetch specific queries based on route
      // Only prefetch if we have the required context (budget version ID)
      if (!versionId) {
        return
      }

      // Students routes (enrollment module)
      if (to.includes('/students/planning') || to.includes('/planning/enrollment')) {
        queryClient.prefetchQuery({
          queryKey: enrollmentKeys.byVersion(versionId),
          queryFn: () => enrollmentApi.getAll(versionId),
        })
      } else if (to.includes('/planning/dhg')) {
        queryClient.prefetchQuery({
          queryKey: dhgKeys.subjectHours(versionId),
          queryFn: () => dhgApi.getSubjectHours(versionId),
        })
        queryClient.prefetchQuery({
          queryKey: dhgKeys.teacherRequirements(versionId),
          queryFn: () => dhgApi.getTeacherRequirements(versionId),
        })
      } else if (to.includes('/students/class-structure') || to.includes('/planning/classes')) {
        // Class structure would use class structure keys if available
        // For now, we'll skip prefetching
      } else if (to.includes('/finance/revenue') || to.includes('/planning/revenue')) {
        // Revenue planning - would prefetch revenue data
      } else if (to.includes('/finance/costs') || to.includes('/planning/costs')) {
        // Cost planning - would prefetch cost data
      } else if (to.includes('/finance/capex') || to.includes('/planning/capex')) {
        // CapEx planning - would prefetch capex data
      }

      // Finance routes (new module structure)
      else if (to.includes('/finance/consolidation') || to.includes('/consolidation/budget')) {
        queryClient.prefetchQuery({
          queryKey: consolidationKeys.summary(versionId),
          queryFn: () => consolidationService.getStatus(versionId),
        })
      } else if (to.includes('/finance/statements') || to.includes('/consolidation/statements')) {
        queryClient.prefetchQuery({
          queryKey: consolidationKeys.statement(versionId, 'INCOME', 'PCG', 'ANNUAL'),
          queryFn: () => consolidationService.getStatement(versionId, 'INCOME', 'PCG', 'ANNUAL'),
        })
      }

      // Insights routes (analysis module)
      else if (to.includes('/insights/kpis')) {
        queryClient.prefetchQuery({
          queryKey: analysisKeys.kpis(versionId),
          queryFn: () => analysisApi.getKPIs(versionId),
        })
      } else if (to.includes('/insights/dashboards')) {
        queryClient.prefetchQuery({
          queryKey: analysisKeys.dashboard(versionId),
          queryFn: () => analysisApi.getDashboardSummary(versionId),
        })
      } else if (to.includes('/insights/variance')) {
        // Variance analysis - would prefetch variance data
      }

      // Settings routes (configuration module)
      else if (to.includes('/settings/versions')) {
        queryClient.prefetchQuery({
          queryKey: versionKeys.lists(),
          queryFn: () => versionsApi.getAll(),
        })
      }

      // Dashboard
      else if (to === '/dashboard' || to.includes('/dashboard')) {
        queryClient.prefetchQuery({
          queryKey: analysisKeys.dashboard(versionId),
          queryFn: () => analysisApi.getDashboardSummary(versionId),
        })
        queryClient.prefetchQuery({
          queryKey: analysisKeys.activity(),
          queryFn: () => analysisApi.getRecentActivity(10),
        })
      }
    },
    [queryClient, router]
  )

  return { prefetchRoute }
}
