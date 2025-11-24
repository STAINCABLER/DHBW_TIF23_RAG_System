type ThemePreferenceOption = 'light' | 'dark' | 'system'

function sanitize(value: string | undefined, fallback: string): string {
  const trimmed = value?.trim()
  return trimmed && trimmed.length > 0 ? trimmed : fallback
}

function resolveThemePreference(value: string | undefined): ThemePreferenceOption {
  if (value === 'light' || value === 'dark' || value === 'system') {
    return value
  }
  return 'system'
}

function resolveBooleanFlag(value: string | undefined): boolean {
  return value?.trim()?.toLowerCase() === 'true'
}

export const appConfig = {
  appName: sanitize(import.meta.env.VITE_APP_NAME, 'Knowledge Console'),
  footerLabel: sanitize(import.meta.env.VITE_APP_FOOTER, 'RAG System'),
  releaseVersion: sanitize(import.meta.env.VITE_APP_RELEASE, 'Release 0.1.0'),
  searchPlaceholder: 'Search databases, documents & chats',
  defaultTheme: resolveThemePreference(import.meta.env.VITE_DEFAULT_THEME),
  mockModeEnabled: resolveBooleanFlag(import.meta.env.VITE_USE_MOCK),
  defaultPalette: sanitize(import.meta.env.VITE_DEFAULT_PALETTE, 'green-07'),
  apiBaseUrl: sanitize(import.meta.env.VITE_API_BASE_URL, '/api'),
} as const
