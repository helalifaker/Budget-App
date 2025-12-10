import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'
import type { Activity } from '@/types/api'
import { ClockIcon, UserIcon } from 'lucide-react'

interface ActivityFeedProps {
  activities: Activity[]
  className?: string
  title?: string
}

export function ActivityFeed({
  activities,
  className,
  title = 'Recent Activity',
}: ActivityFeedProps) {
  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'Just now'
    if (diffMins < 60) return `${diffMins} minute${diffMins > 1 ? 's' : ''} ago`
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getActionColor = (action: string | undefined): string => {
    // Defensive check: handle undefined/null action
    if (!action) return 'bg-bg-muted text-text-primary'

    const actionLower = action.toLowerCase()
    if (actionLower.includes('create')) return 'bg-sage-100 text-sage-800'
    if (actionLower.includes('update')) return 'bg-efir-slate-100 text-efir-slate-800'
    if (actionLower.includes('delete')) return 'bg-terracotta-100 text-terracotta-800'
    if (actionLower.includes('approve')) return 'bg-wine-100 text-wine-800'
    return 'bg-bg-muted text-text-primary'
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {activities.length === 0 ? (
            <div className="text-center py-8 text-text-tertiary">No recent activity</div>
          ) : (
            activities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-subtle transition-colors"
              >
                <div className="flex-shrink-0 w-8 h-8 bg-subtle rounded-full flex items-center justify-center">
                  <UserIcon className="w-4 h-4 text-text-secondary" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm text-text-primary">
                      {activity.user || 'Unknown User'}
                    </span>
                    <Badge className={cn('text-xs', getActionColor(activity.action))}>
                      {activity.action || 'Unknown Action'}
                    </Badge>
                  </div>
                  {activity.details && (
                    <p className="text-sm text-text-secondary line-clamp-2">{activity.details}</p>
                  )}
                  <div className="flex items-center gap-1 mt-1 text-xs text-text-tertiary">
                    <ClockIcon className="w-3 h-3" />
                    <span>
                      {activity.timestamp ? formatTimestamp(activity.timestamp) : 'Unknown time'}
                    </span>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  )
}
