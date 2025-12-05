import { ReactNode } from 'react'
import { EnhancedSidebar } from './EnhancedSidebar'
import { Header } from './Header'
import { CommandPalette } from '@/components/CommandPalette'
import { cn } from '@/lib/utils'

interface MainLayoutProps {
  children: ReactNode
}

export function MainLayout({ children }: MainLayoutProps) {
  return (
    <div
      className={cn('flex h-screen', 'bg-gradient-to-br from-cream-50 via-sand-50 to-cream-100')}
    >
      <EnhancedSidebar />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header />
        <main
          className={cn(
            'flex-1 overflow-y-auto p-6',
            'bg-gradient-to-b from-transparent to-sand-50/50'
          )}
        >
          {children}
        </main>
      </div>

      {/* Global Command Palette (Cmd+K) */}
      <CommandPalette />
    </div>
  )
}
