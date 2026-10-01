import { useContext } from 'react'
import { type AuthState, AuthContext } from './context'

export function useAuth(): AuthState {
  const auth = useContext(AuthContext)
  if (!auth) throw new Error('useAuth must be used inside <AuthProvider>')
  return auth
}
