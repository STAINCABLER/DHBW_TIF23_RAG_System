import { createContext } from 'react'
import type { ThemeMode, ThemePreference } from './types'

export type ThemeContextValue = {
  theme: ThemeMode
  preference: ThemePreference
  setPreference: (pref: ThemePreference) => void
  cyclePreference: () => void
}

export const ThemeContext = createContext<ThemeContextValue | null>(null)
