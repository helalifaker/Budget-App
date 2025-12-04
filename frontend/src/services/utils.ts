import { handleAPIError } from '@/lib/errors'

/**
 * Standardized error handling for service layer requests.
 * Logs a contextual message and preserves the original error type
 * so upstream callers (and toast helpers) can inspect status codes.
 */
export async function withServiceErrorHandling<T>(
  promise: Promise<T>,
  context: string
): Promise<T> {
  try {
    return await promise
  } catch (error) {
    const parsed = handleAPIError(error)
    console.error(`[Service:${context}]`, error)

    if (error instanceof Error && parsed.message) {
      error.message = `${context}: ${parsed.message}`
    }

    throw error
  }
}
