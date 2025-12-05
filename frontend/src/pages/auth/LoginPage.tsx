import { useState, FormEvent, useEffect } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { useAuth } from '@/contexts/AuthContext'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardHeader } from '@/components/ui/card'
import { toast } from 'sonner'
import { School, Loader2 } from 'lucide-react'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const { signIn, user } = useAuth()
  const navigate = useNavigate()

  // Redirect to dashboard if already authenticated
  useEffect(() => {
    if (user) {
      navigate({ to: '/dashboard' })
    }
  }, [user, navigate])

  const handleSubmit = async (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const { error } = await signIn(email, password)

      if (error) {
        toast.error('Login failed', {
          description: error.message || 'Invalid email or password',
        })
      } else {
        toast.success('Welcome back!', {
          description: 'You have successfully logged in',
        })
        // Navigation will happen automatically via useEffect when user state updates
      }
    } catch {
      toast.error('Login failed', {
        description: 'An unexpected error occurred',
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <div className="flex justify-center mb-4">
            <div className="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center">
              <School className="w-10 h-10 text-white" />
            </div>
          </div>
          <h1 className="text-3xl font-bold text-gray-900">EFIR Budget Planning</h1>
          <h2 className="text-xl font-semibold text-gray-700 mt-2">Sign In</h2>
          <CardDescription>
            Enter your credentials to access the budget planning application
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form data-testid="login-form" onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                name="email"
                data-testid="email-input"
                type="email"
                placeholder="your.email@efir.fr"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="email"
                autoFocus
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                data-testid="password-input"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
                autoComplete="current-password"
              />
            </div>
            <Button
              type="submit"
              data-testid="submit-button"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>

          {/* Development helper */}
          {import.meta.env.DEV && import.meta.env.VITE_E2E_TEST_MODE === 'true' && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <p className="text-sm text-blue-800 font-medium mb-2">Test Mode Active</p>
              <p className="text-xs text-blue-700 mb-3">
                Using mock authentication. Choose a test account:
              </p>
              <div className="space-y-1.5 text-xs">
                <div className="flex items-center justify-between bg-white p-2 rounded">
                  <span className="font-medium text-blue-900">Admin:</span>
                  <code className="text-blue-700">admin@efir.local</code>
                </div>
                <div className="flex items-center justify-between bg-white p-2 rounded">
                  <span className="font-medium text-blue-900">Manager:</span>
                  <code className="text-blue-700">manager@efir.local</code>
                </div>
                <div className="flex items-center justify-between bg-white p-2 rounded">
                  <span className="font-medium text-blue-900">HR:</span>
                  <code className="text-blue-700">hr@efir.local</code>
                </div>
                <div className="flex items-center justify-between bg-white p-2 rounded">
                  <span className="font-medium text-blue-900">Academic:</span>
                  <code className="text-blue-700">academic@efir.local</code>
                </div>
                <div className="flex items-center justify-between bg-white p-2 rounded">
                  <span className="font-medium text-blue-900">Viewer:</span>
                  <code className="text-blue-700">user@efir.local</code>
                </div>
                <p className="text-blue-600 font-medium mt-2 pt-2 border-t border-blue-200">
                  Password: <code className="bg-blue-100 px-2 py-0.5 rounded">password123</code>
                </p>
              </div>
            </div>
          )}
          {import.meta.env.DEV && import.meta.env.VITE_E2E_TEST_MODE !== 'true' && (
            <div className="mt-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800 font-medium mb-2">Development Mode</p>
              <p className="text-xs text-yellow-700">
                Configure Supabase credentials in your .env file or enable test mode by setting{' '}
                <code className="bg-yellow-100 px-1 rounded">VITE_E2E_TEST_MODE=true</code>
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
