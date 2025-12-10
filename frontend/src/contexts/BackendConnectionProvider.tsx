/**
 * BackendConnectionProvider
 *
 * Provides global backend connection status to the entire application.
 * Automatically checks health on mount and retries with exponential backoff
 * when disconnected.
 *
 * Features:
 * - Runs health check on app mount
 * - Auto-retries with exponential backoff when disconnected
 * - Provides connection status to all components
 * - Tracks whether user has dismissed the error banner
 */

import React, { createContext, useContext, useEffect, useState, useCallback, useRef } from 'react'
import {
  checkBackendHealth,
  getBackendUrl,
  getStartBackendCommand,
  type HealthCheckResult,
} from '@/services/health'

/** Connection state exposed by the context */
export interface BackendConnectionState {
  /** Whether the backend is currently connected */
  isConnected: boolean
  /** Whether a health check is currently in progress */
  isChecking: boolean
  /** The last error message (null if connected) */
  lastError: string | null
  /** Timestamp of the last successful connection */
  lastConnectedAt: Date | null
  /** Timestamp of the last health check */
  lastCheckedAt: Date | null
  /** Response latency in ms (only when connected) */
  latency: number | null
  /** Backend URL for display */
  backendUrl: string
  /** Command to start the backend */
  startCommand: string
  /** Whether the user has dismissed the banner for this session */
  bannerDismissed: boolean
  /** Manually trigger a health check */
  retry: () => void
  /** Dismiss the connection error banner */
  dismissBanner: () => void
}

const BackendConnectionContext = createContext<BackendConnectionState | null>(null)

/** localStorage key for banner dismissal */
const BANNER_DISMISSED_KEY = 'efir-backend-banner-dismissed'

/** Retry intervals in milliseconds (exponential backoff) */
const RETRY_INTERVALS = [3000, 5000, 10000, 15000, 30000]

/**
 * Get the next retry interval based on the number of failed attempts.
 */
function getRetryInterval(failedAttempts: number): number {
  const index = Math.min(failedAttempts, RETRY_INTERVALS.length - 1)
  return RETRY_INTERVALS[index]
}

/**
 * Check if banner was previously dismissed (from localStorage).
 */
function wasBannerDismissed(): boolean {
  try {
    return localStorage.getItem(BANNER_DISMISSED_KEY) === 'true'
  } catch {
    return false
  }
}

/**
 * Persist banner dismissal to localStorage.
 */
function persistBannerDismissal(dismissed: boolean): void {
  try {
    if (dismissed) {
      localStorage.setItem(BANNER_DISMISSED_KEY, 'true')
    } else {
      localStorage.removeItem(BANNER_DISMISSED_KEY)
    }
  } catch {
    // localStorage unavailable
  }
}

export function BackendConnectionProvider({ children }: { children: React.ReactNode }) {
  // Connection state
  const [isConnected, setIsConnected] = useState<boolean>(false)
  const [isChecking, setIsChecking] = useState<boolean>(true) // Start checking on mount
  const [lastError, setLastError] = useState<string | null>(null)
  const [lastConnectedAt, setLastConnectedAt] = useState<Date | null>(null)
  const [lastCheckedAt, setLastCheckedAt] = useState<Date | null>(null)
  const [latency, setLatency] = useState<number | null>(null)
  const [bannerDismissed, setBannerDismissed] = useState<boolean>(() => wasBannerDismissed())

  // Track failed attempts for exponential backoff
  const failedAttemptsRef = useRef<number>(0)
  const retryTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Perform health check
  const performHealthCheck = useCallback(async (): Promise<HealthCheckResult> => {
    setIsChecking(true)

    const result = await checkBackendHealth()

    setIsConnected(result.connected)
    setLastCheckedAt(result.timestamp)

    if (result.connected) {
      setLastConnectedAt(result.timestamp)
      setLatency(result.latency ?? null)
      setLastError(null)
      failedAttemptsRef.current = 0

      // Clear banner dismissal when connection is restored
      // (so it shows again if connection drops later)
      // Note: We keep it dismissed to not annoy the user
    } else {
      setLatency(null)
      setLastError(result.error ?? 'Connection failed')
      failedAttemptsRef.current += 1
    }

    setIsChecking(false)
    return result
  }, [])

  // Schedule next retry with exponential backoff
  const scheduleRetry = useCallback(() => {
    // Clear any existing timeout
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
    }

    const interval = getRetryInterval(failedAttemptsRef.current)

    retryTimeoutRef.current = setTimeout(async () => {
      const result = await performHealthCheck()

      // If still disconnected, schedule another retry
      if (!result.connected) {
        scheduleRetry()
      }
    }, interval)
  }, [performHealthCheck])

  // Manual retry handler
  const retry = useCallback(async () => {
    // Clear scheduled retry
    if (retryTimeoutRef.current) {
      clearTimeout(retryTimeoutRef.current)
      retryTimeoutRef.current = null
    }

    // Reset failed attempts for immediate retry
    failedAttemptsRef.current = 0

    const result = await performHealthCheck()

    // If still disconnected, schedule auto-retry
    if (!result.connected) {
      scheduleRetry()
    }
  }, [performHealthCheck, scheduleRetry])

  // Dismiss banner handler
  const dismissBanner = useCallback(() => {
    setBannerDismissed(true)
    persistBannerDismissal(true)
  }, [])

  // Initial health check on mount
  useEffect(() => {
    let mounted = true

    const initialCheck = async () => {
      const result = await performHealthCheck()

      if (!mounted) return

      // If disconnected, start auto-retry
      if (!result.connected) {
        scheduleRetry()
      }
    }

    initialCheck()

    return () => {
      mounted = false
      if (retryTimeoutRef.current) {
        clearTimeout(retryTimeoutRef.current)
      }
    }
  }, [performHealthCheck, scheduleRetry])

  // Re-check when tab becomes visible
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible') {
        retry()
      }
    }

    document.addEventListener('visibilitychange', handleVisibilityChange)

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [retry])

  // Periodic health check when connected (every 30 seconds)
  useEffect(() => {
    if (!isConnected) return

    const intervalId = setInterval(async () => {
      const result = await performHealthCheck()

      // If disconnected, start auto-retry
      if (!result.connected) {
        scheduleRetry()
      }
    }, 30000)

    return () => {
      clearInterval(intervalId)
    }
  }, [isConnected, performHealthCheck, scheduleRetry])

  const value: BackendConnectionState = {
    isConnected,
    isChecking,
    lastError,
    lastConnectedAt,
    lastCheckedAt,
    latency,
    backendUrl: getBackendUrl(),
    startCommand: getStartBackendCommand(),
    bannerDismissed,
    retry,
    dismissBanner,
  }

  return (
    <BackendConnectionContext.Provider value={value}>{children}</BackendConnectionContext.Provider>
  )
}

/**
 * Hook to access backend connection state.
 * Must be used within a BackendConnectionProvider.
 */
export function useBackendConnection(): BackendConnectionState {
  const context = useContext(BackendConnectionContext)

  if (!context) {
    throw new Error('useBackendConnection must be used within a BackendConnectionProvider')
  }

  return context
}
