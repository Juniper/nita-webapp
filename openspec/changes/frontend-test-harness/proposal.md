## Why

The SPA has no way to run a test. `frontend/package.json` declares no `test`
script and no test-runner dependency, and there are no test files anywhere under
`frontend/src`. The backend has 204 pytest tests and a CI gate; the frontend has
ESLint and nothing else.

This is not hypothetical debt. Two recent changes were left with unfinished task
sections purely because there was nowhere to put a test:

- `refresh-inflight-action-status` — 5 tasks covering polling start/stop
- `dashboard-recent-activity` — 9 tasks covering the feed ordering rules

The dashboard's ordering logic is the substance of that change — "in-progress
first, then failures, newest-first within each, capped at ten" — and it is
exactly the kind of pure, branchy logic that regresses silently. It was verified
once, by hand, with a throwaway script that was deliberately not committed
because an unrunnable spec implies coverage that does not exist.

The backend already demonstrates the value: reverting the action-history scoping
fix turned 7 tests red immediately, which is how we knew the console-output leak
was real rather than theoretical. The frontend has no equivalent.

## What Changes

- **Add Vitest as the frontend test runner**, configured through the existing
  `vite.config.ts` so tests share the app's resolution, plugins and TypeScript
  settings rather than duplicating them.
- **Add `@testing-library/react` + `jsdom`** for component-level tests, and
  `@testing-library/jest-dom` for DOM matchers, wired through a single setup file
  that also auto-cleans the DOM between tests.
- **Add `npm test` (single run) and `npm run test:watch`** scripts.
- **Add a `frontend-test` CI job** to `pull_workflow.yml`, mirroring the existing
  `frontend-lint` job exactly: Node 22, `npm ci`, npm-cached on
  `frontend/package-lock.json`.
- **Test files live beside their subject** as `*.test.ts` / `*.test.tsx` under
  `frontend/src`, so they are type-checked by the existing `tsc -b` build.

## Capabilities

### Added Capabilities

- `frontend-testing`: a frontend test runner exists, is CI-enforced on pull
  requests, and the SPA's suite passes.

## Impact

- **Frontend**: five dev dependencies (`vitest`, `jsdom`,
  `@testing-library/react`, `@testing-library/jest-dom`,
  `@testing-library/user-event`); a `test` block in `vite.config.ts`; a new
  `src/test/setup.ts`; two new npm scripts.
- **CI**: one new job in `pull_workflow.yml`.
- **Docker**: none. The image build runs `npm ci && npm run build`; the new
  dependencies are dev-only and the build path is unchanged.
- **Unblocks**: the 14 outstanding test tasks in `refresh-inflight-action-status`
  and `dashboard-recent-activity`, which are completed as part of this change so
  the harness ships with real users rather than as empty scaffolding.

### Out of Scope

- **Coverage thresholds.** A percentage gate on a suite this young would measure
  the wrong thing and invite tests written to satisfy the number.
- **End-to-end/browser tests** (Playwright and friends). Different tool, different
  runtime cost, different change.
- **Backfilling tests for pre-existing pages** — Networks, Network Types, Users,
  Teams, Workbook. Valuable, but it would make this change unreviewable. The
  harness makes it possible; doing it is separate work.
- **Replacing the manual verification tasks** in the affected changes. Component
  tests do not exercise Jenkins, SSE against a real server, or the deployed SPA.
