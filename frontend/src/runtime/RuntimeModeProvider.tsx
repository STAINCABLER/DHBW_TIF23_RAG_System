import { useCallback, useEffect, useMemo, useState } from 'react'
import type { ReactNode } from 'react'
import { appConfig } from '../config/appConfig'
import { apiClient, setApiRuntimeMode, type ApiRuntimeMode } from '../api/client'
import { RuntimeModeContext, type RuntimeModeContextValue, type RuntimeStatus } from './context'

export function RuntimeModeProvider({ children }: { children: ReactNode }) {
  const preferredMode: ApiRuntimeMode = appConfig.mockModeEnabled ? 'mock' : 'productive'
  const [mode, setMode] = useState<ApiRuntimeMode>(preferredMode)
  const [status, setStatus] = useState<RuntimeStatus>(preferredMode === 'productive' ? 'checking' : 'ready')
  const [backendHealthy, setBackendHealthy] = useState<boolean | null>(
    preferredMode === 'productive' ? null : false,
  )
  const [error, setError] = useState<string | null>(null)

  const evaluateBackend = useCallback(async () => {
    if (preferredMode !== 'productive') {
      setMode('mock')
      setApiRuntimeMode('mock')
      setBackendHealthy(false)
      setStatus('ready')
      setError(null)
      return false
    }

    setStatus('checking')
    setError(null)

    const healthy = await apiClient.checkBackendHealth({ forceNetwork: true })
    setBackendHealthy(healthy)
    const nextMode: ApiRuntimeMode = healthy ? 'productive' : 'mock'
    setMode(nextMode)
    setApiRuntimeMode(nextMode)
    setStatus('ready')
    if (!healthy) {
      setError('Backend nicht erreichbar')
    }
    return healthy
  }, [preferredMode])

  useEffect(() => {
    let cancelled = false
    const run = async () => {
      const healthy = await evaluateBackend()
      if (cancelled) return
      if (preferredMode === 'productive' && !healthy) {
        console.warn('Backend health check failed, fallback to mock mode.')
      }
    }
    void run()
    return () => {
      cancelled = true
    }
  }, [evaluateBackend, preferredMode])

  const refreshBackendHealth = useCallback(async () => {
    return evaluateBackend()
  }, [evaluateBackend])

  useEffect(() => {
    setApiRuntimeMode(mode)
  }, [mode])

  const value = useMemo<RuntimeModeContextValue>(
    () => ({
      preferredMode,
      mode,
      status,
      backendHealthy,
      error,
      refreshBackendHealth,
    }),
    [backendHealthy, error, mode, preferredMode, refreshBackendHealth, status],
  )

  return <RuntimeModeContext.Provider value={value}>{children}</RuntimeModeContext.Provider>
}
