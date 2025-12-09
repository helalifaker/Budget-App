import * as React from 'react'

import { cn } from '@/lib/utils'

const Textarea = React.forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(({ className, ...props }, ref) => {
  return (
    <textarea
      className={cn(
        'flex min-h-[80px] w-full rounded-button border border-border-medium bg-white px-3 py-2 text-sm text-text-secondary placeholder:text-text-muted',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-gold-500 focus-visible:border-gold-500',
        'disabled:cursor-not-allowed disabled:opacity-50',
        'transition-colors duration-200',
        className
      )}
      ref={ref}
      {...props}
    />
  )
})
Textarea.displayName = 'Textarea'

export { Textarea }
