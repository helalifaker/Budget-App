/**
 * ConnectionStatusIndicator
 *
 * A small, persistent indicator at the bottom-right of all pages showing
 * backend connection status:
 * - 🟢 Green dot: Backend connected
 * - 🔴 Red dot: Backend disconnected
 * - Pulsing animation: Health check in progress
 *
 * Hover/click shows tooltip with:
 * - Current status
 * - Backend URL
 * - Instructions to start backend (if disconnected)
 * - Last check timestamp
 * - Latency (if connected)
 */

import { useState } from 'react'
import { useBackendConnection } from '@/contexts/useBackendConnection'
import { cn } from '@/lib/utils'
import { RefreshCw, Server, Clock, Zap, Terminal } from 'lucide-react'

export function ConnectionStatusIndicator() {
  const {
    isConnected,
    isChecking,
    lastError,
    lastCheckedAt,
    latency,
    backendUrl,
    startCommand,
    retry,
  } = useBackendConnection()

  const [isExpanded, setIsExpanded] = useState(false)

  // Format the last checked time
  const formatTime = (date: Date | null): string => {
    if (!date) return 'Never'
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
    })
  }

  // Copy command to clipboard
  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText(startCommand)
    } catch {
      // Clipboard API not available
    }
  }

  return (
    <div
      className={cn('fixed bottom-4 right-4 z-50', 'flex flex-col items-end gap-2', 'font-body')}
    >
      {/* Expanded tooltip/panel */}
      {isExpanded && (
        <div
          className={cn(
            'bg-paper rounded-lg shadow-efir-md',
            'border border-border-light',
            'p-4 min-w-[280px] max-w-[320px]',
            'animate-in fade-in-0 slide-in-from-bottom-2 duration-200'
          )}
        >
          {/* Header */}
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <Server className="h-4 w-4 text-text-secondary" />
              <span className="text-sm font-medium text-text-primary">Backend Status</span>
            </div>
            <button
              onClick={() => setIsExpanded(false)}
              className="text-text-tertiary hover:text-text-secondary text-lg leading-none"
              aria-label="Close status panel"
            >
              ×
            </button>
          </div>

          {/* Status */}
          <div className="flex items-center gap-2 mb-3">
            <div
              className={cn(
                'w-3 h-3 rounded-full',
                isConnected ? 'bg-emerald-500' : 'bg-red-500',
                isChecking && 'animate-pulse'
              )}
            />
            <span
              className={cn(
                'text-sm font-medium',
                isConnected ? 'text-emerald-600' : 'text-red-600'
              )}
            >
              {isChecking ? 'Checking...' : isConnected ? 'Connected' : 'Disconnected'}
            </span>
          </div>

          {/* Details */}
          <div className="space-y-2 text-xs text-text-secondary">
            {/* Backend URL */}
            <div className="flex items-center gap-2">
              <Server className="h-3 w-3 flex-shrink-0" />
              <span className="truncate">{backendUrl}</span>
            </div>

            {/* Last checked */}
            <div className="flex items-center gap-2">
              <Clock className="h-3 w-3 flex-shrink-0" />
              <span>Last checked: {formatTime(lastCheckedAt)}</span>
            </div>

            {/* Latency (if connected) */}
            {isConnected && latency !== null && (
              <div className="flex items-center gap-2">
                <Zap className="h-3 w-3 flex-shrink-0" />
                <span>Latency: {latency}ms</span>
              </div>
            )}

            {/* Error message (if disconnected) */}
            {!isConnected && lastError && (
              <div className="mt-2 p-2 bg-red-50 rounded text-red-700 text-xs">{lastError}</div>
            )}
          </div>

          {/* Start command (if disconnected) */}
          {!isConnected && (
            <div className="mt-3 pt-3 border-t border-border-light">
              <div className="flex items-center gap-2 mb-2 text-xs text-text-secondary">
                <Terminal className="h-3 w-3" />
                <span>Start backend:</span>
              </div>
              <button
                onClick={copyCommand}
                className={cn(
                  'w-full text-left p-2 rounded text-xs',
                  'bg-slate-100 hover:bg-slate-200',
                  'font-mono text-slate-700',
                  'transition-colors duration-150',
                  'truncate'
                )}
                title="Click to copy"
              >
                {startCommand}
              </button>
              <p className="text-xs text-text-tertiary mt-1 text-center">Click to copy</p>
            </div>
          )}

          {/* Retry button */}
          <button
            onClick={retry}
            disabled={isChecking}
            className={cn(
              'mt-3 w-full flex items-center justify-center gap-2',
              'py-2 px-3 rounded-md text-sm font-medium',
              'bg-gold-100 hover:bg-gold-200 text-gold-800',
              'disabled:opacity-50 disabled:cursor-not-allowed',
              'transition-colors duration-150'
            )}
          >
            <RefreshCw className={cn('h-4 w-4', isChecking && 'animate-spin')} />
            {isChecking ? 'Checking...' : 'Retry Now'}
          </button>
        </div>
      )}

      {/* Status dot button */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        onMouseEnter={() => !isExpanded && setIsExpanded(true)}
        className={cn(
          'group relative',
          'w-8 h-8 rounded-full',
          'flex items-center justify-center',
          'bg-paper border border-border-light shadow-efir-sm',
          'hover:shadow-efir-md',
          'transition-all duration-200'
        )}
        aria-label={isConnected ? 'Backend connected' : 'Backend disconnected'}
        aria-expanded={isExpanded}
      >
        {/* The dot */}
        <div
          className={cn(
            'w-3 h-3 rounded-full',
            isConnected ? 'bg-emerald-500' : 'bg-red-500',
            isChecking && 'animate-pulse'
          )}
        />

        {/* Hover tooltip (only when not expanded) */}
        {!isExpanded && (
          <div
            className={cn(
              'absolute bottom-full right-0 mb-2',
              'px-2 py-1 rounded text-xs font-medium',
              'bg-slate-800 text-white',
              'opacity-0 group-hover:opacity-100',
              'transition-opacity duration-150',
              'whitespace-nowrap pointer-events-none'
            )}
          >
            {isChecking
              ? 'Checking connection...'
              : isConnected
                ? 'Backend connected'
                : 'Backend disconnected'}
          </div>
        )}
      </button>
    </div>
  )
}
