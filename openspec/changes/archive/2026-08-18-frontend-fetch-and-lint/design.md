## Context

`frontend/eslint.config.js` composes `@eslint/js`, `typescript-eslint`,
`eslint-plugin-react-hooks` (flat recommended), and `eslint-plugin-react-refresh`
(vite), over `**/*.{ts,tsx}`. `package.json` exposes `"lint": "eslint ."`.

There is already a clean API layer: `src/api/client.ts` exports `apiFetch`, a
CSRF-aware wrapper (reads the `csrftoken` cookie, calls `GET /api/v1/auth/csrf/`
when needed, leaves `FormData` content-type to the browser).

Above that layer, each page repeats the same shape:

```
const [data, setData] = useState(...)
const [loading, setLoading] = useState(true)
const [error, setError] = useState<string|null>(null)
async function fetchX() { setLoading(true); try { ... setData(...) }
                          catch { setError(...) } finally { setLoading(false) } }
useEffect(() => { fetchX() }, [])         // ◀ react-hooks/set-state-in-effect
```

CI does not run this ESLint at all (super-linter ignores `frontend/`; the
Dockerfile runs `npm run build`, not lint). Current `npm run lint`: 15 errors —
`react-hooks/set-state-in-effect` (8: `NetworkDetailPage` ×3, `WorkbookGrid`,
`NetworkTypesPage`, `NetworksPage`, `TeamsPage`, `UsersPage`) and
`react-refresh/only-export-components` (7: `AuthContext.tsx` ×4,
`LifecycleConsole.tsx` ×3).

## Goals / Non-Goals

**Goals:**
- One shared, typed data-fetching hook; pages stop hand-rolling loading/error.
- All 15 ESLint errors resolved by refactor (no blanket suppressions).
- CI blocks PRs on any frontend ESLint error.

**Non-Goals:**
- A full query library, a separate TS-typecheck gate, new rules, Prettier, or
  touching legacy static JS.

## Decisions

### Decision 1: A lightweight `useApiResource` hook, not a query library

**Choice**: Add a small typed hook, e.g.
`useApiResource<T>(path, options?) => { data, loading, error, reload }`, built on
`apiFetch`. It initialises `loading=true` at declaration, performs the fetch in
an effect via an async inner function, and updates state only **after** the
`await` — so no `setState` runs synchronously in the effect body. It handles
abort on unmount and exposes `reload()` for manual refresh.

**Rationale**: Kills the `set-state-in-effect` errors at the root (the rule's
real concern — synchronous cascading renders), removes duplicated state across
pages, and gives one place for error/loading conventions — without the weight of
TanStack Query for an app this small.

**Alternatives**: TanStack Query/SWR — rejected (overkill, new dep, caching
semantics unneeded). Per-page `eslint-disable` — rejected (silences the smell,
keeps the duplication).

### Decision 2: Refactor pages onto the hook incrementally, preserving behaviour

**Choice**: Convert each affected page to `useApiResource` for its primary
mount-time fetch, keeping paginated-list shapes and existing UI states. Secondary
fetches (e.g. the directory roster in `TeamsPage`) either use the hook or a
plain async handler that does not set state synchronously in an effect.

**Rationale**: Behaviour-preserving, reviewable page-by-page; the drift is in the
wiring, not the UX.

### Decision 3: Split non-component exports into their own modules

**Choice**: Extract the auth context object and the `useAuth` hook from
`context/AuthContext.tsx` into dedicated modules (e.g. `context/auth-context.ts`,
`context/useAuth.ts`), leaving the component file exporting only `AuthProvider`;
move exported types/helpers out of `components/LifecycleConsole.tsx` into a
sibling module. Update importers.

**Rationale**: Keeps Vite Fast Refresh correct and is the maintainer-recommended
resolution for `react-refresh/only-export-components`. Where a single erased
`type` export makes extraction disproportionate, a narrowly-scoped, commented
`// eslint-disable-next-line` is acceptable — but extraction is preferred.

### Decision 4: Enforce via a dedicated `frontend-lint` PR job

**Choice**: Add a job to `.github/workflows/pull_workflow.yml` mirroring the
`django-pytest` job: `actions/setup-node` (Node **22**), `working-directory:
frontend`, `npm ci`, `npm run lint` (`eslint .` over the whole tree). Fails on
non-zero exit.

**Rationale**: Matches the repo's stated intent (the super-linter config comment
says the SPA "is linted via `npm run lint` from within `frontend/`"), gives a
fast isolated required check, and does not rebuild the Docker image.
Full-tree lint is safe because the tree is clean after this change.

## Risks / Trade-offs

- Refactor touches shared modules (`AuthContext`) → guarded by `tsc -b &&
  vite build` and the backend SPA-routing tests; update all importers.
- Hook abstraction could hide per-page nuances (pagination, guards like
  `if (isAdmin)`) → keep `reload()` + an `enabled`/guard option so guarded
  fetches stay expressible.
- Extra `npm ci` in CI → acceptable; runs in parallel with existing jobs.

## Migration Plan

Additive hook + behaviour-preserving page refactors + module splits + one CI job.
No runtime behaviour change, no schema, no data migration. Before merge:
`npm run lint` exits 0 and `npm run build` stays green.

## Open Questions

- Hook shape: return `reload` only, or also `setData` for optimistic updates?
  Proposed: `{ data, loading, error, reload }`, add `setData` only if a page
  needs optimistic edits.
- Node pin: `22` (matches Dockerfile) vs `lts/*`? Proposed: `22`.
