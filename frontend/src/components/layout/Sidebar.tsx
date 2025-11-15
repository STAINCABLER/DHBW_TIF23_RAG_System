import { NavLink, useNavigate } from 'react-router-dom'
import { LayoutDashboard, MessageSquare, History as HistoryIcon, FileText, Plus, BadgeCheck, ExternalLink } from 'lucide-react'
import { UI_EVENTS, emitUiEvent } from '../../utils/events'
import { appConfig } from '../../config/appConfig'
import { useAuth } from '../../auth/useAuth'
import Logo from '../../assets/ltm-logo.svg'

const RELEASE_REPO_URL = 'https://github.com/STAINCABLER/DHBW_TIF23_RAG_System/tree/main/frontend'

const navItems = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
  { to: '/history', label: 'History', icon: HistoryIcon },
  { to: '/docs', label: 'Documents', icon: FileText },
] as const

export function Sidebar() {
  const navigate = useNavigate()
  const { isAdmin } = useAuth()

  const handleNewChat = () => {
    navigate('/chat')
    setTimeout(() => emitUiEvent(UI_EVENTS.NEW_CHAT), 0)
  }

  const handleAdminNavigate = () => {
    if (!isAdmin) return
    navigate('/administrative')
  }

  return (
    <aside className="sidebar" aria-label="Primary">
      <div className="sidebar__logo u-no-select">
        <img src={Logo} alt="LTM Labs" className="sidebar__logo-image" />
        <span className="sidebar__logo-text">{appConfig.appName}</span>
      </div>

      <nav className="sidebar__nav">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              ['sidebar__link', isActive ? 'sidebar__link--active' : '']
                .filter(Boolean)
                .join(' ')
            }
          >
            <item.icon className="sidebar__icon" size={18} aria-hidden />
            <span className="sidebar__label u-no-select">{item.label}</span>
          </NavLink>
        ))}
      </nav>

      <section className="sidebar__quick">
        <p className="sidebar__section-label u-no-select">Quick Actions</p>
        <button
          className="btn btn--ghost"
          type="button"
          onClick={handleNewChat}
        >
          <Plus size={16} aria-hidden />
          New Chat
        </button>
      </section>

      <footer className="sidebar__footer u-no-select">
        {isAdmin ? (
          <button
            type="button"
            className="btn btn--ghost btn--compact"
            onClick={handleAdminNavigate}
            aria-label="Open administrative overview"
          >
            <BadgeCheck size={16} aria-hidden />
            {appConfig.footerLabel}
          </button>
        ) : (
          <p>{appConfig.footerLabel}</p>
        )}
        <a
          href={RELEASE_REPO_URL}
          target="_blank"
          rel="noreferrer"
          className="btn btn--ghost btn--compact"
          aria-label="Open release information on GitHub"
        >
          <ExternalLink size={16} aria-hidden />
          {appConfig.releaseVersion}
        </a>
      </footer>
    </aside>
  )
}
