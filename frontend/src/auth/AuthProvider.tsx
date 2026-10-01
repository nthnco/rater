import { type ReactNode, useCallback, useEffect, useMemo, useState } from 'react'
import * as api from '../api'
import { AuthContext } from './context'

// The cookie is httpOnly, so the frontend can't read it; it learns who's logged in by
// asking the server (GET /me) once on load, then tracks login/logout locally.
export default function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<api.User | null | undefined>(undefined)

  useEffect(() => {
    api
      .getMe()
      .then(setUser)
      .catch(() => setUser(null))
  }, [])

  const signup = useCallback(async (email: string, password: string) => {
    setUser(await api.signup(email, password))
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    setUser(await api.login(email, password))
  }, [])

  const logout = useCallback(async () => {
    await api.logout()
    setUser(null)
  }, [])

  const value = useMemo(() => ({ user, signup, login, logout }), [user, signup, login, logout])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
