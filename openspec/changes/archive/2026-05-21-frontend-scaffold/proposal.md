## Why

The NITA webapp currently serves all UI via Django templates — a server-rendered, jQuery-era interface that is difficult to maintain and extend. The modernization plan calls for a React SPA that talks exclusively to `/api/v1/`, so a reusable, typed frontend skeleton must exist before any feature migration can begin.

## What Changes

- Add a `frontend/` directory at the repo root containing a Vite + React 18 + TypeScript SPA project.
- Configure Vite's dev server to proxy `/api/` requests to `http://localhost:8000` so development works without CORS issues.
- Install and configure Tailwind CSS with dark mode enabled by default.
- Provide a minimal app shell: `<App>` root, React Router v6 with two initial routes (`/login` and `/` for the authenticated shell), and an `AuthContext` that calls `GET /api/v1/auth/me/` on load to determine login state.
- Provide a thin typed API client module (`src/api/client.ts`) that wraps `fetch`, reads the CSRF token from `GET /api/v1/auth/csrf/`, and attaches `X-CSRFToken` on every non-GET request.
- Add placeholder page components: `LoginPage` (calls `POST /api/v1/auth/login/`) and `DashboardPage` (empty shell, authenticated).
- Add `frontend/` to `.gitignore` exclusions for `node_modules` only; source files are committed.
- No Django templates are removed in this change (that is Phase 3, change ⑲).
- No Docker or nginx changes in this change (those are changes ⑤ and ⑥).

## Capabilities

### New Capabilities
- `frontend-skeleton`: The React/TypeScript SPA skeleton — project structure, build tooling, routing, auth context, and API client contract.

### Modified Capabilities

## Impact

- `frontend/` — new directory: `package.json`, `vite.config.ts`, `tsconfig.json`, `tailwind.config.ts`, `src/` tree.
- `.gitignore` — add `frontend/node_modules/`.
- No changes to Django, Python, or existing tests.
- Requires Node.js ≥ 20 in the developer's environment (not yet in Docker — that is change ⑤).
- New npm dependencies: `react`, `react-dom`, `react-router-dom`, `@types/react`, `@types/react-dom`, `typescript`, `vite`, `@vitejs/plugin-react`, `tailwindcss`, `autoprefixer`, `postcss`.
