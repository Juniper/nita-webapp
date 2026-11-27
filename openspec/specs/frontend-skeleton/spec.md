# frontend-skeleton Specification

## Purpose
Initial React SPA scaffold: Vite/TypeScript build tooling, client-side
routing, auth context, CSRF-aware API client, login page, dashboard shell, and
document identity.

## Requirements

### Requirement: SPA Build Tooling
The system SHALL provide a `frontend/` directory at the repo root containing a Vite + React 18 + TypeScript project buildable with `npm run build`. The project SHALL use `@vitejs/plugin-react` and emit static assets to `frontend/dist/`.

#### Scenario: Production build succeeds
- GIVEN Node.js ≥ 20 is installed and `npm install` has been run in `frontend/`
- WHEN `npm run build` is executed in `frontend/`
- THEN the build exits with code 0
- AND `frontend/dist/index.html` exists

#### Scenario: Development server starts
- GIVEN Node.js ≥ 20 is installed and `npm install` has been run in `frontend/`
- WHEN `npm run dev` is executed in `frontend/`
- THEN a local dev server starts (default port 5173)
- AND requests to `/api/` are proxied to `http://localhost:8000`

### Requirement: Dark Mode Default
The system SHALL apply Tailwind CSS with `darkMode: 'class'` strategy. The `<html>` element SHALL have the `dark` class set before the React tree renders, making dark mode the default for all users.

#### Scenario: Dark mode active by default
- GIVEN the SPA is loaded in a browser
- WHEN no user preference has been explicitly set
- THEN the `<html>` element has the class `dark`
- AND Tailwind dark-mode utility classes (e.g., `dark:bg-gray-900`) are applied

### Requirement: Client-Side Routing
The system SHALL use React Router v6 with two initial routes:
- `GET /login` — renders `LoginPage` (accessible without authentication).
- `GET /` — renders the authenticated shell; unauthenticated users are redirected to `/login`.

#### Scenario: Unauthenticated root access redirects to login
- GIVEN the user is not authenticated (GET /api/v1/auth/me/ returns 403)
- WHEN the browser navigates to `/`
- THEN the app redirects to `/login`

#### Scenario: Authenticated root access renders dashboard
- GIVEN the user is authenticated (GET /api/v1/auth/me/ returns 200)
- WHEN the browser navigates to `/`
- THEN `DashboardPage` is rendered showing the logged-in username

#### Scenario: Direct login page access always renders
- GIVEN any authentication state
- WHEN the browser navigates to `/login`
- THEN `LoginPage` is rendered without redirect

### Requirement: Auth Context
The system SHALL provide an `AuthContext` React context that:
- Calls `GET /api/v1/auth/me/` on mount to determine session state.
- Exposes `user: {id, username, is_superuser} | null` and a `logout()` function.
- The `logout()` function calls `POST /api/v1/auth/logout/` and clears the `user` state.

#### Scenario: Auth context detects existing session
- GIVEN a Django session cookie is present in the browser
- WHEN the app mounts and AuthContext initialises
- THEN `user` is set to the logged-in user's info
- AND the app renders the authenticated shell

#### Scenario: Auth context detects no session
- GIVEN no valid session cookie is present
- WHEN the app mounts and AuthContext initialises
- THEN `user` is null
- AND the app redirects to `/login`

### Requirement: CSRF-Aware API Client
The system SHALL provide `src/api/client.ts` that wraps the browser `fetch` API:
- For GET requests: forwards the request with `credentials: 'include'`.
- For POST/PUT/PATCH/DELETE requests: first calls `GET /api/v1/auth/csrf/` (cached after first call) to obtain the CSRF token, then attaches it as the `X-CSRFToken` request header alongside `credentials: 'include'`.

#### Scenario: GET request is sent without CSRF header
- GIVEN the API client is used to call a GET endpoint
- WHEN the request is made
- THEN no `X-CSRFToken` header is attached

#### Scenario: POST request includes CSRF token
- GIVEN the API client is used to call a POST endpoint
- WHEN the request is made
- THEN `X-CSRFToken` is present in the request headers with a non-empty value

#### Scenario: JSON body gets a JSON content type
- GIVEN the API client is used to POST a non-FormData body with no explicit Content-Type
- WHEN the request is made
- THEN the `Content-Type` header is set to `application/json`

#### Scenario: FormData upload preserves the multipart boundary
- GIVEN the API client is used to POST a `FormData` body
- WHEN the request is made
- THEN the client does NOT set a `Content-Type` header
- AND the browser sets `Content-Type: multipart/form-data` with a boundary

