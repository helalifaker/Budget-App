/**
 * useOrganization Hook
 *
 * Provides the current user's organization context for API calls.
 *
 * For EFIR (single-tenant deployment), this returns the default organization.
 * In a multi-tenant setup, this would fetch from user profile or org context.
 *
 * The organization_id is required for calibration-related APIs that are
 * scoped by organization rather than budget version.
 */

import { useQuery } from '@tanstack/react-query'
import { apiRequest } from '@/lib/api-client'

interface Organization {
  id: string
  name: string
  is_active: boolean
}

interface OrganizationResponse {
  organization: Organization | null
  is_default: boolean
}

// Query key factory for organization queries
export const organizationKeys = {
  all: ['organization'] as const,
  current: () => [...organizationKeys.all, 'current'] as const,
}

/**
 * Fetch the current user's organization from the backend.
 * For single-tenant deployments, this returns the default organization.
 */
async function fetchCurrentOrganization(): Promise<OrganizationResponse> {
  try {
    // Try to fetch from the API - backend should return the user's org
    // or the default org for single-tenant deployments
    const response = await apiRequest<OrganizationResponse>({
      method: 'GET',
      url: '/organization/current',
    })
    return response
  } catch {
    // If API endpoint doesn't exist yet, return a fallback
    // This allows the UI to work while the API is being developed
    console.warn('[useOrganization] API endpoint not available, using fallback')
    return {
      organization: null,
      is_default: true,
    }
  }
}

/**
 * Hook to get the current organization.
 *
 * For EFIR (single-tenant), returns the default organization.
 * The organization_id is used for calibration settings which are
 * organization-scoped rather than budget-version-scoped.
 *
 * @example
 * ```tsx
 * const { organizationId, isLoading } = useOrganization()
 *
 * // Use in calibration queries
 * const { data } = useEnrollmentSettings(organizationId)
 * ```
 */
export function useOrganization() {
  const query = useQuery({
    queryKey: organizationKeys.current(),
    queryFn: fetchCurrentOrganization,
    staleTime: 5 * 60 * 1000, // 5 minutes - organization rarely changes
    retry: 1, // Don't retry many times if endpoint doesn't exist
  })

  return {
    organization: query.data?.organization,
    organizationId: query.data?.organization?.id,
    isDefault: query.data?.is_default ?? true,
    isLoading: query.isLoading,
    error: query.error,
  }
}

/**
 * Hook for getting organization ID with a fallback option.
 *
 * This is useful when you want to use a specific organization ID
 * if the current organization query fails or isn't available yet.
 *
 * @param fallbackId - Optional fallback organization ID
 */
export function useOrganizationId(fallbackId?: string): string | undefined {
  const { organizationId, isLoading } = useOrganization()

  // Return fallback while loading or if no organization found
  if (isLoading || !organizationId) {
    return fallbackId
  }

  return organizationId
}
