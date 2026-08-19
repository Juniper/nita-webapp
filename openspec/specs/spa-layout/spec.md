## ADDED Requirements

### Requirement: AppLayout provides persistent application chrome
The SPA SHALL have an `AppLayout` component that renders a top header and left sidebar around its `children`. All authenticated pages SHALL use `AppLayout` as their outermost wrapper.

#### Scenario: Header shows brand and user
- **WHEN** an authenticated user views any protected page
- **THEN** the header SHALL display the application brand name on the left and the signed-in username on the right

#### Scenario: Header provides logout
- **WHEN** the user clicks the logout button in the header
- **THEN** the session SHALL be cleared and the user SHALL be redirected to `/login`

#### Scenario: Sidebar shows navigation links
- **WHEN** an authenticated user views any protected page
- **THEN** the sidebar SHALL display navigation links for: Dashboard (`/`), Network Types (`/network-types`), Networks (`/networks`)

#### Scenario: Active nav link is highlighted
- **WHEN** the current route matches a sidebar link
- **THEN** that link SHALL appear visually distinct (highlighted) from the inactive links

#### Scenario: Login page has no layout chrome
- **WHEN** the user views the login page
- **THEN** the header and sidebar SHALL NOT be rendered

### Requirement: Role-Gated Navigation Entries
The SPA layout SHALL show navigation entries appropriate to the authenticated
user's role: a **User Management** entry (linking to `/users`) SHALL be visible
only to admins, and a **Teams** entry (linking to `/teams`) SHALL be visible only
to `power_user` or `admin`. Role SHALL be derived from the `role` and
`is_superuser` fields returned by `GET /api/v1/auth/me/`.

#### Scenario: Admin sees User Management in the sidebar
- **GIVEN** a logged-in user with `role=admin`
- **WHEN** the app layout renders
- **THEN** a **User Management** navigation entry linking to `/users` is present

#### Scenario: Regular user sees neither admin entry
- **GIVEN** a logged-in user with `role=user`
- **WHEN** the app layout renders
- **THEN** neither **User Management** nor **Teams** entries are shown

#### Scenario: Power user sees Teams but not User Management
- **GIVEN** a logged-in user with `role=power_user`
- **WHEN** the app layout renders
- **THEN** a **Teams** entry is shown and **User Management** is not

### Requirement: SPA Route Allowlist Includes User/Team Routes
The server-side SPA route allowlist (regex in `ngcn_workbench/urls.py`) SHALL
include the `users` and `teams` client routes so they are served the SPA shell on
direct load or refresh, and the `SPA_ROUTES` list in the routing test SHALL stay
in sync.

#### Scenario: Direct load of a new SPA route returns the shell
- **WHEN** `/users` or `/teams` is requested directly from the server
- **THEN** the SPA `index.html` is returned with HTTP 200

#### Scenario: Allowlist drift is caught by tests
- **GIVEN** a client route present in `App.tsx` but missing from the allowlist
- **WHEN** the SPA routing tests run
- **THEN** the parametrised route assertion fails
