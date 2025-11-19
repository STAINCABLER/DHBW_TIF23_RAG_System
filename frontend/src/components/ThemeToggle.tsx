import { Moon, Sun } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

export function ThemeToggle() {
  const { theme, toggleManualTheme } = useTheme()
  const isDark = theme === 'dark'
  const Icon = isDark ? Moon : Sun
  return (
    <button
      type="button"
      className="btn btn--ghost btn--icon"
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-pressed={isDark}
      onClick={toggleManualTheme}
    >
      <Icon size={18} aria-hidden />
    </button>
  )
}
