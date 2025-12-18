import React from 'react'
import ReactDOM from 'react-dom/client'
import * as Sentry from '@sentry/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'sonner'
import { AuthProvider } from './contexts/AuthProvider'
import { VersionProvider } from './contexts/VersionProvider'
import { BackendConnectionProvider } from './contexts/BackendConnectionProvider'
import { queryClient } from './lib/query-client'
import { ErrorBoundary } from './components/ErrorBoundary'
import { ConnectionStatusIndicator } from './components/ConnectionStatusIndicator'
import { ConnectionErrorBanner } from './components/ConnectionErrorBanner'
import App from './App'
import './index.css'

// Initialize Sentry BEFORE React rendering
if (import.meta.env.VITE_SENTRY_DSN_FRONTEND) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN_FRONTEND,
    environment: import.meta.env.VITE_SENTRY_ENVIRONMENT || 'development',
    integrations: [
      Sentry.browserTracingIntegration(),
      Sentry.replayIntegration({
        maskAllText: false,
        blockAllMedia: false,
      }),
    ],
    tracesSampleRate: parseFloat(import.meta.env.VITE_SENTRY_TRACES_SAMPLE_RATE || '0.1'),
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
    release: import.meta.env.VITE_GIT_COMMIT_SHA || 'dev',
    beforeSend(event) {
      // Don't send in development unless explicitly enabled
      if (import.meta.env.DEV && !import.meta.env.VITE_SENTRY_DEBUG) {
        return null
      }
      return event
    },
  })
}

// Ensure root element exists before rendering
const rootElement = document.getElementById('root')
if (!rootElement) {
  throw new Error('Root element not found. Make sure index.html has <div id="root"></div>')
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        {/* BackendConnectionProvider: Checks if backend is reachable */}
        <BackendConnectionProvider>
          {/* Connection status UI - shows banner on first failure, indicator always */}
          <ConnectionErrorBanner />
          <ConnectionStatusIndicator />

          <AuthProvider>
            {/* VersionProvider must be inside AuthProvider (uses auth for API calls) */}
            <VersionProvider>
              <App />
              <Toaster
                position="top-right"
                richColors
                closeButton
                duration={4000}
                toastOptions={{
                  style: {
                    fontFamily: 'Inter, system-ui, sans-serif',
                  },
                }}
              />
              {/* React Query DevTools - only in development */}
              {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
            </VersionProvider>
          </AuthProvider>
        </BackendConnectionProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
)
