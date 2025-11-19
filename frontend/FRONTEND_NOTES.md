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

- `/` Öffentliche Landing mit Marketing-Blöcken
- `/dash` Authentifizierter Dashboard-Startpunkt (innerhalb AppLayout)
- `/login`, `/register`
- `/account` profile & session info
- `/chat` main chat interface with history sidebar
- `/administrative` status cards, deployment/indexing automation notes
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

## Component Inspiration Sources

Evaluations fuer externe Bibliotheken und wofuer wir sie heranziehen.

- **reactcomponents.com** – Katalog/Meta-Suche nach Trend-Komponenten; nutze ich zur Ideensammlung und um moderne Interaktionsmuster (Command Palettes, Timeline Cards) schnell zu vergleichen bevor wir eigenes Markup schreiben.
- **MUI (mui.com)** – Referenz fuer komplexe Formulare, DataGrids, Tabs, Steppers und Responsiveness. Ideal fuer Dashboard-Kacheln, Tabellen-Skeletons sowie Validierungs-Patterns.
- **Ant Design (ant.design)** – Setze ich als Vorlage fuer Enterprise-lastige Komponenten wie TreeSelect, Cascader, Filter-Drawer und dichte Tabellen mit Inline-Actions.
- **RSuite (rsuitejs.com)** – Gute Quelle fuer Timeline-, Kalender-, Tree- und wizards/Steps-Komponenten. Praktisch fuer History-Ansichten und Scheduling-Widgets.
- **React Bootstrap** – Verwende ich fuer klassische Hero-/Marketing-Sections, einfache Formulare und das Grid-System wenn wir schnelle responsive Layouts brauchen.
- **HeroUI** – Modernes, stark visuelles Komponenten-Set fuer Cards, Modals und Buttons mit hohem Kontrast; nutze ich als Inspiration fuer CTA-starke Bereiche (z. B. Upload-Dialoge).
- **Grommet v2** – Fokus auf Accessibility und Data Visualization (Meter, Chart, Distribution). Ziehe ich heran fuer KPI-Anzeigen oder wenn wir flexible Layout-Primitives fuer responsive Panels benoetigen.
- **Evergreen (Segment)** – Schlanke, produktive Admin-Komponenten wie Side Sheets, Toasts, Inline-Editable Tabellen. Eignet sich fuer Settings-, Account- oder Dokument-Listen.
- **React Admin** – Speziell fuer CRUD-Workflows: Resource-Listen, Filterleisten, Bulk-Actions, Edit-Forms. Inspiration fuer History-Management und Dokument-Review-Flows.

## Template Alignment (Nov 15)

- Topbar greeter folgt HeroUI/MUI Layout: dreiteilige Struktur mit zentralem Welcome-Text, Icon-only Actions.
- Cards & Tables erhielten Ant Design / MUI inspirierte Shadows, Typografie (Uppercase Header, Hover States) fuer einheitlichen Admin-Look.
- Document-Tabelle nutzt React-Admin-like Link-Badges zur Navigation, History-Aktionen spiegeln Ant Buttons.

## Landing Page Research (Nov 16)

- **Superside – "20 Best Landing Page Design Examples to Perform in 2025" (Sep 1, 2024)**
  - Betonung auf *einem* klaren, überzeugenden Titel, weil laut Studie bis zu 80 % der Besucher nur die Headline lesen.
  - Hero-Visuals sollen wie ein „digitales Billboard“ wirken; starke Bilder oder Videos steigern Erinnerung (80 % visuell vs. 20 % Text) und konvertieren bis zu 86 % besser.
  - Copy muss knapp bleiben und ein Angebot je Seite fokussieren (mehrere Offerten senken Leads um 266 %). Gliederung über Bullets/Subheads.
  - CTAs brauchen hohe Sichtbarkeit, Kontraste sowie Personalisierung (bis zu +202 % Performance). Idealerweise nur ein primäres Ziel.
  - Trust-Signale (Testimonials, Kontaktinfos) steigern Conversions um bis zu 9 %; Mobile-First + schnelle Ladezeiten (jede Sekunde = −4.42 % Conversion) sind Pflicht.
- **Landingfolio – Inspiration Hub (laufend aktualisiert, Feb 2025 Snapshot)**
  - Zeigt, dass moderne Landingpages über modulare Komponenten (Hero, Feature Cards, Steps, Testimonials) aufgebaut werden; dadurch bleibt das Layout konsistent und wiederverwendbar.
  - Filter nach Industrie, Device und Farbschemata verdeutlichen, wie stark Personalisierung pro Zielgruppe wirkt.
  - Claim „Make beautiful websites, without designing them“ erinnert daran, Design-System-Bausteine zu nutzen (hundreds of components) statt jedes Mal neu zu beginnen ⇒ wir spiegeln das mit klar abgegrenzten Landing-Blöcken.
- **MyCodelessWebsite – Landing Page Website (mycodelesswebsite.com/landing-page-website/)**
  - Seite ist aktuell nur über eine WPX-Fehlerseite bzw. Bot-Verifikation erreichbar; ohne CAPTCHA-Lösung keine Inhalte abrufbar. Sobald der Betreiber wieder ein öffentliches Listing liefert, Insights nachtragen.

- **Umsetzung**
  - Landing-Ansicht auf `/` wurde mit klarer Hero-Story, fokussiertem CTA, Social Proof, Nutzen-Säulen, Workflow-Steps, Metriken und Testimonial neu aufgebaut.
  - Komponenten bleiben modular (Hero, Trust-Logos, Metrics, Feature Cards, Steps, Testimonial, CTA) und folgen den oben genannten Parametern.
