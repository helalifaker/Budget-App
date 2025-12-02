import { useAuth } from '@/contexts/AuthContext'

export function Header() {
  const { user, signOut } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 h-16 flex items-center justify-between px-6">
      <div className="flex items-center space-x-4">
        <h2 className="text-lg font-semibold text-gray-900">Budget Planning Application</h2>
      </div>

      <div className="flex items-center space-x-4">
        <span className="text-sm text-gray-600">{user?.email}</span>
        <button
          onClick={() => signOut()}
          className="px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
        >
          Sign Out
        </button>
      </div>
    </header>
  )
}
