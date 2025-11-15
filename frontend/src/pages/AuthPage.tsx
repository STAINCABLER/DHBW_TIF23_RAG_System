import { Link, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import { useAuth } from '../auth/useAuth'
import { appConfig } from '../config/appConfig'

type Mode = 'login' | 'register'

type Props = {
  mode: Mode
}

export function AuthPage({ mode }: Props) {
  const isLogin = mode === 'login'
  const navigate = useNavigate()
  const { login } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const mockModeEnabled = appConfig.mockModeEnabled

  return (
    <div className="auth-layout">
      <div className="auth-card">
        <p className="u-no-select auth-card__eyebrow">Retrieval Access</p>
        <h1 className="u-no-select">{isLogin ? 'Sign in' : 'Create account'}</h1>
        <form
          className="form-grid"
          onSubmit={(event) => {
            event.preventDefault()
            if (!isLogin) {
              if (mockModeEnabled) {
                setError('Registrierung ist im Mock-Modus deaktiviert. Bitte nutze einen Test-Login.')
              } else {
                setError('Registrierung erfordert ein angebundenes Backend und ist hier deaktiviert.')
              }
              return
            }
            if (!mockModeEnabled) {
              setError('Login ist im Demo-Modus deaktiviert. Aktiviere VITE_USE_MOCK oder verbinde ein Backend.')
              return
            }
            const form = new FormData(event.currentTarget)
            const email = (form.get('email') as string) ?? ''
            const password = (form.get('password') as string) ?? ''
            const result = login(email, password)
            if (!result.success) {
              setError(result.message)
              return
            }
            setError(null)
            navigate('/')
          }}
        >
          {!isLogin && (
            <label>
              <span className="u-no-select">Display Name</span>
              <input type="text" placeholder="Alex Example" required />
            </label>
          )}
          <label>
            <span className="u-no-select">E-mail</span>
            <input type="email" name="email" placeholder="user@example.com" required autoComplete="email" />
          </label>
          <label>
            <span className="u-no-select">Password</span>
            <input
              type="password"
              name="password"
              placeholder="••••••"
              required
              autoComplete={isLogin ? 'current-password' : 'new-password'}
            />
          </label>
          <button type="submit" className="btn btn--primary">
            {isLogin ? 'Sign in' : 'Register'}
          </button>
        </form>
        {error && <p role="alert">{error}</p>}

        {mockModeEnabled && (
          <div className="auth-card__info">
            <p className="u-no-select">Verfügbare Test-Logins (Mock-Modus):</p>
            <ul>
              <li>
                <strong>Test User</strong> — test.user@example.com / <code>user-pass</code>
              </li>
              <li>
                <strong>Test Admin</strong> — test.admin@example.com / <code>admin-pass</code>
              </li>
            </ul>
          </div>
        )}

        <p>
          {isLogin ? 'Need an account?' : 'Already on the platform?'}{' '}
          <Link to={isLogin ? '/register' : '/login'}>{isLogin ? 'Register' : 'Go to login'}</Link>
        </p>
        <Link to="/" className="link link--subtle">
          Back to dashboard
        </Link>
      </div>
    </div>
  )
}
