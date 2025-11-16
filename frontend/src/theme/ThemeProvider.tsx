import { useEffect, useMemo, useState } from 'react'
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

const STORAGE_KEY = 'dhbw_rag_theme'

export function ThemeProvider({ children }: PropsWithChildren) {
  const systemScheme = usePrefersColorScheme()
  const defaultPreference: ThemePreference = appConfig.defaultTheme
  const [preference, setPreference] = useState<ThemePreference>(() => {
    if (typeof window === 'undefined') {
      return defaultPreference
    }
    const stored = window.localStorage.getItem(STORAGE_KEY) as ThemePreference | null
    return stored ?? defaultPreference
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
    if (preference === 'system') {
      window.localStorage.removeItem(STORAGE_KEY)
    } else {
      window.localStorage.setItem(STORAGE_KEY, preference)
    }
  }, [preference])

  const value = useMemo<ThemeContextValue>(
    () => ({
      theme,
      preference,
      setPreference,
      cyclePreference: () => {
        setPreference((current) => {
          if (current === 'system') return 'light'
          if (current === 'light') return 'dark'
          return 'system'
        })
      },
    }),
    [preference, theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export type { ThemeMode, ThemePreference } from './types'
export type { ThemeContextValue } from './context'
