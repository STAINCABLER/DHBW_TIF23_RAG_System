import { createContext } from 'react'
import type { ApiRuntimeMode } from '../api/client'

export type RuntimeStatus = 'idle' | 'checking' | 'ready' | 'error'

export type RuntimeModeContextValue = {
  preferredMode: ApiRuntimeMode
  mode: ApiRuntimeMode
  status: RuntimeStatus
  backendHealthy: boolean | null
  error: string | null
  refreshBackendHealth: () => Promise<boolean>
}

export const RuntimeModeContext = createContext<RuntimeModeContextValue | undefined>(undefined)
