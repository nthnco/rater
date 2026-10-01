import { createContext } from 'react'
import type { User } from '../api'

export type AuthState = {
  /** undefined while we're still asking the server; null when logged out. */
  user: User | null | undefined
  signup: (email: string, password: string) => Promise<void>
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
}

export const AuthContext = createContext<AuthState | null>(null)
