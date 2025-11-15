# DHBW TIF23 RAG – Copilot Instructions

## Architecture Overview
- Monorepo hosts the Flask API in `backend/`, the React/Vite UI in `frontend/`, infra manifests in `docker-stack/`, and planning/API specs under `documentation/`.
- Data flow: UI talks to `/api` (see `backend/app.py`) via `fetch` with cookies; backend keeps everything in memory today (no DB) and exposes chat/account endpoints.
- Docker stack (`docker-stack/docker-compose.yml`) glues Redis, the API, UI, and RedisInsight for diagnostics; compose file assumes prebuilt GHCR images plus an external `proxy-network`.

## Backend (Flask)
- `backend/app.py` wires blueprints from `endpoints/accounts.py` and `endpoints/chats.py`, exports `/api` + `/health`, and returns a machine-readable endpoint list via `app.url_map`.
- Requests expect form-encoded payloads (`request.form.get(...)`), not JSON; remember to send `username`, `password`, or `user_input` fields accordingly.
- Session state lives in signed cookies using `app.secret_key`; `util/session_management.py` guards endpoints and resolves the current `User` from the in-memory registry.
- `util/user.py` stores all test users in the `User.users` class list (seeded with `create_user("test", "test")`); mutating users means editing this static list or extending persistence manually.
- Chats are lightweight objects from `util/chat.py` (`Entry`, `EntryRole`, `Chat`) attached to each user; endpoints currently stub the RAG “magic” so add retrieval logic where `# TODO` markers live.

## Frontend (React + Vite)
- App entry (`frontend/src/main.tsx`) wraps routes in `AuthProvider` (mock logins) and `ThemeProvider` (localStorage-backed `data-theme`) before rendering `App.tsx`.
- Routing is centralized in `src/router/index.tsx`: `AppLayout` applies the sidebar/topbar shell while children render `DashboardPage`, `ChatPage`, `HistoryPage`, etc.
- Runtime config lives in `src/config/appConfig.ts`; only `VITE_*` env vars are read and defaults are sanitized, so keep new switches consistent with this helper.
- API access goes through `src/api/client.ts`, which enforces `credentials: 'include'`, JSON parsing, and mock fallbacks (`appConfig.mockModeEnabled`) backed by `src/data/mockData.ts`.
- Authentication is front-end only: `src/auth/AuthProvider.tsx` toggles between the `MOCK_ACCOUNTS` seeds; registration/login UI (`pages/AuthPage.tsx`) simply reflects that state.
- UI conventions: `src/components/layout/Sidebar.tsx` emits `UI_EVENTS.NEW_CHAT` (from `src/utils/events.ts`) to open modals, `MessageBubble` renders markdown via `react-markdown + remark-gfm`, and the `.u-no-select` utility plus CSS variables in `src/index.css` drive theming.
- Keep forms controlled and use helper formatters from `src/utils/formatters.ts` for bytes/dates to match Dashboard/Account views.

## Docs, Builds & Infra
- Frontend workflow (`frontend/README.md`): `npm install`, `npm run dev`, `npm run build`, optional `npm run preview`; Docker build uses `frontend/Dockerfile` + hardened `nginx.conf` (CSP already defined).
- Backend workflow: `cd backend`, `pip install -r requirements.txt`, run `python app.py`; container variant lives in `backend/Dockerfile` listening on port 4000.
- API/JSON contracts and planning notes live in `documentation/backend/api/*.md` and `documentation/planung/*.md`; read them before changing request/response shapes.
- Project-level decisions must be recorded as Markdown under `documentation/` so new contributors see the rationale next to the specs.
- Frontend-specific choices (UX tradeoffs, component patterns, theming tweaks) belong in `frontend/FRONTEND_NOTES.md`; keep that file in sync when you change UI behavior.
- Environment defaults rely on `.env` (copy from `.env.example`) with `VITE_API_BASE_URL`, `VITE_USE_MOCK`, branding strings, and theme preference.

## Implementation Tips
- When adding backend routes, register them on `api_blueprint` so `/api` automatically advertises them; return JSON and strip sensitive fields (`password`) as shown in `accounts.py`.
- Chat mutations should call `User.add_entry_to_chat` to keep helper views (`get_raw_chats_as_list`) consistent with what `frontend` expects.
- Extend the API client by adding typed helpers to `src/api/client.ts` plus corresponding DTOs in `src/api/types.ts`; wire new UI data flows through React hooks/pages rather than direct fetch calls.
- Modal interactions rely on React portals in `src/components/Modal.tsx`; ensure you toggle `open` state and clean up Escape listeners just like the existing upload/new-chat flows.
- Reuse CSS utility classes and button variants from `src/index.css` to maintain the admin look; Theme changes must set `document.documentElement.dataset.theme` via the provider.
- If you need stack orchestration locally, adapt `docker-stack/docker-compose.yml` but be aware it expects the `proxy-network` to exist or to be swapped out.
