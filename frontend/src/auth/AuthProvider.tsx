import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { MOCK_ACCOUNTS, type MockAccount } from './mockAccounts'
import { AuthContext, type AuthContextValue, type AuthUser, type LoginResult } from './authContext'
import { apiClient } from '../api/client'
import type { Account } from '../api/types'
import { useRuntimeMode } from '../runtime/useRuntimeMode'

const STORAGE_KEY = 'mock-auth:user-id'

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

function mapAccountToAuthUser(account: Account): AuthUser {
  const roleSource = (account as unknown as { profileType?: string }).profileType
  const role = roleSource === 'professional' || roleSource === 'researcher' ? 'admin' : 'user'

  return {
    id: account.accountId ?? `account-${crypto.randomUUID()}`,
    displayName: account.displayName ?? account.email,
    email: account.email,
    role,
  }
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const { mode } = useRuntimeMode()
  const isMockMode = mode === 'mock'
  const [user, setUser] = useState<AuthUser | null>(() => (isMockMode ? getStoredAccount() : null))
  const [isReady, setIsReady] = useState(false)

  const resolveUser = useCallback(async (): Promise<AuthUser | null> => {
    if (isMockMode) {
      return getStoredAccount()
    }
    try {
      const account = await apiClient.getAccount()
      return mapAccountToAuthUser(account)
    } catch {
      return null
    }
  }, [isMockMode])

  useEffect(() => {
    let cancelled = false
    // eslint-disable-next-line react-hooks/set-state-in-effect -- mark hydration start before async work resolves
    setIsReady(false)
    const hydrate = async () => {
      const nextUser = await resolveUser()
      if (cancelled) return
      setUser(nextUser)
      setIsReady(true)
    }
    void hydrate()
    return () => {
      cancelled = true
    }
  }, [resolveUser])

  useEffect(() => {
    if (!isMockMode || typeof window === 'undefined') return
    if (user) {
      window.localStorage.setItem(STORAGE_KEY, user.id)
    } else {
      window.localStorage.removeItem(STORAGE_KEY)
    }
  }, [isMockMode, user])

  const refresh = useCallback(async () => {
    const nextUser = await resolveUser()
    setUser(nextUser)
  }, [resolveUser])

  const login = useCallback(
    async (email: string, password: string): Promise<LoginResult> => {
      if (isMockMode) {
        const match = findAccountByEmail(email)
        if (!match || match.password !== password.trim()) {
          return { success: false, message: 'Ungültige Zugangsdaten für den Mock-Modus.' }
        }
        const authUser: AuthUser = {
          id: match.id,
          displayName: match.displayName,
          role: match.role,
          email: match.email,
        }
        setUser(authUser)
        return { success: true }
      }

      const result = await apiClient.login(email, password)
      if (!result.ok) {
        return { success: false, message: result.message ?? 'Login fehlgeschlagen.' }
      }

      const nextUser = await resolveUser()
      if (!nextUser) {
        return { success: false, message: 'Login erfolgreich, aber Benutzerprofil konnte nicht geladen werden.' }
      }
      setUser(nextUser)
      return { success: true }
    },
    [isMockMode, resolveUser],
  )

  const logout = useCallback(async () => {
    if (isMockMode) {
      setUser(null)
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem(STORAGE_KEY)
      }
      return
    }
    await apiClient.logout()
    setUser(null)
  }, [isMockMode])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAdmin: user?.role === 'admin',
      isReady,
      mode,
      login,
      logout,
      refresh,
    }),
    [isReady, login, logout, mode, refresh, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
