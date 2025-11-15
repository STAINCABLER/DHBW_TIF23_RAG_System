import type { FormEvent } from 'react'
import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'
import { LogIn, LogOut, Settings } from 'lucide-react'
import { ThemeToggle } from '../ThemeToggle'
import { appConfig } from '../../config/appConfig'
import { useAuth } from '../../auth/useAuth'

export function Topbar() {
  const navigate = useNavigate()
  const { user, logout } = useAuth()
  const greeting = useMemo(
    () => (user ? `Willkommen zurück, ${user.displayName}!` : 'Bitte melde dich an, um fortzufahren.'),
    [user],
  )
  const handleSearch = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const formData = new FormData(event.currentTarget)
    const query = (formData.get('query') as string) ?? ''
    if (query.trim().length === 0) return
    // Placeholder for future search integration
    console.info('Search requested:', query)
  }

  const handleLogin = () => navigate('/login')
  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  return (
    <header className="topbar">
      <form className="topbar__search" role="search" onSubmit={handleSearch}>
        <input
          type="search"
          name="query"
          placeholder={appConfig.searchPlaceholder}
          aria-label="Search knowledge base"
          autoComplete="off"
        />
      </form>

      <p className="topbar__greeting u-no-select" aria-live="polite">
        {greeting}
      </p>

      <div className="topbar__actions">
        {user ? (
          <button type="button" className="btn btn--ghost" onClick={handleLogout}>
            <LogOut size={16} aria-hidden />
            Logout
          </button>
        ) : (
          <button type="button" className="btn btn--ghost" onClick={handleLogin}>
            <LogIn size={16} aria-hidden />
            Login
          </button>
        )}
        <ThemeToggle />
        <button
          type="button"
          className="btn btn--ghost btn--icon"
          aria-label="Open account settings"
          onClick={() => navigate('/account')}
        >
          <Settings size={18} aria-hidden />
        </button>
      </div>
    </header>
  )
}
