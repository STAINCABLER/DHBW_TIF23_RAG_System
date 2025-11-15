import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { apiClient } from '../api/client'
import type { Account, SessionToken } from '../api/types'
import { formatDate } from '../utils/formatters'

export function AccountPage() {
  const [account, setAccount] = useState<Account | null>(null)
  const [sessions, setSessions] = useState<SessionToken[]>([])
  const [profileForm, setProfileForm] = useState({ displayName: '', email: '' })
  const [securityForm, setSecurityForm] = useState({ password: '', confirm: '' })

  useEffect(() => {
    apiClient
      .getAccount()
      .then((data) => {
        setAccount(data)
        setProfileForm({ displayName: data.displayName, email: data.email })
      })
      .catch(console.error)
    apiClient.getSessions().then(setSessions).catch(console.error)
  }, [])

  const handleProfileSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
  }

  const handleSecuritySubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSecurityForm({ password: '', confirm: '' })
  }

  const handleLogoutAll = () => {
    console.info('Logout all sessions requested')
  }

  return (
    <div className="page page--account">
      <header className="page__header">
        <div>
          <p className="page__eyebrow u-no-select">Your profile</p>
          <h1 className="page__title u-no-select">Account & Sessions</h1>
        </div>
        <p className="u-no-select">Passe Profil & Sicherheit hier an; Session-Logout findest du unter der Tabelle.</p>
      </header>

      {account && (
        <section className="card-grid">
          <article className="card">
            <header className="card__header">
              <p className="card__eyebrow u-no-select">Profile details</p>
            </header>
            <form className="form-grid" onSubmit={handleProfileSubmit}>
              <label>
                <span className="u-no-select">Display name</span>
                <input
                  type="text"
                  value={profileForm.displayName}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, displayName: event.target.value }))}
                  required
                />
              </label>
              <label>
                <span className="u-no-select">E-Mail</span>
                <input
                  type="email"
                  value={profileForm.email}
                  onChange={(event) => setProfileForm((prev) => ({ ...prev, email: event.target.value }))}
                  required
                />
              </label>
              <button type="submit" className="btn btn--primary">
                Save profile
              </button>
            </form>
          </article>
          <article className="card">
            <header className="card__header">
              <p className="card__eyebrow u-no-select">Security</p>
            </header>
            <form className="form-grid" onSubmit={handleSecuritySubmit}>
              <label>
                <span className="u-no-select">New password</span>
                <input
                  type="password"
                  value={securityForm.password}
                  onChange={(event) => setSecurityForm((prev) => ({ ...prev, password: event.target.value }))}
                  required
                />
              </label>
              <label>
                <span className="u-no-select">Confirm password</span>
                <input
                  type="password"
                  value={securityForm.confirm}
                  onChange={(event) => setSecurityForm((prev) => ({ ...prev, confirm: event.target.value }))}
                  required
                />
              </label>
              <button type="submit" className="btn btn--secondary">
                Update password
              </button>
            </form>
          </article>
          <article className="card">
            <p className="card__eyebrow u-no-select">Created</p>
            <p className="card__body">{formatDate(account.createdAt)}</p>
          </article>
        </section>
      )}

      <section>
        <h2 className="u-no-select">Active Sessions</h2>
        <div className="table-wrapper">
          <table>
            <thead>
              <tr className="u-no-select">
                <th>Token</th>
                <th>Device</th>
                <th>Location</th>
                <th>Created</th>
                <th>Last Used</th>
              </tr>
            </thead>
            <tbody>
              {sessions.map((session) => (
                <tr key={session.tokenId}>
                  <td className="u-no-select">{session.tokenId}</td>
                  <td>{session.device}</td>
                  <td>{session.location}</td>
                  <td>{formatDate(session.createdAt)}</td>
                  <td>{formatDate(session.lastUsedAt)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="account-sessions__actions">
          <button type="button" className="btn btn--primary" onClick={handleLogoutAll}>
            Logout all
          </button>
        </div>
      </section>
    </div>
  )
}
