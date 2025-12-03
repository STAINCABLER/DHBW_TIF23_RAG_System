import { useContext } from 'react'
import { RuntimeModeContext } from './context'

export function useRuntimeMode() {
  const context = useContext(RuntimeModeContext)
  if (!context) {
    throw new Error('useRuntimeMode must be used within RuntimeModeProvider')
  }
  return context
}
