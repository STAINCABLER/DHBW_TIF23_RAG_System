# DHBW RAG Frontend

React + Vite UI zur Bedienung des Retrieval-Augmented-Systems. Das Layout orientiert sich am BetriebMonitor-Web3.0-Projekt und deckt folgende Views ab:

- Dashboard mit Dokument- und Chat-Kacheln
- Administrative Health-Ansicht für Service-Status
- Mehrspaltiges Chat-Interface inkl. Upload-/New-Chat-Modals
- Dokumentverwaltung, Account-/Session-Ansicht sowie History-Tabellen
- Login/Registrierung als eigenständige Seiten

## Tech-Stack

- React 19 + Vite 7 (TypeScript)
- React Router für echtes Multi-Page-Navigationsgefühl
- Eigener Theme-Provider (System-Default + manueller Toggle)
- Styling über CSS-Variablen inkl. `.u-no-select`-Utility für nicht kopierbaren Text
- API-Client nutzt `fetch` mit `credentials: 'include'`, fallbackt optional auf Mock-Daten

## Entwicklung

```bash
cd frontend
cp .env.example .env  # Werte bei Bedarf anpassen
npm install
npm run dev
```

## Environment Variablen

Alle dynamischen Texte und API-Pfade werden über eine `.env` gesteuert (siehe `.env.example`). Vite liest Variablen mit dem Prefix `VITE_` nur zur Build-Zeit ein.

| Variable | Default | Beschreibung |
| --- | --- | --- |
| `VITE_API_BASE_URL` | `/api` | Basis-URL der Backend-API. Wird für alle Fetches genutzt. |
| `VITE_USE_MOCK` | `false` | Aktiviert Demo-Daten, Mock-Login und Test-Accounts; nur setzen, wenn kein Backend angebunden ist. |
| `VITE_APP_NAME` | `Knowledge Console` | Text neben dem Logo sowie Page-Titel. |
| `VITE_APP_FOOTER` | `RAG System` | Footer-Label der Sidebar. |
| `VITE_APP_RELEASE` | `Release 0.1.0` | Release-Anzeige unterhalb des Footers. |
| `VITE_DEFAULT_THEME` | `system` | Start-Theme: `system`, `light` oder `dark`. |

Nicht vergebene oder leere Werte werden automatisch auf die Defaults zurückgesetzt.

### Mock-Login & Rollen

Im Mockup-Modus existiert jetzt ein kleines Auth-Context-System mit zwei fest kodierten Konten. Beide sind nach dem Start ausgeloggt und können über `/login` aktiviert werden.

> Mock-spezifische Inhalte (Test-Accounts, Demo-Daten, gespeicherte Sessions) erscheinen nur, wenn `VITE_USE_MOCK=true`. In produktiven Deployments bleibt die UI neutral, bis echte Endpunkte hinterlegt sind.

| Rolle | Zugangsdaten | Sichtbare Funktionen |
| --- | --- | --- |
| Test User | `test.user@example.com` / `user-pass` | Sieht die Standard-Navigation, Release-Version bleibt statischer Text, nur Login-Button sichtbar. |
| Test Admin | `test.admin@example.com` / `admin-pass` | Release-Version wird zum Button, der `/administrative` öffnet; Logout-Button sichtbar; Admin-Funktionen wie Systemstatus werden freigeschaltet. |

> Die Buttons „Login/Logout“ manipulieren nur den Mock-Status im Frontend. Für echte Authentifizierung müsste später ein Backend-Endpunkt angebunden werden.

## Build & Container

```bash
npm run build
npm run preview # optional

# Docker
docker build -t rag-frontend .
docker run -p 3000:3000 rag-frontend
```

Der Docker-Container basiert auf `node:20-alpine` (Build) und `nginx:1.27-alpine` (Runtime) mit restriktiven Security-Headern. Der Webserver lauscht auf Port `3000`, wie in `docker-stack/docker-compose.yml` vorgesehen.

## Sicherheit & Ressourcen

- CSP über `<meta http-equiv="Content-Security-Policy" ...>` und im Nginx-Container
- Keine Inline-Handler, Theme-State einzig in `localStorage`
- Fonts & Icons via Google Fonts/Emoji – minimale lokale Assets
- Globaler UI-Event-Bus (`UI_EVENTS`) für Modals/Popups pro Seite

Weitere Architekturentscheidungen sind in `frontend/FRONTEND_NOTES.md` dokumentiert.
