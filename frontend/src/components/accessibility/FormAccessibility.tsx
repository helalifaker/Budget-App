/**
 * Accessible Form Components
 *
 * Enhanced form components with proper ARIA attributes for accessibility.
 *
 * WCAG 2.1 Success Criteria:
 * - 1.3.1 (Level A) - Info and Relationships
 * - 3.3.1 (Level A) - Error Identification
 * - 3.3.2 (Level A) - Labels or Instructions
 * - 3.3.3 (Level AA) - Error Suggestion
 *
 * Features:
 * - Proper label associations
 * - Error announcements to screen readers
 * - Required field indicators
 * - Help text with aria-describedby
 */

import {
  forwardRef,
  useId,
  cloneElement,
  isValidElement,
  type ReactNode,
  type ReactElement,
} from 'react'
import { cn } from '@/lib/utils'
import { AlertCircle, CheckCircle2, HelpCircle } from 'lucide-react'

// ============================================================================
// Form Field Wrapper
// ============================================================================

interface FormFieldProps {
  children: ReactNode
  label: string
  htmlFor?: string
  required?: boolean
  error?: string
  hint?: string
  success?: string
  className?: string
}

/**
 * FormField wraps form inputs with proper labels, errors, and hints.
 */
export function FormField({
  children,
  label,
  htmlFor,
  required = false,
  error,
  hint,
  success,
  className,
}: FormFieldProps) {
  const id = useId()
  const inputId = htmlFor || id
  const errorId = `${inputId}-error`
  const hintId = `${inputId}-hint`
  const successId = `${inputId}-success`

  // Build aria-describedby
  const describedBy =
    [error && errorId, hint && hintId, success && successId].filter(Boolean).join(' ') || undefined

  return (
    <div className={cn('space-y-1.5', className)}>
      {/* Label */}
      <label htmlFor={inputId} className="block text-sm font-medium text-text-primary">
        {label}
        {required && (
          <span className="text-error-500 ml-1" aria-hidden="true">
            *
          </span>
        )}
        {required && <span className="sr-only"> (required)</span>}
      </label>

      {/* Hint text (before input for screen reader order) */}
      {hint && (
        <p id={hintId} className="text-xs text-text-secondary flex items-center gap-1">
          <HelpCircle className="h-3 w-3" aria-hidden="true" />
          {hint}
        </p>
      )}

      {/* Input wrapper - clone child with proper aria attributes */}
      <div className="relative">
        {/* Inject aria attributes into child */}
        {isValidElement(children)
          ? cloneElement(children as ReactElement<Record<string, unknown>>, {
              id: inputId,
              'aria-invalid': error ? true : undefined,
              'aria-describedby': describedBy,
              'aria-required': required || undefined,
            })
          : children}
      </div>

      {/* Error message */}
      {error && (
        <p
          id={errorId}
          role="alert"
          aria-live="assertive"
          className="text-xs text-error-600 flex items-center gap-1"
        >
          <AlertCircle className="h-3 w-3" aria-hidden="true" />
          {error}
        </p>
      )}

      {/* Success message */}
      {success && (
        <p
          id={successId}
          role="status"
          aria-live="polite"
          className="text-xs text-sage-600 flex items-center gap-1"
        >
          <CheckCircle2 className="h-3 w-3" aria-hidden="true" />
          {success}
        </p>
      )}
    </div>
  )
}

// ============================================================================
// Accessible Input
// ============================================================================

interface AccessibleInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: boolean
}

/**
 * AccessibleInput with built-in error state styling.
 */
export const AccessibleInput = forwardRef<HTMLInputElement, AccessibleInputProps>(
  function AccessibleInput({ error, className, ...props }, ref) {
    return (
      <input
        ref={ref}
        className={cn(
          'w-full px-3 py-2 text-sm rounded-lg border transition-colors',
          'bg-white text-text-primary placeholder:text-text-muted',
          'focus:outline-none focus:ring-2 focus:ring-gold-500 focus:ring-offset-2',
          error ? 'border-error-500 bg-error-50' : 'border-border-medium hover:border-text-muted',
          className
        )}
        {...props}
      />
    )
  }
)

