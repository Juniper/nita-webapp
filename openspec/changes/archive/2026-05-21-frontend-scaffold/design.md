## Context

The repo currently has no frontend build tooling, no `frontend/` directory, and no JavaScript dependencies. All UI is rendered by Django templates in `ngcn/templates/`. The goal is to introduce a React SPA that lives alongside the Django backend in the same repo, talks only to `/api/v1/`, and can be developed independently before the Django templates are removed.

## Goals / Non-Goals

**Goals:**
- `frontend/` Vite + React 18 + TypeScript project, buildable with `npm run build`.
- Tailwind CSS with dark mode class strategy, dark mode enabled by default (via `<html class="dark">`).
- React Router v6 with two routes: `/login` (unauthenticated) and `/` (authenticated shell).
- `AuthContext` that calls `GET /api/v1/auth/me/` on mount — sets `user` state or redirects to `/login`.
- `src/api/client.ts` — a thin `fetch` wrapper that (a) calls `GET /api/v1/auth/csrf/` once on first non-GET request to obtain and cache the CSRF token, and (b) attaches `X-CSRFToken` header on POST/PUT/PATCH/DELETE.
- `LoginPage` component that POSTs to `/api/v1/auth/login/` and on success updates `AuthContext`.
- `DashboardPage` — empty placeholder that shows the logged-in username.
- Vite dev proxy: `'/api' → 'http://localhost:8000'` so dev server works without CORS.
- `.gitignore` entry for `frontend/node_modules/`.

**Non-Goals:**
- Docker/nginx integration — that is change ⑤ and ⑥.
- Any real feature pages beyond the login/dashboard shell — those are changes ⑩–⑱.
- CSS component library (e.g., shadcn/ui, MUI) — Tailwind utilities only for this scaffold; a component library decision can be deferred to ⑧ `frontend-shell`.
- Tests for the scaffold — testing infrastructure is set up in ⑧ `frontend-shell`.
- End-to-end flows — out of scope.

## Decisions

### D1: Vite over Create React App
**Choice:** Vite with `@vitejs/plugin-react`.
**Rationale:** CRA is unmaintained. Vite has near-instant HMR, native ESM, and first-class TypeScript. Standard choice in 2026.
**Alternatives:** Next.js — rejected because NITA serves the SPA as static files behind nginx, not a Node server; SSR is unnecessary complexity.

### D2: Tailwind CSS for styling
**Choice:** Tailwind CSS v3 with `darkMode: 'class'`.
**Rationale:** Utility-first CSS fits the build-up-from-scratch approach. The `class` strategy lets the app set `dark` on `<html>` and have dark mode on by default without relying on the OS media query.
**Alternatives:** CSS Modules + custom dark variables — more verbose, no design system. MUI/Chakra — premature for a scaffold; adds significant bundle weight.

### D3: `class` dark mode strategy, defaulting to dark
**Choice:** Set `document.documentElement.classList.add('dark')` in `index.html` (or in `main.tsx` before render).
**Rationale:** User requirement. Dark mode as default matches the target audience (network engineers using terminals). System-preference-following can be added later.

### D4: `fetch` wrapper, not Axios
**Choice:** Native `fetch` with a thin wrapper in `src/api/client.ts`.
**Rationale:** Keeps dependencies minimal for the scaffold. Axios can be introduced later if interceptors become complex.

### D5: AuthContext with `GET /api/v1/auth/me/` for session detection
**Choice:** On mount, call `me` endpoint. If 200 → user is logged in. If 403 → redirect to `/login`.
**Rationale:** Works with Django session cookies without storing any state in localStorage. The cookie is automatically sent on every request.

### D6: Single `frontend/` directory at repo root
**Choice:** `frontend/` alongside `build-and-test-webapp/`, `nginx/`, etc.
**Rationale:** Keeps the SPA clearly separated from backend code while remaining in the same repo. Consistent with the overall monorepo intent.

## Risks / Trade-offs

- **Node.js not in Docker yet** — `npm install` / `npm run dev` requires Node ≥ 20 on the developer's host. Docker integration follows in change ⑤.
  → Mitigation: Document `node -v` prerequisite in the scaffold's `README` section or `BUILD.md`.
- **CORS in development** — Vite proxy covers this for `npm run dev`, but if a developer runs `python manage.py runserver` + opens the built `index.html` directly, CSRF cookies won't work.
  → Mitigation: Document that development requires `npm run dev` (not opening `dist/` directly).
- **Bundle size baseline** — Tailwind + React + Router is ~130 kB gzipped. Acceptable for a network ops tool used on corporate LANs.

## Open Questions

- None. All decisions resolved for the scaffold phase.
