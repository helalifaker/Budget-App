import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ActivityFeed } from '@/components/ActivityFeed'
import type { Activity } from '@/types/api'

describe('ActivityFeed', () => {
  let mockDate: Date

  beforeEach(() => {
    // Mock Date to have consistent timestamp testing
    mockDate = new Date('2025-12-05T12:00:00Z')
    vi.setSystemTime(mockDate)
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  const createActivity = (overrides?: Partial<Activity>): Activity => ({
    id: '123e4567-e89b-12d3-a456-426614174000',
    action: 'Updated',
    user: 'John Doe',
    timestamp: new Date(mockDate.getTime() - 3600000).toISOString(), // 1 hour ago
    details: null,
    ...overrides,
  })

  it('renders empty state when no activities provided', () => {
    render(<ActivityFeed activities={[]} />)

    expect(screen.getByText('No recent activity')).toBeInTheDocument()
  })

  it('renders default title "Recent Activity"', () => {
    render(<ActivityFeed activities={[createActivity()]} />)

    expect(screen.getByText('Recent Activity')).toBeInTheDocument()
  })

  it('renders custom title when provided', () => {
    render(<ActivityFeed activities={[createActivity()]} title="Latest Changes" />)

    expect(screen.getByText('Latest Changes')).toBeInTheDocument()
    expect(screen.queryByText('Recent Activity')).not.toBeInTheDocument()
  })

  it('renders single activity with all fields', () => {
    const activity = createActivity({
      user: 'Alice Smith',
      action: 'Created',
      details: 'Added new enrollment projection for 2025-2026',
    })

    render(<ActivityFeed activities={[activity]} />)

    expect(screen.getByText('Alice Smith')).toBeInTheDocument()
    expect(screen.getByText('Created')).toBeInTheDocument()
    expect(screen.getByText('Added new enrollment projection for 2025-2026')).toBeInTheDocument()
  })

  it('renders activity without details', () => {
    const activity = createActivity({
      user: 'Bob Johnson',
      action: 'Updated',
      details: null,
    })

    render(<ActivityFeed activities={[activity]} />)

    expect(screen.getByText('Bob Johnson')).toBeInTheDocument()
    expect(screen.getByText('Updated')).toBeInTheDocument()
  })

  it('renders multiple activities', () => {
    const activities = [
      createActivity({ user: 'Alice', action: 'Created' }),
      createActivity({
        user: 'Bob',
        action: 'Updated',
        id: '223e4567-e89b-12d3-a456-426614174000',
      }),
      createActivity({
        user: 'Charlie',
        action: 'Deleted',
        id: '323e4567-e89b-12d3-a456-426614174000',
      }),
    ]

    render(<ActivityFeed activities={activities} />)

    expect(screen.getByText('Alice')).toBeInTheDocument()
    expect(screen.getByText('Bob')).toBeInTheDocument()
    expect(screen.getByText('Charlie')).toBeInTheDocument()
  })

  describe('Action color coding', () => {
    it('applies green color for "create" actions', () => {
      const activity = createActivity({ action: 'Created budget version' })
      render(<ActivityFeed activities={[activity]} />)

      const badge = screen.getByText('Created budget version')
      expect(badge.className).toMatch(/bg-green-100/)
      expect(badge.className).toMatch(/text-green-800/)
    })

    it('applies blue color for "update" actions', () => {
      const activity = createActivity({ action: 'Updated enrollment data' })
      render(<ActivityFeed activities={[activity]} />)

      const badge = screen.getByText('Updated enrollment data')
      expect(badge.className).toMatch(/bg-blue-100/)
      expect(badge.className).toMatch(/text-blue-800/)
    })

    it('applies red color for "delete" actions', () => {
      const activity = createActivity({ action: 'Deleted class configuration' })
      render(<ActivityFeed activities={[activity]} />)

      const badge = screen.getByText('Deleted class configuration')
      expect(badge.className).toMatch(/bg-red-100/)
      expect(badge.className).toMatch(/text-red-800/)
    })

    it('applies purple color for "approve" actions', () => {
      const activity = createActivity({ action: 'Approved budget' })
      render(<ActivityFeed activities={[activity]} />)

      const badge = screen.getByText('Approved budget')
      expect(badge.className).toMatch(/bg-purple-100/)
      expect(badge.className).toMatch(/text-purple-800/)
    })

    it('applies gray color for other actions', () => {
      const activity = createActivity({ action: 'Viewed report' })
      render(<ActivityFeed activities={[activity]} />)

      const badge = screen.getByText('Viewed report')
      expect(badge.className).toMatch(/bg-gray-100/)
      expect(badge.className).toMatch(/text-gray-800/)
    })

    it('handles case-insensitive action matching', () => {
      const activity = createActivity({ action: 'CREATED' })
      render(<ActivityFeed activities={[activity]} />)

      const badge = screen.getByText('CREATED')
      expect(badge.className).toMatch(/bg-green-100/)
    })
  })

  describe('Timestamp formatting', () => {
    it('shows "Just now" for timestamps less than 1 minute ago', () => {
      const activity = createActivity({
        timestamp: new Date(mockDate.getTime() - 30000).toISOString(), // 30 seconds ago
      })

      render(<ActivityFeed activities={[activity]} />)

      expect(screen.getByText('Just now')).toBeInTheDocument()
    })

    it('shows minutes for timestamps 1-59 minutes ago', () => {
      const activity5min = createActivity({
        timestamp: new Date(mockDate.getTime() - 300000).toISOString(), // 5 minutes ago
        id: '1',
      })
      const activity1min = createActivity({
        timestamp: new Date(mockDate.getTime() - 60000).toISOString(), // 1 minute ago
        id: '2',
      })

      const { rerender } = render(<ActivityFeed activities={[activity5min]} />)
      expect(screen.getByText('5 minutes ago')).toBeInTheDocument()

      rerender(<ActivityFeed activities={[activity1min]} />)
      expect(screen.getByText('1 minute ago')).toBeInTheDocument()
    })

    it('shows hours for timestamps 1-23 hours ago', () => {
      const activity5hours = createActivity({
        timestamp: new Date(mockDate.getTime() - 18000000).toISOString(), // 5 hours ago
        id: '1',
      })
      const activity1hour = createActivity({
        timestamp: new Date(mockDate.getTime() - 3600000).toISOString(), // 1 hour ago
        id: '2',
      })

      const { rerender } = render(<ActivityFeed activities={[activity5hours]} />)
      expect(screen.getByText('5 hours ago')).toBeInTheDocument()

      rerender(<ActivityFeed activities={[activity1hour]} />)
      expect(screen.getByText('1 hour ago')).toBeInTheDocument()
    })

    it('shows days for timestamps 1-6 days ago', () => {
      const activity3days = createActivity({
        timestamp: new Date(mockDate.getTime() - 259200000).toISOString(), // 3 days ago
        id: '1',
      })
      const activity1day = createActivity({
        timestamp: new Date(mockDate.getTime() - 86400000).toISOString(), // 1 day ago
        id: '2',
      })

      const { rerender } = render(<ActivityFeed activities={[activity3days]} />)
      expect(screen.getByText('3 days ago')).toBeInTheDocument()

      rerender(<ActivityFeed activities={[activity1day]} />)
      expect(screen.getByText('1 day ago')).toBeInTheDocument()
    })

    it('shows formatted date for timestamps 7+ days ago', () => {
      const activity = createActivity({
        timestamp: new Date('2025-11-15T12:00:00Z').toISOString(), // 20 days ago
      })

      render(<ActivityFeed activities={[activity]} />)

      expect(screen.getByText('Nov 15, 2025')).toBeInTheDocument()
    })
  })

  it('applies custom className to container', () => {
    const { container } = render(
      <ActivityFeed activities={[createActivity()]} className="custom-class" />
    )

    const card = container.querySelector('.custom-class')
    expect(card).toBeInTheDocument()
  })

  it('renders user icon for each activity', () => {
    const activities = [createActivity({ id: '1' }), createActivity({ id: '2' })]

    const { container } = render(<ActivityFeed activities={activities} />)

    // Each activity should have a user icon container
    const icons = container.querySelectorAll('.bg-gray-200.rounded-full')
    expect(icons.length).toBe(2)
  })

  it('truncates long details text', () => {
    const longDetails =
      'This is a very long details text that should be truncated with line-clamp-2 utility class to prevent overflow and maintain consistent layout across all activity items in the feed.'

    const activity = createActivity({ details: longDetails })
    render(<ActivityFeed activities={[activity]} />)

    const detailsElement = screen.getByText(longDetails)
    expect(detailsElement.className).toMatch(/line-clamp-2/)
  })
})
