import { Monitor, Moon, Sun } from 'lucide-react'
import { useTheme } from '../hooks/useTheme'

const ICONS = {
  light: Sun,
  dark: Moon,
  system: Monitor,
} as const

export function ThemeToggle() {
  const { preference, cyclePreference } = useTheme()
  const Icon = ICONS[preference]
  return (
    <button
      type="button"
      className="btn btn--ghost btn--icon"
      aria-label="Toggle color theme"
      onClick={cyclePreference}
    >
      <Icon size={18} aria-hidden />
    </button>
  )
}
