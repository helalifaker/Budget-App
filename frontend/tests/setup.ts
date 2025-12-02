/**
 * Global test setup for Vitest
 *
 * This file runs before all tests and sets up necessary polyfills
 * and global configurations for the test environment.
 */

import { expect, afterEach, vi } from 'vitest'
import { cleanup } from '@testing-library/react'
import * as matchers from '@testing-library/jest-dom/matchers'

// Extend Vitest's expect with jest-dom matchers
expect.extend(matchers)

// Cleanup after each test
afterEach(() => {
  cleanup()
})

// =============================================================================
// jsdom Polyfills for Radix UI Components
// =============================================================================

/**
 * Radix UI components use pointer events API that jsdom doesn't fully support.
 * These polyfills ensure components work correctly in test environment.
 */

// Extend HTMLElement interface for pointer capture polyfills
interface HTMLElementWithPointerCapture extends HTMLElement {
  _pointerCapture?: number
}

// Polyfill for HTMLElement.prototype.hasPointerCapture
if (typeof HTMLElement !== 'undefined' && !HTMLElement.prototype.hasPointerCapture) {
  HTMLElement.prototype.hasPointerCapture = function (pointerId: number): boolean {
    return (this as HTMLElementWithPointerCapture)._pointerCapture === pointerId
  }
}

// Polyfill for HTMLElement.prototype.setPointerCapture
if (typeof HTMLElement !== 'undefined' && !HTMLElement.prototype.setPointerCapture) {
  HTMLElement.prototype.setPointerCapture = function (pointerId: number): void {
    ;(this as HTMLElementWithPointerCapture)._pointerCapture = pointerId
  }
}

// Polyfill for HTMLElement.prototype.releasePointerCapture
if (typeof HTMLElement !== 'undefined' && !HTMLElement.prototype.releasePointerCapture) {
  HTMLElement.prototype.releasePointerCapture = function (pointerId: number): void {
    const element = this as HTMLElementWithPointerCapture
    if (element._pointerCapture === pointerId) {
      delete element._pointerCapture
    }
  }
}

// Polyfill for Element.prototype.scrollIntoView
if (typeof Element !== 'undefined' && !Element.prototype.scrollIntoView) {
  Element.prototype.scrollIntoView = vi.fn()
}

// Polyfill for window.matchMedia (used by some Radix components)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation((query: string) => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(), // deprecated
    removeListener: vi.fn(), // deprecated
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Polyfill for ResizeObserver
global.ResizeObserver = class ResizeObserver {
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
}

// Polyfill for IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
  constructor() {}
  observe = vi.fn()
  unobserve = vi.fn()
  disconnect = vi.fn()
  root = null
  rootMargin = ''
  thresholds = []
  takeRecords = vi.fn(() => [])
}

// =============================================================================
// Mock console methods to reduce noise in test output
// =============================================================================

// Suppress console.warn for known issues
const originalWarn = console.warn
console.warn = (...args: unknown[]) => {
  // Filter out known warnings that are not actionable in tests
  const warningString = args[0]?.toString() || ''

  const knownWarnings = ['React does not recognize', 'Invalid prop', 'Failed prop type']

  if (!knownWarnings.some((known) => warningString.includes(known))) {
    originalWarn(...args)
  }
}

// =============================================================================
// Test utilities
// =============================================================================

/**
 * Delay utility for testing async operations
 * @param ms - milliseconds to delay
 */
export const delay = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))
