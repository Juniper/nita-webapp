## ADDED Requirements

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

### Requirement: Login Page
The system SHALL provide a `LoginPage` component that renders a username/password form. On submission it calls `POST /api/v1/auth/login/` via the API client. On success it updates `AuthContext` and redirects to `/`. On failure it displays an error message.

#### Scenario: Successful login redirects to dashboard
- GIVEN valid credentials are entered
- WHEN the login form is submitted
- THEN the user is redirected to `/`
- AND the username is visible in the authenticated shell

#### Scenario: Failed login shows error
- GIVEN invalid credentials are entered
- WHEN the login form is submitted
- THEN an error message is displayed on the page
- AND the user remains on `/login`

### Requirement: Dashboard Shell Placeholder
The system SHALL provide a `DashboardPage` component that renders when the user is authenticated. It SHALL display the logged-in username and a logout button. Clicking logout calls `AuthContext.logout()` and redirects to `/login`.

#### Scenario: Dashboard shows username
- GIVEN the user is authenticated
- WHEN `DashboardPage` is rendered
- THEN the page displays the user's username

#### Scenario: Logout button redirects to login
- GIVEN the user is on the dashboard
- WHEN the logout button is clicked
- THEN the user is redirected to `/login`
- AND subsequent navigation to `/` redirects back to `/login`
