# Frontend Decisions and Notes

## Stack

Technische Grundlage fuer das Frontend.

- React + Vite (TypeScript)
- React Router for multi-page style navigation with modal popups per route context
- Styling via CSS Modules + global utility layer (CSS variables for theming)
- Iconography via Lucide CDN, fonts via Google Fonts (Inter + optional monospace fallback)

## Theming

Strategie fuer Light/Dark-Mode und Anpassung.

- Default theme follows `prefers-color-scheme`
- Manual toggle stored in `localStorage` and applied via HTML `data-theme` attribute
- CSS variables define palette for light/dark to keep components consistent

## Accessibility and UX

Leitlinien fuer Bedienbarkeit und Layout.

- Layout inspired by BetriebMonitor Web3.0 (sidebar + content panels)
- Popups implemented as accessible dialogs via React portals, focus trapping
- Text segments that should not be copyable (logo, nav labels, static helper texts) receive utility class `.u-no-select`

## Security

Schutzmassnahmen und sichere Defaults.

- Fetch wrappers always use `credentials: 'include'`
- Central CSRF helper prepared (expects backend to set `csrf-token` cookie or header)
- CSP recommendation for hosting: `default-src 'self'; font-src https://fonts.gstatic.com; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; script-src 'self'; connect-src 'self' https://api.example.tld`
- No inline event handlers; React handles interactions
- Sanitization hook ready if backend ever returns HTML (via DOMPurify)
- Local storage usage limited to theme preference only

## Routing / Pages

Geplante Seitenstruktur und modale Aktionen.

- `/` Dashboard / Landing overview
- `/login`, `/register`
- `/account` profile & session info
- `/chat` main chat interface with history sidebar
- `/history` dedicated chat log management
- Modals for document upload, chat rename/delete, session logout confirmation

## API Integration

Kommunikation mit dem Backend.

- `apiClient` encapsulates base URL, error handling, JSON parsing
- Endpoints derived from documentation/backend/api + planung-json-austausch
- Placeholder mocks during early development, switchable via env flag

## Assets

Umgang mit statischen Ressourcen.

- Minimal local assets (logo SVG, fallback fonts)
- Everything else via CDN to reduce repo size, with graceful fallbacks
