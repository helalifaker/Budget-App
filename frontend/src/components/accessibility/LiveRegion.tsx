/* eslint-disable react-refresh/only-export-components */
/**
 * Live Region Component
 *
 * ARIA live regions announce dynamic content changes to screen readers.
 * This component provides a centralized system for status announcements.
 *
 * WCAG 2.1 Success Criterion 4.1.3 (Level AA) - Status Messages
 *
 * Usage:
 * 1. Wrap your app with LiveRegionProvider
 * 2. Use the useLiveAnnounce hook to make announcements
 * 3. The LiveRegionPortal renders announcements to screen readers
 */

import { createContext, useCallback, useContext, useRef, useState, type ReactNode } from 'react'

type Politeness = 'polite' | 'assertive' | 'off'

interface Announcement {
  id: string
  message: string
  politeness: Politeness
  timestamp: number
}

interface LiveRegionContextType {
  announce: (message: string, politeness?: Politeness) => void
  announcePolite: (message: string) => void
  announceAssertive: (message: string) => void
  clearAnnouncements: () => void
}

const LiveRegionContext = createContext<LiveRegionContextType | null>(null)

interface LiveRegionProviderProps {
  children: ReactNode
}

/**
 * LiveRegionProvider manages screen reader announcements.
 * Place this high in your component tree (e.g., at the app root).
 */
export function LiveRegionProvider({ children }: LiveRegionProviderProps) {
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const announcementIdRef = useRef(0)

  const announce = useCallback((message: string, politeness: Politeness = 'polite') => {
    const id = `announcement-${++announcementIdRef.current}`
    const announcement: Announcement = {
      id,
      message,
      politeness,
      timestamp: Date.now(),
    }

    setAnnouncements((prev) => [...prev, announcement])

    // Clear announcement after it's been read (give screen reader time to read)
    setTimeout(() => {
      setAnnouncements((prev) => prev.filter((a) => a.id !== id))
    }, 3000)
  }, [])

  const announcePolite = useCallback((message: string) => announce(message, 'polite'), [announce])

  const announceAssertive = useCallback(
    (message: string) => announce(message, 'assertive'),
    [announce]
  )

  const clearAnnouncements = useCallback(() => {
    setAnnouncements([])
  }, [])

  return (
    <LiveRegionContext.Provider
      value={{ announce, announcePolite, announceAssertive, clearAnnouncements }}
    >
      {children}
      <LiveRegionPortal announcements={announcements} />
    </LiveRegionContext.Provider>
  )
}

/**
 * LiveRegionPortal renders the actual ARIA live regions.
 * These are visually hidden but read by screen readers.
 */
function LiveRegionPortal({ announcements }: { announcements: Announcement[] }) {
  const politeAnnouncements = announcements.filter((a) => a.politeness === 'polite')
  const assertiveAnnouncements = announcements.filter((a) => a.politeness === 'assertive')

  return (
    <>
      {/* Polite region - waits for user to finish current task */}
      <div role="status" aria-live="polite" aria-atomic="true" className="sr-only">
        {politeAnnouncements.map((a) => (
          <p key={a.id}>{a.message}</p>
        ))}
      </div>

      {/* Assertive region - interrupts immediately */}
      <div role="alert" aria-live="assertive" aria-atomic="true" className="sr-only">
        {assertiveAnnouncements.map((a) => (
          <p key={a.id}>{a.message}</p>
        ))}
      </div>
    </>
  )
}

/**
 * useLiveAnnounce hook for making screen reader announcements.
 *
 * @example
 * const { announce, announcePolite, announceAssertive } = useLiveAnnounce()
 *
 * // After saving data
 * announcePolite('Changes saved successfully')
 *
 * // For errors
 * announceAssertive('Error: Failed to save changes')
 */
export function useLiveAnnounce() {
  const context = useContext(LiveRegionContext)

  if (!context) {
    throw new Error('useLiveAnnounce must be used within a LiveRegionProvider')
  }

  return context
}

/**
 * Standalone StatusMessage component for inline status announcements.
 * Use this for local status messages that should be announced.
 */
export function StatusMessage({
  message,
  politeness = 'polite',
  visible = false,
  className,
}: {
  message: string
  politeness?: Politeness
  visible?: boolean
  className?: string
}) {
  return (
    <div
      role="status"
      aria-live={politeness}
      aria-atomic="true"
      className={visible ? className : 'sr-only'}
    >
      {message}
    </div>
  )
}

export default LiveRegionProvider
