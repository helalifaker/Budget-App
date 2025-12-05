import { useAuth } from '@/contexts/AuthContext'
import { useNavigate } from '@tanstack/react-router'
import { Button } from '@/components/ui/button'
import { GlobalVersionSelector } from '@/components/GlobalVersionSelector'
import { toast } from 'sonner'
import { LogOut, User } from 'lucide-react'

export function Header() {
  const { user, signOut } = useAuth()
  const navigate = useNavigate()

  const handleSignOut = async () => {
    const { error } = await signOut()

    if (error) {
      toast.error('Sign out failed', {
        description: error.message,
      })
    } else {
      toast.success('Signed out successfully', {
        description: 'You have been logged out',
      })
      navigate({ to: '/login' })
    }
  }

  return (
    <header className="bg-white border-b border-sand-200 h-16 flex items-center justify-between px-6">
      {/* Left: App title */}
      <div className="flex items-center space-x-4">
        <h2 className="text-lg font-display font-semibold text-brown-800">EFIR Budget</h2>
      </div>

      {/* Center: Global Version Selector */}
      <div className="flex-1 flex justify-center px-4">
        <GlobalVersionSelector />
      </div>

      {/* Right: User info & logout */}
      <div data-testid="user-menu" className="flex items-center space-x-4">
        <div data-testid="user-info" className="flex items-center gap-2 text-sm text-twilight-600">
          <User data-testid="user-avatar" className="w-4 h-4" />
          <span data-testid="user-email" className="max-w-[180px] truncate">
            {user?.email}
          </span>
        </div>
        <Button
          data-testid="logout-button"
          variant="outline"
          size="sm"
          onClick={handleSignOut}
          className="border-sand-300 text-brown-700 hover:bg-sand-50 hover:border-sand-400"
        >
          <LogOut className="w-4 h-4 mr-2" />
          Sign Out
        </Button>
      </div>
    </header>
  )
}