// ============================================================================
// Accessible Textarea
// ============================================================================

interface AccessibleTextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  error?: boolean
}

/**
 * AccessibleTextarea with built-in error state styling.
 */
export const AccessibleTextarea = forwardRef<HTMLTextAreaElement, AccessibleTextareaProps>(
  function AccessibleTextarea({ error, className, ...props }, ref) {
    return (
      <textarea
        ref={ref}
        className={cn(
          'w-full px-3 py-2 text-sm rounded-lg border transition-colors min-h-[100px]',
          'bg-white text-text-primary placeholder:text-text-muted',
          'focus:outline-none focus:ring-2 focus:ring-gold-500 focus:ring-offset-2',
          error ? 'border-error-500 bg-error-50' : 'border-border-medium hover:border-text-muted',
          className
        )}
        {...props}
      />
    )
  }
)

// ============================================================================
// Form Error Summary
// ============================================================================

interface FormErrorSummaryProps {
  errors: { field: string; message: string }[]
  title?: string
}

/**
 * FormErrorSummary displays a summary of all form errors.
 * Should be placed at the top of the form.
 */
export function FormErrorSummary({
  errors,
  title = 'Please fix the following errors:',
}: FormErrorSummaryProps) {
  if (errors.length === 0) return null

  return (
    <div
      role="alert"
      aria-live="assertive"
      className="p-4 rounded-lg bg-error-50 border border-error-200 mb-4"
    >
      <div className="flex gap-3">
        <AlertCircle className="h-5 w-5 text-error-500 flex-shrink-0 mt-0.5" aria-hidden="true" />
        <div>
          <h3 className="text-sm font-medium text-error-800">{title}</h3>
          <ul className="mt-2 text-sm text-error-700 list-disc list-inside space-y-1">
            {errors.map((error, index) => (
              <li key={index}>
                <a
                  href={`#${error.field}`}
                  className="underline hover:text-error-900 focus:outline-none focus:ring-2 focus:ring-error-500"
                  onClick={(e) => {
                    e.preventDefault()
                    const element = document.getElementById(error.field)
                    if (element) {
                      element.focus()
                      element.scrollIntoView({ behavior: 'smooth', block: 'center' })
                    }
                  }}
                >
                  {error.message}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  )
}

// ============================================================================
// Character Counter
// ============================================================================

interface CharacterCounterProps {
  current: number
  max: number
  id?: string
}

/**
 * CharacterCounter shows remaining characters for text inputs.
 */
export function CharacterCounter({ current, max, id }: CharacterCounterProps) {
  const remaining = max - current
  const isOverLimit = remaining < 0
  const isNearLimit = remaining <= 20 && remaining >= 0

  return (
    <p
      id={id}
      role="status"
      aria-live="polite"
      className={cn(
        'text-xs',
        isOverLimit && 'text-error-600 font-medium',
        isNearLimit && !isOverLimit && 'text-terracotta-600',
        !isOverLimit && !isNearLimit && 'text-text-tertiary'
      )}
    >
      {isOverLimit ? (
        <span>
          <span className="sr-only">Over limit by </span>
          {Math.abs(remaining)} characters over limit
        </span>
      ) : (
        <span>
          <span className="sr-only">
            {remaining} characters remaining out of {max}
          </span>
          <span aria-hidden="true">
            {current}/{max}
          </span>
        </span>
      )}
    </p>
  )
}

// ============================================================================
// Required Fields Legend
// ============================================================================

/**
 * RequiredFieldsLegend explains the required field indicator.
 * Place at the start of forms.
 */
export function RequiredFieldsLegend() {
  return (
    <p className="text-xs text-text-secondary mb-4">
      Fields marked with{' '}
      <span className="text-error-500" aria-hidden="true">
        *
      </span>
      <span className="sr-only">an asterisk</span> are required.
    </p>
  )
}

export default FormField
