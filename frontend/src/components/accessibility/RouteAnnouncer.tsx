/* eslint-disable react-refresh/only-export-components */
/**
 * Route Change Announcer
 *
 * Announces page navigation changes to screen readers.
 * Essential for SPA navigation where the browser doesn't announce page changes.
 *
 * WCAG 2.1 Success Criterion 2.4.2 (Level A) - Page Titled
 *
 * Features:
 * - Automatically detect route changes
 * - Announce page title to screen readers
 * - Focus management after navigation
 */

import { useEffect, useRef, useState } from 'react'
import { useRouterState } from '@tanstack/react-router'

// Map routes to human-readable names
const ROUTE_NAMES: Record<string, string> = {
  '/': 'Home',
  '/login': 'Login',
  '/dashboard': 'Dashboard',
  // Students module (enrollment)
  '/students': 'Students',
  '/students/planning': 'Enrollment Planning',
  '/students/class-structure': 'Class Structure',
  '/students/validation': 'Enrollment Validation',
  '/students/settings': 'Enrollment Settings',
  // Teachers module (workforce)
  '/teachers': 'Teachers',
  '/teachers/employees': 'Employee Registry',
  '/teachers/salaries': 'Salaries & EOS',
  '/teachers/aefe-positions': 'AEFE Positions',
  '/teachers/dhg/planning': 'DHG Workforce Planning',
  '/teachers/dhg/requirements': 'FTE Requirements',
  '/teachers/dhg/gap-analysis': 'Gap Analysis (TRMD)',
  '/teachers/settings': 'Workforce Settings',
  // Finance module
  '/finance': 'Finance',
  '/finance/revenue': 'Revenue Planning',
  '/finance/costs': 'Cost Planning',
  '/finance/capex': 'Capital Expenditure Planning',
  '/finance/consolidation': 'Budget Consolidation',
  '/finance/statements': 'Financial Statements',
  '/finance/settings': 'Finance Settings',
  // Insights module (analysis)
  '/insights': 'Insights',
  '/insights/kpis': 'Key Performance Indicators',
  '/insights/dashboards': 'Dashboards',
  '/insights/variance': 'Variance Analysis',
  // Settings module (configuration)
  '/settings': 'Settings',
  '/settings/versions': 'Budget Versions',
  '/settings/class-sizes': 'Class Size Parameters',
  '/settings/subject-hours': 'Subject Hours',
  '/settings/teacher-costs': 'Teacher Costs',
  '/settings/fees': 'Fee Structure',
  '/settings/timetable': 'Timetable',
  '/settings/system': 'System Configuration',
  '/settings/uploads': 'Data Uploads',
  // Strategic
  '/strategic': '5-Year Strategic Planning',
  // Legacy routes (redirects handle these)
  '/planning/guide': 'Planning Guide',
}

/**
 * Get human-readable name for a route
 */
function getRouteName(pathname: string): string {
  // Exact match
  if (ROUTE_NAMES[pathname]) {
    return ROUTE_NAMES[pathname]
  }

  // Try without trailing slash
  const cleanPath = pathname.replace(/\/$/, '')
  if (ROUTE_NAMES[cleanPath]) {
    return ROUTE_NAMES[cleanPath]
  }

  // Generate from path
  const segments = pathname.split('/').filter(Boolean)
  if (segments.length === 0) return 'Home'

  // Capitalize and join
  return segments.map((s) => s.charAt(0).toUpperCase() + s.slice(1).replace(/-/g, ' ')).join(' - ')
}

interface RouteAnnouncerProps {
  /**
   * Custom announcement format
   */
  announcementFormat?: (pageName: string) => string

  /**
   * Focus main content after navigation
   */
  focusMainContent?: boolean

  /**
   * Delay before announcement (ms)
   */
  delay?: number
}

/**
 * RouteAnnouncer component for announcing navigation changes.
 * Place this once in your app layout.
 */
export function RouteAnnouncer({
  announcementFormat = (pageName) => `Navigated to ${pageName}`,
  focusMainContent = true,
  delay = 100,
}: RouteAnnouncerProps) {
  const routerState = useRouterState()
  const [announcement, setAnnouncement] = useState('')
  const previousPath = useRef<string>('')
  const announcerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const currentPath = routerState.location.pathname

    // Skip if path hasn't changed
    if (currentPath === previousPath.current) return

    // Skip initial render
    if (previousPath.current === '') {
      previousPath.current = currentPath
      return
    }

    previousPath.current = currentPath

    // Delayed announcement
    const timer = setTimeout(() => {
      const pageName = getRouteName(currentPath)
      const message = announcementFormat(pageName)

      // Update announcement
      setAnnouncement(message)

      // Update document title
      document.title = `${pageName} | EFIR Budget`

      // Focus main content for keyboard users
      if (focusMainContent) {
        const mainContent = document.getElementById('main-content')
        if (mainContent) {
          mainContent.focus({ preventScroll: true })
        }
      }

      // Clear announcement after it's been read
      setTimeout(() => setAnnouncement(''), 1000)
    }, delay)

    return () => clearTimeout(timer)
  }, [routerState.location.pathname, announcementFormat, focusMainContent, delay])

  return (
    <div ref={announcerRef} role="status" aria-live="polite" aria-atomic="true" className="sr-only">
      {announcement}
    </div>
  )
}

/**
 * useRouteAnnouncement hook for manual announcements
 */
export function useRouteAnnouncement() {
  const announce = (pageName: string) => {
    // Find or create announcer element
    let announcer = document.getElementById('route-announcer')
    if (!announcer) {
      announcer = document.createElement('div')
      announcer.id = 'route-announcer'
      announcer.setAttribute('role', 'status')
      announcer.setAttribute('aria-live', 'polite')
      announcer.setAttribute('aria-atomic', 'true')
      announcer.className = 'sr-only'
      document.body.appendChild(announcer)
    }

    // Set announcement
    announcer.textContent = `Navigated to ${pageName}`

    // Clear after reading
    setTimeout(() => {
      if (announcer) announcer.textContent = ''
    }, 1000)
  }

  return { announce }
}

export default RouteAnnouncer
