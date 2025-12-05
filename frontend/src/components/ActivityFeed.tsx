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
    if (!action) return 'bg-gray-100 text-gray-800'

    const actionLower = action.toLowerCase()
    if (actionLower.includes('create')) return 'bg-green-100 text-green-800'
    if (actionLower.includes('update')) return 'bg-blue-100 text-blue-800'
    if (actionLower.includes('delete')) return 'bg-red-100 text-red-800'
    if (actionLower.includes('approve')) return 'bg-purple-100 text-purple-800'
    return 'bg-gray-100 text-gray-800'
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {activities.length === 0 ? (
            <div className="text-center py-8 text-gray-500">No recent activity</div>
          ) : (
            activities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-3 rounded-lg hover:bg-gray-50 transition-colors"
              >
                <div className="flex-shrink-0 w-8 h-8 bg-gray-200 rounded-full flex items-center justify-center">
                  <UserIcon className="w-4 h-4 text-gray-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="font-medium text-sm text-gray-900">
                      {activity.user || 'Unknown User'}
                    </span>
                    <Badge className={cn('text-xs', getActionColor(activity.action))}>
                      {activity.action || 'Unknown Action'}
                    </Badge>
                  </div>
                  {activity.details && (
                    <p className="text-sm text-gray-600 line-clamp-2">{activity.details}</p>
                  )}
                  <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
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
