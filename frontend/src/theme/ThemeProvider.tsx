import { useCallback, useEffect, useMemo, useState } from 'react'
import type { PropsWithChildren } from 'react'
import { usePrefersColorScheme } from '../hooks/usePrefersColorScheme'
import { appConfig } from '../config/appConfig'
import { ThemeContext } from './context'
import type { ThemeContextValue } from './context'
import type { ThemePreference } from './types'
import { themes } from './themes.generated'

type ThemeMode = 'light' | 'dark'

type ThemeDefinition = {
  colorScheme: ThemeMode
  bg: string
  surface: string
  surfaceAlt: string
  border: string
  text: string
  muted: string
  primary: string
  primarySoft: string
  shadowSoft: string
}

type GeneratedThemes = Record<string, Record<ThemeMode, ThemeDefinition>>

const PREFERENCE_STORAGE_KEY = 'dhbw_rag_theme_v2'
const MANUAL_STORAGE_KEY = 'dhbw_rag_theme_manual_v2'

const isThemeMode = (value: string | null): value is ThemeMode => value === 'light' || value === 'dark'
const isThemePreference = (value: string | null): value is ThemePreference =>
  value === 'light' || value === 'dark' || value === 'system'

export function ThemeProvider({ children }: PropsWithChildren) {
  const systemScheme = usePrefersColorScheme()
  const defaultPreference: ThemePreference = appConfig.defaultTheme
  const [preference, setPreferenceState] = useState<ThemePreference>(() => {
    if (typeof window === 'undefined') {
      return defaultPreference
    }
    const stored = window.localStorage.getItem(PREFERENCE_STORAGE_KEY)
    if (isThemePreference(stored)) {
      return stored
    }
    return defaultPreference
  })
  const [manualPreference, setManualPreference] = useState<ThemeMode>(() => {
    if (typeof window === 'undefined') {
      return defaultPreference === 'dark' || defaultPreference === 'light' ? defaultPreference : 'light'
    }
    const storedManual = window.localStorage.getItem(MANUAL_STORAGE_KEY)
    if (isThemeMode(storedManual)) {
      return storedManual
    }
    const storedPreference = window.localStorage.getItem(PREFERENCE_STORAGE_KEY)
    if (isThemeMode(storedPreference)) {
      return storedPreference
    }
    return defaultPreference === 'dark' || defaultPreference === 'light' ? defaultPreference : 'light'
  })

  const theme = preference === 'system' ? systemScheme : preference

  useEffect(() => {
    if (typeof document === 'undefined') return

    const mode: ThemeMode = theme === 'dark' ? 'dark' : 'light'
    const paletteId = appConfig.defaultPalette
    const themeDef = (themes as GeneratedThemes)[paletteId]?.[mode]
    if (!themeDef) return

    const root = document.documentElement

    root.style.setProperty('--color-bg', themeDef.bg)
    root.style.setProperty('--color-surface', themeDef.surface)
    root.style.setProperty('--color-surface-alt', themeDef.surfaceAlt)
    root.style.setProperty('--color-border', themeDef.border)
    root.style.setProperty('--color-text', themeDef.text)
    root.style.setProperty('--color-muted', themeDef.muted)
    root.style.setProperty('--color-primary', themeDef.primary)
    root.style.setProperty('--color-primary-soft', themeDef.primarySoft)
    root.style.setProperty('--shadow-soft', themeDef.shadowSoft)

    if (themeDef.colorScheme === 'dark') {
      root.style.colorScheme = 'dark'
    } else if (themeDef.colorScheme === 'light') {
      root.style.colorScheme = 'light'
    }
  }, [theme])

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(PREFERENCE_STORAGE_KEY, preference)
  }, [preference])

  useEffect(() => {
    if (typeof window === 'undefined') return
    window.localStorage.setItem(MANUAL_STORAGE_KEY, manualPreference)
  }, [manualPreference])

  const setPreference = useCallback((next: ThemePreference) => {
    setPreferenceState(next)
    if (next === 'light' || next === 'dark') {
      setManualPreference(next)
    }
  }, [])

  const setAutoTheme = useCallback(
    (enabled: boolean) => {
      setPreferenceState((current) => {
        if (enabled) {
          return 'system'
        }
        if (current === 'system') {
          return manualPreference
        }
        return current
      })
    },
    [manualPreference],
  )

  const toggleManualTheme = useCallback(() => {
    setManualPreference((prev) => {
      const next = prev === 'dark' ? 'light' : 'dark'
      setPreferenceState(next)
      return next
    })
  }, [])

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      preference,
      manualPreference,
      setPreference,
      setAutoTheme,
      toggleManualTheme,
    }),
    [manualPreference, preference, setAutoTheme, setPreference, theme, toggleManualTheme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export type { ThemeMode, ThemePreference } from './types'
export type { ThemeContextValue } from './context'
