import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <div className="auth-layout">
      <div className="auth-card">
        <h1 className="u-no-select">Page not found</h1>
        <p>The requested view does not exist. Please navigate back to the dashboard.</p>
        <Link to="/" className="btn btn--primary">
          Go home
        </Link>
      </div>
    </div>
  )
}
