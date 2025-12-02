/**
 * Lazy-loaded Recharts Components
 *
 * This module lazy loads Recharts to reduce initial bundle size.
 * Recharts is ~100KB and only needed on analysis/dashboard pages.
 *
 * Usage:
 * import { BarChartLazy, LineChartLazy } from '@/components/charts/ChartsLazy'
 * <BarChartLazy data={data} />
 */

import { lazy, Suspense, ComponentProps } from 'react'
import { ChartSkeleton } from '../LoadingSkeleton'

// Lazy load Recharts components
const RechartsBarChart = lazy(() =>
  import('recharts').then((module) => ({ default: module.BarChart }))
)

const RechartsLineChart = lazy(() =>
  import('recharts').then((module) => ({ default: module.LineChart }))
)

const RechartsAreaChart = lazy(() =>
  import('recharts').then((module) => ({ default: module.AreaChart }))
)

const RechartsPieChart = lazy(() =>
  import('recharts').then((module) => ({ default: module.PieChart }))
)

const RechartsComposedChart = lazy(() =>
  import('recharts').then((module) => ({ default: module.ComposedChart }))
)

// Export lazy-loaded chart components with Suspense wrapper
export function BarChartLazy(props: ComponentProps<typeof RechartsBarChart>) {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <RechartsBarChart {...props} />
    </Suspense>
  )
}

export function LineChartLazy(props: ComponentProps<typeof RechartsLineChart>) {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <RechartsLineChart {...props} />
    </Suspense>
  )
}

export function AreaChartLazy(props: ComponentProps<typeof RechartsAreaChart>) {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <RechartsAreaChart {...props} />
    </Suspense>
  )
}

export function PieChartLazy(props: ComponentProps<typeof RechartsPieChart>) {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <RechartsPieChart {...props} />
    </Suspense>
  )
}

export function ComposedChartLazy(props: ComponentProps<typeof RechartsComposedChart>) {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <RechartsComposedChart {...props} />
    </Suspense>
  )
}

// Re-export all other Recharts components that are small
// These will be imported normally (not lazy loaded)
export {
  Bar,
  Line,
  Area,
  Pie,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  Cell,
} from 'recharts'
