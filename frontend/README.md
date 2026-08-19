# NITA Webapp Frontend

React + TypeScript + Vite single-page application for the NITA webapp. It is
served from the root (`/`) by Django in production and talks to the REST API
under `/api/v1/`.

## Getting started

```bash
npm ci
npm run dev      # dev server on :5173, proxies /api to http://localhost:8000
npm run build    # tsc -b && vite build  ->  dist/
npm run lint     # eslint . (enforced in CI)
```

Node.js 22 is used by CI and by the Docker `frontend-builder` stage.

## Layout

```
src/
  api/client.ts        CSRF-aware fetch wrapper (apiFetch)
  hooks/               shared hooks (useApiResource)
  context/             auth context, useAuth/useIsAdmin/useIsPowerUser
  components/          reusable UI (AppLayout, dialogs, WorkbookGrid, ...)
  pages/               one component per route
```

## Routing

React Router runs with `basename="/"`. Django serves `index.html` for the root
and an explicit allowlist of top-level routes (`login`, `network-types`,
`networks`, `users`, `teams`, and their subpaths), so deep links and refreshes
resolve correctly.

**Adding a new top-level route requires updating the allowlist** in
`ngcn_workbench/urls.py` as well as `App.tsx` — otherwise a direct load or
refresh of that URL returns 404 even though in-app navigation works.

## Calling the API

Use `apiFetch` from `src/api/client.ts` rather than bare `fetch`. It sends
session credentials, and for mutating methods it reads the `csrftoken` cookie
(fetching `/api/v1/auth/csrf/` first if needed) and sets `X-CSRFToken`. It
deliberately leaves the `Content-Type` alone for `FormData` bodies so file
uploads keep their multipart boundary.

For mount-time reads use the `useApiResource` hook instead of hand-rolling
state:

```ts
const { data, loading, error, reload, setData, setError } =
  useApiResource<Paginated<Team>>('/api/v1/teams/', { enabled: isPowerUser })
```

It initialises loading at declaration and only updates state after the request
resolves, which keeps components free of the `react-hooks/set-state-in-effect`
error. Pass `enabled` for guarded fetches, `reload()` after a mutation, and
`setData` for optimistic list updates.

## Auth and role gating

`AuthProvider` (in `context/AuthContext.tsx`) hydrates the current user from
`GET /api/v1/auth/me/`, which returns `role` and `teams`. The context object and
hooks live in separate modules (`context/auth-context.ts`, `context/useAuth.ts`)
so component files export only components — required by
`react-refresh/only-export-components`.

Gate UI with `useIsAdmin()` / `useIsPowerUser()`. Note that the login response
does not include `role`, so `LoginPage` re-reads `/auth/me/` after signing in;
without that, role-gated navigation would not appear until a page refresh.

UI gating is a convenience only — the server is the real authorisation
boundary, and the API returns 403/409 regardless of what the UI shows.

## Conventions

- Every `frontend/**/*.{ts,tsx}` file must pass `npm run lint` with zero errors;
  CI fails the pull request otherwise.
- Prefer refactors over suppressions. A narrowly-scoped
  `// eslint-disable-next-line <rule> -- <reason>` is acceptable only with a
  justification comment.
- Keep non-component exports (contexts, hooks, types) out of `.tsx` component
  modules.
