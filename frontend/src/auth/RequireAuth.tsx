import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from './useAuth'

/** Renders children only when logged in; otherwise sends the user to /login and back after. */
export default function RequireAuth({ children }: { children: ReactNode }) {
  const { user } = useAuth()
  const location = useLocation()

  if (user === undefined) return <p className="muted">Loading…</p>
  if (user === null) {
    return <Navigate to={`/login?next=${encodeURIComponent(location.pathname)}`} replace />
  }
  return children
}
