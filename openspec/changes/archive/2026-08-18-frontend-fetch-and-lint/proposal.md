## Why

The React SPA carries two coupled problems. First, its ESLint (`typescript-eslint`
+ `react-hooks` + `react-refresh`, via `frontend/eslint.config.js`) is **not run
by any CI check**: the Pull workflow's super-linter only validates legacy `.js`
(its config `ignores` `frontend/`), and the Dockerfile runs `npm run build`
(`tsc -b && vite build`), not `npm run lint`. Lint regressions merge silently.

Second, the lint that *would* run is already red — **15 errors across 8 files**,
and the largest cluster (`react-hooks/set-state-in-effect`, 8) is not cosmetic:
it points at a **missing abstraction**. Every list page hand-rolls the same
`data / loading / error` state and a `fetchX()` called from `useEffect`, calling
`setState` synchronously in the effect body. The rule is flagging duplicated,
smell-y wiring, not a formatting nit. The remaining errors
(`react-refresh/only-export-components`, 7 — mostly `AuthContext.tsx`) are a
mechanical module-split.

This change fixes the wiring rather than silencing the alarm: introduce a shared
data-fetching hook, refactor the pages onto it (removing the errors at the root),
split the non-component exports, and add a CI gate so the frontend stays clean.

## What Changes

- Introduce a **shared data-fetching hook** (`useApiResource`-style) exposing
  `{ data, loading, error, reload }`, built on the existing
  `src/api/client.ts` (`apiFetch`). Mount-time fetching goes through it and does
  **not** call `setState` synchronously in an effect body.
- **Refactor the list/detail pages** (`NetworksPage`, `NetworkDetailPage`,
  `NetworkTypesPage`, `TeamsPage`, `UsersPage`, `WorkbookGrid`) onto the hook,
  removing the duplicated state and resolving all 8
  `react-hooks/set-state-in-effect` errors.
- **Split non-component exports** out of component modules (extract the auth
  context object + `useAuth` hook from `AuthContext.tsx`; move exported
  types/helpers out of `LifecycleConsole.tsx`), resolving the 7
  `react-refresh/only-export-components` errors.
- Add a **frontend-lint CI gate**: a PR job that runs `npm ci` + `npm run lint`
  in `frontend/` (Node 22, matching the Docker builder) and fails on any error.

## Capabilities

### Added Capabilities

- `frontend-data-fetching`: a shared hook standardises SPA data fetching
  (`data/loading/error/reload`); components do not set state synchronously in
  effects.
- `frontend-lint`: CI runs the frontend ESLint on pull requests and blocks on
  any error; the `frontend/` source passes ESLint with zero errors.

## Impact

- **Frontend**: new `src/hooks/useApiResource.ts` (or similar); refactors in
  `pages/NetworksPage.tsx`, `pages/NetworkDetailPage.tsx`,
  `pages/NetworkTypesPage.tsx`, `pages/TeamsPage.tsx`, `pages/UsersPage.tsx`,
  `components/WorkbookGrid.tsx`; new small modules for the extracted
  context/hook/types from `context/AuthContext.tsx` and
  `components/LifecycleConsole.tsx`; importer updates.
- **CI**: new `frontend-lint` job in `.github/workflows/pull_workflow.yml` — a
  new required PR check.
- **No backend, API, or schema changes.**

### Out of Scope

- Adopting a full query library (TanStack Query / SWR) — overkill for this app's
  size; the lightweight hook is deliberate.
- A separate TypeScript type-check CI gate — already covered by `tsc -b` in the
  build.
- New or stricter ESLint rules beyond the current config; Prettier/formatting.
- Linting the legacy `static/**` jQuery assets (still handled by super-linter).
