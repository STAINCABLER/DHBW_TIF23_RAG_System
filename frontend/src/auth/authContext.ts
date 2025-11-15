import { createContext } from 'react'
import type { MockAccount } from './mockAccounts'

export type AuthUser = Pick<MockAccount, 'id' | 'displayName' | 'role' | 'email'>

export type LoginResult = { success: true } | { success: false; message: string }

export type AuthContextValue = {
  user: AuthUser | null
  isAdmin: boolean
  login: (email: string, password: string) => LoginResult
  logout: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
