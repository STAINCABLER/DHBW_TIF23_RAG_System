import { createContext } from 'react'
import type { MockAccount } from './mockAccounts'
import type { ApiRuntimeMode } from '../api/client'

export type AuthUser = Pick<MockAccount, 'id' | 'displayName' | 'role' | 'email'>

export type LoginResult = { success: true } | { success: false; message: string }

export type AuthContextValue = {
  user: AuthUser | null
  isAdmin: boolean
  isReady: boolean
  mode: ApiRuntimeMode
  login: (email: string, password: string) => Promise<LoginResult>
  logout: () => Promise<void>
  refresh: () => Promise<void>
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
