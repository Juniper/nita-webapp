## Context

The frontend build is Vite 8 + React 19 + TypeScript 6, with `tsconfig.app.json`
covering `include: ["src"]` and the strict `react-hooks` ESLint rules. The Docker
`frontend-builder` stage and the `frontend-lint` CI job both pin Node 22, and the
`frontend-lint` capability already specifies what a frontend CI gate looks like
in this repo — that job is the template to copy rather than reinvent.

`useApiResource` funnels every read through `apiFetch` from `src/api/client.ts`,
and pages reach the router through `react-router-dom`. Those two seams are what
component tests need to control.

## Goals / Non-Goals

**Goals:**
- A frontend test can be written and run, locally and in CI.
- The runner shares the app's existing resolution and TypeScript configuration.
- The harness ships with real tests, not empty scaffolding.

**Non-Goals:**
- Coverage gates, end-to-end tests, or backfilling tests for existing pages.

## Decisions

### Decision 1: Vitest rather than Jest

**Choice**: Vitest, configured inside the existing `vite.config.ts`.

**Rationale**: The project is already a Vite project. Vitest reuses that config —
plugins, alias resolution, TypeScript handling, the React JSX transform — so
there is exactly one place where module resolution is defined. Jest would need a
parallel transform stack (babel or ts-jest, ESM interop, its own moduleNameMapper)
that could drift from the build and produce the failure mode where a test passes
but the bundle breaks. Vitest's `expect`/`describe`/`it` API is Jest-compatible,
so the ecosystem knowledge transfers.

### Decision 2: Explicit imports, not global test APIs

**Choice**: Leave `globals` off; tests import `describe`, `it`, `expect`, `vi`
from `vitest`.

**Rationale**: `globals: true` requires adding `"types": ["vitest/globals"]` to
`tsconfig.app.json`, which pulls test typings into the production type-check for
every file. Explicit imports keep that boundary clean and cost one line per test
file. It also keeps `noUnusedLocals` honest.

### Decision 3: Tests live beside their subject

**Choice**: `src/**/*.test.ts(x)`, next to the module under test, matched by the
Vitest `include` pattern.

**Rationale**: Co-location makes the existence (or absence) of a test obvious when
reading a directory, and it means `tsconfig.app.json`'s `include: ["src"]` already
type-checks tests during `npm run build` — a second gate for free, catching type
errors in tests without a separate tsconfig.

**Consequence (accepted)**: Tailwind's automatic source scanning also sees test
files, so class-like strings in a test could add a few bytes to the production
CSS. Measured at ~30 bytes for the current suite. Noted rather than worked around,
since excluding them costs configuration for negligible benefit.

### Decision 4: A single setup file that auto-cleans

**Choice**: `src/test/setup.ts` imports `@testing-library/jest-dom/vitest` and
registers `afterEach(cleanup)`.

**Rationale**: DOM matchers (`toBeInTheDocument`) make assertions read well, and
automatic cleanup prevents the classic cross-test leak where a previous render is
still mounted and `getByText` matches the wrong element. Doing it once centrally
means no test has to remember.

### Decision 5: Mock at the `apiFetch` seam, not at `fetch`

**Choice**: Component tests `vi.mock('../api/client')` and drive `apiFetch`
directly.

**Rationale**: `apiFetch` is where CSRF handling, credential mode and header
defaults live. Stubbing global `fetch` would force every test to model that
behaviour; stubbing `apiFetch` lets tests express only what the component asks
for. It is also the seam the app itself is written against, so tests exercise the
same contract the pages depend on.

### Decision 6: Fake timers for the polling tests

**Choice**: `vi.useFakeTimers()`, advancing inside `act()` and flushing
microtasks between assertions.

**Rationale**: The polling interval is 15 seconds. Real-time tests would either
take minutes or force the interval to become injectable purely for testability.
Fake timers assert the real production interval without waiting for it.

### Decision 7: A CI job that mirrors `frontend-lint`

**Choice**: A separate `frontend-test` job, same Node 22, same `npm ci`, same
cache key — not a step appended to the lint job.

**Rationale**: Separate jobs run in parallel and report independently, so a
failing test and a failing lint are distinguishable at a glance in the checks
list. This matches how the repo already separates `django_build_and_test` from
`frontend-lint`.

## Risks / Trade-offs

- **A test suite is a maintenance surface.** Mitigated by scope: the tests added
  here target logic that is pure (feed ordering) or behavioural and easy to get
  wrong (polling lifecycle), not markup that will churn.
- **Component tests couple to DOM text.** Assertions such as "no recent activity"
  break if copy changes. Accepted; the alternative (test IDs everywhere) adds
  production markup for test convenience.
- **`vite.config.ts` now needs the Vitest types.** A `/// <reference
  types="vitest/config" />` directive is required or `tsc -b` rejects the `test`
  key. Documented here because the failure message ("'test' does not exist in
  type 'UserConfigExport'") does not suggest the fix.
- **Dev dependency weight.** 78 packages. They are dev-only and do not reach the
  runtime image.

## Migration Plan

Purely additive. No production source changes, no API or schema impact. The
Docker build is unaffected: `npm ci` installs dev dependencies and `npm run build`
is unchanged.

## Open Questions

- **Should `npm test` join the Docker build as a gate?** Currently the image build
  runs lint-free and test-free, relying on CI. Adding it would catch a broken
  build earlier but slow every image build.
- **Coverage reporting later?** Useful as information (which files have no tests
  at all) even without a failing threshold. Deliberately excluded for now.
- **Do the pre-existing pages get backfilled?** The harness makes it possible;
  someone has to decide whether it is worth the effort for pages that are stable.
