import { useAuth } from '@/contexts/AuthContext'

export function LogoutButton() {
  const { signOut } = useAuth()

  return (
    <button
      onClick={() => signOut()}
      className="rounded-md bg-red-600 px-4 py-2 text-white hover:bg-red-700"
    >
      Sign Out
    </button>
  )
}
