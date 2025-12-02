import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query'
import { toastMessages } from './toast-messages'

// Create query cache with global error handling
const queryCache = new QueryCache({
  onError: (error) => {
    // Global query error handler - logged to console
    console.error('Query error:', error)
  },
})

// Create mutation cache with global error handling
const mutationCache = new MutationCache({
  onError: (error) => {
    // Global mutation error handler - handled by individual mutations
    console.error('Mutation error:', error)
  },
})

export const queryClient = new QueryClient({
  queryCache,
  mutationCache,
  defaultOptions: {
    queries: {
      // Caching strategy
      staleTime: 5 * 60 * 1000, // 5 minutes - data is considered fresh
      gcTime: 30 * 60 * 1000, // 30 minutes - keep in garbage collection

      // Retry strategy - smart retry based on error type
      retry: (failureCount, error) => {
        // Don't retry on 4xx client errors (bad request, unauthorized, etc.)
        if (error instanceof Error) {
          const errorMessage = error.message.toLowerCase()
          if (
            errorMessage.includes('400') ||
            errorMessage.includes('401') ||
            errorMessage.includes('403') ||
            errorMessage.includes('404') ||
            errorMessage.includes('422')
          ) {
            return false
          }
        }
        // Retry up to 2 times for network errors and 5xx errors
        return failureCount < 2
      },
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000), // Exponential backoff, max 30s

      // Refetch strategy
      refetchOnWindowFocus: false, // Don't refetch on window focus (prevents excessive requests)
      refetchOnReconnect: true, // Do refetch when internet connection is restored
      refetchOnMount: true, // Refetch on component mount if data is stale

      // Performance
      structuralSharing: true, // Optimize re-renders by sharing unchanged data structures
      throwOnError: false, // Handle errors in components, not globally

      // Network mode
      networkMode: 'online', // Only run queries when online
    },
    mutations: {
      retry: 1, // Retry mutations once on failure
      networkMode: 'online',
      throwOnError: false,
    },
  },
})

// Helper function for optimistic updates
export function setQueryDataOptimistically<T>(
  queryKey: unknown[],
  updater: (old: T) => T
): T | undefined {
  const oldData = queryClient.getQueryData<T>(queryKey)
  if (oldData) {
    const newData = updater(oldData)
    queryClient.setQueryData(queryKey, newData)
    return newData
  }
  return undefined
}

// Helper function for query invalidation with optional toast
export async function invalidateQueriesWithToast(
  queryKey: unknown[],
  message?: string
): Promise<void> {
  await queryClient.invalidateQueries({ queryKey })
  if (message) {
    toastMessages.info.loading(message)
  }
}
