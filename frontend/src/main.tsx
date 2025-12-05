import React from 'react'
import ReactDOM from 'react-dom/client'
import * as Sentry from '@sentry/react'
import { QueryClientProvider } from '@tanstack/react-query'
import { ReactQueryDevtools } from '@tanstack/react-query-devtools'
import { Toaster } from 'sonner'
import { ModuleRegistry, AllCommunityModule } from 'ag-grid-community'
import { AuthProvider } from './contexts/AuthProvider'
import { BudgetVersionProvider } from './contexts/BudgetVersionProvider'
import { queryClient } from './lib/query-client'
import { ErrorBoundary } from './components/ErrorBoundary'
import App from './App'
import './index.css'

// Register AG Grid modules (required for AG Grid v34+)
ModuleRegistry.registerModules([AllCommunityModule])

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
        <AuthProvider>
          {/* BudgetVersionProvider must be inside AuthProvider (uses auth for API calls) */}
          <BudgetVersionProvider>
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
          </BudgetVersionProvider>
        </AuthProvider>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
)