### Requirement: API Client Content-Type Defaulting
The API client (`src/api/client.ts`) SHALL default the `Content-Type` to
`application/json` only when the request body is NOT a `FormData` instance and
no `Content-Type` header has been supplied. For `FormData` bodies the client
SHALL NOT set `Content-Type`, so the browser can supply the correct
`multipart/form-data` boundary (forcing `application/json` causes the server to
reject uploads with HTTP 415).

#### Scenario: JSON body defaults to application/json
- GIVEN a request with a non-`FormData` body and no `Content-Type` header
- WHEN the API client sends it
- THEN the request carries `Content-Type: application/json`

#### Scenario: Caller-supplied Content-Type is preserved
- GIVEN a request with a non-`FormData` body and an explicit `Content-Type` header
- WHEN the API client sends it
- THEN the caller's `Content-Type` is sent unchanged

### Requirement: Login Page
The `LoginPage` SHALL submit its username/password form to
`POST /api/v1/auth/login/` via the API client and update `AuthContext` on
success. It SHALL follow a safe same-origin `next` path or fall back to `/`;
on failure it SHALL display an error and remain on the login page. It SHALL
show a decorative brand mark above its heading.

#### Scenario: Login page shows the brand mark
- WHEN an unauthenticated user opens `/login`
- THEN the brand mark is displayed above the "NITA Webapp" heading
- AND the mark is legible against the login card background

#### Scenario: Login page brand mark is decorative
- WHEN a screen reader traverses the login page
- THEN the mark is not announced
- AND the heading is announced exactly once

#### Scenario: Successful login redirects to dashboard
- GIVEN valid credentials are entered and no `next` parameter is present
- WHEN the login form is submitted
- THEN the user is redirected to `/`
- AND the username is visible in the authenticated shell

#### Scenario: Failed login shows error
- GIVEN invalid credentials are entered
- WHEN the login form is submitted
- THEN an error message is displayed on the page

#### Scenario: Successful login follows a safe next target
- GIVEN the user opened `/login?next=/jenkins/job/test-robot-net1/`
- WHEN valid credentials are submitted
- THEN the browser navigates to `/jenkins/job/test-robot-net1/`

#### Scenario: Unsafe next targets are ignored
- GIVEN the user opened `/login?next=//evil.example/` or `/login?next=https://evil.example/`
- WHEN valid credentials are submitted
- THEN the browser navigates to `/`
- AND only paths beginning with a single `/`, without a URL scheme, are accepted

### Requirement: Dashboard Renders for Authenticated Users
The system SHALL provide a `DashboardPage` component that renders at `/` when the
user is authenticated, wrapped in `AppLayout`. Its content SHALL be the recent
activity feed specified by the `spa-dashboard` capability. Unauthenticated access
to `/` SHALL continue to redirect to `/login`.

#### Scenario: Authenticated root access renders the dashboard
- GIVEN the user is authenticated
- WHEN the user navigates to `/`
- THEN `DashboardPage` is rendered inside `AppLayout` showing the recent activity
  feed

#### Scenario: Unauthenticated root access redirects to login
- GIVEN the user is not authenticated
- WHEN the user navigates to `/`
- THEN the user is redirected to `/login`

#### Scenario: Logout from the dashboard
- GIVEN the user is on the dashboard
- WHEN the logout button in the header is clicked
- THEN the user is redirected to `/login`
- AND subsequent navigation to `/` redirects back to `/login`

### Requirement: Document Identity
The SPA's HTML document SHALL identify the application rather than the project
template it was scaffolded from. The document title SHALL be `NITA Webapp`, and
the favicon SHALL be the NITA brand mark served from `/favicon.svg`.

The favicon SHALL carry explicit colour values rather than relying on
inheritance, and SHALL remain legible on both light and dark browser tab strips.

The `frontend/` tree SHALL NOT contain unreferenced scaffold assets from the
project template.

#### Scenario: Browser tab shows the application title
- WHEN a user opens any page of the SPA
- THEN the browser tab displays `NITA Webapp`

#### Scenario: Browser tab shows the NITA mark
- WHEN a user opens any page of the SPA
- THEN the favicon requested from `/favicon.svg` is the NITA brand mark

#### Scenario: Favicon is legible in a dark tab strip
- GIVEN the operating system is set to a dark colour scheme
- WHEN the browser renders the favicon
- THEN the mark is drawn in a light colour rather than near-black

#### Scenario: No template scaffold assets remain
- WHEN the `frontend/` tree is inspected
- THEN it contains no unreferenced images carried over from the project template

#### Scenario: Favicon does not depend on inherited colour
- GIVEN the favicon is rendered in a browser tab, without a surrounding colour
  context
- WHEN the tab strip uses a light or a dark theme
- THEN the mark is drawn with its own explicit colour values and remains legible
