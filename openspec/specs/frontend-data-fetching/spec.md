# Frontend Data Fetching Specification

## Purpose
Standardised client-side data fetching for the React SPA via a shared hook, so
components do not hand-roll loading/error state or set state synchronously inside
effects.

## Requirements

### Requirement: Shared Data-Fetching Hook
The SPA SHALL provide a shared, typed data-fetching hook that returns a
consistent shape `{ data, loading, error, reload }` for mount-time API reads,
built on the existing CSRF-aware `apiFetch` client. Components performing
mount-time data reads SHALL use this hook rather than hand-rolling
`loading`/`error`/`data` state. The hook SHALL initialise its loading state at
declaration and update state only after the asynchronous request resolves, so no
component sets state synchronously within a `useEffect` body
(`react-hooks/set-state-in-effect` reports zero errors).

#### Scenario: Successful read exposes data and clears loading
- GIVEN a component uses the hook to read a list endpoint
- WHEN the request succeeds
- THEN `loading` transitions to `false`, `data` holds the parsed result, and
  `error` is null

#### Scenario: Failed read surfaces an error
- GIVEN a component uses the hook to read an endpoint
- WHEN the request fails
- THEN `error` holds a message and `loading` is `false`

#### Scenario: Reload re-runs the request
- GIVEN a component has loaded data via the hook
- WHEN `reload()` is invoked (e.g. after a mutation)
- THEN the request is re-issued and `data` reflects the refreshed result

#### Scenario: Conditional fetch does not set state synchronously in an effect
- GIVEN a component that fetches only when a guard is true (e.g. `isAdmin`)
- WHEN ESLint evaluates the component
- THEN no `react-hooks/set-state-in-effect` error is reported
