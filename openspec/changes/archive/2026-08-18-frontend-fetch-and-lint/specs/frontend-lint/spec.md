## ADDED Requirements

### Requirement: CI Enforces Frontend ESLint on Pull Requests
The pull-request CI workflow SHALL run the frontend ESLint (`npm run lint` in
`frontend/`, which executes `eslint .` against `frontend/eslint.config.js`) and
SHALL fail the workflow when ESLint reports one or more errors. The lint job
SHALL install dependencies with `npm ci` and run on Node.js 22 (matching the
Docker `frontend-builder` stage).

#### Scenario: PR with a frontend lint error is blocked
- GIVEN a pull request that introduces a `frontend/` source file with an ESLint
  error
- WHEN the pull-request workflow runs
- THEN the frontend lint job exits non-zero
- AND the pull request's checks report the frontend lint job as failed

#### Scenario: PR with clean frontend passes the lint gate
- GIVEN a pull request whose `frontend/` source has zero ESLint errors
- WHEN the pull-request workflow runs
- THEN the frontend lint job exits zero
- AND the frontend lint check is reported as successful

#### Scenario: Lint runs over the whole frontend tree
- WHEN the frontend lint job runs
- THEN ESLint evaluates all `frontend/**/*.{ts,tsx}` sources (not only the files
  changed in the pull request)

### Requirement: Frontend Source Passes ESLint With Zero Errors
The `frontend/` TypeScript/React source SHALL pass ESLint with zero errors under
`frontend/eslint.config.js`, including the `react-hooks/set-state-in-effect` and
`react-refresh/only-export-components` rules. Violations SHALL be resolved by
idiomatic refactors; blanket rule suppression SHALL NOT be used, and any
`eslint-disable` SHALL be narrowly scoped to a single line with a justifying
comment.

#### Scenario: Clean lint on the current tree
- WHEN `npm run lint` is executed in `frontend/`
- THEN it exits with code 0 and reports zero errors

#### Scenario: Component modules export only components
- GIVEN a `*.tsx` module that renders a component
- WHEN ESLint evaluates the module
- THEN no `react-refresh/only-export-components` error is reported (non-component
  exports such as contexts, hooks, and types live in their own modules)
