import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { MOCK_ACCOUNTS, type MockAccount } from './mockAccounts'
import { AuthContext, type AuthContextValue, type AuthUser, type LoginResult } from './authContext'
import { appConfig } from '../config/appConfig'

const STORAGE_KEY = 'mock-auth:user-id'
const MOCK_MODE_ENABLED = appConfig.mockModeEnabled

function findAccountByEmail(email: string): MockAccount | undefined {
  const lower = email.trim().toLowerCase()
  return MOCK_ACCOUNTS.find((account) => account.email.toLowerCase() === lower)
}

function getStoredAccount(): AuthUser | null {
  if (typeof window === 'undefined') return null
  const storedId = window.localStorage.getItem(STORAGE_KEY)
  if (!storedId) return null
  const match = MOCK_ACCOUNTS.find((account) => account.id === storedId)
  return match ? { ...match } : null
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => (MOCK_MODE_ENABLED ? getStoredAccount() : null))

  useEffect(() => {
    if (!MOCK_MODE_ENABLED || typeof window === 'undefined') return
    if (user) {
      window.localStorage.setItem(STORAGE_KEY, user.id)
    } else {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  }, [user])

  const login = useCallback((email: string, password: string): LoginResult => {
    if (!MOCK_MODE_ENABLED) {
      return { success: false, message: 'Mock-Authentifizierung ist deaktiviert. Setze VITE_USE_MOCK=true.' }
    }
    const match = findAccountByEmail(email)
    if (!match || match.password !== password.trim()) {
      return { success: false, message: 'Ungültige Zugangsdaten für den Mock-Modus.' }
    }
    setUser({ id: match.id, displayName: match.displayName, role: match.role, email: match.email })
    return { success: true }
  }, [])

  const logout = useCallback(() => {
    if (!MOCK_MODE_ENABLED) return
    setUser(null)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user: MOCK_MODE_ENABLED ? user : null,
      isAdmin: MOCK_MODE_ENABLED && user?.role === 'admin',
      login,
      logout,
    }),
    [login, logout, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
