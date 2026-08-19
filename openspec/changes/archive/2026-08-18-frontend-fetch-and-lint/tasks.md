## 1. Shared Data-Fetching Hook

- [x] 1.1 Add `src/hooks/useApiResource.ts`: typed
  `useApiResource<T>(path, options?) => { data, loading, error, reload }`, built
  on `apiFetch`; `loading` initialised at declaration; state updated only after
  `await`; abort on unmount; `reload()` for manual refresh
- [x] 1.2 Support a guard/`enabled` option so conditional fetches
  (e.g. `if (isAdmin)`, `if (isPowerUser)`) are expressible without a synchronous
  in-effect `setState`
- [x] 1.3 (If needed) expose `setData` for optimistic updates where a page mutates
  the fetched list in place

## 2. Refactor Pages onto the Hook (fixes `set-state-in-effect`, 8)

- [x] 2.1 `pages/NetworksPage.tsx` — mount fetch via the hook
- [x] 2.2 `pages/NetworkDetailPage.tsx` — three fetches via the hook/handlers
- [x] 2.3 `pages/NetworkTypesPage.tsx` — mount fetch via the hook
- [x] 2.4 `pages/TeamsPage.tsx` — teams + directory (guarded on `isPowerUser`)
- [x] 2.5 `pages/UsersPage.tsx` — users (guarded on `isAdmin`)
- [x] 2.6 `components/WorkbookGrid.tsx` — effect fetch via the hook/handler
- [x] 2.7 Verify each page preserves existing loading/error/pagination behaviour

## 3. Split Non-Component Exports (fixes `only-export-components`, 7)

- [x] 3.1 `context/AuthContext.tsx` — extract the context object and `useAuth`
  into their own modules; leave the file exporting only `AuthProvider`
- [x] 3.2 `components/LifecycleConsole.tsx` — move exported types/helpers into a
  sibling module so the file exports only the component
- [x] 3.3 Update all importers to the new module paths

## 4. Enforce Frontend ESLint in CI

- [x] 4.1 Add a `frontend-lint` job to `.github/workflows/pull_workflow.yml`
  (`actions/setup-node` Node 22, `working-directory: frontend`, `npm ci`,
  `npm run lint`)
- [x] 4.2 Ensure the job fails the workflow on any ESLint error (non-zero exit)

## 5. Verify

- [x] 5.1 `npm run lint` in `frontend/` exits 0 (zero errors)
- [x] 5.2 `npm run build` (`tsc -b && vite build`) stays green
- [x] 5.3 Backend `pytest` suite still passes (SPA-routing unaffected)
- [ ] 5.4 Confirm the new `frontend-lint` check runs and passes on the PR
