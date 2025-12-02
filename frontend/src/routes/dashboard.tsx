import { createFileRoute } from '@tanstack/react-router'
import { MainLayout } from '@/components/layout/MainLayout'

export const Route = createFileRoute('/dashboard')({
  component: DashboardPage,
})

function DashboardPage() {
  return (
    <MainLayout>
      <div>
        <h1 className="text-2xl font-bold mb-4">Dashboard</h1>
        <p className="text-gray-600">Welcome to the EFIR Budget Planning Application</p>
      </div>
    </MainLayout>
  )
}
