# DHBW TIF23 RAG Frontend Architecture

## Runtime Entry Point & Composition

- `src/main.tsx` bootstraps the SPA with `ReactDOM.createRoot`, wraps the tree in `StrictMode`, and composes providers in the order `RuntimeModeProvider → AuthProvider → ThemeProvider → App`. Each provider contributes runtime mode detection, authentication state, and theming control to the entire component tree.
- `src/App.tsx` renders a `RouterProvider` that drives view selection; no additional global state is kept here.
- Vite serves the bundle on port 3000 (`vite.config.ts`) with `strictPort` to fail fast when the port is taken.

## Routing, Layout, and Navigation Shell

- `src/router/index.tsx` wires React Router v7 routes. Public pages include `/` (landing), `/login`, `/register`, and the fallback `*`. Protected routes live under `ProtectedLayout` (`/dash`, `/chat/:chatId?`, `/history`, `/docs`, `/administrative`, `/account`).
- `ProtectedLayout` now waits for `AuthProvider` to finish hydrating; once ready it redirects unauthenticated users to `/` and otherwise renders `AppLayout`.
- `AppLayout` applies the shared shell with `Sidebar` and `Topbar` and renders child routes via `<Outlet />`.
- `Sidebar` hosts navigation, quick actions, and release info. Buttons dispatch custom UI events (`UI_EVENTS.NEW_CHAT`) that other components pick up.

## Environment & Configuration Pipeline

- `src/config/appConfig.ts` sanitizes Vite env variables (`import.meta.env.VITE_*`) to avoid empty strings leaking into runtime config. Important switches:
  - `mockModeEnabled` captures the preferred data mode (mock vs. backend).
  - `apiBaseUrl` defines the API prefix; `apiClient` derives `/api/*` and `/health` URLs from it.
  - `defaultTheme` / `defaultPalette` drive the runtime theming engine.
- `.env.example` documents required env vars; values must be prefixed with `VITE_` so Vite exposes them at build time.

## Data Access Layer

- `src/api/client.ts` centralizes network access and mock fallbacks. It keeps a mutable runtime mode (`setApiRuntimeMode`) so providers can toggle between fixtures and real requests without rebuilding.
  - `request()` wraps fetch with credentials, JSON headers, and error propagation.
  - `checkBackendHealth({ forceNetwork })` pings `/health`; when not forced it short-circuits in mock mode to keep dev flows fast.
  - `login()` submits form-encoded credentials (`application/x-www-form-urlencoded`) to `/accounts/login` to match the Flask backend.
  - `logout()` POSTs to `/accounts/logout` when productive.
  - `getAccount()` normalizes the backend payload (mapping `id`, `username`, `profile_type`, etc.) into the frontend `Account` shape.
  - `getChats()` and `getChatSummaries()` fetch conversation metadata from `/chats/` and, for details, hydrate each conversation before mapping to `ChatDetail`.
  - `getDocuments()` currently returns an empty array in productive mode because the backend lacks a global `/docs` endpoint; mocks still provide sample data.
- `src/api/types.ts` defines DTO contracts. The `Account` type now includes an optional `profileType` so runtime role mapping can reflect backend data.
- `src/data/mockData.ts` stores the fixtures returned whenever runtime mode equals `mock`.

## State & Context Providers

- `RuntimeModeProvider` (`src/runtime/RuntimeModeProvider.tsx`) determines the active mode:
  - Reads the preferred mode from `appConfig.mockModeEnabled`.
  - When the preference is productive it forces a `/health` probe; success keeps the mode productive while failure logs a warning and downgrades to mock.
  - Exposes `preferredMode`, `mode`, `status`, `backendHealthy`, and `refreshBackendHealth()` through `useRuntimeMode()`.
  - Calls `setApiRuntimeMode` so the API client respects the chosen mode.
