import { createContext } from 'react'
import type { ThemeMode, ThemePreference } from './types'

export type ThemeContextValue = {
  theme: ThemeMode
  preference: ThemePreference
  manualPreference: ThemeMode
  setPreference: (pref: ThemePreference) => void
  setAutoTheme: (enabled: boolean) => void
  toggleManualTheme: () => void
}

export const ThemeContext = createContext<ThemeContextValue | null>(null)
