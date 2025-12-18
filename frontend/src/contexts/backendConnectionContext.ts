import { createContext } from 'react'

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

export const BackendConnectionContext = createContext<BackendConnectionState | null>(null)
