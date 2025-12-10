import { AlertCircle, Loader2 } from 'lucide-react'

export function LoadingState() {
  return (
    <div className="flex items-center justify-center p-8">
      <Loader2 className="h-12 w-12 animate-spin text-primary" />
    </div>
  )
}

export function LoadingSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
  }

  return <Loader2 className={`${sizeClasses[size]} animate-spin text-primary`} />
}

export function ErrorState({ error }: { error: string }) {
  return (
    <div className="rounded-md bg-terracotta-50 p-4">
      <div className="flex">
        <AlertCircle className="h-5 w-5 text-terracotta-400" />
        <div className="ml-3">
          <p className="text-sm text-terracotta-800">{error}</p>
        </div>
      </div>
    </div>
  )
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string
  description?: string
  action?: React.ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center">
      <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
      {description && <p className="mt-2 text-sm text-text-tertiary">{description}</p>}
      {action && <div className="mt-4">{action}</div>}
    </div>
  )
}

export function SkeletonLoader({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 animate-pulse">
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="h-12 bg-subtle dark:bg-border-light rounded" />
      ))}
    </div>
  )
}
