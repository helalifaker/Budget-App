import { ReactNode } from 'react'
import { Breadcrumbs } from './Breadcrumbs'

interface PageContainerProps {
  title: string
  description?: string
  actions?: ReactNode
  children: ReactNode
}

export function PageContainer({ title, description, actions, children }: PageContainerProps) {
  return (
    <div>
      <Breadcrumbs />

      <div className="mb-6">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">{title}</h1>
            {description && <p className="mt-2 text-sm text-gray-600">{description}</p>}
          </div>
          {actions && <div>{actions}</div>}
        </div>
      </div>

      <div className="bg-white rounded-lg shadow p-6">{children}</div>
    </div>
  )
}
