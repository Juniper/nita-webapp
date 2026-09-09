# Frontend Testing Specification

## Purpose
A test runner for the React/TypeScript SPA, CI-enforced on pull requests, so that
frontend regressions cannot merge silently — the counterpart to the backend's
pytest suite and to the `frontend-lint` gate.

## Requirements

### Requirement: Frontend Test Runner Exists
The SPA SHALL provide a test runner executable from `frontend/` as
`npm test` (a single, non-watching run) and `npm run test:watch` (watch mode).
The runner SHALL share the application's Vite configuration so that module
resolution, plugins and TypeScript settings are defined in exactly one place.

Test files SHALL be discovered at `frontend/src/**/*.{test,spec}.{ts,tsx}`,
co-located with the modules they exercise, so that the existing
`tsconfig.app.json` (`include: ["src"]`) type-checks them during
`npm run build`.

A shared setup file SHALL register DOM matchers and SHALL unmount rendered
components between tests, so that no individual test has to perform cleanup.

#### Scenario: Test suite runs to completion
- WHEN `npm test` is run in `frontend/`
- THEN the runner executes every file matching the test pattern
- AND exits zero when all tests pass

#### Scenario: A failing test fails the run
- GIVEN a test file containing a failing assertion
- WHEN `npm test` is run
- THEN the run exits non-zero and names the failing test

#### Scenario: Component tests can render the SPA's pages
- GIVEN a test that renders a page component in a jsdom environment
- WHEN the test queries the rendered output by role or text
- THEN the query resolves against that page's DOM

#### Scenario: Rendered components do not leak between tests
- GIVEN two tests that each render a component
- WHEN the second test queries the DOM
- THEN it does not match elements rendered by the first

#### Scenario: Test files are type-checked by the build
- GIVEN a test file containing a TypeScript type error
- WHEN `npm run build` is run
- THEN the build fails

### Requirement: CI Enforces Frontend Tests on Pull Requests
The pull-request CI workflow SHALL run the frontend test suite (`npm test` in
`frontend/`) and SHALL fail the workflow when one or more tests fail. The job
SHALL install dependencies with `npm ci` and run on Node.js 22, matching the
Docker `frontend-builder` stage and the existing frontend lint job. It SHALL be
a separate job from the lint job so that the two report independently.

#### Scenario: PR with a failing frontend test is blocked
- GIVEN a pull request that introduces a failing frontend test
- WHEN the pull-request workflow runs
- THEN the frontend test job exits non-zero
- AND the pull request's checks report the frontend test job as failed

#### Scenario: PR with a passing suite clears the gate
- GIVEN a pull request whose frontend test suite passes
- WHEN the pull-request workflow runs
- THEN the frontend test job exits zero

#### Scenario: Lint and test failures are distinguishable
- GIVEN a pull request that both fails a test and introduces a lint error
- WHEN the pull-request workflow runs
- THEN the lint job and the test job are reported as two separate failed checks

### Requirement: Frontend Suite Passes
The `frontend/` test suite SHALL pass with zero failures on the default branch.
Tests SHALL isolate the application from the network by mocking the `apiFetch`
seam in `src/api/client.ts` rather than the global `fetch`, and SHALL use fake
timers when asserting interval-driven behaviour so that the production interval
value is exercised without waiting for it.

#### Scenario: Suite is green on the default branch
- WHEN `npm test` is run against the default branch
- THEN every test passes

#### Scenario: Tests make no network requests
- WHEN a component test renders a page that fetches data on mount
- THEN the request is served by the mocked `apiFetch` and no real network call is
  made

#### Scenario: Interval behaviour is asserted without real waiting
- GIVEN a component that refreshes on a 15-second interval
- WHEN a test advances fake timers by 15 seconds
- THEN the refresh is observed without the test taking 15 seconds
