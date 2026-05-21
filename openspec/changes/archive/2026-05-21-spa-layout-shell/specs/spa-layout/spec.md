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
