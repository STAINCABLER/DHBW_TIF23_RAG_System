import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { Pencil } from 'lucide-react'
import { apiClient } from '../api/client'
import type { Account, SessionToken } from '../api/types'
import { formatDate } from '../utils/formatters'
import { useTheme } from '../hooks/useTheme'
import { Modal } from '../components/Modal'

type EditTarget = 'displayName' | 'email' | 'password' | null

export function AccountPage() {
  const [account, setAccount] = useState<Account | null>(null)
  const [sessions, setSessions] = useState<SessionToken[]>([])
  const [editTarget, setEditTarget] = useState<EditTarget>(null)
  const [editValues, setEditValues] = useState({ primary: '', confirm: '' })
  const [editError, setEditError] = useState<string | null>(null)
  const { preference, manualPreference, setAutoTheme } = useTheme()
  const autoThemeEnabled = preference === 'system'

  useEffect(() => {
    apiClient
      .getAccount()
      .then((data) => {
        setAccount(data)
      })
      .catch(console.error)
    apiClient.getSessions().then(setSessions).catch(console.error)
  }, [])

  const handleLogoutAll = () => {
    console.info('Logout all sessions requested')
  }

  const openEditModal = (target: Exclude<EditTarget, null>) => {
    if (!account) return
    setEditError(null)
    if (target === 'displayName') {
      setEditValues({ primary: account.displayName, confirm: '' })
    } else if (target === 'email') {
      setEditValues({ primary: account.email, confirm: account.email })
    } else {
      setEditValues({ primary: '', confirm: '' })
    }
    setEditTarget(target)
  }

  const closeModal = () => {
    setEditTarget(null)
    setEditError(null)
    setEditValues({ primary: '', confirm: '' })
  }

  const saveAccount = (updater: (current: Account) => Account) => {
    setAccount((prev) => {
      if (!prev) return prev
      return updater(prev)
    })
  }

  const handleModalSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!account || !editTarget) return
    setEditError(null)
    const now = new Date().toISOString()
    const trimmed = editValues.primary.trim()

    if (editTarget === 'displayName') {
      if (!trimmed) {
        setEditError('Bitte einen Anzeigenamen angeben.')
        return
      }
      saveAccount((current) => ({
        ...current,
        displayName: trimmed,
        displayNameUpdatedAt: now,
      }))
      closeModal()
      return
    }

    if (editTarget === 'email') {
      if (!trimmed || !editValues.confirm.trim()) {
        setEditError('Bitte beide E-Mail-Felder ausfüllen.')
        return
      }
      if (trimmed !== editValues.confirm.trim()) {
        setEditError('E-Mail-Adressen stimmen nicht überein.')
        return
      }
      saveAccount((current) => ({
        ...current,
        email: trimmed,
        emailUpdatedAt: now,
      }))
      closeModal()
      return
    }

    if (!editValues.primary || !editValues.confirm) {
      setEditError('Bitte beide Passwort-Felder ausfüllen.')
      return
    }
    if (editValues.primary !== editValues.confirm) {
      setEditError('Passwörter stimmen nicht überein.')
      return
    }
    saveAccount((current) => ({
      ...current,
      passwordUpdatedAt: now,
    }))
    closeModal()
  }

  const accountMeta = account
    ? {
        created: account.createdAt,
        displayNameChanged: account.displayNameUpdatedAt ?? account.createdAt,
        emailChanged: account.emailUpdatedAt ?? account.createdAt,
        passwordChanged: account.passwordUpdatedAt ?? account.createdAt,
      }
    : null

  const modalTitle = editTarget
    ? {
        displayName: 'Anzeigenamen bearbeiten',
        email: 'E-Mail-Adresse aktualisieren',
        password: 'Passwort ändern',
      }[editTarget]
    : ''

  const renderFieldValue = (value: string, obfuscate?: boolean) => (obfuscate ? '************' : value)

  return (
    <div className="page page--account">
      <header className="page__header">
        <div>
          <p className="page__eyebrow u-no-select">Your profile</p>
          <h1 className="page__title u-no-select">Account & Sessions</h1>
        </div>
      </header>

      {account && (
        <section className="card-grid">
          <article className="card">
            <header className="card__header">
              <p className="card__eyebrow u-no-select">Profil &amp; Sicherheit</p>
            </header>
            <div className="account-field-list">
              <div className="account-field">
                <div className="account-field__info">
                  <p className="account-field__label u-no-select">Anzeigename</p>
                  <p className="account-field__value">{account.displayName}</p>
                </div>
                <div className="account-field__actions">
                  <button
                    type="button"
                    className="btn btn--ghost btn--icon"
                    onClick={() => openEditModal('displayName')}
                    aria-label="Anzeigenamen bearbeiten"
                  >
                    <Pencil size={16} aria-hidden />
                  </button>
                </div>
              </div>
              <div className="account-field">
                <div className="account-field__info">
                  <p className="account-field__label u-no-select">E-Mail</p>
                  <p className="account-field__value">{account.email}</p>
                </div>
                <div className="account-field__actions">
                  <button
                    type="button"
                    className="btn btn--ghost btn--icon"
                    onClick={() => openEditModal('email')}
                    aria-label="E-Mail-Adresse ändern"
                  >
                    <Pencil size={16} aria-hidden />
                  </button>
                </div>
              </div>
              <div className="account-field">
                <div className="account-field__info">
                  <p className="account-field__label u-no-select">Passwort</p>
                  <p className="account-field__value">{renderFieldValue('************', true)}</p>
                </div>
                <div className="account-field__actions">
                  <button
                    type="button"
                    className="btn btn--ghost btn--icon"
                    onClick={() => openEditModal('password')}
                    aria-label="Passwort aktualisieren"
                  >
                    <Pencil size={16} aria-hidden />
                  </button>
                </div>
              </div>
            </div>
          </article>
          <article className="card">
            <header className="card__header">
              <p className="card__eyebrow u-no-select">Weitere Einstellungen</p>
            </header>
            <div className="setting-toggle">
              <div className="setting-toggle__row">
                <div className="setting-toggle__info">
                  <strong>System-Theme automatisch folgen</strong>
                  <small className="setting-toggle__hint">
                    {autoThemeEnabled
                      ? 'UI folgt aktuell deiner System-Vorgabe.'
                      : `Manueller Modus aktiv – ${manualPreference === 'dark' ? 'Dark' : 'Light'}.`}
                  </small>
                </div>
                <div className="setting-toggle__actions">
                  <label className="toggle-slider">
                    <input
                      type="checkbox"
                      checked={autoThemeEnabled}
                      onChange={(event) => setAutoTheme(event.target.checked)}
                      aria-label="System-Theme automatisch verwenden"
                    />
                    <span className="toggle-slider__track">
                      <span className="toggle-slider__thumb" />
                    </span>
                  </label>
                </div>
              </div>
            </div>
          </article>
          <article className="card">
            <header className="card__header">
              <p className="card__eyebrow u-no-select">Changes</p>
            </header>
            <dl className="account-meta">
              <div className="account-meta__entry">
                <dt className="u-no-select">Account erstellt</dt>
                <dd>{formatDate(accountMeta?.created ?? account.createdAt)}</dd>
              </div>
              <div className="account-meta__entry">
                <dt className="u-no-select">Display Name geändert</dt>
                <dd>{formatDate(accountMeta?.displayNameChanged ?? account.createdAt)}</dd>
              </div>
              <div className="account-meta__entry">
                <dt className="u-no-select">E-Mail geändert</dt>
                <dd>{formatDate(accountMeta?.emailChanged ?? account.createdAt)}</dd>
              </div>
              <div className="account-meta__entry">
                <dt className="u-no-select">Passwort geändert</dt>
                <dd>{formatDate(accountMeta?.passwordChanged ?? account.createdAt)}</dd>
              </div>
            </dl>
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

      <Modal open={Boolean(editTarget)} onClose={closeModal} title={modalTitle}>
        {editTarget && (
          <form className="form-grid" onSubmit={handleModalSubmit}>
            <label>
              <span className="u-no-select">
                {editTarget === 'displayName'
                  ? 'Neuer Anzeigename'
                  : editTarget === 'email'
                    ? 'Neue E-Mail'
                    : 'Neues Passwort'}
              </span>
              <input
                type={editTarget === 'password' ? 'password' : 'text'}
                value={editValues.primary}
                onChange={(event) => setEditValues((prev) => ({ ...prev, primary: event.target.value }))}
                required
              />
            </label>
            {editTarget !== 'displayName' && (
              <label>
                <span className="u-no-select">Zur Bestätigung erneut</span>
                <input
                  type={editTarget === 'password' ? 'password' : 'text'}
                  value={editValues.confirm}
                  onChange={(event) => setEditValues((prev) => ({ ...prev, confirm: event.target.value }))}
                  required
                />
              </label>
            )}
            {editError && (
              <p className="form-error" role="alert">
                {editError}
              </p>
            )}
            <div className="modal__footer">
              <button type="submit" className="btn btn--primary">
                Änderungen anwenden
              </button>
            </div>
          </form>
        )}
      </Modal>
    </div>
  )
}
