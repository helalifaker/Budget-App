import { useContext } from 'react'
import { BackendConnectionContext, type BackendConnectionState } from './backendConnectionContext'

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
