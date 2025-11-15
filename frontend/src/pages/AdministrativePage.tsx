import { useEffect, useState } from 'react'
import { apiClient } from '../api/client'
import type { SystemStatus } from '../api/types'
import { StatusPill } from '../components/StatusPill'
import { formatDate } from '../utils/formatters'

export function AdministrativePage() {
  const [services, setServices] = useState<SystemStatus[]>([])

  useEffect(() => {
    apiClient.getSystemStatus().then(setServices).catch(console.error)
  }, [])

  return (
    <div className="page page--administrative">
      <header className="page__header">
        <div>
          <p className="u-no-select page__eyebrow">Platform health</p>
          <h1 className="page__title u-no-select">Administrative Overview</h1>
        </div>
      </header>

      <section className="card-grid">
        {services.map((service) => (
          <article key={service.name} className="card">
            <header className="card__header">
              <p className="card__eyebrow u-no-select">{service.name}</p>
              <StatusPill status={service.status} />
            </header>
            <p className="card__body">{service.description}</p>
            <footer className="card__footer">
              <time dateTime={service.updatedAt}>Updated {formatDate(service.updatedAt)}</time>
            </footer>
          </article>
        ))}
      </section>

      <section className="card">
        <header className="card__header">
          <p className="card__eyebrow u-no-select">Automation Guardrails</p>
        </header>
        <p className="card__body">
          Deployments and re-indexing are orchestrated automatically by the CI/CD pipeline after tests pass. Manual
          triggers have been removed to prevent accidental downtime—production changes must go through the pipeline.
        </p>
        <p className="card__body">
          Vector synchronization is monitored continuously; if degradation is detected, background jobs pause chat
          traffic before resuming. Use this page to confirm status only.
        </p>
      </section>
    </div>
  )
}
