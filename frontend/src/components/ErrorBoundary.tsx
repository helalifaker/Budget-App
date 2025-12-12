import { Component, ReactNode } from 'react'
import * as Sentry from '@sentry/react'
import { Button } from '@/components/ui/button'
import { AlertTriangle } from 'lucide-react'

interface ErrorBoundaryProps {
  children: ReactNode
  fallback?: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    // Log to Sentry
    Sentry.captureException(error, {
      contexts: { react: { componentStack: errorInfo.componentStack } },
    })
    console.error('ErrorBoundary caught error:', error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    window.location.href = '/dashboard'
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback
      }

      return (
        <div className="flex min-h-screen items-center justify-center bg-subtle">
          <div className="max-w-md rounded-lg border border-terracotta-200 bg-paper p-8 shadow-lg">
            <div className="flex items-center gap-3 text-terracotta">
              <AlertTriangle className="h-8 w-8" />
              <h1 className="text-2xl font-bold">An error occurred</h1>
            </div>

            <p className="mt-4 text-text-secondary">
              We&apos;re sorry, but something went wrong. Please refresh the page or contact support
              if the problem persists.
            </p>

            {this.state.error && (
              <details className="mt-4 rounded bg-bg-muted p-3">
                <summary className="cursor-pointer text-sm font-medium text-text-secondary">
                  Technical details
                </summary>
                <pre className="mt-2 overflow-auto text-xs text-text-secondary">
                  {this.state.error.message}
                  {'\n\n'}
                  {this.state.error.stack}
                </pre>
              </details>
            )}

            <div className="mt-6 flex gap-3">
              <Button onClick={this.handleReset} variant="default">
                Retour au tableau de bord
              </Button>
              <Button onClick={() => window.location.reload()} variant="outline">
                Rafraîchir la page
              </Button>
            </div>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
