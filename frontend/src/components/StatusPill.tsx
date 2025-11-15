type Status = 'online' | 'degraded' | 'offline'

const LABELS: Record<Status, string> = {
  online: 'Online',
  degraded: 'Degraded',
  offline: 'Offline',
}

export function StatusPill({ status }: { status: Status }) {
  return <span className={`status-pill status-pill--${status}`}>{LABELS[status]}</span>
}
