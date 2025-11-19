import { useEffect, useRef, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { useAuth } from '../auth/useAuth'
import { appConfig } from '../config/appConfig'
import { ThemeToggle } from '../components/ThemeToggle'
import Logo from '../assets/ltm-logo.svg'

const landingStats = [
  { value: '90 s', label: 'bis zum ersten Architekturvorschlag' },
  { value: '25%', label: 'Kostensenkung durch passende DB-Stacks' },
  { value: '100%', label: 'Transparente Quellen & Entscheidungen' },
]

const heroChecklist = [
  'Empfehlungen zu Workloads, Latenz, Compliance',
  'Vergleich klassischer SQL, NoSQL & Serverless Optionen',
  'Automatische Schema-Skizzen für den gewählten Stack',
]

const featurePillars = [
  {
    title: 'Diagnose deines Usecases',
    description:
      'Der Assistant stellt tiefergehende Fragen zu Datenvolumen, Konsistenzbedarf, Latenz und Budget, um unwichtige Technologien auszuschließen.',
  },
  {
    title: 'Stack-Empfehlungen',
    description:
      'Vergleicht relationale, dokumenten- oder graphbasierte Optionen, inklusive Cloud-Angeboten und Lizenzmodellen mit Preis-/Leistungs-Hinweisen.',
  },
  {
    title: 'Struktur-Blueprints',
    description:
      'Erzeugt Tabellen-, Collection- oder Vertex-Schemata mit Beziehungen, Partitionierungs- und Indexstrategien zum direkten Export.',
  },
]

const workflowSteps = [
  {
    title: 'Usecase verstehen',
    detail:
      'Der Assistant führt dich durch Fragen zu Lese-/Schreibmustern, Konsistenz, Skalierung und Compliance-Anforderungen.',
  },
  {
    title: 'Kontext anreichern',
    detail: 'Du beantwortest im Chat die Fragen und lädst – falls vorhanden – Architektur-Notizen oder Datenflüsse hoch.',
  },
  {
    title: 'Blueprint erhalten',
    detail: 'Sobald genug Informationen vorliegen, liefert das System DB-Empfehlungen inklusive Strukturentwurf und nächsten Schritten.',
  },
]

const trustBadges = ['DHBW Fakultäten', 'LTM-Labs Research', 'Campus AI Lab', 'Knowledge Ops Teams']

const landingMockMessages = [
  {
    role: 'assistant',
    text: 'Hallo Jana, ich bin dein Database Design Assistant. Wobei kann ich dir heute bei Datenbanken und Strukturen helfen?',
  },
  { role: 'user', text: 'Wir planen eine Plattform für Sensor-Daten mit 5k Events/s und Reporting-Pflicht. Welche DB passt?' },
  {
    role: 'assistant',
    text: 'Lass uns den Fokus schärfen: Welche Latenz erwartest du für Dashboards und welche Compliance-Richtlinien gelten (z. B. DSGVO, BaFin)?',
  },
  { role: 'user', text: 'Dashboards <2s, Batch-Export ok. DSGVO-konform, Daten 3 Jahre aufbewahren.' },
  {
    role: 'assistant',
    text: 'Danke! Bitte lade – falls vorhanden – euer aktuelles ER-Diagramm hoch. Danach skizziere ich eine Kombination aus Timeseries-DB + analytischem Warehouse.',
  },
]

const testimonial = {
  quote:
    '„Der Assistant hat uns geholfen, teure Fehlentscheidungen zu vermeiden. Nach drei Dialogrunden hatten wir einen validierten Mix aus Aurora Postgres und Keyspaces inklusive Schema-Vorschlag.“',
  author: 'Rafael Bach',
  role: 'Head of Platform Engineering, LTM-Labs',
}

const documentationUrl = 'https://github.com/STAINCABLER/DHBW_TIF23_RAG_System'
const licenseUrl = `${documentationUrl}/blob/main/LICENSE`
const operationsUrl = `${documentationUrl}/tree/main/documentation`

export function LandingPage() {
  const { user } = useAuth()
  const showLandingCta = appConfig.mockModeEnabled
  const topbarRef = useRef<HTMLElement>(null)
  const [topbarStuck, setTopbarStuck] = useState(false)

  useEffect(() => {
    const node = topbarRef.current
    if (!node) return

    const observer = new IntersectionObserver(
      ([entry]) => {
        setTopbarStuck(entry.intersectionRatio < 1)
      },
      {
        threshold: [1],
        rootMargin: '-1px 0px 0px 0px',
      },
    )

    observer.observe(node)
    return () => {
      observer.disconnect()
    }
  }, [])

  if (user) {
    return <Navigate to="/dash" replace />
  }

  return (
    <div className="page landing-page">
      <div className="landing__container">
        <header ref={topbarRef} className={`landing__topbar ${topbarStuck ? 'is-stuck' : ''}`}>
          <Link to="/" className="landing__brand" aria-label="Zur Startseite">
            <img src={Logo} alt="LTM-Labs" className="landing__brand-logo" />
            <div className="landing__brand-text u-no-select">
              <span>{appConfig.appName}</span>
              <small>Database Structure Design Assistant</small>
            </div>
          </Link>
          <div className="landing__topbar-actions">
            <Link to="/login" className="btn btn--ghost btn--compact">
              Login
            </Link>
            <ThemeToggle />
          </div>
        </header>

        <section className="landing__hero">
          <div className="landing__copy">
            <p className="landing__pill u-no-select">Database Structure Design Assistant</p>
            <h1 className="landing__title">Finde den richtigen Datenbank-Stack – samt Struktur.</h1>
            <p className="landing__subtitle">
              Unser RAG-gestützter Assistant führt dich durch Fragen zu Workloads, Kostenrahmen und Compliance und liefert daraus die
              passende Technologie-Kombination inklusive Schema-Blueprint.
            </p>
            <ul className="landing__list">
              {heroChecklist.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <div className="landing__actions">
              <Link to="/login" className="btn btn--primary btn--lg">
                Jetzt anmelden
              </Link>
              <Link to="/register" className="btn btn--ghost btn--lg">
                Zugang anfragen
              </Link>
            </div>
            <small className="landing__hint">Noch kein Konto? Fordere einen Campus- oder Partner-Login über das Team an.</small>
          </div>
          <div className="landing__visual">
            <div className="landing__mock">
              <header className="landing__mock-header">
                <span className="u-no-select">Live-Demo</span>
                <span className="landing__status-pill">Online</span>
              </header>
              <div className="landing__mock-body">
                {landingMockMessages.map((msg, index) => (
                  <div key={`${msg.role}-${index}`} className={`landing__mock-message landing__mock-message--${msg.role}`}>
                    <span className="landing__mock-role u-no-select">{msg.role === 'user' ? 'Team' : 'Assistant'}</span>
                    <p>{msg.text}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </section>

        <section className="landing__trust card">
          <p className="landing__trust-label u-no-select">Vertrauenswürdig für</p>
          <div className="landing__logos">
            {trustBadges.map((badge) => (
              <span key={badge} className="landing__logo">
                {badge}
              </span>
            ))}
          </div>
        </section>

        <section className="landing__metrics card">
          {landingStats.map((stat) => (
            <div key={stat.label} className="landing__stat">
              <span className="landing__stat-value">{stat.value}</span>
              <span className="landing__stat-label">{stat.label}</span>
            </div>
          ))}
        </section>

        <section className="landing__grid">
          {featurePillars.map((pillar) => (
            <article key={pillar.title} className="landing__feature-card card">
              <h3>{pillar.title}</h3>
              <p>{pillar.description}</p>
            </article>
          ))}
        </section>

        <section className="landing__steps card">
          <header className="landing__steps-header">
            <p className="landing__pill u-no-select">Workflow</p>
            <h2>So arbeitet der Database Design Assistant</h2>
          </header>
          <ol className="landing__step-list">
            {workflowSteps.map((step, index) => (
              <li key={step.title} className="landing__step">
                <span className="landing__step-index">{index + 1}</span>
                <div>
                  <h4>{step.title}</h4>
                  <p>{step.detail}</p>
                </div>
              </li>
            ))}
          </ol>
        </section>

        <section className="card">
          <p className="landing__pill u-no-select">Stimme aus dem Pilot</p>
          <blockquote className="landing__testimonial">
            <p>{testimonial.quote}</p>
            <footer>
              <strong>{testimonial.author}</strong>
              <span>{testimonial.role}</span>
            </footer>
          </blockquote>
        </section>

        {showLandingCta && (
          <section className="landing__cta card">
            <h3>Bereit für überprüfbare Datenbank-Blueprints?</h3>
            <p>Starte eine Session, beantworte die gezielten Fragen des Assistants und erhalte fundierte Strukturvorschläge.</p>
            <div className="landing__actions">
              <Link to="/login" className="btn btn--primary btn--lg">
                Demo starten
              </Link>
              <a className="btn btn--ghost btn--lg" href={documentationUrl} target="_blank" rel="noreferrer">
                Dokumentation ansehen
              </a>
            </div>
          </section>
        )}

        <footer className="landing__footer card" aria-label="Projektinformationen">
          <div className="landing__footer-meta">
            <span className="landing__footer-version u-no-select">{appConfig.releaseVersion}</span>
            <a href={documentationUrl} target="_blank" rel="noreferrer" className="landing__footer-link">
              GitHub Repository
            </a>
          </div>
          <p className="landing__footer-disclaimer">
            Studentenprojekt in der Alpha-Phase – Ergebnisse dienen Demonstrationszwecken, nicht für produktive Entscheidungen.
          </p>
          <div className="landing__footer-extra">
            <span className="u-no-select">by Tobias Maimone</span>
            <a href={licenseUrl} target="_blank" rel="noreferrer" className="landing__footer-link">
              Lizenzhinweise (in Arbeit)
            </a>
            <a href={operationsUrl} target="_blank" rel="noreferrer" className="landing__footer-link">
              Betriebsanleitungen (in Arbeit)
            </a>
          </div>
        </footer>
      </div>
    </div>
  )
}