- `AuthProvider` (`src/auth/AuthProvider.tsx`) consumes `useRuntimeMode()` and handles both scenarios:
  - In mock mode it validates against `MOCK_ACCOUNTS`, stores the user id in `localStorage`, and surfaces async `login`, `logout`, and `refresh` helpers.
  - In productive mode it hydrates the current session via `apiClient.getAccount()`, performs backend logins/logouts, and exposes a normalized `AuthUser` (mapping backend `profile_type` to frontend roles). Readiness is tracked through `isReady` so route guards wait for hydration.
- `ThemeProvider` (`src/theme/ThemeProvider.tsx`) merges system preferences with persisted overrides and writes CSS variables from generated palettes. `useTheme()` exposes toggles and preference setters.

## Pages & Feature Modules

- `LandingPage` hides the CTA ribbon when the preferred mode is productive, yet still redirects authenticated sessions to `/dash`.
- `AuthPage` defers authentication to `AuthProvider`. It surfaces backend health only when the preferred mode expects a backend connection and lets users trigger re-checks via `refreshBackendHealth()`.
- `DashboardPage`, `ChatPage`, `HistoryPage`, `DocumentsPage`, `AdministrativePage`, and `AccountPage` fetch their data exclusively through `apiClient`, benefitting from the runtime mode switch without additional wiring.
- `ChatPage` composes conversations via `ChatExchange` and listens for `UI_EVENTS.NEW_CHAT` to open creation modals.
- `AccountPage` supports optimistic editing in mock mode and gracefully falls back to empty server responses for sessions/stats in productive mode until backend contracts land.

## UI Building Blocks

- `Modal` implements accessible dialogs via React portals, escape handling, and focus management.
- Layout components (`Sidebar`, `Topbar`, `AppLayout`) enforce the admin dashboard visuals. `Topbar` now awaits the async logout before redirecting.
- Chat components (`ChatExchange`, `MessageBubble`) rely on `react-markdown` + `remark-gfm` to render assistant responses with markdown support.
- Utilities such as `src/utils/events.ts` and `src/utils/formatters.ts` centralize DOM event emission and formatting logic.

## Theming & Styling Stack

- Global styles live in `src/index.css` and `App.css`. Utility classes (`.u-no-select`, button variants, etc.) keep layout consistent across pages.
- `scripts/generate-themes.cjs` reads YAML palettes from `src/themes/*.yml`, produces `src/theme/themes.generated.ts`, and is wired into the `npm run build` script so palettes stay in sync.
- `ThemeToggle` consumes `useTheme()` to flip between dark/light modes, updating CSS variables instantly.

## Tooling & Build Process

- Package tooling: React 19 with Vite 7, TypeScript 5.9, ESLint 9 configured for hooks and React Refresh.
- Scripts: `npm run dev`, `build`, `preview`, `lint`, `generate-themes`, plus `full-check-and-dev` for CI-like end-to-end runs.
- Dockerfile: builds the production bundle and serves it via Nginx (`nginx.conf`) with CSP headers already locked down.

## Mode Switching Model (Mock vs. Productive)

- Runtime mode resolution now requires both a productive preference (`VITE_USE_MOCK=false`) and a successful backend health check. Failing either condition keeps the UI in mock mode to guarantee a usable demo experience.
- The API client and `AuthProvider` respond to mode changes instantly—no rebuilds required. When productive, all auth flows talk to the Flask backend using form-data POSTs and session cookies; when mock, they never leave the browser.
- Consumers access the current mode via both `useRuntimeMode()` and `useAuth()` (`auth.mode`). This prevents components from re-implementing connectivity checks.

## Extension Points & Known Gaps

- Backend coverage remains incomplete (sessions, system status, document lists). API client falls back to empty arrays today; tighten once endpoints exist.
- Error handling is intentionally light (mostly `console.warn` / `console.error`). Add user-visible toasts when the UX should surface failures.
- Document upload and chat export modals are placeholders pending backend integration.
- Consider memoizing expensive chat hydration (multiple `/chats/{id}` calls) once payload sizes grow; caching belongs inside `apiClient`.
