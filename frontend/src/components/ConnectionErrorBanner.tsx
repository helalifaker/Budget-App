/**
 * ConnectionErrorBanner
 *
 * A prominent banner shown at the top of the page when the backend is
 * disconnected. Designed for first-time users who may not know how to
 * start the backend server.
 *
 * Features:
 * - Only shows when disconnected AND not dismissed
 * - Clear message with instructions
 * - Terminal command to start backend (copyable)
 * - Auto-hides when connection is established
 * - Dismissible (saves preference to localStorage)
 */

import { useState } from 'react'
import { useBackendConnection } from '@/contexts/useBackendConnection'
import { cn } from '@/lib/utils'
import { AlertTriangle, X, Terminal, Copy, Check, RefreshCw } from 'lucide-react'

export function ConnectionErrorBanner() {
  const { isConnected, isChecking, bannerDismissed, startCommand, dismissBanner, retry } =
    useBackendConnection()

  const [copied, setCopied] = useState(false)

  // Don't show in E2E test mode (banner blocks UI interactions in Playwright tests)
  const isE2ETestMode = import.meta.env.VITE_E2E_TEST_MODE === 'true'

  // Don't show if connected, dismissed, or in E2E test mode
  if (isConnected || bannerDismissed || isE2ETestMode) {
    return null
  }

  // Copy command to clipboard
  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText(startCommand)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Clipboard API not available
    }
  }

  return (
    <div
      className={cn(
        'fixed top-0 left-0 right-0 z-50',
        'bg-gradient-to-r from-red-50 to-orange-50',
        'border-b border-red-200',
        'shadow-md',
        'animate-in slide-in-from-top duration-300'
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="max-w-7xl mx-auto px-4 py-3">
        <div className="flex items-start gap-3">
          {/* Warning icon */}
          <div className="flex-shrink-0 mt-0.5">
            <AlertTriangle className="h-5 w-5 text-red-500" />
          </div>

          {/* Content */}
          <div className="flex-1 min-w-0">
            {/* Title */}
            <h3 className="text-sm font-semibold text-red-800">Cannot connect to backend server</h3>

            {/* Description */}
            <p className="mt-1 text-sm text-red-700">
              The backend server is not running. Start it with the command below:
            </p>

            {/* Command box */}
            <div className="mt-2 flex items-center gap-2">
              <div
                className={cn(
                  'flex-1 flex items-center gap-2',
                  'bg-slate-800 rounded-md px-3 py-2',
                  'font-mono text-sm text-slate-100',
                  'overflow-x-auto'
                )}
              >
                <Terminal className="h-4 w-4 text-slate-400 flex-shrink-0" />
                <code className="whitespace-nowrap">{startCommand}</code>
              </div>

              {/* Copy button */}
              <button
                onClick={copyCommand}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-2',
                  'bg-slate-700 hover:bg-slate-600 rounded-md',
                  'text-sm font-medium text-white',
                  'transition-colors duration-150'
                )}
                aria-label={copied ? 'Copied!' : 'Copy command'}
              >
                {copied ? (
                  <>
                    <Check className="h-4 w-4" />
                    <span>Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4" />
                    <span>Copy</span>
                  </>
                )}
              </button>

              {/* Retry button */}
              <button
                onClick={retry}
                disabled={isChecking}
                className={cn(
                  'flex items-center gap-1.5 px-3 py-2',
                  'bg-gold-500 hover:bg-gold-600 rounded-md',
                  'text-sm font-medium text-white',
                  'disabled:opacity-50 disabled:cursor-not-allowed',
                  'transition-colors duration-150'
                )}
                aria-label="Retry connection"
              >
                <RefreshCw className={cn('h-4 w-4', isChecking && 'animate-spin')} />
                <span>{isChecking ? 'Checking...' : 'Retry'}</span>
              </button>
            </div>

            {/* Help text */}
            <p className="mt-2 text-xs text-red-600">
              The app will automatically detect when the backend starts and load your data.
            </p>
          </div>

          {/* Dismiss button */}
          <button
            onClick={dismissBanner}
            className={cn(
              'flex-shrink-0 p-1 rounded',
              'text-red-400 hover:text-red-600 hover:bg-red-100',
              'transition-colors duration-150'
            )}
            aria-label="Dismiss banner"
          >
            <X className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  )
}
