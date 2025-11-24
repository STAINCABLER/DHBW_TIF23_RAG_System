import { Link, useNavigate } from 'react-router-dom'
import { FormEvent, useCallback, useEffect, useState } from 'react'
import { useAuth } from '../auth/useAuth'
import { appConfig } from '../config/appConfig'
import { apiClient } from '../api/client'

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
  const shouldCheckBackend = !mockModeEnabled
  const [backendReachable, setBackendReachable] = useState(true)
  const [checkingBackend, setCheckingBackend] = useState(shouldCheckBackend)
  const [submitting, setSubmitting] = useState(false)

  const checkBackend = useCallback(async () => {
    if (!shouldCheckBackend) return true
    setCheckingBackend(true)
    try {
      const reachable = await apiClient.checkBackendHealth()
      setBackendReachable(reachable)
      return reachable
    } catch {
      setBackendReachable(false)
      return false
    } finally {
      setCheckingBackend(false)
    }
  }, [shouldCheckBackend])

  useEffect(() => {
    if (!shouldCheckBackend) return
    void checkBackend()
  }, [checkBackend, shouldCheckBackend])

  const handleSubmit = useCallback(
    async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault()
      setError(null)

      const form = new FormData(event.currentTarget)
      const email = ((form.get('email') as string) ?? '').trim()
      const password = ((form.get('password') as string) ?? '').trim()

      if (!isLogin) {
        setError(
          mockModeEnabled
            ? 'Registrierung ist im Mock-Modus deaktiviert. Bitte nutze einen Test-Login.'
            : 'Registrierung ist in dieser Oberfläche noch nicht verdrahtet. Bitte verwende ein durch das Backend angelegtes Konto.',
        )
        return
      }

      if (mockModeEnabled) {
        const result = login(email, password)
        if (!result.success) {
          setError(result.message)
          return
        }
        setError(null)
        navigate('/dash')
        return
      }

      const reachable = backendReachable || (await checkBackend())
      if (!reachable) {
        setError('Backend aktuell nicht erreichbar. Bitte versuche es in Kürze erneut.')
        return
      }

      try {
        setSubmitting(true)
        const result = await apiClient.login(email, password)
        if (!result.ok) {
          setError(result.message ?? 'Login fehlgeschlagen.')
          return
        }
        setError(null)
        navigate('/dash')
      } catch (requestError) {
        const message = requestError instanceof Error ? requestError.message : 'Unbekannter Fehler'
        setError(`Login fehlgeschlagen: ${message}`)
      } finally {
        setSubmitting(false)
      }
    },
    [backendReachable, checkBackend, isLogin, login, mockModeEnabled, navigate],
  )

  return (
    <div className="auth-layout">
      <div className="auth-card">
        <p className="u-no-select auth-card__eyebrow">Retrieval Access</p>
        <h1 className="u-no-select">{isLogin ? 'Sign in' : 'Create account'}</h1>
        {!mockModeEnabled && (
          <div className="auth-card__alert" role="status" aria-live="polite">
            {checkingBackend ? (
              <p>Verbindung zum Backend wird geprüft …</p>
            ) : backendReachable ? (
              <p>Backend verbunden – Login nutzt jetzt den produktiven Endpunkt.</p>
            ) : (
              <>
                <strong>Backend nicht erreichbar</strong>
                <p>Stelle sicher, dass der Server unter {appConfig.apiBaseUrl} verfügbar ist und versuche es erneut.</p>
                <button type="button" className="btn btn--ghost btn--compact" onClick={() => void checkBackend()}>
                  Erneut prüfen
                </button>
              </>
            )}
          </div>
        )}
        <form className="form-grid" onSubmit={handleSubmit}>
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
          <button type="submit" className="btn btn--primary" disabled={submitting}>
            {submitting ? 'Processing…' : isLogin ? 'Sign in' : 'Register'}
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
          Back to landing
        </Link>
      </div>
    </div>
  )
}
