/**
 * Backend Health Check Service
 *
 * Provides functions to check if the backend server is reachable.
 * Uses the /health endpoint which is public (no auth required).
 */

import axios, { AxiosError } from 'axios'

/** Health check result */
export interface HealthCheckResult {
  /** Whether the backend is reachable */
  connected: boolean
  /** Response latency in milliseconds (only when connected) */
  latency?: number
  /** Error message (only when not connected) */
  error?: string
  /** Timestamp of the check */
  timestamp: Date
}

/** Health check response from backend */
interface HealthResponse {
  status: string
  timestamp?: string
}

/**
 * Get the backend base URL (without /api/v1 suffix).
 * The /health endpoint is at the root, not under /api/v1.
 */
function getBackendBaseUrl(): string {
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
  // Remove /api/v1 suffix if present to get the root URL
  return apiBaseUrl.replace(/\/api\/v1\/?$/, '')
}

/** Default timeout for health checks (3 seconds) */
const HEALTH_CHECK_TIMEOUT = 3000

/**
 * Check if the backend server is reachable.
 *
 * @returns HealthCheckResult with connection status and details
 */
export async function checkBackendHealth(): Promise<HealthCheckResult> {
  const baseUrl = getBackendBaseUrl()
  const startTime = performance.now()
  const timestamp = new Date()

  try {
    const response = await axios.get<HealthResponse>(`${baseUrl}/health`, {
      timeout: HEALTH_CHECK_TIMEOUT,
      // Don't send auth headers - /health is public
      headers: {
        'Content-Type': 'application/json',
      },
    })

    const latency = Math.round(performance.now() - startTime)

    if (response.status === 200 && response.data?.status === 'healthy') {
      return {
        connected: true,
        latency,
        timestamp,
      }
    }

    // Unexpected response format but server is responding
    return {
      connected: true,
      latency,
      timestamp,
    }
  } catch (error) {
    const axiosError = error as AxiosError

    // Determine the error message
    let errorMessage: string

    if (axiosError.code === 'ECONNREFUSED' || axiosError.code === 'ERR_NETWORK') {
      errorMessage = 'Backend server is not running'
    } else if (axiosError.code === 'ECONNABORTED' || axiosError.code === 'ETIMEDOUT') {
      errorMessage = 'Connection timed out'
    } else if (axiosError.response) {
      // Server responded with an error status
      errorMessage = `Server error: ${axiosError.response.status}`
    } else if (axiosError.message) {
      errorMessage = axiosError.message
    } else {
      errorMessage = 'Unknown connection error'
    }

    return {
      connected: false,
      error: errorMessage,
      timestamp,
    }
  }
}

/**
 * Get the backend URL for display purposes.
 */
export function getBackendUrl(): string {
  return getBackendBaseUrl()
}

/**
 * Get the command to start the backend server.
 */
export function getStartBackendCommand(): string {
  return 'cd backend && source .venv/bin/activate && uvicorn app.main:app --reload'
}
