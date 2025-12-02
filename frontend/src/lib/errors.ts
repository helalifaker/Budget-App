import { AxiosError } from 'axios'

export interface APIError {
  message: string
  code?: string
  details?: unknown
}

/**
 * Parse an error into a structured APIError object
 * Does not show toast notifications - use handleAPIErrorToast from toast-messages.ts for that
 *
 * @param error - The error to parse
 * @returns Structured error object with message, code, and details
 */
export function handleAPIError(error: unknown): APIError {
  if (error instanceof AxiosError) {
    const data = error.response?.data as { detail?: string; code?: string } | undefined
    return {
      message: data?.detail || error.message || 'An error occurred',
      code: data?.code,
      details: data,
    }
  }

  if (error instanceof Error) {
    return {
      message: error.message,
    }
  }

  return {
    message: 'An unknown error occurred',
  }
}

/**
 * Get a human-readable error message from an error
 * Does not show toast notifications
 *
 * @param error - The error to extract message from
 * @returns Error message string
 */
export function getErrorMessage(error: unknown): string {
  return handleAPIError(error).message
}

export function isAPIError(error: unknown): error is AxiosError {
  return error instanceof AxiosError
}

export function isUnauthorizedError(error: unknown): boolean {
  return isAPIError(error) && error.response?.status === 401
}

export function isForbiddenError(error: unknown): boolean {
  return isAPIError(error) && error.response?.status === 403
}

export function isNotFoundError(error: unknown): boolean {
  return isAPIError(error) && error.response?.status === 404
}

export function isValidationError(error: unknown): boolean {
  return isAPIError(error) && error.response?.status === 422
}
