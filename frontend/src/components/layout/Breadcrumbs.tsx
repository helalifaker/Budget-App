import { Link, useMatches } from '@tanstack/react-router'

export function Breadcrumbs() {
  const matches = useMatches()

  return (
    <nav className="flex mb-4" aria-label="Breadcrumb">
      <ol className="inline-flex items-center space-x-1 md:space-x-3">
        {matches.map((match, index) => {
          const isLast = index === matches.length - 1

          return (
            <li key={match.id} className="inline-flex items-center">
              {index > 0 && <span className="mx-2 text-gray-400">/</span>}
              {isLast ? (
                <span className="text-gray-700 font-medium">{match.pathname}</span>
              ) : (
                <Link to={match.pathname} className="text-gray-500 hover:text-gray-700">
                  {match.pathname}
                </Link>
              )}
            </li>
          )
        })}
      </ol>
    </nav>
  )
}
