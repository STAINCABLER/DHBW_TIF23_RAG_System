import { useEffect, useState } from 'react'

type Scheme = 'light' | 'dark'

export function usePrefersColorScheme(): Scheme {
  const getScheme = (): Scheme => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return 'light'
    }
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'
  }

  const [scheme, setScheme] = useState<Scheme>(getScheme)

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') {
      return
    }

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = () => setScheme(mediaQuery.matches ? 'dark' : 'light')

    mediaQuery.addEventListener('change', handleChange)
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  return scheme
}
