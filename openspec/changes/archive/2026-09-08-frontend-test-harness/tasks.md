## 1. Runner and configuration

- [x] 1.1 Add dev dependencies: `vitest`, `jsdom`, `@testing-library/react`,
  `@testing-library/jest-dom`, `@testing-library/user-event`
- [x] 1.2 Add a `test` block to `vite.config.ts` (`environment: 'jsdom'`,
  `setupFiles`, `include: ['src/**/*.{test,spec}.{ts,tsx}']`)
- [x] 1.3 Add `/// <reference types="vitest/config" />` so `tsc -b` accepts the
  `test` key
- [x] 1.4 Add `src/test/setup.ts` importing `@testing-library/jest-dom/vitest`
  and registering `afterEach(cleanup)`
- [x] 1.5 Add `test` (`vitest run`) and `test:watch` (`vitest`) npm scripts

## 2. CI

- [x] 2.1 Add a `frontend-test` job to `.github/workflows/pull_workflow.yml`
  mirroring `frontend-lint`: Node 22, npm cache on
  `frontend/package-lock.json`, `npm ci`, then `npm test`
- [x] 2.2 Keep the job separate from `frontend-lint` so the two report
  independently

## 3. Prove the harness on real logic

- [x] 3.1 `dashboardFeed.test.ts` — grouping, ordering, ten-row cap, unrecognised
  statuses, relative time (13 tests)
- [x] 3.2 `NetworkDetailPage.history.test.tsx` — History tab polling lifecycle
  and attribution column (7 tests)
- [x] 3.3 `DashboardPage.test.tsx` — deep links, empty state, error state, row
  cap, polling lifecycle (10 tests)
- [x] 3.4 Confirm the polling tests fail when polling is disabled

## 4. Verify

- [x] 4.1 `npm test` green
- [x] 4.2 `npm run lint` green with test files present
- [x] 4.3 `npm run build` green (test files are type-checked by `tsc -b`)

## 5. Close out the blocked task sections

- [x] 5.1 Complete section 3 of `refresh-inflight-action-status`
- [x] 5.2 Complete section 4 of `dashboard-recent-activity`

## Verification notes

**30 tests across 3 files, all passing.** `npm run lint` and `npm run build` are
both green with the test files in place.

**The polling tests were confirmed to catch regressions.** Replacing the
`usePollWhile` predicate in `NetworkDetailPage` with a constant `false` turns two
tests red and leaves the rest green:

```
× refetches after the interval while a run is Running
× stops polling once the last Running entry reaches a terminal status
Tests  2 failed | 28 passed (30)
```

The file was restored afterwards.

**One trap worth recording**: `screen.getAllByRole('link')` over-counts on any
page wrapped in `AppLayout`, because the sidebar contributes three nav links. The
dashboard tests scope link assertions to hrefs containing `?tab=history`. A naive
count asserted 10 and got 13.

**Note on history**: this change was first built on 2026-09-03 and lost before it
was committed, together with the host toolchain and the deployed hot-patch, when
the working tree was cleaned. It was rebuilt on 2026-09-08 from the same content.
It is worth committing promptly.
